"""Score + SFX + dialogue mix, all synthesized with numpy."""
import math, os, pickle, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voices
from sim import load_tl, CHARS
from timeline import FPS

SR = 44100
RNG = np.random.default_rng(11)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, r, sus=1.0):
    e = np.full(n, sus)
    na, nr = int(a * SR), int(r * SR)
    na = min(na, n); nr = min(nr, n - na)
    if na:
        e[:na] = np.linspace(0, sus, na) ** 1.5
    if nr > 0:
        e[n - nr:] *= np.linspace(1, 0, nr) ** 1.3
    return e


def tt(n):
    return np.arange(n) / SR


# ---------------------------------------------------------------- instruments
def celesta(f, dur=1.8, amp=1.0):
    n = int(dur * SR); t = tt(n)
    y = np.zeros(n)
    for r, a, d in ((1, 1, 1.6), (2, .45, .9), (3, .18, .5), (4.16, .12, .3), (5.43, .05, .2)):
        if f * r < 16000:
            y += a * np.sin(2 * np.pi * f * r * t + RNG.uniform(0, 6)) * np.exp(-t / d * (1 + f / 2000))
    y *= np.minimum(1, t / 0.003)
    return y * amp * 0.5


def musicbox(f, dur=2.2, amp=1.0):
    n = int(dur * SR); t = tt(n)
    y = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 3.98 * t) * np.exp(-t * 6)
         + 0.12 * np.sin(2 * np.pi * f * 9.1 * t) * np.exp(-t * 14)) * np.exp(-t * 1.7)
    return y * np.minimum(1, t / 0.002) * amp * 0.45


def pluck(f, dur=0.6, amp=1.0, bright=0.5):
    n = int(dur * SR)
    N = max(2, int(SR / f))
    buf = RNG.uniform(-1, 1, N)
    # soften the excitation
    for _ in range(int(3 * (1 - bright)) + 1):
        buf = 0.5 * (buf + np.roll(buf, 1))
    out = np.zeros(n)
    i = 0
    dec = 0.996
    while i < n:
        k = min(N, n - i)
        out[i:i + k] = buf[:k]
        buf = dec * 0.5 * (buf + np.roll(buf, 1))
        i += N
    return out * amp * 0.6 * env_adsr(n, 0.002, 0.05)


def harmonic_tone(f, dur, amp, a, r, nh=10, tilt=1.2, vib=0.0, vibf=5.0, cutoff=1800, detune=(0,), formants=None):
    n = int(dur * SR); t = tt(n)
    y = np.zeros(n)
    vibr = 1 + vib * np.sin(2 * np.pi * vibf * t) * np.minimum(1, t / 0.6)
    for dc in detune:
        ff = f * 2 ** (dc / 1200)
        ph = 2 * np.pi * np.cumsum(ff * vibr) / SR
        for h in range(1, nh + 1):
            fh = ff * h
            if fh > 9000:
                break
            g = 1 / h ** tilt * math.exp(-fh / cutoff)
            if formants:
                g = 1e-3 + sum(fa * math.exp(-((fh - fc) / bw) ** 2) for fc, bw, fa in formants)
                g /= h ** 0.3
            y += g * np.sin(h * ph + RNG.uniform(0, 6))
    y /= len(detune)
    return y * env_adsr(n, a, r) * amp


def xylo(f, amp=1.0):
    n = int(0.6 * SR); t = tt(n)
    y = (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.2) + 0.4 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.07)
         + 0.15 * np.sin(2 * np.pi * f * 9.0 * t) * np.exp(-t / 0.03))
    return y * np.minimum(1, t / 0.001) * amp * 0.5


def tuba(f, dur=0.32, amp=1.0):
    form = [(230, 150, 1.0), (520, 220, 0.5), (1100, 300, 0.12)]
    y = harmonic_tone(f, dur, amp * 0.55, 0.03, dur * 0.6, nh=12, formants=form, detune=(0,))
    return y


def pad(f, dur, amp=1.0):
    return harmonic_tone(f, dur, amp * 0.22, min(1.4, dur * 0.4), min(1.6, dur * 0.4), nh=10, tilt=1.0,
                         cutoff=900, detune=(-7, 0, 7), vib=0.002, vibf=0.3)


def choir(f, dur, amp=1.0):
    form = [(320, 120, 1.0), (800, 160, 0.35), (2400, 300, 0.05)]
    return harmonic_tone(f, dur, amp * 0.3, min(1.2, dur * 0.4), min(1.5, dur * 0.4), nh=16, vib=0.006,
                         vibf=4.8, detune=(-9, 0, 8), formants=form)


def cello(f, dur, amp=1.0, a=0.35):
    form = [(250, 200, 1.0), (600, 300, 0.6), (1300, 500, 0.25)]
    return harmonic_tone(f, dur, amp * 0.35, a, min(1.2, dur * 0.5), nh=18, vib=0.004, vibf=5.3,
                         detune=(-4, 4), formants=form)


def sub(f, dur, amp=1.0):
    n = int(dur * SR); t = tt(n)
    return np.sin(2 * np.pi * f * t) * env_adsr(n, 0.3, dur * 0.6) * amp * 0.5


def boom(amp=1.0):
    n = int(1.6 * SR); t = tt(n)
    f = 60 * np.exp(-t * 2) + 38
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    return y * amp * 0.6


# ---------------------------------------------------------------- noise helpers
def bandnoise(n, lo, hi, seed=0):
    r = np.random.default_rng(seed)
    X = np.fft.rfft(r.normal(0, 1, n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    mask = np.exp(-0.5 * ((np.log(fr + 1) - np.log(math.sqrt(lo * hi))) / (0.5 * math.log(hi / lo) + 1e-3)) ** 2)
    y = np.fft.irfft(X * mask, n)
    return y / (np.abs(y).max() + 1e-9)


def slow_lfo(n, rate, seed):
    r = np.random.default_rng(seed)
    k = max(4, int(n / SR * rate) + 4)
    pts = r.uniform(0, 1, k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)


# ---------------------------------------------------------------- moods
MOODS = {
    #           chords (midi), chord seconds
    'mystery': ([[50, 57, 64, 65], [46, 53, 57, 62], [43, 50, 52, 58], [45, 52, 55, 61]], 5.4),
    'comic':   ([[50, 57, 62, 65], [50, 57, 62, 65], [43, 55, 58, 62], [45, 57, 61, 64]], 1.25),
    'tender':  ([[41, 57, 60, 65], [40, 55, 60, 64], [38, 57, 62, 65], [46, 58, 62, 65]], 4.0),
    'sad':     ([[38, 57, 62, 65], [34, 58, 62, 65], [43, 55, 58, 62], [45, 57, 61, 64]], 5.0),
    'wonder':  ([[46, 58, 62, 65], [45, 57, 60, 65], [43, 58, 62, 67], [50, 57, 62, 66]], 4.0),
    'hope':    ([[50, 62, 66, 69], [49, 61, 64, 69], [47, 59, 62, 66], [43, 59, 62, 67]], 3.5),
}
MOOD_GAIN = {'mystery': 1.0, 'comic': 0.9, 'tender': 0.95, 'sad': 1.0, 'wonder': 1.05, 'hope': 1.1}


def add(buf, sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= buf.shape[1] or i + len(sig) <= 0:
        return
    if i < 0:
        sig = sig[-i:]; i = 0
    k = min(len(sig), buf.shape[1] - i)
    l = math.cos((pan + 1) * math.pi / 4)
    r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i:i + k] += sig[:k] * gain * l * 1.414
    buf[1, i:i + k] += sig[:k] * gain * r * 1.414


def render_mood(name, t0, t1, total_n):
    chords, cd = MOODS[name]
    buf = np.zeros((2, total_n))
    fade = 2.0
    s0, s1 = max(0, t0 - 0.2), t1 + fade
    t = s0
    ci = 0
    r = np.random.default_rng(hash(name) % 1000)
    scale_min = [62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 81]
    scale_maj = [62, 64, 66, 69, 71, 74, 76, 78, 81]
    while t < s1:
        ch = chords[ci % len(chords)]
        root = ch[0]
        d = cd + 0.6
        if name == 'mystery':
            # slow, eerie lullaby waltz: choir + pizzicato "oom" + celesta "pah pah"
            for m in ch[1:]:
                add(buf, choir(mtof(m), d + 1.0, 0.5), t, pan=r.uniform(-.5, .5))
            add(buf, cello(mtof(root - 12 if root > 45 else root), d + 1.0, 0.45, a=1.2), t)
            bar = cd / 3
            for b in range(3):
                t0 = t + b * bar
                add(buf, pluck(mtof(root - 12 if b % 2 == 0 else root - 5), 0.8, 0.55, 0.25), t0)
                for beat in (1, 2):
                    for m in (ch[2], ch[3]):
                        add(buf, celesta(mtof(m + 12), 0.9, 0.09), t0 + beat * bar / 3, pan=0.3)
                if r.random() < 0.75:
                    m = r.choice(scale_min) + 12
                    add(buf, musicbox(mtof(m), 2.5, 0.28), t0 + r.choice([0, bar / 3, 2 * bar / 3]), pan=r.uniform(-.6, .6))
        elif name == 'comic':
            # macabre oom-pah-pah waltz with xylophone
            bar = cd
            beat = bar / 3
            add(buf, tuba(mtof(root - 12), 0.34, 0.9), t)
            add(buf, pluck(mtof(root - 12), 0.4, 0.5, 0.3), t)
            for k in (1, 2):
                for m in ch[1:]:
                    add(buf, pluck(mtof(m), 0.22, 0.22, 0.85), t + k * beat, pan=0.35)
            hm = [62, 64, 65, 67, 69, 70, 73, 74, 76, 77]
            idx = getattr(render_mood, '_xi', 4)
            for k in range(3 if r.random() < 0.6 else 6):
                idx = int(np.clip(idx + r.choice([-2, -1, 1, 1, 2, 3, -3]), 0, len(hm) - 1))
                step = beat if k < 3 else beat / 2
                tk = t + (k * beat if r.random() < 0.6 else k * beat / 2)
                if r.random() < 0.85:
                    add(buf, xylo(mtof(hm[idx] + 12), 0.42), tk, pan=-0.3)
            render_mood._xi = idx
        elif name == 'tender':
            for m in ch[1:]:
                add(buf, pad(mtof(m), d + 0.8, 0.8), t, pan=r.uniform(-.4, .4))
            add(buf, pad(mtof(root), d + 0.8, 0.6), t)
            arp = ch[1:] + [ch[2] + 12]
            for k in range(8):
                add(buf, celesta(mtof(arp[k % 4] + 12), 1.6, 0.18), t + k * cd / 8, pan=math.sin(k) * 0.5)
        elif name == 'sad':
            add(buf, cello(mtof(root), d + 1.2, 0.9, a=0.9), t)
            add(buf, cello(mtof(ch[2]), d + 1.2, 0.35, a=1.4), t + 0.3, pan=0.3)
            for m in ch[1:]:
                add(buf, pad(mtof(m), d + 0.8, 0.45), t, pan=r.uniform(-.4, .4))
            for k in range(3):
                if r.random() < 0.6:
                    add(buf, celesta(mtof(r.choice(ch[1:]) + 12), 2.0, 0.14), t + k * cd / 3 + 0.4)
        elif name == 'wonder':
            for m in ch[1:]:
                add(buf, choir(mtof(m), d + 1.0, 0.45), t, pan=r.uniform(-.5, .5))
                add(buf, pad(mtof(m), d + 1.0, 0.4), t)
            add(buf, cello(mtof(root - 12 if root > 45 else root), d + 1, 0.5, a=1.0), t)
            arp = ch[1:] + [m + 12 for m in ch[1:]]
            for k in range(16):
                add(buf, celesta(mtof(arp[k % 6] + 12), 1.2, 0.12 + 0.05 * (k / 16)), t + k * cd / 16,
                    pan=math.sin(k * 0.8) * 0.7)
        elif name == 'hope':
            for m in ch[1:]:
                add(buf, pad(mtof(m), d + 0.8, 0.8), t, pan=r.uniform(-.4, .4))
            add(buf, cello(mtof(root - 12 if root > 47 else root), d + 0.8, 0.6, a=0.5), t)
            for k in range(4):
                add(buf, pluck(mtof(ch[1 + k % 3] + 12), 0.8, 0.3, 0.7), t + k * cd / 4, pan=0.3)
            mel = [r.choice(scale_maj) + 12 for _ in range(3)]
            for j, m in enumerate(mel):
                add(buf, celesta(mtof(m), 1.8, 0.22), t + j * cd / 3 + 0.1, pan=-0.2)
        t += cd
        ci += 1
    # window with fades
    n = total_n
    w = np.zeros(n)
    i0, i1 = int(t0 * SR), min(n, int(t1 * SR))
    w[i0:i1] = 1
    nf = int(fade * SR)
    if i1 < n:
        k = min(nf, n - i1)
        w[i1:i1 + k] = np.linspace(1, 0, k)
    ni = int(0.8 * SR)
    if i0 > 0:
        w[i0:i0 + ni] = np.linspace(0, 1, ni)
    return buf * w * MOOD_GAIN[name]


def mood_at(tl, t):
    m = 'mystery'
    for (mt, name) in sorted(tl.moods):
        if mt <= t:
            m = name
    return m


def chord_at(tl, t):
    ms = sorted(tl.moods)
    m, mt0 = 'mystery', 0
    for (mt, name) in ms:
        if mt <= t:
            m, mt0 = name, mt
    chords, cd = MOODS[m]
    return chords[int((t - max(0, mt0 - 0.2)) / cd) % len(chords)], m


def sting(buf, tl, t, kind, strength):
    ch, m = chord_at(tl, t)
    if kind == 'hi':
        notes = [n + 24 for n in ch[1:]]
        for j, nn in enumerate(notes):
            add(buf, celesta(mtof(nn), 2.2, 0.38 * strength), t - 0.02 + j * 0.075, pan=(j - 1) * 0.4)
        add(buf, musicbox(mtof(notes[-1] + 12), 2.0, 0.18 * strength), t + 0.25, pan=0.5)
        add(buf, pad(mtof(notes[0] - 12), 2.5, 0.35 * strength), t)
    else:
        root = ch[0]
        while root > 45:
            root -= 12
        add(buf, cello(mtof(root), 3.2, 1.1 * strength, a=0.18), t - 0.1)
        add(buf, sub(mtof(root - 12), 3.0, 0.8 * strength), t - 0.05)
        add(buf, boom(0.5 * strength), t - 0.02)


# ---------------------------------------------------------------- sfx
def sfx_sound(name):
    if name == 'whoosh':
        n = int(1.8 * SR)
        y = np.zeros(n)
        seg = int(0.12 * SR)
        hop = seg // 2
        win = np.hanning(seg)
        for k, i in enumerate(range(0, n - seg, hop)):
            u = i / n
            fc = 150 * (25 ** u)
            y[i:i + seg] += bandnoise(seg, fc * 0.6, fc * 1.6, seed=k) * win
        e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        return y * e * 0.5
    if name == 'buzzin':
        n = int(1.2 * SR); t = tt(n)
        f = 260 - 60 * t
        ph = 2 * np.pi * np.cumsum(f) / SR
        y = sum(np.sin(h * ph) / h for h in range(1, 12))
        return y * np.exp(-((t - 0.45) / 0.35) ** 2) * 0.25
    if name == 'owl':
        out = np.zeros(int(1.6 * SR))
        for k, (f0, st, du) in enumerate(((380, 0.0, 0.32), (330, 0.45, 0.6))):
            n = int(du * SR); t = tt(n)
            f = f0 * (1 - 0.04 * t / du) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t))
            y = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.15 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            y += 0.08 * bandnoise(n, 300, 900, k)
            y *= np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
            i = int(st * SR)
            out[i:i + n] += y
        return out * 0.25
    if name == 'chime':
        y = np.zeros(int(3 * SR))
        for j, m in enumerate((86, 90, 93, 98)):
            s = celesta(mtof(m), 2.4, 0.3)
            i = int(j * 0.09 * SR)
            y[i:i + len(s)] += s[:len(y) - i]
        return y
    if name == 'heartbeat':
        y = np.zeros(int(2.4 * SR))
        for st in (0, 0.28, 1.1, 1.38):
            n = int(0.3 * SR); t = tt(n)
            f = 70 * np.exp(-t * 8) + 42
            b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 18)
            i = int(st * SR)
            y[i:i + n] += b * (0.8 if st in (0, 1.1) else 0.55)
        return y * 0.7
    if name == 'erase':
        n = int(1.5 * SR); t = tt(n)
        y = bandnoise(n, 900, 3500, 3)
        am = np.clip(np.sin(2 * np.pi * 3.2 * t), 0, 1) ** 0.6
        return y * am * np.exp(-t * 0.8) * 0.18
    if name == 'sigh':
        n = int(1.3 * SR)
        y = bandnoise(n, 400, 1600, 5)
        e = np.sin(np.pi * np.linspace(0, 1, n) ** 0.6) ** 2
        return y * e * 0.12
    if name == 'shimmer':
        y = np.zeros(int(3 * SR))
        for j, m in enumerate((81, 86, 88, 93, 95, 100)):
            s = celesta(mtof(m), 2.0, 0.15)
            i = int(j * 0.06 * SR)
            y[i:i + len(s)] += s[:len(y) - i]
        return y
    if name == 'paper':
        n = int(1.2 * SR); t = tt(n)
        y = bandnoise(n, 1500, 7000, 8) * (RNG.random(n) < 0.3)
        y = np.convolve(y, np.ones(20) / 20, 'same')
        return y * np.sin(np.pi * t / 1.2) * 0.6
    if name == 'creak':
        n = int(1.0 * SR); t = tt(n)
        rate = 45 - 25 * t
        ph = np.cumsum(rate) / SR
        clicks = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
        y = np.convolve(clicks, np.exp(-np.arange(300) / 40) * np.sin(np.arange(300) * 2 * np.pi * 700 / SR), 'same')
        return y * np.sin(np.pi * t) * 0.25
    if name == 'wind_gust':
        n = int(4 * SR)
        y = bandnoise(n, 200, 1200, 21)
        return y * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 0.35
    return np.zeros(10)


def reverb(x, rt=2.2, seed=0, pre=0.02):
    n = len(x)
    L = int(rt * SR)
    r = np.random.default_rng(seed)
    ir = r.normal(0, 1, (2, L)) * np.exp(-np.arange(L) / SR * 6.9 / rt)
    # darken tail
    for c in range(2):
        ir[c] = np.convolve(ir[c], np.ones(6) / 6, 'same')
    ir[:, :int(pre * SR)] = 0
    ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
    N = 1 << int(math.ceil(math.log2(n + L)))
    out = np.zeros((2, n))
    X = np.fft.rfft(x, N)
    for c in range(2):
        out[c] = np.fft.irfft(X * np.fft.rfft(ir[c], N), N)[:n]
    return out


def main():
    tl = load_tl()
    states = pickle.load(open(os.path.join(HERE, 'states.pkl'), 'rb'))
    dur = tl.end + 0.5
    n = int(dur * SR)
    nfr = len(states)

    # ---- dialogue
    vox = np.zeros(n)
    vox_g = np.zeros(n)  # ghostly send
    for ln in tl.lines:
        a = np.load(os.path.join(voices.CACHE, voices.h(ln['key'] + str(ln['whisper'])) + '.npy')).astype(float)
        i = int(ln['start'] * SR)
        k = min(len(a), n - i)
        vox[i:i + k] += a[:k] * ln['vol']
        if ln['sp'] == 'GOSTE':
            vox_g[i:i + k] += a[:k]
    vox_st = np.stack([vox, vox]) + reverb(vox, 0.9, 1) * 0.09 + reverb(vox_g, 2.0, 2) * 0.22

    # ---- music
    music = np.zeros((2, n))
    ms = sorted(tl.moods)
    for i, (mt, name) in enumerate(ms):
        t1 = ms[i + 1][0] if i + 1 < len(ms) else dur
        if t1 - mt < 0.5:
            continue
        music += render_mood(name, mt, t1, n)
    stg = np.zeros((2, n))
    for (t, kind, s) in sorted(tl.stings):
        sting(stg, tl, t, kind, s)
    music = music * 0.75 + reverb(music[0] * 0.5 + music[1] * 0.5, 2.8, 3, 0.03) * 0.45
    stg = stg * 0.8 + reverb(stg[0] * 0.5 + stg[1] * 0.5, 3.2, 6, 0.03) * 0.55

    # ---- ambience driven by frame state
    def per_frame(fn):
        v = np.array([fn(s) for s in states] + [0.0])
        return np.interp(np.arange(n) / SR * FPS, np.arange(len(v)), v)

    garden = per_frame(lambda s: 1.0 if (s['scene'] == 'garden') else 0.0) * \
        per_frame(lambda s: 1 - s['P']['PHOTO']['alpha'])
    dawn = per_frame(lambda s: s['P']['WORLD']['dawn'])
    amb = np.zeros((2, n))
    wind = np.stack([bandnoise(n, 180, 900, 31), bandnoise(n, 180, 900, 32)])
    amb += wind * (0.05 + 0.07 * slow_lfo(n, 0.15, 5)) * (0.4 + 0.6 * garden)
    # crickets at night, birds at dawn
    cr = np.zeros((2, n))
    for c, pan in ((0, -0.7), (1, 0.6)):
        t = 1.0 + c * 0.5
        while t < dur - 1:
            for k in range(3):
                m = int(0.03 * SR)
                s = np.sin(2 * np.pi * (4500 + c * 300) * tt(m)) * np.hanning(m)
                add(cr, s, t + k * 0.06, pan, 0.028)
            t += RNG.uniform(0.7, 1.6)
    amb += cr * garden * (1 - dawn)
    for k in range(10):
        t = 172 + RNG.uniform(0, 8)
        m = int(0.12 * SR)
        f = np.linspace(3200, 4200, m) * (1 + 0.05 * np.sin(np.linspace(0, 30, m)))
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.hanning(m)
        add(amb, s, t, RNG.uniform(-.7, .7), 0.05)
    # bee buzz follows the bee on screen
    def bee_amp(s):
        if s['scene'] != 'garden':
            return 0.0
        P = s['P']['BEE']
        cx, cy, z = s['cam']
        sx = (P['x'] - cx) * z + 540
        sy = (P['y'] - cy) * z + 960
        on = 1.0 if (-150 < sx < 1230 and -150 < sy < 2070) else 0.25
        return on * min(1.0, 0.35 + 0.25 * z) * (1 - s['P']['PHOTO']['alpha'])
    ba = per_frame(bee_amp)
    t = tt(n)
    f = 225 + 12 * np.sin(2 * np.pi * 0.7 * t) + 6 * np.sin(2 * np.pi * 3.1 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    buzz = sum(np.sin(h * ph) / h ** 1.1 for h in range(1, 10)) * (0.75 + 0.25 * np.sin(2 * np.pi * 31 * t))
    amb += np.stack([buzz, buzz]) * ba * 0.022
    # rain from Clawdia
    ra = per_frame(lambda s: s['P']['CLAWDIA']['rain'] * (1 - s['P']['PHOTO']['alpha']))
    rain = np.stack([bandnoise(n, 2500, 9000, 41), bandnoise(n, 2500, 9000, 42)])
    amb += rain * ra * 0.2
    # one-shot sfx
    sfx = np.zeros((2, n))
    for (t0, name, kw) in tl.events:
        add(sfx, sfx_sound(name), t0, kw.get('pan', 0.0), kw.get('gain', 1.0))
    sfx = sfx + reverb(sfx[0] + sfx[1], 1.6, 4) * 0.25

    # ---- ducking
    e = np.abs(vox)
    win = int(0.05 * SR)
    e = np.convolve(e, np.ones(win) / win, 'same')
    # slow release
    dec = np.exp(-1 / (0.35 * SR))
    from itertools import accumulate
    step = 64
    ed = e[::step]
    ed = np.array(list(accumulate(ed, lambda p, x: max(x, p * dec ** step))))
    ed = np.interp(np.arange(n), np.arange(0, n, step)[:len(ed)], ed)
    duck = 1 - 0.5 * np.clip(ed / 0.12, 0, 1)

    mixd = vox_st * 1.0 + music * 0.33 * duck + stg * 0.36 * (0.55 + 0.45 * duck) + amb * 1.0 * (0.6 + 0.4 * duck) + sfx * 0.8
    sp = np.abs(vox) > 0.02
    spm = np.convolve(sp.astype(float), np.ones(4410) / 4410, 'same') > 0.3
    def db(x, m): return 20 * np.log10(np.sqrt(np.mean(x[:, m] ** 2)) + 1e-9)
    bed = music * 0.33 * duck + amb * (0.6 + 0.4 * duck)
    print('voice during speech dB', db(vox_st, spm), ' bed during speech', db(bed, spm),
          ' bed in gaps', db(bed, ~spm), ' sfx', db(sfx * 0.8, np.ones(n, bool)))
    for nm, x in (('stings', stg * 0.36 * (0.55 + 0.45 * duck)), ('music', music * 0.33 * duck), ('amb', amb), ('buzz', np.stack([buzz, buzz]) * ba * 0.022), ('rain', rain * ra * 0.07)):
        print(nm, db(x, spm), db(x, ~spm))
    # gentle bus limiter
    pk = np.abs(mixd).max()
    mixd = np.tanh(mixd / pk * 1.4) / np.tanh(1.4) * 0.95
    out = (mixd.T * 32767).astype(np.int16)
    import wave
    with wave.open(os.path.join(HERE, 'mix.wav'), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(out.tobytes())
    print('audio done', dur)


if __name__ == '__main__':
    main()
