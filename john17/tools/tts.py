"""Generate the narration track and timeline for the John 17 video.

Reads script/cues.json, speaks every unit with Kokoro TTS, and writes:
  build/voice.wav      48 kHz mono voice track (narrator + Jesus)
  build/timeline.json  units, subtitle chunks, shots, section cards, lip-sync
Usage: python tools/tts.py   (run from the john17/ folder)
"""
import json, re, os, sys, warnings
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

warnings.filterwarnings("ignore")
from kokoro import KPipeline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 24000
OUT_SR = 48000
FPS = 24

# Shots where Jesus is on screen speaking; elsewhere his lines get a speaker label.
JESUS_VISIBLE = {"title", "jesus_talk", "jesus_lookup", "jesus_pray", "jesus_mcu", "glory", "glory_end"}

cues = json.load(open(os.path.join(ROOT, "script", "cues.json")))
os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)

pipes = {}
def pipeline(voice):
    lang = "b" if voice.startswith("b") else "a"
    if lang not in pipes:
        pipes[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    return pipes[lang]

def is_word(tok):
    return re.search(r"[A-Za-z0-9]", tok) is not None

def speak(text, voice, speed):
    """Return (audio float32 @24k, [(token, start, end)])."""
    pipe = pipeline(voice)
    audio, toks, off = [], [], 0.0
    for r in pipe(text, voice=voice, speed=speed):
        a = r.audio.numpy() if hasattr(r.audio, "numpy") else np.asarray(r.audio)
        for tk in r.tokens or []:
            if tk.start_ts is None or tk.end_ts is None:
                continue
            toks.append((tk.text, off + tk.start_ts, off + tk.end_ts))
        audio.append(a.astype(np.float32))
        off += len(a) / SR
    return np.concatenate(audio), toks

def sentence_pauses(audio, toks, extra):
    """Lengthen the pause after sentence-final punctuation inside a unit."""
    if extra <= 0:
        return audio, toks
    cuts = []
    for i, (t, s, e) in enumerate(toks[:-1]):
        if t in (".", "!", "?", ";", ":", "...", "…") and any(is_word(x[0]) for x in toks[i + 1:]):
            nxt = next(x for x in toks[i + 1:] if is_word(x[0]))
            cuts.append((e + nxt[1]) / 2)
    if not cuts:
        return audio, toks
    pieces, prev, shift_at = [], 0, []
    for c in cuts:
        k = int(c * SR)
        pieces.append(audio[prev:k])
        pieces.append(np.zeros(int(extra * SR), np.float32))
        prev = k
        shift_at.append(c)
    pieces.append(audio[prev:])
    new_toks = []
    for t, s, e in toks:
        sh = extra * sum(1 for c in shift_at if c <= s)
        new_toks.append((t, s + sh, e + sh))
    return np.concatenate(pieces), new_toks

units_out, voice_parts = [], []
t = cues["leadIn"]
voice_track = np.zeros(int(t * SR), np.float32)
prev_end = t

for u in cues["units"]:
    who = u["who"]
    voice = cues["voices"][who]
    speed = cues["speed"][who]
    chunks = [c.strip() for c in u["text"].split("|")]
    tts_text = " ".join(chunks)
    suffix = u.get("ttsSuffix", "")
    audio, toks = speak(tts_text + suffix, voice, speed)
    audio, toks = sentence_pauses(audio, toks, 0.22 if who == "jesus" else 0.15)
    if suffix:
        # The suffix is spoken only so the script's last word is fully articulated; cut it off.
        n_script = len(re.findall(r"[A-Za-z0-9]+", tts_text))
        idx = [i for i, x in enumerate(toks) if is_word(x[0])][n_script]
        cut = toks[idx][1] - 0.06
        audio = audio[:int(cut * SR)]
        toks = [x for x in toks[:idx] if x[2] <= cut + 0.01]
        fade = int(0.04 * SR)
        audio[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)

    words = [x for x in toks if is_word(x[0])]
    lead = max(0.0, words[0][1] - 0.05)
    tail_end = min(len(audio) / SR, toks[-1][2] + 0.15)
    audio = audio[int(lead * SR):int(tail_end * SR)]
    toks = [(x, s - lead, e - lead) for x, s, e in toks]
    words = [x for x in toks if is_word(x[0])]
    dur = len(audio) / SR

    t += u.get("pre", 0.6)
    start = t
    # silence up to this unit, then the unit audio
    gap = int(round(start * SR)) - len(voice_track)
    voice_track = np.concatenate([voice_track, np.zeros(max(0, gap), np.float32), audio])
    t = start + dur

    # assign spoken words to subtitle chunks in order
    chunk_rows, wi = [], 0
    for c in chunks:
        n = len(re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)?", c))
        ws = words[wi:wi + n]
        if len(ws) != n:
            sys.exit(f"word alignment failed in {u['id']}: chunk '{c}' wanted {n} got {len(ws)}")
        chunk_rows.append({"text": c, "start": round(start + ws[0][1], 3), "wend": round(start + ws[-1][2], 3),
                           "words": [[w[0], round(start + w[1], 3), round(start + w[2], 3)] for w in ws]})
        wi += n
    if wi != len(words):
        print(f"warning: {u['id']} spoke {len(words)} words, script has {wi}")

    units_out.append({"id": u["id"], "who": who, "ref": u.get("ref"), "start": round(start, 3),
                      "end": round(t, 3), "pre": u.get("pre", 0.6), "chunks": chunk_rows,
                      "shots": u["shots"], "section": u.get("section")})
    print(f"{u['id']} {who:8s} {start:7.2f}-{t:7.2f}  ({dur:5.2f}s)  {tts_text[:60]}")

# ---- subtitles: each chunk shows from its first word until the next chunk (or shortly after the unit)
subs = []
for ui, u in enumerate(units_out):
    nxt_start = units_out[ui + 1]["start"] if ui + 1 < len(units_out) else u["end"] + 3
    for ci, c in enumerate(u["chunks"]):
        s = c["start"] - 0.08
        if ci + 1 < len(u["chunks"]):
            e = u["chunks"][ci + 1]["start"] - 0.08
        else:
            e = min(u["end"] + 0.55, nxt_start - 0.25)
        subs.append({"start": round(s, 3), "end": round(e, 3), "text": c["text"], "who": u["who"],
                     "unit": u["id"], "chunk": ci})

# ---- shots: cut a little before the line that introduces them
shots = [{"id": "title", "start": 0.0}]
for u in units_out:
    for shot_id, from_chunk in u["shots"]:
        if from_chunk == 0:
            cut = u["start"] - min(0.45, u["pre"] * 0.6)
        else:
            cut = u["chunks"][from_chunk]["start"] - 0.12
        if shots[-1]["id"] == shot_id:
            continue
        shots.append({"id": shot_id, "start": round(cut, 3)})
end_start = units_out[-1]["end"] + 1.6
shots.append({"id": "end", "start": round(end_start, 3)})
total = round(end_start + cues["tail"], 3)
for i, s in enumerate(shots):
    s["end"] = shots[i + 1]["start"] if i + 1 < len(shots) else total

# number repeated uses of a shot so each can get its own camera move
seen = {}
for s in shots:
    seen[s["id"]] = seen.get(s["id"], 0) + 1
    s["take"] = seen[s["id"]]

def shot_at(time):
    for s in shots:
        if s["start"] <= time < s["end"]:
            return s["id"]
    return shots[-1]["id"]

for sub in subs:
    if sub["who"] == "jesus" and sub["chunk"] == 0:
        sub["label"] = None if shot_at(sub["start"] + 0.1) in JESUS_VISIBLE else "JESUS"
    else:
        sub["label"] = None

sections = [{"start": round(u["start"] - 0.3, 3), "end": round(u["start"] + 4.6, 3), **u["section"]}
            for u in units_out if u.get("section")]

# ---- lip sync for Jesus: per-frame mouth opening from the voice envelope
voice_track = np.concatenate([voice_track, np.zeros(int(total * SR) - len(voice_track) + SR, np.float32)])
jesus_mask = np.zeros(len(voice_track), bool)
for u in units_out:
    if u["who"] == "jesus":
        jesus_mask[int(u["start"] * SR):int(u["end"] * SR)] = True
nframes = int(np.ceil(total * FPS))
mouth = []
level = 0.0
for f in range(nframes):
    a, b = int(f / FPS * SR), int((f + 1) / FPS * SR)
    seg = voice_track[a:b]
    if not jesus_mask[a:b].any() or len(seg) == 0:
        target = 0.0
    else:
        db = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
        target = float(np.clip((db + 42) / 26, 0, 1))
    level = target if target > level else level * 0.45 + target * 0.55
    mouth.append(round(level, 3))

peak = np.abs(voice_track).max()
voice_track = voice_track / max(peak, 1e-6) * 0.89
out = resample_poly(voice_track[: int(total * SR)], OUT_SR // SR, 1).astype(np.float32)
sf.write(os.path.join(ROOT, "build", "voice.wav"), out, OUT_SR, subtype="PCM_16")

timeline = {"fps": FPS, "duration": total, "leadIn": cues["leadIn"], "units": units_out, "subs": subs,
            "shots": shots, "sections": sections, "mouth": mouth, "end": cues["end"],
            "copyright": cues["copyright"]}
json.dump(timeline, open(os.path.join(ROOT, "build", "timeline.json"), "w"), ensure_ascii=False)
print(f"total {total:.2f}s  shots {len(shots)}  subs {len(subs)}")
