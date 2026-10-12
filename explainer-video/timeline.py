"""Turn the screenplay into absolute timings, a voice track and lip-sync curves."""
import json
import os

import numpy as np

import voice
from script import SCENES, VOICES

FPS = 30
SR = voice.SR
SCENE_GAP = 0.45      # breathing room between scenes (the wipe happens here)
TAIL = 0.0


def _resolve_sfx_time(spec, start, end):
    if isinstance(spec, (int, float)):
        return start + spec
    if spec.startswith("end"):
        return end + float(spec[3:] or 0)
    return start + float(spec)


def build(verbose=True):
    t = 0.0
    beats, scenes, sfx, qa = [], [], [], []
    clips = []  # (who, start, audio)
    for si, sc in enumerate(SCENES):
        s0 = t
        if si > 0:
            t += SCENE_GAP
        for bi, b in enumerate(sc["beats"]):
            t += b["pre"]
            if b["who"]:
                audio, words, q = voice.line(b["who"], b["text"], b["say"], b["speed"])
                dur = len(audio) / SR
                clips.append((b["who"], t, audio))
                qa.append({"scene": sc["id"], "who": b["who"], "text": b["say"] or b["text"], **q})
                if verbose and q["match"] < 0.8:
                    print(f"  ! low ASR match {q['match']}: {b['text']!r} -> {q['heard']!r}")
            else:
                dur = b["hold"] or 0.5
                words = []
            start, end = t, t + dur
            beats.append(dict(scene=si, idx=bi, who=b["who"], text=b["text"], tag=b["tag"],
                              emo=b["emo"], start=start, end=end,
                              words=[(w, s + start, e + start) for w, (s, e) in words]))
            for name, spec in b["sfx"]:
                sfx.append((name, _resolve_sfx_time(spec, start, end)))
            t = end + b["gap"]
        scenes.append(dict(id=sc["id"], start=s0, end=t, music=sc["music"],
                           lens=sc.get("lens")))
    total = t + TAIL
    # voice track + per-character lip sync
    n = int(total * SR) + SR
    track = np.zeros(n, np.float32)
    nframes = int(np.ceil(total * FPS))
    mouth = {k: np.zeros(nframes, np.float32) for k in VOICES}
    rnd = {k: np.zeros(nframes, np.float32) for k in VOICES}
    for who, st, audio in clips:
        i0 = int(st * SR)
        track[i0:i0 + len(audio)] += audio
        o, r = lipsync(audio)
        f0 = int(round(st * FPS))
        m = min(len(o), nframes - f0)
        mouth[who][f0:f0 + m] = np.maximum(mouth[who][f0:f0 + m], o[:m])
        rnd[who][f0:f0 + m] = r[:m]
    tl = dict(fps=FPS, total=total, nframes=nframes, beats=beats, scenes=scenes, sfx=sfx)
    return tl, track[:int(total * SR)], mouth, rnd, qa


def lipsync(audio):
    """Mouth openness and roundness per video frame, from loudness and brightness."""
    hop = SR // FPS
    win = hop * 2
    pad = np.concatenate([np.zeros(hop // 2, np.float32), audio, np.zeros(win, np.float32)])
    nf = int(np.ceil(len(audio) / hop))
    rms = np.zeros(nf)
    cen = np.zeros(nf)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    w = np.hanning(win)
    for i in range(nf):
        seg = pad[i * hop:i * hop + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        rms[i] = np.sqrt(np.mean(seg ** 2) + 1e-12)
        spec = np.abs(np.fft.rfft(seg * w))
        band = (freqs > 150) & (freqs < 6000)
        cen[i] = (spec[band] * freqs[band]).sum() / (spec[band].sum() + 1e-9)
    db = 20 * np.log10(rms + 1e-9)
    ref = np.percentile(db[db > -60], 90) if np.any(db > -60) else -20
    o = np.clip((db - (ref - 30)) / 30, 0, 1) ** 1.3
    # attack fast, release a bit slower so the mouth doesn't flicker
    sm = np.zeros_like(o)
    for i in range(len(o)):
        prev = sm[i - 1] if i else 0
        k = 0.75 if o[i] > prev else 0.45
        sm[i] = prev + (o[i] - prev) * k
    r = np.clip((2600 - cen) / 1600, 0, 1)
    return sm.astype(np.float32), r.astype(np.float32)


def save(tl, mouth, rnd, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".json", "w") as f:
        json.dump(tl, f)
    np.savez_compressed(path + ".npz", **{f"m_{k}": v for k, v in mouth.items()},
                        **{f"r_{k}": v for k, v in rnd.items()})


def load(path):
    with open(path + ".json") as f:
        tl = json.load(f)
    z = np.load(path + ".npz")
    mouth = {k[2:]: z[k] for k in z.files if k.startswith("m_")}
    rnd = {k[2:]: z[k] for k in z.files if k.startswith("r_")}
    return tl, mouth, rnd
