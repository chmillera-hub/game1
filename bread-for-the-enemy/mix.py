"""Final audio mix: dialogue + score (sidechain-ducked under speech) + sound design."""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000


def envelope(x, attack=0.04, release=0.45):
    """Peak-ish envelope follower on a mono signal (fast attack, slow release)."""
    win = int(0.02 * SR)
    rms = np.sqrt(np.maximum(signal.convolve(x ** 2, np.ones(win) / win, mode="same"), 0.0))
    # downsample to 200 Hz for the follower
    hop = SR // 200
    r = rms[::hop]
    out = np.zeros_like(r)
    a = np.exp(-1 / (attack * 200))
    b = np.exp(-1 / (release * 200))
    v = 0.0
    for i, s in enumerate(r):
        v = a * v + (1 - a) * s if s > v else b * v + (1 - b) * s
        out[i] = v
    return np.interp(np.arange(len(x)), np.arange(len(out)) * hop, out)


def load(path, n):
    x, sr = sf.read(path, dtype="float64")
    assert sr == SR, path
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    out = np.zeros((n, 2))
    m = min(n, len(x))
    out[:m] = x[:m]
    return out


def main(work):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    n = int((tl["duration"] + 0.5) * SR)
    voice = load(os.path.join(work, "voice.wav"), n)
    music = load(os.path.join(work, "music.wav"), n)
    sfx = load(os.path.join(work, "sfx.wav"), n)

    venv = envelope(voice.mean(1))
    duck = np.clip(venv / 0.035, 0, 1)  # 1 while someone speaks
    music_gain = 0.8 * (1 - 0.5 * duck)  # about -6 dB under dialogue, fuller between lines
    sfx_gain = 0.85 * (1 - 0.3 * duck)
    mix = voice * 1.0 + music * music_gain[:, None] + sfx * sfx_gain[:, None]

    # gentle bus compression (soft knee) to keep peaks civil on phone speakers
    lvl = envelope(np.abs(mix).max(1), 0.005, 0.25)
    thr = 0.5
    gain = np.where(lvl > thr, (thr + (lvl - thr) * 0.4) / np.maximum(lvl, 1e-9), 1.0)
    mix *= gain[:, None]
    pk = np.max(np.abs(mix))
    mix *= 0.97 / max(pk, 1e-9)
    raw = os.path.join(work, "mix_raw.wav")
    sf.write(raw, mix.astype(np.float32), SR)

    # two-pass EBU R128 loudness normalisation to -15 LUFS (phones / social apps), true-peak -1.5 dB
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    txt = p.stderr[p.stderr.rfind("{"):]
    m = json.loads(txt[: txt.rfind("}") + 1])
    af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          f"aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-af", af, "-ar", "48000",
                    os.path.join(work, "mix.wav")], check=True)
    print("mixed; measured input loudness", m["input_i"], "LUFS")


if __name__ == "__main__":
    main(os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work")))
