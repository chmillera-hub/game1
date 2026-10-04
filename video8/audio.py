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
def thunder(g=0.5):
    n = int(1.6 * sr); return lp(rng.standard_normal(n), 60) * env(n, 0.5) * g * 3
def crack(g=0.4):
    n = int(0.25 * sr); return rng.standard_normal(n) * env(n, 0.04) * g
def blip(f=1400, g=0.08):
    n = int(0.08 * sr); t = np.arange(n) / sr; return np.sin(2 * np.pi * f * t) * np.hanning(n) * g
def roll(d=1.5, g=0.05):
    n = int(d * sr); return lp(rng.standard_normal(n), 30) * (1 + 0.5 * np.sin(np.arange(n) / sr * 40)) * np.hanning(n) * g * 2
def chime(g=0.1):
    o = bell(1568, 1.0, g); b2 = bell(2093, 0.8, g * 0.6); o[:len(b2)] += b2; return o
def groan(d=2.5, g=0.18):
    n = int(d * sr); t = np.arange(n) / sr; f = 70 + 25 * np.sin(t * 3); return (np.sin(2 * np.pi * np.cumsum(f) / sr) + 0.5 * lp(rng.standard_normal(n), 8)) * np.hanning(n) * g
def roar(d=2.0, g=0.12):
    n = int(d * sr); return lp(rng.standard_normal(n), 12) * np.hanning(n) * g * 2
def murmur(d, g=0.04):
    n = int(d * sr); return lp(rng.standard_normal(n), 25) * np.hanning(n) * g * 3
def at(sid, name, off=0.0): return S0(sid) + tag(sid, name)[0] + off
# castle: crowd roar, a distant crack
add(sfx, at("castle", "c1"), roar(3.0, 0.1)); add(sfx, at("castle", "c2", 1.0), roar(3.0, 0.12))
for k in range(4): add(sfx, at("castle", "c2", 4 + 3 * k), crack(0.12))
# tower: lever, uplink blips, thunder-free laugh stinger
sy = tag("tower", "sync"); add(sfx, S0("tower") + sy[0] + 0.2, thump(90, 0.3, 0.9)); add(sfx, S0("tower") + sy[0] + 0.5, click(0.5))
for k in range(18): add(sfx, S0("tower") + sy[0] + 0.7 + k * 0.13, blip(900 + 90 * k, 0.07))
al = tag("tower", "alive"); add(sfx, S0("tower") + al[0], crack(0.5)); add(sfx, S0("tower") + al[0], thunder(0.4))
for k in range(5): add(sfx, S0("tower") + al[1] - 2.2 + k * 0.4, bell(440 * (1 + 0.12 * (k % 3)), 0.8, 0.05))
# gates
add(sfx, at("gates", "g1", 3.0), groan(3.0)); add(sfx, S0("gates") + tag("gates", "open")[0], groan(2.5, 0.2))
add(sfx, at("gates", "g2"), roll(4.0, 0.06)); add(sfx, at("gates", "g2", 1.0), click(0.6)); add(sfx, at("gates", "g3", 0.3), chime(0.1))
# bot1: chime, heart-rate beeps
add(sfx, at("bot1", "b1", -0.1), sparkle(1.2, 0.1))
b = tag("bot1", "b1"); t = b[0] + 3.0
while t < b[1]: add(sfx, S0("bot1") + t, blip(1000, 0.09)); t += 0.5
# disappoint: crowd murmur, shuffling
d1 = tag("disappoint", "d1"); add(sfx, S0("disappoint") + d1[0], murmur(4, 0.03))
d2 = tag("disappoint", "d2"); t = d2[0]
while t < d2[1]: add(sfx, S0("disappoint") + t, thump(120, 0.08, 0.15)); t += 0.45
# supervisor: chime, rock trip thud
add(sfx, at("super", "b2"), chime(0.08)); add(sfx, at("super", "s2", 1.5), thump(60, 0.3, 0.7)); add(sfx, at("super", "s2", 1.6), crack(0.15))
# week: wheel rolls, footsteps, window slams
w1 = tag("week", "w1"); add(sfx, S0("week") + w1[0], roll(w1[1] - w1[0], 0.05))
w2 = tag("week", "w2")
for k in range(4): add(sfx, S0("week") + w2[0] + 0.5 + k * 0.9, thump(110, 0.18, 0.5)); add(sfx, S0("week") + w2[0] + 0.5 + k * 0.9, crack(0.1))
add(sfx, at("week", "b3"), chime(0.07))
# pub: clinks and murmur
p1 = tag("pub", "p1"); add(sfx, S0("pub") + p1[0], murmur(p1[1] - p1[0] + 4, 0.025))
for k in range(5): add(sfx, S0("pub") + p1[1] + 0.5 + k * 1.3, bell(2400 + 150 * (k % 3), 0.35, 0.05))
add(sfx, at("pub", "wp", 0.2), chime(0.08))
# end: soft wind-less chords
e1 = tag("end", "e1"); add(sfx, S0("end") + e1[0], chord([261.6, 329.6, 392.0], 6, 0.05)); e2 = tag("end", "e2")
add(sfx, S0("end") + e2[0], chord([220.0, 277.2, 329.6, 440.0], 8, 0.06)); add(sfx, S0("end") + e2[1] - 2, sparkle(2.5, 0.1))
# sparse plucked arpeggio
mus = np.zeros(N, np.float32)
def pluck(f, d=1.2, g=0.05):
    n = int(d * sr); t = np.arange(n) / sr; return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.35) * g
for sid, notes, step, g in (("title", [220, 261.6, 329.6], 0.6, 0.04), ("end", [261.6, 329.6, 392, 523], 0.7, 0.05), ("tower", [196, 233, 293], 0.8, 0.03)):
    s = SC[sid]; t = s["start"]; k = 0
    while t < s["end"]: add(mus, t, pluck(notes[k % len(notes)], 1.2, g)); t += step; k += 1
# ducking
vabs = np.abs(voice); vs = lp(vabs, int(0.25 * sr)); duck = 1 - 0.55 * np.clip(vs * 14, 0, 1)
mix = voice * 1.0 + (sfx + mus) * duck
mix = np.tanh(mix * 1.1) * 0.92
with wave.open("mix.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr)
