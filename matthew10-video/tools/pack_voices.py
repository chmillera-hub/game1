"""Store the chosen voice takes in the repo so the film can be rebuilt without re-running TTS.

Usage: python pack_voices.py SELECTION_JSON OUT_DIR
Writes OUT_DIR/<id>.opus and OUT_DIR/selection.json (paths relative to OUT_DIR).
"""
import json
import sys
from pathlib import Path

import soundfile as sf


def main():
    sel = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    packed = {}
    for lid, entry in sel.items():
        a, sr = sf.read(entry["path"], dtype="float32")
        if a.ndim > 1:
            a = a.mean(1)
        sf.write(out / f"{lid}.opus", a, sr, format="OGG", subtype="OPUS")
        packed[lid] = {"path": f"{lid}.opus", "words": entry.get("words", []), "engine": entry.get("engine")}
    (out / "selection.json").write_text(json.dumps(packed, indent=1))
    print(f"packed {len(packed)} lines into {out}")


if __name__ == "__main__":
    main()
