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
# soft typing while he posts deep dives (intro, and the start of the boredom scene)
for sid, t0, t1 in (("intro", 0.5, 6.5), ("bored", 0.2, 8.0)):
    t = S0(sid) + t0
    while t < S0(sid) + t1: add(sfx, t, click(0.05 + 0.03 * rng.random())); t += rng.uniform(0.07, 0.26)
bd = tag("bored", "bd"); nb = tag("bored", "nb"); add(sfx, S0("bored") + nb[0] + 1.2, thump(220, 0.08, 0.35)); add(sfx, S0("bored") + nb[0] + 6.4, bell(1175, 1.2, 0.08))
# loneliness: drips, sniffles, a soft sob
lo_ = S0("lonely"); nl = tag("lonely", "nl"); ld = tag("lonely", "ld")
t = lo_ + 1.0
while t < lo_ + ld[1] + 1.5: add(sfx, t, drip(0.08 + 0.05 * rng.random())); t += rng.uniform(0.5, 1.2)
for k in range(5): add(sfx, lo_ + 2.0 + k * 2.7, sniff(0.07))
add(sfx, lo_ + ld[0] - 0.3, sniff(0.1))
for sid in ("fear", "anger", "trapped", "scream", "sad", "irritated", "meaning"):
    t = S0(sid) + 1.5
    while t < SC[sid]["end"] - 1: add(sfx, t, drip(0.035 + 0.02 * rng.random())); t += rng.uniform(1.4, 2.8)
# fear: panic patter, siren, alarm
fr = S0("fear"); nf = tag("fear", "nf"); fd = tag("fear", "fd")
for k in range(int(((fd[1] + 0.8) - (nf[0] + 7.0)) / 0.18)): add(sfx, fr + nf[0] + 7.0 + k * 0.18, thump(rng.uniform(260, 340), 0.04, 0.12))
for k in range(int(((fd[1] + 1.0) - (nf[0] + 7.0)) / 0.5)): add(sfx, fr + nf[0] + 7.0 + k * 0.5, siren(0.5, 0.05))
for k, dt in enumerate((0.0, 0.5, 1.0)): add(sfx, fr + fd[0] + dt - 0.1, thump(120, 0.1, 0.25))
# anger: a shrug, a counter that dings and then buzzes
an = S0("anger"); na = tag("anger", "na"); ad = tag("anger", "ad")
add(sfx, an + na[0] + 0.6, whoosh(0.35, 0.18, 200, 900)); add(sfx, an + ad[0] + 0.5, bell(1319, 1.0, 0.1)); add(sfx, an + ad[0] + 2.2, thump(90, 0.35, 0.45))
n = int(0.5 * sr); tt = np.arange(n) / sr; add(sfx, an + ad[0] + 2.2, np.sign(np.sin(2 * np.pi * 110 * tt)) * np.minimum(1, tt / 0.01) * (1 - tt / 0.5) * 0.06)
# trapped: bars clang, troll pings, a rising alarm for the pain gauge
tr = S0("trapped"); nt = tag("trapped", "nt"); nt3 = tag("trapped", "nt3"); nt4 = tag("trapped", "nt4"); nt2 = tag("trapped", "nt2")
for k in range(5): add(sfx, tr + nt[0] + 4.0 + k * 0.28, bell(rng.choice([420, 520, 630]), 0.9, 0.06)); add(sfx, tr + nt[0] + 4.0 + k * 0.28, thump(80, 0.12, 0.3))
for k in range(5): add(sfx, tr + nt2[0] + 1.0 + k * 0.4, thump(70, 0.25, 0.3))
for k, off in enumerate((1.8, 2.5, 3.2)): add(sfx, tr + nt3[0] + off, bell(880 - 70 * k, 0.9, 0.07))
T4 = "But right there, in close physical proximity to other people, there's no telling what could happen. I could be dehumanized, or gaslit, or ostracized, or told to get lost. And then my loneliness pain could go beyond a ten."
for key in ("dehumanized", "gaslit", "ostracized", "told to get lost"): add(sfx, tr + nt4[0] + T4.index(key) / len(T4) * (nt4[1] - nt4[0]), thump(60, 0.3, 0.45))
g0 = tr + nt4[0] + T4.index("And then") / len(T4) * (nt4[1] - nt4[0]); n = int(3.0 * sr); tt = np.arange(n) / sr
add(sfx, g0, np.sin(2 * np.pi * np.cumsum(300 + 700 * (tt / 3.0) ** 2) / sr) * np.minimum(1, tt / 0.3) * np.minimum(1, (3.0 - tt) / 0.3) * 0.05)
# scream: a harsh burst and the room flinching
sm = S0("scream"); ns = tag("scream", "ns")
add(sfx, sm + ns[0] + 1.0, whoosh(0.6, 0.3, 120, 1500)); add(sfx, sm + ns[0] + 1.1, thump(60, 0.4, 0.5))
# sadness arrives with a warm sparkle
sd_ = S0("sad"); nsa = tag("sad", "nsa")
add(sfx, sd_ + nsa[0] + 1.2, sparkle(2.4, 0.12)); add(sfx, sd_ + nsa[0] + 1.4, chord([262, 330, 392, 523], 3.4, 0.07))
# irritated: the world scrolls by, then the spotlight
ir = S0("irritated"); nir = tag("irritated", "nir"); sd3 = tag("irritated", "sd3")
add(sfx, ir + nir[0] + 1.0, thump(70, 0.25, 0.3))
for k in range(9): add(sfx, ir + nir[0] + 6.2 + k * 1.0, bell(rng.choice([784, 988, 1175]), 0.7, 0.04))
add(sfx, ir + sd3[0] - 0.4, whoosh(0.8, 0.25, 150, 1200)); add(sfx, ir + sd3[0] + 1.4, chord([262, 330, 392, 494], 3.4, 0.08))
# meaning: three zeros land, then a warm close
me = S0("meaning"); nm = tag("meaning", "nm"); nend = tag("meaning", "nend")
for k in range(3): add(sfx, me + nm[0] + 10.6 + k * 0.5, thump(70, 0.3, 0.45))
add(sfx, me + nend[0] + 0.2, chord([262, 330, 392, 523, 659], 5.0, 0.08)); add(sfx, me + nend[0] + 0.5, sparkle(3.0, 0.07))
for i, key in enumerate(("understanding", "find plans", "advocate")): add(sfx, me + nend[0] + ("That's why understanding my emotions matters. It's how I can find plans, and take action, to advocate for my own spiritual and emotional growth.".index(key)) / 140.0 * (nend[1] - nend[0]), bell([784, 988, 1319][i], 1.2, 0.07))
# gentle plucked score (no constant noise or drone bed): wistful minor, then warmer once sadness arrives
F = lambda m: 440 * 2 ** ((m - 69) / 12)
mood = {"title": [45, 52, 57], "intro": [45, 52, 57, 60], "bored": [45, 52, 57, 60], "lonely": [45, 52, 57, 60], "fear": [50, 57, 62, 65], "anger": [43, 50, 55, 58],
        "trapped": [43, 50, 55, 58], "scream": [41, 48, 53, 56], "sad": [48, 55, 60, 64], "irritated": [48, 55, 60, 64], "meaning": [48, 55, 60, 64, 67]}
arp = np.zeros(N, np.float32)
for sid, notes in mood.items():
    spd = 60 / 70; k = 0; t0 = S0(sid) + 0.4
    while t0 < SC[sid]["end"] - 0.5:
        f = F(notes[[0, 2, 1, 3, 2, 1][k % 6] % len(notes)] + 12); n = int(0.7 * sr); tt = np.arange(n) / sr
        add(arp, t0, (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt / 0.1)) * np.exp(-tt / 0.3)); t0 += spd; k += 1
vm = max(np.abs(voice).max(), 1e-6)
duck = np.clip(np.convolve(np.abs(voice), np.ones(int(sr * 0.3)) / (sr * 0.3), "same") * 8, 0, 1)
mix = 0.85 * voice / vm + 0.9 * sfx + 0.05 * arp * (1 - 0.65 * duck)
mix = np.tanh(mix * 1.1) * 0.95
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr, "peak", float(np.abs(mix).max()))
