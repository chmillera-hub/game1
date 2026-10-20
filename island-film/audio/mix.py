"""mix.py - final mix: dialogue + music + ambience + sfx -> build/mix.wav (48 kHz stereo, 16-bit).
Usage: python3 audio/mix.py   (run from film root; run score.py and sfx.py first)
Inputs : build/dialogue.wav, build/music.wav, build/amb.wav, build/sfx.wav, build/timeline.json
Ducking: dialogue envelope (150 ms attack / 400 ms release) -> music -9 dB, ambience -5 dB.
VO lines (narrator/directive) get a short stereo reverb; directive reverb is narrower.
Loudness: ~-14 LUFS integrated (ffmpeg ebur128 measure), true peak <= -1 dBTP (4x oversampled limiter).
Length = timeline duration exactly. Prints a level report.
"""
import json, subprocess, re, numpy as np, soundfile as sf
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt
SR = 48000; T = json.load(open('build/timeline.json')); N = int(round(T['duration'] * SR))
def load(p):
    a, sr = sf.read(p, always_2d=True); assert sr == SR, p
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    return a[:N] if len(a) >= N else np.vstack([a, np.zeros((N - len(a), 2))])
db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
dia, mus, amb, sfx = (load(f'build/{k}.wav') for k in ('dialogue', 'music', 'amb', 'sfx'))
# per-line dialogue levelling (voices.wav levels vary a lot): each line -> -20 dBFS RMS
for sh in T['shots']:
    for l in sh['lines']:
        a = int(l['start'] * SR); b = min(N, int(l['end'] * SR)); seg = dia[a:b]
        if b > a and db(seg) > -80: dia[a:b] *= 10 ** (np.clip(-20 - db(seg), -15, 15) / 20)
# stem gain staging (RMS targets, dBFS) relative to dialogue
spk = np.abs(dia[:, 0]) > 1e-4; dlev = db(dia[spk, :]) if spk.any() else -20
mus *= 10 ** ((dlev - 9 - db(mus)) / 20); amb *= 10 ** ((dlev - 19 - db(amb)) / 20); sfx *= 10 ** (-4 / 20)
# VO reverb
R = np.random.default_rng(7); n = int(.6 * SR); t = np.arange(n) / SR
ir = [R.standard_normal(n) * np.exp(-t / .12) for _ in range(2)]
ir = [sosfilt(butter(2, [300, 6000], 'band', fs=SR, output='sos'), i) for i in ir]; ir = [i / np.sqrt(np.sum(i ** 2)) for i in ir]
rev = np.zeros((N, 2))
for s in T['shots']:
    for l in s['lines']:
        if not l.get('vo'): continue
        a = int(l['start'] * SR); b = min(N, int((l['end'] + .05) * SR)); x = dia[a:b, 0]
        w = .5 if l['speaker'] == 'directive' else 1.0; g = .18
        L = fftconvolve(x, ir[0]); Rr = fftconvolve(x, ir[1]); m = (L + Rr) / 2
        L = m + w * (L - m); Rr = m + w * (Rr - m); e = min(N, a + len(L)) - a
        rev[a:a + e, 0] += L[:e] * g; rev[a:a + e, 1] += Rr[:e] * g
dia = dia + rev
# duck envelope
lvl = np.abs(dia[:, 0]); env = np.zeros(N); aa = np.exp(-1 / (.15 * SR)); rr = np.exp(-1 / (.4 * SR))
blk = 240; bl = lvl[:N // blk * blk].reshape(-1, blk).max(1); ab = aa ** blk; rb = rr ** blk
ek = np.zeros(len(bl)); v = 0
thr = 10 ** (-40 / 20) * max(bl.max(), 1e-6) * 3
for i, x in enumerate(bl):
    tgt = 1.0 if x > thr else 0.0; c = ab if tgt > v else rb; v = tgt + (v - tgt) * c; ek[i] = v
env[:len(ek) * blk] = np.repeat(ek, blk); env[len(ek) * blk:] = ek[-1]
mix = dia + mus * 10 ** (-9 * env / 20)[:, None] + amb * 10 ** (-5 * env / 20)[:, None] + sfx
sf.write('build/mix_pre.wav', mix.astype(np.float32), SR, subtype='FLOAT')
def lufs(p):
    o = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    I = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]); P = float(re.findall(r'Peak:\s+(-?[\d.inf]+) dBFS', o)[-1]); return I, P
I0, _ = lufs('build/mix_pre.wav'); pre = mix.copy()
def limit(mix):
    # true-peak limiter: 4x oversampled peak, gain smoothed (5 ms lookahead / 80 ms release)
    ceil = 10 ** (-1.2 / 20)
    pk = np.abs(resample_poly(mix, 4, 1, axis=0)).max(1).reshape(-1, 4).max(1)[:N]
    g = np.minimum(1, ceil / np.maximum(pk, 1e-9)); la = int(.005 * SR)
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(g, 2 * la + 1); rel = np.exp(-1 / (.08 * SR)); out = np.empty(N); v = 1.0
    for i in range(0, N, 48):  # coarse 1 ms release smoothing
        gm = g[i:i + 48].min(); v = gm if gm < v else gm + (v - gm) * rel ** 48; out[i:i + 48] = v
    out = np.minimum(out, g); return mix * out[:, None], out
gain = -14 - I0
for it in range(3):
    mix, out = limit(pre * 10 ** (gain / 20)); sf.write('build/mix.wav', mix, SR, subtype='PCM_16')
    I, P = lufs('build/mix.wav'); gain += -14 - I
    if abs(I + 14) < .3: break
import os; os.remove('build/mix_pre.wav')
print(f'duration {len(mix)/SR:.3f}s (timeline {T["duration"]})  LUFS {I}  truePeak {P} dBTP  limiter max GR {20*np.log10(out.min()):.1f} dB')
for s in T['shots']:
    a, b = int(s['start'] * SR), int(s['end'] * SR)
    print(f"{s['id']:5} {s['mood'][:14]:14} mix {db(mix[a:b]):6.1f}  dia {db(dia[a:b]):6.1f}  mus {db(mus[a:b]):6.1f}  amb {db(amb[a:b]):6.1f}  sfx {db(sfx[a:b]):6.1f}")
