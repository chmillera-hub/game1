"""Lay out absolute times for every scene and beat from the screenplay + generated line durations.

    python3 tools/build_timeline.py [data/screenplay.json]     -> data/timeline.json, data/timeline.txt
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPEN_HOLD = 1.6      # first frame holds (title) before the first beat
SCENE_LEAD = 0.45    # breathing room after a cut before the first beat
DISSOLVE_LEAD = 0.9  # after a dissolve, wait for it to finish
TAIL = 3.0           # hold at the very end

def main():
    sp = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/screenplay.json")))
    lines = json.load(open(os.path.join(ROOT, "data/lines.json")))
    t = 0.0
    scenes, beats, order = [], {}, []
    for si, sc in enumerate(sp["scenes"]):
        start = t
        tr = sc.get("transition_in", "cut") if si > 0 else "cut"
        tr = "dissolve" if tr in ("dissolve", "crossfade", "fade") else "cut"
        t += OPEN_HOLD if si == 0 else (DISSOLVE_LEAD if tr == "dissolve" else SCENE_LEAD)
        for b in sc["beats"]:
            rec = {"scene": sc["id"], "kind": b["kind"], "start": round(t, 3)}
            if b["kind"] == "line":
                L = lines[b["id"]]
                rec.update(speaker=b["speaker"], text=b["text"], inner=bool(b.get("inner")), audio=L["file"])
                t += L["dur"]
            else:
                t += float(b.get("duration", 1.0))
            rec["end"] = round(t, 3)
            if b.get("sfx"):
                rec["sfx"] = b["sfx"]
            beats[b["id"]] = rec
            order.append(b["id"])
            t += float(b.get("pause_after", 0.0))
        if si == len(sp["scenes"]) - 1:
            t += TAIL
        scenes.append({"id": sc["id"], "slug": sc.get("slug", ""), "location": sc.get("location", ""), "start": round(start, 3),
                       "end": round(t, 3), "transition_in": tr, "music": sc.get("music", {})})
    tl = {"fps": 24, "duration": round(t, 3), "scenes": scenes, "beats": beats, "order": order}
    json.dump(tl, open(os.path.join(ROOT, "data/timeline.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data/timeline.txt"), "w") as f:
        for sc in scenes:
            f.write(f"\n=== {sc['id']} {sc['slug']} [{sc['start']:.1f} - {sc['end']:.1f}] {sc['location']} ({sc['transition_in']})\n")
            for bid in order:
                b = beats[bid]
                if b["scene"] != sc["id"]:
                    continue
                who = b.get("speaker", "--silent--") + ("(inner)" if b.get("inner") else "")
                f.write(f"  {b['start']:7.2f}-{b['end']:7.2f} {bid:8s} {who:15s} {b.get('text','')}\n")
    print(f"timeline: {len(scenes)} scenes, {len(order)} beats, {t:.1f}s ({t/60:.2f} min)")

if __name__ == "__main__":
    main()
