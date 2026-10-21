"""Make a speaking TTS voice sing.

Kokoro speaks a lyric line naturally; we take its per-phoneme durations,
split it into syllables, then rebuild the voice with the WORLD vocoder so
each vowel is stretched over its note and the pitch follows the melody
(with glides, a little scoop and vibrato). Consonants keep their natural
length and land just before the beat, the way singers phrase.
"""
import math
import os
import sys
import warnings

import numpy as np
import pyworld as pw

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from synth import hz  # noqa: E402

SR_TTS = 24000
FP = 5.0                       # WORLD frame period (ms)
VOWELS = set("aeiouyæɑɐɒɔəɘɛɜɪʊʌᵻᵊAIOWYQɚ")
SKIP = set("ˈˌːˑ")             # stress / length marks: no duration of their own
VOICED_CONS = set("bdgvzðʒmnŋlɹrjwʤ")
UNVOICED = set("ptkfθsʃhʧx")

_PIPE = None


def pipeline():
    global _PIPE
    if _PIPE is None:
        from kokoro import KPipeline
        _PIPE = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    return _PIPE


def speak(text, voice, speed=1.0):
    """-> audio (24k float64), [(word, phonemes, t0, t1, [(ph, s0, s1)...])]"""
    audio_parts, words, off = [], [], 0.0
    for r in pipeline()(text, voice=voice, speed=speed):
        a = r.output.audio.numpy().astype(np.float64)
        pd = r.output.pred_dur.tolist()
        # phoneme char k spans pd[k+1] frames of 600 samples (BOS is pd[0])
        edges = np.cumsum([0] + pd) * 600 / SR_TTS
        pos = 0
        for tk in r.tokens:
            ph = tk.phonemes or ""
            spans = []
            for j, ch in enumerate(ph):
                k = pos + j
                spans.append((ch, off + edges[k + 1], off + edges[k + 2]))
            if any(c.isalpha() or c in VOWELS for c in ph) and any(ch.isalnum() for ch in tk.text):
                words.append((tk.text, ph, spans[0][1] if spans else off, spans[-1][2] if spans else off, spans))
            pos += len(ph) + (1 if tk.whitespace else 0)
        audio_parts.append(a)
        off += len(a) / SR_TTS
    return np.concatenate(audio_parts), words


def syllables_of(spans, n_target):
    """Split a word's phoneme spans into n_target (onset, nucleus, coda) groups (lists of spans)."""
    sp = [s for s in spans if s[0] not in SKIP]
    nuclei = []
    i = 0
    while i < len(sp):
        if sp[i][0] in VOWELS:
            j = i
            while j + 1 < len(sp) and sp[j + 1][0] in VOWELS:
                j += 1
            nuclei.append((i, j))
            i = j + 1
        else:
            i += 1
    if not nuclei:  # no vowel at all: treat whole word as one nucleus
        nuclei = [(0, len(sp) - 1)]
    # merge extra nuclei into neighbours / split if too few
    while len(nuclei) > n_target:
        a, b = nuclei[-2], nuclei[-1]
        nuclei[-2:] = [(a[0], b[1])]
    groups = []
    for k, (a, b) in enumerate(nuclei):
        prev_end = nuclei[k - 1][1] + 1 if k > 0 else 0
        next_start = nuclei[k + 1][0] if k + 1 < len(nuclei) else len(sp)
        cons_before = list(range(prev_end, a))
        cons_after = list(range(b + 1, next_start))
        # intervocalic cluster split: 1 consonant -> next onset; 2+ -> first to coda
        if k > 0 and len(cons_before) >= 2:
            groups[-1][2].append(sp[cons_before[0]])
            cons_before = cons_before[1:]
        onset = [sp[x] for x in cons_before]
        nucleus = [sp[x] for x in range(a, b + 1)]
        coda = [sp[x] for x in cons_after] if k + 1 == len(nuclei) else []
        groups.append([onset, nucleus, coda])
    # too few nuclei: duplicate the last nucleus (repeat the vowel on extra notes)
    while len(groups) < n_target:
        on, nu, co = groups[-1]
        t0, t1 = nu[0][1], nu[-1][2]
        mid = (t0 + t1) / 2
        groups[-1] = [on, [(nu[0][0], t0, mid)], []]
        groups.append([[], [(nu[-1][0], mid, t1)], co])
    return groups


def span_t(group):
    if not group:
        return None
    return group[0][1], group[-1][2]


class Note:
    __slots__ = ("syl", "pitch", "start", "dur", "word", "accent", "glide_from", "fall")

    def __init__(self, syl, pitch, start, dur, word, accent=False, fall=False):
        self.syl, self.pitch, self.start, self.dur, self.word = syl, pitch, start, dur, word
        self.accent, self.fall, self.glide_from = accent, fall, None


def sing_phrase(text_words, notes, voice, speed=1.0, vib_depth=0.32, vib_rate=5.6, scoop=0.35,
                formant_shift=1.0, breath=0.0, legato=0.92, seed=0):
    """text_words: list of (word, n_syllables). notes: list of Note (start/dur in seconds, phrase-relative,
    one per syllable in order; pitch None = rest). Returns (audio 24k, timings[(word, t0, t1)])."""
    text = " ".join(w for w, _ in text_words)
    audio, words = speak(text, voice, speed)
    # align TTS words with lyric words in order (letters only)
    def norm(s):
        return "".join(c for c in s.lower() if c.isalnum())
    sung = [n for n in notes if n.pitch is not None]
    groups = []
    wi = 0
    for lw, nsyl in text_words:
        while wi < len(words) and norm(words[wi][0]) != norm(lw):
            wi += 1
        if wi >= len(words):
            raise ValueError(f"word {lw!r} not found in TTS output {[w[0] for w in words]}")
        gs = syllables_of(words[wi][4], nsyl)
        groups.extend(gs)
        wi += 1
    if len(groups) != len(sung):
        raise ValueError(f"{len(groups)} syllables vs {len(sung)} notes for {text!r}")
    # ---- WORLD analysis
    x = audio
    f0, t = pw.dio(x, SR_TTS, frame_period=FP, f0_floor=60, f0_ceil=600)
    f0 = pw.stonemask(x, f0, t, SR_TTS)
    sp = pw.cheaptrick(x, f0, t, SR_TTS)
    ap = pw.d4c(x, f0, t, SR_TTS)
    nfr = len(f0)
    silence_idx = int(np.argmin(np.log(sp + 1e-12).mean(axis=1)))
    # ---- target timeline
    end_t = max(n.start + n.dur for n in notes) + 0.25
    first_onset = 0.0
    tgt_n = int((end_t + 0.6) / (FP / 1000)) + 1
    src_map = np.full(tgt_n, -1.0)          # fractional source frame per target frame (-1 = silence)
    f0_t = np.zeros(tgt_n)
    voiced_force = np.zeros(tgt_n, bool)
    timings = []
    splices = []
    pre = 0.30                               # phrase-relative output starts 0.3s early for leading consonants
    tf = lambda sec: int(round((sec + pre) / (FP / 1000)))
    prev_pitch = None
    for idx, (n, (onset, nucleus, coda)) in enumerate(zip(sung, groups)):
        nxt = sung[idx + 1] if idx + 1 < len(sung) else None
        on_s = span_t(onset)
        nu_s = span_t(nucleus)
        co_s = span_t(coda)
        on_d = min(on_s[1] - on_s[0], 0.13) if on_s else 0.0
        co_d = min(co_s[1] - co_s[0], 0.14) if co_s else 0.0
        note_end = n.start + n.dur
        if nxt is not None and abs(nxt.start - note_end) < 1e-3:
            nxt_on = span_t(groups[idx + 1][0])
            nxt_on_d = min(nxt_on[1] - nxt_on[0], 0.13) if nxt_on else 0.0
            v_end = note_end - nxt_on_d - co_d
        else:
            v_end = n.start + n.dur * legato - co_d
        v_start = n.start
        if v_end - v_start < 0.05:  # very short note: squeeze consonants
            squeeze = max(0.2, (n.dur * 0.8) / max(1e-3, on_d + co_d + 0.05))
            on_d *= min(1.0, squeeze)
            co_d *= min(1.0, squeeze)
            v_end = max(v_start + 0.04, n.start + n.dur * legato - co_d)

        def place(seg, a, b):
            if seg is None or b <= a:
                return
            fa, fb = tf(a), tf(b)
            s0, s1 = seg[0] / (FP / 1000), seg[1] / (FP / 1000)
            for k in range(max(0, fa), min(tgt_n, fb)):
                u = (k - fa) / max(1, fb - fa)
                src_map[k] = s0 + (s1 - s0) * u

        def place_cons(group, a, b, keep_end):
            """Place consonants one by one; unvoiced ones are spliced from the original audio."""
            if not group or b <= a:
                return
            tot = sum(p[2] - p[1] for p in group)
            scale = (b - a) / max(1e-6, tot)
            cur = a
            for (ch, p0, p1) in group:
                d = (p1 - p0) * scale
                place((p0, p1), cur, cur + d)
                if ch in UNVOICED:
                    src_len = p1 - p0
                    if keep_end:
                        s_from = p1 - min(src_len, d)
                    else:
                        s_from = p0
                    splices.append((cur, cur + d, s_from))
                cur += d
        place_cons(onset, v_start - on_d, v_start, keep_end=True)
        if nu_s:
            # stretch the vowel using its middle 70% (stable part), keeping its edges
            a, b = nu_s
            edge = (b - a) * 0.15
            fa, fb = tf(v_start), tf(v_end)
            s_edge0, s_edge1 = (a + edge) / (FP / 1000), (b - edge) / (FP / 1000)
            s_a, s_b = a / (FP / 1000), b / (FP / 1000)
            nfrm = max(1, fb - fa)
            for k in range(max(0, fa), min(tgt_n, fb)):
                u = (k - fa) / nfrm
                if u < 0.08:
                    src_map[k] = s_a + (s_edge0 - s_a) * (u / 0.08)
                elif u > 0.92:
                    src_map[k] = s_edge1 + (s_b - s_edge1) * ((u - 0.92) / 0.08)
                else:  # slow drift through the vowel core with a gentle back-and-forth
                    w = (u - 0.08) / 0.84
                    src_map[k] = s_edge0 + (s_edge1 - s_edge0) * (0.5 - 0.5 * math.cos(math.pi * w))
                voiced_force[k] = True
        place_cons(coda, v_end, v_end + co_d, keep_end=False)
        # pitch for this syllable
        p = math.log2(hz(n.pitch))
        a_t, b_t = v_start - on_d, v_end + co_d
        fa, fb = max(0, tf(a_t)), min(tgt_n, tf(b_t))
        for k in range(fa, fb):
            tt = (k * FP / 1000 - pre) - v_start   # time since vowel start
            pk = p
            if prev_pitch is not None and tt < 0.07:
                g = max(0.0, tt) / 0.07
                pk = prev_pitch + (p - prev_pitch) * (0.5 - 0.5 * math.cos(math.pi * g))
            elif n.accent and tt < 0.09:
                pk = p - scoop / 12 * (1 - max(0.0, tt) / 0.09)
            dur_v = v_end - v_start
            if dur_v > 0.32 and tt > 0.2:
                ramp = min(1.0, (tt - 0.2) / 0.25)
                pk += vib_depth / 12 * ramp * math.sin(2 * math.pi * vib_rate * (tt - 0.2))
            if n.fall and tt > dur_v - 0.18:
                pk -= (tt - (dur_v - 0.18)) / 0.18 * 3 / 12
            f0_t[k] = 2 ** pk
        prev_pitch = p
        timings.append((n.word, n.start - on_d, n.start + n.dur))
    # ---- build target WORLD params
    sp_t = np.zeros((tgt_n, sp.shape[1]))
    ap_t = np.ones((tgt_n, ap.shape[1]))
    f0_out = np.zeros(tgt_n)
    logsp = np.log(sp + 1e-16)
    for k in range(tgt_n):
        s = src_map[k]
        if s < 0:
            sp_t[k] = sp[silence_idx] * 0.05
            continue
        i0 = int(math.floor(min(max(s, 0), nfr - 1)))
        i1 = min(i0 + 1, nfr - 1)
        w = s - i0
        sp_t[k] = np.exp(logsp[i0] * (1 - w) + logsp[i1] * w) * formant_shift_gain(formant_shift)
        ap_t[k] = ap[i0] * (1 - w) + ap[i1] * w
        src_voiced = f0[i0] > 0 or f0[i1] > 0
        if (src_voiced or voiced_force[k]) and f0_t[k] > 0:
            f0_out[k] = f0_t[k]
            if voiced_force[k] and not src_voiced:
                ap_t[k] = np.minimum(ap_t[k], 0.4)
    if breath > 0:
        ap_t = np.clip(ap_t + breath, 0, 1)
    if formant_shift != 1.0:
        sp_t = shift_formants(sp_t, formant_shift)
    y = pw.synthesize(f0_out, np.ascontiguousarray(sp_t), np.ascontiguousarray(ap_t), SR_TTS, FP)
    # splice crisp unvoiced consonants (bursts, hiss) from the original speech
    xf = int(0.004 * SR_TTS)
    for (a, b, s_from) in splices:
        i0 = int((a + pre) * SR_TTS)
        n = int((b - a) * SR_TTS)
        j0 = int(s_from * SR_TTS)
        if n <= 2 * xf or i0 < 0 or i0 + n > len(y) or j0 + n > len(audio):
            continue
        seg = audio[j0:j0 + n].astype(np.float64)
        w = np.ones(n)
        w[:xf] = np.linspace(0, 1, xf)
        w[-xf:] = np.linspace(1, 0, xf)
        y[i0:i0 + n] = y[i0:i0 + n] * (1 - w) + seg * w
    # timings are phrase-relative to the note grid; output audio starts `pre` seconds before t=0
    return y.astype(np.float32), timings, pre


def formant_shift_gain(_):
    return 1.0


def shift_formants(sp, k):
    """Scale the spectral envelope along frequency (k>1: smaller/brighter 'skull' voice)."""
    n = sp.shape[1]
    src = np.clip(np.arange(n) / k, 0, n - 1)
    i0 = np.floor(src).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    w = src - i0
    return sp[:, i0] * (1 - w) + sp[:, i1] * w
