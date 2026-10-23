# Synthesized score + SFX, mixed under the voice tracks -> mix.wav
import json, numpy as np, wave
SR = 44100
tl = json.load(open("timeline.json"))
T = tl["total"] + 0.6
N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}
rng = np.random.default_rng(7)

def note_hz(n):  # midi -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)

def wt(lid, word, k=0):
    c = 0
    for w in L[lid]["words"]:
        if w["w"].lower().strip(".,?!'") == word.lower().strip(".,?!'"):
            if c == k: return w["t"]
            c += 1
    return L[lid]["start"]

music = np.zeros((N, 2)); sfx = np.zeros((N, 2))

def add(buf, t0, sig, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    j = min(N, i + len(sig)); s = sig[: j - i] * gain
    buf[i:j, 0] += s * np.sqrt(0.5 * (1 - pan)); buf[i:j, 1] += s * np.sqrt(0.5 * (1 + pan))

def env_adsr(n, a, r, sustain_shape=None):
    e = np.ones(n); ai = max(1, int(a * SR)); ri = max(1, int(r * SR))
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri)
    return e

def pad(t0, dur, notes, gain=.05, bright=.25):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for m in notes:
        f = note_hz(m)
        for d in (-0.12, 0.0, 0.11):  # detuned chorus
            ff = f * 2 ** (d / 12)
            ph = rng.uniform(0, 6.28)
            s += np.sin(2 * np.pi * ff * t + ph) + bright * np.sin(4 * np.pi * ff * t + ph) * .5 + bright * .3 * np.sin(6 * np.pi * ff * t)
    s *= env_adsr(n, min(1.5, dur / 3), min(1.8, dur / 3)) * (1 + .08 * np.sin(2 * np.pi * .2 * t))
    return s / max(1, len(notes) * 3) * gain

def pluck(f, dur=1.6, gain=.2, bright=.5):  # Karplus-ish soft pluck (lute / piano-ish)
    n = int(dur * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + bright * .5 * np.sin(4 * np.pi * f * t) + bright * .25 * np.sin(6 * np.pi * f * t)) * np.exp(-t * (3.2 + f / 600))
    s[:200] *= np.linspace(0, 1, 200)
    return s * gain

def bell(f, dur=3.0, gain=.15):  # high notes on hopeful words
    n = int(dur * SR); t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + .25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)) * np.exp(-t * 1.3)
    s[:120] *= np.linspace(0, 1, 120)
    return s * gain

def low(f, dur=3.5, gain=.28):  # deep cello/bell swell on heavy words
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.minimum(1, t / .25) * np.exp(-t * .9)
    s = (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t + .3) + .25 * np.sin(6 * np.pi * f * t) + .15 * np.sin(2 * np.pi * f * 1.003 * t)) * e
    return s * gain

def noise(dur, lp=0.0):
    n = int(dur * SR); x = rng.standard_normal(n)
    if lp:  # one-pole low-pass
        y = np.zeros(n); a = lp; acc = 0.0
        for i in range(n): acc += a * (x[i] - acc); y[i] = acc
        x = y / (np.max(np.abs(y)) + 1e-9)
    return x

# ---------- score sections (minor for the heavy middle, warming to major) ----------
Dm, Bb, F, C, Gm, A, Dmaj, G = [50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 58, 62], [45, 52, 57, 61], [50, 57, 62, 66], [43, 55, 59, 62]
def progression(t0, t1, chords, beat, gain=.05, arp=None, arp_gain=.06):
    t = t0; i = 0
    while t < t1 - .5:
        d = min(beat, t1 - t); ch = chords[i % len(chords)]
        add(music, t, pad(t, d + 1.2, ch, gain), pan=.0)
        if arp:
            step = beat / len(arp)
            for k, idx in enumerate(arp):
                if t + k * step < t1 - .2: add(music, t + k * step, pluck(note_hz(ch[idx % 4] + 12), 1.4, arp_gain), pan=(-.3 if k % 2 else .3))
        t += beat; i += 1

S = lambda i: L[i]["start"]; E = lambda i: L[i]["end"]
progression(0, S("a1") - .3, [[38, 45, 50, 53], [38, 45, 50, 53], [34, 41, 46, 50], [36, 43, 48, 52]], 5.0, .06)           # dark drone under the martyrs
progression(S("a1") - .3, S("b1") - .4, [Dm, Bb, F, C], 4.0, .04, arp=[0, 2, 3, 2], arp_gain=.045)                        # lonely modern piano
progression(S("b1") - .4, S("d1") - .4, [Bb, F, C, Dm], 4.5, .04, arp=[0, 3], arp_gain=.04)                               # chatbot: soft
progression(S("d1") - .4, S("e1") - .2, [Dm, Gm, Dm, A], 5.0, .055, arp=[0, 1, 2, 1, 3, 1], arp_gain=.04)                 # Rome: lute plucks
progression(S("e1") - .2, S("e2") - .4, [F, C], 2.0, .05, arp=[0, 1, 2, 3], arp_gain=.05)                                  # the road: lift
progression(S("e2") - .4, S("e5") - .2, [Dm, A, Dm, Bb], 3.0, .045, arp=[0, 0], arp_gain=.05)                             # villa: tense pizzicato
progression(S("e5") - .2, S("f1") - .3, [F, C, Dm, Bb], 3.5, .035)
progression(S("f1") - .3, S("g1") - .5, [Bb, F, C, Dm, Bb, F, C, C], 2.6, .05, arp=[0, 1, 2, 3], arp_gain=.05)            # Philippi: rising hope
progression(S("g1") - .5, T, [Bb, F, C, Dmaj[:1] + [57, 62, 66], G, Dmaj], 4.0, .045, arp=[0, 2, 3, 2], arp_gain=.045)   # dawn: warming toward D major

# ---------- motif notes on cue words ----------
for l in tl["lines"]:
    for w in l.get("hi", []):
        t = wt(l["id"], w); add(music, t, bell(note_hz(rng.choice([81, 86, 88, 93]))), pan=rng.uniform(-.4, .4), gain=.9)
        add(music, t + .18, bell(note_hz(rng.choice([86, 88, 93])) * 1.0, 2.0, .07), pan=.3)
    for w in l.get("lo", []):
        t = wt(l["id"], w); add(music, t - .05, low(note_hz(rng.choice([38, 36, 33]))), gain=1.0)

# ---------- SFX ----------
def clink(t, n=4, g=.12):
    for k in range(n):
        f = rng.uniform(2400, 3800); d = .25; tt = np.arange(int(d * SR)) / SR
        add(sfx, t + k * rng.uniform(.04, .09), np.sin(2 * np.pi * f * tt) * np.exp(-tt * 28) * g, pan=-.3)
def thud(t, g=.35, f=70):
    tt = np.arange(int(.4 * SR)) / SR; add(sfx, t, (np.sin(2 * np.pi * f * tt * (1 - tt)) * np.exp(-tt * 12) + noise(.4) * .15 * np.exp(-tt * 30)) * g)
def whoosh(t, d=.8, g=.25):
    n = noise(d, .08); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2; add(sfx, t, n * e * g)
def crackle(t0, d, g=.06):
    n = int(d * SR); x = np.zeros(n)
    for _ in range(int(d * 18)):
        i = rng.integers(0, n - 400); x[i:i + 400] += rng.standard_normal(400) * np.exp(-np.arange(400) / 60)
    add(sfx, t0, x * g)
def crumple(t, d=.7, g=.18):
    n = int(d * SR); x = rng.standard_normal(n) * (rng.random(n) < .25) * np.repeat(rng.random(n // 300 + 1), 300)[:n]; add(sfx, t, x * g)
def creak(t, d=1.1, g=.12):
    tt = np.arange(int(d * SR)) / SR; f = 180 + 120 * np.sin(tt * 3); ph = np.cumsum(f) / SR
    add(sfx, t, np.sign(np.sin(2 * np.pi * ph)) * (np.sin(2 * np.pi * 9 * tt) > .2) * np.sin(np.pi * tt / d) * g, pan=-.5)
def buzz(t, g=.12):
    tt = np.arange(int(.5 * SR)) / SR; add(sfx, t, np.sin(2 * np.pi * 150 * tt) * (np.sin(2 * np.pi * 14 * tt) > 0) * np.exp(-tt * 2) * g)
def ding(t, g=.18): add(sfx, t, bell(note_hz(88), 1.5, g)); add(sfx, t + .12, bell(note_hz(93), 1.5, g * .8))
def bwomp(t, g=.22):  # comedic low trombone slide
    d = .9; tt = np.arange(int(d * SR)) / SR; f = 110 * 2 ** (-tt * .9); ph = np.cumsum(f) / SR
    s = (np.sin(2 * np.pi * ph) + .5 * np.sin(4 * np.pi * ph) + .3 * np.sin(6 * np.pi * ph)) * np.minimum(1, tt / .05) * np.exp(-tt * 1.5); add(sfx, t, s * g)
def rainloop(t0, t1, g=.02):
    add(sfx, t0, noise(t1 - t0, .35) * g * np.minimum(1, np.minimum(np.arange(int((t1 - t0) * SR)) / SR, (t1 - t0) - np.arange(int((t1 - t0) * SR)) / SR) / .5))

# martyr panels
add(sfx, S("m1"), noise(1.8, .05) * .06 * np.exp(-np.arange(int(1.8 * SR)) / SR))
for k in range(16): thud(S("m3") - .05 + k * .09 + .55, .12, 90 + k * 5)
add(sfx, S("m5") + .2, noise(1.2, .02) * .05)
whoosh(S("m7") - .05, .7, .2); thud(S("m7") + .6, .45, 55); clink(S("m7") + .6, 2, .1)
rainloop(0, S("m1")); rainloop(S("a1") - .3, wt("a2", "People") - .1)
rainloop(wt("a2", "People") - .1, S("a3") - .4, .03)
thud(wt("a2", "Being") + .9, .25, 120)  # shutters close
creak(wt("a2", "Being"), .9, .07)
rainloop(S("b1") - .5, S("d1") - .4, .015)
add(sfx, wt("a4", "post"), bell(note_hz(84), .6, .08)); whoosh(wt("a4", "post") + .1, .5, .08)
bwomp(wt("b5", "dumb") + .25); buzz(wt("b5", "block"), .1)
clink(wt("d1", "chain"), 5, .1); clink(wt("d2", "chains"), 3, .07); clink(S("d7") + .1, 6, .12)
creak(S("d8") + .15, 1.2, .12); clink(S("d8") + 1.5, 3, .06)
whoosh(wt("e1", "sea") - .2, 1.6, .06)
crumple(wt("e3", "Paul") - .5, .4, .1)       # unrolls
crumple(E("e4") + .15, .65, .2)                # crumples
whoosh(E("e4") + 1.05, .45, .2); whoosh(E("e4") + 1.6, 1.0, .35)
crackle(S("e2") - .4, E("e6") - S("e2") + .4, .05)
add(sfx, S("g4") + .45, np.zeros(1)); buzz(S("g4") + .4, .12); ding(S("g4") + .5)

# ---------- voices + ducking ----------
voice = np.zeros(N); duck = np.ones(N)
for l in tl["lines"]:
    if not l["sp"]: continue
    a = np.load(f"tts/{l['id']}.npy"); i = int(l["start"] * SR); j = min(N, i + len(a))
    voice[i:j] += a[: j - i]
    di, dj = max(0, i - int(.25 * SR)), min(N, j + int(.35 * SR)); duck[di:dj] = np.minimum(duck[di:dj], .42)
# smooth the duck envelope
k = int(.2 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
mix = music * duck[:, None] * 1.0 + sfx + voice[:, None] * .92
mix /= max(1.0, np.max(np.abs(mix)) / .97)
pcm = (mix * 32767).astype(np.int16)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("peak music", np.max(np.abs(music)), "len", T)
