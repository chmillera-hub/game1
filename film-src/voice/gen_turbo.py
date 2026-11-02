"""Record three takes of every narration line with Chatterbox-Turbo.

usage: python gen_turbo.py <ref.wav> <outdir> [line indices...]
writes <outdir>/line_XX_takeK.wav
"""
import json, re, sys, os, warnings, time
import numpy as np, soundfile as sf, torch
warnings.filterwarnings('ignore')
torch.set_num_threads(4)
from chatterbox.tts_turbo import ChatterboxTurboTTS

HERE = os.path.dirname(os.path.abspath(__file__))
REF, OUT = sys.argv[1], sys.argv[2]
only = [int(x) for x in sys.argv[3:]]
TAKES = int(os.environ.get('TAKES', 3))
os.makedirs(OUT, exist_ok=True)
script = json.load(open(f'{HERE}/script.json'))

# a few performed beats (paralinguistic cues the model acts out)
TAGS = {1: ('[sigh] ', ''), 24: ('', ' [chuckle]')}

def spoken(i):
    s = re.sub(r'\s*\{[0-9.]+\}\s*', ' ', script[i]['say']).strip()
    pre, post = TAGS.get(i, ('', ''))
    return pre + s + post

m = ChatterboxTurboTTS.from_pretrained('cpu')
m.prepare_conditionals(REF)
t0 = time.time()
for i in (only or range(len(script))):
    text = spoken(i)
    for k in range(TAKES):
        f = f'{OUT}/line_{i:02d}_take{k}.wav'
        if os.path.exists(f):
            continue
        torch.manual_seed(7919 * i + 104729 * k + 17)
        w = m.generate(text, temperature=0.75 if k == 0 else 0.85)
        sf.write(f, w.squeeze().numpy(), m.sr)
        print(f'{i:2d}.{k} {w.shape[-1] / m.sr:5.2f}s  [{time.time() - t0:6.0f}s]  {text}', flush=True)
