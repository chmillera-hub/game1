"""Print x264 zones (frame ranges with bitrate multipliers) from the timeline: more bits where detail carries the
story (cosmos reveal, the Void's starry facade, the final tear), fewer in busy alarm scenes."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
S = {s["id"]: s for s in tl["scenes"]}
B = tl["beats"]
F = lambda t: int(round(t * 24))
zones = [
    (S["s13"]["start"], S["s13"]["end"], 1.15),
    (S["s14"]["start"], S["s14"]["end"], 1.5),
    (B["s16b02"]["start"], B["s16b04"]["end"], 1.35),
    (S["s20"]["start"], S["s20"]["end"], 1.25),
    (S["s02"]["start"] + 1, S["s02"]["end"], 0.85),
    (S["s05"]["start"], S["s05"]["end"], 0.85),
    (S["s07"]["start"], S["s07"]["end"], 0.9),
]
zones.sort()
print("/".join(f"{F(a)},{F(b) - 1},b={m}" for a, b, m in zones))
