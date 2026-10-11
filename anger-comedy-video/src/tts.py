"""Voice acting: Kokoro TTS per line, with pauses, character FX and lip-sync envelopes."""
import hashlib
import json
import os
import re
import subprocess
import numpy as np
import soundfile as sf
from common import BUILD, MODELS, FPS, SR

TTS_DIR = os.path.join(BUILD, 'tts')
os.makedirs(TTS_DIR, exist_ok=True)

# speaker -> (voice spec, lang, base speed, pitch semitones)
VOICES = {
    'me':       ('af_heart', 'en-us', 0.92, 0.0),
    'anger':    ({'am_fenrir': 0.6, 'am_onyx': 0.4}, 'en-us', 0.94, -1.5),
    'doubt':    ('bf_emma', 'en-gb', 0.94, 0.0),
    'boredom':  ('bm_lewis', 'en-gb', 0.86, -1.0),
    'stranger': ('am_michael', 'en-us', 0.95, 0.0),
    'gemini':   ('am_puck', 'en-us', 1.04, 1.0),
}

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODELS, 'kokoro-v1.0.onnx'), os.path.join(MODELS, 'voices-v1.0.bin'))
    return _kokoro


def _voice(spec):
    if isinstance(spec, str):
        return spec
    k = kokoro()
    v = None
    for name, w in spec.items():
        s = k.get_voice_style(name) * w
        v = s if v is None else v + s
    return v


def _trim(a, thr=0.012, pad=0.03, sr=24000):
    idx = np.where(np.abs(a) > thr)[0]
    if len(idx) == 0:
        return a[:0]
    s = max(0, idx[0] - int(pad * sr))
    e = min(len(a), idx[-1] + int(pad * 2 * sr))
    return a[s:e]


def _resample(a, sr_in, sr_out):
    if sr_in == sr_out:
        return a
    n = int(round(len(a) * sr_out / sr_in))
    x_old = np.linspace(0, 1, len(a), endpoint=False)
    x_new = np.linspace(0, 1, n, endpoint=False)
    return np.interp(x_new, x_old, a).astype(np.float32)


def _ffmpeg_filter(a, sr, filt):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', 'pipe:0',
                        '-af', filt, '-f', 'f32le', '-ar', str(sr), '-ac', '1', 'pipe:1'],
                       input=a.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def fx_chain(a, sr, fx, pitch):
    """a: mono float32 at sr (24k from kokoro)."""
    filt = []
    if pitch:
        filt.append(f"rubberband=pitch={2 ** (pitch / 12):.5f}:formant=preserved")
    if 'shout' in fx:
        filt.append("rubberband=pitch=1.06:formant=preserved")
    if filt:
        a = _ffmpeg_filter(a, sr, ','.join(filt))
    if 'shout' in fx:
        a = a / (np.max(np.abs(a)) + 1e-6)
        a = np.tanh(a * 1.8) / np.tanh(1.8)
        a = _ffmpeg_filter(a, sr, "equalizer=f=2500:t=q:w=1.2:g=5,equalizer=f=200:t=q:w=1:g=-2")
    if 'whisper' in fx:
        a = _ffmpeg_filter(a, sr, "highpass=f=250,equalizer=f=4000:t=q:w=1:g=4")
    if 'robot' in fx:
        tt = np.arange(len(a)) / sr
        ring = 0.72 + 0.28 * np.sin(2 * np.pi * 55 * tt)
        a = a * ring
        d = int(0.0045 * sr)
        b = a.copy()
        b[d:] += 0.35 * a[:-d]
        a = _ffmpeg_filter(b, sr, "highpass=f=260,lowpass=f=6500,equalizer=f=1800:t=q:w=1:g=4")
    if 'muffled' in fx:
        a = _ffmpeg_filter(a, sr, "lowpass=f=650,lowpass=f=650")
    return a.astype(np.float32)


def envelope(a, sr, fps=FPS):
    hop = sr // fps
    n = int(np.ceil(len(a) / hop))
    env = np.zeros(n, np.float32)
    rnd = np.zeros(n, np.float32)
    for i in range(n):
        seg = a[i * hop:(i + 1) * hop]
        if len(seg) < 16:
            continue
        rms = np.sqrt(np.mean(seg ** 2)) + 1e-9
        db = 20 * np.log10(rms)
        v = (db + 42) / 28.0
        env[i] = max(0.0, min(1.0, v))
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / sr)
        cen = (spec * freqs).sum() / (spec.sum() + 1e-9)
        rnd[i] = max(0.0, min(1.0, (1400 - cen) / 900)) * env[i]
    # attack/release smoothing + a little sparkle so the mouth doesn't hold still
    out = np.zeros_like(env)
    y = 0.0
    for i in range(n):
        tgt = env[i]
        y = y + (tgt - y) * (0.75 if tgt > y else 0.45)
        out[i] = y
    for i in range(1, n - 1):
        if out[i] > 0.25 and i % 3 == 0:
            out[i] *= 0.82
    return out, rnd


PAUSE_SCALE = 0.8
PAUSE_RE = re.compile(r'\[(\d+(?:\.\d+)?|BLEEP:\d+(?:\.\d+)?)\]')


def parse_text(text):
    """'Hello. [0.6] World.' -> [('t','Hello.'), ('p',0.6), ('t','World.')]"""
    parts = []
    pos = 0
    for m in PAUSE_RE.finditer(text):
        s = text[pos:m.start()].strip()
        if s:
            parts.append(('t', s))
        tok = m.group(1)
        if tok.startswith('BLEEP'):
            parts.append(('b', float(tok.split(':')[1])))
        else:
            parts.append(('p', float(tok) * PAUSE_SCALE))
        pos = m.end()
    s = text[pos:].strip()
    if s:
        parts.append(('t', s))
    return parts


def caption_text(text):
    t = PAUSE_RE.sub(lambda m: ' #@%&! ' if m.group(1).startswith('BLEEP') else ' ', text)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.replace(' ,', ',').replace(' ?', '?').replace(' !', '!')
    return t


def synth(speaker, text, fx=(), speed=None, pitch=None, gain=1.0):
    """Returns dict(audio=float32 @SR, env, round, dur)."""
    vspec, lang, vspeed, vpitch = VOICES[speaker]
    speed = speed if speed is not None else vspeed
    pitch = vpitch if pitch is None else pitch
    key = json.dumps([speaker, str(vspec), text, list(fx), speed, pitch, gain, 'v5'])
    h = hashlib.sha1(key.encode()).hexdigest()[:16]
    wav = os.path.join(TTS_DIR, f'{speaker}_{h}.wav')
    if not os.path.exists(wav):
        k = kokoro()
        voice = _voice(vspec)
        sr0 = 24000
        chunks = []
        frags = []
        pos = 0
        for kind, val in parse_text(text):
            if kind == 't':
                a, sr0 = k.create(val, voice=voice, speed=speed, lang=lang)
                a = _trim(np.asarray(a, np.float32), sr=sr0)
                a = fx_chain(a, sr0, fx, pitch)
                frags.append([pos / sr0, (pos + len(a)) / sr0, val])
                chunks.append(a)
                pos += len(a)
                continue
            elif kind == 'p':
                chunks.append(np.zeros(int(val * sr0), np.float32))
                pos += int(val * sr0)
            else:
                n = int(val * sr0)
                tt = np.arange(n) / sr0
                bl = 0.32 * np.sin(2 * np.pi * 1000 * tt)
                fade = np.minimum(1, np.minimum(tt, tt[::-1]) / 0.01)
                chunks.append((bl * fade).astype(np.float32))
                frags.append([pos / sr0, (pos + n) / sr0, '#@%&!'])
                pos += n
        a = np.concatenate(chunks) if chunks else np.zeros(1000, np.float32)
        peak = np.max(np.abs(a)) + 1e-9
        target = 0.89 if 'shout' in fx else (0.5 if 'whisper' in fx else 0.75)
        a = a / peak * target * gain
        a = _resample(a, sr0, SR)
        sf.write(wav, a, SR, subtype='FLOAT')
        with open(wav + '.json', 'w') as f:
            json.dump(frags, f)
    a, _ = sf.read(wav, dtype='float32')
    with open(wav + '.json') as f:
        frags = json.load(f)
    env, rnd = envelope(a, SR)
    # bleeps keep the mouth flapping (it's funnier)
    return dict(audio=a, env=env, round=rnd, dur=len(a) / SR, wav=wav, frags=frags)
