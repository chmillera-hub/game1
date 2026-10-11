"""Contact sheets of every caption in context (one frame at each caption's midpoint, play time).
    python3 tools/subs_sheets.py      -> out/qa/subs_<n>.png (24 captions per sheet)"""
import json, os, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
caps = json.load(open(os.path.join(ROOT, "data/subtitles.json")))["captions"]
os.makedirs(os.path.join(ROOT, "out/qa"), exist_ok=True)
tl = json.load(open(os.path.join(ROOT, "data/timeline_play.json")))
for k in range(0, len(caps), 24):
    group = caps[k:k + 24]
    # render.mjs --sheet needs a scene id; any id works when --times are given, labels show the beat
    times = ",".join(str(round((c["start"] + c["end"]) / 2, 3)) for c in group)
    out = os.path.join(ROOT, f"out/qa/subs_{k // 24 + 1}.png")
    subprocess.run(["node", "src/render.mjs", "--sheet", group[0]["scene"], "--times", times, "--out", out], cwd=ROOT, check=True)
    print(out, f"captions {k + 1}-{k + len(group)}")
