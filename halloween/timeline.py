"""Absolute timing of every line and beat, plus lip-sync data."""
import json
import os

import numpy as np
import soundfile as sf

from story import CAST, SCRIPT

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = os.path.join(HERE, "build", "voices")
ENV_HZ = 100

# phoneme -> (open bias, round, wide, closed)
ROUND = set("oOuʊWwɔQYɒ")
WIDE = set("iɪeɛAjI")
OPEN = set("aɑæʌəɜɐᵻ")
CLOSED = set("mbp")
TEETH = set("fv")


class Timeline:
    def __init__(self):
        self.items = {}    # id -> dict(kind, start, end, ...)
        self.lines = []    # ordered line dicts
        t = 0.0
        for it in SCRIPT:
            if it[0] == "beat":
                _, bid, dur = it
                self.items[bid] = dict(kind="beat", id=bid, start=t, end=t + dur)
                t += dur
            else:
                _, lid, who, text, opts = it
                with open(os.path.join(VOICES, f"{lid}.json")) as f:
                    meta = json.load(f)
                t += opts.get("gap", 0.0)
                start = t
                words = [dict(w, start=w["start"] + start, end=w["end"] + start) for w in meta["words"]]
                d = dict(kind="line", id=lid, who=who, text=text, start=start, end=start + meta["dur"],
                         words=words, color=CAST[who]["color"], label=CAST[who]["label"])
                self.items[lid] = d
                self.lines.append(d)
                t += meta["dur"]
        self.duration = t
        self._env = {}
        self._vis = {}

    def s(self, i, off=0.0):
        return self.items[i]["start"] + off

    def e(self, i, off=0.0):
        return self.items[i]["end"] + off

    def word(self, lid, text, nth=0, edge="start"):
        """Absolute time of the nth word in a line whose letters match text."""
        key = "".join(ch for ch in text.lower() if ch.isalnum())
        n = 0
        for w in self.items[lid]["words"]:
            if "".join(ch for ch in w["text"].lower() if ch.isalnum()) == key:
                if n == nth:
                    return w[edge]
                n += 1
        raise KeyError(f"{text!r} not in {lid}")

    def env(self, lid):
        if lid not in self._env:
            a, sr = sf.read(os.path.join(VOICES, f"{lid}.wav"), dtype="float32")
            hop = sr // ENV_HZ
            n = len(a) // hop
            frames = a[: n * hop].reshape(n, hop)
            rms = np.sqrt((frames ** 2).mean(axis=1))
            ref = np.percentile(rms[rms > 1e-4], 92) if np.any(rms > 1e-4) else 1.0
            e = np.clip(rms / (ref + 1e-9), 0, 1.4)
            # gentle smoothing (attack fast, release slower)
            out = np.zeros_like(e)
            v = 0.0
            for i, x in enumerate(e):
                v = x if x > v else v * 0.72 + x * 0.28
                out[i] = v
            self._env[lid] = out
        return self._env[lid]

    def visemes(self, lid):
        """[(t0, t1, round, wide, closed)] spreading each word's phonemes across it."""
        if lid not in self._vis:
            out = []
            for w in self.items[lid]["words"]:
                ph = [ch for ch in w.get("ph", "") if ch.isalpha() or ch in "ɑæʌəɜɐɪʊɔɛɒᵻ"]
                if not ph:
                    continue
                dur = max(1e-3, w["end"] - w["start"])
                dt = dur / len(ph)
                for i, p in enumerate(ph):
                    out.append((w["start"] + i * dt, w["start"] + (i + 1) * dt,
                                1.0 if p in ROUND else 0.0, 1.0 if p in WIDE else 0.0,
                                1.0 if p in CLOSED else (0.5 if p in TEETH else 0.0)))
            self._vis[lid] = out
        return self._vis[lid]

    def mouth(self, lid, t):
        """(open, round, wide) for a line at absolute time t."""
        d = self.items[lid]
        if t < d["start"] or t > d["end"]:
            return 0.0, 0.0, 0.0
        e = self.env(lid)
        i = int((t - d["start"]) * ENV_HZ)
        i = max(0, min(len(e) - 1, i))
        op = float(e[i])
        rnd = wide = closed = 0.0
        for (a, b, r, w, cl) in self.visemes(lid):
            if a <= t < b:
                rnd, wide, closed = r, w, cl
                break
        op = op * (1 - 0.85 * closed)
        op = min(1.0, op ** 0.75 * 1.05)
        return op, rnd, wide

    def active_line(self, t, who=None):
        for d in self.lines:
            if d["start"] - 0.05 <= t <= d["end"] + 0.05 and (who is None or d["who"] == who):
                return d
        return None


_TL = None


def get():
    global _TL
    if _TL is None:
        _TL = Timeline()
    return _TL


if __name__ == "__main__":
    T = get()
    print("duration %.2f" % T.duration)
    for k, v in T.items.items():
        print(f"{k:10s} {v['kind']:5s} {v['start']:7.2f} {v['end']:7.2f}")
