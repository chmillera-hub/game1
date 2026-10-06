"""Reverent music beds."""
import numpy as np

import audio as A
from audio import SR, t_, env, lp, noise, norm, note_f


def music_hymn(total):
    """Slow organ-like chords."""
    out = np.zeros(int((total + 8) * SR))
    prog = [[48, 55, 64, 67], [53, 57, 65, 69], [55, 59, 62, 67], [48, 52, 60, 67],
            [57, 60, 64, 69], [53, 60, 65, 69], [55, 62, 65, 71], [48, 55, 64, 72]]
    d = 4.0
    tt = 0.0
    k = 0
    while tt < total + 1:
        ch = prog[k % len(prog)]
        tv = t_(d + 1.2)
        x = sum(np.sin(2 * np.pi * note_f(n) * tv) + 0.4 * np.sin(4 * np.pi * note_f(n) * tv)
                + 0.15 * np.sin(6 * np.pi * note_f(n) * tv) for n in ch)
        x *= env(len(tv), 0.7, 1.2) * (1 + 0.05 * np.sin(2 * np.pi * 5 * tv))
        i = int(tt * SR)
        out[i:i + len(x)] += x[:max(0, len(out) - i)] * 0.2
        tt += d
        k += 1
    return norm(lp(out, 2500), 1.0)[:int(total * SR)]


def music_rain(total):
    t = t_(total)
    x = lp(noise(total), 3000)[:len(t)] * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))
    return norm(x, 1.0)


A.MOODS.update(hymn=music_hymn, rainamb=music_rain)
