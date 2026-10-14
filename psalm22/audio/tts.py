"""Generate the Psalm 22 narration with Kokoro TTS and write phrase timings.

Usage: /opt/venv/bin/python psalm22/audio/tts.py
Outputs (in $WORK/audio, default /opt/work/psalm22/audio):
  narration.wav      48 kHz mono narration track on the final timeline
  phrases.json       per-phrase start/end seconds on the final timeline
"""
import json, os, re
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.environ.get("WORK", "/opt/work/psalm22")
OUT = os.path.join(WORK, "audio")
os.makedirs(os.path.join(OUT, "phr"), exist_ok=True)

VOICE = os.environ.get("VOICE", "am_michael")
SPEED = float(os.environ.get("SPEED", "0.84"))
SR = 48000

INTRO = 5.0          # title shot before the first words
OUTRO = 8.0          # after "He has done it!"
GAP_BLOCK = 1.8      # between blocks
GAP_EXTRA = {"b14": 2.6, "b15": 3.4}   # longer breath before the turn / resurrection
GAP_PUNCT = {",": 0.22, ";": 0.42, ":": 0.38, ".": 0.55, "?": 0.6, "!": 0.6, "—": 0.3}

# pronunciation helpers (display text is unchanged)
RESPELL = {"Bashan": "Bayshan"}
# phoneme fixes applied after espeak phonemization
PHONEME_FIX = [("lˈaɪv fɚɹˈɛvɚ", "lˈɪv fɚɹˈɛvɚ"), ("həznɑːt", "hˈæz nˈɑːt")]


def speakable(text):
    t = text.replace("“", "").replace("”", "").replace("’", "'")
    t = t.replace("—", ",")
    for k, v in RESPELL.items():
        t = re.sub(r"\b%s\b" % k, v, t)
    return t.strip()


def trim(x, thr=0.006, pad=0.03, sr=24000):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(x), idx[-1] + int(pad * 2 * sr))
    return x[a:b]


def main():
    data = json.load(open(os.path.join(ROOT, "text", "psalm22.json")))
    k = Kokoro("/opt/assets/tts/kokoro-v1.0.onnx", "/opt/assets/tts/voices-v1.0.bin")
    t = INTRO
    pieces, phrases = [], []
    for bi, block in enumerate(data["blocks"]):
        if bi > 0:
            t += GAP_EXTRA.get(block["id"], GAP_BLOCK)
        bstart = t
        for pi, text in enumerate(block["phrases"]):
            cache = os.path.join(OUT, "phr", "%s_%02d_%s_%.2f.wav" % (block["id"], pi, VOICE, SPEED))
            if os.path.exists(cache):
                y, _ = sf.read(cache)
            else:
                ph = k.tokenizer.phonemize(speakable(text), "en-us")
                for a, b in PHONEME_FIX:
                    ph = ph.replace(a, b)
                s, sr = k.create(ph, voice=VOICE, speed=SPEED, is_phonemes=True)
                y = resample_poly(trim(np.asarray(s, dtype=np.float64), sr=sr), SR, sr)
                sf.write(cache, y, SR)
            dur = len(y) / SR
            pieces.append((t, y))
            phrases.append({"block": block["id"], "index": pi, "text": text,
                            "start": round(t, 3), "end": round(t + dur, 3)})
            t += dur
            if pi < len(block["phrases"]) - 1:
                last = text.rstrip("”\"")[-1]
                t += GAP_PUNCT.get(last, 0.3)
        for p in phrases:
            if p["block"] == block["id"]:
                p["block_start"] = round(bstart, 3)
    total = t + OUTRO
    track = np.zeros(int(total * SR) + SR)
    for start, y in pieces:
        i = int(start * SR)
        track[i:i + len(y)] += y
    peak = np.max(np.abs(track)) or 1
    track = track / peak * 0.89
    sf.write(os.path.join(OUT, "narration.wav"), track[: int(total * SR)], SR, subtype="PCM_16")
    json.dump({"voice": VOICE, "speed": SPEED, "intro": INTRO, "outro": OUTRO,
               "total": round(total, 3), "phrases": phrases},
              open(os.path.join(OUT, "phrases.json"), "w"), indent=1)
    print("total %.1f s, %d phrases" % (total, len(phrases)))


if __name__ == "__main__":
    main()
