"""Synthesize every line, apply character voice FX, QA with Whisper, write the timeline.

Outputs (in build/):
  voices/<id>.wav    48 kHz stereo, processed, ready to mix
  timeline.json      start/end of every line and marker, captions, lip-sync curves
"""
import difflib
import json
import os
import re
import sys
import zlib

import numpy as np
import soundfile as sf

import dsp
from script import SEQ, VOICES

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
VDIR = os.path.join(BUILD, "voices")
SR_TTS, SR = 24000, 48000
FPS = 24

def space_for(lid, speaker):
    if speaker == "narrator":
        return "narr"
    if speaker == "god":
        return "god"
    if speaker == "fear":
        return "fear"
    if lid.startswith(("mp",)):
        return "outside"
    if lid.startswith("p"):
        return "courtyard"
    return "plaza"


def tts():
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(HERE, "models/kokoro-v1.0.onnx"), os.path.join(HERE, "models/voices-v1.0.bin"))
    os.makedirs(VDIR, exist_ok=True)
    for item in SEQ:
        if item["kind"] != "line":
            continue
        path = os.path.join(VDIR, item["id"] + "_dry.wav")
        if os.path.exists(path) and "--force" not in sys.argv:
            continue
        voice, speed, _ = VOICES[item["speaker"]]
        speed = item.get("speed") or speed
        if isinstance(voice, dict):
            voice = sum(w * k.get_voice_style(v) for v, w in voice.items()).astype(np.float32)
        narr = item["speaker"] == "narrator"
        a, sr = k.create(item["text"], voice=voice, speed=speed, lang="en-us",
                         sentence_pause=0.42 if narr else 0.32, clause_pause=0.16 if narr else 0.12)
        a = trim(a.astype(np.float64), sr)
        sf.write(path, a, sr, subtype="FLOAT")
        print(f"  tts {item['id']:5s} {len(a)/sr:5.2f}s  {item['text'][:60]}")


def trim(a, sr, db=-42):
    hop = int(0.01 * sr)
    fr = np.array([dsp.rms(a[i:i + hop]) for i in range(0, len(a), hop)])
    thr = fr.max() * 10 ** (db / 20)
    on = np.where(fr > thr)[0]
    s, e = max(0, (on[0] - 2) * hop), min(len(a), (on[-1] + 4) * hop)
    return dsp.fade(a[s:e], sr, 0.008, 0.03)


IRS = {}


def ir(name):
    if name not in IRS:
        IRS[name] = {
            "narr": lambda: dsp.make_ir(SR, 0.45, 0.7, 0.008, 2, 0.6),
            "plaza": lambda: dsp.make_ir(SR, 1.0, 0.65, 0.025, 3, 0.9),
            "courtyard": lambda: dsp.make_ir(SR, 0.8, 0.65, 0.018, 4, 0.8),
            "outside": lambda: dsp.make_ir(SR, 1.6, 0.75, 0.04, 5, 1.0),
            "fear": lambda: dsp.make_ir(SR, 1.4, 0.8, 0.03, 6, 1.0),
            "god": lambda: dsp.make_ir(SR, 4.8, 0.55, 0.05, 7, 1.0),
        }[name]()
    return IRS[name]


def fx(item, a):
    """a: dry mono at 24 kHz -> processed stereo at 48 kHz."""
    lid, spk = item["id"], item["speaker"]
    seed = zlib.crc32(lid.encode()) % 1000
    if spk == "god":
        wh = dsp.whisperize(a, SR_TTS, seed=seed, tilt=0.5)
        low = dsp.pitch(a, SR_TTS, 0.5)
        shimmer = dsp.whisperize(dsp.pitch(a, SR_TTS, 1.5), SR_TTS, seed=seed + 1)
        mono = 0.66 * a + 0.62 * wh + 0.36 * low + 0.10 * shimmer
        mono = dsp.highpass(mono, SR_TTS, 60)
        x = dsp.resample(mono, SR_TTS, SR)
        # slow stereo drift so it seems to come from everywhere
        t = np.arange(len(x)) / SR
        p = 0.35 * np.sin(2 * np.pi * 0.23 * t + seed)
        st = np.stack([x * np.sqrt(0.5 - p / 2), x * np.sqrt(0.5 + p / 2)], 1) * 1.41
        out = dsp.reverb(st, ir("god"), wet=0.55, dry=0.75)
        return out * 0.9
    if spk == "fear":
        wh = dsp.whisperize(dsp.pitch(a, SR_TTS, 0.86), SR_TTS, seed=seed, tilt=0.6)
        low = dsp.pitch(a, SR_TTS, 0.7)
        mono = 0.95 * wh + 0.22 * low
        t = np.arange(len(mono)) / SR_TTS
        mono *= 1 - 0.28 * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t))
        x = dsp.resample(mono, SR_TTS, SR)
        t = np.arange(len(x)) / SR
        p = 0.8 * np.sin(2 * np.pi * 0.45 * t + 1.0)   # circles from ear to ear
        st = np.stack([x * np.sqrt(0.5 - p / 2), x * np.sqrt(0.5 + p / 2)], 1) * 1.41
        return dsp.reverb(st, ir("fear"), wet=0.35, dry=1.0)
    if spk == "moses_w":
        wh = dsp.whisperize(a, SR_TTS, seed=seed, tilt=0.4)
        mono = 0.8 * a + 0.55 * wh
        mono = dsp.lowpass(mono, SR_TTS, 7000)
        x = dsp.resample(mono, SR_TTS, SR)
        return dsp.reverb(x, ir("outside"), wet=0.10, dry=1.0)
    x = dsp.resample(dsp.highpass(a, SR_TTS, 70), SR_TTS, SR)
    space = space_for(lid, spk)
    wet = {"narr": 0.05, "plaza": 0.11, "courtyard": 0.09, "outside": 0.08}[space]
    return dsp.reverb(x, ir(space), wet=wet, dry=1.0)


def lipsync(a, sr):
    """Per video frame: mouth openness (0..1) and brightness (0..1, 'ee' vs 'oo')."""
    n = int(np.ceil(len(a) / sr * FPS))
    opens, brights = [], []
    win = int(sr / FPS * 1.4)
    for i in range(n):
        c = int((i + 0.5) / FPS * sr)
        seg = a[max(0, c - win // 2):c + win // 2]
        if len(seg) < 32:
            opens.append(0.0)
            brights.append(0.5)
            continue
        db = 20 * np.log10(dsp.rms(seg) + 1e-9)
        opens.append(float(np.clip((db + 42) / 26, 0, 1)))
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        f = np.fft.rfftfreq(len(seg), 1 / sr)
        band = (f > 200) & (f < 4000)
        cen = float((spec[band] * f[band]).sum() / (spec[band].sum() + 1e-9))
        brights.append(float(np.clip((cen - 900) / 1300, 0, 1)))
    o = np.array(opens)
    o = np.convolve(o, [0.25, 0.5, 0.25], mode="same")
    return [round(v, 3) for v in o], [round(v, 2) for v in brights]


def caption_chunks(text, max_words=9):
    sents = re.findall(r"[^.?!]+[.?!]*(?:\.\.\.)?\s*", text.strip())
    chunks = []
    for s in sents:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) <= max_words:
            chunks.append(s)
            continue
        parts = [p.strip() for p in re.split(r"(?<=,)\s+|(?<=:)\s+", s) if p.strip()]
        cur = ""
        for p in parts:
            if cur and len((cur + " " + p).split()) > max_words:
                chunks.append(cur)
                cur = p
            else:
                cur = (cur + " " + p).strip()
        if cur:
            chunks.append(cur)
    # fold dangling fragments ("He...", "Moses.", "Sometimes,") into the next chunk
    merged = []
    i = 0
    while i < len(chunks):
        c = chunks[i]
        short = len(c.split()) == 1 or (len(c.split()) <= 2 and c.endswith(("...", ",")))
        if short and i + 1 < len(chunks):
            chunks[i + 1] = c + " " + chunks[i + 1]
        else:
            merged.append(c)
        i += 1
    chunks = merged
    # still-long chunks: split in half at a word boundary
    out = []
    for c in chunks:
        w = c.split()
        while len(w) > max_words + 3:
            h = len(w) // 2
            out.append(" ".join(w[:h]))
            w = w[h:]
        out.append(" ".join(w))
    return out


def norm_words(s):
    return re.sub(r"[^a-z' ]", " ", s.lower().replace("—", " ")).split()


def qa_and_timing(lines):
    from faster_whisper import WhisperModel
    m = WhisperModel("small.en", device="cpu", compute_type="int8")
    report = []
    for it in lines:
        a, sr = sf.read(os.path.join(VDIR, it["id"] + "_dry.wav"), dtype="float32")
        a16 = dsp.resample(a.astype(np.float64), sr, 16000).astype(np.float32)
        segs, _ = m.transcribe(a16, word_timestamps=True, language="en")
        words = [w for s in segs for w in (s.words or [])]
        heard = " ".join(w.word.strip() for w in words)
        ratio = difflib.SequenceMatcher(None, norm_words(it["text"]), norm_words(heard)).ratio()
        it["heard"], it["match"] = heard, round(ratio, 2)
        it["words"] = [[round(w.start, 2), round(w.end, 2)] for w in words]
        it["words_n"] = len(words)
        report.append(f"{it['id']:5s} {ratio:4.2f} | {heard}")
    return report


def build():
    tts()
    lines = []
    t = 0.0
    marks, items = {}, []
    for item in SEQ:
        if item["kind"] == "mark":
            marks[item["id"]] = round(t, 3)
        elif item["kind"] == "gap":
            t += item["dur"]
        elif item["kind"] == "sfx":
            items.append({"id": item["id"], "kind": "sfx", "start": round(t, 3), "end": round(t + item["dur"], 3)})
            marks[item["id"]] = round(t, 3)
            t += item["dur"] + item["gap"]
        else:
            a, sr = sf.read(os.path.join(VDIR, item["id"] + "_dry.wav"), dtype="float64")
            dur = len(a) / sr
            out = fx(item, a)
            peak = np.abs(out).max()
            if peak > 0.98:
                out *= 0.98 / peak
            sf.write(os.path.join(VDIR, item["id"] + ".wav"), out.astype(np.float32), SR, subtype="FLOAT")
            op, br = lipsync(a, sr)
            rec = {"id": item["id"], "kind": "line", "speaker": item["speaker"], "text": item["text"],
                   "caption": item["caption"] or item["text"], "style": VOICES[item["speaker"]][2],
                   "start": round(t, 3), "end": round(t + dur, 3), "open": op, "bright": br}
            items.append(rec)
            lines.append(rec)
            marks[item["id"]] = round(t, 3)
            t += dur + item["gap"]
    marks["total"] = round(t, 3)

    report = qa_and_timing(lines)
    time_captions(lines)
    with open(os.path.join(BUILD, "timeline.json"), "w") as f:
        json.dump({"marks": marks, "items": items, "fps": FPS}, f)
    print("\n".join(report))
    print(f"\nTOTAL {t:.1f}s = {int(t // 60)}:{t % 60:04.1f}")


def time_captions(lines):
    """Caption chunks timed from Whisper's word timestamps."""
    for it in lines:
        chunks = caption_chunks(it["caption"])
        n_words = sum(len(c.split()) for c in chunks)
        ws = it["words"]
        caps, wi = [], 0
        for c in chunks:
            k = len(c.split())
            if ws:
                a = ws[min(len(ws) - 1, round(wi * len(ws) / n_words))][0]
            else:
                a = (it["end"] - it["start"]) * wi / n_words
            caps.append([round(it["start"] + a, 2), c])
            wi += k
        caps[0][0] = it["start"]
        it["caps"] = caps


if __name__ == "__main__":
    build()
