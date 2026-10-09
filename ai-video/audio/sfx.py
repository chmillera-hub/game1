"""Procedural sound-effects library.

    render(name, sr=48000, seed=0) -> float32 (n, 2), peak about -12 dBFS
    NAMES    – every available effect
    ALIASES  – forgiving alternative names ("thud" -> brick_thud, ...)

`seed` gives small natural variations (useful for repeated clacks/pops).
All synthesis is numpy/scipy; nothing is sampled from disk.
"""
import math
import os
import sys
from functools import lru_cache

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio.music import (TAU, bp, biquad, dr_kick, dr_snare, dr_swell, dr_timpani,  # noqa: E402
                         dr_wood, env_adsr, fade_edges, hp, hz, inst_bell, inst_brass,
                         inst_pluck, inst_strings_sect, lp, pan, perc_env, pulse, reverb, saw,
                         secs, seeded, sine, smooth_noise, stereoize, tv_filter, tvec, up2)

PEAK_DB = -12.0
_FX = {}


def fx(name, trim=0.0):
    """Register an effect. trim (dB) balances perceived loudness after peak-norm."""
    def deco(fn):
        _FX[name] = (fn, trim)
        return fn
    return deco


def _rng(name, seed):
    return seeded("sfx", name, seed)


def _place(dst, src, t, sr, gain=1.0, p=0.0):
    src = pan(src, p) if src.ndim == 1 else src
    i0 = int(round(t * sr))
    e = min(len(dst), i0 + len(src))
    if e > i0:
        dst[i0:e] += src[: e - i0] * gain


def _cut(y, sr, dur, fade=0.04):
    """Truncate to `dur` seconds with a smooth fade (never a hard cut)."""
    y = np.array(y[: secs(sr, dur)], dtype=float)
    return fade_edges(y, sr, 0.0, fade) if len(y) else y


def _canvas(sr, dur):
    return np.zeros((secs(sr, dur), 2))


def _room(x, sr, mix=0.15, rt60=0.6, predelay=0.008, damp=0.6):
    x = stereoize(x)
    return x + mix * reverb(x, sr, rt60=rt60, predelay=predelay, damp=damp, seed=11)


# =============================================================================
# keyboard / UI
# =============================================================================
def _clack(sr, rng, vel=1.0, space=False):
    n = secs(sr, 0.13)
    t = tvec(n, sr)
    nz = rng.standard_normal(n)
    click = bp(nz, 2000, 6500, sr) * np.exp(-t / 0.0022)
    f0 = (120 if space else 200) * rng.uniform(0.9, 1.1)
    thock = 0.7 * np.sin(TAU * f0 * t) * np.exp(-t / (0.03 if space else 0.016))
    thock += 0.35 * np.sin(TAU * f0 * 2.7 * t) * np.exp(-t / 0.007)
    y = click * 0.9 + thock
    tr = rng.uniform(0.045, 0.07)
    y += 0.35 * bp(nz[::-1], 2500, 7000, sr) * np.exp(-np.maximum(t - tr, 0) / 0.0018) * \
        np.clip((t - tr) / 0.0004, 0, 1) ** 2
    return fade_edges(y * vel, sr, 0.0003, 0.01)


@fx("key_clack")
def _key_clack(sr, rng):
    return pan(_clack(sr, rng), rng.uniform(-0.15, 0.15))


@fx("typing", trim=-1.0)
def _typing(sr, rng):
    out = _canvas(sr, 1.3)
    t = 0.0
    k = 0
    while t < 1.12:
        space = k in (5, 11)
        _place(out, _clack(sr, rng, rng.uniform(0.55, 1.0), space), t, sr, 1.0, rng.uniform(-0.25, 0.25))
        t += max(0.045, rng.gamma(4.0, 0.022)) + (0.12 if k == 7 else 0)
        k += 1
    return out


@fx("send")
def _send(sr, rng):
    out = _canvas(sr, 0.45)
    n = secs(sr, 0.26)
    t = tvec(n, sr)
    nz = rng.standard_normal(n)
    w = tv_filter(nz, 600 * (4000 / 600) ** (t / 0.26), sr, "bandpass", q=1.6, stages=1)
    env = np.sin(np.pi * np.clip(t / 0.26, 0, 1)) ** 2 * np.clip(t / 0.18, 0, 1)
    _place(out, w * env * 0.8, 0.0, sr, 1.0, -0.2)
    nb = secs(sr, 0.17)
    tb = tvec(nb, sr)
    f = 700 + 700 * np.clip(tb / 0.05, 0, 1) ** 0.7
    blip = sine(f, nb, sr) + 0.2 * sine(2 * f, nb, sr)
    blip *= perc_env(nb, sr, 0.06, 0.002)
    _place(out, blip * 0.8, 0.2, sr, 1.0, 0.15)
    return _room(out, sr, 0.12)


@fx("receive")
def _receive(sr, rng):
    out = _canvas(sr, 1.0)
    for i, (m, tt) in enumerate(((83, 0.0), (88, 0.075))):
        n = secs(sr, 0.9)
        t = tvec(n, sr)
        f = hz(m)
        y = (np.sin(TAU * f * t) + 0.12 * np.sin(TAU * 2 * f * t) * np.exp(-t / 0.1)) * \
            np.exp(-t / 0.28) * np.clip(t / 0.003, 0, 1)
        _place(out, fade_edges(y, sr, 0.001, 0.02) * (0.75 if i == 0 else 1.0), tt, sr)
    return _room(out, sr, 0.15)


@fx("pop")
def _pop(sr, rng):
    n = secs(sr, 0.12)
    t = tvec(n, sr)
    f0 = rng.uniform(320, 380)
    f = f0 + 650 * np.clip(t / 0.025, 0, 1)
    y = sine(f, n, sr) * np.exp(-t / 0.022) * np.clip(t / 0.001, 0, 1)
    y += 0.3 * bp(rng.standard_normal(n), 1500, 5000, sr) * np.exp(-t / 0.0015)
    return pan(fade_edges(y, sr, 0.0003, 0.01), 0)


@fx("puzzle_click")
def _puzzle_click(sr, rng):
    out = _canvas(sr, 0.22)
    n = secs(sr, 0.05)
    t = tvec(n, sr)
    tick = np.sin(TAU * 2800 * t) * np.exp(-t / 0.006) + 0.5 * bp(rng.standard_normal(n), 2000, 6000, sr) * \
        np.exp(-t / 0.0015)
    _place(out, fade_edges(tick, sr, 0.0002, 0.005) * 0.6, 0.0, sr)
    n = secs(sr, 0.12)
    t = tvec(n, sr)
    thunk = np.sin(TAU * 900 * t) * np.exp(-t / 0.012) + 0.9 * np.sin(TAU * 175 * t) * np.exp(-t / 0.03)
    thunk += 0.4 * bp(rng.standard_normal(n), 400, 3000, sr) * np.exp(-t / 0.003)
    _place(out, fade_edges(thunk, sr, 0.0012, 0.01), 0.045, sr)
    return out


@fx("scan_beep", trim=-4.0)
def _scan_beep(sr, rng):
    out = _canvas(sr, 0.95)
    n = secs(sr, 0.6)
    t = tvec(n, sr)
    tri = 2 * np.abs((t / 0.3) % 1 - 0.5)
    f = 700 + 800 * tri
    y = sine(f, n, sr) * (0.6 + 0.4 * np.sin(TAU * 28 * t)) * env_adsr(n, sr, 0.04, 1, 1, 0.06, 0.54)
    _place(out, y * 0.45, 0.0, sr, 1.0, -0.2)
    for tt in (0.63, 0.76):
        nb = secs(sr, 0.075)
        tb = tvec(nb, sr)
        b = lp(pulse(1500, nb, sr, 0.5), 3500, sr) * env_adsr(nb, sr, 0.003, 1, 1, 0.01, 0.06, False)
        _place(out, b * 0.8, tt, sr, 1.0, 0.1)
    return out


@fx("power_down")
def _power_down(sr, rng):
    n = secs(sr, 1.4)
    t = tvec(n, sr)
    f = 520 * np.exp(-t / 0.42) + 32
    y = saw(f, n, sr) * 0.6 + sine(f * 0.5, n, sr) * 0.5
    y = tv_filter(y, np.maximum(f * 5, 120), sr, "lowpass", q=1.2, block=128)
    y *= np.exp(-t / 0.55) * np.clip(t / 0.01, 0, 1)
    y += 0.25 * np.sin(TAU * 60 * t) * np.exp(-t / 0.3)
    return pan(fade_edges(y, sr, 0.001, 0.08), 0)


@fx("glitch", trim=-2.0)
def _glitch(sr, rng):
    out = np.zeros(secs(sr, 0.62))
    t = 0.0
    prev = None
    while t < 0.56:
        d = rng.uniform(0.02, 0.065)
        n = secs(sr, d)
        kind = rng.choice(["tone", "crush", "stutter", "gap"], p=[0.35, 0.3, 0.25, 0.1])
        if kind == "tone":
            seg = lp(pulse(rng.uniform(180, 1600), n, sr, rng.uniform(0.2, 0.5)), 6000, sr)
        elif kind == "crush":
            hold = int(rng.integers(6, 24))
            nz = rng.standard_normal(n // hold + 1).repeat(hold)[:n]
            seg = np.round(lp(nz, 5000, sr) * 4) / 4
        elif kind == "stutter" and prev is not None:
            piece = prev[: max(1, len(prev) // 3)]
            seg = np.tile(piece, n // len(piece) + 1)[:n]
        else:
            seg = np.zeros(n)
        seg = fade_edges(seg.astype(float) * rng.uniform(0.4, 1.0), sr, 0.001, 0.002)
        i0 = secs(sr, t)
        e = min(len(out), i0 + n)
        out[i0:e] += seg[: e - i0]
        prev = seg if kind != "gap" else prev
        t += d
    out = lp(out, 8000, sr)
    st = np.stack([out, np.roll(out, 37)], 1)
    return st


# =============================================================================
# impacts
# =============================================================================
@fx("brick_thud")
def _brick_thud(sr, rng):
    out = _canvas(sr, 1.0)
    n = secs(sr, 0.6)
    t = tvec(n, sr)
    f = 52 + 75 * np.exp(-t / 0.03)
    ph = TAU * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t / 0.16) + 0.35 * np.sin(2 * ph) * np.exp(-t / 0.07)
    nz = rng.standard_normal(n)
    imp = 0.8 * lp(nz, 900, sr) * np.exp(-t / 0.03) + 0.45 * bp(nz, 300, 2500, sr) * np.exp(-t / 0.012)
    y = np.tanh(1.5 * (body + imp) * np.clip(t / 0.0008, 0, 1))
    _place(out, fade_edges(y, sr, 0.0003, 0.05), 0.0, sr)
    for k in range(12):    # gravel / mortar debris
        tt = 0.035 + rng.gamma(1.6, 0.08)
        if tt > 0.85:
            continue
        ng = secs(sr, 0.03)
        tg = tvec(ng, sr)
        c = rng.uniform(1200, 4200)
        g = bp(rng.standard_normal(ng), c * 0.7, c * 1.4, sr) * np.exp(-tg / rng.uniform(0.003, 0.009))
        _place(out, fade_edges(g, sr, 0.0003, 0.004), tt, sr, 0.22 * math.exp(-tt * 2.5), rng.uniform(-0.6, 0.6))
    return _room(out, sr, 0.18, 0.7)


@fx("stamp")
def _stamp(sr, rng):
    n = secs(sr, 0.45)
    t = tvec(n, sr)
    f = 55 + 45 * np.exp(-t / 0.02)
    y = np.sin(TAU * np.cumsum(f) / sr) * np.exp(-t / 0.09)
    nz = rng.standard_normal(n)
    y += 0.7 * bp(nz, 500, 2600, sr) * np.exp(-t / 0.014)
    y += 0.45 * (np.sin(TAU * 380 * t) * np.exp(-t / 0.04) + 0.5 * np.sin(TAU * 1050 * t) * np.exp(-t / 0.015))
    y *= np.clip(t / 0.0006, 0, 1)
    return _room(pan(fade_edges(np.tanh(1.3 * y), sr, 0.0003, 0.03), 0), sr, 0.15, 0.5)


@fx("robot_stomp")
def _robot_stomp(sr, rng):
    out = _canvas(sr, 1.0)
    n = secs(sr, 0.09)
    t = tvec(n, sr)
    hiss = bp(rng.standard_normal(n), 2500, 6500, sr) * np.clip(t / 0.06, 0, 1) ** 2
    _place(out, fade_edges(hiss, sr, 0.002, 0.004) * 0.25, 0.0, sr, 1.0, 0.2)
    n = secs(sr, 0.8)
    t = tvec(n, sr)
    f = 42 + 60 * np.exp(-t / 0.025)
    ph = TAU * np.cumsum(f) / sr
    thump = np.sin(ph) * np.exp(-t / 0.2) + 0.4 * np.sin(2 * ph) * np.exp(-t / 0.08)
    clank = np.zeros(n)
    for k, fr in enumerate((223, 487, 811, 1290, 1834, 2650)):
        clank += np.sin(TAU * fr * rng.uniform(0.98, 1.02) * t + k) * np.exp(-t / (0.5 / (1 + 0.5 * k))) / (1 + k * 0.6)
    imp = bp(rng.standard_normal(n), 200, 3000, sr) * np.exp(-t / 0.008)
    y = np.tanh(1.4 * (thump + 0.45 * clank + 0.6 * imp) * np.clip(t / 0.0008, 0, 1))
    _place(out, fade_edges(y, sr, 0.0003, 0.05), 0.085, sr)
    n = secs(sr, 0.35)
    t = tvec(n, sr)
    whine = lp(saw(300 + 220 * t / 0.35, n, sr), 1500, sr) * env_adsr(n, sr, 0.05, 1, 1, 0.1, 0.25)
    _place(out, whine * 0.08, 0.45, sr, 1.0, -0.2)
    return _room(out, sr, 0.2, 0.9)


@fx("boom_cartoon")
def _boom_cartoon(sr, rng):
    out = _canvas(sr, 1.7)
    n = secs(sr, 1.6)
    t = tvec(n, sr)
    f = 42 + 80 * np.exp(-t / 0.06)
    body = np.sin(TAU * np.cumsum(f) / sr) * np.exp(-t / 0.35)
    nz = rng.standard_normal(n)
    fc = 180 + 2200 * np.exp(-t / 0.12)
    puff = tv_filter(nz, fc, sr, "lowpass", q=0.8, block=256) * np.exp(-t / 0.45)
    y = np.tanh(1.6 * (0.9 * body + 0.9 * puff) * np.clip(t / 0.002, 0, 1))
    _place(out, fade_edges(y, sr, 0.0005, 0.2), 0.0, sr)
    for k in range(8):
        tt = rng.uniform(0.05, 0.5)
        ng = secs(sr, 0.02)
        g = bp(rng.standard_normal(ng), 1500, 4500, sr) * np.exp(-tvec(ng, sr) / 0.004)
        _place(out, fade_edges(g, sr, 0.0003, 0.003), tt, sr, 0.12, rng.uniform(-0.7, 0.7))
    return _room(out, sr, 0.25, 1.2)


@fx("thunder", trim=-1.0)
def _thunder(sr, rng):
    n = secs(sr, 3.2)
    t = tvec(n, sr)
    out = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        crack = bp(nz, 500, 4000, sr) * np.exp(-t / 0.07) * 0.22
        for k in range(6):
            tc = rng.uniform(0.0, 0.3)
            crack += 0.15 * np.where(t >= tc, bp(nz, 800, 3500, sr) * np.exp(-np.maximum(t - tc, 0) / 0.02), 0)
        brown = np.cumsum(rng.standard_normal(n))
        brown = hp(brown, 25, sr, 2)
        rumble = lp(brown, 260, sr, 2)
        rumble /= np.abs(rumble).max() + 1e-9
        mod = 0.55 + 0.45 * smooth_noise(n, sr, 3.0, rng)
        env = np.clip(t / 0.12, 0, 1) * np.exp(-t / 1.0)
        out[:, ch] = crack * np.clip(t / 0.002, 0, 1) + rumble * mod * env * 1.6
    out = fade_edges(out, sr, 0.001, 0.4)
    return _room(out, sr, 0.3, 2.0)


@fx("heartbeat")
def _heartbeat(sr, rng):
    out = _canvas(sr, 0.8)
    for tt, f0, a in ((0.0, 52, 1.0), (0.27, 64, 0.75)):
        n = secs(sr, 0.35)
        t = tvec(n, sr)
        f = f0 * (1 + 0.4 * np.exp(-t / 0.02))
        ph = TAU * np.cumsum(f) / sr
        y = (np.sin(ph) + 0.45 * np.sin(2 * ph)) * np.exp(-t / 0.07) * np.clip(t / 0.006, 0, 1)
        y += 0.3 * lp(rng.standard_normal(n), 400, sr) * np.exp(-t / 0.02)
        _place(out, fade_edges(y, sr, 0.001, 0.03) * a, tt, sr)
    return out


# =============================================================================
# air / motion
# =============================================================================
def _sweep_noise(sr, rng, dur, f0, f1, q=1.4, shape="bell"):
    n = secs(sr, dur)
    t = tvec(n, sr)
    u = t / dur
    fc = f0 * (f1 / f0) ** u if shape != "bell" else f0 + (f1 - f0) * np.sin(np.pi * u) ** 1.5
    nz = rng.standard_normal(n)
    y = tv_filter(nz, fc, sr, "bandpass", q=q, stages=1)
    y += 0.5 * lp(nz, 350, sr)
    return y, u


@fx("whoosh")
def _whoosh(sr, rng):
    y, u = _sweep_noise(sr, rng, 0.6, 400, 1900, q=1.2)
    env = np.sin(np.pi * u) ** 2 * (0.6 + 0.4 * u)
    y = fade_edges(y * env, sr, 0.005, 0.02)
    pn = np.clip(-0.7 + 1.4 * u, -1, 1)
    th = (pn + 1) * math.pi / 4
    return np.stack([y * np.cos(th), y * np.sin(th)], 1) * math.sqrt(2)


@fx("swoosh_up")
def _swoosh_up(sr, rng):
    y, u = _sweep_noise(sr, rng, 0.6, 300, 4200, q=1.6, shape="exp")
    env = np.clip(u / 0.85, 0, 1) ** 1.6 * np.clip((1 - u) / 0.15, 0, 1)
    n = len(y)
    tone = sine(300 * 4 ** u, n, sr) * 0.15
    y = fade_edges((y + tone) * env, sr, 0.005, 0.01)
    return _room(pan(y, 0), sr, 0.15)


@fx("page_flip")
def _page_flip(sr, rng):
    out = _canvas(sr, 0.42)
    y, u = _sweep_noise(sr, rng, 0.26, 900, 3200, q=1.0, shape="exp")
    env = np.sin(np.pi * u) ** 1.5
    _place(out, fade_edges(y * env * 0.7, sr, 0.003, 0.01), 0.0, sr, 1.0, -0.2)
    n = secs(sr, 0.06)
    t = tvec(n, sr)
    flap = bp(rng.standard_normal(n), 300, 1500, sr) * np.exp(-t / 0.008) + \
        0.4 * np.sin(TAU * 180 * t) * np.exp(-t / 0.012)
    _place(out, fade_edges(flap, sr, 0.0003, 0.005), 0.25, sr, 1.0, 0.2)
    return out


@fx("paper", trim=-1.0)
def _paper(sr, rng):
    out = _canvas(sr, 1.1)
    y, u = _sweep_noise(sr, rng, 1.0, 500, 2200, q=0.8)
    _place(out, fade_edges(lp(y, 2500, sr) * np.sin(np.pi * u) ** 2 * 0.35, sr, 0.01, 0.05), 0.0, sr)
    for k in range(70):
        tt = float(np.clip(rng.normal(0.45, 0.22), 0.0, 0.95))
        ng = secs(sr, 0.03)
        c = rng.uniform(1200, 5500)
        g = bp(rng.standard_normal(ng), c / 1.5, c * 1.5, sr) * np.exp(-tvec(ng, sr) / rng.uniform(0.002, 0.008))
        _place(out, fade_edges(g, sr, 0.0003, 0.003), tt, sr, rng.uniform(0.15, 0.5), rng.uniform(-0.6, 0.6))
    return out


@fx("laser", trim=-2.0)
def _laser(sr, rng):
    n = secs(sr, 0.32)
    t = tvec(n, sr)
    f = 1800 * np.exp(-t / 0.06) + 260
    y = sine(f * (1 + 0.04 * np.sin(TAU * 55 * t)), n, sr) + 0.25 * lp(pulse(f, n, sr, 0.3), 4000, sr)
    y *= np.exp(-t / 0.12) * np.clip(t / 0.002, 0, 1)
    return _room(pan(fade_edges(y, sr, 0.0005, 0.02), 0), sr, 0.15)


# =============================================================================
# cartoon / comedic
# =============================================================================
@fx("record_scratch")
def _record_scratch(sr, rng):
    # a short "music" source, then read back with a scratching playhead
    src_n = secs(sr, 3.0)
    ts = tvec(src_n, sr)
    src = sum(saw(hz(m), src_n, sr, rng.random()) for m in (57, 61, 64, 69)) / 4
    src = lp(src, 2500, sr) + 0.3 * bp(rng.standard_normal(src_n), 300, 3000, sr)
    src *= 0.7 + 0.3 * np.sin(TAU * 2 * ts)
    dur = 0.6
    n = secs(sr, dur)
    t = tvec(n, sr)
    knots_t = [0.0, 0.07, 0.11, 0.2, 0.25, 0.33, 0.4, 0.52, 0.6]
    knots_r = [1.0, 3.0, -2.6, -2.2, 3.2, 2.0, -1.8, -0.4, 0.0]
    rate = np.interp(t, knots_t, knots_r)
    pos = 1.2 * sr + np.cumsum(rate)
    y = np.interp(pos, np.arange(src_n), src)
    y = np.tanh(2.0 * y) * np.clip(np.abs(rate) / 1.0, 0, 1) ** 0.5
    y += 0.06 * bp(rng.standard_normal(n), 1500, 6000, sr) * (np.abs(rate) > 0.3)
    y = bp(y, 150, 5500, sr)
    return pan(fade_edges(y, sr, 0.002, 0.03), 0)


@fx("buzzer_nope")
def _buzzer_nope(sr, rng):
    out = np.zeros(secs(sr, 0.52))
    for tt, f0 in ((0.0, 155.0), (0.23, 146.0)):
        n = secs(sr, 0.17)
        t = tvec(n, sr)
        src = saw(f0, n, sr) + 0.6 * pulse(f0 * 1.006, n, sr, 0.35)
        y = 0.7 * biquad(src, "bandpass", 530, sr, 4.0) + 0.45 * biquad(src, "bandpass", 1840, sr, 7.0) + \
            0.2 * lp(src, 400, sr)
        y = lp(y, 2600, sr, 2) * env_adsr(n, sr, 0.008, 1, 1, 0.025, 0.145)
        i0 = secs(sr, tt)
        out[i0:i0 + n] += y[: len(out) - i0]
    return pan(out, 0)


@fx("snake_hiss", trim=-3.0)
def _snake_hiss(sr, rng):
    out = _canvas(sr, 1.35)
    n = secs(sr, 1.25)
    t = tvec(n, sr)
    nz = rng.standard_normal(n)
    y = bp(nz, 2600, 7200, sr, 2) + 0.25 * bp(nz, 1200, 2600, sr)
    y = lp(y, 8000, sr)
    env = np.clip(t / 0.18, 0, 1) ** 1.5 * (1 + 0.22 * smooth_noise(n, sr, 7, rng)) * \
        np.clip((1.25 - t) / 0.35, 0, 1)
    _place(out, fade_edges(y * env * 0.7, sr, 0.01, 0.05), 0.1, sr)
    for tt in (0.0, 0.035, 0.95, 0.985):     # tongue flicks "tk-tk"
        ng = secs(sr, 0.02)
        tg = tvec(ng, sr)
        tick = np.sin(TAU * 3100 * tg) * np.exp(-tg / 0.003) + 0.6 * bp(rng.standard_normal(ng), 2000, 5000, sr) * \
            np.exp(-tg / 0.0015)
        _place(out, fade_edges(tick, sr, 0.0002, 0.003), tt, sr, 0.5, 0.15)
    return out


@fx("boing")
def _boing(sr, rng):
    n = secs(sr, 0.95)
    t = tvec(n, sr)
    f = 150 * (1 + 0.1 * t) * (1 + 0.55 * np.exp(-t / 0.22) * np.sin(TAU * 12 * t))
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)
    y *= np.exp(-t / 0.33) * np.clip(t / 0.004, 0, 1)
    y += 0.3 * bp(rng.standard_normal(n), 300, 2000, sr) * np.exp(-t / 0.006)
    return _room(pan(fade_edges(y, sr, 0.0005, 0.05), 0), sr, 0.12)


@fx("sad_trombone", trim=-3.0)
def _sad_trombone(sr, rng):
    notes = [(0.0, 62, 0.42), (0.46, 61, 0.42), (0.92, 60, 0.42), (1.38, 59, 1.35)]
    total = 2.95
    n = secs(sr, total)
    t = tvec(n, sr)
    pitch = np.interp(t, sum([[s, s + 0.03] for s, _, _ in notes], []),
                      sum([[notes[max(0, i - 1)][1], m] for i, (_, m, _) in enumerate(notes)], []))
    amp = np.zeros(n)
    wah = np.full(n, 350.0)
    for i, (s, m, d) in enumerate(notes):
        tt = t - s
        a = np.clip(tt / 0.05, 0, 1) * np.where(tt > d, np.exp(-(tt - d) / 0.06), 1.0)
        a *= tt >= 0
        amp = np.maximum(amp, a * (1.0 if i < 3 else 1.05))
        w = 350 + 1300 * np.clip(tt / 0.16, 0, 1) ** 1.2 * np.exp(-np.maximum(tt - 0.16, 0) / 0.5)
        wah = np.where((tt >= 0) & (tt < d + 0.1), w, wah)
    last = notes[-1][0]
    lt = np.maximum(t - last - 0.25, 0)
    vib = 0.035 * np.clip(lt / 0.3, 0, 1) * np.sin(TAU * 5.2 * lt)
    droop = -0.5 * np.clip((t - last - 0.6) / 0.7, 0, 1)
    f = hz(0) * 2 ** ((pitch + droop) / 12) * (1 + vib)
    src = saw(f, n, sr) + 0.7 * saw(f * 1.004, n, sr, 0.3)
    y = tv_filter(src, wah, sr, "lowpass", q=2.2, block=128)
    y = biquad(y, "peak", 1100, sr, 1.2, 3.0)
    y = np.tanh(1.6 * y * lp(amp, 40, sr, 1))
    return _room(pan(fade_edges(y, sr, 0.002, 0.08), 0), sr, 0.2, 1.0)


@fx("dun_dun_dun")
def _dun_dun_dun(sr, rng):
    hits = [(0.0, [36, 43, 48, 51, 55], 0.22), (0.34, [36, 44, 48, 53, 56], 0.22),
            (0.68, [36, 42, 48, 51, 54], 1.6)]
    out = _canvas(sr, 3.6)
    lo = sr // 2
    for i, (tt, ch, d) in enumerate(hits):
        b = inst_brass(ch, d, lo, rng, peak_fc=2600, base_fc=500, attack=0.015, release=0.5 if i < 2 else 1.2)
        _place(out, up2(b), tt, sr, 0.9)
        s = inst_strings_sect([m + 12 for m in ch[1:]], d, lo, rng, cutoff=3200, attack=0.02,
                              release=0.4 if i < 2 else 1.0)
        _place(out, up2(s), tt, sr, 0.45)
        _place(out, dr_timpani(sr, rng, 36 + (0 if i < 2 else -0), 1.0, 2.2 if i == 2 else 0.9), tt, sr, 0.7)
    return _room(out, sr, 0.35, 2.2, 0.02)


@fx("ta_da")
def _ta_da(sr, rng):
    out = _canvas(sr, 2.0)
    lo = sr // 2
    for tt, ch, d in ((0.0, [60, 64, 67, 72], 0.1), (0.15, [55, 60, 64, 67, 72, 76], 0.95)):
        b = inst_brass(ch, d, lo, rng, peak_fc=3800, base_fc=900, attack=0.012, release=0.5)
        _place(out, up2(b), tt, sr, 1.0)
    for i, m in enumerate((84, 88, 91, 96)):
        _place(out, inst_bell(m, 1.0, 0.5, sr), 0.16 + 0.04 * i, sr, 0.18, -0.4 + 0.27 * i)
    return _room(out, sr, 0.25, 1.4)


@fx("sparkle", trim=-1.0)
def _sparkle(sr, rng):
    out = _canvas(sr, 1.3)
    scale = [84, 86, 88, 91, 93, 96, 98, 100]
    for k in range(10):
        tt = float(np.sort(rng.uniform(0, 0.55, 10))[k])
        m = int(rng.choice(scale))
        _place(out, _cut(inst_bell(m, 0.5, rng.uniform(0.5, 1.0), sr), sr, min(0.9, 1.28 - tt)), tt, sr, 0.3,
               rng.uniform(-0.7, 0.7))
    return _room(out, sr, 0.3, 1.2)


@fx("magic_chime")
def _magic_chime(sr, rng):
    out = _canvas(sr, 1.8)
    for i, m in enumerate((72, 76, 79, 81, 84, 88, 91)):
        _place(out, _cut(inst_bell(m, 1.0, 0.6 + 0.05 * i, sr), sr, 1.75 - 0.065 * i, 0.3), 0.065 * i, sr, 0.35,
               -0.5 + i / 6)
    sh = _sweep_noise(sr, rng, 1.0, 3000, 7000, q=2.0, shape="exp")[0]
    sh = fade_edges(sh * np.linspace(0, 1, len(sh)) ** 2 * np.linspace(1, 0, len(sh)) ** 0.5, sr)
    _place(out, sh * 0.04, 0.1, sr)
    return _room(out, sr, 0.35, 1.6)


@fx("idea_ding", trim=-2.0)
def _idea_ding(sr, rng):
    out = _canvas(sr, 1.6)
    _place(out, inst_bell(88, 1.4, 1.0, sr), 0.0, sr, 0.6)
    _place(out, inst_bell(76, 1.4, 0.6, sr, kind="fm"), 0.0, sr, 0.35)
    _place(out, inst_bell(95, 1.0, 0.4, sr), 0.05, sr, 0.15, 0.3)
    return _room(out, sr, 0.25, 1.3)


@fx("gulp")
def _gulp(sr, rng):
    out = np.zeros(secs(sr, 0.5))
    n = secs(sr, 0.12)
    t = tvec(n, sr)
    f = 450 - 260 * np.clip(t / 0.06, 0, 1)
    y = np.sin(TAU * np.cumsum(f) / sr) * np.exp(-t / 0.035) * np.clip(t / 0.002, 0, 1)
    y += 0.3 * bp(rng.standard_normal(n), 1000, 3000, sr) * np.exp(-t / 0.003)
    out[:n] += fade_edges(y, sr, 0.0005, 0.01) * 0.7
    n = secs(sr, 0.25)
    t = tvec(n, sr)
    f = np.interp(t, [0, 0.04, 0.13], [200, 540, 230])
    y = np.sin(TAU * np.cumsum(f) / sr) * np.exp(-t / 0.07)
    y += 0.4 * np.sin(TAU * 95 * t) * np.exp(-t / 0.05)
    i0 = secs(sr, 0.13)
    out[i0:i0 + n] += fade_edges(y, sr, 0.005, 0.02)[: len(out) - i0]
    return pan(out, 0)


def _crowd(sr, rng, dur, voices, make_voice, vowels):
    """Sum per-voice glottal sources, then shape with formants per vowel group."""
    n = secs(sr, dur)
    groups = [np.zeros((n, 2)) for _ in vowels]
    for k in range(voices):
        src = make_voice(k, n)
        groups[k % len(vowels)] += pan(src, rng.uniform(-0.8, 0.8))
    out = np.zeros((n, 2))
    for g, formants in zip(groups, vowels):
        y = 0.05 * lp(g, 500, sr)
        for fc, q, a in formants:
            if callable(fc):
                y += a * tv_filter(g, fc(n), sr, "bandpass", q=q, stages=1)
            else:
                y += a * biquad(g, "bandpass", fc, sr, q)
        out += y
    return out


@fx("crowd_aww", trim=-3.0)
def _crowd_aww(sr, rng):
    dur = 2.0
    t_all = tvec(secs(sr, dur), sr)

    def voice(k, n):
        t = t_all[:n]
        f0 = rng.choice([rng.uniform(110, 160), rng.uniform(190, 290)])
        on = rng.uniform(0.0, 0.18)
        tt = np.maximum(t - on, 0)
        contour = 1.10 - 0.25 * np.clip(tt / 1.3, 0, 1) ** 0.8
        f = f0 * contour * (1 + 0.006 * np.sin(TAU * rng.uniform(4.5, 6) * t + k)) * \
            (1 + 0.004 * smooth_noise(n, sr, 4, rng))
        src = saw(f, n, sr, rng.random()) + 0.15 * rng.standard_normal(n)
        env = np.clip(tt / 0.22, 0, 1) * np.exp(-np.maximum(tt - 0.5, 0) / 0.55) * (t >= on)
        return src * env * rng.uniform(0.6, 1.0)

    f1 = lambda n: 760 - 200 * np.clip(t_all[:n] / 1.2, 0, 1)    # "a" -> "aw/o"  # noqa: E731
    f2 = lambda n: 1250 - 380 * np.clip(t_all[:n] / 1.2, 0, 1)   # noqa: E731
    out = _crowd(sr, rng, dur, 22, voice, [[(f1, 5.0, 1.0), (f2, 7.0, 0.5), (2500, 9.0, 0.12)]])
    out = lp(out, 4500, sr)
    return _room(fade_edges(out, sr, 0.01, 0.2), sr, 0.3, 1.2)


@fx("crowd_laugh", trim=-4.0)
def _crowd_laugh(sr, rng):
    dur = 2.4
    t_all = tvec(secs(sr, dur), sr)

    def voice(k, n):
        t = t_all[:n]
        f0 = rng.choice([rng.uniform(105, 150), rng.uniform(180, 270)])
        rate = rng.uniform(4.2, 6.2)
        on = rng.uniform(0.0, 0.35)
        nsyl = int(rng.integers(5, 10))
        src = np.zeros(n)
        voiced_env = np.zeros(n)
        breath_env = np.zeros(n)
        pitch = np.full(n, f0)
        for s in range(nsyl):
            ts = on + s / rate + rng.normal(0, 0.012)
            amp = (0.95 ** s) * (1.0 if s > 0 else 0.8) * rng.uniform(0.7, 1.0)
            tt = t - ts
            breath_env += amp * 0.6 * np.exp(-((tt - 0.012) / 0.012) ** 2)
            v = np.clip((tt - 0.02) / 0.015, 0, 1) * np.exp(-np.maximum(tt - 0.035, 0) / 0.045) * (tt > 0.02)
            voiced_env += amp * v * (tt < 0.25)
            pitch = np.where((tt >= 0) & (tt < 1 / rate), f0 * (1.15 - 0.04 * s) * (1 - 0.12 * np.clip(tt * rate, 0, 1)),
                             pitch)
        src = saw(pitch, n, sr, rng.random()) * voiced_env + 0.5 * rng.standard_normal(n) * breath_env
        return src * rng.uniform(0.5, 1.0)

    vowels = [[(780, 5.0, 1.0), (1250, 7.0, 0.5), (2500, 9.0, 0.12)],     # "ha"
              [(550, 5.0, 1.0), (1750, 8.0, 0.45), (2500, 9.0, 0.12)],    # "heh"
              [(400, 5.0, 1.0), (2000, 8.0, 0.35), (2700, 9.0, 0.1)]]     # "hih"
    out = _crowd(sr, rng, dur, 16, voice, vowels)
    out = lp(out, 5000, sr)
    t = t_all
    out *= (np.clip(t / 0.15, 0, 1) * np.exp(-np.maximum(t - 0.9, 0) / 0.8))[:, None]
    return _room(fade_edges(out, sr, 0.01, 0.2), sr, 0.35, 1.0)


# =============================================================================
# a few handy extras
# =============================================================================
@fx("drumroll")
def _drumroll(sr, rng):
    out = _canvas(sr, 2.0)
    t = 0.0
    while t < 1.35:
        _place(out, dr_snare(sr, rng, 0.25 + 0.6 * t / 1.35, soft=0.6), t, sr, 0.5, rng.uniform(-0.1, 0.1))
        t += 0.042 + 0.006 * rng.random()
    _place(out, dr_snare(sr, rng, 1.0), 1.4, sr, 0.9)
    _place(out, dr_kick(sr, rng, 1.0), 1.4, sr, 0.9)
    return _room(out, sr, 0.2, 1.0)


@fx("tiptoe")
def _tiptoe(sr, rng):
    out = _canvas(sr, 1.6)
    for i, m in enumerate((64, 67, 64, 69)):
        _place(out, inst_pluck(m, 0.08, sr, 0.8, 0.5, 0.8, 0.05, i), i * 0.33, sr, 0.6, -0.3 + 0.2 * i)
    return out


@fx("tick")
def _tick(sr, rng):
    return pan(dr_wood(sr, rng, 1.0, 1900), 0.2)


@fx("riser")
def _riser(sr, rng):
    y = dr_swell(sr, rng, 1.8, 1500, 8000)
    n = len(y)
    t = tvec(n, sr)
    y = y + 0.3 * sine(200 * 4 ** (t / 1.8), n, sr) * (t / 1.8) ** 2
    return pan(y, 0)


NAMES = sorted(_FX)
ALIASES = {
    "thud": "brick_thud", "brick": "brick_thud", "bricks": "brick_thud", "click": "puzzle_click",
    "ding": "receive", "message": "receive", "beep": "scan_beep", "scan": "scan_beep",
    "boom": "boom_cartoon", "explosion": "boom_cartoon", "hiss": "snake_hiss",
    "scratch": "record_scratch", "chime": "magic_chime", "laugh": "crowd_laugh",
    "aww": "crowd_aww", "type": "typing", "keyboard": "typing", "key": "key_clack",
    "clack": "key_clack", "nope": "buzzer_nope", "buzzer": "buzzer_nope", "wrong": "buzzer_nope",
    "fanfare": "ta_da", "tada": "ta_da", "sting": "dun_dun_dun", "dramatic": "dun_dun_dun",
    "trombone": "sad_trombone", "womp": "sad_trombone", "idea": "idea_ding", "lightbulb": "idea_ding",
    "magic": "magic_chime", "shimmer": "sparkle", "swoosh": "whoosh", "swish": "whoosh",
    "swoosh_down": "whoosh", "rise": "swoosh_up", "page": "page_flip", "flip": "page_flip",
    "scroll": "paper", "unroll": "paper", "stomp": "robot_stomp", "puzzle": "puzzle_click",
    "shutdown": "power_down", "zap": "laser", "pew": "laser", "lightning": "thunder",
    "heart": "heartbeat", "glitch_short": "glitch", "message_send": "send", "send_message": "send",
}


def resolve(name):
    """Canonical effect name for `name` (aliases, 'sfx_' prefix, trailing
    variant digits like 'pop2' are accepted) or None."""
    import re
    n = (name or "").strip().lower().replace("-", "_").replace(" ", "_")
    for cand in (n, re.sub(r"^sfx_", "", n), re.sub(r"_?\d+$", "", re.sub(r"^sfx_", "", n))):
        if cand in _FX:
            return cand
        if cand in ALIASES:
            return ALIASES[cand]
    return None


@lru_cache(maxsize=256)
def _render_cached(name, sr, seed):
    fn, trim = _FX[name]
    y = stereoize(np.asarray(fn(sr, _rng(name, seed)), dtype=float))
    y = y - y.mean(axis=0, keepdims=True)
    y = hp(y, 25, sr, 2)
    y = fade_edges(y, sr, 0.001, 0.01)
    pk = np.abs(y).max()
    if pk > 0:
        y *= 10 ** ((PEAK_DB + trim) / 20) / pk
    y = y.astype(np.float32)
    y.flags.writeable = False
    return y


def render(name, sr=48000, seed=0):
    """Render effect `name` (or an alias). Raises KeyError for unknown names."""
    key = resolve(name)
    if key is None:
        raise KeyError(f"unknown sfx '{name}'")
    return np.array(_render_cached(key, int(sr), int(seed)))


if __name__ == "__main__":
    import soundfile as sf
    for nm in sys.argv[1:] or NAMES:
        y = render(nm)
        sf.write(f"/tmp/sfx_{nm}.wav", y, 48000)
        print(nm, len(y) / 48000)
