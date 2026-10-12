"""Absolute timing for every line/segment/word, from the voice metadata."""
import json
import os
import re

from config import WORK
import script

VOICE = os.path.join(WORK, "voice")


class Timeline:
    def __init__(self):
        self.lines = {}
        self.order = []
        self.scene_of = {}
        self.scene_start = {}
        self.scene_end = {}
        t = 0.0
        first = True
        for sc in script.SCENES:
            sc_first = True
            for ln in sc["lines"]:
                with open(os.path.join(VOICE, ln["id"] + ".json")) as f:
                    meta = json.load(f)
                start = t + ln["gap"]
                if first:
                    start = ln["gap"]
                    first = False
                if sc_first:
                    self.scene_start[sc["id"]] = start - ln["gap"]
                    sc_first = False
                end = start + meta["duration"]
                meta["start"] = start
                meta["end"] = end
                meta["scene"] = sc["id"]
                meta["gap"] = ln["gap"]
                self.lines[ln["id"]] = meta
                self.order.append(ln["id"])
                self.scene_of[ln["id"]] = sc["id"]
                t = end
            self.scene_end[sc["id"]] = t + sc.get("tail", 0.0)
            t = self.scene_end[sc["id"]]
        self.total = t

    def __call__(self, lid, where="start", seg=None, word=None, frac=None):
        m = self.lines[lid]
        if seg is not None:
            s = m["segments"][seg]
            if where == "end":
                return m["start"] + s["end"]
            return m["start"] + s["start"]
        if word is not None:
            return m["start"] + self.word_time(lid, word, where)
        if frac is not None:
            return m["start"] + m["duration"] * frac
        return m["start"] if where == "start" else m["end"]

    def words(self, lid):
        """[(word, start, end)] relative to line start, aligned via phoneme word boundaries."""
        m = self.lines[lid]
        out = []
        ph = m["phonemes"]
        for s in m["segments"]:
            wl = [w for w in re.split(r"\s+", s["text"].strip()) if re.search(r"\w", w)]
            # phoneme groups between spaces inside this segment's time span
            groups = []
            cur = []
            for p in ph:
                if p["s"] < s["start"] - 1e-6 or p["e"] > s["end"] + 1e-6:
                    continue
                if p["p"] == " ":
                    if cur:
                        groups.append(cur)
                        cur = []
                    continue
                if re.match(r"[\.,!?;:…—\"“”()]", p["p"]):
                    continue
                cur.append(p)
            if cur:
                groups.append(cur)
            if len(groups) == len(wl):
                for w, g in zip(wl, groups):
                    out.append((w, g[0]["s"], g[-1]["e"]))
            else:
                # proportional fallback
                n = len(wl)
                for i, w in enumerate(wl):
                    a = s["start"] + (s["end"] - s["start"]) * i / n
                    b = s["start"] + (s["end"] - s["start"]) * (i + 1) / n
                    out.append((w, a, b))
        return out

    def word_time(self, lid, word, where="start"):
        word = word.lower()
        idx = 0
        if "#" in word:
            word, k = word.split("#")
            idx = int(k)
        hits = [w for w in self.words(lid) if re.sub(r"\W", "", w[0].lower()) == word]
        if not hits:
            raise KeyError(f"{word} not in {lid}")
        w = hits[min(idx, len(hits) - 1)]
        return w[1] if where == "start" else w[2]

    def speaking(self):
        """[(speaker, line_id, start, end)]"""
        return [(self.lines[l]["speaker"], l, self.lines[l]["start"], self.lines[l]["end"]) for l in self.order]


if __name__ == "__main__":
    T = Timeline()
    for lid in T.order:
        m = T.lines[lid]
        print(f"{lid} {m['scene']:10s} {m['speaker']:9s} {m['start']:7.2f} - {m['end']:7.2f}")
    print("total", T.total)
    print(T.words("L13"))
