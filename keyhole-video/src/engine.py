"""Actors: keyframed acting + automatic life layers (blink, saccades, breath, lip-sync, laughter)."""
import json, math, os
import numpy as np
import gfx
from gfx import Track, ease_io, ease_out, ease_in, ease_back, smooth, wobble, clamp, lerp
import rig
from rig import FACE, EXPR

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "build", "timeline.json")))
_TR = np.load(os.path.join(HERE, "build", "tracks.npz"))
TRACKS = {k: _TR[k] for k in _TR.files}
FPS = TL["fps"]
M = TL["marks"]
SH = {s["name"]: (s["t0"], s["t1"]) for s in TL["shots"]}


def LN(who, sub, k=None):
    """Line lookup; returns (t0, t1) or the k-th chunk start."""
    for l in TL["lines"]:
        if l["who"] == who and sub in l["text"]:
            if k is None:
                return l["t0"], l["t1"]
            return l["chunks"][k]
    raise KeyError((who, sub))


def LNB(who, sub, k=0):
    for l in TL["lines"]:
        if l["who"] == who and sub in l["text"]:
            return l["bleeps"][k]
    raise KeyError((who, sub))


def expr_val(v):
    if isinstance(v, str):
        return dict(EXPR[v])
    if isinstance(v, tuple):
        d = dict(EXPR[v[0]])
        d.update(v[1])
        return d
    return dict(v)


class Blinker:
    def __init__(self, seed, lo=2.0, hi=5.2):
        rng = np.random.default_rng(seed)
        t = rng.uniform(0.3, 2.0)
        self.times = []
        while t < 400:
            self.times.append(t)
            if rng.random() < 0.15:
                self.times.append(t + 0.32)
            t += rng.uniform(lo, hi)
        self.times = np.array(self.times)
        self.forced = []

    def force(self, t):
        self.forced.append(t)

    def __call__(self, t):
        v = 0.0
        cand = list(self.times[(self.times > t - 0.3) & (self.times < t + 0.05)]) + [f for f in self.forced if t - 0.3 < f < t + 0.05]
        for b in cand:
            d = t - b
            if 0 <= d < 0.06:
                v = max(v, d / 0.06)
            elif 0.06 <= d < 0.1:
                v = 1.0
            elif 0.1 <= d < 0.2:
                v = max(v, 1 - (d - 0.1) / 0.1)
        return v


class Saccade:
    def __init__(self, seed, amp=0.1):
        rng = np.random.default_rng(seed + 999)
        t = 0.0
        self.keys = []
        while t < 400:
            self.keys.append((t, rng.uniform(-amp, amp), rng.uniform(-amp * 0.6, amp * 0.6)))
            t += rng.uniform(0.6, 2.4)

    def __call__(self, t):
        # binary search
        lo, hi = 0, len(self.keys) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.keys[mid][0] <= t:
                lo = mid
            else:
                hi = mid - 1
        k = self.keys[lo]
        prev = self.keys[lo - 1] if lo > 0 else k
        u = clamp((t - k[0]) / 0.06)
        return lerp(prev[1], k[1], u), lerp(prev[2], k[2], u)


BODY_DEFAULTS = dict(x=0.0, y=0.0, scale=1.0, lean=0.0, bob=0.0, shake=0.0, shrug=0.0, head_dx=0.0,
                     squash=0.0, run=0.0, cross=0.0, knee_dx=0.0, step=0.0)


class Actor:
    def __init__(self, ch, seed=0, talk_name=None, sacc=0.08, blink=True, idle=1.0, kid_laugh=False, **init):
        self.ch = ch
        self.name = ch.name
        self.talk_name = talk_name or ch.name
        self.seed = seed
        self.blinker = Blinker(seed) if blink else None
        self.sacc = Saccade(seed, sacc) if sacc else None
        self.idle = idle
        self.kid_laugh = kid_laugh
        self.tr = {}
        self.static = {}
        init.setdefault("expr", "neutral")
        init.setdefault("look", (0.0, 0.0))
        for k in ("turn", "tilt", "nod"):
            init.setdefault(k, 0.0)
        for k, v in init.items():
            self.set0(k, v)

    def set0(self, k, v):
        if k == "expr":
            v = expr_val(v)
        if isinstance(v, (str, bool)) or v is None or (k in ("legs", "pose", "part")):
            self.static[k] = v
            return
        self.tr[k] = Track(v)

    def at(self, t, dur=0.35, ease=None, **kw):
        for k, v in kw.items():
            if k == "expr":
                v = expr_val(v)
            if k in ("legs", "pose"):
                self.static[k] = v
                continue
            if k not in self.tr:
                self.tr[k] = Track(FACE.get(k, BODY_DEFAULTS.get(k, 0.0)) if not isinstance(v, (tuple, dict)) else v)
            self.tr[k].key(t, v, dur, ease)
        return self

    def blink_at(self, t):
        if self.blinker:
            self.blinker.force(t)
        return self

    def P(self, t):
        P = dict(FACE)
        P.update(BODY_DEFAULTS)
        P.update(self.static)
        for k, tr in self.tr.items():
            v = tr(t)
            if k == "expr":
                P.update(v)
            elif k == "look":
                P["lookx"], P["looky"] = v
            else:
                P[k] = v
        f = int(round(t * FPS))
        s = self.seed
        # idle life
        if self.idle:
            P["tilt"] += 1.6 * self.idle * wobble(t, s, 0.11)
            P["turn"] += 0.035 * self.idle * wobble(t, s + 3, 0.09)
            P["nod"] += 0.03 * self.idle * wobble(t, s + 5, 0.13)
            P["breath"] = math.sin(2 * math.pi * t / 3.7 + s)
        if self.sacc and P.get("fixed_gaze", 0) < 0.5:
            sx, sy = self.sacc(t)
            P["lookx"] += sx
            P["looky"] += sy
        # lip sync
        tr = TRACKS.get(self.talk_name)
        talking = 0.0
        if tr is not None and 0 <= f < len(tr):
            o, w, r, e = tr[f]
            # smoothed activity over neighbouring frames
            lo, hi = max(0, f - 3), min(len(tr), f + 4)
            act = float(np.max(tr[lo:hi, 0])) if hi > lo else 0.0
            if act > 0.03:
                talking = clamp(act / 0.15)
                P["open"] = max(P["open"] * (1 - talking), o * P.get("talk_gain", 1.0))
                P["wide"] = lerp(P["wide"], w, talking)
                P["round"] = lerp(P["round"], r, talking)
                P["press"] *= (1 - 0.85 * talking)
                P["puff"] *= (1 - talking)
                P["nod"] += 0.06 * (e - 0.35) * talking
                P["brow"] += 0.14 * e * talking * P.get("talk_brow", 1.0)
        # laughter
        lt = TRACKS.get(self.talk_name + "_laugh")
        if lt is not None and 0 <= f < len(lt) and lt[f] > 0.01:
            li = float(lt[f])
            lv = dict(EXPR["laughing"])
            if self.kid_laugh:
                lv["squeeze"] = 1.0
                lv["happy"] = 0.0
            for k, v in lv.items():
                P[k] = lerp(P.get(k, FACE.get(k, 0.0)), v, li) if k not in ("happy", "squeeze") else (v if li > 0.35 else P.get(k, 0.0))
            P["open"] = max(P["open"], (tr[f][0] if tr is not None and f < len(tr) else 0.5))
            P["round"] *= (1 - li)
            P["press"] *= (1 - li)
            P["puff"] *= (1 - li)
            P["nod"] -= 0.18 * li
            P["tilt"] += 4 * li * math.sin(t * 3.1 + s)
            P["shake"] = P.get("shake", 0) + li * math.sin(t * 2 * math.pi * 6.5)
        # blink (not if eyes are closed by expression)
        if self.blinker and P["happy"] < 0.5 and P["squeeze"] < 0.5:
            b = self.blinker(t)
            if b > 0:
                P["lid"] = P["lid"] * (1 - b) + 0.0 * b
                P["lidL"] *= (1 - b)
                P["lidR"] *= (1 - b)
        return P

    def draw(self, cv, t, **over):
        P = self.P(t)
        P.update(over)
        self.ch.draw(cv, P, t)
        return P
