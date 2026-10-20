"""Keyframe tracks, actors with automatic acting (blinks, breathing, lip-sync,
emphasis on stressed words, glances) and a camera track."""
import math
import random

from gfx import clamp, ease_in_out, ease_out, lerp, noise1

ON_TWOS = 12.0   # character animation rate (stop-motion feel)


def interp(a, b, u):
    if a is None:
        return b
    if isinstance(a, tuple) and isinstance(b, tuple):
        return tuple(lerp(x, y, u) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return b if u >= 0.5 else a
    return a + (b - a) * u


class Track:
    """Value that moves to targets: .to(t0, value, dur, ease)."""

    def __init__(self, v0):
        self.v0 = v0
        self.segs = []

    def to(self, t0, v, dur=0.3, ease=ease_in_out):
        self.segs.append((t0, t0 + max(dur, 1e-4), v, ease))
        self.segs.sort(key=lambda s: s[0])
        return self

    def at(self, t):
        return self._eval(t, len(self.segs))

    def _eval(self, t, n):
        for i in range(n - 1, -1, -1):
            t0, t1, vt, e = self.segs[i]
            if t >= t0:
                if t >= t1:
                    return vt
                return interp(self._eval(t0, i), vt, e((t - t0) / (t1 - t0)))
        return self.v0


def pulse(x, attack=0.1, decay=0.35):
    if x < 0:
        return 0.0
    if x < attack:
        return x / attack
    return math.exp(-(x - attack) / decay)


class Actor:
    """kind: 'mouse:<name>', 'cat', 'mom', 'sun', 'ghost'."""

    def __init__(self, name, kind, T, seed=0, **base):
        self.name, self.kind, self.T = name, kind, T
        self.base = dict(base)
        self.tracks = {}
        self.lines = []
        self.no_blink = []          # (t0, t1)
        self.forced_blinks = []
        self.hops = []              # (t0, dur, height)
        self.trembles = []          # (t0, t1, amp)
        self.nods = []              # (t0, amount)
        self.looks = Track(None)    # target actor / point / None
        self.mouth_gain = 1.0
        self.emphasis = 1.0
        self.idle = 1.0
        r = random.Random(seed * 7919 + 13)
        self.blinks = []
        tt = r.uniform(0.3, 2.5)
        while tt < T.duration + 5:
            self.blinks.append(tt)
            tt += r.uniform(2.2, 5.2)
        self.twitches = []
        tt = r.uniform(1, 5)
        while tt < T.duration + 5:
            self.twitches.append(tt)
            tt += r.uniform(3.5, 8.0)
        self.phase = r.uniform(0, 6.28)
        self.seed = seed
        if kind.startswith("mouse"):
            from mice import DEFAULT as D
        elif kind == "cat":
            from cat import DEFAULT as D
        elif kind == "mom":
            from mom import DEFAULT as D
        else:
            D = dict(lid=0.0, look=0.0, mouth=0.0, smile=0.5, wobble=0.0, scale=1.0, hidden=False)
        self.defaults = dict(D, hidden=False, z=0, alpha=1.0, walking=0.0, walk=0.0)

    # ---- authoring helpers
    def tr(self, p):
        if p not in self.tracks:
            self.tracks[p] = Track(self.base.get(p, self.defaults.get(p)))
        return self.tracks[p]

    def k(self, t, dur=0.3, ease=ease_in_out, **vals):
        for p, v in vals.items():
            self.tr(p).to(t, v, dur, ease)
        return self

    def snap(self, t, **vals):
        return self.k(t, 1e-3, **vals)

    def says(self, *lids):
        self.lines.extend(lids)
        return self

    def look_at(self, t, target, dur=0.25):
        self.looks.to(t, target, dur, ease_out)
        return self

    def hop(self, t, height=40, dur=0.35):
        self.hops.append((t, dur, height))
        return self

    def tremble(self, t0, t1, amp=3.0):
        self.trembles.append((t0, t1, amp))
        return self

    def nod(self, t, amount=1.0):
        self.nods.append((t, amount))
        return self

    def blink_at(self, t):
        self.forced_blinks.append(t)
        return self

    def hold_still(self, t0, t1):
        self.no_blink.append((t0, t1))
        return self

    # ---- evaluation
    def raw(self, p, t, default=None):
        if p in self.tracks:
            return self.tracks[p].at(t)
        return self.base.get(p, self.defaults.get(p, default))

    def pos(self, t):
        return self.raw("x", t, 0.0), self.raw("y", t, 0.0)

    def head_pos(self, t):
        x, y = self.pos(t)
        s = self.raw("scale", t, 1.0)
        if self.kind == "cat":
            return x, y - 520 * s * self.raw("rise", t, 1.0)
        if self.kind == "mom":
            return x, y
        if self.kind.startswith("mouse:"):
            from mice import KINDS
            K = KINDS[self.kind.split(":")[1]]
            if self.raw("flat", t, False):
                return x, y
            return x, y - (K["chin"] + K["legs"] + 18) * s * K["size"]
        return x, y

    def blink_amount(self, t):
        for a, b in self.no_blink:
            if a <= t <= b:
                return 0.0
        v = 0.0
        for bt in self.blinks + self.forced_blinks:
            d = t - bt
            if -0.01 <= d <= 0.2:
                v = max(v, 1.0 - abs(d - 0.07) / 0.13 if d > 0.07 else d / 0.07)
        return clamp(v)

    def pose(self, t):
        T = self.T
        P = dict(self.base)
        for p, tr in self.tracks.items():
            P[p] = tr.at(t)
        # tremble / shake
        dx = 0.0
        for a, b, amp in self.trembles:
            if a <= t <= b:
                dx += amp * noise1(t * 28.0, self.seed + 3)
        P["x"] = P.get("x", 0.0) + dx
        # hops
        lift = P.get("lift", 0.0)
        sq = P.get("squash", 1.0)
        for t0, dur, hgt in self.hops:
            u = (t - t0) / dur
            if -0.12 <= u < 0:
                sq *= 1 - 0.18 * (1 + u / 0.12)          # anticipation squash
            elif 0 <= u <= 1:
                lift += hgt * math.sin(math.pi * u)
                sq *= 1 + 0.12 * math.sin(math.pi * u)
            elif 1 < u <= 1.35:
                sq *= 1 - 0.14 * math.sin(math.pi * (u - 1) / 0.35)
        P["lift"] = lift
        # breathing / idle
        if self.kind.startswith("mouse"):
            sq *= 1 + 0.012 * math.sin(t * 2 * math.pi / 3.1 + self.phase) * self.idle
            P["tilt"] = P.get("tilt", 0.0) + 1.6 * noise1(t * 0.35, self.seed) * self.idle
            P["whisk"] = P.get("whisk", 0.0) + 0.6 * noise1(t * 0.9, self.seed + 9) * self.idle
            P["tail_t"] = t + self.phase
        P["squash"] = sq
        if self.kind == "cat":
            P["breathe"] = t * 2.0 + self.phase
            P["tail_t"] = t + self.phase
        if self.kind == "mom":
            P["breathe"] = t * 1.6
        # ear twitches
        if self.kind.startswith("mouse"):
            tw = 0.0
            for tt in self.twitches:
                tw += pulse(t - tt, 0.06, 0.18) * (1 if int(tt * 10) % 2 else -1)
            P["ear_twitch"] = P.get("ear_twitch", 0.0) + tw * 0.8 * self.idle
        # look-at
        tgt = self.looks.at(t)
        if tgt is not None and "look" not in self.tracks:
            hx, hy = self.head_pos(t)
            if isinstance(tgt, Actor):
                tx, ty = tgt.head_pos(t)
            else:
                tx, ty = tgt
            ddx, ddy = tx - hx, ty - hy
            d = math.hypot(ddx, ddy) + 1e-6
            P["look"] = (clamp(ddx / d * 1.1, -1, 1), clamp(ddy / d * 0.9, -1, 1))
            if self.kind.startswith("mouse"):
                P["yaw"] = P.get("yaw", 0.0) + clamp(ddx / 900, -0.6, 0.6)
        # blinks
        b = self.blink_amount(t)
        if b > 0:
            P["lid"] = max(P.get("lid", 0.0), b)
        # nods (manual)
        nod = P.get("nod", 0.0)
        for t0, amt in self.nods:
            nod += amt * 9 * math.sin(clamp((t - t0) / 0.45) * math.pi)
        # speaking: lip-sync + emphasis
        speaking = False
        for lid in self.lines:
            d = T.items[lid]
            if d["start"] - 0.02 <= t <= d["end"] + 0.02:
                speaking = True
                op, rnd, wide = T.mouth(lid, t)
                P["mouth"] = max(P.get("mouth", 0.0), op * self.mouth_gain)
                P["mround"] = rnd
                P["mwide"] = wide
                if self.kind == "mom":
                    P["mclosed"] = 0.0
                br, nd = 0.0, 0.0
                for w in d["words"]:
                    dur = w["end"] - w["start"]
                    strong = w["mark"] is not None or dur > 0.42 or w["text"].endswith(("!", "?"))
                    if strong:
                        br = max(br, pulse(t - w["start"], 0.12, 0.45) * (1.0 if w["mark"] else 0.6))
                        nd += pulse(t - w["start"], 0.1, 0.3) * 0.6
                P["brow"] = P.get("brow", 0.0) + 0.45 * br * self.emphasis
                nod += nd * self.emphasis
                if self.kind.startswith("mouse"):
                    P["tilt"] = P.get("tilt", 0.0) + 3.0 * math.sin((t - d["start"]) * 1.7) * self.emphasis
                if self.kind == "cat":
                    P["tilt"] = P.get("tilt", 0.0) + 2.0 * math.sin((t - d["start"]) * 1.3)
                break
        P["nod"] = nod
        P["_speaking"] = speaking
        return P


DRIFT = False   # locked-off cameras (stop-motion style, and far cheaper to encode)


class Cam:
    def __init__(self, cx, cy, zoom=1.0, roll=0.0):
        self.cx, self.cy, self.zoom, self.roll = Track(cx), Track(cy), Track(zoom), Track(roll)
        self.shakes = []

    def k(self, t, dur=1.0, ease=ease_in_out, cx=None, cy=None, zoom=None, roll=None, keep=False):
        if not (DRIFT or keep):
            return self
        if cx is not None:
            self.cx.to(t, cx, dur, ease)
        if cy is not None:
            self.cy.to(t, cy, dur, ease)
        if zoom is not None:
            self.zoom.to(t, zoom, dur, ease)
        if roll is not None:
            self.roll.to(t, roll, dur, ease)
        return self

    def shake(self, t, amp=14, dur=0.4):
        self.shakes.append((t, amp, dur))
        return self

    def at(self, t):
        from gfx import Camera
        cx, cy, z, r = self.cx.at(t), self.cy.at(t), self.zoom.at(t), self.roll.at(t)
        for t0, amp, dur in self.shakes:
            u = (t - t0) / dur
            if 0 <= u <= 1:
                k = (1 - u) ** 2
                cx += amp * k * noise1(t * 40, 1) / z
                cy += amp * k * noise1(t * 40, 2) / z
        return Camera(cx, cy, z, r)


def q(t):
    """Quantize to the stop-motion rate."""
    return math.floor(t * ON_TWOS + 1e-6) / ON_TWOS
