"""DSP helpers + procedural sound effects. Everything is mono float32 @ 48 kHz."""
import numpy as np
from scipy import signal

SR = 48000
_rng = np.random.default_rng(1234)


def rng(seed=None):
    return np.random.default_rng(seed) if seed is not None else _rng


def tt(dur):
    return np.arange(int(round(dur * SR))) / SR


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)


def lp(x, fc, order=2):
    fc = min(fc, SR / 2 * 0.95)
    return signal.sosfilt(signal.butter(order, fc, "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return signal.sosfilt(signal.butter(order, fc, "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    hi = min(hi, SR / 2 * 0.95)
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def peak(x, f, q):
    b, a = signal.iirpeak(min(f, SR / 2 * 0.9), q, fs=SR)
    return signal.lfilter(b, a, x)


def tv_bandpass(x, fc, q=4.0, block=256):
    """Time-varying bandpass: fc is an array (same len as x)."""
    y = np.zeros_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR / 2 * 0.9))
        b, a = signal.iirpeak(f, q, fs=SR)
        seg, zi = signal.lfilter(b, a, x[i:i + block], zi=zi)
        y[i:i + block] = seg
    return y


def tv_lowpass(x, fc, block=256):
    y = np.zeros_like(x)
    zi = np.zeros((1, 2))
    for i in range(0, len(x), block):
        f = float(np.clip(fc[min(i + block // 2, len(fc) - 1)], 30, SR / 2 * 0.9))
        sos = signal.butter(2, f, "low", fs=SR, output="sos")
        seg, zi = signal.sosfilt(sos, x[i:i + block], zi=zi)
        y[i:i + block] = seg
    return y


def norm(x, pk=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x * (pk / m)


def fade(x, fin=0.005, fout=0.01):
    x = x.copy()
    n1, n2 = int(fin * SR), int(fout * SR)
    if n1 > 0:
        x[:n1] *= np.linspace(0, 1, n1)
    if n2 > 0:
        x[-n2:] *= np.linspace(1, 0, n2)
    return x


def smooth_noise(n, rate, seed=None):
    """Band-limited random curve in [-1,1] changing at about `rate` Hz."""
    r = rng(seed)
    k = max(2, int(n / SR * rate) + 3)
    pts = r.uniform(-1, 1, k)
    xs = np.linspace(0, n, k)
    return np.interp(np.arange(n), xs, pts)


def phase_of(freq):
    return np.cumsum(freq) / SR


def additive(freq, nh, amp_fn=lambda k: 1.0 / k):
    """Band-limited additive oscillator with time-varying freq array."""
    ph = 2 * np.pi * phase_of(freq)
    fmax = float(np.max(freq))
    out = np.zeros_like(ph)
    for k in range(1, nh + 1):
        if k * fmax > SR / 2 * 0.9:
            break
        out += amp_fn(k) * np.sin(k * ph)
    return out


def reverb(x, decay=1.2, wet=0.25, tone=5000, seed=3):
    r = rng(seed)
    n = int(decay * SR)
    t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / decay * 6.9)
    ir = lp(ir, tone)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
    w = np.zeros(len(x) + n)
    c = signal.fftconvolve(x, ir)
    w[: len(c)] = c[: len(w)]
    dry = np.concatenate([x, np.zeros(n)])
    return dry * (1 - wet) + w * wet * 1.2


def place(buf, sig, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        sig = sig[-i:]
        i = 0
    j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * gain


# ----------------------------------------------------------------- voice-ish
def vocal(f0, formants, breath=0.2, voiced_env=None, breath_env=None, seed=None, tilt=1.3):
    """Formant synthesis. f0: array; formants: list of (freq, q, gain)."""
    n = len(f0)
    src = additive(f0, 40, lambda k: k ** -tilt)
    noise = rng(seed).standard_normal(n) * 0.6
    ve = np.ones(n) if voiced_env is None else voiced_env
    be = ve if breath_env is None else breath_env
    s = src * ve + noise * be * breath
    out = np.zeros(n)
    for f, q, g in formants:
        out += g * peak(s, f, q)
    return out


VOW_EH = [(560, 5, 1.0), (1750, 7, 0.6), (2550, 8, 0.3)]
VOW_AH = [(750, 5, 1.0), (1200, 6, 0.6), (2600, 8, 0.25)]
VOW_UH = [(600, 5, 1.0), (1150, 6, 0.5), (2450, 8, 0.2)]
VOW_EE = [(320, 5, 0.9), (2300, 8, 0.6), (3000, 9, 0.35)]
VOW_OO = [(350, 5, 1.0), (850, 6, 0.4), (2400, 9, 0.1)]


def laugh_syllables(n_syl, f0s, rate=6.0, vowel=VOW_EH, breath=0.6, dec=0.12, seed=None):
    r = rng(seed)
    dur = n_syl / rate + 0.35
    n = int(dur * SR)
    f0 = np.zeros(n)
    venv = np.zeros(n)
    benv = np.zeros(n)
    for i in range(n_syl):
        st = int(i / rate * SR * r.uniform(0.95, 1.05))
        L = int((1 / rate + 0.15) * SR)
        tl = np.arange(L) / SR
        fs = f0s[i] if hasattr(f0s, "__len__") else f0s
        seg_f = fs * (1 + 0.08 * np.exp(-tl * 18)) * (1 - 0.05 * tl)
        e_h = np.exp(-((tl - 0.02) / 0.025) ** 2)  # 'h' breath onset
        e_v = (1 - np.exp(-tl / 0.012)) * np.exp(-tl / dec)
        j = min(n, st + L)
        f0[st:j] = np.where(f0[st:j] > 0, f0[st:j], seg_f[: j - st])
        venv[st:j] += e_v[: j - st]
        benv[st:j] += e_h[: j - st] * 0.8 + e_v[: j - st] * 0.4
    f0[f0 == 0] = np.mean([f for f in np.atleast_1d(f0s)])
    return vocal(f0, vowel, breath=breath, voiced_env=venv, breath_env=benv, seed=seed)


# ----------------------------------------------------------------- SFX
def sfx_click():
    t = tt(0.03)
    x = rng(1).standard_normal(len(t)) * np.exp(-t / 0.002)
    x = hp(x, 2000) + 0.4 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.006)
    return norm(x, 0.6)


def sfx_typing(dur=2.0, seed=5):
    r = rng(seed)
    out = np.zeros(int((dur + 0.1) * SR))
    t = 0.0
    while t < dur:
        n = int(0.04 * SR)
        tl = np.arange(n) / SR
        bright = r.uniform(1500, 4500)
        k = hp(r.standard_normal(n) * np.exp(-tl / 0.004), bright)
        k += 0.3 * np.sin(2 * np.pi * r.uniform(180, 320) * tl) * np.exp(-tl / 0.01)
        place(out, k, t, r.uniform(0.25, 0.6))
        t += r.uniform(0.055, 0.15) + (0.25 if r.random() < 0.06 else 0)
    return norm(out, 0.6)


def sfx_whoosh(dur=0.6, f0=300, f1=3500, seed=8):
    t = tt(dur)
    n = len(t)
    x = rng(seed).standard_normal(n)
    fc = np.geomspace(f0, f1, n)
    y = tv_bandpass(x, fc, q=1.5)
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    return norm(y * env, 0.7)


def bell(f, dur=1.2, parts=((1, 1, 1.2), (2.0, .4, .6), (3.0, .25, .3), (4.2, .12, .2))):
    t = tt(dur)
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / d) for m, a, d in parts)
    return fade(x, 0.002, 0.05)


def sfx_ding():
    out = np.zeros(int(1.4 * SR))
    place(out, bell(1318.5, 1.0), 0)
    place(out, bell(1975.5, 1.2), 0.11)
    return norm(out, 0.6)


def sfx_snort():
    t = tt(0.32)
    r = rng(11)
    rattle = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 38 * t))
    x = lp(r.standard_normal(len(t)), 1400) * rattle
    x += 0.5 * additive(np.full(len(t), 105.0), 12, lambda k: 1 / k) * rattle
    env = np.minimum(t / 0.02, 1) * np.exp(-t / 0.12)
    return norm(lp(x, 2000) * env, 0.8)


def sfx_knuckles():
    r = rng(12)
    out = np.zeros(int(0.9 * SR))
    for i, tc in enumerate([0.0, 0.16, 0.27, 0.45, 0.6]):
        n = int(0.03 * SR)
        tl = np.arange(n) / SR
        c = bp(r.standard_normal(n), 1500, 7000) * np.exp(-tl / 0.004)
        c[:30] += r.uniform(-1, 1, 30) * 2
        place(out, c, tc, r.uniform(0.6, 1.0))
    return norm(out, 0.8)


def sfx_angelic(dur=5.0):
    t = tt(dur)
    n = len(t)
    out = np.zeros(n)
    for m in [40, 52, 56, 59, 64, 68]:
        for det in (-0.06, 0.0, 0.07):
            f = mtof(m + det) * (1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + m))
            out += additive(f, 30, lambda k: 1 / k)
    y = sum(g * peak(out, ff, q) for ff, q, g in VOW_AH)
    env = np.minimum(t / 1.4, 1) * np.minimum((dur - t) / 1.0, 1)
    shimmer = sum(np.sin(2 * np.pi * mtof(m) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * (0.7 + i * 0.3) * t))
                  for i, m in enumerate([76, 80, 83, 88]))
    y = norm(y * env, 0.8) + 0.08 * shimmer * env
    return norm(reverb(y, 2.5, 0.4), 0.7)


def sfx_thwip():
    t = tt(0.18)
    x = rng(14).standard_normal(len(t))
    y = tv_bandpass(x, np.geomspace(7000, 1800, len(t)), q=2)
    return norm(y * np.sin(np.pi * np.linspace(0, 1, len(t))), 0.6)


def sfx_thwock():
    t = tt(1.0)
    f = 150 + 650 * np.exp(-t / 0.012)
    pop = np.sin(2 * np.pi * phase_of(f)) * np.exp(-t / 0.05)
    click = rng(15).standard_normal(len(t)) * np.exp(-t / 0.003)
    vib = 1 + 0.12 * np.exp(-t / 0.35) * np.sin(2 * np.pi * 9 * t)
    boing = np.sin(2 * np.pi * phase_of(240 * vib)) * np.exp(-t / 0.3) * np.minimum(t / 0.01, 1)
    boing += 0.3 * np.sin(2 * np.pi * phase_of(480 * vib)) * np.exp(-t / 0.2)
    return norm(pop + 0.4 * click + 0.6 * boing, 0.9)


def sfx_vine_boom():
    t = tt(2.6)
    f = 38 + 40 * np.exp(-t / 0.25)
    x = np.sin(2 * np.pi * phase_of(f)) + 0.5 * np.sin(2 * np.pi * phase_of(2 * f))
    x = np.tanh(2.5 * x) * np.exp(-t / 0.9) * np.minimum(t / 0.004, 1)
    thump = lp(rng(16).standard_normal(len(t)), 250) * np.exp(-t / 0.08) * 3
    bwom = np.sin(2 * np.pi * phase_of(150 - 30 * t)) * np.exp(-t / 0.35) * 0.4
    y = x + thump + bwom
    return norm(reverb(y, 1.6, 0.3, 1500)[: int(3.2 * SR)], 0.95)


def sfx_heartbeat(dur=10.0, bpm0=70, bpm1=130):
    out = np.zeros(int((dur + 0.5) * SR))
    t = 0.0
    while t < dur:
        bpm = bpm0 + (bpm1 - bpm0) * (t / dur)
        for off, g in ((0, 1.0), (0.17, 0.7)):
            tl = tt(0.18)
            b = np.sin(2 * np.pi * (55 + 25 * np.exp(-tl / 0.02)) * tl) * np.exp(-tl / 0.05)
            place(out, b, t + off, g)
        t += 60 / bpm
    return norm(lp(out, 300), 0.8)


def sfx_gurgle(dur=2.0, seed=17):
    r = rng(seed)
    out = np.zeros(int((dur + 0.2) * SR))
    t = 0.0
    while t < dur:
        L = r.uniform(0.04, 0.09)
        tl = tt(L)
        f0 = r.uniform(80, 260)
        f = f0 * (1 + 1.2 * tl / L)
        b = np.sin(2 * np.pi * phase_of(f)) * np.sin(np.pi * tl / L)
        place(out, b, t, r.uniform(0.3, 1))
        t += r.uniform(0.03, 0.16)
    rumble = lp(r.standard_normal(len(out)), 180) * (0.5 + 0.5 * smooth_noise(len(out), 8, seed))
    return norm(out + 0.6 * norm(rumble), 0.8)


def sfx_tiny_giggle(seed=18):
    y = laugh_syllables(5, [760, 740, 720, 690, 650], rate=9.5, vowel=VOW_EE, breath=0.3, dec=0.06, seed=seed)
    return norm(hp(y, 300), 0.6)


def sfx_muffled_giggle(dur=2.5, seed=19, intensity=1.0):
    r = rng(seed)
    t = tt(dur)
    n = len(t)
    f0 = (170 + 40 * intensity * smooth_noise(n, 3, seed)) * (1 + 0.02 * r.standard_normal(n).cumsum() / np.sqrt(np.arange(1, n + 1)))
    src = additive(f0, 25, lambda k: k ** -1.1)
    burst_rate = 6.5
    ph = (t * burst_rate) % 1
    bursts = np.exp(-ph / 0.09) * (0.5 + 0.5 * (smooth_noise(n, 3, seed + 1) > -0.4))
    nasal = peak(src, 260, 3) + 0.4 * peak(src, 900, 5)
    y = lp(nasal * bursts, 1100)
    squeal = np.zeros(n)
    for k in range(int(dur * 0.8 * intensity)):
        st = r.uniform(0, max(0.01, dur - 0.3))
        tl = tt(0.25)
        s = np.sin(2 * np.pi * phase_of(np.linspace(700, 950, len(tl)))) * np.sin(np.pi * tl / 0.25)
        place(squeal, s, st, 0.15)
    env = np.minimum(t / 0.05, 1) * np.minimum((dur - t) / 0.1, 1)
    return norm((y + squeal) * env, 0.7)


def fart(dur=3.5, f_lo=55, f_hi=150, seed=21, honk=0.6, wet=0.2):
    """Cartoon fart: buzzing lip-vibration source + resonant lowpass + sputters."""
    r = rng(seed)
    t = tt(dur)
    n = len(t)
    u = t / dur
    contour = f_lo + (f_hi - f_lo) * (np.sin(np.pi * np.clip(u * 1.3, 0, 1)) ** 1.5) * honk
    f = contour * (1 + 0.18 * smooth_noise(n, 9, seed) + 0.06 * smooth_noise(n, 40, seed + 1))
    f = f + (f_lo * 0.3) * smooth_noise(n, 2, seed + 2)
    f = np.maximum(f, 25)
    ph = 2 * np.pi * phase_of(f)
    src = np.tanh(4 * np.sin(ph)) + 0.4 * np.sin(2 * ph + 0.5)
    flutter = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * phase_of(14 + 10 * (smooth_noise(n, 3, seed + 3) + 1))))
    flutter = lp(flutter, 80)
    cut = 350 + 900 * np.clip(contour / f_hi, 0, 1)
    y = tv_lowpass(src * flutter, cut)
    y = peak(y, 180, 2) * 0.5 + y
    env = np.minimum(t / 0.03, 1) * np.clip((dur - t) / 0.25, 0, 1)
    # sputter gaps near the end
    gate = np.ones(n)
    tail = u > 0.78
    gate[tail] = (smooth_noise(n, 22, seed + 4)[tail] > -0.1).astype(float)
    gate = lp(gate, 60)
    y = y * env * gate
    if wet > 0:
        bub = np.zeros(n)
        for _ in range(int(dur * 6 * wet)):
            st = r.uniform(0, dur * 0.95)
            tl = tt(0.05)
            b = np.sin(2 * np.pi * phase_of(r.uniform(90, 200) * (1 + 2 * tl / 0.05))) * np.sin(np.pi * tl / 0.05)
            place(bub, b, st, r.uniform(0.2, 0.6))
        y = y + bub * wet
    return norm(y, 0.9)


def sfx_squelch(seed=22):
    r = rng(seed)
    out = np.zeros(int(0.7 * SR))
    for st in (0.0, 0.07, 0.15, 0.21):
        tl = tt(0.08)
        f = r.uniform(100, 180) * (1 + 2.5 * tl / 0.08)
        place(out, np.sin(2 * np.pi * phase_of(f)) * np.sin(np.pi * tl / 0.08), st, r.uniform(0.6, 1))
    tl = tt(0.35)
    splat = lp(r.standard_normal(len(tl)), 900) * np.exp(-tl / 0.07)
    place(out, splat, 0.02, 1.2)
    return norm(out, 0.85)


def sfx_strain_squeak(dur=0.8, seed=23):
    t = tt(dur)
    f = (720 + 120 * smooth_noise(len(t), 6, seed)) * (1 + 0.03 * np.sin(2 * np.pi * 23 * t))
    s = additive(f, 10, lambda k: k ** -1.4)
    s = bp(s, 600, 3500) * (0.6 + 0.4 * np.sin(2 * np.pi * 17 * t))
    env = np.sin(np.pi * t / dur) ** 0.5
    return norm(s * env, 0.5)


def pluck(f, dur=1.0, bright=0.6, decay=1.5):
    t = tt(dur)
    x = np.zeros(len(t))
    for k in range(1, 16):
        if k * f > SR * 0.45:
            break
        x += (k ** -(1.6 - bright)) * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (decay + 0.8 * k))
    return fade(x, 0.002, 0.05)


def sfx_harp(up=True):
    notes = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84, 86]
    if not up:
        notes = notes[::-1]
    out = np.zeros(int(2.4 * SR))
    for i, m in enumerate(notes):
        place(out, pluck(mtof(m), 1.4, 0.7, 1.2), i * 0.06, 0.5)
    return norm(reverb(out, 1.8, 0.35), 0.6)


def sfx_pop():
    t = tt(0.12)
    f = 300 + 900 * np.exp(-t / 0.02)
    return norm(np.sin(2 * np.pi * phase_of(f)) * np.exp(-t / 0.035), 0.7)


def sfx_bubble_pop():
    t = tt(0.4)
    x = np.sin(2 * np.pi * phase_of(400 + 1600 * np.exp(-t / 0.015))) * np.exp(-t / 0.04)
    x += hp(rng(24).standard_normal(len(t)), 3000) * np.exp(-t / 0.01) * 0.6
    return norm(reverb(x, 0.6, 0.2)[: int(0.7 * SR)], 0.8)


def sfx_slurp(dur=0.9, seed=25):
    t = tt(dur)
    n = len(t)
    x = rng(seed).standard_normal(n)
    fc = np.geomspace(600, 2600, n) * (1 + 0.25 * np.sin(2 * np.pi * 13 * t))
    y = tv_bandpass(x, fc, q=3)
    gate = 0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 9 * t))
    env = np.minimum(t / 0.05, 1) * np.minimum((dur - t) / 0.1, 1)
    return norm(lp(y * gate, 4000) * env, 0.5)


def sfx_woof(seed=26):
    out = np.zeros(int(0.9 * SR))
    for st, p in ((0.0, 1.0), (0.32, 0.92)):
        t = tt(0.22)
        f0 = 330 * p * (1 - 0.35 * t / 0.22)
        ve = np.minimum(t / 0.01, 1) * np.exp(-t / 0.08)
        y = vocal(f0, [(550, 4, 1), (1100, 5, .6), (2500, 6, .25)], breath=0.8, voiced_env=ve, seed=seed)
        place(out, np.tanh(3 * norm(y)), st)
    return norm(reverb(out, 0.5, 0.2)[: len(out)], 0.6)


def sfx_lawnmower(dur=6.0, seed=27):
    t = tt(dur)
    n = len(t)
    f = 32 * (1 + 0.04 * smooth_noise(n, 5, seed))
    x = additive(f, 60, lambda k: k ** -0.8)
    x = lp(np.tanh(2 * x), 900)
    x += 0.2 * lp(rng(seed).standard_normal(n), 2000)
    env = np.minimum(t / 0.6, 1) * np.minimum((dur - t) / 0.6, 1)
    return norm(x * env, 0.4)


def sfx_glass_crack(seed=28):
    r = rng(seed)
    out = np.zeros(int(1.2 * SR))
    for st in (0.0, 0.03, 0.07, 0.12, 0.2):
        tl = tt(0.6)
        c = hp(r.standard_normal(len(tl)), 2500) * np.exp(-tl / 0.015)
        c += sum(np.sin(2 * np.pi * r.uniform(3000, 8000) * tl) * np.exp(-tl / r.uniform(0.05, 0.2)) * 0.2 for _ in range(4))
        place(out, c, st, r.uniform(0.5, 1))
    return norm(out, 0.8)


def sfx_slide_whistle(dur=1.0, f0=1800, f1=280):
    t = tt(dur)
    f = np.geomspace(f0, f1, len(t)) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
    x = np.sin(2 * np.pi * phase_of(f)) + 0.15 * np.sin(4 * np.pi * phase_of(f))
    x += 0.05 * bp(rng(29).standard_normal(len(t)), 1000, 4000)
    env = np.minimum(t / 0.04, 1) * np.minimum((dur - t) / 0.08, 1)
    return norm(x * env, 0.55)


def sfx_thud():
    t = tt(0.6)
    x = np.sin(2 * np.pi * phase_of(45 + 60 * np.exp(-t / 0.03))) * np.exp(-t / 0.12)
    x += lp(rng(30).standard_normal(len(t)), 400) * np.exp(-t / 0.03) * 1.5
    return norm(x, 0.95)


def sfx_can_clank(seed=31):
    r = rng(seed)
    out = np.zeros(int(1.2 * SR))
    for st, g in ((0, 1), (0.2, 0.6), (0.33, 0.4), (0.42, 0.25)):
        tl = tt(0.5)
        c = sum(np.sin(2 * np.pi * fr * tl) * np.exp(-tl / d)
                for fr, d in ((1250, 0.08), (1930, 0.06), (3100, 0.05), (4700, 0.03)))
        c += hp(r.standard_normal(len(tl)), 2000) * np.exp(-tl / 0.006)
        place(out, c, st, g)
    return norm(out, 0.5)


def sfx_ghost(dur=2.4):
    t = tt(dur)
    f = 420 + 260 * np.sin(np.pi * t / dur) - 120 * t / dur
    f = f * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
    x = np.sin(2 * np.pi * phase_of(f)) + 0.08 * bp(rng(32).standard_normal(len(t)), 300, 2000)
    env = np.sin(np.pi * t / dur) ** 1.2
    return norm(reverb(x * env, 2.0, 0.45), 0.5)


def sfx_record_scratch():
    t = tt(0.5)
    x = rng(33).standard_normal(len(t))
    fc = 1200 + 900 * np.sin(2 * np.pi * 5 * t)
    y = tv_bandpass(x, fc, q=3) * (np.abs(np.sin(2 * np.pi * 5 * t)) ** 0.5)
    return norm(y * np.exp(-t / 0.3), 0.7)


def sfx_upload_chime():
    out = np.zeros(int(1.6 * SR))
    for i, m in enumerate([72, 76, 79, 84]):
        place(out, bell(mtof(m), 1.0), i * 0.09, 0.5)
    return norm(out, 0.5)


def sfx_notify(seed=34):
    t = tt(0.15)
    f = 900 + 600 * (t / 0.15)
    return norm(np.sin(2 * np.pi * phase_of(f)) * np.exp(-t / 0.05), 0.4)


def sfx_ticks(dur=3.0):
    out = np.zeros(int((dur + 0.1) * SR))
    t = 0.0
    k = 0
    while t < dur:
        place(out, sfx_click()[: int(0.01 * SR)], t, 0.4)
        t += max(0.025, 0.12 * (1 - t / dur))
        k += 1
    return out


def balloon_squeal(dur, f_start=720, f_end=420, seed=40, stutter=True):
    r = rng(seed)
    t = tt(dur)
    n = len(t)
    u = t / dur
    base = f_start + (f_end - f_start) * u
    f = base * (1 + 0.12 * smooth_noise(n, 4, seed) + 0.04 * smooth_noise(n, 25, seed + 1))
    f = f * (1 + 0.02 * np.sin(2 * np.pi * 31 * t))
    ph = 2 * np.pi * phase_of(f)
    src = np.tanh(2.5 * np.sin(ph)) + 0.3 * np.sin(3 * ph)
    flutter = 0.65 + 0.35 * np.sin(2 * np.pi * phase_of(27 + 8 * smooth_noise(n, 3, seed + 2)))
    y = bp(src * flutter, 350, 5000)
    hiss = bp(r.standard_normal(n), 1500, 7000) * 0.12
    amp = 0.7 + 0.3 * smooth_noise(n, 2, seed + 3)
    if stutter:
        g = (smooth_noise(n, 3.5, seed + 4) > -0.55).astype(float)
        amp = amp * lp(g, 30)
    env = np.minimum(t / 0.05, 1) * np.clip((dur - t) / 0.3, 0, 1)
    return (y + hiss) * amp * env


def sigh_chuckle(dur, f_start=150, f_end=85, seed=41, chuckle_depth=0.8):
    """Long dry-heave exhale with chuckle pulses that fade out."""
    t = tt(dur)
    n = len(t)
    u = t / dur
    f0 = (f_start + (f_end - f_start) * u ** 0.7) * (1 + 0.03 * smooth_noise(n, 12, seed))
    jitter = 1 + 0.06 * rng(seed).standard_normal(n)
    f0 = f0 * lp(jitter, 300)
    rate = 5.8 - 2.5 * u
    puls = 0.5 + 0.5 * np.cos(2 * np.pi * phase_of(rate))
    depth = chuckle_depth * (1 - u) ** 1.5
    chuck = 1 - depth * (1 - puls ** 2)
    venv = np.minimum(t / 0.15, 1) * (1 - u) ** 0.8 * chuck * 0.7
    benv = np.minimum(t / 0.1, 1) * (1 - 0.5 * u) * (0.6 + 0.4 * chuck)
    vow = [(650 - 120 * 0, 4, 1.0), (1150, 5, 0.5), (2450, 7, 0.2)]
    y = vocal(f0, vow, breath=0.9, voiced_env=venv, breath_env=benv, seed=seed, tilt=1.5)
    env = np.clip((dur - t) / 0.4, 0, 1)
    return y * env


def inhale_wheeze(dur=0.7, seed=42):
    t = tt(dur)
    n = len(t)
    f = np.linspace(950, 1350, n) * (1 + 0.03 * smooth_noise(n, 15, seed))
    w = np.sin(2 * np.pi * phase_of(f)) * 0.5
    nz = peak(rng(seed).standard_normal(n), 2800, 3) * 0.6
    env = np.sin(np.pi * t / dur) ** 0.8
    return (w + nz) * env


def sfx_deflate_long(dur=30.0, seed=50):
    """The longest dry-heave sighing chuckle + deflating balloon."""
    r = rng(seed)
    out = np.zeros(int((dur + 1) * SR))
    t = 0.0
    k = 0
    lens = [5.5, 4.2, 6.5, 3.8, 5.0, 4.5, 6.0, 4.0]
    while t < dur - 1.0:
        L = min(lens[k % len(lens)], dur - t)
        energy = 1.0 - 0.55 * (t / dur)
        place(out, norm(sigh_chuckle(L, 155 - 10 * k % 30, 82, seed + k, 0.85 * energy)), t, 0.8 * energy)
        t += L
        if t < dur - 1.0:
            iw = r.uniform(0.5, 0.8)
            place(out, norm(inhale_wheeze(iw, seed + 100 + k)), t, 0.35 * energy)
            t += iw + 0.05
        k += 1
    squeal = balloon_squeal(dur, 760, 380, seed + 7)
    squeal = norm(squeal) * np.linspace(0.55, 0.3, len(squeal))
    place(out, squeal, 0.2, 0.75)
    # occasional wet sputters
    for _ in range(int(dur / 4)):
        place(out, fart(r.uniform(0.25, 0.5), 50, 90, int(r.integers(1000)), 0.2, 0.4), r.uniform(1, dur - 1), 0.25)
    return norm(out, 0.9)


def brass_note(f, dur, wah=True, vib=0.0, seed=60):
    t = tt(dur)
    n = len(t)
    fv = f * (1 + vib * np.minimum(t / 0.6, 1) * np.sin(2 * np.pi * 5.5 * t)) * (1 - 0.03 * np.exp(-t / 0.04))
    x = additive(fv, 28, lambda k: 1 / k)
    env = np.minimum(t / 0.05, 1) * np.clip((dur - t) / 0.12, 0, 1)
    bright = lp(env, 8)
    x = tv_lowpass(x, 300 + 2200 * bright)
    if wah:
        x = 0.4 * x + tv_bandpass(x, 500 + 1300 * np.minimum(t / 0.25, 1), q=2.5)
    return x * env


def sfx_sad_trombone():
    out = np.zeros(int(3.8 * SR))
    notes = [(55, 0.0, 0.42), (54, 0.45, 0.42), (53, 0.9, 0.42), (52, 1.35, 2.0)]
    for m, st, d in notes:
        place(out, brass_note(mtof(m), d, True, 0.03 if d > 1 else 0.0), st)
    return norm(reverb(out, 1.2, 0.2)[: len(out)], 0.85)


def honk(f, dur, droop=0.0):
    t = tt(dur)
    fv = f * (1 - 0.08 * np.exp(-t / 0.03)) * (1 - droop * t / dur)
    ph = 2 * np.pi * phase_of(fv)
    x = np.sign(np.sin(ph)) * 0.6 + np.sin(2 * ph) * 0.3
    x = lp(x, 6000)
    x = peak(x, 1100, 2) + peak(x, 2300, 3) * 0.6 + 0.3 * x
    env = np.minimum(t / 0.01, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return x * env


def sfx_clown_honk(sad=True):
    out = np.zeros(int(1.6 * SR))
    if sad:
        place(out, honk(340, 0.28), 0.0)
        place(out, honk(300, 0.7, 0.3), 0.42)
    else:
        place(out, honk(360, 0.18), 0.0)
        place(out, honk(360, 0.18), 0.26)
    return norm(out, 0.8)


def sfx_tiny_squeak(seed=70):
    out = np.zeros(int(1.2 * SR))
    place(out, norm(balloon_squeal(0.45, 900, 1200, seed, stutter=False)), 0.0, 0.6)
    place(out, fart(0.35, 60, 110, seed, 0.3, 0.1), 0.5, 0.35)
    return out


def sfx_heh(seed=71):
    y = laugh_syllables(1, [120], rate=4, vowel=VOW_EH, breath=0.8, dec=0.1, seed=seed)
    return norm(y, 0.6)


def sfx_rumble(dur=3.0, seed=72):
    t = tt(dur)
    x = lp(rng(seed).standard_normal(len(t)), 120)
    env = np.minimum(t / 1.5, 1) * np.minimum((dur - t) / 0.3, 1)
    return norm(x * env, 0.7)


def sfx_gasp(seed=73):
    t = tt(0.45)
    n = len(t)
    nz = rng(seed).standard_normal(n)
    y = peak(nz, 1400, 2) + 0.6 * peak(nz, 2600, 3)
    env = np.minimum(t / 0.08, 1) * np.exp(-np.maximum(t - 0.1, 0) / 0.08)
    return norm(y * env, 0.5)


def sfx_riser(dur=2.0, seed=74):
    t = tt(dur)
    x = rng(seed).standard_normal(len(t))
    y = tv_bandpass(x, np.geomspace(400, 6000, len(t)), q=2)
    tone = np.sin(2 * np.pi * phase_of(np.geomspace(200, 1600, len(t)))) * 0.3
    env = (t / dur) ** 2
    return norm((y + tone) * env, 0.6)


SFX = {
    "click": sfx_click, "typing": sfx_typing, "whoosh": sfx_whoosh, "ding": sfx_ding,
    "snort": sfx_snort, "knuckles": sfx_knuckles, "angelic": sfx_angelic, "thwip": sfx_thwip,
    "thwock": sfx_thwock, "vine_boom": sfx_vine_boom, "heartbeat": sfx_heartbeat,
    "gurgle": sfx_gurgle, "tiny_giggle": sfx_tiny_giggle, "muffled_giggle": sfx_muffled_giggle,
    "fart_long": lambda: fart(3.6, 48, 170, 21, 0.9, 0.15), "fart_small": lambda: fart(0.6, 70, 120, 5, 0.4, 0.0),
    "squelch": sfx_squelch, "strain_squeak": sfx_strain_squeak, "harp_up": lambda: sfx_harp(True),
    "harp_down": lambda: sfx_harp(False), "pop": sfx_pop, "bubble_pop": sfx_bubble_pop, "slurp": sfx_slurp,
    "woof": sfx_woof, "lawnmower": sfx_lawnmower, "glass_crack": sfx_glass_crack,
    "slide_whistle": sfx_slide_whistle, "thud": sfx_thud, "can_clank": sfx_can_clank, "ghost": sfx_ghost,
    "record_scratch": sfx_record_scratch, "upload_chime": sfx_upload_chime, "notify": sfx_notify,
    "ticks": sfx_ticks, "deflate_long": sfx_deflate_long, "sad_trombone": sfx_sad_trombone,
    "clown_honk": sfx_clown_honk, "honk_happy": lambda: sfx_clown_honk(False), "tiny_squeak": sfx_tiny_squeak,
    "heh": sfx_heh, "rumble": sfx_rumble, "gasp": sfx_gasp, "riser": sfx_riser,
}


# ----------------------------------------------------------------- v2 additions
def sfx_maniacal_laugh(seed=80):
    out = np.zeros(int(3.4 * SR))
    f1 = [260, 250, 245, 238, 232, 225, 218, 210, 200]
    f2 = [300, 285, 270, 262, 250, 240, 228, 215, 200, 185]
    place(out, laugh_syllables(len(f1), f1, rate=7.5, vowel=VOW_AH, breath=0.35, dec=0.1, seed=seed), 0.0)
    place(out, laugh_syllables(len(f2), f2, rate=8.0, vowel=VOW_AH, breath=0.35, dec=0.09, seed=seed + 1), 1.55)
    return norm(reverb(norm(out), 1.2, 0.3)[: len(out)], 0.8)


def sfx_breath_in(dur=1.6, seed=81):
    t = tt(dur)
    n = len(t)
    x = rng(seed).standard_normal(n)
    y = peak(x, 1300, 1.2) + 0.5 * peak(x, 2600, 2)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.2
    return norm(lp(y, 6000) * env, 0.45)


def sfx_breath_out(dur=1.8, seed=82):
    t = tt(dur)
    n = len(t)
    x = rng(seed).standard_normal(n)
    y = peak(x, 700, 1.0) + 0.4 * peak(x, 1500, 2)
    env = np.minimum(t / 0.15, 1) * np.exp(-t / (dur * 0.5))
    return norm(lp(y, 4000) * env, 0.45)


def sfx_fart_bomb(seed=83):
    t = tt(3.5)
    n = len(t)
    boom = np.zeros(n)
    vb = sfx_vine_boom()
    boom[: len(vb)] += vb[:n]
    blast = lp(rng(seed).standard_normal(n), 900) * np.exp(-t / 0.35) * np.minimum(t / 0.004, 1)
    rumble = lp(rng(seed + 1).standard_normal(n), 120) * np.exp(-t / 1.2)
    f = fart(2.4, 40, 140, seed, 1.0, 0.25)
    out = boom * 0.8 + norm(blast) * 0.7 + norm(rumble) * 0.6
    place(out, f, 0.05, 0.9)
    return norm(out, 0.95)


def sfx_jet_fart(seed=84):
    out = np.zeros(int(1.8 * SR))
    place(out, fart(1.1, 90, 260, seed, 1.0, 0.0), 0.0)
    place(out, sfx_whoosh(1.2, 400, 4000, seed), 0.2, 0.6)
    return norm(out, 0.85)


def sfx_splort(seed=85):
    out = np.zeros(int(1.0 * SR))
    place(out, fart(0.45, 60, 110, seed, 0.4, 0.8), 0.0, 0.7)
    place(out, sfx_squelch(seed), 0.25, 1.0)
    return norm(out, 0.85)


SFX.update({"maniacal_laugh": sfx_maniacal_laugh, "breath_in": sfx_breath_in, "breath_out": sfx_breath_out,
            "fart_bomb": sfx_fart_bomb, "jet_fart": sfx_jet_fart, "splort": sfx_splort})
