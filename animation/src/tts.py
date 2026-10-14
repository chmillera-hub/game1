"""Voice acting: Kokoro (timestamped ONNX) -> wav + phoneme timings -> visemes.

Runs with the system python (onnxruntime + kokoro_onnx tokenizer).
"""
import json
import os
import subprocess
import tempfile

import numpy as np
import soundfile as sf

SR = 24000
MODEL = '/opt/tools/kokoro/ts/onnx/model.onnx'
VOICES = '/opt/tools/kokoro/voices-v1.0.bin'

_sess = None
_voices = None
_tok = None


def _load():
    global _sess, _voices, _tok
    if _sess is None:
        import onnxruntime as rt
        from kokoro_onnx.tokenizer import Tokenizer
        so = rt.SessionOptions()
        so.intra_op_num_threads = 4
        _sess = rt.InferenceSession(MODEL, so)
        _voices = np.load(VOICES)
        _tok = Tokenizer()
    return _sess, _voices, _tok


def style_vec(voice_mix, n_tokens):
    _, voices, _ = _load()
    tot = sum(voice_mix.values())
    v = sum(voices[k][n_tokens] * (w / tot) for k, w in voice_mix.items())
    return v.astype(np.float32)


def synth(text, voice_mix, speed=1.0, lang='en-us'):
    """Returns audio (float32, 24k) and [(phoneme, start, end)]."""
    sess, voices, tok = _load()
    ph = tok.phonemize(text, lang)
    vocab = tok.vocab
    chars = [c for c in ph if c in vocab]
    ids = [vocab[c] for c in chars]
    if len(ids) > 500:
        raise ValueError('line too long for one pass: %d tokens' % len(ids))
    st = style_vec(voice_mix, len(ids))
    wav, dur = sess.run(None, {'input_ids': np.array([[0, *ids, 0]], dtype=np.int64),
                               'style': st, 'speed': np.array([speed], dtype=np.float32)})
    wav = wav[0].astype(np.float32)
    dur = np.asarray(dur).ravel().astype(np.float64)
    edges = np.concatenate([[0], np.cumsum(dur)])
    edges = edges * (len(wav) / edges[-1]) / SR
    timings = []
    for i, c in enumerate(chars):
        timings.append((c, float(edges[i + 1]), float(edges[i + 2])))
    return wav, timings, ph


def pitch_shift(wav, semitones, formant=True, tempo=1.0):
    if abs(semitones) < 1e-3 and abs(tempo - 1) < 1e-3:
        return wav
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, 'a.wav'), os.path.join(d, 'b.wav')
        sf.write(a, wav, SR)
        cmd = ['rubberband', '-q', '-p', str(semitones), '-t', str(1.0 / tempo), '--fine']
        if formant:
            cmd.append('-F')
        subprocess.run(cmd + [a, b], check=True, capture_output=True)
        out, _ = sf.read(b, dtype='float32')
    return out


def trim(wav, timings, thresh=0.01, pad=0.06):
    """Trim leading/trailing silence; shift timings accordingly."""
    env = np.abs(wav)
    idx = np.nonzero(env > thresh * env.max())[0]
    if len(idx) == 0:
        return wav, timings, 0.0
    s = max(0, idx[0] - int(pad * SR))
    e = min(len(wav), idx[-1] + int(pad * SR))
    off = s / SR
    tt = [(p, max(0.0, a - off), max(0.0, b - off)) for (p, a, b) in timings]
    return wav[s:e], tt, off


# ------------------------------------------------------------------ visemes
VIS = {
    'AA': dict(jaw=0.62, wide=0.15), 'EH': dict(jaw=0.42, wide=0.40), 'IY': dict(jaw=0.18, wide=0.70),
    'AO': dict(jaw=0.50, round=0.55), 'UW': dict(jaw=0.18, round=0.95), 'AH': dict(jaw=0.36, wide=0.05),
    'IH': dict(jaw=0.25, wide=0.45), 'ER': dict(jaw=0.28, round=0.35),
    'MBP': dict(press=1.0), 'FV': dict(jaw=0.06, press=0.45, lip_raise=0.2), 'TH': dict(jaw=0.16, wide=0.20),
    'T': dict(jaw=0.16, wide=0.30), 'SH': dict(jaw=0.14, round=0.55), 'K': dict(jaw=0.28, wide=0.10),
    'W': dict(jaw=0.08, round=1.0), 'R': dict(jaw=0.20, round=0.40), 'Y': dict(jaw=0.14, wide=0.50),
    'REST': dict(),
}
CH = {}
for c in 'aɑæʌɐ':
    CH[c] = 'AA'
for c in 'ɛe':
    CH[c] = 'EH'
for c in 'iɪᵻ':
    CH[c] = 'IY' if c == 'i' else 'IH'
for c in 'ɔoɒ':
    CH[c] = 'AO'
for c in 'uʊ':
    CH[c] = 'UW'
for c in 'əɜ':
    CH[c] = 'AH'
CH['ɚ'] = 'ER'
for c in 'pbm':
    CH[c] = 'MBP'
for c in 'fv':
    CH[c] = 'FV'
for c in 'θð':
    CH[c] = 'TH'
for c in 'tdnlszɾ':
    CH[c] = 'T'
for c in 'ʃʒʧʤ':
    CH[c] = 'SH'
for c in 'kgŋhx':
    CH[c] = 'K'
CH['w'] = 'W'
CH['ɹ'] = 'R'
CH['r'] = 'R'
CH['j'] = 'Y'
CHANNELS = ('jaw', 'wide', 'round', 'press', 'lip_raise')


def visemes(timings, wav, fps=24, n_frames=None):
    """Per-frame mouth channels with coarticulation and loudness scaling."""
    dur = len(wav) / SR
    n = n_frames or int(np.ceil(dur * fps)) + 1
    t = np.arange(n) / fps
    # loudness envelope (per frame, 30 ms window)
    win = int(0.03 * SR)
    # the last frame can fall past the end of the audio: an empty window is silence, not NaN
    rms = np.array([np.sqrt(np.mean(seg ** 2) + 1e-12) if len(seg := wav[max(0, int(x * SR) - win):int(x * SR) + win]) else 0.0
                    for x in t])
    rms = rms / (np.percentile(rms[rms > 1e-4], 90) + 1e-9) if np.any(rms > 1e-4) else rms
    loud = np.clip(rms, 0, 1.3)
    out = {c: np.zeros(n) for c in CHANNELS}
    wsum = np.zeros(n) + 1e-6
    stress = False
    press_max = np.zeros(n)
    for (p, a, b) in timings:
        if p in 'ˈˌ':
            stress = True
            continue
        v = CH.get(p)
        if v is None:
            continue
        tgt = VIS[v]
        mid = 0.5 * (a + b)
        width = max(0.045, (b - a) * 0.75)
        w = np.exp(-0.5 * ((t - mid) / width) ** 2)
        amp = 1.25 if (stress and v in ('AA', 'EH', 'IY', 'AO', 'UW', 'AH', 'IH', 'ER')) else 1.0
        if v in ('AA', 'EH', 'IY', 'AO', 'UW', 'AH', 'IH', 'ER'):
            stress = False
        for c in CHANNELS:
            out[c] += w * tgt.get(c, 0.0) * (amp if c == 'jaw' else 1.0)
        wsum += w
        if v == 'MBP':
            inside = (t >= a - 0.015) & (t <= b + 0.01)
            press_max[inside] = 1.0
    for c in CHANNELS:
        out[c] = out[c] / np.maximum(wsum, 0.6)
    # loudness: quiet audio -> smaller mouth; silence -> closed
    gate = np.clip(loud * 1.6, 0, 1) ** 0.7
    out['jaw'] *= 0.55 + 0.6 * np.clip(loud, 0, 1)
    for c in ('jaw', 'wide', 'round'):
        out[c] *= gate
    out['press'] = np.maximum(out['press'] * gate, press_max)
    out['jaw'] *= (1 - 0.85 * press_max)
    # light smoothing (2-frame)
    k = np.array([0.25, 0.5, 0.25])
    for c in CHANNELS:
        out[c] = np.convolve(np.pad(out[c], 1, mode='edge'), k, mode='valid')
    return {c: np.nan_to_num(out[c]).tolist() for c in CHANNELS}


def word_spans(tim):
    """[(start, end)] per word from phoneme timings (spaces/punctuation separate words)."""
    words, cur = [], None
    for (p, a, b) in tim:
        if p == ' ' or p in '.,!?;:—-':
            if cur:
                words.append(cur)
                cur = None
            continue
        if p in 'ˈˌː':
            if cur:
                cur = (cur[0], b)
            continue
        cur = (a if cur is None else cur[0], b)
    if cur:
        words.append(cur)
    return words


def cut_words(wav, tim, spec):
    """spec 'first:N' keeps the first N words, 'last:N' keeps the last N."""
    if not spec:
        return wav, tim
    kind, n = spec.split(':')
    n = int(n)
    ws = word_spans(tim)
    if kind == 'first':
        end = ws[min(n, len(ws)) - 1][1] + 0.045
        e = int(end * SR)
        out = wav[:e].copy()
        fade = min(int(0.03 * SR), len(out))
        out[-fade:] *= np.linspace(1, 0, fade)
        return out, [(p, a, b) for (p, a, b) in tim if a < end]
    st = max(0.0, ws[-n][0] - 0.03)
    s = int(st * SR)
    out = wav[s:].copy()
    fade = min(int(0.015 * SR), len(out))
    out[:fade] *= np.linspace(0, 1, fade)
    return out, [(p, a - st, b - st) for (p, a, b) in tim if b > st]


def high_shelf(wav, gain_db=-4.0, f0=6000.0):
    from scipy.signal import lfilter
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / 2 * np.sqrt(2)
    cw = np.cos(w0)
    b0 = A * ((A + 1) + (A - 1) * cw + 2 * np.sqrt(A) * alpha)
    b1 = -2 * A * ((A - 1) + (A + 1) * cw)
    b2 = A * ((A + 1) + (A - 1) * cw - 2 * np.sqrt(A) * alpha)
    a0 = (A + 1) - (A - 1) * cw + 2 * np.sqrt(A) * alpha
    a1 = 2 * ((A - 1) - (A + 1) * cw)
    a2 = (A + 1) - (A - 1) * cw - 2 * np.sqrt(A) * alpha
    return lfilter([b0 / a0, b1 / a0, b2 / a0], [1, a1 / a0, a2 / a0], wav).astype(np.float32)


def make_line(text, voice, out_wav, fps=24, trim_spec=None, hushed=False):
    """voice: dict(mix={...}, speed=, pitch=, formant=True, pitch2=, lang=, gain=)."""
    wav, tim, ph = synth(text, voice['mix'], speed=voice.get('speed', 1.0), lang=voice.get('lang', 'en-us'))
    wav, tim = cut_words(wav, tim, trim_spec)
    if voice.get('pitch', 0) or voice.get('tempo', 1.0) != 1.0:
        tempo = voice.get('tempo', 1.0)
        wav = pitch_shift(wav, voice.get('pitch', 0), voice.get('formant', True), tempo)
        tim = [(p, a / tempo, b / tempo) for (p, a, b) in tim]
    if voice.get('pitch2'):
        wav = pitch_shift(wav, voice['pitch2'], True)
    if hushed:
        wav = high_shelf(wav, -4.0, 6000.0)
    wav, tim, off = trim(wav, tim)
    peak = np.max(np.abs(wav)) + 1e-9
    wav = wav / peak * 0.9 * voice.get('gain', 1.0)
    sf.write(out_wav, wav, SR)
    vis = visemes(tim, wav, fps=fps)
    return dict(text=text, phonemes=ph, dur=len(wav) / SR, timings=tim, visemes=vis)
