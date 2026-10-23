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

def lpf(x, a):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / a) ** 4); return np.fft.irfft(X, len(x))
def tt(d): return np.arange(int(d * SR)) / SR
S = lambda i: L[i]["start"]; E = lambda i: L[i]["end"]
BPM = 96; BT = 60 / BPM
# ---------- instruments ----------
def ep(t0, notes, d, g=.05):  # soft electric-piano chord
    for k, m in enumerate(notes): add(music, t0 + k * .012, pluck(note_hz(m), d, g, .35), pan=(-.2 if k % 2 else .2))
def bass(t0, m, d, g=.22):
    t = tt(d); f = note_hz(m); s = (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 2.5) * np.minimum(1, t / .01); add(music, t0, s, gain=g)
def hat(t0, g=.03):
    n = noise(.08); n = n - lpf(n, 6000); add(music, t0, n * np.exp(-tt(.08) * 60), gain=g, pan=.35)
def brush(t0, g=.025):
    n = lpf(noise(.25), 5000); add(music, t0, n * np.exp(-tt(.25) * 14), gain=g, pan=-.3)
def kick(t0, g=.18):
    t = tt(.3); f = 60 + 60 * np.exp(-t * 30); add(music, t0, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12), gain=g)
# jazz ii-V-I loop in F (Gm7 C7 Fmaj7 Dm7)
JZ = [([43], [55, 58, 62, 65]), ([48], [55, 58, 60, 64]), ([41], [57, 60, 64, 65]), ([38], [57, 60, 62, 65])]
WALK = [[43, 46, 50, 52], [48, 47, 46, 45], [41, 45, 48, 50], [38, 41, 43, 44]]
def lounge(t0, t1, g=1.0, drums=True):
    t = t0; bar = 0
    while t < t1 - .2:
        root, ch = JZ[bar % 4]
        if t + 4 * BT > t1 + 1: break
        ep(t, ch, 2.6, .045 * g); ep(t + 2.5 * BT, ch, 1.4, .03 * g)
        for b in range(4):
            bass(t + b * BT, WALK[bar % 4][b], BT * 1.1, .2 * g)
            if drums:
                hat(t + b * BT + BT * .66, .02 * g); brush(t + b * BT, .02 * g)
                if b in (0, 2): kick(t + b * BT, .1 * g)
        t += 4 * BT; bar += 1
def strings(t0, d, notes, g=.05):
    t = tt(d + 1.5); s = np.zeros_like(t)
    for m in notes:
        for dd in (-.08, 0, .08):
            f = note_hz(m) * 2 ** (dd / 12) * (1 + .003 * np.sin(2 * np.pi * 5 * t + rng.uniform(0, 6)))
            s += sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 7))
    s = lpf(s, 2400) * env_adsr(len(t), min(1.2, d / 2), 1.5) / (len(notes) * 3)
    add(music, t0, s, gain=g)
def chords(t0, t1, seq, bl, g=.05):
    t = t0; i = 0
    while t < t1 - .4: strings(t, min(bl, t1 - t), seq[i % len(seq)], g); t += bl; i += 1
def ding(t, g=.25):
    add(sfx, t, bell(note_hz(88), 2.5, g)); add(sfx, t, bell(note_hz(100), 1.5, g * .4))
def bwomp(t, g=.2):
    d = .9; x = tt(d); f = 110 * 2 ** (-x * .9); ph = np.cumsum(f) / SR
    add(sfx, t, (np.sin(2 * np.pi * ph) + .5 * np.sin(4 * np.pi * ph) + .3 * np.sin(6 * np.pi * ph)) * np.minimum(1, x / .05) * np.exp(-x * 1.5), gain=g)
def stopper(t, g=.15):  # record-stop: a falling tone and cut
    d = .5; x = tt(d); f = 600 * np.exp(-x * 6); add(sfx, t, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 3), gain=g)
def sparkle(t, g=.12):
    for k, m in enumerate([84, 88, 91, 96, 100]): add(sfx, t + k * .09, bell(note_hz(m), 1.2, g))
def murmur(t0, t1, g=.018):
    d = t1 - t0; x = lpf(noise(d), 700) - lpf(noise(d), 200); add(sfx, t0, x * (1 + .4 * np.sin(2 * np.pi * .3 * tt(d))) * env_adsr(len(x), 1, 1), gain=g)
def clink(t, g=.08):
    for k in range(2): x = tt(.4); add(sfx, t + k * .05, np.sin(2 * np.pi * rng.uniform(2600, 3400) * x) * np.exp(-x * 14), gain=g)
def buzz(t, g=.12):
    x = tt(.5); add(sfx, t, np.sin(2 * np.pi * 150 * x) * (np.sin(2 * np.pi * 14 * x) > 0) * np.exp(-x * 2), gain=g)
def scribble(t, d, g=.05):
    n = noise(d); add(sfx, t, (n - lpf(n, 3000)) * (np.sin(2 * np.pi * 9 * tt(d)) > 0), gain=g)
def pour(t, d, g=.06):
    n = lpf(noise(d), 1500); add(sfx, t, n * (1 + .5 * np.sin(2 * np.pi * 11 * tt(d))) * env_adsr(len(n), .2, .4), gain=g)

# ---------- score ----------
lounge(0, S('n2') - .5, 1.0)                                         # the bar: light, playful
murmur(0, S('n2'))
chords(S('n2') - .5, S('bell'), [[50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [45, 52, 57, 61]], 4.5, .05)   # table twelve: tender strings
chords(S('j17') - .3, S('bell'), [[38, 50, 57, 62]], 6, .03)        # deep pedal under "the worst night"
lounge(S('h6') - .1, S('n3') - .4, .55, drums=False)
chords(S('n3') - .5, S('n4') - .4, [[46, 53, 58, 62], [48, 55, 60, 64], [41, 53, 57, 60]], 3.5, .04)
lounge(S('n3') - .5, S('n4') - .3, .7)
chords(S('n4') - .4, T, [[46, 53, 58, 62], [48, 55, 60, 64], [41, 53, 57, 60], [41, 53, 57, 60, 65]], 4.0, .06)          # warm swell to the end
for k, m in enumerate([72, 74, 77, 81, 79, 77]): add(music, S('morn') + .6 + k * .55, pluck(note_hz(m), 2.2, .07))
# cue notes on hopeful / heavy words
for l in tl["lines"]:
    for w in l.get("hi", []): add(music, wt(l["id"], w), bell(note_hz(rng.choice([81, 84, 88, 89]))), pan=rng.uniform(-.4, .4), gain=.9)
    for w in l.get("lo", []): add(music, wt(l["id"], w) - .05, low(note_hz(rng.choice([38, 36, 41]))), gain=.9)
# ---------- SFX & comic stings ----------
for b in (E('j4') + .9, E('j10') + .8, E('j13') + .9, S('bell')): ding(b)
scribble(S('tag') + .2, 1.4)
add(sfx, wt('h4', 'shoes') + .3, pluck(note_hz(60), .6, .12)); add(sfx, wt('h4', 'shoes') + .5, pluck(note_hz(55), .8, .12))   # plunk-plunk at the sandals
for k in range(6): add(sfx, wt('j3', 'alone') + k * .3, bell(note_hz(96 - k), .4, .03))    # chat notifications
bwomp(wt('j6', 'Zero') + .2, .14)
stopper(wt('j7', 'water') + .1)
for t in (wt('j9', 'safe') - .3, wt('j9', 'safe') - .05): add(sfx, t, lpf(noise(.15), 400) * np.exp(-tt(.15) * 30), gain=.25)   # pat-pat on the table
add(sfx, wt('j10', 'eternities') + .3, pluck(note_hz(79), .3, .1))                         # the pen hits the floor
stopper(S('b1') + .2, .1); bwomp(wt('b1', 'out'), .12)
pour(S('wine') + .2, 1.6); sparkle(S('wine') + .3)
for k in range(3): clink(S('wine') + 1.0 + k * .35)
for t in (wt('d1', 'Height'), wt('d2', 'Income') if False else E('j5') - .2, wt('j6', 'Zero') + .1, wt('j7', 'walk')): scribble(t, .25, .06)
buzz(S('morn') + .6); add(sfx, S('morn') + .7, bell(note_hz(88), 1.2, .12))
# ---------- voices + ducking ----------
voice = np.zeros(N); duck = np.ones(N)
for l in tl["lines"]:
    if not l["sp"]: continue
    a = np.load(f"tts/{l['id']}.npy"); i = int(l["start"] * SR); j = min(N, i + len(a))
    voice[i:j] += a[: j - i]
    di, dj = max(0, i - int(.2 * SR)), min(N, j + int(.3 * SR)); duck[di:dj] = np.minimum(duck[di:dj], .45)
k = int(.2 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
music /= max(1e-6, np.percentile(np.abs(music), 99.9)) / .45
mix = music * duck[:, None] + sfx + voice[:, None] * .95
mix /= max(1.0, np.max(np.abs(mix)) / .97)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", T)
