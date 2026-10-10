"""New SFX for the assembly video (mono 48 kHz)."""
import numpy as np
from audio_lib import (SR, tt, rng, lp, hp, bp, peak, place, norm, fade, reverb, phase_of, additive, smooth_noise,
                       laugh_syllables, vocal, VOW_AH, VOW_EH, VOW_EE, VOW_OO, SFX, fart)
import audio_lib as A


def crowd_laugh(dur=3.0, n=26, size=1.0, seed=200):
    """A gym full of kids laughing: many small laughs + murmur, in a big room."""
    r = rng(seed)
    out = np.zeros(int((dur + 1.0) * SR))
    for i in range(n):
        f0 = r.uniform(190, 420)
        ns = int(r.integers(4, 11))
        rate = r.uniform(5.5, 9.0)
        f0s = [f0 * (1 - 0.03 * k) for k in range(ns)]
        v = [VOW_AH, VOW_EH, VOW_EE][i % 3]
        x = laugh_syllables(ns, f0s, rate=rate, vowel=v, breath=r.uniform(0.3, 0.6), dec=0.09, seed=seed + i)
        place(out, norm(x) * r.uniform(0.3, 1.0), r.uniform(0, dur * 0.35))
    murmur = bp(r.standard_normal(len(out)), 300, 3000) * 0.15
    t = np.arange(len(out)) / SR
    env = np.minimum(t / 0.15, 1) * np.exp(-np.maximum(t - dur * 0.55, 0) / (dur * 0.3))
    y = (out + murmur) * env
    return norm(reverb(y, 1.6, 0.3)[: len(out)], 0.85 * size)


def crowd_murmur(dur=2.5, seed=210, gasp=False):
    r = rng(seed)
    out = np.zeros(int((dur + 0.5) * SR))
    for i in range(14):
        L = r.uniform(0.4, 1.2)
        tl = tt(L)
        f0 = r.uniform(150, 320) * (1 + 0.1 * np.sin(2 * np.pi * r.uniform(2, 5) * tl))
        venv = np.sin(np.pi * tl / L) ** 1.5 * (0.6 + 0.4 * np.sin(2 * np.pi * r.uniform(4, 7) * tl))
        x = vocal(f0, [VOW_AH, VOW_EH, VOW_OO][i % 3], breath=0.4, voiced_env=venv, seed=seed + i)
        place(out, lp(norm(x), 1800) * r.uniform(0.3, 0.8), r.uniform(0, dur - L))
    if gasp:
        place(out, A.sfx_gasp(), 0.0, 0.8)
    return norm(reverb(out, 1.4, 0.3)[: len(out)], 0.6)


def applause(dur=3.0, seed=220):
    r = rng(seed)
    out = np.zeros(int((dur + 0.6) * SR))
    t = 0.0
    while t < dur:
        dens = 1.0 - 0.6 * max(0, (t - dur * 0.5) / (dur * 0.5))
        L = int(0.025 * SR)
        tl = np.arange(L) / SR
        c = bp(r.standard_normal(L), r.uniform(800, 2500), 7000) * np.exp(-tl / 0.006)
        place(out, c, t, r.uniform(0.3, 1.0) * dens)
        t += r.uniform(0.002, 0.012) / max(dens, 0.2)
    return norm(reverb(out, 1.2, 0.25)[: len(out)], 0.6)


def crickets(dur=3.0, seed=230):
    out = np.zeros(int((dur + 0.3) * SR))
    t = 0.0
    k = 0
    while t < dur:
        for j in range(3):
            tl = tt(0.035)
            ch = np.sin(2 * np.pi * 4600 * tl) * np.sin(np.pi * tl / 0.035) * (0.7 + 0.3 * np.sin(2 * np.pi * 300 * tl))
            place(out, ch, t + j * 0.05, 0.5)
        t += 0.55 + 0.1 * np.sin(k)
        k += 1
    return norm(out, 0.35)


def pig_squeal(dur=2.4, seed=240):
    """Panicked pig-like squeals (cartoon)."""
    r = rng(seed)
    out = np.zeros(int((dur + 0.4) * SR))
    t = 0.0
    while t < dur:
        L = r.uniform(0.35, 0.7)
        tl = tt(L)
        f = (900 + 500 * np.sin(np.pi * tl / L)) * (1 + 0.04 * np.sin(2 * np.pi * 24 * tl))
        venv = np.minimum(tl / 0.02, 1) * np.clip((L - tl) / 0.08, 0, 1)
        x = vocal(f, [(1200, 4, 1.0), (2600, 5, 0.6), (3800, 6, 0.3)], breath=0.5, voiced_env=venv, seed=int(r.integers(1000)), tilt=1.0)
        place(out, np.tanh(2.5 * norm(x)), t, r.uniform(0.6, 1.0))
        t += L + r.uniform(0.02, 0.12)
    return norm(out, 0.75)


def cough(seed=250):
    out = np.zeros(int(0.9 * SR))
    for st, g in ((0.0, 1.0), (0.32, 0.7)):
        t = tt(0.25)
        nz = rng(seed).standard_normal(len(t))
        y = peak(nz, 600, 2) + 0.6 * peak(nz, 1500, 3)
        env = np.minimum(t / 0.01, 1) * np.exp(-t / 0.07)
        place(out, y * env, st, g)
    return norm(reverb(out, 1.4, 0.35)[: len(out)], 0.6)


def clock_ticks(dur=8.0):
    out = np.zeros(int((dur + 0.2) * SR))
    for k in range(int(dur)):
        tl = tt(0.03)
        f = 3200 if k % 2 == 0 else 2400
        place(out, np.sin(2 * np.pi * f * tl) * np.exp(-tl / 0.006), k * 1.0, 0.5)
    return norm(out, 0.4)


def rimshot():
    out = np.zeros(int(1.6 * SR))
    from music import snare, hat
    place(out, snare(), 0.0, 0.7)
    place(out, snare(), 0.16, 0.8)
    t = tt(1.2)
    cym = hp(rng(9).standard_normal(len(t)), 5000) * np.exp(-t / 0.4)
    place(out, cym, 0.42, 0.6)
    return norm(out, 0.8)


def door_creak(seed=260):
    t = tt(1.2)
    f = 180 + 120 * np.sin(np.pi * t / 1.2) + 30 * smooth_noise(len(t), 12, seed)
    x = additive(f, 30, lambda k: 1 / k) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 35 * t)))
    x = bp(x, 400, 3000) * np.sin(np.pi * t / 1.2)
    return norm(x, 0.45)


def footsteps(n=6, gap=0.35, seed=270):
    out = np.zeros(int((n * gap + 0.5) * SR))
    for k in range(n):
        tl = tt(0.12)
        s = lp(rng(seed + k).standard_normal(len(tl)), 900) * np.exp(-tl / 0.03)
        s += np.sin(2 * np.pi * 90 * tl) * np.exp(-tl / 0.04)
        place(out, s, k * gap, 0.8 if k % 2 == 0 else 0.6)
    return norm(reverb(out, 1.0, 0.25)[: len(out)], 0.6)


def tiny_beep():
    t = tt(0.25)
    return norm(np.sin(2 * np.pi * 1760 * t) * np.minimum(t / 0.005, 1) * np.clip((0.25 - t) / 0.03, 0, 1), 0.4)


def sparkle():
    out = np.zeros(int(2.2 * SR))
    for i, m in enumerate([84, 88, 91, 96, 100]):
        place(out, A.bell(float(A.mtof(m)), 1.2), i * 0.07, 0.4)
    return norm(reverb(out, 1.5, 0.3)[: len(out)], 0.5)


def mic_feedback():
    t = tt(0.7)
    f = 2600 + 200 * t
    return norm(np.sin(2 * np.pi * phase_of(f)) * np.minimum(t / 0.2, 1) * np.clip((0.7 - t) / 0.05, 0, 1), 0.3)


SFX2 = {
    "laugh_small": lambda: crowd_laugh(1.8, 12, 0.7, 201), "laugh_big": lambda: crowd_laugh(3.2, 34, 1.0, 202),
    "laugh_huge": lambda: crowd_laugh(4.0, 46, 1.0, 203), "laugh_hollow": lambda: A.lp(crowd_laugh(2.6, 24, 0.8, 204), 1800),
    "murmur": crowd_murmur, "murmur_gasp": lambda: crowd_murmur(2.0, 211, True), "applause": applause,
    "crickets": crickets, "pig_squeal": pig_squeal, "cough": cough, "clock_ticks": clock_ticks, "rimshot": rimshot,
    "door_creak": door_creak, "footsteps": footsteps, "tiny_beep": tiny_beep, "sparkle": sparkle, "mic_feedback": mic_feedback,
    "giggle_few": lambda: crowd_laugh(1.0, 5, 0.5, 205),
}
ALL_SFX = dict(SFX)
ALL_SFX.update(SFX2)
