"""Voices for Fine Print.

    python3 voice.py build/events.json build/

Speaks the film's cue sheet with Kokoro TTS into one stem, voices.wav:
the narrator; "you", a different person each time you say no; and the
commands, shouted through a hard, narrow band. Every line is placed at the
time the film gives it, and checked against the length the film budgeted.
Model files are looked for in $KOKORO_DIR (default: build/kokoro).
"""
import json
import os
import sys
import wave

import numpy as np
from kokoro_onnx import Kokoro

SR = 48000
events_path, out_dir = sys.argv[1], sys.argv[2]
data = json.load(open(events_path))
T, cues = data['T'], data['cues']
N = int((T['END'] + 0.5) * SR)
model_dir = os.environ.get('KOKORO_DIR', os.path.join(out_dir, 'kokoro'))
tts = Kokoro(os.path.join(model_dir, 'kokoro-v1.0.onnx'), os.path.join(model_dir, 'voices-v1.0.bin'))

NARRATOR, NARRATOR_SPEED = 'af_bella', 0.95


def speak(text, voice, speed):
    """TTS at 48 kHz, with the silence trimmed off both ends."""
    a, sr = tts.create(text, voice=voice, speed=speed, lang='en-us')
    a = np.asarray(a, dtype=np.float64)
    X = np.fft.rfft(a)
    m = len(a) * SR // sr
    a = np.fft.irfft(np.concatenate([X, np.zeros(m // 2 + 1 - len(X))]), m) * (SR / sr)
    loud = np.flatnonzero(np.abs(a) > 0.01 * np.max(np.abs(a)))
    pad = int(0.03 * SR)
    return a[max(0, loud[0] - pad):loud[-1] + pad] if len(loud) else a


def shape(x, lo=None, hi=None, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR) + 1e-9
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / f) ** order)
    if hi:
        m *= 1 / (1 + (f / hi) ** order)
    return np.fft.irfft(X * m, len(x))


def place(stem, sig, t, gain=1.0, pan=0.5):
    i0 = int(round(t * SR))
    n = min(len(sig), N - i0)
    if n > 0:
        stem[0, i0:i0 + n] += sig[:n] * gain * np.cos(pan * np.pi / 2) * np.sqrt(2)
        stem[1, i0:i0 + n] += sig[:n] * gain * np.sin(pan * np.pi / 2) * np.sqrt(2)


stem = np.zeros((2, N))
report = []
for c in sorted(cues['voice'], key=lambda c: c['t0']):
    if c['who'] == 'narrator':
        sig, gain, pan = shape(speak(c['text'], NARRATOR, NARRATOR_SPEED), lo=70), 1.0, 0.5
    elif c['who'] == 'you':
        sig, gain, pan = shape(speak(c['text'], c['voice'], 1.0), lo=90), 0.9, 0.44
    else:
        # a command: loud, close to clipping, and narrow, like it came through a speaker
        raw = speak(c['text'], c['voice'], 1.08)
        raw = shape(raw, lo=320, hi=3600, order=3)
        sig = np.tanh(3.2 * raw / (np.max(np.abs(raw)) + 1e-9)) / np.tanh(3.2)
        sig, gain, pan = shape(sig, hi=5200) * 0.55, 1.0, 0.68
    place(stem, sig, c['t0'], gain, pan)
    end = c['t0'] + len(sig) / SR
    report.append((c['t0'], end, c['t0'] + c['dur'], c['who'], c['text']))

x = stem / (np.max(np.abs(stem)) + 1e-9) * 0.95
pcm = np.clip(x.T * 32767, -32768, 32767).astype('<i2')
with wave.open(os.path.join(out_dir, 'voices.wav'), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
for t0, t1, budget, who, text in report:
    flag = f'  <-- {t1 - budget:+.2f}s over its budget' if t1 > budget + 0.12 else ''
    print(f'{t0:7.2f}-{t1:7.2f}  {who:8s} {text}{flag}')
