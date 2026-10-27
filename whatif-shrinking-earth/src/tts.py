"""Synthesize every line of the screenplay with Kokoro and record word timings.

Output: build/voice/<id>.wav (48 kHz mono, loudness-normalized) and
build/voice/lines.json with per-word timings and phonemes for lip-sync.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
import pyloudnorm
import soundfile as sf
from scipy.signal import resample_poly

import paths
from script import LINES, VOICES

KSR = 24000
TARGET_LUFS = -20.0


def trim(audio, sr, words, thresh_db=-50.0, pad=0.03, pad_end=0.10):
    """Trim leading/trailing silence; shift word timings to match."""
    env = np.abs(audio)
    peak = env.max() + 1e-9
    above = np.where(env > peak * 10 ** (thresh_db / 20))[0]
    if len(above) == 0:
        return audio, words
    a = max(0, above[0] - int(pad * sr))
    b = min(len(audio), above[-1] + int(pad_end * sr))
    off = a / sr
    out = []
    for w in words:
        out.append(dict(w, start=max(0.0, w["start"] - off), end=max(0.0, w["end"] - off)))
    return audio[a:b], out


def pitch_shift(audio, sr, semitones, formant):
    if abs(semitones) < 1e-3:
        return audio
    ratio = 2 ** (semitones / 12.0)
    with tempfile.TemporaryDirectory() as td:
        src, dst = os.path.join(td, "a.wav"), os.path.join(td, "b.wav")
        sf.write(src, audio, sr, subtype="FLOAT")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
             f"rubberband=pitch={ratio:.5f}:formant={formant}:pitchq=quality:transients=smooth",
             "-ar", str(sr), "-c:a", "pcm_f32le", dst],
            check=True)
        out, _ = sf.read(dst, dtype="float32")
    if out.ndim > 1:
        out = out.mean(axis=1)
    return out[: len(audio)] if len(out) >= len(audio) else np.pad(out, (0, len(audio) - len(out)))


def synth_chunk(pipe, text, voice, speed):
    """Synthesize text; '{0.8}' markers insert silence between two words."""
    import re
    marks = []
    parts = re.split(r"\{([0-9.]+)\}", text)
    clean = ""
    for i, ptxt in enumerate(parts):
        if i % 2 == 0:
            clean += ptxt
        else:
            nwords = len(re.findall(r"[A-Za-z0-9']+", clean))
            marks.append((nwords, float(ptxt)))
    clean = re.sub(r"\s+", " ", clean).strip()
    a, words = _synth(pipe, clean, voice, speed)
    for nw, pause in reversed(marks):
        if nw <= 0 or nw >= len(words):
            continue
        cut = 0.5 * (words[nw - 1]["end"] + words[nw]["start"])
        k = int(cut * KSR)
        a = np.concatenate([a[:k], np.zeros(int(pause * KSR), np.float32), a[k:]])
        for w in words[nw:]:
            w["start"] += pause
            w["end"] += pause
    return a, words


def _synth(pipe, text, voice, speed):
    audio, words, t_off = [], [], 0.0
    for r in pipe(text, voice=voice, speed=speed):
        a = r.audio.numpy().astype(np.float32)
        for t in (r.tokens or []):
            if t.start_ts is None or t.end_ts is None:
                continue
            if not any(ch.isalnum() for ch in t.text):
                continue
            words.append({"text": t.text, "start": t_off + float(t.start_ts),
                          "end": t_off + float(t.end_ts), "ph": t.phonemes or ""})
        audio.append(a)
        t_off += len(a) / KSR
    return np.concatenate(audio), words


def main(only=None):
    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a")
    pipe_b = KPipeline(lang_code="b")  # British G2P for the narrator
    meter = pyloudnorm.Meter(paths.SR)
    meta_path = os.path.join(paths.VOICE, "lines.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

    for lid, speaker, chunks, spd, gain_db in LINES:
        if only and lid not in only:
            continue
        voice, base_speed, semis = VOICES[speaker]
        p = pipe_b if voice.startswith("b") else pipe
        line_audio, line_words, chunk_spans, t = [], [], [], 0.0
        for text, pause in chunks:
            a, words = synth_chunk(p, text, voice, base_speed * spd)
            a, words = trim(a, KSR, words)
            # 5 ms fades against clicks
            f = int(0.005 * KSR)
            a[:f] *= np.linspace(0, 1, f)
            a[-f:] *= np.linspace(1, 0, f)
            for w in words:
                line_words.append(dict(w, start=w["start"] + t, end=w["end"] + t))
            chunk_spans.append([t, t + len(a) / KSR])
            line_audio.append(a)
            t += len(a) / KSR
            if pause > 0:
                line_audio.append(np.zeros(int(pause * KSR), np.float32))
                t += pause
        audio = np.concatenate(line_audio)
        formant = "shifted" if semis > 0 else "preserved"
        audio = pitch_shift(audio, KSR, semis, formant)
        audio = resample_poly(audio, paths.SR // 1000, KSR // 1000).astype(np.float32)
        # loudness normalize (pad very short clips for the meter)
        probe = audio if len(audio) > paths.SR * 0.5 else np.pad(audio, (0, int(paths.SR * 0.5)))
        lufs = meter.integrated_loudness(probe)
        if np.isfinite(lufs):
            audio *= 10 ** ((TARGET_LUFS + gain_db - lufs) / 20)
        peak = np.abs(audio).max()
        if peak > 0.89:
            audio *= 0.89 / peak
        sf.write(os.path.join(paths.VOICE, f"{lid}.wav"), audio, paths.SR, subtype="PCM_16")
        meta[lid] = {"speaker": speaker, "dur": len(audio) / paths.SR, "words": line_words,
                     "chunks": chunk_spans, "text": re.sub(r"\s*\{[0-9.]+\}\s*", " ", " ".join(c[0] for c in chunks))}
        print(f"{lid} {speaker:8s} {len(audio)/paths.SR:6.2f}s  {meta[lid]['text'][:60]}", flush=True)
        json.dump(meta, open(meta_path, "w"), indent=1)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
