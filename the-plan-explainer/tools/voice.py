#!/usr/bin/env python3
"""Narration: script.json -> build/voice/*.wav + build/timeline.{json,js}

Each line is spoken with Kokoro TTS, then transcribed back with Whisper to get
per-word timings (used for captions, kinetic text, bleeps and the hard cut at
the end). Results are cached per line, so editing one line only regenerates
that line.

Models are downloaded on first run into $PLAN_MODEL_DIR
(default ~/.cache/the-plan-explainer).
"""
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.request

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
VOICE_DIR = os.path.join(BUILD, "voice")
MODEL_DIR = os.environ.get("PLAN_MODEL_DIR", os.path.expanduser("~/.cache/the-plan-explainer"))
FPS = 30
SR = 24000
CACHE_VERSION = 3

MODELS = {
    "kokoro-v1.0.onnx": "https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://huggingface.co/fastrtc/kokoro-onnx/resolve/main/voices-v1.0.bin",
}

# Whisper writes numbers as digits; map them back so they line up with the script.
NUMBER_WORDS = {"20": "twenty", "50": "fifty", "100": "hundred", "1": "one", "2": "two"}


def model_path(name):
    os.makedirs(MODEL_DIR, exist_ok=True)
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        print(f"  downloading {name} ...", flush=True)
        urllib.request.urlretrieve(MODELS[name], path + ".part")
        os.replace(path + ".part", path)
    return path


def norm(word):
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    return NUMBER_WORDS.get(w, w)


def trim(audio, lead=0.03, tail=0.08):
    """Strip Kokoro's leading/trailing silence, keeping a small margin."""
    env = np.abs(audio)
    thresh = max(env.max() * 0.02, 1e-4)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return audio
    a = max(0, idx[0] - int(lead * SR))
    b = min(len(audio), idx[-1] + int(tail * SR))
    return audio[a:b]


def align(tokens, asr_words, dur):
    """Give every script token a (start, end) using the Whisper words as anchors."""
    script_norm = [norm(t) for t in tokens]
    asr_norm = [norm(w["w"]) for w in asr_words]
    times = [None] * len(tokens)
    sm = difflib.SequenceMatcher(a=script_norm, b=asr_norm, autojunk=False)
    for block in sm.get_opcodes():
        tag, i1, i2, j1, j2 = block
        if tag == "equal" or (tag == "replace" and (i2 - i1) == (j2 - j1)):
            for k in range(i2 - i1):
                w = asr_words[j1 + k]
                times[i1 + k] = [w["s"], w["e"]]
        elif tag == "replace" and j2 > j1:
            # n script tokens spoken as m whisper tokens: spread them over that span
            s, e = asr_words[j1]["s"], asr_words[j2 - 1]["e"]
            n = i2 - i1
            for k in range(n):
                times[i1 + k] = [s + (e - s) * k / n, s + (e - s) * (k + 1) / n]
    # Fill gaps (tokens Whisper skipped) by interpolating between neighbours.
    i = 0
    while i < len(tokens):
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < len(tokens) and times[j] is None:
            j += 1
        left = times[i - 1][1] if i > 0 else 0.0
        right = times[j][0] if j < len(tokens) else dur
        if right - left < 0.08 * (j - i) and i > 0:
            left = times[i - 1][0]
            times[i - 1][1] = left + (right - left) / (j - i + 1)
            left = times[i - 1][1]
        for k in range(i, j):
            frac0 = (k - i) / (j - i)
            frac1 = (k - i + 1) / (j - i)
            times[k] = [left + (right - left) * frac0, left + (right - left) * frac1]
        i = j
    return [[round(s, 3), round(e, 3)] for s, e in times]


STOPWORDS = {"the", "a", "an", "to", "of", "and", "or", "for", "with", "your", "you", "my", "in", "on", "at",
             "that", "is", "i", "i'm", "i'll", "if", "but", "so", "about", "any", "have", "it", "its", "be",
             "as", "how", "when", "from", "by", "are", "has", "all"}


def pages_for(tokens, max_chars=52):
    """Split a line into caption pages (dynamic programming over break points).

    Breaking after punctuation is cheap, breaking right after "the", "your" and
    friends is expensive, and one- or two-word pages cost extra.
    """
    def bare(tok):
        return re.sub(r"[^a-z']", "", tok.lower())

    def ends_sentence(tok):
        return tok[-1] in ".?!" and not re.fullmatch(r"(?:[A-Za-z]\.)+", tok)

    def width(i, j):
        return sum(len(t) for t in tokens[i:j]) + (j - i - 1)

    def cost(i, j):
        words = j - i
        c = 10.0 + (6 if words < 3 else 0) + (4 if words == 1 else 0)
        last = tokens[j - 1]
        # don't strand the first word or two of a new sentence at the end of a page
        inner = [k for k in range(i, j - 1) if ends_sentence(tokens[k])]
        if inner and j - 1 - inner[-1] <= 2 and not ends_sentence(last):
            c += 6
        if j < len(tokens):
            if ends_sentence(last) or last.endswith("..."):
                c -= 8
            elif last[-1] in ",;:":
                c -= 5
            if bare(last) in STOPWORDS:
                c += 10
            if bare(tokens[j]) in STOPWORDS:
                c -= 1.5
        return c

    n = len(tokens)
    best = [0.0] + [float("inf")] * n
    prev = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j - 1, -1, -1):
            if j - i > 1 and width(i, j) > max_chars:
                break
            c = best[i] + cost(i, j)
            if c < best[j]:
                best[j], prev[j] = c, i
    pages, j = [], n
    while j > 0:
        pages.append([prev[j], j])
        j = prev[j]
    return pages[::-1]


def mouth_envelope(audio):
    hop = SR // FPS
    n = int(np.ceil(len(audio) / hop))
    rms = np.array([np.sqrt(np.mean(audio[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(n)])
    ref = np.percentile(rms, 92) + 1e-9
    env = np.clip(rms / ref, 0, 1)
    env = np.convolve(env, [0.25, 0.5, 0.25], mode="same")
    return [int(round(v * 100)) for v in env]


def censor(word):
    letters = re.sub(r"[^A-Za-z]", "", word)
    return word[0] + "*" * (len(letters) - 1) + word[len(letters):] if letters else word


def main():
    with open(os.path.join(ROOT, "script.json")) as f:
        script = json.load(f)
    os.makedirs(VOICE_DIR, exist_ok=True)

    tts = None
    asr = None
    out_lines = {}
    order = []
    t = float(script.get("preroll", 3.0))

    for line in script["lines"]:
        lid, who = line["id"], line["who"]
        v = script["voices"][who]
        say = line.get("say", line["text"])
        key = hashlib.sha1(json.dumps([CACHE_VERSION, v["voice"], v["speed"], say]).encode()).hexdigest()[:16]
        wav_path = os.path.join(VOICE_DIR, f"{lid}.wav")
        meta_path = os.path.join(VOICE_DIR, f"{lid}.json")

        meta = None
        if os.path.exists(wav_path) and os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            if meta.get("key") != key:
                meta = None

        if meta is None:
            if tts is None:
                from kokoro_onnx import Kokoro
                tts = Kokoro(model_path("kokoro-v1.0.onnx"), model_path("voices-v1.0.bin"))
            if asr is None:
                from faster_whisper import WhisperModel
                asr = WhisperModel("small.en", device="cpu", compute_type="int8",
                                   download_root=os.path.join(MODEL_DIR, "whisper"))
            print(f"  voicing {lid}: {say}", flush=True)
            audio, sr = tts.create(say, voice=v["voice"], speed=v["speed"], lang="en-us")
            assert sr == SR
            audio = trim(np.asarray(audio, dtype=np.float32))
            sf.write(wav_path, audio, SR, subtype="PCM_16")
            segs, _ = asr.transcribe(resample_poly(audio, 2, 3).astype(np.float32),
                                     word_timestamps=True, language="en", beam_size=5)
            words = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)}
                     for s in segs for w in s.words]
            meta = {"key": key, "heard": " ".join(w["w"] for w in words), "asr": words}
            with open(meta_path, "w") as f:
                json.dump(meta, f, indent=1)

        audio, _ = sf.read(wav_path, dtype="float32")
        dur = len(audio) / SR
        tokens = line["text"].split()
        times = align(tokens, meta["asr"], dur)

        bleeps = []
        shown = list(tokens)
        for b in line.get("bleep", []):
            b = {"word": b} if isinstance(b, str) else b
            for i, tok in enumerate(tokens):
                if norm(tok) == norm(b["word"]):
                    # Whisper's word edges drift by ~0.1s, so pad generously without a measured 'at'
                    span = b.get("at") or [times[i][0] - 0.06, times[i][1] + 0.16]
                    bleeps.append([max(0.0, span[0]), min(dur, span[1])])
                    shown[i] = censor(tok)
                    # keep caption highlight in step with the bleep
                    times[i] = [bleeps[-1][0], bleeps[-1][1]]
                    if i + 1 < len(tokens) and times[i + 1][0] < times[i][1]:
                        times[i + 1][0] = min(times[i][1], times[i + 1][1] - 0.05)

        cut = None
        if "cut" in line:
            c = line["cut"]
            target = norm(c["word"])
            idx = max(i for i, tok in enumerate(tokens) if norm(tok) == target)
            cut = round(c["at"] if "at" in c else times[idx][0] + c.get("after", 0.08), 3)
            shown[idx] = tokens[idx][0] + "—"
            times[idx] = [min(times[idx][0], cut - 0.05), cut]
            dur = cut

        start = round(t, 3)
        end = round(t + dur, 3)
        out_lines[lid] = {
            "who": who,
            "start": start,
            "end": end,
            "text": line["text"],
            "heard": meta["heard"],
            "words": [{"w": shown[i], "s": round(start + times[i][0], 3), "e": round(start + min(times[i][1], dur), 3)}
                      for i in range(len(tokens))],
            "pages": pages_for(tokens),
            "mouth": mouth_envelope(audio[: int(dur * SR)]),
            "bleeps": [[round(a, 3), round(b, 3)] for a, b in bleeps],
            "cut": cut,
            "wav": f"build/voice/{lid}.wav",
        }
        order.append(lid)
        t = end + float(line.get("pause", 0.4))

    duration = round(t + float(script.get("tail", 1.5)), 3)
    timeline = {"fps": FPS, "duration": duration, "preroll": script.get("preroll", 3.0),
                "voices": script["voices"], "order": order, "lines": out_lines}
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump(timeline, f, indent=1)
    with open(os.path.join(BUILD, "timeline.js"), "w") as f:
        f.write("// generated by tools/voice.py, do not edit\nwindow.TIMELINE = ")
        json.dump(timeline, f, separators=(",", ":"))
        f.write(";\n")

    print(f"timeline: {len(order)} lines, {duration:.1f}s")
    mismatches = 0
    for lid in order:
        L = out_lines[lid]
        a = [norm(w) for w in L["text"].split()]
        b = [norm(w) for w in L["heard"].split()]
        ratio = difflib.SequenceMatcher(a=a, b=b).ratio()
        if ratio < 0.85:
            mismatches += 1
            print(f"  check {lid} ({ratio:.2f}) heard: {L['heard']}")
    if mismatches == 0:
        print("  all lines transcribe back cleanly")


if __name__ == "__main__":
    sys.exit(main())
