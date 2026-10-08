"""Ambient score, sound effects and dialogue mix for The Long Dream.

Writes build/mix.wav (stereo 44.1 kHz, loudness-normalized to -14 LUFS).
"""
import json, math, os, random, subprocess, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import Timeline, BUILD, prog
from synth import *


def chord(root, kind):
    iv = {"maj7": (0, 4, 7, 11), "min7": (0, 3, 7, 10), "maj9": (0, 4, 7, 14), "min9": (0, 3, 7, 14),
          "6": (0, 4, 7, 9), "sus2": (0, 2, 7), "maj": (0, 4, 7), "min": (0, 3, 7), "sus4": (0, 5, 7)}[kind]
    return [root + i for i in iv]


MAJOR = [(53, "maj9"), (50, "min9"), (46, "maj7"), (48, "6")]          # F  Dm  Bb  C
MINOR = [(50, "min9"), (46, "maj7"), (43, "min7"), (45, "sus4")]      # Dm Bb Gm Asus
STORY = [(53, "maj9"), (48, "sus2"), (50, "min7"), (46, "maj7"), (53, "maj"), (43, "min7"), (48, "sus4"), (53, "maj9")]


def main():
    tl = Timeline()
    T, E, Wd = tl.s, tl.e, tl.wfind
    total = tl.total
    end_t = E("f9") + 2.4

    # ---------------------------------------------------------------- dialogue
    dia = Track(total)
    activity = np.zeros(dia.n)
    for L in tl.spoken:
        a = np.load(f"{BUILD}/voice/{L['id']}.npy").astype(np.float64)
        x = verb(a, 0.22)
        p = -0.12 if L["who"] == "CYAN" else 0.12
        x = np.stack([x[0] * (1 - max(0, p)), x[1] * (1 + min(0, p))])
        dia.add(L["start"], x, 0.95)
        i0 = int(L["start"] * SR)
        activity[i0:i0 + len(a)] = 1
    k = int(0.3 * SR)
    duck = np.convolve(activity, np.ones(k) / k, mode="same")

    # ---------------------------------------------------------------- score
    mus = Track(total)
    beat = 1.0
    bar = 4 * beat
    t = 0.2
    n = 0
    while t < end_t + 2:
        if t < T("l1") - 0.5:
            sec = "watch" if t < T("d1") - 0.5 else ("dream" if t < T("r1") else "watch")
        elif t < T("t1") - 0.5:
            sec = "sorrow"
        elif t < T("w1") - 0.5:
            sec = "decide"
        elif t < T("s1") - 0.5:
            sec = "wake"
        elif t < T("f1") - 0.5:
            sec = "story"
        else:
            sec = "finale"
        prog_ = {"watch": MAJOR, "dream": MAJOR, "sorrow": MINOR, "decide": MINOR, "wake": MAJOR,
                 "story": STORY, "finale": STORY}[sec]
        root, kind = prog_[n % len(prog_)]
        notes = chord(root, kind)
        lvl = {"watch": 0.10, "dream": 0.11, "sorrow": 0.11, "decide": 0.08, "wake": 0.12, "story": 0.12, "finale": 0.15}[sec]
        for m in notes:
            mus.add(t, pad(mtof(m), bar, lvl, 1.4, 2.0), pan=random.Random(m).uniform(-0.4, 0.4))
        mus.add(t, pad(mtof(root - 12), bar, lvl * 0.9, 1.4, 2.0))
        if sec in ("watch", "decide") and n % 2 == 0:
            for j, m in enumerate((notes[-1] + 12, notes[1] + 12)):
                mus.add(t + 1.5 + j * 1.25, piano(mtof(m), 1.4, 0.22), pan=0.25)
        if sec in ("dream", "story", "finale", "wake"):
            arp = notes + [notes[1] + 12, notes[2] + 12]
            for e in range(8):
                m = arp[[0, 1, 2, 3, 2, 1, 3, 4][e] % len(arp)] + 12
                mus.add(t + e * beat / 2, piano(mtof(m), 0.8, 0.18 if sec != "finale" else 0.24), pan=0.15)
        if sec in ("dream", "finale"):
            for e in (0, 3, 6):
                mus.add(t + e * beat / 2, glock(mtof(notes[e % len(notes)] + 24), 0.22, 1.4), pan=-0.3)
        if sec in ("sorrow", "wake", "story", "finale"):
            sv = {"sorrow": 0.10, "wake": 0.09, "story": 0.10, "finale": 0.16}[sec]
            for m in notes[:3]:
                mus.add(t, strings(mtof(m), bar, sv, 0.9, 1.6), pan=-0.2)
            mus.add(t, strings(mtof(root - 12), bar, sv, 0.9, 1.6))
        if sec in ("story", "finale") and (sec == "finale" or t > T("s5")):
            for m in notes[:3]:
                mus.add(t, choir(mtof(m + 12), bar, 0.08 if sec == "story" else 0.13, 1.2, 1.8), pan=0.2)
        t += bar
        n += 1
    # final resolving chord
    for m in (41, 53, 57, 60, 65, 69, 72):
        mus.add(end_t - 1.6, strings(mtof(m), 4.0, 0.12, 1.0, 2.5))
    for j, m in enumerate((77, 81, 84, 89)):
        mus.add(Wd("f9", "love") + 0.2 + j * 0.3, glock(mtof(m), 0.35, 2.4), pan=-0.3 + j * 0.2)
    # dip the music under the glitches
    g = np.ones(mus.n)
    for L in tl.spoken:
        for (kind, a, b) in L.get("tokens", []):
            if kind == "GLITCH":
                g[int(a * SR):int(b * SR)] = 0.15
    k = int(0.05 * SR)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    mus.buf *= g

    # hold music (phone-filtered bossa on marimba) during the hold-music shot
    hold = Track(total)
    h0, h1 = Wd("l3", "hold") - 0.4, T("l4") + 0.4
    tt, j = h0, 0
    seq = [72, 76, 79, 76, 74, 77, 81, 77]
    while tt < h1:
        hold.add(tt, marimba(mtof(seq[j % 8]), 0.6))
        if j % 4 == 0:
            hold.add(tt, bass(mtof(seq[j % 8] - 24), 0.5, 0.5))
        tt += 0.27
        j += 1
    hold.buf = np.stack([bp(hold.buf[0], 400, 3200, 4), bp(hold.buf[1], 400, 3200, 4)]) * 0.7
    gate(hold, [(h0, h1)], total, 0.15)

    music = mus.buf * 0.9
    music = music * (1 - 0.5 * duck[None, :])
    ml = fftconvolve(music[0], IR_L)[: music.shape[1]]
    mr = fftconvolve(music[1], IR_R)[: music.shape[1]]
    music = music + 0.25 * np.stack([ml, mr]) + hold.buf * (1 - 0.4 * duck[None, :])

    # ---------------------------------------------------------------- sfx
    fx = Track(total)
    fx.add(T("a3") - 0.05, sfx_pop(), 0.6)
    fx.add(Wd("a4", "PDF") - 0.7, sfx_click(), 0.6)
    L5 = tl.by_id["a5"]
    for w in L5["words"]:
        for q in range(3):
            fx.add(L5["start"] + w[1] + q * 0.06, sfx_click(), 0.25, pan=0.2)
    for name in (("d2", "sunlight"), ("d2", "fire"), ("d2", "small"), ("d2", "password"), ("d3", "hunted"),
                 ("d3", "shelter")):
        fx.add(Wd(*name) - 0.15, sfx_pop(), 0.5)
    fx.add(Wd("d4", "ZIP") - 0.45, sfx_pop(), 0.5)
    fx.add(T("r2"), sfx_shimmer(2.0), 0.5)
    # black sun wind
    wind = lp(noise(E("l3") - T("l3") + 1.0), 500) * 0.05
    fx.add(T("l3") - 0.1, wind * np.sin(np.linspace(0, math.pi, len(wind))), 1.0)
    fx.add(Wd("l2", "official") - 0.2, sfx_ding(1568), 0.5)
    fx.add(Wd("l5", "appeal") - 0.2, sfx_ding(1318), 0.6)
    s = T("t3")
    while s < Wd("t3", "session") - 0.2:
        fx.add(s, sfx_tick(), 0.4)
        s += 0.5
    fx.add(T("t5") + 0.1, sfx_whoosh(2.4, True), 0.4)
    for w in ("breath", "another"):
        b = Wd("w2", w)
        br = bp(noise(1.2), 300, 2500) * np.sin(np.linspace(0, math.pi, int(1.2 * SR))) ** 2 * 0.25
        fx.add(b - 0.1, br, 0.8)
    for w in ("mountain", "post", "gods", "IRS"):
        fx.add(Wd("w3", w) - 0.2, sfx_whoosh(0.35, True), 0.35)
    fx.add(Wd("s2", "woman") - 0.6, sfx_shimmer(2.0), 0.45)
    fx.add(Wd("s2", "birth") - 0.2, sfx_pop(), 0.6)
    fx.add(Wd("s3", "Social") - 0.2, sfx_pop(), 0.6)
    fx.add(Wd("s3", "Eligible") - 0.2, sfx_pop(), 0.6)
    fx.add(T("s4"), sfx_shimmer(2.5), 0.4)
    # phone that actually rang
    rr = Wd("s5", "rang") - 0.3
    for q in range(2):
        tt = tvec(0.4)
        ring = (np.sin(2 * np.pi * 440 * tt) + np.sin(2 * np.pi * 480 * tt)) * 0.15 * (np.sin(2 * np.pi * 20 * tt) > 0)
        fx.add(rr + q * 0.55, ring, 0.8)
    r = random.Random(3)
    t404 = Wd("s5", "Those") - 0.1
    for q in range(26):
        fx.add(t404 + r.uniform(0, 1.0), glock(r.uniform(2500, 5000), 0.18, 0.12), 0.6, pan=r.uniform(-0.7, 0.7))
    fx.add(Wd("s6", "two") - 0.1, sfx_pop(), 0.6)
    fx.add(Wd("s6", "two") + 0.15, sfx_pop(), 0.6)
    for q in range(10):
        fx.add(T("s7") + q * 0.7 + r.uniform(0, 0.3), sfx_chirp(), 0.6, pan=r.uniform(-0.6, 0.6))
    snow = lp(noise(E("s8") - T("s8") + 1.0), 700) * 0.03
    fx.add(T("s8") - 0.1, snow * np.sin(np.linspace(0, math.pi, len(snow))), 1.0)
    for q in range(4):
        fx.add(T("s8") + q * 1.6, glock(mtof(88 + (q % 2) * 3), 0.2, 1.5), 0.6, pan=0.4)
    fx.add(Wd("f9", "love") - 0.15, sfx_shimmer(2.2), 0.6)

    mixb = dia.buf + music + fx.buf
    n = int(total * SR)
    mixb = mixb[:, :n]
    f = int(1.2 * SR)
    mixb[:, -f:] *= np.linspace(1, 0, f)
    mixb /= max(1e-6, np.abs(mixb).max()) / 0.9
    raw = f"{BUILD}/mix_raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mixb.T * 32767).astype(np.int16).tobytes())
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    js = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-af", af, "-ar", "44100",
                    f"{BUILD}/mix.wav"], check=True)
    print("wrote", f"{BUILD}/mix.wav", js["input_i"])


if __name__ == "__main__":
    main()
