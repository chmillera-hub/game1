import json, os, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
from lines import LINES, VOICES
k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
out = {}
if os.path.exists("audio/voice/durations.json"):
    out = json.load(open("audio/voice/durations.json"))
for lid, (spk, text, cap, speed) in LINES.items():
    path = f"audio/voice/{lid}.wav"
    key = f"{spk}|{text}|{speed}"
    if lid in out and out[lid].get("key") == key and os.path.exists(path):
        continue
    voice, lang = VOICES[spk]
    s, sr = k.create(text, voice=voice, speed=speed, lang=lang)
    s = np.asarray(s, dtype=np.float32)
    # trim leading/trailing silence
    thr = 0.01 * np.abs(s).max()
    idx = np.where(np.abs(s) > thr)[0]
    a, b = max(0, idx[0] - int(0.03*sr)), min(len(s), idx[-1] + int(0.08*sr))
    s = s[a:b]
    sf.write(path, s, sr)
    out[lid] = {"key": key, "dur": len(s)/sr, "sr": sr}
    print(lid, round(len(s)/sr, 2), flush=True)
json.dump(out, open("audio/voice/durations.json", "w"), indent=1)
print("TOTAL voiced", sum(v["dur"] for v in out.values()))
