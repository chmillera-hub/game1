"""Procedural sound effects and the night ambience bed.

render_sfx(tl) -> (sfx_dry, sfx_hall_send, ambience) as stereo arrays.
Every effect is synthesized from oscillators and filtered noise; each kind has
a level, a hall-reverb send and a pre-roll (how far before its cue it starts,
so e.g. a whoosh peaks on the cut).
"""
import math

import numpy as np

from audio_dsp import (SR, bp, env_points, eq, fade_edges, hp, lp, midi_hz, ns, pan, saw, sine, smooth_curve,
                       square, sweep, tarr)
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


# ----------------------------------------------------------------------------
# effects: each returns (signal mono or stereo, preroll_seconds)
# ----------------------------------------------------------------------------


def fx_window(rng, ctx):
    n = ns(0.75)
    t = tarr(n)
    f = 160 + 70 * np.sin(2 * np.pi * 1.4 * t) + 25 * lp(noise(rng, n), 30, 1) * 8
    src = saw(np.clip(f, 60, 400), n) * (0.6 + 0.4 * np.clip(lp(np.abs(noise(rng, n)), 25, 1) * 4, 0, 1))
    creak = bp(src, 450, 2400, 2) * env_points(n, [(0, 0), (0.08, 1), (0.45, 0.6), (0.7, 0)])
    click = bp(noise(rng, ns(0.012)), 1500, 6000, 2) * np.linspace(1, 0, ns(0.012))
    y = norm(creak, 0.35)
    y[:len(click)] += 0.5 * click
    return pan(y, -0.55), 0.0


def fx_cloth(rng, ctx):
    n = ns(0.8)
    g = lp(np.abs(noise(rng, n)), 18, 2)
    g = g / (g.max() + 1e-9)
    y = bp(noise(rng, n), 900, 5200, 2) * g * env_points(n, [(0, 0), (0.12, 1), (0.6, 0.6), (0.8, 0)])
    return pan(norm(y, 0.3), -0.2), 0.0


def fx_mug_clink(rng, ctx):
    n = ns(0.6)
    y = bell_partials(2350, n, ((1, 1.0, 0.16), (1.48, 0.6, 0.11), (2.18, 0.35, 0.07), (2.93, 0.2, 0.05)))
    y[:ns(0.001)] *= np.linspace(0, 1, ns(0.001))
    th = lp(noise(rng, ns(0.05)), 380, 2) * np.exp(-np.arange(ns(0.05)) / ns(0.01))
    y[:len(th)] += 0.8 * th
    y2 = np.zeros(n)
    k = ns(0.085)
    y2[k:] = 0.45 * y[: n - k]
    return pan(norm(y + y2, 0.35), 0.1), 0.0


def fx_sparkle(rng, ctx):
    n = ns(1.6)
    y = np.zeros((2, n))
    notes = [98, 93, 102, 97, 105]
    for i, m in enumerate(notes):
        k = ns(0.07 * i + rng.uniform(0, 0.03))
        b = bell_partials(midi_hz(m), n - k, ((1, 1, 0.7), (2.76, 0.3, 0.25), (5.4, 0.1, 0.1)))
        b[:ns(0.001)] *= np.linspace(0, 1, ns(0.001))
        y[:, k:] += pan(b * (0.9 ** i), rng.uniform(-0.6, 0.6))
    sh = hp(noise(rng, n), 7000, 2) * env_points(n, [(0, 0), (0.1, 1), (1.2, 0)]) * 0.15
    y += pan(sh, 0.2)
    return norm(y, 0.3), 0.0


_pluck_count = {"i": 0, "last": -10}


def fx_pluck_up(rng, ctx):
    t = ctx["t"]
    if t - _pluck_count["last"] > 2.5:
        _pluck_count["i"] = 0
    _pluck_count["last"] = t
    i = _pluck_count["i"]
    _pluck_count["i"] += 1
    m = [74, 78, 81, 86, 90][min(i, 4)]
    f0 = midi_hz(m)
    n = ns(0.6)
    tt = tarr(n)
    f = f0 * (1 + 0.6 * np.exp(-tt / 0.012))
    y = np.sin(osc_phase(f)) * decay(n, 0.12, 0.001)
    y += 0.3 * np.sin(2 * osc_phase(f)) * decay(n, 0.05, 0.001)
    return pan(norm(y, 0.32), 0.25 * (i - 1.5)), 0.0


def fx_shrink_down(rng, ctx):
    n = ns(0.55)
    f = glide(1100, 260, n)
    y = np.sin(osc_phase(f)) * env_points(n, [(0, 0), (0.03, 1), (0.4, 0.7), (0.55, 0)])
    y += 0.25 * np.sin(osc_phase(f * 2.01)) * env_points(n, [(0, 0), (0.03, 1), (0.3, 0.2), (0.55, 0)])
    w = sweep(noise(rng, n), glide(4000, 600, n), "band", 1.2) * env_points(n, [(0, 0), (0.05, 1), (0.55, 0)])
    y = 0.8 * norm(y) + 0.35 * norm(w)
    return pan(norm(y, 0.28), 0.0), 0.0


def fx_squeeze(rng, ctx):
    n = ns(0.6)
    t = tarr(n)
    fc = 750 + 380 * np.sin(2 * np.pi * 2.2 * t) * np.exp(-t / 0.4) + 200 * t
    car = np.sin(osc_phase(fc + 60 * np.sin(2 * np.pi * 38 * t)))
    sq = bp(car, 500, 3000, 1) * env_points(n, [(0, 0), (0.04, 1), (0.45, 0.6), (0.6, 0)])
    wh = np.sin(osc_phase(glide(140, 70, n))) * decay(n, 0.12, 0.005)
    y = 0.6 * norm(sq) + 0.5 * norm(wh)
    return pan(norm(y, 0.3), 0.0), 0.0


def fx_whoosh(rng, ctx, dur=1.15, f=(260, 1900, 420), peak=0.55, p=(-0.8, 0.8)):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    k = peak
    fc = np.where(x < k, f[0] * (f[1] / f[0]) ** (x / k), f[1] * (f[2] / f[1]) ** ((x - k) / (1 - k)))
    y = sweep(noise(rng, n), fc, "band", 0.9)
    env = np.where(x < k, (x / k) ** 2.2, ((1 - x) / (1 - k)) ** 1.6)
    y = y * env
    return stereo_sweep(norm(y, 0.42), *p), dur * k


def fx_whoosh_up(rng, ctx):
    n = ns(1.8)
    x = np.linspace(0, 1, n)
    fc = 300 * (6000 / 300) ** x
    y = sweep(noise(rng, n), fc, "band", 1.1) * x ** 2.0 * (1 - smooth_curve(n, ns(1.62), ns(1.8)))
    tone = np.sin(osc_phase(glide(500, 2200, n))) * x ** 3 * 0.25 * (1 - smooth_curve(n, ns(1.55), ns(1.8)))
    tone += 0.15 * np.sin(osc_phase(glide(750, 3300, n))) * x ** 3 * (1 - smooth_curve(n, ns(1.55), ns(1.8)))
    return stereo_sweep(norm(y + tone, 0.42), -0.4, 0.4), 0.0


def fx_bubble(rng, ctx):
    n = ns(1.6)
    bl = np.sin(osc_phase(glide(180, 560, ns(0.13)))) * decay(ns(0.13), 0.06, 0.002)
    y = np.zeros(n)
    y[:len(bl)] += bl
    t = tarr(n)
    sh = np.zeros(n)
    for m, a in ((86, 1.0), (90, 0.7), (93, 0.6), (98, 0.4)):
        sh += a * np.sin(2 * np.pi * midi_hz(m) * t) * (1 + 0.3 * np.sin(2 * np.pi * (3 + m % 5) * t))
    sh *= env_points(n, [(0, 0), (0.3, 0.6), (0.9, 0.35), (1.6, 0)]) * 0.12
    y = norm(y, 0.5) + sh
    return pan(norm(y, 0.3), 0.0), 0.0


def fx_pop_small(rng, ctx):
    n = ns(0.18)
    f0 = rng.uniform(1100, 1700)
    y = np.sin(osc_phase(glide(f0, f0 * 0.45, n))) * decay(n, 0.035, 0.0008)
    c = hp(noise(rng, ns(0.004)), 2000, 2) * np.linspace(1, 0, ns(0.004))
    y[:len(c)] += 0.3 * c
    return pan(norm(y, 0.28), rng.uniform(-0.4, 0.4)), 0.0


def fx_weight(rng, ctx):
    n = ns(0.9)
    y = np.sin(osc_phase(glide(95, 55, n))) * decay(n, 0.22, 0.003)
    y += 0.6 * bp(noise(rng, n), 120, 700, 2) * decay(n, 0.05, 0.001)
    y += 0.25 * bell_partials(210, n, ((1, 1, 0.35), (1.57, 0.6, 0.25), (2.3, 0.3, 0.15)))
    return pan(norm(y, 0.5), 0.0), 0.0


def fx_ear_pop(rng, ctx):
    n = ns(0.3)
    y = np.sin(osc_phase(glide(560, 170, ns(0.08)))) * decay(ns(0.08), 0.03, 0.001)
    y = np.concatenate([y, np.zeros(n - len(y))])
    puff = lp(noise(rng, n), 900, 2) * decay(n, 0.04, 0.002) * 0.4
    return pan(norm(y + puff, 0.32), 0.15), 0.0


def fx_scale_step(rng, ctx):
    n = ns(0.7)
    t = tarr(n)
    thump = np.sin(osc_phase(glide(110, 60, n))) * decay(n, 0.09, 0.002)
    spring = np.sin(osc_phase(320 * (1 + 0.12 * np.sin(2 * np.pi * 17 * t) * np.exp(-t / 0.18)))) * decay(n, 0.2, 0.004)
    rattle = bp(noise(rng, n), 1800, 6000, 2) * decay(n, 0.03, 0.001)
    y = norm(thump, 0.6) + 0.35 * norm(spring) + 0.2 * norm(rattle)
    return pan(norm(y, 0.45), 0.0), 0.0


def fx_needle(rng, ctx):
    n = ns(1.5)
    y = np.zeros(n)
    times = np.cumsum(0.11 * np.concatenate([np.linspace(1.0, 0.35, 9), np.linspace(0.35, 0.9, 6)]))
    for k, tk in enumerate(times):
        i = ns(tk)
        if i + ns(0.006) < n:
            c = bp(noise(rng, ns(0.006)), 2500, 7500, 2) * np.linspace(1, 0, ns(0.006))
            c[:ns(0.0004)] *= np.linspace(0, 1, ns(0.0004))
            y[i:i + len(c)] += c * (0.6 + 0.4 * (k % 2))
    i = ns(times[-1] + 0.05)
    m = n - i
    tt = tarr(m)
    boing = np.sin(osc_phase(430 * (1 + 0.18 * np.sin(2 * np.pi * 13 * tt) * np.exp(-tt / 0.25)))) * decay(m, 0.22, 0.004)
    y[i:] += 0.6 * norm(boing)
    return pan(norm(y, 0.35), 0.1), 0.0


def _spin(rng, dur, rate0, rate1, band, whistle=None):
    n = ns(dur)
    t = tarr(n)
    rate = glide(rate0, rate1, n)
    ph = osc_phase(rate)
    am = np.abs(np.sin(ph / 2)) ** 2
    y = bp(noise(rng, n), band[0], band[1], 2) * am
    env = env_points(n, [(0, 0), (0.25, 1), (dur - 0.3, 0.9), (dur, 0)])
    y *= env
    if whistle:
        y += 0.15 * np.sin(osc_phase(glide(whistle[0], whistle[1], n))) * env * am
    p = np.sin(ph / 2)
    th = (np.clip(p, -1, 1) + 1) * np.pi / 4
    st = np.stack([y * np.cos(th), y * np.sin(th)])
    return norm(st, 0.33)


def fx_spin_slow(rng, ctx):
    return _spin(rng, 2.0, 1.4, 1.8, (300, 1500)), 0.0


def fx_spin_fast(rng, ctx):
    return _spin(rng, 1.0, 4.0, 9.0, (500, 3200), (900, 1500)), 0.0


def fx_tick_fast(rng, ctx):
    n = ns(2.0)
    y = np.zeros(n)
    t = 0.0
    k = 0
    while t < 1.85:
        rate = 2 + 12 * (t / 1.85) ** 1.5
        i = ns(t)
        m = ns(0.03)
        if i + m < n:
            tick = bp(noise(rng, m), 2000, 5000, 2) * decay(m, 0.004, 0.0005)
            tick += 0.5 * np.sin(2 * np.pi * (1800 if k % 2 else 1500) * tarr(m)) * decay(m, 0.008, 0.0005)
            y[i:i + m] += tick
        t += 1 / rate
        k += 1
    return pan(norm(y, 0.3), 0.2), 0.0


def fx_thud(rng, ctx):
    n = ns(0.9)
    y = np.sin(osc_phase(glide(80, 42, n))) * decay(n, 0.25, 0.002)
    y += 0.5 * lp(noise(rng, n), 300, 2) * decay(n, 0.05, 0.001)
    return pan(norm(y, 0.55), 0.0), 0.0


def fx_pump(rng, ctx):
    n = ns(1.5)
    y = np.zeros(n)
    for k in range(3):
        i = ns(0.06 + 0.45 * k)
        m = ns(0.32)
        if i + m > n:
            break
        hiss = bp(noise(rng, m), 2200, 7500, 2) * env_points(m, [(0, 0), (0.12, 1), (0.22, 0.5), (0.32, 0)])
        squeak = np.sin(osc_phase(glide(1500, 1800, m) + 120 * np.sin(2 * np.pi * 30 * tarr(m)))) \
            * env_points(m, [(0, 0), (0.03, 0.6), (0.1, 0.1), (0.32, 0)])
        y[i:i + m] += 0.8 * hiss + 0.15 * squeak
    return pan(norm(y, 0.3), 0.1), 0.0


def fx_steam(rng, ctx):
    n = ns(3.0)
    y = hp(noise(rng, n), 3500, 2) * env_points(n, [(0, 0), (0.8, 1), (2.0, 0.8), (3.0, 0)])
    y = lp(y, 9000, 2)
    bub = np.zeros(n)
    for _ in range(18):
        i = rng.integers(0, n - ns(0.05))
        m = ns(0.05)
        f0 = rng.uniform(180, 420)
        bub[i:i + m] += np.sin(osc_phase(glide(f0, f0 * 1.8, m))) * decay(m, 0.015, 0.001)
    st = np.stack([y, hp(noise(rng, n), 3500, 2) * env_points(n, [(0, 0), (0.8, 1), (2.0, 0.8), (3.0, 0)])])
    st = norm(st, 0.25) + pan(norm(bub, 0.12), 0.0)
    return st, 0.0


def fx_rumble(rng, ctx):
    n = ns(3.6)
    y = lp(noise(rng, n), 120, 2) * env_points(n, [(0, 0), (1.4, 1), (2.6, 0.8), (3.6, 0)])
    cr = np.zeros(n)
    for _ in range(40):
        i = rng.integers(0, n - 200)
        cr[i:i + 120] += rng.uniform(-1, 1) * np.linspace(1, 0, 120)
    cr = lp(cr, 2200, 2) * env_points(n, [(0, 0), (1.0, 1), (3.6, 0)])
    st = np.stack([y + 0.3 * cr, lp(noise(rng, n), 120, 2) * env_points(n, [(0, 0), (1.4, 1), (2.6, 0.8), (3.6, 0)])
                   + 0.3 * cr])
    return norm(st, 0.55), 0.0


def fx_riser(rng, ctx):
    t = ctx["t"]
    # length: up to the next big hit if one follows soon
    nxt = [tt for tt, k in ctx["events"] if k in ("implode", "boom", "whoosh_up") and t < tt < t + 7.5]
    dur = (nxt[0] - t + 0.6) if nxt else 2.6
    n = ns(dur)
    x = np.linspace(0, 1, n)
    y = sweep(noise(rng, n), 400 * (7000 / 400) ** x, "band", 1.3) * x ** 2.4
    tone = np.sin(osc_phase(glide(220, 440, n))) * x ** 2.5 * 0.35
    tone += 0.2 * np.sin(osc_phase(glide(330, 660, n))) * x ** 2.5
    out = (y / (np.max(np.abs(y)) + 1e-9) + tone) * (1 - smooth_curve(n, n - ns(0.25), n))
    return stereo_sweep(norm(out, 0.38), -0.3, 0.3), 0.0


def fx_elephant(rng, ctx):
    n = ns(0.95)
    t = tarr(n)
    f = np.interp(t, [0, 0.18, 0.55, 0.95], [330, 640, 470, 410]) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
    src = saw(f, n) * (1 + 0.35 * np.sin(2 * np.pi * 27 * t))
    y = eq(lp(src, 3200, 2), ("peak", 1100, 1.2, 8.0), ("peak", 2300, 2.0, 5.0), ("highpass", 200, 0.7, 0.0))
    y *= env_points(n, [(0, 0), (0.05, 1), (0.7, 0.85), (0.95, 0)])
    breath = bp(noise(rng, n), 1000, 4000, 2) * env_points(n, [(0, 0), (0.05, 0.3), (0.95, 0)]) * 0.15
    return pan(norm(y + breath * np.max(np.abs(y)), 0.42), 0.2), 0.0


def fx_fling(rng, ctx):
    w, _ = fx_whoosh(rng, ctx, 0.6, (500, 2600, 700), 0.4, (-0.6, 0.7))
    n = ns(0.6)
    t = tarr(n)
    zing = np.sin(osc_phase(glide(3200, 1100, n) * (1 + 0.01 * np.sin(2 * np.pi * 30 * t)))) \
        * env_points(n, [(0, 0), (0.02, 1), (0.5, 0.3), (0.6, 0)])
    y = w + stereo_sweep(norm(zing, 0.18), -0.3, 0.9)
    return norm(y, 0.35), 0.0


def fx_crunch(rng, ctx):
    n = ns(1.2)
    y = np.zeros(n)
    t = 0.0
    while t < 1.0:
        i = ns(t)
        m = ns(rng.uniform(0.004, 0.02))
        if i + m < n:
            y[i:i + m] += bp(noise(rng, m), 900, 6000, 2) * np.hanning(m) * rng.uniform(0.4, 1.0)
        t += 0.06 * (1 - t) ** 1.5 + 0.004
    grr = lp(noise(rng, n), 180, 2) * (1 + np.sin(2 * np.pi * 31 * tarr(n))) * env_points(n, [(0, 0), (0.9, 1), (1.2, 0)])
    th = np.sin(osc_phase(glide(90, 45, ns(0.4)))) * decay(ns(0.4), 0.12, 0.002)
    out = norm(y, 0.6) + 0.4 * norm(grr)
    k = ns(0.95)
    out[k:k + len(th)] += 0.6 * th[: n - k]
    return pan(norm(out, 0.42), 0.0), 0.0


def fx_boom_small(rng, ctx):
    n = ns(1.8)
    y = np.sin(osc_phase(glide(78, 36, n))) * decay(n, 0.5, 0.004)
    y += 0.5 * bp(noise(rng, n), 80, 450, 2) * decay(n, 0.09, 0.002)
    return pan(norm(y, 0.55), 0.0), 0.0


def fx_implode(rng, ctx):
    n = ns(1.45)
    x = np.linspace(0, 1, n)
    y = sweep(noise(rng, n), 9000 * (250 / 9000) ** x, "low", 0.8) * x ** 3.0
    tone = np.sin(osc_phase(glide(900, 90, n))) * x ** 3 * 0.4
    y = (norm(y) + tone) * (1 - smooth_curve(n, ns(1.3), ns(1.33)))
    th = np.sin(osc_phase(glide(140, 60, ns(0.12)))) * decay(ns(0.12), 0.04, 0.001)
    k = ns(1.3)
    y[k:k + len(th)] += 0.5 * th[: n - k]
    return stereo_sweep(norm(y, 0.45), 0.6, -0.1), 1.3 - 0.05


def fx_boom(rng, ctx):
    n = ns(5.5)
    t = tarr(n)
    f = 26 + 40 * np.exp(-t / 0.5)
    sub = np.sin(osc_phase(f)) * decay(n, 1.5, 0.004)
    sub += 0.25 * np.sin(2 * osc_phase(f)) * decay(n, 0.8, 0.004)
    hit = lp(noise(rng, n), 260, 2) * decay(n, 0.22, 0.002)
    tail = np.stack([lp(noise(rng, n), 90, 2), lp(noise(rng, n), 90, 2)]) * decay(n, 1.8, 0.2)[None, :]
    body = np.sin(osc_phase(glide(120, 70, n))) * decay(n, 0.35, 0.003)
    body = np.tanh(2.0 * body)
    mono = norm(sub, 0.55) + 0.35 * norm(hit) + 0.3 * norm(body)
    st = np.stack([mono, mono]) + 0.25 * tail / (np.max(np.abs(tail)) + 1e-9)
    return norm(st, 0.7), 0.0


def fx_orbit_whir(rng, ctx):
    n = ns(4.0)
    t = tarr(n)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * 26 * t)
    tone = np.sin(2 * np.pi * 230 * t + 0.5 * np.sin(2 * np.pi * 26 * t)) * am
    band = bp(noise(rng, n), 700, 2200, 2) * am
    env = env_points(n, [(0, 0), (0.8, 1), (3.0, 0.8), (4.0, 0)])
    y = (0.6 * norm(tone) + 0.4 * norm(band)) * env
    p = 0.6 * np.sin(2 * np.pi * 3.2 * t)
    th = (p + 1) * np.pi / 4
    return norm(np.stack([y * np.cos(th), y * np.sin(th)]), 0.22), 0.0


def fx_gw_chirp(rng, ctx):
    t0 = ctx["t"]
    try:
        end = anchors.resolve(anchors.Wd("L47", "space", "end", 0.12))
    except Exception:
        end = t0 + 3.9
    D = max(2.0, end - t0)
    n = ns(D)
    t = tarr(n)
    tau = (D + 0.004) - t
    f = 55.0 * ((D + 0.004) / tau) ** 0.375
    f = np.minimum(f, 900)
    a = (f / f[0]) ** (2 / 3)
    ph = osc_phase(f)
    y = np.tanh(1.6 * np.sin(ph)) * a
    y += 0.35 * np.sin(2 * ph) * a
    y = hp(y, 45, 2)
    y *= smooth_curve(n, 0, ns(0.4))
    y[-ns(0.004):] *= np.linspace(1, 0, ns(0.004))
    return pan(norm(y, 0.45), 0.0), 0.0


def fx_space_tone(rng, ctx):
    n = ns(6.5)
    t = tarr(n)
    y = np.zeros(n)
    for m, a, beat in ((62, 1.0, 0.21), (69, 0.7, 0.33), (74, 0.5, 0.17), (81, 0.25, 0.27)):
        f = midi_hz(m)
        y += a * (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f + beat) * t)) * 0.5
    y *= env_points(n, [(0, 0), (1.8, 1), (3.5, 0.8), (6.5, 0)])
    return np.stack([norm(y, 0.16), norm(np.roll(y, ns(0.011)), 0.16)]), 0.0


def fx_boing(rng, ctx):
    n = ns(0.75)
    t = tarr(n)
    f = 290 * (1 + 0.28 * np.sin(2 * np.pi * 15 * t) * np.exp(-t / 0.3)) * (1 - 0.1 * t)
    y = np.sin(osc_phase(f)) * decay(n, 0.25, 0.003)
    y += 0.3 * np.sin(2 * osc_phase(f)) * decay(n, 0.12, 0.003)
    return pan(norm(y, 0.36), 0.15), 0.0


def fx_chime(rng, ctx):
    n = ns(3.2)
    y = np.zeros((2, n))
    for i, m in enumerate((93, 98, 102, 105)):
        k = ns(0.09 * i + rng.uniform(0, 0.02))
        b = bell_partials(midi_hz(m), n - k, ((1, 1, 1.4), (2.76, 0.35, 0.5), (5.4, 0.12, 0.2)))
        b[:ns(0.001)] *= np.linspace(0, 1, ns(0.001))
        y[:, k:] += pan(b * 0.85 ** i, -0.6 + 0.4 * i)
    return norm(y, 0.3), 0.0


FX = dict(window=fx_window, cloth=fx_cloth, mug_clink=fx_mug_clink, sparkle=fx_sparkle, pluck_up=fx_pluck_up,
          shrink_down=fx_shrink_down, squeeze=fx_squeeze, whoosh=fx_whoosh, whoosh_up=fx_whoosh_up,
          bubble=fx_bubble, pop_small=fx_pop_small, weight=fx_weight, ear_pop=fx_ear_pop,
          scale_step=fx_scale_step, needle=fx_needle, spin_slow=fx_spin_slow, spin_fast=fx_spin_fast,
          tick_fast=fx_tick_fast, thud=fx_thud, pump=fx_pump, steam=fx_steam, rumble=fx_rumble, riser=fx_riser,
          elephant=fx_elephant, fling=fx_fling, crunch=fx_crunch, boom_small=fx_boom_small, implode=fx_implode,
          boom=fx_boom, orbit_whir=fx_orbit_whir, gw_chirp=fx_gw_chirp, space_tone=fx_space_tone, boing=fx_boing,
          chime=fx_chime)

# level (dB) and hall-reverb send per kind
LEVEL = dict(window=-14, cloth=-18, mug_clink=-15, sparkle=-13, pluck_up=-12, shrink_down=-12, squeeze=-12,
             whoosh=-11, whoosh_up=-9, bubble=-11, pop_small=-12, weight=-9, ear_pop=-11, scale_step=-10,
             needle=-11, spin_slow=-13, spin_fast=-12, tick_fast=-14, thud=-8, pump=-12, steam=-12, rumble=-9,
             riser=-11, elephant=-8, fling=-11, crunch=-11, boom_small=-7, implode=-8, boom=-11, orbit_whir=-13,
             gw_chirp=-7, space_tone=-12, boing=-10, chime=-11)
HALL = dict(sparkle=0.4, pluck_up=0.2, bubble=0.35, pop_small=0.15, shrink_down=0.2, whoosh_up=0.25,
            chime=0.45, space_tone=0.6, boom=0.25, boom_small=0.2, implode=0.15, riser=0.2, elephant=0.15,
            weight=0.1, thud=0.1, needle=0.1, tick_fast=0.1, squeeze=0.1, window=0.1, mug_clink=0.15,
            orbit_whir=0.2, gw_chirp=0.0, steam=0.2, rumble=0.2, crunch=0.15, boing=0.15, fling=0.15)

# ----------------------------------------------------------------------------
# ambience (night crickets + soft wind)
# ----------------------------------------------------------------------------


def _impulses(n, times):
    x = np.zeros(n)
    idx = (np.asarray(times) * SR).astype(int)
    idx = idx[(idx >= 0) & (idx < n)]
    np.add.at(x, idx, 1.0)
    return x


def render_ambience(total, seed=5):
    from scipy import signal
    rng = np.random.default_rng(seed)
    n = ns(total)
    out = np.zeros((2, n))
    # field crickets: chirps of 3-4 pulses
    for c, (fc, rate, lev, p) in enumerate(((4450, 1.35, 1.0, -0.55), (4720, 1.1, 0.75, 0.45),
                                            (4180, 1.6, 0.5, 0.1), (4930, 0.9, 0.4, 0.8), (4300, 1.25, 0.3, -0.9))):
        times = []
        t = rng.uniform(0, 0.8)
        while t < total:
            npulse = rng.integers(3, 5)
            for k in range(npulse):
                times.append(t + k * 0.034)
            t += (1 / rate) * rng.uniform(0.8, 1.25)
            if rng.random() < 0.06:
                t += rng.uniform(1.0, 3.0)  # pause now and then
        pl = ns(0.016)
        shape = np.hanning(pl)
        envc = signal.oaconvolve(_impulses(n, times), shape, mode="full")[:n]
        tt = np.arange(n) / SR
        car = np.sin(2 * np.pi * fc * tt + 0.8 * np.sin(2 * np.pi * 31 * tt))
        y = car * envc * lev
        th = (p + 1) * np.pi / 4
        out[0] += y * math.cos(th)
        out[1] += y * math.sin(th)
    # distant trill (tree crickets) breathing in and out
    tt = np.arange(n) / SR
    trill = np.sin(2 * np.pi * 2870 * tt) * (0.5 + 0.5 * np.sin(2 * np.pi * 47 * tt)) ** 3
    trill *= 0.18 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.045 * tt + 1.0))
    out[0] += trill * 0.8
    out[1] += np.roll(trill, ns(0.013)) * 0.8
    out = lp(out, 7000, 2)
    # soft wind
    w = lp(rng.standard_normal((2, n)), 420, 2)
    w = lp(w, 700, 1)
    wa = 0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * tt + 2.0) * np.sin(2 * np.pi * 0.023 * tt)
    w *= (0.3 + 0.7 * wa)[None, :]
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.5 + w / (np.max(np.abs(w)) + 1e-9) * 0.22
    return out


def ambience_gate(total, events):
    """1 where crickets are on (events) AND the shot is an outdoor night shot."""
    n = ns(total)
    state = np.zeros(n)
    on = False
    last = 0.0
    evs = sorted([(t, k) for t, k in events if k in ("crickets_on", "crickets_off")])
    for t, k in evs:
        if on:
            state[ns(last):ns(t)] = 1.0
        on = (k == "crickets_on")
        last = t
    if on:
        state[ns(last):] = 1.0
    # scene gating
    shots = direction.SHOTS
    st = [anchors.resolve(s["start"]) for s in shots]
    scene = np.zeros(n)
    for i, s in enumerate(shots):
        a = st[i]
        b = st[i + 1] if i + 1 < len(shots) else total
        lev = {"roof": 1.0, "pinch": 1.0, "split_moon": 0.8, "suitcase": 0.3}.get(s["scene"], 0.0)
        scene[ns(a):ns(b)] = lev
    g = state * scene
    # smooth transitions (~0.9 s)
    k = ns(0.9)
    win = np.hanning(k)
    win /= win.sum()
    from scipy import signal
    g = signal.oaconvolve(np.concatenate([np.full(k, g[0]), g, np.full(k, g[-1])]), win, mode="same")[k:-k]
    return np.clip(g, 0, 1)


def render_sfx(tl):
    total = tl["total"]
    n = ns(total)
    dry = np.zeros((2, n))
    hall = np.zeros((2, n))
    events = [(anchors.resolve(a), k) for a, k, _ in direction.SFX]
    log = []
    for idx, (t, kind) in enumerate(sorted(events)):
        if kind in ("crickets_on", "crickets_off"):
            continue
        if kind not in FX:
            print("  (unknown sfx kind, skipped):", kind)
            continue
        rng = np.random.default_rng(1234 + idx)
        sig, pre = FX[kind](rng, dict(t=t, events=events, tl=tl))
        st = sig if sig.ndim == 2 else pan(sig, 0.0)
        st = fade_edges(st.copy(), 0.001, 0.005)
        g = 10 ** (LEVEL.get(kind, -12) / 20)
        i = ns(t - pre)
        k0 = 0
        if i < 0:
            k0, i = -i, 0
        j = min(n, i + st.shape[1] - k0)
        if j <= i:
            continue
        seg = st[:, k0:k0 + (j - i)] * g
        dry[:, i:j] += seg
        hall[:, i:j] += seg * HALL.get(kind, 0.05)
        log.append((t, kind, 20 * np.log10(np.max(np.abs(seg)) + 1e-9)))
    amb = render_ambience(total)
    gate = ambience_gate(total, events)
    amb *= gate[None, :] * 10 ** (-24 / 20)
    return dry, hall, amb, log, gate
