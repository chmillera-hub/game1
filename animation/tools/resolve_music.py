"""Resolve the anchor-based music plan into an absolute-time cue sheet in PLAY time for audio/music.py.

    python3 tools/resolve_music.py [data/music_plan.json] -> data/music_cues.json
    python3 audio/music.py data/music_cues.json out/music.wav

Plan anchors (from/to/open_at/hits.at) are story-time anchors (data/timeline.json); they are mapped through
data/timewarp.json (tools/speed_dialogue.py) so the score follows the faster dialogue. Anchors: number |
's05' (scene start) | 's05.end' | 's05b03' | 's05b03.end-0.4' | 's05b03.mid+1' | 'film.end'
"""
import json, os, re, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_warp():
    p = os.path.join(ROOT, "data/timewarp.json")
    if not os.path.exists(p):
        return lambda t: t
    k = json.load(open(p))["knots"]
    S = np.array([a for a, _ in k]); P = np.array([b for _, b in k])
    return lambda t: float(P[-1] + (t - S[-1])) if t >= S[-1] else float(np.interp(t, S, P))


def resolver(tl):
    scenes = {s["id"]: s for s in tl["scenes"]}
    def R(a):
        if isinstance(a, (int, float)):
            return float(a)
        if a.strip() == "film.end":
            return tl["duration"]
        m = re.match(r"^([A-Za-z0-9_]+)(\.(start|end|mid))?([+-][0-9.]+)?$", a.strip())
        if not m:
            raise ValueError("bad anchor " + a)
        idn, _, which, off = m.groups()
        rec = tl["beats"].get(idn) or scenes.get(idn)
        if rec is None:
            raise ValueError("unknown anchor " + a)
        which = which or "start"
        base = rec["end"] if which == "end" else (rec["start"] + rec["end"]) / 2 if which == "mid" else rec["start"]
        return base + (float(off) if off else 0.0)
    return R


def main():
    plan = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data/music_plan.json")))
    tl = json.load(open(os.path.join(ROOT, "data/timeline.json")))
    play_path = os.path.join(ROOT, "data/timeline_play.json")
    play = json.load(open(play_path)) if os.path.exists(play_path) else tl
    R, W = resolver(tl), load_warp()
    P = lambda a: round(W(R(a)), 3)
    cues = []
    for c in plan["cues"]:
        cue = {k: v for k, v in c.items() if k not in ("from", "to", "hits", "open_at")}
        cue["start"], cue["end"] = max(0.0, P(c["from"])), min(play["duration"], P(c["to"]))
        if "open_at" in c:
            cue["open_at"] = P(c["open_at"])
        cue["hits"] = [dict({k: v for k, v in h.items() if k != "at"}, t=P(h["at"])) for h in c.get("hits", [])]
        cues.append(cue)
    tl_rel = "data/timeline_play.json" if os.path.exists(play_path) else "data/timeline.json"
    out = {"timeline": tl_rel, "speech_from": tl_rel, "duration": play["duration"], "cues": cues}
    json.dump(out, open(os.path.join(ROOT, "data/music_cues.json"), "w"), indent=1)
    for c in cues:
        print(f"{c['start']:7.2f}-{c['end']:7.2f} {c['mood']:16s} int={c.get('intensity')} "
              f"open={c.get('open_at', '-')} hits={[(h['t'], h['type']) for h in c['hits']]}")


if __name__ == "__main__":
    main()
