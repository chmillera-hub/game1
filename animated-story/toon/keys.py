"""Keyframed properties and attribute-style state."""
import math

DEFAULTS = dict(
    x=540.0, y=1400.0, scale=1.0, facing=1, rot=0.0, sx=1.0, sy=1.0, alpha=1.0, visible=1,
    eyes="open", look=0.0, looky=0.0, blink=0.0, brow=0.0, browy=0.0, mouth="smile", talk=0.0,
    aLx=0.22, aLy=0.97, aRx=0.22, aRy=0.97, flail=0.0, kick=0.0, shiver=0.0, walk=0.0, sit=0,
    seated=0, sweat=0.0, tears=0.0, blush=0.0, shades=1.0, holdshades=0, glint=0.0, hold=None,
    costume=None, bob=1.0, puff=0.0, sparkle=0.0, hop=0.0, layer=0, z=0.0, waveR=0.0, waveL=0.0,
    rub=0.0, clap=0.0, gest=0.6, autoblink=1, lean=0.0, slip_text="?",
)


class State(dict):
    def __getattr__(self, k):
        if k in self:
            return self[k]
        return DEFAULTS.get(k)


EASE = {
    "lin": lambda u: u,
    "in": lambda u: u * u,
    "out": lambda u: 1 - (1 - u) * (1 - u),
    "inout": lambda u: u * u * (3 - 2 * u),
    "back": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
    "bounce": lambda u: _bounce(u),
    "elastic": lambda u: 1 - math.cos(u * math.pi * 4.5) * math.exp(-u * 6) if u < 1 else 1,
}


def _bounce(u):
    n1, d1 = 7.5625, 2.75
    if u < 1 / d1:
        return n1 * u * u
    if u < 2 / d1:
        u -= 1.5 / d1
        return n1 * u * u + 0.75
    if u < 2.5 / d1:
        u -= 2.25 / d1
        return n1 * u * u + 0.9375
    u -= 2.625 / d1
    return n1 * u * u + 0.984375


class Track:
    """Keys: list of (t, value, ease). The ease on a key describes how we arrive at it
    from the previous key; 'step' means jump at that time."""

    def __init__(self, initial):
        self.keys = [(-1e9, initial, "step")]

    def add(self, t, v, ease="step"):
        # keep sorted; replace keys at identical time
        ks = self.keys
        i = len(ks)
        while i > 0 and ks[i - 1][0] > t:
            i -= 1
        if i > 0 and abs(ks[i - 1][0] - t) < 1e-9:
            ks[i - 1] = (t, v, ease)
        else:
            ks.insert(i, (t, v, ease))

    def get(self, t):
        ks = self.keys
        lo, hi = 0, len(ks) - 1
        if t >= ks[-1][0]:
            return ks[-1][1]
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if ks[mid][0] <= t:
                lo = mid
            else:
                hi = mid
        t0, v0, _ = ks[lo]
        t1, v1, e1 = ks[hi]
        if e1 == "step" or not isinstance(v0, (int, float)) or not isinstance(v1, (int, float)) \
                or isinstance(v0, bool):
            return v0
        u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        u = EASE[e1](max(0.0, min(1.0, u)))
        return v0 + (v1 - v0) * u


class Keyed:
    """An object whose properties are keyframed over (shot-local) time."""

    def __init__(self, **init):
        init = expand(init)
        self.tracks = {}
        self.init = dict(init)
        for k, v in init.items():
            self.tracks[k] = Track(v)

    def _track(self, k):
        if k not in self.tracks:
            self.tracks[k] = Track(DEFAULTS.get(k))
        return self.tracks[k]

    def set(self, t, **kv):
        kv = expand(kv)
        for k, v in kv.items():
            self._track(k).add(t, v, "step")
        return self

    def to(self, t, dur, ease="inout", **kv):
        kv = expand(kv)
        for k, v in kv.items():
            tr = self._track(k)
            cur = tr.get(t)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and dur > 0:
                tr.add(t, cur, "step")
                tr.add(t + dur, v, ease)
            else:
                tr.add(t + dur * 0.5 if dur > 0 else t, v, "step")
        return self

    def get(self, k, t):
        tr = self.tracks.get(k)
        if tr is None:
            return DEFAULTS.get(k)
        return tr.get(t)

    def state(self, t):
        s = State()
        for k, tr in self.tracks.items():
            s[k] = tr.get(t)
        return s


def expand(kv):
    """Expand `arms='preset'` into numeric arm channels."""
    if "arms" in kv:
        from .characters import ARMS
        kv = dict(kv)
        a = kv.pop("arms")
        aLx, aLy, aRx, aRy = ARMS[a] if isinstance(a, str) else a
        kv.update(aLx=aLx, aLy=aLy, aRx=aRx, aRy=aRy)
    if "armL" in kv:
        from .characters import ARMS
        kv = dict(kv)
        a = ARMS[kv.pop("armL")]
        kv.update(aLx=a[0], aLy=a[1])
    if "armR" in kv:
        from .characters import ARMS
        kv = dict(kv)
        a = ARMS[kv.pop("armR")]
        kv.update(aRx=a[2], aRy=a[3])
    return kv
