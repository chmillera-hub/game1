import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"] * sr) + sr
rng = np.random.default_rng(5)
SC = {s["id"]: s for s in tl["scenes"]}
def tag(sc, name):
    """(start, end) of a tagged item, in seconds RELATIVE to its scene's start."""
    for z in SC[sc]["sents"]:
        if z["tag"] == name: return z["start"] - SC[sc]["start"], z["end"] - SC[sc]["start"]
def S0(sc): return SC[sc]["start"]
def lp(x, k): return np.convolve(x, np.ones(max(1, k)) / max(1, k), "same")
def bp(x, lo, hi): return lp(x, int(sr / lo)) - lp(x, int(sr / hi))
def add(buf, t0, x, g=1.0):
    i = int(t0 * sr)
    if i < 0 or i >= len(buf): return
    j = min(len(buf), i + len(x)); buf[i:j] += x[: j - i] * g
env = lambda n, a: np.exp(-np.arange(n) / (sr * a))
def thump(f=70, d=0.2, g=1.0):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * (1 - 0.3 * t / d) * t) * env(n, d / 3) + lp(rng.standard_normal(n), 40) * env(n, d / 5) * 0.6) * g
def bell(f, d=1.8, g=0.2):
    n = int(d * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.3) + 0.3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.15)) * np.exp(-t / (d / 3)) * g
def sparkle(d=2.0, g=0.12):
    out = np.zeros(int(d * sr)); notes = [784, 988, 1175, 1319, 1568, 1760, 2093, 2349]
    for k in range(16):
        f = notes[rng.integers(0, len(notes))]; t0 = rng.uniform(0, d - 0.6); n = int(0.6 * sr); tt = np.arange(n) / sr
        add(out, t0, np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * rng.uniform(0.4, 1))
    return out * g
def breath(d, g=0.25, rise=False):
    n = int(d * sr); t = np.arange(n) / sr; x = bp(rng.standard_normal(n), 500, 2600); x /= (np.abs(x).max() + 1e-6)
    e = (t / d) ** 1.3 if rise else np.minimum(1, t / 0.3) * (1 - t / d) ** 1.5
    return x * e * g
def gust(d=3.0, g=0.12):
    n = int(d * sr); t = np.arange(n) / sr; x = bp(rng.standard_normal(n), 150, 900); x /= (np.abs(x).max() + 1e-6)
    return x * np.sin(np.pi * t / d) ** 2 * g
def cricket(g=0.05):
    n = int(0.16 * sr); t = np.arange(n) / sr; out = np.zeros(int(0.5 * sr))
    for k in range(3): add(out, k * 0.05, np.sin(2 * np.pi * 4300 * t[: int(0.03 * sr)]) * np.hanning(int(0.03 * sr)))
    return out * g
def fly(d=0.9, g=0.07):
    n = int(d * sr); t = np.arange(n) / sr; f = 190 + 25 * np.sin(2 * np.pi * 3 * t)
    return (np.sin(2 * np.pi * np.cumsum(f) / sr) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 2) / sr)) * np.hanning(n) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)) * g

voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for z in sc["sents"]:
        if z["file"]:
            with wave.open(z["file"]) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            add(voice, z["start"], a)
sfx = np.zeros(N, np.float32)
add(sfx, S0("setup") + 0.3, gust(3.2, 0.1))                                              # evening breeze
sp = S0("speech"); s2 = tag("speech", "s2"); seeit = sp + s2[0] + 0.76 * (s2[1] - s2[0])
add(sfx, seeit - 0.2, sparkle(2.4, 0.13)); add(sfx, seeit, bell(1319, 2.2, 0.12))        # the kingdom shimmers into view
od = tag("odds", "odds"); oddsT = "Look, man... we're living with overwhelming odds against us. The Pharisees are super powerful. Rome probably despises me personally. I don't have money. I don't have an army. I don't have political connections. I'm literally just some guy hanging out with you. And they're probably going to kill you. So what are you even trying to say?"
for key in ("The Pharisees are", "Rome probably", "I don't have money", "I don't have an army", "I don't have political", "I'm literally just", "And they're probably"):
    add(sfx, S0("odds") + od[0] + oddsT.index(key) / len(oddsT) * (od[1] - od[0]), thump(220, 0.12, 0.35))   # each worry lands like a stone
dr = tag("drone", "drone"); dT = "If you aren't building the kingdom with me... then what are you doing? Are you going to be an obedient drone? You think that's going to help build the kingdom? You think the kingdom will come if you contribute to the system of death and destruction and hell on earth?"
t_dr = S0("drone") + dr[0] + dT.index("obedient") / len(dT) * (dr[1] - dr[0]); t_sy = S0("drone") + dr[0] + dT.index("system of death") / len(dT) * (dr[1] - dr[0])
for k in range(int((t_sy - t_dr) / 0.5)): add(sfx, t_dr + k * 0.5, thump(90, 0.15, 0.45))   # drones marching in step
n = int(1.8 * sr); tt = np.arange(n) / sr
add(sfx, t_sy, (np.sin(2 * np.pi * 48 * tt) + lp(rng.standard_normal(n), 60) * 1.5) * np.exp(-tt / 0.5) * 0.5)
fo = tag("force", "force"); fT = "The world will force you to see what I'm saying. If not today, then tomorrow. If not tomorrow, then someday in your life. You will see that there is no other way but to build the kingdom now, with me and with the Father."
def fat(s_): return S0("force") + fo[0] + fT.index(s_) / len(fT) * (fo[1] - fo[0])
for s_, f_ in (("If not today", 523), ("then tomorrow", 659), ("then someday", 784)): add(sfx, fat(s_), bell(f_, 1.6, 0.14))
add(sfx, fat("build the kingdom now"), sparkle(2.0, 0.12)); add(sfx, fat("build the kingdom now"), bell(1047, 2.0, 0.14))
# the long silence: crickets, a fly, a tumbleweed
lg = tag("silence", "long"); L0 = S0("silence") + lg[0]; L1 = S0("silence") + lg[1]
t = L0 - 1.0
while t < L1 + 0.2: add(sfx, t, cricket(0.035 + 0.02 * rng.random())); t += 0.55 + 0.25 * rng.random()
for k in range(3): add(sfx, L0 + 1.0 + k * 2.4, fly(0.9, 0.06))
add(sfx, L0 + 2.4, gust(2.6, 0.08))
for k in range(26): add(sfx, L0 + 2.6 + k * 0.17, thump(rng.uniform(300, 420), 0.05, 0.05))
# the sigh
sg = S0("sigh"); inh = tag("sigh", "inhale"); cs = tag("sigh", "cosmic"); ex = tag("sigh", "exhale")
add(sfx, sg + inh[0], breath(inh[1] - inh[0], 0.22, rise=True))
add(sfx, sg + cs[0] + 0.1, breath(4.2, 0.22)); add(sfx, sg + ex[0], breath(3.4, 0.14))
for k, f_ in enumerate((220, 277, 330, 440)):
    n = int(5.0 * sr); tt = np.arange(n) / sr; add(sfx, sg + cs[0] + k * 0.25, np.sin(2 * np.pi * f_ * tt) * np.minimum(1, tt / 1.2) * np.exp(-tt / 2.0) * 0.05)
add(sfx, sg + cs[0] + 1.0, sparkle(5.0, 0.09)); add(sfx, sg + cs[0] + 4.2, sparkle(4.0, 0.08)); add(sfx, sg + cs[0] + 7.6, sparkle(4.0, 0.08))
# soft plucked arpeggio (no constant noise or drone bed): not during the silence
F = lambda m: 440 * 2 ** ((m - 69) / 12)
mood = {"setup": [50, 57, 62, 66], "speech": [50, 57, 62, 66], "stare": [47, 54, 59, 62], "bro": [45, 52, 57, 60], "odds": [45, 52, 57, 60], "drone": [43, 50, 55, 58],
        "force": [48, 55, 60, 64], "sigh": [48, 55, 60, 64, 67]}
arp = np.zeros(N, np.float32)
for sid, notes in mood.items():
    step = 60 / 78; k = 0; t0 = S0(sid) + 0.4
    while t0 < SC[sid]["end"] - 0.5:
        f = F(notes[[0, 2, 1, 3, 2, 1][k % 6]] + 12); n = int(0.7 * sr); tt = np.arange(n) / sr
        add(arp, t0, (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt / 0.1)) * np.exp(-tt / 0.28))
        t0 += step; k += 1
vm = max(np.abs(voice).max(), 1e-6)
duck = np.clip(np.convolve(np.abs(voice), np.ones(int(sr * 0.3)) / (sr * 0.3), "same") * 8, 0, 1)
mix = 0.85 * voice / vm + 0.9 * sfx + 0.055 * arp * (1 - 0.6 * duck)
mix = np.tanh(mix * 1.1) * 0.95
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr)
