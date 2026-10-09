"""Render every dialogue line with Kokoro TTS, then build lip-sync envelopes.

Outputs
    build/vo/<id>.wav        48 kHz mono float WAV, edges trimmed
    build/vo/manifest.json   {id: {"char", "text", "dur"}}
    build/lipsync.json       {id: {"open": [...], "round": [...]}} one value per video frame (FPS)

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
from script_data import LINES, VOICES  # noqa: E402


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


def lipsync_env(x, sr):
    """Per-frame mouth openness (0..1) and roundness (0..1) from the waveform."""
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
    return [round(float(v), 3) for v in opens], [round(float(v), 3) for v in rounds]


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
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.89
        sf.write(VO_DIR / f"{lid}.wav", x.astype(np.float32), SR, subtype="FLOAT")
        o, r = lipsync_env(x, SR)
        lips[lid] = {"open": o, "round": r}
        manifest[lid] = {"char": char, "text": display, "dur": round(len(x) / SR, 3)}
        print(f"{lid:4s} {char:5s} {len(x)/SR:5.2f}s  {display}")
    manifest_path.write_text(json.dumps(manifest, indent=1))
    LIPSYNC.write_text(json.dumps(lips))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
