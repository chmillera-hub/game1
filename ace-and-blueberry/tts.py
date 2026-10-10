import os, sys, json
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from fractions import Fraction
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from story import VOICES, LINES

OUT = os.path.join(HERE, "voices")
os.makedirs(OUT, exist_ok=True)
SR = 48000

k = Kokoro(os.path.join(HERE, "models", "kokoro-v1.0.onnx"), os.path.join(HERE, "models/voices-v1.0.bin"))

# espeak diphthongs/affricates -> the single-symbol forms Kokoro was trained on
MAP = [("aɪ", "I"), ("aʊ", "W"), ("eɪ", "A"), ("ɔɪ", "Y"), ("oʊ", "O"), ("dʒ", "ʤ"), ("tʃ", "ʧ")]
only = set(sys.argv[1:])
for lid, (who, text) in LINES.items():
    if only and lid not in only:
        continue
    v = VOICES[who]
    ph = k.tokenizer.phonemize(text, "en-us")
    for a, b in MAP:
        ph = ph.replace(a, b)
    samples, sr = k.create(ph, voice=v["voice"], speed=v["speed"], is_phonemes=True)
    x = np.asarray(samples, dtype=np.float64)
    # pitch shift by resampling: treat audio as if recorded at sr*pitch, convert to SR
    src_rate = sr * v["pitch"]
    frac = Fraction(SR / src_rate).limit_denominator(400)
    y = resample_poly(x, frac.numerator, frac.denominator)
    # trim leading/trailing silence
    a = np.abs(y)
    thr = 0.01 * a.max()
    idx = np.where(a > thr)[0]
    pad = int(0.04 * SR)
    y = y[max(0, idx[0] - pad): min(len(y), idx[-1] + pad)]
    # fade edges
    f = int(0.01 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    y = y / (np.abs(y).max() + 1e-9) * 0.89
    sf.write(os.path.join(OUT, lid + ".wav"), y.astype(np.float32), SR)
    print(f"{lid:12s} {who:5s} {len(y)/SR:5.2f}s  {text}")
