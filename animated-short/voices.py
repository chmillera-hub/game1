"""Synthesize dialogue, lip-sync it, and lay it out on a timeline.

usage: python3 voices.py <workdir>
Writes <workdir>/audio/lines/*.wav, <workdir>/timeline.json,
<workdir>/audio/dialogue.wav and <workdir>/captions.srt
"""
import hashlib, json, os, re, subprocess, sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import SCRIPT, VOICES, CAPTIONS  # noqa: E402

WORK = sys.argv[1]
MODELS = os.path.join(WORK, "models")
RHUBARB = os.path.join(WORK, "tools/Rhubarb-Lip-Sync-1.13.0-Linux/rhubarb")
LINES = os.path.join(WORK, "audio/lines")
SR = 24000
FPS = 24
PAUSE_SCALE = 1.1   # breathing room between lines
os.makedirs(LINES, exist_ok=True)

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(f"{MODELS}/kokoro-v1.0.onnx", f"{MODELS}/voices-v1.0.bin")
    return _kokoro


def trim(a, thresh=0.012, pad=0.06):
    env = np.convolve(np.abs(a), np.ones(240) / 240, mode="same")
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(a), idx[-1] + int(pad * SR))
    out = a[s:e].copy()
    f = int(0.012 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


PHRASE_GAP = {"...": 0.42, ".": 0.30, "?": 0.30, "!": 0.26}


def phrases(text):
    """Split a line at ellipses and sentence ends so each phrase gets a breath."""
    parts = re.split(r"(\.\.\.|[.?!](?=\s))", text)
    out, buf = [], ""
    for p in parts:
        if p in PHRASE_GAP:
            buf += p
            if buf.strip():
                out.append((buf.strip(), PHRASE_GAP[p]))
            buf = ""
        else:
            buf += p
    if buf.strip():
        out.append((buf.strip(), 0.0))
    return out


def synth(lid, speaker, text, extra):
    voice, speed, pitch = VOICES[speaker]
    speed = extra.get("speed", 1.0) * speed
    key = hashlib.sha1(f"v2|{voice}|{speed:.3f}|{pitch:.3f}|{text}".encode()).hexdigest()[:10]
    wav = os.path.join(LINES, f"{lid}_{key}.wav")
    if not os.path.exists(wav):
        chunks = []
        segs = phrases(text)
        for i, (ptxt, gap) in enumerate(segs):
            a, sr = kokoro().create(ptxt, voice=voice, speed=speed, lang="en-us")
            assert sr == SR
            chunks.append(trim(np.asarray(a, dtype=np.float32)))
            if i < len(segs) - 1:
                chunks.append(np.zeros(int(gap * SR), dtype=np.float32))
        a = np.concatenate(chunks)
        tmp = wav + ".raw.wav"
        sf.write(tmp, a, SR)
        if abs(pitch - 1.0) > 1e-3:
            # play back slower => lower pitch and slower delivery
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                            f"asetrate={int(SR * pitch)},aresample={SR}", wav], check=True)
            os.remove(tmp)
        else:
            os.replace(tmp, wav)
    return wav


def lipsync(wav, text):
    cache = wav.replace(".wav", ".cues.json")
    if not os.path.exists(cache):
        txt = wav.replace(".wav", ".txt")
        with open(txt, "w") as f:
            f.write(text)
        out = subprocess.run([RHUBARB, "-q", "-f", "json", "-d", txt, "--extendedShapes", "GHX", wav],
                             check=True, capture_output=True, text=True).stdout
        with open(cache, "w") as f:
            f.write(out)
    with open(cache) as f:
        return [(c["start"], c["value"]) for c in json.load(f)["mouthCues"]]


def envelope(a):
    hop = SR // FPS
    n = int(np.ceil(len(a) / hop))
    env = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    return (env / (env.max() + 1e-9)).round(3).tolist()


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    t = 0.0
    lines, marks, vocals = [], {}, []
    last_end = 0.0
    for entry in SCRIPT:
        kind = entry[0]
        if kind == "vocal":
            _, vid, speaker, text, offset, gain = entry
            wav = synth(vid, speaker, text, {"speed": 1.4})  # laughs run quicker than speech
            a, _ = sf.read(wav, dtype="float32")
            st = last_end + offset
            vocals.append({"id": vid, "speaker": speaker, "start": round(st, 3),
                           "end": round(st + len(a) / SR, 3), "wav": wav, "gain": gain,
                           "env": envelope(a)})
        elif kind == "mark":
            marks[entry[1]] = round(t, 3)
        elif kind == "pause":
            t += entry[1] * PAUSE_SCALE
        else:
            _, lid, speaker, text, extra = entry
            wav = synth(lid, speaker, text, extra)
            a, _ = sf.read(wav, dtype="float32")
            dur = len(a) / SR
            cues = lipsync(wav, text)
            lines.append({
                "id": lid, "speaker": speaker, "text": text,
                "caption": CAPTIONS.get(lid, text),
                "start": round(t, 3), "end": round(t + dur, 3), "wav": wav,
                "cues": [[round(t + c, 3), v] for c, v in cues],
                "env": envelope(a),
            })
            t += dur
            last_end = t
    total = round(t, 3)

    # dialogue stem (mono, 48k for mixing)
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for ln in lines + vocals:
        a, _ = sf.read(ln["wav"], dtype="float32")
        s = int(ln["start"] * SR)
        track[s:s + len(a)] += a * ln.get("gain", 1.0)
    sf.write(os.path.join(WORK, "audio/dialogue_24k.wav"), track, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "audio/dialogue_24k.wav"),
                    "-ar", "48000", os.path.join(WORK, "audio/dialogue.wav")], check=True)

    with open(os.path.join(WORK, "timeline.json"), "w") as f:
        json.dump({"fps": FPS, "duration": total, "marks": marks, "lines": lines, "vocals": vocals}, f)

    with open(os.path.join(WORK, "captions.srt"), "w") as f:
        for i, ln in enumerate(lines, 1):
            who = ln["speaker"].capitalize()
            f.write(f"{i}\n{srt_time(ln['start'])} --> {srt_time(ln['end'] + 0.25)}\n"
                    f"{'' if who == 'Narrator' else ''}{ln['caption']}\n\n")

    words = sum(len(ln["text"].split()) for ln in lines)
    speech = sum(ln["end"] - ln["start"] for ln in lines)
    print(f"lines={len(lines)} words={words} speech={speech:.1f}s total={total:.1f}s "
          f"({int(total // 60)}:{total % 60:04.1f})")
    print("marks:", marks)


if __name__ == "__main__":
    main()
