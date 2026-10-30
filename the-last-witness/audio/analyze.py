#!/usr/bin/env python3
"""Visual + numeric checks of the rendered soundtrack (you cannot listen, so look).

For each window: spectrogram of mix.wav (0-8 kHz) on top, and short-term levels of the
voice / music / sfx stems (K-weighted, 400 ms, LUFS-like) below, with speech beats,
mood changes and word cues marked.  PNGs go to build/audio/plots/.

Run:  python3 -I audio/analyze.py            (default windows)
      python3 -I audio/analyze.py 890 950    (custom window, seconds)
"""
import json
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import mix as M  # noqa: E402

OUT = os.path.join(ROOT, "build", "audio")
PLOTS = os.path.join(OUT, "plots")
SR = 48000


def rd(name):
    with wave.open(os.path.join(OUT, name)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768


def find(tl, text):
    for b in tl["beats"]:
        if b.get("text", "").startswith(text):
            return b
    raise KeyError(text)


def default_windows(tl):
    acts = tl["acts"]
    death = find(tl, "Until your breath slows.")["start"]
    bang = find(tl, "And pressed the button.")["start"]
    begin = find(tl, '"Let\'s begin."')["start"]
    bored = find(tl, '"I make sure you never rot')["start"]
    return [
        ("act_card_II", acts[1]["start"] - 20, acts[1]["start"] + 25),
        ("death", death - 25, death + 25),
        ("big_bang", bang - 15, bang + 45),
        ("lets_begin", begin - 20, begin + 15),
        ("boredom_loneliness", bored - 10, bored + 50),
        ("ending", tl["duration"] - 45, tl["duration"]),
        ("opening", 0, 45),
    ]


def plot(name, t0, t1, tl, mix, voice, music, sfx):
    W, H1, H2 = 1600, 360, 300
    img = Image.new("RGB", (W, H1 + H2 + 40), (14, 14, 18))
    d = ImageDraw.Draw(img)
    i0, i1 = int(t0 * SR), int(t1 * SR)
    x = mix[i0:i1].astype(np.float64)
    # spectrogram
    nfft, hop = 2048, max(1, (i1 - i0) // W)
    win = np.hanning(nfft)
    cols = []
    for k in range(W):
        a = k * hop
        seg = x[a:a + nfft]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        cols.append(np.abs(np.fft.rfft(seg * win)))
    S = 20 * np.log10(np.array(cols).T + 1e-9)
    fmax = 8000
    nb = int(fmax / (SR / nfft))
    S = S[:nb][::-1]
    S = np.clip((S - (S.max() - 80)) / 80, 0, 1)
    rows = np.linspace(0, nb - 1, H1).astype(int)
    S = S[rows]
    rgb = np.stack([S ** 1.5 * 255, S ** 0.9 * 200, S ** 0.5 * 120], -1).astype(np.uint8)
    img.paste(Image.fromarray(rgb), (0, 0))
    for f in (1000, 2000, 4000):
        y = int(H1 * (1 - f / fmax))
        d.line([(0, y), (W, y)], fill=(70, 70, 90))
        d.text((4, y - 12), f"{f // 1000}k", fill=(150, 150, 170))
    # levels
    def lev(sig):
        s, L = M.block_loudness(sig[i0:i1], 0.4, 0.05)
        return (s / SR), L
    y0 = H1 + 20

    def ymap(L):
        return y0 + int((0 - np.clip(L, -60, 0)) / 60 * H2)
    for L in (-10, -20, -30, -40, -50):
        d.line([(0, ymap(L)), (W, ymap(L))], fill=(45, 45, 55))
        d.text((4, ymap(L) - 12), f"{L}", fill=(120, 120, 140))
    for sig, col in ((sfx, (120, 200, 120)), (music, (240, 160, 60)), (voice, (110, 170, 255))):
        ts, L = lev(sig)
        pts = [(int(t / (t1 - t0) * W), ymap(l)) for t, l in zip(ts + 0.2, L)]
        d.line(pts, fill=col, width=2)
    # annotations
    def xmap(t):
        return int((t - t0) / (t1 - t0) * W)
    for b in tl["beats"]:
        if b["end"] < t0 or b["start"] > t1 or b["kind"] != "speech":
            continue
        d.rectangle([xmap(b["start"]), y0 + H2 + 4, xmap(b["end"]), y0 + H2 + 10], fill=(90, 130, 200))
        d.text((max(0, xmap(b["start"])), y0 + H2 + 10), b["text"][:28], fill=(170, 190, 230))
    for c in tl["music"]["cues"]:
        if t0 <= c["t"] <= t1:
            d.line([(xmap(c["t"]), 0), (xmap(c["t"]), 14)], fill=(255, 255, 255), width=2)
            d.text((xmap(c["t"]) + 3, 2), f"{c['kind']}:{c['word']}", fill=(255, 255, 255))
    for m in tl["music"]["moods"]:
        if t0 <= m["t"] <= t1:
            d.line([(xmap(m["t"]), y0), (xmap(m["t"]), y0 + 14)], fill=(255, 120, 200), width=2)
            d.text((xmap(m["t"]) + 3, y0), m["mood"], fill=(255, 140, 210))
    for s in range(int(np.ceil(t0)), int(t1) + 1, 5):
        d.text((xmap(s), H1 + 2), f"{s}", fill=(200, 200, 200))
    d.text((W - 360, H1 + 2), f"{name}  blue=voice  orange=music  green=sfx", fill=(230, 230, 230))
    os.makedirs(PLOTS, exist_ok=True)
    p = os.path.join(PLOTS, f"{name}.png")
    img.save(p)
    return p


def main():
    tl = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
    mix, voice, music, sfx = (rd(f + ".wav") for f in ("mix", "voice", "music", "sfx"))
    if len(sys.argv) == 3:
        wins = [(f"win_{sys.argv[1]}_{sys.argv[2]}", float(sys.argv[1]), float(sys.argv[2]))]
    else:
        wins = default_windows(tl)
    for name, a, b in wins:
        print(plot(name, max(0, a), min(tl["duration"], b), tl, mix, voice, music, sfx))


if __name__ == "__main__":
    main()
