"""Kokoro TTS wrapper that returns audio plus per-phoneme and per-word timing.

Uses the timestamped ONNX export (outputs `waveform` and `durations`) so the
renderer can drive lip-sync from real phoneme timing and the score can land
notes on specific words.
"""
import os
import re

import numpy as np
import onnxruntime as rt
from kokoro_onnx.tokenizer import Tokenizer

SR = 24000
MODEL_DIR = os.environ.get("KOKORO_DIR", "/tmp/claude-0/models")


class TTS:
    def __init__(self, model_dir=MODEL_DIR):
        opts = rt.SessionOptions()
        opts.intra_op_num_threads = 4
        self.sess = rt.InferenceSession(os.path.join(model_dir, "model_ts.onnx"), opts)
        self.tok = Tokenizer()
        self.model_dir = model_dir
        self._voices = {}

    def voice(self, spec):
        """spec: 'af_heart' or 'af_nicole:0.6,af_bella:0.4' (weighted blend)."""
        if spec in self._voices:
            return self._voices[spec]
        parts = []
        for item in spec.split(","):
            name, _, w = item.partition(":")
            arr = np.fromfile(os.path.join(self.model_dir, name.strip() + ".bin"), dtype=np.float32)
            parts.append((arr.reshape(-1, 1, 256), float(w or 1.0)))
        total = sum(w for _, w in parts)
        v = sum(a * (w / total) for a, w in parts).astype(np.float32)
        self._voices[spec] = v
        return v

    def _word_len(self, w):
        p = self.tok.phonemize(w)
        return max(1, len([c for c in p if c not in STRESS and c not in PUNCT and c != " "]))

    def synth(self, text, voice, speed=1.0, lang="en-us"):
        phon = self.tok.phonemize(text, lang)
        phon = " ".join(phon.split())
        known = self.tok.known(phon)
        ids = self.tok.tokenize(known)
        v = self.voice(voice)
        style = v[min(len(ids), len(v)) - 1]
        out = self.sess.run(None, {
            "input_ids": np.array([[0, *ids, 0]], dtype=np.int64),
            "style": style.astype(np.float32),
            "speed": np.array([speed], dtype=np.float32),
        })
        audio = np.asarray(out[0]).ravel().astype(np.float32)
        dur = np.asarray(out[1]).ravel().astype(np.float64)
        spf = len(audio) / dur.sum()  # samples per duration frame
        edges = np.concatenate([[0], np.cumsum(dur)]) * spf
        # token i (0-based in `known`) spans edges[i+1]..edges[i+2] (skip leading pad)
        phones = []
        for i, ch in enumerate(known):
            phones.append([ch, edges[i + 1] / SR, edges[i + 2] / SR])
        audio, head = trim(audio)
        shift = head / SR
        for p in phones:
            p[1] = max(0.0, p[1] - shift)
            p[2] = max(0.0, p[2] - shift)
        dur_s = len(audio) / SR
        for p in phones:
            p[1] = min(p[1], dur_s)
            p[2] = min(p[2], dur_s)
        words = words_from_phones(text, phones, self._word_len)
        return audio, phones, words, known


def trim(audio, thresh=0.012, pad=0.03):
    env = np.abs(audio)
    idx = np.where(env > thresh)[0]
    if len(idx) == 0:
        return audio, 0
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(audio), idx[-1] + int(pad * 1.5 * SR))
    return audio[a:b], a


PUNCT = set(".,!?;:—…\"“”()-")


STRESS = set("ˈˌː")


def words_from_phones(text, phones, word_len=None):
    """Group phonemes into words at spaces, then align them to the text's words.

    espeak sometimes fuses short words ("out of" -> one group), so groups and
    words are matched by a small DP over phoneme lengths; a fused group is split
    between its words in proportion to their own phoneme lengths."""
    groups, cur = [], []
    for ch, a, b in phones:
        if ch == " ":
            if cur:
                groups.append(cur)
            cur = []
        elif ch in PUNCT:
            continue
        else:
            cur.append((ch, a, b))
    if cur:
        groups.append(cur)
    tw = re.findall(r"[A-Za-z0-9'’]+(?:[-–][A-Za-z0-9'’]+)*", text)
    if not groups or not tw:
        return []
    if len(groups) == len(tw) or word_len is None:
        pairs = [([w], [g]) for w, g in zip(tw, groups)] if len(groups) == len(tw) else None
    else:
        pairs = None
    if pairs is None:
        wl = [word_len(w) for w in tw]
        gl = [len([p for p in g if p[0] not in STRESS]) for g in groups]
        n, m = len(tw), len(groups)
        INF = 1e9
        cost = [[INF] * (m + 1) for _ in range(n + 1)]
        back = [[None] * (m + 1) for _ in range(n + 1)]
        cost[0][0] = 0
        for i in range(n + 1):
            for j in range(m + 1):
                if cost[i][j] >= INF:
                    continue
                for dw, dg in ((1, 1), (2, 1), (3, 1), (1, 2)):
                    if i + dw > n or j + dg > m:
                        continue
                    a = sum(wl[i:i + dw]); b = sum(gl[j:j + dg])
                    c = cost[i][j] + abs(a - b) / max(a, b) + 0.15 * (dw + dg - 2)
                    if c < cost[i + dw][j + dg]:
                        cost[i + dw][j + dg] = c
                        back[i + dw][j + dg] = (i, j)
        if cost[n][m] >= INF:
            return []
        pairs, i, j = [], n, m
        while (i, j) != (0, 0):
            pi, pj = back[i][j]
            pairs.append((tw[pi:i], groups[pj:j], wl[pi:i]))
            i, j = pi, pj
        pairs.reverse()
    out = []
    for item in pairs:
        ws, gs = item[0], item[1]
        t0, t1 = gs[0][0][1], gs[-1][-1][2]
        if len(ws) == 1:
            out.append({"w": ws[0], "t0": round(t0, 3), "t1": round(t1, 3)})
        else:
            lens = item[2]
            tot = float(sum(lens)); acc = 0
            for w, L in zip(ws, lens):
                a = t0 + (t1 - t0) * acc / tot
                acc += L
                b = t0 + (t1 - t0) * acc / tot
                out.append({"w": w, "t0": round(a, 3), "t1": round(b, 3)})
    return out
