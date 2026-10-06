"""Procedural sound effects and music."""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 24000
_rng = np.random.default_rng(4)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.005, r=None):
    e = np.ones(n)
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    if r:
        nr = min(n, int(r * SR))
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, f):
    return sosfilt(butter(2, f, "low", fs=SR, output="sos"), x)


def hp(x, f):
    return sosfilt(butter(2, f, "high", fs=SR, output="sos"), x)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "band", fs=SR, output="sos"), x)


def noise(d):
    return _rng.uniform(-1, 1, int(d * SR))


def glide(f0, f1, d, curve=1.0):
    t = t_(d)
    u = (t / d) ** curve
    f = f0 + (f1 - f0) * u
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def norm(x, g=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * g


# ------------------------------------------------------------- effects
def snare_hit(d=0.12):
    n = noise(d) * np.exp(-t_(d) * 28)
    return bp(n, 900, 6000) * 0.8 + np.sin(2 * np.pi * 190 * t_(d)) * np.exp(-t_(d) * 30) * 0.4


def sfx_drumroll(d=2.6):
    out = np.zeros(int((d + 1.6) * SR))
    k = 0.0
    while k < d:
        amp = 0.25 + 0.75 * (k / d) ** 1.5
        h = snare_hit()
        i = int(k * SR)
        out[i:i + len(h)] += h * amp * (0.8 + 0.2 * _rng.random())
        k += 1 / 26
    c = sfx_cymbal()
    i = int(d * SR)
    out[i:i + len(c)] += c * 0.9
    return norm(out, 0.8)


def sfx_cymbal(d=1.5):
    n = hp(noise(d), 5000) * np.exp(-t_(d) * 3.2)
    return norm(n, 0.7)


def sfx_pop():
    d = 0.14
    x = glide(380, 1300, d, 0.6) * np.exp(-t_(d) * 22)
    return norm(x, 0.7)


def sfx_tink():
    d = 0.5
    t = t_(d)
    x = (np.sin(2 * np.pi * 2600 * t) + 0.5 * np.sin(2 * np.pi * 3900 * t)) * np.exp(-t * 10)
    return norm(x, 0.45)


def sfx_ding(f=1760):
    d = 1.2
    t = t_(d)
    x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)
         + 0.2 * np.sin(2 * np.pi * f * 3.02 * t)) * np.exp(-t * 4)
    return norm(x, 0.45)


def sfx_bling():
    a = sfx_ding(1568)
    b = sfx_ding(2349)
    out = np.zeros(len(a) + int(0.09 * SR))
    out[:len(a)] += a
    out[int(0.09 * SR):] += b
    return norm(out, 0.5)


def sfx_sparkle(d=1.4, dens=40):
    out = np.zeros(int((d + 0.4) * SR))
    for _ in range(int(dens * d)):
        f = _rng.uniform(2500, 6000)
        dd = 0.18
        t = t_(dd)
        s = np.sin(2 * np.pi * f * t) * np.exp(-t * 26)
        i = int(_rng.uniform(0, d) * SR)
        out[i:i + len(s)] += s * _rng.uniform(0.2, 0.6)
    return norm(out, 0.4)


def sfx_zap():
    d = 0.7
    x = glide(1800, 160, d, 0.5) * np.exp(-t_(d) * 3)
    x += lp(noise(d), 3000) * np.exp(-t_(d) * 5) * 0.4
    return norm(x, 0.6)


def sfx_lazy_zap():
    d = 1.4
    t = t_(d)
    f = 700 + 120 * np.sin(2 * np.pi * 3 * t) - 300 * t / d
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5)
    return norm(x, 0.45)


def sfx_whoosh(d=0.6, f0=300, f1=3000):
    n = noise(d)
    out = np.zeros_like(n)
    seg = 8
    L = len(n) // seg
    for i in range(seg):
        f = f0 + (f1 - f0) * i / seg
        out[i * L:(i + 1) * L] = bp(n[i * L:(i + 1) * L], f * 0.6, min(f * 1.4, 11000))
    out *= np.sin(np.linspace(0, np.pi, len(out)))
    return norm(out, 0.5)


def sfx_boom():
    d = 1.4
    t = t_(d)
    x = np.sin(2 * np.pi * (55 + 40 * np.exp(-t * 8)) * t) * np.exp(-t * 3.5)
    x += lp(noise(d), 800) * np.exp(-t * 4) * 0.8
    return norm(x, 0.85)


def sfx_splat():
    d = 0.5
    t = t_(d)
    x = lp(noise(d), 1400) * np.exp(-t * 12) + glide(500, 90, d) * np.exp(-t * 10) * 0.6
    return norm(x, 0.8)


def sfx_glitter_hit():
    a = sfx_splat()
    b = sfx_sparkle(2.4, 60)
    out = np.zeros(len(b) + 100)
    out[:len(a)] += a
    out[:len(b)] += b * 0.9
    return norm(out, 0.85)


def sfx_thud():
    d = 0.25
    t = t_(d)
    x = np.sin(2 * np.pi * 75 * t) * np.exp(-t * 18) + lp(noise(d), 400) * np.exp(-t * 25) * 0.5
    return norm(x, 0.7)


def sfx_stomp():
    d = 0.3
    t = t_(d)
    x = np.sin(2 * np.pi * (90 - 40 * t / d) * t) * np.exp(-t * 14) + lp(noise(d), 600) * np.exp(-t * 20) * 0.6
    return norm(x, 0.75)


def sfx_sad_trombone():
    notes = [(392, 0.45), (370, 0.45), (349, 0.45), (330, 1.4)]
    parts = []
    for f, d in notes:
        t = t_(d)
        vib = 1 + (0.012 * np.sin(2 * np.pi * 6 * t) if d > 1 else 0)
        ph = 2 * np.pi * np.cumsum(f * vib * np.ones(len(t))) / SR
        x = sum(np.sin(ph * h) / h ** 1.2 for h in range(1, 9))
        x *= env(len(t), 0.03, 0.12)
        if d > 1:
            x *= np.linspace(1, 0.2, len(t))
        parts.append(lp(x, 2200))
    return norm(np.concatenate(parts), 0.55)


def sfx_slide_down():
    d = 0.9
    x = glide(1300, 260, d, 0.8)
    x = (x + 0.3 * np.sign(x)) * env(len(x), 0.02, 0.15)
    return norm(lp(x, 4000), 0.5)


def sfx_slide_updown():
    a = glide(400, 1200, 0.35)
    b = glide(1200, 500, 0.35)
    x = np.concatenate([a, b]) * env(len(a) + len(b), 0.02, 0.1)
    return norm(x, 0.35)


def sfx_squeal():
    d = 1.9
    t = t_(d)
    f = 1050 + 280 * np.sin(2 * np.pi * 5.5 * t) + 200 * np.sin(2 * np.pi * 0.7 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.6 * np.sin(2 * ph) + 0.35 * np.sin(3 * ph)
    x *= 1 + 0.35 * np.sin(2 * np.pi * 23 * t)
    x *= env(len(t), 0.03, 0.4)
    return norm(lp(x, 5000), 0.5)


def sfx_swirl():
    d = 2.2
    t = t_(d)
    f = 300 * 2 ** (3 * t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t))
    x += sfx_whoosh(d, 200, 4000)[:len(t)] * 0.8
    x *= env(len(t), 0.3, 0.6)
    return norm(x, 0.5)


def sfx_door():
    d = 0.5
    t = t_(d)
    x = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 14) + lp(noise(d), 1200) * np.exp(-t * 30)
    return norm(x, 0.7)


def sfx_water(d=3.0):
    n = noise(d)
    x = bp(n, 800, 5000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3 * t_(d))))
    x *= env(len(x), 0.15, 0.4)
    return norm(x, 0.3)


def sfx_splash():
    d = 0.6
    x = bp(noise(d), 600, 6000) * np.exp(-t_(d) * 7)
    return norm(x, 0.5)


def sfx_tiptoe():
    out = np.zeros(int(1.8 * SR))
    for i, f in enumerate([523, 659, 523, 784]):
        d = 0.25
        t = t_(d)
        x = np.sin(2 * np.pi * f * t) * np.exp(-t * 18)
        k = int(i * 0.4 * SR)
        out[k:k + len(x)] += x
    return norm(out, 0.35)


def sfx_tada():
    out = np.zeros(int(1.8 * SR))
    for i, (f, st) in enumerate([(523, 0), (659, 0.12), (784, 0.24), (1047, 0.36)]):
        d = 1.2 if i == 3 else 0.3
        t = t_(d)
        x = sum(np.sin(2 * np.pi * f * h * t) / h for h in (1, 2, 3)) * np.exp(-t * (3 if i == 3 else 10))
        k = int(st * SR)
        out[k:k + len(x)] += x
    return norm(out, 0.45)


def sfx_blink():
    d = 0.08
    x = glide(2000, 3000, d) * np.exp(-t_(d) * 40)
    return norm(x, 0.25)


def sfx_heart():
    d = 0.8
    t = t_(d)
    x = glide(900, 1600, d, 0.5) * np.exp(-t * 3) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t))
    return norm(x, 0.35)


def sfx_curtain():
    return sfx_whoosh(2.4, 150, 1200)


def sfx_applause(d=3.0):
    out = np.zeros(int(d * SR))
    for _ in range(int(140 * d)):
        cd = 0.03
        c = bp(noise(cd), 1200, 5000) * np.exp(-t_(cd) * 120)
        i = int(_rng.uniform(0, d - cd) * SR)
        out[i:i + len(c)] += c * _rng.uniform(0.3, 1)
    out *= env(len(out), 0.3, 1.2)
    return norm(out, 0.4)


SFX = {
    "drumroll": sfx_drumroll, "cymbal": sfx_cymbal, "pop": sfx_pop, "tink": sfx_tink,
    "ding": sfx_ding, "bling": sfx_bling, "sparkle": sfx_sparkle, "zap": sfx_zap,
    "lazyzap": sfx_lazy_zap, "whoosh": sfx_whoosh, "boom": sfx_boom, "splat": sfx_splat,
    "glitterhit": sfx_glitter_hit, "thud": sfx_thud, "stomp": sfx_stomp,
    "trombone": sfx_sad_trombone, "slidedown": sfx_slide_down, "slideupdown": sfx_slide_updown,
    "squeal": sfx_squeal, "swirl": sfx_swirl, "door": sfx_door, "water": sfx_water,
    "splash": sfx_splash, "tiptoe": sfx_tiptoe, "tada": sfx_tada, "blink": sfx_blink,
    "heart": sfx_heart, "curtain": sfx_curtain, "applause": sfx_applause,
}
_cache = {}


def get_sfx(name):
    if name not in _cache:
        _cache[name] = SFX[name]().astype(np.float32)
    return _cache[name]


# ------------------------------------------------------------- music
def note_f(n):
    return 440 * 2 ** ((n - 69) / 12)


def pluck(f, d, bright=0.5):
    t = t_(d)
    x = (np.sin(2 * np.pi * f * t) + bright * 0.5 * np.sin(4 * np.pi * f * t)
         + bright * 0.2 * np.sin(6 * np.pi * f * t))
    return x * np.exp(-t * 5) * env(len(t), 0.004)


def pad(freqs, d):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t + i) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t) for i, f in enumerate(freqs))
    x *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * t) ** 2
    return lp(x * env(len(t), 0.8, 0.8), 1800)


def music_show(total):
    """Light circus waltz."""
    bpm = 138
    beat = 60 / bpm
    out = np.zeros(int((total + 3) * SR))
    prog = [(48, [64, 67, 72]), (45, [64, 69, 72]), (41, [65, 69, 72]), (43, [62, 67, 71]),
            (48, [64, 67, 72]), (45, [60, 64, 69]), (43, [62, 65, 71]), (43, [62, 67, 71])]
    melody = [76, 79, 77, 76, 74, 72, 74, 76, 72, 74, 71, 67, 72, 76, 74, 67]
    bar = 0
    tt = 0.0
    while tt < total + 1:
        root, ch = prog[bar % len(prog)]
        i = int(tt * SR)
        b = pluck(note_f(root), beat * 1.2, 0.8) * 0.9
        out[i:i + len(b)] += b[:len(out) - i]
        for k in (1, 2):
            j = int((tt + k * beat) * SR)
            for n in ch:
                c = pluck(note_f(n), beat * 0.8, 0.3) * 0.22
                out[j:j + len(c)] += c[:max(0, len(out) - j)]
        if bar % 2 == 0:
            for k in range(2):
                n = melody[(bar + k) % len(melody)]
                j = int((tt + k * beat * 1.5) * SR)
                m = pluck(note_f(n + 12), beat * 1.4, 0.2) * 0.18
                out[j:j + len(m)] += m[:max(0, len(out) - j)]
        tt += 3 * beat
        bar += 1
    return norm(lp(out, 5000), 1.0)[:int(total * SR)]


def music_dream(total, prog=None, tone=1.0):
    out = np.zeros(int((total + 6) * SR))
    prog = prog or [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    d = 4.0
    tt = 0.0
    k = 0
    rnd = np.random.default_rng(9)
    while tt < total + 1:
        p = pad([note_f(n) for n in prog[k % len(prog)]], d + 1.0)
        i = int(tt * SR)
        out[i:i + len(p)] += p[:max(0, len(out) - i)] * 0.3
        for _ in range(3):
            n = rnd.choice(prog[k % len(prog)]) + 24
            j = int((tt + rnd.uniform(0, d)) * SR)
            b = pluck(note_f(n), 1.5, 0.1) * 0.12 * tone
            out[j:j + len(b)] += b[:max(0, len(out) - j)]
        tt += d
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_lounge(total):
    return music_dream(total, [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]], 1.6)


def music_sneaky(total):
    """Pizzicato tiptoe bass line."""
    out = np.zeros(int((total + 2) * SR))
    beat = 0.42
    line = [45, 0, 48, 0, 52, 0, 51, 0, 50, 0, 48, 0, 45, 47, 48, 0]
    tt = 0.0
    k = 0
    while tt < total:
        n = line[k % len(line)]
        if n:
            p = pluck(note_f(n + 12), 0.3, 0.6)
            i = int(tt * SR)
            out[i:i + len(p)] += p[:max(0, len(out) - i)]
        tt += beat
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


MOODS = {"show": music_show, "dream": music_dream, "lounge": music_lounge, "sneaky": music_sneaky}
