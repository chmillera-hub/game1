# Epic synthesized score: war drums, pipe drone, heroic chanter melody, choir swells + SFX -> mix.wav
import json, numpy as np, wave
SR = 44100
tl = json.load(open("timeline.json"))
T = tl["total"] + 0.6
N = int(T * SR)
L = {l["id"]: l for l in tl["lines"]}
rng = np.random.default_rng(11)
S = lambda i: L[i]["start"]; E = lambda i: L[i]["end"]
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
def wt(lid, word, k=0):
    c = 0
    for w in L[lid]["words"]:
        if ''.join(ch for ch in w["w"].lower() if ch.isalnum()) == ''.join(ch for ch in word.lower() if ch.isalnum()):
            if c == k: return w["t"]
            c += 1
    return L[lid]["start"]

music = np.zeros((N, 2)); drums = np.zeros((N, 2)); sfx = np.zeros((N, 2))
def add(buf, t0, sig, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N or len(sig) == 0: return
    if i < 0: sig = sig[-i:]; i = 0
    j = min(N, i + len(sig)); s = sig[: j - i] * gain
    buf[i:j, 0] += s * np.sqrt(0.5 * (1 - pan)); buf[i:j, 1] += s * np.sqrt(0.5 * (1 + pan))
def tt(d): return np.arange(int(d * SR)) / SR
def fade(n, a=.02, r=.1):
    e = np.ones(n); ai = max(1, min(n, int(a * SR))); ri = max(1, min(n, int(r * SR))); e[:ai] *= np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e
def lp(x, a):  # cheap low-pass via FFT brickwall-ish taper (a = cutoff Hz)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= 1 / (1 + (f / a) ** 4); return np.fft.irfft(X, len(x))
def noise(d): return rng.standard_normal(int(d * SR))

# ---------- instruments ----------
def saw(f, t, nh=12):
    s = np.zeros_like(t)
    for k in range(1, nh + 1): s += np.sin(2 * np.pi * f * k * t) / k
    return s
def strings(t0, dur, notes, gain=.05, att=1.2):
    t = tt(dur + 1.5); s = np.zeros_like(t)
    for m in notes:
        for d in (-.08, .0, .07):
            vib = 1 + .003 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6))
            s += saw(hz(m) * 2 ** (d / 12) * vib, t, 8)
    s = lp(s, 2200) * fade(len(t), min(att, dur / 2), 1.5) / (len(notes) * 3)
    add(music, t0, s, gain=gain)
def choir(t0, dur, notes, gain=.05):  # "aah": harmonics weighted by vowel formants
    t = tt(dur + 1.5); s = np.zeros_like(t)
    for m in notes:
        f0 = hz(m)
        for d in (-.1, .1):
            vib = 1 + .006 * np.sin(2 * np.pi * 5.5 * t + rng.uniform(0, 6)); ph = 2 * np.pi * f0 * 2 ** (d / 12) * np.cumsum(vib) / SR
            for k in range(1, 18):
                fk = f0 * k; w = np.exp(-((fk - 750) / 220) ** 2) + .7 * np.exp(-((fk - 1150) / 250) ** 2) + .3 * np.exp(-((fk - 2600) / 400) ** 2) + .15
                s += np.sin(k * ph) * w / k ** .3
    s *= fade(len(t), min(1.4, dur / 2), 1.6) / (len(notes) * 12)
    add(music, t0, s, gain=gain, pan=.1)
def drone(t0, dur, gain=.035, root=38):  # pipe drones on D and A
    t = tt(dur); s = np.zeros_like(t)
    for m in (root, root + 7, root + 12):
        s += saw(hz(m) * (1 + .0007 * np.sin(2 * np.pi * .3 * t)), t, 18)
    s = lp(s, 2600); s *= (1 + .5 * np.exp(-((np.arange(len(t)) / SR * 0)))) * 0 + 1
    s *= fade(len(t), 1.5, 1.5) / 3
    add(music, t0, s, gain=gain)
def chanter(t0, m, d, gain=.09, grace=None):  # reedy pipe chanter note with an optional grace note
    t = tt(d + .06); f = hz(m)
    vib = 1 + .004 * np.sin(2 * np.pi * 6 * t)
    s = saw(f * vib, t, 14) + .5 * np.sign(np.sin(2 * np.pi * f * 2 * t)) * .15
    s = lp(s, 3800) * fade(len(t), .015, .05)
    add(music, t0, s, gain=gain, pan=-.15)
    if grace: g = tt(.045); add(music, t0 - .045, lp(saw(hz(grace), g, 14), 3800) * fade(len(g), .005, .01), gain=gain * .8, pan=-.15)
def boom(t0, g=.5, f0=90, f1=42, d=1.1):  # taiko-ish war drum
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 18); ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 4.5) + lp(noise(d), 900) * np.exp(-t * 30) * .4
    add(drums, t0, s, gain=g)
def snare(t0, g=.12):
    t = tt(.25); add(drums, t0, (lp(noise(.25), 5000) * np.exp(-t * 22) + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30) * .4), gain=g, pan=.2)
def cymbal_swell(t_hit, d=2.0, g=.12):
    t = tt(d); x = noise(d); x = x - lp(x, 3000); add(drums, t_hit - d, x * (t / d) ** 3, gain=g)
    t2 = tt(2.5); y = noise(2.5); y = y - lp(y, 2500); add(drums, t_hit, y * np.exp(-t2 * 2.2), gain=g * .8)
def bell(f, d=3.0, g=.15):
    t = tt(d); s = (np.sin(2 * np.pi * f * t) + .45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3)) * np.exp(-t * 1.3); s[:120] *= np.linspace(0, 1, 120); return s * g
def lowhit(f, d=3.5, g=.3):
    t = tt(d); e = np.minimum(1, t / .2) * np.exp(-t * .9); return (np.sin(2 * np.pi * f * t) + .5 * np.sin(4 * np.pi * f * t) + .25 * np.sin(6 * np.pi * f * t)) * e * g

# ---------- the heroic tune (D mixolydian), played again and again, rising ----------
BEAT = 60 / 90
TUNE = [(69, 1, 74), (74, 1, None), (76, 1, None), (78, 1, 79), (76, 1, None), (74, 1, None), (71, 1, 76), (69, 1, None),
        (74, 1, None), (76, 1, None), (78, 1, None), (81, 1, 83), (79, 1, None), (78, 1, None), (76, 1, None), (74, 2, 76),
        (78, 1, None), (81, 1, None), (83, 1, None), (81, 1, 83), (78, 1, None), (76, 1, None), (74, 1, None), (76, 1, None),
        (78, 1, 79), (76, 1, None), (74, 1, None), (71, 1, None), (69, 1, 71), (74, 3, 76)]
def play_tune(t0, t1, gain=.08, transpose=0):
    t = t0
    while t < t1 - .5:
        for m, b, gr in TUNE:
            d = b * BEAT
            if t + d > t1: return
            chanter(t, m + transpose, d * .95, gain, gr + transpose if gr else None)
            t += d
def war_drums(t0, t1, g=.45, dense=1):
    t = t0; k = 0
    pat = [1, 0, 0, 1, 1, 0, 1, 0] if dense else [1, 0, 0, 0, 1, 0, 0, 0]
    while t < t1:
        if pat[k % 8]: boom(t, g * (1.0 if k % 8 == 0 else .7))
        if dense and k % 4 == 2: snare(t, .08 * dense)
        if dense > 1 and k % 2 == 1: snare(t + BEAT / 2, .05)
        t += BEAT / 2 * 2 / 2 * 1; t += 0; k += 1
        t += 0
        t = t0 + k * BEAT / 2

Gm = [43, 55, 58, 62]
Dm, Bb, F, C, G, A, D = [50, 57, 62, 65], [46, 53, 58, 62], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62], [45, 52, 57, 61], [50, 57, 62, 66]
def chords(t0, t1, seq, beat_len, inst='strings', gain=.05):
    t = t0; i = 0
    while t < t1 - .4:
        d = min(beat_len, t1 - t); ch = seq[i % len(seq)]
        (strings if inst == 'strings' else choir)(t, d, ch, gain); t += beat_len; i += 1

# 1. the hill: drone rising, low boom on "wound"
drone(0, S('a2'), .03); chords(0, S('a2'), [Dm], 6, 'choir', .04)
# 2. the meeting + forge: low strings, half-time drums
chords(S('a2') - .4, S('a5') - .4, [Dm, Bb, C, Dm], BEAT * 8, 'strings', .05)
war_drums(S('a4') - .3, S('a5') - .4, .3, 0)
# 3. banner: the tune enters, full drums, swell into "soul"
cymbal_swell(S('a5') - .4, 2.4, .1)
play_tune(S('a5') - .4, S('b1') + .2, .075)
war_drums(S('a5') - .4, S('b1'), .45, 1); drone(S('a5') - .4, S('b1') - S('a5') + .8, .03)
chords(S('a5') - .4, S('b1'), [D, G, A, D], BEAT * 4, 'choir', .05)
# 4. citadel / journals / the silent army: somber
chords(S('b1') - .2, S('c1') - .4, [Dm, Dm, Bb, A, Dm, Gm, A, A], BEAT * 8, 'strings', .045)
chords(S('b5') - .4, S('c1') - .4, [Dm, Bb], BEAT * 8, 'choir', .03)
war_drums(S('b2'), S('b3'), .22, 0)
# 5. the rally and the ram: build, the tune returns higher
chords(S('c1') - .4, S('c3') - .4, [Dm, Bb, C, D], BEAT * 4, 'strings', .055)
drone(S('c1') - .4, S('c3') - S('c1'), .03)
tP = wt('c2', 'pound'); k = 0
while tP + k * .95 < S('c3') - .4: boom(tP + k * .95, .7, 110, 38, 1.4); k += 1   # ram hits, synced to the animation
play_tune(S('c1') - .4, S('c3') - .4, .07)
cymbal_swell(wt('c2', 'crack'), 2.0, .14)
# 6. doubt: tender; then "lift ours" swell
chords(S('c3') - .4, S('c5') - .2, [Bb, F, Gm, A], BEAT * 6, 'strings', .04)
cymbal_swell(wt('c5', 'lift'), 2.2, .1); chords(S('c5') - .3, S('d1') - .3, [D, G], BEAT * 3, 'choir', .07)
# 7. platitudes: march, mid energy
war_drums(S('d1') - .4, S('e1') - .4, .32, 1)
chords(S('d1') - .4, S('e1') - .4, [Dm, C, Bb, C], BEAT * 8, 'strings', .045)
play_tune(S('d4') - .4, S('d5') - .4, .055, -12)
# 8. tipping point: build
chords(S('e1') - .4, S('e2') - .6, [Bb, C, D, D], BEAT * 4, 'choir', .055); war_drums(S('e1') - .4, S('e2') - .6, .38, 2)
cymbal_swell(wt('e1', 'hide'), 2.4, .12)
# 9. lonely: near silence, a soft minor pad
chords(S('e2') - .6, S('e4') - .4, [Dm, Bb], BEAT * 6, 'strings', .03)
# 10. embrace: warm major
chords(S('e4') - .4, S('f1') - .5, [Bb, F, C, F], BEAT * 4, 'choir', .055)
# 11. molt -> key -> release -> dragons: full epic, the tune again and again
drone(S('f1') - .5, T - S('f1') + .5, .035)
war_drums(wt('f1', 'loud') - .2, T - 1, .5, 2)
chords(S('f1') - .5, T - .5, [D, G, A, D, Bb, C, D, D], BEAT * 4, 'choir', .06)
chords(S('f1') - .5, T - .5, [D, G, A, D, Bb, C, D, D], BEAT * 4, 'strings', .04)
play_tune(wt('f1', 'loud') - .2, S('f4') - .2, .07)
play_tune(S('f4') - .2, T - 1.2, .085, 0)
cymbal_swell(wt('f1', 'dragon'), 2.4, .14); cymbal_swell(S('f4'), 2.0, .16)
boom(S('f4'), .9, 120, 35, 2.5)

# ---------- cue notes: high on hopeful words, low on heavy ones ----------
for l in tl["lines"]:
    for w in l.get("hi", []):
        t = wt(l["id"], w); add(music, t, bell(hz(rng.choice([81, 86, 90, 93]))), pan=rng.uniform(-.4, .4))
    for w in l.get("lo", []):
        t = wt(l["id"], w); add(music, t - .05, lowhit(hz(rng.choice([38, 36, 33]))))

# ---------- SFX ----------
def clang(t0, g=.18):
    t = tt(1.2); s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, dcy in ((1220, 6), (2730, 9), (3980, 12), (610, 4))) * .3
    add(sfx, t0, s + noise(1.2) * np.exp(-t * 60) * .3, gain=g, pan=.3)
def roar_crowd(t0, d=3.0, g=.12):
    t = tt(d); x = lp(noise(d), 1400) - lp(noise(d), 250); env = np.minimum(1, t / .4) * np.exp(-np.maximum(0, t - 1.2) * 1.3)
    add(sfx, t0, x * env * (1 + .3 * np.sin(2 * np.pi * 7 * t)), gain=g)
def dragon_roar(t0, g=.2, pan=0):
    d = 1.8; t = tt(d); f = 140 * np.exp(-t * .8) + 40; ph = 2 * np.pi * np.cumsum(f) / SR
    s = (saw(1, ph / (2 * np.pi), 1) * 0 + np.sign(np.sin(ph)) * .5 + np.sin(ph * 1.5) * .3) * (1 + .6 * np.sin(2 * np.pi * 23 * t))
    s = lp(s, 1400) + lp(noise(d), 1800) * .5
    add(sfx, t0, s * np.minimum(1, t / .1) * np.exp(-t * 1.3), gain=g, pan=pan)
def whoosh(t0, d=.8, g=.2):
    n = lp(noise(d), 900); add(sfx, t0, n * np.sin(np.linspace(0, np.pi, len(n))) ** 2, gain=g)
def crack(t0, g=.25):
    for k in range(5): add(sfx, t0 + k * .05, noise(.08) * np.exp(-tt(.08) * 50), gain=g * (1 - k * .15))
    add(sfx, t0, lowhit(55, 1.5, .5))
def squawk(t0, g=.12):
    d = .3; t = tt(d); f = 1800 + 900 * np.sin(2 * np.pi * 9 * t); ph = 2 * np.pi * np.cumsum(f) / SR
    add(sfx, t0, np.sign(np.sin(ph)) * np.exp(-t * 6) * .5, gain=g, pan=.4)
def shing(t0, g=.12):
    t = tt(1.0); add(sfx, t0, (noise(1.0) - lp(noise(1.0), 4000)) * np.exp(-t * 4) * .6 + np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 3) * .2, gain=g)
def wind(t0, t1, g=.03):
    d = t1 - t0; x = lp(noise(d), 500); add(sfx, t0, x * (1 + .5 * np.sin(2 * np.pi * .15 * tt(d))) * fade(len(x), 1, 1), gain=g)
def rain(t0, t1, g=.02):
    d = t1 - t0; x = noise(d) - lp(noise(d), 1500); add(sfx, t0, x * fade(len(x), .5, .5), gain=g)
def flame(t0, d, g=.06):
    x = lp(noise(d), 600); add(sfx, t0, x * fade(len(x), .4, .6), gain=g)

wind(0, S('a4')); wind(S('a5') - .4, S('b1') + 1, .04)
for w in ('forge', 'intense', 'posts', 'conversations', 'art', 'presence'): clang(wt('a4', w) - .02)
flame(S('a4') - .3, S('a5') - S('a4'), .05)
roar_crowd(wt('a5', 'soul'), 3.2, .14); whoosh(S('a5') - .2, 1.2, .1)
rain(S('b5') - .4, S('c1') - .4); rain(wt('c4', 'brokenhearted') - .3, wt('c5', 'lift') + 1.5)
shing(wt('c1', 'mission') - .1)
crack(wt('c2', 'crack')); roar_crowd(wt('c2', 'crack') + .2, 2.5, .1)
roar_crowd(wt('c5', 'lift') + .6, 2.6, .08)
for k in range(8): squawk(wt('d7', 'called') - 1.2 + k * .22)
for w in ('Emails', 'Texts', 'Comments', 'Plead', 'demand', 'Actionable'): whoosh(wt('d4', w), .5, .07)
whoosh(wt('f1', 'loud') - .2, 1.4, .25); crack(wt('f1', 'loud') - .1, .2)
flame(wt('f1', 'loud'), E('f1') - wt('f1', 'loud') + 1, .08)
dragon_roar(wt('f1', 'dragon') + .3, .22)
for w in ('forged', 'fires', 'agony'): clang(wt('f2', w))
for k in range(9): add(sfx, wt('f2', 'prison') - .6 + k * .3, noise(.06) * np.exp(-tt(.06) * 60), gain=.15)   # locks clicking
shing(S('f3') - .3, .1)
roar_crowd(S('f4') + .1, 4.5, .18)
for k, (d, p) in enumerate([(0, -.5), (.6, .5), (1.3, -.3), (2.0, .4), (3.0, 0)]): dragon_roar(S('f4') + 1.0 + d, .14, p)

# ---------- simple reverb on music + drums (FFT convolution with a decaying noise tail) ----------
def reverb(x, sec=2.2, mix=.25):
    ir = rng.standard_normal(int(sec * SR)) * np.exp(-np.arange(int(sec * SR)) / SR * 3.2); ir[0] = 0
    n = len(x) + len(ir); nf = 1 << (n - 1).bit_length(); out = np.zeros_like(x)
    for c in range(2):
        y = np.fft.irfft(np.fft.rfft(x[:, c], nf) * np.fft.rfft(ir, nf), nf)[:len(x)]
        out[:, c] = x[:, c] + y / np.max(np.abs(ir)) * mix * .02
    return out
bed = reverb(music + drums * .8, 2.4, .9)

# ---------- voices + ducking ----------
voice = np.zeros(N); duck = np.ones(N)
for l in tl["lines"]:
    if not l["sp"]: continue
    a = np.load(f"tts/{l['id']}.npy"); i = int(l["start"] * SR); j = min(N, i + len(a))
    voice[i:j] += a[: j - i]
    di, dj = max(0, i - int(.2 * SR)), min(N, j + int(.3 * SR)); duck[di:dj] = np.minimum(duck[di:dj], .5)
k = int(.25 * SR); duck = np.convolve(duck, np.ones(k) / k, mode="same")
bed /= np.percentile(np.abs(bed), 99.9) / .55
mix = bed * duck[:, None] + sfx * 1.0 + voice[:, None] * .95
mix /= max(1.0, np.max(np.abs(mix)) / .97)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("ok", T)
