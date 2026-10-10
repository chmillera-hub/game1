"""Spectrogram + loudness strip of an audio file, annotated with the timeline.

    python3 tools/spectro.py build/mix.wav build/tests/mix_spec.png [--start S --end E]
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TIMELINE  # noqa: E402


def main(src, out, start=None, end=None, width=2400):
    x, sr = sf.read(src, always_2d=True)
    x = x.mean(axis=1)
    s0 = int((start or 0) * sr)
    s1 = int(end * sr) if end else len(x)
    x = x[s0:s1]
    t0 = s0 / sr
    f, t, S = signal.spectrogram(x, sr, nperseg=2048, noverlap=1024)
    S = 10 * np.log10(S + 1e-12)
    fmax = 12000
    keep = f <= fmax
    S = S[keep]
    # log-frequency rows
    rows = 300
    lf = np.logspace(np.log10(40), np.log10(fmax), rows)
    idx = np.clip(np.searchsorted(f[keep], lf), 0, S.shape[0] - 1)
    S = S[idx][::-1]
    S = np.clip((S + 110) / 90, 0, 1)
    cols = np.clip((np.arange(width) / width * S.shape[1]).astype(int), 0, S.shape[1] - 1)
    S = S[:, cols]
    rgb = np.stack([S ** 0.7 * 255, S ** 1.5 * 200, (1 - S) * S * 4 * 255], axis=-1).clip(0, 255).astype(np.uint8)
    spec = Image.fromarray(rgb)
    # loudness strip (short-term RMS dB)
    hop = max(1, len(x) // width)
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(width)])
    dbv = 20 * np.log10(rms + 1e-9)
    strip = Image.new("RGB", (width, 120), (15, 15, 20))
    d = ImageDraw.Draw(strip)
    for i, v in enumerate(dbv):
        h = int(np.clip((v + 60) / 60, 0, 1) * 110)
        d.line([(i, 119), (i, 119 - h)], fill=(90, 200, 160))
    for lvl in (-12, -24, -36, -48):
        y = 119 - int((lvl + 60) / 60 * 110)
        d.line([(0, y), (width, y)], fill=(60, 60, 70))
        d.text((2, y - 10), f"{lvl}dB", fill=(150, 150, 150))
    img = Image.new("RGB", (width, rows + 120 + 70), (0, 0, 0))
    img.paste(spec, (0, 0))
    img.paste(strip, (0, rows))
    d = ImageDraw.Draw(img)
    dur = len(x) / sr
    tl = json.loads(Path(TIMELINE).read_text())

    def X(tt):
        return int((tt - t0) / dur * width)
    for s in tl["scenes"]:
        if t0 <= s["start"] <= t0 + dur:
            d.line([(X(s["start"]), 0), (X(s["start"]), rows + 120)], fill=(255, 255, 255))
            d.text((X(s["start"]) + 3, 3), s["id"], fill=(255, 255, 255))
    y = rows + 122
    for k, ln in enumerate(tl["lines"]):
        if t0 <= ln["start"] <= t0 + dur:
            c = (255, 170, 80) if ln["char"] == "rae" else (90, 230, 220)
            d.rectangle([X(ln["start"]), y + (k % 3) * 20, X(ln["end"]), y + (k % 3) * 20 + 14], outline=c)
            d.text((X(ln["start"]) + 2, y + (k % 3) * 20 + 1), ln["id"], fill=c)
    for sec in range(int(t0), int(t0 + dur) + 1, 10 if dur > 60 else 1):
        d.text((X(sec), rows + 105), str(sec), fill=(200, 200, 0))
    img.save(out)
    print(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    st = en = None
    if "--start" in a:
        i = a.index("--start"); st = float(a[i + 1]); del a[i:i + 2]
    if "--end" in a:
        i = a.index("--end"); en = float(a[i + 1]); del a[i:i + 2]
    main(a[0], a[1], st, en)
