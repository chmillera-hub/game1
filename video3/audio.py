import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"] * sr) + sr
rng = np.random.default_rng(7)
SC = {s["id"]: s for s in tl["scenes"]}
def tag(sc, name):
    for z in SC[sc]["sents"]:
        if z["tag"] == name: return z["start"], z["end"]
def lp(x, k): return np.convolve(x, np.ones(k) / k, "same")
def add(buf, t0, x, g=1.0):
    i = int(t0 * sr); j = min(len(buf), i + len(x))
    if i < len(buf) and i >= 0: buf[i:j] += x[: j - i] * g
env = lambda n, a: np.exp(-np.arange(n) / (sr * a))
def thump(f=60, d=0.25, g=1.0):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * (1 - 0.3 * t / d) * t) * env(n, d / 3) + lp(rng.standard_normal(n), 40) * env(n, d / 5) * 0.8) * g
def step(g=1.0): return thump(75, 0.22, g)
voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for z in sc["sents"]:
        if z["file"]:
            with wave.open(z["file"]) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            add(voice, z["start"], a)
sfx = np.zeros(N, np.float32)
# door creak + footsteps (enter)
s0 = SC["enter"]["start"]
n = int(1.7 * sr); t = np.arange(n) / sr
creak = np.sin(2 * np.pi * np.cumsum(150 + 140 * (t / 1.7) + 12 * np.sin(2 * np.pi * 9 * t)) / sr) * 0.12 + lp(rng.standard_normal(n), 6) * 0.05
add(sfx, s0 + 0.3, creak * np.sin(np.pi * t / 1.7) ** 0.7)
for i, ts in enumerate([2.3, 3.0, 3.7, 4.4]): add(sfx, s0 + ts, step(0.55))
# knees + hands hit the floor (kneel)
k0 = SC["kneel"]["start"]; add(sfx, k0 + 0.8, thump(55, 0.3, 0.7)); add(sfx, k0 + 1.35, thump(50, 0.3, 0.5)); add(sfx, k0 + 2.0, thump(45, 0.3, 0.6))
# the shout: boom + rumble
e0 = tag("enough", "enough")[0]; n = int(2.6 * sr); t = np.arange(n) / sr
boom = np.sin(2 * np.pi * 42 * t) * np.exp(-t / 0.9) + lp(rng.standard_normal(n), 120) * 2 * np.exp(-t / 0.5) + np.sin(2 * np.pi * 28 * t) * np.exp(-t / 1.4) * 0.8
add(sfx, e0 - 0.05, boom, 0.9)
# thermal: glitch, heartbeat, scan beeps, door close
t0 = SC["thermal"]["start"]; cut = t0 + 0.9
add(sfx, cut, lp(rng.standard_normal(int(0.25 * sr)), 3) * 0.25 * np.linspace(1, 0, int(0.25 * sr)))
th2 = tag("thermal", "th2")[0]; th3 = tag("thermal", "th3")[0]; lv = tag("thermal", "leave")
tt = cut
while tt < lv[1] - 0.8:
    bpm = np.interp(tt, [cut, th3, lv[0]], [150, 130, 105]); per = 60 / bpm
    add(sfx, tt, thump(62, 0.2, 0.8)); add(sfx, tt + 0.16, thump(52, 0.22, 0.55)); tt += per
for ts in (cut + 0.6, cut + 1.2, th2 + 0.2, th3 + 0.2):
    n = int(0.09 * sr); add(sfx, ts, np.sin(2 * np.pi * 1300 * np.arange(n) / sr) * np.hanning(n) * 0.12)
dc = lv[1] - 1.1
add(sfx, dc, thump(80, 0.35, 1.0)); n = int(0.03 * sr); add(sfx, dc + 0.22, lp(rng.standard_normal(n), 2) * np.hanning(n) * 0.5)
for ts in (lv[0] + 0.0, lv[0] + 0.55): add(sfx, ts, step(0.35))
# flicker shimmer
f0 = tag("alone", "flick")[0] + 1.5; n = int(1.6 * sr); t = np.arange(n) / sr
add(sfx, f0 - 0.05, sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5) * g for f, g in ((1318, .08), (1975, .05), (2637, .035), (3951, .02))))
add(sfx, SC["end"]["start"] + 0.4, sum(np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9) * g for f, g in ((659, .05), (988, .04))))
# fire crackle (whole piece)
fire = lp(rng.standard_normal(N), 25) * 0.05 + lp(rng.standard_normal(N), 400) * 0.35 * 0.07
for _ in range(int(tl["total"] * 9)):
    n = int(rng.uniform(0.006, 0.03) * sr); i = int(rng.uniform(0, N - n))
    fire[i:i + n] += rng.standard_normal(n) * np.linspace(1, 0, n) * rng.uniform(0.02, 0.12)
fire[int(SC["end"]["start"] * sr):] *= 0.0 + np.linspace(1, 0, N - int(SC["end"]["start"] * sr))
# pad
F = lambda m: 440 * 2 ** ((m - 69) / 12)
chords = {"title": [38, 45, 50], "room": [38, 45, 50, 53], "enter": [36, 43, 48, 51], "confess": [34, 41, 46, 49], "silence": [34, 41, 46, 49],
          "kneel": [38, 45, 50, 53], "enough": [31, 38, 43, 46], "thermal": [36, 43, 46, 51], "alone": [43, 50, 55, 59], "end": [43, 50, 55, 62]}
t = np.arange(N) / sr; pad = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    a, b = max(0, int((sc["start"] - 1.5) * sr)), min(N, int((sc["end"] + 1.5) * sr)); tt = t[a:b]; seg = np.zeros(b - a, np.float32)
    for m in chords[sc["id"]]:
        f = F(m); seg += np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 2 * tt + 1) + 0.5 * np.sin(2 * np.pi * f * 1.004 * tt)
    seg *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.1 * tt)
    e = np.minimum(1, np.minimum(np.arange(len(seg)), len(seg) - np.arange(len(seg))) / (1.5 * sr)); pad[a:b] += seg * e / len(chords[sc["id"]])
pad /= np.abs(pad).max()
vm = max(np.abs(voice).max(), 1e-6)
duck = np.clip(np.convolve(np.abs(voice), np.ones(int(sr * 0.3)) / (sr * 0.3), "same") * 8, 0, 1)
mix = 0.85 * voice / vm + 0.9 * sfx + 0.5 * fire * (1 - 0.3 * duck) + 0.14 * pad * (1 - 0.6 * duck)
mix = np.tanh(mix * 1.1) * 0.95
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr)
