"""Lab Partners sounds: bleeps, record scratch, boss music, golf claps, crowd laughter."""
import numpy as np

import audio as A
from audio import SR, t_, env, lp, hp, bp, noise, glide, norm, note_f

rng = np.random.default_rng(33)


def bleep():
    d = 0.45
    t = t_(d)
    return norm(np.sin(2 * np.pi * 1000 * t) * env(len(t), 0.005, 0.01), 0.45)


def scratch():
    d = 0.7
    t = t_(d)
    f = 1800 * np.exp(-t * 5) + 200
    x = bp(noise(d), 300, 4000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR * 0.02))
    x += np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    return norm(x * env(len(t), 0.01, 0.2), 0.7)


def golfclap():
    out = np.zeros(int(1.6 * SR))
    for i in range(6):
        d = 0.05
        c = bp(noise(d), 800, 4000) * np.exp(-t_(d) * 90)
        k = int(i * 0.26 * SR)
        out[k:k + len(c)] += c
    return norm(out, 0.5)


def ha_voice(d, f0):
    t = t_(d)
    out = np.zeros(len(t))
    k = 0.0
    while k < d - 0.15:
        dd = rng.uniform(0.12, 0.18)
        tt = t_(dd)
        f = f0 * (1 + 0.1 * rng.uniform(-1, 1)) * (1 - 0.2 * tt / dd)
        saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
        syl = bp(saw, 500, 1500) + 0.3 * bp(noise(dd), 800, 3000)
        syl *= np.sin(np.pi * tt / dd) ** 2
        i = int(k * SR)
        out[i:i + len(syl)] += syl[:len(out) - i]
        k += dd + rng.uniform(0.02, 0.08)
    return out


def crowd_laugh(d=5.0, n=22):
    out = np.zeros(int(d * SR))
    for j in range(n):
        st = rng.uniform(0, 1.2)
        ln = rng.uniform(1.8, d - st)
        v = ha_voice(ln, rng.uniform(110, 260)) * rng.uniform(0.4, 1.0)
        i = int(st * SR)
        out[i:i + len(v)] += v[:len(out) - i]
    out *= env(len(out), 0.4, 1.2)
    return norm(out, 0.7)


def chuckle():
    return norm(ha_voice(1.0, 120) * env(int(1.0 * SR), 0.05, 0.3), 0.4)


def ovation():
    a = A.sfx_applause(5.0)
    c = crowd_laugh(5.0, 10) * 0.5
    return norm(a + c[:len(a)], 0.8)


def squeal():
    return A.sfx_squeal()


def slip():
    d = 0.6
    x = glide(300, 1600, d, 0.6) * env(int(d * SR), 0.01, 0.2)
    return norm(x, 0.5)


def crash_land():
    return A.sfx_boom()


def clink():
    d = 1.0
    t = t_(d)
    x = (np.sin(2 * np.pi * 2800 * t) + 0.6 * np.sin(2 * np.pi * 4100 * t)) * np.exp(-t * 6)
    return norm(x, 0.45)


def heartgrow():
    a = A.sfx_ding(784)
    b = A.sfx_ding(1175)
    out = np.zeros(len(a) + int(0.25 * SR))
    out[:len(a)] += a
    out[int(0.25 * SR):] += b
    return norm(out, 0.5)


def mech_step():
    d = 0.8
    t = t_(d)
    x = np.sin(2 * np.pi * (45 + 30 * np.exp(-t * 10)) * t) * np.exp(-t * 5) + lp(noise(d), 500) * np.exp(-t * 8)
    return norm(x, 0.9)


def shatter():
    d = 1.0
    out = hp(noise(d), 2500) * np.exp(-t_(d) * 9) * 0.6
    for i in range(18):
        k = int(rng.uniform(0, 0.5) * SR)
        dd = 0.12
        f = rng.uniform(2500, 7000)
        ping = np.sin(2 * np.pi * f * t_(dd)) * np.exp(-t_(dd) * 40) * rng.uniform(0.3, 1.0)
        out[k:k + len(ping)] += ping[:len(out) - k]
    return norm(out, 0.6)


def sweep():
    d = 0.45
    t = t_(d)
    return norm(bp(noise(d), 1500, 6000) * np.sin(np.pi * t / d) ** 2, 0.3)


for name, fn in dict(shatter=shatter, sweep=sweep, bleep=bleep, scratch=scratch, golfclap=golfclap, crowdlaugh=crowd_laugh, chuckle=chuckle,
                     ovation=ovation, slip=slip, crashland=crash_land, clink=clink, heartgrow=heartgrow,
                     mechstep=mech_step).items():
    A.SFX[name] = fn


def music_lab(total):
    """Bouncy mad-science bed: plucky arpeggios over oom-pah bass."""
    out = np.zeros(int((total + 3) * SR))
    beat = 0.28
    arp = [60, 64, 67, 72, 67, 64, 62, 65, 69, 74, 69, 65, 59, 62, 67, 71, 67, 62, 60, 64, 67, 72, 76, 72]
    bass = [36, 43, 38, 45, 31, 38, 36, 43]
    tt = 0.0
    k = 0
    while tt < total:
        n = arp[k % len(arp)]
        p = A.pluck(note_f(n + 12), 0.25, 0.7) * 0.3
        i = int(tt * SR)
        out[i:i + len(p)] += p[:max(0, len(out) - i)]
        if k % 3 == 0:
            b = bass[(k // 3) % len(bass)]
            d = 0.3
            tv = t_(d)
            bb = lp(2 * ((tv * note_f(b)) % 1) - 1, 700) * np.exp(-tv * 8)
            out[i:i + len(bb)] += bb[:max(0, len(out) - i)] * 0.5
        tt += beat
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_boss(total):
    """Over-the-top boss theme: pounding drums, organ stabs, choir pad in minor."""
    out = np.zeros(int((total + 4) * SR))
    beat = 0.33
    prog = [[45, 48, 52], [45, 48, 52], [41, 45, 48], [43, 47, 50]]
    tt = 0.0
    k = 0
    while tt < total:
        i = int(tt * SR)
        d = 0.4
        td = t_(d)
        drum = np.sin(2 * np.pi * (50 + 60 * np.exp(-td * 20)) * td) * np.exp(-td * 9)
        out[i:i + len(drum)] += drum[:max(0, len(out) - i)] * (1.0 if k % 2 == 0 else 0.6)
        if k % 4 == 0:
            ch = prog[(k // 8) % 4]
            dd = beat * 3.6
            tv = t_(dd)
            stab = sum((2 * ((tv * note_f(n + 12)) % 1) - 1) + 0.5 * np.sin(2 * np.pi * note_f(n + 24) * tv)
                       for n in ch)
            stab = lp(stab, 2600) * np.exp(-tv * 2.5) * 0.35
            out[i:i + len(stab)] += stab[:max(0, len(out) - i)]
        if k % 2 == 1:
            sn = hp(noise(0.12), 2000) * np.exp(-t_(0.12) * 30) * 0.25
            out[i:i + len(sn)] += sn[:max(0, len(out) - i)]
        tt += beat
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_beach(total):
    """Steel-drum-ish island bed."""
    out = np.zeros(int((total + 3) * SR))
    beat = 0.3
    mel = [72, 76, 79, 76, 74, 77, 81, 77, 72, 76, 79, 84, 79, 76, 74, 72]
    tt = 0.0
    k = 0
    while tt < total:
        n = mel[k % len(mel)]
        d = 0.5
        tv = t_(d)
        f = note_f(n)
        x = (np.sin(2 * np.pi * f * tv) + 0.5 * np.sin(2 * np.pi * f * 2.0 * tv) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tv))
        x *= np.exp(-tv * 6) * 0.25
        i = int(tt * SR)
        if k % 4 != 3:
            out[i:i + len(x)] += x[:max(0, len(out) - i)]
        if k % 2 == 0:
            bb = A.pluck(note_f([48, 53, 55, 53][(k // 8) % 4]), 0.4, 0.4) * 0.4
            out[i:i + len(bb)] += bb[:max(0, len(out) - i)]
        tt += beat
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_sad(total):
    return A.music_dream(total, [[45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59], [40, 47, 52, 55]], 0.8)


A.MOODS.update(lab=music_lab, boss=music_boss, beach=music_beach, sad=music_sad)
