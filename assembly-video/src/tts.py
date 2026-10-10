import json, os, re, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from kokoro_onnx import Kokoro
from lines import LINES, VOICES, PHONEME_FIX

k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
out = {}
if os.path.exists("audio/voice/durations.json"):
    out = json.load(open("audio/voice/durations.json"))
for lid, (spk, text, cap, speed) in LINES.items():
    path = f"audio/voice/{lid}.wav"
    voice, lang, pitch = VOICES[spk]
    ph = k.tokenizer.phonemize(text, lang)
    for a_, b_ in PHONEME_FIX.get(lang, []):
        ph = re.sub(a_, b_, ph)
    key = f"{spk}|{voice}|{pitch}|{ph}|{speed}"
    if lid in out and out[lid].get("key") == key and os.path.exists(path):
        continue
    # pitch shift by resampling: generate slower, then speed up (raises pitch + formants -> younger voice)
    s, sr = k.create(ph, voice=voice, speed=speed / pitch, lang=lang, is_phonemes=True)
    s = np.asarray(s, dtype=np.float64)
    if abs(pitch - 1.0) > 1e-3:
        up = 100
        down = int(round(100 * pitch))
        s = resample_poly(s, up, down)
    s = s.astype(np.float32)
    thr = 0.01 * np.abs(s).max()
    idx = np.where(np.abs(s) > thr)[0]
    a, b = max(0, idx[0] - int(0.03 * sr)), min(len(s), idx[-1] + int(0.08 * sr))
    s = s[a:b]
    sf.write(path, s, sr)
    out[lid] = {"key": key, "dur": len(s) / sr, "sr": sr}
    print(lid, round(len(s) / sr, 2), flush=True)
json.dump(out, open("audio/voice/durations.json", "w"), indent=1)
print("TOTAL voiced", round(sum(out[l]["dur"] for l in LINES), 1))
