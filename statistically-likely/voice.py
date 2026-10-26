"""Voices for Statistically Likely: the narrator, the comment, and the mob.

    python3 voice.py build/events.json build/

Reads the cue sheet the film exports (captions, mirror pairs, the comment,
the shouts) and speaks it with Kokoro TTS, writing two stems:
  narration.wav  the narrator, plus the comment as a whisper
  crowd.wav      the mob: two dozen voices, shouted and overlapping
Model files are looked for in $KOKORO_DIR (default: build/kokoro).
"""
import json
import os
import re
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
rng = np.random.default_rng(7)

NARRATOR = 'af_heart'   # warm, unhurried
COMMENT = 'af_nicole'   # breathy and close, like a thought you didn't invite
CROWD = ['am_adam', 'am_echo', 'am_eric', 'am_fenrir', 'am_liam', 'am_michael', 'am_onyx', 'am_puck',
         'af_sarah', 'af_sky', 'af_jessica', 'af_river', 'af_nova', 'af_kore', 'bm_daniel', 'bm_lewis',
         'bf_isabella', 'bf_alice']


def speak(text, voice, speed):
    """TTS at 48 kHz, with the silence trimmed off both ends."""
    a, sr = tts.create(text, voice=voice, speed=speed, lang='en-us')
    a = np.asarray(a, dtype=np.float64)
    X = np.fft.rfft(a)
    a = np.fft.irfft(np.concatenate([X, np.zeros(len(a) * SR // sr // 2 + 1 - len(X))]), len(a) * SR // sr) * (SR / sr)
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
    if n <= 0:
        return
    stem[0, i0:i0 + n] += sig[:n] * gain * np.cos(pan * np.pi / 2) * np.sqrt(2)
    stem[1, i0:i0 + n] += sig[:n] * gain * np.sin(pan * np.pi / 2) * np.sqrt(2)


def clean(line):
    """Caption typography to something a voice can read."""
    s = line.replace('—', ',').replace('…', '').replace('“', '').replace('”', '').strip()
    s = re.sub(r'\s*,\s*$', ',', s)
    return s[0].upper() + s[1:]


narration = np.zeros((2, N))
crowd = np.zeros((2, N))
report = []

# ---- the narrator reads the captions ----
for c in cues['captions']:
    t, prev_end = c['t0'] + 0.2, None
    for i, line in enumerate(c['lines']):
        if i > 0:
            t = max(c['t0'] + c['l2'] + 0.05, prev_end + 0.25)
        final = c is cues['captions'][-1]
        sig = speak(clean(line), NARRATOR, 0.9 if final else 0.95)
        place(narration, shape(sig, lo=70), t)
        prev_end = t + len(sig) / SR
        report.append((t, prev_end, c['t1'], clean(line)))

# ...the mirror, each phrase and then its reflection...
for p in cues['pairs']:
    for text, t, until in ((p['left'], p['s'] + 0.25, p['s'] + p['flip']), (p['right'], p['s'] + p['flip'] + 0.45, p['s'] + p['dur'] - 0.8)):
        sig = speak(clean(text), NARRATOR, 0.95)
        place(narration, shape(sig, lo=70), t)
        report.append((t, t + len(sig) / SR, until, clean(text)))

# ...the internet's arrival, and the last word
for text, t, until in ((cues['mobCaption']['text'], cues['mobCaption']['t0'] + 0.1, T['freeze']),
                       (cues['tagline']['text'] + '.', cues['tagline']['t'], T['blackOut'])):
    sig = speak(clean(text), NARRATOR, 0.9)
    place(narration, shape(sig, lo=70), t)
    report.append((t, t + len(sig) / SR, until, clean(text)))

# ---- the comment, whispered as it types: only its words, exactly ----
free_at = 0
for card, fragment in zip(cues['card'], ('avoid men at all costs.', 'Stick with your girlfriends.', 'statistically likely to do you harm.')):
    t = max(card['t0'] + card['text'].index(fragment) / cues['cps'], free_at)
    sig = shape(speak(fragment, COMMENT, 1.05), lo=140)
    free_at = t + len(sig) / SR + 0.15
    place(narration, sig, t, 1.3, 0.5)
    d = int(0.035 * SR)
    place(narration, np.concatenate([np.zeros(d), shape(sig, hi=3000)]), t, 0.32, 0.25)
    place(narration, np.concatenate([np.zeros(2 * d), shape(sig, hi=3000)]), t, 0.26, 0.75)
    report.append((t, t + len(sig) / SR, None, '(whisper) ' + fragment))

# ---- the mob ----
def shout(text, voice, speed, pitch):
    sig = speak(text, voice, speed)
    idx = np.arange(0, len(sig) - 1, pitch)
    sig = np.interp(idx, np.arange(len(sig)), sig)
    sig = np.tanh(3.0 * sig / (np.max(np.abs(sig)) + 1e-9)) / np.tanh(3.0)
    return shape(sig, lo=280, hi=4800)


for s in cues['shouts']:
    text = s['text'].lower().replace(' = ', ', ')
    text = text[0].upper() + text[1:] + ('?' if text.startswith('what') else '!')
    pan = min(max(s['x'] / 1920, 0.08), 0.92)
    voices = rng.choice(CROWD, size=3, replace=False)
    sig = shout(text, voices[0], rng.uniform(1.15, 1.35), rng.uniform(0.92, 1.1))
    place(crowd, sig, s['t'], rng.uniform(0.75, 1.0), pan)
    # the pile-on: the same words picked up by others, further away
    for v in voices[1:1 + int(rng.integers(1, 3))]:
        echo = shape(shout(text, v, rng.uniform(1.1, 1.4), rng.uniform(0.9, 1.12)), hi=2500)
        place(crowd, echo, s['t'] + rng.uniform(0.15, 0.6), rng.uniform(0.25, 0.4), float(rng.uniform(0.1, 0.9)))


def write(path, x):
    x = x / (np.max(np.abs(x)) + 1e-9) * 0.95
    pcm = np.clip(x.T * 32767, -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


write(os.path.join(out_dir, 'narration.wav'), narration)
write(os.path.join(out_dir, 'crowd.wav'), crowd)
for t0, t1, until, text in sorted(report):
    flag = '  <-- runs past its window' if until is not None and t1 > until - 0.1 else ''
    print(f'{t0:7.2f}-{t1:7.2f}  {text}{flag}')
