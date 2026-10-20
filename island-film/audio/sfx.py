"""sfx.py - synthesize ambience beds + keyed SFX (numpy, deterministic seed).
Usage: python3 audio/sfx.py   (run from film root)
Inputs : build/timeline.json
Outputs: build/amb.wav (stereo ambience beds per shot setting, 0.4 s crossfades)
         build/sfx.wav (stereo spot effects keyed to shot descs / word times)
Both 48 kHz float, length = timeline duration exactly.
"""
import json, numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt
SR = 48000; T = json.load(open('build/timeline.json')); DUR = T['duration']; N = int(round(DUR * SR))
R = np.random.default_rng(1234)
def filt(x, lo=None, hi=None, o=2):
    if lo and hi: s = butter(o, [lo, hi], 'band', fs=SR, output='sos')
    elif lo: s = butter(o, lo, 'high', fs=SR, output='sos')
    else: s = butter(o, hi, 'low', fs=SR, output='sos')
    return sosfilt(s, x)
def noise(n): return R.standard_normal(n)
def lfo(n, f, ph=0): return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)
def env(n, a, r):
    e = np.ones(n); A = max(1, int(a * SR)); Rl = max(1, int(r * SR))
    e[:A] = np.linspace(0, 1, A); e[-Rl:] *= np.linspace(1, 0, Rl) ** 2; return e
def norm(x): return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
# --- beds (generated full length once, mono pairs for stereo width) ---
def surf(n):
    sw = np.clip(0.55 + 0.45 * lfo(n, 1 / 7.5) + 0.2 * lfo(n, 1 / 11.3, 1), 0.05, None) ** 1.5
    return [norm(filt(noise(n), 200, 3000)) * sw * .5 + norm(filt(noise(n), hi=400)) * .3 for _ in range(2)]
def wind(n, k=1.0):
    g = 0.6 + 0.4 * lfo(n, 1 / 9.1) * lfo(n, 1 / 3.7, .5)
    return [norm(filt(noise(n), 150, 900 * k)) * g * .45 for _ in range(2)]
def insects(n):
    t = np.arange(n) / SR; tr = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t))) * (0.5 + .5 * lfo(n, .21))
    return [np.sin(2 * np.pi * (4700 + 300 * c) * t) * tr * .06 + norm(filt(noise(n), 5000, 9000)) * .03 for c in range(2)]
def rain(n, heavy=False):
    b = [norm(filt(noise(n), 800, 7000)) * (.45 if heavy else .3) for _ in range(2)]
    for _ in range(int(n / SR * 6)):
        p = R.integers(0, n - 2000); c = R.integers(0, 2)
        b[c][p:p + 1500] += np.sin(2 * np.pi * R.uniform(2500, 4500) * np.arange(1500) / SR) * np.exp(-np.arange(1500) / 150) * .25
    return b
BEDS = {}
def bed(name, n):
    if name not in BEDS:
        BEDS[name] = {'surf': surf, 'wind': wind, 'insects': insects, 'rain': rain,
                      'storm': lambda n: [a + b + c for a, b, c in zip(rain(n, True), wind(n, 2.5), surf(n))]}[name](n)
    return BEDS[name]
def setting_mix(s):
    x = (s['setting'] + ' ' + s['desc'][:80]).lower(); m = {}
    if 'storm' in x and 'after' not in x: return {'storm': 1.0}
    if any(k in x for k in ('surf', 'beach', 'tide', 'reef', 'sea', 'point', 'ocean', 'shallows', 'island')): m['surf'] = .8
    if 'jungle' in x or 'spring' in x or 'clearing' in x: m['surf'] = .25
    if 'wind' in x or 'island wide' in x: m['wind'] = .5
    if 'night' in x: m['insects'] = .6; m['surf'] = .5
    if 'rain' in x and 'after' not in x: m['rain'] = 1.0
    if 'hut' in x and 'inside' in x: m = {'surf': .2}
    if not m: m = {'surf': .5}
    m.setdefault('wind', .2); return m
amb = np.zeros((N, 2)); XF = .4
for s in T['shots']:
    a = max(0, int((s['start'] - XF / 2) * SR)); b = min(N, int((s['end'] + XF / 2) * SR)); n = b - a
    e = env(n, XF if a else 0, XF if b < N else 0) ** .5
    for k, g in setting_mix(s).items():
        L, Rr = bed(k, N)
        amb[a:b, 0] += L[a:b] * g * e; amb[a:b, 1] += Rr[a:b] * g * e
amb[:int(.25 * SR)] *= np.linspace(.5, 1, int(.25 * SR))[:, None]
# gulls: sparse chirps on day beach shots
out = np.zeros((N, 2))
def put(sig, t, pan=0.5, g=1.0):
    i = int(t * SR); sig = sig[:max(0, N - i)]
    if i < 0 or not len(sig): return
    out[i:i + len(sig), 0] += sig * g * np.sqrt(1 - pan); out[i:i + len(sig), 1] += sig * g * np.sqrt(pan)
def tone(f0, f1, d, a=.01, r=.2, shape='sin'):
    n = int(d * SR); f = np.geomspace(f0, f1, n); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env(n, a, r)
def gull():
    return np.concatenate([tone(2200, 1400, .18, .02, .1) * (1 + .3 * np.sin(np.arange(int(.18 * SR)) / 40)) for _ in range(2)]) * .5
for s in T['shots']:
    x = s['setting'].lower()
    if ('beach' in x or 'island' in x or 'surf' in x) and 'night' not in x and 'storm' not in x:
        t = s['start'] + 1.3
        while t < s['end'] - 1: put(gull(), t, R.uniform(.2, .8), .05); t += R.uniform(3.5, 7)
amb += out; out[:] = 0
# thunder in storm shots
for s in T['shots']:
    if 'storm' in s['setting'].lower():
        t = s['start'] + .4
        while t < s['end']:
            n = int(3 * SR); th = filt(noise(n), hi=120, o=4) * env(n, .05, 2.5) * (1 + .5 * lfo(n, 3)); put(norm(th) * .5, t, .5)
            t += R.uniform(2.6, 4)
amb += out; out[:] = 0
# --- spot SFX ---
SH = {s['id']: s for s in T['shots']}
def word(sid, w, which=0):
    hits = [x for l in SH[sid]['lines'] for x in l['words'] if w.lower() in x['w'].lower()]
    return hits[which]['start'] if hits else SH[sid]['start'] + 1
def chime(): return sum(tone(f, f, 1.6, .01, 1.4) * g for f, g in ((880, .5), (1318.5, .35), (1760, .2)))
put(chime() * .25, word('s01a', 'online') + .5); put(chime() * .25, word('s09b', 'restored') + .3)
for s in T['shots']:
    for l in s['lines']:
        if l['speaker'] == 'directive': put(tone(2400, 2600, .06, .003, .04) * .08, l['start'] - .06)
def sweep(): return filt(noise(int(1.6 * SR)), 1500, 6000) * env(int(1.6 * SR), .5, .9) * .25 + tone(400, 1600, 1.6, .3, .9) * .1
put(sweep(), word('s01b', 'Scanning')); put(sweep() * .8, word('s09c', 'Scanning'))
def click(): return filt(noise(400), 2000, 8000) * np.exp(-np.arange(400) / 40)
for sid in ('s03a', 's03c', 's03d'):
    t = SH[sid]['start'] + .3
    while t < SH[sid]['end'] - .3: put(click() * .25, t, R.uniform(.3, .7)); t += R.uniform(.08, .5 if sid != 's03d' else 1.5)
def pour(d):
    n = int(d * SR); x = filt(noise(n), 400, 4000) * (.7 + .3 * lfo(n, 7)) * env(n, .3, .6)
    return norm(x) * .05
put(pour(3.5), SH['s04b']['start'] + .4); put(pour(4), SH['s08b']['start'] + .3)
def scratch(): n = int(.25 * SR); return filt(noise(n), 2500, 7000) * env(n, .02, .1) * .25
t = SH['s04c']['start'] + .3
while t < SH['s04c']['end'] - .3: put(scratch(), t, .45); t += .32
def tap(): n = int(.12 * SR); return filt(noise(n), 300, 1500) * np.exp(-np.arange(n) / 600) * .5 + tone(180, 120, .12, .001, .08) * .3
t = SH['s04e']['start'] + .2
while t < SH['s04e']['end'] - .2: put(tap(), t, R.uniform(.3, .7), .5); t += R.uniform(.18, .35)
b5 = SH['s05b']['start'] + .6; put(click() * .6, b5); put(tone(110, 110, 3.5, .5, 1.5) * .05 + tone(220, 220, 3.5, .5, 1.5) * .03, b5 + .05)
def whoosh(): n = int(1.2 * SR); return filt(noise(n), 200, 2500) * env(n, .5, .6) * .3
c5 = SH['s05c']['start'] + 1.0; put(whoosh(), c5); put(tone(98, 98, SH['s05c']['end'] - c5, .6, 1) * .05, c5 + .5)
put(tone(660, 110, 3.0, .05, 1.5) * .12 + tone(990, 165, 3.0, .05, 1.5) * .05, word('s06e', 'on', -1) + .8)
def creak(): n = int(.7 * SR); f = 90 + 40 * np.sin(np.arange(n) / SR * 3); return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * env(n, .2, .3) * .03
for t in np.arange(SH['s07a']['start'] + .5, SH['s07a']['end'], 2.3): put(filt(creak(), 200, 1200), t, R.uniform(.3, .7))
def step(): n = int(.1 * SR); return filt(noise(n), 100, 900) * np.exp(-np.arange(n) / 500) * .35
for t in np.arange(word('s08a', 'One'), SH['s08a']['end'] - .1, .3): put(step(), t, .5)
sf.write('build/amb.wav', amb.astype(np.float32), SR, subtype='FLOAT')
sf.write('build/sfx.wav', out.astype(np.float32), SR, subtype='FLOAT')
print('amb peak', np.abs(amb).max(), 'sfx peak', np.abs(out).max())
