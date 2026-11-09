"""Voice acting: synthesise every spoken `line` beat of the screenplay with Kokoro TTS (Apache-2.0).

    python3 audio/tts.py [data/screenplay.json] [beat_ids,comma,separated]
        -> audio/wav/<beat>.wav, data/lines.json (dur, whisper word times, ^/~ word marks with times)

Delivery keywords in the beat's `delivery` adjust speed/gaps; shaky/crying deliveries get vibrato + tremolo;
whisper deliveries get an airy EQ. `^word` / `~word` marks are stripped for speech and recorded (with their
aligned times) for the score's high/low word-painting notes. "f***" -> the line is spoken up to that word and
a comedic bleep is appended (the rest of the sentence is dropped).
"""
import json, os, re, subprocess, sys, tempfile, difflib
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100

# blend: [(voice, weight)], speed: kokoro speed, tempo: extra WSOLA time-stretch (1 = none), pitch: resample ratio
VOICES = {
    "NARRATOR": {"blend": [("af_heart", 0.5), ("am_michael", 0.5)], "speed": 0.98, "tempo": 1.0, "pitch": 1.0, "gap": 0.42, "gain_db": 0.0},
    "JESUS":    {"blend": [("am_michael", 0.72), ("am_fenrir", 0.28)], "speed": 0.95, "tempo": 1.0, "pitch": 0.985, "gap": 0.4, "gain_db": 0.0},
    "USER":     {"blend": [("af_bella", 0.7), ("af_sarah", 0.3)], "speed": 1.06, "tempo": 1.0, "pitch": 1.02, "gap": 0.28, "gain_db": 0.0},
    "FEAR":     {"blend": [("af_nicole", 0.5), ("af_bella", 0.5)], "speed": 0.96, "tempo": 0.95, "pitch": 1.12, "gap": 0.4, "gain_db": 0.5},
    "MAGICIAN": {"blend": [("bm_fable", 0.6), ("am_onyx", 0.4)], "speed": 0.9, "tempo": 1.0, "pitch": 0.9, "gap": 0.35, "gain_db": 0.0},
}

# Speech-only rewrites (subtitles keep the screenplay text). Regex -> replacement.
SPEAK_SUBS = [
    (r"\bWhat the actual\b", "What... the actual"),
]
# Whole-phrase phoneme overrides (Kokoro IPA) for words the voice/ASR mangle.
PHONEMES = {
    "teehee.": "tˌiːhˈiː.", "teehee!": "tˌiːhˈiː!", "teehee": "tˌiːhˈiː.", "tee-hee.": "tˌiːhˈiː.", "tee hee.": "tˌiːhˈiː.",
}

def has(d, *words):
    d = (d or "").lower()
    return any(w in d for w in words)

def parse_marks(text):
    """Strip ^/~ marks. Returns (clean_text, [(word_index, word, 'high'|'low')])."""
    marks, out = [], []
    for i, tok in enumerate(text.split()):
        m = re.match(r"^([\"'(.…]*)([\^~])(.+)$", tok)
        if m:
            marks.append((i, re.sub(r"[^A-Za-z']", "", m.group(3)), "high" if m.group(2) == "^" else "low"))
            tok = m.group(1) + m.group(3)
        out.append(tok)
    return " ".join(out), marks

def split_phrases(text):
    parts, buf = [], ""
    for c in re.split(r"(\.\.\.|…)", text):
        if c in ("...", "…"):
            if buf.strip(): parts.append((buf.strip() + "...", 1.0))
            buf = ""
        else:
            buf += c
    if buf.strip(): parts.append((buf.strip(), 0.0))
    out = []
    for p, gm in parts:
        sents = [s for s in re.split(r"(?<=[.?!])\s+", p) if s.strip()]
        for i, s in enumerate(sents):
            out.append((s, 1.0 if i < len(sents) - 1 else gm))
    return out

def trim(a, thr_db=-46, pad=0.03, sr=SR):
    if len(a) == 0: return a
    win = int(sr * 0.01); n = len(a) // win
    if n < 2: return a
    rms = np.sqrt(np.mean(a[: n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    idx = np.where(20 * np.log10(rms + 1e-9) > thr_db)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] * win - int(pad * sr)): min(len(a), (idx[-1] + 1) * win + int(pad * sr))]

def ffmpeg_filter(a, sr, af):
    with tempfile.TemporaryDirectory() as td:
        i, o = os.path.join(td, "i.wav"), os.path.join(td, "o.wav")
        sf.write(i, a, sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", i, "-af", af, "-ar", str(sr), o], check=True)
        b, _ = sf.read(o, dtype="float32")
    return b

def fade(a, sr, fi=0.01, fo=0.04):
    a = a.copy(); ni, no = int(fi * sr), int(fo * sr)
    if ni: a[:ni] *= np.linspace(0, 1, ni)
    if no: a[-no:] *= np.linspace(1, 0, no)
    return a

def bleep(dur=0.42, f=1000.0):
    t = np.arange(int(dur * SR)) / SR
    s = 0.5 * np.sin(2 * np.pi * f * t) + 0.08 * np.sin(2 * np.pi * 2 * f * t)
    return fade(s.astype(np.float32), SR, 0.008, 0.02)

class TTS:
    def __init__(self):
        from kokoro_onnx import Kokoro
        self.k = Kokoro(os.path.join(ROOT, "models/kokoro-v1.0.onnx"), os.path.join(ROOT, "models/voices-v1.0.bin"))
        self.styles = {}
    def style(self, blend):
        key = tuple(blend)
        if key not in self.styles:
            st = None
            for name, w in blend:
                v = self.k.get_voice_style(name) * w
                st = v if st is None else st + v
            self.styles[key] = st
        return self.styles[key]
    def say(self, blend, text, speed):
        ph = PHONEMES.get(text.strip().lower())
        if ph:
            s, sr = self.k.create(ph, voice=self.style(blend), speed=speed, lang="en-us", is_phonemes=True)
        else:
            s, sr = self.k.create(text, voice=self.style(blend), speed=speed, lang="en-us")
        return resample_poly(s, 147, 80).astype(np.float32)  # 24k -> 44.1k

def process(a, cfg, d, inner=False):
    chain = []
    tempo = cfg.get("tempo", 1.0)
    pitch = cfg["pitch"]
    if pitch != 1.0:
        chain.append(f"asetrate={int(SR * pitch)},aresample={SR},atempo={tempo / pitch:.4f}")
    elif tempo != 1.0:
        chain.append(f"atempo={tempo:.4f}")
    if has(d, "trembl", "shak", "cry", "sob", "crack", "tearful", "tears", "quiver", "wobbl"):
        chain.append(f"vibrato=f=5.5:d={0.05 if has(d, 'cry', 'sob') else 0.03}")
        chain.append(f"tremolo=f=7:d={0.16 if has(d, 'cry', 'sob') else 0.1}")
    if has(d, "whisper", "hush"):
        chain.append("highpass=f=180,lowpass=f=7500,volume=-2dB")
    for af in chain:
        a = ffmpeg_filter(a, SR, af)
    return a

def synth_line(tts, beat):
    spk = beat["speaker"]; cfg = VOICES[spk]; d = beat.get("delivery", "")
    text, marks = parse_marks(beat["text"])
    speed, gap = cfg["speed"], cfg["gap"]
    if has(d, "slow", "halting", "measured", "careful", "tender"): speed *= 0.95; gap *= 1.15
    if has(d, "quick", "rush", "panic", "frantic", "blurt", "fast", "snap"): speed *= 1.06; gap *= 0.7
    bleeped = "f***" in text
    say_text = text.split("f***")[0].rstrip(" ,") if bleeped else text
    for pat, rep in SPEAK_SUBS:
        say_text = re.sub(pat, rep, say_text)
    pieces = []
    for phrase, gm in split_phrases(say_text):
        pieces.append(trim(tts.say(cfg["blend"], phrase, speed)))
        pieces.append(np.zeros(int(gap * (1.0 + 0.5 * gm) * SR), np.float32))
    a = np.concatenate(pieces[:-1]) if len(pieces) > 1 else pieces[0]
    a = process(a, cfg, d)
    if bleeped:
        a = np.concatenate([a, np.zeros(int(0.03 * SR), np.float32), bleep() * (np.abs(a).max() * 0.9)])
    a = a * (10 ** (cfg["gain_db"] / 20))
    a = a / (np.max(np.abs(a)) + 1e-9) * 0.85
    return fade(a.astype(np.float32), SR), text, marks, bleeped

def align(asr, a, pad=0.3):
    a16 = resample_poly(np.concatenate([np.zeros(int(pad * SR), np.float32), a]), 160, 441).astype(np.float32)
    segs, _ = asr.transcribe(a16, word_timestamps=True, language="en", beam_size=5)
    return [{"w": w.word.strip(), "start": round(max(0.0, w.start - pad), 3), "end": round(max(0.0, w.end - pad), 3),
             "p": round(w.probability, 3)} for s in segs for w in s.words]

def norm_words(t):
    return re.findall(r"[a-z']+", t.lower().replace("’", "'"))

def mark_times(text, marks, words, dur):
    toks = text.split()
    want = [re.sub(r"[^a-z']", "", t.lower()) for t in toks]
    got = [re.sub(r"[^a-z']", "", w["w"].lower()) for w in words]
    sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
    m = {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n): m[a + k] = words[b + k]
    out = []
    for idx, word, kind in marks:
        w = m.get(idx)
        if w is None:  # interpolate by position
            s = dur * idx / max(1, len(toks)); w = {"start": s, "end": s + 0.3}
        out.append({"word": word, "kind": kind, "start": w["start"], "end": w["end"]})
    return out

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
            a, text, marks, bleeped = synth_line(tts, b)
            words = align(asr, a)
            spoken = text.split("f***")[0] if bleeped else text
            ratio = difflib.SequenceMatcher(None, norm_words(spoken), norm_words(" ".join(w["w"] for w in words))).ratio()
            f = os.path.join("audio/wav", f"{b['id']}.wav")
            sf.write(os.path.join(ROOT, f), a, SR, subtype="PCM_16")
            lines[b["id"]] = {"speaker": b["speaker"], "text": text, "file": f, "dur": round(len(a) / SR, 3),
                              "words": words, "marks": mark_times(text, marks, words, len(a) / SR),
                              "bleep": bleeped, "asr_match": round(ratio, 3)}
            flag = "" if ratio > 0.85 else "   <-- CHECK"
            print(f"{b['id']:8s} {b['speaker']:9s} {len(a)/SR:5.2f}s match={ratio:.2f}{flag} | {text[:70]}", flush=True)
    json.dump(lines, open(out_path, "w"), indent=1)

if __name__ == "__main__":
    main()
