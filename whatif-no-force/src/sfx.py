"""Procedural sound effects and the rainy-diner ambience for video 2.

render_sfx(tl) -> (sfx_dry, sfx_hall_send, ambience, log, gate) as stereo arrays
(gate: the control-rate rain / room-tone scene gates).
Every effect is synthesized from oscillators and filtered noise; each kind has
a level, a hall-reverb send, a diner-room send and a pre-roll (how far before
its cue it starts, so e.g. a page swish peaks on the cut).

The ambience is one continuous bed: rain on the window (steady, heavier from
"rain_heavy", easing to gutter drips from "rain_ease") with distant wet
traffic, plus diner room tone (fridge hum, neon buzz, the far kitchen). It
follows the shots: full in the diner, rain only and softer in the sketchbook.
"""
import math

import numpy as np
from scipy import signal

from audio_dsp import (SR, biquad, bp, convolve, env_points, fade_edges, hp, lp, make_ir, midi_hz, ns, pan, saw,
                       smooth_curve, sweep, tarr)
import anchors
import direction

# ----------------------------------------------------------------------------
# building blocks
# ----------------------------------------------------------------------------


def noise(rng, n):
    return rng.standard_normal(n)


def glide(f0, f1, n, curve="exp"):
    x = np.linspace(0, 1, n)
    if curve == "exp":
        return f0 * (f1 / f0) ** x
    return f0 + (f1 - f0) * x


def osc_phase(f):
    return 2 * np.pi * np.cumsum(f) / SR


def decay(n, tau, attack=0.002):
    t = tarr(n)
    return (1 - np.exp(-t / max(1e-4, attack))) * np.exp(-t / tau)


def bell_partials(f0, n, parts):
    t = tarr(n)
    y = np.zeros(n)
    for r, a, d in parts:
        if f0 * r < 18000:
            y += a * np.exp(-t / d) * np.sin(2 * np.pi * f0 * r * t + r)
    return y


def stereo_sweep(x, p0, p1):
    n = len(x)
    p = np.linspace(p0, p1, n)
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(th), x * np.sin(th)])


def norm(x, peak=0.5):
    m = np.max(np.abs(x)) + 1e-12
    return x / m * peak


def wobble(rng, n, fc, sr=SR):
    """Smooth random curve with unit standard deviation."""
    pre = int(sr / fc)
    x = signal.sosfilt(signal.butter(2, fc, fs=sr, output="sos"), rng.standard_normal(n + pre))[pre:]
    return x / (np.std(x) + 1e-12)


def reson(x, f0, q):
    """Resonant band-pass (0 dB at f0)."""
    return signal.sosfilt(biquad("bandpass", f0, q), x)


def crackle(rng, n, rate, lo=1500, hi=9000, width=0.0015):
    """Sparse tiny noise bursts: paper crinkle, grit."""
    k = rng.poisson(rate * n / SR)
    imp = np.zeros(n)
    imp[rng.integers(0, n, k)] = rng.uniform(0.2, 1.0, k)
    env = signal.oaconvolve(imp, np.hanning(max(3, ns(width))))[:n]
    return bp(noise(rng, n), lo, hi, 2) * env


def add_at(y, sig, t, p=0.0, g=1.0):
    """Mix sig (mono or stereo) into y (mono or stereo) starting at t seconds."""
    if y.ndim == 2 and sig.ndim == 1:
        sig = pan(sig, p)
    i = ns(t)
    k0 = 0
    if i < 0:
        k0, i = -i, 0
    j = min(y.shape[-1], i + sig.shape[-1] - k0)
    if j > i:
        y[..., i:j] += g * sig[..., k0:k0 + (j - i)]


# ----------------------------------------------------------------------------
# effects: each returns (signal mono or stereo, preroll_seconds)
# ----------------------------------------------------------------------------


def _step(rng, vel=1.0, squeak=False):
    m = ns(0.3)
    heel = lp(noise(rng, m), 320, 2) * decay(m, 0.022, 0.0015)
    body = np.sin(osc_phase(glide(105, 58, m))) * decay(m, 0.03, 0.002)
    tick = bp(noise(rng, m), 1800, 5200, 2) * decay(m, 0.003, 0.0004)
    y = norm(heel) + 0.55 * norm(body) + 0.12 * norm(tick)
    toe = bp(noise(rng, m), 600, 2600, 2) * decay(m, 0.012, 0.002)  # the sole rolls onto the toe
    add_at(y, 0.4 * norm(toe), rng.uniform(0.05, 0.08))
    if squeak:
        q = ns(0.06)
        f = glide(rng.uniform(1700, 2000), rng.uniform(2300, 2700), q) * (1 + 0.02 * np.sin(2 * np.pi * 60 * tarr(q)))
        add_at(y, 0.1 * np.sin(osc_phase(f)) * env_points(q, [(0, 0), (0.01, 1), (0.04, 0.5), (0.06, 0)]), 0.07)
    return y * vel


def fx_footsteps(rng, ctx):
    # Kai crossing the tiled floor with the coffee pot: sneakers, approaching, settling
    n = ns(2.4)
    y = np.zeros((2, n))
    times = [0.0, 0.46, 0.93, 1.37, 1.78]
    for i, s in enumerate(times):
        x = i / (len(times) - 1)
        vel = (0.55 + 0.45 * x) * (0.6 if i == len(times) - 1 else 1.0) * rng.uniform(0.9, 1.05)
        add_at(y, _step(rng, vel, squeak=i in (1, 3)), s + rng.uniform(-0.015, 0.015), 0.7 - 0.5 * x)
    return norm(y, 0.4), 0.0


def fx_coffee_pour(rng, ctx):
    # coffee into Hale's mug: the cavity note rises as it fills, two last drips
    dur = 1.0
    m = ns(dur)
    out = np.zeros(ns(dur + 0.35))
    gurgle = np.clip(0.65 + 0.3 * wobble(rng, m, 25), 0.15, 1.2)
    src = noise(rng, m) * gurgle
    fc = glide(480, 1150, m)
    stream = sweep(src, fc, "band", 2.5, 256) + 0.5 * sweep(src, fc * 2.3, "band", 3.5, 256)
    fizz = hp(noise(rng, m), 3800, 2) * (0.5 + 0.5 * gurgle)
    body = lp(noise(rng, m), 300, 2)
    y = norm(stream) + 0.12 * norm(fizz) + 0.15 * norm(body)
    out[:m] = y * env_points(m, [(0, 0), (0.04, 1), (dur - 0.18, 0.9), (dur - 0.05, 0.25), (dur, 0)])
    for k in range(2):
        q = ns(0.05)
        d = np.sin(osc_phase(glide(900, 1700, q))) * decay(q, 0.012, 0.0008)
        add_at(out, 0.35 * d, dur + 0.06 + 0.13 * k + rng.uniform(0, 0.03))
    return pan(norm(out, 0.32), -0.2), 0.0


def fx_cup_set(rng, ctx):
    # the pot set down on the formica: a short ceramic-and-glass tock
    n = ns(0.5)
    knock = lp(noise(rng, n), 700, 2) * decay(n, 0.01, 0.0005)
    body = np.sin(2 * np.pi * 230 * tarr(n)) * decay(n, 0.018, 0.001)
    ring = bell_partials(1860, n, ((1, 1.0, 0.06), (1.63, 0.55, 0.045), (2.71, 0.3, 0.03), (3.9, 0.15, 0.02)))
    y = norm(knock) + 0.45 * norm(body) + 0.16 * norm(ring)
    k = ns(0.016)
    y2 = np.zeros(n)
    y2[k:] = 0.3 * y[:n - k]
    return pan(norm(y + y2, 0.4), -0.1), 0.0


def fx_car_door_slam(rng, ctx):
    # out on the wet street, through the glass: thump, latch, panel ring, slap off the far wall
    n = ns(2.4)
    thump = np.tanh(2.0 * np.sin(osc_phase(glide(115, 52, n)))) * decay(n, 0.085, 0.0015)
    slab = lp(noise(rng, n), 450, 2) * decay(n, 0.045, 0.0008)
    latch = bp(noise(rng, n), 1100, 3800, 2) * decay(n, 0.007, 0.0004)
    panel = bell_partials(305, n, ((1, 1, 0.11), (1.47, 0.6, 0.08), (2.13, 0.4, 0.06), (3.3, 0.2, 0.035)))
    y = norm(thump) + 0.7 * norm(slab) + 0.4 * norm(latch) + 0.22 * norm(panel)
    add_at(y, 0.25 * norm(latch[:ns(0.1)]), 0.035)
    y = lp(y, 1500, 2)
    echo = np.zeros(n)
    for d, a, f in ((0.19, 0.22, 900), (0.43, 0.08, 600)):
        k = ns(d)
        echo[k:] += a * lp(y, f, 2)[:n - k]
    return pan(norm(y + echo, 0.5), -0.4), 0.0


def fx_booth_squeak(rng, ctx):
    # Kai slides into the vinyl booth: rubbery stick-slip and the cushion sighing
    n = ns(0.8)
    t = tarr(n)
    f = np.clip(330 + 150 * np.sin(2 * np.pi * 1.9 * t + 0.5) + 60 * wobble(rng, n, 8), 160, 900)
    rough = np.clip(0.55 + 0.45 * wobble(rng, n, 45), 0.1, 1.0)
    sq = bp(saw(f, n) * rough, 450, 2800, 2) * env_points(n, [(0, 0), (0.05, 0.6), (0.22, 1), (0.45, 0.35),
                                                              (0.62, 0)])
    puff = lp(noise(rng, n), 380, 2) * env_points(n, [(0, 0), (0.07, 1), (0.3, 0.35), (0.7, 0)])
    return pan(norm(0.5 * norm(sq) + 0.65 * norm(puff), 0.3), 0.35), 0.0


def fx_sketchbook_open(rng, ctx):
    n = ns(0.75)
    flap = lp(noise(rng, n), 500, 2) * env_points(n, [(0, 0), (0.06, 1), (0.2, 0.3), (0.32, 0)])
    rust = crackle(rng, n, 260, 1500, 7000) * env_points(n, [(0, 0), (0.03, 1), (0.25, 0.6), (0.4, 0)])
    air = bp(noise(rng, n), 700, 3500, 2) * env_points(n, [(0, 0), (0.1, 0.3), (0.3, 1), (0.38, 0)])
    y = 0.6 * norm(flap) + 0.45 * norm(rust) + 0.4 * norm(air)
    m = ns(0.06)
    add_at(y, 0.8 * norm(lp(noise(rng, m), 900, 2) * decay(m, 0.008, 0.0005)), 0.37)  # the cover lands
    return pan(norm(y, 0.3), 0.25), 0.0


def fx_pencil_sketch(rng, ctx):
    # graphite on paper: long lines, quick hatching, pauses; length from params["dur"]
    dur = float(ctx["params"].get("dur", 4.0))
    n = ns(dur)
    y = np.zeros(n)
    t = rng.uniform(0.05, 0.25)
    while t < dur - 0.25:
        if rng.random() < 0.4:
            L = rng.uniform(0.45, 1.1)
            m = ns(L)
            am = np.abs(np.sin(np.pi * rng.uniform(5.5, 8.5) * tarr(m))) ** 0.8
        else:
            L = rng.uniform(0.25, 0.8)
            m = ns(L)
            am = env_points(m, [(0, 0), (0.03, 1), (L - 0.07, 0.8), (L, 0)])
        tooth = np.clip(0.55 + 0.45 * wobble(rng, m, 260), 0.05, 1.3)
        s = bp(noise(rng, m), rng.uniform(1600, 2600), rng.uniform(6500, 9500), 2) * am * tooth
        s += 0.15 * bp(noise(rng, m), 500, 1400, 2) * am
        add_at(y, s * rng.uniform(0.55, 1.0), t)
        t += L + rng.uniform(0.07, 0.5)
    y = fade_edges(y, 0.05, 0.2)
    return pan(norm(y, 0.25), 0.3 if ctx["scene"] == "diner" else 0.05), 0.0


def fx_page_turn(rng, ctx):
    # a sketchbook page lifts, swishes over (peaking on the cut) and flops down
    n = ns(0.8)
    s = rng.uniform(0.9, 1.1)
    lift = bp(noise(rng, n), 500, 2600, 2) * env_points(n, [(0, 0), (0.05 * s, 0.6), (0.12 * s, 0.25),
                                                            (0.5 * s, 0)])
    swish = sweep(noise(rng, n), glide(900, 4200, n), "band", 0.7, 256) \
        * env_points(n, [(0, 0), (0.1 * s, 0.25), (0.27 * s, 1), (0.42 * s, 0.35), (0.6 * s, 0)])
    flop = lp(noise(rng, n), 650, 2) * env_points(n, [(0, 0), (0.38 * s, 0), (0.41 * s, 1), (0.52 * s, 0.15),
                                                      (0.62 * s, 0)])
    crk = crackle(rng, n, 180, 1800, 8000) * env_points(n, [(0, 0), (0.04 * s, 1), (0.45 * s, 0.5), (0.6 * s, 0)])
    y = 0.45 * norm(lift) + norm(swish) + 0.5 * norm(flop) + 0.35 * norm(crk)
    return stereo_sweep(norm(y, 0.32), 0.35, -0.35), 0.22 * s


def _babble(rng, dur, voices=12, sr=16000):
    """A murmuring crowd: glottal buzz through vowel formants, syllables, phrases, pauses."""
    n = int(dur * sr)
    t = np.arange(n) / sr
    vowels = ((730, 1090), (530, 1840), (300, 2250), (570, 870), (330, 900), (660, 1700))
    sos = [(signal.butter(2, [f1 * 0.8, f1 * 1.25], "band", fs=sr, output="sos"),
            signal.butter(2, [f2 * 0.85, f2 * 1.18], "band", fs=sr, output="sos")) for f1, f2 in vowels]
    out = np.zeros((2, n))
    for v in range(voices):
        f = rng.uniform(95, 230) * (1 + 0.07 * np.sin(2 * np.pi * rng.uniform(0.25, 0.8) * t + rng.uniform(0, 6))
                                    + 0.025 * wobble(rng, n, 6, sr))
        src = 2 * ((np.cumsum(f) / sr) % 1.0) - 1.0
        ph = t * rng.uniform(3.2, 5.0) + rng.uniform(0, 1)
        seq = rng.integers(0, len(vowels), int(ph[-1]) + 2)[ph.astype(int)]
        syl = 0.5 - 0.5 * np.cos(2 * np.pi * (ph % 1.0))  # zero where the vowel changes
        talk = np.clip(wobble(rng, n, 0.8, sr) + 0.6, 0, 1)
        y = np.zeros(n)
        for j, (s1, s2) in enumerate(sos):
            w = seq == j
            if w.any():
                y += w * (signal.sosfilt(s1, src) + 0.6 * signal.sosfilt(s2, src))
        y *= syl * talk * rng.uniform(0.35, 1.0)
        th = (rng.uniform(-0.8, 0.8) + 1) * np.pi / 4
        out[0] += y * math.cos(th)
        out[1] += y * math.sin(th)
    return signal.resample_poly(out, SR // sr, 1, axis=1)


def fx_crowd_murmur(rng, ctx):
    # witnesses: a room full of people murmuring, swelling into "seen"
    y = lp(_babble(rng, 2.9, 12), 3200, 2)
    y *= env_points(y.shape[1], [(0, 0), (0.6, 1), (1.6, 0.9), (2.9, 0)])[None, :]
    return norm(y, 0.35), 0.35


def _clank(rng, f0, n, ring=1.0):
    """Heavy steel: a bolt clack plus inharmonic plate partials."""
    hit = hp(noise(rng, n), 1500, 2) * decay(n, 0.004, 0.0003)
    thud = lp(noise(rng, n), 300, 2) * decay(n, 0.03, 0.001)
    plate = bell_partials(f0, n, ((1, 1, 0.5 * ring), (2.0, 0.5, 0.35 * ring), (2.76, 0.45, 0.25 * ring),
                                  (3.0, 0.3, 0.3 * ring), (4.07, 0.25, 0.15 * ring), (5.4, 0.15, 0.1 * ring)))
    return 0.5 * norm(hit) + 0.7 * norm(thud) + 0.5 * norm(plate)


def _slide(rng, dur):
    """A barred door rolling open on its track and hitting the stop."""
    m = ns(dur)
    y = np.zeros(ns(dur + 0.8))
    rattle = 0.6 + 0.4 * np.sin(2 * np.pi * rng.uniform(14, 22) * tarr(m)) ** 2
    roll = lp(noise(rng, m), 380, 2) * rattle * env_points(m, [(0, 0), (0.15, 1), (dur - 0.2, 0.8), (dur, 0.4)])
    grit = crackle(rng, m, 90, 600, 3000) * env_points(m, [(0, 0), (0.1, 1), (dur, 0.5)])
    y[:m] = norm(roll) + 0.35 * norm(grit)
    add_at(y, 0.9 * _clank(rng, rng.uniform(160, 190), ns(0.8), 0.7), dur - 0.02)
    return y


def fx_cell_doors(rng, ctx):
    # every cell door opens: one heavy bolt here, then the whole block down the corridor
    n = ns(4.8)
    y = np.zeros((2, n))
    f0 = midi_hz(53)  # F3: leans on the F-major bloom at "opens"
    add_at(y, _clank(rng, f0, ns(2.0), 1.0), 0.0, -0.2)
    times = 0.12 + np.cumsum(rng.uniform(0.07, 0.2, 13))
    for k, tk in enumerate(times):
        far = (k + 1) / len(times)
        c = _clank(rng, f0 * rng.choice([1.0, 1.5, 2.0]) * rng.uniform(0.98, 1.02), ns(1.2), 0.6)
        add_at(y, lp(c, 2600 - 1700 * far, 2) * 0.55 * (1 - 0.8 * far), tk, rng.uniform(-0.9, 0.9))
    add_at(y, 0.5 * _slide(rng, 1.1), 0.25, -0.35)
    add_at(y, lp(0.32 * _slide(rng, 1.3), 1200, 2), 0.7, 0.55)
    add_at(y, lp(0.2 * _slide(rng, 1.2), 800, 2), 1.3, -0.75)
    return norm(y, 0.5), 0.0


def fx_door_creak(rng, ctx):
    # a door eased open after a soft latch click: warm and slow, not spooky
    m = ns(1.45)
    y = np.zeros(ns(1.8))
    rate = 28 + 60 * env_points(m, [(0, 0.15), (0.35, 0.9), (0.8, 1.0), (1.2, 0.55), (1.45, 0.3)]) \
        * (1 + 0.12 * wobble(rng, m, 6))
    imp = np.diff(np.floor(np.cumsum(rate / SR)), prepend=0.0) * rng.uniform(0.5, 1.0, m)
    src = imp + 0.04 * noise(rng, m) * (rate / 90)
    body = reson(src, 310, 6) + 0.6 * reson(src, 720, 7) + 0.3 * reson(src, 1550, 8)
    y[ns(0.12):ns(0.12) + m] = norm(body * env_points(m, [(0, 0), (0.08, 1), (1.2, 0.7), (1.45, 0)]))
    q = ns(0.03)
    add_at(y, 0.5 * norm(bp(noise(rng, q), 1500, 6000, 2) * decay(q, 0.004, 0.0003)), 0.0)
    return pan(norm(y, 0.3), -0.25), 0.1


def fx_coins(rng, ctx):
    # a handful of coins into a jar; one wobbles to rest
    n = ns(1.3)
    y = np.zeros((2, n))
    for tk in np.sort(np.concatenate([rng.uniform(0, 0.25, 6), rng.uniform(0.2, 0.6, 5)])):
        m = ns(0.4)
        b = bell_partials(rng.uniform(2600, 4600), m, ((1, 1, rng.uniform(0.04, 0.1)), (1.52, 0.6, 0.05),
                                                       (2.41, 0.4, 0.035), (3.3, 0.2, 0.02)))
        b[:ns(0.0008)] *= np.linspace(0, 1, ns(0.0008))
        add_at(y, b * rng.uniform(0.3, 1.0), tk, rng.uniform(-0.35, 0.45))
    tk, gap = 0.65, 0.08
    for k in range(9):
        m = ns(0.06)
        add_at(y, bell_partials(3300, m, ((1, 1, 0.012), (2.41, 0.4, 0.008))) * 0.35 * 0.85 ** k, tk, 0.3)
        tk += gap
        gap *= 0.78
    return norm(y, 0.3), 0.0


def fx_tank_rumble(rng, ctx):
    # tanks out of sight: diesel growl and track clatter roll up, then stop
    dur = 4.6
    n = ns(dur)
    speed = env_points(n, [(0, 0.85), (2.2, 1.05), (3.0, 0.7), (4.6, 0.45)])
    ph = osc_phase(31 * speed)
    eng = sum((1.0 / h) * np.sin(h * ph + h) for h in range(1, 8)) * (1 + 0.35 * np.sin(0.5 * ph))
    eng = np.tanh(1.5 * eng)
    rumble = lp(noise(rng, n), 110, 2)
    clat = np.zeros(n)
    tk = 0.0
    while tk < 3.1:
        m = ns(0.05)
        add_at(clat, lp(hp(noise(rng, m), 300, 2), 1600, 2) * decay(m, 0.012, 0.0006) * rng.uniform(0.5, 1.0), tk)
        tk += 1.0 / (8.0 * float(speed[min(n - 1, ns(tk))]))
    y = norm(eng) + 0.8 * norm(rumble) + 0.3 * norm(clat)
    y = lp(y * env_points(n, [(0, 0), (1.2, 1), (2.3, 1), (3.1, 0.55), (4.6, 0)]), 900, 2)
    return stereo_sweep(norm(y, 0.5), -0.35, 0.15), 0.4


def fx_rain_heavy(rng, ctx):
    # the storm leans in: far thunder rolls and a gust throws rain at the glass
    # (the bed itself gets heavier from here: see rain_intensity)
    dur = 6.5
    n = ns(dur)
    t = tarr(n)
    roll = np.zeros((2, n))
    for c, w, a in ((0.35, 0.18, 0.6), (0.9, 0.35, 1.0), (1.7, 0.5, 0.8), (2.8, 0.7, 0.55), (4.0, 0.9, 0.3)):
        bump = a * np.exp(-0.5 * ((t - c) / w) ** 2)
        roll += np.stack([lp(noise(rng, n), 140, 2), lp(noise(rng, n), 140, 2)]) * bump[None, :]
    body = lp(noise(rng, n), 55, 2) * env_points(n, [(0, 0), (0.6, 1), (3.0, 0.6), (6.0, 0)])
    crack = bp(noise(rng, n), 250, 1100, 2) * env_points(n, [(0, 0), (0.25, 1), (0.6, 0.25), (1.2, 0)])
    gust = lp(np.stack([hp(noise(rng, n), 900, 2), hp(noise(rng, n), 900, 2)]), 7000, 2) \
        * env_points(n, [(0, 0), (0.7, 1), (2.5, 0.45), (5.5, 0)])[None, :]
    y = norm(roll) + 0.5 * norm(body)[None, :] + 0.12 * norm(crack)[None, :] + 0.16 * norm(gust)
    return norm(y, 0.5), 0.0


def _lubdub(rng, vel):
    m = ns(0.55)
    lub = np.tanh(2.2 * np.sin(osc_phase(glide(64, 40, m)))) * decay(m, 0.075, 0.006)
    dub = np.tanh(2.0 * np.sin(osc_phase(glide(74, 46, m)))) * decay(m, 0.055, 0.005)
    thump = lp(noise(rng, m), 160, 2) * decay(m, 0.03, 0.004)
    y = norm(lub) + 0.25 * norm(thump)
    add_at(y, 0.7 * norm(dub) + 0.18 * norm(thump), 0.29)
    return y * vel


def fx_heartbeat(rng, ctx):
    # Kai's pulse under the turn: slow, a little faster as the memory surfaces
    dur = float(ctx["params"].get("dur", 8.0))
    y = np.zeros(ns(dur + 0.8))
    t = 0.1
    while t < dur - 0.2:
        vel = min(1.0, (t + 0.4) / 2.2) * min(1.0, (dur - t) / 2.6)
        add_at(y, _lubdub(rng, vel * rng.uniform(0.93, 1.0)), t)
        t += 60.0 / (60 + 8 * t / dur)
    return pan(norm(y, 0.55), 0.0), 0.0


def fx_metal_thud(rng, ctx):
    # his face against the hood: a dull, body-damped sheet-metal thud, heard as memory
    n = ns(2.4)
    thump = np.tanh(2.5 * np.sin(osc_phase(glide(100, 48, n)))) * decay(n, 0.11, 0.0015)
    body = lp(noise(rng, n), 320, 2) * decay(n, 0.035, 0.0008)
    sheet = bell_partials(118, n, ((1, 1, 0.32), (1.62, 0.7, 0.24), (2.31, 0.5, 0.18), (3.12, 0.3, 0.12),
                                   (4.2, 0.2, 0.08), (5.6, 0.12, 0.05)))
    y = lp(norm(thump) + 0.5 * norm(body) + 0.35 * norm(sheet), 2400, 2)
    return pan(norm(y, 0.55), 0.0), 0.0


def fx_car_drive_away(rng, ctx):
    # "She drives home": the engine pulls away on the wet road, tires hissing, gone
    dur = 5.5
    n = ns(dur)
    away = smooth_curve(n, 0, n)
    rpm = env_points(n, [(0, 0.8), (0.6, 1.25), (1.8, 1.05), (2.2, 1.3), (5.5, 1.15)])
    ph = osc_phase(36 * rpm * (1 - 0.05 * away))  # a touch of doppler as it recedes
    eng = np.tanh(1.3 * sum((1.0 / h) * np.sin(h * ph + 0.7 * h) for h in range(1, 7)))
    tires = bp(noise(rng, n), 450, 3800, 2) * (0.75 + 0.25 * wobble(rng, n, 9))
    y = sweep(0.8 * norm(eng) + norm(tires), 3200 * (1 - 0.82 * away) + 300, "low", 0.7, 512)
    y *= env_points(n, [(0, 0), (0.25, 0.8), (0.8, 1), (dur, 0)]) * (1 - 0.85 * away) ** 1.3
    return stereo_sweep(norm(y, 0.45), 0.05, 0.75), 0.15


def fx_page_flip_many(rng, ctx):
    # a hundred drawings of the same night riffled past in one breath
    dur = 1.7
    n = ns(dur + 0.3)
    y = np.zeros(n)
    t = 0.0
    while t < dur:
        x = t / dur
        m = ns(0.05)
        f = bp(noise(rng, m), rng.uniform(900, 1600), rng.uniform(5000, 8000), 2) * decay(m, 0.01, 0.0008)
        th = lp(noise(rng, m), 500, 2) * decay(m, 0.006, 0.0005)
        add_at(y, (norm(f) + 0.35 * norm(th)) * rng.uniform(0.5, 1.0) * (0.6 + 0.4 * math.sin(math.pi * x)), t)
        t += 0.095 - 0.06 * math.sin(math.pi * x) + rng.uniform(-0.008, 0.008)
    air = bp(noise(rng, n), 400, 2400, 2) * env_points(n, [(0, 0), (0.25, 1), (dur - 0.3, 0.8), (dur + 0.2, 0)])
    y = y + 0.3 * norm(air) * np.max(np.abs(y))
    return stereo_sweep(norm(y, 0.3), 0.3, -0.2), 0.05


def _call_warble(rng):
    out = []
    for k in range(rng.integers(3, 7)):
        m = ns(rng.uniform(0.06, 0.13))
        f = glide(rng.uniform(1900, 3600), rng.uniform(1900, 3600), m) \
            * (1 + 0.04 * np.sin(2 * np.pi * rng.uniform(30, 60) * tarr(m)))
        out += [(np.sin(osc_phase(f)) + 0.15 * np.sin(2 * osc_phase(f))) * np.hanning(m),
                np.zeros(ns(rng.uniform(0.03, 0.08)))]
    return np.concatenate(out)


def _call_chip(rng):
    out = []
    for k in range(rng.integers(2, 5)):
        m = ns(rng.uniform(0.035, 0.05))
        out += [np.sin(osc_phase(glide(rng.uniform(5200, 6200), rng.uniform(3300, 3900), m))) * np.hanning(m),
                np.zeros(ns(rng.uniform(0.05, 0.09)))]
    return np.concatenate(out)


def _call_feebee(rng):
    f0 = rng.uniform(3500, 4000)
    out = []
    for r, L in ((1.0, 0.24), (0.89, 0.3)):  # two whistled notes, the second a step lower
        m = ns(L)
        out += [np.sin(osc_phase(f0 * r * glide(1.0, 0.985, m))) * np.hanning(m) ** 0.7, np.zeros(ns(0.05))]
    return np.concatenate(out)


def fx_birds_dawn(rng, ctx):
    # first birds after the rain: sparse calls through the glass, mostly in the dialogue gaps
    t0 = ctx["t"]
    dur = 26.0
    y = np.zeros((2, ns(dur)))
    speech = [(ln["start"] - t0, ln["end"] - t0) for ln in ctx["tl"]["lines"]]
    birds = ((_call_warble, -0.65, 1.0), (_call_chip, 0.55, 0.6), (_call_feebee, 0.85, 0.7), (_call_warble, -0.15, 0.5))
    t = 0.6
    while t < dur - 1.5:
        fn, p, a = birds[rng.integers(0, len(birds))]
        s = fn(rng)
        L = len(s) / SR
        talking = any(a0 - 0.1 < t + L and t < a1 + 0.1 for a0, a1 in speech)
        if talking and rng.random() < 0.55:
            t += rng.uniform(0.4, 1.2)
            continue
        fade = min(1.0, (t + 0.5) / 5.0) * min(1.0, (dur - t) / 6.0)
        add_at(y, s * a * fade * (0.4 if talking else 1.0) * rng.uniform(0.6, 1.0), t, p + rng.uniform(-0.1, 0.1))
        t += L + rng.uniform(0.8, 2.6)
    return norm(lp(y, 6500, 2), 0.3), 0.0


def fx_fist_bump(rng, ctx):
    # knuckles meeting, gently
    n = ns(0.4)
    knock = lp(noise(rng, n), 850, 2) * decay(n, 0.009, 0.0007)
    body = np.sin(osc_phase(glide(150, 95, n))) * decay(n, 0.02, 0.0015)
    skin = bp(noise(rng, n), 1400, 4200, 2) * decay(n, 0.004, 0.0004)
    return pan(norm(norm(knock) + 0.6 * norm(body) + 0.18 * norm(skin), 0.45), 0.0), 0.0


def _bell(rng, f0, n, vel):
    b = bell_partials(f0 * rng.uniform(0.997, 1.003), n,
                      ((1, 1.0, 0.55), (2.0, 0.3, 0.3), (2.76, 0.28, 0.22), (4.07, 0.14, 0.12), (5.4, 0.08, 0.07)))
    b[:ns(0.0008)] *= np.linspace(0, 1, ns(0.0008))
    return b * vel


def fx_door_bell(rng, ctx):
    # the door bell as Hale goes out into the morning, and again as the door swings shut
    y = np.zeros((2, ns(3.2)))
    f0 = midi_hz(101)  # F7: sits inside the dawn chords
    for tk, v in ((0.0, 1.0), (0.1, 0.7), (0.22, 0.55), (0.38, 0.4), (0.6, 0.25)):
        add_at(y, _bell(rng, f0, ns(1.6), v), tk + rng.uniform(-0.01, 0.01), -0.45)
    for tk, v in ((1.55, 0.45), (1.68, 0.28), (1.85, 0.15)):
        add_at(y, _bell(rng, f0, ns(1.3), v), tk, -0.45)
    m = ns(0.15)
    add_at(y, 0.4 * norm(lp(noise(rng, m), 300, 2) * decay(m, 0.035, 0.002)), 1.52, -0.45)
    return norm(lp(y, 9000, 2), 0.32), 0.0


FX = dict(footsteps=fx_footsteps, coffee_pour=fx_coffee_pour, cup_set=fx_cup_set, car_door_slam=fx_car_door_slam,
          booth_squeak=fx_booth_squeak, sketchbook_open=fx_sketchbook_open, pencil_sketch=fx_pencil_sketch,
          page_turn=fx_page_turn, crowd_murmur=fx_crowd_murmur, cell_doors=fx_cell_doors, door_creak=fx_door_creak,
          coins=fx_coins, tank_rumble=fx_tank_rumble, rain_heavy=fx_rain_heavy, heartbeat=fx_heartbeat,
          metal_thud=fx_metal_thud, car_drive_away=fx_car_drive_away, page_flip_many=fx_page_flip_many,
          birds_dawn=fx_birds_dawn, fist_bump=fx_fist_bump, door_bell=fx_door_bell)
BED = ("rain_on", "room_tone_on", "rain_heavy", "rain_ease")  # kinds the ambience bed reacts to

# level (dB), hall-reverb send and diner-room send per kind
LEVEL = dict(footsteps=-17, coffee_pour=-17, cup_set=-16, car_door_slam=-12, booth_squeak=-19, sketchbook_open=-17,
             pencil_sketch=-24, page_turn=-18, crowd_murmur=-19, cell_doors=-12, door_creak=-17, coins=-18,
             tank_rumble=-13, rain_heavy=-15, heartbeat=-10, metal_thud=-10, car_drive_away=-15,
             page_flip_many=-16, birds_dawn=-19, fist_bump=-13, door_bell=-16)
HALL = dict(car_door_slam=0.35, cell_doors=0.4, crowd_murmur=0.3, tank_rumble=0.25, rain_heavy=0.3, metal_thud=0.3,
            car_drive_away=0.25, door_creak=0.12, coins=0.15, birds_dawn=0.25, heartbeat=0.05, page_turn=0.04,
            page_flip_many=0.05, pencil_sketch=0.03, door_bell=0.18)
ROOM = dict(footsteps=0.35, coffee_pour=0.3, cup_set=0.35, booth_squeak=0.3, sketchbook_open=0.3, pencil_sketch=0.25,
            page_turn=0.12, page_flip_many=0.15, fist_bump=0.35, door_bell=0.3)

# ----------------------------------------------------------------------------
# ambience: rain on the window + diner room tone
# ----------------------------------------------------------------------------

CTRL = 100  # control rate (Hz) for intensity, gusts and scene gates
RAIN_HEAVY = 1.6  # bed intensity at the turn (1 = steady night rain)
RAIN_DRIPS = 0.04  # after the ease: only drips
SKETCH_RAIN = dict(sketch_memory=0.85)  # rain gate inside the sketchbook (default 0.6)

A_WASH = 10 ** (-41 / 20)  # rms at intensity 1
A_ROOF = 10 ** (-47 / 20)
A_TICK = 10 ** (-40 / 20)
A_SPLAT = 10 ** (-38 / 20)
A_DRIP = 10 ** (-36 / 20)
A_TRAFFIC = 10 ** (-55 / 20)
A_CAR = 10 ** (-40 / 20)
A_HUM = 10 ** (-53 / 20)
A_NEON = 10 ** (-62 / 20)
A_KITCHEN = 10 ** (-44 / 20)


def _ss(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def rain_intensity(tc, t_heavy, t_ease):
    """1 = steady night rain, RAIN_HEAVY at the turn (settling a little by the
    reckoning), RAIN_DRIPS once it has eased at dawn."""
    I = np.ones_like(tc)
    if t_heavy is not None:
        I = I + (RAIN_HEAVY - 1) * _ss((tc - t_heavy) / 3.0)
        settle = (t_ease if t_ease is not None else tc[-1]) - t_heavy - 30.0
        I = I - 0.25 * _ss((tc - t_heavy - 30.0) / max(1.0, settle))
    if t_ease is not None:
        ie = float(np.interp(t_ease, tc, I))
        I = np.where(tc < t_ease, I, ie + (RAIN_DRIPS - ie) * _ss((tc - t_ease) / 8.0))
    return I


def scene_gates(tc, total):
    """(rain, room) gates per shot: the diner gets both; the sketchbook keeps a softer rain."""
    shots = direction.SHOTS
    st = [anchors.resolve(s["start"]) for s in shots] + [total + 1.0]
    rain = np.ones_like(tc)
    room = np.ones_like(tc)
    for i, s in enumerate(shots):
        m = (tc >= st[i]) & (tc < st[i + 1])
        if s["scene"] != "diner":
            rain[m] = SKETCH_RAIN.get(s["scene"], 0.6)
            room[m] = 0.0
    k = int(0.9 * CTRL)
    w = np.hanning(k)
    w /= w.sum()
    out = []
    for g in (rain, room):
        g = np.concatenate([np.full(k, g[0]), g, np.full(k, g[-1])])
        out.append(np.convolve(g, w, mode="same")[k:-k])
    return out


def _cwobble(rng, m, fc):
    return wobble(rng, m, fc, CTRL)


def _events(rng, rate, tc, rmax):
    """Inhomogeneous Poisson event times (rate sampled on tc) by thinning."""
    k = rng.poisson(rmax * tc[-1])
    t = np.sort(rng.uniform(0, tc[-1], k))
    return t[rng.random(k) < np.interp(t, tc, rate) / rmax]


def _scatter(n, t, amp, bank, which):
    """Sum of bank[which[i]] * amp[i] placed at times t (vectorized)."""
    K = bank.shape[1]
    idx = (np.round(t * SR).astype(np.int64)[:, None] + np.arange(K)[None, :]).ravel()
    val = (amp[:, None] * bank[which]).ravel()
    ok = idx < n
    return np.bincount(idx[ok], weights=val[ok], minlength=n)[:n]


def _bank(rng, count, dur, fmin, fmax, tmin, tmax, grit):
    K = ns(dur)
    t = tarr(K)
    b = np.zeros((count, K))
    for i in range(count):
        b[i] = np.sin(2 * np.pi * rng.uniform(fmin, fmax) * t + rng.uniform(0, 6.3)) * np.exp(-t / rng.uniform(tmin, tmax))
        b[i] += grit * rng.standard_normal(K) * np.exp(-t / (0.4 * tmin))
        b[i] *= np.hanning(2 * K)[K:] ** 0.5
    return b / np.max(np.abs(b), axis=1, keepdims=True)


def _drip(rng, f):
    """Gutter drip into a puddle: a rising plink and a tiny splash."""
    m = ns(0.07)
    ff = np.concatenate([glide(f * 0.62, f, ns(0.014)), np.full(m - ns(0.014), f)])
    y = np.sin(osc_phase(ff)) * decay(m, rng.uniform(0.012, 0.022), 0.0006)
    q = ns(0.004)
    y[:q] += 0.3 * hp(noise(rng, q), 2000, 2) * np.linspace(1, 0, q)
    return y


def _car_pass(rng, dur, way):
    """A car passing on the wet street outside, behind the glass."""
    n = ns(dur)
    t = tarr(n)
    c = dur / 2
    near = np.exp(-0.5 * ((t - c) / 0.9) ** 2)
    hiss = bp(noise(rng, n), 350, 2600, 2) * (0.25 + 0.75 * near) \
        * env_points(n, [(0, 0), (1.0, 1), (dur - 1.0, 1), (dur, 0)])
    ph = osc_phase(42 * (1 + 0.035 * np.tanh((c - t) / 0.6)))
    eng = lp(np.tanh(1.2 * sum(np.sin(h * ph) / h for h in (1, 2, 3, 4))), 400, 2) * near ** 1.5
    y = lp(norm(hiss) + 0.35 * norm(eng), 2400, 2)
    th = (np.clip(way * 0.85 * np.tanh((t - c) / 1.2), -1, 1) + 1) * np.pi / 4
    return norm(np.stack([y * np.cos(th), y * np.sin(th)]), 1.0)


def _kitchen(rng):
    """Something small in the far kitchen: a plate, a spoon, a pan set down."""
    n = ns(0.5)
    r = rng.random()
    if r < 0.45:
        y = bell_partials(rng.uniform(1800, 3200), n, ((1, 1, 0.08), (1.58, 0.5, 0.06), (2.4, 0.3, 0.04)))
    elif r < 0.8:
        y = np.zeros(n)
        for k in range(3):
            add_at(y, bell_partials(rng.uniform(3000, 4500), ns(0.12), ((1, 1, 0.025), (2.3, 0.4, 0.015)))
                   * rng.uniform(0.4, 1.0), 0.05 * k + rng.uniform(0, 0.02))
    else:
        y = norm(lp(noise(rng, n), 400, 2) * decay(n, 0.04, 0.002)) \
            + 0.3 * bell_partials(220, n, ((1, 1, 0.15), (2.3, 0.4, 0.08)))
    y[:ns(0.001)] *= np.linspace(0, 1, ns(0.001))
    return lp(norm(y, 1.0), 3500, 2)


def render_ambience(total, events, tl, seed=7):
    rng = np.random.default_rng(seed)
    n = ns(total)
    tc = np.arange(int(total * CTRL) + 2) / CTRL
    ts = tarr(n)

    def up(c):
        return np.interp(ts, tc, c)

    def first(kind):
        v = [t for t, k, _ in events if k == kind]
        return min(v) if v else None

    def onset(t0):
        if t0 is None:
            return np.zeros_like(tc)
        return np.ones_like(tc) if t0 <= 0.05 else _ss((tc - t0) / 1.0)

    t_heavy, t_ease = first("rain_heavy"), first("rain_ease")
    I = rain_intensity(tc, t_heavy, t_ease)
    g_rain, g_room = scene_gates(tc, total)
    end = np.clip((total - tc) / 3.0, 0, 1)
    g_rain = g_rain * onset(first("rain_on")) * end
    g_room = g_room * onset(first("room_tone_on")) * end
    out = np.zeros((2, n))

    # rain wash on the glass (gusting, with a fast granular flutter) and the roof/heavy band
    gust = 1 + 0.13 * _cwobble(rng, len(tc), 0.07) + 0.06 * _cwobble(rng, len(tc), 14.0)
    sos_w = np.concatenate([signal.butter(2, [260, 7800], "band", fs=SR, output="sos"),
                            biquad("highshelf", 3300, 0.7, -5.0), biquad("peak", 1600, 0.8, 2.5)])
    env = up(I * gust * g_rain)
    for c in range(2):
        w = signal.sosfilt(sos_w, rng.standard_normal(n))
        out[c] += w * (A_WASH / (np.std(w) + 1e-12)) * env
    heavy = np.clip((I - 1.0) / (RAIN_HEAVY - 1.0), 0, 1)
    env = up((0.25 * np.minimum(I, 1.0) + 0.75 * heavy) * g_rain)
    for c in range(2):
        w = bp(rng.standard_normal(n), 110, 520, 2)
        out[c] += w * (A_ROOF / (np.std(w) + 1e-12)) * env
    del env, w

    # droplets ticking on the glass, bigger splats on the sill
    ticks = _bank(rng, 24, 0.006, 2200, 6500, 0.0005, 0.0014, 0.3)
    splats = _bank(rng, 8, 0.03, 700, 1500, 0.002, 0.005, 0.5)
    for bank, base, ex, A in ((ticks, 85.0, 1.6, A_TICK), (splats, 5.0, 1.8, A_SPLAT)):
        rate = base * np.maximum(I, 0) ** ex * (g_rain > 0.01)
        for c in range(2):
            t = _events(rng, rate, tc, rate.max() + 1e-6)
            amp = np.minimum(rng.lognormal(0, 0.45, len(t)), 2.2) * np.interp(t, tc, g_rain)
            out[c] += A * _scatter(n, t, amp, bank, rng.integers(0, len(bank), len(t)))

    # gutter drips: steady under the rain, faster when it pours, slowing after it stops
    wet = I.copy()
    if t_ease is not None:
        ie = float(np.interp(t_ease, tc, I))
        wet = np.where(tc < t_ease, I, 0.2 + (ie - 0.2) * np.exp(-(tc - t_ease) / 14.0))
    for p, base, f in ((-0.75, 0.83, 1047.0), (0.5, 1.17, 1397.0), (0.88, 1.73, 880.0), (-0.3, 2.3, 1760.0)):
        t = rng.uniform(0, base)
        while t < total - 0.1:
            gr = float(np.interp(t, tc, g_rain))
            if gr > 0.01:
                add_at(out, _drip(rng, f * rng.uniform(0.97, 1.03)), t, p, A_DRIP * gr * rng.uniform(0.6, 1.0))
            t += base * float(np.interp(t, tc, wet)) ** -0.6 * rng.uniform(0.8, 1.2)

    # distant wet traffic: a low hiss, and now and then a car going by
    env = up((0.7 + 0.3 * _cwobble(rng, len(tc), 0.03)) * g_rain)
    for c in range(2):
        w = bp(rng.standard_normal(n), 140, 1300, 2)
        out[c] += w * (A_TRAFFIC / (np.std(w) + 1e-12)) * env
    del env, w
    avoid = [(t - 6, t + 6) for t, k, _ in events if k in ("car_door_slam", "car_drive_away")]
    if t_heavy is not None:
        avoid.append((t_heavy - 8, (t_ease if t_ease is not None else total) + 2))
    t = 8.0
    while t < total - 8:
        if not any(a <= t + 6 and t <= b for a, b in avoid):
            g = A_CAR * float(np.interp(t + 3, tc, g_rain)) * (0.7 if t_ease is not None and t > t_ease else 1.0)
            add_at(out, _car_pass(rng, 6.0, 1 if rng.random() < 0.5 else -1), t, g=g)
        t += rng.uniform(20, 38)

    # room tone: fridge hum (the compressor cuts out for the turn, back at dawn), neon buzz
    lines = {ln["id"]: ln for ln in tl["lines"]}
    t_off = lines["L31"]["end"] + 0.12 if "L31" in lines else None
    t_on = lines["L42"]["end"] + 0.35 if "L42" in lines else None
    comp = np.ones_like(tc)
    if t_off is not None and t_on is not None and t_on > t_off:
        comp = 1 - _ss((tc - t_off) / 1.2) + _ss((tc - t_on) / 2.0)
    harm = ((1, 0.3), (2, 1.0), (3, 0.42), (4, 0.28), (5, 0.12), (6, 0.07))
    per = tarr(SR // 60)
    hum = sum(a * np.sin(2 * np.pi * 60.0 * h * per + rng.uniform(0, 6.3)) for h, a in harm)
    hum = np.resize(hum * A_HUM / math.sqrt(sum(a * a for _, a in harm) / 2), n)
    hum *= up((0.92 + 0.08 * np.sin(2 * np.pi * 0.13 * tc)) * (0.25 + 0.75 * comp) * g_room)
    buzz = np.exp(-((tarr(SR // 120) * 120.0 - 0.5) / 0.05) ** 2)
    buzz = bp(np.tile(buzz - buzz.mean(), 40), 200, 4500, 2)[-(SR // 120):]  # one settled period
    buzz = np.resize(buzz * A_NEON / (np.std(buzz) + 1e-12), n)
    buzz *= up((1 + 0.3 * (_cwobble(rng, len(tc), 0.5) > 2.2)) * g_room)
    out[0] += 0.75 * hum + 0.65 * buzz
    out[1] += 0.66 * hum + 0.76 * buzz
    del hum, buzz
    m = ns(0.3)
    for tk, g in ((t_off, 1.0), (t_on, 0.7)):  # the compressor relay
        if tk is not None:
            th = lp(noise(rng, m), 260, 2) * decay(m, 0.03, 0.002) \
                + 0.2 * bp(noise(rng, m), 900, 2500, 2) * decay(m, 0.006, 0.0005)
            add_at(out, th, tk, -0.5, 10 ** (-46 / 20) * g * float(np.interp(tk, tc, g_room)) / np.max(np.abs(th)))

    # the far kitchen, quiet through the turn and the reckoning
    ir_k = make_ir(t60=0.6, predelay=0.012, bright=0.35, seed=41, early=6, width=0.9)
    hush = (t_heavy - 2.0 if t_heavy is not None else total, (t_on if t_on is not None else total) + 3.0)
    t = rng.uniform(4, 9)
    while t < total - 4:
        g = float(np.interp(t, tc, g_room))
        if not hush[0] <= t <= hush[1] and g > 0.05:
            ev = _kitchen(rng)
            wetk = convolve(np.concatenate([ev, np.zeros(ir_k.shape[1])]), ir_k)
            dry = np.zeros_like(wetk)
            dry[:, :len(ev)] = pan(ev, 0.5)
            add_at(out, 0.35 * dry + 0.8 * wetk, t, g=A_KITCHEN * g * rng.uniform(0.5, 1.0))
        t += rng.uniform(7, 16)
    return out, np.stack([g_rain, g_room])


def render_sfx(tl):
    total = tl["total"]
    n = ns(total)
    dry = np.zeros((2, n))
    hall = np.zeros((2, n))
    events = sorted(((anchors.resolve(a), k, dict(p or {})) for a, k, p in direction.SFX), key=lambda e: (e[0], e[1]))
    shot_t = np.array([anchors.resolve(s["start"]) for s in direction.SHOTS])
    ir_room = make_ir(t60=0.5, predelay=0.005, bright=0.4, seed=31, early=10, width=0.85)
    log = []
    for idx, (t, kind, params) in enumerate(events):
        if kind not in FX:
            if kind not in BED:
                print("  (unknown sfx kind, skipped):", kind)
            continue
        rng = np.random.default_rng(1234 + idx)
        scene = direction.SHOTS[max(0, int(np.searchsorted(shot_t, t, side="right")) - 1)]["scene"]
        sig, pre = FX[kind](rng, dict(t=t, events=events, tl=tl, params=params, scene=scene))
        st = sig if sig.ndim == 2 else pan(sig, 0.0)
        st = fade_edges(st.copy(), 0.001, 0.005) * 10 ** (LEVEL.get(kind, -14) / 20)
        if ROOM.get(kind):
            st = np.concatenate([st, np.zeros((2, ir_room.shape[1]))], 1)
            st = st + ROOM[kind] * convolve(st, ir_room)
        add_at(dry, st, t - pre)
        add_at(hall, st, t - pre, g=HALL.get(kind, 0.05))
        log.append((t, kind, 20 * np.log10(np.max(np.abs(st)) + 1e-9)))
    amb, gate = render_ambience(total, events, tl)
    for t, kind, _ in events:  # the bed's level a few seconds after each of its cues
        if kind in BED:
            d = 9.0 if kind == "rain_ease" else 2.0
            a, b = ns(min(total - 3.5, t + d)), ns(min(total - 0.5, t + d + 3.0))
            log.append((t, kind + " (bed rms)", 10 * np.log10(np.mean(amb[:, a:b] ** 2) + 1e-12)))
    return dry, hall, amb, log, gate
