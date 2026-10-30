"""Score + sound design + mix -> BUILD/mix.wav"""
import math
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
from common import BUILD, TL, LINES, SCENES, DUR, L, at, word_t, hsh
import shots
import world

SR = 48000
N = int((DUR + 1.0) * SR)
rng = np.random.default_rng(7)
voice = np.zeros((N, 2))
music = np.zeros((N, 2))
sfx = np.zeros((N, 2))


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pan2(x, p=0.0):
    a = (p + 1) * math.pi / 4
    return np.stack([x * math.cos(a), x * math.sin(a)], 1)


def add(buf, t, x, p=0.0, g=1.0):
    i = int(t * SR)
    if i >= N or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    x = x[: N - i]
    buf[i:i + len(x)] += pan2(x, p) * g if x.ndim == 1 else x * g


def env(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, sus, na) ** 1.5
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def lp(x, fc, order=2):
    return sosfilt(butter(order, fc, "low", fs=SR, output="sos"), x)


def bp(x, f1, f2):
    return sosfilt(butter(2, [f1, f2], "band", fs=SR, output="sos"), x)


# ---------------------------------------------------------------- instruments
def tone(f, dur, harm, detune=0.0015, vib=0.0, vib_f=5.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, detune):
        ff = f * (1 + d)
        ph0 = rng.random() * 6.28
        mod = 1 + vib * np.sin(2 * np.pi * vib_f * tt + ph0)
        phase = 2 * np.pi * np.cumsum(ff * mod) / SR
        for h, a in enumerate(harm, 1):
            if a <= 0 or ff * h > 12000:
                continue
            out += a * np.sin(h * phase + ph0 * h)
    return out / 2


def pad(fs, t0, dur, amp=0.1, bright=0.4, a=1.5, r=2.0, choir=False):
    for k, f in enumerate(fs):
        if choir:
            hs = [sum(math.exp(-((f * h - fm) / bw) ** 2) * g for fm, bw, g in ((800, 180, 1), (1150, 200, 0.6), (2900, 400, 0.25)))
                  + 0.15 / h for h in range(1, 16)]
        else:
            hs = [(1 / h) * math.exp(-h * (1 - bright) * 0.6) for h in range(1, 12)]
        x = tone(f, dur + r, hs, vib=0.003, vib_f=4.5 + k * 0.3) * env(int((dur + r) * SR), a, r)
        add(music, t0, x, p=(k / max(1, len(fs) - 1) - 0.5) * 0.8, g=amp / len(fs) ** 0.5)


def piano(f, t, amp=0.12, dur=4.0, p=0.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * math.sqrt(1 + 0.0004 * h * h)
        if fh > 14000:
            break
        x += (1 / h ** 1.3) * np.sin(2 * np.pi * fh * tt) * np.exp(-tt * (0.9 + h * 0.55))
    x *= env(n, 0.004, 0.3)
    add(music, t, x, p, amp)


def bell(f, t, amp=0.1, p=0.0, dur=3.5):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for r_, a_, d_ in ((1, 1, 1.6), (2.0, 0.45, 2.2), (3.01, 0.25, 3.0), (4.16, 0.18, 4.0), (5.43, 0.08, 5.0)):
        x += a_ * np.sin(2 * np.pi * f * r_ * tt) * np.exp(-tt * d_)
    x *= env(n, 0.003, 0.4)
    add(music, t, x, p, amp)


def cello(f, t0, dur, amp=0.12, p=0.0, a=0.6):
    hs = [(1 / h) * math.exp(-h * 0.25) for h in range(1, 14)]
    x = tone(f, dur, hs, detune=0.001, vib=0.004, vib_f=5.3)
    x = lp(x, 1800) * env(len(x), a, min(1.0, dur * 0.5))
    add(music, t0, x, p, amp)


def drum(t, amp=0.3, f0=90, f1=42, dec=0.55, buf=None, p=0.0):
    n = int(1.2 * SR)
    tt = np.arange(n) / SR
    fr = f1 + (f0 - f1) * np.exp(-tt * 18)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / dec * 2.2)
    x += lp(rng.standard_normal(n), 900) * np.exp(-tt * 60) * 0.3
    add(music if buf is None else buf, t, x, p, amp)


def swell(t0, dur, amp=0.08, fc=6000):
    n = int(dur * SR)
    x = lp(rng.standard_normal(n), fc) * np.linspace(0, 1, n) ** 3
    x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    add(music, t0, np.stack([x, np.roll(x, 300)], 1) * amp)


# ---------------------------------------------------------------- harmony
C = dict(Dm=[50, 53, 57], Bb=[46, 50, 53], Gm=[43, 50, 55], A=[45, 52, 57], F=[41, 48, 53, 57], C=[48, 52, 55],
         Dm9=[50, 53, 57, 64], Bbmaj7=[46, 50, 53, 57], Fa=[45, 48, 53], Gm7=[43, 50, 53, 58], D=[50, 54, 57],
         Csus=[48, 53, 55])
SC = {k: v for k, v in SCENES.items()}
PLAN = [  # (scene, progression, chord seconds, pad amp, brightness, choir)
    ("open", ["Dm9"], 4.0, 0.10, 0.35, True),
    ("horde", ["Dm", "Bb", "Gm", "A"], 5.0, 0.13, 0.35, False),
    ("soul", ["Bb", "F", "C", "F"], 1.85, 0.12, 0.55, True),
    ("wake", ["Dm9", "Bbmaj7"], 4.8, 0.08, 0.35, False),
    ("hands", ["Dm", "Bb", "Gm", "A"], 2.8, 0.09, 0.35, False),
    ("witness", ["Dm", "Bb", "Gm", "A"], 4.1, 0.13, 0.45, False),
    ("knees", ["Dm", "Bb", "F", "C", "Gm", "A"], 4.2, 0.12, 0.4, False),
    ("sky", ["Bbmaj7", "Fa", "Gm7", "Csus"], 6.4, 0.11, 0.5, True),
    ("building", ["Dm", "C", "Bb", "C"], 4.0, 0.12, 0.5, False),
    ("flag", ["Dm", "Bb", "F", "C"], 3.9, 0.17, 0.6, True),
    ("heli", ["Dm", "Dm"], 6.9, 0.07, 0.3, False),
    ("cabin", ["Dm9", "F", "Bbmaj7", "F", "Gm7", "Csus", "F", "F"], 5.06, 0.08, 0.35, False),
    ("end", ["Bb", "F", "C", "D"], 3.05, 0.16, 0.6, True),
]
CHORD_AT = []
for sc, prog, cd, amp, br, ch in PLAN:
    t0, t1 = SC[sc]
    t = t0
    k = 0
    while t < t1 - 0.2:
        d = min(cd, t1 - t)
        last = t + d >= t1 - 0.2
        name = prog[k % len(prog)]
        CHORD_AT.append((t, t + d, name))
        skip = sc == "sky" and t < L("y2")[0] - 0.3   # silence around "Is anyone there?"
        if not skip:
            pad([midi(m) for m in C[name]], t, d + (0.4 if not last else 1.5), amp, br, a=1.2 if sc != "flag" else 0.6)
            if ch:
                pad([midi(m + 12) for m in C[name][1:]], t, d + 0.4, amp * 0.6, 0.5, a=1.5, choir=True)
            # bass
            root = C[name][0] - 12
            cello(midi(root), t, d + 0.3, amp * (0.9 if sc in ("horde", "witness", "flag", "knees") else 0.5), a=0.8)
        t += d
        k += 1


def chord(t):
    for a, b, n in CHORD_AT:
        if a <= t < b:
            return C[n]
    return C["Dm"]


# ---------------------------------------------------------------- melodic layers
def melody(t0, t1, notes, step, amp=0.11, inst=piano):
    t = t0
    k = 0
    while t < t1:
        m = notes[k % len(notes)]
        if m:
            inst(midi(m), t, amp, p=0.15 * math.sin(k))
        t += step
        k += 1


# open: chime when the eyes open
bell(midi(81), 1.0, 0.07)
bell(midi(86), 1.45, 0.05)
# horde: war drums ~70 bpm
h0, h1 = SC["horde"]
t = h0 + 0.3
while t < h1:
    drum(t, 0.33)
    if int((t - h0) / 0.857) % 4 == 3:
        drum(t + 0.43, 0.18, f0=120, f1=60)
    t += 0.857
# soul: rising celesta arpeggio + bloom
s0, s1 = SC["soul"]
arp = [65, 69, 72, 77, 81, 84, 89]
for k in range(14):
    bell(midi(arp[k % 7] + (12 if k >= 7 else 0) - 12), s0 + 0.4 + k * 0.33, 0.05, p=math.sin(k) * 0.5)
swell(shots.t_hit - 1.2, 1.2, 0.06)
pad([midi(m) for m in (65, 69, 72, 77)], shots.t_hit, 2.5, 0.14, 0.7, a=0.05, r=2.5)
bell(midi(89), shots.t_hit, 0.09)
# wake: heartbeat + sparse piano
for tb in (shots.w0 + 0.2, shots.w0 + 1.15, shots.w0 + 2.3):
    drum(tb, 0.35, f0=70, f1=38, dec=0.35)
    drum(tb + 0.24, 0.22, f0=65, f1=36, dec=0.3)
melody(SC["wake"][0] + 3.0, SC["wake"][1], [69, None, 74, 72, None, 69, 65, None], 0.9, 0.08)
melody(SC["hands"][0] + 0.5, SC["hands"][1], [74, 72, 69, None, 72, 69, 65, None, 67, 69, None, None], 0.8, 0.08)
# witness: distant drums under, tension
v0, v1 = SC["witness"]
t = v0 + 0.5
while t < v1:
    drum(t, 0.16, f0=80, f1=40)
    t += 1.2
# knees: lament melody
k0, k1 = SC["knees"]
melody(k0 + 1.0, k1 - 1.0, [74, 72, 70, 69, None, 69, 70, 72, 69, None, None, None, 77, 76, 74, 73, 74, None, None, None], 0.62, 0.075)
# sky: staircase of rising bells on y7
y7a, y7b = L("y7")
stair = [62, 64, 65, 67, 69, 70, 72, 74, 76, 77, 79, 81]
for k, m in enumerate(stair):
    bell(midi(m), y7a + k * (y7b - y7a) / len(stair), 0.06, p=-0.5 + k / 12)
# building: soft ostinato + climbing notes
b0, b1 = SC["building"]
t = shots.t_stand
k = 0
while t < b1:
    m = chord(t)
    piano(midi(m[k % len(m)] + 12), t, 0.05, dur=1.2, p=0.3 * math.sin(k))
    t += 0.38
    k += 1
for k in range(10):
    piano(midi(62 + [0, 2, 3, 5, 7, 9, 10, 12, 14, 15][k]), shots.t_climb + 0.2 + k * 0.33, 0.07, p=-0.3 + k * 0.06)
# flag: peak drums
f0, f1 = SC["flag"]
t = f0
while t < f1:
    drum(t, 0.3)
    drum(t + 0.48, 0.15, f0=110, f1=55)
    t += 0.96
melody(f0 + 0.5, f1, [81, 79, 77, 76, 77, None, 74, None], 0.97, 0.06, inst=lambda f, t, a, p: cello(f, t, 0.9, a * 0.8, p, a=0.15))
# heli: low ostinato
r0, r1 = SC["heli"]
t = r0
while t < r1:
    cello(midi(38), t, 0.45, 0.06, a=0.05)
    t += 0.5
# cabin: tender piano
c0, c1 = SC["cabin"]
melody(L("i3")[0] - 2, L("i8")[0], [None, 69, None, 72, None, 74, None, None], 1.1, 0.05)
melody(L("i8")[0], c1, [77, 76, 74, 72, 74, None, 81, 79, 77, None, None, None], 0.8, 0.06)
# end: rising bells into the light
e0, e1 = SC["end"]
melody(e0 + 0.5, e1, [74, 78, 81, 86, None, 81, 78, 74, None, None], 0.6, 0.05, inst=lambda f, t, a, p: bell(f, t, a, p))
pad([midi(m) for m in (50, 54, 57, 62, 66)], word_t("e2", "heaven", 1) - 0.1, 4.5, 0.18, 0.7, a=0.4, r=3.0, choir=True)
bell(midi(86), word_t("e2", "heaven", 1), 0.12)
bell(midi(90), word_t("e2", "heaven", 1) + 0.25, 0.08)

# ---------------------------------------------------------------- word accents: high hopeful / low heavy
for lid in TL["order"]:
    for ac in LINES[lid]["accents"]:
        t = ac["t"]
        ch = chord(t)
        if ac["kind"] == "hi":
            top = max(m for m in ch) + 24
            while top > 90:
                top -= 12
            bell(midi(top), t - 0.03, 0.085)
            bell(midi(top + 7 if top + 7 <= 93 else top - 5), t + 0.12, 0.04)
            pad([midi(top), midi(top - 5)], t - 0.2, 1.6, 0.05, 0.6, a=0.3, r=1.5)
        else:
            root = ch[0] - 24
            while root < 33:
                root += 12
            cello(midi(root), t - 0.25, 2.4, 0.2, a=0.35)
            drum(t - 0.05, 0.12, f0=55, f1=32, dec=0.9)

# ---------------------------------------------------------------- sound design
def noise(n, fc_lo=None, fc_hi=None):
    x = rng.standard_normal(n)
    if fc_lo and fc_hi:
        return bp(x, fc_lo, fc_hi)
    if fc_hi:
        return lp(x, fc_hi)
    return x


def amp_curve(points):
    """Piecewise-linear gain over the whole film."""
    tt = np.arange(N) / SR
    xs, ys = zip(*points)
    return np.interp(tt, xs, ys)


# wind (exteriors)
W_ = noise(N, 150, 900)
W_ *= 0.6 + 0.4 * np.sin(2 * np.pi * np.arange(N) / SR * 0.11)
gw = amp_curve([(0, 0.05), (SC["sky"][0], 0.06), (SC["sky"][0] + 0.5, 0.12), (L("y2")[0], 0.1), (SC["building"][1], 0.09),
                (SC["heli"][1], 0.09), (SC["cabin"][0], 0.0), (SC["cabin"][1], 0.0), (SC["end"][0], 0.07), (DUR, 0.05)])
sfx += np.stack([W_ * gw, np.roll(W_, 1200) * gw], 1)
# horde rumble + footfalls
R_ = lp(np.cumsum(rng.standard_normal(N)) * 0.02, 180)
R_ -= lp(R_, 20)
gr = amp_curve([(0, 0.1), (SC["horde"][0], 0.25), (SC["knees"][0], 0.25), (SC["sky"][0], 0.12), (SC["building"][0], 0.06),
                (SC["heli"][0], 0.08), (SC["cabin"][0], 0.0), (DUR, 0.0)])
sfx += pan2(R_ * gr / (np.std(R_) + 1e-9) * 0.15)
t = 0.0
while t < SC["cabin"][0]:
    g = float(np.interp(t, [0, SC["sky"][0], SC["building"][0], SC["cabin"][0]], [0.10, 0.10, 0.03, 0.03]))
    drum(t, g, f0=140, f1=70, dec=0.12, buf=sfx, p=hsh(int(t * 10), 3) * 1.6 - 0.8)
    t += 0.09 + hsh(int(t * 100), 4) * 0.12
# beams: synced to the on-screen deaths
for tb, X, Zd in world.beam_times(shots.HORDE, 0, SC["cabin"][0]):
    if SC["sky"][0] + 4 < tb < SC["sky"][0] + 10:
        continue
    n = int(0.5 * SR)
    tt = np.arange(n) / SR
    fz = 2400 * np.exp(-tt * 9) + 300
    z = np.sin(2 * np.pi * np.cumsum(fz) / SR) * np.exp(-tt * 9)
    z += noise(n, 2000, 8000) * np.exp(-tt * 20) * 0.4
    sh = noise(int(1.6 * SR), 3000, 9000) * np.exp(-np.arange(int(1.6 * SR)) / SR * 2.2) * 0.25  # dust shimmer
    add(sfx, tb - 0.12, z, p=max(-0.9, min(0.9, X / 40)), g=0.05)
    add(sfx, tb, sh, p=max(-0.9, min(0.9, X / 40)), g=0.05)
# soul descent glissando
s0_, th = SC["soul"][0], shots.t_hit
n = int((th - s0_) * SR)
tt = np.arange(n) / SR
gl = sum(np.sin(2 * np.pi * np.cumsum(f * (1 + tt / tt[-1] * 0.5)) / SR) for f in (880, 1320, 1760)) / 3
add(sfx, s0_, gl * np.linspace(0, 1, n) ** 2, g=0.06)
drum(th, 0.5, f0=60, f1=30, dec=1.5, buf=sfx)
# ladder clanks
for k in range(11):
    tc = shots.t_climb + 0.15 + k * 0.32
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    cl = sum(a * np.sin(2 * np.pi * 820 * r * tt) * np.exp(-tt * d) for r, a, d in ((1, 1, 18), (2.71, 0.6, 25), (5.13, 0.3, 40)))
    add(sfx, tc, cl, p=-0.2 + 0.1 * (k % 2), g=0.06 * (1 - k / 14))
# flag flapping
fl_g = amp_curve([(0, 0), (shots.t_grab + 0.5, 0), (shots.t_grab + 1.0, 0.18), (SC["flag"][1], 0.18), (SC["heli"][0] + 1, 0.25),
                  (shots.t_rope, 0.3), (shots.t_up, 0.2), (SC["heli"][1], 0.0), (DUR, 0)])
F_ = noise(N, 250, 2200) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * np.arange(N) / SR * 3.1)) ** 3)
sfx += pan2(F_ * fl_g * 0.6, 0.2)
# helicopter: rotor thwop + hum + whine; muffled in the cabin; far at the end
tt = np.arange(N) / SR
rot = (np.abs(np.sin(np.pi * tt * 5.2)) ** 8)
Hn = lp(rng.standard_normal(N), 700) * rot * 1.5 + np.sin(2 * np.pi * 72 * tt) * 0.25 + np.sin(2 * np.pi * 1840 * tt) * 0.02
hg = amp_curve([(0, 0), (SC["heli"][0] - 0.5, 0), (SC["heli"][0] + 3.0, 0.22), (shots.t_rope, 0.3), (SC["heli"][1], 0.3),
                (SC["cabin"][0] + 0.2, 0.0), (DUR, 0)])
sfx += pan2(Hn * hg, 0.0)
Hc = lp(Hn, 260)
cg = amp_curve([(0, 0), (SC["cabin"][0] - 0.2, 0), (SC["cabin"][0] + 0.3, 0.3), (SC["cabin"][1] - 1.0, 0.22), (SC["end"][0] + 0.5, 0.0),
                (DUR, 0)])
sfx += pan2(Hc * cg * 1.4)
eg = amp_curve([(0, 0), (SC["end"][0], 0.12), (SC["end"][1], 0.01), (DUR, 0)])
sfx += pan2(lp(Hn, 500) * eg, -0.3)
# rope drop + grab
n = int(0.9 * SR)
add(sfx, shots.t_rope, noise(n, 400, 3000) * np.linspace(1, 0, n) ** 2, g=0.1)
add(sfx, shots.t_grabz + 0.3, noise(int(0.3 * SR), 500, 4000) * np.linspace(1, 0, int(0.3 * SR)), g=0.12)

# ---------------------------------------------------------------- voices
REVERB_SEND = dict(N=0.06, Z=0.12, HA=0.10, HB=0.10)
vsend = np.zeros((N, 2))
for lid in TL["order"]:
    d = LINES[lid]
    y, sr = sf.read(f"{BUILD}/lines/{lid}.wav")
    g = 0.78 if d["spk"] == "N" else 0.9
    add(voice, d["t0"], y, p=0.0, g=g)
    add(vsend, d["t0"], y, p=0.0, g=g * REVERB_SEND[d["spk"]])


# ---------------------------------------------------------------- reverb + mix
def reverb(x, secs=2.6, lpf=5000):
    n = int(secs * SR)
    tt = np.arange(n) / SR
    irl = lp(rng.standard_normal(n), lpf) * np.exp(-tt * 6.9 / secs)
    irr = lp(rng.standard_normal(n), lpf) * np.exp(-tt * 6.9 / secs)
    irl /= np.sqrt(np.sum(irl ** 2)); irr /= np.sqrt(np.sum(irr ** 2))
    return np.stack([fftconvolve(x[:, 0], irl)[:N], fftconvolve(x[:, 1], irr)[:N]], 1)


music = music * 0.8 + reverb(music, 3.0) * 0.45
sfx = sfx + reverb(sfx, 1.6, 3000) * 0.2
voice = voice + reverb(vsend, 1.2, 4000)
# duck music under speech
va = np.abs(voice).max(1)
va = lp(va, 3)
va = np.clip(va / (np.percentile(va[va > 0.01], 60) + 1e-9), 0, 1) if np.any(va > 0.01) else va
duck = 1.0 - 0.45 * va
mix = voice + music * duck[:, None] * 0.75 + sfx * 0.6
# gentle bus compression via soft clip, then peak normalise
mix = np.tanh(mix * 1.1) / 1.1
mix /= np.max(np.abs(mix)) / 0.89
sf.write(f"{BUILD}/mix.wav", mix.astype(np.float32), SR, subtype="FLOAT")
print("mix ok", mix.shape[0] / SR)
