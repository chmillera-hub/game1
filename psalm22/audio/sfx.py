#!/usr/bin/env python3
"""Psalm 22 - sound design (all procedural; crowd voices made with the local Kokoro TTS).

Every cue is anchored to a shot id (shot start/end/fraction) or to a narration phrase from
timeline.json / phrases.json, so a regenerated timeline just needs a re-run.

Usage:  /opt/venv/bin/python psalm22/audio/sfx.py
Outputs ($WORK/audio):
  sfx.wav                    48 kHz stereo float, all sound design
  stems/sfx_amb.wav          ambience beds (wind, night, water, birds, fire, crowd ...)
  stems/sfx_fx.wav           spot effects (animals, hammer, dice, sword, earthquake ...)
  stems/sfx_trans.wav        transition whooshes / flash swells / final swell
  sfx_cues.json              the resolved cue list (seconds)
  sfx_cache/                 cached TTS crowd clips
"""
import json, os, sys, zlib
import numpy as np
from scipy.signal import lfilter, resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dsp  # noqa: E402
from dsp import SR  # noqa: E402

OUT = dsp.AUDIO
CACHE = os.path.join(OUT, "sfx_cache")
HAMMER_OFFSET = 0.32       # s after the start of "they pierce my hands..." (same as music.py)


def R(key):
    return np.random.default_rng(zlib.crc32(str(key).encode()))


def N(d):
    return int(round(d * SR))


# ============================================================================ building blocks
def slow_random(n, rng, rate=.3, lo=0., hi=1.):
    """Smooth random curve in [lo, hi] with roughly `rate` changes per second."""
    m = max(4, int(n / SR * rate) + 4)
    pts = rng.random(m)
    x = np.interp(np.linspace(0, m - 1, n), np.arange(m), pts)
    x = dsp.smooth(x, .35 / max(rate, 1e-3))
    x = (x - x.min()) / (np.ptp(x) + 1e-9)
    return lo + (hi - lo) * x


def tv_biquad(x, kind, fc, q=.707, chunk=256):
    """Time-varying RBJ biquad, coefficients updated per chunk (state carried over)."""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), (len(x),))
    y = np.empty_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), chunk):
        c = dsp._biquad(kind, float(np.clip(fc[min(i + chunk // 2, len(x) - 1)], 20, SR * .45)), q)[0]
        y[i:i + chunk], zi = lfilter(c[:3], c[3:], x[i:i + chunk], zi=zi)
    return y


def env_ad(n, a, d, shape=1.0):
    """Attack (s) then exponential decay with time-constant d (s)."""
    t = np.arange(n) / SR
    e = np.where(t < a, (t / max(a, 1e-4)) ** shape, np.exp(-(t - a) / max(d, 1e-4)))
    return e


def modal(freqs, amps, decays, dur, rng=None, jitter=0.0):
    t = np.arange(N(dur)) / SR
    y = np.zeros_like(t)
    for f, a, d in zip(freqs, amps, decays):
        ph = rng.random() * 2 * np.pi if rng is not None else 0
        f = f * (1 + (rng.normal(0, jitter) if rng is not None else 0))
        y += a * np.sin(2 * np.pi * f * t + ph) * np.exp(-t / d)
    return y


def grains(dur, rng, rate, f_lo, f_hi, glen=(.002, .012), amp=(.3, 1.)):
    """Sparse filtered noise clicks (gravel, crackle, dust)."""
    n = N(dur)
    y = np.zeros(n)
    k = rng.poisson(rate * dur)
    for _ in range(k):
        L = N(rng.uniform(*glen))
        if L < 8:
            continue
        g = rng.standard_normal(L) * np.exp(-np.linspace(0, 6, L)) * rng.uniform(*amp)
        f = np.exp(rng.uniform(np.log(f_lo), np.log(f_hi)))
        g = dsp.bp(g, f, q=2.0)
        i = rng.integers(0, max(1, n - L))
        y[i:i + L] += g
    return y


def harmonic_source(f0, rng, jitter=.02, shimmer=.1, rolloff=1.0, fmax=7000, sub=0.0):
    """Additive glottal-like source following an f0 curve (per-sample array)."""
    n = len(f0)
    jit = 1 + jitter * dsp.smooth(rng.standard_normal(n), .004)
    ph = np.cumsum(f0 * jit) / SR
    y = np.zeros(n)
    K = int(fmax / max(40.0, float(np.min(f0))))
    for k in range(1, K + 1):
        amp = 1.0 / k ** rolloff
        y += amp * np.sin(2 * np.pi * k * ph + rng.random() * 6.28) * (f0 * k < fmax)
    if sub:
        y += sub * np.sin(np.pi * ph) * (1 + np.sin(2 * np.pi * ph * .5))
    y *= 1 + shimmer * dsp.smooth(rng.standard_normal(n), .01)
    return y / (np.std(y) + 1e-9)


def formants(x, fl, gains=None, q=None, curve=None):
    """Parallel band-pass formant filter. fl: list of formant freqs (scalar or per-sample arrays)."""
    gains = gains or [1.0] * len(fl)
    q = q or [4.0] * len(fl)
    y = np.zeros_like(x)
    for f, g, qq in zip(fl, gains, q):
        if np.ndim(f) == 0:
            y += g * dsp.bp(x, float(f), q=qq)
        else:
            y += g * tv_biquad(x, "bp", f, q=qq)
    return y


def curve(n, pts):
    """Breakpoint curve over a clip: pts = [(fraction 0..1, value), ...]"""
    return np.interp(np.linspace(0, 1, n), [p[0] for p in pts], [p[1] for p in pts])


def norm(x, peak=1.0):
    return x * (peak / (np.max(np.abs(x)) + 1e-9))


# ============================================================================ ambience generators
def wind(dur, rng, center=550, gust=.22, howl=.25, dust=.0, depth=.65):
    n = N(dur)
    g = slow_random(n, rng, rate=gust)
    g2 = slow_random(n, rng, rate=gust * 3.1)
    out = np.zeros((n, 2))
    for ch in range(2):
        w = dsp.noise(n, rng, "pink")
        fc = center * (.45 + 1.3 * g * (.75 + .25 * g2))
        body = tv_biquad(w, "lp", fc, .6) - .7 * tv_biquad(w, "lp", fc * .22, .6)
        y = body * ((1 - depth) + depth * g ** 1.4)
        if howl:
            fh = 420 + 520 * g * (.8 + .2 * g2)
            y += howl * tv_biquad(w, "bp", fh, 9.0) * g ** 3 * 2.2
        if dust:
            s = dsp.hp(w, 3500) * (g ** 2) * dust * .5
            s *= 1 + .6 * dsp.smooth(rng.standard_normal(n), .01)
            y += s
        out[:, ch] = y
        g = np.roll(g, N(.13))
    return norm(out, .5)


def thunder(dur, rng, dist=1.0):
    n = N(dur)
    t = np.arange(n) / SR
    env = np.zeros(n)
    for k in range(rng.integers(4, 8)):
        t0 = rng.uniform(0, dur * .45) if k else 0.0
        a, d = rng.uniform(.05, .4), rng.uniform(.6, 2.2)
        env += rng.uniform(.4, 1.0) * np.where(t < t0, 0, np.minimum(1, (t - t0) / a)) * np.exp(-np.maximum(0, t - t0 - a) / d)
    y = np.zeros((n, 2))
    for ch in range(2):
        b = dsp.noise(n, rng, "brown")
        r = dsp.lp(b, 260 / dist, order=2) + .5 * dsp.lp(b, 70, order=2)
        y[:, ch] = r * env * (1 + .3 * dsp.smooth(rng.standard_normal(n), .03))
    return norm(dsp.fade(y, .2, 1.0), .8)


def crickets(dur, rng, count=4):
    n = N(dur)
    y = np.zeros((n, 2))
    t = np.arange(n) / SR
    for c in range(count):
        f = rng.uniform(4200, 5200)
        per = rng.uniform(.45, .8)
        pulses = rng.integers(3, 5)
        car = np.sin(2 * np.pi * f * t + rng.random() * 6)
        gate = np.zeros(n)
        tc = rng.uniform(0, per)
        while tc < dur:
            for p in range(pulses):
                i = N(tc + p * .022)
                L = N(.012)
                if i + L < n:
                    gate[i:i + L] += np.hanning(L)
            tc += per * rng.uniform(.92, 1.08)
        a = rng.uniform(.3, 1.0) * (.6 + .4 * slow_random(n, rng, .1))
        y += dsp.pan(car * gate * a, rng.uniform(-.8, .8))
    return norm(dsp.lp(y, 7000), .3)


def cicadas(dur, rng):
    n = N(dur)
    y = np.zeros((n, 2))
    t = np.arange(n) / SR
    for c in range(3):
        f = rng.uniform(5500, 7500)
        am = .5 + .5 * np.sin(2 * np.pi * rng.uniform(80, 140) * t)
        sw = slow_random(n, rng, .15, .2, 1.0)
        sig = dsp.bp(rng.standard_normal(n), f, q=6) * am * sw
        y += dsp.pan(sig, rng.uniform(-.7, .7))
    return norm(y, .25)


def birds(dur, rng, density=.6):
    n = N(dur)
    y = np.zeros((n, 2))
    nb = max(1, int(dur * density))
    for _ in range(nb):
        t0 = rng.uniform(0, max(.1, dur - 1.5))
        base = rng.uniform(2200, 4800)
        notes = rng.integers(2, 7)
        tt = t0
        p = rng.uniform(-.9, .9)
        amp = rng.uniform(.2, 1.0)
        kind = rng.integers(0, 3)
        for k in range(notes):
            L = rng.uniform(.04, .14)
            m = N(L)
            u = np.linspace(0, 1, m)
            if kind == 0:
                f = base * (1 + .35 * u)
            elif kind == 1:
                f = base * (1.3 - .4 * u)
            else:
                f = base * (1 + .15 * np.sin(2 * np.pi * u * rng.uniform(2, 5)))
            ph = 2 * np.pi * np.cumsum(f) / SR
            s = np.sin(ph) * np.sin(np.pi * u) ** 2 * amp
            i = N(tt)
            if i + m < n:
                y[i:i + m] += dsp.pan(s, p)
            tt += L + rng.uniform(.03, .12)
    return norm(dsp.lp(y, 9000), .3)


def water_roar(dur, rng):
    n = N(dur)
    y = np.zeros((n, 2))
    surge = slow_random(n, rng, .25, .5, 1.0)
    for ch in range(2):
        b = dsp.noise(n, rng, "brown")
        p = dsp.noise(n, rng, "pink")
        roar = dsp.lp(b, 500, order=2) * 1.0 + dsp.bp(p, 900, q=.6) * .5
        spray = dsp.hp(p, 2500) * slow_random(n, rng, .5, .1, 1.0) ** 2 * .35
        y[:, ch] = (roar * surge + spray)
    return norm(y, .6)


def fire(dur, rng, size=1.0):
    n = N(dur)
    y = np.zeros((n, 2))
    for ch in range(2):
        b = dsp.noise(n, rng, "brown")
        roar = dsp.bp(b, 300, q=.5) * (.6 + .4 * slow_random(n, rng, 2.0)) * .5 * size
        cr = grains(dur, rng, 9 * size, 1200, 6000, (.001, .006), (.2, 1.0))
        pops = grains(dur, rng, .8 * size, 500, 2500, (.004, .02), (.6, 1.4))
        y[:, ch] = roar + cr * 1.2 + pops
    return norm(y, .5)


def candle(dur, rng):
    n = N(dur)
    b = dsp.noise(n, rng, "brown")
    flut = slow_random(n, rng, 6.0, .2, 1.0) ** 2
    y = dsp.bp(b, 160, q=.7) * flut
    y += .25 * grains(dur, rng, 1.2, 1500, 5000, (.001, .004), (.2, .6))
    return norm(dsp.stereo(y) * [1, .9], .2)


def room_tone(dur, rng, lp=300):
    n = N(dur)
    y = np.stack([dsp.lp(dsp.noise(n, rng, "pink"), lp, order=2) for _ in range(2)], 1)
    return norm(y, .15)


def footsteps(dur, rng, people=6, period=(.5, .65), soft=1.0, wet=False):
    n = N(dur)
    y = np.zeros((n, 2))
    for k in range(people):
        per = rng.uniform(*period)
        p = rng.uniform(-.8, .8)
        amp = rng.uniform(.3, 1.0)
        t = rng.uniform(0, per)
        while t < dur - .2:
            g = grains(.12, rng, 220, 300 if not wet else 600, 3500, (.002, .01), (.3, 1.))
            th = dsp.lp(rng.standard_normal(N(.05)), 220) * np.exp(-np.linspace(0, 5, N(.05)))
            s = g * .7
            s[:len(th)] += th * 2.5
            if wet:
                s += .3 * dsp.bp(rng.standard_normal(len(s)), 1500, 1.5) * np.exp(-np.linspace(0, 4, len(s)))
            i = N(t)
            m = min(len(s), n - i)
            y[i:i + m] += dsp.pan(s[:m] * amp * soft, p)
            t += per * rng.uniform(.9, 1.1)
    return norm(dsp.lp(y, 6000), .5)


def cloth(dur, rng, bright=1.0):
    n = N(dur)
    w = rng.standard_normal(n)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    gr = .5 + .5 * np.abs(dsp.smooth(rng.standard_normal(n), .006)) * 6
    y = dsp.bp(w, 1800 * bright, q=.6) * e * np.clip(gr, 0, 2)
    return norm(y, .5)


# ============================================================================ creatures
def vocalize(dur, rng, f0pts, fpts, amp_pts, rough=.5, rough_rate=30, noise_amt=.3, sub=.3,
             jitter=.03, fmax=6000, rolloff=1.0, q=(5, 6, 7, 8)):
    """Animal vocalisation: harmonic source with f0 contour -> time-varying formants."""
    n = N(dur)
    f0 = curve(n, f0pts)
    src = harmonic_source(f0, rng, jitter=jitter, sub=sub, fmax=fmax, rolloff=rolloff)
    rr = rough_rate * (1 + .3 * dsp.smooth(rng.standard_normal(n), .02))
    am = 1 + rough * np.sin(2 * np.pi * np.cumsum(rr) / SR)
    src = src * am + noise_amt * rng.standard_normal(n) * (.5 + .5 * am)
    fl = [curve(n, [(u, v[i]) for u, v in fpts]) for i in range(len(fpts[0][1]))]
    y = formants(src, fl, gains=[1.0, .7, .45, .3][:len(fl)], q=list(q)[:len(fl)])
    y *= curve(n, amp_pts)
    return norm(y, 1.0)


def lion_roar(rng, dur=2.0):
    y = vocalize(dur, rng,
                 f0pts=[(0, 120), (.12, 200), (.35, 175), (.75, 110), (1, 70)],
                 fpts=[(0, (380, 850, 2100, 3000)), (.25, (560, 1150, 2400, 3300)),
                       (.7, (420, 900, 2200, 3100)), (1, (300, 650, 1900, 2800))],
                 amp_pts=[(0, 0), (.06, .7), (.2, 1.0), (.55, .9), (.85, .4), (1, 0)],
                 rough=.65, rough_rate=27, noise_amt=.55, sub=.6, jitter=.05, rolloff=.85)
    y = dsp.filt(y, "lowshelf", 200, gain_db=6)
    return y


def lion_growl(rng, dur=2.4):
    return vocalize(dur, rng, f0pts=[(0, 62), (.4, 75), (1, 55)],
                    fpts=[(0, (280, 700, 1900)), (1, (260, 620, 1800))],
                    amp_pts=[(0, 0), (.2, .8), (.5, 1), (.8, .7), (1, 0)],
                    rough=.9, rough_rate=17, noise_amt=.7, sub=.5, jitter=.06)


def dog_growl(rng, dur=2.0):
    f = rng.uniform(85, 120)
    y = vocalize(dur, rng, f0pts=[(0, f * .9), (.3, f * 1.1), (.7, f), (1, f * .85)],
                 fpts=[(0, (550, 1350, 2600)), (.5, (650, 1500, 2800)), (1, (500, 1250, 2500))],
                 amp_pts=[(0, 0), (.1, .9), (.4, 1), (.6, .8), (.85, 1), (1, 0)],
                 rough=.85, rough_rate=rng.uniform(32, 45), noise_amt=.6, sub=.4, jitter=.05)
    return y


def dog_snarl(rng):
    f = rng.uniform(220, 330)
    return vocalize(.45, rng, f0pts=[(0, f), (.3, f * 1.25), (1, f * .8)],
                    fpts=[(0, (800, 1700, 3000)), (1, (700, 1500, 2800))],
                    amp_pts=[(0, 0), (.08, 1), (.6, .7), (1, 0)],
                    rough=.6, rough_rate=50, noise_amt=1.0, sub=.2, jitter=.08)


def dog_yelp(rng):
    f = rng.uniform(600, 900)
    return vocalize(.22, rng, f0pts=[(0, f), (.3, f * 1.4), (1, f * .7)],
                    fpts=[(0, (900, 2000, 3200)), (1, (800, 1800, 3000))],
                    amp_pts=[(0, 0), (.1, 1), (1, 0)], rough=.2, noise_amt=.4, sub=0)


def bull_snort(rng):
    n = N(.75)
    w = rng.standard_normal(n)
    e = env_ad(n, .015, .22)
    fl = 1 + .55 * np.sin(2 * np.pi * rng.uniform(35, 48) * np.arange(n) / SR)
    y = formants(w * fl, [280, 850, 2300], gains=[1, .6, .3], q=[2, 3, 4]) * e
    th = dsp.lp(rng.standard_normal(N(.2)), 120) * np.exp(-np.linspace(0, 6, N(.2)))
    y[:len(th)] += th * 1.2
    return norm(y, 1.0)


def bull_bellow(rng):
    return vocalize(2.2, rng, f0pts=[(0, 95), (.2, 110), (.7, 88), (1, 70)],
                    fpts=[(0, (420, 950, 2300)), (.6, (380, 800, 2100)), (1, (260, 600, 1900))],
                    amp_pts=[(0, 0), (.15, .8), (.5, 1), (.85, .6), (1, 0)],
                    rough=.45, rough_rate=22, noise_amt=.35, sub=.5, jitter=.03)


def hoof(rng, power=1.0):
    n = N(.25)
    t = np.arange(n) / SR
    f = rng.uniform(60, 95)
    thud = np.sin(2 * np.pi * f * t * (1 - .3 * t)) * np.exp(-t / .05)
    hit = dsp.bp(rng.standard_normal(n), rng.uniform(250, 600), q=.8) * np.exp(-t / .03)
    dirt = grains(.25, rng, 160, 400, 4000, (.002, .008), (.1, .5)) * np.exp(-t / .08)
    return (thud * 1.4 + hit * .8 + dirt) * power


def hooves(dur, rng, bulls=3):
    n = N(dur)
    y = np.zeros((n, 2))
    for b in range(bulls):
        per = rng.uniform(1.0, 1.35)
        ph0 = rng.uniform(0, 2 * np.pi)
        w = rng.uniform(.25, .45) * (1 if b % 2 else -1)
        t = rng.uniform(0, per)
        dist = rng.uniform(.5, 1.0)
        while t < dur - .3:
            for off in (0, .27, .5, .77):
                tt = t + off * per + rng.normal(0, .015)
                p = np.sin(ph0 + 2 * np.pi * w * tt / 6)
                h = hoof(rng, dist * rng.uniform(.6, 1.0))
                place_st(y, dsp.pan(h, .85 * p), tt)
            t += per
    return norm(y, .8)


def boxsmooth(x, L):
    """Centred moving average of length 2L+1 (cumsum, O(n))."""
    if L < 1:
        return x
    c = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(len(x))
    a = np.clip(i - L, 0, len(x))
    b = np.clip(i + L + 1, 0, len(x))
    return (c[b] - c[a]) / (b - a)


def place_st(buf, x, t):
    return dsp.place(buf, x, t)


# ============================================================================ objects / foley
def water_pour(rng, dur=3.4, slow=.75):
    n = N(dur)
    y = np.zeros(n)
    t = np.arange(n) / SR
    env = curve(n, [(0, 0), (.08, 1), (.6, 1), (.75, .5), (1, 0)])
    # stream bubbles
    k = int(260 * dur)
    for _ in range(k):
        f0 = np.exp(rng.uniform(np.log(700), np.log(3800))) * slow
        L = N(.04)
        tt = np.arange(L) / SR
        d = .13 * f0 + .0072 * f0 ** 1.5
        s = np.sin(2 * np.pi * f0 * tt * (1 + .1 * d * tt)) * np.exp(-d * tt)
        i = rng.integers(0, n - L)
        y[i:i + L] += s * rng.uniform(.05, .3) * env[i]
    # glugs from the jar
    tg = .1
    while tg < dur * .65:
        f0 = rng.uniform(220, 420) * slow
        L = N(.12)
        tt = np.arange(L) / SR
        s = np.sin(2 * np.pi * f0 * tt * (1 + 2.0 * tt)) * np.exp(-tt / .035)
        dsp.place(y, s * .7, tg)
        tg += rng.uniform(.18, .3) / slow
    hiss = dsp.bp(rng.standard_normal(n), 2500, q=.5) * env * .25
    y += hiss
    # splash on the dry ground + trickle into cracks
    sp = N(.8)
    s = dsp.lp(rng.standard_normal(sp), 3500) * env_ad(sp, .01, .18)
    dsp.place(y, s * .8, .35)
    y += grains(dur, rng, 40, 1500, 6000, (.002, .01), (.1, .4)) * curve(n, [(0, 0), (.2, 1), (1, .2)])
    return norm(y, 1.0)


def creak(rng, dur=1.6):
    n = N(dur)
    y = np.zeros(n)
    rate = curve(n, [(0, 18), (.3, 45), (.7, 30), (1, 15)]) * (1 + .2 * dsp.smooth(rng.standard_normal(n), .02))
    ph = np.cumsum(rate) / SR
    imp = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (1 + .5 * rng.standard_normal(n))
    for f, g in ((190, 1.0), (430, .8), (780, .6), (1450, .35), (2600, .2)):
        y += g * dsp.bp(imp, f * rng.uniform(.95, 1.05), q=12)
    y *= curve(n, [(0, 0), (.1, 1), (.8, .8), (1, 0)])
    return norm(y, 1.0)


def hammer_iron(rng):
    f0 = 1080
    ratios = [1, 2.76, 5.40, 8.93, 13.34]
    y = modal([f0 * r for r in ratios], [1, .55, .35, .22, .12], [.32, .2, .13, .09, .06], 1.2, rng, .01)
    n = len(y)
    t = np.arange(n) / SR
    click = dsp.bp(rng.standard_normal(n), 4500, q=.7) * np.exp(-t / .004)
    thud = dsp.lp(rng.standard_normal(n), 300, order=2) * np.exp(-t / .06) + np.sin(2 * np.pi * 140 * t) * np.exp(-t / .08)
    return norm(y * .7 + click * .9 + thud * 1.2, 1.0)


def dice(rng, slow=1.5):
    dur = 1.6 * slow
    n = N(dur)
    y = np.zeros((n, 2))
    for d in range(2):
        t = rng.uniform(0, .05)
        gap = rng.uniform(.16, .2) * slow
        amp = 1.0
        p = rng.uniform(-.3, .3)
        while gap > .012 and t < dur - .05:
            L = N(.03)
            tt = np.arange(L) / SR
            f = rng.uniform(2400, 3800) / (slow ** .3)
            s = (dsp.bp(rng.standard_normal(L), f, q=3) * np.exp(-tt / .006) +
                 .4 * np.sin(2 * np.pi * f * 1.1 * tt) * np.exp(-tt / .012)) * amp
            dsp.place(y, dsp.pan(s, p), t)
            t += gap
            gap *= rng.uniform(.68, .82)
            amp *= .82
    y += .15 * dsp.stereo(dsp.bp(rng.standard_normal(n), 1800, .7) * curve(n, [(0, 0), (.05, 1), (.6, .3), (1, 0)]))
    return norm(y, 1.0)


def sword_drop(rng):
    dur = 2.5
    n = N(dur)
    y = np.zeros(n)
    fr = [420, 1135, 2190, 3560, 5230, 7310]
    ring = modal(fr, [.5, .7, .55, .4, .3, .2], [.5, .38, .28, .2, .14, .1], dur, rng, .01)
    ring2 = modal([f * 1.013 for f in fr], [.4, .5, .4, .3, .2, .15], [.3, .25, .2, .15, .1, .08], dur, rng, .01)
    dsp.place(y, ring * .6, 0)
    dsp.place(y, ring2[:n - N(.085)] * .5, .085)
    t = np.arange(n) / SR
    thud = dsp.lp(rng.standard_normal(n), 400, order=2) * np.exp(-t / .07)
    dust = dsp.lp(dsp.noise(n, rng, "pink"), 2500) * curve(n, [(0, 0), (.02, .5), (.3, .15), (1, 0)])
    y += thud * 1.2 + dust * .5
    return norm(y, 1.0)


def metal_clink(rng):
    f0 = rng.uniform(1800, 2900)
    y = modal([f0, f0 * 2.32, f0 * 3.9, f0 * 5.3], [1, .6, .35, .2], [.35, .22, .12, .08], .9, rng, .01)
    n = len(y)
    t = np.arange(n) / SR
    y += dsp.lp(rng.standard_normal(n), 900) * np.exp(-t / .03) * 1.5
    return norm(y, 1.0)


def bread_tear(rng):
    dur = .9
    n = N(dur)
    y = grains(dur, rng, 160, 2000, 7500, (.001, .005), (.2, 1.0))
    y += .4 * dsp.bp(rng.standard_normal(n), 1200, .7) * curve(n, [(0, 0), (.15, 1), (.7, .6), (1, 0)])
    return norm(y, 1.0)


def earthquake(dur, rng, peak=.55):
    n = N(dur)
    env = curve(n, [(0, 0), (peak * .6, .5), (peak, 1.0), (peak + .15, .7), (1, 0)])
    y = np.zeros((n, 2))
    for ch in range(2):
        b = dsp.noise(n, rng, "brown")
        sub = dsp.lp(b, 55, order=2) * 2.0
        mid = dsp.lp(b, 260, order=2)
        am = .6 + .4 * slow_random(n, rng, 3.0)
        deb = grains(dur, rng, 70, 500, 4500, (.002, .015), (.1, 1.)) * env ** 2
        y[:, ch] = (sub + mid * .8) * am * env + deb * .6
    return norm(y, 1.0)


def stone_roll(rng, dur=3.6):
    n = N(dur)
    t = np.arange(n) / SR
    rot = curve(n, [(0, 1.4), (1, .5)])
    am = .55 + .45 * np.abs(np.sin(np.pi * np.cumsum(rot) / SR))
    env = curve(n, [(0, 0), (.08, 1), (.8, .8), (.93, .3), (1, 0)])
    b = dsp.noise(n, rng, "brown")
    grind = dsp.bp(dsp.noise(n, rng, "pink"), 380, q=.9) * .7 + dsp.lp(b, 150, order=2)
    grav = grains(dur, rng, 90, 600, 5000, (.002, .012), (.1, 1.0))
    y = (grind * am + grav * .5) * env
    # final settling thud
    L = N(.6)
    tt = np.arange(L) / SR
    th = (np.sin(2 * np.pi * 48 * tt) + dsp.lp(rng.standard_normal(L), 250)) * np.exp(-tt / .12)
    dsp.place(y, th * 1.6, dur - .55)
    return norm(dsp.stereo(y), 1.0)


def disintegrate(rng, dur=3.0):
    n = N(dur)
    y = np.zeros((n, 2))
    env = curve(n, [(0, 0), (.15, 1), (.6, .7), (1, 0)])
    for ch in range(2):
        g = grains(dur, rng, 900, 2500, 11000, (.001, .004), (.05, .5))
        s = dsp.hp(dsp.noise(n, rng, "pink"), 1800) * .3
        y[:, ch] = (g + s) * env * tv_biquad(np.ones(n), "lp", curve(n, [(0, 12000), (1, 4000)]))
    return norm(y, 1.0)


# ============================================================================ transitions
def whoosh(dur, rng, f0=250, f1=4000, peak=.8, kind="rise"):
    n = N(dur)
    u = np.linspace(0, 1, n)
    if kind == "rise":
        env = np.where(u < peak, (u / peak) ** 2.5, np.exp(-(u - peak) / (1 - peak) * 4))
        fc = f0 * (f1 / f0) ** np.clip(u / peak, 0, 1)
    else:   # fall
        env = np.where(u < .25, u / .25, np.exp(-(u - .25) * 3))
        fc = f1 * (f0 / f1) ** u
    y = np.zeros((n, 2))
    for ch in range(2):
        w = dsp.noise(n, rng, "pink")
        y[:, ch] = tv_biquad(w, "bp", fc, q=1.2) * env
    return norm(y, 1.0)


def bloom(dur, rng):
    """Bright shimmer after a white flash."""
    n = N(dur)
    t = np.arange(n) / SR
    y = np.zeros((n, 2))
    for ch in range(2):
        s = dsp.hp(dsp.noise(n, rng, "pink"), 3000) * np.exp(-t / (dur * .35))
        tone = sum(np.sin(2 * np.pi * f * t + rng.random() * 6) for f in (1174.7, 1760.0, 2349.3)) * .05 * np.exp(-t / (dur * .4))
        y[:, ch] = s * .5 + tone
    return norm(dsp.fade(y, .02, .5), 1.0)


def sub_boom(rng, dur=3.0, f=42):
    n = N(dur)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t * (1 - .15 * t / dur)) * np.exp(-t / .9)
    y += dsp.lp(rng.standard_normal(n), 120, order=2) * np.exp(-t / .5) * .6
    return norm(dsp.stereo(dsp.fade(y, .005, .3)), 1.0)


# ============================================================================ crowd (TTS)
CROWD_LINES = [
    "Hoshia et atzmekha!", "Red min ha tzlav!", "Melekh ha yehudim!", "Acherim hoshia, et atzmo lo yukhal.",
    "Batach ba Adonai, yatzilehu!", "Re'u oto! Ha!", "Ha ha!", "Im ata ben Elohim, red!",
    "Mah zeh? Mah hu omer?", "Ken, ken, ze hu.", "Lo, lo! Hu lo!", "Tiru, tiru!",
]
CROWD_VOICES = ["am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_onyx", "am_puck",
                "bm_george", "bm_lewis", "bm_daniel", "af_sarah", "bf_emma"]


def crowd_clips():
    os.makedirs(CACHE, exist_ok=True)
    clips = []
    todo = []
    for vi, v in enumerate(CROWD_VOICES):
        for li in range(3):
            line = CROWD_LINES[(vi * 5 + li * 7) % len(CROWD_LINES)]
            sp = 1.0 + .12 * ((vi + li) % 3)
            path = os.path.join(CACHE, "crowd_%s_%d.wav" % (v, li))
            todo.append((path, v, line, sp))
    missing = [x for x in todo if not os.path.exists(x[0])]
    if missing:
        try:
            from kokoro_onnx import Kokoro
            k = Kokoro("/opt/assets/tts/kokoro-v1.0.onnx", "/opt/assets/tts/voices-v1.0.bin")
            for path, v, line, sp in missing:
                s, sr = k.create(line, voice=v, speed=sp, lang="en-us")
                y = resample_poly(np.asarray(s, dtype=float), SR // 1000, sr // 1000)
                dsp.write(path, y, "PCM_16")
        except Exception as e:   # no TTS available: fall back to a noise murmur
            print("WARNING: crowd TTS unavailable (%s) - using synthetic murmur" % e)
            return []
    for path, *_ in todo:
        clips.append(dsp.read(path))
    return clips


def murmur(dur, rng, clips, density=7.0, lpf=2200, spread=.9):
    n = N(dur)
    y = np.zeros((n, 2))
    if not clips:
        w = np.stack([dsp.bp(dsp.noise(n, rng, "pink"), 500, .8) for _ in range(2)], 1)
        return norm(w * (.6 + .4 * slow_random(n, rng, 3.0))[:, None], .4)
    k = int(dur * density)
    for _ in range(k):
        c = clips[rng.integers(len(clips))]
        rate = rng.uniform(.88, 1.1)
        c = resample_poly(c, 100, int(100 * rate))
        g = 10 ** (rng.uniform(-14, 0) / 20)
        dsp.place(y, dsp.pan(c * g, rng.uniform(-spread, spread)), rng.uniform(-1, dur))
    y = dsp.lp(dsp.hp(y, 180), lpf, order=2)
    return norm(y, .6)


def jeer(rng, clips, which):
    if not clips:
        return np.zeros((N(.5), 2))
    c = clips[which % len(clips)]
    c = resample_poly(c, 100, int(100 * rng.uniform(.95, 1.05)))
    c = dsp.filt(dsp.hp(c, 200), "peak", 2500, q=1, gain_db=3)
    return norm(dsp.pan(c, rng.uniform(-.6, .6)), 1.0)


# ============================================================================ the cue sheet
# Ambience layers: gain in dB per shot id (missing shot = silent). Crossfade between shots.
AMB = {
    "wind": dict(gen="wind", xf=1.2, args=dict(center=520, gust=.2, howl=.3, dust=.15),
                 shots={"s00": -10, "s01a": -11, "s01b": -8, "s02a": -12, "s05": -12, "s06a": -16, "s06b": -16,
                        "s07b": -13, "s09a": -6, "s09b": -9, "s11b": -8, "s12a": -11, "s12b": -13,
                        "s13a": -12, "s13b": -13, "s14a": -14, "s14b": -18, "s14c": -18}),
    "breeze": dict(gen="wind", xf=1.5, args=dict(center=900, gust=.15, howl=.0, dust=.0, depth=.4),
                   shots={"s02b": -18, "s08": -20, "s15": -24, "s16a": -16, "s16b": -20, "s16c": -20, "s18b": -16,
                          "s19a": -20, "s19b": -18, "s20b": -20, "s20c": -15}),
    "dry": dict(gen="wind", xf=1.0, args=dict(center=1400, gust=.3, howl=.0, dust=.4, depth=.5),
                shots={"s11a": -15}),
    "thunder": dict(gen="thunder_bed", xf=2.0, args={},
                    shots={"s01b": -8, "s02a": -14, "s05": -12, "s06a": -16, "s06b": -16, "s09a": -10, "s09b": -12,
                           "s12a": -12, "s13a": -12, "s13b": -14}),
    "crickets": dict(gen="crickets", xf=1.0, args=dict(count=5),
                     shots={"s02b": -20, "s08": -24, "s20a": -26, "s20b": -22}),
    "cicadas": dict(gen="cicadas", xf=.8, args={}, shots={"s11a": -24}),
    "birds": dict(gen="birds", xf=1.5, args=dict(density=.7),
                  shots={"s15": -22, "s16a": -18, "s16b": -22, "s16c": -20, "s18b": -20, "s19a": -24, "s20c": -18}),
    "water": dict(gen="water_roar", xf=.25, args={}, shots={"s04a": -7, "s04b": -10}),
    "room": dict(gen="room_tone", xf=.6, args={}, shots={"s03": -20, "s07a": -22, "s10b": -24, "s17b": -24}),
    "fire": dict(gen="fire", xf=.8, args=dict(size=1.0), shots={"s20a": -10}),
    "torches": dict(gen="fire", xf=.8, args=dict(size=.6), shots={"s08": -14}),
    "candle": dict(gen="candle", xf=.5, args={}, shots={"s10b": -14}),
    "lamps": dict(gen="fire", xf=1.0, args=dict(size=.3), shots={"s17a": -24, "s17b": -24}),
    "crowd": dict(gen="murmur", xf=.8, args=dict(density=9),
                  shots={"s06a": -10, "s06b": -11, "s13a": -20, "s13b": -24}),
    "assembly": dict(gen="murmur", xf=1.5, args=dict(density=12, lpf=1500, spread=1.0),
                     shots={"s16a": -24, "s17a": -26}),
    "mob": dict(gen="footsteps", xf=.8, args=dict(people=10, period=(.45, .6)), shots={"s08": -16}),
    "seabed": dict(gen="footsteps", xf=.5, args=dict(people=12, period=(.5, .7), wet=True), shots={"s04a": -20}),
    "soldiers": dict(gen="footsteps", xf=.5, args=dict(people=3, period=(.6, .75)), shots={"s12a": -18}),
}

# Spot effects: (shot, anchor, offset s, generator, gain dB, pan, stem)
#   anchor: "start" | "end" | float fraction of the shot | ("ph", k, "start"/"end") = k-th phrase
#   of the shot's block (k counts from 0 in the block)
FX = [
    ("s00", "start", 2.3, "thunder", -6, -.4, "fx"),            # storm front creeping in
    ("s01b", "start", .4, "thunder", -9, .3, "fx"),              # sky turns dark at midday
    ("s02a", .6, 0, "thunder", -16, -.5, "fx"),
    ("s03", "start", .05, "curtain", -10, .0, "fx"),            # parting the temple curtain
    ("s04b", "end", -1.9, "water_crash", -6, .0, "fx"),          # walls of water crash together
    ("s05", "start", 1.0, "steps_by", -11, .0, "fx"),            # sandaled feet stride past
    ("s05", .55, 0, "steps_by", -12, .3, "fx"),
    ("s06a", ("ph", 1, "end"), .05, "jeer:0", -14, -.4, "fx"),
    ("s06b", "start", .05, "jeer:1", -15, .4, "fx"),
    ("s06b", ("ph", 4, "end"), .1, "jeer:2", -12, -.2, "fx"),
    ("s07a", .3, 0, "ox_breath", -16, .5, "fx"),
    ("s07a", .7, 0, "straw", -18, -.4, "fx"),
    ("s08", ("ph", 0, "end"), -.1, "thunder", -18, .5, "fx"),
    ("s09a", "start", 0, "hooves", -7, .0, "fx"),
    ("s09a", ("ph", 0, "end"), .1, "snort", -8, -.5, "fx"),
    ("s09a", ("ph", 1, "start"), 1.4, "bellow", -12, .5, "fx"),
    ("s09a", ("ph", 1, "end"), .05, "snort", -7, .4, "fx"),
    ("s09b", "start", 0, "lion_growl", -9, .2, "fx"),
    ("s09b", ("ph", 3, "end"), -.05, "lion_roar", -6, .0, "fx"),  # after "...mouths wide against me."
    ("s10a", "start", .1, "water_pour", -10, .0, "fx"),
    ("s10a", ("ph", 1, "start"), .3, "creak", -11, .2, "fx"),     # bones out of joint
    ("s11b", "start", .2, "dust_gust", -7, -.6, "fx"),
    ("s12a", "start", .1, "dogs", -6, .0, "fx"),
    ("s12b", ("ph", 1, "start"), HAMMER_OFFSET, "hammer", -4, .1, "fx"),
    ("s13b", ("ph", 3, "start"), -.25, "dice", -7, .0, "fx"),
    ("s13b", ("ph", 3, "end"), .15, "snatch", -16, .3, "fx"),
    ("s14b", "start", .25, "sword", -4, -.1, "fx"),
    ("s14b", ("ph", 3, "end"), -.6, "dogs_scatter", -10, .3, "fx"),
    ("s14c", .2, 0, "disintegrate", -10, -.3, "fx"),
    ("s14c", .45, 0, "disintegrate", -11, .4, "fx"),
    ("s15", "start", -2.4, "earthquake", 2, .0, "fx"),          # peaks on the white flash
    ("s15", "start", .2, "stone", -9, .2, "fx"),
    ("s17b", "start", .5, "bread", -10, .0, "fx"),
    ("s19a", .15, 0, "clink", -11, -.3, "fx"),
    ("s19a", .45, 0, "clink", -12, .3, "fx"),
    ("s19a", .75, 0, "clink", -13, .0, "fx"),
    ("s19b", .2, 0, "kneel", -12, .0, "fx"),
    ("s20c", .25, 0, "linen", -16, .3, "fx"),
]
# transitions: generated automatically from timeline transition_in (+ the final swell)
TRANS_GAIN = {"flash": -9, "fade_black": -15, "dissolve": -26}


def make_fx(kind, rng, clips):
    if kind == "thunder":
        return thunder(rng.uniform(6, 9), rng, dist=1.4)
    if kind == "curtain":
        return dsp.stereo(dsp.lp(cloth(1.4, rng, .6), 3000))
    if kind == "water_crash":
        n = N(4)
        t = np.arange(n) / SR
        y = water_roar(4, rng) * np.exp(-t / 1.2)[:, None] * 1.4
        y += sub_boom(rng, 4, 38) * .8
        return dsp.fade(norm(y, 1.), .25, 1.0)
    if kind == "steps_by":
        return footsteps(1.8, rng, people=1, period=(.48, .52)) * curve(N(1.8), [(0, 0), (.5, 1), (1, 0)])[:, None]
    if kind.startswith("jeer:"):
        return jeer(rng, clips, int(kind.split(":")[1]) * 7 + 3)
    if kind == "ox_breath":
        n = N(1.6)
        y = dsp.lp(rng.standard_normal(n), 900) * curve(n, [(0, 0), (.3, 1), (.5, .2), (.8, .7), (1, 0)])
        return dsp.stereo(norm(y, 1.))
    if kind == "straw":
        return dsp.stereo(dsp.hp(cloth(1.0, rng, 1.6), 1500))
    if kind == "hooves":
        return hooves(6.0, rng, bulls=3) * curve(N(6), [(0, .5), (.15, 1), (.85, 1), (1, 0)])[:, None]
    if kind == "snort":
        return dsp.stereo(bull_snort(rng))
    if kind == "bellow":
        return dsp.stereo(dsp.lp(bull_bellow(rng), 3000))
    if kind == "lion_growl":
        return dsp.stereo(lion_growl(rng))
    if kind == "lion_roar":
        return dsp.stereo(lion_roar(rng))
    if kind == "water_pour":
        return dsp.stereo(water_pour(rng))
    if kind == "creak":
        return dsp.stereo(creak(rng))
    if kind == "dust_gust":
        y = wind(3.5, rng, center=1600, gust=1.2, howl=0, dust=1.0, depth=.9)
        return y * curve(N(3.5), [(0, 0), (.3, 1), (1, 0)])[:, None]
    if kind == "dogs":
        y = np.zeros((N(4.6), 2))
        for i, (t0, p) in enumerate(((0, -.6), (.7, .5), (1.6, -.1), (2.4, .7), (3.0, -.5))):
            g = dog_growl(rng, rng.uniform(1.4, 2.2)) * rng.uniform(.6, 1.0)
            dsp.place(y, dsp.pan(g, p), t0)
        for t0 in (1.2, 2.9):
            dsp.place(y, dsp.pan(dog_snarl(rng) * .7, rng.uniform(-.7, .7)), t0)
        return norm(y, 1.)
    if kind == "dogs_scatter":
        y = footsteps(1.2, rng, people=4, period=(.12, .16)) * .5
        dsp.place(y, dsp.pan(dog_yelp(rng), -.5), .2)
        dsp.place(y, dsp.pan(dog_yelp(rng) * .7, .6), .55)
        return norm(y, 1.)
    if kind == "hammer":
        return dsp.stereo(hammer_iron(rng))
    if kind == "dice":
        return dice(rng)
    if kind == "snatch":
        return dsp.stereo(cloth(.5, rng, 1.2))
    if kind == "sword":
        return dsp.stereo(sword_drop(rng))
    if kind == "disintegrate":
        return disintegrate(rng)
    if kind == "earthquake":
        return earthquake(6.5, rng, peak=.38)
    if kind == "stone":
        return stone_roll(rng)
    if kind == "bread":
        return dsp.stereo(bread_tear(rng))
    if kind == "clink":
        return dsp.stereo(metal_clink(rng))
    if kind == "kneel":
        y = cloth(1.2, rng, .8)
        n = len(y)
        t = np.arange(n) / SR
        y += dsp.lp(rng.standard_normal(n), 250) * np.exp(-np.maximum(0, t - .6) / .05) * (t > .6) * .8
        y += grains(1.2, rng, 60, 800, 4000, (.002, .01), (.1, .4)) * (t > .6)
        return dsp.stereo(norm(y, 1.))
    if kind == "linen":
        n = N(5)
        y = dsp.bp(rng.standard_normal(n), 1100, .5) * (.5 + .5 * np.abs(np.sin(2 * np.pi * 1.7 * np.arange(n) / SR))) ** 3
        return dsp.stereo(dsp.fade(norm(y, 1.), 1.0, 1.5))
    raise ValueError(kind)


def make_amb(gen, dur, rng, args, clips):
    if gen == "wind":
        return wind(dur, rng, **args)
    if gen == "thunder_bed":
        y = np.zeros((N(dur), 2))
        t = rng.uniform(0, 3)
        while t < dur:
            th = thunder(rng.uniform(5, 8), rng, dist=rng.uniform(1.5, 2.5))
            dsp.place(y, th * rng.uniform(.4, 1.0), t)
            t += rng.uniform(7, 13)
        y += np.stack([dsp.lp(dsp.noise(N(dur), rng, "brown"), 60, order=2) for _ in range(2)], 1) * .08
        return y
    if gen == "crickets":
        return crickets(dur, rng, **args)
    if gen == "cicadas":
        return cicadas(dur, rng)
    if gen == "birds":
        return birds(dur, rng, **args)
    if gen == "water_roar":
        return water_roar(dur, rng)
    if gen == "room_tone":
        return room_tone(dur, rng)
    if gen == "fire":
        return fire(dur, rng, **args)
    if gen == "candle":
        return candle(dur, rng)
    if gen == "murmur":
        return murmur(dur, rng, clips, **args)
    if gen == "footsteps":
        return footsteps(dur, rng, **args)
    raise ValueError(gen)


# ============================================================================ build
def resolve(T, shot, anchor, offset):
    s = T["shot"][shot]
    if anchor == "start":
        t = s["t0"]
    elif anchor == "end":
        t = s["t1"]
    elif isinstance(anchor, (int, float)):
        t = s["t0"] + anchor * (s["t1"] - s["t0"])
    else:
        _, k, which = anchor
        ph = T["blocks"][s["block"]]["phrases"]
        t = ph[min(k, len(ph) - 1)][which]
    return t + offset


def main():
    T = dsp.load_timing()
    total = T["total"]
    n = N(total)
    stems = {k: np.zeros((n, 2)) for k in ("amb", "fx", "trans")}
    clips = crowd_clips()
    outdoor = dsp.hall_ir(rt60=1.3, predelay=.012, seed=31, bright=.7, width=1.0)
    small = dsp.hall_ir(rt60=.6, predelay=.006, seed=32, bright=.8)
    big = dsp.hall_ir(rt60=2.6, predelay=.03, seed=33)
    cues = []

    # ---------------- ambience layers
    shots = T["shots"]
    for name, L in AMB.items():
        gains = np.full(n, -120.0)
        for s in shots:
            if s["id"] in L["shots"]:
                a, b = N(s["t0"]), N(s["t1"])
                gains[a:b] = L["shots"][s["id"]]
        if gains.max() <= -100:
            continue
        lin = dsp.undb(gains)
        lin[gains <= -100] = 0
        # equal crossfade ramps at shot changes
        lin = boxsmooth(boxsmooth(lin, N(L["xf"] / 2)), N(L["xf"] / 2))
        on = np.where(lin > 1e-4)[0]
        # generate only over active spans (merge gaps < 2 s)
        spans = []
        i0 = on[0]
        prev = on[0]
        for i in on[1:]:
            if i - prev > 2 * SR:
                spans.append((i0, prev))
                i0 = i
            prev = i
        spans.append((i0, prev))
        for (a, b) in spans:
            rng = R((name, a))
            dur = (b - a) / SR + .05
            y = make_amb(L["gen"], dur, rng, L.get("args", {}), clips)
            y = dsp.stereo(y)[:b - a]
            y = y * lin[a:a + len(y), None]
            stems["amb"][a:a + len(y)] += y
            cues.append({"type": "amb", "layer": name, "start": round(a / SR, 2), "end": round(b / SR, 2)})
    stems["amb"] = dsp.reverb(stems["amb"], outdoor, wet=.18, dry=1.0)

    # ---------------- spot effects
    for (shot, anchor, off, kind, gdb, p, stem) in FX:
        if shot not in T["shot"]:
            continue
        t = resolve(T, shot, anchor, off)
        rng = R((shot, kind, str(anchor), off))
        y = dsp.stereo(make_fx(kind, rng, clips))
        if p:
            m = y.mean(1)
            y = .35 * y + .65 * dsp.pan(m, p) * 1.2
        ir = small if kind in ("ox_breath", "straw", "bread", "curtain", "candle") else outdoor
        if kind in ("thunder", "earthquake", "lion_roar", "hammer", "sword"):
            ir = big if kind != "thunder" else outdoor
        y = dsp.reverb(np.concatenate([y, np.zeros((N(1.5), 2))]), ir, wet=.35, dry=1.0)
        dsp.place(stems[stem], y * dsp.undb(gdb), t)
        cues.append({"type": "fx", "kind": kind, "shot": shot, "time": round(t, 3), "gain_db": gdb})

    # ---------------- transitions
    for s in shots:
        tr = s["transition_in"]
        if tr not in TRANS_GAIN or s["t0"] <= 0:
            continue
        if tr == "flash" and abs(s["t0"] - T["phrases"][-1]["start"]) < 1.0:
            continue            # the final swell below covers the last flash
        rng = R(("tr", s["id"]))
        t = s["t0"]
        g = dsp.undb(TRANS_GAIN[tr])
        if tr == "flash":
            pre = 2.2
            w = whoosh(pre + .6, rng, 200, 6000, peak=pre / (pre + .6))
            dsp.place(stems["trans"], w * g, t - pre)
            dsp.place(stems["trans"], bloom(3.0, rng) * g * .6, t)
            dsp.place(stems["trans"], sub_boom(rng, 3.0) * g * .7, t)
        elif tr == "fade_black":
            w = whoosh(2.0, rng, 150, 2500, kind="fall")
            dsp.place(stems["trans"], w * g, t - 1.4)
            dsp.place(stems["trans"], sub_boom(rng, 3.5, 36) * g * .6, t - .3)
        elif tr == "dissolve":
            w = whoosh(1.6, rng, 400, 3000, peak=.55)
            dsp.place(stems["trans"], w * g, t - .9)
        cues.append({"type": "transition", "shot": s["id"], "kind": tr, "time": round(t, 3)})
    # final swell into "He has done it!" + bloom
    climax = T["phrases"][-1]["start"]
    rng = R("final")
    w = whoosh(4.6, rng, 120, 7000, peak=4.0 / 4.6)
    dsp.place(stems["trans"], w * dsp.undb(-12), climax - 4.0)
    dsp.place(stems["trans"], bloom(6.0, rng) * dsp.undb(-14), climax)
    cues.append({"type": "transition", "kind": "final_swell", "time": round(climax, 3)})
    stems["trans"] = dsp.reverb(stems["trans"], big, wet=.3, dry=1.0)

    # ---------------- write
    os.makedirs(os.path.join(OUT, "stems"), exist_ok=True)
    for k, y in stems.items():
        y = dsp.hp(y, 25, order=2)
        y = dsp.fade(y, 0.0, 2.0)
        stems[k] = y
        dsp.write(os.path.join(OUT, "stems", "sfx_%s.wav" % k), y)
    mix = sum(stems.values())
    dsp.write(os.path.join(OUT, "sfx.wav"), mix)
    json.dump({"cues": cues}, open(os.path.join(OUT, "sfx_cues.json"), "w"), indent=1)
    print("sfx.wav %.1f s, peak %.1f dBFS, %d cues" % (len(mix) / SR, dsp.db(np.max(np.abs(mix))), len(cues)))


if __name__ == "__main__":
    main()
