"""Dungeon sound effects and music, registered into the shared audio module."""
import numpy as np

import audio as A
from audio import SR, t_, env, lp, hp, bp, noise, glide, norm, note_f

rng = np.random.default_rng(12)


def clank():
    d = 0.5
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in ((820, 9), (1370, 12), (2210, 15), (3150, 18)))
    x += hp(noise(d), 2000) * np.exp(-t * 40) * 0.6
    return norm(x, 0.5)


def step():
    d = 0.35
    t = t_(d)
    x = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 16) + lp(noise(d), 500) * np.exp(-t * 22) * 0.8
    c = clank()[:len(t)] * 0.25
    return norm(x + c, 0.7)


def slash():
    d = 0.45
    w = A.sfx_whoosh(0.3, 1500, 6000)
    out = np.zeros(int(d * SR))
    out[:len(w)] += w
    t = t_(0.4)
    ring = np.sin(2 * np.pi * 3400 * t) * np.exp(-t * 14) * 0.25
    out[int(0.1 * SR):int(0.1 * SR) + len(ring)] += ring[:len(out) - int(0.1 * SR)]
    return norm(out, 0.6)


def chop():
    d = 0.4
    t = t_(d)
    x = lp(noise(d), 2500) * np.exp(-t * 30) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 25) * 0.6
    return norm(x, 0.7)


def rustle():
    d = 0.9
    x = bp(noise(d), 1500, 6000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t_(d)))) * env(int(d * SR), 0.05, 0.4)
    return norm(x, 0.4)


def webtear():
    out = np.zeros(int(0.8 * SR))
    for i in range(7):
        d = 0.06
        b = hp(noise(d), 3000) * np.exp(-t_(d) * 50)
        k = int((i * 0.07 + rng.uniform(0, 0.03)) * SR)
        out[k:k + len(b)] += b
    return norm(out, 0.4)


def rattle():
    out = np.zeros(int(1.2 * SR))
    for i in range(6):
        c = clank() * 0.6
        ch = chop()
        c[:len(ch)] += ch * 0.4
        k = int(i * 0.16 * SR)
        out[k:k + len(c)] += c[:len(out) - k]
    return norm(out, 0.6)


def explosion():
    d = 2.6
    t = t_(d)
    x = np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 6)) * t) * np.exp(-t * 2.2)
    x += lp(noise(d), 1500) * np.exp(-t * 2.8) * 1.2
    for i in range(30):
        c = chop() * rng.uniform(0.1, 0.4)
        k = int(rng.uniform(0.1, 1.8) * SR)
        x[k:k + len(c)] += c[:len(x) - k]
    return norm(x, 0.95)


def rumble(d=3.0):
    t = t_(d)
    x = lp(noise(d), 180) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)) * env(len(t), 0.3, 1.0)
    return norm(x, 0.8)


def crumble():
    d = 2.4
    x = rumble(d) * 0.7
    for i in range(50):
        c = chop() * rng.uniform(0.05, 0.3)
        k = int(rng.uniform(0, d - 0.4) * SR)
        x[k:k + len(c)] += c
    return norm(x, 0.85)


def stoneshift():
    d = 0.7
    t = t_(d)
    x = bp(noise(d), 120, 900) * (0.5 + 0.5 * np.sin(2 * np.pi * 40 * t)) * env(len(t), 0.02, 0.2)
    return norm(x, 0.7)


def hiss():
    d = 1.6
    x = hp(noise(d), 4000) * np.exp(-t_(d) * 1.8)
    return norm(x, 0.4)


def splash_big():
    d = 1.0
    t = t_(d)
    x = bp(noise(d), 300, 5000) * np.exp(-t * 4)
    return norm(x, 0.6)


def scurry():
    out = np.zeros(int(1.2 * SR))
    for i in range(26):
        d = 0.02
        c = bp(noise(d), 2000, 7000) * np.exp(-t_(d) * 200)
        k = int((i * 0.04 + rng.uniform(0, 0.015)) * SR)
        out[k:k + len(c)] += c * rng.uniform(0.4, 1.0)
    out *= np.linspace(0.5, 1, len(out)) * np.linspace(1, 0.3, len(out))
    return norm(out, 0.35)


def growl(d=2.2):
    t = t_(d)
    f = 70 + 10 * np.sin(2 * np.pi * 1.3 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = sum(np.sin(ph * h) / h for h in range(1, 12))
    x *= 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 13 * t))
    x += bp(noise(d), 200, 1200) * 0.6
    x = lp(x, 1500) * env(len(t), 0.2, 0.5)
    return norm(x, 0.75)


def drip():
    d = 0.6
    t = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(900 + 1400 * np.exp(-t * 40)) / SR) * np.exp(-t * 25)
    echo = np.zeros_like(x)
    k = int(0.18 * SR)
    echo[k:] = x[:-k] * 0.35
    return norm(x + echo, 0.35)


def heartbeat():
    out = np.zeros(int(1.0 * SR))
    for k0, a in ((0, 1.0), (0.22, 0.7)):
        d = 0.25
        t = t_(d)
        b = np.sin(2 * np.pi * 50 * t) * np.exp(-t * 20) * a
        k = int(k0 * SR)
        out[k:k + len(b)] += b
    return norm(out, 0.7)


def wind_fall(d=4.0):
    n = noise(d)
    out = np.zeros_like(n)
    seg = 16
    L = len(n) // seg
    for i in range(seg):
        f = 300 + 1500 * i / seg
        out[i * L:(i + 1) * L] = bp(n[i * L:(i + 1) * L], f * 0.5, f * 1.5)
    out *= env(len(out), 0.6, 0.4)
    return norm(out, 0.55)


def grind(d=3.2):
    t = t_(d)
    x = bp(noise(d), 1500, 7000) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 31 * t)))
    for f in (1830, 2470, 3990):
        x += np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 7 * t)) * 0.12
    for i in range(60):
        c = chop() * rng.uniform(0.05, 0.25)
        k = int(rng.uniform(0, d - 0.4) * SR)
        x[k:k + len(c)] += c
    x *= env(len(t), 0.05, 0.4)
    return norm(x, 0.7)


def impact():
    d = 2.0
    t = t_(d)
    x = np.sin(2 * np.pi * (38 + 50 * np.exp(-t * 10)) * t) * np.exp(-t * 3)
    x += lp(noise(d), 900) * np.exp(-t * 6)
    c = clank()
    x[:len(c)] += c * 0.6
    return norm(x, 1.0)


def bonk():
    d = 0.6
    t = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(600 - 300 * t / d) / SR) * np.exp(-t * 7)
    x += np.sin(2 * np.pi * 1250 * t) * np.exp(-t * 30) * 0.6
    return norm(x, 0.8)


def throw():
    return A.sfx_whoosh(0.5, 400, 3000)


def crunch():
    out = np.zeros(int(3.5 * SR))
    for i in range(14):
        d = 0.18
        c = bp(noise(d), 600, 5000) * np.exp(-t_(d) * 18) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 60 * t_(d))))
        k = int((i * 0.24 + rng.uniform(0, 0.05)) * SR)
        out[k:k + len(c)] += c * rng.uniform(0.5, 1)
    return norm(out, 0.7)


def snore():
    d = 3.2
    t = t_(d)
    x = np.zeros_like(t)
    inh = (t < 1.6)
    rattle_ = np.sin(2 * np.pi * 26 * t) > 0.2
    saw = 2 * ((t * 85) % 1) - 1
    x += np.where(inh, saw * rattle_ * np.sin(np.pi * np.clip(t / 1.6, 0, 1)), 0) * 0.9
    x += lp(noise(d), 700) * np.where(inh, 0.3, 0.4 * np.clip(np.sin(np.pi * (t - 1.7) / 1.3), 0, 1))
    x = lp(x, 1800)
    return norm(x, 0.75)


def drool():
    d = 0.3
    t = t_(d)
    x = np.sin(2 * np.pi * np.cumsum(300 + 900 * t / d) / SR) * np.exp(-t * 14) + lp(noise(d), 1200) * np.exp(-t * 30) * 0.3
    return norm(x, 0.45)


def stomp_big():
    d = 1.4
    t = t_(d)
    x = np.sin(2 * np.pi * (40 + 30 * np.exp(-t * 12)) * t) * np.exp(-t * 4) + lp(noise(d), 300) * np.exp(-t * 6)
    return norm(x, 0.9)


def tap():
    d = 0.15
    t = t_(d)
    x = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40) + lp(noise(d), 1500) * np.exp(-t * 60) * 0.4
    return norm(x, 0.5)


def cricket(d=4.0):
    out = np.zeros(int(d * SR))
    k = 0.0
    while k < d - 0.3:
        for j in range(3):
            dd = 0.03
            tt = t_(dd)
            c = np.sin(2 * np.pi * 4300 * tt) * np.sin(np.pi * tt / dd)
            i = int((k + j * 0.045) * SR)
            out[i:i + len(c)] += c
        k += 0.7
    return norm(out, 0.18)


def snort():
    d = 0.5
    t = t_(d)
    x = bp(noise(d), 200, 1400) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 34 * t))) * np.exp(-t * 6)
    return norm(x, 0.8)


def sting():
    d = 3.0
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) for f in (1480, 1568, 1661, 1760)) * env(len(t), 1.2, 1.0)
    x += sum(np.sin(2 * np.pi * f * t) for f in (73.4, 77.8)) * 0.8 * env(len(t), 0.5, 1.5)
    return norm(x, 0.35)


def hit():
    d = 3.0
    t = t_(d)
    x = np.sin(2 * np.pi * (30 + 70 * np.exp(-t * 5)) * t) * np.exp(-t * 1.5)
    x += lp(noise(d), 400) * np.exp(-t * 3) * 0.6
    return norm(x, 0.95)


def torch_whoosh():
    return A.sfx_whoosh(0.7, 200, 1500)


def cave_amb(d=24.0):
    x = lp(noise(d), 260) * 0.25
    t = t_(d)
    x *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t)
    for i in range(int(d / 2.5)):
        dr = drip() * rng.uniform(0.15, 0.5)
        k = int(rng.uniform(0, d - 0.7) * SR)
        x[k:k + len(dr)] += dr
    return norm(x, 0.35)


def sizzle():
    d = 2.0
    t = t_(d)
    x = hp(noise(d), 2500) * (0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 11 * t))) * env(len(t), 0.2, 0.6)
    return norm(x, 0.12)


def twinkle_ko():
    out = np.zeros(int(1.6 * SR))
    for i, f in enumerate((1568, 2093, 1568, 2093, 1568)):
        d = 0.3
        tt = t_(d)
        b = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 12)
        k = int(i * 0.18 * SR)
        out[k:k + len(b)] += b
    return norm(out, 0.3)


for name, fn in dict(clank=clank, step=step, slash=slash, chop=chop, rustle=rustle, webtear=webtear,
                     rattle=rattle, explosion=explosion, rumble=rumble, crumble=crumble,
                     stoneshift=stoneshift, hiss=hiss, splashbig=splash_big, scurry=scurry,
                     growl=growl, drip=drip, heartbeat=heartbeat, windfall=wind_fall, grind=grind,
                     impact=impact, bonk=bonk, throw=throw, crunch=crunch, snore=snore,
                     drool=drool, stompbig=stomp_big, tap=tap, cricket=cricket, snort=snort,
                     sting=sting, hit=hit, torchwhoosh=torch_whoosh, caveamb=cave_amb,
                     sizzle=sizzle, ko=twinkle_ko).items():
    A.SFX[name] = fn


# ---------------------------------------------------------------- music
def saw(f, d, bright=3000):
    t = t_(d)
    x = 2 * ((t * f) % 1) - 1
    return lp(x, bright)


def music_epic(total):
    """Dark orchestral feel in D minor: drones, choir pad, war drums, low brass swells."""
    out = np.zeros(int((total + 8) * SR))
    prog = [[50, 53, 57], [46, 50, 53], [43, 46, 50], [45, 49, 52]]
    bar = 4.0
    tt = 0.0
    k = 0
    while tt < total + 1:
        ch = prog[k % 4]
        # choir-ish pad: detuned saws through a vowel band
        d = bar + 1.0
        tv = t_(d)
        pad = sum(saw(note_f(n + 12) * dt, d, 2200) for n in ch for dt in (0.997, 1.003))
        pad = bp(pad, 350, 1400) * env(len(tv), 0.9, 1.0) * 0.18
        i = int(tt * SR)
        out[i:i + len(pad)] += pad[:max(0, len(out) - i)]
        # low brass swell on the root
        br = saw(note_f(ch[0] - 12), d, 900) * env(len(tv), 1.5, 1.2) * 0.35
        out[i:i + len(br)] += br[:max(0, len(out) - i)]
        # war drums: boom . . boom boom .
        for off, amp in ((0, 1.0), (1.5, 0.6), (2.0, 0.8), (3.0, 0.5), (3.5, 0.7)):
            dd = 0.9
            td = t_(dd)
            drum = np.sin(2 * np.pi * (55 + 40 * np.exp(-td * 12)) * td) * np.exp(-td * 5) + lp(noise(dd), 300) * np.exp(-td * 12) * 0.4
            j = int((tt + off) * SR)
            out[j:j + len(drum)] += drum[:max(0, len(out) - j)] * amp * 0.9
        tt += bar
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_tense(total):
    out = np.zeros(int((total + 4) * SR))
    t = t_(total + 4)
    drone = saw(note_f(38), total + 4, 400) * 0.5 + np.sin(2 * np.pi * note_f(38) * 1.5 * t) * 0.12
    drone *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * t)
    out += drone
    hi = sum(np.sin(2 * np.pi * f * t) for f in (1174.7, 1244.5)) * 0.03 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t))
    out += hi
    k = 0.0
    while k < total:
        hb = heartbeat()
        i = int(k * SR)
        out[i:i + len(hb)] += hb * 0.5
        k += 1.6
    return norm(out, 1.0)[:int(total * SR)]


def music_quirky(total):
    """Light, bouncy bassoon-and-pizzicato comedy bed."""
    out = np.zeros(int((total + 3) * SR))
    beat = 0.36
    bass = [43, 0, 50, 0, 47, 0, 50, 0, 45, 0, 52, 0, 48, 0, 50, 47]
    mel = [67, 0, 0, 71, 69, 0, 67, 0, 64, 0, 66, 67, 69, 0, 0, 0]
    tt = 0.0
    k = 0
    while tt < total:
        n = bass[k % 16]
        i = int(tt * SR)
        if n:
            d = 0.3
            tv = t_(d)
            b = lp(2 * ((tv * note_f(n)) % 1) - 1, 900) * np.exp(-tv * 7)
            out[i:i + len(b)] += b * 0.6
        m = mel[k % 16]
        if m and (k // 16) % 2 == 1:
            p = A.pluck(note_f(m), 0.35, 0.6) * 0.35
            out[i:i + len(p)] += p[:max(0, len(out) - i)]
        tt += beat
        k += 1
    return norm(out, 1.0)[:int(total * SR)]


def music_drone(total):
    t = t_(total)
    x = saw(note_f(33), total, 250) * 0.6 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t))
    return norm(x, 1.0)


A.MOODS.update(epic=music_epic, tense=music_tense, quirky=music_quirky, drone=music_drone)
