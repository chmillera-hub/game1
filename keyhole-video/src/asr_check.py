import json, re
from faster_whisper import WhisperModel
m = WhisperModel("small.en", device="cpu", compute_type="int8")
import soundfile as sf, numpy as np
from scipy import signal
a, sr = sf.read("build/dialogue.wav"); a = a.mean(1) if a.ndim > 1 else a
a = signal.resample_poly(a, 1, 3).astype(np.float32)
segs, info = m.transcribe(a, word_timestamps=False, vad_filter=False, beam_size=5)
segs = list(segs)
tl = json.load(open("build/timeline.json"))
for l in tl["lines"]:
    txt = " ".join(s.text.strip() for s in segs if s.end > l["t0"] + 0.1 and s.start < l["t1"] - 0.1)
    ref = re.sub(r"\[p[\d.]+\]", " ", re.sub(r"\[B:\w+\]", "<BLEEP>", l["text"]))
    print(f"{l['t0']:6.1f} {l['who']:7s} REF: {ref}\n{'':15s}ASR: {txt}")
