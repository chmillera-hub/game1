"""Builds timeline.json: scene/line/mark times plus per-frame mouth envelopes for lip-sync."""
import os, sys, json
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from story import LINES, SCENES, CAPTIONS

FPS = 24
SR = 48000


def envelope(y):
    hop = SR // FPS
    n = int(np.ceil(len(y) / hop))
    e = np.zeros(n)
    for i in range(n):
        seg = y[i * hop:(i + 1) * hop]
        e[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    ref = np.percentile(e[e > 0], 90) if np.any(e > 0) else 1
    e = np.clip(e / (ref + 1e-9), 0, 1.15)
    e = np.where(e < 0.12, 0, e)
    # light smoothing so the mouth doesn't flutter
    k = np.array([0.25, 0.5, 0.25])
    e = np.convolve(e, k, mode="same")
    return [round(float(v), 3) for v in e]


t = 0.0
scenes, lines, marks = [], [], {}
for name, music, beats in SCENES:
    start = t
    for b in beats:
        kind = b[0]
        if kind == "wait":
            t += b[1]
        elif kind == "mark":
            marks[f"{name}.{b[1]}"] = round(t, 4)
        elif kind == "say":
            lid = b[1]
            who, text = LINES[lid]
            y, sr = sf.read(os.path.join(HERE, "voices", lid + ".wav"))
            assert sr == SR
            dur = len(y) / SR
            lines.append(dict(id=lid, who=who, text=CAPTIONS.get(lid, text), start=round(t, 4),
                              end=round(t + dur, 4), env=envelope(y)))
            t += dur
    scenes.append(dict(name=name, music=music, start=round(start, 4), end=round(t, 4)))

tl = dict(fps=FPS, duration=round(t, 4), scenes=scenes, lines=lines, marks=marks)
json.dump(tl, open(os.path.join(HERE, "timeline.json"), "w"))
for s in scenes:
    print(f"{s['name']:8s} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end']-s['start']:.1f}s)  {s['music']}")
print(f"TOTAL {t:.2f}s = {int(t//60)}:{t%60:04.1f}")
