import json, wave, numpy as np
tl = json.load(open("timeline.json")); sr = tl["sr"]; N = int(tl["total"] * sr) + sr
rng = np.random.default_rng(11)
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
def step(g=0.4): return thump(110, 0.1, g)
def knock(g=0.4):
    n = int(0.09 * sr); t = np.arange(n) / sr
    return (np.sin(2 * np.pi * 900 * t) + 0.6 * np.sin(2 * np.pi * 1700 * t) + lp(rng.standard_normal(n), 3) * 0.5) * env(n, 0.02) * g
def whoosh(d=0.6, g=0.3, lo=300, hi=2500):
    n = int(d * sr); t = np.arange(n) / sr; x = rng.standard_normal(n); out = np.zeros(n)
    for k in range(8):
        f = lo * (hi / lo) ** (k / 7); out += np.convolve(x, np.sin(2 * np.pi * f * np.arange(0, 0.004, 1 / sr)) / 50, "same") * np.exp(-((t / d - (k / 8 + 0.1)) ** 2) / 0.04)
    return out / (np.abs(out).max() + 1e-6) * g * np.hanning(n)
def sparkle(d=2.0, g=0.12):
    out = np.zeros(int(d * sr)); notes = [784, 988, 1175, 1319, 1568, 1760, 2093, 2349]
    for k in range(16):
        f = notes[rng.integers(0, len(notes))]; t0 = rng.uniform(0, d - 0.6); n = int(0.6 * sr); tt = np.arange(n) / sr
        add(out, t0, np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * rng.uniform(0.4, 1))
    return out * g
def chord(notes, d=3.0, g=0.07, att=0.4):
    n = int(d * sr); t = np.arange(n) / sr; out = np.zeros(n)
    for f in notes: out += np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t)
    return out / len(notes) * np.minimum(1, t / att) * np.minimum(1, (d - t) / (d * 0.5)) * g
def whistle(notes, dur=0.28, g=0.08):
    out = []
    for f in notes:
        n = int(dur * sr); t = np.arange(n) / sr; fr = f * (1 + 0.012 * np.sin(2 * np.pi * 6 * t)) * (1 + 0.04 * np.exp(-t / 0.03))
        out.append(np.sin(2 * np.pi * np.cumsum(fr) / sr) * np.hanning(n) * (0.8 + 0.2 * np.sin(2 * np.pi * 5 * t)) * g + lp(rng.standard_normal(n), 6) * 0.01 * np.hanning(n))
    return np.concatenate(out)
def bark(f0=520, g=0.22):
    n = int(0.16 * sr); t = np.arange(n) / sr; fr = f0 * (1 - 0.35 * t / 0.16)
    return (np.sin(2 * np.pi * np.cumsum(fr) / sr) + 0.5 * np.sin(4 * np.pi * np.cumsum(fr) / sr) + lp(rng.standard_normal(n), 5) * 0.8) * np.exp(-t / 0.06) * g
def pant(g=0.05):
    n = int(0.22 * sr); t = np.arange(n) / sr; x = lp(rng.standard_normal(n), 8) - lp(rng.standard_normal(n), 60); return x / (np.abs(x).max() + 1e-6) * np.hanning(n) * g

voice = np.zeros(N, np.float32)
for sc in tl["scenes"]:
    for z in sc["sents"]:
        if z["file"]:
            with wave.open(z["file"]) as w: a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
            add(voice, z["start"], a)
sfx = np.zeros(N, np.float32)
# --- the walk: a whistled tune, footsteps, a stone kicked
tune = [659, 784, 880, 784, 659, 523, 587, 659, 523, 440, 523, 587]
w0 = S0("walk"); w1 = tag("walk", "w1"); wh = tag("walk", "whistle"); kk = tag("walk", "kick"); kd = tag("walk", "kicked"); dg = tag("walk", "dogw")
add(sfx, w0 + 0.8, whistle(tune, 0.3, 0.05)); add(sfx, w0 + wh[0] + 0.1, whistle(tune[::-1][:7] + tune[:4], 0.28, 0.09))
for k in range(int((kd[1] + 0.8 - 0.2) / 0.52)): add(sfx, w0 + 0.2 + k * 0.52, step(0.3))
add(sfx, w0 + kk[0] + 2.8, thump(160, 0.12, 0.7)); add(sfx, w0 + kk[0] + 2.85, knock(0.3)); add(sfx, w0 + kk[0] + 3.8, knock(0.2))
# --- ticket: a stamp, a poof as Death leaves
tk = tag("ticket", "tk"); add(sfx, S0("ticket") + tk[1] - 2.4, thump(90, 0.2, 0.7)); add(sfx, S0("ticket") + tk[1] - 0.8, whoosh(0.9, 0.35))
# --- the cross: stretch, cough, jaw clatters to the floor, the divine light
cr = S0("cross"); c1 = tag("cross", "c1"); c2 = tag("cross", "c2"); dl = tag("cross", "delay"); br = tag("cross", "bring")
for k in range(7): add(sfx, cr + c1[0] + 4.6 + k * 0.03, thump(rng.uniform(180, 260), 0.05, 0.05))
add(sfx, cr + c1[0] + 4.6, thump(200, 0.08, 0.18))                                          # a little cough
for k in range(14): add(sfx, cr + c2[0] + 0.15 + k * 0.045 * (1 + k * 0.12), knock(0.5 * 0.8 ** (k / 3)))   # jaw clattering down
add(sfx, cr + c2[0] + 0.7, thump(70, 0.35, 0.8)); add(sfx, cr + c2[0], chord([523, 659, 784, 1047], 3.2, 0.07)); add(sfx, cr + c2[0] + 0.2, sparkle(2.6, 0.12))
add(sfx, cr + dl[0] - 0.4, thump(130, 0.22, 0.35)); n = int(0.25 * sr); tt = np.arange(n) / sr
add(sfx, cr + dl[0] - 0.15, np.sin(2 * np.pi * np.cumsum(260 - 150 * tt / 0.25) / sr) * np.hanning(n) * 0.18)   # gulp
# --- carry: heavy lift, thieves vanish in fire, then rise as light
cy = S0("carry"); c3 = tag("carry", "c3"); th = tag("carry", "thieves"); pa = tag("carry", "para")
add(sfx, cy + c3[0] + 3.0, thump(45, 0.6, 1.0)); add(sfx, cy + c3[0] + 3.0, lp(rng.standard_normal(int(0.5 * sr)), 30) * env(int(0.5 * sr), 0.15) * 0.5)
for off in (2.4, 3.4): add(sfx, cy + th[0] + off, whoosh(0.8, 0.4, 150, 1400))                      # the thieves vanish in fire
for off in (2.7, 3.7): add(sfx, cy + th[0] + off, chord([110, 131, 165, 220], 1.4, 0.10, 0.05)); add(sfx, cy + th[0] + off, thump(60, 0.3, 0.4))   # two ominous stabs: devil souls
# --- whisper: the souls turn divine, then Death vanishes in smoke
wh = S0("whisper"); wl = tag("whisper", "will"); rl = tag("whisper", "rules")
add(sfx, wh + wl[1] + 0.4, sparkle(3.0, 0.13)); add(sfx, wh + wl[1] + 0.8, chord([392, 494, 587, 784], 3.0, 0.07)); add(sfx, wh + wl[1] + 0.4, whoosh(1.2, 0.2, 400, 3000))
add(sfx, wh + rl[1] + 0.5, whoosh(1.2, 0.4, 150, 1800))
# --- arrive: Death pops into heaven in smoke, drops Jesus (loud thud), the Father's boom, an awkward wait
ar = S0("arrive"); pp = tag("arrive", "pop"); thd = tag("arrive", "thud"); arise = tag("arrive", "arise"); land = thd[1] - 0.45
add(sfx, ar + pp[0] + 0.2, whoosh(1.4, 0.45, 150, 1800)); add(sfx, ar + pp[0] + 0.6, thump(70, 0.25, 0.5))
n = int(0.55 * sr); tt = np.arange(n) / sr
add(sfx, ar + land - 0.55, np.sin(2 * np.pi * np.cumsum(1400 - 1000 * tt / 0.55) / sr) * np.hanning(n) * 0.07)
n = int(2.0 * sr); tt = np.arange(n) / sr
add(sfx, ar + land, (np.sin(2 * np.pi * 52 * tt) + 0.6 * np.sin(2 * np.pi * 38 * tt) + lp(rng.standard_normal(n), 90) * 1.4) * np.exp(-tt / 0.45) * 0.95)
add(sfx, ar + arise[0], chord([392, 494, 587, 784], 3.0, 0.07)); add(sfx, ar + arise[0] + 0.2, sparkle(2.4, 0.1)); add(sfx, ar + arise[0] + 1.0, sparkle(2.4, 0.07))
st = tag("arrive", "stand"); gd = tag("arrive", "getdog")
for k in range(4): add(sfx, ar + st[0] + 1.8 + k * 0.28, whoosh(0.2, 0.1, 800, 3000))
for k in range(5): add(sfx, ar + gd[0] + 0.3 + k * 0.5, step(0.3))
# --- the dog
dgs = S0("dog"); bk = tag("dog", "bark"); jm = tag("dog", "jump"); cd = tag("dog", "cuddle")
for k in range(int(2.6 / 0.07)): add(sfx, dgs + bk[0] - 0.4 + k * 0.07, thump(rng.uniform(300, 420), 0.03, 0.12))     # paws pattering
for k, off in enumerate((0.0, 0.5, 0.95)): add(sfx, dgs + bk[0] + off, bark(520 - 40 * k))
add(sfx, dgs + jm[0] + 2.6, whoosh(0.6, 0.25, 400, 2200)); add(sfx, dgs + jm[0] + 3.5, thump(120, 0.14, 0.4))
add(sfx, dgs + jm[0] + 3.7, bark(760, 0.14))
for k in range(8): add(sfx, dgs + cd[0] + 0.1 + k * 0.28, pant(0.06))
add(sfx, dgs + cd[0], sparkle(2.0, 0.06))
# --- light plucked score (no constant noise or drone bed)
F = lambda m: 440 * 2 ** ((m - 69) / 12)
mood = {"ticket": [45, 52, 57, 60], "walk": [50, 57, 62, 65], "carry": [45, 52, 57, 60], "whisper": [48, 55, 60, 64], "arrive": [48, 55, 60, 64, 67], "dog": [48, 55, 60, 64, 67]}
arp = np.zeros(N, np.float32)
for sid, notes in mood.items():
    spd = 60 / (96 if sid in ("walk", "dog") else 74); k = 0; t0 = S0(sid) + 0.4
    while t0 < SC[sid]["end"] - 0.5:
        f = F(notes[[0, 2, 1, 3, 2, 1][k % 6]] + (0 if k % 2 == 0 and sid == "walk" else 12)); n = int(0.6 * sr); tt = np.arange(n) / sr
        add(arp, t0, (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2 * tt) * np.exp(-tt / 0.1)) * np.exp(-tt / 0.25))
        t0 += spd; k += 1
vm = max(np.abs(voice).max(), 1e-6)
duck = np.clip(np.convolve(np.abs(voice), np.ones(int(sr * 0.3)) / (sr * 0.3), "same") * 8, 0, 1)
mix = 0.85 * voice / vm + 0.9 * sfx + 0.055 * arp * (1 - 0.6 * duck)
mix = np.tanh(mix * 1.1) * 0.95
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", len(mix) / sr, "peak", float(np.abs(mix).max()))
