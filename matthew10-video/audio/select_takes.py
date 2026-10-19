"""Pick the best Chatterbox take per line (fallback: Kokoro).

Scores each take on intelligibility (ASR vs script), voice consistency
(speaker similarity from score_takes.py), duration sanity relative to the
Kokoro read, and unexpected long silences.

Usage: python select_takes.py script.json TAKE_DIR SIM_JSON KOKORO_DIR OUT_JSON
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

sys.path.insert(0, str(Path(__file__).parent))
from prepare import trim, SR  # noqa: E402


def norm(s):
    s = s.lower().replace("’", "'").replace("—", " ").replace("-", " ")
    return re.sub(r"[^a-z' ]+", " ", s).split()


def longest_gap(a, sr):
    win = int(0.02 * sr)
    env = np.sqrt(np.convolve(a * a, np.ones(win) / win, mode="same") + 1e-12)
    quiet = 20 * np.log10(env) < -45
    best = run = 0
    for q in quiet:
        run = run + 1 if q else 0
        best = max(best, run)
    return best / sr


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    takes, sims = Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text())
    kdir, out = Path(sys.argv[4]), Path(sys.argv[5])
    model = WhisperModel("small.en", device="cpu", compute_type="int8", download_root="/opt/models/whisper")

    def asr(a):
        a16 = resample_poly(a, 2, 3).astype(np.float32)
        segs, _ = model.transcribe(a16, word_timestamps=True, beam_size=5)
        return [(float(w.start), float(w.end), w.word.strip()) for s in segs for w in s.words]

    sel, report = {}, []
    for sc in script["scenes"]:
        for b in sc["beats"]:
            if "id" not in b:
                continue
            lid = b["id"]
            ref = norm(b.get("tts", b["text"]))
            ka, _ = sf.read(kdir / f"{lid}.wav", dtype="float32")
            kdur = len(trim(ka)) / SR
            allow_gap = 1.0 if "..." in b["text"] else 0.7
            cands = []
            for p in sorted(takes.glob(f"{lid}_t*.wav")):
                a, sr = sf.read(p, dtype="float32")
                a = trim(a)
                dur = len(a) / SR
                words = asr(a)
                match = SequenceMatcher(None, ref, norm(" ".join(w[2] for w in words))).ratio()
                sim = sims.get(p.name, {}).get("sim", 0.0)
                r = dur / max(kdur, 0.3)
                gap = longest_gap(a, SR)
                score = 3.0 * match + 1.0 * sim
                if r > 1.7 or r < 0.55:
                    score -= 1.0
                if gap > allow_gap:
                    score -= 0.8 * (gap - allow_gap)
                cands.append({"path": str(p), "match": match, "sim": sim, "dur": dur, "ratio": r, "gap": gap,
                              "score": score, "words": words})
            cands.sort(key=lambda c: -c["score"])
            best = cands[0] if cands and cands[0]["match"] >= 0.88 else None
            if best is None:
                kwords = asr(trim(ka))
                sel[lid] = {"path": str(kdir / f"{lid}.wav"), "words": kwords, "engine": "kokoro"}
                report.append((lid, "KOKORO", cands[0]["match"] if cands else 0, 0, kdur))
            else:
                sel[lid] = {"path": best["path"], "words": best["words"], "engine": "chatterbox"}
                report.append((lid, Path(best["path"]).name, best["match"], best["sim"], best["dur"]))
            for c in cands:
                print(f"  {Path(c['path']).name:12s} match={c['match']:.2f} sim={c['sim']:.3f} dur={c['dur']:.2f} "
                      f"ratio={c['ratio']:.2f} gap={c['gap']:.2f} score={c['score']:.2f}", flush=True)
            print(f"{lid}: -> {sel[lid]['engine']} {Path(sel[lid]['path']).name}", flush=True)
    out.write_text(json.dumps(sel, indent=1))
    n_k = sum(1 for v in sel.values() if v["engine"] == "kokoro")
    print(f"selected {len(sel)} lines; {n_k} fell back to Kokoro")


if __name__ == "__main__":
    main()
