"""Intelligibility check: transcribe the finished mix and compare it with the script.

Usage: python check_mix.py BUILD_DIR MIX_WAV
Prints a per-scene word-match ratio between what speech recognition hears in
the full mix (music and effects included) and the scripted lines.
"""
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from scipy.signal import resample_poly


def norm(s):
    s = s.lower().replace("’", "'").replace("—", " ").replace("-", " ")
    return re.sub(r"[^a-z' ]+", " ", s).split()


def main():
    tl = json.loads((Path(sys.argv[1]) / "timeline.json").read_text())
    a, sr = sf.read(sys.argv[2], dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    a16 = resample_poly(a, 1, sr // 16000).astype(np.float32) if sr % 16000 == 0 else resample_poly(a, 16000, sr).astype(np.float32)
    model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root="/opt/models/whisper")
    worst = 1.0
    for s in tl["scenes"]:
        seg = a16[int(s["start"] * 16000): int(s["end"] * 16000)]
        segs, _ = model.transcribe(seg, beam_size=5, vad_filter=False)
        heard = norm(" ".join(x.text for x in segs))
        ref = norm(" ".join(l["text"] for l in tl["lines"] if l["scene"] == s["id"]))
        r = SequenceMatcher(None, ref, heard).ratio() if ref else 1.0
        worst = min(worst, r)
        print(f"{s['id']:9s} word match {r:.2f}  ({len(ref)} scripted words)")
    print(f"lowest scene: {worst:.2f}")


if __name__ == "__main__":
    main()
