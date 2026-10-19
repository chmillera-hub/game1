"""Build the master timeline and lip-sync envelopes from the chosen line audio.

Usage: python prepare.py script.json SELECTION_JSON OUT_DIR
  SELECTION_JSON maps line id -> {"path": wav, "words": [[start, end, word], ...]}
  (lines missing from it fall back to /opt/work/tts/<id>.wav with no word timings)
Writes OUT_DIR/timeline.json, OUT_DIR/lipsync.json and OUT_DIR/lines/<id>.wav
(trimmed, level-matched 24 kHz mono).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

SR = 24000
FPS = 100


def load(path):
    a, sr = sf.read(path, dtype="float32")
    if a.ndim > 1:
        a = a.mean(1)
    if sr != SR:
        g = np.gcd(sr, SR)
        a = resample_poly(a, SR // g, sr // g).astype(np.float32)
    return a


def trim(a, thresh_db=-42, pad=0.05):
    win = int(0.02 * SR)
    env = np.sqrt(np.convolve(a * a, np.ones(win) / win, mode="same") + 1e-12)
    db = 20 * np.log10(env)
    idx = np.where(db > thresh_db)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(a), idx[-1] + int(pad * SR))
    out = a[s:e].copy()
    n = int(0.01 * SR)
    out[:n] *= np.linspace(0, 1, n)
    out[-n * 3:] *= np.linspace(1, 0, n * 3)
    return out


def level(a, target_db=-20.0):
    """Match active-speech RMS so every voice sits at a similar level."""
    win = int(0.05 * SR)
    env = np.sqrt(np.convolve(a * a, np.ones(win) / win, mode="same") + 1e-12)
    active = env[env > np.percentile(env, 60)]
    rms = np.sqrt(np.mean(active ** 2)) if len(active) else 1e-3
    g = 10 ** (target_db / 20) / max(rms, 1e-5)
    out = a * g
    peak = np.max(np.abs(out))
    if peak > 0.95:
        out *= 0.95 / peak
    return out.astype(np.float32)


def envelopes(a):
    hop = SR // FPS
    win = int(0.03 * SR)
    n = int(np.ceil(len(a) / hop))
    pad = np.pad(a, (win, win))
    rms = np.zeros(n)
    for i in range(n):
        seg = pad[i * hop + win - win // 2: i * hop + win + win // 2]
        rms[i] = np.sqrt(np.mean(seg * seg) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    peak = np.percentile(db, 95)
    floor = peak - 30
    o = np.clip((db - floor) / (peak - floor - 3), 0, 1) ** 1.25
    # attack/release smoothing so the jaw moves like a jaw
    sm = np.zeros_like(o)
    v = 0.0
    for i, x in enumerate(o):
        k = 0.65 if x > v else 0.32
        v += (x - v) * k
        sm[i] = v
    # brightness: sibilants/"ee" widen, dark vowels round
    hi = sosfilt(butter(4, [2500, 7000], btype="band", fs=SR, output="sos"), a)
    lo = sosfilt(butter(4, [200, 1400], btype="band", fs=SR, output="sos"), a)
    wide = np.zeros(n)
    for i in range(n):
        s0, s1 = i * hop, min(len(a), i * hop + win)
        eh = np.mean(hi[s0:s1] ** 2) + 1e-12
        el = np.mean(lo[s0:s1] ** 2) + 1e-12
        wide[i] = 10 * np.log10(eh / el)
    wide = np.clip((wide + 12) / 18, -0.4, 1.0)
    wide = np.convolve(wide, np.ones(5) / 5, mode="same")
    slow = np.convolve(sm, np.ones(30) / 30, mode="same")
    r = lambda x: [round(float(v), 3) for v in x]
    return {"fps": FPS, "open": r(sm), "wide": r(wide * (sm > 0.08)), "slow": r(slow)}


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    sel_path = Path(sys.argv[2])
    sel = json.loads(sel_path.read_text()) if sel_path.exists() else {}
    for entry in sel.values():   # paths in a packed selection are relative to it
        if "path" in entry and not Path(entry["path"]).is_absolute():
            entry["path"] = str(sel_path.parent / entry["path"])
    out = Path(sys.argv[3])
    (out / "lines").mkdir(parents=True, exist_ok=True)
    lips, lines, scenes = {}, [], []
    t = 0.0
    for sc in script["scenes"]:
        s0 = t
        for b in sc["beats"]:
            if "pause" in b:
                t += b["pause"]
                continue
            lid = b["id"]
            entry = sel.get(lid, {})
            a = load(entry.get("path", f"/opt/work/tts/{lid}.wav"))
            a = level(trim(a))
            if b.get("cut"):
                a = a[: max(1, len(a) - int(b["cut"] * SR))]
                n = int(0.02 * SR)
                a[-n:] *= np.linspace(1, 0, n)
            sf.write(out / "lines" / f"{lid}.wav", a, SR)
            t += b.get("pre", 0.3)
            dur = len(a) / SR
            lines.append({
                "id": lid, "who": b["who"], "text": b["text"], "start": round(t, 3), "end": round(t + dur, 3),
                "scene": sc["id"], "verse": b.get("verse", False), "fx": b.get("fx"),
                "words": entry.get("words", []),
            })
            lips[lid] = envelopes(a)
            t += dur
        scenes.append({"id": sc["id"], "title": sc["title"], "start": round(s0, 3), "end": round(t, 3),
                       "verse": sc.get("verse")})
    timeline = {"duration": round(t, 3), "scenes": scenes, "lines": lines}
    (out / "timeline.json").write_text(json.dumps(timeline, indent=1))
    (out / "lipsync.json").write_text(json.dumps(lips))
    print(f"duration {t:.2f}s, {len(lines)} lines")
    for s in scenes:
        print(f"  {s['id']:9s} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end']-s['start']:.1f}s)")


if __name__ == "__main__":
    main()
