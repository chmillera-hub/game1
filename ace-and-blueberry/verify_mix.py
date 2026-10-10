import sys, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
a, sr = sf.read(sys.argv[1]); a = a.mean(axis=1) if a.ndim > 1 else a
a = resample_poly(a, 1, 3).astype(np.float32)
m = WhisperModel('small.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe(a, beam_size=3, language='en', vad_filter=False)
for s in segs: print(f"{s.start:7.2f} {s.text.strip()}")
