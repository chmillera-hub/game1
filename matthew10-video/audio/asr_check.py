"""Transcribe rendered lines, compare against the script, and save word timings.

Usage: python asr_check.py script.json WAV_DIR OUT_JSON
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
    s = s.lower().replace("’", "'").replace("—", " ")
    return re.sub(r"[^a-z' ]+", " ", s).split()


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    wavs = Path(sys.argv[2])
    model = WhisperModel("small.en", device="cpu", compute_type="int8",
                         download_root="/opt/models/whisper")
    report = {}
    worst = []
    for scene in script["scenes"]:
        for b in scene["beats"]:
            if "id" not in b:
                continue
            a, sr = sf.read(wavs / f"{b['id']}.wav", dtype="float32")
            a16 = resample_poly(a, 2, 3).astype(np.float32)
            segs, _ = model.transcribe(a16, word_timestamps=True, beam_size=5)
            words = [(float(w.start), float(w.end), w.word.strip())
                     for s in segs for w in s.words]
            heard = " ".join(w[2] for w in words)
            ref = norm(b.get("tts", b["text"]))
            hyp = norm(heard)
            ratio = SequenceMatcher(None, ref, hyp).ratio()
            report[b["id"]] = {"duration": len(a) / sr, "words": words,
                               "heard": heard, "match": ratio}
            worst.append((ratio, b["id"], heard))
            flag = "" if ratio > 0.9 else "  <-- CHECK"
            print(f"{b['id']:4s} {ratio:.2f} {len(a)/sr:5.2f}s | {heard}{flag}")
    Path(sys.argv[3]).write_text(json.dumps(report, indent=1))
    worst.sort()
    print("lowest:", worst[:5])


if __name__ == "__main__":
    main()
