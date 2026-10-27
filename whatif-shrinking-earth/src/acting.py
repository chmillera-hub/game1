"""Stateless character acting: every value is a pure function of time.

Layers (in order):
  expression presets (blended keys) -> gaze (eyes fast, head lags) ->
  lip-sync from phoneme timings + voice envelope -> speech emphasis (brow
  flicks, nods) -> gestures (nod, shake, laugh, sigh...) -> blinks ->
  micro-saccades, breathing, idle sway.
"""
import bisect
import json
import math
import os

import numpy as np
import soundfile as sf

import paths
import poses
import rig
from anchors import resolve, tl
from gfx import clamp, fbm1, smoothstep

FACE_KEYS = list(rig.default_face().keys())

# --------------------------------------------------------------------------
# expression presets (only differences from rig.default_face)
# --------------------------------------------------------------------------
EXPR = {
    "neutral": {},
    "content": dict(msmile=0.45, lower=0.25, braise=0.05),
    "happy": dict(msmile=0.85, lower=0.55, braise=0.25, blush=0.45),
    "grin": dict(msmile=0.95, lower=0.5, mopen_base=0.16, mteeth=1.0, braise=0.2, blush=0.4),
    "laugh": dict(msmile=1.0, lower=0.85, eopen=0.35, braise=0.35, mopen_base=0.45, mteeth=0.9, blush=0.55),
    "amused": dict(msmile=0.6, lower=0.4, masym=0.35, basym=0.3, braise=0.1),
    "sad": dict(tilt=0.8, binner=1.0, bouter=-0.3, eopen=0.74, msmile=-0.55, lower=0.15),
    "sad_deep": dict(tilt=0.8, binner=1.0, bouter=-0.25, eopen=0.7, msmile=-0.6, lower=0.2, wet=0.85),
    "hurt": dict(tilt=0.55, binner=0.8, eopen=0.8, msmile=-0.42, masym=0.15, lower=0.15),
    "wistful": dict(tilt=0.4, binner=0.6, eopen=0.8, msmile=0.0, lower=0.22),
    "worried": dict(binner=0.9, bouter=0.1, eopen=1.0, msmile=-0.35, tilt=0.2, pupil=0.9),
    "curious": dict(braise=0.45, basym=0.25, eopen=1.0, msmile=0.25, pupil=1.05),
    "skeptical": dict(basym=0.9, eopen=0.84, msmile=0.3, masym=0.55),
    "surprised": dict(eopen=1.22, braise=0.95, mopen_base=0.32, mround=0.6, pupil=0.8),
    "alarmed": dict(eopen=1.25, braise=0.9, binner=0.6, mopen_base=0.45, mround=0.25, pupil=0.75),
    "tender": dict(msmile=0.42, binner=0.4, eopen=0.8, lower=0.32, blush=0.42),
    "guilty": dict(binner=0.9, tilt=0.35, msmile=-0.08, masym=0.25, eopen=0.8),
    "thinking": dict(bfurrow=0.35, basym=0.35, eopen=0.86, msmile=0.0, masym=0.45),
    "awe": dict(eopen=1.12, braise=0.6, mopen_base=0.18, mround=0.4, msmile=0.1, pupil=1.15),
    "sheepish": dict(msmile=0.62, binner=0.5, braise=0.3, lower=0.35, masym=0.3, blush=0.6),
    "determined": dict(msmile=0.38, bfurrow=0.22, eopen=0.95, braise=0.1),
    "warm": dict(msmile=0.7, lower=0.45, braise=0.15, blush=0.45),
    "teary_smile": dict(msmile=0.5, binner=0.6, wet=0.8, lower=0.42, eopen=0.8, blush=0.5),
    "peaceful": dict(eopen=0.0, msmile=0.38, lower=0.3, blush=0.45),
    "excited": dict(eopen=1.12, braise=0.6, msmile=0.9, mopen_base=0.22, mteeth=1.0, lower=0.3, blush=0.5),
    "sly": dict(msmile=0.55, masym=0.55, lower=0.45, basym=0.4, eopen=0.8),
    "uncomfortable": dict(binner=0.5, braise=0.4, eopen=1.05, msmile=-0.25, masym=0.3),
    "strain": dict(eopen=0.45, bfurrow=0.6, binner=-0.2, msmile=-0.4, braise=0.2),
    "honest": dict(binner=0.75, tilt=0.3, eopen=0.84, msmile=-0.2, lower=0.2),
    "relieved": dict(msmile=0.5, binner=0.35, eopen=0.85, lower=0.3),
    "hopeful": dict(binner=0.5, braise=0.3, eopen=1.02, msmile=0.2, wet=0.35),
}

NEUTRAL = rig.default_face()
NEUTRAL["mopen_base"] = 0.0


def expr_face(name, extra=None):
    f = dict(NEUTRAL)
    for part in name.split("+"):
        f.update(EXPR[part])
    if extra:
        f.update(extra)
    return f


# --------------------------------------------------------------------------
# keyed blending
# --------------------------------------------------------------------------

def _blend(a, b, u):
    if a is None or b is None:
        return b if u >= 0.5 else a
    if isinstance(a, dict):
        return {k: _blend(a.get(k, b.get(k)), b.get(k, a.get(k)), u) for k in set(a) | set(b)}
    if isinstance(a, (tuple, list)):
        return tuple(_blend(x, y, u) for x, y in zip(a, b))
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        return b if u >= 0.5 else a
    return a + (b - a) * u


class Track:
    """Keys (t, value, trans). Value holds until the next key, which blends in over `trans` s."""

    def __init__(self, keys, default):
        self.keys = sorted(keys, key=lambda k: k[0])
        self.times = [k[0] for k in self.keys]
        self.default = default

    def at(self, t):
        i = bisect.bisect_right(self.times, t) - 1
        if i < 0:
            return self.default
        t0, v, tr = self.keys[i]
        prev = self.keys[i - 1][1] if i > 0 else self.default
        if i > 0:
            # previous may itself still be blending; approximate with its settled value
            pass
        if tr <= 1e-6:
            return v
        u = smoothstep(0.0, 1.0, (t - t0) / tr)
        if u >= 1.0:
            return v
        return _blend(prev, v, u)


# --------------------------------------------------------------------------
# lip-sync
# --------------------------------------------------------------------------
# viseme: (open, wide, round, teeth, tongue)
VIS = {
    "REST": (0.0, 1.0, 0.0, 0.2, 0.0),
    "MBP": (0.0, 0.92, 0.1, 0.0, 0.0),
    "FV": (0.12, 1.02, 0.0, 1.0, 0.0),
    "TH": (0.22, 1.0, 0.0, 0.8, 0.9),
    "TD": (0.26, 1.0, 0.0, 0.7, 0.6),
    "S": (0.12, 1.12, 0.0, 1.0, 0.0),
    "SH": (0.24, 0.76, 0.55, 1.0, 0.0),
    "KG": (0.34, 1.0, 0.0, 0.4, 0.3),
    "R": (0.26, 0.82, 0.45, 0.4, 0.2),
    "W": (0.18, 0.55, 0.92, 0.0, 0.0),
    "Y": (0.26, 1.05, 0.0, 0.7, 0.3),
    "H": (0.36, 1.0, 0.0, 0.3, 0.2),
    "AA": (0.88, 1.05, 0.0, 0.5, 0.3),
    "AE": (0.72, 1.15, 0.0, 0.7, 0.2),
    "E": (0.52, 1.15, 0.0, 0.8, 0.2),
    "I": (0.32, 1.2, 0.0, 0.9, 0.1),
    "O": (0.64, 0.75, 0.78, 0.3, 0.1),
    "U": (0.3, 0.55, 0.95, 0.1, 0.0),
    "ER": (0.4, 0.85, 0.4, 0.5, 0.2),
    "AH": (0.42, 1.0, 0.1, 0.5, 0.2),
}
PH = {
    "p": "MBP", "b": "MBP", "m": "MBP", "f": "FV", "v": "FV", "θ": "TH", "ð": "TH",
    "t": "TD", "d": "TD", "n": "TD", "l": "TD", "ɾ": "TD", "ʔ": "TD", "s": "S", "z": "S",
    "ʃ": "SH", "ʒ": "SH", "ʧ": "SH", "ʤ": "SH", "k": "KG", "g": "KG", "ɡ": "KG", "ŋ": "KG",
    "h": "H", "ɹ": "R", "r": "R", "w": "W", "j": "Y",
    "ɑ": "AA", "ɐ": "AH", "ʌ": "AH", "a": "AA", "æ": "AE", "ɛ": "E", "e": "E", "ɪ": "I", "i": "I",
    "ʊ": "U", "u": "U", "ɔ": "O", "o": "O", "ɒ": "O", "ə": "AH", "ᵊ": "AH", "ɜ": "ER", "ɚ": "ER",
    "A": ("E", "I"), "I": ("AA", "I"), "W": ("AA", "U"), "O": ("O", "U"), "Y": ("O", "I"),
    "Q": ("O", "U"),
}
VOWELS = set("ɑɐʌaæɛeɪiʊuɔoɒəᵊɜɚAIWOYQ")


def phoneme_units(ph):
    units = []
    for ch in ph:
        if ch in "ˈˌː ":
            continue
        v = PH.get(ch)
        if v is None:
            continue
        if isinstance(v, tuple):
            units.append((v[0], 1.4))
            units.append((v[1], 1.0))
        else:
            units.append((v, 2.0 if ch in VOWELS else 1.0))
    return units


def build_lipsync_keys(line):
    """Mouth keys (t, viseme) for a line, anticipating ~30 ms."""
    keys = []
    words = line["words"]
    prev_end = None
    for w in words:
        if prev_end is not None and w["start"] - prev_end > 0.09:
            keys.append((0.5 * (prev_end + w["start"]), "REST"))
        units = phoneme_units(w.get("ph", "")) or [("AH", 1.0)]
        tot = sum(u[1] for u in units)
        t = w["start"]
        dur = max(0.05, w["end"] - w["start"])
        for vis, wt in units:
            d = dur * wt / tot
            keys.append((t + d * 0.5 - 0.03, vis))
            t += d
        prev_end = w["end"]
    keys.append((line["end"] + 0.02, "REST"))
    keys.insert(0, (line["start"] - 0.06, "REST"))
    return keys


_ENV = {}


def envelope(lid):
    """Voice RMS envelope at 100 Hz, normalized to the line's loud parts."""
    if lid in _ENV:
        return _ENV[lid]
    cache = os.path.join(paths.CACHE, f"env_{lid}.npy")
    wav = os.path.join(paths.VOICE, f"{lid}.wav")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(wav):
        e = np.load(cache)
    else:
        a, sr = sf.read(wav, dtype="float32")
        hop = sr // 100
        n = len(a) // hop
        fr = a[: n * hop].reshape(n, hop)
        e = np.sqrt((fr ** 2).mean(1) + 1e-12)
        ref = np.percentile(e, 92) + 1e-6
        e = np.clip(e / ref, 0, 1.3)
        # light smoothing
        k = np.array([0.25, 0.5, 0.25])
        e = np.convolve(e, k, mode="same")
        np.save(cache, e)
    _ENV[lid] = e
    return e


def env_at(lid, t_rel):
    e = envelope(lid)
    x = t_rel * 100.0
    i = int(math.floor(x))
    if i < 0 or i >= len(e) - 1:
        return 0.0
    f = x - i
    return float(e[i] * (1 - f) + e[i + 1] * f)


def mouth_from_keys(keys, t):
    times = [k[0] for k in keys]
    i = bisect.bisect_right(times, t) - 1
    if i < 0:
        return VIS["REST"]
    if i >= len(keys) - 1:
        return VIS[keys[-1][1]]
    t0, v0 = keys[i]
    t1, v1 = keys[i + 1]
    u = clamp((t - t0) / max(1e-3, t1 - t0))
    u = u * u * (3 - 2 * u)
    a, b = VIS[v0], VIS[v1]
    return tuple(x + (y - x) * u for x, y in zip(a, b))


# --------------------------------------------------------------------------
# gestures (additive offsets), all stateless
# --------------------------------------------------------------------------

def _bump(u):
    return math.sin(math.pi * clamp(u)) if 0 <= u <= 1 else 0.0


def gesture_offsets(kind, u, amp):
    """Return dict of additive offsets for face/pose at phase u in [0,1]."""
    o = {}
    if kind == "nod":
        o["pitch"] = -0.10 * amp * _bump(u)
    elif kind == "nod2":
        o["pitch"] = -0.08 * amp * abs(math.sin(2 * math.pi * u)) * (1 - 0.3 * u)
    elif kind == "shake":
        o["yaw"] = 0.13 * amp * math.sin(2 * math.pi * 2 * u) * (1 - u)
    elif kind == "tilt":
        o["roll"] = 0.12 * amp * _bump(u)
    elif kind == "shrug":
        o["shrug"] = 1.0 * amp * _bump(u)
        o["braise"] = 0.3 * amp * _bump(u)
    elif kind == "laugh":
        env = _bump(u)
        o["head_dy"] = 4.0 * amp * math.sin(2 * math.pi * 7 * u) * env
        o["shrug"] = 0.35 * amp * env * (0.5 + 0.5 * math.sin(2 * math.pi * 7 * u))
        o["pitch"] = 0.05 * amp * env
    elif kind == "sigh":
        env = _bump(u)
        o["shrug"] = 0.8 * amp * math.sin(math.pi * clamp(u * 1.6)) if u < 0.62 else -0.3 * amp * _bump((u - 0.62) / 0.38)
        o["pitch"] = -0.04 * amp * env
    elif kind == "sniff":
        o["pitch"] = 0.05 * amp * _bump(u)
        o["shrug"] = 0.3 * amp * _bump(u)
    elif kind == "flinch":
        o["head_dy"] = -6.0 * amp * _bump(u)
        o["eopen"] = 0.25 * amp * _bump(u)
        o["braise"] = 0.4 * amp * _bump(u)
    elif kind == "swallow":
        o["pitch"] = -0.04 * amp * _bump(u)
        o["msmile"] = -0.1 * amp * _bump(u)
    elif kind == "bounce":
        o["head_dy"] = -5.0 * amp * _bump(u)
    return o


# --------------------------------------------------------------------------
# character model
# --------------------------------------------------------------------------
CHAR = {"pip": rig.PIP, "tess": rig.TESS}
SPEAKER = {"pip": "PIP", "tess": "TESS"}
BASE_PLACE = {"tess": (470.0, 1440.0, 0.78), "pip": (690.0, 1460.0, 0.70)}
MOON_WORLD = (760.0, 470.0)
MUG_ROOF = {"pip": (790.0, 1470.0), "tess": (395.0, 1452.0)}

GAZE_POINTS = {
    "moon": MOON_WORLD,
    "sky": (560.0, 640.0), "sky_l": (380.0, 700.0), "sky_r": (740.0, 640.0), "sky_hi": (560.0, 420.0),
    "icon1": (250.0, 720.0), "icon2": (450.0, 680.0), "icon3": (650.0, 680.0), "icon4": (840.0, 720.0),
    "window": (190.0, 1250.0), "mug_roof_pip": MUG_ROOF["pip"], "mug_roof_tess": MUG_ROOF["tess"],
    "town": (300.0, 1100.0),
}


def head_world(name, place, pose=None):
    ch = CHAR[name]
    x, y, s = place
    R = ch["R"]
    hy = -(ch["torso_h"] + ch["neck_len"] + 0.86 * R)
    return x, y + hy * s


class Actor:
    def __init__(self, name, keys):
        self.name = name
        self.ch = CHAR[name]
        other = "tess" if name == "pip" else "pip"
        self.other = other
        ek, gk, pk, xk, sk, wk, rk = [], [], [], [], [], [], []
        self.gestures = []
        self.blink_force = []
        self.flags = []
        for anchor, d in keys:
            t = resolve(anchor)
            if "e" in d:
                ek.append((t, expr_face(d["e"], d.get("ex")), d.get("et", 0.35)))
            if "g" in d:
                gk.append((t, d["g"], d.get("gt", 0.14)))
                if d.get("gblink", True):
                    self.blink_force.append(t + 0.01)
            if "p" in d:
                pk.append((t, poses.pose_for(name, d["p"]), d.get("pt", 0.6)))
            if "x" in d:
                xk.append((t, d["x"], d.get("xt", 0.8)))
            if "stand" in d:
                sk.append((t, d["stand"], d.get("st", 0.7)))
            if "wet" in d:
                wk.append((t, d["wet"], d.get("wt", 1.0)))
            if "tear" in d:
                rk.append((t, d["tear"], d.get("tt", 1.6)))
            for gname in ([d["gest"]] if isinstance(d.get("gest"), str) else d.get("gest", [])):
                self.gestures.append((t + d.get("gdel", 0.0), gname, d.get("gd", 0.6), d.get("ga", 1.0)))
            if d.get("blink"):
                self.blink_force.append(t)
            if "flag" in d:
                self.flags.append((t, d["flag"]))
        self.expr = Track(ek, expr_face("neutral"))
        self.gaze = gk
        self.pose = Track(pk, poses.pose_for(name, "hug" if name == "pip" else "mug"))
        self.xoff = Track(xk, 0.0)
        self.stand = Track(sk, 0.0)
        self.wet = Track(wk, 0.0)
        self.tear = Track(rk, 0.0)
        self.lines = [ln for ln in tl()["lines"] if ln["speaker"] == SPEAKER[name]]
        self.line_starts = [ln["start"] for ln in self.lines]
        self.lip = {ln["id"]: build_lipsync_keys(ln) for ln in self.lines}
        self._blinks()
        self._emphasis()

    # ---------------- blinks
    def _blinks(self):
        rng = np.random.default_rng(11 if self.name == "pip" else 23)
        t = rng.uniform(0.5, 2.0)
        T = tl()["total"]
        bl = []
        while t < T:
            bl.append(t)
            t += rng.uniform(3.0, 6.0) if self.name == "tess" else rng.uniform(2.7, 5.4)
        bl += self.blink_force
        for ln in self.lines:
            if rng.uniform() < 0.3:
                bl.append(ln["start"] - 0.05)
        bl.sort()
        # drop blinks closer than 0.45 s to the previous
        out = []
        for b in bl:
            if b < 0.7:  # first frame doubles as the thumbnail: eyes open
                continue
            if not out or b - out[-1] > 0.45:
                out.append(b)
        self.blinks = out

    def blink_at(self, t):
        i = bisect.bisect_right(self.blinks, t + 0.1) - 1
        v = 0.0
        for j in (i, i - 1):
            if j < 0:
                continue
            b = self.blinks[j]
            d = t - b
            if -0.05 <= d < 0.0:
                v = max(v, (d + 0.05) / 0.05)
            elif 0.0 <= d < 0.04:
                v = max(v, 1.0)
            elif 0.04 <= d < 0.13:
                v = max(v, 1 - (d - 0.04) / 0.09)
        return v

    # ---------------- speech emphasis
    def _emphasis(self):
        self.emph = []
        for ln in self.lines:
            for k, w in enumerate(ln["words"]):
                dur = w["end"] - w["start"]
                ph = w.get("ph", "")
                if "ˈ" in ph and dur > 0.2 and len(w["text"]) >= 4:
                    h = (sum(ord(ch_) for ch_ in w["text"]) + k * 7) % 3
                    if h != 0:
                        self.emph.append((w["start"], dur, 0.6 + 0.4 * (h == 1)))
            if ln["text"].strip().endswith("?"):
                self.emph.append((ln["end"] - 0.35, 0.5, -1.0))  # question: brows up + tilt

    def speaking(self, t):
        i = bisect.bisect_right(self.line_starts, t + 0.08) - 1
        if i < 0:
            return None
        ln = self.lines[i]
        if t <= ln["end"] + 0.12:
            return ln
        return None

    # ---------------- gaze
    def gaze_target(self, tgt, place, other_place):
        hx, hy = head_world(self.name, place)
        if isinstance(tgt, (tuple, list)):
            return tgt
        if tgt == "other":
            return head_world(self.other, other_place)
        if tgt == "other_hands":
            ox, oy, os_ = other_place
            return ox + 75 * os_, oy - 150 * os_
        if tgt == "mug":
            x, y, s = place
            return x + 50 * s, y - 95 * s
        if tgt == "hands":
            x, y, s = place
            return x + 60 * s, y - 110 * s
        if tgt == "down":
            return hx + 40, hy + 280
        if tgt == "down_l":
            return hx - 160, hy + 230
        if tgt == "away":
            return hx - 330, hy + 60
        if tgt == "away_r":
            return hx + 330, hy + 90
        if tgt == "cam":
            return None
        return GAZE_POINTS[tgt]

    def gaze_angles(self, tgt, place, other_place):
        p = self.gaze_target(tgt, place, other_place)
        if p is None:
            return 0.0, 0.0
        hx, hy = head_world(self.name, place)
        dx, dy = p[0] - hx, p[1] - hy
        return math.atan2(dx, 300.0), math.atan2(-dy, 300.0)

    def gaze_at(self, t, place, other_place, lag=0.0, trans_mul=1.0):
        """Blend of gaze angles (h, v) with per-key transitions."""
        keys = self.gaze
        if not keys:
            return self.gaze_angles("other" if self.name == "tess" else "moon", place, other_place)
        tt = t - lag
        times = [k[0] for k in keys]
        i = bisect.bisect_right(times, tt) - 1
        if i < 0:
            return self.gaze_angles(keys[0][1], place, other_place)
        cur = self.gaze_angles(keys[i][1], place, other_place)
        if i == 0:
            return cur
        prev = self.gaze_angles(keys[i - 1][1], place, other_place)
        tr = keys[i][2] * trans_mul
        u = smoothstep(0, 1, (tt - keys[i][0]) / max(1e-3, tr))
        return prev[0] + (cur[0] - prev[0]) * u, prev[1] + (cur[1] - prev[1]) * u

    # ---------------- full state
    def place_at(self, t, base=None):
        x, y, s = base or BASE_PLACE[self.name]
        x += self.xoff.at(t)
        st = self.stand.at(t)
        y -= st * 185.0 * s
        return (x, y, s), st

    def state(self, t, place, other_place):
        f = dict(self.expr.at(t))
        pose = dict(self.pose.at(t))
        # wet eyes / tears tracks add on top
        f["wet"] = max(f.get("wet", 0.0), self.wet.at(t))
        f["tear"] = self.tear.at(t)
        # gaze
        gh, gv = self.gaze_at(t, place, other_place)
        hh, hv = self.gaze_at(t, place, other_place, lag=0.1, trans_mul=3.2)
        yaw = clamp(0.12 + 0.62 * hh, -0.45, 0.5)
        pitch = clamp(0.25 * hv, -0.2, 0.32)
        f["yaw"] = yaw + f.get("yaw_off", 0.0)
        f["pitch"] = pitch
        f["roll"] = f.get("roll", 0.0)
        gx = clamp((0.95 * gh - (yaw - 0.12)) * 2.4, -0.95, 0.95)
        gy = clamp(-(gv - 1.5 * pitch) * 1.8, -1.0, 1.0)
        # micro-saccades
        seed = 3 if self.name == "pip" else 9
        k = math.floor(t * 1.15)
        fr = t * 1.15 - k

        def h(i_):
            x = math.sin((i_ + seed * 17.3) * 12.9898) * 43758.5453
            return (x - math.floor(x)) * 2 - 1

        u = smoothstep(0.0, 0.05, fr)
        f["gx"] = clamp(gx + 0.06 * (h(k - 1) * (1 - u) + h(k) * u), -1, 1)
        f["gy"] = clamp(gy + 0.05 * (h(k + 500 - 1) * (1 - u) + h(k + 500) * u), -1, 1)
        # looking down lowers the lids
        if f["gy"] > 0.25:
            f["eopen"] = f["eopen"] * (1 - 0.32 * (f["gy"] - 0.25))
        if f["gy"] < -0.5:
            f["eopen"] = f["eopen"] + 0.08 * (-f["gy"] - 0.5)
        # idle sway
        f["roll"] += 0.025 * fbm1(t * 0.35, seed)
        f["yaw"] += 0.02 * fbm1(t * 0.3, seed + 5)
        pose["breath"] = math.sin(2 * math.pi * t / (3.5 if self.name == "pip" else 4.3) + seed)
        pose.setdefault("head_dy", 0.0)
        # speech
        ln = self.speaking(t)
        mo = f.get("mopen_base", 0.0)
        if ln is not None:
            vis = mouth_from_keys(self.lip[ln["id"]], t)
            env = env_at(ln["id"], t - ln["start"])
            op = vis[0] * (0.5 + 0.85 * min(1.0, env)) if vis[0] > 0 else 0.0
            f["mopen"] = max(op, mo * 0.4)
            f["mwide"] = vis[1] * (1 + 0.1 * f.get("msmile", 0))
            f["mround"] = max(vis[2], f.get("mround", 0) * 0.3)
            f["mteeth"] = vis[3]
            f["mtongue"] = vis[4]
            # smiling while talking keeps a gentler smile
            f["msmile"] = f.get("msmile", 0) * 0.75
            # talking head motion from loudness
            f["pitch"] += 0.022 * (env - 0.5)
            f["roll"] += 0.015 * math.sin(t * 3.1 + seed)
        else:
            f["mopen"] = mo
        # emphasis beats
        for (te, dur, a) in self.emph:
            if te - 0.1 <= t <= te + dur + 0.3:
                u = (t - te + 0.1) / (dur + 0.4)
                b = _bump(u)
                if a < 0:
                    f["braise"] = f.get("braise", 0) + 0.35 * b
                    f["roll"] += 0.06 * b
                else:
                    f["braise"] = f.get("braise", 0) + 0.18 * a * b
                    f["pitch"] -= 0.03 * a * b
        # gestures
        for (tg, kind, dur, amp) in self.gestures:
            if tg <= t <= tg + dur:
                off = gesture_offsets(kind, (t - tg) / dur, amp)
                for kk, vv in off.items():
                    if kk in ("shrug", "head_dy"):
                        pose[kk] = pose.get(kk, 0.0) + vv
                    else:
                        f[kk] = f.get(kk, 0.0) + vv
        # blink (closing eyes already shut does nothing)
        f["blink"] = max(f.get("blink", 0.0), self.blink_at(t))
        f.pop("mopen_base", None)
        f.pop("yaw_off", None)
        return f, pose


_ACTORS = None


def actors():
    global _ACTORS
    if _ACTORS is None:
        import acting_script
        _ACTORS = {n: Actor(n, acting_script.KEYS[n]) for n in ("pip", "tess")}
        # two people blinking on the same frame looks mechanical: nudge Pip's blink later
        tb = _ACTORS["tess"].blinks
        moved = []
        for b in _ACTORS["pip"].blinks:
            j = bisect.bisect_left(tb, b - 0.2)
            if j < len(tb) and abs(tb[j] - b) < 0.2:
                b = tb[j] + 0.32
            moved.append(b)
        _ACTORS["pip"].blinks = sorted(moved)
    return _ACTORS
