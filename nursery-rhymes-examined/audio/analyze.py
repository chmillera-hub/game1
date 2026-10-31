#!/usr/bin/env python3
"""Visual checks of the rendered soundtrack (you cannot listen, so look).

Per window: spectrogram of mix.wav (0-8 kHz, top) and K-weighted 400 ms levels of the
voice / music / sfx stems (bottom), with speech beats, moods, cues, sfx events and songEnd marked.
PNGs go to build/audio/plots/.

Run:  python3 -I audio/analyze.py            (default windows)
      python3 -I audio/analyze.py 120 140    (custom window, seconds)
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


def default_windows(tl):
    se = tl["songEnd"]
    s0 = tl["song"][0]["t"]
    rain = min(e["t"] for e in tl["sfx"] if e["name"] == "rain")
    d = tl["duration"]
    return [("opening", 0, 25), ("song_start", s0 - 8, s0 + 16), ("song_stop", se - 6, se + 8),
            ("song_stop_zoom", se - 1.0, se + 2.0), ("rain_torrent", rain - 4, rain + 40), ("ending", d - 40, d)]


def plot(name, t0, t1, tl, mix, voice, music, sfx):
    W, H1, H2 = 1600, 360, 300
    img = Image.new("RGB", (W, H1 + H2 + 40), (14, 14, 18))
    d = ImageDraw.Draw(img)
    i0, i1 = int(t0 * SR), int(t1 * SR)
    x = mix[i0:i1].astype(np.float64)
    nfft = 2048 if t1 - t0 > 5 else 1024
    hop = max(1, (i1 - i0) // W)
    win = np.hanning(nfft)
    cols = []
    for k in range(W):
        seg = x[k * hop:k * hop + nfft]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        cols.append(np.abs(np.fft.rfft(seg * win)))
    S = 20 * np.log10(np.array(cols).T + 1e-9)
    fmax = 8000
    nb = int(fmax / (SR / nfft))
    S = S[:nb][::-1]
    S = np.clip((S - (S.max() - 75)) / 75, 0, 1)
    S = S[np.linspace(0, nb - 1, H1).astype(int)]
    rgb = np.stack([S ** 1.5 * 255, S ** 0.9 * 200, S ** 0.5 * 120], -1).astype(np.uint8)
    img.paste(Image.fromarray(rgb), (0, 0))
    for f in (500, 1000, 2000, 4000):
        y = int(H1 * (1 - f / fmax))
        d.line([(0, y), (W, y)], fill=(70, 70, 90))
        d.text((4, y - 12), f"{f}", fill=(150, 150, 170))
    y0 = H1 + 20

    def ymap(L):
        return y0 + int((0 - np.clip(L, -70, 0)) / 70 * H2)

    def xmap(t):
        return int((t - t0) / (t1 - t0) * W)
    for L in (-10, -20, -30, -40, -50, -60):
        d.line([(0, ymap(L)), (W, ymap(L))], fill=(45, 45, 55))
        d.text((4, ymap(L) - 12), f"{L}", fill=(120, 120, 140))
    hopb = 0.05 if t1 - t0 > 5 else 0.01
    blk = 0.4 if t1 - t0 > 5 else 0.05
    for sig, col in ((sfx, (120, 200, 120)), (music, (240, 160, 60)), (voice, (110, 170, 255))):
        s, L = M.block_loudness(sig[i0:i1], blk, hopb)
        pts = [(xmap(t0 + t + blk / 2), ymap(l)) for t, l in zip(s / SR, L)]
        if len(pts) > 1:
            d.line(pts, fill=col, width=2)
    for b in tl["beats"]:
        if b["end"] < t0 or b["start"] > t1 or b["kind"] != "speech":
            continue
        d.rectangle([xmap(b["start"]), y0 + H2 + 4, xmap(b["end"]), y0 + H2 + 10], fill=(90, 130, 200))
        d.text((max(0, xmap(b["start"])), y0 + H2 + 10), b["text"][:40], fill=(170, 190, 230))
    for c in tl["music"]["cues"]:
        if t0 <= c["t"] <= t1:
            d.line([(xmap(c["t"]), 0), (xmap(c["t"]), 14)], fill=(255, 255, 255), width=2)
            d.text((xmap(c["t"]) + 3, 2), f"{c['kind']}:{c['word']}", fill=(255, 255, 255))
    for e in tl["sfx"]:
        if t0 <= e["t"] <= t1:
            d.line([(xmap(e["t"]), 18), (xmap(e["t"]), 30)], fill=(120, 255, 120), width=2)
            d.text((xmap(e["t"]) + 3, 18), e["name"], fill=(140, 255, 140))
    for m in tl["music"]["moods"]:
        if t0 <= m["t"] <= t1:
            d.line([(xmap(m["t"]), y0), (xmap(m["t"]), y0 + 14)], fill=(255, 120, 200), width=2)
            d.text((xmap(m["t"]) + 3, y0), m["mood"], fill=(255, 140, 210))
    se = tl["songEnd"]
    if t0 <= se <= t1:
        d.line([(xmap(se), 0), (xmap(se), H1 + H2 + 20)], fill=(255, 60, 60), width=1)
        d.text((xmap(se) + 3, 34), "songEnd", fill=(255, 90, 90))
    step = 5 if t1 - t0 > 12 else (1 if t1 - t0 > 4 else 0.5)
    for s in np.arange(np.ceil(t0 / step) * step, t1, step):
        d.text((xmap(s), H1 + 2), f"{s:g}", fill=(200, 200, 200))
    d.text((W - 420, H1 + 2), f"{name}  blue=voice  orange=music  green=sfx", fill=(230, 230, 230))
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
