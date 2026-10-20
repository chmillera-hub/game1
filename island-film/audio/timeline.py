# script.json + build/lines.json -> build/timeline.json (absolute times) + build/dialogue.wav (48 kHz mono)
import json, os
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = json.load(open(os.path.join(ROOT, "script.json")))
lines = json.load(open(os.path.join(ROOT, "build", "lines.json")))
FPS = sc["fps"]

t = 0.0
shots, notes = [], []
for sh in sc["shots"]:
    start = t
    cur = t + sh["pad"]
    out_lines = []
    for ln in sh["lines"]:
        info = lines[ln["id"]]
        ls = cur + ln["gap"]
        le = ls + info["dur"]
        out_lines.append({**{k: ln[k] for k in ("id", "speaker", "text", "vo", "emotion")},
                          "start": round(ls, 3), "end": round(le, 3),
                          "words": [{"w": w["w"], "start": round(ls + w["start"], 3), "end": round(ls + w["end"], 3)}
                                    for w in info["words"]]})
        for n in ln["notes"]:
            key = n["word"].lower().strip(".,!?…")
            hit = next((w for w in out_lines[-1]["words"] if w["w"].lower().strip(".,!?…") == key), None)
            if hit:
                notes.append({"t": hit["start"], "end": hit["end"], "type": n["type"], "word": n["word"],
                              "line": ln["id"]})
            else:
                print("note word not found", ln["id"], n["word"])
        cur = le
    end = max(cur + sh["tail"], start + sh["minDur"])
    # snap shot boundaries to frames
    end = round(end * FPS) / FPS
    shots.append({**{k: sh[k] for k in ("id", "scene", "setting", "framing", "desc", "mood")},
                  "start": round(start, 4), "end": round(end, 4), "dur": round(end - start, 4),
                  "lines": out_lines})
    t = end

tl = {"title": sc["title"], "fps": FPS, "width": sc["width"], "height": sc["height"], "duration": round(t, 4),
      "frames": int(round(t * FPS)), "shots": shots, "notes": notes}
json.dump(tl, open(os.path.join(ROOT, "build", "timeline.json"), "w"), indent=1)

# dialogue stem
SR = 48000
dia = np.zeros(int((t + 1) * SR))
for sh in shots:
    for ln in sh["lines"]:
        y, sr = sf.read(os.path.join(ROOT, "build", "voices", ln["id"] + ".wav"))
        a = int(ln["start"] * SR)
        dia[a:a + len(y)] += y
sf.write(os.path.join(ROOT, "build", "dialogue.wav"), dia[:int(t * SR)], SR, subtype="PCM_16")
print(f"duration {t:.1f}s  frames {tl['frames']}  shots {len(shots)}  notes {len(notes)}")
for sh in shots:
    print(f"{sh['id']} {sh['start']:7.2f} {sh['dur']:5.2f}  {sh['framing']}")
