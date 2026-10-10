"""Render every dialogue line with Kokoro TTS, then build lip-sync envelopes.

Outputs
    build/vo/<id>.wav        48 kHz mono float WAV, edges trimmed
    build/vo/manifest.json   {id: {"char", "text", "dur"}}
    build/lipsync.json       {id: {"open": [...], "round": [...]}} one value per video frame (FPS);
                             RMS envelope + forced lip closures on m/b/p (faster-whisper words + espeak-ng)
    build/vo/bilabials.json  the closure times used, per line (QA)

Quill gets a light "android" treatment: a short static comb filter for a faint
metallic sheen plus a gentle band-limit, kept subtle so every word stays clear.
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FPS, KOKORO_MODEL, KOKORO_VOICES, LIPSYNC, SR, VO_DIR  # noqa: E402
from script_data import LINES, VOICES, WHISPER  # noqa: E402


def trim_silence(x, sr, thresh_db=-45.0, pad=0.03):
    frame = int(sr * 0.01)
    n = len(x) // frame
    if n == 0:
        return x
    rms = np.sqrt(np.mean(x[: n * frame].reshape(n, frame) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-12)
    idx = np.where(db > thresh_db)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] * frame - int(pad * sr))
    b = min(len(x), (idx[-1] + 1) * frame + int(pad * sr))
    return x[a:b]


def android_fx(x, sr):
    d = int(sr * 0.0011)
    comb = np.zeros_like(x)
    comb[d:] = x[:-d]
    y = x + 0.22 * comb
    # second, even shorter tap gives a faint "hollow" resonance
    d2 = int(sr * 0.00037)
    comb2 = np.zeros_like(x)
    comb2[d2:] = x[:-d2]
    y = y - 0.08 * comb2
    b, a = signal.butter(2, [95 / (sr / 2), 9000 / (sr / 2)], btype="band")
    y = signal.lfilter(b, a, y)
    return y


def whisperize(x, sr, amount=0.8, order=44, frame_ms=25.0, hop_ms=10.0, seed=5):
    """Turn speech into a whisper: per-frame LPC envelope driven by white noise
    instead of the voiced residual, blended with `1 - amount` of the dry voice
    (a little voicing keeps it intelligible)."""
    from scipy.linalg import solve_toeplitz
    rng = np.random.default_rng(seed)
    n, hop = int(sr * frame_ms / 1000), int(sr * hop_ms / 1000)
    win = np.hanning(n)
    pre = signal.lfilter([1, -0.92], [1], x)
    out = np.zeros(len(x) + n)
    norm = np.zeros(len(x) + n)
    for i in range(0, len(x) - n, hop):
        seg = pre[i:i + n] * win
        r = np.correlate(seg, seg, "full")[n - 1:n + order]
        if r[0] < 1e-9:
            continue
        r[0] *= 1.0001
        a = solve_toeplitz(r[:order], -r[1:order + 1])
        A = np.concatenate([[1.0], a])
        res = signal.lfilter(A, [1.0], seg)
        g = np.sqrt(np.mean(res ** 2))
        y = signal.lfilter([1.0], A, rng.standard_normal(n) * g) * win
        out[i:i + n] += y
        norm[i:i + n] += win ** 2
    out = out[: len(x)] / np.maximum(norm[: len(x)], 1e-3)
    out = signal.lfilter([1], [1, -0.92], out)
    out = signal.sosfilt(signal.butter(2, 300, btype="high", fs=sr, output="sos"), out)
    out *= np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(out ** 2)) + 1e-12)
    return amount * out + (1 - amount) * x


def lipsync_env(x, sr, closures=()):
    """Per-frame mouth openness (0..1) and roundness (0..1) from the waveform.
    `closures`: line-relative times (s) where the lips must shut (m/b/p, see bilabial_times)."""
    hop = sr // FPS
    n = int(np.ceil(len(x) / hop))
    pad = np.pad(x, (0, n * hop - len(x) + hop))
    opens, rounds = [], []
    win = np.hanning(hop * 2)
    for i in range(n):
        seg = pad[i * hop: i * hop + hop * 2]
        if len(seg) < hop * 2:
            seg = np.pad(seg, (0, hop * 2 - len(seg)))
        rms = np.sqrt(np.mean(seg ** 2) + 1e-12)
        opens.append(rms)
        spec = np.abs(np.fft.rfft(seg * win))
        freqs = np.fft.rfftfreq(len(seg), 1 / sr)
        band = (freqs > 150) & (freqs < 5000)
        c = float(np.sum(freqs[band] * spec[band]) / (np.sum(spec[band]) + 1e-9))
        rounds.append(c)
    opens = np.array(opens)
    peak = np.percentile(opens, 95) + 1e-9
    opens = np.clip(opens / peak, 0, 1) ** 0.75
    opens[opens < 0.08] = 0.0
    # low centroid -> rounder mouth ("oo"/"oh"), high centroid -> wide ("ee"/"s")
    rounds = np.array(rounds)
    rounds = np.clip((2200 - rounds) / 1400, 0, 1)
    # light smoothing so the mouth doesn't chatter
    k = np.array([0.25, 0.5, 0.25])
    opens = np.convolve(opens, k, mode="same")
    rounds = np.convolve(rounds, k, mode="same")
    # m / b / p: nasals and voiced stops carry plenty of energy, so the RMS envelope never closes on them.
    # Force a lip closure at each one: the two frames around it shut (frame i is shown at line time i / FPS),
    # one eased frame either side.
    for tc in closures:
        i0 = int(np.floor(tc * FPS))
        for i, w in ((i0 - 1, 0.45), (i0, 0.0), (i0 + 1, 0.0), (i0 + 2, 0.45)):
            if 0 <= i < len(opens):
                opens[i] *= w
                rounds[i] *= 0.3 if w == 0.0 else 0.7
    return [round(float(v), 3) for v in opens], [round(float(v), 3) for v in rounds]


# ----------------------------------------------------------------------------- bilabial closures
BILABIAL = {"m", "b", "p"}
_WHISPER = None


def _g2p(word):
    """espeak-ng phonemes (Kirshenbaum ASCII, stress marks stripped) for one word."""
    import subprocess
    out = subprocess.run(["espeak-ng", "-q", "-x", "--sep=_", "-v", "en-us", word],
                         capture_output=True, text=True, check=True).stdout
    return [p.strip("',") for p in out.strip().replace(" ", "_").split("_") if p.strip("',")]


def _is_vowel(p):
    return any(c in "aeiouAEIOUV@3" for c in p)


def bilabial_times(x, sr):
    """Line-relative times (s) of lip closures for every m/b/p.

    Words and their timings come from faster-whisper (word_timestamps) on the trimmed VO; each word is
    phonemized with espeak-ng (so silent letters like the b in 'lamb' are skipped). A bilabial's position is
    first estimated from the phoneme order (vowels weighted x2), then snapped to the deepest dip of the
    1.2-5 kHz band energy within +-90 ms of that estimate: the lips are shut where the formants vanish
    (nasal murmur for m, the closure for b/p). Adjacent bilabials (the 'mb' in 'number') make one closure."""
    global _WHISPER
    from faster_whisper import WhisperModel
    if _WHISPER is None:
        _WHISPER = WhisperModel("small.en", device="cpu", compute_type="int8",
                                download_root="/home/user/models/whisper")
    y16 = signal.resample_poly(x, 1, sr // 16000).astype(np.float32)
    segs, _ = _WHISPER.transcribe(y16, word_timestamps=True, language="en", beam_size=5)
    words = [w for s in segs for w in s.words]
    # band energy in 20 ms windows, 5 ms hop
    sos = signal.butter(4, [1200, 5000], btype="band", fs=sr, output="sos")
    hf = signal.sosfilt(sos, x) ** 2
    hop, win = int(0.005 * sr), int(0.02 * sr)
    c = np.cumsum(np.concatenate([[0.0], hf]))
    starts = np.arange(0, max(1, len(x) - win), hop)
    e_hf = 10 * np.log10((c[starts + win] - c[starts]) / win + 1e-12)
    t_hf = (starts + win / 2) / sr
    out = []
    for w in words:
        word = "".join(ch for ch in w.word if ch.isalpha() or ch in "'-")
        if not word:
            continue
        ph = _g2p(word)
        if not any(p in BILABIAL for p in ph):
            continue
        wt = np.array([2.0 if _is_vowel(p) else 1.0 for p in ph])
        edges = np.concatenate([[0.0], np.cumsum(wt)]) / wt.sum()
        k = 0
        while k < len(ph):
            if ph[k] not in BILABIAL:
                k += 1
                continue
            j = k
            while j + 1 < len(ph) and ph[j + 1] in BILABIAL:
                j += 1
            frac = 0.5 * (edges[k] + edges[j + 1])
            est = w.start + frac * (w.end - w.start)
            lo, hi = max(est - 0.09, w.start - 0.06), min(est + 0.09, w.end + 0.03)
            m = (t_hf >= lo) & (t_hf <= hi)
            tc = float(t_hf[m][np.argmin(e_hf[m])]) if m.any() else est
            out.append({"word": word, "ph": "_".join(ph[k:j + 1]), "est": round(est, 3), "t": round(tc, 3)})
            k = j + 1
    return out


def _lips_for(lid, x, log=None):
    try:
        bl = bilabial_times(x, SR)
    except Exception as e:  # no faster-whisper / espeak-ng: fall back to the plain envelope
        print(f"  {lid}: bilabial closures skipped ({e})")
        bl = []
    if log is not None:
        log[lid] = bl
    o, r = lipsync_env(x, SR, [b["t"] for b in bl])
    return {"open": o, "round": r}


def lips_only(only=None):
    """Rebuild build/lipsync.json from the existing build/vo/<id>.wav (no TTS; audio unchanged).
    Also writes build/vo/bilabials.json (word, phonemes, estimated and snapped closure time) for QA."""
    lips = json.loads(LIPSYNC.read_text()) if LIPSYNC.exists() else {}
    log_path = VO_DIR / "bilabials.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    for lid in LINES:
        if only and lid not in only:
            continue
        x, sr = sf.read(VO_DIR / f"{lid}.wav")
        assert sr == SR
        lips[lid] = _lips_for(lid, np.asarray(x, dtype=np.float64), log)
        print(f"{lid:4s} closures: " + ", ".join(f"{b['word']}[{b['ph']}]@{b['t']:.2f}" for b in log[lid]))
    LIPSYNC.write_text(json.dumps(lips))
    log_path.write_text(json.dumps(log, indent=1))


def main(only=None):
    from kokoro_onnx import Kokoro

    VO_DIR.mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    manifest_path = VO_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    lips = json.loads(LIPSYNC.read_text()) if LIPSYNC.exists() else {}
    for lid, (char, display, tts_text, speed) in LINES.items():
        if only and lid not in only:
            continue
        v = VOICES[char]
        text = tts_text or display
        samples, sr = k.create(text, voice=v["voice"], speed=speed or v["speed"], lang=v["lang"])
        x = np.asarray(samples, dtype=np.float64)
        x = signal.resample_poly(x, SR, sr)
        x = trim_silence(x, SR)
        if char == "quill":
            x = android_fx(x, SR)
        if lid in WHISPER:
            x = whisperize(x, SR, WHISPER[lid])
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
        sf.write(VO_DIR / f"{lid}.wav", x.astype(np.float32), SR, subtype="FLOAT")
        lips[lid] = _lips_for(lid, x)
        manifest[lid] = {"char": char, "text": display, "dur": round(len(x) / SR, 3)}
        print(f"{lid:4s} {char:5s} {len(x)/SR:5.2f}s  {display}")
    manifest_path.write_text(json.dumps(manifest, indent=1))
    LIPSYNC.write_text(json.dumps(lips))


if __name__ == "__main__":
    # python3 audio/tts.py [ids]          synthesize VO + lip-sync
    # python3 audio/tts.py --lips [ids]   lip-sync only, from the existing VO files
    if "--lips" in sys.argv:
        lips_only(set(a for a in sys.argv[1:] if a != "--lips") or None)
    else:
        main(set(sys.argv[1:]) or None)
