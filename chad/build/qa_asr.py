#!/usr/bin/env python3
"""Optional QA: transcribe every generated voice line with faster-whisper and flag
lines whose transcript drifts from the script (mispronunciations, mangled FX).

    pip install faster-whisper && python build/qa_asr.py
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build import ROOT, voice_line  # noqa: E402
from dsp import SR  # noqa: E402


def words(s):
    return re.sub(r"[^a-z' ]+", " ", s.lower().replace("-", " ")).split()


def main():
    from faster_whisper import WhisperModel
    import numpy as np
    from scipy.signal import resample_poly

    model = WhisperModel(sys.argv[1] if len(sys.argv) > 1 else "small.en", device="cpu", compute_type="int8")
    script = json.loads((ROOT / "script.json").read_text())
    worst = []
    for sc in script["scenes"]:
        for ln in sc["lines"]:
            y = voice_line(script["speakers"][ln["who"]], ln["text"], script.get("lexicon"))
            y16 = resample_poly(y, 1, 3).astype(np.float32)  # 48k -> 16k
            segs, _ = model.transcribe(y16, language="en", beam_size=5)
            heard = " ".join(s.text for s in segs).strip()
            ratio = difflib.SequenceMatcher(None, words(ln["text"]), words(heard)).ratio()
            worst.append((ratio, ln["id"], ln["text"], heard))
            flag = "  " if ratio > 0.8 else "!!"
            print(f"{flag} {ratio:.2f} {ln['id']:14s} {ln['text']!r}\n          heard: {heard!r}", flush=True)
    worst.sort()
    print("\nlowest matches:")
    for r, i, t, h in worst[:8]:
        print(f"  {r:.2f} {i}: {t!r} -> {h!r}")


if __name__ == "__main__":
    main()
