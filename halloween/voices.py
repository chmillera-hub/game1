"""Voice acting: synthesize every scripted line with Kokoro TTS.

Output per line (in build/voices/):
  <id>.wav   48 kHz mono float
  <id>.json  {"dur", "words": [{"text", "start", "end", "mark", "chunk", "ph"}]}
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import warnings

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import CAST, SCRIPT  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "voices")
SR = 48000
DEFAULT_PAUSE = 0.35


def parse_chunks(text):
    """'a | b |0.8| c' -> [(chunk_text, pause_after), ...]"""
    parts = re.split(r"\s*\|([0-9.]*)\|?\s*", text)
    chunks = []
    for i in range(0, len(parts), 2):
        t = parts[i].strip()
        pause = DEFAULT_PAUSE
        if i + 1 < len(parts) and parts[i + 1]:
            pause = float(parts[i + 1])
        if t:
            chunks.append((t, pause))
    return chunks


def display_words(chunk):
    """Split a chunk into display words, pulling out ^/_ marks."""
    words = []
    for w in chunk.split():
        mark = None
        m = re.match(r"^([\"'(]*)([\^_])(.*)$", w)
        if m:
            mark = "hi" if m.group(2) == "^" else "lo"
            w = m.group(1) + m.group(3)
        words.append((w, mark))
    return words


def letters(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def trim_bounds(a, sr, thresh=0.006, pad_in=0.03, pad_out=0.09):
    env = np.abs(a)
    win = int(sr * 0.01)
    if len(env) > win:
        env = np.convolve(env, np.ones(win) / win, mode="same")
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return 0, len(a)
    s = max(0, idx[0] - int(pad_in * sr))
    e = min(len(a), idx[-1] + int(pad_out * sr))
    return s, e


def pitch_shift(a, semis, formant):
    if abs(semis) < 1e-3:
        return a
    tmp_in = os.path.join(OUT, "_ps_in.wav")
    tmp_out = os.path.join(OUT, "_ps_out.wav")
    sf.write(tmp_in, a, SR, subtype="FLOAT")
    ratio = 2 ** (semis / 12.0)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_in, "-af",
         f"rubberband=pitch={ratio:.5f}:formant={formant}:pitchq=quality:transients=smooth",
         "-c:a", "pcm_f32le", tmp_out], check=True)
    b, _ = sf.read(tmp_out, dtype="float32")
    if b.ndim > 1:
        b = b[:, 0]
    if len(b) < len(a):
        b = np.pad(b, (0, len(a) - len(b)))
    return b[: len(a)]


def synth_line(pipe, lid, who, text, opts):
    cast = CAST[who]
    spoken = opts.get("tts", text)
    key = hashlib.md5(json.dumps([cast, spoken, text, DEFAULT_PAUSE, 3]).encode()).hexdigest()[:12]
    jpath = os.path.join(OUT, f"{lid}.json")
    wpath = os.path.join(OUT, f"{lid}.wav")
    if os.path.exists(jpath) and os.path.exists(wpath):
        with open(jpath) as f:
            if json.load(f).get("key") == key:
                return
    pieces, words, t = [], [], 0.0
    for ci, (chunk, pause) in enumerate(parse_chunks(spoken)):
        dwords = display_words(chunk)
        tts_text = " ".join(w for w, _ in dwords)
        auds, toks = [], []
        off = 0.0
        for r in pipe(tts_text, voice=cast["voice"], speed=cast["speed"]):
            a = r.audio.numpy()
            for tk in r.tokens:
                if tk.start_ts is None:
                    continue
                toks.append((tk.text, off + tk.start_ts, off + tk.end_ts, tk.phonemes or ""))
            auds.append(a)
            off += len(a) / 24000.0
        a24 = np.concatenate(auds)
        a = resample_poly(a24, 2, 1).astype(np.float32)
        s, e = trim_bounds(a, SR)
        a = a[s:e]
        shift = s / SR
        # align tokens -> display words by consuming letters
        ti = 0
        for w, mark in dwords:
            need = letters(w)
            got, st, en, ph = "", None, None, []
            while ti < len(toks) and (len(got) < len(need) or not need):
                tx, ts, te, tp = toks[ti]
                ti += 1
                lt = letters(tx)
                if not lt and need:
                    continue  # punctuation token
                st = ts if st is None else st
                en = te
                got += lt
                ph.append(tp)
                if not need:
                    break
            if st is None:  # pure punctuation word, glue to previous
                st = en = (words[-1]["end"] - t) if words else 0.0
            words.append(dict(text=w, start=round(t + max(0.0, st - shift), 3),
                              end=round(t + max(0.0, en - shift), 3), mark=mark,
                              chunk=ci, ph=" ".join(ph)))
        pieces.append(a)
        t += len(a) / SR
        pieces.append(np.zeros(int(pause * SR), np.float32))
        t += pause
    pieces = pieces[:-1]  # no trailing pause
    audio = np.concatenate(pieces)
    formant = "shifted" if cast["pitch"] >= 2.5 else "preserved"
    audio = pitch_shift(audio, cast["pitch"], formant)
    peak = np.max(np.abs(audio)) + 1e-9
    audio = (audio / peak * 0.89).astype(np.float32)
    dur = len(audio) / SR
    for w in words:
        w["end"] = min(w["end"], dur)
    sf.write(wpath, audio, SR, subtype="FLOAT")
    with open(jpath, "w") as f:
        json.dump(dict(key=key, id=lid, who=who, text=text, dur=round(dur, 3), words=words), f, indent=1)
    print(f"{lid:4s} {who:8s} {dur:5.2f}s  {text[:60]}")


def main():
    os.makedirs(OUT, exist_ok=True)
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    only = set(sys.argv[1:])
    for item in SCRIPT:
        if item[0] != "line":
            continue
        _, lid, who, text, opts = item
        if only and lid not in only:
            continue
        synth_line(pipe, lid, who, text, opts)


if __name__ == "__main__":
    main()
