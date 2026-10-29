"""Original ambient score, synthesized (no samples): pads, strings, choir, piano, drones, swells.
Timed to script/timeline.json.  Usage: python3 -I audio/music.py <out.wav>
"""
import json, os, sys

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(f"{ROOT}/script/timeline.json"))
shots = {s["id"]: s for s in json.load(open(f"{ROOT}/script/shots.json"))["shots"]}
U = {u["id"]: u for u in tl["units"]}
TOTAL = tl["duration"]
N = int(TOTAL * SR) + SR * 6
L = np.zeros(N, np.float32)
Rt = np.zeros(N, np.float32)
rng = np.random.default_rng(22)


def mf(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a, r, curve=2.0):
    e = np.ones(n, np.float32)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na: e[:na] = (np.linspace(0, 1, na) ** curve)
    if nr: e[-nr:] *= (np.linspace(1, 0, nr) ** curve)
    return e


def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N: return
    n = min(len(sig), N - i)
    lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + n] += sig[:n] * gain * lg
    Rt[i:i + n] += sig[:n] * gain * rg


def additive(f0, dur, amp_of, detunes=(0.0,), vib=(0.0, 0.0), maxf=7000.0, drift=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for dc in detunes:
        ph0 = rng.uniform(0, 2 * np.pi)
        vr = vib[0] * rng.uniform(0.9, 1.1)
        cents = dc + vib[1] * np.sin(2 * np.pi * vr * t + ph0) + drift * np.sin(2 * np.pi * 0.07 * t + ph0)
        f = f0 * 2 ** (cents / 1200)
        phase = 2 * np.pi * np.cumsum(f) / SR
        k = 1
        while k * f0 < maxf:
            a = amp_of(k, k * f0)
            if a > 1e-4:
                out += (a * np.sin(k * phase + rng.uniform(0, 2 * np.pi))).astype(np.float32)
            k += 1
    return out / max(1, len(detunes))


def lp(fc, slope=2.0):
    return lambda k, f: (1.0 / k) / (1 + (f / fc) ** slope)


def pad(midis, t0, dur, gain=0.08, fc=900, a=2.5, r=3.0, pan_spread=0.6):
    for i, m in enumerate(midis):
        s = additive(mf(m), dur, lp(fc, 2.4), detunes=(-9, 0, 8), vib=(0.25, 3), maxf=5000, drift=4)
        s *= env(len(s), a, r)
        add(s, t0, pan=(i / max(1, len(midis) - 1) - 0.5) * 2 * pan_spread, gain=gain)


def strings(midis, t0, dur, gain=0.06, fc=2200, a=3.0, r=3.0):
    for i, m in enumerate(midis):
        s = additive(mf(m), dur, lp(fc, 3.0), detunes=(-6, 0, 6, 11), vib=(5.2, 9), maxf=7000)
        s *= env(len(s), a, r)
        add(s, t0, pan=rng.uniform(-0.7, 0.7), gain=gain)


FORMANTS = [(730, 90, 1.0), (1090, 110, 0.5), (2440, 160, 0.22)]  # "ah"


def choir(midis, t0, dur, gain=0.05, a=2.5, r=3.0):
    def amp(k, f):
        g = sum(w * np.exp(-((f - fc) / bw) ** 2) for fc, bw, w in FORMANTS)
        return (0.25 / k + g) / (1 + (f / 3500) ** 3)
    for m in midis:
        s = additive(mf(m), dur, amp, detunes=(-12, -4, 4, 12), vib=(5.0, 14), maxf=6000)
        s *= env(len(s), a, r)
        add(s, t0, pan=rng.uniform(-0.6, 0.6), gain=gain)


def piano(m, t0, vel=0.6, dur=6.0, pan=0.0):
    f0 = mf(m)
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n, np.float32)
    B = 0.0004
    for k in range(1, 18):
        fk = f0 * k * np.sqrt(1 + B * k * k)
        if fk > 9000: break
        decay = 1.2 + 0.9 * k ** 0.9 + f0 / 300
        a = (vel ** (1 + k * 0.08)) / k ** 1.1
        s += (a * np.exp(-decay * t) * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28))).astype(np.float32)
    hammer = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t * 90) * 0.04 * vel
    s += hammer
    s *= env(n, 0.004, 0.4, 1.0)
    add(s, t0, pan=pan, gain=0.22)


def drone(m, t0, dur, gain=0.07):
    s = additive(mf(m), dur, lp(300, 2.0), detunes=(-4, 4), vib=(0.15, 4), maxf=1200)
    s *= env(len(s), 4.0, 4.0)
    s *= (0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * np.arange(len(s)) / SR)).astype(np.float32)
    add(s, t0, gain=gain)


def boom(t0, gain=0.5):
    n = int(4.0 * SR); t = np.arange(n) / SR
    f = 55 * np.exp(-t * 1.2) + 28
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    s += rng.normal(0, 1, n) * np.exp(-t * 18) * 0.15
    sos = butter(4, 160, 'low', fs=SR, output='sos')
    add(sosfilt(sos, s).astype(np.float32), t0, gain=gain)


def swell(t0, dur, gain=0.12):
    # reversed-cymbal-like rising air
    n = int(dur * SR); t = np.arange(n) / SR
    s = rng.normal(0, 1, n) * (t / dur) ** 3
    sos = butter(2, [1500, 9000], 'band', fs=SR, output='sos')
    s = sosfilt(sos, s).astype(np.float32)
    add(s, t0, pan=-0.3, gain=gain); add(s[::-1][::-1].copy(), t0, pan=0.3, gain=gain)


def pulse(m, t0, dur, period=0.83, gain=0.06):
    k = 0
    while k * period < dur:
        s = additive(mf(m), 0.45, lp(700, 2.5), detunes=(-5, 5), maxf=3000)
        s *= env(len(s), 0.02, 0.35, 1.5)
        add(s, t0 + k * period, pan=-0.2 if k % 2 else 0.2, gain=gain * (1.0 if k % 2 == 0 else 0.7))
        k += 1


def bell(m, t0, gain=0.05, pan=0.0):
    n = int(5 * SR); t = np.arange(n) / SR
    f = mf(m)
    s = sum(a * np.exp(-t * d) * np.sin(2 * np.pi * f * r * t) for r, a, d in [(1, 1, 0.9), (2.76, 0.4, 1.6), (5.4, 0.2, 2.5), (8.93, 0.08, 3.5)])
    add(s.astype(np.float32), t0, pan=pan, gain=gain)


CH = {
    'Dm': [50, 57, 62, 65, 69], 'Bb': [46, 53, 58, 62, 65], 'F': [41, 53, 57, 60, 65], 'C': [48, 55, 60, 64, 67],
    'Gm': [43, 50, 55, 58, 62], 'A': [45, 52, 57, 61, 64], 'Dsus': [50, 57, 62, 64, 69], 'D': [50, 57, 62, 66, 69, 74],
    'Am': [45, 52, 57, 60, 64], 'Fadd9': [41, 53, 57, 60, 67],
}

T1 = U['u01']['start']; T_ONE = U['u11']['start']; T_B = U['u12']['start']; T_SEIZE = U['u27']['start']
T_CH = shots['S21_chapter']['start']; T_C = U['u28']['start']; T_WORLD = U['u34']['start']; T_CRE = U['u36']['start']
T_GETH = U['u37']['start']; T_FIN = U['u40']['start']; T_END = shots['S34_end']['start']

# ---- Title + John 10:25-30 : gentle D minor, swelling at "I and the Father are one"
drone(38, 0.0, T_B + 2)
seq = ['Dm', 'Bb', 'F', 'C']
t = 0.0; i = 0
while t < T_ONE - 4:
    d = min(8.0, T_ONE - 2 - t)
    pad(CH[seq[i % 4]], t, d + 3.0, gain=0.055)
    t += 8.0; i += 1
melA = [(74, 0.0), (72, 1.0), (69, 2.0), (67, 4.0), (69, 5.0), (65, 6.5)]
for bar in range(int((T_ONE - 6) // 8)):
    base = 6.0 + bar * 8.0
    for m, dt in melA[: 3 + (bar % 3)]:
        piano(m - (0 if bar % 2 == 0 else 2), base + dt, vel=0.45 + 0.1 * (bar % 2), pan=0.15)
piano(62, 1.2, 0.5); piano(69, 2.2, 0.45); piano(74, 3.0, 0.4)
swell(T_ONE - 3.0, 3.0, gain=0.08)
boom(T_ONE - 0.05, gain=0.45)
pad(CH['Dsus'], T_ONE - 2.0, 7.5, gain=0.06, fc=1400)
strings([62, 69, 74, 77], T_ONE - 1.5, 7.0, gain=0.05)
choir([62, 69, 74], T_ONE - 0.8, 6.5, gain=0.06)
bell(86, T_ONE + 0.2, 0.05, 0.3); bell(81, T_ONE + 1.4, 0.04, -0.3)

# ---- John 10:31-39 : stones and accusation — darker, pulsing
seqB = ['Dm', 'Gm', 'Bb', 'A']
t = T_B; i = 0
while t < T_SEIZE + 2:
    pad(CH[seqB[i % 4]], t, 10.0, gain=0.05, fc=700)
    t += 7.0; i += 1
pulse(38, T_B + 0.5, T_SEIZE + 4.5 - T_B, period=0.83, gain=0.07)
pulse(45, T_B + 14.5, T_SEIZE - T_B - 12, period=1.66, gain=0.04)
drone(33, T_B, T_SEIZE + 6 - T_B, gain=0.06)
for k, tt in enumerate(np.arange(T_B + 2, T_SEIZE, 9.0)):
    piano(62 if k % 2 == 0 else 60, tt, 0.35, pan=-0.2); piano(57, tt + 1.4, 0.3, pan=0.2)
strings([50, 57, 62], T_SEIZE - 6, 9.0, gain=0.045, a=5.0)
swell(T_SEIZE - 1.0, 2.6, gain=0.07)
boom(T_SEIZE + 1.8, gain=0.4)
pad(CH['A'], T_SEIZE + 1.0, 6.0, gain=0.05)

# ---- Chapter card: suspended, warm, quiet
pad(CH['Fadd9'], T_CH - 1.0, (T_C - T_CH) + 5, gain=0.05, fc=1600, a=2.0)
for k, m in enumerate([77, 81, 84, 88]):
    bell(m, T_CH + 0.4 + k * 0.7, 0.035, pan=(-1) ** k * 0.4)

# ---- John 17:20-26 : the prayer — warm, building through glory and creation
seqC = ['F', 'C', 'Dm', 'Bb']
t = T_C; i = 0
while t < T_GETH - 2:
    g = 0.05 + (0.012 if t > T_WORLD else 0.0)
    pad(CH[seqC[i % 4]], t, 11.0, gain=g, fc=1100 if t < T_WORLD else 1500)
    t += 8.0; i += 1
melC = [(69, 0.0), (72, 1.0), (74, 2.0), (77, 3.5), (76, 5.0), (74, 6.0)]
for bar in range(int((T_GETH - T_C) // 8)):
    base = T_C + 0.8 + bar * 8.0
    for m, dt in melC[: 3 + (bar % 4)]:
        piano(m - [0, 2, 0, -2][bar % 4], base + dt, vel=0.42 + 0.06 * (bar % 3), pan=0.1)
strings([53, 60, 65, 69], T_WORLD - 1.0, T_CRE - T_WORLD + 2, gain=0.04, a=6.0)
swell(T_CRE - 3.0, 3.0, gain=0.09)
boom(T_CRE - 0.1, gain=0.4)
choir([65, 69, 72, 77], T_CRE - 1.0, (T_GETH - T_CRE) + 1.5, gain=0.055, a=3.0)
strings([65, 72, 77, 81], T_CRE - 0.5, (T_GETH - T_CRE) + 1.0, gain=0.045)
for k in range(6):
    bell([81, 84, 88, 86, 84, 81][k], T_CRE + 0.5 + k * 1.3, 0.035, pan=(-1) ** k * 0.5)
# Gethsemane: intimate — piano and a soft pad only
pad(CH['Dm'], T_GETH - 1.5, 11.0, gain=0.045, fc=800)
for k, (m, dt) in enumerate([(62, 0.5), (65, 1.6), (69, 2.7), (67, 4.4), (65, 5.6), (62, 6.8)]):
    piano(m, T_GETH + dt, 0.4, pan=-0.1)
# build to the final resolution on D major
pad(CH['Bb'], T_GETH + 6.0, 8.0, gain=0.05)
pad(CH['C'], T_GETH + 12.5, 6.0, gain=0.055)
strings([58, 65, 70], T_GETH + 6.5, 11.5, gain=0.04, a=4.0)
swell(T_FIN - 3.0, 3.0, gain=0.09)
boom(T_FIN - 0.05, gain=0.45)
pad(CH['D'], T_FIN - 0.5, TOTAL - T_FIN + 2, gain=0.065, fc=1600, r=6.0)
strings([62, 69, 74, 78], T_FIN - 0.2, TOTAL - T_FIN, gain=0.045, r=6.0)
choir([62, 66, 69, 74], T_FIN, TOTAL - T_FIN - 1.0, gain=0.055, r=6.0)
drone(38, T_FIN - 1.0, TOTAL - T_FIN + 2, gain=0.06)
for k, m in enumerate([62, 66, 69, 74, 78, 81, 78, 74]):
    piano(m, T_END + 0.6 + k * 0.55, 0.38 - 0.02 * k, pan=0.2 * (-1) ** k)
bell(86, T_END + 5.5, 0.04)

# ---- reverb (synthetic hall) and master
def hall(seconds=4.6, seed=3):
    r = np.random.default_rng(seed)
    n = int(seconds * SR); t = np.arange(n) / SR
    irs = []
    for ch in range(2):
        ir = r.normal(0, 1, n) * np.exp(-6.9 * t / seconds)
        sos = butter(1, 5200, 'low', fs=SR, output='sos')
        ir = sosfilt(sos, ir)
        for d, a in [(0.013, 0.5), (0.021, 0.4), (0.034, 0.3), (0.047, 0.25)]:
            ir[int((d + 0.003 * ch) * SR)] += a
        irs.append((ir / np.sqrt(np.sum(ir ** 2))).astype(np.float32))
    return irs
irL, irR = hall()
wetL = fftconvolve(L, irL)[:N]
wetR = fftconvolve(Rt, irR)[:N]
mixL = 0.62 * L + 0.55 * wetL
mixR = 0.62 * Rt + 0.55 * wetR
sos = butter(2, 30, 'high', fs=SR, output='sos')
out = np.stack([sosfilt(sos, mixL), sosfilt(sos, mixR)], axis=1)[: int(TOTAL * SR)]
fade = np.ones(len(out)); nf = int(3.5 * SR); fade[-nf:] = np.linspace(1, 0, nf) ** 1.5
out *= fade[:, None]
out /= max(1e-6, np.max(np.abs(out))) / 0.8
sf.write(sys.argv[1], out.astype(np.float32), SR, subtype='PCM_24')
print('music written', sys.argv[1], f'{len(out) / SR:.2f}s')
