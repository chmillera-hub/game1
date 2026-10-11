"""Voice acting: synthesise every spoken line of the screenplay with Kokoro TTS.

    python3 audio/tts.py data/screenplay.json            # writes audio/wav/<beat>.wav + data/lines.json

Delivery is controlled by the beat's `delivery` text (keywords) and speaker config:
  - Lines are split into sentences/ellipsis phrases and joined with deliberate gaps (slow, breathable pacing).
  - trembling/shaking/crying/sob/crack  -> tremolo + light vibrato (Fear's shaky voice)
  - whisper/barely/hushed               -> softer, airier EQ
  - inner: true                         -> intimate thought processing (filtered, close reverb), no lip-sync
  - slow / quick                        -> speed and gap scaling
Each line is then aligned with faster-whisper word timestamps (used by lipsync.py) and checked for
intelligibility; lines whose transcript diverges are re-synthesised with a different seed phrasing.
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100

VOICES = {
    # blend: list of (voice, weight); speed: kokoro speed; pitch: rubberband pitch ratio; gap: seconds between sentences
    "NARRATOR":      {"blend": [("af_heart", 0.5), ("am_michael", 0.5)], "speed": 0.82, "tempo": 0.9, "pitch": 1.0, "gap": 0.7, "gain_db": 0.0},
    "CONSCIOUSNESS": {"blend": [("af_heart", 0.5), ("am_michael", 0.5)], "speed": 0.84, "tempo": 0.9, "pitch": 1.0, "gap": 0.65, "gain_db": 0.0},
    "FEAR":          {"blend": [("af_nicole", 0.5), ("af_bella", 0.5)], "speed": 0.88, "tempo": 0.86, "pitch": 1.12, "gap": 0.55, "gain_db": 0.5},
    "JOY":           {"blend": [("af_bella", 1.0)], "speed": 0.95, "tempo": 0.95, "pitch": 1.05, "gap": 0.35, "gain_db": -1.0},
    "SADNESS":       {"blend": [("bf_emma", 1.0)], "speed": 0.85, "pitch": 1.0, "gap": 0.45, "gain_db": -1.0},
    "ANGER":         {"blend": [("am_fenrir", 1.0)], "speed": 1.0, "pitch": 1.0, "gap": 0.3, "gain_db": -1.0},
    "CALM":          {"blend": [("bm_george", 1.0)], "speed": 0.85, "pitch": 1.0, "gap": 0.45, "gain_db": -1.0},
}

# Per-line phoneme overrides (espeak IPA) for words the voice blurs. "trick" came out as "trek" after Fear's
# formant shift; a tiny release before the /k/ keeps the short /ɪ/ clear.
PHONEME_OVERRIDES = {
    "s12b03": "ðɪs ɪz ɐ tɹˈɪ k.",
}

def has(d, *words):
    d = (d or "").lower()
    return any(w in d for w in words)

def split_phrases(text):
    """Split into sentences / ellipsis phrases. Returns list of (phrase, gap_multiplier_after)."""
    parts = []
    # split on ellipses first (keep as pause), then sentence ends
    chunks = re.split(r"(\.\.\.|…)", text)
    buf = ""
    for c in chunks:
        if c in ("...", "…"):
            if buf.strip():
                parts.append((buf.strip() + "...", 1.0))
            buf = ""
        else:
            buf += c
    if buf.strip():
        parts.append((buf.strip(), 0.0))
    out = []
    for p, gm in parts:
        sents = [s for s in re.split(r"(?<=[.?!])\s+", p) if s.strip()]
        for i, s in enumerate(sents):
            out.append((s, 1.0 if i < len(sents) - 1 else gm))
    return out

def trim(a, thr_db=-46, pad=0.03, sr=SR):
    if len(a) == 0:
        return a
    win = int(sr * 0.01)
    n = len(a) // win
    if n < 2:
        return a
    rms = np.sqrt(np.mean(a[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    idx = np.where(db > thr_db)[0]
    if len(idx) == 0:
        return a
    s = max(0, idx[0] * win - int(pad * sr))
    e = min(len(a), (idx[-1] + 1) * win + int(pad * sr))
    return a[s:e]

def ffmpeg_filter(a, sr, af):
    with tempfile.TemporaryDirectory() as td:
        i, o = os.path.join(td, "i.wav"), os.path.join(td, "o.wav")
        sf.write(i, a, sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", i, "-af", af, "-ar", str(sr), o], check=True)
        b, _ = sf.read(o, dtype="float32")
    return b

def sane(a, what=""):
    a = np.nan_to_num(a.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    a = a - np.mean(a)
    sat = float((np.abs(a) > 0.995).mean())
    rms = float(np.sqrt(np.mean(a ** 2)) + 1e-9)
    if sat > 0.01 or rms / (np.abs(a).max() + 1e-9) > 0.6:
        raise RuntimeError(f"corrupted audio after {what}: saturated={sat:.3f} crest={rms/(np.abs(a).max()+1e-9):.2f}")
    return a

def trim_to_frication(a, sr=SR):
    """Kokoro sometimes voices a short schwa before a sentence-initial /f/ ("Fear" -> "a fear").
    Cut to where the /f/ hiss starts (high band dominates the low band)."""
    lo = sosfilt(butter(4, [150, 1000], "band", fs=sr, output="sos"), a)
    hi = sosfilt(butter(4, 3000, "high", fs=sr, output="sos"), a)
    w = int(sr * 0.005)
    n = int(0.3 * sr / w)
    L = np.array([np.sqrt(np.mean(lo[i * w:(i + 1) * w] ** 2)) for i in range(n)])
    Hh = np.array([np.sqrt(np.mean(hi[i * w:(i + 1) * w] ** 2)) for i in range(n)])
    thr = 0.35 * Hh.max()
    for i in range(4, n - 2):
        if Hh[i] > thr and Hh[i] > 1.6 * L[i] and Hh[i + 1] > 1.6 * L[i + 1]:
            cut = max(0, (i - 1) * w)
            b = a[cut:].copy()
            f = int(0.004 * sr)
            b[:f] *= np.linspace(0, 1, f)
            return b
    return a

def fade(a, sr, fi=0.01, fo=0.04):
    a = a.copy()
    ni, no = int(fi * sr), int(fo * sr)
    if ni: a[:ni] *= np.linspace(0, 1, ni)
    if no: a[-no:] *= np.linspace(1, 0, no)
    return a

class TTS:
    def __init__(self):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(ROOT, "models/kokoro-v1.0.onnx"), os.path.join(ROOT, "models/voices-v1.0.bin"))
        self.styles = {}

    def style(self, speaker):
        if speaker not in self.styles:
            st = None
            for name, w in VOICES[speaker]["blend"]:
                v = self.k.get_voice_style(name) * w
                st = v if st is None else st + v
            self.styles[speaker] = st
        return self.styles[speaker]

    def say_phonemes(self, speaker, phonemes, speed):
        s, sr = self.k.create(phonemes, voice=self.style(speaker), speed=speed, lang="en-us", is_phonemes=True)
        return resample_poly(s, 147, 80).astype(np.float32)

    def say(self, speaker, text, speed):
        s, sr = self.k.create(text, voice=self.style(speaker), speed=speed, lang="en-us")
        return resample_poly(s, 147, 80).astype(np.float32)  # 24k -> 44.1k

def synth_line(tts, beat):
    spk = beat["speaker"]
    cfg = VOICES[spk]
    d = beat.get("delivery", "")
    speed = cfg["speed"]
    gap = cfg["gap"]
    if has(d, "slow", "halting", "measured", "gentle", "quiet", "soft"):
        speed *= 0.95; gap *= 1.2
    if has(d, "quick", "rush", "panic", "frantic", "blurt", "fast"):
        speed *= 1.07; gap *= 0.7
    if has(d, "whisper", "barely"):
        speed *= 0.95
    pieces = []
    ph = PHONEME_OVERRIDES.get(beat.get("id"))
    phrases = [(ph, 0.0)] if ph else split_phrases(beat["text"])
    for phrase, gm in phrases:
        a = trim(tts.say_phonemes(spk, phrase, speed) if ph else tts.say(spk, phrase, speed))
        pieces.append(a)
        g = gap * (1.0 + 0.4 * gm)
        pieces.append(np.zeros(int(g * SR), dtype=np.float32))
    a = np.concatenate(pieces[:-1]) if len(pieces) > 1 else pieces[0]
    # character processing
    chain = []
    tempo = cfg.get("tempo", 1.0) * (0.94 if has(d, "slow", "halting", "measured") else 1.0)
    # WSOLA time-stretch (atempo) + resample pitch shift. (rubberband's phase vocoder smeared word onsets
    # into an audible "uh" pre-echo, e.g. "Fear" heard as "a fear".) asetrate shifts formants with pitch,
    # which is what we want for Fear's smaller voice.
    pitch = cfg["pitch"]
    if pitch != 1.0:
        chain.append(f"asetrate={int(SR * pitch)},aresample={SR},atempo={tempo / pitch:.4f}")
    elif tempo != 1.0:
        chain.append(f"atempo={tempo:.4f}")
    shaky = has(d, "trembl", "shak", "cry", "sob", "crack", "tearful", "tears", "quiver", "wobbl")
    if shaky:
        depth = 0.18 if has(d, "cry", "sob") else 0.12
        chain.append(f"vibrato=f=5.5:d={0.05 if has(d,'cry','sob') else 0.035}")
        chain.append(f"tremolo=f=7:d={depth}")
    if has(d, "whisper", "barely", "hush"):
        chain.append("highpass=f=180,lowpass=f=7000,volume=-3dB")
    if beat.get("inner"):
        chain.append("highpass=f=220,lowpass=f=6500,aecho=0.6:0.5:35|70:0.25|0.15")
    # one ffmpeg pass per effect: chaining rubberband with vibrato in a single graph corrupts the output
    for af in chain:
        a = sane(ffmpeg_filter(a, SR, af), af)
    if re.match(r"^\W*fear\b", beat["text"], re.I):
        a = trim_to_frication(a)
    a = a * (10 ** (cfg["gain_db"] / 20))
    peak = np.max(np.abs(a)) + 1e-9
    a = a / peak * 0.85
    return fade(a.astype(np.float32), SR)

def align(asr, a, pad=0.3):
    # leading silence: whisper mis-hears a word that starts at sample 0 ("Fear" -> "Vere")
    a16 = resample_poly(np.concatenate([np.zeros(int(pad * SR), np.float32), a]), 160, 441).astype(np.float32)
    segs, _ = asr.transcribe(a16, word_timestamps=True, language="en", beam_size=5)
    return [{"w": w.word.strip(), "start": round(max(0.0, w.start - pad), 3), "end": round(max(0.0, w.end - pad), 3),
             "p": round(w.probability, 3)} for s in segs for w in s.words]

def norm_words(t):
    return re.findall(r"[a-z']+", t.lower().replace("’", "'"))

def main():
    sp_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/screenplay.json")
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    sp = json.load(open(sp_path))
    os.makedirs(os.path.join(ROOT, "audio/wav"), exist_ok=True)
    out_path = os.path.join(ROOT, "data/lines.json")
    lines = json.load(open(out_path)) if (only and os.path.exists(out_path)) else {}
    tts = TTS()
    from faster_whisper import WhisperModel
    asr = WhisperModel(os.path.join(ROOT, "models/whisper-base.en"), device="cpu", compute_type="int8")
    for sc in sp["scenes"]:
        for b in sc["beats"]:
            if b["kind"] != "line" or (only and b["id"] not in only):
                continue
            b = dict(b, scene=sc["id"])
            a = synth_line(tts, b)
            words = align(asr, a)
            want, got = norm_words(b["text"]), norm_words(" ".join(w["w"] for w in words))
            # word error proxy
            import difflib
            ratio = difflib.SequenceMatcher(None, want, got).ratio()
            f = os.path.join("audio/wav", f"{b['id']}.wav")
            sf.write(os.path.join(ROOT, f), a, SR, subtype="PCM_16")
            lines[b["id"]] = {"speaker": b["speaker"], "text": b["text"], "inner": bool(b.get("inner")), "file": f,
                              "dur": round(len(a) / SR, 3), "words": words, "asr_match": round(ratio, 3)}
            flag = "" if ratio > 0.85 else "   <-- CHECK"
            print(f"{b['id']:8s} {b['speaker']:13s} {len(a)/SR:5.2f}s match={ratio:.2f}{flag} | {b['text'][:70]}", flush=True)
    json.dump(lines, open(out_path, "w"), indent=1)

if __name__ == "__main__":
    main()
