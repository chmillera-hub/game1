"""Synthesised sound design: ambience beds + one-shot effects, aligned to the timeline."""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audiofx as fx  # noqa: E402

SR = 48000
rng = np.random.default_rng(1234)


def env_exp(n, decay):
    return np.exp(-np.arange(n) / (decay * SR))


def noise(n, color="white"):
    x = rng.standard_normal(n)
    if color == "pink":
        X = np.fft.rfft(x)
        f = np.arange(len(X)) + 1
        X /= np.sqrt(f)
        x = np.fft.irfft(X, n)
    elif color == "brown":
        x = np.cumsum(x)
        x -= np.convolve(x, np.ones(4801) / 4801, mode="same")
    return x / (np.max(np.abs(x)) + 1e-9)


def bp(x, lo, hi, order=2):
    return fx.butter(x, SR, "bandpass", (lo, hi), order)


def lp(x, f, order=2):
    return fx.butter(x, SR, "lowpass", f, order)


def hp(x, f, order=2):
    return fx.butter(x, SR, "highpass", f, order)


def lfo(n, rate, depth, phase=0.0):
    t = np.arange(n) / SR
    return 1 + depth * np.sin(2 * np.pi * rate * t + phase)


def smooth_noise(n, rate):
    k = max(2, int(n / SR * rate))
    pts = rng.random(k + 2)
    xs = np.linspace(0, n, k + 2)
    return np.interp(np.arange(n), xs, pts)


# ----------------------------------------------------------------- one-shots
def crackle(n, density=6.0, amp=0.5):
    out = np.zeros(n)
    times = np.cumsum(rng.exponential(1.0 / density, int(n / SR * density * 2) + 5))
    for tt in times:
        i = int(tt * SR)
        L = int(SR * (0.002 + 0.01 * rng.random()))
        if i + L >= n:
            break
        burst = rng.standard_normal(L) * env_exp(L, 0.002) * amp * (0.3 + rng.random())
        out[i:i + L] += burst
    return hp(out, 900)


def s_bread_break():
    n = int(0.6 * SR)
    x = crackle(n, density=120, amp=0.8) * env_exp(n, 0.18)
    tear = bp(noise(n), 300, 2200) * env_exp(n, 0.12) * 0.5
    return (x + tear) * 0.9


def s_knock():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    body = (np.sin(2 * np.pi * 95 * t) * 0.9 + np.sin(2 * np.pi * 182 * t) * 0.5 + np.sin(2 * np.pi * 410 * t) * 0.25) * env_exp(n, 0.07)
    click = bp(noise(n), 800, 4000) * env_exp(n, 0.008) * 0.6
    return body + click


def s_knock3():
    n = int(1.6 * SR)
    out = np.zeros(n)
    for i, tt in enumerate([0.0, 0.45, 0.9]):
        k = s_knock() * (1.0 if i < 2 else 1.1)
        a = int(tt * SR)
        out[a:a + len(k)] += k[: n - a]
    return out


def metal_ping(n, base, decay=0.3, amp=0.3):
    t = np.arange(n) / SR
    ratios = [1.0, 2.76, 5.4, 8.93]
    x = sum(np.sin(2 * np.pi * base * r * t + rng.random() * 6) / (1 + i) for i, r in enumerate(ratios))
    return x * env_exp(n, decay) * amp


def s_chains(dur=1.0, count=6):
    """Heavy iron chain shifting: low, muffled clanks (no bright jingle)."""
    n = int((dur + 0.6) * SR)
    out = np.zeros(n)
    for k in range(count):
        a = int(rng.random() * dur * SR)
        L = int(0.35 * SR)
        p = metal_ping(L, 180 + rng.random() * 260, 0.05 + rng.random() * 0.05, 0.22 + rng.random() * 0.12)
        p += lp(noise(L), 600) * env_exp(L, 0.015) * 0.25
        out[a:a + L] += p[: n - a]
    return lp(out, 1600, 4) * 1.2


def s_breath_shaky(dur=2.2):
    """A trembling exhale held back by grief: breathy, unvoiced, with a fine tremor."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    air = bp(noise(n, "pink"), 350, 2600)
    shape = np.minimum(t / 0.35, 1.0) * np.exp(-np.maximum(t - 0.5, 0) / 0.75)
    tremor = 1 + 0.45 * np.sin(2 * np.pi * (7.5 + 1.5 * smooth_noise(n, 2)) * t)
    catch = 1 - 0.7 * np.exp(-((t - 0.95) / 0.08) ** 2)  # a small catch in the breath
    return air * shape * tremor * catch * 0.5


def s_bolt():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    slide = bp(noise(n), 1800, 4200) * np.clip(1 - t / 0.55, 0, 1) * (t < 0.55) * 0.35
    clank = np.zeros(n)
    a = int(0.58 * SR)
    L = n - a
    clank[a:] = metal_ping(L, 420, 0.18, 0.7) + bp(noise(L), 200, 1200) * env_exp(L, 0.03) * 0.5
    return slide + clank


def s_creak(dur=1.8):
    """Heavy wooden door swinging on iron hinges: a low, noisy groan with no musical pitch."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    body = lp(noise(n, "brown"), 260, 4) * 1.6
    grain = bp(noise(n), 500, 1400) * 0.12
    stick = lp((smooth_noise(n, 22) > 0.55).astype(float), 40)  # irregular stick-slip friction
    x = (body + grain * stick) * (0.35 + 0.65 * stick)
    x *= np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    thud = s_thud(60, 0.5, 0.35)
    a = n - len(thud) - int(0.05 * SR)
    x[a:a + len(thud)] += thud
    return x * 0.8


def s_thud(freq=70, dur=0.6, amp=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.6 * np.exp(-t / 0.03))
    ph = np.cumsum(2 * np.pi * f / SR)
    return (np.sin(ph) * env_exp(n, 0.12) + lp(noise(n), 900) * env_exp(n, 0.02) * 0.4) * amp


def s_bread_thud():
    out = s_thud(110, 0.5, 0.5)
    jar = metal_ping(int(0.6 * SR), 520, 0.09, 0.12)
    n = max(len(out), len(jar) + int(0.12 * SR))
    o = np.zeros(n)
    o[: len(out)] += out
    a = int(0.12 * SR)
    o[a:a + len(jar)] += lp(jar, 2500)
    return o


def s_door_bang():
    x = s_thud(55, 1.4, 1.2)
    x[: len(x)] += bp(noise(len(x)), 150, 2500) * env_exp(len(x), 0.05) * 0.6
    return x


def s_door_close():
    x = s_thud(65, 1.0, 0.8)
    b = s_bolt()
    n = len(b) + int(0.35 * SR)
    o = np.zeros(n)
    o[: len(x)] += x
    o[int(0.35 * SR):int(0.35 * SR) + len(b)] += b * 0.6
    return o


def s_light_swell(dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    k = (t / dur) ** 2.2
    air = bp(noise(n), 2000, 9000) * k * 0.35
    shimmer = sum(np.sin(2 * np.pi * f * t) for f in [1760, 2217, 2637, 3520]) * k * 0.05
    return air + shimmer


def s_rumble(dur=5.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(noise(n, "brown"), 80, 4) * 2.5
    e = np.minimum(t / 0.3, 1) * np.exp(-np.maximum(t - 0.6, 0) / 1.6)
    return x * e


def s_cloth(dur=1.2):
    n = int(dur * SR)
    x = bp(noise(n), 1200, 6000) * lp(np.abs(noise(n)), 25) * 1.8
    t = np.arange(n) / SR
    x *= np.sin(np.pi * np.clip(t / dur, 0, 1))
    th = s_thud(90, 0.4, 0.35)
    a = int(0.75 * SR)
    x[a:a + len(th)] += th[: n - a]
    return x * 0.6


# ----------------------------------------------------------------- ambience beds
def amb_room(n):
    tone = lp(noise(n, "pink"), 400) * 0.03
    fire = crackle(n, density=2.5, amp=0.12)
    return tone + fire


def amb_street(n):
    wind = bp(noise(n, "pink"), 200, 1400) * (0.5 + 0.5 * smooth_noise(n, 0.3)) * 0.07
    torch = lp(noise(n, "brown"), 300) * 0.05 + crackle(n, density=5, amp=0.1)
    return wind + torch


def amb_cell(n):
    # only the cell's low, close room hum (no synthesised water drops: their rising chirps read as
    # electronic beeps rather than water)
    return lp(noise(n, "brown"), 120) * 0.04


def amb_jer(n):
    torch = lp(noise(n, "brown"), 400) * 0.07 + crackle(n, density=8, amp=0.12)
    crowd = bp(noise(n, "pink"), 250, 1100) * (0.4 + 0.6 * smooth_noise(n, 4)) * 0.06
    steps = np.zeros(n)
    t = 0.2
    while t < n / SR - 0.5:
        a = int(t * SR)
        st = s_thud(140 + 60 * rng.random(), 0.15, 0.12)
        steps[a:a + len(st)] += st[: n - a]
        t += 0.32 + 0.2 * rng.random()
    return torch + crowd + steps


def amb_desert(n):
    return bp(noise(n, "pink"), 150, 2600) * (0.35 + 0.65 * smooth_noise(n, 0.4)) * 0.1


def amb_dawn(n):
    breeze = bp(noise(n, "pink"), 200, 1800) * (0.5 + 0.5 * smooth_noise(n, 0.3)) * 0.04
    birds = np.zeros(n)
    t = 0.8
    while t < n / SR - 1:
        a = int(t * SR)
        for c in range(int(2 + 3 * rng.random())):
            L = int(0.09 * SR)
            tt = np.arange(L) / SR
            f0 = 2800 + 1800 * rng.random()
            chirp = np.sin(2 * np.pi * (f0 * tt + 9000 * tt ** 2 * (1 if rng.random() > 0.5 else -1))) * np.sin(np.pi * tt / tt[-1]) * 0.045
            b = a + int(c * 0.12 * SR)
            birds[b:b + L] += chirp[: max(0, n - b)]
        t += 1.2 + 2.5 * rng.random()
    return breeze + birds


AMB = {"lamp_room": amb_room, "room_murmur": amb_room, "street_amb": amb_street, "cell_amb": amb_cell, "jer_amb": amb_jer,
       "desert_amb": amb_desert, "dawn_amb": amb_dawn}
ONE = {"bread_break": (s_bread_break, 0.9), "knock3": (s_knock3, 1.0), "door_unbolt": (s_bolt, 0.6), "door_creak": (lambda: s_creak(1.8), 0.7),
       "chain_tremble": (lambda: s_chains(1.0, 4), 0.35), "chains_move": (lambda: s_chains(0.7, 5), 0.45), "bread_thud": (s_bread_thud, 0.8),
       "breath_shaky": (s_breath_shaky, 0.55),
       "light_swell": (s_light_swell, 0.8), "divine_rumble": (s_rumble, 0.9), "cloth_kneel": (s_cloth, 0.8), "door_bang": (s_door_bang, 1.0),
       "door_close": (s_door_close, 0.8)}


def env_of_time(tl, t):
    for s in tl["shots"]:
        if s["start"] <= t < s["end"]:
            return s["env"], s["id"]
    return "dry", ""


def render(work):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    total = tl["duration"] + 2
    n = int(total * SR)
    out = np.zeros((n, 2))
    # ambience beds follow the shots' environments; contiguous shots share one bed
    bed_of = {"room_warm": amb_room, "street": amb_street, "cell": amb_cell, "memory": amb_jer, "desert": amb_desert, "outdoor": amb_dawn}
    segs = []
    for sh in tl["shots"]:
        if segs and segs[-1][0] == sh["env"]:
            segs[-1][2] = sh["end"]
        else:
            segs.append([sh["env"], sh["start"], sh["end"]])
    for env, t0, t1 in segs:
        if env not in bed_of:
            continue
        L = int((t1 - t0 + 0.8) * SR)
        x = bed_of[env](L)
        fade = np.ones(L)
        fi, fo = int(0.4 * SR), int(0.8 * SR)
        if t0 > 0:  # the film's first frame starts with sound already present
            fade[:fi] = np.linspace(0, 1, fi)
        fade[-fo:] = np.linspace(1, 0, fo)
        x = x * fade
        a2 = int(max(0, t0 - 0.2) * SR) if t0 > 0 else 0
        b2 = min(n, a2 + L)
        out[a2:b2, 0] += x[: b2 - a2]
        out[a2:b2, 1] += x[: b2 - a2] * 0.97
    # one-shots with environment reverb
    for e in tl["sfx"]:
        if e["name"] not in ONE:
            continue
        fn, g = ONE[e["name"]]
        x = fn() * g
        env, _ = env_of_time(tl, e["t"] + 0.05)
        kw = dict(fx.ENV.get(env, fx.ENV["dry"]))
        wet = kw.pop("wet")
        st = fx.reverb(x, SR, wet=min(0.6, wet * 1.4), **kw)
        a = int(e["t"] * SR)
        b = min(n, a + len(st))
        out[a:b] += st[: b - a]
    pk = np.max(np.abs(out))
    if pk > 0.95:
        out *= 0.95 / pk
    sf.write(os.path.join(work, "sfx.wav"), out.astype(np.float32), SR)
    print("sfx rendered", total, "s")


if __name__ == "__main__":
    render(os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work")))
