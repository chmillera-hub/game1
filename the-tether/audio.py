"""Score, sound design and final mix for The Tether -> build/mix.wav (48 kHz stereo).

Everything is synthesized here. Sound effects are driven by the same curves the
picture uses (lightning flashes, heartbeat, crawl gait, sobs) so they land on
the frame; those functions mirror film.html.
"""
import json, math, os, wave
import numpy as np
from scipy.signal import butter, sosfilt, oaconvolve, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build")
TL = json.load(open(os.path.join(OUT, "timeline.json")))
M, CUES, DUR = TL["marks"], TL["cues"], TL["duration"]
SR = 48000
N = int((DUR + 1) * SR)
rng = np.random.default_rng(7)

# ------------------------------------------------------------- helpers ----
def bus():
    return np.zeros((2, N))

def place(b, sig, t0, gain=1.0, pan=0.0):
    """Add mono (n,) or stereo (2,n) `sig` into bus `b` at time t0 (constant-power pan)."""
    i0 = int(round(t0 * SR))
    if sig.ndim == 1:
        a = (pan + 1) * math.pi / 4
        sig = np.vstack([sig * math.cos(a), sig * math.sin(a)]) * math.sqrt(2)
    if i0 < 0:
        sig, i0 = sig[:, -i0:], 0
    n = min(sig.shape[1], N - i0)
    if n > 0:
        b[:, i0:i0 + n] += sig[:, :n] * gain

def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos"), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos"), x)

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def fade_env(n, att, rel):
    e = np.ones(n)
    a, r = int(att * SR), int(rel * SR)
    if a > 0:
        e[:a] = np.sin(np.linspace(0, math.pi / 2, a)) ** 2
    if r > 0:
        e[-r:] *= np.cos(np.linspace(0, math.pi / 2, r)) ** 2
    return e

def saw(freq_curve):
    ph = np.cumsum(freq_curve / SR) + rng.random()
    return 2 * (ph % 1.0) - 1

def drift(n, depth, rate=0.15):
    """Slow random pitch wander (ratio around 1)."""
    k = max(4, int(n / SR * rate * 4) + 4)
    pts = rng.normal(0, 1, k)
    return 1 + depth * np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)

def reverb_ir(rt60, damp=3500, seed=0, pre=0.02):
    r = np.random.default_rng(seed)
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    tau = rt60 / 6.9
    out = []
    for ch in range(2):
        z = r.normal(0, 1, n)
        low = lp(z, damp)
        ir = low * np.exp(-t / tau) + (z - low) * np.exp(-t / (tau * 0.35))
        ir = np.concatenate([np.zeros(int(pre * SR)), ir])
        out.append(ir / np.sqrt((ir ** 2).sum()))
    return np.array(out)

def reverb(b, ir, wet, dry=1.0):
    y = np.vstack([oaconvolve(b[0], ir[0])[:N], oaconvolve(b[1], ir[1])[:N]])
    return dry * b + wet * y

def smooth(x, fc):
    return lp(x, fc, 1)

# ------------------------------------------- picture curves (mirror JS) ----
def hash_(n):
    n = np.sin(n * 127.1 + 311.7) * 43758.5453
    return n - np.floor(n)

def noise1(x, seed=0):
    i = np.floor(x); f = x - i; u = f * f * (3 - 2 * f)
    return (hash_(i + seed * 57.31) * (1 - u) + hash_(i + 1 + seed * 57.31) * u) * 2 - 1

def sm(t):
    t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

def ramp(t, a, b):
    return sm((t - a) / (b - a))

def win(t, a, b, c, d):
    return ramp(t, a, b) * (1 - ramp(t, c, d))

def crawl_speed(t):
    v = 0.27 * ramp(t, M["jesus"] - 1.5, M["jesus"] + 1.5) * (1 - ramp(t, M["plea"] - 0.5, M["plea"] + 1.8))
    v = v * (1 - win(t, 48.6, 49.5, 51.9, 53.2))
    v = v * (1 - 0.92 * win(t, M["father"] + 1.2, M["father"] + 1.7, M["father"] + 8, M["father"] + 10.5))
    v = v * (1 + 0.3 * noise1(t * 0.45, 4))
    return np.maximum(0, v)

DT = 1 / 120
TT = np.arange(1, int((DUR + 2) / DT) + 1) * DT
PT = np.concatenate([[0], np.cumsum(crawl_speed(TT) * DT)])

def time_of_p(p):
    i = np.searchsorted(PT, p)
    return i * DT if i < len(PT) else None

def sob_level(t):
    return (0.35 * win(t, M["plea"] + 1, M["plea"] + 3, M["withdraw"], M["withdraw"] + 1)
            + 0.75 * ramp(t, M["curl"] + 2, M["curl"] + 6)
            - 0.35 * win(t, M["grief"] + 15.5, M["grief"] + 16.5, M["pullback"] + 6, M["pullback"] + 9))

def bpm(t):
    return (68 + 18 * ramp(t, M["plea"], M["plea"] + 4) + 10 * ramp(t, M["curl"], M["curl"] + 4)
            - 14 * ramp(t, M["pullback"], M["pullback"] + 8))

# ========================================================= INSTRUMENTS ====
def pad(notes, t0, t1, level, att=3.0, rel=4.0, cutoff=1400, voices=3, detune=7, vib=0.0, kind="saw"):
    n = int((t1 - t0 + rel) * SR)
    out = np.zeros((2, n))
    for m in notes:
        f0 = mtof(m)
        for v in range(voices):
            cents = (v - (voices - 1) / 2) * detune
            fc = f0 * 2 ** (cents / 1200) * drift(n, 0.0015)
            if vib:
                fc = fc * (1 + vib * np.sin(2 * math.pi * 5.2 * np.arange(n) / SR + rng.random() * 6))
            s = saw(fc) if kind == "saw" else np.sin(2 * math.pi * np.cumsum(fc / SR))
            pan = (v - (voices - 1) / 2) * 0.6
            a = (pan + 1) * math.pi / 4
            out[0] += s * math.cos(a); out[1] += s * math.sin(a)
    out = np.vstack([lp(out[0], cutoff), lp(out[1], cutoff)])
    out /= max(1, len(notes) * voices) ** 0.5
    return out * fade_env(n, att, rel) * level

def choir(notes, t0, t1, level, att=4, rel=5):
    n = int((t1 - t0 + rel) * SR)
    mono = np.zeros(n)
    for m in notes:
        for v in range(4):
            f = mtof(m) * 2 ** ((v - 1.5) * 6 / 1200) * (1 + 0.004 * np.sin(2 * math.pi * (4.6 + v * 0.3) * np.arange(n) / SR))
            mono += saw(f * drift(n, 0.002))
    voc = bp(mono, 650, 950) * 1.0 + bp(mono, 1050, 1300) * 0.6 + bp(mono, 2600, 3100) * 0.25
    voc = lp(voc, 3500) / (len(notes) * 4) ** 0.5
    st = np.vstack([voc, np.roll(voc, int(0.013 * SR))])
    return st * fade_env(n, att, rel) * level

def piano(m, vel=0.3, dur=7.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = mtof(m); s = np.zeros(n)
    for k in range(1, 8):
        fk = f * k * (1 + 0.0004 * k * k)
        s += np.sin(2 * math.pi * fk * t + rng.random()) * (1 / k ** 1.4) * np.exp(-t * (0.55 + 0.5 * k))
    s += lp(rng.normal(0, 1, n), 2500) * np.exp(-t * 90) * 0.05
    s *= (1 - np.exp(-t * 400))
    return lp(s, 4200) * vel

def bell(m, vel=0.2, dur=8.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = mtof(m); s = np.zeros(n)
    for ratio, amp, dec in [(1, 1, 0.5), (2.0, 0.5, 0.8), (2.76, 0.42, 1.2), (4.07, 0.25, 1.8), (5.43, 0.18, 2.6), (0.5, 0.3, 0.35)]:
        s += np.sin(2 * math.pi * f * ratio * t + rng.random()) * amp * np.exp(-t * dec)
    return s * (1 - np.exp(-t * 600)) * vel

def thunder(close, strength, dur=7.0):
    n = int(dur * SR); t = np.arange(n) / SR
    z = rng.normal(0, 1, n)
    rumble = lp(z, 140, 2) * 6 + lp(z, 420, 2) * 1.5
    am = 0.55 + 0.45 * np.abs(lp(rng.normal(0, 1, n), 6, 1)) * 18
    env = (1 - np.exp(-t * (40 if close else 4))) * np.exp(-t / (2.2 if close else 1.8))
    s = rumble * np.clip(am, 0, 2) * env
    if close:
        crack = hp(z, 900) * np.exp(-t * 18) * 0.9 + lp(z, 2500) * np.exp(-t * 9) * 0.8
        s = s + crack
    s = s / (np.abs(s).max() + 1e-9)
    st = np.vstack([s, np.roll(s, int(0.021 * SR)) * 0.95])
    return st * strength

def heartbeat_thump(gain):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 52 * np.exp(-t * 6)
    s = np.sin(2 * math.pi * np.cumsum(f / SR)) * np.exp(-t * 16) * (1 - np.exp(-t * 300))
    s += lp(rng.normal(0, 1, n), 180) * np.exp(-t * 40) * 0.6
    return s * gain

def breath(dur, center, width, gain, stutter=0):
    n = int(dur * SR); t = np.arange(n) / SR
    z = bp(rng.normal(0, 1, n), center - width, center + width)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    if stutter:
        env *= 0.35 + 0.65 * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * stutter * t + 0.3)))
        env = lp(env, 40, 1)
    return z * env * gain / (np.abs(z).max() + 1e-9)

# ============================================================== VOICES ====
def load_voice(rel):
    with wave.open(os.path.join(OUT, rel)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    g = math.gcd(sr, SR)
    return resample_poly(x, SR // g, sr // g)

def build_voices():
    vN, vJ, vI, vG = bus(), bus(), bus(), bus()
    for c in CUES:
        if c["who"] == "G":
            for k, p in enumerate(c["parts"]):
                x = hp(load_voice(p["file"]), 260)
                place(vG, x, p["start"], gain=[0.55, 0.45, 0.42, 0.35][k], pan=[-0.5, 0.55, 0.0, -0.2][k])
            continue
        x = load_voice(c["file"])
        if c["who"] == "N":
            place(vN, lp(x, 9000), c["start"], gain=0.9)
        elif c["who"] == "J":
            x = lp(hp(x, 120), 6500)
            place(vJ, x, c["start"], gain=0.8)
        else:
            x = lp(hp(x, 140), 5200)
            place(vI, x, c["start"], gain=0.62, pan=-0.05)
            place(vI, x, c["start"] + 0.012, gain=0.25, pan=0.3)   # doubled: inside his head
    vN = reverb(vN, reverb_ir(1.2, 4000, 1), 0.10)
    vJ = reverb(vJ, reverb_ir(2.2, 3500, 2), 0.22)
    vI = reverb(vI, reverb_ir(3.5, 3000, 3), 0.38)
    vG = reverb(vG, reverb_ir(6.0, 2600, 4), 0.85, dry=0.55)
    return vN + vJ + vI + vG

# =============================================================== SCORE ====
def build_score():
    mus = bus()
    m = M
    # (t0, t1, notes, level, kwargs)
    pads = [
        (0.0, 28, [38, 45], 0.20, dict(att=7, rel=5, cutoff=500)),
        (5.0, 27, [74, 81], 0.025, dict(att=6, rel=5, cutoff=6000, kind="sine", voices=2)),
        (24, 55.5, [50, 53, 57], 0.10, dict(att=5, rel=4, cutoff=900)),
        (24, 55.5, [38], 0.10, dict(att=5, rel=4, cutoff=300)),
        (m["father"] + 0.6, 67, [34, 46, 53, 58, 62], 0.19, dict(att=4, rel=4, cutoff=1300, vib=0.002)),
        (66, 76.5, [43, 50, 55, 58, 62], 0.15, dict(att=3, rel=4, cutoff=1200, vib=0.002)),
        (76, 84.5, [45, 52, 57, 62], 0.13, dict(att=3, rel=4, cutoff=1100)),
        (82.5, 96, [38, 50, 53, 57], 0.10, dict(att=4, rel=4, cutoff=900, vib=0.003)),
        (95, 108, [34, 46, 53, 58, 62], 0.10, dict(att=4, rel=5, cutoff=1000, vib=0.003)),
        (106.5, 126.5, [38], 0.10, dict(att=3, rel=4, cutoff=260)),
        (107, 126, [74, 76, 77], 0.03, dict(att=5, rel=4, cutoff=5000, kind="sine", voices=2)),
        (m["hover"] - 1, m["withdraw"] + 1, [63, 69], 0.035, dict(att=4, rel=2, cutoff=3000, kind="sine", voices=2)),
        (m["withdraw"] + 0.3, 138.5, [46, 53, 58, 62, 65], 0.15, dict(att=2.5, rel=4, cutoff=1600, vib=0.004)),
        (138, 146.5, [45, 53, 57, 60, 65], 0.14, dict(att=3, rel=4, cutoff=1500, vib=0.004)),
        (145.7, 158, [43, 50, 55, 58, 62], 0.10, dict(att=3, rel=4, cutoff=1200, vib=0.003)),
        (157.5, 169.5, [41, 53, 57, 60, 65, 69], 0.12, dict(att=3, rel=4, cutoff=2200, vib=0.004)),
        (168.9, 182.5, [46, 53, 58, 62], 0.12, dict(att=3, rel=4, cutoff=1400, vib=0.004)),
        (181.7, 190.5, [43, 55, 58, 62], 0.11, dict(att=3, rel=4, cutoff=1300, vib=0.004)),
        (190, 198, [45, 52, 57, 61, 64], 0.12, dict(att=3, rel=4, cutoff=1400, vib=0.004)),
        (197, 210.5, [38, 50, 57, 62, 65], 0.15, dict(att=3, rel=4, cutoff=1700, vib=0.004)),
        (210, 220, [34, 46, 53, 58, 62, 65], 0.17, dict(att=3, rel=4, cutoff=1900, vib=0.004)),
        (219, DUR - 1, [38, 50, 54, 57, 62, 66], 0.15, dict(att=3, rel=6, cutoff=1500, vib=0.003)),
    ]
    for t0, t1, notes, lvl, kw in pads:
        place(mus, pad(notes, t0, t1, lvl, **kw), t0)
    for t0, t1, notes, lvl in [(m["father"] + 2, 81, [58, 62, 65], 0.06), (m["grief"], 197, [57, 62, 65], 0.05),
                               (204, 222, [62, 65, 69], 0.06), (219, DUR - 1, [62, 66, 69], 0.05)]:
        place(mus, choir(notes, t0, t1, lvl), t0)
    # piano motif: sparse, falling
    motif = [(84.0, 69, .22), (86.6, 65, .18), (89.2, 64, .18), (91.5, 62, .2), (95.6, 74, .2), (97.4, 72, .17), (99.0, 70, .17),
             (101.6, 69, .2), (104.8, 65, .15),
             (m["curl"] + 0.3, 65, .24), (m["curl"] + 1.8, 69, .2), (m["curl"] + 3.3, 72, .2), (m["curl"] + 5.0, 70, .22),
             (m["curl"] + 7.2, 69, .2), (m["curl"] + 9.4, 65, .18), (m["curl"] + 11.4, 67, .18), (m["curl"] + 13.0, 69, .22),
             (m["tether"] + 0.4, 70, .18), (m["tether"] + 3.0, 69, .16), (m["tether"] + 6.0, 65, .16), (m["grief"] + 0.4, 67, .17),
             (m["grief"] + 4.4, 62, .16), (m["grief"] + 8.2, 64, .16),
             (197.6, 74, .2), (199.6, 72, .17), (201.2, 69, .17), (203.2, 65, .16), (205.2, 67, .17), (207.2, 69, .2),
             (210.2, 77, .2), (212.2, 76, .18), (214.2, 74, .2), (216.8, 69, .18), (219.6, 62, .22), (220.4, 66, .18), (221.2, 69, .18)]
    for t, note, v in motif:
        place(mus, piano(note, v), t, pan=0.15 * math.sin(note))
        place(mus, piano(note - 12, v * 0.35), t + 0.01, pan=-0.2)
    # bells: thread sparkles, the falling tear, the title
    r = np.random.default_rng(3)
    t = m["thread"] + 0.8
    while t < m["tether"] + 2:
        place(mus, bell(int(r.choice([77, 79, 81, 84, 86, 89])), 0.035 + 0.03 * r.random(), 5), t, pan=r.uniform(-0.8, 0.8))
        t += r.uniform(0.35, 1.1)
    tear0 = m["grief"] + 9.6
    place(mus, bell(81, 0.08), tear0 - 0.4, pan=0.2)
    place(mus, bell(74, 0.12, 10), tear0 + 5.4, pan=-0.1)
    place(mus, bell(50, 0.10, 10), tear0 + 5.42)
    place(mus, bell(74, 0.07, 10), m["title"])
    # rising swell into the ghost whisper
    n = int(3.2 * SR); tt = np.arange(n) / SR
    swell = hp(rng.normal(0, 1, n), 3000) * (tt / 3.2) ** 3 * 0.06
    place(mus, np.vstack([swell, np.roll(swell, 300)]), m["ghost"] - 3.2)
    return mus

# ================================================================= SFX ====
def build_sfx():
    sfx = bus()
    for f in TL["flashes"]:
        close = f["where"] == "father"
        delay = 0.03 if close else 0.9 + 1.2 * float(hash_(np.array(f["t"])))
        place(sfx, thunder(close, (0.85 if close else 0.32) * f["s"] ** 0.8, 8 if close else 6), f["t"] + delay)
    # heartbeat: thumps where the ember pulses (phase wraps of t*bpm/60)
    t = np.arange(M["plea"], M["pullback"] + 18, 0.001)
    beats = np.floor(t * bpm(t) / 60)
    idx = np.nonzero(np.diff(beats) > 0)[0] + 1
    for tb in t[idx]:
        g = (0.22 * ramp(tb, M["plea"], M["plea"] + 3) + 0.2 * win(tb, M["hover"] - 3, M["hover"], M["curl"], M["curl"] + 4)
             - 0.12 * ramp(tb, M["inner"], M["inner"] + 6) - 0.1 * ramp(tb, M["pullback"] + 2, M["pullback"] + 14))
        g = max(0.0, g)
        if g > 0.005:
            place(sfx, heartbeat_thump(g), tb)
            place(sfx, heartbeat_thump(g * 0.6), tb + 0.17 * 60 / bpm(tb))
    # crawling: cloth drag under the speed curve, a dull touch on each hand plant
    tt = np.arange(N) / SR
    spd = np.interp(tt, np.arange(len(PT)) * DT, np.concatenate([[0], crawl_speed(TT)]))
    drag = bp(rng.normal(0, 1, N), 250, 1800) * smooth(spd, 3) * 0.16
    sfx[0] += drag; sfx[1] += np.roll(drag, 200)
    for o, sf in [(0.0, 0.38), (0.5, 0.38)]:
        k = 0
        while True:
            p = k - o + sf
            tp = time_of_p(p) if p > 0 else None
            if p > PT[-1]:
                break
            if tp is not None and p > 0:
                n = int(0.25 * SR); x = np.arange(n) / SR
                thud = lp(rng.normal(0, 1, n), 300) * np.exp(-x * 30) * 0.5 + np.sin(2 * np.pi * 1900 * x) * np.exp(-x * 25) * 0.015
                place(sfx, thud * 0.35, tp, pan=-0.1)
            k += 1
    # effort breaths while crawling: one exhale per gait cycle
    for k in range(1, int(PT[-1]) + 1):
        tp = time_of_p(k + 0.2)
        if tp:
            place(sfx, breath(0.9, 700, 450, 0.035), tp, pan=0.05)
    # sobs: catches of breath on the heaves the picture shows
    t = np.arange(M["plea"], M["fade"], 0.002)
    sp = t * 0.62 + 0.4 * noise1(t * 0.3, 21)
    ph = sp - np.floor(sp)
    lev = sob_level(t)
    for target, gain, stut in [(0.1, 1.0, 9), (0.3, 0.6, 0)]:
        cross = np.nonzero((ph[:-1] < target) & (ph[1:] >= target))[0]
        for i in cross:
            if lev[i] < 0.05:
                continue
            place(sfx, breath(0.45 if stut else 0.8, 1300 if stut else 600, 700 if stut else 350, 0.06 * lev[i] * gain, stut), t[i] - 0.12, pan=0.05)
    # wind of the void
    w = lp(rng.normal(0, 1, N), 380, 2)
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * tt / 23) + 0.2 * np.sin(2 * np.pi * tt / 7.3)
    wind = w * lfo * (0.05 + 0.05 * ramp(tt, 0, 6) * (1 - ramp(tt, 24, 30)) + 0.03 * ramp(tt, M["pullback"], M["fade"]))
    sfx[0] += wind; sfx[1] += np.roll(wind, 1500)
    return sfx

# ================================================================= MIX ====
def main():
    print("voices..."); voices = build_voices()
    print("score..."); mus = build_score()
    mus = reverb(mus, reverb_ir(4.5, 3000, 11), 0.42)
    print("sfx..."); sfx = build_sfx()
    sfx_wet = reverb(sfx, reverb_ir(3.2, 2500, 12), 0.35)
    # long echoes on the late sobs: "reverberating through the fabric of existence"
    late = sfx_wet * 0
    tt = np.arange(N) / SR
    gate = ramp(tt, M["pullback"] - 1, M["pullback"] + 1)
    for d, g in [(0.45, 0.45), (0.9, 0.3), (1.6, 0.2), (2.5, 0.12)]:
        late += np.roll(sfx_wet * gate, int(d * SR), axis=1) * g
    sfx_wet += late * 0.6
    # duck the score under speech
    env = smooth(np.abs(voices).mean(axis=0), 2.5)
    duck = 1 - 0.55 * np.clip(env / 0.025, 0, 1)
    mix = voices * 1.0 + mus * duck * 1.15 + sfx_wet * 0.9
    # fade the very end
    mix *= 1 - ramp(tt, DUR - 2.5, DUR - 0.2)
    peak = np.abs(mix).max()
    mix = mix / peak * 0.97
    mix = np.tanh(mix * 1.15) / np.tanh(1.15)
    rms = np.sqrt((mix ** 2).mean())
    print(f"peak {peak:.3f} -> normalised; rms {20 * np.log10(rms):.1f} dBFS")
    pcm = (np.clip(mix, -1, 1).T * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, "mix.wav"), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote build/mix.wav", f"{N / SR:.1f}s")


if __name__ == "__main__":
    main()
