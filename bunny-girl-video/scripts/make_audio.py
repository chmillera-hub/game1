"""Music, sound effects and the final mix.

An original, bouncy tune in C major (written here note by note), played by
General MIDI instruments through FluidSynth, with the instruments changing
per scene. The tune drops out on "And suddenly...", a drum roll builds, and
a crash + new section starts on "POOF!". Sound effects land on the words
(boings on "Hop!", pops on the dog names, a harp on "hug!", ...).

Writes build/mix.wav (48 kHz stereo, loudness-normalised); with --cartoon,
build/mix_cartoon.wav with extra effects for the cartoon version's actions.
Needs: fluidsynth + FluidR3_GM.sf2, mido, numpy, scipy, soundfile, ffmpeg.
"""
import argparse
import json
import os
import subprocess
import sys

import mido
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline  # noqa: E402

BUILD = os.path.join(os.path.dirname(HERE), "build")
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
SR = 48000

# ---------------------------------------------------------------- the tune
# (note, beat, length in beats) per bar; chords: C Am F G C Am F-G C
THEME_A = [
    [(76, 0, .5), (79, .5, .5), (79, 1, 1), (76, 2, .5), (72, 2.5, .5), (74, 3, 1)],
    [(76, 0, 1), (72, 1, .5), (69, 1.5, .5), (72, 2, 2)],
    [(77, 0, .5), (81, .5, .5), (81, 1, 1), (77, 2, .5), (72, 2.5, .5), (74, 3, 1)],
    [(74, 0, 1), (71, 1, .5), (67, 1.5, .5), (74, 2, 2)],
    [(76, 0, .5), (79, .5, .5), (84, 1, 1), (83, 2, .5), (81, 2.5, .5), (79, 3, 1)],
    [(81, 0, .5), (79, .5, .5), (76, 1, 1), (72, 2, 1), (76, 3, 1)],
    [(77, 0, 1), (81, 1, 1), (79, 2, 1), (71, 3, 1)],
    [(72, 0, 3)],
]
THEME_B = [
    [(67, 0, 1), (72, 1, 1), (76, 2, 1), (79, 3, 1)],
    [(81, 0, 1.5), (79, 1.5, .5), (76, 2, 2)],
    [(77, 0, 1), (76, 1, 1), (74, 2, 1), (72, 3, 1)],
    [(74, 0, 1.5), (76, 1.5, .5), (74, 2, 2)],
    [(76, 0, 1), (79, 1, 1), (84, 2, 1.5), (83, 3.5, .5)],
    [(81, 0, 1), (76, 1, 1), (81, 2, 1), (79, 3, 1)],
    [(77, 0, 1), (74, 1, 1), (71, 2, 1), (74, 3, 1)],
    [(72, 0, 3)],
]
PROG = ["C", "Am", "F", "G", "C", "Am", "FG", "C"]
CHORD = {"C": (60, 64, 67), "Am": (57, 60, 64), "F": (57, 60, 65), "G": (55, 59, 62)}
ROOT = {"C": 36, "Am": 33, "F": 29, "G": 31}

# General MIDI programs (0-based)
GLOCK, CELESTA, MUSICBOX, VIBES, MARIMBA, XYLO = 9, 8, 10, 11, 12, 13
NYLON, ACBASS, PIZZ, STRINGS, HARP, BRASS, WARMPAD = 24, 32, 45, 48, 46, 61, 89
DRUM_CH = 9
SHAKER, CLAP, TAMB, TRIANGLE, CRASH, SPLASH, SNARE, WOOD = 70, 39, 54, 81, 49, 55, 38, 76

# per-scene arrangement
STYLE = {
    "title":     dict(mel=GLOCK, dbl=MARIMBA, chords=NYLON, bass=PIZZ, shaker=True, clap=False, pad=None, harp=False, vel=1.0),
    "bunny":     dict(mel=GLOCK, dbl=MARIMBA, chords=NYLON, bass=PIZZ, shaker=True, clap=False, pad=None, harp=False, vel=1.0),
    "park":      dict(mel=XYLO, dbl=GLOCK, chords=NYLON, bass=PIZZ, shaker=True, clap=True, pad=None, harp=False, vel=1.0),
    "invisible": dict(mel=CELESTA, dbl=VIBES, chords=None, bass=PIZZ, shaker=False, clap=False, pad=WARMPAD, harp=True, vel=0.8),
    "hug":       dict(mel=MUSICBOX, dbl=None, chords=None, bass=ACBASS, shaker=False, clap=False, pad=STRINGS, harp=True, vel=0.8),
    "poof":      dict(mel=XYLO, dbl=GLOCK, chords=NYLON, bass=PIZZ, shaker=True, clap=True, pad=None, harp=False, vel=1.05),
    "family":    dict(mel=GLOCK, dbl=MARIMBA, chords=NYLON, bass=PIZZ, shaker=True, clap=True, pad=STRINGS, harp=False, vel=1.0),
    "end":       dict(mel=GLOCK, dbl=MARIMBA, chords=NYLON, bass=PIZZ, shaker=True, clap=False, pad=STRINGS, harp=False, vel=0.95),
}
CH_MEL, CH_DBL, CH_CHORD, CH_BASS, CH_PAD, CH_HARP, CH_BRASS, CH_FX = 0, 1, 2, 3, 4, 5, 6, 7


class Midi:
    """Collect events in seconds; write a type-0 file at a fixed 120 BPM."""

    def __init__(self):
        self.ev = []
        self.prog = {}

    def program(self, t, ch, prog):
        if self.prog.get(ch) != prog:
            self.ev.append((t, 0, mido.Message("program_change", channel=ch, program=prog)))
            self.prog[ch] = prog

    def cc(self, t, ch, ctrl, val):
        self.ev.append((t, 0, mido.Message("control_change", channel=ch, control=ctrl, value=int(val))))

    def note(self, t, ch, note, vel, dur):
        vel = int(max(1, min(127, vel)))
        self.ev.append((t, 2, mido.Message("note_on", channel=ch, note=note, velocity=vel)))
        self.ev.append((t + dur, 1, mido.Message("note_off", channel=ch, note=note, velocity=0)))

    def save(self, path):
        mid = mido.MidiFile(type=0, ticks_per_beat=480)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
        last = 0
        for t, _, msg in sorted(self.ev, key=lambda e: (e[0], e[1])):
            tick = int(round(max(t, 0) * 960))
            tr.append(msg.copy(time=tick - last))
            last = tick
        tr.append(mido.MetaMessage("end_of_track", time=960 * 3))
        mid.save(path)


def setup_mix(m):
    for ch, (vol, pan, rev) in {CH_MEL: (100, 64, 60), CH_DBL: (70, 84, 50), CH_CHORD: (72, 44, 40),
                                CH_BASS: (96, 64, 25), CH_PAD: (58, 64, 70), CH_HARP: (80, 54, 70),
                                CH_BRASS: (90, 64, 55), CH_FX: (100, 70, 70), DRUM_CH: (85, 64, 35)}.items():
        m.cc(0, ch, 7, vol)
        m.cc(0, ch, 10, pan)
        m.cc(0, ch, 91, rev)
        m.cc(0, ch, 93, 10)


def play_bars(m, t0, bar_len, n_bars, scene_at, start_bar=0, final_chord=False, stop_at=None):
    """Lay down n_bars of the tune starting at t0 (bars alternate A/B themes)."""
    beat = bar_len / 4
    for i in range(n_bars):
        b = start_bar + i
        tb = t0 + i * bar_len
        if stop_at is not None and tb >= stop_at:
            break
        st = STYLE[scene_at(tb)]
        theme = THEME_A if (b // 8) % 2 == 0 else THEME_B
        k = b % 8
        v = st["vel"]
        m.program(tb, CH_MEL, st["mel"])
        if st["dbl"] is not None:
            m.program(tb, CH_DBL, st["dbl"])
        if st["chords"] is not None:
            m.program(tb, CH_CHORD, st["chords"])
        m.program(tb, CH_BASS, st["bass"])
        if st["pad"] is not None:
            m.program(tb, CH_PAD, st["pad"])
        m.program(tb, CH_HARP, HARP)
        last = final_chord and i == n_bars - 1
        if last:  # "ta-da": everyone hits the final C chord
            m.program(tb, CH_BRASS, BRASS)
            for n in (60, 64, 67, 72):
                m.note(tb, CH_BRASS, n, 92, beat * 3.2)
                m.note(tb, CH_PAD, n, 70, beat * 4)
            m.note(tb, CH_MEL, 84, 110, beat * 3)
            for j, n in enumerate((72, 76, 79, 84, 88, 91, 96)):
                m.note(tb + j * beat * 0.12, CH_FX, n, 90 - j * 4, beat * 2)
            m.note(tb, CH_BASS, 36, 100, beat * 3)
            m.note(tb, DRUM_CH, CRASH, 105, beat * 2)
            continue
        # melody (+ softer double an octave down for warmth)
        for n, pos, ln in theme[k]:
            m.note(tb + pos * beat, CH_MEL, n, 96 * v, ln * beat * 0.95)
            if st["dbl"] is not None:
                m.note(tb + pos * beat, CH_DBL, n - 12, 60 * v, ln * beat * 0.9)
        chords = [PROG[k]] if PROG[k] != "FG" else ["F", "G"]
        for ci, ch_name in enumerate(chords):
            span = 4 // len(chords)
            off = ci * span
            root = ROOT[ch_name]
            # oom-pah bass: root on 1, fifth on 3
            m.note(tb + off * beat, CH_BASS, root, 92 * v, beat * 0.9)
            if span == 4:
                m.note(tb + 2 * beat, CH_BASS, root + 7, 80 * v, beat * 0.9)
            if st["chords"] is not None:  # guitar "chick" on 2 and 4
                for pos in ([1, 3] if span == 4 else [1]):
                    for j, n in enumerate(CHORD[ch_name]):
                        m.note(tb + (off + pos) * beat + j * 0.012, CH_CHORD, n, 62 * v, beat * 0.45)
            if st["pad"] is not None:
                for n in CHORD[ch_name]:
                    m.note(tb + off * beat, CH_PAD, n, 44 * v, span * beat * 0.98)
            if st["harp"]:  # rolling harp arpeggio
                arp = list(CHORD[ch_name]) + [CHORD[ch_name][0] + 12]
                for j in range(span * 2):
                    m.note(tb + (off + j * 0.5) * beat, CH_HARP, arp[j % 4] + 12, 50 * v, beat * 0.9)
        # percussion
        for e in range(8):
            if st["shaker"]:
                m.note(tb + e * beat / 2, DRUM_CH, SHAKER, (46 if e % 2 == 0 else 30) * v, beat * 0.3)
        if st["clap"]:
            for pos in (1, 3):
                m.note(tb + pos * beat, DRUM_CH, CLAP, 58 * v, beat * 0.3)
        if b % 4 == 0:
            m.note(tb, DRUM_CH, TRIANGLE, 52 * v, beat)


def render(mid_path, wav_path, gain=0.55):
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", str(gain), "-r", str(SR), "-F", wav_path, SF2, mid_path],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    a, sr = sf.read(wav_path, dtype="float32", always_2d=True)
    assert sr == SR
    return a


# ---------------------------------------------------------- synth effects
def env_exp(n, tau, attack=0.004):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / tau)


def sfx_boing(dur=0.42):
    t = np.arange(int(dur * SR)) / SR
    f = (330 + 260 * (1 - np.exp(-t * 9))) * (1 + 0.10 * np.sin(2 * np.pi * 17 * t) * np.exp(-t * 4))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env_exp(len(t), 0.16) * 0.55


def sfx_pop(dur=0.12):
    t = np.arange(int(dur * SR)) / SR
    f = 380 + 1500 * (t / dur) ** 0.6
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env_exp(len(t), 0.035, attack=0.002) * 0.7


def bandpass(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def sfx_whoosh(dur=0.55, seed=1, gain=0.18):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    seg = 1024  # sweep the band upward in short overlapping chunks
    for i in range(0, n, seg // 2):
        c = 500 + 2600 * (i / n)
        chunk = bandpass(x[i:i + seg], c * 0.6, min(c * 1.6, SR / 2 - 100))
        w = np.hanning(len(chunk))
        out[i:i + len(chunk)] += chunk * w
    t = np.arange(n) / n
    return out * np.sin(np.pi * t) ** 2 * gain


def sfx_poof(dur=0.9):
    rng = np.random.default_rng(5)
    n = int(dur * SR)
    noise = sosfilt(butter(2, 1800, btype="low", fs=SR, output="sos"), rng.normal(0, 1, n))
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (95 - 40 * t) * t)
    return (noise * env_exp(n, 0.22, 0.01) * 0.55 + thump * env_exp(n, 0.12) * 0.6)


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf):
        return
    x = x[: len(buf) - i]
    left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * gain * left * 1.414
    buf[i:i + len(x), 1] += x * gain * right * 1.414


def fit(a, n):
    out = np.zeros((n, 2), np.float32)
    out[: min(n, len(a))] = a[:n]
    return out


def sfx_click(seed=9):
    """Camera shutter: two short filtered clicks."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(0.16 * SR))
    for t0, g in ((0.0, 1.0), (0.07, 0.7)):
        n = int(0.025 * SR)
        burst = bandpass(rng.normal(0, 1, n), 1500, 7000) * env_exp(n, 0.006, 0.0005) * g
        i = int(t0 * SR)
        out[i:i + n] += burst
    return out * 0.8


def sfx_rain(dur, seed=12):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    x = bandpass(rng.normal(0, 1, n), 1200, 9000) * 0.12
    drops = np.zeros(n)
    for _ in range(int(dur * 40)):
        i = rng.integers(0, n - 2000)
        drops[i:i + 2000] += np.sin(2 * np.pi * rng.uniform(2500, 5000) * np.arange(2000) / SR) * env_exp(2000, 0.004) * 0.15
    k = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (0.12 * SR))
    return (x + drops) * k


def cartoon_sfx(ev, fx, synth):
    """Extra sounds for actions that only happen in the cartoon version."""
    fx.program(0, CH_BRASS, PIZZ)
    for j, n in enumerate((84, 88, 91, 96, 100)):             # idea! "ding"
        fx.note(ev["idea"] - 0.1 + j * 0.05, CH_FX, n, 92, 0.9)
    t0, t1 = ev["tiptoe"]                                     # tiptoeing to the bush
    for j, n in enumerate((67, 71, 74, 79, 74, 79)):
        fx.note(t0 + j * (t1 - t0) / 6, CH_BRASS, n, 72, 0.12)
    for t in ev["catches"]:                                   # ball caught
        fx.note(t, DRUM_CH, WOOD, 70, 0.1)
    t = ev["snow_on"]                                         # snowflake twinkles
    for j, n in enumerate((96, 91, 98, 93, 100, 95)):
        fx.note(t + 0.02 + j * 0.11, CH_PAD, n, 62, 0.5)
    fx.note(ev["wolf_dash"], DRUM_CH, WOOD, 60, 0.1)
    place(synth, sfx_pop(), ev["peekaboo"] - 0.18, 0.55, pan=0.4)    # he pops up
    place(synth, sfx_pop(), ev["rain_on"] - 0.08, 0.4, pan=-0.2)     # umbrella opens
    place(synth, sfx_rain(ev["snow_on"] - ev["rain_on"] + 0.15), ev["rain_on"] - 0.05, 0.7)
    place(synth, sfx_click(), ev["photo"], 0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cartoon", action="store_true", help="add the cartoon version's extra sound effects")
    args = ap.parse_args()
    tl = timeline.load()
    T = tl["duration_video"]
    N = int(T * SR)
    scene_at = timeline.scene_at(tl)
    ev = tl["events"]

    # ---- music part A: start to "And suddenly..."
    bar_a = 4 * 60 / 104
    stop_a = ev["music_stop"]
    a = Midi()
    setup_mix(a)
    play_bars(a, 0.0, bar_a, int(stop_a / bar_a) + 2, scene_at, stop_at=stop_a + 0.6)
    a.save(os.path.join(BUILD, "music_a.mid"))
    music_a = render(os.path.join(BUILD, "music_a.mid"), os.path.join(BUILD, "music_a.wav"))

    # ---- music part B: POOF to the final "ta-da" chord
    t_b, t_final = ev["poof"], ev["final_chord"]
    n_b = 15
    bar_b = (t_final - t_b) / n_b
    b = Midi()
    setup_mix(b)
    play_bars(b, 0.0, bar_b, n_b + 1, lambda t: scene_at(t + t_b), final_chord=True)
    b.save(os.path.join(BUILD, "music_b.mid"))
    music_b = render(os.path.join(BUILD, "music_b.mid"), os.path.join(BUILD, "music_b.wav"))

    # ---- MIDI sound effects on the words
    fx = Midi()
    setup_mix(fx)
    fx.program(0, CH_FX, GLOCK)
    fx.program(0, CH_HARP, HARP)
    fx.program(0, CH_PAD, CELESTA)
    for j, n in enumerate((84, 88, 91, 96)):                 # opening sparkle
        fx.note(0.02 + j * 0.07, CH_FX, n, 80, 0.6)
    for k, (t, n) in enumerate(zip(ev["dog_names"], (84, 86, 88, 91, 93))):
        fx.note(t + 0.02, CH_FX, n, 70, 0.4)                 # a bell per dog
    t = ev["peekaboo"]
    for j, n in enumerate((79, 84, 88, 91, 96, 100)):       # peek-a-boo twinkle
        fx.note(t + 0.05 + j * 0.06, CH_PAD, n, 78, 0.7)
    for t in ev["hugs"]:                                    # harp glissando
        for j, n in enumerate((72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91)):
            fx.note(t - 0.15 + j * 0.035, CH_HARP, n, 70, 0.9)
    t0, t1 = ev["drumroll"]                                 # building drum roll
    t = t0
    while t < t1 - 0.02:
        p = (t - t0) / (t1 - t0)
        fx.note(t, DRUM_CH, SNARE, 26 + 84 * p ** 1.5, 0.05)
        t += 0.045
    fx.note(ev["poof"], DRUM_CH, CRASH, 120, 2.0)
    fx.note(ev["poof"], DRUM_CH, SPLASH, 90, 1.0)
    for j, n in enumerate((96, 93, 91, 88, 84, 81, 79, 76)):  # sparkle cascade
        fx.note(ev["poof"] + 0.08 + j * 0.05, CH_FX, n, 84, 0.6)
    fx.note(ev["family"], DRUM_CH, TRIANGLE, 70, 1.5)
    t = ev["the_end"]
    for j, n in enumerate((72, 76, 79, 84, 88)):
        fx.note(t + j * 0.06, CH_FX, n, 86, 0.8)
    fx.note(t, DRUM_CH, SPLASH, 70, 1.0)
    synth = np.zeros((N, 2), np.float32)
    if args.cartoon:
        cartoon_sfx(ev, fx, synth)
    fx.save(os.path.join(BUILD, "fx.mid"))
    fx_audio = render(os.path.join(BUILD, "fx.mid"), os.path.join(BUILD, "fx.wav"))

    # ---- synth sound effects
    for j, t in enumerate(ev["hops"]):
        place(synth, sfx_boing() * (1 + 0.1 * j), t - 0.03, 0.55, pan=-0.2 + 0.2 * j)
    for j, t in enumerate(ev["dog_names"]):
        place(synth, sfx_pop(), t - 0.04, 0.5, pan=[-0.5, 0.4, -0.2, 0.5, 0.0][j])
    for t in ev["transitions"]:
        place(synth, sfx_whoosh(seed=int(t * 10)), t - 0.3, 1.0)
    place(synth, sfx_poof(), ev["poof"] - 0.02, 0.6)

    # ---- mix
    narr, sr = sf.read(os.path.join(BUILD, "narration.wav"), dtype="float32")
    assert sr == SR
    voice = fit(np.stack([narr, narr], 1), N)

    music = np.zeros((N, 2), np.float32)
    ma = fit(music_a, N)
    fade = np.clip((stop_a - np.arange(N) / SR) / 0.6, 0, 1).astype(np.float32)  # out on "suddenly"
    music += ma * fade[:, None]
    ib = int(t_b * SR)
    mb = music_b[: N - ib]
    music[ib:ib + len(mb)] += mb
    tail = np.clip((T - np.arange(N) / SR) / 0.8, 0, 1).astype(np.float32)        # tidy ending
    music *= tail[:, None]

    # duck the music under the voice
    hop = 480
    rms = np.sqrt(np.convolve(narr ** 2, np.ones(hop) / hop, mode="same"))[: N]
    rms = np.pad(rms, (0, max(0, N - len(rms))))
    active = (rms > 0.02).astype(np.float32)
    duck = np.empty_like(active)
    g = 0.0
    a_up, a_dn = np.exp(-1 / (0.03 * SR)), np.exp(-1 / (0.45 * SR))
    for i in range(0, N, hop):  # block-wise attack/release follower
        tgt = active[i:i + hop].max()
        coef = a_up if tgt > g else a_dn
        g = tgt + (g - tgt) * coef ** hop
        duck[i:i + hop] = g
    music_gain = 1.0 - 0.5 * duck

    def rms_of(x):
        return float(np.sqrt(np.mean(x ** 2) + 1e-12))

    speech = voice[active > 0]
    m_ref = rms_of(music[np.abs(music).sum(1) > 1e-4])
    music *= (rms_of(speech) * 0.42 / m_ref) * music_gain[:, None]
    fx_audio = fit(fx_audio, N) * (rms_of(speech) * 0.5 / m_ref)
    mix = voice + music + fx_audio + synth * 0.8
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    tag = "_cartoon" if args.cartoon else ""
    raw = os.path.join(BUILD, f"mix{tag}_raw.wav")
    sf.write(raw, mix, SR, subtype="PCM_24")

    # loudness: -14 LUFS, true peak -1.5 dB (typical for Reels/TikTok/Shorts)
    out = os.path.join(BUILD, f"mix{tag}.wav")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    js = json.loads(p.stderr[p.stderr.rindex("{"):])
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
                    f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
                    f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:"
                    f"offset={js['target_offset']},aresample={SR}",
                    "-c:a", "pcm_s16le", out], check=True)
    print("mix written:", out, "input loudness", js["input_i"], "LUFS")


if __name__ == "__main__":
    main()
