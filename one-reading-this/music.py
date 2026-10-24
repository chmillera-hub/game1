"""Procedural score: pads, piano, bass, plus word-synced accents.

High bells / pizzicato lift hopeful or light words; low cello swells sit under
heavy or existential words. Music ducks under dialogue. Rain ambience in the
kitchen. Writes build/mix.wav (stereo 44.1k)."""
import json, wave
import numpy as np
from script import BEATS

SR = 44100
rng = np.random.default_rng(7)

C = {  # chord voicings (MIDI)
    "D": [38, 50, 57, 62, 66, 69], "Bm": [35, 47, 54, 59, 62, 66], "G": [31, 43, 55, 59, 62, 67],
    "A": [33, 45, 52, 57, 61, 64], "Em": [28, 40, 52, 55, 59, 64], "F#m": [30, 42, 54, 57, 61, 66],
    "C": [36, 48, 55, 60, 64, 67], "Asus": [33, 45, 52, 57, 62, 64], "Dmaj7": [38, 50, 57, 61, 66, 69],
}
PROG = {
    "heavy": ["Bm", "G", "Em", "F#m"],
    "warm": ["D", "A", "Bm", "G"],
    "tender": ["G", "D", "Em", "Asus"],
    "light": ["D", "G", "A", "D"],
    "rise": ["G", "A", "Bm", "D"],
    "wonder": ["Em", "C", "G", "D"],
    "end": ["G", "A", "Dmaj7", "Dmaj7"],
}
MOOD = {}
for rng_, mood in [((0, 1), "heavy"), ((2, 12), "warm"), ((13, 16), "heavy"), ((17, 17), "light"),
                   ((18, 18), "rise"), ((19, 23), "tender"), ((24, 24), "heavy"), ((25, 29), "light"),
                   ((30, 34), "heavy"), ((35, 35), "tender"), ((36, 39), "light"), ((40, 40), "rise"),
                   ((41, 42), "tender"), ((43, 46), "heavy"), ((47, 48), "rise"), ((49, 51), "tender"),
                   ((52, 54), "light"), ((55, 56), "heavy"), ((57, 61), "tender"), ((62, 63), "wonder"),
                   ((64, 66), "warm"), ((67, 68), "rise"), ((69, 71), "end")]:
    for k in range(rng_[0], rng_[1] + 1):
        MOOD[k] = mood
BAR = 4.0


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def env_adsr(n, a, r, sus=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-3))
    rel_start = n / SR - r
    e *= np.clip(1 - (t - rel_start) / max(r, 1e-3), 0, 1)
    return e * sus


def add(buf, start, sig, pan=0.0):
    k = int(start * SR)
    if k >= buf.shape[1] or k + len(sig) <= 0:
        return
    if k < 0:
        sig = sig[-k:]; k = 0
    sig = sig[:buf.shape[1] - k]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[0, k:k + len(sig)] += sig * l * 1.414
    buf[1, k:k + len(sig)] += sig * r * 1.414


def pad_note(m, dur, bright=1.0, det=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + det)
    s = np.zeros(n)
    for h in range(1, 7):
        s += np.sin(2 * np.pi * f * h * t + h) / h ** (1.6 / bright)
        s += np.sin(2 * np.pi * f * h * 1.003 * t) / h ** (1.6 / bright) * 0.6
    trem = 1 + 0.08 * np.sin(2 * np.pi * 0.23 * t + m)
    return s * trem * env_adsr(n, 1.6, 1.8) * 0.06


def piano(m, vel=0.5, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m); s = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * np.sqrt(1 + 0.0004 * h * h)
        s += np.sin(2 * np.pi * fh * t) * np.exp(-t * (1.2 + h * 0.9)) / h ** 1.1
    s *= np.minimum(1, t / 0.004)
    s += rng.normal(0, 1, n) * np.exp(-t * 90) * 0.02  # hammer
    return s * vel * 0.35 * env_adsr(n, 0.004, 0.25)


def bell(m, vel=0.5, dur=3.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 1.1) +
         0.5 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 2.2) +
         0.25 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 3.5) +
         0.12 * np.sin(2 * np.pi * f * 5.43 * t) * np.exp(-t * 6))
    return s * np.minimum(1, t / 0.003) * vel * 0.22


def cello(m, dur=3.2, vel=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.8)
    ph = 2 * np.pi * hz(m) * np.cumsum(vib) / SR
    s = np.zeros(n)
    for h in range(1, 10):
        s += np.sin(ph * h) / h * (0.85 ** h)
    e = env_adsr(n, 0.7, 1.4)
    return s * e * vel * 0.18


def pizz(m, vel=0.5):
    n = int(0.6 * SR); t = np.arange(n) / SR; f = hz(m)
    s = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (9 + 5 * h)) / h for h in range(1, 6))
    return s * np.minimum(1, t / 0.002) * vel * 0.32


def main():
    tl = json.load(open("build/timeline.json"))
    beats = tl["beats"]; total = tl["total"]
    n = int(total * SR) + SR
    mus = np.zeros((2, n), np.float32)
    acc = np.zeros((2, n), np.float32)

    def beat_at(t):
        k = 0
        for j, b in enumerate(beats):
            if b["start"] - 0.4 <= t:
                k = j
        return k

    # ---- bed: bars of chords
    nbars = int(np.ceil(total / BAR)) + 1
    bar_moods = []
    counters = {}
    for bi in range(nbars):
        t0 = bi * BAR
        mood = MOOD[beat_at(t0 + 0.5)]
        idx = counters.get(mood, 0); counters[mood] = idx + 1
        prev = bar_moods[-1][0] if bar_moods else None
        if mood != prev:
            idx = 0; counters[mood] = 1
        ch = PROG[mood][idx % 4]
        if t0 > total - 9:
            ch = "Dmaj7" if t0 > total - 5 else "A" if t0 < total - 7 else "G"
        bar_moods.append((mood, ch))
        notes = C[ch]
        bright = {"heavy": 0.7, "warm": 1.0, "tender": 0.9, "light": 1.15, "rise": 1.3, "wonder": 1.25, "end": 1.1}[mood]
        lvl = {"heavy": 0.8, "warm": 0.85, "tender": 0.85, "light": 0.75, "rise": 1.05, "wonder": 1.1, "end": 1.0}[mood]
        for j, m in enumerate(notes[1:]):
            if mood == "heavy" and j == len(notes) - 2:
                continue
            add(mus, t0 - 0.3, pad_note(m, BAR + 1.8, bright, det=0.0005 * j) * lvl, pan=-0.5 + j * 0.25)
        # bass
        bnote = notes[0] + (12 if notes[0] < 34 else 0)
        add(mus, t0, cello(bnote, BAR + 0.8, 0.35 if mood == "heavy" else 0.22), 0)
        # piano figures
        if mood in ("warm", "tender", "light", "rise", "wonder", "end"):
            pat = {"warm": [0, 1.5, 2, 3], "tender": [0, 1, 2.5], "light": [0, 0.5, 1, 2, 2.5, 3],
                   "rise": [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5], "wonder": [0, 1, 2, 3], "end": [0, 1.5, 3]}[mood]
            tones = [x for x in notes if 55 <= x <= 79] + [x + 12 for x in notes if 55 <= x + 12 <= 81]
            tones = sorted(set(tones))
            for k, p in enumerate(pat):
                m = tones[(k * 2 + bi) % len(tones)]
                add(mus, t0 + p, piano(m, 0.28 + 0.1 * (k == 0)), pan=0.3 * np.sin(k + bi))
        else:
            add(mus, t0, piano(notes[1] + 12, 0.35, 4), -0.2)
            add(mus, t0 + 2, piano(notes[2] + 12, 0.25, 4), 0.2)

    def chord_at(t):
        return C[bar_moods[min(int(t // BAR), len(bar_moods) - 1)][1]]

    # ---- word-synced accents
    for b in beats:
        for kind, t in b["cues"]:
            notes = chord_at(t)
            if kind == "hi":
                hi = sorted(set([x + 24 for x in notes[2:] if x + 24 <= 93]))[-3:]
                for k, m in enumerate(hi):
                    add(acc, t - 0.05 + k * 0.13, bell(m, 0.55 - k * 0.08), pan=-0.3 + k * 0.3)
            elif kind == "lo":
                root = notes[0] if notes[0] >= 31 else notes[0] + 12
                add(acc, t - 0.25, cello(root, 3.4, 0.9), -0.1)
                add(acc, t - 0.25, cello(root + 7, 3.0, 0.4), 0.15)
                add(acc, t - 0.05, piano(root, 0.6, 4), 0)
            elif kind == "laugh":
                tones = [x for x in notes if 60 <= x + 12 <= 88]
                for k, m in enumerate(tones[:3]):
                    add(acc, t + 0.05 + k * 0.09, pizz(m + 12, 0.6), pan=-0.4 + k * 0.4)
            elif kind == "swell":
                for k, m in enumerate(sorted(notes[2:])):
                    s = pad_note(m + 12, 5.0, 1.4) * np.linspace(0.2, 1.6, int(5.0 * SR)) ** 1.5
                    add(acc, t - 1.6, s * 1.4, -0.4 + k * 0.2)
                add(acc, t + 0.1, bell(notes[-1] + 24, 0.5), 0.2)
            elif kind == "stab":
                add(acc, t - 0.02, bell(86, 0.7), -0.2)
                add(acc, t - 0.02, bell(81, 0.5), 0.2)

    # ---- duck under dialogue
    voice = np.load("build/voice_mix.npy")[:n]
    v = np.zeros(n, np.float32); v[:len(voice)] = voice
    hop = 441
    e = np.sqrt(np.convolve(v ** 2, np.ones(hop) / hop, "same"))[::hop]
    e = np.clip(e / (np.percentile(e[e > 0.01], 90) + 1e-6), 0, 1)
    sm = np.zeros_like(e); a = 0
    for i, x in enumerate(e):
        a = a + (0.5 if x > a else 0.06) * (x - a)
        sm[i] = a
    duck = np.repeat(sm, hop)[:n]
    duck = np.pad(duck, (0, n - len(duck)))
    mus *= (1 - 0.55 * duck)
    acc *= (1 - 0.3 * duck)

    # ---- rain ambience (kitchen only; eases at the end)
    rain = np.zeros(n, np.float32)
    white = rng.normal(0, 1, n).astype(np.float32)
    # cheap coloured noise: difference of two moving averages
    lo = np.convolve(white, np.ones(9) / 9, "same")
    lo2 = np.convolve(white, np.ones(60) / 60, "same")
    rain = (lo - lo2) * 0.5
    gain = np.zeros(n, np.float32)
    import script
    for b, sb in zip(beats, script.BEATS):
        shot = sb.get("shot", "two")
        g = 0.0 if shot.startswith("vis:") and "|" not in shot else 0.055
        if sb.get("fx", {}).get("rain_ease") or b["i"] >= 69:
            g = 0.02
        s0 = int(b["start"] * SR); s1 = int(b["next"] * SR)
        gain[s0:s1] = g
    gain[:int(beats[0]["start"] * SR)] = 0.055
    gain = np.convolve(gain, np.ones(SR) / SR, "same")
    # drips
    for t in np.cumsum(rng.uniform(0.4, 1.8, 600)):
        if t < total:
            d = int(0.03 * SR); tt = np.arange(d) / SR
            k = int(t * SR)
            if k + d < n:
                rain[k:k + d] += np.sin(2 * np.pi * rng.uniform(1800, 3200) * tt) * np.exp(-tt * 160) * 0.5
    rain *= gain * 0.7

    music = mus * 0.36 + acc * 0.6
    music[0] += rain; music[1] += rain * 0.95
    mix = music.copy()
    mix[0] += v * 0.92; mix[1] += v * 0.92
    peak = np.max(np.abs(mix))
    mix = np.tanh(mix / peak * 1.25) * 0.9
    write("build/mix.wav", mix)
    write("build/music_only.wav", music / (np.max(np.abs(music)) + 1e-9) * 0.8)
    print("written", mix.shape[1] / SR, "s")


def write(p, x):
    with wave.open(p, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x.T, -1, 1) * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    main()
