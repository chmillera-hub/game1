"""Synthesize every line with Piper, then lay out the timeline.

Writes:
  build/voice/<id>.npy   mono float32 @ SR
  build/timeline.json    start/end, mouth envelope and word timings per line
"""
import json, os, re, sys, wave, io
import numpy as np
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(__file__))
from script import VOICES, LINES, CAPTIONS, SPEAKERS, RATE

VOICE_DIR = os.environ.get("VOICE_DIR", "/tmp/claude-0/voices")
BUILD = os.environ["BUILD"]
SR = 44100
FPS = 30

os.makedirs(f"{BUILD}/voice", exist_ok=True)
_models = {}


def synth(who, text, rate=None):
    from piper import PiperVoice, SynthesisConfig
    model, spk, ls, ns, nw = VOICES[who]
    ls = rate or ls
    if model not in _models:
        _models[model] = PiperVoice.load(f"{VOICE_DIR}/{model}.onnx")
    v = _models[model]
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        v.synthesize_wav(text, w, syn_config=SynthesisConfig(
            speaker_id=spk, length_scale=ls, noise_scale=ns, noise_w_scale=nw))
    buf.seek(0)
    with wave.open(buf) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = resample_poly(a, SR, sr).astype(np.float32)
    a = trim(a)
    return (a * (0.89 / (np.abs(a).max() + 1e-6))).astype(np.float32)


def trim(a, thr=0.008):
    env = np.abs(a)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] - int(0.04 * SR))
    e = min(len(a), idx[-1] + int(0.06 * SR))
    return a[s:e]


def bleep(dur=0.55):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, np.minimum(t, dur - t) / 0.01)
    return (0.35 * np.sin(2 * np.pi * 1000 * t) * env).astype(np.float32)


TOKEN_RE = re.compile(r"\[(BLEEP|NAME|GLITCH)\]")


def redact_chime(dur=0.75):
    """Soft two-tone 'redacted' chime standing in for the viewer's legal name."""
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for k, (f, t0) in enumerate(((880, 0.0), (1318.5, 0.18), (1174.7, 0.36))):
        tt = np.clip(t - t0, 0, None)
        out += (t >= t0) * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.22) * 0.22
    return out.astype(np.float32)


def glitch(dur=0.9, seed=3):
    """Garbled static for thoughts the constituent cannot read yet."""
    r = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = r.standard_normal(n)
    gate = (np.sin(2 * np.pi * 13 * t) > -0.2).astype(float)
    tone = np.sign(np.sin(2 * np.pi * (220 + 900 * r.random()) * t)) * 0.3
    seg = int(0.045 * SR)
    for i in range(0, n, seg):
        tone[i:i + seg] *= r.uniform(0.2, 1.0)
        noise[i:i + seg] *= r.uniform(0.1, 1.0)
    env = np.minimum(1, np.minimum(t, dur - t) / 0.03)
    return ((noise * 0.12 + tone * 0.25) * gate * env).astype(np.float32)


def assemble(who, text, lid):
    """Synthesize text, splicing in token sounds. Returns audio and token spans (s)."""
    parts = TOKEN_RE.split(text)
    out, toks, pos = [], [], 0
    gap = np.zeros(int(0.06 * SR), np.float32)
    for i, p in enumerate(parts):
        if i % 2 == 1:
            snd = {"BLEEP": bleep(), "NAME": redact_chime(), "GLITCH": glitch(seed=len(toks) + 3)}[p]
            out += [gap, snd, gap]
            toks.append((p, (pos + len(gap)) / SR, (pos + len(gap) + len(snd)) / SR))
            pos += len(snd) + 2 * len(gap)
        elif re.search(r"[A-Za-z0-9]", p):
            a = synth(who, p.strip(), RATE.get(lid))
            out.append(a)
            pos += len(a)
    return np.concatenate(out), toks


def envelope(a):
    hop = SR // FPS
    n = int(np.ceil(len(a) / hop))
    pad = np.pad(a, (0, n * hop - len(a)))
    rms = np.sqrt((pad.reshape(n, hop) ** 2).mean(1))
    rms = rms / (np.percentile(rms, 95) + 1e-6)
    return np.clip(rms, 0, 1)


def syllables(w):
    return max(1, len(re.findall(r"[aeiouy]+", w.lower()))) + 0.4


def word_times(text, a, spans=None):
    """Rough per-word timings: phrases are matched to detected pauses,
    words inside a phrase are spread by syllable weight."""
    words = text.split()
    if spans is None:
        spans = [(0, len(a) / SR)]
    # detect pauses
    hop = int(0.01 * SR)
    n = len(a) // hop
    rms = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1))
    quiet = rms < 0.02
    pauses = []
    i = 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if (j - i) * 0.01 >= 0.14 and i > 0 and j < n:
                pauses.append(((i + j) / 2 * 0.01, (j - i) * 0.01, i * 0.01, j * 0.01))
            i = j
        else:
            i += 1
    # phrase boundaries after words ending in punctuation
    bounds = [k for k, w in enumerate(words[:-1]) if re.search(r"[,.?!;:]$|\.\.\.$", w)]
    pauses.sort(key=lambda p: -p[1])
    chosen = sorted(pauses[: len(bounds)], key=lambda p: p[0])
    if len(chosen) < len(bounds):
        # not enough audible pauses: fall back to pure syllable spreading
        bounds = []
        chosen = []
    total = len(a) / SR
    seg_edges = [(0.0, None)] + [(p[2], p[3]) for p in chosen] + [(None, total)]
    phrases = []
    start = 0
    for b in bounds + [len(words) - 1]:
        phrases.append(words[start: b + 1])
        start = b + 1
    out = []
    for pi, ph in enumerate(phrases):
        t0 = 0.0 if pi == 0 else seg_edges[pi][1]
        t1 = total if pi == len(phrases) - 1 else seg_edges[pi + 1][0]
        wts = [syllables(w) for w in ph]
        tot = sum(wts)
        t = t0
        for w, wt in zip(ph, wts):
            d = (t1 - t0) * wt / tot
            out.append((w, round(t, 3), round(t + d, 3)))
            t += d
    return out


_asr = None


def asr_words(a):
    global _asr
    from faster_whisper import WhisperModel
    if _asr is None:
        _asr = WhisperModel("small.en", device="cpu", compute_type="int8")
    a16 = resample_poly(a, 160, 441).astype(np.float32)
    segs, _ = _asr.transcribe(a16, language="en", word_timestamps=True, beam_size=5)
    return [(w.word.strip(), round(w.start, 3), round(w.end, 3)) for s in segs for w in s.words]


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def align(text, heard, dur):
    """Map caption words onto Whisper word times; unmatched words are
    interpolated between their matched neighbours."""
    import difflib
    words = text.split()
    times = [None] * len(words)
    sm = difflib.SequenceMatcher(a=[norm(w) for w in words], b=[norm(h[0]) for h in heard], autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            h = heard[blk.b + k]
            times[blk.a + k] = (h[1], h[2])
    # fill gaps
    i = 0
    while i < len(words):
        if times[i] is None:
            j = i
            while j < len(words) and times[j] is None:
                j += 1
            t0 = times[i - 1][1] if i > 0 else 0.0
            t1 = times[j][0] if j < len(words) else dur
            wts = [syllables(w) for w in words[i:j]]
            tot = sum(wts)
            t = t0
            for k in range(i, j):
                d = (t1 - t0) * wts[k - i] / tot
                times[k] = (t, t + d)
                t += d
            i = j
        else:
            i += 1
    return [(w, round(a, 3), round(b, 3)) for w, (a, b) in zip(words, times)]


def main():
    timeline = []
    t = 0.0
    for lid, who, text, pre, post in LINES:
        t += pre
        if who is None:
            timeline.append(dict(id=lid, who=None, start=round(t, 3), end=round(t + post, 3)))
            t += post
            continue
        cache = f"{BUILD}/voice/{lid}.npy"
        meta = f"{BUILD}/voice/{lid}.json"
        if os.path.exists(cache) and os.path.exists(meta) and json.load(open(meta))["text"] == text \
                and json.load(open(meta)).get("voice") == list(VOICES[who]) + [RATE.get(lid)]:
            a = np.load(cache)
        else:
            import difflib
            best = None
            for take in range(5):
                a, toks = assemble(who, text, lid)
                heard = asr_words(a)
                want = [norm(w) for w in TOKEN_RE.sub(" ", text).split()]
                got = [norm(h[0]) for h in heard]
                score = difflib.SequenceMatcher(a=want, b=got).ratio()
                if best is None or score > best[0]:
                    best = (score, a, heard, toks)
                if score >= 0.96:
                    break
            score, a, heard, toks = best
            np.save(cache, a)
            json.dump(dict(text=text, voice=list(VOICES[who]) + [RATE.get(lid)], heard=heard, score=score,
                           tokens=toks), open(meta, "w"))
        dur = len(a) / SR
        cap = CAPTIONS.get(lid, text)
        env = envelope(a)
        toks = json.load(open(meta)).get("tokens", [])
        timeline.append(dict(id=lid, who=who, text=cap, start=round(t, 3), end=round(t + dur, 3),
                             tokens=[(k, round(t + a0, 3), round(t + a1, 3)) for k, a0, a1 in toks],
                             env=[round(float(x), 3) for x in env],
                             words=align(cap, json.load(open(meta))["heard"], dur)))
        heard = " ".join(h[0] for h in json.load(open(meta))["heard"])
        print(f"{lid:9s} {who:6s} {t:7.2f}  {dur:5.2f}s {json.load(open(meta)).get('score', 0):.2f} {heard[:90]}")
        t += dur + post
    json.dump(dict(total=round(t, 3), lines=timeline), open(f"{BUILD}/timeline.json", "w"))
    print(f"TOTAL {t:.1f}s = {int(t // 60)}:{t % 60:04.1f}")


if __name__ == "__main__":
    main()
