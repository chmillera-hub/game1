"""Synthesize every line with Piper, then lay them on a timeline.

Outputs (in build/):
  lines/<label>.wav   processed 44.1 kHz mono clips
  voice.wav           the full dialogue track
  timeline.json       scene/beat timing + per-frame mouth envelope for lip-sync
"""
import json, os, subprocess, sys, wave
import numpy as np
from piper import PiperVoice, SynthesisConfig
from screenplay import CAST, SCENES

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = os.environ.get("VOICES_DIR", os.path.join(HERE, "voices"))
BUILD = os.path.join(HERE, "build")
SR, FPS = 44100, 30
os.makedirs(os.path.join(BUILD, "lines"), exist_ok=True)

_models = {}
def model(name):
    if name not in _models:
        _models[name] = PiperVoice.load(os.path.join(VOICES, name + ".onnx"))
    return _models[name]

def read_wav(path):
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        return x, w.getframerate()

def synth(beat):
    c = CAST[beat["speaker"]]
    raw = os.path.join(BUILD, "lines", beat["label"] + ".raw.wav")
    out = os.path.join(BUILD, "lines", beat["label"] + ".wav")
    cfg = SynthesisConfig(speaker_id=c["spk"], length_scale=beat["length"] or c["length"],
                          noise_scale=0.72, noise_w_scale=0.85)
    with wave.open(raw, "wb") as w:
        model(c["model"]).synthesize_wav(beat["text"], w, syn_config=cfg)
    filters = [f"aresample={SR}"]
    if c["pitch"]:
        filters.append(f"rubberband=pitch={2 ** (c['pitch'] / 12):.5f}")
    if beat["thought"]:
        # inner voice: softer, slightly hollow and echoing
        filters += ["highpass=f=160", "aecho=0.8:0.6:60|140:0.35|0.2", "volume=0.8"]
    # trim leading/trailing silence so timing is tight
    filters += ["silenceremove=start_periods=1:start_threshold=-45dB",
                "areverse", "silenceremove=start_periods=1:start_threshold=-45dB", "areverse"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", ",".join(filters),
                    "-ac", "1", "-ar", str(SR), out], check=True)
    os.remove(raw)
    x, _ = read_wav(out)
    return x * beat["vol"]

def main():
    t = 0.0
    timeline = dict(fps=FPS, scenes=[], beats=[])
    clips = []
    for sid, chapter, beats in SCENES:
        s0 = t
        for b in beats:
            if b["type"] == "pause":
                timeline["beats"].append(dict(label=b["label"], type="pause", start=t, end=t + b["dur"]))
                t += b["dur"]
                continue
            x = synth(b)
            dur = len(x) / SR
            timeline["beats"].append(dict(label=b["label"], type="line", speaker=b["speaker"],
                                          caption=b["caption"], thought=b["thought"],
                                          start=round(t, 4), end=round(t + dur, 4)))
            clips.append((t, x, b))
            print(f"{t:7.2f}  {b['speaker']:7s} {dur:5.2f}s  {b['text']}")
            t += dur + b["gap"]
        timeline["scenes"].append(dict(id=sid, chapter=chapter, start=round(s0, 4), end=round(t, 4)))
    total = t
    timeline["duration"] = round(total, 4)

    voice = np.zeros(int(total * SR) + SR)
    nframes = int(np.ceil(total * FPS))
    mouth = np.zeros(nframes)
    for start, x, b in clips:
        i = int(start * SR)
        voice[i:i + len(x)] += x
        if b["thought"]:
            continue
        # mouth envelope: RMS per video frame, normalised per clip, lightly smoothed
        hop = SR // FPS
        env = np.array([np.sqrt(np.mean(x[k:k + hop] ** 2)) for k in range(0, len(x), hop)])
        env = np.clip(env / (np.percentile(env, 90) + 1e-6), 0, 1.2)
        env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
        f0 = int(round(start * FPS))
        mouth[f0:f0 + len(env)] = np.maximum(mouth[f0:f0 + len(env)], env[:max(0, nframes - f0)])
    timeline["mouth"] = [round(float(v), 3) for v in mouth]

    voice = voice / max(1e-6, np.abs(voice).max()) * 0.89
    with wave.open(os.path.join(BUILD, "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((voice * 32767).astype(np.int16).tobytes())
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump(timeline, f)
    print(f"TOTAL {total:.2f}s = {int(total // 60)}:{total % 60:05.2f}")

if __name__ == "__main__":
    main()
