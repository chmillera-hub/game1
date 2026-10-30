#!/usr/bin/env python3
"""Procedural sound-effect + ambience library for "The Family Inside".

All sounds are synthesised deterministically (seeded numpy RNG) at 48 kHz from
shaped / filtered noise, resonators and envelopes. Every sound is faded at its
edges so nothing clicks.

API
  SR                         sample rate (48000)
  sfx(name, seed=0)          -> float32 array (mono (n,) or stereo (n,2)) or None
  amb(name, dur, seed=0)     -> float32 stereo (n,2) of `dur` seconds, or None
  SFX_NAMES, AMB_NAMES       available names
Unknown names print a warning and return None (never raise).

One-shots are peak-normalised to about -6 dBFS; ambience beds are rendered at a
consistent quiet nominal level (the mixer applies the cue gain on top).

Run `python3 audio/sfx.py [outdir]` to render every sound to wavs for inspection.
"""
import sys
import zlib
import numpy as np
from scipy import signal

SR = 48000


# ----------------------------------------------------------------- helpers
def _rng(name, seed=0):
    return np.random.default_rng(zlib.crc32(name.encode()) + 7919 * int(seed))


def _n(sec):
    return max(1, int(round(sec * SR)))


def _sos(kind, f, order=2):
    f = np.clip(np.atleast_1d(np.asarray(f, float)), 10, SR / 2 * 0.95)
    return signal.butter(order, f if len(f) > 1 else f[0], kind, fs=SR, output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("lowpass", f, order), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=0)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", [lo, hi], order), x, axis=0)


def reson(x, f, tau):
    """Two-pole resonator at f Hz with amplitude decay time-constant tau (s)."""
    r = np.exp(-1.0 / (tau * SR))
    w = 2 * np.pi * f / SR
    a = [1.0, -2 * r * np.cos(w), r * r]
    b = [(1 - r * r) * np.sin(w) + 1e-9]
    return signal.lfilter(b, a, x)


def modes(x, freqs, taus, amps):
    y = np.zeros(len(x))
    for f, t, a in zip(freqs, taus, amps):
        if f < SR / 2 * 0.95:
            y += a * reson(x, f, t)
    return y


def fade(x, fi=0.004, fo=0.03):
    x = np.array(x, dtype=np.float64, copy=True)
    n = len(x)
    a, b = min(_n(fi), n // 2), min(_n(fo), n // 2)
    if a > 0:
        w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
        x[:a] = (x[:a].T * w).T
    if b > 0:
        w = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
        x[-b:] = (x[-b:].T * w).T
    return x


def smooth_noise(rng, n, rate_hz):
    """Slow random control signal ~N(0,1) varying at about rate_hz."""
    k = max(4, int(n / SR * rate_hz) + 4)
    pts = rng.standard_normal(k)
    xi = np.linspace(0, k - 3, n)
    return np.interp(xi, np.arange(k), pts)


def burst_env(n, attack, decay):
    t = np.arange(n) / SR
    return (1 - np.exp(-t / max(attack, 1e-4))) * np.exp(-t / decay)


def bell(n, peak=0.5, p=2.0):
    """Smooth asymmetric hump 0..1..0 with maximum at fraction `peak`."""
    u = np.linspace(0, 1, n)
    a = np.where(u < peak, u / peak, (1 - u) / (1 - peak))
    return np.sin(np.clip(a, 0, 1) * np.pi / 2) ** p


def place(dst, src, i0):
    i0 = int(i0)
    if i0 >= len(dst):
        return
    s0 = max(0, -i0)
    i0 = max(0, i0)
    m = min(len(src) - s0, len(dst) - i0)
    if m > 0:
        dst[i0:i0 + m] += src[s0:s0 + m]


def norm_peak(x, db=-6.0):
    x = fade(x)
    p = np.max(np.abs(x)) + 1e-12
    return (x * (10 ** (db / 20) / p)).astype(np.float32)


def pink(rng, n):
    w = rng.standard_normal(n)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    return signal.lfilter(b, a, w) * 8


def brown(rng, n):
    return signal.lfilter([1], [1, -0.995], rng.standard_normal(n)) * 0.1


def _wood_knock(rng, f0=140, bright=1.0, dur=0.25):
    n = _n(dur)
    exc = rng.standard_normal(n) * burst_env(n, 0.0004, 0.004)
    body = modes(exc, [f0, f0 * 2.3, f0 * 3.9, 620 * bright, 1150 * bright],
                 [0.05, 0.03, 0.02, 0.012, 0.007], [1.0, 0.6, 0.35, 0.4, 0.25])
    click = hp(exc, 1500) * 0.25 * bright
    return lp(body + click, 6000)


# ----------------------------------------------------------------- one-shots
def s_whoosh_soft(rng):
    n = _n(1.3)
    x = pink(rng, n)
    env = bell(n, 0.55, 2.2)
    fc = 300 + 1500 * bell(n, 0.55, 1.0)
    # time-varying band via block processing of two filtered copies (crossfade)
    lo = bp(x, 150, 700)
    hi_ = bp(x, 600, 2500)
    mix = (fc - 300) / 1500
    y = (lo * (1 - mix) + hi_ * mix) * env
    pan = np.linspace(-0.35, 0.35, n)
    L = y * np.cos((pan + 1) * np.pi / 4)
    R = y * np.sin((pan + 1) * np.pi / 4)
    return np.stack([L, R], 1)


def s_pencil_tap(rng):
    out = np.zeros(_n(0.75))
    for i, t in enumerate([0.0, 0.19, 0.37]):
        n = _n(0.08)
        exc = rng.standard_normal(n) * burst_env(n, 0.0002, 0.0012)
        tap = modes(exc, [780, 1650, 2900, 4300], [0.012, 0.008, 0.005, 0.003],
                    [1.0, 0.6, 0.4, 0.2]) + hp(exc, 2500) * 0.3
        place(out, tap * (1.0 - 0.12 * i) * rng.uniform(0.9, 1.05), _n(t))
    return lp(out, 7000)


def s_flame_burst(rng):
    n = _n(1.6)
    t = np.arange(n) / SR
    x = pink(rng, n)
    env = (1 - np.exp(-t / 0.05)) * np.exp(-t / 0.45)
    lo = lp(x, 350, 2)
    mid = bp(x, 400, 2200)
    sweep = np.clip(1 - t / 0.5, 0, 1)
    y = (lo * 1.0 + mid * 0.6 * sweep) * env
    # a few sparks
    for _ in range(14):
        i = int(rng.uniform(0.02, 0.9) * SR)
        m = _n(0.01)
        c = hp(rng.standard_normal(m), 2000) * burst_env(m, 0.0002, 0.0015)
        place(y, c * rng.uniform(0.05, 0.25) * np.exp(-i / SR / 0.5), i)
    return y


def s_fire_roar(rng):
    n = _n(3.2)
    x = brown(rng, n) + 0.3 * pink(rng, n)
    mod = 1 + 0.35 * smooth_noise(rng, n, 4)
    env = bell(n, 0.2, 1.5)
    y = lp(x, 500, 2) * mod * env + bp(pink(rng, n), 500, 1600) * 0.15 * env * mod
    return y


def s_bellows(rng):
    n = _n(0.6)
    x = pink(rng, n)
    env = bell(n, 0.35, 2.0)
    air = bp(x, 250, 1400) * env + lp(x, 200) * env * 0.6
    # leather/wood creak at the start of the squeeze
    m = _n(0.12)
    pulses = np.zeros(m)
    pulses[::int(SR / 95)] = 1.0
    cr = modes(pulses * np.hanning(m), [420, 980, 1700], [0.01, 0.006, 0.004], [1, .5, .3])
    place(air, cr * 0.15, 0)
    return air


def _creak(rng, dur, f_lo, f_hi, formants=(520, 1180, 2300, 3400)):
    """Stick-slip creak: irregular impulse train through wood resonances."""
    n = _n(dur)
    u = np.linspace(0, 1, n)
    rate = f_lo + (f_hi - f_lo) * (0.5 - 0.5 * np.cos(np.pi * u * 1.6)) \
        + 12 * smooth_noise(rng, n, 9)
    phase = np.cumsum(np.maximum(rate, 20) / SR)
    tr = np.diff(np.floor(phase), prepend=0.0)
    tr *= 1 + 0.5 * rng.standard_normal(n)
    amp = bell(n, 0.4, 1.0) * (0.6 + 0.4 * np.abs(smooth_noise(rng, n, 6)))
    exc = tr * amp
    y = modes(exc, formants, [0.008, 0.006, 0.004, 0.003], [1.0, 0.8, 0.5, 0.3])
    y += bp(rng.standard_normal(n), 800, 3000) * amp * 0.02
    return lp(y, 6000)


def s_door_creak(rng):
    return _creak(rng, 1.3, 55, 190)


def s_chair_scrape(rng):
    n = _n(0.7)
    y = _creak(rng, 0.7, 110, 260, formants=(310, 760, 1500, 2600))
    noise = bp(rng.standard_normal(n), 300, 2500) * bell(n, 0.45, 1.0) * 0.08
    knock = _wood_knock(rng, 120, 0.7, 0.3)
    out = np.zeros(_n(0.9))
    place(out, y + noise, 0)
    place(out, knock * 0.6, _n(0.62))
    return out


def s_footsteps_wood(rng):
    out = np.zeros(_n(2.6))
    for i in range(4):
        t = 0.08 + i * rng.uniform(0.52, 0.6)
        k = _wood_knock(rng, rng.uniform(95, 130), 0.5, 0.35)
        n = _n(0.12)
        scuff = bp(rng.standard_normal(n), 400, 3000) * bell(n, 0.3, 1.5) * 0.04
        place(out, lp(k, 2500) * rng.uniform(0.75, 1.0) * (1 - 0.08 * i), _n(t))
        place(out, scuff, _n(t + 0.03))
        if rng.random() < 0.5:
            cr = _creak(rng, 0.25, 140, 220) * 0.15
            place(out, cr, _n(t + 0.05))
    return out


def s_mug_set(rng):
    n = _n(0.6)
    exc = rng.standard_normal(n) * burst_env(n, 0.0002, 0.0009)
    ceramic = modes(exc, [1870, 3120, 4690, 6350], [0.06, 0.04, 0.025, 0.015],
                    [1.0, 0.7, 0.45, 0.25])
    wood = _wood_knock(rng, 150, 0.6, 0.6)
    y = ceramic * 0.35 + wood[:n] * 0.9
    # tiny second contact (the base settling)
    y2 = np.zeros(n)
    place(y2, (ceramic * 0.12 + wood[:n] * 0.25)[: _n(0.3)], _n(0.035))
    return lp(y + y2, 9000)


def s_sniff(rng):
    out = np.zeros(_n(0.9))
    for t0, d, a in [(0.0, 0.16, 0.6), (0.24, 0.38, 1.0)]:
        n = _n(d)
        x = rng.standard_normal(n)
        env = np.linspace(0, 1, n) ** 1.5 * bell(n, 0.85, 0.6)
        y = modes(bp(x, 600, 6000), [1100, 2600, 3900], [0.004, 0.003, 0.002], [1, .7, .4])
        y = y * env + bp(x, 1500, 5000) * env * 0.05
        place(out, y * a, _n(t0))
    return lp(out, 7000)


def s_phone_buzz(rng):
    out = np.zeros(_n(1.3))
    for t0 in (0.0, 0.62):
        n = _n(0.42)
        t = np.arange(n) / SR
        f = 172 + 3 * np.sin(2 * np.pi * 7 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        motor = np.tanh(2.5 * np.sin(ph)) + 0.3 * np.sin(2 * ph)
        env = np.minimum(1, t / 0.03) * np.minimum(1, (t[-1] - t) / 0.04)
        rattle = modes(motor * (np.abs(np.sin(ph)) > 0.9), [340, 910, 2100],
                       [0.02, 0.01, 0.006], [1, .6, .3])
        y = lp(motor * 0.5 + rattle * 0.8, 3500) * env
        place(out, y, _n(t0))
    return out


def s_tin_open(rng):
    out = np.zeros(_n(1.0))
    # short scrape of the lid edge
    n = _n(0.22)
    scr = bp(rng.standard_normal(n), 2000, 7000) * bell(n, 0.6, 1.2)
    scr *= 1 + 0.6 * np.sin(2 * np.pi * 37 * np.arange(n) / SR)
    place(out, scr * 0.05, 0)
    # pop as the lid frees, then light metallic ring
    m = _n(0.8)
    exc = rng.standard_normal(m) * burst_env(m, 0.0002, 0.0015)
    ring = modes(exc, [1240, 2930, 4410, 6080, 7350], [0.12, 0.08, 0.06, 0.04, 0.03],
                 [1.0, 0.7, 0.5, 0.35, 0.2])
    pop = lp(exc, 900) * 2.0
    place(out, ring * 0.3 + pop, _n(0.2))
    return out


def s_paper_rustle(rng):
    n = _n(1.1)
    x = rng.standard_normal(n)
    dens = np.clip(0.3 + 0.7 * bell(n, 0.4, 1.0) + 0.4 * smooth_noise(rng, n, 12), 0, None)
    crinkle = (rng.random(n) < dens * 0.004).astype(float) * rng.uniform(0.3, 1, n)
    cr = modes(crinkle, [2600, 4100, 5800], [0.002, 0.0015, 0.001], [1, .8, .5])
    hiss = bp(x, 1800, 8000) * dens * 0.04
    return lp(cr * 0.5 + hiss, 10000) * bell(n, 0.4, 0.5)


def s_cloth_rustle(rng):
    n = _n(0.9)
    x = rng.standard_normal(n)
    am = np.clip(bell(n, 0.4, 1.0) * (0.7 + 0.5 * smooth_noise(rng, n, 10)), 0, None)
    return bp(x, 700, 5000) * am * 0.3 + lp(x, 600) * am * 0.1


def s_water_pour(rng):
    dur = 2.6
    n = _n(dur)
    env = np.minimum(1, np.arange(n) / _n(0.25)) * np.minimum(1, (n - np.arange(n)) / _n(0.5))
    stream = bp(pink(rng, n), 300, 3000) * 0.08 * env
    out = stream.copy()
    # bubbles: decaying sines with rising pitch (Minnaert resonance)
    nb = int(dur * 45)
    for _ in range(nb):
        t0 = rng.uniform(0.05, dur - 0.25)
        f0 = rng.uniform(350, 1400) * (1 + 0.3 * t0 / dur)  # vessel fills, pitch rises
        d = rng.uniform(0.02, 0.07)
        m = _n(d * 4)
        tt = np.arange(m) / SR
        f = f0 * (1 + 2.0 * tt / (d * 4) * 0.4)
        b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / d) * (1 - np.exp(-tt / 0.001))
        place(out, b * rng.uniform(0.05, 0.25) * env[min(int(t0 * SR), n - 1)], _n(t0))
    return lp(out, 6000)


def s_door_unlock(rng):
    out = np.zeros(_n(0.9))
    # key slides in: short metallic scratch
    n = _n(0.18)
    sc = bp(rng.standard_normal(n), 2500, 8000) * bell(n, 0.5, 1.0) * 0.06
    place(out, sc, 0)
    # two pin clicks + bolt clunk
    for t, f, a in [(0.28, 3300, 0.6), (0.36, 2700, 0.5), (0.55, 900, 1.0)]:
        m = _n(0.15)
        exc = rng.standard_normal(m) * burst_env(m, 0.0002, 0.001)
        c = modes(exc, [f, f * 1.47, f * 2.13], [0.015, 0.01, 0.006], [1, .6, .3])
        if f < 1500:
            c = c + _wood_knock(rng, 110, 0.6, 0.15)[:m] * 0.8
        place(out, c * a, _n(t))
    return lp(out, 9000)


def s_door_knock(rng):
    """Two soft knuckle raps on a solid wooden door."""
    out = np.zeros(_n(0.55), dtype=np.float32)
    for k, t0 in enumerate((0.0, 0.26)):
        rap = _wood_knock(rng, f0=118 + 6 * k, bright=0.8, dur=0.22)
        place(out, rap * (0.9 if k == 0 else 0.8), int(t0 * SR))
    return fade(out)


SFX = {k[2:]: v for k, v in globals().items() if k.startswith("s_")}
SFX_NAMES = sorted(SFX)


def sfx(name, seed=0):
    f = SFX.get(name)
    if f is None:
        print(f"[sfx] WARNING: unknown sfx '{name}' - skipped", file=sys.stderr)
        return None
    y = f(_rng(name, seed))
    return norm_peak(y, -6.0)


# ----------------------------------------------------------------- ambiences
def _stereo(rng, mono_fn, n, corr=0.6):
    """Two independent renders blended into a stereo pair with correlation ~corr."""
    a, b = mono_fn(), mono_fn()
    return np.stack([a, corr * a + np.sqrt(1 - corr ** 2) * b], 1)


def a_room_tone(rng, n):
    def one():
        x = brown(rng, n) * 0.6 + pink(rng, n) * 0.02
        x = lp(hp(x, 40), 900)
        return x * (1 + 0.08 * smooth_noise(rng, n, 0.2))
    y = _stereo(rng, one, n, 0.5)
    hum = 0.04 * np.sin(2 * np.pi * 60 * np.arange(n) / SR)[:, None] * np.array([[1, 0.9]])
    y = y + hum * np.std(y)
    return y / (np.sqrt(np.mean(y ** 2)) + 1e-12) * 10 ** (-50 / 20)


def a_clock_tick(rng, n):
    y = np.zeros((n, 2))
    k = 0
    t = 0.25
    while t < n / SR:
        m = _n(0.12)
        exc = rng.standard_normal(m) * burst_env(m, 0.0001, 0.0007)
        s = 1.0 if k % 2 == 0 else 0.86
        c = modes(exc, [2150 * s, 3600 * s, 5200 * s, 950 * s], [0.012, 0.008, 0.005, 0.02],
                  [1, .6, .35, .4])
        c = lp(c, 8000) * rng.uniform(0.9, 1.0)
        # tiny room reflection
        c2 = c.copy()
        place(c2, c * 0.18, _n(0.011))
        place(y[:, 0], c2 * 0.9, int(t * SR))
        place(y[:, 1], c2 * 0.75, int(t * SR) + 12)
        k += 1
        t += 1.0
    return y / (np.max(np.abs(y)) + 1e-12) * 10 ** (-30 / 20)


def a_fire_crackle(rng, n):
    dur = n / SR
    def roar_one():
        x = brown(rng, n)
        x = lp(hp(x, 50), 450)
        return x * np.clip(1 + 0.35 * smooth_noise(rng, n, 1.3) + 0.15 * smooth_noise(rng, n, 7), 0.2, None)
    roar = _stereo(rng, roar_one, n, 0.7)
    roar = roar / (np.sqrt(np.mean(roar ** 2)) + 1e-12) * 10 ** (-38 / 20)
    cr = np.zeros((n, 2))
    t = 0.0
    while True:
        t += rng.exponential(1 / 7.0)
        if t >= dur - 0.05:
            break
        cluster = 1 if rng.random() < 0.7 else rng.integers(2, 6)
        pan = rng.uniform(-0.5, 0.5)
        for j in range(cluster):
            tj = t + j * rng.uniform(0.008, 0.05)
            m = _n(0.06)
            exc = rng.standard_normal(m) * burst_env(m, 0.0001, rng.uniform(0.0004, 0.003))
            f = rng.uniform(900, 4500)
            c = reson(exc, f, rng.uniform(0.002, 0.008)) * 0.5 + hp(exc, 1500) * 0.3
            if rng.random() < 0.15:  # deeper wood pop
                c = c + reson(exc, rng.uniform(250, 600), 0.01) * 0.8
            a = min(1.0, rng.pareto(2.5) * 0.25 + 0.05)
            i = int(tj * SR)
            place(cr[:, 0], c * a * np.cos((pan + 1) * np.pi / 4), i)
            place(cr[:, 1], c * a * np.sin((pan + 1) * np.pi / 4), i)
    cr = lp(cr, 7000)
    cr = cr / (np.max(np.abs(cr)) + 1e-12) * 10 ** (-24 / 20)
    return roar + cr


def _bird_phrase(rng):
    kind = rng.integers(0, 3)
    out = []
    count = rng.integers(3, 8)
    base = rng.uniform(2600, 4800)
    for i in range(count):
        d = rng.uniform(0.04, 0.12) if kind != 2 else rng.uniform(0.15, 0.3)
        m = _n(d)
        u = np.linspace(0, 1, m)
        if kind == 0:     # down-slur chirps
            f = base * (1.25 - 0.4 * u)
        elif kind == 1:   # up-sweep "tweet"
            f = base * (0.8 + 0.45 * u ** 2)
        else:             # whistled note with vibrato
            f = base * 0.75 * (1 + 0.03 * np.sin(2 * np.pi * 28 * u * d))
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) + 0.15 * np.sin(2 * ph)
        s *= np.sin(np.pi * u) ** 1.5
        out.append(s * rng.uniform(0.6, 1.0))
        out.append(np.zeros(_n(rng.uniform(0.03, 0.12))))
    return np.concatenate(out)


def a_birds_morning(rng, n):
    dur = n / SR
    y = np.zeros((n, 2))
    birds = [(rng.uniform(-0.8, 0.8), rng.uniform(0.4, 1.0), rng.uniform(1.5, 4.0)) for _ in range(4)]
    for pan, amp, gap in birds:
        t = rng.uniform(0, gap)
        while t < dur:
            p = _bird_phrase(rng) * amp
            i = int(t * SR)
            place(y[:, 0], p * np.cos((pan + 1) * np.pi / 4), i)
            place(y[:, 1], p * np.sin((pan + 1) * np.pi / 4), i)
            t += len(p) / SR + rng.exponential(gap)
    # distance: soften highs, short diffuse tail
    y = lp(hp(y, 1500), 6500)
    m = _n(0.35)
    ir = rng.standard_normal((m, 2)) * np.exp(-np.arange(m) / SR / 0.08)[:, None]
    ir[0] += 4.0
    wet = np.stack([signal.fftconvolve(y[:, c], ir[:, c])[:n] for c in range(2)], 1)
    air = lp(hp(pink(rng, n), 200), 2000)[:, None] * np.array([[1, 1]])
    air = air / (np.sqrt(np.mean(air ** 2)) + 1e-12) * 10 ** (-54 / 20)
    wet = wet / (np.max(np.abs(wet)) + 1e-12) * 10 ** (-26 / 20)
    return wet + air


AMB = {k[2:]: v for k, v in globals().items() if k.startswith("a_")}
AMB_NAMES = sorted(AMB)


def amb(name, dur, seed=0):
    f = AMB.get(name)
    if f is None:
        print(f"[sfx] WARNING: unknown ambience '{name}' - skipped", file=sys.stderr)
        return None
    n = _n(dur)
    y = f(_rng(name, seed), n)
    y = fade(y, 0.05, 0.05)
    return np.nan_to_num(y).astype(np.float32)


if __name__ == "__main__":
    import os
    import soundfile as sf
    out = sys.argv[1] if len(sys.argv) > 1 else "build/sfx_preview"
    os.makedirs(out, exist_ok=True)
    for nm in SFX_NAMES:
        y = sfx(nm)
        sf.write(f"{out}/{nm}.wav", y, SR, subtype="PCM_16")
        print(f"{nm:16s} {len(y)/SR:5.2f}s peak {20*np.log10(np.max(np.abs(y))):6.1f} dB")
    for nm in AMB_NAMES:
        y = amb(nm, 10)
        rms = 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-12)
        sf.write(f"{out}/amb_{nm}.wav", y, SR, subtype="PCM_16")
        print(f"amb {nm:12s} rms {rms:6.1f} dB peak {20*np.log10(np.max(np.abs(y))):6.1f}")
