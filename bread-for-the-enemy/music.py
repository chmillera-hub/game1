"""
Original score for BREAD FOR THE ENEMY, written as MIDI events on an absolute
clock (seconds) and rendered with FluidSynth + the FluidR3 General MIDI soundfont.

Central idea: one hymn-like "love motif" (D major) that travels through the film:
  flute at the supper -> English horn in D minor under Paul's guilt -> French horn
  when Jesus appears on the Damascus road -> oboe when Asher breaks the bread ->
  full orchestra and choir at the Romans 8 climax -> flute at dawn.
"""
import json
import os
import subprocess
import sys

import mido
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audiofx  # noqa: E402

SF2 = os.environ.get("BFE_SF2", "/usr/share/sounds/sf2/FluidR3_GM.sf2")
TPS = 960  # ticks per second (tempo fixed at 60 bpm, 960 ticks per beat)

PROG = {0: 48, 1: 49, 2: 42, 3: 43, 4: 46, 5: 0, 6: 73, 7: 68, 8: 60, 10: 52, 11: 47, 12: 44, 13: 119, 14: 69, 15: 53}
NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def P(n):
    """'F#4' -> midi number."""
    if isinstance(n, int):
        return n
    name = n[0]
    acc = 0
    i = 1
    while i < len(n) and n[i] in "#b":
        acc += 1 if n[i] == "#" else -1
        i += 1
    octv = int(n[i:])
    return 12 * (octv + 1) + NAMES[name] + acc


class Score:
    def __init__(self):
        self.ev = []  # (time, order, msg)

    def note(self, ch, pitch, t, dur, vel=64):
        p = P(pitch)
        self.ev.append((t, 1, mido.Message("note_on", channel=ch, note=p, velocity=int(max(1, min(127, vel))))))
        self.ev.append((t + dur, 0, mido.Message("note_off", channel=ch, note=p, velocity=0)))

    def chord(self, ch, pitches, t, dur, vel=60, roll=0.0):
        for i, p in enumerate(pitches):
            self.note(ch, p, t + i * roll, dur - i * roll, vel)

    def cc(self, ch, num, val, t):
        self.ev.append((t, 0, mido.Message("control_change", channel=ch, control=num, value=int(max(0, min(127, val))))))

    def ramp(self, ch, v0, v1, t0, t1, num=11, steps=None):
        steps = steps or max(2, int((t1 - t0) * 12))
        for i in range(steps + 1):
            k = i / steps
            self.cc(ch, num, v0 + (v1 - v0) * k, t0 + (t1 - t0) * k)

    def melody(self, ch, notes, t0, beat, vel=64, legato=0.98, transpose=0, swell=True):
        t = t0
        for i, (p, b) in enumerate(notes):
            if p is not None:
                v = vel + (6 if swell and b >= 2 else 0)
                self.note(ch, P(p) + transpose, t, b * beat * legato, v)
            t += b * beat
        return t

    def arp(self, ch, pitches, t0, t1, step, vel=50, pattern=None):
        pattern = pattern or [0, 1, 2, 3, 2, 1]
        t, i = t0, 0
        while t < t1 - 0.01:
            p = pitches[pattern[i % len(pattern)] % len(pitches)]
            self.note(ch, p, t, step * 2.5, vel + (8 if i % len(pattern) == 0 else 0))
            t += step
            i += 1

    def silence(self, t):
        for ch in PROG:
            self.ev.append((t, 0, mido.Message("control_change", channel=ch, control=123, value=0)))

    def write(self, path, end):
        mid = mido.MidiFile(ticks_per_beat=TPS)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))
        for ch, pg in PROG.items():
            tr.append(mido.Message("program_change", channel=ch, program=pg, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=7, value=100, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=11, value=100, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=70, time=0))
        ev = sorted(self.ev, key=lambda e: (e[0], e[1]))
        last = 0
        for t, _, msg in ev:
            tick = int(round(max(0, t) * TPS))
            msg = msg.copy(time=max(0, tick - last))
            tr.append(msg)
            last = max(last, tick)
        tr.append(mido.MetaMessage("end_of_track", time=int(end * TPS) - last if end * TPS > last else 0))
        mid.save(path)


# the love motif (beats). Phrase A answers on E (half cadence); phrase B resolves to D.
LOVE_A = [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("B4", 1), ("A4", 1), ("F#4", 2), ("G4", 1.5), ("F#4", 0.5), ("E4", 1), ("D4", 1), ("E4", 4)]
LOVE_B = [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("D5", 1), ("C#5", 1), ("B4", 2), ("A4", 1), ("G4", 1), ("F#4", 1), ("E4", 1), ("D4", 4)]
LOVE_A_MIN = [("F4", 1.5), ("G4", 0.5), ("A4", 2), ("Bb4", 1), ("A4", 1), ("F4", 2), ("G4", 1.5), ("F4", 0.5), ("E4", 1), ("D4", 1), ("E4", 4)]

CH = dict(D=["D3", "A3", "D4", "F#4"], Bm=["B2", "F#3", "B3", "D4"], G=["G2", "D3", "B3", "D4"], A=["A2", "E3", "A3", "C#4"],
          Em=["E3", "B3", "E4", "G4"], DF=["F#2", "D3", "A3", "D4"], Dm=["D3", "A3", "D4", "F4"], Bb=["Bb2", "F3", "Bb3", "D4"],
          F=["F2", "C3", "A3", "C4"], C=["C3", "G3", "C4", "E4"], Gm=["G2", "D3", "G3", "Bb3"], Am=["A2", "E3", "A3", "C4"],
          A7=["A2", "E3", "G3", "C#4"])
BASS = dict(D="D2", Bm="B1", G="G1", A="A1", Em="E2", DF="F#1", Dm="D2", Bb="Bb1", F="F1", C="C2", Gm="G1", Am="A1", A7="A1")


def pad(s, ch, prog, t0, bar, vel=52, bass_ch=3, bass_vel=48, harp=None, harp_vel=44):
    t = t0
    for name in prog:
        s.chord(ch, CH[name], t, bar * 1.02, vel)
        if bass_ch is not None:
            s.note(bass_ch, BASS[name], t, bar * 1.0, bass_vel)
        if harp is not None:
            ps = [CH[name][0], CH[name][1], CH[name][2], CH[name][3]]
            ps = [P(p) + 12 for p in ps]
            s.arp(4, ps, t, t + bar, harp, harp_vel, pattern=[0, 1, 2, 3, 2, 1])
        t += bar
    return t


def compose(tl):
    s = Score()
    cue = {m["cue"]: m["t"] for m in tl["music"]}
    lines = tl["lines"]

    def line_t(who, text_start):
        for ln in lines:
            if ln["who"] == who and ln["text"].startswith(text_start):
                return ln["start"]
        raise KeyError(text_start)

    # ------------------------------------------------------------- PROLOGUE (D major)
    bar = 4 * (60 / 72)
    s.ramp(0, 70, 92, 0, 6)
    pad(s, 0, ["D", "Bm", "G", "A", "DF", "G"], 0.0, bar, vel=50, harp=bar / 8, harp_vel=40)
    s.chord(0, ["E3", "B3", "D4", "G4"], 6 * bar, bar * 0.5, 44)
    s.chord(0, CH["A"], 6.5 * bar, bar * 0.62, 42)
    # flute answers between the spoken lines
    s.melody(6, [("A4", 0.5), ("D5", 1.5), ("C#5", 0.5), ("B4", 0.5), ("A4", 2)], 9.75, 60 / 72, vel=48)
    s.melody(14, [("G4", 1.5), ("F#4", 0.5), ("E4", 1), ("D4", 1), ("E4", 3)], 19.9, 60 / 72, vel=50)

    # ------------------------------------------------------------- STREET (D minor, dark)
    t0 = cue["street"]
    s.ramp(1, 60, 85, t0, t0 + 8)
    for i, (b, c) in enumerate([("D1", ["D2", "A2"]), ("Bb0", ["D2", "F2"]), ("D1", ["D2", "A2"])]):
        s.note(3, b, t0 + i * 6.1, 6.2, 52)
        s.chord(1, c, t0 + i * 6.1, 6.2, 42)
    for k, p in enumerate(["D3", "F3", "A3", "Bb2", "D3", "A2"]):
        s.note(5, p, t0 + 1.2 + k * 2.9, 3.2, 38)
    s.melody(2, [("A3", 3), ("Bb3", 2), ("A3", 3)], cue["street"] + 11.9, 1.0, vel=48)
    # ------------------------------------------------------------- CHURCH (warm minor -> F)
    t0 = 41.49
    s.ramp(1, 70, 92, t0, t0 + 3)
    for name, a, b in [("Dm", 41.49, 47.6), ("Bb", 47.6, 53.6), ("F", 53.6, 59.8), ("C", 59.8, 65.2), ("Dm", 65.2, 70.9)]:
        s.chord(1, CH[name], a, b - a + 0.2, 46)
        s.note(3, BASS[name], a, b - a, 40)
        s.chord(4, [P(p) + 12 for p in CH[name]], a, 3.0, 40, roll=0.09)
    s.chord(10, ["F3", "A3", "C4", "F4"], 60.2, 5.0, 40)
    s.ramp(10, 40, 90, 60.2, 62.5)
    s.ramp(10, 90, 30, 63.5, 65.3)
    s.note(2, "Bb2", 65.3, 3.0, 50)
    s.note(2, "A2", 68.3, 2.6, 46)
    # street again
    t0 = 70.86
    s.note(3, "D1", t0, 4.3, 46)
    s.chord(1, ["D2", "A2"], t0, 4.3, 40)

    # ------------------------------------------------------------- CELL (sparse, low)
    t0 = cue["cell"]
    s.ramp(1, 40, 70, t0, t0 + 6)
    s.chord(1, ["D2", "A2", "F3"], t0 + 1.0, 26.0, 36)
    t_rev = 110.31
    s.ramp(12, 30, 80, t_rev, 127.0)
    s.chord(12, ["D3", "Eb3"], t_rev, 17.0, 40)
    s.note(3, "D1", 118.67, 9.0, 44)
    s.note(2, "F3", 127.6, 5.4, 52)
    s.note(2, "E3", 133.0, 3.5, 46)
    s.chord(0, ["D3", "A3", "F4"], 135.3, 2.4, 32)
    s.note(5, "A4", 136.2, 2.0, 34)
    # English horn: the love motif in D minor, soft, under Paul's memory
    s.ramp(14, 70, 82, 138.0, 140)
    s.melody(14, LOVE_A_MIN[:7], 138.6, 1.05, vel=46)
    s.chord(1, CH["Dm"], 138.6, 6.3, 30)
    s.chord(1, CH["Gm"], 144.9, 6.0, 30)

    # ------------------------------------------------------------- JERUSALEM (phrygian, terror)
    t0 = cue["jerusalem"]
    s.ramp(12, 50, 100, t0, t0 + 4)
    s.chord(12, ["D3", "Eb3", "A3"], t0, 5.0, 56)
    beat = 60 / 76
    for k in range(int(5.0 / beat)):
        s.note(11, "D2", t0 + k * beat, 0.3, 74 - k * 3)
    s.chord(2, ["D2", "A2"], t0 + 2.6, 2.0, 70)
    t_y = line_t("yosef", "Asher. Don't")
    s.chord(1, ["D3", "F#3", "A3", "D4"], t_y - 0.4, 9.5, 44)
    s.ramp(1, 40, 80, t_y - 0.4, t_y + 2)
    s.melody(14, [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("B4", 1), ("A4", 1), ("F#4", 2)], t_y + 3.2, 0.9, vel=44)
    t_s = line_t("saul", "Take him")
    s.silence(t_s - 0.05)
    s.note(11, "D2", t_s, 0.8, 110)
    s.chord(2, ["D2", "D3"], t_s, 0.9, 100)
    s.chord(3, ["D1", "A1"], t_s, 1.2, 100)
    s.chord(8, ["D3", "Eb3", "A3"], t_s, 1.1, 82)
    s.chord(1, ["A4", "A5"], 168.6, 3.4, 40)
    s.ramp(1, 30, 70, 168.6, 170.2)
    s.chord(4, ["A5", "E6"], 168.9, 2.0, 34)
    s.note(2, "D2", 171.9, 2.0, 44)

    # ------------------------------------------------------------- CELL (confession)
    s.note(3, "D1", 178.3, 14.0, 34)
    s.chord(1, CH["Bb"], 193.9, 5.0, 34)
    s.chord(1, CH["F"], 198.9, 4.2, 30)
    for k, p in enumerate(["D3", "A3", "F4", "E4", "Bb2", "F3", "D4", "C4", "G2", "D3", "Bb3", "A3", "A2", "E3", "C#4", "E4"]):
        s.note(5, p, 203.3 + k * 0.95, 2.6, 40 if k % 4 == 0 else 32)
    s.chord(1, ["D2", "A2", "F3"], 208.5, 9.0, 30)
    s.note(5, "E4", 217.6, 3.0, 30)
    s.note(5, "Bb2", 217.6, 3.0, 30)

    # ------------------------------------------------------------- DAMASCUS
    t0 = cue["damascus"]
    s.ramp(1, 30, 100, t0, 229.9)
    s.chord(1, ["A1", "A2", "E3"], t0, 10.1, 48)
    s.ramp(12, 30, 110, 225.0, 229.9)
    s.chord(12, ["A2", "E3", "A3", "C#4"], 225.0, 4.9, 60)
    for k in range(18):
        s.note(11, "A1", 226.0 + k * 0.2, 0.18, 40 + k * 3)
    s.note(13, "C5", 227.4, 2.6, 110)  # reverse cymbal into the flash
    t_f = 229.94
    s.ramp(10, 110, 60, t_f, t_f + 8)
    s.chord(10, ["D3", "A3", "D4", "F#4", "A4", "D5"], t_f, 9.0, 96)
    s.chord(0, ["D2", "A2", "D3", "F#3", "A3", "D4", "F#4"], t_f, 6.0, 90)
    s.chord(8, ["D3", "F#3", "A3"], t_f, 3.0, 80)
    s.note(11, "D2", t_f, 1.4, 120)
    s.note(3, "D1", t_f, 9.0, 80)
    s.ramp(0, 100, 60, t_f + 1, t_f + 8)
    s.chord(4, ["D4", "F#4", "A4", "D5", "F#5", "A5", "D6"], 230.84, 3.5, 56, roll=0.07)
    s.chord(10, ["B2", "F#3", "B3", "D4"], 239.0, 2.0, 46)
    # the love motif on French horn as Jesus is revealed
    t_j = 240.8
    s.cc(8, 11, 85, t_j)
    beatJ = 0.92
    pad(s, 0, ["D", "Bm", "G", "A", "D", "G", "Em", "A"], t_j, 4 * beatJ, vel=44, bass_vel=40)
    s.melody(8, LOVE_A, t_j, beatJ, vel=62)
    t2 = t_j + 16 * beatJ
    s.melody(6, [("F#5", 1.5), ("G5", 0.5), ("A5", 2), ("D6", 1), ("C#6", 1), ("B5", 2), ("A5", 1), ("G5", 1), ("F#5", 1), ("E5", 1)], t2, beatJ, vel=44)
    s.chord(0, CH["G"], 262.3, 3.0, 42)
    s.chord(0, CH["DF"], 265.3, 3.0, 40)
    s.chord(0, CH["Em"], 268.3, 3.0, 38)
    s.chord(0, CH["A"], 270.0, 1.6, 36)
    s.chord(0, CH["D"], 271.5, 2.2, 42)
    s.chord(4, ["D4", "F#4", "A4", "D5", "F#5"], 271.5, 2.0, 48, roll=0.08)

    # ------------------------------------------------------------- CELL 2 (lament bass)
    t0 = cue["cell2"]
    for k, (b, name) in enumerate([("D3", "Dm"), ("C3", "Am"), ("Bb2", "Gm"), ("A2", "A")]):
        a = t0 + 0.5 + k * 7.0
        s.note(2, b, a, 7.0, 44)
        s.chord(5, [P(p) + 12 for p in CH[name][1:]], a + 0.6, 3.2, 30)
        s.chord(5, [P(p) + 12 for p in CH[name][1:]], a + 4.0, 2.8, 26)
    s.ramp(1, 30, 70, 301.7, 304.8)
    for name, a, b in [("D", 304.8, 309.0), ("G", 309.0, 313.6), ("DF", 313.6, 317.0), ("A", 317.0, 320.6)]:
        s.chord(1, CH[name], a, b - a + 0.3, 40)
        s.note(3, BASS[name], a, b - a, 34)
    for k, p in enumerate(["D3", "F3", "E3", "A2"]):
        s.note(2, p, 321.0 + k * 3.0, 3.1, 36)
    s.note(1, "A5", 333.4, 2.6, 30)

    # ------------------------------------------------------------- TURN (the bread)
    t0 = cue["turn"]
    s.chord(15, ["D4", "E4", "A4", "D5"], t0, 5.0, 44)
    s.ramp(15, 40, 80, t0, t0 + 2)
    s.ramp(15, 80, 30, t0 + 3, t0 + 5)
    s.arp(4, [P("D4"), P("A4"), P("D5"), P("F#5")], 340.8, 344.4, 0.47, 34)
    t_m = 344.6
    beatM = 0.9375
    s.ramp(0, 60, 96, t_m - 0.5, t_m + 3)
    pad(s, 0, ["D", "Bm", "G", "A"], t_m, 4 * beatM, vel=50, harp=beatM / 2, harp_vel=36)
    s.melody(7, LOVE_A, t_m, beatM, vel=62)
    t2 = t_m + 16 * beatM
    phrase2 = [("A4", 1), ("D5", 2), ("C#5", 1), ("B4", 1), ("A4", 1), ("F#4", 1), ("E4", 1), ("D4", 4)]
    pad(s, 0, ["D", "G", "A", "D"], t2, 2 * beatM, vel=52)
    s.chord(0, CH["D"], t2 + 8 * beatM, 4 * beatM, 52)
    s.melody(7, phrase2, t2, beatM, vel=66)
    s.melody(8, phrase2, t2, beatM, vel=50, transpose=-12)
    s.chord(10, ["D4", "F#4", "A4"], t2 + 4 * beatM, 6.0, 40)
    s.note(3, "D2", t2 + 8 * beatM, 3.0, 46)

    # ------------------------------------------------------------- STOP (door bang)
    s.silence(cue["stop"] - 0.02)
    t_tom = line_t("asher", "Tomorrow")
    s.chord(1, ["D2", "A2"], t_tom - 0.3, 10.5, 34)
    s.ramp(1, 40, 70, t_tom, t_tom + 8)

    # ------------------------------------------------------------- ROMANS 8 (the build)
    t0 = cue["romans8"]
    s.chord(1, CH["Dm"], t0, 3.6, 40)
    s.note(4, "A4", t0 + 0.5, 2.0, 36)
    beatR = 60 / 76
    prog_minor = [("Dm", 390.38), ("Bb", 393.5), ("F", 396.6), ("C", 399.7), ("Dm", 402.8), ("Bb", 404.4)]
    s.ramp(2, 60, 100, 390.4, 406.0)
    s.ramp(3, 60, 100, 390.4, 406.0)
    for i, (name, a) in enumerate(prog_minor):
        b = prog_minor[i + 1][1] if i + 1 < len(prog_minor) else 406.0
        s.chord(1, CH[name], a, b - a + 0.2, 42 + i * 3)
        root = P(BASS[name]) + 12
        t = a
        k = 0
        while t < b - 0.05:
            s.note(2, root + (12 if k % 4 == 3 else 0), t, beatR * 0.45, 52 + i * 3)
            s.note(3, root - 12, t, beatR * 0.45, 46 + i * 3)
            t += beatR / 2
            k += 1
        s.note(11, BASS[name], a, 0.6, 50 + i * 6)
    # "No! In all these things..." -> D major, horns
    t_no = 405.99
    major = [("D", t_no), ("G", 408.9), ("A", 410.2), ("D", 412.49), ("A", 414.2), ("Bm", 415.95), ("G", 418.4), ("DF", 421.7),
             ("Em", 423.6), ("A", 425.1), ("D", 426.21)]
    s.ramp(10, 40, 100, 412.5, 426.0)
    for i, (name, a) in enumerate(major[:-1]):
        b = major[i + 1][1]
        s.chord(0, CH[name], a, b - a + 0.15, 58 + i * 2)
        if a >= 412.4:
            s.chord(10, CH[name][1:], a, b - a + 0.1, 48 + i * 2)
        root = P(BASS[name]) + 12
        t = a
        k = 0
        while t < b - 0.05:
            s.note(2, root + (7 if k % 4 == 2 else 0), t, beatR * 0.45, 64 + i)
            s.note(3, root - 12, t, beatR * 0.45, 58 + i)
            t += beatR / 2
            k += 1
        s.note(11, BASS[name], a, 0.5, 62 + i * 3)
    s.melody(8, [("D4", 1), ("F#4", 1), ("A4", 2), ("D5", 3)], t_no + 0.1, beatR, vel=74)
    s.melody(8, [("A4", 1), ("B4", 1), ("C#5", 1), ("D5", 1), ("E5", 2), ("F#5", 3)], 418.4, beatR, vel=70)
    for k in range(int(1.0 / 0.08)):
        s.note(11, "A1", 425.1 + k * 0.08, 0.07, 60 + k * 3)
    # final line: the love motif in full orchestra and choir, resolving on D as the line ends
    t_fin = 426.21
    beatF = (432.74 - t_fin) / 7.0
    fin = [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("B4", 1), ("A4", 1), ("D5", 4)]
    s.melody(8, fin, t_fin, beatF, vel=80)
    s.melody(10, fin, t_fin, beatF, vel=78, transpose=0)
    s.melody(6, fin, t_fin, beatF, vel=64, transpose=12)
    for name, a, b in [("D", t_fin, t_fin + 2 * beatF), ("Bm", t_fin + 2 * beatF, t_fin + 4 * beatF), ("G", t_fin + 4 * beatF, t_fin + 5 * beatF),
                       ("A", t_fin + 5 * beatF, t_fin + 6 * beatF), ("D", t_fin + 6 * beatF, 437.5)]:
        s.chord(0, CH[name] + [P(CH[name][2]) + 12], a, b - a + 0.1, 74)
        s.note(3, BASS[name], a, b - a, 72)
        s.chord(10, CH[name][1:], a, b - a, 70)
    s.note(11, "D2", t_fin + 6 * beatF, 2.0, 100)
    s.chord(4, ["D3", "A3", "D4", "F#4", "A4", "D5", "F#5", "A5", "D6"], t_fin + 6 * beatF, 4.0, 60, roll=0.05)
    s.ramp(0, 100, 50, 434.0, 437.5)
    s.ramp(10, 100, 30, 434.0, 437.5)

    # ------------------------------------------------------------- DAWN
    t0 = cue["dawn"]
    beatD = 60 / 66
    s.cc(0, 11, 70, t0)
    pad(s, 1, ["D", "G", "D", "A", "Bm", "G", "D", "A"], t0 + 0.5, 4 * beatD, vel=40, harp=beatD / 2, harp_vel=32, bass_vel=30)
    s.melody(6, [(p[:-1] + str(int(p[-1]) + 1), b) for p, b in LOVE_A], t0 + 0.5 + 4 * beatD, beatD, vel=46)
    t_card = 456.44
    s.chord(1, CH["G"], t_card - 3.0, 3.0, 40)
    s.chord(1, CH["D"] + ["A4", "D5"], t_card, 7.2, 44)
    s.note(3, "D2", t_card, 7.2, 36)
    s.chord(4, ["D3", "A3", "D4", "F#4", "A4", "D5"], t_card, 6.0, 44, roll=0.12)
    s.ramp(1, 90, 0, t_card + 3.5, tl["duration"] + 0.3)
    s.ramp(4, 90, 0, t_card + 4.0, tl["duration"] + 0.3)
    return s


def render(work):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    s = compose(tl)
    mid = os.path.join(work, "music.mid")
    s.write(mid, tl["duration"] + 3)
    raw = os.path.join(work, "music_raw.wav")
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.55", "-r", "48000", "-o", "synth.reverb.active=1",
                    "-o", "synth.reverb.room-size=0.82", "-o", "synth.reverb.damp=0.35", "-o", "synth.reverb.width=0.9",
                    "-o", "synth.reverb.level=0.55", "-o", "synth.chorus.active=0", "-F", raw, SF2, mid], check=True)
    x, sr = sf.read(raw, dtype="float64")
    # extra hall around the soundfont for a filmic space
    wet = np.stack([audiofx.reverb(x[:, c], sr, wet=0.35, rt60=2.4, predelay=0.03, damp=6000)[:, c] for c in range(2)], axis=1)
    n = int((tl["duration"] + 2) * sr)
    out = np.zeros((n, 2))
    m = min(n, len(wet))
    out[:m] = wet[:m]
    pk = np.max(np.abs(out))
    out *= 0.9 / max(pk, 1e-6)
    sf.write(os.path.join(work, "music.wav"), out.astype(np.float32), sr)
    print("music rendered", out.shape[0] / sr, "s")


if __name__ == "__main__":
    render(os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work")))
