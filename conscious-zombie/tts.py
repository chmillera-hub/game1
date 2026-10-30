"""Voice pass: synthesize lines, build timeline.json + voice stems."""
import json, os, re, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
from kokoro_onnx import Kokoro
from script import SCENES, VOICES, clean, accents

BUILD = sys.argv[1] if len(sys.argv) > 1 else "build"
MODEL = os.environ.get("KOKORO_DIR", "/tmp/claude-0/tts")
SR, FPS = 48000, 24
os.makedirs(f"{BUILD}/lines", exist_ok=True)

kok = Kokoro(f"{MODEL}/kokoro-v1.0.onnx", f"{MODEL}/voices-v1.0.bin")


def zombie_fx(y):
    # pitch down ~1.2 semitones (and a bit slower), mild grit, soften highs
    y = resample_poly(y, 107, 100)
    grit = np.tanh(y * 5.0) / 5.0
    y = 0.8 * y + 0.35 * grit
    sos = butter(2, 5200, "low", fs=SR, output="sos")
    return sosfilt(sos, y)


def synth(spk, text):
    voice, lang, speed = VOICES[spk]
    s, sr = kok.create(text, voice=voice, speed=speed, lang=lang)
    y = resample_poly(s.astype(np.float64), SR // sr, 1)
    if spk == "Z":
        y = zombie_fx(y)
    # trim leading/trailing near-silence, keep 30 ms tails
    a = np.abs(y)
    idx = np.where(a > 0.01)[0]
    if len(idx):
        y = y[max(0, idx[0] - int(0.03 * SR)): idx[-1] + int(0.06 * SR)]
    return y / (np.max(np.abs(y)) + 1e-9) * 0.9


def envelope(y):
    hop = SR // FPS
    n = int(np.ceil(len(y) / hop))
    rms = np.array([np.sqrt(np.mean(y[i*hop:(i+1)*hop] ** 2) + 1e-12) for i in range(n)])
    zc = np.array([np.mean(np.abs(np.diff(np.sign(y[i*hop:(i+1)*hop])))) / 2 for i in range(n)])
    rms = rms / (np.percentile(rms, 95) + 1e-9)
    op = np.clip((rms - 0.08) * 1.25, 0, 1)
    # smooth (fast attack, slower release)
    out, v = [], 0.0
    for x in op:
        v = v + (x - v) * (0.75 if x > v else 0.45)
        out.append(round(float(v), 3))
    wide = np.clip(zc * 6, 0, 1)
    return out, [round(float(w), 3) for w in wide]


def gaps(y):
    """Centers (s) of silent gaps >= 120 ms inside the line."""
    hop = int(0.01 * SR)
    e = np.array([np.sqrt(np.mean(y[i:i+hop] ** 2)) for i in range(0, len(y) - hop, hop)])
    quiet = e < 0.02
    res, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        if not q and start is not None:
            if i - start >= 12 and start > 5:
                res.append((start + i) / 2 * 0.01)
            start = None
    return res


def chunk_text(text, maxlen=58):
    """Split into subtitle chunks at punctuation, keeping chunks short."""
    parts = re.split(r"(?<=[.?!,])\s+|(?<=\.\.\.)\s*", text)
    parts = [p.strip() for p in parts if p and p.strip()]
    chunks, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > maxlen:
            chunks.append(cur)
            cur = p
        else:
            cur = (cur + " " + p).strip() if cur else p
        if cur.endswith((".", "?", "!")) and not cur.endswith("...") and len(cur) > 22:
            chunks.append(cur)
            cur = ""
    if cur:
        chunks.append(cur)
    return chunks


timeline = {"fps": FPS, "sr": SR, "scenes": [], "lines": {}}
t = 0.0
order = []
for scene, lines in SCENES:
    s0 = t
    for lid, spk, text, pb, pa in lines:
        y = synth(spk, clean(text))
        sf.write(f"{BUILD}/lines/{lid}.wav", y, SR)
        dur = len(y) / SR
        t += pb
        env, wide = envelope(y)
        txt = clean(text)
        chunks = chunk_text(txt)
        g = gaps(y)
        # time chunks: proportional by characters, snapped to detected pauses
        total = sum(len(c) for c in chunks)
        acc, cuts = 0, []
        for c in chunks[:-1]:
            acc += len(c)
            est = dur * acc / total
            near = [x for x in g if abs(x - est) < 0.7 and all(abs(x - k) > 0.3 for k in cuts)]
            cuts.append(min(near, key=lambda x: abs(x - est)) if near else est)
        bounds = [0.0] + cuts + [dur]
        subs = [{"text": c, "t0": round(t + bounds[i], 3), "t1": round(t + bounds[i+1], 3)}
                for i, c in enumerate(chunks)]
        acc_t = [{"t": round(t + f * dur, 3), "kind": k} for f, k in accents(text)]
        timeline["lines"][lid] = {"spk": spk, "scene": scene, "text": txt, "t0": round(t, 3),
                                  "t1": round(t + dur, 3), "env": env, "wide": wide,
                                  "subs": subs, "accents": acc_t}
        order.append(lid)
        print(f"{lid:4s} {spk:2s} {t:7.2f} {dur:5.2f}  {txt[:60]}")
        t += dur + pa
    timeline["scenes"].append({"id": scene, "t0": round(s0, 3), "t1": round(t, 3)})
timeline["order"] = order
timeline["duration"] = round(t, 3)
json.dump(timeline, open(f"{BUILD}/timeline.json", "w"))
print("TOTAL", round(t, 2), "s")
