"""Synthesize the score + sound effects, keyed to build/timeline.json, and mix
them under the dialogue track (with ducking) into build/mix.wav."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
SR = 44100
TL = json.load(open(os.path.join(B, "timeline.json")))
BE = {b["label"]: b for b in TL["beats"]}
SC = {s["id"]: s for s in TL["scenes"]}
bs = lambda l: BE[l]["start"]
be = lambda l: BE[l]["end"]
bf = lambda l, f: bs(l) + (be(l) - bs(l)) * f
DUR = TL["duration"] + 0.5
N = int(DUR * SR)
rng = np.random.default_rng(3)

music = np.zeros((N, 2))
sfx = np.zeros((N, 2))

def midi(n): return 440 * 2 ** ((n - 69) / 12)
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "Ab": 8, "A": 9, "Bb": 10, "B": 11}
def n(name):  # "C4" -> midi
    p, o = name[:-1], int(name[-1]); return 12 * (o + 1) + NOTE[p]

def add(buf, t, x, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    x = x[:N - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * l * 1.41
    buf[i:i + len(x), 1] += x * gain * r * 1.41

def env_adsr(L, a, r):
    e = np.ones(L); A = max(1, int(a * SR)); R = max(1, int(r * SR))
    e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e

def pluck(f, dur=1.6, bright=1.0, decay=2.5):
    L = int(dur * SR); t = np.arange(L) / SR
    x = sum((1 / k ** (1.6 - .4 * bright)) * np.sin(2 * np.pi * f * k * t) * np.exp(-t * decay * k ** .7) for k in range(1, 6))
    x *= np.minimum(1, t / .004)
    return x * env_adsr(L, .002, .05)

def musicbox(f, dur=1.2):
    L = int(dur * SR); t = np.arange(L) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 3) + .35 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 7) + .2 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 12)
    return x * env_adsr(L, .002, .05)

def pad(freqs, dur, a=1.2, r=1.5):
    L = int(dur * SR); t = np.arange(L) / SR
    x = np.zeros(L)
    for f in freqs:
        for d in (-.12, .12):
            x += np.sin(2 * np.pi * (f + d) * t + rng.random() * 6) + .25 * np.sin(2 * np.pi * 2 * (f + d) * t)
    x /= len(freqs) * 2
    return x * env_adsr(L, a, r) * (1 + .1 * np.sin(2 * np.pi * .3 * t))

def bassnote(f, dur=.8):
    L = int(dur * SR); t = np.arange(L) / SR
    return (np.sin(2 * np.pi * f * t) + .3 * np.sin(4 * np.pi * f * t)) * np.exp(-t * 2.2) * env_adsr(L, .01, .1)

CH = {  # chord name -> midi notes (root position-ish, mid register)
    "C": [48, 60, 64, 67], "F": [41, 60, 65, 69], "G": [43, 59, 62, 67], "Am": [45, 60, 64, 69], "Dm": [38, 57, 62, 65],
    "Bb": [46, 58, 62, 65], "Em": [40, 59, 64, 67], "D": [38, 57, 62, 66], "A": [45, 57, 61, 64], "Bm": [47, 59, 62, 66],
    "Gd": [43, 59, 62, 67], "Fmaj7": [41, 57, 64, 69], "Bbadd9": [46, 58, 62, 65, 72], "Gm": [43, 58, 62, 67],
}

# ------------------------------------------------------------- waltz (title + s1 + early s2)
def waltz(t0, t1, bpm=100, gain=1.0, prog=("C", "Am", "F", "G"), melody=True):
    beat = 60 / bpm; bar = 3 * beat
    mel = [[76, 79, 81], [79, 76, 72], [77, 76, 74], [74, 0, 71],
           [72, 76, 79], [81, 79, 76], [77, 74, 72], [71, 72, 0]]
    i = 0; t = t0
    while t < t1:
        ch = CH[prog[i % len(prog)]]
        k = min(1, (t1 - t) / 1.0)
        add(music, t, bassnote(midi(ch[0]), bar), .32 * gain * k, -.2)
        for b in (1, 2):
            for m in ch[1:]: add(music, t + b * beat, pluck(midi(m), 1.0, .6, 4), .07 * gain * k, .25)
        if melody:
            for j, m in enumerate(mel[i % len(mel)]):
                if m: add(music, t + j * beat, musicbox(midi(m), 1.4), .12 * gain * k, -.1 + .2 * (j % 2))
        t += bar; i += 1

waltz(0.6, bs("crickets") - .1, bpm=96, gain=1.0)

# awkward / dismissive section: sparse minor pads
t = be("crickets") + .4
for name in ["Am", "F", "Dm", "Am", "F", "Em"]:
    if t > SC["s2"]["end"]: break
    d = min(4.0, SC["s2"]["end"] - t + 1)
    add(music, t, pad([midi(m) for m in CH[name][1:]], d + 1.0, 1.0, 1.5), .14, 0)
    add(music, t, bassnote(midi(CH[name][0]), 2.5), .25)
    t += 4.0

# ------------------------------------------------------------- s3
t0 = SC["s3"]["start"]
for i, m in enumerate([81, 84, 88, 84, 81, 79, 76, 79]):  # curious bird motif
    add(music, t0 + .3 + i * .45, musicbox(midi(m), 1.2), .09, .4)
add(music, t0, pad([midi(m) for m in (57, 64, 69)], be("s3b") - t0 + 1, 1.5, 1.0), .10)
joy0, joy1 = be("s3b") + .1, bs("s3d1") - .25
add(music, joy0, pad([midi(m) for m in (53, 60, 65, 69, 72)], joy1 - joy0 + .3, 1.2, .25), .16)
arp = [65, 69, 72, 77, 81, 77, 72, 69, 67, 72, 76, 79, 84, 79, 76, 72]
tt = joy0 + .2; k = 0
while tt < joy1 - .1:
    add(music, tt, musicbox(midi(arp[k % len(arp)] + (12 if k > 12 else 0)), 1.2), .1 + .03 * min(1, k / 8), .3 * np.sin(k))
    tt += .24; k += 1
# tension drone under "manic?" -> confrontation
td0 = bs("s3d1") - .1
add(music, td0, pad([midi(38), midi(45), midi(50)], bs("s3h") - td0 + .5, .6, .8), .16)
for i in range(int((bs("s3h") - td0) / 1.2)):
    add(music, td0 + i * 1.2, pluck(midi(38), 1.2, .3, 3), .12)
# sad resolution
t = bs("s3h") - .2
for name in ["Dm", "Bb", "Gm", "Am"]:
    add(music, t, pad([midi(m) for m in CH[name][1:]], 3.8, 1.0, 1.4), .13)
    add(music, t, bassnote(midi(CH[name][0]), 2.5), .2)
    t += 2.6

# ------------------------------------------------------------- s4 wistful
t = SC["s4"]["start"] + .2
melo = [69, 72, 76, 74, 72, 71, 72, 69]
i = 0
while t < SC["s4"]["end"] - .8:
    name = ["Am", "F", "C", "G"][i % 4]
    add(music, t, pad([midi(m) for m in CH[name][1:]], 4.6, 1.3, 1.6), .12)
    add(music, t, bassnote(midi(CH[name][0]), 3), .22)
    for j in range(2):
        add(music, t + j * 2, pluck(midi(melo[(i * 2 + j) % len(melo)] + 12), 2.2, .9, 1.6), .11, -.2)
    t += 4.0; i += 1

# ------------------------------------------------------------- s5 mechanical cycle
t0, t1 = SC["s5"]["start"] + .4, SC["s5"]["end"] - .2
ost = [62, 65, 69, 65, 62, 65, 69, 72]
tt = t0; k = 0
while tt < t1:
    p = (tt - t0) / (t1 - t0)
    detune = -12 * max(0, (tt - (t1 - 1.6)) / 1.6) ** 2  # winding down at the end
    add(music, tt, musicbox(midi(ost[k % 8] + detune), 1.0), .14, .3 * np.sin(k * .7))
    if k % 8 == 0: add(music, tt, bassnote(midi(38 + detune), 2), .22)
    step = .25 if tt < bs("s5f") else max(.12, .25 - (tt - bs("s5f")) * .05)
    tt += step; k += 1

# ------------------------------------------------------------- s6 after the outburst
r0 = be("s6b") + 1.0
add(music, r0, pad([midi(m) for m in (58, 62, 65, 72)], SC["s6"]["end"] - r0 + 1.5, 3.0, 1.5), .17)
add(music, r0 + .5, bassnote(midi(46), 4), .2)
for i, m in enumerate([77, 74, 72, 70, 74, 77]):
    add(music, bs("s6c") + 1 + i * 1.8, pluck(midi(m), 2.5, .8, 1.4), .09, .2)

# ------------------------------------------------------------- s7 hard truth: sparse piano
t = SC["s7"]["start"] + .2
for name, mel in [("F", 72), ("Dm", 69), ("Bb", 70), ("C", 67), ("F", 72), ("Dm", 74), ("Bb", 72), ("C", 72)]:
    if t > SC["s7"]["end"]: break
    for m in CH[name][1:]: add(music, t, pluck(midi(m), 3, .5, 1.1), .06)
    add(music, t, bassnote(midi(CH[name][0]), 2.5), .18)
    add(music, t + 1.1, pluck(midi(mel + 12), 2.5, .9, 1.3), .08, -.2)
    t += 2.3

# ------------------------------------------------------------- s8 takeaway -> gallop finale
s8 = SC["s8"]["start"]
t = s8 + .1
for name in ["F", "C", "Bb"]:
    for m in CH[name][1:]: add(music, t, pluck(midi(m), 3, .5, 1.1), .06)
    add(music, t, bassnote(midi(CH[name][0]), 2.5), .18)
    t += 2.4
walk0 = be("s8b") + .2
dissolve = be("s8b") + 3.1
run0 = dissolve + 1.2
stopT = bs("s8e") + .5
add(music, walk0, pad([midi(m) for m in (50, 57, 62, 66, 69)], run0 - walk0 + .5, run0 - walk0, .3), .2)
for i in range(8):
    add(music, walk0 + i * (run0 - walk0) / 8, musicbox(midi([62, 66, 69, 74, 66, 69, 74, 78][i]), 1.2), .1 + i * .01)
beat = 60 / 138.0
prog8 = ["D", "A", "Bm", "G", "D", "A", "G", "A"]
mel8 = [[78, 76, 74, 76], [73, 74, 76, 69], [74, 76, 78, 81], [83, 81, 78, 76], [78, 81, 83, 86], [85, 83, 81, 78], [79, 81, 83, 79], [81, 0, 85, 0]]
end_t = bs("end") + 1.5
t = run0; i = 0
while t < end_t:
    ch = CH[prog8[i % 8]]
    for b in range(4):
        tb = t + b * beat
        # gallop rhythm in the bass: da-da-DUM
        for off, g in ((0, .14), (beat / 4, .14), (beat / 2, .26)):
            add(music, tb + off, bassnote(midi(ch[0]), .35), g)
        for m in ch[1:]: add(music, tb + beat / 2, pluck(midi(m + 12), .5, .7, 5), .035, .3)
        m = mel8[i % 8][b]
        if m: add(music, tb, pluck(midi(m), 1.0, 1.0, 2.2), .1, -.2)
    add(music, t, pad([midi(m) for m in ch[1:]], 4 * beat + .6, .3, .5), .08)
    t += 4 * beat; i += 1
# final ringing chord
add(music, end_t, pad([midi(m) for m in (50, 57, 62, 66, 69, 74)], 6, .2, 4), .22)
for j, m in enumerate([62, 66, 69, 74, 78]): add(music, end_t + j * .08, pluck(midi(m), 5, 1.0, .9), .09)

# ============================================================ SFX
def noise(L): return rng.standard_normal(L)
def lowpass(x, a):  # one-pole
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a * (x[i] - s); y[i] = s
    return y
def lp_fast(x, k):  # moving-average low-pass (vectorised)
    return np.convolve(x, np.ones(k) / k, mode="same")

def chirp(f0, f1, d):
    L = int(d * SR); t = np.arange(L) / SR
    f = np.linspace(f0, f1, L); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.sin(np.pi * t / d) ** 2

def birdsong(t, gain=.05, pan=.5):
    for j in range(rng.integers(2, 5)):
        f0 = rng.uniform(2800, 4200); add(sfx, t + j * .11, chirp(f0, f0 * rng.uniform(1.1, 1.5), .08), gain, pan)

# ambient birds in the happy clearing
tt = 1.0
while tt < bs("crickets"):
    birdsong(tt, .035, rng.uniform(-.7, .7)); tt += rng.uniform(1.5, 3.5)
tt = SC["s4"]["start"]
while tt < SC["s4"]["end"]:
    birdsong(tt, .03, rng.uniform(-.7, .7)); tt += rng.uniform(1.8, 3.8)
# crickets
c0, c1 = bs("crickets") - .05, be("crickets") + .15
tt = c0
while tt < c1:
    L = int(.05 * SR); tc = np.arange(L) / SR
    add(sfx, tt, np.sin(2 * np.pi * 4700 * tc) * (np.sin(2 * np.pi * 60 * tc) > 0) * np.hanning(L), .05, .4)
    add(sfx, tt + .03, np.sin(2 * np.pi * 4700 * tc) * (np.sin(2 * np.pi * 60 * tc) > 0) * np.hanning(L), .045, .4)
    tt += .42
# bubble pop
L = int(.08 * SR); tp = np.arange(L) / SR
add(sfx, bs("s2g") + .8, np.sin(2 * np.pi * (900 - 6000 * tp) * tp) * np.exp(-tp * 60), .35)
# bird arrives / sings / leaves
s3 = SC["s3"]["start"]
for k in range(6): birdsong(s3 + .4 + k * .3, .05, .6)
for k in range(4): birdsong(be("s3c") + .2 + k * .25, .05, .7)
# whoosh on camera punch
L = int(.35 * SR); tw = np.arange(L) / SR
add(sfx, bs("s3g") - .25, lp_fast(noise(L), 12) * np.sin(np.pi * tw / .35) ** 2, .25)

# hooves
def clop(gain=.3, pitch=1.0):
    L = int(.09 * SR); t = np.arange(L) / SR
    return (np.sin(2 * np.pi * 180 * pitch * t) * np.exp(-t * 55) + .5 * lp_fast(noise(L), 3) * np.exp(-t * 90)) * gain
def walk_clops(t0, t1, rate):  # rate = gait cycles/sec, 4 footfalls per cycle
    tt = t0
    while tt < t1: add(sfx, tt, clop(.18, rng.uniform(.9, 1.1)), 1, .2); tt += 1 / (rate * 4)
walk_clops(14.0, 15.9, 1.25)
walk_clops(be("s8b") + .3, be("s8b") + 3.2, 1.7)
walk_clops(dissolve - .4, run0, 1.7)
tt = run0
while tt < stopT + 1.4:
    fade = 1 - max(0, (tt - stopT) / 1.4)
    for off in (0, .07, .19, .26):
        add(sfx, tt + off, clop(.32 * fade, rng.uniform(.8, 1.0)), 1, 0)
    tt += 1 / 2.3

# rain + thunder in s6
r0, r1 = SC["s6"]["start"], be("s6b") + .1
L = int((r1 - r0 + .3) * SR)
rain_n = noise(L); rain_n = rain_n - lp_fast(rain_n, 6)  # high-passed hiss
e = np.ones(L); e[:SR] = np.linspace(0, 1, SR); e[-int(.15 * SR):] = np.linspace(1, 0, int(.15 * SR))
add(sfx, r0, rain_n * e, .09, -.3); add(sfx, r0, np.roll(rain_n, 999) * e, .09, .3)
def thunder(t, dur, gain):
    L = int(dur * SR); tt = np.arange(L) / SR
    x = lp_fast(noise(L), 160) * 6 + lp_fast(noise(L), 40) * 1.5 * np.exp(-tt * 6)
    add(sfx, t, x * np.minimum(1, tt / .05) * np.exp(-tt * (3 / dur)), gain)
thunder(SC["s6"]["start"] + .3, 3.5, .5)
thunder(bf("s6b", .86), 3.0, .75)
# honey pot drop
L = int(.25 * SR); th = np.arange(L) / SR
add(sfx, be("s6b") + .7, (np.sin(2 * np.pi * 120 * th) * np.exp(-th * 25) + .4 * lp_fast(noise(L), 4) * np.exp(-th * 40)), .5, .2)
# pasture wind + birds
w0 = dissolve - .4
L = int((DUR - w0) * SR)
wind = lp_fast(noise(L), 220) * 9 * (1 + .5 * np.sin(2 * np.pi * .15 * np.arange(L) / SR))
e = np.ones(L); e[:SR] = np.linspace(0, 1, SR); e[-2 * SR:] = np.linspace(1, 0, 2 * SR)
add(sfx, w0, wind * e, .05)
tt = w0
while tt < DUR - 2:
    birdsong(tt, .03, rng.uniform(-.7, .7)); tt += rng.uniform(1.5, 3.0)

# ------------------------------------------------------------- reverb on music
def reverb(x, secs=2.2, mix=.28):
    L = int(secs * SR); t = np.arange(L) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(L) * np.exp(-t * 3.2); ir[0] = 0; ir /= np.sqrt((ir ** 2).sum())
        nfft = 1 << int(np.ceil(np.log2(len(x) + L)))
        y = np.fft.irfft(np.fft.rfft(x[:, ch], nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
        out[:, ch] = x[:, ch] * (1 - mix) + y * mix * .6
    return out
music = reverb(music)
sfx = reverb(sfx, 1.2, .15)

# ------------------------------------------------------------- mix with ducking
with wave.open(os.path.join(B, "voice.wav")) as w:
    voice = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
venv = lp_fast(np.abs(voice), 2205)
venv = np.clip(venv / (np.percentile(venv[venv > 1e-4], 90) + 1e-9), 0, 1)
venv = np.maximum.accumulate(venv[::-1])[::-1] * 0 + venv  # (kept simple)
venv = lp_fast(venv, 8820)
duck = 1 - .5 * np.clip(venv * 1.5, 0, 1)
mix = music * duck[:, None] * .9 + sfx + np.stack([voice, voice], 1) * 1.0
bed = music * duck[:, None] * .9 + sfx
sp = venv > .3
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
print(f"voice(speech) {rms(voice[sp]):.1f} dB | bed(speech) {rms(bed[sp]):.1f} dB | bed(no speech) {rms(bed[~sp]):.1f} dB | music raw {rms(music):.1f} | sfx {rms(sfx):.1f}")
peak = np.abs(mix).max()
mix = np.tanh(mix * .95) * .97  # soft limiter: keeps dialogue level, tames thunder peaks
with wave.open(os.path.join(B, "mix.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("mix written", DUR, "s, peak", peak)
