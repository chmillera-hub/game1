"""Voice acting: synthesize every script line with Kokoro TTS, then derive
lip-sync envelopes and estimated word timings.

Outputs:
  out/lines/<line_id>.wav   (48 kHz mono float32, cached by content hash)
  out/lipsync.json          {line_id: {open: [...], wide: [...], word_starts: [...]}}
Returns {line_id: duration_seconds}.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
LINES = os.path.join(OUT, "lines")
KOKORO_DIR = os.environ.get(
    "KOKORO_DIR",
    "/tmp/claude-0/-home-user-game1/3880d59f-fdde-59ad-bf81-afdfa4c1b224/scratchpad/kokoro")
SR = 48000
LIP_RATE = 100

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(KOKORO_DIR, "model.onnx"),
                         os.path.join(KOKORO_DIR, "voices.npz"))
    return _kokoro


def voice_style(spec):
    """'bm_george' or 'bm_george*0.7+am_fenrir*0.3' -> style array or name."""
    if "+" not in spec and "*" not in spec:
        return spec
    k = kokoro()
    acc = None
    for part in spec.split("+"):
        name, _, w = part.partition("*")
        arr = k.voices[name.strip()] * float(w or 1.0)
        acc = arr if acc is None else acc + arr
    return acc


def resample(a, sr_in, sr_out):
    if sr_in == sr_out:
        return a
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(sr_in, sr_out)
    return resample_poly(a, sr_out // g, sr_in // g).astype(np.float32)


def post_fx(wav_path, pitch=1.0, fx=None):
    """Optional pitch shift (rubberband, tempo preserved) via ffmpeg."""
    if pitch == 1.0 and not fx:
        return
    filters = []
    if pitch != 1.0:
        filters.append(f"rubberband=pitch={pitch}:formant=preserved")
    if fx == "phone":
        filters.append("highpass=f=300,lowpass=f=3400")
    tmp = wav_path + ".fx.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav_path, "-af",
                    ",".join(filters), "-c:a", "pcm_f32le", tmp], check=True)
    os.replace(tmp, wav_path)


def synth_line(line, voices):
    """Synthesize one line dict -> path to wav (cached)."""
    who = line["who"]
    v = dict(voices.get(who, {}))
    v.update({k: line[k] for k in ("voice", "speed", "lang", "pitch", "fx") if k in line})
    voice = v.get("voice", "af_heart")
    speed = float(v.get("speed", 1.0))
    lang = v.get("lang", "en-us")
    pitch = float(v.get("pitch", 1.0))
    fx = v.get("fx")
    say = line.get("say", line["text"])  # 'say' lets spoken text differ from caption
    key = hashlib.sha1(json.dumps([say, voice, speed, lang, pitch, fx, 3]).encode()).hexdigest()[:12]
    path = os.path.join(LINES, f"{line['id']}.wav")
    keyf = path + ".key"
    if os.path.exists(path) and os.path.exists(keyf) and open(keyf).read() == key:
        return path
    audio, sr = kokoro().create(say, voice=voice_style(voice), speed=speed, lang=lang)
    audio = resample(np.asarray(audio, dtype=np.float32), sr, SR)
    # tiny fades to avoid clicks
    f = int(0.006 * SR)
    if len(audio) > 2 * f:
        audio[:f] *= np.linspace(0, 1, f)
        audio[-f:] *= np.linspace(1, 0, f)
    sf.write(path, audio, SR, subtype="FLOAT")
    post_fx(path, pitch, fx)
    with open(keyf, "w") as fh:
        fh.write(key)
    return path


def lipsync(audio, text):
    """Per-10ms mouth 'open' (0..1) and 'wide' (-1..1) + word start estimates."""
    hop = SR // LIP_RATE
    win = hop * 3
    n = max(1, int(np.ceil(len(audio) / hop)))
    pad = np.concatenate([np.zeros(win), audio, np.zeros(win)])
    rms = np.zeros(n)
    cen = np.zeros(n)
    window = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    for i in range(n):
        seg = pad[i * hop + win - win // 2: i * hop + win + win // 2][:win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        rms[i] = np.sqrt(np.mean(seg ** 2) + 1e-12)
        spec = np.abs(np.fft.rfft(seg * window))
        band = (freqs > 200) & (freqs < 8000)
        s = spec[band]
        cen[i] = (freqs[band] * s).sum() / (s.sum() + 1e-9)
    db = 20 * np.log10(rms + 1e-9)
    ref = np.percentile(db, 95)
    open_ = np.clip((db - (ref - 32)) / 28, 0, 1) ** 1.2
    # attack fast / release slower
    sm = np.zeros_like(open_)
    v = 0.0
    for i, x in enumerate(open_):
        v = v + (x - v) * (0.65 if x > v else 0.3)
        sm[i] = v
    wide = np.clip((cen - 1800) / 1400, -1, 1)
    wide = np.convolve(wide, np.ones(5) / 5, mode="same")
    wide = np.where(sm > 0.08, wide, 0)

    # word timing estimate: distribute words over voiced span by weight
    words = text.split()
    voiced = np.where(sm > 0.12)[0]
    t0 = voiced[0] / LIP_RATE if len(voiced) else 0.0
    t1 = voiced[-1] / LIP_RATE if len(voiced) else len(audio) / SR
    weights = []
    for w in words:
        core = re.sub(r"[^A-Za-z0-9']", "", w)
        wt = 0.6 + len(core) * 0.32
        if re.search(r"[.!?…]$", w):
            wt += 2.2
        elif re.search(r"[,;:—-]$", w):
            wt += 1.1
        weights.append(wt)
    tot = sum(weights) or 1
    starts, acc = [], 0.0
    for wt in weights:
        starts.append(round(t0 + (t1 - t0) * acc / tot, 3))
        acc += wt
    return {"open": [round(float(x), 3) for x in sm],
            "wide": [round(float(x), 3) for x in wide],
            "word_starts": starts}


def run(script_path=os.path.join(ROOT, "script.json")):
    os.makedirs(LINES, exist_ok=True)
    with open(script_path) as f:
        script = json.load(f)
    voices = script.get("voices", {})
    durations, lip = {}, {}
    todo = [b for sc in script["scenes"] for b in sc["beats"] if b.get("t", "line") == "line"]
    for i, b in enumerate(todo):
        path = synth_line(b, voices)
        audio, sr = sf.read(path, dtype="float32")
        durations[b["id"]] = round(len(audio) / sr, 4)
        lip[b["id"]] = lipsync(audio, b.get("caption", b["text"]))
        print(f"[tts] {i+1}/{len(todo)} {b['id']} {durations[b['id']]:.2f}s", file=sys.stderr)
    with open(os.path.join(OUT, "lipsync.json"), "w") as f:
        json.dump(lip, f)
    with open(os.path.join(OUT, "durations.json"), "w") as f:
        json.dump(durations, f, indent=1)
    return durations


if __name__ == "__main__":
    run()
