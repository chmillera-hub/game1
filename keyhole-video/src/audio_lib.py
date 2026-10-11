"""Procedural audio: instruments, reverb, sound effects, laughter."""
import numpy as np
from scipy import signal

SR = 48000
rng_global = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def n(name):
    """'C4' -> midi number"""
    if name[1:2] in ("#", "b"):
        p, o = name[:2], name[2:]
    else:
        p, o = name[:1], name[1:]
    return 12 * (int(o) + 1) + NOTE[p]


def adsr(nsamp, a=0.01, d=0.1, s=0.7, r=0.2, gate=None):
    """gate: seconds the note is held (release starts after)."""
    if gate is None:
        gate = nsamp / SR - r
    t = np.arange(nsamp) / SR
    env = np.zeros(nsamp)
    a = max(a, 1e-4)
    m = t < a
    env[m] = t[m] / a
    m = (t >= a) & (t < a + d)
    env[m] = 1 - (1 - s) * (t[m] - a) / max(d, 1e-4)
    m = (t >= a + d) & (t < gate)
    env[m] = s
    lvl_at_gate = s if gate >= a + d else (gate / a if gate < a else 1 - (1 - s) * (gate - a) / max(d, 1e-4))
    m = t >= gate
    env[m] = lvl_at_gate * np.exp(-(t[m] - gate) / max(r / 4, 1e-4))
    return env


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def highpass(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bandpass(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], "band")
    return signal.lfilter(b, a, x)


# ---------------------------------------------------------------- instruments
def ks_pluck(freq, dur, bright=0.5, decay=0.996, seed=None):
    """Karplus-Strong plucked string via IIR comb (fast)."""
    rng = np.random.default_rng(seed)
    N = int(SR / freq)
    nsamp = int(dur * SR)
    exc = rng.uniform(-1, 1, N)
    exc = lowpass(exc, 1500 + 6000 * bright, 1)
    x = np.zeros(nsamp)
    x[:N] = exc
    # y[n] = x[n] + decay*0.5*(y[n-N] + y[n-N-1])
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -decay * 0.5
    a[N + 1] = -decay * 0.5
    y = signal.lfilter([1.0], a, x)
    fade = int(0.02 * SR)
    y[-fade:] *= np.linspace(1, 0, fade)
    return y / (np.abs(y).max() + 1e-9)


def epiano(freq, dur, vel=0.8, gate=None):
    """FM electric piano (Rhodes-ish)."""
    t = t_axis(dur)
    if gate is None:
        gate = dur * 0.7
    idx = (1.6 * vel) * np.exp(-t * 3.0) + 0.15
    mod = np.sin(2 * np.pi * freq * t)
    car = np.sin(2 * np.pi * freq * t + idx * mod)
    # tine bell partial
    bell = 0.18 * vel * np.sin(2 * np.pi * freq * 7.0 * t) * np.exp(-t * 14)
    env = adsr(len(t), 0.003, 1.2, 0.35, 0.5, gate) * np.exp(-t * 0.6)
    return (car + bell) * env


def piano(freq, dur, vel=0.7, gate=None):
    """Soft additive piano."""
    t = t_axis(dur)
    if gate is None:
        gate = dur * 0.8
    y = np.zeros_like(t)
    B = 0.0004
    for k in range(1, 9):
        fk = freq * k * np.sqrt(1 + B * k * k)
        if fk > 14000:
            break
        amp = (1.0 / k ** 1.3) * (0.6 + 0.4 * vel)
        dec = 0.9 + 0.45 * k + freq / 900
        y += amp * np.sin(2 * np.pi * fk * t + 0.3 * k) * np.exp(-t * dec)
    # slight detuned unison for warmth
    y += 0.25 * np.sin(2 * np.pi * freq * 1.0015 * t) * np.exp(-t * 1.2)
    ham = np.random.default_rng(int(freq)).normal(0, 1, len(t)) * np.exp(-t * 90) * 0.04 * vel
    y += lowpass(ham, 2500)
    rel = np.ones_like(t)
    m = t > gate
    rel[m] = np.exp(-(t[m] - gate) / 0.12)
    att = np.minimum(1, t / 0.004)
    return y * rel * att * vel


def musicbox(freq, dur, vel=0.7):
    t = t_axis(dur)
    y = (np.sin(2 * np.pi * freq * t) * np.exp(-t * 2.2)
         + 0.35 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
         + 0.12 * np.sin(2 * np.pi * freq * 5.4 * t) * np.exp(-t * 12)
         + 0.08 * np.sin(2 * np.pi * freq * 8.9 * t) * np.exp(-t * 20))
    y *= np.minimum(1, t / 0.002)
    return y * vel


def pad(freqs, dur, a=1.2, r=1.5, bright=1200, detune=0.006, seed=0):
    """Warm detuned saw pad, low-passed, slow envelope."""
    t = t_axis(dur)
    rng = np.random.default_rng(seed)
    y = np.zeros_like(t)
    for f in freqs:
        for d in (-detune, 0, detune):
            ph = rng.uniform(0, 1)
            saw = 2 * ((f * (1 + d) * t + ph) % 1.0) - 1
            y += saw
    y /= max(1, len(freqs) * 3)
    y = lowpass(y, bright, 2)
    env = adsr(len(t), a, 0.3, 0.9, r, max(a, dur - r))
    return y * env


def bass(freq, dur, vel=0.8, gate=None):
    t = t_axis(dur)
    if gate is None:
        gate = dur * 0.85
    y = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * 2 * freq * t) + 0.08 * np.sin(2 * np.pi * 3 * freq * t)
    y = np.tanh(1.3 * y)
    env = adsr(len(t), 0.005, 0.25, 0.6, 0.12, gate)
    return y * env * vel


def pizz(freq, dur=0.6, vel=0.8, seed=None):
    y = ks_pluck(freq, dur, bright=0.25, decay=0.985, seed=seed)
    return lowpass(y, 2500) * vel


def clarinet(freq, dur, vel=0.6, gate=None):
    """Odd-harmonic reed-ish tone with vibrato."""
    t = t_axis(dur)
    if gate is None:
        gate = dur * 0.85
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.3)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    y = np.sin(ph) + 0.33 * np.sin(3 * ph) + 0.15 * np.sin(5 * ph) + 0.06 * np.sin(7 * ph)
    y = lowpass(y, 3000)
    env = adsr(len(t), 0.03, 0.1, 0.85, 0.08, gate)
    return y * env * vel


def cello(freq, dur, vel=0.6, a=0.4, r=0.8):
    t = t_axis(dur)
    vib = 1 + 0.003 * np.sin(2 * np.pi * 4.8 * t)
    ph = np.cumsum(freq * vib) / SR
    saw = 2 * (ph % 1.0) - 1
    y = lowpass(saw, 900, 2) + 0.3 * lowpass(saw, 300, 1)
    env = adsr(len(t), a, 0.2, 0.9, r, max(a, dur - r))
    return y * env * vel


# ---------------------------------------------------------------- effects
_IR_CACHE = {}


def reverb(x, wet=0.25, decay=1.8, tone=5000, predelay=0.02, stereo=True):
    """Convolution reverb with synthetic decorrelated IR. x mono -> (n,2)"""
    key = (decay, tone, predelay)
    if key not in _IR_CACHE:
        rng = np.random.default_rng(11)
        L = int(decay * SR)
        tt = np.arange(L) / SR
        irs = []
        for ch in range(2):
            nz = rng.normal(0, 1, L) * np.exp(-tt * 6.9 / decay)
            nz = lowpass(nz, tone, 1)
            pd = np.zeros(int(predelay * SR))
            ir = np.concatenate([pd, nz])
            ir /= np.sqrt((ir ** 2).sum())
            irs.append(ir)
        _IR_CACHE[key] = irs
    irs = _IR_CACHE[key]
    if x.ndim == 2:
        xm = x.mean(1)
        dry = x
    else:
        xm = x
        dry = np.stack([x, x], 1)
    out = np.zeros((len(x) + len(irs[0]) - 1, 2))
    for ch in range(2):
        out[:, ch] = signal.fftconvolve(xm, irs[ch])[: len(out)]
    out *= wet
    out[: len(x)] += dry * (1 - wet * 0.5)
    return out


def place(buf, clip, t, gain=1.0, pan=0.0):
    """Mix clip (mono or stereo) into stereo buf at time t."""
    i = int(round(t * SR))
    if i >= len(buf):
        return
    if clip.ndim == 1:
        l = np.cos((pan + 1) * np.pi / 4)
        r = np.sin((pan + 1) * np.pi / 4)
        clip = np.stack([clip * l * 1.414, clip * r * 1.414], 1)
    if i < 0:
        clip = clip[-i:]
        i = 0
    j = min(len(buf), i + len(clip))
    buf[i:j] += clip[: j - i] * gain


def resample(x, ratio):
    """Speed up by ratio (pitch up). Linear-phase polyphase resampling."""
    from fractions import Fraction
    fr = Fraction(ratio).limit_denominator(200)
    return signal.resample_poly(x, fr.denominator, fr.numerator)


# ---------------------------------------------------------------- sfx
def sfx_tick(vel=1.0, tock=False):
    t = t_axis(0.08)
    rng = np.random.default_rng(3 if tock else 4)
    f = 2400 if not tock else 1800
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 180) + 0.5 * bandpass(rng.normal(0, 1, len(t)), 2000, 6000) * np.exp(-t * 300)
    return y * 0.35 * vel


def sfx_snort(pitch=1.0, seed=1):
    rng = np.random.default_rng(seed)
    dur = 0.28
    t = t_axis(dur)
    nz = rng.normal(0, 1, len(t))
    # nasal fluttery noise: amplitude-modulated low band noise
    flutter = 0.6 + 0.4 * np.sin(2 * np.pi * 38 * pitch * t)
    y = bandpass(nz, 250 * pitch, 1400 * pitch) * flutter
    y += 0.4 * np.sin(2 * np.pi * 180 * pitch * t + 3 * np.sin(2 * np.pi * 38 * pitch * t))
    env = np.minimum(1, t / 0.015) * np.exp(-t * 9)
    return y * env * 0.5


def sfx_sizzle(dur=2.0, seed=5):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    nz = highpass(rng.normal(0, 1, len(t)), 3000)
    crack = np.zeros_like(t)
    for _ in range(int(dur * 40)):
        i = rng.integers(0, len(t) - 500)
        crack[i:i + 300] += rng.normal(0, 1, 300) * np.exp(-np.arange(300) / 40) * rng.uniform(0.5, 2)
    y = nz * 0.15 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.7 * t)) + highpass(crack, 2000) * 0.15
    env = np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.5)
    return y * env


def sfx_crickets(dur=4.0, seed=8, density=1.0):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    y = np.zeros_like(t)
    for c in range(3):
        f = rng.uniform(4200, 5200)
        rate = rng.uniform(0.55, 0.9)  # seconds between chirp groups
        tt = rng.uniform(0, rate)
        while tt < dur - 0.2:
            for p in range(3):
                i0 = int((tt + p * 0.022) * SR)
                L = int(0.014 * SR)
                if i0 + L < len(y):
                    tp = np.arange(L) / SR
                    y[i0:i0 + L] += np.sin(2 * np.pi * f * tp) * np.sin(np.pi * tp / tp[-1]) * (0.5 + 0.5 * (c == 0))
            tt += rate * rng.uniform(0.85, 1.15) / density
    env = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.6)
    return y * env * 0.07


def sfx_whoosh(dur=0.8, seed=9):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    nz = rng.normal(0, 1, len(t))
    # sweep bandpass by chunked filtering
    out = np.zeros_like(nz)
    seg = 1024
    for i in range(0, len(nz), seg):
        fr = i / len(nz)
        fc = 300 + 2500 * np.sin(np.pi * fr)
        b, a = signal.butter(2, [fc * 0.6 / (SR / 2), fc * 1.6 / (SR / 2)], "band")
        out[i:i + seg] = signal.lfilter(b, a, nz[i:i + seg])
    env = np.sin(np.pi * t / dur) ** 2
    return out * env * 0.35


def sfx_bleep(dur):
    t = t_axis(dur)
    y = np.sin(2 * np.pi * 1000 * t)
    f = int(0.006 * SR)
    env = np.ones_like(t)
    env[:f] = np.linspace(0, 1, f)
    env[-f:] = np.linspace(1, 0, f)
    return y * env * 0.14


def sfx_alarm(dur=1.6):
    t = t_axis(dur)
    f = 620 + 140 * np.sin(2 * np.pi * 2.5 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) + 0.3 * np.sin(2 * ph)
    y = lowpass(y, 2500)
    env = np.minimum(1, t / 0.05) * np.minimum(1, (dur - t) / 0.4)
    return y * env * 0.10


def sfx_knuckles(seed=12):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(0.7 * SR))
    for k, tt in enumerate([0.0, 0.12, 0.2, 0.34, 0.41]):
        i = int(tt * SR)
        L = int(0.03 * SR)
        c = bandpass(rng.normal(0, 1, L), 800, 5000) * np.exp(-np.arange(L) / (0.004 * SR))
        out[i:i + L] += c * rng.uniform(0.6, 1.0)
    return out * 0.6


def sfx_creak(dur=1.6, seed=13):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    # stick-slip: irregular pulse train with slowly varying rate, through resonances
    rate = 90 + 60 * np.sin(2 * np.pi * 0.6 * t) + 25 * rng.normal(0, 1, len(t)).cumsum() / SR
    ph = np.cumsum(rate) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    y = np.zeros_like(t)
    for f, q in [(420, 0.08), (890, 0.06), (1500, 0.05)]:
        b, a = signal.iirpeak(f / (SR / 2), 1 / q)
        y += signal.lfilter(b, a, pulses)
    env = np.minimum(1, t / 0.1) * np.minimum(1, (dur - t) / 0.3)
    return y * env * 0.5


def sfx_sniff():
    rng = np.random.default_rng(14)
    t = t_axis(0.35)
    y = bandpass(rng.normal(0, 1, len(t)), 1500, 6000)
    env = np.sin(np.pi * np.minimum(1, t / 0.3)) ** 2 * (t < 0.3)
    return y * env * 0.18


def sfx_flip():
    rng = np.random.default_rng(15)
    t = t_axis(0.25)
    y = bandpass(rng.normal(0, 1, len(t)), 200, 1500) * np.exp(-t * 25) * 0.6
    return y


def breath(dur=0.35, inhale=True, seed=0, gain=0.12):
    rng = np.random.default_rng(seed)
    t = t_axis(dur)
    y = bandpass(rng.normal(0, 1, len(t)), 900, 4500)
    if inhale:
        env = (t / dur) ** 1.5 * np.minimum(1, (dur - t) / 0.04)
    else:
        env = np.exp(-t * 6) * np.minimum(1, t / 0.02)
    return y * env * gain


# ---------------------------------------------------------------- laughter
def make_laugh(syllables, sr_in, kind="adult", dur=2.0, seed=0, pitch=1.0, gain=1.0):
    """Granular laugh built from TTS 'ha' syllables (list of arrays at sr_in).
    Returns (audio@SR, list of syllable onset times)."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int((dur + 1.0) * SR))
    onsets = []
    if kind == "kid":
        ioi0, ioi_jit, slen, bout = 0.15, 0.025, 0.13, (5, 9)
    elif kind == "soft":
        ioi0, ioi_jit, slen, bout = 0.24, 0.04, 0.16, (3, 5)
    elif kind == "chuckle":
        ioi0, ioi_jit, slen, bout = 0.2, 0.03, 0.12, (3, 4)
    else:
        ioi0, ioi_jit, slen, bout = 0.19, 0.03, 0.16, (5, 8)
    tt = 0.0
    while tt < dur - 0.2:
        nb = rng.integers(*bout)
        for k in range(nb):
            if tt > dur - 0.1:
                break
            s = syllables[rng.integers(len(syllables))]
            # pitch contour: start high, fall across bout
            semis = (3.0 - 4.0 * k / max(1, nb - 1)) + rng.normal(0, 0.6)
            r = pitch * 2 ** (semis / 12)
            x = resample(s, r * SR / sr_in) if abs(r * SR / sr_in - 1) > 1e-3 else s
            L = int(slen * SR * rng.uniform(0.85, 1.15))
            x = x[:L].copy()
            fade = int(0.05 * SR)
            if len(x) > fade:
                x[-fade:] *= np.linspace(1, 0, fade) ** 1.5
            amp = (1.0 - 0.45 * k / nb) * rng.uniform(0.8, 1.0)
            # breathy onset
            hb = breath(0.05, inhale=False, seed=int(rng.integers(1e6)), gain=0.25)
            i = int(tt * SR)
            out[i:i + len(x)] += x * amp
            out[i:i + len(hb)] += hb * amp
            onsets.append(tt)
            tt += ioi0 * rng.uniform(1 - ioi_jit / ioi0, 1 + ioi_jit / ioi0) * (1 + 0.2 * k / nb)
        # inhale between bouts
        if tt < dur - 0.6 and kind != "chuckle":
            ib = breath(0.32, inhale=True, seed=int(rng.integers(1e6)), gain=0.10 if kind != "kid" else 0.07)
            i = int((tt + 0.02) * SR)
            out[i:i + len(ib)] += ib
            tt += 0.42
        else:
            tt += 0.15
    out = out[: int((tt + 0.3) * SR)]
    return out * gain, onsets
