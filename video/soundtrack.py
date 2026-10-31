"""Soundtrack for The Hearthdeep Files video.

Reads the per-scene segment logs written by render.cjs (frame counts plus the frames where a
line is revealed or a page turns) and synthesises a matching score: a slow ambient pad that
changes chord with each page, a bell for every revealed line, and a paper whoosh per page turn.

usage: python3 soundtrack.py <segs dir> <out.wav>
"""
import json
import os
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(7)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# One chord per page: cover, cast, koans 1-13, epilogue (D minor modal, resolving to D major).
CHORDS = [
    [38, 45, 50, 53, 60, 64], [34, 41, 50, 57, 60], [41, 48, 55, 57, 60], [36, 43, 52, 62],
    [31, 38, 46, 53, 57], [34, 41, 50, 57], [38, 45, 50, 53, 60, 64], [33, 40, 43, 48, 50],
    [29, 36, 52, 55, 57], [40, 48, 50, 55], [31, 38, 53, 58], [33, 40, 50, 52],
    [34, 41, 50, 57, 60], [36, 41, 48, 55, 57], [38, 45, 54, 61, 64], [38, 45, 54, 64, 69],
]
MINOR_PENTA = [74, 77, 79, 81, 84, 86]
MAJOR_PENTA = [74, 76, 78, 81, 83, 86]


def load(segdir):
    segs = []
    for name in sorted(os.listdir(segdir)):
        if name.startswith('seg') and name.endswith('.json'):
            with open(os.path.join(segdir, name)) as f:
                segs.append(json.load(f))
    segs.sort(key=lambda s: s['scene'])
    return segs


def pad_voice(freq, n, phase):
    t = np.arange(n) / SR
    detune = 0.0016
    v = (np.sin(2 * np.pi * freq * (1 - detune) * t + phase)
         + np.sin(2 * np.pi * freq * (1 + detune) * t + phase * 1.7)
         + 0.12 * np.sin(2 * np.pi * freq * 2 * t + phase * 0.3))
    trem = 0.82 + 0.18 * np.sin(2 * np.pi * (0.06 + 0.03 * rng.random()) * t + phase)
    return v * trem


def bell(freq, dur=3.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for ratio, amp, decay in [(1, 1, 2.6), (2.0, 0.32, 1.4), (3.01, 0.16, 0.8), (4.17, 0.07, 0.45)]:
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / decay)
    attack = np.minimum(1, t / 0.006)
    return out * attack


def whoosh(dur=0.75):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    t = np.arange(n) / SR
    cut = 3200 * (600 / 3200) ** (t / dur)  # sweep down
    lo = np.zeros(n)
    hi = np.zeros(n)
    a_lo = 0.0
    a_hi = 0.0
    for i in range(n):  # one-pole low-pass minus a slower one gives a soft band-pass
        k = 1 - np.exp(-2 * np.pi * cut[i] / SR)
        a_lo += k * (noise[i] - a_lo)
        k2 = 1 - np.exp(-2 * np.pi * (cut[i] * 0.25) / SR)
        a_hi += k2 * (a_lo - a_hi)
        lo[i] = a_lo
        hi[i] = a_hi
    band = lo - hi
    env = np.minimum(1, t / 0.09) * np.exp(-np.maximum(0, t - 0.09) / 0.22)
    return band * env


def reverb_ir(seconds=2.8):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((2, n)) * np.exp(-t / 0.75)
    ir[:, : int(0.012 * SR)] = 0
    return ir / np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))


def convolve(x, h):
    n = len(x) + len(h) - 1
    size = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(h, size), size)[:len(x)]


def place(buf, sig, start, pan=0.0, gain=1.0):
    s = int(start * SR)
    if s >= buf.shape[1]:
        return
    e = min(buf.shape[1], s + len(sig))
    left = np.cos((pan + 1) * np.pi / 4)
    right = np.sin((pan + 1) * np.pi / 4)
    buf[0, s:e] += sig[: e - s] * gain * left
    buf[1, s:e] += sig[: e - s] * gain * right


def main(segdir, out):
    segs = load(segdir)
    fps = segs[0]['fps']
    starts, t = [], 0.0
    for s in segs:
        starts.append(t)
        t += s['frames'] / fps
    total = t
    n = int(total * SR) + SR
    pad = np.zeros((2, n))
    fx = np.zeros((2, n))

    xf = 2.5
    for i, s in enumerate(segs):
        a = max(0.0, starts[i] - xf / 2)
        b = min(total, starts[i] + s['frames'] / fps + xf / 2)
        m = int((b - a) * SR)
        tt = np.arange(m) / SR
        env = np.minimum(1, tt / xf) * np.minimum(1, (b - a - tt) / xf)
        env = 0.5 - 0.5 * np.cos(np.pi * np.clip(env, 0, 1))
        chord = CHORDS[min(s['scene'], len(CHORDS) - 1)]
        for j, note in enumerate(chord):
            amp = 0.055 if note < 48 else 0.04 if note < 60 else 0.026
            v = pad_voice(midi(note), m, rng.random() * 6.28) * amp * env
            place(pad, v, a, pan=(-0.45 if j % 2 else 0.45) * (j / len(chord)))

    for i, s in enumerate(segs):
        scale = MAJOR_PENTA if s['scene'] >= 14 else MINOR_PENTA
        for ev in s['events']:
            at = starts[i] + ev['f'] / fps
            if ev['type'] == 'beat':
                note = scale[(ev['k'] - 1) % len(scale)]
                place(fx, bell(midi(note)), at, pan=0.35 if ev['k'] % 2 else -0.35, gain=0.16)
                place(fx, bell(midi(note - 12), 2.4), at + 0.02, pan=0, gain=0.05)
            elif ev['type'] == 'turn':
                place(fx, whoosh(), at, pan=-0.2, gain=0.55)

    for j, note in enumerate([74, 77, 81, 86]):  # opening arpeggio
        place(fx, bell(midi(note)), 0.8 + j * 0.32, pan=-0.3 + j * 0.2, gain=0.1)
    for j, note in enumerate([62, 69, 74, 78, 81]):  # closing chord
        place(fx, bell(midi(note), 4.5), total - 9 + j * 0.08, pan=-0.4 + j * 0.2, gain=0.09)

    ir = reverb_ir()
    wet = np.stack([convolve(fx[0], ir[0]), convolve(fx[1], ir[1])])
    padwet = np.stack([convolve(pad[0], ir[1]), convolve(pad[1], ir[0])])
    mix = pad * 0.85 + padwet * 0.25 + fx * 0.9 + wet * 0.45
    mix = mix[:, : int(total * SR)]

    tt = np.arange(mix.shape[1]) / SR
    mix *= np.minimum(1, tt / 1.5) * np.clip((total - tt) / 3.0, 0, 1)
    mix = np.tanh(mix / np.max(np.abs(mix)) * 1.15) / np.tanh(1.15) * 0.89

    pcm = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
    with wave.open(out, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(f'wrote {out}: {total:.1f} s, {len(segs)} segments')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
