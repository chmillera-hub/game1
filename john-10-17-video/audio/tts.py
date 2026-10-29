"""Synthesize the narration with Kokoro (am_michael) and build the subtitle timeline.

Usage: python3 -I audio/tts.py <kokoro_dir> <out_dir>
Writes <out_dir>/narration.wav (48 kHz mono) and script/timeline.json.
"""
import difflib, json, os, re, sys

import librosa
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KDIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(f"{OUT}/units", exist_ok=True)

VOICE, SPEED, SR = "am_michael", 0.86, 48000
PAUSE_SCALE = 1.8          # stretch the scripted pauses toward the reference's measured pacing
INTRA_GAP = 0.42           # extra silence inserted at subtitle breaks inside a sentence
ABSOLUTE_PAUSES = {"u27", "u40"}  # chapter break and ending are timed exactly
NARRATION_START = 5.2      # seconds: title card plays first
TAIL = 9.5                 # end card after the last pause

script = json.load(open(f"{ROOT}/script/narration.json"))
units = script["units"]

def tokens(s):
    s = s.replace("’", "'").replace("‘", "'")
    return [w for w in re.findall(r"[a-z0-9']+", s.lower().replace("'", ""))]

def trim(a, sr, thresh_db=-42.0, margin=0.03):
    frame = int(0.01 * sr)
    n = len(a) // frame
    rms = np.sqrt(np.mean(a[: n * frame].reshape(n, frame) ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms / (rms.max() + 1e-12))
    idx = np.where(db > thresh_db)[0]
    s = max(0, idx[0] * frame - int(margin * sr))
    e = min(len(a), (idx[-1] + 1) * frame + int(margin * sr))
    out = a[s:e].copy()
    f = int(0.012 * sr)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out

kokoro = Kokoro(f"{KDIR}/kokoro-v1.0.onnx", f"{KDIR}/voices-v1.0.bin")
asr = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=4)

timeline = {"fps": 24, "width": 720, "height": 1280, "narration_start": NARRATION_START, "units": []}
pieces, cursor = [], NARRATION_START
for u in units:
    tts_tokens = tokens(u["tts"])
    sub_tokens = [tokens(s.replace("|", " ")) for s in u["subs"]]
    assert sum(sub_tokens, []) == tts_tokens, (u["id"], tts_tokens, sub_tokens)

    a, sr = kokoro.create(u["tts"], voice=VOICE, speed=u.get("speed", SPEED), lang="en-us")
    a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
    a = trim(a, SR)
    sf.write(f"{OUT}/units/{u['id']}.wav", a, SR)
    dur = len(a) / SR

    # Word timing via ASR, aligned to the script words.
    y16 = librosa.resample(a, orig_sr=SR, target_sr=16000)
    segs, _ = asr.transcribe(y16, beam_size=5, word_timestamps=True, condition_on_previous_text=False)
    rec = [(tokens(w.word), w.start, w.end) for s in segs for w in (s.words or [])]
    rec_tok, rec_t = [], []
    for toks, ws, we in rec:
        for t in toks:
            rec_tok.append(t); rec_t.append((ws, we))
    times = [None] * len(tts_tokens)
    sm = difflib.SequenceMatcher(a=tts_tokens, b=rec_tok, autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = rec_t[blk.b + k]
    # Interpolate any unmatched words.
    known = [i for i, t in enumerate(times) if t]
    for i in range(len(times)):
        if times[i] is None:
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            s0 = times[prev][1] if prev is not None else 0.0
            s1 = times[nxt][0] if nxt is not None else dur
            times[i] = (s0, s1)
    hyp = " ".join(rec_tok)
    ratio = sm.ratio()
    print(f"{u['id']} dur={dur:5.2f}s match={ratio:.2f}  ASR: {hyp}", flush=True)

    # Open up a short pause at each subtitle break inside the sentence, cutting at
    # the quietest point between the two words so the edit is inaudible.
    bounds, wi = [], 0
    for toks in sub_tokens[:-1]:
        wi += len(toks)
        bounds.append(wi)
    if bounds:
        frame = int(0.005 * SR)
        segs_audio, shift, last, new_times = [], 0.0, 0, list(times)
        for b in bounds:
            g0, g1 = times[b - 1][1], times[b][0]
            lo, hi = int(max(0, min(g0, g1) - 0.06) * SR), int((max(g0, g1) + 0.06) * SR)
            hi = max(hi, lo + 2 * frame)
            n = (hi - lo) // frame
            e = [np.sum(a[lo + k * frame: lo + (k + 1) * frame] ** 2) for k in range(n)]
            cut = lo + int(np.argmin(e)) * frame + frame // 2
            piece = a[last:cut].copy()
            f = int(0.008 * SR)
            if last > 0: piece[:f] *= np.linspace(0, 1, f)
            piece[-f:] *= np.linspace(1, 0, f)
            segs_audio += [piece, np.zeros(int(INTRA_GAP * SR), np.float32)]
            for i in range(b, len(times)):
                new_times[i] = (new_times[i][0] + INTRA_GAP, new_times[i][1] + INTRA_GAP)
            last = cut
        tailp = a[last:].copy(); f = int(0.008 * SR); tailp[:f] *= np.linspace(0, 1, f)
        segs_audio.append(tailp)
        a = np.concatenate(segs_audio).astype(np.float32)
        times = new_times
        dur = len(a) / SR
        sf.write(f"{OUT}/units/{u['id']}.wav", a, SR)

    subs, wi = [], 0
    for s, toks in zip(u["subs"], sub_tokens):
        w0, w1 = wi, wi + len(toks) - 1
        subs.append({"text": s, "speech_start": round(cursor + times[w0][0], 3),
                     "speech_end": round(cursor + min(times[w1][1], dur), 3)})
        wi += len(toks)
    timeline["units"].append({"id": u["id"], "sec": u["sec"], "style": u.get("style", "normal"),
                              "start": round(cursor, 3), "end": round(cursor + dur, 3),
                              "pause": u["pause"], "subs": subs, "asr_match": round(ratio, 3)})
    pieces.append((cursor, a))
    cursor += dur + (u["pause"] if u["id"] in ABSOLUTE_PAUSES else u["pause"] * PAUSE_SCALE)

total = cursor + TAIL
track = np.zeros(int(total * SR) + SR, dtype=np.float32)
for start, a in pieces:
    i = int(round(start * SR))
    track[i:i + len(a)] += a
track = track[: int(total * SR)]
sf.write(f"{OUT}/narration.wav", track, SR, subtype="PCM_24")

# Subtitle display windows: lead in slightly before speech, hold briefly after.
flat = [(ui, s) for ui, u in enumerate(timeline["units"]) for s in u["subs"]]
for k, (ui, s) in enumerate(flat):
    show = s["speech_start"] - 0.15
    if k + 1 < len(flat):
        nxt = flat[k + 1][1]["speech_start"] - 0.15
        hide = min(s["speech_end"] + 0.9, nxt - 0.05)
    else:
        hide = s["speech_end"] + 1.6
    s["show"], s["hide"] = round(show, 3), round(max(hide, s["speech_end"] + 0.1), 3)
timeline["duration"] = round(total, 3)
json.dump(timeline, open(f"{ROOT}/script/timeline.json", "w"), indent=1, ensure_ascii=False)
print(f"total duration {total:.2f}s, narration ends {cursor:.2f}s")
