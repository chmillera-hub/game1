"""Voices, music cues and sound effects for DO NOT DISTURB."""
import numpy as np
from toon.audio import (SR, T, env_adsr, expdecay, saw, sq, tri, lp, hp, bp, noise, reverb, mtof, place, ks_pluck,
                        epiano, kick, snare, hat, crash, normalize, RNG, _ff)

VOICES = {
    "tired": dict(voice="am_fenrir", speed=0.86, pitch=0.93, gain=1.0),
    "emb": dict(voice="am_puck", speed=1.14, pitch=1.12, gain=1.0),
    "boss": dict(voice="bm_lewis", speed=0.92, pitch=0.9, gain=1.0),
    "aide": dict(voice="af_sarah", speed=1.0, pitch=1.0, gain=0.95),
    "guard": dict(voice="am_eric", speed=0.88, pitch=0.9, gain=1.0),
    "recept": dict(voice="af_nicole", speed=1.0, pitch=1.05, gain=0.95),
    "sci": dict(voice="af_kore", speed=1.05, pitch=1.0, gain=0.95),
    "narr2": dict(voice="af_heart", speed=1.02, pitch=1.0, gain=1.0),
}


# ------------------------------------------------------------------------------------------ music
def _chord(root, kind):
    return {"m7": [root, root + 3, root + 7, root + 10], "M7": [root, root + 4, root + 7, root + 11],
            "7": [root, root + 4, root + 7, root + 10], "m": [root, root + 3, root + 7],
            "M": [root, root + 4, root + 7]}[kind]


def music_lofi(dur):
    bpm = 80
    beat = 60 / bpm
    bar = beat * 4
    prog = [(57, "m7"), (62, "m7"), (55, "7"), (60, "M7")]
    n = int(dur * SR) + 2 * SR
    buf = np.zeros(n)
    k_ = kick(0.3)
    s_ = lp(snare(0.2), 4000)
    for b in range(int(dur / bar) + 2):
        t0 = b * bar
        root, kind = prog[b % 4]
        for m in _chord(root, kind):
            place(buf, epiano(mtof(m), bar * 1.0, 0.4), t0, 0.12)
            place(buf, epiano(mtof(m), bar * 0.5, 0.25), t0 + beat * 2.5, 0.08)
        place(buf, epiano(mtof(root - 24), bar, 0.7), t0, 0.35)
        for k in range(4):
            if k in (0,):
                place(buf, k_, t0 + k * beat, 0.7)
            if k == 2:
                place(buf, k_, t0 + k * beat + beat * 0.5, 0.5)
            if k in (1, 3):
                place(buf, s_, t0 + k * beat, 0.35)
            place(buf, hat(), t0 + k * beat + beat * 0.5 + 0.02, 0.25)
    crackle = (RNG.random(len(buf)) < 0.0004) * RNG.uniform(-1, 1, len(buf))
    buf += lp(crackle, 3000) * 0.4
    buf = lp(buf, 6000)
    return buf[: int(dur * SR)]


def music_lofi_muffled(dur):
    return lp(music_lofi(dur), 500, 4) * 1.6


def music_sneak(dur):
    """Tiptoe pizzicato: creeping minor line, plucked."""
    bpm = 108
    beat = 60 / bpm
    line_ = [45, None, 48, None, 49, None, 50, None, 51, 52, None, 45, 44, None, 45, None]
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    k = 0
    tt = 0.0
    while tt < dur:
        m = line_[k % len(line_)]
        if m is not None:
            place(buf, ks_pluck(mtof(m), 0.3, 0.7, 0.99), tt, 0.7)
            place(buf, ks_pluck(mtof(m + 12), 0.2, 0.9, 0.99), tt, 0.25)
        if k % 4 == 0:
            place(buf, bp(noise(int(0.04 * SR)), 1500, 4000) * expdecay(int(0.04 * SR), 0.01), tt, 0.35)
        tt += beat / 2
        k += 1
    return buf[: int(dur * SR)]


def music_panic(dur):
    bpm = 168
    beat = 60 / bpm
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    tt = 0.0
    k = 0
    motif = [57, 58, 57, 60, 57, 61, 57, 62]
    while tt < dur:
        m = motif[k % len(motif)] + 12 * ((k // 16) % 2)
        x = saw(mtof(m), T(beat / 2 * 0.9)) * env_adsr(int(beat / 2 * 0.9 * SR), 0.005, 0.05, 0.6, 0.04)
        place(buf, lp(x, 2500), tt, 0.16)
        if k % 2 == 0:
            place(buf, kick(0.2), tt, 0.6)
        if k % 4 == 2:
            place(buf, snare(0.12), tt, 0.4)
        tt += beat / 2
        k += 1
    trem = lp(saw(mtof(45), T(dur + 1)) + saw(mtof(52), T(dur + 1)), 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 12 * T(dur + 1)))
    buf[: len(trem)] += trem[: len(buf)] * 0.05
    return buf[: int(dur * SR)]


def music_muzak(dur):
    bpm = 104
    beat = 60 / bpm
    bar = beat * 4
    prog = [(60, "M7"), (57, "m7"), (62, "m7"), (55, "7")]
    n = int(dur * SR) + 2 * SR
    buf = np.zeros(n)
    for b in range(int(dur / bar) + 2):
        t0 = b * bar
        root, kind = prog[b % 4]
        for off in (0, beat * 1.5, beat * 3):
            for m in _chord(root, kind):
                place(buf, epiano(mtof(m), beat * 1.2, 0.35), t0 + off, 0.07)
        place(buf, ks_pluck(mtof(root - 24), 0.6, 0.3), t0, 0.5)
        place(buf, ks_pluck(mtof(root - 17), 0.6, 0.3), t0 + beat * 2, 0.4)
        for k in range(8):
            place(buf, hat(0.02), t0 + k * beat / 2, 0.12)
        mel = [72, 74, 76, 79]
        place(buf, np.sin(2 * np.pi * mtof(mel[b % 4]) * T(beat * 1.8)) * env_adsr(int(beat * 1.8 * SR), 0.05, 0.2, 0.6, 0.3),
              t0 + beat, 0.08)
    return (buf + 0.2 * reverb(buf, 1.2)[: len(buf)])[: int(dur * SR)]


def music_spy(dur):
    bpm = 96
    beat = 60 / bpm
    walk = [40, 43, 45, 46, 47, 46, 45, 43]
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    tt, k = 0.0, 0
    while tt < dur:
        place(buf, ks_pluck(mtof(walk[k % 8]), 0.5, 0.25, 0.995), tt, 0.8)
        if k % 2 == 1:
            place(buf, lp(noise(int(0.12 * SR)), 5000) * expdecay(int(0.12 * SR), 0.04), tt, 0.12)
        if k % 8 == 4:
            for m in (64, 67, 70, 74):
                place(buf, epiano(mtof(m), 0.4, 0.4), tt, 0.08)
        tt += beat / 2
        k += 1
    return buf[: int(dur * SR)]


def music_chase(dur):
    bpm = 176
    beat = 60 / bpm
    n = int(dur * SR) + SR
    buf = np.zeros(n)
    tt, k = 0.0, 0
    bass = [40, 40, 52, 40, 43, 40, 50, 41]
    while tt < dur:
        place(buf, lp(saw(mtof(bass[k % 8]), T(beat / 2 * 0.8)), 900) * env_adsr(int(beat / 2 * 0.8 * SR), 0.005, 0.05, 0.6, 0.03), tt, 0.3)
        if k % 2 == 0:
            place(buf, kick(0.2), tt, 0.8)
        else:
            place(buf, snare(0.1), tt, 0.35)
        place(buf, hat(), tt, 0.25)
        tt += beat / 2
        k += 1
    t_ = T(dur + 1)
    siren = np.sin(2 * np.pi * np.cumsum(700 + 250 * np.sin(2 * np.pi * 1.2 * t_)) / SR) * 0.05
    buf[: len(siren)] += siren[: len(buf)]
    return buf[: int(dur * SR)]


def music_eerie(dur):
    t_ = T(dur + 1)
    drone = sum(np.sin(2 * np.pi * mtof(m) * t_ * (1 + 0.002 * np.sin(t_ * 0.3 + m))) for m in (33, 40, 45))
    drone = drone * (0.6 + 0.4 * np.sin(2 * np.pi * 0.1 * t_)) * 0.25
    wind = lp(noise(len(t_)), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t_)) * 0.15
    buf = drone + wind
    for k in range(int(dur / 2.3)):
        tt = k * 2.3 + RNG.uniform(0, 1)
        f = RNG.uniform(900, 2200)
        x = np.sin(2 * np.pi * f * T(0.4) * (1 - T(0.4) * 0.3)) * expdecay(int(0.4 * SR), 0.05)
        place(buf, x, tt, 0.15)
    buf = buf + 0.5 * reverb(buf, 2.5)[: len(buf)]
    return buf[: int(dur * SR)]


def music_tender(dur):
    """Music-box waltz."""
    bpm = 90
    beat = 60 / bpm
    mel = [76, 79, 84, 83, 79, 76, 74, 76, 79, 77, 74, 71]
    chords = [(60, "M"), (55, "M"), (57, "m"), (53, "M")]
    n = int(dur * SR) + 2 * SR
    buf = np.zeros(n)
    tt, k = 0.0, 0
    while tt < dur:
        f = mtof(mel[k % len(mel)])
        x = (np.sin(2 * np.pi * f * T(1.2)) + 0.3 * np.sin(2 * np.pi * 4 * f * T(1.2))) * expdecay(int(1.2 * SR), 0.35)
        place(buf, x, tt, 0.14)
        if k % 3 == 0:
            root, kind = chords[(k // 3) % 4]
            for m in _chord(root, kind):
                place(buf, epiano(mtof(m - 12), beat * 3, 0.3), tt, 0.06)
        tt += beat
        k += 1
    return (buf + 0.4 * reverb(buf, 1.8)[: len(buf)])[: int(dur * SR)]


def music_reveal(dur):
    t_ = T(dur + 1)
    pad = np.zeros(len(t_))
    for m in (45, 52, 57, 60, 64):
        pad += saw(mtof(m) * (1 + 0.003 * np.sin(t_ * 0.5 + m)), t_)
    pad = lp(pad, 1400) * 0.06 * np.minimum(1, t_ / 3)
    buf = pad.copy()
    for k in range(int(dur / 1.6)):
        m = [69, 72, 76, 74, 72, 71, 69, 64][k % 8]
        place(buf, epiano(mtof(m), 2.5, 0.5), k * 1.6, 0.12)
    buf = buf + 0.6 * reverb(buf, 3.0)[: len(buf)]
    return buf[: int(dur * SR)]


MUSIC = {"lofi": music_lofi, "lofi_muffled": music_lofi_muffled, "sneak": music_sneak, "panic": music_panic,
         "muzak": music_muzak, "spy": music_spy, "chase": music_chase, "eerie": music_eerie, "tender": music_tender,
         "reveal": music_reveal}


# ------------------------------------------------------------------------------------------ SFX
def s_game():
    buf = np.zeros(int(2.0 * SR))
    for k in range(10):
        f0 = RNG.uniform(500, 1400)
        tt = T(0.08)
        x = sq(f0 * (1 - tt * 4), tt, 0.5) * expdecay(len(tt), 0.04)
        place(buf, x, k * 0.19 + RNG.uniform(0, 0.05), 0.12)
    return buf


def s_crash_clatter():
    buf = np.zeros(int(1.6 * SR))
    for k in range(9):
        n = int(RNG.uniform(0.05, 0.25) * SR)
        f = RNG.uniform(300, 2500)
        x = bp(noise(n), f, f * 2.2) * expdecay(n, 0.05)
        x += np.sin(2 * np.pi * f * 0.5 * np.arange(n) / SR) * expdecay(n, 0.08) * 0.4
        place(buf, x, RNG.uniform(0, 1.0), RNG.uniform(0.4, 0.9))
    return buf + 0.3 * reverb(buf, 0.8)[: len(buf)]


def s_rumble():
    t_ = T(2.2)
    x = lp(noise(len(t_)), 120, 4) * 6 + np.sin(2 * np.pi * 38 * t_) * 0.5
    x *= env_adsr(len(t_), 0.15, 0.4, 0.7, 0.9)
    return np.tanh(x) * 0.9


def s_bang():
    buf = np.zeros(int(1.4 * SR))
    for k in range(3):
        n = int(0.25 * SR)
        x = lp(noise(n), 400) * expdecay(n, 0.03) * 3 + np.sin(2 * np.pi * 90 * T(0.25)) * expdecay(n, 0.05)
        place(buf, np.tanh(x), k * 0.33, 0.9)
    return buf + 0.2 * reverb(buf, 0.6)[: len(buf)]


def s_glass():
    n = int(1.6 * SR)
    x = hp(noise(n), 2500) * expdecay(n, 0.12) * 0.8
    for k in range(30):
        f = RNG.uniform(2500, 7000)
        place(x, np.sin(2 * np.pi * f * T(0.2)) * expdecay(int(0.2 * SR), 0.04), RNG.uniform(0.02, 0.9),
              RNG.uniform(0.1, 0.3))
    place(x, lp(noise(int(0.2 * SR)), 600) * expdecay(int(0.2 * SR), 0.03), 0, 0.8)
    return x


def s_tiptoe():
    buf = np.zeros(int(2.0 * SR))
    for k in range(8):
        n = int(0.05 * SR)
        place(buf, bp(noise(n), 800, 2500) * expdecay(n, 0.01), k * 0.25, 0.35)
    return buf


def s_scratch():
    buf = np.zeros(int(2.4 * SR))
    for k in range(14):
        n = int(RNG.uniform(0.06, 0.15) * SR)
        x = bp(noise(n), 2000, 6000) * np.sin(np.pi * np.arange(n) / n)
        place(buf, x, k * 0.16 + RNG.uniform(0, 0.05), 0.5)
    return buf


def s_pant():
    buf = np.zeros(int(3.0 * SR))
    for k in range(int(3.0 / 0.22)):
        n = int(0.16 * SR)
        x = bp(noise(n), 700 if k % 2 else 900, 3000) * np.sin(np.pi * np.arange(n) / n)
        place(buf, x, k * 0.22, 0.32)
    return buf


def s_bark():
    buf = np.zeros(int(1.2 * SR))
    for k in range(2):
        tt = T(0.18)
        f = 520 * np.exp(-tt * 4)
        x = (saw(1, np.cumsum(f) / SR) * 0.7 + bp(noise(len(tt)), 600, 2500) * 0.6) * env_adsr(len(tt), 0.005, 0.05, 0.6, 0.06)
        place(buf, bp(x, 300, 3000), k * 0.32, 0.9)
    return buf


def s_zap():
    n = int(0.8 * SR)
    x = noise(n) * (np.sin(2 * np.pi * 60 * T(0.8)) > 0) * expdecay(n, 0.2)
    x = bp(x, 800, 6000) + saw(110, T(0.8)) * 0.3 * expdecay(n, 0.2)
    return np.tanh(x * 1.5) * 0.7


def s_tap():
    n = int(0.08 * SR)
    return lp(noise(n), 1500) * expdecay(n, 0.01) * 0.9


def s_boing():
    t_ = T(0.7)
    f = 160 + 300 * t_
    return np.sin(2 * np.pi * np.cumsum(f + 40 * np.sin(2 * np.pi * 14 * t_)) / SR) * expdecay(len(t_), 0.25) * 0.6


def s_tweet():
    buf = np.zeros(int(1.6 * SR))
    for k in range(4):
        tt = T(0.12)
        f = 2600 + 900 * np.sin(np.pi * tt / 0.12)
        place(buf, np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(tt), 0.01, 0.03, 0.7, 0.03), k * 0.35, 0.25)
    return buf


def s_zip():
    t_ = T(0.35)
    f = 300 + 3000 * (t_ / 0.35) ** 2
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + hp(noise(len(t_)), 3000) * 0.4) * env_adsr(len(t_), 0.01, 0.1, 0.6, 0.1)


def s_rustle():
    n = int(0.8 * SR)
    return bp(noise(n), 1500, 6000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 6 * T(0.8)))) * env_adsr(n, 0.05, 0.1, 0.8, 0.2) * 0.4


def s_click():
    n = int(0.06 * SR)
    return bp(noise(n), 1500, 5000) * expdecay(n, 0.008) * 0.9


def s_growl():
    t_ = T(1.4)
    x = saw(1, np.cumsum(90 + 15 * np.sin(2 * np.pi * 9 * t_)) / SR)
    return lp(x, 700) * env_adsr(len(t_), 0.1, 0.2, 0.8, 0.3) * 0.5


def s_rattle():
    buf = np.zeros(int(1.5 * SR))
    for k in range(18):
        n = int(0.04 * SR)
        f = RNG.uniform(2000, 4000)
        place(buf, np.sin(2 * np.pi * f * T(0.04)) * expdecay(n, 0.01), k * 0.08, 0.3)
    return buf


def s_chomp():
    n = int(0.25 * SR)
    x = lp(noise(n), 1200) * expdecay(n, 0.04) * 2 + np.sin(2 * np.pi * 180 * T(0.25)) * expdecay(n, 0.05)
    return np.tanh(x) * 0.9


def s_van_door():
    buf = np.zeros(int(1.6 * SR))
    for k in range(3):
        n = int(0.3 * SR)
        x = lp(noise(n), 300) * expdecay(n, 0.05) * 3 + np.sin(2 * np.pi * 70 * T(0.3)) * expdecay(n, 0.08)
        place(buf, np.tanh(x), k * 0.42, 0.8)
    return buf


def s_alarm():
    t_ = T(4.0)
    f = 650 + 350 * (np.sin(2 * np.pi * 1.5 * t_) > 0)
    x = sq(1, np.cumsum(f) / SR, 0.5) * 0.25
    return lp(x, 3000)


def s_wind():
    n = int(3.0 * SR)
    x = bp(noise(n), 300, 2000) * np.linspace(0.3, 1.0, n)
    return x * 0.5


def s_impact():
    n = int(0.8 * SR)
    x = lp(noise(n), 300) * expdecay(n, 0.1) * 4 + np.sin(2 * np.pi * 45 * T(0.8)) * expdecay(n, 0.2)
    return np.tanh(x) * 0.95


def s_drip():
    t_ = T(0.25)
    f = 1200 + 1400 * np.exp(-t_ * 30)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * expdecay(len(t_), 0.04) * 0.5
    return x + 0.6 * reverb(x, 1.5)[: len(x)]


def s_sense():
    t_ = T(2.0)
    x = np.sin(2 * np.pi * 180 * t_) * expdecay(len(t_), 0.6) * 0.5
    x += np.sin(2 * np.pi * 360 * t_ * (1 + 0.05 * t_)) * expdecay(len(t_), 0.4) * 0.25
    return x + 0.5 * reverb(x, 2.5)[: len(x)]


def s_hiss():
    n = int(1.2 * SR)
    return hp(noise(n), 3000) * env_adsr(n, 0.05, 0.2, 0.8, 0.4) * 0.5


def s_shriek():
    t_ = T(1.0)
    f = 900 + 500 * np.sin(2 * np.pi * 7 * t_) + 600 * t_
    x = saw(1, np.cumsum(f) / SR) * 0.4 + bp(noise(len(t_)), 1500, 5000) * 0.5
    return np.tanh(bp(x, 600, 5000) * 2) * env_adsr(len(t_), 0.02, 0.2, 0.8, 0.3) * 0.6


def s_purr():
    t_ = T(2.5)
    x = lp(noise(len(t_)), 200, 4) * (0.5 + 0.5 * np.sin(2 * np.pi * 24 * t_)) * 6
    return np.tanh(x) * env_adsr(len(t_), 0.3, 0.2, 0.8, 0.6) * 0.5


def s_chitter():
    buf = np.zeros(int(1.0 * SR))
    for k in range(9):
        tt = T(0.04)
        f = RNG.uniform(1800, 3000)
        place(buf, np.sin(2 * np.pi * f * tt) * np.sin(np.pi * np.arange(len(tt)) / len(tt)), k * 0.07, 0.35)
    return buf


def s_poke():
    t_ = T(0.12)
    return np.sin(2 * np.pi * np.cumsum(300 + 1500 * t_ / 0.12) / SR) * expdecay(len(t_), 0.04) * 0.6


def s_typing():
    buf = np.zeros(int(2.5 * SR))
    tt = 0
    while tt < 2.3:
        n = int(0.03 * SR)
        place(buf, bp(noise(n), 2000, 7000) * expdecay(n, 0.006), tt, 0.5)
        tt += RNG.uniform(0.06, 0.16)
    return buf


def s_buzz():
    t_ = T(0.6)
    return lp(sq(120, t_, 0.5), 2000) * env_adsr(len(t_), 0.01, 0.05, 0.9, 0.05) * 0.3


def s_whimper():
    t_ = T(1.0)
    f = 700 - 250 * t_ + 30 * np.sin(2 * np.pi * 8 * t_)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_adsr(len(t_), 0.1, 0.2, 0.6, 0.4) * 0.35


def s_dun():
    buf = np.zeros(int(2.0 * SR))
    for m in (36, 43, 48):
        x = lp(saw(mtof(m), T(1.6)), 900) * expdecay(int(1.6 * SR), 0.6)
        place(buf, x, 0, 0.25)
    place(buf, kick(0.4), 0, 1.0)
    return buf + 0.4 * reverb(buf, 1.6)[: len(buf)]


def s_sigh():
    n = int(1.2 * SR)
    return bp(noise(n), 300, 1800) * env_adsr(n, 0.15, 0.3, 0.6, 0.6) * 0.45


def s_door_slam():
    n = int(0.6 * SR)
    x = lp(noise(n), 500) * expdecay(n, 0.04) * 3 + np.sin(2 * np.pi * 80 * T(0.6)) * expdecay(n, 0.08)
    return np.tanh(x) * 0.9


def s_burst():
    return np.concatenate([s_door_slam(), np.zeros(int(0.05 * SR))]) + 0


SFX = {
    "game": s_game, "clatter": s_crash_clatter, "rumble": s_rumble, "bang": s_bang, "glass": s_glass,
    "tiptoe": s_tiptoe, "stairscratch": s_scratch, "pant": s_pant, "bark": s_bark, "zap": s_zap, "tap": s_tap,
    "boing2": s_boing, "tweet": s_tweet, "zip": s_zip, "rustle": s_rustle, "click": s_click, "growl": s_growl,
    "rattle": s_rattle, "chomp": s_chomp, "vandoor": s_van_door, "alarm": s_alarm, "wind": s_wind,
    "impact": s_impact, "drip": s_drip, "sense": s_sense, "hiss": s_hiss, "shriek": s_shriek, "purr": s_purr,
    "chitter": s_chitter, "poke": s_poke, "typing": s_typing, "buzz": s_buzz, "whimper": s_whimper, "dun": s_dun,
    "sigh": s_sigh, "doorslam": s_door_slam,
}
