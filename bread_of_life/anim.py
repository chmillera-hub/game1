"""Performance system: expression/gaze/head/arm keyframes + automatic life
(lip sync, blinks, saccades, breathing, idle sway, speech emphasis).

Everything is evaluated once for all frames into numpy tracks so the parallel
renderer only has to index them.
"""
import json
import math
import os

import numpy as np
import soundfile as sf

from config import FPS, WORK
from body import DEFAULT_POLE
from rig import DEFAULT_P

NUM_PARAMS = [k for k, v in DEFAULT_P.items() if isinstance(v, float)]

EXPR_KEYS = ["eo_l", "eo_r", "lo_l", "lo_r", "br_l", "br_r", "bi_l", "bi_r", "bfur", "m_smile", "m_smirk",
             "m_press", "m_open", "m_wide", "m_round", "m_teeth", "pupil", "wet", "blush", "shrug"]

EXPR = {
    "neutral": {},
    "gentle": dict(m_smile=0.18, lo_l=0.15, lo_r=0.15, bi_l=0.12, bi_r=0.12),
    "warm": dict(m_smile=0.45, lo_l=0.35, lo_r=0.35, eo_l=0.88, eo_r=0.88, bi_l=0.1, bi_r=0.1),
    "joy": dict(m_smile=0.75, lo_l=0.55, lo_r=0.55, eo_l=0.7, eo_r=0.7, br_l=0.2, br_r=0.2, m_open=0.12, m_teeth=0.6),
    "compassion": dict(bi_l=0.45, bi_r=0.45, m_smile=0.12, eo_l=0.88, eo_r=0.88, lo_l=0.2, lo_r=0.2),
    "sorrow": dict(bi_l=0.75, bi_r=0.75, br_l=-0.1, br_r=-0.1, eo_l=0.72, eo_r=0.72, m_smile=-0.3),
    "firm": dict(bi_l=-0.22, bi_r=-0.22, bfur=0.25, eo_l=1.0, eo_r=1.0, m_press=0.35),
    "intense": dict(bi_l=-0.4, bi_r=-0.4, bfur=0.5, eo_l=1.06, eo_r=1.06, m_press=0.3, pupil=0.9),
    "sad_smile": dict(bi_l=0.55, bi_r=0.55, m_smile=0.3, eo_l=0.8, eo_r=0.8, lo_l=0.3, lo_r=0.3),
    "surprised": dict(br_l=0.8, br_r=0.8, eo_l=1.18, eo_r=1.18, m_open=0.22, pupil=0.85),
    "skeptical": dict(br_l=0.55, br_r=-0.2, bi_r=-0.3, eo_l=0.95, eo_r=0.74, m_smirk=0.35, m_smile=-0.1),
    "suspicious": dict(bi_l=-0.3, bi_r=-0.3, bfur=0.3, eo_l=0.74, eo_r=0.74, m_press=0.45, m_smile=-0.15),
    "indignant": dict(bi_l=-0.4, bi_r=-0.4, bfur=0.6, br_l=0.1, br_r=0.1, eo_l=1.1, eo_r=1.1, m_smile=-0.35),
    "anxious": dict(bi_l=0.55, bi_r=0.55, br_l=0.2, br_r=0.2, eo_l=1.05, eo_r=1.05, m_smile=-0.2, m_press=0.2),
    "hopeful": dict(bi_l=0.5, bi_r=0.5, br_l=0.15, br_r=0.15, eo_l=1.08, eo_r=1.08, m_smile=0.15, wet=0.6),
    "longing": dict(bi_l=0.65, bi_r=0.65, eo_l=0.95, eo_r=0.95, wet=0.85, m_smile=-0.08),
    "tearful": dict(bi_l=0.85, bi_r=0.85, eo_l=0.74, eo_r=0.74, lo_l=0.25, lo_r=0.25, wet=1.0, m_smile=-0.35),
    "moved": dict(bi_l=0.6, bi_r=0.6, eo_l=0.84, eo_r=0.84, lo_l=0.32, lo_r=0.32, wet=0.9, m_smile=0.35),
    "awe": dict(br_l=0.55, br_r=0.55, bi_l=0.3, bi_r=0.3, eo_l=1.12, eo_r=1.12, m_open=0.1, pupil=1.15),
    "confused": dict(br_l=0.5, br_r=-0.1, bi_l=0.3, bfur=0.3, eo_l=1.0, eo_r=0.9, m_smile=-0.15, m_smirk=-0.2),
    "shocked": dict(br_l=0.9, br_r=0.9, bi_l=0.3, bi_r=0.3, eo_l=1.22, eo_r=1.22, m_open=0.28, pupil=0.75),
    "hurt": dict(bi_l=0.7, bi_r=0.7, bfur=0.35, eo_l=0.8, eo_r=0.8, m_press=0.35, m_smile=-0.3),
    "resolute": dict(bi_l=0.2, bi_r=0.2, eo_l=1.0, eo_r=1.0, m_press=0.25, m_smile=0.05),
    "knowing": dict(m_smile=0.32, m_smirk=0.35, lo_l=0.3, lo_r=0.3, eo_l=0.85, eo_r=0.85, br_l=0.15),
    "guilty": dict(bi_l=0.45, bi_r=0.45, eo_l=0.78, eo_r=0.78, m_press=0.3, m_smile=-0.15),
    "ashamed": dict(bi_l=0.5, bi_r=0.5, eo_l=0.7, eo_r=0.7, m_press=0.25, m_smile=-0.2, blush=0.25),
    "pleading": dict(bi_l=0.8, bi_r=0.8, br_l=0.2, br_r=0.2, eo_l=1.0, eo_r=1.0, wet=0.7, m_smile=-0.2),
    "peace": dict(m_smile=0.22, lo_l=0.25, lo_r=0.25, eo_l=0.82, eo_r=0.82, bi_l=0.15, bi_r=0.15),
    "grumble": dict(bi_l=-0.35, bi_r=-0.2, bfur=0.45, eo_l=0.8, eo_r=0.85, m_press=0.2, m_smile=-0.3, m_smirk=0.25),
    "eyes_closed": dict(eo_l=0.0, eo_r=0.0, bi_l=0.2, bi_r=0.2),
}

# --- visemes ----------------------------------------------------------------
V_OPEN = {"a": 0.78, "ɑ": 0.75, "æ": 0.7, "ɐ": 0.55, "ʌ": 0.5, "ə": 0.32, "ɚ": 0.3, "ɜ": 0.38, "ᵊ": 0.25,
          "ɛ": 0.5, "e": 0.45, "i": 0.22, "ɪ": 0.28, "j": 0.18, "ᵻ": 0.25,
          "o": 0.5, "ɔ": 0.58, "ɒ": 0.6, "u": 0.18, "ʊ": 0.24, "w": 0.12,
          "ɹ": 0.18, "ɾ": 0.2, "r": 0.2, "l": 0.26, "n": 0.16, "t": 0.14, "d": 0.16, "k": 0.2, "ɡ": 0.2, "g": 0.2,
          "ŋ": 0.2, "h": 0.3, "s": 0.08, "z": 0.08, "ʃ": 0.12, "ʒ": 0.12, "ʧ": 0.12, "ʤ": 0.12,
          "θ": 0.12, "ð": 0.12, "f": 0.05, "v": 0.05, "p": 0.0, "b": 0.0, "m": 0.0, "x": 0.25, "ʔ": 0.1,
          "ç": 0.2, "ʲ": 0.15}
V_WIDE = {"i": 0.55, "ɪ": 0.4, "j": 0.4, "e": 0.35, "ɛ": 0.3, "æ": 0.35, "a": 0.15, "s": 0.35, "z": 0.3,
          "t": 0.2, "d": 0.2, "n": 0.15, "θ": 0.2, "ð": 0.2, "ᵻ": 0.3}
V_ROUND = {"o": 0.65, "ɔ": 0.55, "ɒ": 0.4, "u": 0.95, "ʊ": 0.7, "w": 1.0, "ɹ": 0.4, "ʃ": 0.55, "ʒ": 0.5,
           "ʧ": 0.5, "ʤ": 0.5, "ɚ": 0.3}
V_TEETH = {"f": 1.0, "v": 1.0, "s": 0.8, "z": 0.8, "θ": 0.7, "ð": 0.7, "i": 0.5, "ɪ": 0.4, "ʃ": 0.5, "t": 0.4,
           "d": 0.4, "ɛ": 0.35, "æ": 0.4, "e": 0.4}
CLOSURE = set("pbm")
VOWELS = set("aɑæɐʌəɚɜᵊɛeiɪoɔɒuʊᵻ")


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def bump(t, center, width):
    """Smooth 0->1->0 bump of total length `width` centered at `center`."""
    x = (t - (center - width / 2)) / width
    return np.where((x > 0) & (x < 1), np.sin(np.clip(x, 0, 1) * np.pi) ** 2, 0.0)


def noise1(t, seed, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros_like(t)
    amp = 1.0
    tot = 0
    for o in range(octaves):
        f = 0.5 * (2 ** o) * rng.uniform(0.8, 1.25)
        ph = rng.uniform(0, 2 * np.pi)
        ph2 = rng.uniform(0, 2 * np.pi)
        out += amp * (0.6 * np.sin(2 * np.pi * f * t + ph) + 0.4 * np.sin(2 * np.pi * f * 1.618 * t + ph2))
        tot += amp
        amp *= 0.5
    return out / tot


class Perf:
    def __init__(self, name, seed=0):
        self.name = name
        self.seed = seed
        self.ekeys = [(0.0, "neutral", {}, 0.01)]
        self.hkeys = []  # head/body pose keys: (t, dict, dur)
        self.gkeys = []  # gaze keys: (t, gx, gy, dur)
        self.akeys = {"arm_l": [], "arm_r": []}
        self.tears = []  # (side, t0, t1)
        self.fixed = []  # (t0, t1, dict) hard overrides
        self.nods = []  # (t, amount, dur)
        self.shakes = []  # (t, amp, dur, cycles)
        self.mimes = []  # (t0, t1, amount): talking we see but do not hear (under narration)
        self.blink_rate = [(0.0, 1.0)]
        self.extra_blinks = []
        self.no_blink = []  # (t0, t1)
        self.speaking_lines = []
        self.listen_nods = True
        self.wind = [(0.0, 0.0)]
        self.lip_gain = 1.5

    # --- authoring API ---
    def expr(self, t, name, dur=0.5, **over):
        self.ekeys.append((t, name, over, dur))
        return self

    def pose(self, t, dur=0.8, **kw):
        self.hkeys.append((t, kw, dur))
        return self

    def look(self, t, gx, gy=0.0, dur=0.18):
        self.gkeys.append((t, gx, gy, dur))
        return self

    def arm(self, t, side, spec, dur=0.7):
        if spec is not None:
            spec = dict(spec, side_hint=(1 if side == "r" else -1))
        self.akeys["arm_" + side].append((t, spec, dur))
        return self

    def tear(self, side, t0, t1):
        self.tears.append((side, t0, t1))
        return self

    def nod(self, t, amount=4.0, dur=0.6):
        self.nods.append((t, amount, dur))
        return self

    def shake(self, t, amp=4.0, dur=1.0, cycles=2):
        """A slow, slight side-to-side shake of the head (a wordless "no")."""
        self.shakes.append((t, amp, dur, cycles))
        return self

    def mime(self, t0, t1, amount=0.35):
        self.mimes.append((t0, t1, amount))
        return self

    def blink(self, t):
        self.extra_blinks.append(t)
        return self

    def blinks(self, t, rate):
        self.blink_rate.append((t, rate))
        return self

    def hold_eyes(self, t0, t1):
        self.no_blink.append((t0, t1))
        return self

    # --- evaluation ---
    def evaluate(self, n_frames, T, voice_dir):
        t = np.arange(n_frames) / FPS
        out = {k: np.full(n_frames, DEFAULT_P[k], dtype=np.float64) for k in NUM_PARAMS}
        out["t"] = t.copy()
        # 1) expressions (each key sets all expression params; missing -> default)
        keys = sorted(self.ekeys, key=lambda k: k[0])
        for k in EXPR_KEYS:
            out[k] = self._keyed(t, [(kt, self._expr_val(name, over, k), d) for kt, name, over, d in keys], DEFAULT_P[k])
        # 2) head/body pose keys (sticky per param)
        hk = sorted(self.hkeys, key=lambda k: k[0])
        params = set()
        for _, kw, _ in hk:
            params |= set(kw.keys())
        for p in params:
            seq = [(kt, kw[p], d) for kt, kw, d in hk if p in kw]
            out[p] = self._keyed(t, seq, DEFAULT_P.get(p, 0.0))
        # 3) gaze
        gk = sorted(self.gkeys, key=lambda k: k[0])
        out["gx"] = self._keyed(t, [(kt, gx, d) for kt, gx, gy, d in gk], 0.0)
        out["gy"] = self._keyed(t, [(kt, gy, d) for kt, gx, gy, d in gk], 0.0)
        # 4) speech
        speak = np.zeros(n_frames)
        lip = self._lipsync(t, T, voice_dir, speak)
        # 5) automatic life
        rng = np.random.default_rng(self.seed + 17)
        # idle sway (less while speaking? a bit more expressive while speaking)
        amp = 1.0 + 0.5 * speak
        out["yaw"] += 1.3 * noise1(t * 0.32, self.seed + 1) * amp
        out["pitch"] += 0.9 * noise1(t * 0.41, self.seed + 2) * amp
        out["roll"] += 0.9 * noise1(t * 0.27, self.seed + 3)
        out["bx"] += 0.03 * noise1(t * 0.2, self.seed + 4)
        # breathing
        period = 4.2
        out["breath"] += 0.5 + 0.5 * np.sin(2 * np.pi * t / period + self.seed)
        # speech emphasis: nods + brow raises on stressed words
        for (t0, amount, d) in self.nods:
            out["pitch"] += amount * bump(t, t0 + d / 2, d)
        for (t0, sa, d, cyc) in self.shakes:
            x = np.clip((t - t0) / d, 0.0, 1.0)
            env = np.sin(np.pi * x) ** 1.5
            dy = sa * env * np.sin(2 * np.pi * cyc * x)
            out["yaw"] += dy
            out["roll"] += 0.18 * sa * env * np.sin(2 * np.pi * cyc * x - 0.6)
            out["gx"] -= 0.012 * dy  # the eyes stay on the listener while the head turns
        out["pitch"] += lip["nod"]
        out["br_l"] += lip["brow"]
        out["br_r"] += lip["brow"]
        out["yaw"] += lip["yaw"]
        out["breath"] += lip["inhale"]
        # mouth: blend expression with visemes
        s = speak
        out["m_open"] = out["m_open"] * (1 - s) + lip["open"] * self.lip_gain + out["m_open"] * s * 0.3
        out["m_wide"] = out["m_wide"] + lip["wide"]
        out["m_round"] = out["m_round"] * (1 - s) + lip["round"]
        out["m_teeth"] = np.maximum(out["m_teeth"] * (1 - s), lip["teeth"])
        out["m_smile"] = out["m_smile"] * (1 - 0.45 * lip["round"]) * (1 - 0.25 * s)
        out["m_press"] = out["m_press"] * (1 - s)
        for (t0, t1, amount) in self.mimes:
            env = np.clip((t - t0) / 0.3, 0, 1) * np.clip((t1 - t) / 0.3, 0, 1)
            syl = np.maximum(0.0, np.sin(t * 8.7 + self.seed) * np.sin(t * 2.1 + 0.7 * self.seed))
            out["m_open"] += amount * env * syl
            out["pitch"] += 1.5 * env * np.sin(t * 3.3 + self.seed)
        # saccades when not speaking
        sac_x = np.zeros(n_frames)
        sac_y = np.zeros(n_frames)
        tt = rng.uniform(0.3, 1.0)
        cur = (0.0, 0.0)
        while tt < t[-1]:
            nxt = (rng.uniform(-0.07, 0.07), rng.uniform(-0.05, 0.04))
            i0 = int(tt * FPS)
            i1 = min(n_frames, i0 + 2)
            sac_x[i0:] = nxt[0]
            sac_y[i0:] = nxt[1]
            tt += rng.uniform(0.7, 2.2)
        out["gx"] += sac_x * (1 - 0.5 * s)
        out["gy"] += sac_y * (1 - 0.5 * s)
        # blinks
        mult = np.ones(n_frames)
        bt = self._blink_times(t, rng, out)
        for b in bt:
            mult = np.minimum(mult, self._blink_curve(t, b))
        out["eo_l"] = out["eo_l"] * mult
        out["eo_r"] = out["eo_r"] * mult
        # tears
        for side, t0, t1 in self.tears:
            k = "tear_l" if side == "l" else "tear_r"
            prog = np.clip((t - t0) / max(t1 - t0, 1e-3), 0, None)
            out[k] = np.maximum(out[k], np.where(t >= t0, np.minimum(prog * 1.4, 1.6), 0.0))
        # wind
        wt = sorted(self.wind)
        out["wind"] = np.interp(t, [w[0] for w in wt] + [t[-1] + 1], [w[1] for w in wt] + [wt[-1][1]])
        # secondary hair motion from head yaw velocity (simple lag spring)
        yaw = out["yaw"]
        vel = np.gradient(yaw) * FPS
        hd = np.zeros(n_frames)
        x, v = 0.0, 0.0
        for i in range(n_frames):
            target = -vel[i] * 0.004
            a = 40.0 * (target - x) - 7.0 * v
            v += a / FPS
            x += v / FPS
            hd[i] = x
        out["hair_dx"] += hd
        # arms
        arms = {}
        for side in ("arm_l", "arm_r"):
            arms[side] = self._arm_track(t, self.akeys[side])
        # fixed overrides
        for (t0, t1, d) in self.fixed:
            m = (t >= t0) & (t < t1)
            for k, v in d.items():
                out[k][m] = v
        out["speak"] = speak
        return out, arms

    def _expr_val(self, name, over, k):
        base = EXPR[name] if isinstance(name, str) else name
        if k in over:
            return over[k]
        return base.get(k, DEFAULT_P[k])

    @staticmethod
    def _keyed(t, seq, default):
        """Piecewise transitions: at each key time the value eases to the key's value over dur."""
        out = np.full(len(t), float(default))
        if not seq:
            return out
        seq = sorted(seq, key=lambda s: s[0])
        cur = float(default)
        fr = np.arange(len(t))
        for i, (kt, v, d) in enumerate(seq):
            i0 = int(round(kt * FPS))
            if i0 >= len(t):
                break
            i0 = max(i0, 0)
            start_val = out[i0] if i0 < len(t) else cur
            d = max(d, 1e-3)
            seg = slice(i0, len(t))
            x = (t[seg] - kt) / d
            out[seg] = start_val + (v - start_val) * smoothstep(x)
            cur = v
        return out

    def _blink_times(self, t, rng, out):
        times = []
        rates = sorted(self.blink_rate)
        tt = rng.uniform(0.5, 2.0)
        while tt < t[-1]:
            r = [rr for (rt, rr) in rates if rt <= tt]
            rate = r[-1] if r else 1.0
            if rate <= 0:
                tt += 0.5
                continue
            ok = not any(a <= tt <= b for a, b in self.no_blink)
            if ok:
                times.append(tt)
                if rng.uniform() < 0.12:
                    times.append(tt + 0.28)
            tt += rng.uniform(2.2, 5.0) / rate
        times += self.extra_blinks
        # blink on large gaze shifts
        for (kt, gx, gy, d) in self.gkeys:
            if rng.uniform() < 0.45:
                times.append(kt + 0.01)
        return sorted(times)

    @staticmethod
    def _blink_curve(t, b):
        close, hold, open_ = 0.065, 0.035, 0.12
        y = np.ones(len(t))
        a = (t >= b) & (t < b + close)
        y[a] = 1 - (t[a] - b) / close
        h = (t >= b + close) & (t < b + close + hold)
        y[h] = 0.0
        o = (t >= b + close + hold) & (t < b + close + hold + open_)
        y[o] = smoothstep((t[o] - b - close - hold) / open_)
        return y

    def _arm_track(self, t, keys):
        """Returns a list (per frame) of arm specs with interpolated targets."""
        n = len(t)
        res = [None] * n
        if not keys:
            return res
        keys = sorted(keys, key=lambda k: k[0])
        rest_cache = {}
        prev = None
        for i, (kt, spec, d) in enumerate(keys):
            t_end = keys[i + 1][0] if i + 1 < len(keys) else t[-1] + 1
            i0 = max(0, int(round(kt * FPS)))
            i1 = min(n, int(round(t_end * FPS)))
            for f in range(i0, i1):
                x = smoothstep((t[f] - kt) / max(d, 1e-3))
                res[f] = _blend_arm(prev, spec, x)
            prev = _blend_arm(prev, spec, 1.0) if spec else None
        return res

    def _lipsync(self, t, T, voice_dir, speak):
        n = len(t)
        z = lambda: np.zeros(n)
        res = dict(open=z(), wide=z(), round=z(), teeth=z(), nod=z(), brow=z(), yaw=z(), inhale=z())
        rng = np.random.default_rng(self.seed + 99)
        hi = 240
        for lid in self.speaking_lines:
            m = T.lines[lid]
            t0 = m["start"]
            dur = m["duration"]
            # audio envelope
            wav, sr = sf.read(os.path.join(voice_dir, lid + ".wav"))
            hop = sr // 100
            nwin = len(wav) // hop
            env = np.sqrt(np.mean(wav[: nwin * hop].reshape(nwin, hop) ** 2, axis=1) + 1e-12)
            env = env / (np.percentile(env, 92) + 1e-9)
            env = np.clip(env, 0, 1.2)
            env_t = (np.arange(nwin) + 0.5) / 100.0
            # high-rate viseme targets
            N = int(dur * hi) + 2
            th = np.arange(N) / hi
            o = np.zeros(N)
            w = np.zeros(N)
            r = np.zeros(N)
            te = np.zeros(N)
            closed = np.zeros(N, dtype=bool)
            for p in m["phonemes"]:
                c = p["p"]
                a = int(p["s"] * hi)
                b = max(a + 1, int(p["e"] * hi))
                if c in V_OPEN:
                    o[a:b] = V_OPEN[c]
                    w[a:b] = V_WIDE.get(c, 0.0)
                    r[a:b] = V_ROUND.get(c, 0.0)
                    te[a:b] = V_TEETH.get(c, 0.0)
                    if c in CLOSURE:
                        closed[a:b] = True
            # coarticulation smoothing
            def smooth(x, sig):
                k = np.exp(-0.5 * (np.arange(-3 * sig, 3 * sig + 1) / sig) ** 2)
                k /= k.sum()
                return np.convolve(x, k, mode="same")
            sig = int(0.028 * hi)
            o = smooth(o, sig)
            w = smooth(w, sig)
            r = smooth(r, int(0.04 * hi))
            te = smooth(te, sig)
            e = np.interp(th, env_t, env)
            o = o * (0.35 + 0.75 * np.clip(e, 0, 1)) * np.clip(e * 4, 0, 1)
            o[closed] = np.minimum(o[closed], 0.02)
            # sample at frame times with a slight lead
            lead = 0.035
            ft = t - t0 + lead
            mask = (ft >= 0) & (ft <= dur)
            res["open"] += np.where(mask, np.interp(ft, th, o), 0.0)
            res["wide"] += np.where(mask, np.interp(ft, th, w), 0.0)
            res["round"] += np.where(mask, np.interp(ft, th, r), 0.0)
            res["teeth"] += np.where(mask, np.interp(ft, th, te) * np.clip(np.interp(ft, th, o) * 3, 0, 1), 0.0)
            sp = np.clip((np.minimum(t - t0 + 0.15, t0 + dur + 0.25 - t)) / 0.15, 0, 1)
            speak[:] = np.maximum(speak, sp)
            # emphasis: stressed syllables with strong energy -> small nod + brow lift
            ph = m["phonemes"]
            last = -10
            for i, p in enumerate(ph):
                if p["p"] == "ˈ" and i + 1 < len(ph):
                    ts = ph[i + 1]["s"]
                    ev = float(np.interp(ts + 0.06, env_t, env))
                    if ev > 0.75 and ts - last > 0.9 and rng.uniform() < 0.75:
                        amt = rng.uniform(1.6, 3.2)
                        res["nod"] += amt * bump(t, t0 + ts + 0.12, 0.42)
                        res["brow"] += rng.uniform(0.12, 0.3) * bump(t, t0 + ts + 0.05, 0.55)
                        last = ts
            # phrase-level head drift + inhale before each segment
            for si, s in enumerate(m["segments"]):
                target = rng.uniform(-3.0, 3.0)
                ts = t0 + s["start"]
                te_ = t0 + s["end"]
                x = smoothstep((t - ts) / 0.6) * (1 - smoothstep((t - te_) / 0.8))
                res["yaw"] += target * x
                res["inhale"] += 0.6 * bump(t, ts - 0.25, 0.7)
        return res


def _t3(t):
    return (t[0], t[1], t[2] if len(t) > 2 else 0.6)


def _lerp3(p, q, x):
    return tuple(a + (b - a) * x for a, b in zip(p, q))


def _blend_arm(a, b, x):
    """Blend between two gesture specs; None means the arm hangs at rest."""
    if b is None and a is None:
        return None
    if b is None:
        if x >= 1.0:
            return None
        spec = dict(a)
        spec["rest_blend"] = float(x)
        spec["tilt"] = a.get("tilt", 0.0) * (1.0 - x)
        spec["wrist"] = a.get("wrist", 8.0) + (8.0 - a.get("wrist", 8.0)) * x
        spec["pole"] = _lerp3(a.get("pole") or DEFAULT_POLE, DEFAULT_POLE, x)
        if a.get("hand", "relaxed") != "relaxed":
            spec["hand"] = a.get("hand", "relaxed")
            spec["hand_b"] = "relaxed"
            spec["hand_t"] = float(x)
        return spec
    if a is None:
        spec = dict(b)
        spec["rest_blend"] = float(1.0 - x)
        spec["tilt"] = b.get("tilt", 0.0) * x
        spec["wrist"] = 8.0 + (b.get("wrist", 8.0) - 8.0) * x
        spec["pole"] = _lerp3(DEFAULT_POLE, b.get("pole") or DEFAULT_POLE, x)
        if x < 1.0:
            spec["hand"] = "relaxed"
            spec["hand_b"] = b.get("hand", "relaxed")
            spec["hand_t"] = float(x)
        return spec
    spec = dict(b)
    ta, tb = _t3(a["target"]), _t3(b["target"])
    spec["target"] = tuple(p + (q - p) * x for p, q in zip(ta, tb))
    wa, wb = a.get("wrist", 8.0), b.get("wrist", 8.0)
    spec["wrist"] = wa + (wb - wa) * x
    spec["tilt"] = a.get("tilt", 0.0) + (b.get("tilt", 0.0) - a.get("tilt", 0.0)) * x
    spec["pole"] = _lerp3(a.get("pole") or DEFAULT_POLE, b.get("pole") or DEFAULT_POLE, x)
    if x < 1.0 and a.get("hand") != b.get("hand"):
        spec["hand"] = a.get("hand", "relaxed")
        spec["hand_b"] = b.get("hand", "relaxed")
        spec["hand_t"] = float(x)
    return spec
