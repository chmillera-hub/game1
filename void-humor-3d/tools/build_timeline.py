"""Absolute (play-time) seconds for every scene and beat, from the screenplay + generated audio lengths.

    python3 tools/build_timeline.py [data/screenplay.json] [--estimate]
        -> data/timeline.json, data/timeline.txt

Line beats last as long as their audio (data/lines.json); vocal beats as long as data/vocals.json says (or
their `duration`); silent beats their `duration`. `overlap: true` starts a beat together with the previous one
(time then advances to whichever ends later). --estimate uses word counts when audio isn't generated yet.
Word marks (^/~) are converted to absolute times for the score.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPEN_HOLD = 0.6      # frame 0 is the film: only a short breath before the first line
SCENE_LEAD = 0.35
DISSOLVE_LEAD = 0.7
TAIL = 2.5
WPM = {"NARRATOR": 160, "JESUS": 150, "USER": 175, "FEAR": 150, "MAGICIAN": 140}

def load(p):
    p = os.path.join(ROOT, p)
    return json.load(open(p)) if os.path.exists(p) else {}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    estimate = "--estimate" in sys.argv
    sp = json.load(open(args[0] if args else os.path.join(ROOT, "data/screenplay.json")))
    lines = {} if estimate else load("data/lines.json")
    vocals = {} if estimate else load("data/vocals.json")
    t = 0.0
    scenes, beats, order = [], {}, []
    prev_start, prev_end = 0.0, 0.0
    for si, sc in enumerate(sp["scenes"]):
        start = t
        tr = sc.get("transition_in", "cut") if si > 0 else "cut"
        tr = "dissolve" if tr in ("dissolve", "crossfade", "fade") else "cut"
        t += OPEN_HOLD if si == 0 else (DISSOLVE_LEAD if tr == "dissolve" else SCENE_LEAD)
        for b in sc["beats"]:
            kind = b["kind"]
            bstart = prev_start + float(b.get("overlap_offset", 0)) if b.get("overlap") else t
            rec = {"scene": sc["id"], "kind": kind, "start": round(bstart, 3)}
            if kind == "line":
                L = lines.get(b["id"])
                text = re.sub(r"[\^~](?=\w)", "", b["text"])
                if L:
                    dur = L["dur"]; rec["audio"] = L["file"]
                    rec["marks"] = [{**m, "start": round(bstart + m["start"], 3), "end": round(bstart + m["end"], 3)} for m in L.get("marks", [])]
                else:
                    dur = len(re.findall(r"[A-Za-z']+", text)) / WPM.get(b["speaker"], 155) * 60 + 0.3
                rec.update(speaker=b["speaker"], text=text)
            elif kind == "vocal":
                V = vocals.get(b["id"])
                dur = V["dur"] if V else float(b.get("duration", 1.0))
                if V: rec["audio"] = V["file"]
                rec.update(speaker=b["speaker"], vocal=b["vocal"], caption=b.get("caption"))
            else:
                dur = float(b.get("duration", 1.0))
            rec["end"] = round(bstart + dur, 3)
            if b.get("sfx"): rec["sfx"] = b["sfx"]
            beats[b["id"]] = rec
            order.append(b["id"])
            end = bstart + dur
            if b.get("overlap"):
                t = max(prev_end, end)
            else:
                t = end
            prev_start, prev_end = bstart, t
            t += float(b.get("pause_after", 0.0))
        if si == len(sp["scenes"]) - 1:
            t += TAIL
        scenes.append({"id": sc["id"], "slug": sc.get("slug", ""), "location": sc.get("location", ""), "start": round(start, 3),
                       "end": round(t, 3), "transition_in": tr, "music": sc.get("music", {}), "time_of_day": sc.get("time_of_day", "")})
    tl = {"fps": 24, "duration": round(t, 3), "scenes": scenes, "beats": beats, "order": order, "estimated": estimate}
    json.dump(tl, open(os.path.join(ROOT, "data/timeline.json"), "w"), indent=1)
    with open(os.path.join(ROOT, "data/timeline.txt"), "w") as f:
        for sc in scenes:
            f.write(f"\n=== {sc['id']} {sc['slug']} [{sc['start']:.1f} - {sc['end']:.1f}] {sc['location']} ({sc['transition_in']})\n")
            for bid in order:
                b = beats[bid]
                if b["scene"] != sc["id"]: continue
                who = b.get("speaker", "--silent--") + (f"[{b['vocal']}]" if b.get("vocal") else "")
                f.write(f"  {b['start']:7.2f}-{b['end']:7.2f} {bid:8s} {who:22s} {b.get('text', b.get('caption') or '')}\n")
    print(f"timeline: {len(scenes)} scenes, {len(order)} beats, {t:.1f}s ({t/60:.2f} min){' [ESTIMATED]' if estimate else ''}")

if __name__ == "__main__":
    main()
