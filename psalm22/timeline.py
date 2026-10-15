"""Build timeline.json: global frame ranges for every shot, synced to the narration.

Usage: python3 psalm22/timeline.py   (after audio/tts.py)
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("WORK", "/opt/work/psalm22")
FPS = 24
LEAD_BLOCK = 0.6      # cut this many seconds before a block's first phrase
DISSOLVE = 14         # frames of overlap for dissolves (rendered as tail of the previous shot)


def main():
    ph = json.load(open(os.path.join(WORK, "audio", "phrases.json")))
    shots = json.load(open(os.path.join(ROOT, "text", "shots.json")))["shots"]
    # shots without a script are folded into the previous shot (it simply runs longer)
    have = lambda sid: os.path.exists(os.path.join(ROOT, "blender", "shots", sid + ".py"))
    dropped = [s["id"] for s in shots if not have(s["id"])]
    if dropped and os.environ.get("KEEP_MISSING") != "1":
        print("folding shots without scripts into the previous shot:", " ".join(dropped))
        shots = [s for s in shots if have(s["id"])]
    phrases = ph["phrases"]
    total = ph["total"]
    by_block = {}
    for p in phrases:
        by_block.setdefault(p["block"], []).append(p)

    cuts = []
    for s in shots:
        if s["block"] == "intro":
            cuts.append(0.0)
            continue
        bp = by_block[s["block"]]
        i = s["from"]
        if i == 0:
            cuts.append(bp[0]["start"] - LEAD_BLOCK)
        else:
            cuts.append((bp[i - 1]["end"] + bp[i]["start"]) / 2 - 0.08)
    total_frames = int(round(total * FPS))
    starts = [int(round(c * FPS)) for c in cuts]
    out = []
    for k, s in enumerate(shots):
        f0 = starts[k]
        f1 = starts[k + 1] if k + 1 < len(shots) else total_frames
        nxt = shots[k + 1]["transition_in"] if k + 1 < len(shots) else None
        tail = DISSOLVE if nxt == "dissolve" else 0
        t0 = f0 / FPS
        rel = [{"text": p["text"], "start": round(p["start"] - t0, 3), "end": round(p["end"] - t0, 3)}
               for p in phrases if p["end"] > t0 and p["start"] < f1 / FPS]
        e = dict(s)
        e.update({"start_frame": f0, "nframes": f1 - f0, "tail": tail,
                  "render_frames": f1 - f0 + tail, "seconds": round((f1 - f0) / FPS, 2),
                  "phrases": rel})
        out.append(e)
    tl = {"fps": FPS, "total_frames": total_frames, "total_seconds": total,
          "dissolve_frames": DISSOLVE, "render_resolution": [540, 960],
          "final_resolution": [720, 1280], "shots": out}
    json.dump(tl, open(os.path.join(ROOT, "timeline.json"), "w"), indent=1, ensure_ascii=False)
    for e in out:
        print("%-5s %5d +%4d (%5.2fs) tail %2d  %s" % (e["id"], e["start_frame"], e["nframes"], e["seconds"], e["tail"], e["title"]))
    print("total frames", total_frames, "render frames", sum(e["render_frames"] for e in out))


if __name__ == "__main__":
    main()
