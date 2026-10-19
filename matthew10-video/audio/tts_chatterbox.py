"""Render expressive takes of every line with Chatterbox.

Each character's timbre comes from a Kokoro reference clip (refs/<who>.wav), and
each line carries its own emotion exaggeration (`ex`) and pacing (`cfg`).

Usage: python tts_chatterbox.py script.json REF_DIR OUT_DIR [line_id ...]
Writes OUT_DIR/<id>_t<k>.wav. Existing takes are skipped, so it can resume.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from chatterbox.tts import ChatterboxTTS

torch.set_num_threads(4)

# Narration is long and steady, so two takes are enough; dialogue gets three.
TAKES = {"narrator": 2}
DEFAULT_TAKES = 3


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    refs = Path(sys.argv[2])
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[4:])
    cast = script["cast"]
    model = ChatterboxTTS.from_pretrained(device="cpu")

    lines = [b for sc in script["scenes"] for b in sc["beats"]
             if "id" in b and (not only or b["id"] in only)]
    # Group by speaker so the voice conditioning is prepared once per character.
    lines.sort(key=lambda b: b["who"])
    current = None
    for b in lines:
        who = b["who"]
        c = cast[who]
        ex = b.get("ex", c["ex"])
        cfg = b.get("cfg", c["cfg"])
        text = b.get("tts", b["text"])
        if current != who:
            model.prepare_conditionals(str(refs / f"{who}.wav"), exaggeration=ex)
            current = who
        for k in range(TAKES.get(who, DEFAULT_TAKES)):
            dest = out / f"{b['id']}_t{k}.wav"
            if dest.exists():
                continue
            torch.manual_seed(1000 * k + int(b["id"][1:]) + (500 if b["id"][0] == "N" else 0))
            t = time.time()
            wav = model.generate(text, exaggeration=ex, cfg_weight=cfg, temperature=0.75)
            a = wav.squeeze(0).numpy().astype(np.float32)
            sf.write(dest, a, model.sr)
            print(f"{b['id']:4s} t{k} {who:8s} ex={ex:.2f} cfg={cfg:.2f} "
                  f"{len(a)/model.sr:5.2f}s in {time.time()-t:5.1f}s", flush=True)


if __name__ == "__main__":
    main()
