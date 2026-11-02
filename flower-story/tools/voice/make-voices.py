#!/usr/bin/env python3
"""
make-voices.py — cast and synthesise the film's narration and voice acting.

Reads tools/voice/cues.raw.json (from extract-cues.js) plus the 07/08 dialogue
(those scenes draw their own balloons), assigns a voice to every line, renders
each with the Kokoro neural TTS model, schedules it against the picture, and
writes tools/voice/voices.wav (48 kHz stereo, same length as the film) and
tools/voice/schedule.json.

Run with the Python that has kokoro-onnx installed:
  python make-voices.py --model kokoro-v1.0.onnx --voices voices-v1.0.bin
"""
import argparse, json, os, re
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--model', required=True)
ap.add_argument('--voices', required=True)
ap.add_argument('--total', type=float, default=522.3)
args = ap.parse_args()

SR = 48000
starts = {}
for line in open(os.path.join(HERE, 'starts.txt')):
    sid, s = line.split()
    starts[sid] = float(s)

# ---- casting -------------------------------------------------------------
# (kokoro voice, speed, gain, pan)  — pan -1 left .. 1 right
CAST = {
    'narrator': ('am_michael', 0.94, 1.00, 0.0),
    'me':       ('am_michael', 1.00, 1.00, -0.12),
    'h1':       ('am_fenrir', 1.04, 0.95, 0.15),
    'h2':       ('af_bella', 1.04, 0.92, 0.18),
    'h3':       ('af_nicole', 1.02, 0.95, 0.1),
    'h4':       ('am_puck', 1.06, 0.92, 0.22),
    'emb':      ('bm_george', 0.88, 1.00, 0.15),
    'wonder':   ('af_heart', 0.98, 0.95, -0.2),
    'granny':   ('bf_isabella', 0.92, 0.55, -0.35),
    'teen':     ('am_echo', 1.08, 0.55, 0.3),
    'gossip3':  ('af_sarah', 1.05, 0.55, 0.0),
    'gossip4':  ('af_bella', 1.05, 0.55, 0.25),
}
CHORUS = {
    'hikers':   [('am_fenrir', 1.06, 0.62, 0.1), ('af_bella', 1.08, 0.58, 0.25), ('am_puck', 1.1, 0.58, -0.05)],
    'emotions': [('af_heart', 0.86, 0.42, -0.3), ('am_puck', 0.84, 0.36, 0.25), ('af_nicole', 0.88, 0.36, -0.1), ('bf_emma', 0.85, 0.34, 0.35), ('af_sky', 0.87, 0.34, 0.05)],
}

def speakable(s):
    s = s.replace('\n', ' ')
    s = s.replace('$10', 'ten dollars').replace('$200', 'two hundred dollars').replace('$300', 'three hundred dollars')
    s = s.replace('…', '... ').replace('—', ', ').replace('’', "'").replace('“', '"').replace('”', '"')
    s = re.sub(r'\s+', ' ', s).strip(' ,')
    if s.startswith('...'): s = s[3:].strip()
    return s

raw = json.load(open(os.path.join(HERE, 'cues.raw.json')))
lines = []
GOSSIP = {'…a FLOWER?': 'gossip3', 'smiling like a lunatic': 'granny', 'must be some flower': 'teen', 'where do we get one?': 'gossip4'}
for c in raw:
    k, txt, who, sc = c['kind'], c['text'], c['who'], c['scene']
    if k == 'hand' and sc == 'complexity':
        continue                                    # notebook annotations stay silent
    if sc == 'reflection' and k == 'title':
        continue                                    # the end card is left to the music
    if sc == 'title':
        continue                                    # the opening title is read once, below
    if k == 'narration':
        if txt == 'and says, “Can we stop here?”':
            lines.append(dict(T=c['T0'], text='and says,', role='narrator', win=c['T1'] - c['T0']))
            continue
        lines.append(dict(T=c['T0'], text=txt, role='narrator', win=c['T1'] - c['T0']))
    elif k == 'title':
        lines.append(dict(T=c['T0'] + 0.4, text=txt, role='narrator', win=c['T1'] - c['T0']))
    elif k == 'hand':
        if sc == 'three-heads':
            lines.append(dict(T=c['T0'] + 0.1, text=txt, role='emotions', win=c['T1'] - c['T0']))
        else:
            lines.append(dict(T=c['T0'] + 0.15, text=txt, role='wonder', win=c['T1'] - c['T0']))
    elif k == 'dialogue':
        role = who or GOSSIP.get(txt, 'gossip3')
        if role == 'all': role = 'hikers'
        bg = sc == 'word-spreads'
        lines.append(dict(T=c['T0'] + 0.1, text=txt, role=role, win=c['T1'] - c['T0'], bg=bg))

# scenes 07/08 draw their own balloons; their cues (local times) come from the source
for sid, local in [('return', [(16.3, 21.3, 'Did you find the meaning you were looking for at the summit?', 'me'),
                               (23.75, 26.0, 'It was fine, I guess.', 'h1'), (26.35, 28.5, 'What about you?', 'h1'),
                               (29.25, 31.6, 'I found a flower.', 'me'), (31.95, 36.7, 'And not just any flower—a flower I gave meaning to.', 'me')]),
                   ('three-heads', [(0.6, 5.4, 'It wasn’t important until I saw it and made it matter.', 'me'),
                                    (6.1, 13.75, 'It was something small, but when I gave it a part of my soul, it felt meaningful to me.', 'me'),
                                    (22.3, 24.6, 'Bro, are you okay?', 'h1'), (25.0, 27.45, 'That sounds… intense.', 'h1')])]:
    for t0, t1, txt, who in local:
        lines.append(dict(T=starts[sid] + t0 + 0.1, text=txt, role=who, win=t1 - t0))

# the opening title, read slowly as it writes on
lines.append(dict(T=2.0, text='The Hikers, the Flower, and the Meaning We Create.', role='narrator', win=9.0, speed=0.86))
lines.sort(key=lambda l: l['T'])

# ---- synthesis -----------------------------------------------------------
k = Kokoro(args.model, args.voices)
cache = {}
def synth(text, voice, speed):
    key = (text, voice, round(speed, 3))
    if key not in cache:
        a, sr = k.create(speakable(text), voice=voice, speed=speed, lang='en-us')
        a = np.asarray(a, dtype=np.float32)
        # resample 24k -> 48k (linear is fine for speech at 2x), trim silence, normalise
        x = np.interp(np.arange(0, len(a) * 2) / 2.0, np.arange(len(a)), a).astype(np.float32)
        nz = np.where(np.abs(x) > 0.01)[0]
        if len(nz): x = x[max(0, nz[0] - 480): nz[-1] + 2400]
        rms = np.sqrt(np.mean(x ** 2) + 1e-12)
        x = x * (0.11 / rms)                       # consistent loudness across voices
        pk = np.max(np.abs(x))
        if pk > 0.89: x *= 0.89 / pk
        cache[key] = x
    return cache[key]

out = np.zeros((int((args.total + 1) * SR), 2), dtype=np.float32)
sched = []
fg_end = 0.0
for i, l in enumerate(lines):
    role = l['role']
    voices = CHORUS[role] if role in CHORUS else [CAST[role]]
    v0, sp0, g0, p0 = voices[0]
    sp = l.get('speed', sp0)
    clip = synth(l['text'], v0, sp)
    dur = len(clip) / SR
    bg = l.get('bg', False)
    # the next foreground line bounds how long this one may run
    nxt = next((m['T'] for m in lines[i + 1:] if not m.get('bg')), args.total)
    room = max(l['win'] + 0.6, nxt - l['T'] - 0.15)
    if not bg and dur > room and sp < 1.25:
        sp2 = min(1.25, sp * dur / room)
        clip = synth(l['text'], v0, sp2); dur = len(clip) / SR; sp = sp2
    start = l['T'] if bg else max(l['T'], fg_end + 0.12)
    for j, (v, s_, g, pan) in enumerate(voices):
        c = clip if j == 0 else synth(l['text'], v, s_ * sp / sp0)
        off = int((start + j * 0.07) * SR)
        L, R = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
        n = min(len(c), len(out) - off)
        if n <= 0: continue
        out[off:off + n, 0] += c[:n] * g * L * 1.41
        out[off:off + n, 1] += c[:n] * g * R * 1.41
    if not bg: fg_end = start + dur
    sched.append(dict(start=round(start, 2), cue=round(l['T'], 2), late=round(start - l['T'], 2), dur=round(dur, 2), speed=round(sp, 3), role=role, text=l['text']))
    print(f"{start:7.2f} (+{start - l['T']:.2f}) {dur:5.2f}s x{sp:.2f} {role:9s} {l['text'][:70]}")

pk = np.max(np.abs(out))
if pk > 0.95: out *= 0.95 / pk
sf.write(os.path.join(HERE, 'voices.wav'), out, SR, subtype='PCM_16')
json.dump(sched, open(os.path.join(HERE, 'schedule.json'), 'w'), indent=1, ensure_ascii=False)
late = [s for s in sched if s['late'] > 0.6]
print(f"\n{len(sched)} lines; {len(late)} start more than 0.6 s after their text appears; max lateness {max(s['late'] for s in sched):.2f} s")
