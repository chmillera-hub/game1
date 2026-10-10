"""New music for the assembly video."""
import numpy as np
from audio_lib import SR, tt, mtof, lp, hp, bp, peak, place, norm, reverb, rng, additive, VOW_AH
from music import (seq, CH, sum_inst, pizz, glock, ep, upright, strings, choir, piano, kick, snare, clap, hat, shaker,
                   tuba, sub808, brass_stab, arp_pluck, square_lead, track_creator, track_muzak, track_outro, track_tension,
                   supersaw)


def timpani(f, dur):
    t = tt(max(dur, 1.2))
    x = np.sin(2 * np.pi * f * (1 + 0.02 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.6)
    x += 0.5 * np.sin(2 * np.pi * f * 1.5 * t) * np.exp(-t / 0.3)
    x += lp(rng(int(f)).standard_normal(len(t)), 400) * np.exp(-t / 0.03)
    return x


def track_epic(dur=12.0):
    """Overblown 'sacrificial' choir chant for the gym bros carrying Carter."""
    b = 60 / 132
    out = np.zeros(int((dur + 3) * SR))
    prog = [("Dm_", 38), ("Bb", 34), ("C", 36), ("Dm_", 38)]
    nb = int(dur / (4 * b)) + 1
    for i in range(nb):
        t0 = i * 4 * b
        name, bass = prog[i % 4]
        c = CH[name] if name != "Dm_" else [50, 53, 57]
        place(out, sum_inst(choir, [m + 12 for m in c], 4 * b), t0, 0.06)
        for k in range(4):
            place(out, timpani(float(mtof(bass)), b), t0 + k * b, 0.35 if k % 2 == 0 else 0.22)
        seq(out, strings, [(k * 0.5, c[k % 3] + 24, 0.45) for k in range(8)], t0, b, 0.05)
        place(out, kick(1.2), t0, 0.5)
    return out


def track_playful(dur=30.0):
    """Light pizzicato + glock for the role play."""
    b = 60 / 112
    out = np.zeros(int((dur + 2) * SR))
    prog = ["C", "Am", "F", "G7"]
    mel = [[(0, 72, .5), (.5, 76, .5), (1, 79, 1), (2.5, 77, .5), (3, 76, 1)],
           [(0, 72, .5), (.5, 69, .5), (1, 72, 1), (2, 74, .5), (2.5, 72, .5), (3, 71, 1)]]
    nb = int(dur / (4 * b)) + 1
    for i in range(nb):
        t0 = i * 4 * b
        c = CH[prog[i % 4]]
        seq(out, pizz, [(k, c[k % len(c)] - 12, 0.5) for k in range(4)], t0, b, 0.35)
        seq(out, pizz, [(k + 0.5, c[(k + 1) % len(c)], 0.4, 0.6) for k in range(4)], t0, b, 0.25)
        seq(out, glock, mel[i % 2], t0, b, 0.12)
    return out


def track_funk(dur=24.0):
    """Carter killing it on stage."""
    b = 60 / 108
    out = np.zeros(int((dur + 2) * SR))
    prog = [("Dm7", 38), ("Gm7", 43), ("Dm7", 38), ("A7", 45)]
    nb = int(dur / (4 * b)) + 1
    for i in range(nb):
        t0 = i * 4 * b
        name, bass = prog[i % 4]
        c = CH[name]
        for k in range(4):
            place(out, kick(0.8), t0 + k * b, 0.5 if k % 2 == 0 else 0.3)
            for s in range(4):
                place(out, hat(False, k * 4 + s), t0 + k * b + s * b / 4, 0.05 if s % 2 else 0.08)
        place(out, snare(), t0 + b, 0.3)
        place(out, snare(), t0 + 3 * b, 0.3)
        bl = [(0, bass, .4), (.75, bass, .25), (1, bass + 12, .3), (1.75, bass + 10, .25), (2, bass + 7, .4), (2.75, bass + 5, .25), (3.5, bass + 3, .4)]
        seq(out, upright, bl, t0, b, 0.55)
        for st in (0.5, 1.75, 2.5, 3.75):
            place(out, sum_inst(ep, c, b * 0.25), t0 + st * b, 0.1)
        if i % 2 == 1:
            place(out, sum_inst(brass_stab, [m + 12 for m in c], b * 0.5), t0 + 3 * b, 0.07)
    return out


def track_sad_piano(dur=24.0):
    """Hollow, lonely piano for the empty solo act."""
    b = 60 / 72
    out = np.zeros(int((dur + 4) * SR))
    prog = [("Am", 45), ("F", 41), ("C", 48), ("E7", 40)]
    nb = int(dur / (4 * b)) + 1
    for i in range(nb):
        t0 = i * 4 * b
        name, bass = prog[i % 4]
        c = CH[name]
        seq(out, piano, [(0, bass - 12, 3.5)], t0, b, 0.3)
        seq(out, piano, [(k, c[k % len(c)] + 12, 1.2, 0.6) for k in range(4)], t0, b, 0.12)
        if i % 2 == 0:
            seq(out, piano, [(0.5, c[2] + 24, 1.5, 0.5), (2.5, c[1] + 24, 1.5, 0.4)], t0, b, 0.08)
    return norm(reverb(out, 2.2, 0.35)[: len(out)])


def track_sincere(dur=20.0):
    """Warm, sincere strings for the heckler moment and the knowing look."""
    b = 60 / 76
    out = np.zeros(int((dur + 3) * SR))
    prog = [("F", 41), ("C", 36), ("Dm", 38), ("Bb", 34)]
    nb = int(dur / (4 * b)) + 1
    for i in range(nb):
        t0 = i * 4 * b
        name, bass = prog[i % 4]
        c = CH[name]
        place(out, sum_inst(strings, [m for m in c] + [c[0] + 12], 4 * b), t0, 0.08)
        seq(out, strings, [(0, bass - 12, 3.8)], t0, b, 0.12)
        seq(out, piano, [(k * 0.5, c[k % 3] + 12, 0.6, 0.5) for k in range(8)], t0, b, 0.08)
    return norm(reverb(out, 1.8, 0.25)[: len(out)])


TRACKS2 = {
    "office": track_creator, "assembly": track_muzak, "epic": track_epic, "playful": track_playful, "funk": track_funk,
    "sad_piano": track_sad_piano, "sincere": track_sincere, "outro": track_outro, "tension": track_tension,
}
