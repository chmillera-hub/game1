"""Per-frame mouth data for every spoken (non-inner) line.

    python3 audio/lipsync.py            # reads data/lines.json + data/timeline.json, writes data/lipsync.json

open  : jaw opening from the loudness envelope (fast attack, softer release)
round : lip rounding from aligned phonemes (oo / o / w ...)
wide  : lip spreading from aligned phonemes (ee / s / sh ...)
Bilabials (p b m) briefly close the lips; f/v nearly close them. Phonemes are placed inside each word's
whisper timestamp span, vowels weighted longer than consonants.
"""
import json, os, re, sys
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24

ROUND = set("uʊoɔɒw") | {"oʊ", "aʊ", "ɔː", "uː", "ɔɪ"}
WIDE = set("iɪeɛæsʃʒzjç") | {"iː", "eɪ", "tʃ", "dʒ", "aɪ"}
OPEN = set("aɑʌɐəɜæ") | {"ɑː", "ɜː", "aɪ", "aʊ"}
CLOSE = set("pbm")
LABIODENTAL = set("fv")
VOWELS = set("aeiouɑɐɒæɔəɛɜɪʊʌyø") | {"ː"}

_tok = None
def phonemes(word):
    global _tok
    if _tok is None:
        from kokoro_onnx.tokenizer import Tokenizer
        _tok = Tokenizer()
    p = _tok.phonemize(word, "en-us")
    p = re.sub(r"[ˈˌ\s\.\?\!,;:'\"\-]", "", p)
    # group diphthongs / affricates / long marks
    out, i = [], 0
    while i < len(p):
        two = p[i : i + 2]
        if two in ("oʊ", "aʊ", "eɪ", "aɪ", "ɔɪ", "tʃ", "dʒ") or (len(two) == 2 and two[1] == "ː"):
            out.append(two); i += 2
        else:
            out.append(p[i]); i += 1
    return out

def shape(ph):
    """(round, wide, open_scale, close_force)"""
    if ph in CLOSE: return (0.1, 0.0, 0.0, 1.0)
    if ph in LABIODENTAL: return (0.0, 0.25, 0.25, 0.7)
    r = 0.85 if ph in ROUND or (len(ph) > 1 and ph[0] in "uoɔ") else 0.0
    w = 0.6 if ph in WIDE or (len(ph) > 1 and ph[0] in "ie") else 0.0
    o = 1.15 if ph in OPEN else (1.0 if any(c in VOWELS for c in ph) else 0.6)
    return (r, w, o, 0.0)

def smooth(x, attack, release):
    y = np.zeros_like(x)
    v = 0.0
    for i, xi in enumerate(x):
        k = attack if xi > v else release
        v = v + (xi - v) * k
        y[i] = v
    return y

def frames_for(line, start):
    a, sr = sf.read(os.path.join(ROOT, line["file"]), dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    n = int(np.ceil(len(a) / sr * FPS)) + 1
    t = np.arange(n) / FPS
    win = int(sr * 0.045)
    rms = np.zeros(n)
    for i, ti in enumerate(t):
        c = int(ti * sr)
        seg = a[max(0, c - win // 2) : c + win // 2]
        rms[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    db = 20 * np.log10(rms + 1e-6)
    ref = np.percentile(db[db > -60], 90) if np.any(db > -60) else -20
    op = np.clip((db - (ref - 30)) / 30, 0, 1) ** 1.3
    # phoneme tracks
    rnd = np.zeros(n); wid = np.zeros(n); osc = np.ones(n); clo = np.zeros(n)
    for w in line.get("words", []):
        word = re.sub(r"[^A-Za-z']", "", w["w"])
        if not word: continue
        phs = phonemes(word)
        if not phs: continue
        weights = np.array([2.0 if any(c in VOWELS for c in p) else 1.0 for p in phs])
        edges = w["start"] + np.concatenate([[0], np.cumsum(weights) / weights.sum()]) * max(0.05, w["end"] - w["start"])
        for p, s0, s1 in zip(phs, edges[:-1], edges[1:]):
            r_, w_, o_, c_ = shape(p)
            i0, i1 = int(round(s0 * FPS)), max(int(round(s0 * FPS)) + 1, int(round(s1 * FPS)))
            for i in range(i0, min(i1, n)):
                rnd[i] = max(rnd[i], r_); wid[i] = max(wid[i], w_); osc[i] = o_; clo[i] = max(clo[i], c_)
    rnd = smooth(rnd, 0.55, 0.35); wid = smooth(wid, 0.55, 0.35)
    open_ = op * osc * (1 - 0.85 * clo)
    open_ = smooth(open_, 0.75, 0.45)
    open_ = np.clip(open_ * 0.95, 0, 1)
    return {"start": round(start, 4), "fps": FPS,
            "open": [round(float(v), 3) for v in open_],
            "wide": [round(float(v * 0.9), 3) for v in wid],
            "round": [round(float(v), 3) for v in rnd]}

def main():
    lines = json.load(open(os.path.join(ROOT, "data/lines.json")))
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    out = {}
    for bid, line in lines.items():
        if line.get("inner") or bid not in tl["beats"]:
            continue
        out[bid] = frames_for(line, tl["beats"][bid]["start"])
    json.dump(out, open(os.path.join(ROOT, "data/lipsync.json"), "w"))
    print(f"lipsync for {len(out)} lines")

if __name__ == "__main__":
    main()
