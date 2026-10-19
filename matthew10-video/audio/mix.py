"""Mix dialogue, score and synthesized sound design into the final soundtrack.

Usage: python mix.py BUILD_DIR SCORE_WAV OUT_WAV
  BUILD_DIR holds timeline.json and lines/<id>.wav from prepare.py.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve, resample_poly

SR = 48000
rng = np.random.default_rng(7)


# ------------------------------------------------------------------ helpers
def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, btype="low", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, btype="high", fs=SR, output="sos"), x)


def mixsig(*sigs):
    """sum signals of different lengths (pads to the longest)"""
    n = max(len(x) for x in sigs)
    out = np.zeros(n)
    for x in sigs:
        out[: len(x)] += x
    return out


def db(v):
    return 10 ** (v / 20)


def env_ad(n, a, d):
    """attack/decay envelope in samples"""
    e = np.ones(n)
    na, nd = max(1, int(a * SR)), max(1, int(d * SR))
    e[:na] = np.linspace(0, 1, na)
    if nd < n:
        e[-nd:] *= np.linspace(1, 0, nd)
    return e


def place(bus, sig, t, gain=1.0, pan=0.0):
    """add a mono or stereo signal into a stereo bus at time t (s)"""
    i = int(t * SR)
    if i >= bus.shape[0] or i + len(sig) <= 0:
        return
    if sig.ndim == 1:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        sig = np.stack([sig * l * 1.414, sig * r * 1.414], 1)
    s0 = max(0, -i)
    sig = sig[s0:]
    i = max(0, i)
    n = min(len(sig), bus.shape[0] - i)
    bus[i:i + n] += sig[:n] * gain


def ir(rt60, predelay=0.01, bright=6000, length=None, stereo=True):
    n = int((length or rt60 * 1.2) * SR)
    t = np.arange(n) / SR
    out = []
    for _ in range(2 if stereo else 1):
        x = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)
        x = lp(x, bright)
        x[: int(predelay * SR)] = 0
        out.append(x / np.sqrt(np.sum(x ** 2)))
    return np.stack(out, 1) if stereo else out[0]


def reverb(mono, imp, wet):
    dry = np.stack([mono, mono], 1)
    w = np.stack([fftconvolve(mono, imp[:, 0])[: len(mono) + len(imp) - 1],
                  fftconvolve(mono, imp[:, 1])[: len(mono) + len(imp) - 1]], 1)
    out = np.zeros_like(w)
    out[: len(dry)] += dry * (1 - wet * 0.5)
    out += w * wet
    return out


# ------------------------------------------------------------------ synthesized sounds
def noise(d):
    return rng.standard_normal(int(d * SR))


def brown(d):
    x = np.cumsum(rng.standard_normal(int(d * SR)))
    x = hp(x, 20)
    return x / (np.abs(x).max() + 1e-9)


def click(freq=3000, d=0.012, q=0.5):
    x = noise(d) * np.exp(-np.arange(int(d * SR)) / (SR * d * 0.25))
    return bp(x, freq * (1 - q * 0.5), min(freq * (1 + q), SR / 2 - 100))


def tick(high=True):
    n = int(0.05 * SR)
    x = np.zeros(n)
    c = click(3800 if high else 2600, 0.02) * 0.9
    x[: len(c)] += c
    x += np.sin(2 * np.pi * (1900 if high else 1500) * np.arange(n) / SR) * np.exp(-np.arange(n) / (SR * 0.008)) * 0.25
    return x


def clink(f=2200, d=0.6, amp=1.0):
    t = np.arange(int(d * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t + rng.random() * 6) * np.exp(-t / (dec * d))
            for m, a, dec in [(1, 1, 0.35), (2.76, 0.6, 0.2), (5.4, 0.35, 0.12), (8.93, 0.2, 0.07)])
    return x * amp * 0.25


def chirp(f0, f1, d, amp=1.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = np.linspace(f0, f1, n)
    ph = 2 * np.pi * np.cumsum(f) / SR
    e = np.sin(np.pi * np.arange(n) / n) ** 1.5
    return np.sin(ph) * e * amp


def birdsong(d, density=1.0, seed=1):
    r = np.random.default_rng(seed)
    out = np.zeros(int(d * SR))
    t = 0.0
    while t < d - 0.5:
        # a phrase of 2-6 chirps
        n = r.integers(2, 7)
        base = r.uniform(3200, 5200)
        for _ in range(n):
            dur = r.uniform(0.035, 0.09)
            c = chirp(base * r.uniform(1.0, 1.25), base * r.uniform(0.75, 0.95), dur, r.uniform(0.3, 1.0))
            i = int(t * SR)
            out[i:i + len(c)] += c[: max(0, min(len(c), len(out) - i))]
            t += dur + r.uniform(0.03, 0.09)
        t += r.uniform(0.5, 2.5) / density
    return out


def flutter(d=0.6, amp=1.0):
    n = int(d * SR)
    t = np.arange(n) / SR
    mod = (0.5 + 0.5 * np.sin(2 * np.pi * 17 * t)) ** 2
    x = bp(noise(d), 300, 3000) * mod * np.sin(np.pi * t / d)
    return x * amp


def crackle(d, rate=12, amp=1.0, seed=3):
    r = np.random.default_rng(seed)
    out = np.zeros(int(d * SR))
    for _ in range(int(d * rate)):
        c = click(r.uniform(1500, 6000), r.uniform(0.004, 0.02))
        i = int(r.uniform(0, d - 0.03) * SR)
        out[i:i + len(c)] += c * r.uniform(0.2, 1.0)
    return out * amp


def hum(d, f=120, amp=1.0, flicker=None):
    t = np.arange(int(d * SR)) / SR
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.3 for k in range(1, 8))
    x += 0.15 * bp(noise(d), 2000, 6000)
    if flicker is not None:
        x *= flicker(t)
    return x * amp / 3


def babble(d, amp=1.0):
    t = np.arange(int(d * SR)) / SR
    x = bp(noise(d), 250, 1800, 3)
    mod = 0.6 + 0.4 * np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 0.7 * t + 1)
    return x * mod * amp


def typing(d, rate=7, amp=1.0, seed=5):
    r = np.random.default_rng(seed)
    out = np.zeros(int(d * SR) + SR)
    t = 0.0
    while t < d:
        c = mixsig(click(r.uniform(1800, 3500), 0.015), 0.5 * click(r.uniform(400, 800), 0.03))
        i = int(t * SR)
        out[i:i + len(c)] += c * r.uniform(0.5, 1.0)
        t += r.exponential(1 / rate) + 0.04
    return out[: int(d * SR)] * amp


def buzz(d, amp=1.0):
    t = np.arange(int(d * SR)) / SR
    x = np.sign(np.sin(2 * np.pi * 165 * t)) * 0.5 + np.sin(2 * np.pi * 330 * t) * 0.3
    gate = ((t % 0.6) < 0.38).astype(float)
    gate = lp(gate, 40)
    return lp(x, 2500) * gate * amp


def impact(amp=1.0):
    d = 3.0
    t = np.arange(int(d * SR)) / SR
    f = 70 * np.exp(-t * 1.5) + 32
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    hit = lp(noise(d), 3000) * np.exp(-t * 18)
    ring = sum(np.sin(2 * np.pi * fr * t) * np.exp(-t * dc) * a for fr, dc, a in [(523, 1.2, 0.3), (1240, 1.8, 0.2), (2210, 2.5, 0.12)])
    return (boom * 1.0 + hit * 0.5 + ring * 0.6) * amp


def glass(crack=True, amp=1.0, seed=9):
    r = np.random.default_rng(seed)
    d = 1.2 if crack else 2.5
    out = np.zeros(int(d * SR))
    n = 25 if crack else 140
    for _ in range(n):
        f = r.uniform(2500, 9000)
        dur = r.uniform(0.05, 0.4)
        t = np.arange(int(dur * SR)) / SR
        s = np.sin(2 * np.pi * f * t) * np.exp(-t / (dur * 0.2)) * r.uniform(0.2, 1)
        tt = r.uniform(0, 0.25 if crack else 1.6) ** (1.5 if not crack else 1)
        i = int(tt * SR)
        out[i:i + len(s)] += s[: max(0, min(len(s), len(out) - i))]
    out += crackle(d, 60 if crack else 120, 1.2, seed + 1)
    return out * amp * 0.3


def whoosh(d=1.2, amp=1.0, up=True):
    n = int(d * SR)
    x = noise(d)
    out = np.zeros(n)
    seg = 2048
    for s in range(0, n, seg):
        u = s / n if up else 1 - s / n
        f = 300 + 3000 * u
        out[s:s + seg] = bp(x[s:s + seg], f * 0.7, f * 1.3)
    return out * np.sin(np.pi * np.arange(n) / n) * amp


def footstep(amp=1.0):
    d = 0.18
    t = np.arange(int(d * SR)) / SR
    return (lp(noise(d), 400) * np.exp(-t * 40) + bp(noise(d), 1500, 4000) * np.exp(-t * 60) * 0.3) * amp


# ------------------------------------------------------------------ timeline helpers
def word_times(line):
    words = line["text"].split()
    asr = [w for w in line.get("words", []) if any(c.isalpha() for c in w[2])]
    n = len(words)
    if len(asr) >= 2:
        return [line["start"] + asr[min(len(asr) - 1, round(i * (len(asr) - 1) / max(1, n - 1)))][0] for i in range(n)]
    total = sum(len(w) + 1 for w in words)
    out, acc = [], 0
    for w in words:
        out.append(line["start"] + acc / total * (line["end"] - line["start"]))
        acc += len(w) + 1
    return out


def main():
    build = Path(sys.argv[1])
    tl = json.loads((build / "timeline.json").read_text())
    T = tl["duration"] + 0.5
    n = int(T * SR)
    voice = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    sc = {s["id"]: s for s in tl["scenes"]}
    ln = {l["id"]: l for l in tl["lines"]}
    W = lambda lid, i: word_times(ln[lid])[max(0, min(len(ln[lid]["text"].split()) - 1, i))]

    # ---------------------------------------------------------- dialogue
    rooms = {
        "table": (ir(0.55, 0.012, 5000), 0.16), "sword": (ir(2.2, 0.03, 4500), 0.22), "mask": (ir(0.35, 0.006, 7000), 0.12),
        "cross": (ir(2.4, 0.03, 4500), 0.22), "office": (ir(0.7, 0.015, 5000), 0.14), "park": (ir(0.25, 0.02, 6000), 0.06),
        "sparrows": (ir(2.2, 0.03, 5000), 0.2), "call": (ir(0.4, 0.008, 6000), 0.1), "road": (ir(2.2, 0.03, 5000), 0.2),
        "epilogue": (ir(0.6, 0.015, 6500), 0.12),
    }
    bedroom_start = ln["L15"]["end"] + 0.7
    for l in tl["lines"]:
        a, sr = sf.read(build / "lines" / f"{l['id']}.wav", dtype="float32")
        a = resample_poly(a, SR // 24000, 1).astype(np.float64) if sr == 24000 else a.astype(np.float64)
        gain = 1.0
        imp, wet = rooms[l["scene"]]
        if l["who"] == "narrator":
            a = a * 1.05
            imp, wet = ir(1.8, 0.02, 5000), 0.14
        if l["who"] == "ai":
            # the AI: a touch of air and shimmer so it reads as a different kind of presence
            a = a + 0.25 * hp(a, 4000)
            imp, wet = ir(1.2, 0.02, 7000), 0.18
            gain = 0.95
        if l.get("fx") == "phone":
            a = 0.72 * bp(a, 320, 3400, 3) * 1.6 + 0.28 * a
        if l["scene"] == "mask" and l["start"] >= bedroom_start and l["who"] == "maya":
            imp, wet = ir(0.3, 0.005, 7000), 0.06                  # close and dry in the dark bedroom
        out = reverb(a, imp, wet) * gain
        place(voice, out, l["start"])

    # ---------------------------------------------------------- sound design
    # 1. table: room tone, cutlery, clock
    t0, t1 = sc["table"]["start"], sc["table"]["end"]
    place(sfx, lp(brown(t1 - t0 + 1), 300) * db(-44), t0)
    q = ln["L13"]["end"]
    for s in np.arange(t0 + 0.5, t1 + 0.6, 1.0):
        g = db(-40) if s < q else db(-27)                          # the clock gets loud in the silence
        place(sfx, tick(int(s) % 2 == 0), s, g, 0.6)
    cut_end = ln["L5"]["start"]
    for s in np.arange(0.6, cut_end, 0.55):
        if rng.random() < 0.55:
            place(sfx, clink(rng.uniform(2600, 3400), 0.3, 0.6), s + rng.uniform(0, 0.1), db(-33), rng.uniform(-0.3, 0.3))
    for s in np.arange(ln["L7"]["start"], ln["L8"]["start"], 0.55):
        if rng.random() < 0.5:
            place(sfx, clink(rng.uniform(2600, 3400), 0.3, 0.6), s, db(-34), 0.0)
    place(sfx, clink(2100, 0.9, 1.0), ln["L8"]["end"] + 0.25, db(-24), 0.0)                 # fork set down
    place(sfx, lp(noise(0.7), 900) * env_ad(int(0.7 * SR), 0.05, 0.4), ln["L13"]["end"] + 0.2, db(-36), 0.4)  # chair shifts
    # 2. sword: fire, impact
    s0, s1 = sc["sword"]["start"], sc["sword"]["end"]
    fire = lp(brown(s1 - s0 + 2), 200) * 0.6 + crackle(s1 - s0 + 2, 14, 0.8)
    place(sfx, fire * env_ad(len(fire), 1.5, 1.5), s0 - 0.5, db(-34))
    strike = W("N1", len(ln["N1"]["text"].split()) - 1) + 0.15
    place(sfx, whoosh(0.6, 1.0, False), strike - 0.55, db(-26))
    place(sfx, impact(1.0), strike, db(-17))
    # 3. mask: bathroom hum, typing, message pops
    m0 = sc["mask"]["start"]
    place(sfx, hum(bedroom_start - m0 + 0.5, 120, 1.0) * env_ad(int((bedroom_start - m0 + 0.5) * SR), 0.3, 0.5), m0, db(-50))
    place(sfx, lp(brown(sc["mask"]["end"] - bedroom_start + 1), 250), bedroom_start, db(-48))
    place(sfx, typing(ln["L16"]["end"] - ln["L16"]["start"] + 0.2, 7, 1.0), ln["L16"]["start"] - 0.6, db(-34), 0.1)
    for lid in ["L18", "L20"]:
        place(sfx, typing(ln[lid]["end"] - ln[lid]["start"], 6, 0.8, seed=sum(map(ord, lid))), ln[lid]["start"] - 0.2, db(-38), 0.1)
    for lid in ["L17", "L19", "L21"]:
        pop = mixsig(chirp(880, 1320, 0.09, 0.5), chirp(1320, 1760, 0.12, 0.3))
        place(sfx, pop, ln[lid]["start"] - 0.25, db(-36))
    # 4. cross: glass
    words4 = ln["N4"]["text"].split()
    idx = lambda w, frm=0: next((i for i in range(frm, len(words4)) if words4[i].lower().startswith(w)), 0)
    tcrack, tfall = W("N4", idx("whoever", 2)), W("N4", idx("loses"))
    place(sfx, glass(True, 1.0), tcrack, db(-20))
    place(sfx, glass(False, 1.0, 11), tfall, db(-17))
    place(sfx, impact(0.5), tfall, db(-24))
    place(sfx, lp(brown(sc["cross"]["end"] - ln["N5"]["start"] + 1), 300), ln["N5"]["start"] - 0.5, db(-44))
    # 5. office: hum, flicker buzz, typing, murmur; then overload
    o0, o1 = sc["office"]["start"], sc["office"]["end"]
    tover = ln["L26"]["end"] + 0.4
    od = o1 - o0 + 0.1
    flick = lambda t: 0.6 + 0.4 * (np.sin(t * 37) * np.sin(t * 11.3) > 0.7)
    grow = np.clip((np.arange(int(od * SR)) / SR - (tover - o0)) / 3.0, 0, 1)
    swell = 1 + grow * 4.0
    place(sfx, hum(od, 120, 1.0, flick) * swell, o0, db(-36))
    place(sfx, babble(od, 1.0) * swell, o0, db(-40))
    place(sfx, typing(od, 5, 1.0, 21) * swell, o0, db(-40), -0.4)
    place(sfx, typing(od, 4, 1.0, 22) * swell, o0, db(-43), 0.5)
    tin = np.sin(2 * np.pi * 5600 * np.arange(int(od * SR)) / SR) * grow ** 2
    place(sfx, tin, o0, db(-30))
    # 6. park: birds, breeze, wings
    p0, p1 = sc["park"]["start"], sc["park"]["end"]
    pd = p1 - p0 + 0.5
    place(sfx, birdsong(pd, 1.2, 4), p0, db(-34), -0.4)
    place(sfx, birdsong(pd, 0.8, 5), p0, db(-38), 0.5)
    place(sfx, bp(brown(pd), 200, 1200) * env_ad(int(pd * SR), 1.0, 1.0), p0, db(-40))
    for tt in [p0 + 0.9, p0 + 1.9, ln["L28"]["start"] + 1.3, ln["L29"]["start"] + 0.6]:
        place(sfx, flutter(0.5), tt, db(-30), 0.3)
    # 7. sparrows: the flock takes off
    q0, q1 = sc["sparrows"]["start"], sc["sparrows"]["end"]
    for k in range(10):
        place(sfx, flutter(0.7, 1.0), q0 + 0.2 + k * 0.18, db(-30 - k), rng.uniform(-0.6, 0.6))
    place(sfx, whoosh(2.0, 1.0, True), q0, db(-34))
    place(sfx, birdsong(q1 - q0, 0.6, 8), q0, db(-40), 0.3)
    place(sfx, flutter(0.6), ln["N7"]["start"] - 0.4, db(-28), 0.4)
    # 8. call: vibrate, answer, hang up
    k0 = sc["call"]["start"]
    place(sfx, buzz(1.9), k0 + 0.1, db(-30))
    place(sfx, chirp(660, 990, 0.12, 0.6), ln["L31"]["start"] - 0.9, db(-38))
    t_hang = ln["L36"]["end"] + 0.5
    place(sfx, chirp(990, 660, 0.15, 0.6), t_hang, db(-36))
    place(sfx, lp(brown(sc["call"]["end"] - k0 + 1), 250), k0, db(-47))
    pop = mixsig(chirp(880, 1320, 0.09, 0.5), chirp(1320, 1760, 0.12, 0.3))
    for lid in ["L38", "L39"]:
        place(sfx, pop, ln[lid]["start"] - 0.25, db(-38))
    # 9. road: night wind, crickets into dawn birds, footsteps
    r0, r1 = sc["road"]["start"], sc["road"]["end"]
    rd = r1 - r0 + 1.5
    place(sfx, bp(brown(rd), 100, 900) * env_ad(int(rd * SR), 0.8, 1.0), r0 - 0.5, db(-36))
    crick = np.sin(2 * np.pi * 4300 * np.arange(int(rd * SR)) / SR) * ((np.arange(int(rd * SR)) / SR * 18) % 1 < 0.25)
    crick *= np.clip(1 - np.arange(int(rd * SR)) / (rd * SR), 0, 1)
    place(sfx, crick, r0 - 0.5, db(-46), -0.5)
    place(sfx, birdsong(rd, 0.6, 12) * np.linspace(0, 1, int(rd * SR)), r0 - 0.5, db(-38), 0.4)
    for k, s in enumerate(np.arange(r0, r1 + 0.6, 0.506)):
        place(sfx, footstep(1.0), s, db(-34) * (1 - 0.5 * (s - r0) / (r1 - r0 + 1)), -0.15 if k % 2 else 0.15)
    # 10. epilogue: airy room, a message, typing, birds at the window
    e0, e1 = sc["epilogue"]["start"], tl["duration"]
    ed = e1 - e0 + 0.5
    place(sfx, birdsong(ed, 0.5, 14), e0, db(-42), 0.5)
    place(sfx, lp(brown(ed), 400) * 0.6, e0, db(-48))
    t_buzz = ln["L41"]["end"] + 0.6
    place(sfx, buzz(0.9), t_buzz, db(-31))
    place(sfx, typing(0.9, 8, 1.0, 31), t_buzz + 4.1, db(-36))
    place(sfx, mixsig(chirp(880, 1320, 0.09, 0.5), chirp(1320, 1760, 0.12, 0.3)), t_buzz + 5.05, db(-36))
    place(sfx, flutter(0.6), W("N9", 6) - 0.5, db(-30), 0.4)

    # ---------------------------------------------------------- music with ducking under the voices
    mus, msr = sf.read(sys.argv[2], dtype="float64")
    if msr != SR:
        mus = resample_poly(mus, SR, msr, axis=0)
    mus = np.pad(mus, ((0, max(0, n - len(mus))), (0, 0)))[:n]
    v = np.abs(voice).mean(1)
    win = int(0.05 * SR)
    venv = np.sqrt(np.convolve(v ** 2, np.ones(win) / win, mode="same"))
    act = (venv > db(-42)).astype(float)
    # attack 60 ms, release 500 ms
    sm = np.zeros(n)
    a_k, r_k = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.5 * SR))
    st = 0.0
    step = 64
    for i in range(0, n, step):
        x = act[i]
        st += ((a_k if x > st else r_k) * step) * (x - st)
        st = min(1.0, max(0.0, st))
        sm[i:i + step] = st
    music_gain = np.full(n, db(9.0))
    for s in tl["scenes"]:
        i0, i1 = int(s["start"] * SR), int(s["end"] * SR)
        inter = s["id"] in ("sword", "cross", "sparrows", "road")
        music_gain[i0:i1] = db(7.0 if inter else 9.0)
    duck = np.full(n, db(-8.0))
    for s in tl["scenes"]:
        if s["id"] in ("sword", "cross", "sparrows", "road"):
            duck[int(s["start"] * SR):int(s["end"] * SR)] = db(-10.0)
    gain = music_gain * (1 - sm * (1 - duck))
    music = mus * gain[:, None]

    mix = voice * db(0) + sfx * db(1.5) + music
    # speech-to-background ratio per line (intelligibility check)
    bg = sfx * db(1.5) + music
    ratios = []
    for l in tl["lines"]:
        i0, i1 = int(l["start"] * SR), int(l["end"] * SR)
        vr = np.sqrt(np.mean(voice[i0:i1] ** 2)) + 1e-9
        br = np.sqrt(np.mean(bg[i0:i1] ** 2)) + 1e-9
        ratios.append((round(20 * np.log10(vr / br), 1), l["id"], l["scene"]))
    ratios.sort()
    print("speech-to-background dB (lowest first):", ratios[:8])
    print("median:", ratios[len(ratios) // 2][0])
    Path(sys.argv[3] + ".snr.json").write_text(json.dumps(ratios))
    # gentle bus limiter
    peak = np.abs(mix).max()
    if peak > 0.98:
        mix *= 0.98 / peak
    sf.write(sys.argv[3], mix.astype(np.float32), SR, subtype="FLOAT")
    print(f"wrote {sys.argv[3]}  {T:.1f}s  peak {peak:.2f}")


if __name__ == "__main__":
    main()
