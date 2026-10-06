"""Extra sounds and music for Redditor Existentialist."""
import numpy as np

import audio as A
from audio import SR, t_, env, lp, hp, bp, noise, glide, norm, note_f

rng = np.random.default_rng(21)


def typing(d=2.4):
    out = np.zeros(int(d * SR))
    k = 0.0
    while k < d - 0.05:
        dd = 0.03
        c = bp(noise(dd), 1500, 6000) * np.exp(-t_(dd) * 160)
        i = int(k * SR)
        out[i:i + len(c)] += c * rng.uniform(0.5, 1.0)
        k += rng.uniform(0.06, 0.16)
    return norm(out, 0.35)


def slap():
    d = 0.25
    t = t_(d)
    x = bp(noise(d), 800, 5000) * np.exp(-t * 40) + np.sin(2 * np.pi * 300 * t) * np.exp(-t * 50) * 0.4
    return norm(x, 0.8)


def poof():
    d = 0.8
    x = lp(noise(d), 2500) * np.exp(-t_(d) * 6) * env(int(d * SR), 0.02)
    return norm(x, 0.5)


def slam():
    d = 1.0
    t = t_(d)
    x = np.sin(2 * np.pi * (60 + 40 * np.exp(-t * 15)) * t) * np.exp(-t * 6) + lp(noise(d), 600) * np.exp(-t * 14)
    return norm(x, 0.9)


def tick():
    d = 0.05
    x = bp(noise(d), 2000, 6000) * np.exp(-t_(d) * 120)
    return norm(x, 0.4)


def ticking(d=6.0):
    out = np.zeros(int(d * SR))
    for k in range(int(d)):
        c = tick()
        i = int(k * SR)
        out[i:i + len(c)] += c
    return norm(out, 0.4)


def cut_clap():
    d = 0.3
    x = hp(noise(d), 1500) * np.exp(-t_(d) * 30)
    return norm(x, 0.8)


def wallsink():
    d = 1.4
    t = t_(d)
    x = lp(noise(d), 300) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * env(len(t), 0.1, 0.5)
    return norm(x, 0.6)


def boing():
    d = 0.6
    t = t_(d)
    f = 220 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    return norm(x, 0.4)


for name, fn in dict(typing=typing, slap=slap, poof=poof, slam=slam, tick=tick, ticking=ticking,
                     cutclap=cut_clap, wallsink=wallsink, boing=boing).items():
    A.SFX[name] = fn


def music_lofi(total):
    """Sleepy lo-fi: soft Rhodes-ish chords, dusty kick and snare, vinyl hiss."""
    out = np.zeros(int((total + 4) * SR))
    bpm = 72
    beat = 60 / bpm
    prog = [[50, 53, 57, 60], [55, 59, 62, 65], [48, 52, 55, 59], [45, 48, 52, 55]]
    tt = 0.0
    k = 0
    while tt < total + 1:
        ch = prog[k % 4]
        d = beat * 4 + 0.5
        tv = t_(d)
        c = sum(np.sin(2 * np.pi * note_f(n) * tv) * (1 + 0.3 * np.sin(2 * np.pi * 5 * tv)) for n in ch)
        c *= np.exp(-tv * 0.6) * env(len(tv), 0.02, 0.4) * 0.12
        i = int(tt * SR)
        out[i:i + len(c)] += c[:max(0, len(out) - i)]
        for b in range(4):
            j = int((tt + b * beat) * SR)
            if b % 2 == 0:
                dk = 0.3
                tk = t_(dk)
                kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 10)
                out[j:j + len(kick)] += kick[:max(0, len(out) - j)] * 0.5
            else:
                ds = 0.25
                sn = lp(noise(ds), 3000) * np.exp(-t_(ds) * 18) * 0.25
                out[j:j + len(sn)] += sn[:max(0, len(out) - j)]
        tt += beat * 4
        k += 1
    out += lp(noise(len(out) / SR), 4000)[:len(out)] * 0.015
    return norm(lp(out, 3500), 1.0)[:int(total * SR)]


def music_void(total):
    t = t_(total)
    x = sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate((55, 55 * 1.498, 110.3)))
    x *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.04 * t)
    x += lp(noise(total), 200)[:len(t)] * 0.6
    return norm(x, 1.0)


def music_hope(total):
    return A.music_dream(total, [[53, 57, 60, 64], [55, 59, 62, 67], [57, 60, 64, 69], [52, 55, 60, 64]], 1.4)


A.MOODS.update(lofi=music_lofi, void=music_void, hope=music_hope)
