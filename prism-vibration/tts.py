"""Synthesize narration with Piper; writes per-scene wavs + timings.json."""
import json, subprocess, sys, wave, os
import numpy as np
from narration import SCENES

OUT = sys.argv[1]
MODEL = sys.argv[2]
LEAD, GAP, TAIL = 0.6, 0.45, 1.0
os.makedirs(OUT, exist_ok=True)
timings = {}
for name, sents in SCENES:
    chunks, cues, t = [], [], LEAD
    rate = None
    for i, s in enumerate(sents):
        fn = f"{OUT}/{name}_{i}.wav"
        if not os.path.exists(fn):
            subprocess.run([sys.executable, "-m", "piper", "-m", MODEL, "-f", fn, "--length-scale", "1.05"],
                           input=s.encode(), check=True, capture_output=True)
        with wave.open(fn) as w:
            rate = w.getframerate()
            a = np.frombuffer(w.readframes(w.getnframes()), np.int16)
        cues.append([t, t + len(a) / rate, s])
        chunks.append(a)
        t += len(a) / rate + GAP
    dur = t - GAP + TAIL
    audio = np.zeros(int(dur * rate), np.int16)
    for (t0, _, _), a in zip(cues, chunks):
        i0 = int(t0 * rate)
        audio[i0:i0 + len(a)] = a
    with wave.open(f"{OUT}/{name}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(audio.tobytes())
    timings[name] = {"dur": dur, "cues": cues}
    print(f"{name:10s} {dur:6.1f}s")
json.dump(timings, open(f"{OUT}/timings.json", "w"), indent=1)
print("total", sum(v["dur"] for v in timings.values()))
