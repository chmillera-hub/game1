"""Timeline: turns script.json + synthesized line durations into scene timing.

Scenes never hard-code dialogue times. They ask SceneInfo for line/cue times,
so re-recording a line (different length) keeps the animation in sync.
"""
import json
import os
import bisect

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "script.json")
TIMELINE = os.path.join(ROOT, "out", "timeline.json")
LIP = os.path.join(ROOT, "out", "lipsync.json")

LIP_RATE = 100  # lip-sync samples per second


class Line:
    def __init__(self, d):
        self.id = d["id"]
        self.who = d["who"]
        self.text = d["text"]
        self.caption = d.get("caption", d["text"])
        self.start = d["start"]          # scene-local seconds
        self.end = d["end"]
        self.gstart = d["gstart"]        # global seconds
        self.meta = d.get("meta", {})
        self.nocap = d.get("nocap", False)

    @property
    def dur(self):
        return self.end - self.start

    def progress(self, t):
        return 0.0 if t <= self.start else 1.0 if t >= self.end else (t - self.start) / self.dur

    def __repr__(self):
        return f"<Line {self.id} {self.who} {self.start:.2f}-{self.end:.2f}>"


class SceneInfo:
    def __init__(self, d, lip):
        self.id = d["id"]
        self.module = d["module"]
        self.start = d["start"]          # global seconds
        self.dur = d["dur"]
        self.cues = d["cues"]            # name -> scene-local seconds
        self.lines = [Line(x) for x in d["lines"]]
        self.meta = d.get("meta", {})
        self._by_id = {l.id: l for l in self.lines}
        self._lip = lip

    # --- lookups -----------------------------------------------------------
    def cue(self, name, default=None):
        if name in self.cues:
            return self.cues[name]
        if default is not None:
            return default
        raise KeyError(f"cue '{name}' not in scene {self.id}: {sorted(self.cues)}")

    def line(self, lid):
        return self._by_id[lid]

    def lines_of(self, who):
        return [l for l in self.lines if l.who == who]

    def active_line(self, t, who=None):
        for l in self.lines:
            if l.start <= t < l.end and (who is None or l.who == who):
                return l
        return None

    def last_line(self, t, who=None):
        """Most recent line that has started by t (or None)."""
        best = None
        for l in self.lines:
            if l.start <= t and (who is None or l.who == who):
                best = l
        return best

    def talking(self, who, t):
        return self.active_line(t, who) is not None

    def mouth(self, who, t):
        """(open 0..1, wide -1..1) for character `who` at scene time t."""
        l = self.active_line(t, who)
        if l is None:
            return (0.0, 0.0)
        env = self._lip.get(l.id)
        if not env:
            return (0.0, 0.0)
        i = int((t - l.start) * LIP_RATE)
        if i < 0 or i >= len(env["open"]):
            return (0.0, 0.0)
        return (env["open"][i], env["wide"][i])

    def word_at(self, t, lid):
        """Index of the word being spoken in line `lid` at time t (estimate)."""
        l = self._by_id[lid]
        env = self._lip.get(lid)
        if not env or t < l.start:
            return -1
        return bisect.bisect_right(env["word_starts"], t - l.start) - 1


class Timeline:
    def __init__(self, path=TIMELINE, lip_path=LIP):
        with open(path) as f:
            d = json.load(f)
        lip = {}
        if os.path.exists(lip_path):
            with open(lip_path) as f:
                lip = json.load(f)
        self.total = d["total"]
        self.scenes = [SceneInfo(s, lip) for s in d["scenes"]]
        self._by_id = {s.id: s for s in self.scenes}

    def scene(self, sid):
        return self._by_id[sid]

    def scene_at(self, gt):
        for s in self.scenes:
            if s.start <= gt < s.start + s.dur:
                return s
        return self.scenes[-1]


def build_timeline(durations, script_path=SCRIPT, out_path=TIMELINE):
    """durations: {line_id: seconds}. Writes timeline.json and returns it.

    Beat types inside each scene's "beats":
      {"t": "line", "id", "who", "text", "pre", "post", "overlap", ...}
      {"t": "pause", "dur", "cue"?}   – silence, optional cue name at its start
      {"t": "cue", "name"}           – zero-length named marker
    A line's "overlap" (seconds) starts it that much before the previous
    beat ended (for interruptions). Scene keys: "min_dur", "tail".
    """
    with open(script_path) as f:
        script = json.load(f)
    g = 0.0
    scenes = []
    for sc in script["scenes"]:
        t = sc.get("head", 0.0)
        cues, lines = {"start": 0.0}, []
        for b in sc["beats"]:
            kind = b.get("t", "line")
            if kind == "pause":
                if b.get("cue"):
                    cues[b["cue"]] = t
                t += float(b["dur"])
                if b.get("end_cue"):
                    cues[b["end_cue"]] = t
            elif kind == "cue":
                cues[b["name"]] = t
            elif kind == "line":
                t += float(b.get("pre", 0.15))
                t -= float(b.get("overlap", 0.0))
                d = float(durations[b["id"]])
                meta = {k: v for k, v in b.items()
                        if k not in ("t", "id", "who", "text", "caption", "pre", "post",
                                     "overlap", "nocap")}
                lines.append({"id": b["id"], "who": b["who"], "text": b["text"],
                              "caption": b.get("caption", b["text"]),
                              "nocap": b.get("nocap", False),
                              "start": round(t, 4), "end": round(t + d, 4),
                              "gstart": round(g + t, 4), "meta": meta})
                cues[b["id"]] = t
                cues[b["id"] + ".end"] = t + d
                t += d + float(b.get("post", 0.25))
            else:
                raise ValueError(f"unknown beat type {kind} in {sc['id']}")
        t += sc.get("tail", 0.3)
        dur = max(t, float(sc.get("min_dur", 0)))
        cues["end"] = dur
        scenes.append({"id": sc["id"], "module": sc["module"], "start": round(g, 4),
                       "dur": round(dur, 4), "cues": cues, "lines": lines,
                       "meta": {k: v for k, v in sc.items() if k not in ("beats",)}})
        g += dur
    out = {"total": round(g, 4), "scenes": scenes}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    return out
