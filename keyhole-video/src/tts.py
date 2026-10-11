"""Kokoro TTS wrapper with per-phoneme timings (timestamped ONNX export) and a disk cache."""
import hashlib, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TTS_DIR = os.path.join(os.path.dirname(HERE), "tts")
CACHE = os.path.join(HERE, "cache_tts")
os.makedirs(CACHE, exist_ok=True)
SR = 24000

_k = None
_sess = None


def _load():
    global _k, _sess
    if _k is None:
        import onnxruntime as ort
        from kokoro_onnx import Kokoro
        _k = Kokoro(os.path.join(TTS_DIR, "kokoro-v1.0.onnx"), os.path.join(TTS_DIR, "voices-v1.0.bin"))
        so = ort.SessionOptions()
        so.intra_op_num_threads = 4
        _sess = ort.InferenceSession(os.path.join(TTS_DIR, "kokoro-timed.onnx"), so)
    return _k, _sess


def phonemize(text):
    k, _ = _load()
    return k.tokenizer.phonemize(text, "en-us")


def _style(voice, ntok):
    k, _ = _load()
    if isinstance(voice, dict):
        st = sum(w * k.voices[v][ntok] for v, w in voice.items())
    else:
        st = k.voices[voice][ntok]
    return np.asarray(st, dtype=np.float32).reshape(1, 256)


def synth(text, voice, speed=1.0, phonemes=None):
    """Return (audio float32 @24k, phones list of (char, t0, t1), phoneme string).
    Leading/trailing silence trimmed (phone times adjusted)."""
    key = hashlib.md5(json.dumps(["v2", text, voice, round(speed, 3), phonemes], sort_keys=True).encode()).hexdigest()
    fn = os.path.join(CACHE, key + ".npz")
    if os.path.exists(fn):
        z = np.load(fn, allow_pickle=True)
        return z["audio"], [tuple(p) for p in z["phones"].tolist()], str(z["ph"])
    k, sess = _load()
    ph = phonemes if phonemes is not None else k.tokenizer.phonemize(text, "en-us")
    toks = k.tokenizer.tokenize(ph)
    # keep the char list aligned with tokens (tokenize drops unknown chars)
    chars = [c for c in ph if c in k.tokenizer.vocab]
    assert len(chars) == len(toks), (len(chars), len(toks))
    out = sess.run(None, {
        "input_ids": np.array([[0, *toks, 0]], dtype=np.int64),
        "style": _style(voice, len(toks)),
        "speed": np.array([speed], dtype=np.float32),
    })
    audio = np.asarray(out[0]).ravel().astype(np.float32)
    dur = np.asarray(out[1]).ravel().astype(np.float64)
    edges = np.concatenate([[0], np.cumsum(np.round(dur))]) * 600.0 / SR
    # token i (1-based, after BOS) spans edges[i]..edges[i+1]
    phones = [(chars[i], float(edges[i + 1]), float(edges[i + 2])) for i in range(len(chars))]
    # trim silence
    env = np.abs(audio)
    thr = max(1e-4, env.max() * 0.012)
    idx = np.where(env > thr)[0]
    a0 = max(0, idx[0] - int(0.03 * SR)) if len(idx) else 0
    a1 = min(len(audio), idx[-1] + int(0.06 * SR)) if len(idx) else len(audio)
    audio = audio[a0:a1].copy()
    off = a0 / SR
    end = len(audio) / SR
    phones = [(c, min(max(0.0, t0 - off), end), min(max(0.0, t1 - off), end)) for c, t0, t1 in phones]
    fade = int(0.008 * SR)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    np.savez(fn, audio=audio, phones=np.array(phones, dtype=object), ph=ph)
    return audio, phones, ph
