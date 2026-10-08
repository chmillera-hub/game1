"""Lounge jazz, a tender piano confession, a chaos-mode banger and all the SFX."""
import json, math, os, random, subprocess, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import Timeline, BUILD
from world import Room
from synth import *


def chord(root, kind):
    iv = {"maj7": (0, 4, 7, 11), "min7": (0, 3, 7, 10), "dom7": (0, 4, 7, 10), "maj9": (0, 4, 7, 14),
          "min9": (0, 3, 7, 14), "6": (0, 4, 7, 9), "maj": (0, 4, 7), "sus4": (0, 5, 7)}[kind]
    return [root + i for i in iv]


def lounge(tr, t0, t1):
    beat = 60 / 92
    prog = [(55, "min7"), (48, "dom7"), (53, "maj7"), (50, "min7")]      # Gm7 C7 Fmaj7 Dm7
    t, bar = t0, 0
    while t < t1:
        root, kind = prog[bar % 4]
        notes = chord(root, kind)
        for j, m in enumerate(notes):
            tr.add(t + beat * 0.0 + j * 0.02, epiano(mtof(m + 12 if m < 55 else m), beat * 1.6, 0.32), pan=-0.2 + 0.1 * j)
            tr.add(t + beat * 2.5 + j * 0.02, epiano(mtof(m + 12 if m < 55 else m), beat * 1.0, 0.22), pan=-0.2 + 0.1 * j)
        walk = [root - 12, root - 12 + 4, root - 12 + 7, root - 12 + 9]
        for b in range(4):
            tr.add(t + b * beat, bass(mtof(walk[b]), beat * 0.9, 0.45))
            tr.add(t + b * beat, snare(0.03, 0.18, 2000, 7000), pan=0.3)
            tr.add(t + b * beat + beat * 0.66, hat(0.04), pan=0.4)
        t += 4 * beat
        bar += 1


def tender(tr, t0, t1):
    beat = 60 / 66
    prog = [(53, "maj9"), (50, "min9"), (46, "maj7"), (48, "sus4")]
    t, bar = t0, 0
    while t < t1:
        root, kind = prog[bar % 4]
        notes = chord(root, kind)
        tr.add(t, piano(mtof(root - 12), beat * 3.5, 0.4))
        for e, m in enumerate((notes[0], notes[1], notes[2], notes[3] if len(notes) > 3 else notes[1] + 12)):
            tr.add(t + e * beat, piano(mtof(m + 12), beat * 1.6, 0.26), pan=0.15)
        for m in notes[:3]:
            tr.add(t, strings(mtof(m), beat * 4, 0.07, 1.0, 1.6), pan=-0.2)
        t += 4 * beat
        bar += 1


def banger(tr, t0, t1):
    beat = 60 / 128
    prog = [(57, "min"), (53, "maj"), (48, "maj"), (55, "maj")]
    t, bar = t0, 0
    while t < t1:
        root, kind = prog[bar % 4]
        notes = chord(root, kind)
        for b in range(4):
            tr.add(t + b * beat, kick(0.9))
            if b % 2:
                tr.add(t + b * beat, snare(0.35, 0.18, 1200, 8000))
            for h in range(2):
                tr.add(t + b * beat + h * beat / 2 + beat / 4, hat(0.12), pan=0.3)
            tr.add(t + b * beat + beat / 2, bass(mtof(root - 24), beat * 0.4, 0.6))
        for e in range(8):
            m = notes[[0, 1, 2, 1, 2, 0, 2, 1][e]] + 12
            tr.add(t + e * beat / 2, marimba(mtof(m), 0.6), pan=-0.3)
        tr.add(t, glock(mtof(notes[2] + 24), 0.4, 0.6), pan=0.3)
        t += 4 * beat
        bar += 1


def main():
    tl = Timeline()
    room = Room(tl)
    T, E, Wd = tl.s, tl.e, tl.wfind
    total = tl.total

    dia = Track(total)
    activity = np.zeros(dia.n)
    pans = {"CFO": -0.2, "CEO": 0.0, "TYLER": 0.2, "PAM": 0.35, "KID": -0.1, "CYAN": 0.3, "GOLD": 0.4, "JESUS": -0.35, "DIR": 0.0}
    for L in tl.spoken:
        a = np.load(f"{BUILD}/voice/{L['id']}.npy").astype(np.float64)
        who = L["who"]
        if who == "DIR":
            a = bp(a, 180, 6500) * 1.2       # a little TV-speaker colour
            x = verb(a, 0.10, room=True)
        elif who in ("CYAN", "GOLD", "JESUS"):
            x = verb(a, 0.2)
        else:
            x = verb(a, 0.12, room=True)
        p = pans.get(who, 0)
        x = np.stack([x[0] * (1 - max(0, p)), x[1] * (1 + min(0, p))])
        dia.add(L["start"], x, 0.95)
        i0 = int(L["start"] * SR)
        activity[i0:i0 + len(a)] = 1
    k = int(0.3 * SR)
    duck = np.convolve(activity, np.ones(k) / k, mode="same")

    mus = Track(total)
    lounge(mus, T("d1") - 0.4, T("p3"))
    gate(mus, [(T("d1") - 0.4, T("d2") + 0.2), (T("t2") - 0.1, T("p3") - 0.2)], total, 0.12)
    ten = Track(total)
    tender(ten, T("p3") - 0.2, E("t7") + 1.5)
    gate(ten, [(T("p3") - 0.2, E("t7") + 1.0)], total, 0.5)
    ban = Track(total)
    banger(ban, room.chaos0 - 0.05, room.door0)
    gate(ban, [(room.chaos0 - 0.05, room.door0)], total, 0.03)
    out = Track(total)
    lounge(out, T("d10") - 0.2, total)
    gate(out, [(T("d10") - 0.2, total)], total, 0.5)
    choir_t = Track(total)
    for m in (50, 57, 62, 66, 69):
        choir_t.add(room.door0 + 0.3, choir(mtof(m), 3.2, 0.12, 0.6, 1.6))
    music = mus.buf * 0.42 + ten.buf * 0.55 + ban.buf * 0.5 + out.buf * 0.4 + choir_t.buf * 0.6
    music = music * (1 - 0.55 * duck[None, :])
    ml = fftconvolve(music[0], IR_L)[: music.shape[1]]
    mr = fftconvolve(music[1], IR_R)[: music.shape[1]]
    music = music + 0.18 * np.stack([ml, mr])

    fx = Track(total)
    # CRT power-on and flicker
    tt = tvec(0.6)
    fx.add(0.5, np.sin(2 * np.pi * 60 * tt) * 0.15 * np.exp(-tt / 0.3) + hp(noise(0.6), 6000) * 0.05 * np.exp(-tt / 0.2), 1.0)
    for q in range(5):
        fx.add(room.boot_on + q * 0.11, sfx_click(), 0.7)
    for i, ln in enumerate(range(4)):
        for q in range(8):
            fx.add(i * 0.25 + q * 0.03, sfx_click(), 0.15)
    for q in range(3):
        fx.add(T("hush") + 0.4 + q * 0.6, sfx_cricket(), 1.0, pan=0.4)
    fx.add(room.pen_drop + 0.45, glock(2600, 0.3, 0.15), 0.8)
    fx.add(room.pen_drop + 0.6, glock(2900, 0.2, 0.1), 0.6)
    for w in ("Number", "Number"):
        pass
    fx.add(T("d3") + 2.5, sfx_pop(), 0.5)
    fx.add(T("d4"), sfx_pop(), 0.5)
    fx.add(Wd("d5", "audited"), sfx_thump(90, 0.3, 0.7), 0.8)
    fx.add(Wd("d5", "fine"), sfx_ding(1568), 0.5)
    fx.add(T("m3") + 0.4, glock(3200, 0.25, 0.4), 0.7)
    fx.add(Wd("t6", "Draw") - 0.2, sfx_pop(), 0.5)
    fx.add(Wd("k1", "messy") - 0.2, sfx_pop(), 0.5)
    fx.add(T("g2"), sfx_pop(), 0.5)
    # the blue glitch
    for tb in (T("c5") + 1.5, T("c7") - 0.3):
        fx.add(tb, sfx_scratch() * 0.5 + snare(0.2, 0.3, 300, 6000), 0.7)
    fx.add(T("think") + 0.2, sfx_tick(), 0.3)
    fx.add(E("d9") - 0.1, sfx_whoosh(0.8, True), 0.7)
    fx.add(room.chaos0 + 0.62, sfx_thump(65, 0.4, 0.9), 0.8)
    fx.add(room.chaos0 + 1.2, sfx_kaching(), 0.5)
    r = random.Random(4)
    for q in range(12):
        fx.add(room.chaos0 + r.uniform(0, room.door0 - room.chaos0), sfx_chirp(), 0.6, pan=r.uniform(-0.6, 0.6))
    fx.add(room.door0 - 0.1, sfx_scratch(), 1.0)
    fx.add(room.door0 + 0.1, sfx_creak(), 0.8, pan=-0.5)
    for q in range(4):
        fx.add(room.door0 + 0.4 + q * 0.32, sfx_step(), 0.7, pan=-0.4)
    # applause at the bow
    ap = np.zeros(int(3.0 * SR))
    for q in range(260):
        i = int(r.uniform(0, 2.6) * SR)
        c = bp(noise(0.03), 900, 5000) * np.exp(-tvec(0.03) / 0.006)
        ap[i:i + len(c)] += c[: len(ap) - i] * r.uniform(0.3, 1.0)
    ap *= np.minimum(1, np.linspace(0, 3, len(ap))) * np.linspace(1, 0.2, len(ap))
    fx.add(room.bow - 0.2, ap * 0.5, 1.0)
    # CRT power-off
    tt = tvec(0.5)
    fx.add(room.tv_off, np.sin(2 * np.pi * np.cumsum(2000 * np.exp(-tt / 0.08) + 80) / SR) * 0.2 * np.exp(-tt / 0.15), 1.0)
    # tiny bleep stays in the voice track

    mixb = dia.buf + music + fx.buf
    n = int(total * SR)
    mixb = mixb[:, :n]
    f = int(0.8 * SR)
    mixb[:, -f:] *= np.linspace(1, 0, f)
    mixb /= max(1e-6, np.abs(mixb).max()) / 0.9
    raw = f"{BUILD}/mix_raw.wav"
    with wave.open(raw, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mixb.T * 32767).astype(np.int16).tobytes())
    o = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    js = json.loads(o[o.rindex("{"):o.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:"
          f"measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}:"
          f"measured_thresh={js['input_thresh']}:offset={js['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-af", af, "-ar", "44100",
                    f"{BUILD}/mix.wav"], check=True)
    print("wrote", f"{BUILD}/mix.wav", js["input_i"])


if __name__ == "__main__":
    main()
