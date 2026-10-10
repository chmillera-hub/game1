import json, os, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from lines import LINES, VOICES, PHONEME_FIX, PREFIX_HMM
from hmm import airy_hmm
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
out = {}
if os.path.exists("audio/voice/durations.json"):
    out = json.load(open("audio/voice/durations.json"))
for lid, (spk, text, cap, speed) in LINES.items():
    path = f"audio/voice/{lid}.wav"
    voice, lang = VOICES[spk]
    ph = k.tokenizer.phonemize(text, lang)
    for a_, b_ in PHONEME_FIX.get(lang, []):
        ph = re.sub(a_, b_, ph)
    key = f"{spk}|{ph}|{speed}|v4{'hmm' if lid in PREFIX_HMM else ''}"
    if lid in out and out[lid].get("key") == key and os.path.exists(path):
        continue
    s, sr = k.create(ph, voice=voice, speed=speed, lang=lang, is_phonemes=True)
    s = np.asarray(s, dtype=np.float32)
    # trim leading/trailing silence
    thr = 0.01 * np.abs(s).max()
    idx = np.where(np.abs(s) > thr)[0]
    a, b = max(0, idx[0] - int(0.03*sr)), min(len(s), idx[-1] + int(0.08*sr))
    s = s[a:b]
    if lid in PREFIX_HMM:
        h = airy_hmm(sr) * (np.abs(s).max() * 0.8)
        s = np.concatenate([h, np.zeros(int(0.32 * sr), np.float32), s]).astype(np.float32)
    sf.write(path, s, sr)
    out[lid] = {"key": key, "dur": len(s)/sr, "sr": sr}
    print(lid, round(len(s)/sr, 2), flush=True)
json.dump(out, open("audio/voice/durations.json", "w"), indent=1)
print("TOTAL voiced", sum(v["dur"] for v in out.values()))
