import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"] * sr) + sr
rng = np.random.default_rng(3)
SC = {s["id"]: s for s in tl["scenes"]}
def tag(sc, name):
    for z in SC[sc]["sents"]:
        if z["tag"] == name: return z["start"], z["end"]
def lp(x, k): return np.convolve(x, np.ones(k) / k, "same")
def bp(x, lo, hi): return lp(x, max(1, int(sr / lo))) - lp(x, max(1, int(sr / hi)))
def add(buf, t0, x, g=1.0):
    i = int(t0 * sr)
    if i < 0 or i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += x[: j - i] * g
env = lambda n, a: np.exp(-np.arange(n) / (sr * a))
tt = lambda d: np.arange(int(d * sr)) / sr
def thump(f=70, d=0.25, g=1.0):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * (1 - 0.3 * t / d) * t) * env(n, d / 3) + lp(rng.standard_normal(n), 40) * env(n, d / 5) * 0.8) * g
def whoosh(d=0.6, f0=300, f1=2400, g=0.3):
    n = int(d * sr); t = np.arange(n) / sr; x = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):
        f = f0 * (f1 / f0) ** (k / 7); out += np.convolve(x, np.sin(2 * np.pi * f * np.arange(0, 0.004, 1 / sr)) / 50, "same") * np.exp(-((t / d - (k / 8 + 0.1)) ** 2) / 0.04)
    return out / (np.abs(out).max() + 1e-6) * g * np.hanning(n)
def pop(g=1.0):
    n = int(0.5 * sr); t = np.arange(n) / sr
    s = np.sin(2 * np.pi * np.cumsum(1100 * np.exp(-t / 0.03) + 180) / sr) * np.exp(-t / 0.05) + rng.standard_normal(n) * np.exp(-t / 0.004) * 0.6
    return (s + 0.4 * np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.15)) * g
def sparkle(d=2.0, g=0.12):
    out = np.zeros(int(d * sr)); notes = [784, 988, 1175, 1319, 1568, 1760, 2093, 2349]
    for k in range(18):
        f = notes[rng.integers(0, len(notes))]; t0 = rng.uniform(0, d - 0.6); n = int(0.6 * sr); t = np.arange(n) / sr
        add(out, t0, np.sin(2 * np.pi * f * t) * np.exp(-t / 0.18) * rng.uniform(0.4, 1))
    return out * g
def roar(d=2.2, g=0.5):
    n = int(d * sr); t = np.arange(n) / sr; x = bp(rng.standard_normal(n), 250, 1800)
    v = np.zeros(n)
    for k in range(26): f = rng.uniform(180, 520); v += np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * rng.uniform(4, 8) * t)) * 0.03
    e = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 0.5)
    return (x / (np.abs(x).max() + 1e-6) * 0.9 + v) * e * g

voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for z in sc["sents"]:
        if z["file"]:
            with wave.open(z["file"]) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            add(voice, z["start"], a)
sfx = np.zeros(N, np.float32)
# the demand: the crowd roars, the gauntlet hums
d0, r0 = tag("demand", "dem"), tag("demand", "roar"); st = SC["demand"]["start"]
add(sfx, st + d0[0] + 2.0, roar(r0[1] - (d0[0] + 2.0) + 0.3, 0.45))
h0 = tag("demand", "hum")[0]; n = int((SC["snap"]["start"] + 0.9 - st - h0) * sr)
if n > 0:
    t = np.arange(n) / sr; hum = (np.sin(2 * np.pi * 82 * t) + 0.6 * np.sin(2 * np.pi * 164 * t) + 0.3 * np.sin(2 * np.pi * 246 * t + 1)) * (0.4 + 0.6 * t / t[-1]) * (0.8 + 0.2 * np.sin(2 * np.pi * 5 * t))
    add(sfx, st + h0, hum * 0.12)
# the snap: soft pop + sparkle as the food appears
p0 = SC["snap"]["start"] + tag("snap", "pop")[0] + 0.3
add(sfx, p0, pop(0.7)); add(sfx, p0 + 0.2, sparkle(2.4, 0.14))
# the crowd freezes: a low gasp/murmur
# rage + flip: stomping, table flip and loaves
f0 = SC["flip"]["start"]; fn = tag("flip", "flipn")[0]
for k in range(6): add(sfx, f0 + fn + 0.4 + k * 0.42, thump(90, 0.2, 0.5))
tf = f0 + fn + 3.0
add(sfx, tf, thump(55, 0.6, 1.0)); add(sfx, tf, lp(rng.standard_normal(int(0.5 * sr)), 30) * env(int(0.5 * sr), 0.15) * 0.8)
for k in range(12): add(sfx, tf + 0.15 + k * 0.09, thump(rng.uniform(180, 320), 0.1, rng.uniform(0.15, 0.35)))
# phasing through: airy whooshes; the table is reset
ph = f0 + tag("flip", "phase")[0]
add(sfx, ph + 1.1, whoosh(1.2, 200, 3000, 0.4)); add(sfx, ph + 4.4, sparkle(1.5, 0.1)); add(sfx, ph + 4.4, whoosh(0.9, 400, 2400, 0.25))
# violence: punch passes through, soldier tumbles, hand through smoke
v0 = SC["violence"]["start"]; pn = tag("violence", "punch")[0]
add(sfx, v0 + pn + 1.8, whoosh(0.5, 300, 2600, 0.45)); add(sfx, v0 + pn + 3.4, thump(60, 0.4, 0.9)); add(sfx, v0 + pn + 3.4, lp(rng.standard_normal(int(0.4 * sr)), 20) * env(int(0.4 * sr), 0.1) * 0.5)
add(sfx, v0 + pn + 6.0, whoosh(0.8, 250, 1800, 0.3))
# the soldiers storm off
l0 = SC["leave"]["start"]; sm = tag("leave", "storm")[0]
for k in range(14): add(sfx, l0 + sm + 2.2 + k * 0.45, thump(100, 0.18, 0.35))
s2 = l0 + tag("leave", "snap2")[0] + 0.4
add(sfx, s2, pop(0.7)); add(sfx, s2 + 0.1, sparkle(2.4, 0.14))
# crowd murmur throughout, softer after the snap; fire-free outdoor air
mur = bp(rng.standard_normal(N), 200, 1400) * 0.05
lvl = np.ones(N, np.float32) * 0.8
mur *= (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * np.arange(N) / sr + 1))
# warm score: pad + gentle plucked arpeggio (minor -> major after the snap)
F = lambda m: 440 * 2 ** ((m - 69) / 12)
mood = {"title": [45, 52, 57], "square": [45, 52, 57, 60], "demand": [43, 50, 55, 58], "snap": [48, 55, 60, 64], "stunned": [48, 55, 60, 64], "rage": [50, 57, 62, 65],
        "flip": [47, 54, 59, 62], "violence": [50, 57, 62, 65], "leave": [48, 55, 60, 64], "metaphor": [48, 55, 60, 64, 67], "end": [48, 55, 60, 64, 67, 72]}
bright = {"snap", "stunned", "leave", "metaphor", "end"}
t = np.arange(N) / sr; pad = np.zeros(N, np.float32); arp = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    a, b = max(0, int((sc["start"] - 1.5) * sr)), min(N, int((sc["end"] + 1.5) * sr)); tq = t[a:b]; seg = np.zeros(b - a, np.float32); notes = mood[sc["id"]]
    for m in notes:
        f = F(m); seg += np.sin(2 * np.pi * f * tq) + 0.4 * np.sin(2 * np.pi * f * 2 * tq + 1) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tq)
    seg *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.1 * tq)
    e = np.minimum(1, np.minimum(np.arange(len(seg)), len(seg) - np.arange(len(seg))) / (1.5 * sr)); pad[a:b] += seg * e / len(notes)
    if sc["id"] in bright:
        step = 60 / 104 / 2; k = 0; tt0 = sc["start"]
        while tt0 < sc["end"] - 0.3:
            f = F(notes[k % len(notes)] + 12); n = int(0.5 * sr); tq2 = np.arange(n) / sr
            add(arp, tt0, np.sin(2 * np.pi * f * tq2) * np.exp(-tq2 / 0.18) + 0.3 * np.sin(2 * np.pi * f * 2 * tq2) * np.exp(-tq2 / 0.1), 1.0)
            tt0 += step; k += 1
pad /= np.abs(pad).max()
vm = max(np.abs(voice).max(), 1e-6)
duck = np.clip(np.convolve(np.abs(voice), np.ones(int(sr * 0.3)) / (sr * 0.3), "same") * 8, 0, 1)
mix = 0.85 * voice / vm + 0.9 * sfx + mur * (1 - 0.4 * duck) + 0.13 * pad * (1 - 0.6 * duck) + 0.07 * arp * (1 - 0.5 * duck)
mix = np.tanh(mix * 1.1) * 0.95
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr)
