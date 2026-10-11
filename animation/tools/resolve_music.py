"""Resolve an anchor-based music plan into an absolute-time cue sheet for audio/music.py.

    python3 tools/resolve_music.py [data/music_plan.json] -> data/music_cues.json

Plan format: {"cues": [{"from": anchor, "to": anchor, "mood": str, "intensity": 0..1, "key": opt,
                        "fade_in": s, "fade_out": s, "hits": [{"at": anchor, "type": "swell|sting|drop|silence|resolve"}]}]}
Anchors: number | 's05' (scene start) | 's05.end' | 's05b03' | 's05b03.end-0.4' | 's05b03.mid+1'
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resolver(tl):
    scenes = {s["id"]: s for s in tl["scenes"]}
    def R(a):
        if isinstance(a, (int, float)):
            return float(a)
        m = re.match(r"^([A-Za-z0-9_]+)(\.(start|end|mid))?([+-][0-9.]+)?$", a.strip())
        if not m:
            raise ValueError("bad anchor " + a)
        idn, _, which, off = m.groups()
        rec = tl["beats"].get(idn) or scenes.get(idn)
        if rec is None:
            raise ValueError("unknown anchor " + a)
        which = which or "start"
        base = rec["end"] if which == "end" else (rec["start"] + rec["end"]) / 2 if which == "mid" else rec["start"]
        return round(base + (float(off) if off else 0.0), 3)
    return R

def main():
    plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/music_plan.json")))
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    R = resolver(tl)
    cues = []
    for c in plan["cues"]:
        cue = {k: v for k, v in c.items() if k not in ("from", "to", "hits")}
        cue["start"], cue["end"] = max(0.0, R(c["from"])), min(tl["duration"], R(c["to"]))
        cue["hits"] = [{"t": R(h["at"]), "type": h["type"]} for h in c.get("hits", [])]
        cues.append(cue)
    out = {"duration": tl["duration"], "cues": cues}
    json.dump(out, open(os.path.join(ROOT, "data/music_cues.json"), "w"), indent=1)
    for c in cues:
        print(f"{c['start']:7.2f}-{c['end']:7.2f} {c['mood']:16s} int={c.get('intensity')} hits={[(h['t'], h['type']) for h in c['hits']]}")

if __name__ == "__main__":
    main()
