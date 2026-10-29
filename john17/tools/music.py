"""Synthesise the ambient score for the John 17 film (original, royalty-free).

Soft detuned pads follow a chord plan tied to the three sections of the prayer,
with sparse piano-like arpeggios, a low drone, swells at the "glory" verses and
a synthetic hall reverb. Writes build/music.wav (48 kHz stereo).
Usage: python tools/music.py   (run from the john17/ folder, after tools/tts.py)
"""
import json, os
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, butter, sosfilt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
tl = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
T = tl["duration"]
N = int(T * SR) + SR * 6
out = np.zeros((2, N), np.float32)
rng = np.random.default_rng(17)

def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
def n(name, octave):
    return 12 * (octave + 1) + NOTE[name]

# Chord voicings (MIDI): low, mid and colour tones. Key of D major.
CH = {
    "Dadd9": [n("D", 2), n("A", 2), n("D", 3), n("F#", 3), n("A", 3), n("E", 4)],
    "D":     [n("D", 2), n("A", 2), n("D", 3), n("F#", 3), n("A", 3), n("D", 4)],
    "D/F#":  [n("F#", 2), n("A", 2), n("D", 3), n("F#", 3), n("A", 3), n("D", 4)],
    "Bm7":   [n("B", 1), n("F#", 2), n("B", 2), n("D", 3), n("F#", 3), n("A", 3)],
    "Bm":    [n("B", 1), n("F#", 2), n("B", 2), n("D", 3), n("F#", 3), n("B", 3)],
    "Gmaj7": [n("G", 1), n("D", 2), n("G", 2), n("B", 2), n("D", 3), n("F#", 3)],
    "G":     [n("G", 1), n("D", 2), n("G", 2), n("B", 2), n("D", 3), n("G", 3)],
    "Em7":   [n("E", 2), n("B", 2), n("E", 3), n("G", 3), n("B", 3), n("D", 4)],
    "Asus4": [n("A", 1), n("E", 2), n("A", 2), n("D", 3), n("E", 3), n("A", 3)],
    "A":     [n("A", 1), n("E", 2), n("A", 2), n("C#", 3), n("E", 3), n("A", 3)],
    "A/C#":  [n("C#", 2), n("E", 2), n("A", 2), n("C#", 3), n("E", 3), n("A", 3)],
    "F#m":   [n("F#", 1), n("C#", 2), n("F#", 2), n("A", 2), n("C#", 3), n("F#", 3)],
}

def sec(unit_id):
    return next(u["start"] for u in tl["units"] if u["id"] == unit_id)

s1, s2, s3 = sec("u06"), sec("u11"), sec("u26")
judas, evil = sec("u18"), sec("u21")
glory1, glory2 = sec("u10"), sec("u31")
outro = sec("u34")
end_card = next(s["start"] for s in tl["shots"] if s["id"] == "end")

# (start, end, progression, chord length, brightness, level)
PLAN = [
    (0.0, s1, ["Dadd9", "Bm7", "Gmaj7", "Asus4"], 8.0, 0.55, 0.85),
    (s1, s2, ["G", "D/F#", "Em7", "Asus4", "A", "Dadd9", "Gmaj7", "A"], 7.2, 0.7, 0.95),
    (s2, s3, ["Bm", "G", "D", "A", "Em7", "Bm7", "Gmaj7", "Asus4"], 8.0, 0.5, 0.8),
    (s3, outro, ["D", "A/C#", "Bm7", "G", "D/F#", "Gmaj7", "Asus4", "A"], 6.6, 0.75, 1.0),
    (outro, end_card, ["Bm7", "Gmaj7", "D", "Asus4"], 7.0, 0.45, 0.75),
    (end_card, T + 4, ["Dadd9"], 30.0, 0.6, 0.9),
]

def env_adsr(length, a, r, sus_len):
    t = np.arange(length) / SR
    e = np.minimum(1.0, t / a)
    rel_start = sus_len
    e = np.where(t > rel_start, e * np.exp(-(t - rel_start) / (r / 4.0)), e)
    return e.astype(np.float32)

def pad_note(m, t0, t1, amp, bright, pan):
    f0 = mtof(m)
    length = int((t1 - t0 + 3.0) * SR)
    t = np.arange(length) / SR
    sig = np.zeros(length, np.float32)
    cutoff = 500 + 2200 * bright
    for det in (-0.07, 0.0, 0.065):
        f = f0 * 2 ** (det / 12)
        ph = rng.uniform(0, 2 * np.pi)
        vib = 0.0012 * np.sin(2 * np.pi * 4.8 * t + ph)
        for k in range(1, 14):
            fk = f * k
            if fk > 9000:
                break
            g = (1.0 / k) / (1 + (fk / cutoff) ** 4)
            if g < 0.004:
                continue
            sig += (g * np.sin(2 * np.pi * fk * t * (1 + vib) + ph * k)).astype(np.float32)
    sig *= env_adsr(length, 1.8, 2.8, t1 - t0) * amp / 3.0
    i0 = int(t0 * SR)
    seg = out[:, i0:i0 + length]
    L = min(seg.shape[1], length)
    out[0, i0:i0 + L] += sig[:L] * np.sqrt(0.5 - pan * 0.5)
    out[1, i0:i0 + L] += sig[:L] * np.sqrt(0.5 + pan * 0.5)

def pluck(m, t0, amp, pan):
    f0 = mtof(m)
    length = int(3.5 * SR)
    t = np.arange(length) / SR
    sig = np.zeros(length, np.float32)
    for k, (g, d) in enumerate([(1.0, 1.1), (0.45, 0.8), (0.22, 0.55), (0.12, 0.4), (0.06, 0.3)], start=1):
        fk = f0 * k * (1 + 0.0004 * k * k)
        sig += (g * np.sin(2 * np.pi * fk * t) * np.exp(-t / d)).astype(np.float32)
    attack = np.minimum(1.0, t / 0.004)
    sig *= attack * amp
    i0 = int(t0 * SR)
    L = min(N - i0, length)
    if L <= 0:
        return
    out[0, i0:i0 + L] += sig[:L] * np.sqrt(0.5 - pan * 0.5)
    out[1, i0:i0 + L] += sig[:L] * np.sqrt(0.5 + pan * 0.5)

def swell_level(t):
    """Extra brightness/level around the 'glory' verses."""
    g = 0.0
    for c, w in ((glory1 + 3, 6.0), (glory2 + 5, 8.0)):
        g = max(g, np.exp(-((t - c) / w) ** 2))
    return g

chords = []
for start, end, prog, clen, bright, level in PLAN:
    t, i = start, 0
    while t < end - 0.5:
        t1 = min(end, t + clen)
        chords.append((t, t1, prog[i % len(prog)], bright, level))
        t, i = t1, i + 1

for (t0, t1, name, bright, level) in chords:
    mid = (t0 + t1) / 2
    sw = swell_level(mid)
    dark = 0.25 if (judas + 6 < mid < judas + 16) or (evil < mid < evil + 8) else 0.0
    b = min(1.0, bright + 0.35 * sw - dark)
    lv = level * (1 + 0.5 * sw) * (1 - 0.25 * dark)
    voices = CH[name]
    for j, m in enumerate(voices):
        pan = (-0.5 + j / max(1, len(voices) - 1)) * 0.7
        amp = 0.055 * lv * (0.8 if j == 0 else 1.0) * (0.8 if j >= 4 else 1.0)
        pad_note(m, t0, t1 + 0.4, amp, b, pan)
    if sw > 0.3:  # high shimmer octave during glory
        for m in voices[3:]:
            pad_note(m + 12, t0, t1 + 0.4, 0.03 * sw * lv, 0.9, 0.0)
    # sparse arpeggio of chord tones, an octave or two up
    density = 1.35 if t0 >= s3 and t0 < outro else (0.75 if t0 < s1 or t0 >= outro else 0.95)
    tt = t0 + 0.3
    tones = [m + 12 for m in voices[2:]] + [m + 24 for m in voices[3:5]]
    while tt < t1 - 0.2:
        m = tones[rng.integers(len(tones))]
        pluck(m, tt, 0.05 * lv * (0.7 + 0.3 * rng.random()), rng.uniform(-0.6, 0.6))
        tt += (0.9 + rng.random() * 0.9) / density

# low drone on D through the whole piece, softer during the outro
t = np.arange(N) / SR
drone = 0.008 * np.sin(2 * np.pi * mtof(n("D", 2)) * t) + 0.005 * np.sin(2 * np.pi * mtof(n("A", 2)) * t)
out += drone.astype(np.float32)

# keep it warm but not boomy: band-limit to 70 Hz - 6.5 kHz
sos = butter(2, [70, 6500], "band", fs=SR, output="sos")
out = sosfilt(sos, out, axis=1).astype(np.float32)

# hall reverb: exponentially decaying filtered noise, decorrelated per channel
ir_len = int(3.4 * SR)
tt = np.arange(ir_len) / SR
ir = np.zeros((2, ir_len), np.float32)
for ch in range(2):
    noise = np.random.default_rng(100 + ch).standard_normal(ir_len).astype(np.float32)
    noise = sosfilt(butter(2, [200, 5000], "band", fs=SR, output="sos"), noise)
    ir[ch] = noise * np.exp(-tt / 0.9) * np.minimum(1, tt / 0.02)
ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))
wet = np.stack([fftconvolve(out[ch], ir[ch])[:N] for ch in range(2)]).astype(np.float32)
mix = 0.62 * out + 0.55 * wet

# fades
fade_in = np.minimum(1, t / 2.5)
fade_out = np.clip((T - t) / 5.0, 0, 1)
mix *= (fade_in * fade_out).astype(np.float32)
mix = mix[:, : int(T * SR)]
mix /= np.abs(mix).max() + 1e-9
mix *= 0.7
sf.write(os.path.join(ROOT, "build", "music.wav"), mix.T, SR, subtype="PCM_16")
print(f"music: {T:.1f}s, {len(chords)} chords")
