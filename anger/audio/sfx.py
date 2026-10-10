"""Synthesize every sound effect of "ANGER" with numpy -> build/sfx/<name>.wav (48 kHz stereo float).

    python3 audio/sfx.py                    # every effect
    python3 audio/sfx.py stomp drip ...     # just these

Everything is procedural (the machinery of ../if-you-have-time/audio/sfx.py, extended):
  * filtered / granular noise, swept and time-varying band-passes, pitch-dropping sine thumps;
  * modal hits: inharmonic exponentially-decaying partials for armor plates, blades, iron, wood, stone;
  * Poisson "crackle" (heavy-tailed impulse trains through short noise grains) for splinters, sparks,
    gravel, saliva and fire;
  * a Rosenberg glottal-pulse source (jitter, shimmer, diplophonia, breath noise gated by the glottal
    opening) through cascaded time-varying formant resonators (Klatt-style) for every vocal sound:
    the groan, throat clear, snore, giggle, snort, huff, growl and snarl;
  * a synthetic stereo cave reverb (pre-delay, early reflections, a tail that darkens as it decays).
Each effect seeds its own RNG from its name, so building one effect alone gives the same file as a full
build. *_loop effects are seamless: noise beds are crossfaded into themselves and event tails (drips,
pops, the snore's reverb) are folded around the loop point; the DC high-pass is applied circularly.
Every file is normalized to -3 dBFS peak; the mixer sets the final gain from the timeline.
"""
import sys
import zlib
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import SFX_DIR, SR  # noqa: E402

RNG = np.random.default_rng(0)
FRAME = 1 / 24


def reseed(name):
    global RNG
    RNG = np.random.default_rng(zlib.crc32(name.encode()))


# ============================================================================ building blocks

def N(d):
    return max(0, int(round(d * SR)))


def t_axis(d):
    return np.arange(N(d)) / SR


def noise(d, color="white"):
    x = RNG.standard_normal(N(d))
    if color == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
        a = [1, -2.494956002, 2.017265875, -0.522189400]
        x = signal.lfilter(b, a, x) * 8
    elif color == "brown":
        x = signal.lfilter([1.0], [1, -0.997], x) * 0.06
    return x


def _butter(kind, f, order):
    if kind == "band":
        lo, hi = max(f[0], 10.0), min(f[1], SR * 0.47)
        return signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.butter(order, min(max(f, 5.0), SR * 0.47), btype=kind, fs=SR, output="sos")


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_butter("band", (lo, hi), order), x, axis=0)


def lp(x, f, order=2):
    return signal.sosfilt(_butter("low", f, order), x, axis=0)


def hp(x, f, order=2):
    return signal.sosfilt(_butter("high", f, order), x, axis=0)


def _rbj(kind, f, q):
    w0 = 2 * np.pi * min(max(f, 10.0), SR * 0.45) / SR
    al = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    if kind == "bp":
        b = [al, 0.0, -al]
    elif kind == "lp":
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    else:
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    a = np.array([1 + al, -2 * c, 1 - al])
    return np.array(b) / a[0], a / a[0]


def rbp(x, f, q):
    """Static constant-peak (0 dB) band-pass biquad."""
    b, a = _rbj("bp", f, q)
    return signal.lfilter(b, a, x)


def tv_filter(x, f, q=0.707, kind="bp", block=64):
    """Time-varying RBJ biquad (bp / lp / hp); f and q are scalars or per-sample contours."""
    n = len(x)
    f = np.broadcast_to(np.asarray(f, float), (n,))
    q = np.broadcast_to(np.asarray(q, float), (n,))
    y = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        j = min(n, i + block)
        m = (i + j) // 2
        b, a = _rbj(kind, f[m], q[m])
        y[i:j], zi = signal.lfilter(b, a, x[i:j], zi=zi)
    return y


def _kl(f, bw):
    r = np.exp(-np.pi * bw / SR)
    B = 2 * r * np.cos(2 * np.pi * min(f, SR * 0.45) / SR)
    C = -r * r
    return np.array([1 - B - C, 0.0, 0.0]), np.array([1.0, -B, -C])


def reson(x, f, bw, block=64):
    """Klatt two-pole resonator (unity gain at DC) with optional per-sample frequency / bandwidth."""
    n = len(x)
    f = np.asarray(f, float)
    bw = np.asarray(bw, float)
    if f.ndim == 0 and bw.ndim == 0:
        b, a = _kl(float(f), float(bw))
        return signal.lfilter(b, a, x)
    f = np.broadcast_to(f, (n,))
    bw = np.broadcast_to(bw, (n,))
    y = np.empty(n)
    zi = np.zeros(2)
    for i in range(0, n, block):
        j = min(n, i + block)
        m = (i + j) // 2
        b, a = _kl(f[m], bw[m])
        y[i:j], zi = signal.lfilter(b, a, x[i:j], zi=zi)
    return y


# formant targets (male adult), (freq, bandwidth) for F1..F5
VOWELS = {
    "uh": [(620, 80), (1200, 90), (2450, 120), (3300, 200), (3900, 250)],
    "ah": [(730, 90), (1090, 100), (2440, 120), (3300, 200), (3900, 250)],
    "aw": [(570, 80), (840, 90), (2410, 120), (3300, 200), (3900, 250)],
    "oh": [(480, 70), (900, 90), (2400, 120), (3300, 200), (3900, 250)],
    "oo": [(320, 60), (850, 90), (2250, 120), (3300, 200), (3900, 250)],
    "eh": [(530, 70), (1840, 100), (2480, 120), (3400, 200), (4000, 250)],
    "mm": [(260, 55), (1150, 380), (2250, 420), (3300, 520), (3900, 600)],    # closed-mouth nasal murmur
    "kh": [(450, 160), (1500, 260), (2600, 300), (3500, 400), (4200, 500)],   # constricted, rasping throat
}


def tract(keys, n, scale=1.0, bwscale=1.0):
    """[(t, vowel), ...] -> five (freq contour, bandwidth contour) tracks; scale < 1 = a bigger tract,
    bwscale > 1 broadens the formants (noise-excited, whispery or snarling sounds)."""
    tt = np.arange(n) / SR
    ts = [k[0] for k in keys]
    out = []
    for i in range(5):
        fs = [VOWELS[v][i][0] * scale for _, v in keys]
        bs = [VOWELS[v][i][1] * bwscale for _, v in keys]
        out.append((np.interp(tt, ts, fs), np.interp(tt, ts, bs)))
    return out


def cascade(x, tracks):
    for f, bw in tracks:
        f, bw = np.asarray(f, float), np.asarray(bw, float)
        if f.ndim and np.ptp(f) == 0:
            f = f[0]
        if bw.ndim and np.ptp(bw) == 0:
            bw = bw[0]
        x = reson(x, f, bw)
    return x


def smooth(n, hz):
    """Smooth random contour (unit std, zero mean) with ~hz bandwidth."""
    if n < 32:
        return np.zeros(n)
    m = int(n / SR * hz * 2) + 4
    x = np.interp(np.linspace(0, m - 1, n), np.arange(m), RNG.standard_normal(m))
    x = signal.sosfiltfilt(signal.butter(2, min(hz, SR / 4), fs=SR, output="sos"), x)
    return (x - x.mean()) / (x.std() + 1e-12)


def smooth_env(x, hz=30.0):
    """Zero-phase smoothing of a control envelope (no lag), kept >= 0."""
    return np.maximum(signal.sosfiltfilt(signal.butter(2, hz, fs=SR, output="sos"), x), 0.0)


def rough(n, hz, depth=0.8, power=2.0):
    """Granular amplitude modulation (>= 0, mean ~1) for scrapes, grinds and rustles."""
    m = np.abs(smooth(n, hz)) ** power
    return (1 - depth) + depth * m / (m.mean() + 1e-12)


def curve(n, pts, log=False):
    """Piecewise-linear (or log-linear) contour through (t seconds, value) key points."""
    tt = np.arange(n) / SR
    ts = [p[0] for p in pts]
    vs = np.array([p[1] for p in pts], float)
    if log:
        return np.exp(np.interp(tt, ts, np.log(vs)))
    return np.interp(tt, ts, vs)


def decay(d, tau, att=0.001):
    t = t_axis(d)
    return np.clip(t / att, 0, 1) * np.exp(-t / tau)


def endfade(x, frac=0.15, most=0.05):
    """Raised-cosine taper over the end of a finite event so a truncated ring never clicks."""
    k = min(int(len(x) * frac), N(most))
    if k > 1:
        x = x.copy()
        x[-k:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, k))
    return x


def u(x):
    return x / (np.max(np.abs(x)) + 1e-12)


def rmsn(x, mask=None):
    v = x if mask is None else x[mask]
    return x / (np.sqrt(np.mean(v ** 2)) + 1e-12)


# ----------------------------------------------------------------------------- voice

def glottal(f0, oq=0.6, rq=0.7, jitter=0.01, shimmer=0.04, diplo=0.0):
    """Rosenberg glottal pulse train on a per-sample f0 contour. Returns (flow derivative, flow).
    oq open quotient, rq rise fraction of the open phase; jitter (smooth period perturbation), shimmer
    (per-cycle amplitude noise) and diplo (alternate-cycle amplitude = subharmonic roughness) may be
    scalars or per-sample contours."""
    f0 = np.asarray(f0, float)
    n = len(f0)
    jb = float(np.clip(np.mean(f0) * 0.7, 12, 120))
    f = np.maximum(f0 * (1 + np.asarray(jitter, float) * smooth(n, jb)), 5.0)
    ph = np.cumsum(f) / SR
    cyc = np.floor(ph).astype(np.int64)
    frac = ph - cyc
    oq = np.asarray(oq, float)
    tp, tn = oq * rq, oq * (1 - rq)
    g = np.where(frac < tp, 0.5 * (1 - np.cos(np.pi * np.minimum(frac / tp, 1.0))),
                 np.where(frac < tp + tn, np.cos(0.5 * np.pi * np.clip((frac - tp) / tn, 0, 1)), 0.0))
    nc = int(cyc[-1]) + 2
    sh = RNG.standard_normal(nc)
    alt = np.where(np.arange(nc) % 2 == 0, 1.0, -1.0)
    amp = 1 + np.asarray(shimmer, float) * sh[cyc] + np.asarray(diplo, float) * alt[cyc]
    g = g * np.clip(amp, 0.05, None)
    return np.diff(g, prepend=0.0), g


def voice(f0, amp, tracks, breath=0.15, oq=0.6, rq=0.7, jitter=0.012, shimmer=0.05, diplo=0.0,
          drift=0.008, asp=(400, 7000), par=()):
    """Source-filter voice: glottal flow derivative + aspiration noise (gated by the glottal opening),
    mixed by `breath` (0..1, scalar or contour), scaled by `amp`, through cascaded formant tracks;
    `par` adds parallel resonances [(f, bw, gain)] on the same excitation (chest, nasal cavity)."""
    f0 = np.asarray(f0, float)
    n = len(f0)
    f0 = f0 * (1 + drift * smooth(n, 3))
    dg, g = glottal(f0, oq, rq, jitter, shimmer, diplo)
    on = amp > 0.02
    if not on.any():
        on = np.ones(n, bool)
    dg = dg / (np.sqrt(np.mean(dg[on] ** 2)) + 1e-12)
    a = bp(noise(n / SR), *asp) * (0.3 + g / (g.max() + 1e-12))
    a = a / (np.sqrt(np.mean(a[on] ** 2)) + 1e-12)
    br = np.asarray(breath, float)
    exc = (dg * (1 - br) + a * br) * amp
    y = cascade(exc, tracks)
    if par:
        y = u(y) + sum(g * u(reson(exc, f, bw)) for f, bw, g in par)
    return y


# ----------------------------------------------------------------------------- hits and textures

PLATE = (1.0, 1.59, 2.14, 2.30, 2.65, 2.92, 3.50, 4.15, 4.62, 5.40, 6.20, 7.10)   # armor plates
BAR = (1.0, 2.756, 5.404, 8.933, 13.34)                                             # free bar: blades


def sat(x, drive=2.5):
    """Soft (tanh) saturation of a ~unit-peak signal: adds harmonics so a sub boom is still felt as
    weight on small speakers (the ear infers the missing fundamental)."""
    return np.tanh(drive * x) / np.tanh(drive)


def thump(d, f0, f1, tau, ptau=0.03, h2=0.15, att=0.0015):
    """Sine whose pitch falls from f0 to f1 (time constant ptau), decaying with tau: the body of a hit."""
    t = t_axis(d)
    f = f1 + (f0 - f1) * np.exp(-t / ptau)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return endfade((np.sin(ph) + h2 * np.sin(2 * ph)) * np.exp(-t / tau) * np.clip(t / att, 0, 1))


def modal(freqs, amps, taus, d, att=0.0004):
    t = t_axis(d)
    x = np.zeros_like(t)
    for f, a, tau in zip(freqs, amps, taus):
        if f < SR * 0.45:
            x += a * np.sin(2 * np.pi * f * t + RNG.uniform(0, 2 * np.pi)) * np.exp(-t / tau)
    return endfade(x * np.clip(t / att, 0, 1))


def metal_hit(f0, d=0.6, tau=0.25, hard=0.7, ratios=PLATE, beat=0.5):
    """Struck metal: inharmonic modes (split pairs beat slowly) + a bright strike transient. Peak ~1."""
    t = t_axis(d)
    rs = np.array(ratios, float) * (1 + 0.025 * RNG.standard_normal(len(ratios)))
    rs[0] = 1.0
    amps = RNG.uniform(0.45, 1.0, len(rs)) * rs ** (-1.2 + 0.9 * hard)
    taus = tau * rs ** -0.45 * RNG.uniform(0.7, 1.3, len(rs))
    x = np.zeros_like(t)
    for f, a, tt in zip(f0 * rs, amps, taus):
        if f > SR * 0.45:
            continue
        ph = RNG.uniform(0, 2 * np.pi)
        e = np.exp(-t / tt)
        x += a * np.sin(2 * np.pi * f * t + ph) * e
        if beat:
            x += a * beat * 0.5 * np.sin(2 * np.pi * (f + RNG.uniform(0.8, 4.0)) * t + ph + 1.0) * e
    x = u(x) * np.clip(t / 0.0004, 0, 1)
    return endfade(x + u(hp(noise(d), 2500)) * np.exp(-t / 0.0007) * 0.45 * hard)


def stone_hit(size=0.3, bright=1.0):
    """Knock of stone on stone: size 0 (a grain, ~5 kHz tick) .. 1 (a rock, ~500 Hz knock + thump)."""
    f0 = 5000 * 0.1 ** size * RNG.uniform(0.8, 1.25)
    tau = 0.0025 + 0.022 * size
    d = tau * 9 + 0.015
    t = t_axis(d)
    rs = (1.0, RNG.uniform(1.3, 1.7), RNG.uniform(1.9, 2.6), RNG.uniform(2.8, 3.9))
    x = u(modal([f0 * r for r in rs], (1.0, 0.7, 0.45, 0.3), [tau / r ** 0.4 for r in rs], d, att=0.0003))
    x = x + u(hp(noise(d), 1500)) * np.exp(-t / (0.0005 + 0.001 * size)) * 0.7 * bright
    if size > 0.35:
        x = x + thump(d, 170 - 90 * size, 60, tau=0.015 + 0.04 * size, ptau=0.01) * (size - 0.3) * 1.6
    return x


def wood_hit(f0=220, d=0.5, tau=0.06, crack=0.4):
    """Knock / crack of wood: damped plank modes + a noisy knock (crack > 1 = splintery)."""
    t = t_axis(d)
    rs = np.array([1.0, 1.73, 2.61, 3.85, 5.12]) * (1 + 0.04 * RNG.standard_normal(5))
    rs[0] = 1.0
    x = u(modal(f0 * rs, (1.0, 0.7, 0.5, 0.3, 0.2), tau / rs ** 0.6, d))
    knock = u(bp(noise(d), 250, 5000)) * np.exp(-t / 0.005) * np.clip(t / 0.0003, 0, 1)
    return endfade(x + knock * crack)


def crackle(d, rate, lo=1500, hi=9000, grain=0.0006, alpha=1.6, cap=8.0):
    """Poisson impulses (rate: events/s, scalar or contour) with heavy-tailed amplitudes, each a short
    decaying noise grain, band-passed: splinters, sparks, gravel, saliva, fire."""
    n = N(d)
    rate = np.broadcast_to(np.asarray(rate, float), (n,))
    hit = RNG.random(n) < rate / SR
    a = np.minimum(RNG.pareto(alpha, n) + 1.0, cap) * np.where(RNG.random(n) < 0.5, -1.0, 1.0)
    imp = np.where(hit, a, 0.0)
    k = max(8, N(grain * 6))
    kern = RNG.standard_normal(k) * np.exp(-np.arange(k) / max(1.0, grain * SR))
    return bp(signal.fftconvolve(imp, kern)[:n], lo, hi)


def whoosh(d, f0, f1, q=1.5, color="pink"):
    n = N(d)
    f = f0 * (f1 / f0) ** (np.arange(n) / max(1, n - 1))
    return tv_filter(noise(d, color), f, q)


def bubble(f, d=0.06, tau=0.012, rise=1.6):
    """Water bubble: a sine whose pitch glides (rise > 1 up, < 1 down) as it decays."""
    t = t_axis(d)
    ff = f * (1 + (rise - 1) * (1 - np.exp(-t / 0.01)))
    return endfade(np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t / tau) * np.clip(t / 0.001, 0, 1))


def wet(d, rate, lo=600, hi=3500, tau=(0.002, 0.007), rise=(0.7, 1.8)):
    """Wet texture: Poisson-timed tiny bubble pops (rate events/s, scalar or contour) - saliva, mucus,
    squelch. Each pop is a short sine whose pitch glides up or down."""
    n = N(d)
    cum = np.cumsum(np.broadcast_to(np.asarray(rate, float), (n,))) / SR
    x = np.zeros(n)
    for i in np.searchsorted(cum, np.sort(RNG.uniform(0, cum[-1], RNG.poisson(cum[-1])))):
        b = bubble(np.exp(RNG.uniform(np.log(lo), np.log(hi))), 0.04, tau=RNG.uniform(*tau), rise=RNG.uniform(*rise))
        j = min(n, i + len(b))
        x[i:j] += b[: j - i] * RNG.uniform(0.3, 1.0)
    return x


def drop(f=1500, rise=1.8, tau=0.02):
    """A water drop: tiny impact click + rising bubble 'plink'."""
    d = 0.14
    t = t_axis(d)
    return bubble(f, d, tau, rise) + u(hp(noise(d), 3000)) * np.exp(-t / 0.0004) * 0.35


def splat(size=1.0):
    """A wet plop: slap of liquid + falling 'blop' + droplets."""
    d = 0.3
    t = t_axis(d)
    x = u(bp(noise(d), 250, 4000)) * decay(d, 0.006 + 0.004 * size, 0.0008) * 0.8
    x += bubble(300 - 80 * size, d, tau=0.02 + 0.012 * size, rise=0.62) * 0.65
    x += thump(d, 170, 90, tau=0.018) * 0.4 * size
    for _ in range(4):
        b = bubble(RNG.uniform(1500, 3500), 0.03, tau=0.004, rise=1.4) * 0.15
        i = N(RNG.uniform(0.012, 0.07))
        x[i:i + len(b)] += b[: len(x) - i]
    return x * np.clip(t / 0.0005, 0, 1)


def claw():
    """One claw tip ticking / skidding on stone."""
    d = 0.03
    t = t_axis(d)
    x = u(modal(RNG.uniform(2500, 7500, 3), (1.0, 0.7, 0.5), RNG.uniform(0.001, 0.003, 3), d, att=0.0002))
    x = x + u(hp(noise(d), 3000)) * np.exp(-t / 0.0004) * 0.8
    return x + u(bp(noise(d), 2000, 8000)) * np.exp(-t / 0.006) * 0.25


def creak(d, f0=55, f1=85, res=((650, 4.0), (1400, 5.0), (2700, 5.0)), jitter=0.2):
    """Leather / strap creak: stick-slip pulse train through a few resonances."""
    n = N(d)
    dg, _ = glottal(curve(n, [(0, f0), (d, f1)]), oq=0.3, rq=0.5, jitter=jitter, shimmer=0.45)
    return u(sum(rbp(dg, f, q) / (i + 1) for i, (f, q) in enumerate(res)))


# ----------------------------------------------------------------------------- space and assembly

def pan2(x, p=0.0):
    """Mono -> stereo, constant power; p scalar or per-sample contour (-1 left .. +1 right)."""
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * np.sqrt(2)


def place(buf, x, t, gain=1.0, pan=None):
    """Add x into buf at t seconds (mono x is panned when buf is stereo)."""
    if buf.ndim == 2 and x.ndim == 1:
        x = pan2(x, 0.0 if pan is None else pan)
    i = N(t)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i] * gain


def cave(x, rt=2.0, wet=0.3, pre=0.018, bright=6500, dark=1400, taps=6):
    """Synthetic stereo cave reverb: pre-delay, sparse early reflections, a noise tail with RT60 `rt`
    whose spectrum darkens as it decays. Returns dry + wet * reverb, len(x) + 1.15 * rt long."""
    if x.ndim == 1:
        x = pan2(x, 0.0)
    L = N(rt * 1.15)
    t = np.arange(L) / SR
    env = np.exp(-6.91 * t / rt)
    w = np.exp(-t / (0.22 * rt))
    p = N(pre)
    irs = []
    for _ in range(2):
        nz = RNG.standard_normal(L)
        ir = (lp(nz, bright) * w + lp(nz, dark) * (1 - w) * 1.4) * env
        ir[:p] = 0
        ir[p:] *= np.clip((t[p:] - pre) / 0.012, 0, 1)
        er = np.zeros(L)
        for _ in range(taps):
            dt = pre + RNG.uniform(0.004, 0.075)
            er[min(L - 1, N(dt))] += RNG.uniform(0.4, 1.0) * RNG.choice([-1, 1]) * np.exp(-6.91 * dt / rt)
        er = lp(er, bright)
        ir = ir + er * np.sqrt(np.sum(ir ** 2)) * 0.6 / (np.sqrt(np.sum(er ** 2)) + 1e-12)
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    y = np.pad(x, ((0, L), (0, 0)))
    wl = signal.fftconvolve(y[:, 0], irs[0])[: len(y)]
    wr = signal.fftconvolve(y[:, 1], irs[1])[: len(y)]
    return y + wet * np.stack([wl, wr], 1)


def fade(x, fi=0.005, fo=0.02):
    n = len(x)
    e = np.ones(n)
    a, b = min(n, N(fi)), min(n, N(fo))
    if a:
        e[:a] = np.linspace(0, 1, a)
    if b:
        e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return x * (e[:, None] if x.ndim == 2 else e)


def fit(x, d, fo=0.03):
    """Pad / cut to exactly d seconds, fading the end."""
    n = N(d)
    if len(x) < n:
        x = np.pad(x, ((0, n - len(x)),) + ((0, 0),) * (x.ndim - 1))
    return fade(x[:n], 0, fo)


def trim_tail(x, db=-62.0, pad=0.03):
    a = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    idx = np.nonzero(a > a.max() * 10 ** (db / 20))[0]
    end = min(len(x), (idx[-1] if len(idx) else len(x)) + N(pad))
    return fade(x[:end], 0, min(0.04, end / SR / 4))


def norm(x, peak_db=-3.0):
    return x / (np.max(np.abs(x)) + 1e-12) * 10 ** (peak_db / 20)


def loop_xfade(x, L, xf):
    """x has >= L + xf samples: returns L samples whose head is an equal-power crossfade from the
    continuation x[L:L+xf] into x[:xf], so the wrap x[L-1] -> x[0] is continuous (uncorrelated beds)."""
    y = x[:L].copy()
    r = np.linspace(0, np.pi / 2, xf)
    fi, fo = np.sin(r), np.cos(r)
    if x.ndim == 2:
        fi, fo = fi[:, None], fo[:, None]
    y[:xf] = x[:xf] * fi + x[L:L + xf] * fo
    return y


def fold(x, L):
    """Wrap everything past L back onto the start (circular placement of event tails)."""
    y = x[:L].copy()
    i = L
    while i < len(x):
        k = min(L, len(x) - i)
        y[:k] += x[i:i + k]
        i += k
    return y


def circ_hp(x, f=20.0):
    """High-pass a loop in its periodic steady state (filter two copies, keep the second)."""
    L = len(x)
    return hp(np.concatenate([x, x], axis=0), f)[L:]


# ============================================================================ ambience loops

def cave_air_loop():
    """S1-S2 tunnel / cavern air, 20 s seamless: deep rumble, a slow hollow 'moan' band drifting in
    pitch, faint air hiss and three far-off echoing drips (3.1, 9.7, 15.2 s)."""
    L, xf = N(20.0), N(2.5)
    n = L + xf
    tot = n / SR
    t = np.arange(n) / SR
    chans = []
    for ch in range(2):
        rumble = rmsn(lp(noise(tot, "brown"), 110, 4))
        fb = 280 * 2 ** (0.7 * np.sin(2 * np.pi * t / 10.0 + ch * 1.3) + 0.3 * np.sin(2 * np.pi * t / 6.67 + 0.5))
        moan = rmsn(tv_filter(noise(tot, "pink"), fb, q=6.0))
        gm = 0.55 + 0.45 * np.sin(2 * np.pi * t / 20.0 + ch * 2.1)
        air = rmsn(bp(noise(tot, "pink"), 600, 4000))
        chans.append(loop_xfade(rumble + moan * 0.3 * gm + air * 0.06, L, xf))
    bed = np.stack(chans, 1)
    ev = np.zeros((L + N(5.0), 2))
    for tt, f, pan, g in ((3.1, 1500, -0.6, 1.0), (9.7, 1950, 0.55, 0.7), (15.2, 1250, 0.15, 0.85)):
        place(ev, lp(drop(f), 5000) * g, tt, pan=pan)
    ev = cave(ev, rt=3.5, wet=2.5, pre=0.04, taps=8)
    return bed + fold(ev, L) * 0.6


def _torch_tick():
    d = 0.006
    return u(hp(noise(d), 2500)) * decay(d, 0.0005, 0.0001)


def _torch_pop():
    d = 0.04
    t = t_axis(d)
    x = u(bp(noise(d), 700, 6000)) * decay(d, 0.003, 0.0002)
    return x + np.sin(2 * np.pi * RNG.uniform(1500, 3500) * t) * np.exp(-t / 0.004) * 0.5


def _torch_pfft():
    d = RNG.uniform(0.06, 0.12)
    n = N(d)
    return u(bp(noise(d), 900, 5000) * rough(n, 150, 0.7, 2)) * np.sin(np.pi * np.arange(n) / n) ** 2


def torch_loop():
    """Torch flame, 12 s seamless: a flickering low roar and soft gas hiss (crossfaded bed) with
    crackle - ticks, pops and the odd sappy 'pfft' (~9 events/s, folded around the loop)."""
    L, xf = N(12.0), N(1.5)
    n = L + xf
    tot = n / SR
    flick = smooth(n, 5)
    chans = []
    for _ in range(2):
        f2 = np.clip(1 + 0.25 * flick + 0.12 * smooth(n, 13), 0.4, None)
        roar = rmsn(bp(noise(tot, "pink"), 60, 700)) * f2
        body = rmsn(bp(noise(tot, "pink"), 300, 1800)) * f2 ** 1.5 * 0.35
        hiss = rmsn(bp(noise(tot), 2000, 8000)) * f2 * 0.05
        chans.append(loop_xfade(roar + body + hiss, L, xf))
    bed = np.stack(chans, 1)
    ev = np.zeros((L + N(1.0), 2))
    tt = RNG.uniform(0.05, 0.15)
    while tt < L / SR:
        r = RNG.random()
        if r < 0.72:
            s = _torch_tick() * RNG.uniform(0.2, 0.7)
        elif r < 0.95:
            s = _torch_pop() * RNG.uniform(0.5, 1.0)
        else:
            s = _torch_pfft() * 0.5
        place(ev, s, tt, pan=RNG.uniform(-0.25, 0.25))
        tt += RNG.exponential(1 / 9.0)
    return bed * 0.45 + fold(ev, L)


def deep_air_loop():
    """S4-S6 grotto air, 24 s seamless: sub rumble, a hollow low resonance, a slowly beating 55 Hz drone
    (integer cycles -> periodic), five far drips with wall echoes and one distant pebble trickle (~18.3 s)."""
    L, xf = N(24.0), N(3.0)
    n = L + xf
    tot = n / SR
    t = np.arange(n) / SR
    chans = []
    for ch in range(2):
        rumble = rmsn(lp(noise(tot, "brown"), 75, 4))
        fb = 150 * 2 ** (0.35 * np.sin(2 * np.pi * t / 12.0 + ch))
        hollow = rmsn(tv_filter(noise(tot, "pink"), fb, q=8.0)) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 8.0 + ch * 1.7))
        air = rmsn(bp(noise(tot, "pink"), 700, 3500))
        chans.append(loop_xfade(rumble + hollow * 0.3 + air * 0.03, L, xf))
    bed = np.stack(chans, 1)
    tl = np.arange(L) / SR
    drone = 0.25 * (np.sin(2 * np.pi * 55 * tl) + np.sin(2 * np.pi * 55.25 * tl + 1.0)) \
        + 0.08 * np.sin(2 * np.pi * 110.25 * tl)
    bed = bed + drone[:, None]
    ev = np.zeros((L + N(5.0), 2))
    for tt, f, pan, g in ((2.2, 1350, -0.7, 0.9), (7.9, 1800, 0.4, 0.6), (11.6, 1550, -0.2, 0.75),
                          (16.4, 2100, 0.75, 0.5), (21.0, 1200, -0.45, 0.8)):
        dr = lp(drop(f), 4500) * g
        place(ev, dr, tt, pan=pan)
        for k, (dt, gg) in enumerate(((0.23, 0.35), (0.5, 0.2), (0.81, 0.11))):
            place(ev, lp(dr, 3000 / (k + 1)) * gg, tt + dt, pan=-pan * 0.8)
    for k in range(7):
        s = lp(stone_hit(RNG.uniform(0.05, 0.25)), 3500) * RNG.uniform(0.15, 0.35) * 0.85 ** k
        place(ev, s, 18.3 + k * 0.09 + RNG.uniform(0, 0.05), pan=0.6)
    ev = cave(ev, rt=2.8, wet=2.0, pre=0.03)
    return bed * 0.5 + fold(ev, L) * 0.55


def _snore_cycle(T, fl0, fl1, wp, a=0.35, b=1.95, c=2.25):
    """One snore breath (T s, + tails): palatal-flutter inhale a..b, held breath, lip-flap exhale from c
    with a wheezy nose whistle following the (t, Hz) points wp."""
    e = wp[-1][0] + 0.2
    n = N(T + 2.5)
    end = n / SR
    t = np.arange(n) / SR
    # --- inhale: the soft palate flapping at ~30-40 Hz (irregular), noisy airflow gated by each flap
    fl = curve(n, [(0, fl0), (a, fl0), (b - 0.3, fl1), (b, fl1 * 1.3), (end, fl1)])
    dg, g = glottal(fl, oq=0.6, rq=0.55, jitter=0.08, shimmer=0.35)
    on = (t > a) & (t < b)
    turb = rmsn(bp(noise(end, "pink"), 100, 4000), on)
    exc = rmsn(dg, on) * 0.9 + turb * (0.08 + 1.2 * (g / (g.max() + 1e-12)) ** 2) * 0.5
    env = smooth_env(curve(n, [(0, 0), (a, 0), (a + 0.3, 0.3), (a + 0.95, 0.7), (b - 0.22, 1.0),
                               (b - 0.05, 0.85), (b, 0), (end, 0)]), 30)
    tr = tract([(0, "aw"), (a + 0.6, "aw"), (b, "ah"), (end, "ah")], n, scale=0.82)
    sn = u(cascade(exc * env, tr)) + 0.45 * u(reson(exc * env, 240, 80))
    # wet 'snerk' as the throat closes
    sk = u(bp(noise(0.08, "pink"), 300, 2500)) * decay(0.08, 0.01, 0.002) + thump(0.08, 420, 190, tau=0.014)
    out = u(sn)
    i = N(b - 0.03)
    out[i:i + len(sk)] += u(sk)[: n - i] * 0.35
    # --- exhale: 'pbbb' lip flap, breath through rounded lips
    benv = smooth_env(curve(n, [(0, 0), (c, 0), (c + 0.07, 1), (c + 0.5, 0.65), (e - 0.3, 0.35), (e, 0), (end, 0)]), 30)
    br = cascade(bp(noise(end, "pink"), 150, 5000) * benv, tract([(0, "oh"), (end, "uh")], n, 0.9))
    lph = np.cumsum(curve(n, [(0, 24), (c, 24), (c + 0.25, 18), (end, 18)])) / SR
    lenv = curve(n, [(0, 0), (c, 0), (c + 0.03, 1), (c + 0.24, 0.35), (c + 0.32, 0), (end, 0)])
    lip = lp(noise(end, "pink"), 1200) * (0.5 + 0.5 * np.cos(2 * np.pi * lph)) ** 6 * lenv
    # --- the wheezy whistle riding the exhale
    fw = curve(n, [(0, wp[0][1])] + list(wp) + [(end, wp[-1][1])], log=True)
    fw = fw * (1 + 0.012 * np.sin(2 * np.pi * 5.3 * t) + 0.008 * smooth(n, 18))
    wamp = smooth_env(curve(n, [(0, 0), (wp[0][0] - 0.15, 0), (wp[0][0] + 0.12, 1), (wp[-1][0] - 0.1, 0.85),
                                (wp[-1][0] + 0.12, 0), (end, 0)]), 20)
    wamp = wamp * np.clip(0.75 + 0.35 * smooth(n, 9), 0.2, 1.3)
    wph = 2 * np.pi * np.cumsum(fw) / SR
    tone = np.sin(wph) + 0.12 * np.sin(2 * wph + 0.5)
    airy = rmsn(tv_filter(noise(end), fw, q=30), wamp > 0.1)
    wh = (tone * 0.7 + airy * 0.3) * wamp
    return out + u(br) * 0.3 + u(lip) * 0.22 + wh * 0.22


def snore_loop():
    """The hermit's snore from the dark (screen-left), 18.0 s seamless = 4 breaths of 4.3-4.8 s. Each:
    a big rattling palatal-flutter inhale (0.35-1.95 s into the breath, crescendo, the loud part) ending
    in a wet 'snerk', a held beat, then a 'pbbb' lip-flap exhale with a wheezy whistle gliding up and down
    (~2.3-3.8 s). Breath starts: 0.0, 4.5, 8.8, 13.6 s."""
    cycles = [  # (length, flutter start Hz, flutter end Hz, whistle (t, Hz) points, gain)
        (4.5, 29, 37, ((2.45, 1650), (2.95, 2080), (3.55, 1480)), 1.0),
        (4.3, 32, 40, ((2.4, 1820), (3.05, 2300), (3.5, 1950)), 0.9),
        (4.8, 27, 35, ((2.5, 1500), (3.1, 1900), (3.75, 1240)), 1.0),
        (4.4, 31, 39, ((2.4, 1700), (2.8, 2200), (3.15, 2050), (3.6, 1450)), 0.94),
    ]
    L = N(sum(c[0] for c in cycles))
    buf = np.zeros(L + N(3.0))
    t0 = 0.0
    for T, f0, f1, wp, g in cycles:
        place(buf, _snore_cycle(T, f0, f1, wp) * g, t0)
        t0 += T
    return fold(cave(pan2(buf, -0.35), rt=1.9, wet=0.28, pre=0.02), L)


# ============================================================================ S1: the tunnel

def sword_chop():
    """Blade swish, then the CHOP at +0.083 s (2 frames): fibrous wet thwack + crackling fibres + a
    faint blade ring; severed vine bits rustle to ~0.5 s."""
    d = 1.0
    hit = 2 * FRAME
    x = np.zeros(N(d))
    sw = whoosh(hit + 0.03, 450, 2800, q=1.2)
    e = np.clip(np.arange(len(sw)) / (hit * SR), 0, 1) ** 3
    e[N(hit):] *= np.exp(-np.arange(len(e) - N(hit)) / (0.006 * SR))
    place(x, u(sw * e) * 0.35, 0.0)
    td = 0.6
    n = N(td)
    tt = t_axis(td)
    th = thump(td, 210, 90, tau=0.05, ptau=0.015)
    fib = u(crackle(td, 2500 * np.exp(-tt / 0.03), 700, 7500, grain=0.0004))
    wet = u(bp(noise(td, "pink"), 250, 1800)) * decay(td, 0.035, 0.001)
    ring = metal_hit(1350, td, tau=0.3, hard=0.4, ratios=BAR, beat=0.3)
    leaves = u(bp(noise(td), 1500, 7000) * rough(n, 45, 0.9, 3)) * curve(n, [(0, 0), (0.05, 1), (0.45, 0), (td, 0)])
    place(x, th * 0.9 + fib * 0.55 + wet * 0.6 + ring * 0.1 + leaves * 0.15, hit)
    return cave(pan2(x, 0.05), rt=1.5, wet=0.22)


def vines_fall():
    """Severed vines and roots slither down and land in pieces (soft thuds 0.28-1.32 s), leafy rustle
    and fibres snapping."""
    d = 2.0
    n = N(d)
    buf = np.zeros((n, 2))
    renv = curve(n, [(0, 0), (0.06, 1.0), (0.5, 0.8), (1.3, 0.3), (1.8, 0), (d, 0)])
    for ch in range(2):
        buf[:, ch] += u(bp(noise(d), 1200, 8000) * rough(n, 35, 0.9, 3)) * renv * 0.35
    snaps = u(crackle(0.4, 600, 1500, 7000, grain=0.0004)) * decay(0.4, 0.12, 0.002) * 0.3
    place(buf, snaps, 0.0, pan=0.1)
    for k, (tt, f) in enumerate(((0.28, 210), (0.46, 170), (0.63, 240), (0.8, 150), (0.98, 200), (1.15, 180), (1.32, 230))):
        pc = thump(0.3, f, f * 0.55, tau=0.03, ptau=0.012) * 0.7 \
            + u(bp(noise(0.3, "pink"), 600, 5000)) * decay(0.3, 0.012) * 0.45
        place(buf, pc * RNG.uniform(0.5, 1.0) * 0.9 ** k, tt, pan=RNG.uniform(-0.5, 0.5))
    return cave(buf, rt=1.5, wet=0.22)


def web_tear():
    """Gauntlet back-hand swipe (whoosh 0-0.15) tearing thick webs: sticky crackling tear 0.06-0.48 s
    (peak ~0.1), stretchy silk hiss, elastic strand plinks."""
    d = 0.8
    n = N(d)
    buf = np.zeros((n, 2))
    sw = whoosh(0.16, 700, 2400, q=1.3) * np.sin(np.pi * np.arange(N(0.16)) / N(0.16)) ** 2
    place(buf, u(sw) * 0.4, 0.0, pan=-0.2)
    tenv = curve(n, [(0, 0), (0.05, 0), (0.1, 1), (0.28, 0.7), (0.48, 0), (d, 0)])
    tear = u(crackle(d, 3500 * tenv, 2200, 9500, grain=0.00035)) * 0.8
    stretch = u(tv_filter(noise(d), curve(n, [(0, 1800), (0.5, 3200), (d, 3200)]), q=3) * rough(n, 70, 0.8, 2) * tenv) * 0.35
    place(buf, tear + stretch, 0.0, pan=0.05)
    for k in range(5):
        place(buf, modal([RNG.uniform(650, 1400)], [1.0], [0.008], 0.05) * 0.25,
              0.08 + k * 0.07 + RNG.uniform(0, 0.03), pan=RNG.uniform(-0.4, 0.4))
    place(buf, metal_hit(2100, 0.3, tau=0.05, hard=0.5) * 0.08, 0.06)
    return cave(buf, rt=1.5, wet=0.18)


def door_locked():
    """Locked door: hand on the iron ring (clink +0.00), YANK at +0.10 (bolt clack + heavy wood THUNK,
    the ring rattling against its plate to ~0.35), a second smaller shove-thunk at +0.48 with rattle."""
    d = 1.5
    buf = np.zeros((N(d), 2))
    place(buf, metal_hit(1900, 0.3, tau=0.05, hard=0.5) * 0.2, 0.0, pan=0.05)
    for tt, g in ((0.10, 1.0), (0.48, 0.72)):
        knock = wood_hit(105, 0.7, tau=0.08, crack=0.5) + thump(0.7, 140, 80, tau=0.07) * 0.9
        place(buf, knock * g, tt, pan=0.0)
        place(buf, metal_hit(950, 0.5, tau=0.1, hard=0.8, ratios=BAR) * 0.45 * g, tt + 0.004, pan=0.1)
        hits = tt + 0.02 + np.cumsum([0, 0.07, 0.055, 0.045, 0.035, 0.03])
        for k, th in enumerate(hits):
            place(buf, metal_hit(RNG.uniform(1300, 1700), 0.4, tau=0.09, hard=0.9) * 0.5 * g * 0.78 ** k,
                  th, pan=0.08)
        place(buf, u(bp(noise(0.5, "pink"), 1500, 8000)) * curve(N(0.5), [(0, 0), (0.05, 1), (0.5, 0)]) ** 2 * 0.06 * g,
              tt + 0.03, pan=-0.2)
    return cave(buf, rt=1.6, wet=0.22)


def door_explode():
    """THE DOOR BURSTS. Shoulder impact + BOOM at +0.00 (peak within ~10 ms; low boom decays over ~1 s),
    a splintering burst with big wood snaps 0-0.6 s, a gust of cold air, then planks, iron bands
    (clangs ~0.34, 0.71, 1.18, 1.62 s) and stones clattering 0.15-2.6 s; a big cavern tail to ~5 s."""
    d = 3.0
    n = N(d)
    buf = np.zeros((n, 2))
    boom = thump(d, 100, 32, tau=0.4, ptau=0.06, h2=0.35)
    sub2 = thump(d, 60, 38, tau=0.9, ptau=0.2, h2=0.0) * 0.3
    rumble = u(lp(noise(d, "brown"), 160, 4)) * curve(n, [(0, 0), (0.02, 1), (0.5, 0.45), (2.5, 0.08), (d, 0)])
    blast = u(bp(noise(d, "pink"), 100, 4000)) * decay(d, 0.09, 0.001)
    crack = u(hp(noise(d), 1500)) * decay(d, 0.01, 0.0003)
    place(buf, wood_hit(140, 0.5, tau=0.05, crack=1.5) * 0.9, 0.0)
    gust = u(tv_filter(noise(d, "pink"), curve(n, [(0, 2500), (0.8, 350), (d, 350)], log=True), q=1.0)) \
        * curve(n, [(0, 0), (0.05, 1), (0.9, 0), (d, 0)]) ** 1.5
    crunch = u(bp(noise(d), 400, 3000)) * decay(d, 0.12, 0.001)
    place(buf, boom + sub2 + rumble * 0.45 + blast * 1.3 + crunch * 0.8 + crack * 1.0 + gust * 0.35, 0.0)
    srate = curve(n, [(0, 3500), (0.12, 2500), (0.5, 500), (1.0, 0), (d, 0)])
    for ch in range(2):
        buf[:, ch] += u(crackle(d, srate, 700, 9000, grain=0.0005, alpha=1.3)) * 0.65 \
            + u(crackle(d, srate * 0.5, 200, 2500, grain=0.0018)) * 0.6
    for _ in range(7):
        place(buf, wood_hit(RNG.uniform(300, 750), 0.3, tau=0.025, crack=1.2) * RNG.uniform(0.2, 0.38),
              RNG.uniform(0.0, 0.25), pan=RNG.uniform(-0.6, 0.6))
    for _ in range(12):
        tt = 0.2 + 2.2 * RNG.random() ** 1.6
        place(buf, wood_hit(RNG.uniform(110, 380), 0.5, tau=RNG.uniform(0.04, 0.09), crack=0.5)
              * RNG.uniform(0.25, 0.6) * (1 - tt / 3), tt, pan=RNG.uniform(-0.85, 0.85))
    for k, tt in enumerate((0.34, 0.71, 1.18, 1.62)):
        place(buf, metal_hit(RNG.uniform(260, 520), 1.0, tau=RNG.uniform(0.25, 0.5), hard=0.8) * (0.4 - 0.06 * k),
              tt, pan=RNG.uniform(-0.7, 0.7))
    for _ in range(30):
        tt = 0.12 + 2.4 * RNG.random() ** 1.8
        place(buf, stone_hit(RNG.uniform(0.05, 0.6)) * RNG.uniform(0.15, 0.45), tt, pan=RNG.uniform(-0.9, 0.9))
    return cave(buf, rt=3.0, wet=0.35, pre=0.02, taps=8)


def debris_rain():
    """After the door: pebbles, splinters and grit raining down (dense -> sparse over ~3.2 s), sand hiss."""
    d = 3.6
    n = N(d)
    buf = np.zeros((n, 2))
    tt = 0.0
    while tt < 3.2:
        if RNG.random() < 0.75:
            s = stone_hit(RNG.uniform(0.0, 0.35) * RNG.random())
        else:
            s = wood_hit(RNG.uniform(500, 1400), 0.12, tau=RNG.uniform(0.008, 0.02), crack=0.6)
        place(buf, s * RNG.uniform(0.15, 0.6) * (0.4 + 0.6 * np.exp(-tt / 1.2)), tt, pan=RNG.uniform(-0.9, 0.9))
        tt += RNG.exponential(1 / (45 * np.exp(-tt / 0.9) + 3))
    sand = curve(n, [(0, 0), (0.08, 1), (3.4, 0), (d, 0)]) ** 2
    for ch in range(2):
        buf[:, ch] += u(bp(noise(d, "pink"), 1500, 9000)) * sand * rough(n, 25, 0.7, 2) * 0.12
    return cave(buf, rt=2.8, wet=0.3)


# ============================================================================ S2: the cavern

def scurry():
    """Claws skittering on stone: a fast four-legged gallop (strides ~0.1 s) crossing left -> right,
    loudest ~0.6 s, gone by 1.2 s; distant, in a big space."""
    d = 1.3
    n = N(d)
    t = t_axis(d)
    buf = np.zeros((n, 2))
    tt = 0.03
    while tt < 1.18:
        a = np.sin(np.pi * np.clip(tt / 1.2, 0, 1)) ** 1.2
        for off in (0.0, 0.017, 0.045, 0.062):
            ts = tt + off + RNG.normal(0, 0.003)
            place(buf, claw() * a * RNG.uniform(0.5, 1.0), ts, pan=-0.8 + 1.6 * ts / d)
        tt += 0.1 * RNG.uniform(0.9, 1.1)
    env = np.sin(np.pi * np.clip(t / 1.2, 0, 1)) ** 1.5
    rustle = u(bp(noise(d), 400, 2500) * rough(n, 60, 0.8, 2)) * env * 0.12
    buf += pan2(rustle, -0.8 + 1.6 * t / d)
    return cave(lp(buf, 9000), rt=3.2, wet=0.4, pre=0.03)


def stone_shift():
    """A stone tilts under his boot: grinding rock 0-0.28, a clack at +0.22, the armored stumble
    (jingle + boot scuff ~0.25-0.6) and loosened pebbles to ~1 s."""
    d = 1.2
    n = N(d)
    buf = np.zeros((n, 2))
    gd = 0.3
    gn = N(gd)
    grind = u(bp(noise(gd, "pink"), 250, 2500) * rough(gn, 90, 0.9, 2.5)) * np.sin(np.pi * np.arange(gn) / gn) ** 0.7
    grind = grind + u(lp(noise(gd, "brown"), 200)) * np.sin(np.pi * np.arange(gn) / gn) * 0.5
    place(buf, grind * 0.7, 0.0, pan=0.0)
    place(buf, stone_hit(0.6) * 0.9, 0.22)
    place(buf, thump(0.4, 120, 60, tau=0.06) * 0.6, 0.22)
    for k in range(5):
        place(buf, metal_hit(RNG.uniform(1100, 2600), 0.25, tau=RNG.uniform(0.04, 0.08), hard=0.8) * RNG.uniform(0.2, 0.45),
              0.25 + k * 0.05 + RNG.uniform(0, 0.03), pan=RNG.uniform(-0.3, 0.3))
    sc = u(bp(noise(0.25), 600, 4000)) * decay(0.25, 0.06, 0.005)
    place(buf, sc * 0.45 + thump(0.25, 110, 60, tau=0.05) * 0.5, 0.3, pan=-0.1)
    for _ in range(6):
        place(buf, stone_hit(RNG.uniform(0.05, 0.25)) * RNG.uniform(0.15, 0.35), RNG.uniform(0.3, 0.95),
              pan=RNG.uniform(-0.5, 0.5))
    return cave(buf, rt=3.2, wet=0.25)


def torch_whoosh():
    """The torch tumbling end over end through the air: flame 'fwoom' pulses at the tumble rate
    (2.4 -> 3 Hz), receding to the right; 1.3 s, ending into the splash."""
    d = 1.3
    n = N(d)
    t = t_axis(d)
    ph = np.cumsum(curve(n, [(0, 2.4), (d, 3.0)])) / SR
    am = 0.3 + 0.7 * (0.5 + 0.5 * np.cos(2 * np.pi * ph)) ** 3
    wh = tv_filter(noise(d, "pink"), 450 + 1100 * am, q=1.1)
    roar = bp(noise(d, "pink"), 80, 900)
    cr = crackle(d, 40, 2000, 8000, grain=0.0004)
    env = np.clip(t / 0.05, 0, 1) * (1 - 0.55 * t / d)
    x = (u(wh) * am * 0.9 + u(roar) * (0.4 + 0.6 * am) * 0.5 + u(cr) * 0.15) * env
    x = tv_filter(x, curve(n, [(0, 9000), (d, 3500)], log=True), q=0.707, kind="lp")
    st = pan2(x, curve(n, [(0, -0.05), (d, 0.45)]))
    return fit(cave(st, rt=3.0, wet=0.2), 1.36, fo=0.06)


def torch_splash():
    """The torch hits the pool at +0.00: plunge thud + bubble 'bloop' + spray (to ~0.4 s), droplets,
    then the steam HISS and sizzle (peak ~0.12-0.35 s, dying over ~2.5 s) with gurgles; cavern tail."""
    d = 3.2
    n = N(d)
    buf = np.zeros((n, 2))
    place(buf, thump(0.5, 160, 70, tau=0.06, ptau=0.02) * 0.8, 0.0)
    place(buf, bubble(320, 0.2, tau=0.05, rise=2.6) * 0.7, 0.004)
    sd = 0.8
    spray = u(bp(noise(sd), 500, 8000)) * curve(N(sd), [(0, 0), (0.008, 1), (0.08, 0.5), (0.6, 0), (sd, 0)]) ** 1.5
    place(buf, spray * 0.8, 0.0, pan=0.1)
    for _ in range(14):
        tt = 0.08 + 0.8 * RNG.random() ** 1.5
        place(buf, bubble(RNG.uniform(700, 3000), 0.06, tau=RNG.uniform(0.008, 0.02), rise=1.5) * RNG.uniform(0.1, 0.35),
              tt, pan=RNG.uniform(-0.5, 0.6))
    for _ in range(10):
        place(buf, bubble(RNG.uniform(150, 600), 0.1, tau=RNG.uniform(0.02, 0.04), rise=1.8) * RNG.uniform(0.1, 0.3),
              RNG.uniform(0.05, 0.9), pan=RNG.uniform(-0.2, 0.3))
    henv = curve(n, [(0, 0), (0.04, 0), (0.12, 1), (0.35, 0.8), (1.2, 0.35), (2.6, 0.05), (3.0, 0), (d, 0)])
    for ch in range(2):
        hiss = u(hp(noise(d), 2500) + 0.5 * bp(noise(d), 4000, 10000)) * henv * (0.85 + 0.15 * smooth(n, 30))
        buf[:, ch] += hiss * 0.5 + u(crackle(d, 900 * henv, 2500, 10000, grain=0.0002)) * 0.25
    return cave(buf, rt=3.2, wet=0.3)


def drip():
    """A cave drip at +0.00 ('plink': click + rising bubble), its echoes off far walls (0.19, 0.41,
    0.66, 0.95 s, alternating sides, darker each time) and a long cavern tail."""
    d = 1.4
    x0 = drop(1650, 1.8, 0.02)
    st = np.zeros((N(d), 2))
    place(st, x0, 0.0, pan=0.15)
    for k, (dt, g, pan) in enumerate(((0.19, 0.32, -0.5), (0.41, 0.2, 0.6), (0.66, 0.12, -0.3), (0.95, 0.07, 0.4))):
        place(st, lp(x0, 5000 / (k + 1) ** 0.6) * g, dt, pan=pan)
    return cave(st, rt=3.2, wet=0.45, pre=0.03)


# ============================================================================ S3: the fall

def rock_crack():
    """Stone cracking under his weight: a sharp SNAP at +0.00, micro-fractures spreading, a second crack
    at +0.45, a low strained groan of rock, grit trickling."""
    d = 1.6
    n = N(d)
    buf = np.zeros((n, 2))

    def snap(g):
        sd = 0.35
        s = u(hp(noise(sd), 900)) * decay(sd, 0.003, 0.0002)
        s += u(modal([170, 310, 540, 890], (1.0, 0.7, 0.5, 0.3), (0.04, 0.03, 0.02, 0.012), sd)) * 0.8
        s += thump(sd, 120, 60, tau=0.06) * 0.6
        return s * g

    place(buf, snap(1.0), 0.0, pan=0.0)
    place(buf, snap(0.55), 0.45, pan=0.2)
    rate = curve(n, [(0, 1500), (0.1, 800), (0.45, 900), (0.6, 200), (1.1, 0), (d, 0)])
    for ch in range(2):
        buf[:, ch] += u(crackle(d, rate, 400, 6000, grain=0.0008)) * 0.45
    groan = u(lp(noise(d, "brown"), 260)) * smooth_env(curve(n, [(0, 0), (0.1, 0.8), (0.6, 1), (1.3, 0), (d, 0)]), 10)
    place(buf, groan * rough(n, 12, 0.6, 2) * 0.5, 0.0)
    for _ in range(8):
        place(buf, stone_hit(RNG.uniform(0.0, 0.2)) * RNG.uniform(0.1, 0.25), RNG.uniform(0.2, 1.2), pan=RNG.uniform(-0.5, 0.5))
    return cave(buf, rt=2.6, wet=0.3)


def floor_collapse():
    """The floor gives way at +0.00: break crack + boom, a rumble swelling to ~0.3 s, then a long
    crumbling cascade of rock chunks dropping into the shaft (densest 0-1.5 s, getting farther and
    darker to ~3.8 s), dust hiss; ~4.6 s plus tail."""
    d = 4.6
    n = N(d)
    buf = np.zeros((n, 2))
    core = thump(d, 75, 32, tau=0.5, ptau=0.06, h2=0.3)
    core += u(bp(noise(d), 300, 3000)) * decay(d, 0.15, 0.001) * 0.7
    core += u(hp(noise(d), 1000)) * decay(d, 0.01, 0.0003) * 1.0
    core += u(bp(noise(d, "pink"), 100, 3000)) * decay(d, 0.1, 0.002) * 0.9
    core += u(lp(noise(d, "brown"), 120, 4)) * smooth_env(curve(n, [(0, 0), (0.05, 0.7), (0.3, 1), (3.5, 0.15), (d, 0)]), 8) * 0.5
    place(buf, core, 0.0)
    place(buf, stone_hit(1.0) * 0.9, 0.0)
    for _ in range(70):
        tt = 0.02 + 3.8 * RNG.random() ** 2.2
        dist = tt / 3.8
        s = stone_hit(RNG.uniform(0.1, 0.9) * (1 - 0.5 * dist))
        place(buf, lp(s, 9000 * (1 - 0.8 * dist)) * RNG.uniform(0.2, 0.6) * (1 - 0.6 * dist), tt, pan=RNG.uniform(-0.8, 0.8))
    for _ in range(6):
        tt, g, p = RNG.uniform(0.1, 1.2), RNG.uniform(0.35, 0.6), RNG.uniform(-0.6, 0.6)
        place(buf, stone_hit(RNG.uniform(0.9, 1.0)) * g, tt, pan=p)
        place(buf, thump(0.4, 110, 50, tau=0.08) * 0.8 * g, tt, pan=p)
    denv = smooth_env(curve(n, [(0, 0), (0.05, 0.4), (0.3, 1), (3.0, 0.2), (d, 0)]), 8)
    for ch in range(2):
        buf[:, ch] += u(hp(noise(d, "pink"), 1500)) * denv * rough(n, 20, 0.6, 2) * 0.15
    return cave(buf, rt=3.0, wet=0.35, taps=8)


def armor_clank():
    """His gauntlet slams onto the ledge at +0.00: hard stone hit + gauntlet clang, the body armor's
    jolt rattle 0.03-0.2 s, pebbles falling away to ~0.9 s."""
    d = 1.2
    buf = np.zeros((N(d), 2))
    place(buf, thump(0.4, 125, 70, tau=0.05) * 0.8, 0.0)
    place(buf, stone_hit(0.7) * 0.6, 0.0)
    place(buf, u(crackle(0.12, 3000, 500, 6000, grain=0.0007)) * decay(0.12, 0.02) * 0.5, 0.0)
    place(buf, metal_hit(820, 0.8, tau=0.25, hard=0.85) * 0.7, 0.002, pan=-0.15)
    for k in range(4):
        place(buf, metal_hit(RNG.uniform(320, 1200), 0.5, tau=RNG.uniform(0.08, 0.2), hard=0.7) * RNG.uniform(0.25, 0.45),
              0.03 + k * 0.045 + RNG.uniform(0, 0.02), pan=RNG.uniform(-0.3, 0.3))
    for _ in range(7):
        place(buf, lp(stone_hit(RNG.uniform(0.05, 0.3)), 6000) * RNG.uniform(0.1, 0.3), RNG.uniform(0.15, 0.9),
              pan=RNG.uniform(-0.5, 0.5))
    return cave(buf, rt=2.6, wet=0.28)


def dust_slip():
    """Gauntlet fingers sliding on dusty stone, ~4.1 s: four slips starting 0.0, 1.15, 2.2, 3.25 s
    (each a gritty metal-on-rock scrape, the last the longest), small catches (clinks) at the end of
    the first three (~0.55, 1.65, 2.85 s), dust and pebbles trickling away below."""
    d = 4.3
    n = N(d)
    buf = np.zeros((n, 2))
    env = np.zeros(n)
    slides = ((0.0, 0.55, 0.8), (1.15, 0.5, 0.7), (2.2, 0.65, 0.9), (3.25, 0.8, 1.0))
    for s, ln, g in slides:
        env += curve(n, [(0, 0), (s, 0), (s + 0.04, g), (s + ln * 0.7, g * 0.8), (s + ln, 0), (d, 0)])
    for ch in range(2):
        gr = bp(noise(d), 700, 6000) * rough(n, 120, 0.9, 2.5)
        met = rbp(gr, 1850, 25) + rbp(gr, 3100, 30) * 0.7
        buf[:, ch] += (u(gr) * 0.6 + u(met) * 0.3) * env + u(crackle(d, 900 * env, 800, 7000, grain=0.0005)) * 0.3
        tr = smooth_env(np.convolve(env, np.ones(N(0.4)) / N(0.4))[:n], 6)
        buf[:, ch] += u(bp(noise(d, "pink"), 1500, 8000)) * tr * rough(n, 30, 0.7, 2) * 0.12
    for s, ln, g in slides[:3]:
        place(buf, metal_hit(RNG.uniform(1400, 2200), 0.3, tau=0.05, hard=0.7) * 0.3 * g, s + ln, pan=-0.1)
    for _ in range(16):
        place(buf, lp(stone_hit(RNG.uniform(0.05, 0.3)), 5000) * RNG.uniform(0.08, 0.22), RNG.uniform(0.2, 4.1),
              pan=RNG.uniform(-0.6, 0.6))
    return cave(buf, rt=2.4, wet=0.3)


def sword_stab():
    """Both hands ram the sword into the shaft wall at +0.00: a CHANK - blade clang (long ring), rock
    crunch, weight thump - with a spray of sparks (to ~0.6 s)."""
    d = 1.8
    t = t_axis(d)
    x = metal_hit(640, d, tau=0.7, hard=0.85, ratios=BAR, beat=0.5) * 0.8
    x += metal_hit(1150, d, tau=0.4, hard=0.9) * 0.35
    x += np.pad(stone_hit(0.8), (0, N(d)))[: N(d)] * 0.7
    x += thump(d, 130, 60, tau=0.09, ptau=0.02) * 0.9
    x += u(crackle(d, 4000 * np.exp(-t / 0.05), 400, 7000, grain=0.0008)) * 0.6
    buf = pan2(x, 0.0)
    for ch in range(2):
        buf[:, ch] += u(crackle(d, 1500 * np.exp(-t / 0.25), 5000, 14000, grain=0.00015, alpha=1.3)) * 0.3
    return cave(buf, rt=2.4, wet=0.28)


def sword_scrape():
    """4.70 s: the blade gouging down the shaft wall - a screaming metal squeal (blade modes driven by
    stick-slip friction, pitch sinking as the fall slows), grinding rock, crackling sparks and soil;
    it starts juddering ~3.4 s and fades out over the last 0.1 s, so heavy_impact (+4.65) takes over."""
    d = 4.7
    n = N(d)
    t = t_axis(d)
    speed = curve(n, [(0, 1.0), (0.4, 1.0), (2.4, 0.78), (3.8, 0.5), (d, 0.38)])
    jph = np.cumsum(curve(n, [(0, 13), (d, 8)])) / SR
    judder = 1 - np.clip((t - 3.3) / 0.6, 0, 1) * 0.55 * (1 - (0.5 + 0.5 * np.sin(2 * np.pi * jph)) ** 2)
    fr, gate = glottal((140 + 220 * speed) * (1 + 0.12 * smooth(n, 15)), oq=0.35, rq=0.5, jitter=0.12, shimmer=0.45)
    fr = rmsn(fr) + rmsn(hp(noise(d), 1000)) * (0.25 + gate / gate.max()) * 0.6
    scale = (0.7 + 0.3 * speed) * (1 + 0.03 * smooth(n, 2.5) + 0.008 * smooth(n, 11))
    sq = np.zeros(n)
    for f, bw, a in ((2240, 22, 1.0), (3390, 30, 0.8), (5020, 40, 0.55), (6870, 55, 0.35), (9150, 80, 0.2)):
        sq += rmsn(reson(fr, f * scale, bw)) * a
    sph = 2 * np.pi * np.cumsum(2950 * scale * (1 + 0.015 * smooth(n, 9))) / SR
    squeal = (np.sin(sph) + 0.25 * np.sin(2 * sph)) * np.clip(0.45 + 0.7 * smooth(n, 7), 0, None) ** 1.5
    screech = (rmsn(sq) * 0.75 + rmsn(squeal) * 0.45) * judder
    env = curve(n, [(0, 0), (0.03, 1), (4.4, 0.85), (4.6, 0.6), (d, 0)])
    buf = pan2(screech * env * 0.9, 0.0)
    for ch in range(2):
        grind = rmsn(bp(noise(d, "pink"), 120, 1600) * rough(n, 110, 0.9, 2.0)) * 0.6 \
            + u(crackle(d, 900 * speed, 250, 2500, grain=0.0018)) * 1.2
        sparks = u(crackle(d, 320 * speed ** 1.5, 5500, 15000, grain=0.00015, alpha=1.25)) * 2.0
        buf[:, ch] += (grind * 0.55 + sparks) * env
    for _ in range(40):
        place(buf, stone_hit(RNG.uniform(0.0, 0.3)) * RNG.uniform(0.3, 0.9), RNG.uniform(0.05, 4.5), pan=RNG.uniform(-0.6, 0.6))
    return fit(cave(buf, rt=2.2, wet=0.22), d, fo=0.1)


def heavy_impact():
    """He hits the bottom at +0.00: a massive low boom (decays ~1 s), the body thud, an armor CRASH
    (plates clashing 0-0.08 s, rattling to ~0.35), gravel crunch, rubble, a dust burst; grotto tail."""
    d = 2.6
    n = N(d)
    buf = np.zeros((n, 2))
    core = thump(d, 85, 28, tau=0.45, ptau=0.06, h2=0.3) + thump(d, 160, 80, tau=0.08, ptau=0.02, h2=0.3) * 0.7
    core += thump(d, 330, 230, tau=0.035, ptau=0.01) * 0.45
    core += u(lp(noise(d, "pink"), 300)) * decay(d, 0.05, 0.002) * 0.7
    core += u(bp(noise(d, "pink"), 250, 2500)) * decay(d, 0.04, 0.001) * 0.6
    core += u(bp(noise(d, "pink"), 300, 4000)) * decay(d, 0.35, 0.01) * 0.45
    place(buf, core, 0.0)
    grate = curve(n, [(0, 6000), (0.05, 2000), (0.3, 100), (0.6, 0), (d, 0)])
    for ch in range(2):
        buf[:, ch] += u(crackle(d, grate, 300, 6000, grain=0.001)) * 0.45
    for _ in range(9):
        place(buf, metal_hit(RNG.uniform(280, 1100), 1.0, tau=RNG.uniform(0.15, 0.45), hard=0.8) * RNG.uniform(0.3, 0.6),
              RNG.uniform(0.0, 0.08), pan=RNG.uniform(-0.5, 0.5))
    for _ in range(4):
        place(buf, metal_hit(RNG.uniform(600, 1800), 0.5, tau=0.1, hard=0.7) * RNG.uniform(0.15, 0.3),
              RNG.uniform(0.1, 0.35), pan=RNG.uniform(-0.5, 0.5))
    for _ in range(12):
        place(buf, stone_hit(RNG.uniform(0.2, 0.6)) * RNG.uniform(0.15, 0.4), 0.02 + 0.9 * RNG.random() ** 1.5,
              pan=RNG.uniform(-0.8, 0.8))
    return cave(buf, rt=2.4, wet=0.3)


def armor_clatter():
    """Armor settling after the impact: a loose plate bouncing (hits 0.0, 0.17, 0.31, 0.42, 0.5, 0.56 s,
    decaying) and a rattle of smaller pieces, done by ~1.2 s."""
    d = 1.6
    buf = np.zeros((N(d), 2))
    f0 = RNG.uniform(500, 700)
    tt, gap, g = 0.0, 0.17, 1.0
    while g > 0.08:
        place(buf, metal_hit(f0 * RNG.uniform(0.97, 1.03), 0.6, tau=0.2, hard=0.75) * g, tt, pan=0.25)
        tt += gap
        gap *= 0.8
        g *= 0.72
    for _ in range(8):
        place(buf, metal_hit(RNG.uniform(900, 2600), 0.3, tau=RNG.uniform(0.04, 0.1), hard=0.7) * RNG.uniform(0.15, 0.35),
              RNG.uniform(0.0, 0.9) ** 1.3, pan=RNG.uniform(-0.4, 0.4))
    return cave(buf, rt=2.0, wet=0.25)


# ============================================================================ S4: the depths

def anger_groan():
    """Anger, dazed at the bottom: a deep pained 'mmh-UHHH...' - f0 88 -> 101 Hz on the effort (+0.35 s),
    falling to ~80 by 1.25 s and breaking into creaky fry (1.4-1.95 s), breathy, a breath out to ~2.3 s."""
    d = 2.4
    n = N(d)
    f0 = curve(n, [(0, 88), (0.12, 95), (0.35, 101), (0.8, 93), (1.25, 82), (1.5, 72), (1.75, 56), (2.0, 48), (d, 48)])
    amp = curve(n, [(0, 0), (0.05, 0.3), (0.16, 0.65), (0.4, 1.0), (0.8, 0.85), (1.2, 0.62), (1.5, 0.38),
                    (1.8, 0.14), (1.98, 0), (d, 0)])
    amp = smooth_env(amp, 25) * (1 + 0.06 * smooth(n, 7))
    breath = curve(n, [(0, 0.35), (0.35, 0.2), (1.1, 0.3), (1.8, 0.6), (d, 0.7)])
    shim = curve(n, [(0, 0.06), (1.3, 0.1), (1.9, 0.3), (d, 0.3)])
    diplo = curve(n, [(0, 0.0), (1.3, 0.05), (1.8, 0.3), (d, 0.3)])
    oq = curve(n, [(0, 0.62), (0.4, 0.55), (1.6, 0.5), (d, 0.45)])
    tr = tract([(0, "mm"), (0.12, "mm"), (0.26, "uh"), (1.2, "uh"), (1.75, "oh"), (d, "oh")], n, scale=0.93)
    v = voice(f0, amp, tr, breath=breath, oq=oq, jitter=0.014, shimmer=shim, diplo=diplo, drift=0.012)
    be = smooth_env(curve(n, [(0, 0), (1.55, 0), (1.85, 1), (2.3, 0), (d, 0)]), 20)
    br = cascade(bp(noise(d, "pink"), 200, 5000) * be, tract([(0, "uh")], n, 0.93))
    x = lp(u(v) + u(br) * 0.12, 6000)
    return cave(pan2(x, -0.1), rt=1.7, wet=0.18)


def pebbles_shift():
    """Somewhere in the dark (right) a few pebbles shift: a small grind (0-0.12) and three little
    tumbling runs of ticks (0.05, 0.35, 0.7 s)."""
    d = 1.5
    buf = np.zeros((N(d), 2))
    gd = 0.14
    place(buf, u(bp(noise(gd), 600, 4000) * rough(N(gd), 80, 0.9, 2)) * np.sin(np.pi * np.arange(N(gd)) / N(gd)) * 0.45,
          0.0, pan=0.35)
    place(buf, stone_hit(0.42) * 0.7, 0.04, pan=0.35)
    for s0 in (0.05, 0.35, 0.7):
        tt, gap, g = s0, RNG.uniform(0.07, 0.12), RNG.uniform(0.6, 1.0)
        while g > 0.1:
            place(buf, stone_hit(RNG.uniform(0.02, 0.22)) * g, tt, pan=0.35 + RNG.uniform(-0.15, 0.15))
            tt += gap
            gap *= RNG.uniform(0.72, 0.9)
            g *= 0.78
    return cave(buf, rt=2.0, wet=0.3)


def monster_growl():
    """The crawler's low growl approaching out of the dark: two rough phrases (0.1-1.7 s, then
    1.95-4.05 s, louder, peak ~3.1 s): f0 ~58-78 Hz with heavy jitter + diplophonia (subharmonic rattle),
    throat flutter, raspy turbulence through a snarling tract; drifting in from the right."""
    d = 4.3
    n = N(d)
    f0 = curve(n, [(0, 60), (0.7, 70), (1.7, 58), (1.95, 62), (2.8, 78), (3.4, 72), (4.1, 56), (d, 54)])
    amp = curve(n, [(0, 0), (0.1, 0), (0.45, 0.45), (1.2, 0.6), (1.65, 0.12), (1.8, 0.05), (2.0, 0.12), (2.5, 0.75),
                    (3.1, 1.0), (3.7, 0.85), (4.05, 0.05), (4.15, 0), (d, 0)])
    amp = smooth_env(amp, 20)
    flut = 1 + 0.35 * np.sin(2 * np.pi * np.cumsum(27 * (1 + 0.15 * smooth(n, 4))) / SR)
    tr = tract([(0, "oh"), (1.0, "uh"), (2.0, "oh"), (3.0, "ah"), (d, "uh")], n, scale=0.95)
    v = voice(f0, amp * flut, tr, breath=0.35, oq=0.5, rq=0.65, jitter=0.07, shimmer=0.3, diplo=0.35,
              drift=0.03, asp=(300, 5000), par=((170, 90, 0.6), (340, 120, 0.25)))
    rasp = cascade(bp(noise(d, "pink"), 300, 4000) * amp * rough(n, 35, 0.8, 2), tract([(0, "uh")], n, 0.95, 2.0))
    drool = u(wet(d, 9.0 * (amp > 0.25), 800, 3000, tau=(0.003, 0.008))) * 0.1
    x = lp(u(v) + u(rasp) * 0.25 + drool, 5000)
    return cave(pan2(x, curve(n, [(0, 0.3), (d, 0.05)])), rt=2.4, wet=0.32, pre=0.025)


def monster_hiss():
    """The crawler's head looms, jaw opening: a wet saliva click (0-0.08), a snarling hiss peaking ~0.2 s,
    held with tremor to ~1.1 s and dying by 1.6 s, a rough throaty snarl underneath, wet crackles."""
    d = 1.9
    n = N(d)
    x = np.zeros(n)
    jd = 0.12
    jaw = u(crackle(jd, 2500, 1000, 6000, grain=0.0005)) * decay(jd, 0.04) * 0.4 \
        + u(bp(noise(jd, "pink"), 200, 1200)) * decay(jd, 0.015, 0.002) * 0.3
    place(x, jaw, 0.0)
    henv = smooth_env(curve(n, [(0, 0), (0.05, 0), (0.2, 1.0), (0.45, 0.85), (1.1, 0.7), (1.6, 0), (d, 0)]), 15) \
        * (1 + 0.15 * smooth(n, 11))
    hn = noise(d)
    hiss = (u(cascade(hp(hn, 1200), tract([(0, "ah")], n, 1.25, 3.0))) * 0.4 + u(bp(hn, 3000, 9000)) * 0.6) * henv
    f0 = curve(n, [(0, 120), (0.05, 120), (0.25, 145), (0.8, 110), (1.3, 90), (d, 90)])
    sa = smooth_env(curve(n, [(0, 0), (0.06, 0), (0.22, 1), (0.7, 0.6), (1.2, 0), (d, 0)]), 20)
    snarl = voice(f0, sa, tract([(0, "ah")], n, 1.2), breath=0.6, oq=0.5, jitter=0.08, shimmer=0.35, diplo=0.3, asp=(500, 6000))
    x += hiss + u(snarl) * 0.45 + u(wet(d, 45 * henv, 900, 3500)) * 0.15
    return cave(pan2(x, 0.05), rt=1.8, wet=0.22)


def drool_drip():
    """A viscous strand of drool stretching (0-0.38 s, soft sticky crackle) and landing with a wet
    'plap' at +0.40 s."""
    d = 0.9
    n = N(d)
    x = np.zeros(n)
    se = curve(n, [(0, 0), (0.05, 0.6), (0.3, 1), (0.38, 0), (d, 0)])
    x += u(wet(d, 160 * se, 500, 2500, tau=(0.004, 0.012), rise=(0.6, 1.4))) * 0.18
    x += u(tv_filter(noise(d, "pink"), curve(n, [(0, 400), (0.38, 900), (d, 900)]), q=6) * se) * 0.06
    place(x, splat(1.2), 0.40)
    sd = 0.3
    place(x, u(wet(sd, 600 * np.exp(-t_axis(sd) / 0.06), 400, 2000, tau=(0.004, 0.012), rise=(0.6, 1.3))) * 0.35, 0.41)
    return cave(pan2(x, 0.05), rt=1.6, wet=0.15)


def rock_whoosh():
    """A thrown rock flying in from the dark at screen-left, tumbling (14 Hz flutter), swelling; it
    arrives at +0.35 s (= rock_hit) and cuts off there."""
    d = 0.4
    n = N(d)
    t = t_axis(d)
    hit = 0.35
    wh = tv_filter(noise(d, "pink"), curve(n, [(0, 380), (hit, 1300), (d, 1300)], log=True), q=1.6)
    flut = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 7 * t))
    env = np.where(t < hit, (t / hit) ** 2.2, np.exp(-(t - hit) / 0.008))
    return fit(pan2(u(wh) * flut * env, curve(n, [(0, -0.85), (hit, -0.05), (d, -0.05)])), d, fo=0.02)


def rock_bonk():
    """CLONK at +0.00: the hollow 'tonk' of a rock on the crawler's skull (430 Hz body with a slight pitch
    drop, ~160 ms ring), a hard stone click, a skull thud; the rock drops and bounces at +0.42 and
    +0.62, then rolls to ~0.95 s."""
    d = 1.3
    t = t_axis(d)
    ph = 2 * np.pi * np.cumsum(430 * (1 + 0.09 * np.exp(-t / 0.025))) / SR
    tonk = sum(a * np.sin(r * ph) * np.exp(-t / tau) for r, a, tau in
               ((1, 1.0, 0.16), (2.32, 0.45, 0.07), (3.95, 0.22, 0.035), (5.6, 0.1, 0.02)))
    tonk = u(tonk * np.clip(t / 0.0006, 0, 1))
    x = tonk + u(hp(noise(d), 2000)) * decay(d, 0.0008, 0.0002) * 0.55 + thump(d, 170, 95, tau=0.035, ptau=0.01) * 0.55
    buf = pan2(x, 0.0)
    place(buf, stone_hit(0.3) * 0.3, 0.0)
    place(buf, stone_hit(0.45) * 0.35, 0.42, pan=0.1)
    place(buf, stone_hit(0.38) * 0.22, 0.62, pan=0.15)
    for k in range(6):
        place(buf, stone_hit(0.12) * 0.1 * 0.8 ** k, 0.7 + k * 0.045, pan=0.2)
    return cave(buf, rt=1.8, wet=0.22)


def body_thud():
    """The knocked-out crawler drops at +0.00 (body thud + flesh slap), head and limbs flop at +0.13
    with claws clattering, a little gravel."""
    d = 1.0
    buf = np.zeros((N(d), 2))
    slap = u(bp(noise(0.3), 250, 2500)) * decay(0.3, 0.02, 0.001)
    body = thump(0.8, 110, 48, tau=0.12, ptau=0.03, h2=0.3) + u(lp(noise(0.8, "pink"), 300)) * decay(0.8, 0.05, 0.002) * 0.6
    body += thump(0.8, 300, 210, tau=0.03, ptau=0.01) * 0.35
    place(buf, body, 0.0)
    place(buf, slap * 0.5, 0.0)
    place(buf, thump(0.4, 140, 70, tau=0.05) * 0.5, 0.13, pan=0.15)
    place(buf, slap * 0.35, 0.13, pan=0.15)
    for _ in range(5):
        place(buf, claw() * RNG.uniform(0.2, 0.4), RNG.uniform(0.12, 0.3), pan=RNG.uniform(-0.2, 0.3))
    for ch in range(2):
        buf[:, ch] += u(crackle(d, curve(N(d), [(0, 1500), (0.2, 0), (d, 0)]), 400, 5000, grain=0.001)) * 0.25
    return cave(buf, rt=1.8, wet=0.22)


def tail_grab():
    """The leather glove shoots out of the dark (sleeve swish 0-0.07) and grabs the slick tail at
    +0.08: wet slap + squish, then the leather creaks as it tightens (0.12-0.5 s)."""
    d = 0.8
    buf = np.zeros((N(d), 2))
    sw = whoosh(0.1, 600, 1800, q=1.4) * np.sin(np.pi * np.arange(N(0.1)) / N(0.1)) ** 2
    place(buf, u(sw) * 0.3, 0.0, pan=-0.5)
    g = 0.08
    place(buf, u(bp(noise(0.15), 300, 3000)) * decay(0.15, 0.012, 0.0008) * 0.8 + thump(0.15, 180, 110, tau=0.025) * 0.6, g, pan=-0.3)
    sq = tv_filter(noise(0.2, "pink"), curve(N(0.2), [(0, 900), (0.2, 500)]), q=4) * decay(0.2, 0.05, 0.003)
    place(buf, u(sq) * 0.4, g + 0.01, pan=-0.3)
    ce = curve(N(0.4), [(0, 0), (0.05, 1), (0.3, 0.6), (0.4, 0)])
    place(buf, creak(0.4, 55, 85) * ce * 0.35, g + 0.04, pan=-0.35)
    return cave(buf, rt=1.5, wet=0.18)


def drag():
    """1.8 s: the limp crawler hauled off over gravel into the dark at screen-left in three tugs
    (0.0, 0.62, 1.2 s): gravel crunch, body scrape, claws ticking, receding left and darker."""
    d = 1.9
    n = N(d)
    t = t_axis(d)
    env = np.zeros(n)
    for s, ln in ((0.0, 0.5), (0.62, 0.5), (1.2, 0.55)):
        env += curve(n, [(0, 0), (s, 0), (s + 0.06, 1), (s + ln * 0.6, 0.8), (s + ln, 0.15), (s + ln + 0.06, 0), (d, 0)])
    env *= curve(n, [(0, 1), (d, 0.55)])
    pan = curve(n, [(0, 0.0), (d, -0.75)])
    cut = curve(n, [(0, 9000), (d, 2500)], log=True)
    buf = np.zeros((n, 2))
    for ch in range(2):
        gr = u(crackle(d, 2500 * env, 400, 6000, grain=0.0012)) * 0.7
        sc = u(bp(noise(d, "pink"), 150, 2500) * rough(n, 60, 0.7, 1.5)) * env * 0.5
        lo = u(lp(noise(d, "brown"), 180)) * env * 0.4
        buf[:, ch] = tv_filter(gr + sc + lo, cut, q=0.707, kind="lp")
    buf = buf * pan2(np.ones(n), pan)
    for _ in range(8):
        tt = RNG.uniform(0.05, 1.6)
        place(buf, lp(stone_hit(RNG.uniform(0.1, 0.3)), 9000 * (1 - 0.6 * tt / d)) * RNG.uniform(0.15, 0.35) * (1 - 0.4 * tt / d),
              tt, pan=float(np.interp(tt, t, pan)))
    for _ in range(6):
        tt = RNG.uniform(0.05, 1.5)
        place(buf, claw() * RNG.uniform(0.1, 0.25), tt, pan=float(np.interp(tt, t, pan)))
    return cave(buf, rt=1.8, wet=0.25)


def crunching():
    """~3.5 s from the dark at screen-left: eight chomps (~0.0, 0.38, 0.75, 1.15, 1.52, 1.95, 2.33,
    2.75 s) - bone snaps on the 1st, 3rd and 5th - wet squelches and saliva, lip smacks, a slurp
    (~2.95 s) and a gulp (~3.3 s)."""
    d = 3.6
    n = N(d)
    x = np.zeros(n)
    chomps = (0.0, 0.38, 0.75, 1.15, 1.52, 1.95, 2.33, 2.75)
    strength = (1.0, 0.85, 1.0, 0.7, 0.9, 0.6, 0.75, 0.5)
    bone = (1, 0, 1, 0, 1, 0, 0, 0)
    for tc, g, b in zip(chomps, strength, bone):
        tc = max(0.0, tc + RNG.uniform(-0.02, 0.02))
        cd = 0.3
        ct = t_axis(cd)
        cr = u(crackle(cd, 6000 * np.exp(-ct / 0.025), 900, 6500, grain=0.0006, alpha=1.4)) * 0.55
        cr += u(crackle(cd, 2500 * np.exp(-ct / 0.035), 250, 2000, grain=0.002)) * 0.4
        cr += thump(cd, 260, 150, tau=0.012) * 0.25
        if b:
            cr += u(modal(RNG.uniform(1700, 2700, 3), (1.0, 0.6, 0.4), (0.006, 0.004, 0.003), cd)) * 0.4
            cr += u(hp(noise(cd), 1500)) * decay(cd, 0.0015, 0.0002) * 0.3 + thump(cd, 220, 140, tau=0.02) * 0.35
        cr = lp(cr, RNG.uniform(3500, 7000))
        cr += u(wet(cd, 1200 * np.exp(-ct / 0.07), 350, 1600, tau=(0.004, 0.012))) * 0.6
        sq = tv_filter(noise(cd, "pink"), curve(N(cd), [(0, 500), (cd, 900)]), q=3) * decay(cd, 0.06, 0.004) * rough(N(cd), 50, 0.7, 2)
        cr += u(sq) * 0.2 + u(wet(cd, 60, 1500, 4000)) * 0.15
        place(x, cr * g, tc)
        sm = u(bp(noise(0.05), 500, 3500)) * decay(0.05, 0.008, 0.0005) * 0.3
        place(x, sm * g, tc + RNG.uniform(0.18, 0.24))
    sd = 0.35
    sn = N(sd)
    sl = tv_filter(noise(sd), curve(sn, [(0, 800), (sd, 2500)], log=True), q=5) * rough(sn, 40, 0.8, 2) \
        * np.sin(np.pi * np.arange(sn) / sn) ** 1.5
    place(x, u(sl) * 0.4, 2.95)
    place(x, thump(0.15, 180, 110, tau=0.03) * 0.5 + u(bp(noise(0.15), 300, 1500)) * decay(0.15, 0.015, 0.002) * 0.3, 3.3)
    return cave(pan2(lp(x, 8000), -0.45), rt=1.6, wet=0.25)


# ============================================================================ S5: the voice

def armor_scrape():
    """Anger shoving himself back against the rock wall: two pushes of plate scraping on rock (0.0-0.6,
    0.75-1.35 s) with metallic grind and grit, the body settling (thud + leather creak ~0.62), clinks
    at 0.05, 0.64 and 1.3 s."""
    d = 1.6
    n = N(d)
    buf = np.zeros((n, 2))
    env = curve(n, [(0, 0), (0.04, 0.8), (0.4, 1.0), (0.6, 0), (0.75, 0), (0.8, 0.7), (1.15, 0.8), (1.35, 0), (d, 0)])
    for ch in range(2):
        gr = bp(noise(d), 600, 5000) * rough(n, 110, 0.85, 2)
        met = rbp(gr, 1550, 30) + rbp(gr, 2420, 35) * 0.8 + rbp(gr, 3650, 40) * 0.5
        buf[:, ch] += (u(gr) * 0.45 + u(met) * 0.35 + u(crackle(d, 800 * env, 600, 5000, grain=0.0006)) * 0.25) * env
    place(buf, thump(0.4, 95, 55, tau=0.08) * 0.7, 0.62)
    place(buf, creak(0.25, 60, 90) * curve(N(0.25), [(0, 0), (0.04, 1), (0.25, 0)]) * 0.25, 0.55, pan=-0.1)
    for tt in (0.05, 0.64, 1.3):
        place(buf, metal_hit(RNG.uniform(700, 1600), 0.4, tau=0.08, hard=0.7) * 0.3, tt, pan=RNG.uniform(-0.2, 0.2))
    return cave(buf, rt=1.6, wet=0.18)


# ============================================================================ S6: the friend

def saliva_drip():
    """A thick drop of the friend's saliva landing on Anger's cheek: a wet 'plap' at +0.02 with tiny
    splatter, a sticky trickle after."""
    d = 0.6
    n = N(d)
    x = np.zeros(n)
    place(x, splat(1.3), 0.02)
    x += u(wet(d, curve(n, [(0, 0), (0.08, 0), (0.12, 90), (0.4, 0), (d, 0)]), 500, 2500, tau=(0.003, 0.01))) * 0.15
    return cave(pan2(x, 0.0), rt=1.2, wet=0.1)


def _brass(f, d, tau=0.55):
    t = t_axis(d)
    x = np.zeros_like(t)
    for k in range(1, int(4500 / f) + 1):
        tk = tau / (1 + 0.22 * (k - 1))
        x += (1 / k) * np.sin(2 * np.pi * k * f * t + RNG.uniform(0, 2 * np.pi)) * np.exp(-t / tk)
    return x * np.clip(t / 0.012, 0, 1)


def startle_sting():
    """Anger startled awake: an orchestral HIT at +0.00 (D-minor brass stab + timpani + low drum +
    splash) and his sharp intake gasp (+0.04 to ~0.35 s); short hall tail."""
    d = 1.6
    n = N(d)
    buf = np.zeros((n, 2))
    brass = np.zeros((n, 2))
    for f, p in ((73.42, -0.3), (110.0, 0.3), (146.83, -0.15), (174.61, 0.2), (220.0, -0.35), (293.66, 0.35)):
        for c in (-4, 0, 4):
            place(brass, _brass(f * 2 ** (c / 1200), d, tau=0.32), 0.0, pan=p + c / 20)
    buf += u(brass) * 0.42
    drums = sat(thump(d, 120, 73, tau=0.35, ptau=0.02, h2=0.3), 2.0) + u(bp(noise(d), 100, 900)) * decay(d, 0.02, 0.0008) * 0.6
    drums += thump(d, 75, 45, tau=0.25, ptau=0.03) * 0.9 + u(bp(noise(d), 1000, 8000)) * decay(d, 0.012, 0.0005) * 0.35
    place(buf, u(drums), 0.0)
    for ch in range(2):
        buf[:, ch] += u(hp(noise(d), 4000)) * decay(d, 0.35, 0.002) * 0.22
    gd = 0.4
    gn = N(gd)
    ge = smooth_env(curve(gn, [(0, 0), (0.04, 0.9), (0.1, 1.0), (0.24, 0.6), (0.31, 0), (gd, 0)]), 40)
    gasp = cascade(bp(noise(gd), 400, 6000) * ge, tract([(0, "ah"), (0.3, "uh"), (gd, "uh")], gn, 0.93))
    va = smooth_env(curve(gn, [(0, 0), (0.01, 0.5), (0.05, 0), (0.26, 0), (0.29, 0.25), (0.33, 0), (gd, 0)]), 60)
    catch = voice(np.full(gn, 128.0), va, tract([(0, "uh")], gn, 0.93), breath=0.4)
    place(buf, u(gasp) * 0.6 + u(catch) * 0.2, 0.04, pan=-0.1)
    return cave(buf, rt=1.8, wet=0.3)


def creature_huff():
    """The friend's indignant huff through its huge nose: a short nasal grunt 'hm' (0-0.16) and a big
    nasal blast of air (peak ~0.09 s, decaying to ~0.7 s) with a nostril flutter."""
    d = 0.9
    n = N(d)
    t = t_axis(d)
    f0 = curve(n, [(0, 80), (0.16, 64), (d, 60)])
    va = smooth_env(curve(n, [(0, 0), (0.012, 1), (0.1, 0.7), (0.17, 0), (d, 0)]), 50)
    grunt = voice(f0, va, tract([(0, "mm")], n, 0.72), breath=0.25, oq=0.55, jitter=0.02, shimmer=0.08)
    ae = smooth_env(curve(n, [(0, 0), (0.03, 0.4), (0.09, 1), (0.3, 0.45), (0.7, 0), (d, 0)]), 30)
    fl = 1 + 0.3 * np.sin(2 * np.pi * 38 * t) * np.exp(-t / 0.2)
    nz = bp(noise(d, "pink"), 120, 6000) * ae * fl
    air = u(cascade(nz, tract([(0, "mm")], n, 0.72))) + u(hp(nz, 1500)) * 0.35 + u(reson(nz, 900, 250)) * 0.3
    return cave(pan2(u(grunt) * 0.6 + u(air), 0.1), rt=1.8, wet=0.2)


def stomp():
    """One ENORMOUS footfall of the friend at +0.00 (soft attack, peak within ~15 ms): a deep sub boom
    (62 -> 27 Hz) and a furry thud, a low rumble tail (~1 s), ground-shake pebble rattle 0.03-0.5 s and
    dust/grit falling from the ceiling to ~1.6 s."""
    d = 2.0
    n = N(d)
    buf = np.zeros((n, 2))
    core = thump(d, 62, 27, tau=0.3, ptau=0.07, h2=0.3, att=0.004)
    core += thump(d, 150, 85, tau=0.1, ptau=0.02, h2=0.3, att=0.004) * 0.8
    core += thump(d, 320, 220, tau=0.035, ptau=0.01, att=0.004) * 0.45
    core += u(lp(noise(d, "pink"), 450, 4)) * decay(d, 0.04, 0.004) * 0.6
    core += u(bp(noise(d, "pink"), 150, 900)) * decay(d, 0.06, 0.006) * 0.5
    ct = t_axis(d)
    core += u(crackle(d, 5000 * np.exp(-ct / 0.03), 300, 5000, grain=0.0012)) * 0.5
    core += u(lp(noise(d, "brown"), 90, 4)) * smooth_env(curve(n, [(0, 0), (0.02, 1), (0.3, 0.6), (1.4, 0), (d, 0)]), 10) * 0.35
    place(buf, core, 0.0)
    for _ in range(25):
        tt = 0.03 + 0.47 * RNG.random() ** 1.7
        place(buf, stone_hit(RNG.uniform(0.0, 0.15)) * RNG.uniform(0.08, 0.2) * (1 - tt), tt, pan=RNG.uniform(-0.8, 0.8))
    for _ in range(7):
        place(buf, lp(stone_hit(RNG.uniform(0.05, 0.3)), 6000) * RNG.uniform(0.1, 0.25), RNG.uniform(0.35, 1.6),
              pan=RNG.uniform(-0.7, 0.7))
    de = smooth_env(curve(n, [(0, 0), (0.05, 0), (0.15, 1), (1.6, 0), (d, 0)]), 8)
    for ch in range(2):
        buf[:, ch] += u(hp(noise(d, "pink"), 2000)) * de * rough(n, 25, 0.6, 2) * 0.06
    return cave(buf, rt=2.0, wet=0.3)


def foot_tap_heavy():
    """The friend tapping its foot, impatient: five slow heavy taps at 0.0, 1.0, 2.0, 3.0, 4.0 s
    (each a low padded thud with a little pebble rattle); 5.0 s."""
    d = 5.0
    buf = np.zeros((N(d), 2))
    for k, g in enumerate((1.0, 0.9, 1.0, 0.92, 0.96)):
        tap = thump(0.8, 85, 50, tau=0.12, ptau=0.03, h2=0.25, att=0.004) \
            + thump(0.8, 175, 110, tau=0.04, ptau=0.015, h2=0.3, att=0.003) * 0.6 \
            + thump(0.8, 300, 230, tau=0.025, ptau=0.01, att=0.003) * 0.35 \
            + u(lp(noise(0.8, "pink"), 400)) * decay(0.8, 0.025, 0.003) * 0.4
        place(buf, tap * g, float(k), pan=0.15)
        for _ in range(3):
            place(buf, stone_hit(RNG.uniform(0.0, 0.12)) * RNG.uniform(0.05, 0.12), k + RNG.uniform(0.02, 0.2),
                  pan=RNG.uniform(-0.5, 0.6))
    return fit(cave(buf, rt=1.8, wet=0.22), d, fo=0.3)


def creature_snort():
    """The friend's big wet snort at +0.00: an ingressive nasal snort with palatal flutter and mucus
    crackle (0-0.31 s, closing with a wet 'gk'), then a short 'pff' of air through the lips (0.42-0.75)."""
    d = 1.1
    n = N(d)
    t = t_axis(d)
    fl = curve(n, [(0, 30), (0.3, 24), (d, 24)])
    dg, g = glottal(fl, oq=0.5, rq=0.5, jitter=0.12, shimmer=0.45)
    on = t < 0.31
    exc = rmsn(dg, on) * 0.8 + rmsn(lp(bp(noise(d), 120, 4000), 2500), on) * (0.1 + (g / g.max()) ** 2) * 0.7
    env = smooth_env(curve(n, [(0, 0), (0.03, 0.6), (0.2, 1.0), (0.29, 0.9), (0.31, 0), (d, 0)]), 60)
    e = exc * env
    snort = u(cascade(e, tract([(0, "mm")], n, 0.72, 1.5))) + u(reson(e, 200, 90)) * 0.6 + u(bp(e, 1200, 3500)) * 0.08
    mucus = u(wet(d, curve(n, [(0, 0), (0.04, 300), (0.3, 200), (0.33, 0), (d, 0)]), 500, 2200, tau=(0.003, 0.01))) * 0.25
    x = lp(u(snort), 3500) + mucus
    place(x, u(bp(noise(0.08, "pink"), 300, 2500)) * decay(0.08, 0.01, 0.001) * 0.3 + thump(0.08, 260, 150, tau=0.012) * 0.3, 0.3)
    pd = 0.4
    pe = smooth_env(curve(N(pd), [(0, 0), (0.01, 1), (0.08, 0.6), (0.33, 0), (pd, 0)]), 40)
    puff = cascade(bp(noise(pd, "pink"), 200, 5000) * pe, tract([(0, "oo")], N(pd), 0.8))
    place(x, u(puff) * 0.35 + thump(pd, 140, 90, tau=0.012) * 0.15, 0.42)
    return cave(pan2(x, 0.1), rt=1.8, wet=0.2)


def creature_giggle():
    """The friend giggling behind its paws: muffled nasal 'hm-hm-hm' pulses from a huge body, bouncing in
    pitch (~95-185 Hz), three phrases - 5 pulses from 0.06 s (every ~0.128 s), a snorty intake at 0.76,
    7 pulses from 0.92 s (~0.118 s), an intake at 1.84, 4 softer dying pulses from 1.98 s (~0.125 s) -
    then a soft nasal sigh 2.42-2.85 s (Anger's throat clear lands at +2.40 in the timeline)."""
    d = 3.1
    n = N(d)
    f0 = np.full(n, 125.0)
    amp = np.zeros(n)
    leak = np.zeros(n)
    phrases = ((0.06, 5, 0.128, 150, 115, 0.85, 0.7), (0.92, 7, 0.118, 156, 112, 1.0, 0.55),
               (1.98, 4, 0.125, 132, 100, 0.5, 0.2))
    for s, k, p, fh, fl, a0, a1 in phrases:
        for i in range(k):
            ts = s + i * p + RNG.uniform(-0.008, 0.008)
            fr = i / max(1, k - 1)
            fc = (fh + (fl - fh) * fr) * (1 + 0.045 * (1 if i % 2 == 0 else -1))
            dur = p * 0.7
            i0 = N(ts)
            i1 = min(n, i0 + N(dur))
            tt = np.arange(i1 - i0) / SR
            f0[i0:i1] = fc * (1.12 - 0.12 * np.clip(tt / dur, 0, 1))
            amp[i0:i1] = (a0 + (a1 - a0) * fr) * np.clip(tt / 0.012, 0, 1) * (1 - tt / dur) ** 0.8
            if RNG.random() < 0.4:
                leak[i0:i1] = amp[i0:i1] * 0.8
    f0 = smooth_env(f0, 80)
    v = voice(f0, amp, tract([(0, "mm")], n, 0.78), breath=0.12, oq=0.55, jitter=0.01, shimmer=0.06)
    chest = reson(v, 130, 60)
    lk = cascade(bp(noise(d), 300, 4000) * leak, tract([(0, "eh")], n, 0.8))
    x = lp(u(v) + u(chest) * 0.3 + u(lk) * 0.25, 1400)
    for ti, ln in ((0.76, 0.1), (1.84, 0.09)):
        sn = N(ln + 0.06)
        st = np.arange(sn) / SR
        fg = (0.5 + 0.5 * np.cos(2 * np.pi * 34 * st)) ** 4
        win = np.sin(np.pi * np.clip(st / ln, 0, 1))
        it = cascade(bp(noise(sn / SR, "pink"), 150, 4000) * (0.3 + fg) * win, tract([(0, "mm")], sn, 0.75))
        place(x, endfade(u(it)) * 0.4, ti)
    sd = 0.46
    se = smooth_env(curve(N(sd), [(0, 0), (0.05, 1), (0.4, 0), (sd, 0)]), 20)
    place(x, u(cascade(bp(noise(sd, "pink"), 150, 5000) * se, tract([(0, "mm")], N(sd), 0.75))) * 0.25, 2.42)
    return cave(pan2(x, 0.1), rt=1.8, wet=0.2)


def anger_throat_clear():
    """Anger catches his smirk and clears his throat: a rough constricted 'hhrr' (0-0.3 s, peak ~0.12) and,
    after a glottal stop, a firm low 'HM' (0.36-0.78 s, f0 112 -> 82 Hz); a little breath out after."""
    d = 1.1
    n = N(d)
    f0 = curve(n, [(0, 72), (0.3, 68), (0.34, 112), (0.45, 104), (0.7, 88), (0.78, 82), (d, 80)])
    amp = curve(n, [(0, 0), (0.015, 0.7), (0.12, 1.0), (0.26, 0.8), (0.3, 0), (0.36, 0), (0.37, 0.8), (0.42, 1.0),
                    (0.6, 0.75), (0.78, 0), (d, 0)])
    amp = smooth_env(amp, 60)
    breath = curve(n, [(0, 0.5), (0.3, 0.5), (0.34, 0.1), (d, 0.15)])
    jit = curve(n, [(0, 0.12), (0.3, 0.12), (0.34, 0.012), (d, 0.012)])
    shim = curve(n, [(0, 0.3), (0.3, 0.3), (0.34, 0.05), (d, 0.05)])
    dip = curve(n, [(0, 0.45), (0.3, 0.45), (0.34, 0.0), (d, 0.0)])
    oq = curve(n, [(0, 0.4), (0.3, 0.4), (0.34, 0.6), (d, 0.6)])
    tr = tract([(0, "kh"), (0.12, "uh"), (0.3, "uh"), (0.35, "mm"), (d, "mm")], n, 0.92)
    v = voice(f0, amp, tr, breath=breath, oq=oq, jitter=jit, shimmer=shim, diplo=dip, drift=0.01)
    rasp_env = amp * (np.arange(n) < N(0.31))
    rn = bp(noise(d), 800, 4500) * rasp_env * rough(n, 40, 0.8, 2)
    rasp = u(rbp(rn, 1900, 4) + rbp(rn, 2900, 4) * 0.7)
    be = smooth_env(curve(n, [(0, 0), (0.78, 0), (0.83, 1), (1.0, 0), (d, 0)]), 30)
    nose = cascade(bp(noise(d, "pink"), 200, 4000) * be, tract([(0, "mm")], n, 0.92))
    x = lp(u(v) + rasp * 0.35 + u(nose) * 0.12, 6500)
    return cave(pan2(x, -0.1), rt=1.6, wet=0.15)


# ============================================================================ motion-locked (scenes place these)

def _armor_step(run=False):
    """Heavy plate-armored footfall on stone, heel strike at +0.00: boot thud + sole + grit scuff, then
    the armor's jingle (plate ticks 0.01-0.12 s, a greave clank, a mail shimmer)."""
    d = 0.55 if run else 0.75
    buf = np.zeros((N(d), 2))
    td = 0.4
    tt = t_axis(td)
    thud = thump(td, 125 if run else 105, 55, tau=0.035 if run else 0.05, ptau=0.015)
    sole = u(lp(noise(td, "pink"), 600)) * decay(td, 0.018, 0.001) * 0.5
    grit = u(crackle(td, 3000 * np.exp(-tt / 0.03), 800, 6000, grain=0.0007)) * (0.35 if run else 0.25)
    scuff = u(bp(noise(td), 1200, 5000)) * curve(N(td), [(0, 0), (0.02, 1), (0.1, 0), (td, 0)]) * 0.2
    p = RNG.uniform(-0.12, 0.12)
    place(buf, thud + sole + grit + scuff, 0.0, pan=p)
    span = 0.08 if run else 0.11
    for _ in range(RNG.integers(4, 7)):
        place(buf, metal_hit(RNG.uniform(900, 2600), 0.25, tau=RNG.uniform(0.03, 0.08), hard=0.8) * RNG.uniform(0.2, 0.45)
              * (1.3 if run else 1.0), RNG.uniform(0.01, span), pan=p + RNG.uniform(-0.2, 0.2))
    place(buf, metal_hit(RNG.uniform(380, 620), 0.4, tau=0.07, hard=0.6) * 0.3, RNG.uniform(0.008, 0.03), pan=p)
    md = 0.15
    place(buf, u(crackle(md, 2500 * np.exp(-t_axis(md) / 0.04), 4000, 11000, grain=0.0002)) * 0.2, 0.015, pan=p)
    return cave(buf, rt=1.5, wet=0.15)


def armor_shift():
    """Armor plates shifting with a body movement: leather strap creak (0.05-0.35), a plate sliding over
    plate (0.1-0.45), clinks at ~0.12, 0.36, 0.5 s, a little mail shimmer and cloth."""
    d = 0.9
    n = N(d)
    buf = np.zeros((n, 2))
    place(buf, creak(0.3, 50, 75) * curve(N(0.3), [(0, 0), (0.05, 1), (0.3, 0)]) * 0.35, 0.05, pan=-0.1)
    se = curve(n, [(0, 0), (0.1, 0), (0.15, 1), (0.4, 0.6), (0.45, 0), (d, 0)])
    sc = lp(bp(noise(d), 1000, 6000) * rough(n, 80, 0.8, 2), 5000)
    met = rbp(sc, 1700, 30) + rbp(sc, 2600, 35) * 0.7 + rbp(sc, 3900, 40) * 0.5
    place(buf, (u(met) * 0.4 + u(sc) * 0.08) * se, 0.0)
    for tt in (0.12, 0.36, 0.5):
        place(buf, metal_hit(RNG.uniform(800, 2200), 0.3, tau=0.06, hard=0.7) * RNG.uniform(0.25, 0.4), tt + RNG.uniform(-0.01, 0.01),
              pan=RNG.uniform(-0.2, 0.2))
    place(buf, u(crackle(0.4, 600, 4000, 11000, grain=0.0002)) * curve(N(0.4), [(0, 0), (0.1, 1), (0.4, 0)]) * 0.12, 0.1)
    for ch in range(2):
        buf[:, ch] += u(bp(noise(d), 400, 3000) * rough(n, 20, 0.8, 2)) * curve(n, [(0, 0), (0.1, 0.5), (0.6, 0), (d, 0)]) * 0.08
    return cave(buf, rt=1.5, wet=0.15)


# ============================================================================ registry

EFFECTS = {f.__name__: f for f in [
    cave_air_loop, torch_loop, deep_air_loop, snore_loop,
    sword_chop, vines_fall, web_tear, door_locked, door_explode, debris_rain,
    scurry, stone_shift, torch_whoosh, torch_splash, drip,
    rock_crack, floor_collapse, armor_clank, dust_slip, sword_stab, sword_scrape, heavy_impact, armor_clatter,
    anger_groan, pebbles_shift, monster_growl, monster_hiss, drool_drip, rock_whoosh, rock_bonk, body_thud,
    tail_grab, drag, crunching,
    armor_scrape,
    saliva_drip, startle_sting, creature_huff, stomp, foot_tap_heavy, creature_snort, creature_giggle,
    anger_throat_clear,
    armor_shift]}
# motion-locked footfalls; the extra variants are optional alternates scenes may cycle through
EFFECTS.update({
    "armor_step": lambda: _armor_step(False),
    "armor_step_2": lambda: _armor_step(False),
    "armor_step_3": lambda: _armor_step(False),
    "armor_step_run": lambda: _armor_step(True),
    "armor_step_run_2": lambda: _armor_step(True),
})


def render(name):
    """Synthesize one effect -> normalized stereo float array (the exact file contents)."""
    reseed(name)
    x = EFFECTS[name]()
    if x.ndim == 1:
        x = pan2(x, 0.0)
    if name.endswith("_loop"):
        x = circ_hp(x, 20.0)
    else:
        x = trim_tail(fade(hp(x, 20.0), 0.0003, 0.01))
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{name}: non-finite samples")
    return norm(x, -3.0)


def main(only=None):
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    if only:
        bad = sorted(set(only) - set(EFFECTS))
        if bad:
            raise SystemExit(f"unknown effect(s): {', '.join(bad)}")
    for name in EFFECTS:
        if only and name not in only:
            continue
        x = render(name)
        sf.write(SFX_DIR / f"{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")
        print(f"{name:20s} {len(x) / SR:6.2f}s")


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
