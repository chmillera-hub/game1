import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"] * sr) + sr
rng = np.random.default_rng(13)
SC = {s["id"]: s for s in tl["scenes"]}
def tag(sc, name):
    """(start, end) of a tagged item, in seconds RELATIVE to its scene's start."""
    for z in SC[sc]["sents"]:
        if z["tag"] == name: return z["start"] - SC[sc]["start"], z["end"] - SC[sc]["start"]
def S0(sc): return SC[sc]["start"]
def lp(x, k): return np.convolve(x, np.ones(max(1, k)) / max(1, k), "same")
def add(buf, t0, x, g=1.0):
    i = int(t0 * sr)
    if i < 0 or i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += x[: j - i] * g
env = lambda n, a: np.exp(-np.arange(n) / (sr * a))
def thump(f=70, d=0.2, g=1.0):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * (1 - 0.3 * t / d) * t) * env(n, d / 3) + lp(rng.standard_normal(n), 40) * env(n, d / 5) * 0.6) * g
def click(g=0.05):
    n = int(0.02 * sr); return (lp(rng.standard_normal(n), 2) * np.hanning(n)) * g
def drip(g=0.12):
    n = int(0.25 * sr); t = np.arange(n) / sr; f = 1100 * np.exp(-t / 0.06) + 500
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * env(n, 0.07) * g
def bell(f, d=1.6, g=0.15):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.3)) * np.exp(-t / (d / 3)) * g
def chord(notes, d=3.0, g=0.07, att=0.4):
    n = int(d * sr); t = np.arange(n) / sr; out = np.zeros(n)
    for f in notes: out += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)
    return out / len(notes) * np.minimum(1, t / att) * np.minimum(1, (d - t) / (d * 0.5)) * g
def sparkle(d=2.0, g=0.12):
    out = np.zeros(int(d * sr)); notes = [784, 988, 1175, 1319, 1568, 1760, 2093]
    for k in range(14):
        f = notes[rng.integers(0, len(notes))]; t0 = rng.uniform(0, d - 0.6); n = int(0.6 * sr); tt = np.arange(n) / sr
        add(out, t0, np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * rng.uniform(0.4, 1))
    return out * g
def sniff(g=0.09):
    n = int(0.28 * sr); t = np.arange(n) / sr; x = lp(rng.standard_normal(n), 4) - lp(rng.standard_normal(n), 40); x = x / (np.abs(x).max() + 1e-6)
    return x * (np.sin(np.pi * t / 0.28) ** 2) * (1 + 0.4 * np.sin(2 * np.pi * 30 * t)) * g
def siren(d=0.5, g=0.09, lo=640, hi=880):
    n = int(d * sr); t = np.arange(n) / sr; f = np.where((t * 4) % 1 < 0.5, lo, hi); return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.minimum(1, t / 0.02) * g
def whoosh(d=0.6, g=0.3, lo=300, hi=2500):
    n = int(d * sr); t = np.arange(n) / sr; x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(8):
        f = lo * (hi / lo) ** (k / 7); out += np.convolve(x, np.sin(2 * np.pi * f * np.arange(0, 0.004, 1 / sr)) / 50, "same") * np.exp(-((t / d - (k / 8 + 0.1)) ** 2) / 0.04)
    return out / (np.abs(out).max() + 1e-6) * g * np.hanning(n)

voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for z in sc["sents"]:
        if z["file"]:
            with wave.open(z["file"]) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            add(voice, z["start"], a)
sfx = np.zeros(N, np.float32)
def crack(g=0.4):
    n = int(0.25 * sr); return rng.standard_normal(n) * env(n, 0.04) * g
def blip(f=1400, g=0.08, d=0.08):
    n = int(d * sr); t = np.arange(n) / sr; return np.sin(2 * np.pi * f * t) * np.hanning(n) * g
def squelch(g=0.2, d=0.5):
    n = int(d * sr); t = np.arange(n) / sr; f = 300 + 500 * np.sin(t * 40) ** 2
    return (np.sin(2 * np.pi * np.cumsum(f) / sr) * 0.6 + lp(rng.standard_normal(n), 6) * 0.5) * np.hanning(n) * g
def shing(g=0.12, d=0.9):
    n = int(d * sr); t = np.arange(n) / sr; return (np.sin(2 * np.pi * 3100 * t) + 0.6 * np.sin(2 * np.pi * 4650 * t) + 0.3 * np.sin(2 * np.pi * 6200 * t)) * np.exp(-t / 0.25) * np.minimum(1, t / 0.01) * g
def growl(g=0.12, d=0.8):
    n = int(d * sr); t = np.arange(n) / sr; return lp(rng.standard_normal(n), 60) * (1 + 0.8 * np.sin(2 * np.pi * 28 * t)) * np.hanning(n) * g * 3
def wobble(g=0.08, d=1.5, f0=520):
    n = int(d * sr); t = np.arange(n) / sr; f = f0 + 60 * np.sin(2 * np.pi * 5 * t); return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.hanning(n) * g
def crackle(d, g=0.04):
    out = np.zeros(int(d * sr)); t = 0.0
    while t < d - 0.05: add(out, t, click(g * rng.uniform(0.3, 1.2))); t += rng.exponential(0.12)
    return out
def at(sid, name, off=0.0): return S0(sid) + tag(sid, name)[0] + off
def end_(sid, name, off=0.0): return S0(sid) + tag(sid, name)[1] + off
# couch: little game blips from the TV, a wiggle when the idea crawls in
for k in range(10): add(sfx, at("couch", "c1", 0.3 + k * 0.6), blip(660 + 110 * (k % 4), 0.03))
add(sfx, end_("couch", "c1", -2.6), wobble(0.06, 1.2, 700)); add(sfx, at("couch", "c2", 0.2), bell(988, 0.8, 0.06))
add(sfx, at("couch", "c2", 3.5), wobble(0.05, 3.0, 440))
# ship: the tadpole floats out, squelch on implant, a stamp
add(sfx, at("ship", "m1", 0.6), wobble(0.06, 2.5, 380))
im = tag("ship", "implant"); add(sfx, S0("ship") + im[0], whoosh(0.9, 0.12, 400, 1800)); add(sfx, S0("ship") + im[0] + 1.15, squelch(0.25)); add(sfx, S0("ship") + im[0] + 1.2, thump(60, 0.4, 0.5))
add(sfx, at("ship", "s1", 3.0), thump(90, 0.25, 0.9)); add(sfx, at("ship", "s1", 3.0), crack(0.15))
# wake: groans of waking (soft thumps), sword drawn, the leap
add(sfx, at("wake", "w1", 3.2), thump(110, 0.2, 0.3)); add(sfx, at("wake", "w1", 4.0), thump(100, 0.2, 0.3))
add(sfx, at("wake", "w1", 7.6), wobble(0.04, 1.4, 600))
add(sfx, at("wake", "r1", 0.5), shing(0.13)); lp_ = tag("wake", "leap"); add(sfx, S0("wake") + lp_[0], whoosh(0.8, 0.2, 300, 2400))
# freeze: everything stops with a resonant ping and a reverse swell
add(sfx, S0("freeze") + 0.02, bell(1568, 2.4, 0.14)); add(sfx, S0("freeze") + 0.02, bell(1046, 2.6, 0.08)); add(sfx, S0("freeze") + 0.05, crack(0.12))
add(sfx, at("freeze", "f1", 2.0), whoosh(1.6, 0.08, 200, 900)); add(sfx, at("freeze", "f1", 3.9), thump(80, 0.25, 0.6))
for k, o in enumerate((2.2, 4.3, 8.0)): add(sfx, at("freeze", "f2", o), blip(880 + 220 * k, 0.07, 0.12))
# boost: growls, sword swings and poofs
for k in range(6): add(sfx, S0("boost") + 2.4 + k * 1.9, growl(0.09, 0.7))
b2 = tag("boost", "b2")
for i in range(6):
    dt = S0("boost") + b2[0] + 0.6 + i * 1.1; add(sfx, dt - 0.15, whoosh(0.35, 0.12, 600, 3000)); add(sfx, dt, thump(140, 0.15, 0.45)); add(sfx, dt + 0.05, whoosh(0.6, 0.06, 200, 900))
add(sfx, at("boost", "b1", 7.6), wobble(0.05, 2.0, 330))
# scales: wooden creaks as the beam tips, a thud for NO
for o in (0.5, 4.5, 8.5, 9.5): add(sfx, at("scales", "q1", o), thump(180, 0.12, 0.25))
add(sfx, at("scales", "q2", 0.3), bell(784, 1.2, 0.06)); add(sfx, at("scales", "q3", 0.3), thump(70, 0.4, 0.9)); add(sfx, at("scales", "q3", 1.0), thump(160, 0.2, 0.3))
# camp: soft fire crackle (sparse clicks only), the ranger's glowing flex
c = SC["camp"]; add(sfx, c["start"], crackle(c["end"] - c["start"], 0.035))
add(sfx, at("camp", "r3", 0.8), wobble(0.05, 1.0, 520))
# money: coin clink, ghostly swells for the workers
for o in (0.4, 0.55): add(sfx, at("money", "o1", o), bell(2400, 0.5, 0.06))
for o in (2.0, 3.5, 5.0): add(sfx, at("money", "o2", o), chord([196.0, 233.1, 293.7], 2.0, 0.04))
# end: the coin pulled away, closing chords
add(sfx, at("end", "e2", 2.0), wobble(0.04, 6.0, 300))
e3 = tag("end", "e3"); add(sfx, S0("end") + e3[0], chord([220.0, 261.6, 329.6], 4, 0.06)); add(sfx, S0("end") + e3[0] + 2.0, chord([174.6, 220.0, 261.6, 349.2], 6, 0.07)); add(sfx, S0("end") + e3[0] + 2.0, sparkle(2.5, 0.08))
mus = np.zeros(N, np.float32)
def pluck(f, d=1.2, g=0.05):
    n = int(d * sr); t = np.arange(n) / sr; return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.35) * g
for sid, notes, step, g in (("title", [220, 261.6, 329.6, 415.3], 0.55, 0.04), ("camp", [196, 246.9, 293.7], 0.8, 0.03), ("end", [220, 261.6, 329.6, 440], 0.75, 0.04)):
    s = SC[sid]; t = s["start"]; k = 0
    while t < s["end"]: add(mus, t, pluck(notes[k % len(notes)], 1.2, g)); t += step; k += 1
vabs = np.abs(voice); vs = lp(vabs, int(0.25 * sr)); duck = 1 - 0.55 * np.clip(vs * 14, 0, 1)
mix = voice * 1.0 + (sfx + mus) * duck
mix = np.tanh(mix * 1.1) * 0.92
with wave.open("mix.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr)
