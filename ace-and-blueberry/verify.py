import os, sys
from faster_whisper import WhisperModel
import soundfile as sf, numpy as np
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import LINES
m = WhisperModel('small.en', device='cpu', compute_type='int8')
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voices')
for lid, (who, text) in LINES.items():
    a, sr = sf.read(os.path.join(d, lid + '.wav'))
    a = resample_poly(a, 1, 3).astype(np.float32)
    a = np.concatenate([np.zeros(8000, np.float32), a, np.zeros(8000, np.float32)])
    segs, _ = m.transcribe(a, beam_size=3, language='en')
    got = ' '.join(s.text.strip() for s in segs)
    print(f"{lid:12s} | {text}  ==>  {got}")
