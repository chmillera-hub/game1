# Voice synthesis: script.json -> build/voices/<line>.wav (48 kHz mono) + build/lines.json
# lines.json[id] = {dur, words:[{w,start,end}], mouth:{hz:100, open:[], wide:[], round:[], press:[]}}
import json, os, subprocess, sys
import numpy as np, soundfile as sf, onnxruntime as ort
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, "..", "models")
OUT = os.path.join(ROOT, "build", "voices")
os.makedirs(OUT, exist_ok=True)

CAST = {  # voice, default speed, ffmpeg post filter
    "narrator":  ("af_heart",  0.92, "highpass=f=70"),
    "keeper":    ("am_michael", 0.95, "highpass=f=70"),
    "directive": ("bf_emma",   1.0,  "highpass=f=220,lowpass=f=7600,aecho=0.8:0.45:19:0.2,"
                                     "chorus=0.6:0.9:28:0.28:0.25:2"),
    "mira":      ("af_heart",  1.0,  "rubberband=pitch=1.17:formant=shifted,highpass=f=90"),
    "grandpa":   ("bm_george", 0.9,  "rubberband=pitch=0.95:formant=preserved,highpass=f=60"),
}

# phoneme -> (open, wide, round, press)
VIS = {}
for ch in "aɑʌæɐ": VIS[ch] = (0.85, 0.3, 0.0, 0)
for ch in "əᵻ": VIS[ch] = (0.45, 0.15, 0.0, 0)
for ch in "eɛ": VIS[ch] = (0.55, 0.6, 0.0, 0)
for ch in "iɪj": VIS[ch] = (0.3, 0.85, 0.0, 0)
for ch in "oɔɒ": VIS[ch] = (0.6, -0.2, 0.75, 0)
for ch in "uʊw": VIS[ch] = (0.25, -0.4, 0.95, 0)
for ch in "ɹɚɝ": VIS[ch] = (0.3, 0.0, 0.5, 0)
for ch in "ʃʒ": VIS[ch] = (0.25, 0.0, 0.6, 0)
for ch in "szʦtdnlθðkɡgŋhɾʔç": VIS[ch] = (0.2, 0.4, 0.0, 0)
for ch in "mbp": VIS[ch] = (0.0, 0.0, 0.0, 1)
for ch in "fv": VIS[ch] = (0.08, 0.2, 0.0, 0.5)

kok = Kokoro(os.path.join(M, "kokoro-v1.0.onnx"), os.path.join(M, "voices-v1.0.bin"))
sess = ort.InferenceSession(os.path.join(M, "kokoro-ts.onnx"), providers=["CPUExecutionProvider"])
vocab = kok.tokenizer.vocab if hasattr(kok.tokenizer, "vocab") else None


def synth(text, voice, speed):
    ph = kok.tokenizer.phonemize(text, "en-us")
    chars = [c for c in ph if (vocab is None or c in vocab)]
    toks = kok.tokenizer.tokenize("".join(chars))
    assert len(toks) == len(chars), (len(toks), len(chars))
    style = kok.get_voice_style(voice)[len(toks)]
    ids = np.array([[0] + toks + [0]], dtype=np.int64)
    wav, dur = sess.run(None, {"input_ids": ids, "style": style, "speed": np.array([speed], dtype=np.float32)})
    wav, dur = wav[0], dur[0]
    cum = np.concatenate([[0], np.cumsum(dur)])
    tt = cum / cum[-1] * (len(wav) / 24000.0)  # token boundary times (s)
    return wav, "".join(chars), tt


def process(line):
    voice, spd0, filt = CAST[line["speaker"]]
    spd = line.get("speed", 1.0) * spd0  # line speed is relative to the voice's default pace
    wav, chars, tt = synth(line["text"], voice, spd)
    # trim BOS/EOS silence
    t0 = max(0.0, tt[1] - 0.04)
    t1 = min(len(wav) / 24000.0, tt[-2] + 0.18)
    seg = wav[int(t0 * 24000): int(t1 * 24000)]
    raw = os.path.join(OUT, line["id"] + ".raw.wav")
    fin = os.path.join(OUT, line["id"] + ".wav")
    sf.write(raw, seg, 24000)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", filt + ",aresample=48000",
                    "-ac", "1", "-c:a", "pcm_s16le", fin], check=True)
    os.remove(raw)
    dur = sf.info(fin).duration
    # per-char times (shifted by trim); char i spans tt[i+1]..tt[i+2]
    starts = tt[1:-2] - t0
    ends = tt[2:-1] - t0
    # words from phoneme spaces
    pw = []  # (start, end) per phoneme word
    cur = None
    for i, c in enumerate(chars):
        if c == " ":
            if cur: pw.append(cur); cur = None
            continue
        if c in ".,!?;:…—\"'()":
            continue
        if cur is None: cur = [starts[i], ends[i]]
        else: cur[1] = ends[i]
    if cur: pw.append(cur)
    tw = line["text"].split()
    words = []
    if len(pw) == len(tw):
        for w, (a, b) in zip(tw, pw):
            words.append({"w": w, "start": round(float(a), 3), "end": round(float(b), 3)})
    elif len(pw) < len(tw):  # phonemizer merged words ("not a" -> one token): DP-align by phoneme length
        Lw = [max(1, len([c for c in kok.tokenizer.phonemize(w, "en-us") if c.isalpha() or c in "ˈˌː"])) for w in tw]
        Pj = [max(1e-3, b - a) for a, b in pw]
        n, m = len(tw), len(pw)
        INF = 1e9
        dp = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[0] * (m + 1) for _ in range(n + 1)]
        dp[0][0] = 0
        tot_L, tot_P = sum(Lw), sum(Pj)
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                for k in range(1, 4):  # a phoneme word may cover up to 3 text words
                    if i - k < 0 or dp[i - k][j - 1] >= INF: continue
                    c = abs(sum(Lw[i - k:i]) / tot_L - Pj[j - 1] / tot_P) + 0.02 * (k - 1)
                    if dp[i - k][j - 1] + c < dp[i][j]: dp[i][j] = dp[i - k][j - 1] + c; bk[i][j] = k
        i, j, groups = n, m, []
        while i > 0: k = bk[i][j]; groups.append((i - k, i, j - 1)); i -= k; j -= 1
        for s, e, pj in reversed(groups):
            a, b = pw[pj]; sub = sum(Lw[s:e]); acc = 0
            for q in range(s, e):
                wa = a + (b - a) * acc / sub; acc += Lw[q]; wb = a + (b - a) * acc / sub
                words.append({"w": tw[q], "start": round(float(wa), 3), "end": round(float(wb), 3)})
    else:  # proportional fallback by character count
        tot = sum(len(w) for w in tw); acc = 0
        span0 = pw[0][0] if pw else 0; span1 = pw[-1][1] if pw else dur
        for w in tw:
            a = span0 + (span1 - span0) * acc / tot; acc += len(w)
            b = span0 + (span1 - span0) * acc / tot
            words.append({"w": w, "start": round(a, 3), "end": round(b, 3)})
        print("  word-count mismatch", line["id"], len(pw), len(tw), file=sys.stderr)
    # mouth tracks at 100 Hz
    n = int(dur * 100) + 1
    tr = np.zeros((4, n))
    for i, c in enumerate(chars):
        v = VIS.get(c)
        if not v: continue
        a, b = int(starts[i] * 100), max(int(starts[i] * 100) + 1, int(ends[i] * 100))
        for k in range(4): tr[k, a:min(b, n)] = v[k]
    # coarticulation smoothing (~35 ms gaussian)
    ker = np.exp(-0.5 * (np.arange(-8, 9) / 3.5) ** 2); ker /= ker.sum()
    for k in range(4): tr[k] = np.convolve(tr[k], ker, mode="same")
    # loudness gate from actual audio
    y, sr = sf.read(fin)
    hop = sr // 100
    rms = np.array([np.sqrt(np.mean(y[j * hop:(j + 1) * hop] ** 2) + 1e-12) for j in range(n)])
    env = np.clip(rms / (np.percentile(rms, 90) + 1e-9), 0, 1.2)
    env = np.convolve(env, ker, mode="same")
    tr[0] *= np.clip(env * 1.3, 0, 1.1)
    tr[1] *= np.clip(env * 1.6, 0, 1)
    rd = lambda a: [round(float(x), 2) for x in a]
    return {"dur": round(dur, 3), "words": words,
            "mouth": {"hz": 100, "open": rd(tr[0]), "wide": rd(tr[1]), "round": rd(tr[2]), "press": rd(tr[3])}}


if __name__ == "__main__":
    sc = json.load(open(os.path.join(ROOT, "script.json")))
    only = set(sys.argv[1:])
    path = os.path.join(ROOT, "build", "lines.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    for sh in sc["shots"]:
        for ln in sh["lines"]:
            if only and ln["id"] not in only and ln["speaker"] not in only: continue
            res[ln["id"]] = process(ln)
            print(ln["id"], ln["speaker"], res[ln["id"]]["dur"], flush=True)
    json.dump(res, open(path, "w"))
