"""Per-frame mouth data (24 fps) for every line and mouth-driven vocal beat (play time).

    python3 audio/lipsync.py      # reads data/lines.json, data/vocals.json, data/timeline.json -> data/lipsync.json

open  : jaw opening from the loudness envelope (fast attack, softer release), scaled by phoneme openness
round : lip rounding from aligned phonemes (oo / o / w ...)
wide  : lip spreading (ee / s / sh ...)
close : bilabials (p b m) press the lips shut; f/v nearly close them
Vocals: laughs/giggles/screams -> loudness only; whisper -> small; mm-hm/hum -> closed lips; huff -> puff.
NARRATOR is voice-over: no mouth data.
"""
import json, os, re
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
    p = re.sub(r"[ˈˌ\s\.\?\!,;:'\"\-]", "", _tok.phonemize(word, "en-us"))
    out, i = [], 0
    while i < len(p):
        two = p[i:i + 2]
        if two in ("oʊ", "aʊ", "eɪ", "aɪ", "ɔɪ", "tʃ", "dʒ") or (len(two) == 2 and two[1] == "ː"):
            out.append(two); i += 2
        else:
            out.append(p[i]); i += 1
    return out

def shape(ph):
    if ph in CLOSE: return (0.1, 0.0, 0.0, 1.0)
    if ph in LABIODENTAL: return (0.0, 0.25, 0.25, 0.7)
    r = 0.85 if ph in ROUND or (len(ph) > 1 and ph[0] in "uoɔ") else 0.0
    w = 0.6 if ph in WIDE or (len(ph) > 1 and ph[0] in "ie") else 0.0
    o = 1.15 if ph in OPEN else (1.0 if any(c in VOWELS for c in ph) else 0.6)
    return (r, w, o, 0.0)

def smooth(x, attack, release):
    y = np.zeros_like(x); v = 0.0
    for i, xi in enumerate(x):
        v += (xi - v) * (attack if xi > v else release); y[i] = v
    return y

def loudness(path):
    a, sr = sf.read(os.path.join(ROOT, path), dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    n = int(np.ceil(len(a) / sr * FPS)) + 1
    win = int(sr * 0.045)
    rms = np.array([np.sqrt(np.mean(a[max(0, int(i / FPS * sr) - win // 2): int(i / FPS * sr) + win // 2] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms + 1e-6)
    ref = np.percentile(db[db > -60], 90) if np.any(db > -60) else -20
    return n, np.clip((db - (ref - 30)) / 30, 0, 1) ** 1.3

def line_frames(L):
    n, op = loudness(L["file"])
    rnd = np.zeros(n); wid = np.zeros(n); osc = np.ones(n); clo = np.zeros(n)
    bleep_from = None
    if L.get("bleep") and L.get("words"):
        bleep_from = int((L["words"][-1]["end"] + 0.05) * FPS)
    for w in L.get("words", []):
        word = re.sub(r"[^A-Za-z']", "", w["w"])
        if not word: continue
        phs = phonemes(word)
        if not phs: continue
        weights = np.array([2.0 if any(c in VOWELS for c in p) else 1.0 for p in phs])
        edges = w["start"] + np.concatenate([[0], np.cumsum(weights) / weights.sum()]) * max(0.05, w["end"] - w["start"])
        for p, s0, s1 in zip(phs, edges[:-1], edges[1:]):
            r_, w_, o_, c_ = shape(p)
            i0 = int(round(s0 * FPS)); i1 = max(i0 + 1, int(round(s1 * FPS)))
            for i in range(i0, min(i1, n)):
                rnd[i] = max(rnd[i], r_); wid[i] = max(wid[i], w_); osc[i] = o_; clo[i] = max(clo[i], c_)
    if bleep_from is not None:   # mouth keeps shaping an "F" under the bleep, then an open "uh"
        for i in range(bleep_from, n):
            clo[i] = 0.7 if i < bleep_from + 3 else 0.0; wid[i] = 0.3
    rnd = smooth(rnd, 0.55, 0.35); wid = smooth(wid, 0.55, 0.35); clo = smooth(clo, 0.8, 0.5)
    open_ = smooth(op * osc * (1 - 0.85 * clo), 0.75, 0.45)
    return np.clip(open_ * 0.95, 0, 1), wid * 0.9, rnd, clo

def vocal_frames(V):
    n, op = loudness(V["file"])
    z = np.zeros(n)
    kind = V["vocal"]
    if kind in ("mmhm", "hum"):
        return op * 0.08, z + 0.1, z + 0.2, np.clip(op * 2, 0, 1) * 0.9
    if kind == "whisper":
        return smooth(op * 0.35, 0.6, 0.4), z + 0.3, z, z
    if kind == "huff":
        return smooth(op * 0.5, 0.7, 0.3), z, z + 0.5, z
    if kind in ("laugh_maniacal", "laugh_soft", "giggle", "scream_short", "gasp", "whimper", "sigh", "cough", "snort"):
        k = {"laugh_maniacal": 1.0, "scream_short": 1.0, "gasp": 0.7, "laugh_soft": 0.6, "giggle": 0.45, "whimper": 0.3,
             "sigh": 0.35, "cough": 0.7, "snort": 0.2}[kind]
        return smooth(op * k, 0.8, 0.35), z + (0.3 if kind in ("giggle", "laugh_soft") else 0.1), z + (0.4 if kind == "scream_short" else 0), z
    return None

def main():
    lines = json.load(open(os.path.join(ROOT, "data/lines.json")))
    vp = os.path.join(ROOT, "data/vocals.json")
    vocals = json.load(open(vp)) if os.path.exists(vp) else {}
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    out = {}
    r3 = lambda a: [round(float(v), 3) if np.isfinite(v) else 0.0 for v in a]   # no NaN: browsers reject it in JSON
    for bid, L in lines.items():
        if L["speaker"] == "NARRATOR" or bid not in tl["beats"]: continue
        o, w, r, c = line_frames(L)
        out[bid] = {"speaker": L["speaker"], "start": tl["beats"][bid]["start"], "fps": FPS, "open": r3(o), "wide": r3(w), "round": r3(r), "close": r3(c)}
    for bid, V in vocals.items():
        if V["speaker"] == "NARRATOR" or bid not in tl["beats"]: continue
        fr = vocal_frames(V)
        if fr is None: continue
        o, w, r, c = fr
        out[bid] = {"speaker": V["speaker"], "vocal": V["vocal"], "start": tl["beats"][bid]["start"], "fps": FPS,
                    "open": r3(o), "wide": r3(w), "round": r3(r), "close": r3(c)}
    json.dump(out, open(os.path.join(ROOT, "data/lipsync.json"), "w"), allow_nan=False)
    print(f"lipsync: {len(out)} clips")

if __name__ == "__main__":
    main()
