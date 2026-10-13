"""
Voice acting for A NEW COMMANDMENT.

Uses Kokoro-82M (ONNX, timestamped export) which reports per-phoneme durations,
so every line comes with phoneme timings that drive the lip-sync.

Casting (Kokoro voice ids):
  narrator  bm_george   classic British storyteller
  jesus     am_michael  warm, unhurried
  paul      bm_lewis    deep, weathered British (old Paul)
  saul      bm_lewis    same man 34 years younger: brighter, faster, harder
  asher     am_fenrir   intense, mid-range
  yosef     bm_fable    a gentle father, lowered and given a fuller chest (F0 about 105 Hz)
  phoebe    bf_emma     warm, clear reader of Paul's letter in Rome
  guard     am_onyx     gruff and low
  child     a blend of af_heart and am_puck, lifted into a boy's register (F0 about 195 Hz)
            with only a small formant lift, so it sounds young rather than sped-up
  epic      bm_daniel   the closing voice: a deep, warm British reader (F0 about 113 Hz)
"""
import hashlib
import json
import os
import subprocess

import numpy as np
import soundfile as sf

SR = 24000
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work"))
MODELS = os.environ.get("BFE_MODELS", os.path.join(WORK, "models"))
CACHE = os.path.join(WORK, "voice_cache")

CAST = {
    "narrator": dict(voice="bm_george"),
    "jesus": dict(voice="am_michael"),
    "paul": dict(voice="bm_lewis"),
    "saul": dict(voice="bm_lewis", pitch=1.06, speed_mul=1.06),
    "asher": dict(voice="am_fenrir"),
    "yosef": dict(voice="bm_fable", pitch=0.84, formant=0.93),
    "phoebe": dict(voice="bf_emma"),
    "guard": dict(voice="am_onyx", pitch=0.97),
    "child": dict(voice="af_heart*0.55+am_puck*0.45", pitch=1.08, formant=1.04, speed_mul=0.92),
    "epic": dict(voice="bm_daniel", pitch=0.88, formant=0.95),
}

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro

        _kokoro = Kokoro(os.path.join(MODELS, "kokoro-ts.onnx"), os.path.join(MODELS, "voices-v1.0.bin"))
        # this export names its timing output "durations"; the library looks for "duration"
        _kokoro.has_timings = True
    return _kokoro


def _ffmpeg_filter(x, af):
    """Run a mono float signal through an ffmpeg audio filter chain."""
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
         "-af", af, "-f", "f32le", "-ar", str(SR), "-ac", "1", "pipe:1"],
        input=x.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def _trim(x, timings, thresh=0.004, keep=0.06):
    """Trim leading/trailing near-silence; shift timings accordingly."""
    env = np.abs(x)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return x, timings
    a = max(0, idx[0] - int(keep * SR))
    b = min(len(x), idx[-1] + int(keep * SR))
    shift = a / SR
    t2 = [(p, max(0.0, s - shift), max(0.0, e - shift)) for (p, s, e) in timings]
    return x[a:b], t2


def synth(who, text, speed=1.0, fx=None):
    """Return (audio float32 mono @24k, phoneme timings [(ph, start, end)]) for one line."""
    cast = CAST[who]
    sp = speed * cast.get("speed_mul", 1.0)
    key = json.dumps([who, cast, text, round(sp, 3), fx, 3], sort_keys=True)
    h = hashlib.sha1(key.encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    wav_p = os.path.join(CACHE, h + ".wav")
    js_p = os.path.join(CACHE, h + ".json")
    if os.path.exists(wav_p) and os.path.exists(js_p):
        x, _ = sf.read(wav_p, dtype="float32")
        return x, [tuple(t) for t in json.load(open(js_p))]

    k = kokoro()
    voice = cast["voice"]
    if "+" in voice:
        # weighted blend of voice styles, e.g. "af_heart*0.55+am_puck*0.45"
        parts = [v.split("*") for v in voice.split("+")]
        voice = sum(float(w) * k.get_voice_style(name) for name, w in parts).astype(np.float32)
    audio, sr, spoken = k.create_timed(text, voice=voice, speed=sp, lang="en-us",
                                       sentence_pause=0.22, clause_pause=0.08)
    assert sr == SR
    x = np.asarray(audio, dtype=np.float32)
    tim = [(t.phoneme, float(t.start), float(t.end)) for t in spoken]

    pitch = cast.get("pitch")
    if pitch:
        # formant: factor for the vocal-tract resonances (1 = keep the voice's own size).
        # Shift everything by the formant factor first, then move only the pitch the rest of the way.
        form = cast.get("formant", 1.0)
        if abs(form - 1.0) > 1e-3:
            x = _ffmpeg_filter(x, f"rubberband=pitch={form}:formant=shifted:transients=smooth")
        rest = pitch / form
        if abs(rest - 1.0) > 1e-3:
            x = _ffmpeg_filter(x, f"rubberband=pitch={rest}:formant=preserved:transients=smooth")

    if fx == "tremble":
        # held-back tears: slow pitch waver + slight amplitude flutter
        x = _ffmpeg_filter(x, "vibrato=f=5.2:d=0.06,tremolo=f=4.6:d=0.12")
    elif fx == "child_whisper":
        # breathy: add envelope-following high-passed noise, soften the voiced part
        env = np.convolve(np.abs(x), np.ones(240) / 240, mode="same")
        rng = np.random.default_rng(7)
        n = rng.standard_normal(len(x)).astype(np.float32)
        n = _ffmpeg_filter(n, "highpass=f=1800,lowpass=f=7000")
        x = 0.55 * x + 2.2 * n * env
    x, tim = _trim(x, tim)
    # normalise speech level per line (peak-safe RMS normalisation)
    rms = np.sqrt(np.mean(x[np.abs(x) > 0.01] ** 2)) if np.any(np.abs(x) > 0.01) else 0.05
    x = x * (0.11 / max(rms, 1e-4))
    pk = np.max(np.abs(x))
    if pk > 0.95:
        x *= 0.95 / pk
    sf.write(wav_p, x, SR)
    json.dump(tim, open(js_p, "w"))
    return x, tim


# ----------------------------------------------------------------------------
# Lip-sync: phonemes -> mouth curves (open, wide, closed) sampled at RATE Hz
# ----------------------------------------------------------------------------
RATE = 60

# (open 0..1, wide -1 round .. +1 spread)
VISEME = {}
for ch in "aɑæʌ":
    VISEME[ch] = (0.95, 0.15)
for ch in "ɐ":
    VISEME[ch] = (0.7, 0.1)
for ch in "eɛ":
    VISEME[ch] = (0.6, 0.55)
for ch in "ɪiᵻ":
    VISEME[ch] = (0.35, 0.8)
for ch in "oɔ":
    VISEME[ch] = (0.7, -0.75)
for ch in "ʊuw":
    VISEME[ch] = (0.35, -1.0)
for ch in "ɚɜəɝ":
    VISEME[ch] = (0.45, -0.25)
for ch in "ɹr":
    VISEME[ch] = (0.3, -0.6)
for ch in "ʃʒʧʤ":
    VISEME[ch] = (0.3, -0.7)
for ch in "fv":
    VISEME[ch] = (0.12, 0.3)
for ch in "θð":
    VISEME[ch] = (0.25, 0.3)
for ch in "sztdnlkgŋɡj":
    VISEME[ch] = (0.2, 0.35)
for ch in "hç":
    VISEME[ch] = (0.4, 0.0)
CLOSED = set("mbp")


def mouth_curves(x, timings, rate=RATE):
    """Build per-frame mouth parameters for one clip."""
    n = int(np.ceil(len(x) / SR * rate)) + 1
    open_t = np.zeros(n)
    wide_t = np.zeros(n)
    close_t = np.zeros(n)
    w_acc = np.zeros(n) + 1e-6
    for ph, s, e in timings:
        if ph in CLOSED:
            a, b = int(s * rate), int(np.ceil(e * rate))
            close_t[a:b + 1] = 1.0
            continue
        v = VISEME.get(ph)
        if v is None:
            continue
        a, b = int(s * rate), max(int(s * rate) + 1, int(np.ceil(e * rate)))
        for i in range(a, min(b + 1, n)):
            open_t[i] = max(open_t[i], v[0])
            wide_t[i] += v[1]
            w_acc[i] += 1
    wide_t = wide_t / w_acc
    # loudness envelope scales openness (quiet = smaller mouth)
    hop = SR // rate
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(x) else 0 for i in range(n)])
    loud = np.clip(rms / 0.12, 0, 1.3) ** 0.6
    open_t = open_t * (0.35 + 0.75 * loud)
    open_t[rms < 0.006] = 0
    # coarticulation smoothing (attack faster than release)
    def smooth(arr, up=0.55, down=0.35):
        out = np.zeros_like(arr)
        v = 0.0
        for i, a in enumerate(arr):
            k = up if a > v else down
            v = v + (a - v) * k
            out[i] = v
        return out
    o = smooth(open_t)
    w = smooth(wide_t, 0.4, 0.4)
    c = smooth(close_t, 0.7, 0.5)
    o = o * (1 - 0.85 * c)
    return dict(open=np.round(o, 3).tolist(), wide=np.round(w, 3).tolist(), close=np.round(c, 3).tolist(),
                loud=np.round(np.clip(rms / 0.12, 0, 1.5), 3).tolist())
