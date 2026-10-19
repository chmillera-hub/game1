"""Score Chatterbox takes: speaker similarity to each character's reference.

Runs in the Chatterbox venv (needs its voice encoder).
Usage: python score_takes.py script.json REF_DIR TAKE_DIR OUT_JSON
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
from chatterbox.models.voice_encoder import VoiceEncoder


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    refs, takes = Path(sys.argv[2]), Path(sys.argv[3])
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file
    ve = VoiceEncoder()
    ve.load_state_dict(load_file(hf_hub_download("ResembleAI/chatterbox", "ve.safetensors")))
    ve.eval()

    def embed(path):
        wav, _ = librosa.load(str(path), sr=16000)
        e = ve.embeds_from_wavs([wav], sample_rate=16000)[0]
        return e / (np.linalg.norm(e) + 1e-9)

    ref_emb = {who: embed(refs / f"{who}.wav") for who in script["cast"]}
    out = {}
    for sc in script["scenes"]:
        for b in sc["beats"]:
            if "id" not in b:
                continue
            for p in sorted(takes.glob(f"{b['id']}_t*.wav")):
                sim = float(np.dot(embed(p), ref_emb[b["who"]]))
                out[p.name] = {"sim": round(sim, 4), "who": b["who"]}
                print(f"{p.name:12s} {b['who']:8s} sim={sim:.3f}", flush=True)
    Path(sys.argv[4]).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
