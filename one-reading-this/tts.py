"""Synthesize every line with Piper and record sentence-level timings.

Output: build/voice/NNN.wav (44.1 kHz mono) and build/voice.json with, per beat,
the duration and a list of (text, t0, t1) segments used for subtitle and
music-cue timing.
"""
import json, os, re, subprocess, sys, wave
import numpy as np
from piper import PiperVoice, SynthesisConfig
from script import BEATS

VOICES = os.environ.get("VOICES", "voices")
OUT = "build/voice"
SR_OUT = 44100

CAST = {
    # model, length_scale, pitch (semitones), noise
    "N": ("en_GB-alan-medium", 1.08, -0.5, 0.55),
    "M": ("en_US-lessac-high", 1.02, 0.6, 0.62),
    "A": ("en_US-ryan-high", 1.13, -2.2, 0.6),
}
SENT_GAP = 0.24
TILDE_GAP = 0.42


def main():
    os.makedirs(OUT, exist_ok=True)
    voices = {}
    meta = []
    for i, b in enumerate(BEATS):
        spk = b["s"]
        model, ls, pitch, noise = CAST[spk]
        if model not in voices:
            voices[model] = PiperVoice.load(f"{VOICES}/{model}.onnx")
        v = voices[model]
        sr = v.config.sample_rate
        cfg = SynthesisConfig(length_scale=ls, noise_scale=noise, noise_w_scale=0.8)
        pieces = [p.strip() for p in b["t"].split("~")]
        audio = [np.zeros(int(0.05 * sr), np.float32)]
        segs = []
        t = 0.05
        for pi, piece in enumerate(pieces):
            if not piece:
                continue
            chunks = list(v.synthesize(piece, cfg))
            # map piper sentences back onto the text roughly by splitting on sentence ends
            sents = [s for s in re.split(r"(?<=[.?!])\s+", piece) if s]
            if len(sents) != len(chunks):
                sents = [piece] + [""] * (len(chunks) - 1)
            for ci, ch in enumerate(chunks):
                a = ch.audio_int16_array.astype(np.float32) / 32768.0
                a = trim(a, sr)
                segs.append([sents[ci], t, t + len(a) / sr])
                audio.append(a)
                t += len(a) / sr
                gap = SENT_GAP if ci < len(chunks) - 1 else 0
                if ci == len(chunks) - 1 and pi < len(pieces) - 1:
                    gap = TILDE_GAP
                audio.append(np.zeros(int(gap * sr), np.float32))
                t += gap
        audio.append(np.zeros(int(0.08 * sr), np.float32))
        a = np.concatenate(audio)
        raw = f"{OUT}/{i:03d}_raw.wav"
        write_wav(raw, a, sr)
        out = f"{OUT}/{i:03d}.wav"
        semis = pitch
        filt = f"rubberband=pitch={2 ** (semis / 12):.5f}:formant=preserved," if abs(semis) > 0.01 else ""
        eq = {"A": "equalizer=f=180:t=q:w=1:g=3,", "N": "equalizer=f=140:t=q:w=1:g=2,", "M": ""}[spk]
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                        f"{filt}{eq}aresample={SR_OUT}", "-ac", "1", out], check=True)
        dur = wav_len(out)
        # rubberband keeps tempo, so segment times stay valid; clamp to final length
        segs = [[s, min(t0, dur), min(t1, dur)] for s, t0, t1 in segs]
        meta.append(dict(i=i, dur=dur, segs=segs))
        print(f"{i:03d} {spk} {dur:5.2f}s  {b['t'][:60]}", flush=True)
    json.dump(meta, open("build/voice.json", "w"), indent=1)
    print("total voice", sum(m["dur"] for m in meta))


def trim(a, sr, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(0.02 * sr))
    e = min(len(a), idx[-1] + int(0.06 * sr))
    return a[s:e]


def write_wav(path, a, sr):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


if __name__ == "__main__":
    main()
