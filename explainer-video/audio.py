"""Procedural background music, sound effects and the final mix (all synthesized)."""
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, d, s, r, sr=SR):
    a, d, r = int(a * sr), int(d * sr), int(r * sr)
    sus = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, max(a, 1)), np.linspace(1, s, max(d, 1)),
                        np.full(sus, s), np.linspace(s, 0, max(r, 1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n - len(e)))


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


# ------------------------------------------------------------------ instruments
def epiano(freq, dur, vel=0.5):
    """Soft electric-piano-ish tone: a few decaying partials plus a tine 'ping'."""
    n = int((dur + 1.2) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h, amp, dec in [(1, 1.0, 1.6), (2, 0.35, 0.9), (3, 0.12, 0.5), (4, 0.05, 0.3)]:
        out += amp * np.sin(2 * np.pi * freq * h * t + 0.3 * h) * np.exp(-t / (dec * (1 + 200 / freq)))
    out += 0.08 * np.sin(2 * np.pi * freq * 7.1 * t) * np.exp(-t / 0.05)
    out *= 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)  # gentle tremolo
    rel = np.ones(n)
    k = int(dur * SR)
    rel[k:] = np.exp(-(np.arange(n - k)) / (0.25 * SR))
    a = np.minimum(1, t / 0.004)
    return out * rel * a * vel


def pad(freq, dur, vel=0.3):
    n = int((dur + 1.0) * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.12, 0.0, 0.12):
        f = freq * 2 ** (det / 12)
        ph = rng.uniform(0, 2 * np.pi)
        out += np.sin(2 * np.pi * f * t + ph) + 0.25 * np.sin(4 * np.pi * f * t + ph)
    out = lp(out, 1800)
    return out * env_adsr(n, 0.8, 0.5, 0.8, 1.0) * vel / 3


def bass(freq, dur, vel=0.5):
    n = int((dur + 0.3) * SR)
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(4 * np.pi * freq * t)
    return out * env_adsr(n, 0.01, 0.2, 0.7, 0.25) * vel


def pluck(freq, dur=0.5, vel=0.3):
    n = int((dur + 0.6) * SR)
    t = np.arange(n) / SR
    out = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(4 * np.pi * freq * t + 1)
           + 0.2 * np.sin(6 * np.pi * freq * t)) * np.exp(-t / 0.28)
    return out * np.minimum(1, t / 0.002) * vel


def bell(freq, dur=1.2, vel=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = (np.sin(2 * np.pi * freq * t) + 0.5 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t / 0.3)
           + 0.25 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t / 0.12))
    return out * np.exp(-t / (dur * 0.35)) * np.minimum(1, t / 0.002) * vel


def kick(vel=0.6):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 50 + 70 * np.exp(-t / 0.04)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.12) * vel


def hat(vel=0.15, dec=0.03):
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7000) * np.exp(-t / dec) * vel


def shaker(vel=0.08):
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    e = np.minimum(1, t / 0.03) * np.exp(-np.maximum(0, t - 0.03) / 0.03)
    return bp(rng.standard_normal(n), 4000, 10000) * e * vel


def snap(vel=0.2):
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    return (bp(rng.standard_normal(n), 1200, 5000) * np.exp(-t / 0.05)
            + 0.4 * np.sin(2 * np.pi * 220 * t) * np.exp(-t / 0.03)) * vel


def place(buf, x, at):
    i = int(at * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x, i = x[-i:], 0
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m]


def reverb(x, secs=2.2, wet=0.25, seed=3):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (secs / 5))
    ir = lp(ir, 5000)
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    y = fftconvolve(x, ir)[:len(x)]
    return x * (1 - wet) + y * wet * 1.6


# ------------------------------------------------------------------ music
# chords as MIDI note lists (root in bass register given separately)
MOODS = {
    "playful": dict(bpm=100, prog=[(53, [65, 69, 72, 76]), (52, [64, 67, 71, 74]),
                                   (50, [62, 65, 69, 72]), (55, [62, 65, 67, 71])],
                    style="bouncy"),
    "tense": dict(bpm=78, prog=[(45, [57, 60, 64, 67]), (41, [57, 60, 65, 69]),
                                (50, [57, 62, 65, 69]), (40, [56, 59, 64, 68])],
                  style="tense"),
    "turn": dict(bpm=84, prog=[(41, [60, 65, 69, 72]), (43, [62, 67, 71, 74]),
                               (45, [60, 64, 69, 72]), (43, [62, 65, 67, 71])],
                 style="build"),
    "hopeful": dict(bpm=96, prog=[(48, [64, 67, 72, 76]), (55, [62, 67, 71, 74]),
                                  (45, [64, 67, 69, 72]), (41, [65, 69, 72, 77])],
                    style="hopeful"),
    "warm": dict(bpm=80, prog=[(41, [64, 69, 72, 76]), (43, [62, 67, 71, 74]),
                               (40, [64, 67, 71, 76]), (45, [64, 67, 72, 76]),
                               (41, [65, 69, 72, 77]), (43, [62, 67, 71, 74]),
                               (48, [64, 67, 72, 79]), (48, [64, 67, 72, 76])],
                 style="warm"),
}


def music_section(mood, dur, seed=0):
    m = MOODS[mood]
    beat = 60 / m["bpm"]
    bar = beat * 4
    n = int((dur + 3) * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    r = np.random.default_rng(seed)
    nbars = int(np.ceil(dur / bar)) + 1
    st = m["style"]
    for b in range(nbars):
        root, chord = m["prog"][b % len(m["prog"])]
        t0 = b * bar
        # pad bed
        for i, note in enumerate(chord):
            p = pad(mtof(note), bar, 0.10 if st != "tense" else 0.12)
            place(L if i % 2 else R, p * 0.9, t0)
            place(R if i % 2 else L, p * 0.6, t0)
        # bass
        bvel = 0.32
        if st in ("bouncy", "hopeful"):
            for k, off in enumerate([0, 1.5, 2, 3.5] if st == "bouncy" else [0, 2, 2.5]):
                bb = bass(mtof(root), beat * 0.9, bvel)
                place(L, bb, t0 + off * beat)
                place(R, bb, t0 + off * beat)
        elif st == "tense":
            bb = bass(mtof(root), bar * 0.95, bvel * 0.9)
            place(L, bb, t0)
            place(R, bb, t0)
        else:
            for off in (0, 2):
                bb = bass(mtof(root), beat * 1.9, bvel)
                place(L, bb, t0 + off * beat)
                place(R, bb, t0 + off * beat)
        # keys
        if st == "bouncy":
            for k in range(8):
                if k in (0, 3, 4, 6):
                    for note in chord[:3]:
                        e = epiano(mtof(note), beat * 0.4, 0.07)
                        place(L, e, t0 + k * beat / 2)
                        place(R, e * 0.8, t0 + k * beat / 2 + 0.006)
            arp = chord + [chord[1] + 12]
            for k in range(8):
                if r.random() < 0.6:
                    p = pluck(mtof(arp[(k * 3 + b) % len(arp)] + 12), 0.3, 0.035)
                    place(L if k % 2 else R, p, t0 + k * beat / 2)
        elif st == "tense":
            for k, note in enumerate([chord[0], chord[2], chord[1], chord[3]]):
                e = epiano(mtof(note), beat * 1.5, 0.06)
                place(L if k % 2 else R, e, t0 + k * beat)
            if b % 2 == 1:
                place(L, bell(mtof(chord[-1] + 12), 2.0, 0.025), t0 + 3.5 * beat)
        elif st == "build":
            for k in range(8):
                note = chord[(k * 2 + b) % 4] + 12
                p = pluck(mtof(note), 0.35, 0.04 + 0.002 * b)
                place(L if k % 2 else R, p, t0 + k * beat / 2)
            for note in chord:
                e = epiano(mtof(note), bar * 0.9, 0.04)
                place(L, e, t0)
                place(R, e, t0 + 0.01)
        elif st == "hopeful":
            for k in range(4):
                for note in chord[:3]:
                    e = epiano(mtof(note), beat * 0.7, 0.06)
                    place(L, e, t0 + k * beat + (beat / 2 if k == 3 else 0))
                    place(R, e * 0.85, t0 + k * beat + 0.007 + (beat / 2 if k == 3 else 0))
            arp = [chord[0], chord[1], chord[2], chord[3], chord[2] + 12, chord[3], chord[2], chord[1]]
            for k in range(8):
                p = pluck(mtof(arp[k] + 12), 0.3, 0.03)
                place(L if k % 2 else R, p, t0 + k * beat / 2)
        else:  # warm
            for k, note in enumerate(chord + [chord[2] + 12]):
                e = epiano(mtof(note), bar - k * beat * 0.5, 0.06)
                place(L if k % 2 else R, e, t0 + k * beat * 0.5)
        # drums
        if st in ("bouncy", "hopeful"):
            for k in range(4):
                if k in (0, 2):
                    place(L, kick(0.28), t0 + k * beat)
                    place(R, kick(0.28), t0 + k * beat)
                if k in (1, 3):
                    s = snap(0.07)
                    place(L, s, t0 + k * beat)
                    place(R, s, t0 + k * beat)
            for k in range(8):
                h = shaker(0.05 if k % 2 else 0.03)
                place(R if k % 2 else L, h, t0 + k * beat / 2)
        elif st == "build":
            for k in range(4):
                place(L, kick(0.18), t0 + k * beat)
                place(R, kick(0.18), t0 + k * beat)
                place(L, hat(0.035), t0 + k * beat + beat / 2)
        elif st == "tense":
            place(L, kick(0.16), t0)
            place(R, kick(0.16), t0)
            place(L, kick(0.10), t0 + 2.5 * beat)
            place(R, kick(0.10), t0 + 2.5 * beat)
        elif st == "warm" and b >= 2:
            for k in range(8):
                place(R if k % 2 else L, shaker(0.025), t0 + k * beat / 2)
    L, R = reverb(L, wet=0.28, seed=1), reverb(R, wet=0.28, seed=2)
    out = np.stack([L, R], 1)[:int(dur * SR)]
    return out


def build_music(scenes, total):
    """One continuous bed: consecutive scenes with the same mood share a section."""
    sections = []
    for sc in scenes:
        if sections and sections[-1][0] == sc["music"]:
            sections[-1][2] = sc["end"]
        else:
            sections.append([sc["music"], sc["start"], sc["end"]])
    sections[-1][2] = total
    out = np.zeros((int(total * SR) + SR, 2))
    xf = 1.6
    for i, (mood, s, e) in enumerate(sections):
        s0 = max(0, s - (xf / 2 if i else 0))
        e0 = min(total, e + (xf / 2 if i < len(sections) - 1 else 0))
        seg = music_section(mood, e0 - s0, seed=i)
        n = len(seg)
        g = np.ones(n)
        k = int(xf * SR)
        if i:
            g[:k] = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
        if i < len(sections) - 1:
            g[-k:] = np.cos(np.linspace(0, np.pi / 2, k)) ** 2
        else:
            fo = int(3.0 * SR)
            g[-fo:] *= np.linspace(1, 0, fo) ** 1.5
        i0 = int(s0 * SR)
        out[i0:i0 + n] += seg * g[:, None]
    return out[:int(total * SR)]


# ------------------------------------------------------------------ sound effects
def sfx(name):
    t = lambda d: np.arange(int(d * SR)) / SR
    if name == "doorbell":
        a = bell(mtof(76), 1.2, 0.5)
        b = bell(mtof(72), 1.6, 0.5)
        out = np.zeros(int(2.2 * SR))
        place(out, a, 0)
        place(out, b, 0.45)
        return out * 0.8
    if name == "thump":
        x = t(0.4)
        f = 45 + 60 * np.exp(-x / 0.05)
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.1)
        rustle = bp(rng.standard_normal(len(x)), 800, 4000) * np.exp(-x / 0.08) * 0.3
        return (body + rustle) * 0.7
    if name == "footsteps":
        out = np.zeros(int(1.6 * SR))
        for k in range(9):
            x = t(0.12)
            st = (np.sin(2 * np.pi * 90 * x) * 0.6 + bp(rng.standard_normal(len(x)), 300, 2500) * 0.5)
            place(out, st * np.exp(-x / 0.03) * (0.5 - k * 0.045), k * 0.16)
        return out
    if name in ("door_open", "door_close"):
        x = t(0.5)
        if name == "door_close":
            body = np.sin(2 * np.pi * np.cumsum(70 + 50 * np.exp(-x / 0.03)) / SR) * np.exp(-x / 0.09)
            click = bp(rng.standard_normal(len(x)), 1500, 6000) * np.exp(-x / 0.01) * 0.6
            return (body + click) * 0.55
        click = bp(rng.standard_normal(len(x)), 2000, 7000) * np.exp(-x / 0.008) * 0.5
        creak = np.sin(2 * np.pi * (300 + 120 * x) * x) * np.exp(-x / 0.25) * 0.05
        return click + creak
    if name == "ping":
        x = t(0.5)
        return (np.sin(2 * np.pi * 1320 * x) * np.exp(-x / 0.08)
                + 0.5 * np.sin(2 * np.pi * 1980 * x) * np.exp(-x / 0.05)) * 0.22
    if name == "block":
        x = t(0.5)
        low = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-x / 0.2) + 60) / SR) * np.exp(-x / 0.12)
        click = hp(rng.standard_normal(len(x)), 3000) * np.exp(-x / 0.006) * 0.4
        return (low + click) * 0.5
    if name == "denied":
        x = t(0.42)
        s = np.sign(np.sin(2 * np.pi * 150 * x)) * 0.3 + np.sin(2 * np.pi * 150 * x) * 0.5
        e = np.concatenate([np.ones(int(0.15 * SR)), np.zeros(int(0.06 * SR)), np.ones(int(0.21 * SR))])[:len(x)]
        return lp(s * e, 1200) * 0.18
    if name == "whoosh":
        x = t(0.7)
        nz = rng.standard_normal(len(x))
        e = np.sin(np.pi * x / 0.7) ** 2
        out = np.zeros(len(x))
        for i in range(0, len(x), 1024):
            fc = 400 + 3000 * np.sin(np.pi * (i / len(x)))
            out[i:i + 1024] = bp(nz[i:i + 1024 + 2048], fc * 0.6, fc * 1.4)[:len(out[i:i + 1024])]
        return lp(out * e, 6000) * 0.35
    if name == "pop":
        x = t(0.18)
        f = 900 * np.exp(-x / 0.03) + 300
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.04) * 0.25
    if name == "slam":
        x = t(1.2)
        boom = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-x / 0.06)) / SR) * np.exp(-x / 0.3)
        hit = bp(rng.standard_normal(len(x)), 200, 3000) * np.exp(-x / 0.05) * 0.5
        shim = sum(np.sin(2 * np.pi * f * x) for f in (523, 659, 784)) * np.exp(-x / 0.5) * 0.08
        return (boom * 0.7 + hit + shim) * 0.6
    if name == "lock":
        x = t(0.3)
        c1 = hp(rng.standard_normal(len(x)), 2500) * np.exp(-x / 0.01)
        out = c1 * 0.4
        place(out, hp(rng.standard_normal(int(0.1 * SR)), 2000) * np.exp(-t(0.1) / 0.006) * 0.5, 0.09)
        place(out, np.sin(2 * np.pi * 1800 * t(0.1)) * np.exp(-t(0.1) / 0.02) * 0.2, 0.09)
        return out
    if name == "heartbeat":
        out = np.zeros(int(3.0 * SR))
        for k in range(3):
            for off, v in ((0, 0.6), (0.22, 0.4)):
                x = t(0.25)
                b = np.sin(2 * np.pi * np.cumsum(40 + 30 * np.exp(-x / 0.03)) / SR) * np.exp(-x / 0.08)
                place(out, lp(b, 200) * v, k * 0.9 + off)
        return out * 0.9
    if name == "chime":
        out = np.zeros(int(2.2 * SR))
        for k, nnote in enumerate((72, 76, 79, 84)):
            place(out, bell(mtof(nnote), 1.6, 0.13), k * 0.07)
        return out
    if name == "sparkle":
        out = np.zeros(int(2.2 * SR))
        for k in range(10):
            nnote = [84, 88, 91, 96, 91, 88, 93, 96, 100, 103][k]
            place(out, bell(mtof(nnote), 0.8, 0.06), k * 0.05)
        return out
    if name == "shield":
        x = t(1.2)
        sw = np.sin(2 * np.pi * np.cumsum(300 + 500 * x) / SR) * np.exp(-x / 0.4) * 0.12
        return sw + np.pad(bell(mtof(79), 1.0, 0.12), (0, len(x)))[:len(x)]
    if name == "scribble":
        out = np.zeros(int(2.4 * SR))
        for k in range(10):
            d = rng.uniform(0.08, 0.18)
            x = t(d)
            s = bp(rng.standard_normal(len(x)), 2000, 6000) * np.sin(np.pi * x / d) * 0.08
            place(out, s, k * 0.22 + rng.uniform(0, 0.05))
        return out
    if name == "typing":
        out = np.zeros(int(2.5 * SR))
        tt = 0
        while tt < 2.3:
            x = t(0.04)
            place(out, hp(rng.standard_normal(len(x)), 2500) * np.exp(-x / 0.006) * 0.12, tt)
            tt += rng.uniform(0.07, 0.16)
        return out
    if name == "send":
        x = t(0.5)
        f = 500 + 1200 * x / 0.5
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * x / 0.5) * 0.15
    if name == "tick":
        x = t(0.3)
        return (np.sin(2 * np.pi * 1046 * x) * np.exp(-x / 0.06)
                + 0.4 * np.sin(2 * np.pi * 1568 * x) * np.exp(-x / 0.04)) * 0.18
    if name == "shutter":
        x = t(0.25)
        out = hp(rng.standard_normal(len(x)), 1500) * np.exp(-x / 0.012) * 0.35
        place(out, hp(rng.standard_normal(int(0.05 * SR)), 1500) * np.exp(-t(0.05) / 0.01) * 0.25, 0.09)
        return out
    raise KeyError(name)


def mix(voice, scenes, sfx_events, total):
    n = int(total * SR)
    vtrack = np.zeros(n)
    vtrack[:min(n, len(voice))] = voice[:n]
    # gentle voice polish: high-pass rumble, slight presence
    vtrack = hp(vtrack, 70)
    peak = np.percentile(np.abs(vtrack[np.abs(vtrack) > 1e-4]), 99.5)
    vtrack *= 0.55 / max(peak, 1e-6)
    music = build_music(scenes, total)[:n]
    music /= max(np.abs(music).max(), 1e-6)
    # duck music under the voice
    env = np.abs(vtrack)
    win = int(0.05 * SR)
    env = np.convolve(env, np.ones(win) / win, "same")
    active = np.clip(env / 0.03, 0, 1)
    sm = np.zeros_like(active)
    a_up, a_dn = 1 - np.exp(-1 / (0.05 * SR)), 1 - np.exp(-1 / (0.6 * SR))
    # fast vectorized-ish smoothing via block processing
    prev = 0.0
    blk = 480
    for i in range(0, n, blk):
        tgt = active[i:i + blk].max()
        k = a_up if tgt > prev else a_dn
        prev = prev + (tgt - prev) * (1 - (1 - k) ** blk)
        sm[i:i + blk] = prev
    gain = 0.30 * (1 - 0.5 * sm)
    music = music * gain[:, None]
    fx = np.zeros(n)
    for name, at in sfx_events:
        x = sfx(name)
        place(fx, x * (0.45 / max(np.abs(x).max(), 0.45)), at)  # cap transient peaks
    fx *= 0.8
    st = np.stack([vtrack + fx, vtrack + fx], 1) + music
    st = np.tanh(st * 1.05) * 0.97  # gentle soft limiter, never clips
    return st.astype(np.float32)
