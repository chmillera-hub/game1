"""Procedural performance curves (pure numpy, no bpy): emotions, lip sync, blinks, gaze, head, breathing.

Everything is sampled per frame. A Performance collects layers and produces:
  keys[name]  -> np.array(n_frames) shape-key weights (ARKit names + Microsoft viseme names)
  gaze        -> (n, 3) world-space gaze target points
  head        -> (n, 3) extra head rotation (pitch, yaw, roll) radians on top of look-at
  breath      -> (n,) breathing phase signal in [-1, 1]
"""
import math
import numpy as np

SYM = ["browDown", "browOuterUp", "cheekSquint", "eyeBlink", "eyeSquint", "eyeWide", "mouthSmile", "mouthFrown",
       "mouthPress", "mouthStretch", "mouthUpperUp", "mouthLowerDown", "mouthDimple", "noseSneer", "eyeLookDown",
       "eyeLookUp", "eyeLookIn", "eyeLookOut"]

# Emotion presets in ARKit terms. Keys without Left/Right that are in SYM are applied to both sides.
EMOTIONS = {
    "neutral": {},
    "calm": {"mouthSmile": 0.06, "eyeSquint": 0.06},
    "attentive": {"browInnerUp": 0.12, "eyeWide": 0.06},
    "sorrowful": {"browInnerUp": 0.55, "browDown": 0.1, "eyeSquint": 0.15, "mouthFrown": 0.28, "mouthPress": 0.15, "eyeBlink": 0.04},
    "sad_firm": {"browInnerUp": 0.35, "browDown": 0.28, "mouthPress": 0.3, "mouthFrown": 0.15, "eyeSquint": 0.2},
    "tender": {"browInnerUp": 0.3, "mouthSmile": 0.25, "cheekSquint": 0.15, "eyeSquint": 0.15, "eyeBlink": 0.03},
    "hopeful": {"browInnerUp": 0.28, "browOuterUp": 0.25, "mouthSmile": 0.3, "eyeWide": 0.1},
    "protective": {"browDown": 0.38, "mouthPress": 0.28, "eyeSquint": 0.25, "jawForward": 0.08},
    "reverent": {"browInnerUp": 0.3, "eyeBlink": 0.08, "mouthSmile": 0.1},
    "firm": {"browDown": 0.28, "mouthPress": 0.22, "eyeSquint": 0.15},
    "absolute": {"browDown": 0.12, "eyeWide": 0.08, "mouthPress": 0.12},
    "earnest": {"browInnerUp": 0.38, "browOuterUp": 0.15, "eyeWide": 0.1},
    "searching": {"browInnerUp": 0.38, "browDown": 0.1, "eyeSquint": 0.12},
    "reasoning": {"browOuterUpLeft": 0.32, "browInnerUp": 0.12, "browDownRight": 0.12, "mouthSmileLeft": 0.08},
    "pained": {"browInnerUp": 0.68, "browDown": 0.2, "eyeSquint": 0.35, "mouthFrown": 0.28, "mouthStretch": 0.12},
    "pleading": {"browInnerUp": 0.62, "eyeWide": 0.15, "mouthFrown": 0.1},
    "gentle": {"mouthSmile": 0.22, "browInnerUp": 0.2, "eyeSquint": 0.15},
    "impatient": {"browDown": 0.48, "noseSneer": 0.2, "mouthPress": 0.32, "eyeSquint": 0.3, "mouthLeft": 0.1},
    "contempt": {"browDown": 0.3, "noseSneer": 0.3, "mouthSmileRight": 0.25, "mouthPressLeft": 0.2, "eyeSquint": 0.3},
    "cold_fury": {"browDown": 0.72, "noseSneer": 0.45, "mouthPress": 0.45, "eyeSquint": 0.35, "jawForward": 0.12, "mouthUpperUp": 0.12},
    "furious": {"browDown": 0.9, "noseSneer": 0.6, "eyeWide": 0.25, "mouthUpperUp": 0.35, "mouthStretch": 0.25},
    "cold": {"browDown": 0.22, "mouthPress": 0.28, "eyeSquint": 0.2},
    "shaken": {"browInnerUp": 0.68, "eyeWide": 0.25, "mouthFrown": 0.15, "mouthStretch": 0.15, "mouthLowerDown": 0.1},
    "scared": {"browInnerUp": 0.72, "browOuterUp": 0.42, "eyeWide": 0.5, "mouthStretch": 0.3, "jawOpen": 0.05},
    "worried": {"browInnerUp": 0.62, "browDown": 0.15, "mouthPress": 0.2, "mouthFrown": 0.15},
    "stunned": {"browInnerUp": 0.45, "browOuterUp": 0.4, "eyeWide": 0.35, "jawOpen": 0.08, "mouthFunnel": 0.05},
    "breaking": {"browInnerUp": 0.88, "browDown": 0.3, "eyeSquint": 0.5, "cheekSquint": 0.3, "mouthFrown": 0.5,
                 "mouthStretch": 0.3, "mouthUpperUp": 0.12, "eyeBlink": 0.18},
    "crying": {"browInnerUp": 0.8, "browDown": 0.25, "eyeSquint": 0.45, "cheekSquint": 0.25, "mouthFrown": 0.45,
               "mouthStretch": 0.2, "eyeBlink": 0.2},
    "guarded": {"browDown": 0.22, "mouthPress": 0.22, "eyeSquint": 0.15},
    "hopeful_tears": {"browInnerUp": 0.6, "mouthSmile": 0.35, "eyeSquint": 0.35, "cheekSquint": 0.3},
    "warm_tears": {"browInnerUp": 0.5, "mouthSmile": 0.45, "eyeSquint": 0.4, "cheekSquint": 0.4},
    "joy": {"mouthSmile": 0.55, "cheekSquint": 0.4, "eyeSquint": 0.3, "browOuterUp": 0.15},
    "longing": {"browInnerUp": 0.5, "eyeBlink": 0.08, "mouthSmile": 0.1},
    "awe": {"browInnerUp": 0.45, "browOuterUp": 0.45, "eyeWide": 0.25, "jawOpen": 0.05, "mouthSmile": 0.1},
    "warm": {"mouthSmile": 0.35, "cheekSquint": 0.25, "eyeSquint": 0.2},
    "love": {"mouthSmile": 0.42, "cheekSquint": 0.3, "eyeSquint": 0.3, "browInnerUp": 0.25},
    "prayer": {"browInnerUp": 0.38, "eyeBlink": 0.1, "mouthSmile": 0.05},
    "prayer_warm": {"browInnerUp": 0.32, "mouthSmile": 0.2, "eyeSquint": 0.15},
    "soft": {"mouthSmile": 0.15, "browInnerUp": 0.1},
    "heavy": {"browInnerUp": 0.32, "browDown": 0.2},
    "tense": {"browDown": 0.32, "mouthPress": 0.25, "eyeSquint": 0.15},
    "hard": {"browDown": 0.5, "mouthPress": 0.35, "eyeSquint": 0.3, "noseSneer": 0.15},
    "scoff": {"browDown": 0.25, "noseSneer": 0.4, "mouthSmileLeft": 0.3, "mouthUpperUpLeft": 0.25, "eyeSquint": 0.25},
    "doubt": {"browInnerUp": 0.4, "browDownLeft": 0.25, "mouthPressLeft": 0.25, "mouthFrown": 0.12},
    "eyes_closed_peace": {"eyeBlink": 1.0, "mouthSmile": 0.25, "browInnerUp": 0.2},
    "eyes_closed_cry": {"eyeBlink": 0.95, "browInnerUp": 0.7, "mouthFrown": 0.35, "eyeSquint": 0.4, "cheekSquint": 0.3},
}

MOUTH_KEYS = {"mouthSmileLeft", "mouthSmileRight", "mouthFrownLeft", "mouthFrownRight", "mouthPressLeft",
              "mouthPressRight", "mouthStretchLeft", "mouthStretchRight", "mouthUpperUpLeft", "mouthUpperUpRight",
              "mouthLowerDownLeft", "mouthLowerDownRight", "mouthFunnel", "mouthPucker", "mouthLeft", "mouthRight",
              "jawOpen", "jawForward"}

VISEMES = ["aa_02", "aa_ah_ax_01", "ao_03", "aw_09", "ay_11", "d_t_n_19", "er_05", "ey_eh_uh_04", "f_v_18", "h_12",
           "k_g_ng_20", "l_14", "ow_08", "oy_10", "p_b_m_21", "r_13", "sh_ch_jh_zh_16", "s_z_15", "th_dh_17",
           "w_uw_07", "y_iy_ih_ix_06"]
VOWELS = {"aw_09", "oy_10", "ay_11", "ow_08", "aa_02", "aa_ah_ax_01", "ao_03", "ey_eh_uh_04", "er_05",
          "y_iy_ih_ix_06", "w_uw_07"}
# how strongly each viseme is shown (closures must fully close; small consonants subtle)
VIS_GAIN = {"p_b_m_21": 1.0, "f_v_18": 0.9, "w_uw_07": 0.85, "ow_08": 0.85, "sh_ch_jh_zh_16": 0.75,
            "aa_02": 0.75, "aa_ah_ax_01": 0.65, "ao_03": 0.75, "aw_09": 0.75, "ay_11": 0.7, "oy_10": 0.75,
            "ey_eh_uh_04": 0.6, "er_05": 0.6, "y_iy_ih_ix_06": 0.55, "d_t_n_19": 0.35, "s_z_15": 0.45,
            "th_dh_17": 0.5, "k_g_ng_20": 0.35, "l_14": 0.4, "r_13": 0.45, "h_12": 0.3}


def expand(preset, scale=1.0):
    out = {}
    for k, v in preset.items():
        if k in SYM:
            out[k + "Left"] = out.get(k + "Left", 0) + v * scale
            out[k + "Right"] = out.get(k + "Right", 0) + v * scale
        else:
            out[k] = out.get(k, 0) + v * scale
    return out


def smoothstep(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def value_noise(n, fps, freq, seed, octaves=2):
    """Smooth 1D noise in [-1, 1] sampled per frame."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / fps
    out = np.zeros(n)
    amp, f, tot = 1.0, freq, 0.0
    for _ in range(octaves):
        knots = rng.uniform(-1, 1, int(t[-1] * f) + 4 if n else 4)
        x = t * f
        i = np.floor(x).astype(int)
        u = smoothstep(x - i)
        out += amp * (knots[i] * (1 - u) + knots[i + 1] * u)
        tot += amp
        amp *= 0.5
        f *= 2.1
    return out / tot


class Performance:
    def __init__(self, n_frames, fps=24, seed=0):
        self.n = n_frames
        self.fps = fps
        self.seed = seed
        self.t = np.arange(n_frames) / fps
        self.keys = {}
        self.emotion_events = []      # (t, name, intensity, ramp)
        self.speech = []              # word dicts with phonemes, times in shot-local seconds
        self.env = np.zeros(n_frames)  # speech loudness envelope per frame (0..1)
        self.blink_extra = []         # forced blink times
        self.no_blink = []            # (t0, t1) windows (eyes closed by emotion etc.)
        self.gaze_events = []         # (t, target_xyz or callable, speed)
        self.head_events = []         # (t, kind, amount, dur)
        self.blink_rate = 3.6         # mean seconds between blinks

    # ---------------------------------------------------------------- emotions
    def emotion(self, t, name, intensity=1.0, ramp=0.5):
        self.emotion_events.append((t, name, intensity, ramp))

    def _emotion_layer(self):
        ev = sorted(self.emotion_events, key=lambda e: e[0])
        if not ev:
            ev = [(0.0, "neutral", 1.0, 0.1)]
        names = set()
        for e in ev:
            names |= set(expand(EMOTIONS[e[1]]).keys())
        layer = {k: np.zeros(self.n) for k in names}
        cur = {k: 0.0 for k in names}
        # piecewise: blend from previous state to new preset over its ramp time
        state_prev = {k: 0.0 for k in names}
        for idx, (t0, name, inten, ramp) in enumerate(ev):
            target = {k: 0.0 for k in names}
            target.update(expand(EMOTIONS[name], inten))
            t1 = ev[idx + 1][0] if idx + 1 < len(ev) else self.t[-1] + 1
            m = (self.t >= t0) & (self.t < t1)
            if not m.any():
                state_prev = target
                continue
            u = smoothstep((self.t[m] - t0) / max(ramp, 1e-3))
            for k in names:
                layer[k][m] = state_prev[k] * (1 - u) + target[k] * u
            # state at end of segment
            u_end = smoothstep(np.array([(t1 - t0) / max(ramp, 1e-3)]))[0]
            state_prev = {k: state_prev[k] * (1 - u_end) + target[k] * u_end for k in names}
        if ev[0][0] > 0:
            first = expand(EMOTIONS[ev[0][1]], ev[0][2])
            m = self.t < ev[0][0]
            for k in names:
                layer[k][m] = first.get(k, 0.0)
        return layer

    # ---------------------------------------------------------------- speech
    def add_speech(self, words, line_start_local, env=None):
        """words: [{start, end, phonemes, emph}] already in shot-local seconds."""
        self.speech.extend(words)

    def set_envelope(self, env):
        self.env = np.maximum(self.env, env)

    def _speech_layer(self):
        fps = self.fps
        vis = {v: np.zeros(self.n) for v in VISEMES}
        if not self.speech:
            return vis, np.zeros(self.n)
        for w in self.speech:
            ph = w.get("phonemes") or []
            if not ph:
                continue
            t0, t1 = w["start"], max(w["end"], w["start"] + 0.06)
            weights = np.array([1.6 if p in VOWELS else (0.7 if p in ("p_b_m_21", "d_t_n_19", "k_g_ng_20") else 1.0)
                                for p in ph])
            edges = t0 + (t1 - t0) * np.concatenate([[0], np.cumsum(weights) / weights.sum()])
            for i, p in enumerate(ph):
                if p == "sil_00" or p not in vis:
                    continue
                a, b = edges[i], edges[i + 1]
                c = (a + b) / 2
                half = max((b - a) / 2, 0.035)
                # coarticulation: attack/release extend beyond the phoneme
                lead = 0.06 if p == "p_b_m_21" else 0.05
                x = self.t
                shape = np.where(x < c, smoothstep((x - (a - lead)) / (c - (a - lead))),
                                 smoothstep(((b + lead) - x) / ((b + lead) - c)))
                vis[p] = np.maximum(vis[p], shape * VIS_GAIN.get(p, 0.6) * (0.45 if w.get("silent") else 1.0))
        # closures win: suppress open shapes during p/b/m
        closure = vis["p_b_m_21"]
        for v in VISEMES:
            if v not in ("p_b_m_21", "f_v_18"):
                vis[v] *= (1 - 0.85 * closure)
        total = sum(vis.values())
        scale = np.where(total > 1.1, 1.1 / np.maximum(total, 1e-6), 1.0)
        for v in VISEMES:
            vis[v] *= scale
        # light smoothing (3-frame)
        k = np.array([0.25, 0.5, 0.25])
        for v in VISEMES:
            vis[v] = np.convolve(vis[v], k, mode="same")
        jaw = np.convolve(self.env, np.ones(3) / 3, mode="same") * 0.18
        return vis, jaw

    # ---------------------------------------------------------------- blinks
    def blink(self, t):
        self.blink_extra.append(t)

    def _blink_layer(self):
        rng = np.random.default_rng(self.seed + 17)
        times = []
        t = rng.uniform(0.3, 2.0)
        while t < self.t[-1] + 0.5 if self.n else False:
            times.append(t)
            t += max(0.7, rng.gamma(4.0, self.blink_rate / 4.0))
        times += self.blink_extra
        out = np.zeros(self.n)
        for bt in times:
            if any(a <= bt <= b for a, b in self.no_blink):
                continue
            close, hold, opn = 0.075, 0.035, 0.15
            x = self.t - bt
            v = np.where(x < 0, 0, np.where(x < close, smoothstep(x / close),
                         np.where(x < close + hold, 1, smoothstep(1 - (x - close - hold) / opn))))
            v[(x < 0) | (x > close + hold + opn)] = 0
            depth = 1.0 if rng.random() > 0.12 else 0.6
            out = np.maximum(out, v * depth)
        return out

    # ---------------------------------------------------------------- compose
    def compose(self, idle=1.0):
        keys = {}
        emo = self._emotion_layer()
        vis, jaw = self._speech_layer()
        speaking = np.clip(sum(vis.values()) * 1.5, 0, 1)
        for k, v in emo.items():
            if k in MOUTH_KEYS:
                v = v * (1 - 0.45 * speaking)
            keys[k] = v.copy()
        for k, v in vis.items():
            keys[k] = keys.get(k, 0) + v
        keys["jawOpen"] = keys.get("jawOpen", 0) + jaw
        # idle micro-motion so faces never freeze
        s = self.seed
        for k, amp, f in (("browInnerUp", 0.05, 0.35), ("mouthSmileLeft", 0.03, 0.25), ("mouthSmileRight", 0.03, 0.27),
                          ("browOuterUpLeft", 0.025, 0.3), ("eyeSquintLeft", 0.03, 0.2), ("eyeSquintRight", 0.03, 0.22),
                          ("mouthPressLeft", 0.02, 0.4), ("mouthPressRight", 0.02, 0.42), ("noseSneerLeft", 0.015, 0.3)):
            s += 1
            keys[k] = keys.get(k, np.zeros(self.n)) + idle * amp * (0.5 + 0.5 * value_noise(self.n, self.fps, f, s))
        # speech-synced brow raises on emphasized words
        br = np.zeros(self.n)
        for w in self.speech:
            e = w.get("emph", 0.0)
            if e > 0.35:
                c = (w["start"] + w["end"]) / 2
                br = np.maximum(br, (e - 0.35) * 0.55 * np.exp(-((self.t - c) / 0.22) ** 2))
        keys["browInnerUp"] = keys.get("browInnerUp", 0) + br * 0.7
        keys["browOuterUpLeft"] = keys.get("browOuterUpLeft", 0) + br
        keys["browOuterUpRight"] = keys.get("browOuterUpRight", 0) + br * 0.9
        blink = self._blink_layer()
        for side in ("Left", "Right"):
            base = keys.get("eyeBlink" + side, np.zeros(self.n))
            keys["eyeBlink" + side] = np.clip(base + (1 - base) * blink, 0, 1)
        for k in list(keys):
            keys[k] = np.clip(keys[k], 0.0, 1.0)
        self.keys = keys
        return keys
