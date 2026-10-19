"""Generates the soundtrack for an explainer video (explainer/<name>-soundtrack.wav).

    python3 explainer/music.py open-gate
    python3 explainer/music.py strangers

Each preset lists sections of warm pad + arpeggio, low dissonant drones,
and percussive hits, all timed to the video's scenes.
"""
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100

# Chord voicings as MIDI notes; 4 seconds per chord.
DARK = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]    # Am F C G
BRIGHT = [[48, 52, 55], [53, 57, 60], [55, 59, 62], [57, 60, 64]]  # C F G Am
CHEERY = [[60, 64, 67], [65, 69, 72], [67, 71, 74], [60, 64, 67]]  # C F G C, an octave up

PRESETS = {
    # FORCE is pressed at 72.8s, the stamp lands at 75.6s, warmth returns at 81s.
    'open-gate': dict(
        duration=97.0,
        sections=[(0.0, 72.8, DARK, 1.0), (81.0, 97.0, BRIGHT, 1.1)],
        drones=[(72.8, 81.0)],
        hits=[(72.8, 90, 0.6), (75.6, 55, 0.9)],
    ),
    # "Best society ever" plays falsely cheery until the reveal at 85s.
    'strangers': dict(
        duration=122.0,
        sections=[(0.0, 79.0, DARK, 0.9), (79.0, 85.0, CHEERY, 0.8), (93.0, 104.0, DARK, 0.8),
                  (104.0, 122.0, BRIGHT, 1.1)],
        drones=[(85.0, 93.0)],
        hits=[(85.0, 60, 0.9)],
    ),
}

name = sys.argv[1] if len(sys.argv) > 1 else 'open-gate'
cfg = PRESETS[name]
DUR = cfg['duration']

t = np.arange(int(SR * DUR)) / SR
out = np.zeros_like(t)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def env(start, end, attack, release):
    e = np.clip((t - start) / attack, 0, 1) * np.clip((end - t) / release, 0, 1)
    return e * ((t >= start) & (t < end))


def tone(freq, weights=(1, 0.35, 0.15, 0.06)):
    sig = np.zeros_like(t)
    for k, w in enumerate(weights, 1):
        for detune in (-0.0025, 0.0025):
            sig += w * np.sin(2 * np.pi * freq * k * (1 + detune) * t + k)
    return sig / 2


cache = {}


def note(m):
    if m not in cache:
        cache[m] = tone(hz(m))
    return cache[m]


def section(start, end, prog, level):
    cs = start
    i = 0
    while cs < end:
        ce = min(cs + 4.0, end)
        chord = prog[i % len(prog)]
        e = env(cs, ce + 0.6, 1.2, 1.4)
        for m in chord:
            out[:] += level * 0.10 * e * note(m)
        out[:] += level * 0.08 * e * note(chord[0] - 12)
        # arpeggio: eighth notes at 120 bpm
        arp = chord + [chord[1] + 12]
        for j in range(16):
            ns = cs + j * 0.25
            if ns >= ce:
                break
            m = arp[j % 4] + 12
            mask = (t >= ns) & (t < ns + 1.2)
            d = t[mask] - ns
            out[mask] += level * 0.045 * np.exp(-d * 4.5) * np.sin(2 * np.pi * hz(m) * d) * np.minimum(d * 200, 1)
        cs = ce
        i += 1


for sec in cfg['sections']:
    section(*sec)

# Low dissonant drone with swelling noise.
rng = np.random.default_rng(7)
noise = np.convolve(rng.standard_normal(len(t)), np.ones(60) / 60, mode='same')
for start, end in cfg['drones']:
    de = env(start, end, 0.4, 1.5)
    out += 0.16 * de * (tone(hz(33), (1, 0.5, 0.3)) + tone(hz(34), (1, 0.5, 0.3)))
    out += 0.5 * de * np.clip((t - start) / 3, 0, 1) * noise

# Percussive hits.
for at, f, amp in cfg['hits']:
    m = (t >= at) & (t < at + 1.5)
    d = t[m] - at
    out[m] += amp * np.exp(-d * 6) * np.sin(2 * np.pi * f * d * (1 + np.exp(-d * 20)))

# Global fade in/out and normalise.
out *= np.clip(t / 1.5, 0, 1) * np.clip((DUR - t) / 3.0, 0, 1)
out /= np.max(np.abs(out)) / 0.85

pcm = (np.repeat(out[:, None], 2, axis=1) * 32767).astype(np.int16)
path = Path(__file__).with_name(f'{name}-soundtrack.wav')
with wave.open(str(path), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', path)
