"""Synthesize every script line, apply per-character voice processing, and
write build/schedule.json with absolute line / word / phoneme timing."""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "..", "build")
CACHE = os.path.join(BUILD, "voice_cache")
os.makedirs(CACHE, exist_ok=True)

FX = {
    "warm": "highpass=f=70,equalizer=f=220:t=q:w=1.2:g=1.5",
    "narr": "highpass=f=70,equalizer=f=220:t=q:w=1.2:g=2,equalizer=f=4500:t=q:w=1:g=-1",
    "gruff": "highpass=f=60,equalizer=f=160:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=4:attack=5:release=80",
    "crisp": "highpass=f=90,equalizer=f=3200:t=q:w=1:g=2",
    "tremble": "highpass=f=90,vibrato=f=6.5:d=0.07",
    "soft": "highpass=f=70,lowpass=f=7500,equalizer=f=300:t=q:w=1:g=1.5",
    "elder": "highpass=f=80,vibrato=f=5.2:d=0.05,lowpass=f=8000",
}
TARGET_RMS = {"anger": 0.11, "fear": 0.085, "sad": 0.07, "nar": 0.08, "nana": 0.075}


def process(raw, out, cast, shout):
    filters = []
    st = cast.get("pitch", 0)
    if abs(st) > 0.05:
        filters.append(f"rubberband=pitch={2 ** (st / 12):.5f}:pitchq=quality")
    filters.append(FX[cast["fx"]])
    if shout:
        filters.append("volume=2.2,asoftclip=type=tanh,volume=0.6")
    filters.append("aresample=48000")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", ",".join(filters),
                    "-ac", "1", out], check=True)


def main():
    sys.path.insert(0, HERE)
    from tts_engine import TTS
    script = json.load(open(os.path.join(HERE, "script.json")))
    tts = None
    cursor = 0.0
    sched = {"lines": [], "cast": script["cast"]}
    for ln in script["lines"]:
        cast = script["cast"][ln["sp"]]
        speed = ln.get("speed", cast["speed"])
        say = ln.get("say", ln["text"])
        key = hashlib.md5(json.dumps([say, cast, speed, ln.get("shout", False)]).encode()).hexdigest()[:12]
        wav = os.path.join(CACHE, f"{ln['id']}_{key}.wav")
        meta = wav.replace(".wav", ".json")
        if not os.path.exists(meta):
            if tts is None:
                tts = TTS()
            audio, phones, words, known = tts.synth(say, cast["voice"], speed)
            raw = wav.replace(".wav", "_raw.wav")
            sf.write(raw, audio, 24000)
            process(raw, wav, cast, ln.get("shout", False))
            os.remove(raw)
            # loudness normalize (RMS over voiced samples)
            y, sr = sf.read(wav)
            voiced = y[np.abs(y) > 0.01]
            rms = np.sqrt(np.mean(voiced ** 2)) if len(voiced) else 1
            y = y * (TARGET_RMS.get(ln["sp"], 0.08) / rms)
            peak = np.max(np.abs(y))
            if peak > 0.95:
                y *= 0.95 / peak
            sf.write(wav, y.astype(np.float32), sr)
            # map subtitle words (text) to tts words (say) by index when counts match
            json.dump({"phones": [[p[0], round(float(p[1]), 3), round(float(p[2]), 3)] for p in phones],
                       "words": [{k: (float(v) if k in ("t0", "t1") else v) for k, v in w.items()} for w in words],
                       "dur": len(y) / sr, "known": known}, open(meta, "w"))
            print(f"synth {ln['id']:5s} {len(y) / sr:5.2f}s  {say}")
        m = json.load(open(meta))
        start = cursor + ln.get("pause", 0.4)
        end = start + m["dur"]
        cursor = end
        sched["lines"].append({
            "id": ln["id"], "sc": ln["sc"], "sp": ln["sp"], "text": ln["text"], "say": say,
            "t0": round(start, 3), "t1": round(end, 3), "wav": os.path.relpath(wav, BUILD),
            "hi": ln.get("hi", []), "lo": ln.get("lo", []), "shout": ln.get("shout", False),
            "words": [{"w": w["w"], "t0": round(start + w["t0"], 3), "t1": round(start + w["t1"], 3)} for w in m["words"]],
            "phones": [[p[0], round(start + p[1], 3), round(start + p[2], 3)] for p in m["phones"] if p[0] != " "],
        })
    sched["duration"] = round(cursor + script.get("tail", 4.0), 3)
    json.dump(sched, open(os.path.join(BUILD, "schedule.json"), "w"), indent=0)
    print(f"total duration {sched['duration']:.1f}s, {len(sched['lines'])} lines")


if __name__ == "__main__":
    main()
