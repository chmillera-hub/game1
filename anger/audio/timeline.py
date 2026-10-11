"""Walk script_data.SEQ and produce build/timeline.json with absolute times.

timeline.json schema
{
  "fps": 24, "duration": <seconds>,
  "scenes": [{"id": "s1", "start": .., "end": ..}, ...],
  "lines":  [{"id": "q01", "char": "quill", "text": "..", "start": .., "end": ..}, ...],
  "beats":  {"rae_enters": 16.8, ...},
  "music":  [{"cue": "symphony", "start": .., "end": .., "gain_db": .., "fade_in": .., "fade_out": ..}],
  "sfx":    [{"name": "door_open", "start": .., "gain_db": .., "end": <optional, for loops>,
              "skip": <optional, seconds trimmed off the head of the file>}]
}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import FPS, TIMELINE, VO_DIR  # noqa: E402
from script_data import LINES, MUSIC_CUES, SEQ  # noqa: E402


def build():
    manifest = json.loads((VO_DIR / "manifest.json").read_text())
    now = 0.0
    scenes, lines, music, sfx = [], [], [], []
    beats = {}
    pending_end = []  # (list_entry, beat_name)
    cue_dur = {}      # cue -> played duration of its latest start

    for ev in SEQ:
        kind = ev[0]
        if kind == "scene":
            if scenes:
                scenes[-1]["end"] = round(now, 3)
            scenes.append({"id": ev[1], "start": round(now, 3), "end": None})
        elif kind == "beat":
            off = ev[2] if len(ev) > 2 else 0.0
            beats[ev[1]] = round(now + off, 3)
        elif kind == "wait":
            now += ev[1]
        elif kind in ("line", "line_at", "line_end_at"):
            lid = ev[1]
            dur = manifest[lid]["dur"]
            char, display = LINES[lid][0], LINES[lid][1]
            if kind == "line":
                start = now - (ev[2] if len(ev) > 2 else 0.0)
                now = max(now, start + dur)
            elif kind == "line_at":             # overlay: starts at now + offset, time does not advance
                start = now + ev[2]
            else:                               # overlay that ENDS at now + offset (narration lands on the action)
                start = now + ev[2] - dur
            lines.append({"id": lid, "char": char, "text": display,
                          "start": round(start, 3), "end": round(start + dur, 3)})
        elif kind == "music":
            kw = ev[2] if len(ev) > 2 else {}
            cue = ev[1]
            dur = kw.get("dur", MUSIC_CUES[cue])   # dur < cue length plays only the head (mix.py fades it)
            cue_dur[cue] = dur
            entry = {"cue": cue, "start": round(now, 3), "end": round(now + dur, 3),
                     "gain_db": kw.get("gain_db", 0.0), "fade_in": kw.get("fade_in", 0.0),
                     "fade_out": kw.get("fade_out", 0.0)}
            music.append(entry)
            if "end_beat" in kw:
                pending_end.append((entry, kw["end_beat"]))
        elif kind == "music_hold":
            now += cue_dur.get(ev[1], MUSIC_CUES[ev[1]])
        elif kind == "sfx":
            kw = ev[2] if len(ev) > 2 else {}
            entry = {"name": ev[1], "start": round(now + kw.get("offset", 0.0), 3),
                     "gain_db": kw.get("gain_db", 0.0)}
            if kw.get("skip"):          # play the file from `skip` s in (start time unchanged)
                entry["skip"] = kw["skip"]
            sfx.append(entry)
            if "end_beat" in kw:
                pending_end.append((entry, kw["end_beat"]))
        else:
            raise ValueError(f"unknown event {ev}")

    scenes[-1]["end"] = round(now, 3)
    for entry, b in pending_end:
        entry["end"] = beats[b]
    lines.sort(key=lambda l: l["start"])
    tl = {"fps": FPS, "duration": round(now, 3), "scenes": scenes, "lines": lines,
          "beats": beats, "music": music, "sfx": sfx}
    TIMELINE.write_text(json.dumps(tl, indent=1))
    return tl


if __name__ == "__main__":
    tl = build()
    for s in tl["scenes"]:
        print(f"{s['id']}: {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end']-s['start']:.2f}s)")
    print("duration", tl["duration"])
    for m in tl["music"]:
        print("music", m)
