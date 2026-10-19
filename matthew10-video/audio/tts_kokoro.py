"""Render every scripted line with Kokoro TTS.

Usage: python tts_kokoro.py script.json OUT_DIR [line_id ...]
Writes OUT_DIR/<id>.wav (24 kHz mono, silence-trimmed).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL = "/opt/models/kokoro/kokoro-v1.0.onnx"
VOICES = "/opt/models/kokoro/voices-v1.0.bin"
SR = 24000


def trim(a, thresh=0.006, pad=0.04):
    env = np.convolve(np.abs(a), np.ones(240) / 240, mode="same")
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(a), idx[-1] + int(pad * SR))
    return a[s:e]


def fade(a, fin=0.01, fout=0.03):
    a = a.copy()
    n1, n2 = int(fin * SR), int(fout * SR)
    a[:n1] *= np.linspace(0, 1, n1)
    a[-n2:] *= np.linspace(1, 0, n2)
    return a


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[3:])
    k = Kokoro(MODEL, VOICES)
    cast = script["cast"]
    for scene in script["scenes"]:
        for b in scene["beats"]:
            if "id" not in b or (only and b["id"] not in only):
                continue
            c = cast[b["who"]]
            text = b.get("tts", b["text"])
            speed = b.get("speed", c["speed"])
            voice = b.get("voice", c["voice"])
            samples, sr = k.create(text, voice=voice, speed=speed, lang=c["lang"])
            assert sr == SR
            a = trim(samples.astype(np.float32))
            if b.get("cut"):
                a = a[: len(a) - int(b["cut"] * SR)]
            a = fade(a)
            sf.write(out / f"{b['id']}.wav", a, SR)
            print(f"{b['id']:4s} {b['who']:8s} {len(a)/SR:5.2f}s  {text[:60]}")


if __name__ == "__main__":
    main()
