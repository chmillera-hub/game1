"""Generate the narration with Kokoro-82M, fitting every line to its caption window.

usage: python gen_kokoro.py <voice> <outdir>
writes <outdir>/line_XX.wav (24 kHz mono) and <outdir>/takes.json
"""
import json, re, sys, os, warnings
import numpy as np, soundfile as sf
warnings.filterwarnings('ignore')
from kokoro import KPipeline

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
SR = 24000
LEAD, GAP = 0.18, 0.7          # speech starts LEAD after the caption; leaves GAP before the next line
lines = json.load(open(f'{HERE}/lines.json'))
script = json.load(open(f'{HERE}/script.json'))
assert len(lines) == len(script)

pipe = KPipeline(lang_code=VOICE[0], repo_id='hexgrad/Kokoro-82M')
if '+' in VOICE[2:]:
    pass

# per-mood delivery: base speed (slower = older, more deliberate) and pause scale
MOOD = {
    'reflective': (0.86, 1.0), 'weary': (0.82, 1.1), 'hushed': (0.82, 1.0), 'plain': (0.86, 1.0), 'wry': (0.88, 1.0),
    'warm': (0.86, 1.0), 'wonder': (0.82, 1.2), 'tender': (0.84, 1.1), 'proud': (0.88, 1.0), 'moved': (0.84, 1.0),
    'wistful': (0.84, 1.1), 'peaceful': (0.84, 1.0), 'firm': (0.9, 1.0), 'urgent': (0.94, 0.9), 'defiant': (0.92, 1.0),
    'playful': (0.9, 1.0), 'steady': (0.88, 1.0), 'resolute': (0.9, 1.0), 'loving': (0.86, 1.1), 'quiet': (0.8, 1.0),
    'vow': (0.88, 1.0), 'gentle': (0.88, 1.0), 'certain': (0.86, 1.1), 'hopeful': (0.88, 1.0), 'intimate': (0.86, 1.1),
    'revelation': (0.86, 1.1), 'earnest': (0.9, 1.0), 'vulnerable': (0.88, 1.0), 'final': (0.76, 1.3), 'rising': (0.84, 1.1),
    'last': (0.74, 1.0),
}

def trim(a, thr=0.012, pad=0.03):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    s = max(0, idx[0] - int(pad * SR)); e = min(len(a), idx[-1] + int(pad * 1.5 * SR))
    return a[s:e]

def phrases(say):
    parts = re.split(r'\s*\{([0-9.]+)\}\s*', say)
    out = []
    for i in range(0, len(parts), 2):
        pause = float(parts[i + 1]) if i + 1 < len(parts) else 0.0
        out.append((parts[i].strip(), pause))
    return out

cache = {}
def synth(text, speed):
    k = (text, round(speed, 3))
    if k not in cache:
        cache[k] = trim(np.concatenate([a.numpy() for _, _, a in pipe(text, voice=VOICE, speed=speed, split_pattern=None)]))
    return cache[k]

def render(say, speed, pscale):
    segs = []
    for text, pause in phrases(say):
        segs.append(synth(text, speed))
        if pause:
            segs.append(np.zeros(int(pause * pscale * SR), np.float32))
    return np.concatenate(segs)

takes = []
for i, (L, S) in enumerate(zip(lines, script)):
    base, pscale = MOOD[S['mood']]
    budget = L['win'] - LEAD - GAP
    if i == len(lines) - 1:
        budget = 4.5
    speed = base
    a = render(S['say'], speed, pscale)
    while len(a) / SR > budget and speed < 1.06:
        speed = round(speed + 0.03, 3)
        a = render(S['say'], speed, pscale)
    while len(a) / SR > budget and pscale > 0.4:
        pscale = round(pscale - 0.15, 3)
        a = render(S['say'], speed, pscale)
    dur = len(a) / SR
    sf.write(f'{OUT}/line_{i:02d}.wav', a, SR)
    takes.append({'i': i, 'speed': speed, 'pscale': pscale, 'dur': round(dur, 3), 'budget': round(budget, 2), 'fits': dur <= budget})
    print(f'{i:2d} {S["mood"]:<10} speed {speed:.2f} pauses x{pscale:.2f} dur {dur:5.2f} / {budget:5.2f} {"" if dur <= budget else "OVER"}', flush=True)
json.dump(takes, open(f'{OUT}/takes.json', 'w'), indent=1)
