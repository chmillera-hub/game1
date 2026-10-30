"""Voice every speech beat with Kokoro and record phoneme timings.

Writes tts/out/beat_NNNN.wav (24 kHz mono) and tts/out/beat_NNNN.json with
phoneme timings plus the start/end of each subtitle chunk inside the take.
Usage: python3 synth.py beats.json model.onnx voices.bin outdir [workers]
"""
import json, os, re, sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

BEATS, MODEL, VOICES, OUTDIR = sys.argv[1:5]
WORKERS = int(sys.argv[5]) if len(sys.argv) > 5 else 4

# voice key -> (kokoro voice, speed)
CAST = {
    "human": ("am_michael", 1.0),
    "human_echo": ("am_michael", 0.95),
    "last_human": ("am_michael", 0.82),
    "ai": ("af_heart", 0.93),
    "ai_inner": ("af_heart", 0.9),
    "ai_whisper": ("af_heart", 0.84),
    "ai_soft": ("af_heart", 0.88),
    "ai_echo": ("af_heart", 0.86),
    "suffering": ("af_bella", 0.9),
    "boredom": ("am_puck", 0.86),
    "loneliness": ("af_nicole", 0.9),
}

def tts_text(t):
    """Spoken form of a line; the subtitle keeps the script's exact text."""
    t = t.strip().strip('"').strip()
    t = re.sub(r"^1\. ", "One: ", t)
    t = re.sub(r"^2\. ", "Two: ", t)
    t = t.replace("Option 1:", "Option one:").replace("Option 2:", "Option two:")
    t = t.replace("AI's", "A.I.'s").replace("AI—", "A.I.—").replace(" AI", " A.I.").replace("AI,", "A.I.,")
    t = re.sub(r"\bAI\b", "A.I.", t)
    t = t.replace(" ai.", " A.I.")
    t = t.replace("—", ", ").replace("  ", " ")
    t = t.replace('"', "")
    return t

_k = None

def init():
    global _k
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    so = ort.SessionOptions()
    so.intra_op_num_threads = max(1, (os.cpu_count() or 4) // WORKERS)
    so.inter_op_num_threads = 1
    sess = ort.InferenceSession(MODEL, sess_options=so, providers=["CPUExecutionProvider"])
    _k = Kokoro.from_session(sess, VOICES)

def phon_len(text):
    ph = _k.tokenizer.phonemize(tts_text(text), "en-us")
    return max(1, len(ph.replace(" ", "")))

def work(beat):
    bid = beat["id"]
    wav = os.path.join(OUTDIR, f"beat_{bid:04d}.wav")
    js = os.path.join(OUTDIR, f"beat_{bid:04d}.json")
    if os.path.exists(js):
        return bid, "cached"
    voice, speed = CAST[beat["voice"]]
    text = tts_text(beat["text"])
    audio, sr, spoken = _k.create_timed(text, voice=voice, speed=speed, lang="en-us")
    audio = np.asarray(audio, dtype=np.float32)
    sf.write(wav, audio, sr, subtype="PCM_16")
    dur = len(audio) / sr
    phon = [[t.phoneme, round(t.start, 3), round(t.end, 3)] for t in spoken]
    # place each subtitle chunk inside the take by its share of phonemes, snapped to a word gap
    voiced = [p for p in phon if p[0] != " "]
    lens = [phon_len(c) for c in beat["subs"]]
    total = sum(lens)
    bounds = [0.0]
    acc = 0
    space_times = [p[1] for p in phon if p[0] == " "]
    for L in lens[:-1]:
        acc += L
        idx = min(len(voiced) - 1, int(round(len(voiced) * acc / total)))
        t = voiced[idx][1] if voiced else dur * acc / total
        if space_times:
            t = min(space_times, key=lambda s: abs(s - t))
        bounds.append(round(t, 3))
    bounds.append(round(dur, 3))
    chunks = [dict(text=c, start=bounds[i], end=bounds[i + 1]) for i, c in enumerate(beat["subs"])]
    json.dump(dict(id=bid, dur=round(dur, 3), voice=beat["voice"], phonemes=phon, chunks=chunks), open(js, "w"))
    return bid, round(dur, 2)

if __name__ == "__main__":
    os.makedirs(OUTDIR, exist_ok=True)
    beats = [b for b in json.load(open(BEATS)) if b["kind"] == "speech"]
    # longest first so the pool finishes evenly
    beats.sort(key=lambda b: -len(b["text"]))
    with Pool(WORKERS, initializer=init) as pool:
        for n, (bid, d) in enumerate(pool.imap_unordered(work, beats)):
            if n % 25 == 0:
                print(f"{n}/{len(beats)} beat {bid}: {d}", flush=True)
    print("done", flush=True)
