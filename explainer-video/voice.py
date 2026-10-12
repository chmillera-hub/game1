"""Voice lines: synthesis with Kokoro, then word timing + QA with Whisper."""
import hashlib
import json
import os
import re
import difflib

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from script import VOICES

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
VOICE_DIR = os.path.join(BUILD, "voice")
MODEL_DIR = os.environ.get("KOKORO_MODEL_DIR", os.path.join(BUILD, "models"))
SR = 48000  # project sample rate

_kokoro = None
_whisper = None


def _models():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"),
                         os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _kokoro


def _asr():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _whisper


NUMS = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen".split()


def norm(w):
    w = re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))
    return NUMS[int(w)] if w.isdigit() and int(w) < len(NUMS) else w


def trim(a, sr, db=-42, pad=0.04):
    env = np.abs(a)
    thr = 10 ** (db / 20) * max(env.max(), 1e-6)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(pad * sr))
    e = min(len(a), idx[-1] + int(pad * sr * 2))
    return a[s:e]


def _align(tokens, asr_words, dur):
    """Give every script token a (start, end) using Whisper word times."""
    n = len(tokens)
    times = [None] * n
    a = [norm(t) for t in tokens]
    b = [norm(w[0]) for w in asr_words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = asr_words[blk.b + k][1:3]
    # fuzzy fill for replaced spans of the same length
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                times[i1 + k] = asr_words[j1 + k][1:3]
    # interpolate the gaps by character length
    known = [i for i in range(n) if times[i] is not None]
    if not known:
        tot = sum(len(t) + 1 for t in tokens)
        acc = 0.0
        for i, t in enumerate(tokens):
            s = acc / tot * dur
            acc += len(t) + 1
            times[i] = (s, acc / tot * dur)
        return times
    i = 0
    while i < n:
        if times[i] is not None:
            i += 1
            continue
        j = i
        while j < n and times[j] is None:
            j += 1
        t0 = times[i - 1][1] if i > 0 else 0.0
        t1 = times[j][0] if j < n else dur
        span = tokens[i:j]
        tot = sum(len(t) + 1 for t in span)
        acc = 0.0
        for k, t in enumerate(span):
            s = t0 + (t1 - t0) * acc / tot
            acc += len(t) + 1
            times[i + k] = (s, t0 + (t1 - t0) * acc / tot)
        i = j
    # make monotonic
    for i in range(1, n):
        if times[i][0] < times[i - 1][0]:
            times[i] = (times[i - 1][0], max(times[i][1], times[i - 1][0]))
    return [(float(s), float(e)) for s, e in times]


def map_caption(cap_tokens, say_tokens, say_times):
    """Map caption tokens onto spoken tokens by relative character position."""
    if [norm(t) for t in cap_tokens] == [norm(t) for t in say_tokens]:
        return say_times
    pos = []
    acc = 0
    tot = sum(len(t) + 1 for t in say_tokens)
    for t in say_tokens:
        pos.append((acc / tot, (acc + len(t)) / tot))
        acc += len(t) + 1
    xs = [p[0] for p in pos] + [1.0]
    ts = [s for s, _ in say_times] + [say_times[-1][1]]
    out = []
    acc = 0
    tot = sum(len(t) + 1 for t in cap_tokens)
    for t in cap_tokens:
        a = acc / tot
        b = (acc + len(t)) / tot
        out.append((float(np.interp(a, xs, ts)), float(np.interp(b, xs, ts))))
        acc += len(t) + 1
    return out


def line(who, text, say=None, speed=None):
    """Return (audio@SR float32, caption word timings, qa dict). Cached on disk."""
    voice, vspeed, _, _ = VOICES[who]
    speed = speed or vspeed
    spoken = say or text
    key = hashlib.sha1(f"{voice}|{speed}|{spoken}|v2".encode()).hexdigest()[:16]
    os.makedirs(VOICE_DIR, exist_ok=True)
    wav = os.path.join(VOICE_DIR, key + ".wav")
    meta = os.path.join(VOICE_DIR, key + ".json")
    if not os.path.exists(wav):
        kk = _models()
        a, sr = kk.create(spoken, voice=voice, speed=speed, lang="en-us")
        a = trim(np.asarray(a, dtype=np.float32), sr)
        a = resample_poly(a, SR // 8000, sr // 8000).astype(np.float32)
        sf.write(wav, a, SR)
    audio, _ = sf.read(wav, dtype="float32")
    if not os.path.exists(meta):
        a16 = resample_poly(audio, 1, 3).astype(np.float32)
        segs, _ = _asr().transcribe(a16, word_timestamps=True, beam_size=5)
        words = [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words]
        with open(meta, "w") as f:
            json.dump({"spoken": spoken, "asr": words}, f)
    with open(meta) as f:
        m = json.load(f)
    dur = len(audio) / SR
    say_tokens = spoken.split()
    say_times = _align(say_tokens, [tuple(w) for w in m["asr"]], dur)
    cap_tokens = text.split()
    cap_times = map_caption(cap_tokens, say_tokens, say_times)
    heard = " ".join(norm(w[0]) for w in m["asr"])
    want = " ".join(norm(t) for t in say_tokens)
    ratio = difflib.SequenceMatcher(a=want.split(), b=heard.split()).ratio()
    qa = {"heard": " ".join(w[0] for w in m["asr"]), "match": round(ratio, 3)}
    return audio, list(zip(cap_tokens, cap_times)), qa
