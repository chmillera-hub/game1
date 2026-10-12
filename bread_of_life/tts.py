"""Voice acting: Kokoro-82M (timestamped ONNX export) with per-phoneme timing.

For every line in script.py this writes <WORK>/voice/<id>.wav (24 kHz mono)
and <id>.json with segment, subtitle-chunk and phoneme timings (seconds,
relative to the start of the line's audio).
"""
import hashlib
import json
import os
import sys

import numpy as np
import onnxruntime as ort
import soundfile as sf
from kokoro_onnx.tokenizer import Tokenizer

from config import MODELS, TTS_SR, WORK
import script

OUT = os.path.join(WORK, "voice")
CACHE = os.path.join(WORK, "voice_cache")
os.makedirs(OUT, exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

FRAME = 600  # samples per duration unit at 24 kHz

_sess = None
_tok = None
_voices = None


def _init():
    global _sess, _tok, _voices
    if _sess is None:
        so = ort.SessionOptions()
        so.intra_op_num_threads = os.cpu_count() or 4
        _sess = ort.InferenceSession(os.path.join(MODELS, "ts", "model.onnx"), so)
        _tok = Tokenizer()
        _voices = np.load(os.path.join(MODELS, "voices-v1.0.bin"))


def style_pack(voice):
    _init()
    if isinstance(voice, str):
        return _voices[voice]
    total = sum(voice.values())
    return sum(_voices[k] * (w / total) for k, w in voice.items())


def phonemize(text, lang):
    _init()
    return _tok.phonemize(text, lang)


def synth(text, voice, lang="en-us", speed=1.0):
    """Returns (audio float32 @24k, phonemes str, per-token (start, end) seconds)."""
    _init()
    key = hashlib.sha1(json.dumps([text, voice, lang, speed], sort_keys=True).encode()).hexdigest()[:16]
    cpath = os.path.join(CACHE, key + ".npz")
    if os.path.exists(cpath):
        z = np.load(cpath, allow_pickle=False)
        return z["audio"], str(z["ph"]), z["times"]
    ph = _tok.phonemize(text, lang)
    known = _tok.known(ph)
    ids = _tok.tokenize(known)
    pack = style_pack(voice)
    style = pack[len(ids) - 1].reshape(1, 256).astype(np.float32)
    wav, dur = _sess.run(None, {
        "input_ids": np.array([[0, *ids, 0]], dtype=np.int64),
        "style": style,
        "speed": np.array([speed], dtype=np.float32),
    })
    wav = wav.ravel().astype(np.float32)
    dur = dur.ravel().astype(np.float64)
    edges = np.concatenate([[0.0], np.cumsum(dur)]) * FRAME
    scale = len(wav) / edges[-1]
    edges *= scale
    # token i (excluding the leading pad) spans edges[i+1]..edges[i+2]
    times = np.stack([edges[1:-2], edges[2:-1]], axis=1) / TTS_SR
    assert len(times) == len(known), (len(times), len(known))
    np.savez(cpath, audio=wav, ph=np.array(known), times=times)
    return wav, known, times


def trim(audio, times, thresh_db=-42.0, pad=0.04):
    """Trim leading/trailing silence, shifting token times to match."""
    win = 240
    n = len(audio) // win
    if n == 0:
        return audio, times
    rms = np.sqrt(np.mean(audio[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    voiced = np.where(db > thresh_db)[0]
    if len(voiced) == 0:
        return audio, times
    a = max(0, voiced[0] * win - int(pad * TTS_SR))
    b = min(len(audio), (voiced[-1] + 1) * win + int(pad * TTS_SR))
    out = audio[a:b].copy()
    # short fades to avoid clicks
    f = min(120, len(out) // 4)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    t = times - a / TTS_SR
    t = np.clip(t, 0, len(out) / TTS_SR)
    return out, t


def split_subs(seg_text, lang, ph_known, times):
    """Find subtitle chunk boundaries ('/' markers) in seconds within a segment."""
    parts = [p.strip() for p in seg_text.split("/")]
    if len(parts) == 1:
        return [(parts[0], 0.0, None)]
    chunks = []
    acc = ""
    n_tokens = len(ph_known)
    prev_t = 0.0
    for i, p in enumerate(parts):
        if i < len(parts) - 1:
            acc = (acc + " " + p).strip()
            k = len(_tok.known(_tok.phonemize(acc, lang)))
            k = min(max(k, 1), n_tokens - 1)
            t = float(times[k][0])
            chunks.append((p, prev_t, t))
            prev_t = t
        else:
            chunks.append((p, prev_t, None))
    return chunks


def build_line(ln):
    spk = ln["speaker"]
    vc = script.VOICES[spk]
    pieces = []
    seg_meta = []
    phon = []
    t0 = 0.0
    for seg in ln["segments"]:
        text_tts = seg["text"].replace(" / ", " ").replace("/", " ")
        speed = seg.get("speed", vc["speed"])
        audio, ph, times = synth(text_tts, vc["voice"], vc["lang"], speed)
        audio, times = trim(audio, times)
        dur = len(audio) / TTS_SR
        subs = split_subs(seg["text"], vc["lang"], ph, times)
        chunks = []
        for (txt, a, b) in subs:
            chunks.append({"text": txt, "start": t0 + a, "end": t0 + (b if b is not None else dur)})
        for c, (a, b) in zip(ph, times):
            phon.append({"p": c, "s": round(t0 + float(a), 4), "e": round(t0 + float(b), 4)})
        seg_meta.append({"text": seg["text"].replace(" / ", " ").replace("/", " "), "start": t0, "end": t0 + dur, "subs": chunks})
        pieces.append(audio)
        pause = seg["pause"]
        pieces.append(np.zeros(int(pause * TTS_SR), dtype=np.float32))
        t0 += dur + pause
    # drop the trailing pause from the audio but remember it as tail
    tail = ln["segments"][-1]["pause"]
    audio = np.concatenate(pieces[:-1])
    sf.write(os.path.join(OUT, ln["id"] + ".wav"), audio, TTS_SR)
    meta = {
        "id": ln["id"], "speaker": spk, "duration": len(audio) / TTS_SR, "tail": tail,
        "segments": seg_meta, "phonemes": phon,
    }
    with open(os.path.join(OUT, ln["id"] + ".json"), "w") as f:
        json.dump(meta, f, indent=1)
    return meta


def build_walla():
    os.makedirs(os.path.join(OUT, "walla"), exist_ok=True)
    out = []
    for i, (v, text) in enumerate(script.WALLA):
        lang = "en-gb" if v.startswith("b") else "en-us"
        audio, ph, times = synth(text, v, lang, 1.08)
        audio, times = trim(audio, times)
        p = os.path.join(OUT, "walla", f"w{i:02d}.wav")
        sf.write(p, audio, TTS_SR)
        out.append(p)
    return out


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for scene, ln in script.all_lines():
        if only and ln["id"] not in only:
            continue
        m = build_line(ln)
        print(f"{ln['id']} {ln['speaker']:9s} {m['duration']:6.2f}s")
    if not only:
        build_walla()
