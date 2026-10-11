"""Procedural sound-effects library (TIREDNESS; core inherited from the previous film).

    render(name, sr=48000, seed=0) -> float32 (n, 2), peak about -12 dBFS (+ trim)
    NAMES    – every available effect
    ALIASES  – forgiving alternative names ("thud" -> brick_thud, "bite" -> chomp, ...)
    LOOPS    – {name: period_s} for loopable beds (pod_hum, alarm, dog_pant, ...)
    loop_events(name, t0, t1, gain_db=0, pan=0) -> SFX() entries tiling [t0, t1)

`seed` gives small natural variations (useful for repeated clacks/pops/steps).
Loopable effects ignore the seed (identical content tiles seamlessly): each
clip is one period plus a LOOP_XF raised-cosine head/tail, so clips placed
every `period` seconds crossfade with unity gain and no seam.
All synthesis is numpy/scipy; nothing is sampled from disk. See API_audio.md.
"""
import math
import os
import sys
from functools import lru_cache

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio.music import (TAU, bp, biquad, dr_boom, dr_crash, dr_kick, dr_snare, dr_swell,  # noqa: E402
                         dr_timpani, dr_wood, env_adsr, fade_edges, hp, hz, inst_bell, inst_brass,
                         inst_pluck, inst_strings_sect, lp, pan, perc_env, pulse, reverb, saw,
                         secs, seeded, sine, smooth_noise, stereoize, tv_filter, tvec, up2)

PEAK_DB = -12.0
LOOP_XF = 0.08          # seconds of raised-cosine overlap on loopable clips
_FX = {}
LOOPS = {}


def fx(name, trim=0.0, loop=None):
    """Register an effect. trim (dB) balances perceived loudness after peak-norm.
    loop=P: the function returns exactly one period (P s) of periodic content."""
    def deco(fn):
        _FX[name] = (fn, trim)
        if loop:
            LOOPS[name] = float(loop)
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


def _neighbor_trumpet(sr, seed_rng):
    """Honky, slightly off-key amateur trumpet riff (the noisy neighbor)."""
    notes = [(0.0, 67, 0.16), (0.2, 67, 0.16), (0.4, 72, 0.32), (0.78, 71, 0.14),
             (0.96, 69, 0.14), (1.14, 70.6, 0.55)]   # last note sour on purpose
    total = 1.95
    n = secs(sr, total)
    t = tvec(n, sr)
    pitch = np.full(n, float(notes[0][1]))
    amp = np.zeros(n)
    for s, m, d in notes:
        tt = t - s
        on = (tt >= 0) & (tt < d + 0.08)
        pitch = np.where(tt >= 0, m - 0.35 * np.exp(-np.maximum(tt, 0) / 0.03), pitch)
        a = np.clip(tt / 0.02, 0, 1) * np.where(tt > d, np.exp(-(tt - d) / 0.04), 1.0)
        amp = np.maximum(amp, np.where(on, a, 0))
    vib = 0.02 * np.sin(TAU * 6.0 * t) * np.clip((t - 1.3) / 0.2, 0, 1)
    f = hz(0) * 2 ** (pitch / 12) * (1 + vib)
    src = saw(f, n, sr) + 0.5 * saw(f * 1.006, n, sr, 0.2)
    y = tv_filter(src, 900 + 2600 * lp(amp, 30, sr, 1), sr, "lowpass", q=1.6, block=128)
    y = biquad(y, "peak", 1500, sr, 1.0, 5.0)
    y = np.tanh(2.2 * y * lp(amp, 50, sr, 1))
    return fade_edges(y, sr, 0.002, 0.06)


@fx("trumpet")
def _trumpet(sr, rng):
    return _room(pan(_neighbor_trumpet(sr, rng), 0.25), sr, 0.25, 0.9)


@fx("trumpet_muffled", trim=-9.0)
def _trumpet_muffled(sr, rng):
    """The same riff heard through noise-cancelling headphones: dull + far."""
    y = lp(_neighbor_trumpet(sr, rng), 380, sr, 2)
    y = lp(y, 520, sr, 2)
    return _room(pan(y, 0.25), sr, 0.35, 0.6)


@fx("whistle")
def _whistle(sr, rng):
    """Innocent 'who, me?' whistle: pure gliding tone + a breath of air.

    A real whistle is almost a sine (fundamental ~1-2.4 kHz) with smooth
    portamento between notes, light vibrato and a little breath noise.
    """
    # (start, midi, dur): slide up, then a sing-song little tune
    notes = [(0.00, 81, 0.20), (0.22, 86, 0.28), (0.56, 84, 0.16), (0.76, 83, 0.16),
             (0.96, 81, 0.16), (1.16, 83, 0.46)]
    total = 1.85
    n = secs(sr, total)
    t = tvec(n, sr)
    # pitch track with ~60 ms glides between targets (the whistler's slide)
    knots_t, knots_m = [0.0], [notes[0][1] - 3]
    for s, m, d in notes:
        knots_t += [s + 0.06, s + d]
        knots_m += [m, m]
    midi = np.interp(t, knots_t, knots_m)
    vib = 0.18 * np.sin(TAU * 5.6 * t) * np.clip((t - 0.3) / 0.4, 0, 1)
    f = hz(0) * 2 ** ((midi + vib) / 12)
    phase = TAU * np.cumsum(f) / sr
    tone = np.sin(phase) + 0.06 * np.sin(2 * phase)
    amp = np.zeros(n)
    for s, m, d in notes:
        tt = t - s
        a = np.clip(tt / 0.025, 0, 1) * np.clip((s + d + 0.03 - t) / 0.04, 0, 1)
        amp = np.maximum(amp, np.where(tt >= 0, a, 0))
    amp = lp(amp, 35, sr, 1)
    breath = bp(rng.standard_normal(n), 1500, 3200, sr) * 0.05
    y = (tone + breath) * amp
    return _room(pan(fade_edges(y, sr, 0.005, 0.05), 0.1), sr, 0.18, 0.7)


# =============================================================================
# TIREDNESS: helpers
# =============================================================================
def _modes(t, modes, ph0=0.0):
    """Sum of decaying sines [(f, amp, decay_s)] (struck wood/metal/ceramic)."""
    y = np.zeros_like(t)
    for k, (f, a, d) in enumerate(modes):
        if f < 23000:
            y += a * np.sin(TAU * f * t + 1.3 * k + ph0) * np.exp(-t / d)
    return y


def _sweep(f, sr, ph0=0.0):
    """Sine following a per-sample frequency curve."""
    return np.sin(TAU * np.cumsum(f) / sr + ph0)


def _thump(sr, dur, f_end, f_start, sweep, decay, harm=0.3):
    n = secs(sr, dur)
    t = tvec(n, sr)
    ph = TAU * np.cumsum(f_end + (f_start - f_end) * np.exp(-t / sweep)) / sr
    return (np.sin(ph) + harm * np.sin(2 * ph)) * np.exp(-t / decay) * np.clip(t / 0.001, 0, 1)


def _tick(sr, rng, lo=1500.0, hi=6000.0, d=0.003, dur=0.025):
    """Tiny noise click (claws, debris, crackle)."""
    n = secs(sr, dur)
    t = tvec(n, sr)
    y = bp(rng.standard_normal(n), lo, hi, sr) * np.exp(-t / d) * np.clip(t / 0.0002, 0, 1)
    return fade_edges(y, sr, 0.0001, 0.003)


def _ping(sr, rng, f, d):
    """Glassy/ceramic shard: two inharmonic partials + a tick."""
    n = secs(sr, min(0.6, d * 6 + 0.012))
    t = tvec(n, sr)
    r2 = rng.uniform(1.9, 2.7)
    y = np.sin(TAU * f * t + rng.uniform(0, TAU)) * np.exp(-t / d)
    if f * r2 < 20000:
        y += 0.45 * np.sin(TAU * f * r2 * t) * np.exp(-t / (0.5 * d))
    y += 0.35 * bp(rng.standard_normal(n), min(f * 0.8, 9000), min(f * 2.5, 20000), sr) * np.exp(-t / 0.0008)
    return fade_edges(y * np.clip(t / 0.0003, 0, 1), sr, 0.0002, 0.003)


def _glottal(f0, n, sr, rng, jitter=0.01, tilt=1500.0, rough=0.0, rough_rate=28.0):
    """Voiced source (saw with spectral tilt), pitch jitter, optional roughness."""
    f = np.broadcast_to(np.asarray(f0, dtype=float), (n,)) * (1 + jitter * smooth_noise(n, sr, 25, rng))
    src = lp(saw(f, n, sr, rng.random()), tilt, sr, 1)
    if rough:
        src = src * (1 + rough * smooth_noise(n, sr, rough_rate, rng))
    return src


def _formants(src, sr, F, block=128):
    """Formant bank: [(fc scalar or per-sample array, q, gain)] of 0 dB bandpasses."""
    y = np.zeros_like(src)
    for fc, q, g in F:
        if np.ndim(fc) == 0:
            y += g * biquad(src, "bandpass", fc, sr, q)
        else:
            y += g * tv_filter(src, fc, sr, "bandpass", q=q, block=block, stages=1)
    return y


def _norm(x):
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-12)


def _stickslip(sr, rng, dur, rate, amp, jitter=0.12):
    """Friction impulse train: rate (Hz) and amp per-sample curves -> impulses
    (feed through _resonate for creaks, scrapes, drawer slides)."""
    n = secs(sr, dur)
    x = np.zeros(n)
    rate = np.broadcast_to(np.asarray(rate, dtype=float), (n,))
    amp = np.broadcast_to(np.asarray(amp, dtype=float), (n,))
    t = 0.0
    while True:
        i = int(t * sr)
        if i >= n:
            break
        r = max(float(rate[i]), 5.0)
        x[i] += amp[i] * rng.uniform(0.5, 1.0) * (1.0 if rng.random() > 0.2 else -0.6)
        t += max(1.0 / sr, (1.0 / r) * (1 + jitter * rng.normal()))
    return x


def _resonate(x, sr, modes):
    """Impulses through resonant bandpasses [(f, q, gain)]."""
    y = np.zeros_like(x)
    for f, q, g in modes:
        y += g * biquad(x, "bandpass", f, sr, q)
    return y


def _pnoise(n, sr, rng, lo=20.0, hi=None, tilt_db_oct=0.0):
    """Exactly periodic (period n samples) band-limited noise, unit RMS."""
    F = np.fft.rfftfreq(n, 1.0 / sr)
    mag = ((F >= lo) & (F <= (hi or sr / 2))).astype(float)
    if tilt_db_oct:
        mag = mag * (np.maximum(F, 1.0) / 1000.0) ** (tilt_db_oct / 6.02)
    y = np.fft.irfft(mag * np.exp(1j * rng.uniform(0, TAU, len(F))), n)
    return y / (np.std(y) + 1e-12)


def _step(sr, rng, vel=1.0, toe=0.07, hard=1.0):
    """One shoe step on a wooden/hard floor: heel thump + board modes, then a scuffy toe."""
    n = secs(sr, 0.3)
    t = tvec(n, sr)
    k = rng.uniform(0.9, 1.1)
    y = 0.7 * _sweep((118 + 80 * np.exp(-t / 0.01)) * k, sr) * np.exp(-t / 0.025)
    y += _modes(t, [(235 * k, 0.6, 0.025), (470 * k, 0.5, 0.015), (910 * k, 0.3 * hard, 0.008)], rng.uniform(0, TAU))
    y += 0.45 * hard * bp(rng.standard_normal(n), 800, 4000, sr) * np.exp(-t / 0.004)
    y *= np.clip(t / 0.001, 0, 1)
    tt = np.maximum(t - toe, 0)
    toe_s = (0.35 * bp(rng.standard_normal(n), 900, 4500, sr) * np.exp(-tt / 0.008) +
             0.25 * _modes(tt, [(310 * k, 0.6, 0.015), (690 * k, 0.4, 0.008)])) * (t >= toe) * np.clip(tt / 0.001, 0, 1)
    return fade_edges((y + toe_s * rng.uniform(0.6, 1.0)) * vel, sr, 0.0003, 0.03)


def _chip(f0, d, sr, duty=0.25, f1=None, decay=None):
    """8-bit square voice: optional exponential sweep f0 -> f1, optional decay."""
    n = secs(sr, d)
    t = tvec(n, sr)
    f = f0 if f1 is None else f0 * (f1 / f0) ** (t / d)
    y = pulse(f, n, sr, duty)
    env = np.clip(t / 0.002, 0, 1) * np.clip((d - t) / 0.008, 0, 1)
    if decay:
        env = env * np.exp(-t / decay)
    return y * env


# =============================================================================
# TIREDNESS: doors, knocks, impacts
# =============================================================================
@fx("door_bang")
def _door_bang(sr, rng):
    """Fist pounding a wooden front door (one hit; seeds vary weight/pitch/rattle)."""
    out = _canvas(sr, 0.8)
    n = secs(sr, 0.6)
    t = tvec(n, sr)
    k = rng.uniform(0.93, 1.07)
    body = _sweep((104 + 70 * np.exp(-t / 0.012)) * k, sr) * np.exp(-t / 0.06)
    panel = _modes(t, [(176 * k, 0.8, 0.05), (303 * k, 0.75, 0.038), (512 * k, 0.6, 0.026),
                       (858 * k, 0.35, 0.016), (1390 * k, 0.15, 0.01)], rng.uniform(0, TAU))
    imp = lp(rng.standard_normal(n), 1800, sr, 2) * np.exp(-t / 0.006)
    y = np.tanh(1.4 * (0.7 * body + 1.2 * panel + 0.8 * imp) * np.clip(t / 0.0015, 0, 1))
    _place(out, fade_edges(y, sr, 0.0003, 0.05), 0.0, sr)
    for j in range(int(rng.integers(2, 5))):        # door shaking in its frame / latch
        tt = 0.012 + 0.017 * j + rng.uniform(0, 0.012)
        _place(out, _tick(sr, rng, 900, 3400, 0.004, 0.03), tt, sr, 0.12 * 0.75 ** j, rng.uniform(-0.2, 0.2))
    return _room(out, sr, 0.22, 0.55, 0.006, 0.55)


@fx("knock", trim=-2.0)
def _knock(sr, rng):
    """Light knuckle knock, two raps."""
    out = _canvas(sr, 0.6)
    for i, tt in enumerate((0.0, 0.17 + rng.uniform(-0.012, 0.012))):
        n = secs(sr, 0.2)
        t = tvec(n, sr)
        k = rng.uniform(0.96, 1.04)
        y = _modes(t, [(415 * k, 0.6, 0.03), (760 * k, 0.5, 0.02), (1320 * k, 0.32, 0.012), (2150 * k, 0.15, 0.007)])
        y += 0.5 * np.sin(TAU * 150 * t) * np.exp(-t / 0.025)
        y += 0.45 * bp(rng.standard_normal(n), 1800, 6000, sr) * np.exp(-t / 0.0012)
        _place(out, fade_edges(y * np.clip(t / 0.0006, 0, 1), sr, 0.0002, 0.02), tt, sr, 1.0 if i == 0 else 0.82)
    return _room(out, sr, 0.18, 0.45, 0.005, 0.5)


@fx("body_thud")
def _body_thud(sr, rng):
    """Heavy body hitting the floor or a wall: soft attack, big low thump, cloth, rattle."""
    out = _canvas(sr, 0.95)
    n = secs(sr, 0.7)
    t = tvec(n, sr)
    k = rng.uniform(0.92, 1.08)
    f = (78 + 80 * np.exp(-t / 0.02)) * k
    ph = TAU * np.cumsum(f) / sr
    body = np.sin(ph) * np.exp(-t / 0.09) + 0.6 * np.sin(2 * ph) * np.exp(-t / 0.05)
    flesh = _norm(bp(rng.standard_normal(n), 150, 1100, sr, 2)) * 0.35 * np.exp(-t / 0.035)
    floor = _modes(t, [(140 * k, 0.6, 0.06), (232 * k, 0.6, 0.04), (410 * k, 0.45, 0.025), (690 * k, 0.25, 0.015)],
                   rng.uniform(0, TAU))
    cloth = bp(rng.standard_normal(n), 900, 3500, sr) * np.exp(-t / 0.02) * 0.3
    y = np.tanh(1.5 * (0.6 * body + flesh + floor + cloth) * np.clip(t / 0.003, 0, 1))
    _place(out, fade_edges(y, sr, 0.001, 0.06), 0.0, sr)
    for j in range(5):                                # boards / things on shelves
        tt = 0.02 + rng.gamma(1.5, 0.05)
        _place(out, _tick(sr, rng, 600, 2500, 0.005, 0.03), tt, sr, 0.08, rng.uniform(-0.5, 0.5))
    return _room(out, sr, 0.2, 0.6)


@fx("ceiling_thud")
def _ceiling_thud(sr, rng):
    """Head bonking the ceiling: hollow drywall knock + plaster tick and flakes."""
    out = _canvas(sr, 0.95)
    n = secs(sr, 0.5)
    t = tvec(n, sr)
    k = rng.uniform(0.95, 1.05)
    hollow = _modes(t, [(205 * k, 1.0, 0.07), (330 * k * rng.uniform(0.97, 1.03), 0.7, 0.05),
                        (520 * k * rng.uniform(0.96, 1.04), 0.45, 0.035), (790 * k, 0.25, 0.02)], rng.uniform(0, TAU))
    thump = _sweep((85 + 60 * np.exp(-t / 0.01)) * rng.uniform(0.9, 1.1), sr) * np.exp(-t / 0.05)
    imp = bp(rng.standard_normal(n), 300, 2500, sr) * np.exp(-t / 0.004)
    y = np.tanh(1.3 * (hollow + 0.6 * thump + 0.6 * imp) * np.clip(t / 0.0012, 0, 1))
    _place(out, fade_edges(y, sr, 0.0005, 0.05), 0.0, sr)
    _place(out, _tick(sr, rng, 2500, 7000, 0.002, 0.02), 0.004, sr, 0.25, 0.1)
    for j in range(int(rng.integers(5, 9))):
        tt = 0.08 + rng.gamma(1.6, 0.09)
        if tt < 0.85:
            _place(out, _tick(sr, rng, 2000, 6000, rng.uniform(0.001, 0.003), 0.015), tt, sr,
                   0.06 * rng.uniform(0.4, 1.0), rng.uniform(-0.6, 0.6))
    return _room(out, sr, 0.2, 0.5)


@fx("bonk")
def _bonk(sr, rng):
    """Cartoon head bonk: hollow 'tonk' with a quick pitch drop and wobble."""
    n = secs(sr, 0.5)
    t = tvec(n, sr)
    f0 = 560 * rng.uniform(0.94, 1.06)
    f = f0 * (0.82 + 0.18 * np.exp(-t / 0.03)) * (1 + 0.03 * np.exp(-t / 0.15) * np.sin(TAU * 14 * t))
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) * np.exp(-t / 0.11) + 0.45 * np.sin(1.48 * ph + 0.5) * np.exp(-t / 0.05) \
        + 0.2 * np.sin(2.9 * ph) * np.exp(-t / 0.02)
    y += 0.5 * bp(rng.standard_normal(n), 800, 4000, sr) * np.exp(-t / 0.0015)
    y += 0.4 * _sweep(140 + 80 * np.exp(-t / 0.01), sr) * np.exp(-t / 0.03)
    return _room(pan(fade_edges(y * np.clip(t / 0.0008, 0, 1), sr, 0.0003, 0.04), 0), sr, 0.12, 0.4)


@fx("impact_heavy")
def _impact_heavy(sr, rng):
    """Huge ground impact: sub boom, crunch, debris, short rumble — then it stops."""
    out = _canvas(sr, 1.3)
    n = secs(sr, 1.2)
    t = tvec(n, sr)
    k = rng.uniform(0.9, 1.1)
    ph = TAU * np.cumsum((40 + 95 * np.exp(-t / 0.04)) * k) / sr + rng.uniform(0, TAU)
    boom = np.sin(ph) * np.exp(-t / 0.25) + 0.7 * np.sin(2 * ph) * np.exp(-t / 0.12)
    crunch = _norm(bp(rng.standard_normal(n), 200, 4500, sr, 2)) * 0.3 * (np.exp(-t / 0.03) + 0.3 * np.exp(-t / 0.15))
    thud = _modes(t, [(160 * k, 0.8, 0.07), (290 * k, 0.7, 0.05), (520 * k, 0.5, 0.03), (870 * k, 0.3, 0.02)],
                  rng.uniform(0, TAU))
    y = np.tanh(2.2 * (0.5 * boom + 1.5 * crunch + 1.5 * thud) * np.clip(t / 0.001, 0, 1))
    _place(out, fade_edges(y, sr, 0.0003, 0.3), 0.0, sr)
    for j in range(36):
        tt = 0.02 + rng.gamma(1.4, 0.12)
        if tt > 1.0:
            continue
        g = 0.18 * np.exp(-tt / 0.4) * rng.uniform(0.3, 1.0)
        if rng.random() < 0.5:
            _place(out, _tick(sr, rng, 500, 4000, rng.uniform(0.002, 0.008), 0.04), tt, sr, g, rng.uniform(-0.8, 0.8))
        else:
            _place(out, _ping(sr, rng, rng.uniform(700, 2600), rng.uniform(0.008, 0.03)), tt, sr, g * 0.6,
                   rng.uniform(-0.8, 0.8))
    br = np.cumsum(rng.standard_normal(n))
    rum = lp(hp(br, 30, sr, 2), 220, sr, 2)
    rum = rum / (np.abs(rum).max() + 1e-9) * np.clip(t / 0.03, 0, 1) * np.exp(-t / 0.28) * 0.25
    _place(out, rum, 0.0, sr)
    return _room(fade_edges(out, sr, 0.0, 0.25), sr, 0.22, 1.0)


@fx("house_rumble")
def _house_rumble(sr, rng):
    """Room-shaking rumble (~1.2 s): low shake + house groan + rattling dishes/frames/glass."""
    dur = 1.3
    n = secs(sr, dur)
    t = tvec(n, sr)
    env = np.clip(t / 0.1, 0, 1) * np.clip((dur - t) / 0.45, 0, 1) * (0.75 + 0.25 * smooth_noise(n, sr, 9, rng))
    out = np.zeros((n, 2))
    for ch in range(2):
        br = hp(np.cumsum(rng.standard_normal(n)), 25, sr, 2)
        low = lp(br, 110, sr, 2)
        mid = bp(rng.standard_normal(n), 120, 420, sr, 2)
        out[:, ch] = (0.6 * low / (np.abs(low).max() + 1e-9) + 0.9 * mid / (np.abs(mid).max() + 1e-9)) * env
    _place(out, _thump(sr, 0.5, 55, 110, 0.03, 0.15, 0.6), 0.0, sr, 0.5)
    for kind, rate, g in (("dish", 24, 0.24), ("frame", 15, 0.2), ("glass", 30, 0.15)):
        tt = rng.uniform(0.03, 0.1)
        while tt < dur - 0.25:
            a = float(np.interp(tt, t, env)) * rng.uniform(0.5, 1.0)
            if kind == "dish":
                s = _ping(sr, rng, rng.uniform(2300, 3600), 0.012)
            elif kind == "frame":
                s = _tick(sr, rng, 600, 1400, 0.006, 0.03)
            else:
                s = _ping(sr, rng, rng.uniform(1400, 2200), 0.008)
            _place(out, s, tt, sr, g * a, rng.uniform(-0.7, 0.7))
            tt += (1.0 / rate) * rng.uniform(0.6, 1.5)
    return _room(fade_edges(out, sr, 0.005, 0.15), sr, 0.15, 0.6)


# =============================================================================
# TIREDNESS: glass
# =============================================================================
def _glass(sr, rng, dur, size=1.0):
    out = _canvas(sr, dur)
    n = secs(sr, 0.6)
    t = tvec(n, sr)
    thump = _sweep((70 + 90 * np.exp(-t / 0.02)) / size ** 0.3, sr) * np.exp(-t / (0.06 * size))
    crash = hp(rng.standard_normal(n), 700, sr) * (0.8 * np.exp(-t / (0.05 * size)) + 0.3 * np.exp(-t / (0.2 * size)))
    crash = lp(crash, 8500, sr)
    y = np.tanh(1.3 * (0.7 * thump + crash) * np.clip(t / 0.0005, 0, 1))
    _place(out, fade_edges(y, sr, 0.0003, 0.1), 0.0, sr, 0.9)
    for k in range(int(60 * size)):                   # the pane bursting: dense shards
        tt = abs(rng.normal(0, 0.05 * size)) + rng.exponential(0.02)
        f = math.exp(rng.uniform(math.log(1700), math.log(7000)))
        _place(out, _ping(sr, rng, f, rng.uniform(0.012, 0.06)), tt, sr,
               rng.uniform(0.15, 0.45) * math.exp(-tt * 3), rng.uniform(-0.8, 0.8))
    for k in range(int(45 * size)):                   # falling, tinkling, bouncing
        tt = 0.12 * size + rng.gamma(2.0, 0.18 * size)
        if tt > dur - 0.15:
            continue
        f = math.exp(rng.uniform(math.log(1500), math.log(6000)))
        d = rng.uniform(0.01, 0.05)
        g = rng.uniform(0.08, 0.3) * math.exp(-(tt - 0.1) / (0.7 * size))
        pn = rng.uniform(-0.9, 0.9)
        _place(out, _ping(sr, rng, f, d), tt, sr, g, pn)
        if rng.random() < 0.35:
            _place(out, _ping(sr, rng, f * rng.uniform(0.97, 1.03), d * 0.7), tt + rng.uniform(0.04, 0.09), sr,
                   g * 0.5, pn)
    for k in range(int(4 * size)):                    # a few chunkier pieces
        _place(out, _ping(sr, rng, rng.uniform(900, 1600), 0.08), rng.uniform(0.1, 0.6) * size, sr, 0.25,
               rng.uniform(-0.6, 0.6))
    return out


@fx("glass_smash", trim=-1.0)
def _glass_smash(sr, rng):
    """A window pane breaking + shards tinkling down (~1.7 s)."""
    return _room(_glass(sr, rng, 1.7, 1.0), sr, 0.2, 0.7)


@fx("glass_crash_big")
def _glass_crash_big(sr, rng):
    """Crashing THROUGH a big window: body impact, huge burst, a second break, long debris."""
    out = _glass(sr, rng, 2.8, 1.8)
    _place(out, _thump(sr, 0.6, 50, 120, 0.02, 0.12, 0.4), 0.0, sr, 0.7)
    _place(out, _glass(sr, rng, 1.4, 0.7), 0.32, sr, 0.55)
    return _room(out, sr, 0.25, 1.1)


# =============================================================================
# TIREDNESS: critter ("the thing") and the creature
# =============================================================================
@fx("scratch_wood", trim=0.0)
def _scratch_wood(sr, rng):
    """Small claws scratching wood: 3-5 quick stick-slip strokes."""
    out = _canvas(sr, 1.1)
    t0 = 0.0
    for s in range(int(rng.integers(3, 6))):
        d = rng.uniform(0.1, 0.2)
        n = secs(sr, d)
        t = tvec(n, sr)
        rate = rng.uniform(140, 260) * (1 + 0.3 * np.sin(np.pi * t / d))
        amp = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.7
        x = _stickslip(sr, rng, d, rate, amp, 0.3)
        y = _resonate(x, sr, [(700, 5, 0.6), (1500, 6, 0.55), (2600, 7, 0.35), (4000, 8, 0.12)])
        y += 0.012 * bp(rng.standard_normal(n), 2000, 6000, sr) * amp
        _place(out, fade_edges(y, sr, 0.003, 0.01), t0, sr, rng.uniform(0.7, 1.0), rng.uniform(-0.3, 0.3))
        t0 += d + rng.uniform(0.04, 0.11)
        if t0 > 0.95:
            break
    return _room(out, sr, 0.12, 0.4)


@fx("scurry", trim=0.0)
def _scurry(sr, rng):
    """Tiny claws pattering past (~0.8 s), gallop groups, panning across."""
    dur = 0.85
    out = _canvas(sr, dur + 0.1)
    t = 0.02
    while t < dur - 0.03:
        u = t / dur
        g = math.sin(math.pi * min(1.0, u * 1.05)) ** 0.6
        for leg in range(4):
            tt = t + leg * rng.uniform(0.008, 0.016)
            n = secs(sr, 0.03)
            tl = tvec(n, sr)
            y = 0.8 * bp(rng.standard_normal(n), 2200, 6000, sr) * np.exp(-tl / 0.0012) \
                + 0.7 * np.sin(TAU * rng.uniform(260, 420) * tl) * np.exp(-tl / 0.007) \
                + 0.3 * np.sin(TAU * rng.uniform(900, 1300) * tl) * np.exp(-tl / 0.004)
            _place(out, fade_edges(y * np.clip(tl / 0.0003, 0, 1), sr, 0.0002, 0.003), tt, sr,
                   g * rng.uniform(0.4, 1.0) * (1.0 if leg % 2 == 0 else 0.7), -0.7 + 1.4 * u)
        t += rng.uniform(0.06, 0.08)
    return _room(out, sr, 0.12, 0.4)


def _squeak(sr, rng, d, f0, up=1.25):
    n = secs(sr, d)
    t = tvec(n, sr)
    f = f0 * np.interp(t / d, [0, 0.3, 1], [1.0, up, 0.88]) * (1 + 0.03 * np.sin(TAU * rng.uniform(28, 40) * t))
    ph = TAU * np.cumsum(f) / sr
    y = np.sin(ph) + 0.22 * np.sin(2 * ph + 0.3) + 0.06 * np.sin(3 * ph)
    y += 0.08 * bp(rng.standard_normal(n), 1500, 5000, sr)
    return y * np.clip(t / 0.008, 0, 1) * np.clip((d - t) / 0.03, 0, 1)


@fx("critter_squeak", trim=-8.0)
def _critter_squeak(sr, rng):
    """Small rodent-ish squeak (one or two chirps; seeds vary)."""
    out = _canvas(sr, 0.5)
    d1 = rng.uniform(0.13, 0.19)
    _place(out, _squeak(sr, rng, d1, rng.uniform(2100, 2600)), 0.0, sr, 1.0, 0.05)
    if rng.random() < 0.7:
        _place(out, _squeak(sr, rng, rng.uniform(0.07, 0.1), rng.uniform(2500, 3000), 1.15), d1 + 0.05, sr, 0.7, 0.1)
    return _room(out, sr, 0.1, 0.35)


@fx("critter_hiss", trim=-4.0)
def _critter_hiss(sr, rng):
    """Small spitty hiss (the thing)."""
    dur = 0.55
    n = secs(sr, dur)
    t = tvec(n, sr)
    nz = rng.standard_normal(n)
    y = _formants(nz, sr, [(2500, 3.0, 1.0), (3900, 3.0, 0.55), (1500, 2.5, 0.45)])
    env = np.clip(t / 0.015, 0, 1) * np.exp(-np.maximum(t - 0.05, 0) / 0.18) * (1 + 0.25 * smooth_noise(n, sr, 18, rng))
    spit = bp(nz, 1200, 7000, sr) * np.exp(-t / 0.006) * 1.2
    y = lp(y * env + spit, 7000, sr)
    return _room(pan(fade_edges(y, sr, 0.001, 0.05), 0), sr, 0.1, 0.4)


@fx("chomp", trim=1.5)
def _chomp(sr, rng):
    """Cartoon bite: teeth clack + a downward 'chmp' pop with a little crunch (no gore)."""
    out = _canvas(sr, 0.45)
    n = secs(sr, 0.05)
    t = tvec(n, sr)
    k = rng.uniform(0.9, 1.1)
    clack = _modes(t, [(2900 * k, 0.8, 0.006), (4600 * k, 0.45, 0.004), (1700 * k, 0.45, 0.008)], rng.uniform(0, TAU)) \
        + 0.5 * bp(rng.standard_normal(n), 2000, 8000, sr) * np.exp(-t / 0.0012)
    clack = fade_edges(clack * np.clip(t / 0.0003, 0, 1), sr, 0.0002, 0.005)
    _place(out, clack, 0.0, sr, 0.8)
    _place(out, clack, 0.006, sr, 0.45, 0.1)
    n = secs(sr, 0.24)
    t = tvec(n, sr)
    pop = _sweep((170 + 330 * np.exp(-t / 0.03)) * rng.uniform(0.88, 1.12), sr) * np.exp(-t / 0.06) * np.clip(t / 0.002, 0, 1)
    crunch = bp(rng.standard_normal(n), 800, 3500, sr) * np.exp(-t / 0.03) * (0.4 + 0.6 * np.abs(smooth_noise(n, sr, 110, rng)))
    _place(out, fade_edges(pop + 0.35 * crunch, sr, 0.0005, 0.02), 0.004, sr, 1.0)
    return _room(out, sr, 0.1, 0.35)


@fx("creature_hiss", trim=-1.0)
def _creature_hiss(sr, rng):
    """Big breathy threat hiss with a rough throat growl underneath (sewer space)."""
    dur = 1.5
    n = secs(sr, dur)
    t = tvec(n, sr)
    env = np.clip(t / 0.06, 0, 1) ** 1.3 * np.clip((dur - t) / 0.6, 0, 1) ** 1.2 * (1 + 0.2 * smooth_noise(n, sr, 11, rng))
    nz = rng.standard_normal(n)
    F1 = 820 + 140 * np.sin(np.pi * t / dur)
    breath = _norm(_formants(nz, sr, [(F1, 3.0, 1.0), (1700, 4.0, 0.6), (2700, 5.0, 0.35)]))
    sss = _norm(bp(nz, 3500, 7000, sr)) * 0.22
    f0 = 68 * rng.uniform(0.92, 1.08) * (1 + 0.08 * np.sin(np.pi * t / dur))
    growl = _glottal(f0, n, sr, rng, 0.04, 900, rough=0.7, rough_rate=30)
    growl = _norm(lp(_formants(growl, sr, [(480, 3, 1.0), (1100, 4, 0.5)]), 1500, sr)) * 0.45
    genv = np.clip((t - 0.08) / 0.2, 0, 1) * np.clip((dur - t) / 0.5, 0, 1)
    y = (breath + sss) * env + growl * genv
    return _room(pan(fade_edges(y, sr, 0.005, 0.1), 0), sr, 0.25, 1.6)


@fx("creature_snarl")
def _creature_snarl(sr, rng):
    """Rough rising snarl (voiced growl with period-doubling rattle), not gory."""
    dur = 1.25
    n = secs(sr, dur)
    t = tvec(n, sr)
    f0 = np.interp(t, [0, 0.25, 0.8, dur], [78, 112, 96, 70]) * rng.uniform(0.94, 1.06)
    src = _glottal(f0, n, sr, rng, jitter=0.03, tilt=2200, rough=0.6, rough_rate=32)
    src = src * (1 + 0.35 * np.sin(np.pi * np.cumsum(f0) / sr))            # subharmonic rattle
    F2 = np.interp(t, [0, 0.3, dur], [1200, 1650, 1300])
    y = _norm(_formants(src, sr, [(650, 4, 1.0), (F2, 6, 0.6), (2600, 8, 0.25)]))
    y += 0.3 * _norm(_formants(rng.standard_normal(n), sr, [(900, 3, 1.0), (2400, 4, 0.4)]))
    env = np.clip(t / 0.15, 0, 1) ** 1.5 * np.clip((dur - t) / 0.35, 0, 1) * (1 + 0.25 * smooth_noise(n, sr, 14, rng))
    y = np.tanh(0.6 * y * env)
    return _room(pan(fade_edges(y, sr, 0.005, 0.08), 0), sr, 0.25, 1.3)


@fx("creature_chitter", trim=-3.0)
def _creature_chitter(sr, rng):
    """Curious clicks and chirps ending on a rising 'huh?' chirp (seeds vary)."""
    out = _canvas(sr, 1.3)
    t = 0.0

    def chirp(t0, d, f0, rise, g):
        n = secs(sr, d)
        tl = tvec(n, sr)
        ph = TAU * np.cumsum(f0 * (1 + rise * (tl / d) ** 1.3)) / sr
        y = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * np.sin(np.pi * tl / d) ** 0.8
        _place(out, y, t0, sr, g, rng.uniform(-0.2, 0.2))

    for g in range(int(rng.integers(3, 5))):
        if g == 0 or rng.random() < 0.55:
            for c in range(int(rng.integers(3, 7))):
                n = secs(sr, 0.02)
                tl = tvec(n, sr)
                y = np.sin(TAU * rng.uniform(1700, 3000) * tl) * np.exp(-tl / 0.0025) \
                    + 0.35 * bp(rng.standard_normal(n), 1500, 5000, sr) * np.exp(-tl / 0.001)
                _place(out, fade_edges(y, sr, 0.0002, 0.004), t, sr, rng.uniform(0.5, 0.9), rng.uniform(-0.2, 0.2))
                t += rng.uniform(0.025, 0.04)
        else:
            d = rng.uniform(0.06, 0.1)
            chirp(t, d, rng.uniform(1200, 1700), rng.uniform(-0.25, 0.5), 0.55)
            t += d + 0.03
        t += rng.uniform(0.06, 0.13)
        if t > 0.95:
            break
    chirp(min(t, 1.0), 0.12, rng.uniform(1250, 1500), 0.7, 0.65)
    return _room(out, sr, 0.2, 0.9)


@fx("creature_purr", trim=-1.0)
def _creature_purr(sr, rng):
    """Soft rumbly purr (~1.5 s): ~25 Hz larynx flutter on exhale, then inhale."""
    dur = 1.6
    n = secs(sr, dur)
    t = tvec(n, sr)
    breath = np.interp(t, [0, 0.08, 0.68, 0.78, 0.86, 1.45, dur], [0, 1, 0.9, 0.25, 0.75, 0.7, 0])
    rate = np.where(t < 0.78, 26.0, 23.0) + 1.5 * smooth_noise(n, sr, 3, rng)
    frac = (np.cumsum(rate) / sr) % 1.0
    flutter = np.sin(np.pi * frac) ** 4
    src = lp(rng.standard_normal(n), 1100, sr, 2) + 0.5 * lp(saw(rate * 4, n, sr), 600, sr)
    y = _norm(_formants(src * flutter, sr, [(140, 2.0, 1.0), (300, 2.5, 0.75), (650, 3.0, 0.3)]))
    y += 0.08 * _norm(bp(rng.standard_normal(n), 600, 2500, sr)) * flutter
    return _room(pan(fade_edges(y * breath, sr, 0.01, 0.08), 0), sr, 0.12, 0.6)


@fx("creature_chirp_sad", trim=-3.0)
def _creature_chirp_sad(sr, rng):
    """Small sad descending coo, then a smaller one, with a quiver."""
    out = _canvas(sr, 1.15)
    k = rng.uniform(0.95, 1.05)
    for t0, d, f0, f1, f2, a in ((0.0, 0.55, 760, 840, 520, 1.0), (0.62, 0.38, 640, 660, 420, 0.65)):
        n = secs(sr, d)
        t = tvec(n, sr)
        u = t / d
        f = np.interp(u, [0, 0.25, 1], [f0, f1, f2]) * k * (1 + 0.013 * np.clip(u * 2 - 0.4, 0, 1) * np.sin(TAU * 6.5 * t))
        ph = TAU * np.cumsum(f) / sr
        y = lp(np.sin(ph) + 0.3 * np.sin(2 * ph + 0.4) + 0.1 * np.sin(3 * ph + 1), 2500, sr)
        y += 0.05 * bp(rng.standard_normal(n), 800, 3000, sr)
        _place(out, y * np.clip(t / 0.04, 0, 1) * np.clip((d - t) / 0.15, 0, 1) ** 1.2, t0, sr, a)
    return _room(out, sr, 0.25, 1.2)


# =============================================================================
# TIREDNESS: Impulsivity (the dog-thing)
# =============================================================================
@fx("dog_pant", trim=-1.0, loop=2.0)
def _dog_pant(sr, rng):
    """Goofy big-dog panting, 7 'hah-hih' cycles per 2 s (loopable)."""
    P = 2.0
    nP = secs(sr, P)
    y = np.zeros(2 * nP)
    cyc = 7
    for c in range(cyc):
        t0 = c * P / cyc
        for kind, off, d, g in (("ex", 0.0, 0.12, 1.0), ("in", 0.15, 0.09, 0.5)):
            n = secs(sr, d)
            t = tvec(n, sr)
            nz = rng.standard_normal(n)
            if kind == "ex":
                src = nz + 0.35 * lp(saw(np.full(n, 230.0 * rng.uniform(0.95, 1.05)), n, sr), 1500, sr)
                F = [(760, 3.5, 1.0), (1350, 5, 0.6), (2600, 6, 0.22)]
            else:
                src = nz
                F = [(560, 3.0, 0.6), (1900, 4, 0.7), (3000, 5, 0.25)]
            s = _formants(src, sr, F) * np.clip(t / 0.012, 0, 1) * np.exp(-np.maximum(t - 0.02, 0) / (d * 0.45))
            s = fade_edges(s, sr, 0.001, 0.01)
            i0 = secs(sr, t0 + off)
            y[i0:i0 + n] += s * g * rng.uniform(0.85, 1.0)
    return pan(_fold(y, nP), 0)


@fx("dog_woof", trim=-1.0)
def _dog_woof(sr, rng):
    """One goofy 'bwoof'."""
    dur = 0.42
    n = secs(sr, dur)
    t = tvec(n, sr)
    f0 = np.interp(t, [0, 0.05, 0.3, dur], [300, 340, 240, 200]) * rng.uniform(0.95, 1.05)
    src = _glottal(f0, n, sr, rng, jitter=0.02, tilt=2500, rough=0.25, rough_rate=40)
    F1 = np.interp(t, [0, 0.06, 0.25, dur], [380, 780, 650, 420])
    F2 = np.interp(t, [0, 0.06, 0.25, dur], [900, 1450, 1300, 1000])
    y = _norm(_formants(src, sr, [(F1, 4, 1.0), (F2, 6, 0.6), (2600, 8, 0.2)]))
    y += 0.4 * _norm(_formants(rng.standard_normal(n), sr, [(F1, 3, 1.0), (F2, 4, 0.5)])) * np.exp(-t / 0.05)
    env = np.clip(t / 0.015, 0, 1) * np.exp(-np.maximum(t - 0.08, 0) / 0.12)
    y = np.tanh(0.7 * y * env)
    return _room(pan(fade_edges(y, sr, 0.001, 0.05), 0), sr, 0.15, 0.5)


# =============================================================================
# TIREDNESS: cage, lab, facility
# =============================================================================
@fx("cage_creak", trim=-2.0)
def _cage_creak(sr, rng):
    """Small metal cage door slowly creaking open, ending against the bars."""
    dur = 1.6
    n = secs(sr, dur)
    t = tvec(n, sr)
    rate = np.interp(t, [0, 0.25, 0.7, 1.1, 1.4], [35, 140, 260, 180, 90]) * (1 + 0.08 * smooth_noise(n, sr, 6, rng))
    amp = np.interp(t, [0, 0.12, 0.6, 1.2, 1.4, dur], [0, 0.8, 1.0, 0.7, 0.2, 0])
    x = _stickslip(sr, rng, dur, rate, amp, 0.06)
    y = _resonate(x, sr, [(720, 30, 0.8), (1480, 35, 0.7), (2290, 40, 0.5), (3410, 40, 0.25), (310, 12, 0.6)])
    y += 0.004 * bp(rng.standard_normal(n), 1500, 4000, sr) * amp
    out = _canvas(sr, dur + 0.3)
    _place(out, fade_edges(y, sr, 0.01, 0.05), 0.0, sr)
    n2 = secs(sr, 0.3)
    t2 = tvec(n2, sr)
    clank = _modes(t2, [(510, 0.6, 0.08), (1230, 0.5, 0.05), (2210, 0.35, 0.03), (3460, 0.2, 0.02)]) \
        + 0.4 * bp(rng.standard_normal(n2), 800, 4000, sr) * np.exp(-t2 / 0.003)
    _place(out, fade_edges(clank * np.clip(t2 / 0.0005, 0, 1), sr, 0.0003, 0.05), dur - 0.12, sr,
           0.35 * np.abs(y).max() / 0.5, 0.2)
    return _room(out, sr, 0.22, 0.9)


@fx("cage_rattle")
def _cage_rattle(sr, rng):
    """Wire cage shaken: a quick irregular run of metal clanks (~0.8 s)."""
    out = _canvas(sr, 0.95)
    t = 0.0
    while t < 0.75:
        n = secs(sr, 0.15)
        tl = tvec(n, sr)
        k = rng.uniform(0.9, 1.1)
        y = _modes(tl, [(1180 * k, 0.6, 0.04), (2050 * k, 0.5, 0.03), (3150 * k, 0.32, 0.02),
                        (4300 * k, 0.12, 0.012), (420 * k, 0.45, 0.03)])
        y += 0.45 * bp(rng.standard_normal(n), 800, 5000, sr) * np.exp(-tl / 0.002)
        y += 0.35 * np.sin(TAU * 150 * tl) * np.exp(-tl / 0.02)
        _place(out, fade_edges(y * np.clip(tl / 0.0004, 0, 1), sr, 0.0002, 0.02), t, sr,
               rng.uniform(0.4, 1.0) * (1 - 0.5 * t), rng.uniform(-0.4, 0.4))
        t += rng.uniform(0.03, 0.09)
    return _room(out, sr, 0.2, 0.8)


@fx("latch_click", trim=0.0)
def _latch_click(sr, rng):
    """Metal latch: spring 'ch' then the bolt 'chk'."""
    out = _canvas(sr, 0.32)
    n = secs(sr, 0.06)
    t = tvec(n, sr)
    c1 = _modes(t, [(3200, 0.7, 0.006), (5100, 0.35, 0.004), (1900, 0.35, 0.008)]) \
        + 0.4 * bp(rng.standard_normal(n), 2000, 8000, sr) * np.exp(-t / 0.0008)
    _place(out, fade_edges(c1 * np.clip(t / 0.0002, 0, 1), sr, 0.0001, 0.005), 0.0, sr, 0.6)
    n = secs(sr, 0.15)
    t = tvec(n, sr)
    c2 = _modes(t, [(1400, 0.8, 0.015), (2650, 0.5, 0.01), (4100, 0.22, 0.006)]) \
        + 0.6 * np.sin(TAU * 300 * t) * np.exp(-t / 0.012) + 0.45 * bp(rng.standard_normal(n), 1000, 6000, sr) * np.exp(-t / 0.001)
    _place(out, fade_edges(c2 * np.clip(t / 0.0002, 0, 1), sr, 0.0001, 0.02), 0.065 + rng.uniform(-0.01, 0.01), sr, 1.0)
    return _room(out, sr, 0.15, 0.5)


@fx("alarm", trim=-4.5, loop=2.0)
def _alarm(sr, rng):
    """Facility siren, two 'whoop's per 2 s (loopable)."""
    P = 2.0
    nP = secs(sr, P)
    t = tvec(nP, sr)
    u = t % 1.0
    f = 470 + 830 * np.clip(u / 0.82, 0, 1) ** 0.7
    src = 0.7 * pulse(f, nP, sr, 0.5) + 0.3 * saw(f, nP, sr)
    y = src * np.clip(u / 0.03, 0, 1) * np.clip((0.9 - u) / 0.06, 0, 1)
    y = _circ(lambda z: np.tanh(2.0 * bp(biquad(z, "peak", 1100, sr, 1.0, 4.0), 350, 3800, sr)), y)
    st = stereoize(y)
    return _circ(lambda z: z + 0.35 * reverb(z, sr, rt60=1.4, predelay=0.03, damp=0.5, seed=17), st)


@fx("pod_hum", trim=-7.0, loop=3.0)
def _pod_hum(sr, rng):
    """Deep containment-pod machine hum with a slow beat and a faint whine (loop 3 s)."""
    P = 3.0
    nP = secs(sr, P)
    t = tvec(nP, sr)
    y = np.zeros((nP, 2))
    for f, a in ((50.0, 0.55), (100.0, 0.7), (100 + 1 / 3, 0.35), (150.0, 0.5), (150 + 2 / 3, 0.25),
                 (200.0, 0.35), (250.0, 0.2), (300.0, 0.14), (350.0, 0.07)):
        for ch in range(2):
            y[:, ch] += a * np.sin(TAU * f * t + rng.uniform(0, TAU))
    whine = np.sin(TAU * 1200.0 * t) * (0.5 + 0.5 * np.sin(TAU * t / P)) * 0.04
    y += pan(whine, 0.2)
    for ch in range(2):
        y[:, ch] += 0.12 * _pnoise(nP, sr, rng, 80, 700, -3)
    return y


# =============================================================================
# TIREDNESS: people (steps, breath, voice-ish)
# =============================================================================
@fx("footstep", trim=3.0)
def _footstep(sr, rng):
    """One shoe step on a hard floor (seeds vary)."""
    return _room(pan(_step(sr, rng, 1.0, rng.uniform(0.055, 0.085)), rng.uniform(-0.15, 0.15)), sr, 0.15, 0.5)


@fx("footsteps_run", trim=2.0)
def _footsteps_run(sr, rng):
    """Fast running footsteps (~1 s, 6-7 steps)."""
    out = _canvas(sr, 1.15)
    t = 0.0
    k = 0
    while t < 0.95:
        _place(out, _step(sr, rng, rng.uniform(0.75, 1.0), rng.uniform(0.025, 0.04), 1.2), t, sr, 1.0,
               0.15 if k % 2 else -0.15)
        t += rng.uniform(0.13, 0.16)
        k += 1
    return _room(out, sr, 0.15, 0.5)


@fx("foot_tap")
def _foot_tap(sr, rng):
    """A single shoe tap on a wooden floor (impatient foot; seeds vary)."""
    n = secs(sr, 0.25)
    t = tvec(n, sr)
    k = rng.uniform(0.92, 1.08)
    y = _modes(t, [(260 * k, 0.6, 0.03), (540 * k, 0.5, 0.02), (990 * k, 0.32, 0.012), (1750 * k, 0.12, 0.007)])
    y += 0.5 * _sweep(110 + 60 * np.exp(-t / 0.008), sr) * np.exp(-t / 0.02)
    y += 0.35 * bp(rng.standard_normal(n), 1500, 5000, sr) * np.exp(-t / 0.0015)
    return _room(pan(fade_edges(y * np.clip(t / 0.0006, 0, 1), sr, 0.0003, 0.03), rng.uniform(-0.1, 0.1)), sr, 0.15, 0.45)


@fx("tap_tap", trim=0.0)
def _tap_tap(sr, rng):
    """Two quick fingertip taps on a shoulder (cloth over body)."""
    out = _canvas(sr, 0.45)
    for i, tt in enumerate((0.0, 0.14 + rng.uniform(-0.015, 0.015))):
        n = secs(sr, 0.1)
        t = tvec(n, sr)
        y = lp(rng.standard_normal(n), 1400, sr, 2) * np.exp(-t / 0.01) \
            + 0.6 * np.sin(TAU * rng.uniform(170, 210) * t) * np.exp(-t / 0.018)
        y += 0.1 * bp(rng.standard_normal(n), 2000, 5000, sr) * np.exp(-t / 0.008)
        _place(out, fade_edges(y * np.clip(t / 0.0015, 0, 1), sr, 0.0005, 0.02), tt, sr, 1.0 if i == 0 else 0.85)
    return _room(out, sr, 0.1, 0.3)


@fx("cloth_rustle", trim=-6.0)
def _cloth_rustle(sr, rng):
    """Soft sweater rustle: two movements of fabric swish with fibre crackle."""
    dur = 0.75
    out = _canvas(sr, dur)
    n = secs(sr, dur)
    t = tvec(n, sr)
    env = (0.6 * np.exp(-((t - 0.18) / 0.09) ** 2) + np.exp(-((t - 0.45) / 0.12) ** 2)) * (1 + 0.3 * smooth_noise(n, sr, 20, rng))
    nz = rng.standard_normal(n)
    _place(out, (bp(nz, 400, 4000, sr) * 0.6 + lp(nz, 500, sr) * 0.35) * env, 0.0, sr)
    for k in range(60):
        tt = rng.uniform(0.05, dur - 0.05)
        _place(out, _tick(sr, rng, 1500, 5500, rng.uniform(0.0005, 0.002), 0.01), tt, sr,
               0.12 * float(np.interp(tt, t, env)) * rng.random(), rng.uniform(-0.4, 0.4))
    return fade_edges(out, sr, 0.01, 0.05)


def _breath_voice(sr, rng, n, t, F1, F2, f0, breath_env, voice_env, vmix, F3=2500.0):
    nz = rng.standard_normal(n)
    br = _norm(_formants(nz, sr, [(F1, 3.0, 1.0), (F2, 4.0, 0.65), (F3, 5.0, 0.3), (3500, 4.0, 0.12)]))
    v = _norm(_formants(_glottal(f0, n, sr, rng, 0.015, 1400), sr, [(F1, 5.0, 1.0), (F2, 7.0, 0.45), (F3, 9.0, 0.15)]))
    return br * breath_env + vmix * v * voice_env


@fx("sigh", trim=-3.0)
def _sigh(sr, rng):
    """A tired human exhale 'hhhaaah' (~0.8 s) with a hint of voice at the start."""
    dur = 0.85
    n = secs(sr, dur)
    t = tvec(n, sr)
    F1 = np.interp(t, [0, 0.2, dur], [650, 600, 480])
    F2 = np.interp(t, [0, dur], [1150, 1000])
    f0 = np.interp(t, [0, 0.3, dur], [105, 92, 80]) * rng.uniform(0.95, 1.05)
    benv = np.clip(t / 0.07, 0, 1) ** 1.5 * np.exp(-np.maximum(t - 0.12, 0) / 0.28)
    venv = np.clip(t / 0.05, 0, 1) * np.clip((0.35 - t) / 0.2, 0, 1)
    y = _breath_voice(sr, rng, n, t, F1, F2, f0, benv, venv, 0.18)
    return _room(pan(fade_edges(lp(y, 6000, sr), sr, 0.005, 0.08), 0), sr, 0.1, 0.4)


@fx("yawn", trim=-2.0)
def _yawn(sr, rng):
    """Human yawn: breathy inhale, then a voiced 'aaah-oh-mm' sliding down."""
    dur = 2.0
    n = secs(sr, dur)
    t = tvec(n, sr)
    k = rng.uniform(0.94, 1.06)
    f0 = np.interp(t, [0.5, 0.7, 1.1, 1.6, 1.95], [120, 165, 150, 110, 85]) * k
    F1 = np.interp(t, [0, 0.5, 0.9, 1.4, 1.8, dur], [500, 700, 820, 650, 420, 320])
    F2 = np.interp(t, [0, 0.5, 0.9, 1.4, 1.8, dur], [1300, 1200, 1150, 950, 850, 800])
    inh = np.interp(t, [0, 0.15, 0.5, 0.62], [0, 0.6, 0.9, 0])
    venv = np.interp(t, [0.45, 0.62, 1.2, 1.7, dur], [0, 1.0, 0.85, 0.4, 0])
    y = _breath_voice(sr, rng, n, t, F1, F2, f0, 0.55 * inh + 0.3 * venv, venv, 0.8)
    return _room(pan(fade_edges(lp(y, 6000, sr), sr, 0.01, 0.1), 0), sr, 0.12, 0.45)


@fx("cough", trim=1.0)
def _cough(sr, rng):
    """One short human cough ('kh-uh')."""
    dur = 0.4
    n = secs(sr, dur)
    t = tvec(n, sr)
    F1 = np.interp(t, [0, 0.1, dur], [620, 550, 480])
    f0 = np.interp(t, [0, 0.05, 0.25, dur], [150, 135, 110, 100]) * rng.uniform(0.9, 1.1)
    benv = np.clip(t / 0.004, 0, 1) * (0.85 * np.exp(-t / 0.05) + 0.3 * np.exp(-t / 0.14))
    venv = np.clip((t - 0.01) / 0.02, 0, 1) * np.exp(-np.maximum(t - 0.03, 0) / 0.07)
    y = _breath_voice(sr, rng, n, t, F1, 1400.0, f0, benv, venv, 0.45)
    return _room(pan(fade_edges(lp(y, 6500, sr), sr, 0.0005, 0.05), 0), sr, 0.12, 0.4)


# =============================================================================
# TIREDNESS: house foley
# =============================================================================
@fx("drawer_open", trim=0.0)
def _drawer_open(sr, rng):
    """Wooden drawer sliding open, a stop knock, contents shifting."""
    out = _canvas(sr, 0.85)
    d = 0.45
    n = secs(sr, d)
    t = tvec(n, sr)
    env = np.clip(t / 0.05, 0, 1) * (0.8 + 0.2 * np.sin(np.pi * t / d))
    x = _stickslip(sr, rng, d, 70 + 40 * np.sin(np.pi * t / d), env, 0.35)
    y = _resonate(x, sr, [(220, 4, 0.8), (480, 5, 0.6), (950, 6, 0.4), (1800, 6, 0.2)])
    y += 0.02 * bp(rng.standard_normal(n), 300, 2000, sr) * env
    _place(out, fade_edges(y, sr, 0.01, 0.02), 0.0, sr, 1.0)
    n2 = secs(sr, 0.2)
    t2 = tvec(n2, sr)
    knock = _modes(t2, [(180, 0.8, 0.04), (420, 0.6, 0.025), (900, 0.35, 0.012)]) \
        + 0.4 * bp(rng.standard_normal(n2), 500, 3000, sr) * np.exp(-t2 / 0.003)
    g = np.abs(y).max() * 1.4 + 1e-6
    _place(out, fade_edges(knock * np.clip(t2 / 0.0008, 0, 1), sr, 0.0003, 0.03), d, sr, g)
    for j in range(3):
        _place(out, _ping(sr, rng, rng.uniform(2200, 3800), 0.012), d + 0.02 + 0.03 * j + rng.uniform(0, 0.02), sr,
               0.2 * g, rng.uniform(-0.4, 0.4))
    return _room(out, sr, 0.12, 0.4)


@fx("plate_clink", trim=-5.0)
def _plate_clink(sr, rng):
    """Ceramic plates touching (clink + a smaller settle)."""
    out = _canvas(sr, 0.7)
    k = rng.uniform(0.95, 1.05)
    for tt, a in ((0.0, 1.0), (0.11 + rng.uniform(0, 0.03), 0.45)):
        n = secs(sr, 0.55)
        t = tvec(n, sr)
        y = _modes(t, [(1260 * k, 0.35, 0.14), (2110 * k, 1.0, 0.11), (3360 * k, 0.55, 0.08),
                       (4870 * k, 0.25, 0.05), (6500 * k, 0.08, 0.03)])
        y += 0.35 * bp(rng.standard_normal(n), 2000, 8000, sr) * np.exp(-t / 0.001)
        _place(out, fade_edges(y * np.clip(t / 0.0003, 0, 1), sr, 0.0002, 0.05), tt, sr, a, rng.uniform(-0.2, 0.2))
    return _room(out, sr, 0.15, 0.5)


@fx("chair_creak", trim=-2.0)
def _chair_creak(sr, rng):
    """Gaming chair creak (plastic/metal stick-slip)."""
    dur = 0.7
    n = secs(sr, dur)
    t = tvec(n, sr)
    rate = np.interp(t, [0, 0.2, 0.5, dur], [70, 150, 120, 60]) * rng.uniform(0.9, 1.1)
    amp = np.interp(t, [0, 0.08, 0.45, dur], [0, 1, 0.8, 0])
    x = _stickslip(sr, rng, dur, rate, amp, 0.08)
    y = _resonate(x, sr, [(380, 10, 0.7), (820, 18, 0.6), (1450, 22, 0.45), (2300, 25, 0.22)])
    return _room(pan(fade_edges(y, sr, 0.01, 0.05), 0), sr, 0.12, 0.4)


@fx("mouse_click", trim=0.0)
def _mouse_click(sr, rng):
    """Gaming-mouse click (press + release)."""
    out = _canvas(sr, 0.16)
    for tt, a in ((0.0, 1.0), (0.055 + rng.uniform(-0.01, 0.01), 0.55)):
        n = secs(sr, 0.03)
        t = tvec(n, sr)
        k = rng.uniform(0.9, 1.1)
        y = _modes(t, [(2400 * k, 0.6, 0.004), (4100 * k, 0.35, 0.003), (1100 * k, 0.4, 0.006)], rng.uniform(0, TAU)) \
            + 0.4 * bp(rng.standard_normal(n), 2000, 7000, sr) * np.exp(-t / 0.0007)
        _place(out, fade_edges(y * np.clip(t / 0.0002, 0, 1), sr, 0.0001, 0.005), tt, sr, a, 0.1)
    return _room(out, sr, 0.06, 0.25)


# =============================================================================
# TIREDNESS: vehicles, motion
# =============================================================================
@fx("van_door")
def _van_door(sr, rng):
    """Sliding van door: roll along the track, then a heavy metal slam + latch."""
    out = _canvas(sr, 1.5)
    d = 0.5
    n = secs(sr, d)
    t = tvec(n, sr)
    env = np.clip(t / 0.08, 0, 1) ** 1.2
    roll = lp(rng.standard_normal(n), 700, sr, 2) * 0.5
    clicks = _resonate(_stickslip(sr, rng, d, 18 + 30 * t / d, env, 0.2), sr, [(600, 5, 0.6), (1300, 6, 0.4), (2400, 7, 0.2)])
    y = (roll + 6.0 * clicks + 0.08 * bp(rng.standard_normal(n), 1500, 4000, sr)) * env
    _place(out, fade_edges(y, sr, 0.01, 0.01), 0.0, sr, 0.35 / (np.abs(y).max() + 1e-9), -0.3)
    n = secs(sr, 0.9)
    t = tvec(n, sr)
    k = rng.uniform(0.92, 1.08)
    thump = _sweep((80 + 90 * np.exp(-t / 0.015)) * k, sr) * np.exp(-t / 0.1)
    panel = _modes(t, [(185 * k, 0.8, 0.18), (412 * k, 0.7, 0.14), (690 * k, 0.55, 0.1), (1130 * k, 0.4, 0.07),
                       (1720 * k, 0.25, 0.05), (2650 * k, 0.12, 0.03)], rng.uniform(0, TAU))
    imp = bp(rng.standard_normal(n), 300, 5000, sr) * np.exp(-t / 0.006)
    s = np.tanh(1.6 * (thump + 0.6 * panel + 0.8 * imp) * np.clip(t / 0.0008, 0, 1))
    _place(out, fade_edges(s, sr, 0.0003, 0.1), 0.48, sr, 1.0)
    n = secs(sr, 0.1)
    t = tvec(n, sr)
    latch = _modes(t, [(1500, 0.6, 0.012), (2700, 0.4, 0.008)]) + 0.4 * bp(rng.standard_normal(n), 1500, 6000, sr) * np.exp(-t / 0.001)
    _place(out, fade_edges(latch, sr, 0.0002, 0.02), 0.5, sr, 0.25, 0.1)
    return _room(out, sr, 0.15, 0.7)


@fx("smear_zip", trim=-1.0)
def _smear_zip(sr, rng):
    """Super-fast cartoon teleport 'zip!' panning across."""
    d = 0.32
    n = secs(sr, d)
    t = tvec(n, sr)
    u = t / d
    y = tv_filter(rng.standard_normal(n), 900 * (7000 / 900) ** np.clip(u / 0.6, 0, 1), sr, "bandpass", q=2.0,
                  stages=1, block=64)
    y = _norm(y) + 0.9 * _sweep(500 * (2600 / 500) ** np.clip(u / 0.5, 0, 1), sr)
    y *= np.clip(u / 0.08, 0, 1) * np.exp(-np.maximum(u - 0.35, 0) / 0.15)
    th = (np.clip(-0.8 + 1.6 * u / 0.6, -1, 1) + 1) * math.pi / 4
    return np.stack([y * np.cos(th), y * np.sin(th)], 1) * math.sqrt(2)


@fx("wind_fall")
def _wind_fall(sr, rng):
    """Falling wind rush (~1.5 s), building, with cloth flutter and a thin whistle."""
    dur = 1.6
    n = secs(sr, dur)
    t = tvec(n, sr)
    u = t / dur
    out = np.zeros((n, 2))
    for ch in range(2):
        nz = rng.standard_normal(n)
        w = _norm(tv_filter(nz, 350 + 1100 * u ** 1.4 + 200 * smooth_noise(n, sr, 4, rng), sr, "bandpass", q=0.9, stages=1))
        low = _norm(lp(nz, 180, sr, 2)) * 0.6
        whistle = _norm(tv_filter(nz, 1800 + 500 * u + 150 * smooth_noise(n, sr, 2, rng), sr, "bandpass", q=9,
                                  stages=1)) * 0.15
        flutter = 1 + 0.35 * u * np.sin(TAU * np.cumsum(14 + 6 * u) / sr + ch)
        out[:, ch] = (w + low + whistle) * flutter
    out *= ((0.25 + 0.75 * u ** 1.2) * np.clip(t / 0.25, 0, 1))[:, None]
    return fade_edges(out, sr, 0.01, 0.06)


# =============================================================================
# TIREDNESS: headphones, game, UI
# =============================================================================
@fx("anc_on", trim=-2.0)
def _anc_on(sr, rng):
    """Noise-cancelling engaging: plastic click, the room hush draining away with
    an ear-pressure 'thoom', and a tiny two-note chime."""
    out = _canvas(sr, 1.3)
    n = secs(sr, 0.04)
    t = tvec(n, sr)
    click = _modes(t, [(1800, 0.6, 0.004), (3100, 0.35, 0.003)]) + 0.3 * bp(rng.standard_normal(n), 1500, 6000, sr) * np.exp(-t / 0.0008)
    _place(out, fade_edges(click * np.clip(t / 0.0002, 0, 1), sr, 0.0001, 0.005), 0.0, sr, 0.5)
    d = 0.7
    n = secs(sr, d)
    t = tvec(n, sr)
    room = tv_filter(rng.standard_normal(n), 3000 * np.exp(-t / 0.12) + 120, sr, "lowpass", q=0.7, block=256)
    room = _norm(room) * np.clip(t / 0.02, 0, 1) * np.exp(-t / 0.18) * 0.18
    th = _sweep((70 * np.exp(-t / 0.25) + 40) * rng.uniform(0.9, 1.1), sr) * np.clip(t / 0.04, 0, 1) * np.exp(-t / 0.22) * 0.4
    _place(out, fade_edges(room + th, sr, 0.002, 0.05), 0.03, sr)
    for m, tt, g in ((79, 0.45, 0.2), (86, 0.55, 0.24)):
        nb = secs(sr, 0.6)
        tb = tvec(nb, sr)
        f = hz(m)
        ding = (np.sin(TAU * f * tb) + 0.1 * np.sin(TAU * 2 * f * tb)) * np.exp(-tb / 0.16) * np.clip(tb / 0.003, 0, 1)
        _place(out, fade_edges(ding, sr, 0.001, 0.03), tt, sr, g, 0.1)
    return _room(out, sr, 0.1, 0.4)


@fx("game_blips", trim=-4.0)
def _game_blips(sr, rng):
    """A burst of 8-bit game sounds (~1.5 s): jumps, coins, lasers, hits, power-ups."""
    out = _canvas(sr, 1.6)
    t = 0.0
    while t < 1.3:
        kind = rng.choice(["jump", "coin", "laser", "hit", "power", "blip", "bounce"],
                          p=[0.22, 0.18, 0.15, 0.12, 0.1, 0.13, 0.1])
        if kind == "jump":
            y = _chip(rng.uniform(260, 320), 0.13, sr, 0.5, rng.uniform(700, 900))
        elif kind == "coin":
            y = np.concatenate([_chip(988, 0.06, sr, 0.5), _chip(1319, 0.22, sr, 0.5, decay=0.08)])
        elif kind == "laser":
            y = _chip(rng.uniform(1200, 1600), 0.11, sr, 0.25, rng.uniform(220, 320))
        elif kind == "hit":
            n = secs(sr, 0.08)
            hold = int(rng.integers(6, 14))
            y = np.repeat(rng.uniform(-1, 1, n // hold + 1), hold)[:n] * np.exp(-tvec(n, sr) / 0.025)
        elif kind == "power":
            y = np.concatenate([_chip(hz(m), 0.035, sr, 0.125) for m in (72, 76, 79, 84, 88)])
        elif kind == "blip":
            y = _chip(rng.choice([880.0, 1046.5, 1174.7]), 0.045, sr, 0.5)
        else:
            y = np.concatenate([_chip(600, 0.05, sr, 0.25), _chip(900, 0.06, sr, 0.25, decay=0.03)])
        _place(out, fade_edges(np.asarray(y, dtype=float), sr, 0.001, 0.005), t, sr, 0.5, rng.uniform(-0.25, 0.25))
        t += len(y) / sr + rng.uniform(0.03, 0.18)
    return _room(lp(out, 7000, sr), sr, 0.1, 0.3)


@fx("game_music_leak", trim=-8.0, loop=2.0)
def _game_music_leak(sr, rng):
    """Tinny chiptune leaking out of headphones (loop 2 s = one bar at 120 BPM)."""
    P = 2.0
    nP = secs(sr, P)
    y = np.zeros(2 * nP)

    def put(sig, tt, g):
        i0 = secs(sr, tt)
        y[i0:i0 + len(sig)] += sig * g

    for k, m in enumerate((45, 57, 45, 57, 41, 53, 43, 55)):          # A F G bassline
        put(_chip(hz(m), 0.2, sr, 0.5, decay=0.12), k * 0.25, 0.5)
    lead = [76, 0, 79, 81, 0, 79, 76, 74, 72, 0, 74, 76, 0, 79, 74, 0]
    for k, m in enumerate(lead):
        if m:
            put(_chip(hz(m), 0.11, sr, 0.25, decay=0.09), k * 0.125, 0.35)
    for k in range(4):                                                 # noise 'drums'
        n = secs(sr, 0.06)
        hold = 3 if k % 2 == 0 else 1
        nz = np.repeat(rng.uniform(-1, 1, n // hold + 1), hold)[:n] * np.exp(-tvec(n, sr) / (0.03 if k % 2 == 0 else 0.015))
        put(nz, k * 0.5, 0.25)
    y = _fold(y, nP)
    y = _circ(lambda z: biquad(lp(hp(z, 600, sr, 2), 2600, sr, 2), "peak", 1700, sr, 1.2, 6.0), y)
    return pan(y, 0.15)


# =============================================================================
# TIREDNESS: sewer, powers, stingers
# =============================================================================
@fx("drip", trim=-2.0)
def _drip(sr, rng):
    """One water drip in a tunnel: bubble 'plink' + long echoey tail."""
    out = _canvas(sr, 2.2)
    f0 = rng.uniform(850, 1500)
    n = secs(sr, 0.12)
    t = tvec(n, sr)
    y = _sweep(f0 * (1 + 0.7 * (1 - np.exp(-t / 0.006))), sr) * np.exp(-t / 0.022) * np.clip(t / 0.0008, 0, 1)
    y += 0.2 * bp(rng.standard_normal(n), 2000, 7000, sr) * np.exp(-t / 0.001)
    _place(out, fade_edges(y, sr, 0.0002, 0.02), 0.0, sr, 1.0, rng.uniform(-0.4, 0.4))
    return out + 0.45 * reverb(out, sr, rt60=2.2, predelay=0.03, damp=0.5, seed=13)


@fx("water_splash")
def _water_splash(sr, rng):
    """Body landing in shallow water: thump, splash, bubbles, droplets raining back."""
    out = _canvas(sr, 1.7)
    n = secs(sr, 0.9)
    t = tvec(n, sr)
    thump = _sweep(75 + 80 * np.exp(-t / 0.02), sr) * np.exp(-t / 0.07)
    body = lp(rng.standard_normal(n), 3500, sr, 2) * (0.8 * np.exp(-t / 0.06) + 0.35 * np.exp(-t / 0.25)) \
        * (1 + 0.5 * smooth_noise(n, sr, 60, rng))
    spray = bp(rng.standard_normal(n), 2500, 8000, sr) * np.exp(-t / 0.12) * 0.2
    _place(out, fade_edges(np.tanh(1.2 * (0.8 * thump + body + spray) * np.clip(t / 0.002, 0, 1)), sr, 0.001, 0.2), 0.0, sr)
    for k in range(30):
        tt = rng.exponential(0.12)
        if tt > 0.7:
            continue
        f0, d = rng.uniform(350, 1400), rng.uniform(0.015, 0.05)
        nb = secs(sr, d * 4)
        tb = tvec(nb, sr)
        b = _sweep(f0 * (1 + 0.5 * (1 - np.exp(-tb / (d * 0.5)))), sr) * np.exp(-tb / d) * np.clip(tb / 0.001, 0, 1)
        _place(out, fade_edges(b, sr, 0.0003, 0.005), tt, sr, 0.25 * rng.uniform(0.3, 1.0), rng.uniform(-0.6, 0.6))
    for k in range(18):
        tt = 0.15 + rng.gamma(2.0, 0.15)
        if tt > 1.5:
            continue
        f0 = rng.uniform(1200, 2800)
        nb = secs(sr, 0.06)
        tb = tvec(nb, sr)
        b = _sweep(f0 * (1 + 0.6 * (1 - np.exp(-tb / 0.005))), sr) * np.exp(-tb / 0.012) * np.clip(tb / 0.0005, 0, 1)
        _place(out, fade_edges(b, sr, 0.0002, 0.005), tt, sr, 0.12 * math.exp(-(tt - 0.15) / 0.6), rng.uniform(-0.8, 0.8))
    return _room(out, sr, 0.25, 1.4)


@fx("sewer_ambience", trim=-6.0, loop=3.0)
def _sewer_ambience(sr, rng):
    """Sewer room tone (loop 3 s): low air rumble, faint hum, trickle, two distant echoing drips."""
    P = 3.0
    nP = secs(sr, P)
    t = tvec(nP, sr)
    y = np.zeros((nP, 2))
    for ch in range(2):
        y[:, ch] = 0.3 * _pnoise(nP, sr, rng, 30, 220, -4.5) + 0.12 * _pnoise(nP, sr, rng, 220, 1500, -3)
        babble = 0.5 + 0.5 * np.abs(_pnoise(nP, sr, rng, 4, 30))
        y[:, ch] += 0.05 * _pnoise(nP, sr, rng, 900, 3500) * babble
    y += pan(0.08 * np.sin(TAU * 55.0 * t) + 0.04 * np.sin(TAU * 110.0 * t), 0)
    ev = np.zeros((2 * nP, 2))
    for tt, f0, p in ((0.7, rng.uniform(900, 1200), -0.6), (2.1, rng.uniform(1100, 1500), 0.5)):
        nb = secs(sr, 0.12)
        tb = tvec(nb, sr)
        dr = _sweep(f0 * (1 + 0.7 * (1 - np.exp(-tb / 0.006))), sr) * np.exp(-tb / 0.022) * np.clip(tb / 0.0008, 0, 1)
        _place(ev, lp(fade_edges(dr, sr, 0.0002, 0.02), 3500, sr), tt, sr, 0.25, p)
    ev = _fold(ev, nP)
    ev = _circ(lambda z: 0.25 * z + 0.6 * reverb(z, sr, rt60=2.5, predelay=0.05, damp=0.6, seed=19), ev)
    return y + ev


@fx("power_surge")
def _power_surge(sr, rng):
    """Powers kicking in: rising electric hum and whine, crackles, a teal sparkle."""
    dur = 1.8
    out = _canvas(sr, dur + 0.7)
    n = secs(sr, dur)
    t = tvec(n, sr)
    u = t / dur
    f = 60 * rng.uniform(0.92, 1.08) * 4.0 ** (u ** 1.6)
    hum = tv_filter(0.6 * saw(f, n, sr, rng.random()) + 0.3 * pulse(2 * f, n, sr, 0.3, rng.random()),
                    300 + 3500 * u ** 2, sr, "lowpass", q=1.5, block=256)
    whine = _sweep(400 * rng.uniform(0.9, 1.1) * 4 ** (u ** 1.3), sr) * 0.15 * u
    env = np.clip(u / 0.15, 0, 1) * (0.4 + 0.6 * u) * np.clip((dur - t) / 0.05, 0, 1)
    _place(out, fade_edges((hum + whine) * env, sr, 0.005, 0.05), 0.0, sr)
    for k in range(60):
        tt = dur * rng.random() ** 0.5
        _place(out, _tick(sr, rng, 1500, 7000, rng.uniform(0.0005, 0.002), 0.012), tt, sr,
               0.25 * tt / dur * rng.uniform(0.3, 1.0), rng.uniform(-0.6, 0.6))
    for k, m in enumerate(sorted(rng.choice([84, 86, 88, 91, 93, 96, 98], 5, replace=False))):
        _place(out, _cut(inst_bell(int(m), 0.6, 0.7, sr), sr, 0.8, 0.2), dur - 0.15 + 0.05 * k, sr, 0.22,
               -0.5 + 0.25 * k)
    return _room(out, sr, 0.2, 1.0)


@fx("stinger_shock")
def _stinger_shock(sr, rng):
    """Orchestral shock hit ('struck by lightning' freeze): dissonant brass sfz,
    shrieking string cluster, timpani, boom, cymbal."""
    out = _canvas(sr, 2.4)
    lo = sr // 2
    b = inst_brass([36, 48, 55, 56, 61, 62], 0.35, lo, rng, peak_fc=3200, base_fc=700, attack=0.006,
                   release=0.9, fc_attack=0.025)
    _place(out, up2(b), 0.0, sr, 0.9)
    s = up2(inst_strings_sect([83, 84, 89, 90], 0.9, lo, rng, cutoff=5000, attack=0.012, release=0.6))
    trem = 1 - 0.4 * (0.5 + 0.5 * np.sin(TAU * 13 * tvec(len(s), sr)))
    _place(out, s * trem[:, None], 0.0, sr, 0.3)
    _place(out, dr_timpani(sr, rng, 43, 1.0, 1.6), 0.0, sr, 0.45)
    _place(out, dr_boom(sr, rng, 1.0, 2.0), 0.0, sr, 0.25)
    _place(out, dr_snare(sr, rng, 1.0), 0.0, sr, 0.4)
    _place(out, dr_crash(sr, rng, 1.0, 1.8), 0.0, sr, 0.35)
    return _room(out, sr, 0.3, 1.8)


@fx("lightning_zap", trim=-1.0)
def _lightning_zap(sr, rng):
    """Electric crack + buzzing crackle for the freeze flash (~0.9 s)."""
    dur = 0.9
    out = _canvas(sr, dur + 0.3)
    n = secs(sr, dur)
    t = tvec(n, sr)
    crack = bp(rng.standard_normal(n), 600, 7000, sr) * np.exp(-t / 0.012) * 0.6
    buzz = pulse(110 * (1 + 0.02 * smooth_noise(n, sr, 30, rng)), n, sr, 0.15) * (0.5 + 0.5 * np.abs(smooth_noise(n, sr, 45, rng)))
    buzz = np.tanh(3 * bp(buzz, 150, 4000, sr) * np.exp(-t / 0.3) * 0.5) * 0.6
    _place(out, fade_edges((crack + buzz) * np.clip(t / 0.0005, 0, 1), sr, 0.0002, 0.1), 0.0, sr)
    tt = 0.01
    while tt < dur - 0.1:
        _place(out, _tick(sr, rng, 1000, 7000, rng.uniform(0.0005, 0.002), 0.012), tt, sr,
               rng.uniform(0.2, 0.7) * math.exp(-tt / 0.35), rng.uniform(-0.6, 0.6))
        tt += rng.exponential(0.018)
    return _room(out, sr, 0.15, 0.6)


@fx("eye_open", trim=-3.0)
def _eye_open(sr, rng):
    """Waking up: muffled world swelling back, a soft dreamy low tone, ringing ears."""
    dur = 2.4
    n = secs(sr, dur)
    t = tvec(n, sr)
    u = t / dur
    out = np.zeros((n, 2))
    for ch in range(2):
        out[:, ch] = _norm(tv_filter(rng.standard_normal(n), 250 + 900 * np.clip(u / 0.7, 0, 1) ** 1.5, sr,
                                     "lowpass", q=0.7, block=256)) * 0.3
    env = np.clip(t / 0.7, 0, 1) ** 1.5 * np.clip((dur - t) / 0.9, 0, 1)
    out *= env[:, None]
    tone = (np.sin(TAU * 146.8 * t) + 0.6 * np.sin(TAU * 220.0 * t + 1) + 0.25 * np.sin(TAU * 293.7 * t)) * env * 0.35
    ring = (np.sin(TAU * 3950 * t) + 0.7 * np.sin(TAU * 4010 * t)) * np.clip(t / 0.15, 0, 1) * np.exp(-t / 0.9) * 0.06
    out += pan(tone, 0) + pan(ring, 0.1)
    return fade_edges(out, sr, 0.01, 0.2)


@fx("sonar_ping")
def _sonar_ping(sr, rng):
    """The new sense: deep soft 'whoom', a cool ping with two echoes, glassy shimmer."""
    out = _canvas(sr, 2.4)
    n = secs(sr, 1.6)
    t = tvec(n, sr)
    ph = TAU * np.cumsum((58 + 30 * np.exp(-t / 0.12)) * rng.uniform(0.95, 1.05)) / sr
    whoom = (np.sin(ph) + 0.9 * np.sin(2 * ph) + 0.45 * np.sin(3 * ph)) * np.clip(t / 0.05, 0, 1) ** 2 * np.exp(-t / 0.45)
    air = _norm(lp(rng.standard_normal(n), 600, sr)) * np.clip(t / 0.08, 0, 1) * np.exp(-t / 0.25) * 0.15
    _place(out, fade_edges(whoom + air, sr, 0.002, 0.1), 0.0, sr, 0.9)
    for i, (tt, g) in enumerate(((0.06, 1.0), (0.42, 0.45), (0.78, 0.2))):
        nb = secs(sr, 1.0)
        tb = tvec(nb, sr)
        p = (np.sin(TAU * 1318.5 * tb) + 0.6 * np.sin(TAU * 1322.0 * tb) + 0.15 * np.sin(TAU * 2637 * tb)) \
            * np.exp(-tb / 0.35) * np.clip(tb / 0.004, 0, 1)
        _place(out, fade_edges(p, sr, 0.001, 0.05), tt, sr, 0.4 * g, (-0.4, 0.4, -0.2)[i])
    for k, m in enumerate((88, 95, 100, 104)):
        _place(out, _cut(inst_bell(m, 0.9, 0.5, sr), sr, 1.2), 0.1 + 0.07 * k, sr, 0.06, -0.5 + 0.33 * k)
    return _room(out, sr, 0.35, 2.0)


@fx("squish", trim=-1.0)
def _squish(sr, rng):
    """Wet step: muffled thump, a squelch sweep, a little suction pop."""
    out = _canvas(sr, 0.5)
    n = secs(sr, 0.3)
    t = tvec(n, sr)
    k = rng.uniform(0.85, 1.15)
    thump = _sweep((95 + 50 * np.exp(-t / 0.01)) * k, sr, rng.uniform(0, TAU)) * np.exp(-t / rng.uniform(0.03, 0.05)) \
        * rng.uniform(0.6, 1.0)
    wet = tv_filter(rng.standard_normal(n), (450 + 1300 * (1 - np.exp(-t / rng.uniform(0.035, 0.07)))) * k, sr,
                    "bandpass", q=4.0, stages=1, block=64)
    wet = _norm(wet) * 0.3 * np.exp(-t / 0.07) * (0.6 + 0.4 * np.abs(smooth_noise(n, sr, 90, rng)))
    _place(out, fade_edges((0.7 * thump + wet) * np.clip(t / 0.003, 0, 1), sr, 0.0005, 0.03), 0.0, sr)
    nb = secs(sr, 0.04)
    tb = tvec(nb, sr)
    pop = _sweep((600 + 700 * tb / 0.04) * rng.uniform(0.8, 1.2), sr) * np.exp(-tb / 0.01)
    _place(out, fade_edges(pop, sr, 0.0005, 0.005), 0.2 + rng.uniform(-0.06, 0.06), sr, 0.3)
    return _room(out, sr, 0.15, 0.5)


@fx("sad_chime", trim=-3.0)
def _sad_chime(sr, rng):
    """Soft descending minor chime (E6 C6 A5)."""
    out = _canvas(sr, 2.4)
    for i, m in enumerate((88, 84, 81)):
        mm = m + rng.normal(0, 0.06)
        tt = 0.22 * i + rng.uniform(-0.015, 0.015) * (i > 0)
        _place(out, _cut(inst_bell(mm, 1.6, (0.7 - 0.1 * i) * rng.uniform(0.85, 1.0), sr), sr, 2.0 - 0.2 * i, 0.4),
               tt, sr, 0.45, 0.3 - 0.3 * i)
        _place(out, _cut(inst_bell(mm - 12, 1.6, 0.4, sr, kind="fm"), sr, 1.8 - 0.2 * i, 0.4), tt, sr, 0.15,
               0.3 - 0.3 * i)
    return _room(out, sr, 0.35, 1.6)


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
_NEW_ALIASES = {   # TIREDNESS (never overrides an alias above)
    "bang": "door_bang", "pound": "door_bang", "door": "door_bang", "door_pound": "door_bang",
    "knuckle_knock": "knock", "door_knock": "knock", "knock_knock": "knock",
    "smash": "glass_smash", "glass": "glass_smash", "shatter": "glass_smash", "window_smash": "glass_smash",
    "window_break": "glass_smash", "glass_big": "glass_crash_big", "window_crash": "glass_crash_big",
    "crash_through": "glass_crash_big", "big_glass": "glass_crash_big",
    "rumble": "house_rumble", "quake": "house_rumble", "house_shake": "house_rumble",
    "body": "body_thud", "body_fall": "body_thud", "fall_thud": "body_thud", "wall_thud": "body_thud",
    "head_ceiling": "ceiling_thud", "ceiling": "ceiling_thud", "head_bonk": "bonk", "conk": "bonk",
    "claws": "scratch_wood", "wood_scratch": "scratch_wood", "scrabble": "scratch_wood",
    "patter": "scurry", "skitter": "scurry", "scamper": "scurry", "squeak": "critter_squeak",
    "eek": "critter_squeak", "hiss_small": "critter_hiss", "thing_hiss": "critter_hiss",
    "bite": "chomp", "nom": "chomp", "chomp_bite": "chomp", "snap": "chomp",
    "hiss_big": "creature_hiss", "monster_hiss": "creature_hiss", "snarl": "creature_snarl",
    "growl": "creature_snarl", "chitter": "creature_chitter", "chirp": "creature_chitter",
    "clicks": "creature_chitter", "purr": "creature_purr", "coo": "creature_chirp_sad",
    "sad_chirp": "creature_chirp_sad", "whimper": "creature_chirp_sad",
    "pant": "dog_pant", "panting": "dog_pant", "woof": "dog_woof", "bark": "dog_woof",
    "creak": "cage_creak", "cage_open": "cage_creak", "cage": "cage_rattle", "rattle": "cage_rattle",
    "latch": "latch_click", "unlatch": "latch_click", "siren": "alarm", "klaxon": "alarm", "alert": "alarm",
    "run": "footsteps_run", "running": "footsteps_run", "footsteps": "footsteps_run", "steps": "footsteps_run",
    "step": "footstep", "van": "van_door", "van_slam": "van_door", "sliding_door": "van_door",
    "exhale": "sigh", "anc": "anc_on", "noise_cancel": "anc_on", "headphones": "anc_on", "headphones_on": "anc_on",
    "game": "game_blips", "8bit": "game_blips", "blips": "game_blips", "chiptune": "game_music_leak",
    "leak": "game_music_leak", "headphone_leak": "game_music_leak", "zip": "smear_zip",
    "teleport": "smear_zip", "smear": "smear_zip", "tap": "tap_tap", "shoulder_tap": "tap_tap",
    "toe_tap": "foot_tap", "foot": "foot_tap", "rustle": "cloth_rustle", "cloth": "cloth_rustle",
    "sweater": "cloth_rustle", "drawer": "drawer_open", "plate": "plate_clink", "clink": "plate_clink",
    "dish": "plate_clink", "chair": "chair_creak", "water_drip": "drip", "drop": "drip", "splash": "water_splash",
    "sewer": "sewer_ambience", "ambience": "sewer_ambience", "room_tone": "sewer_ambience",
    "power": "power_surge", "surge": "power_surge", "powerup": "power_surge", "power_up": "power_surge",
    "shock": "stinger_shock", "stinger": "stinger_shock", "orchestra_hit": "stinger_shock",
    "electric": "lightning_zap", "crackle": "lightning_zap", "electrocute": "lightning_zap",
    "zap_lightning": "lightning_zap", "mouse": "mouse_click", "wind": "wind_fall", "falling": "wind_fall",
    "fall": "wind_fall", "impact": "impact_heavy", "land": "impact_heavy", "slam": "impact_heavy",
    "crash": "impact_heavy", "wake": "eye_open", "awaken": "eye_open", "tinnitus": "eye_open",
    "ears_ringing": "eye_open", "sonar": "sonar_ping", "ping": "sonar_ping", "sense": "sonar_ping",
    "squelch": "squish", "wet_step": "squish", "hum": "pod_hum", "pods": "pod_hum",
    "machine_hum": "pod_hum", "sad_ding": "sad_chime", "chime_sad": "sad_chime",
}
for _k, _v in _NEW_ALIASES.items():
    if _k not in ALIASES and _k not in _FX:
        ALIASES[_k] = _v


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


def _circ(fn, y):
    """Apply a causal process (IIR filter, reverb) circularly to one loop period."""
    n = len(y)
    out = fn(np.concatenate([y, y, y], axis=0))
    return out[n: 2 * n]


def _fold(y, n):
    """Wrap a 2-period event buffer onto one period (tails ring into the next loop)."""
    y = np.asarray(y, dtype=float)
    out = y[:n].copy()
    k = 1
    while k * n < len(y):
        seg = y[k * n: (k + 1) * n]
        out[: len(seg)] += seg
        k += 1
    return out


def _loop_clip(y, sr, P):
    nP = secs(sr, P)
    y = stereoize(np.asarray(y, dtype=float))
    y = _fold(y, nP) if len(y) > nP else np.pad(y, ((0, nP - len(y)), (0, 0)))
    y = y - y.mean(axis=0, keepdims=True)
    y = _circ(lambda z: hp(z, 25, sr, 2), y)
    F = min(secs(sr, LOOP_XF), nP // 4)
    w = 0.5 - 0.5 * np.cos(np.pi * np.arange(F) / F)
    y = np.concatenate([y, y[:F]], axis=0)
    y[:F] *= w[:, None]
    y[nP:] *= (1.0 - w)[:, None]
    return y


def loop_events(name, t0, t1, gain_db=0.0, pan=0.0):
    """SFX() entries that tile a loopable effect over [t0, t1) (scene-local s)."""
    key = resolve(name)
    P = LOOPS[key]
    out, k = [], 0
    while t0 + k * P < t1 - 1e-6:
        out.append((round(t0 + k * P, 6), key, gain_db, pan))
        k += 1
    return out


@lru_cache(maxsize=256)
def _render_cached(name, sr, seed):
    fn, trim = _FX[name]
    if name in LOOPS:      # seed-independent so repeated placements tile seamlessly
        y = _loop_clip(fn(sr, _rng(name, 0)), sr, LOOPS[name])
    else:
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
