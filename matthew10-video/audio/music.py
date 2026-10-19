"""Compose the score as MIDI, cue by cue, aligned to the timeline.

Usage: python music.py timeline.json OUT.mid
Render: fluidsynth -ni -F out.wav -r 48000 FluidR3_GM.sf2 OUT.mid
"""
import json
import sys
from pathlib import Path

import mido

TPB = 480          # ticks per beat; tempo is 60 bpm so 1 beat = 1 second
CH = {"piano": 0, "strings": 1, "pad": 2, "choir": 3, "cello": 4, "celesta": 5, "guitar": 6, "timp": 7,
      "chime": 8, "horn": 10, "bass": 11, "slow": 12}
PROG = {"piano": 0, "strings": 48, "pad": 89, "choir": 52, "cello": 42, "celesta": 8, "guitar": 24, "timp": 47,
        "chime": 14, "horn": 60, "bass": 43, "slow": 49}

N = {n: i for i, n in enumerate(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"])}
N.update({"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10})


def note(name):
    """'D4' -> 62"""
    p, o = name[:-1], int(name[-1])
    return 12 * (o + 1) + N[p]


def notes(s):
    return [note(x) for x in s.split()]


class Score:
    def __init__(self):
        self.ev = []   # (time_s, priority, channel, msg)

    def add(self, t, ch, msg, pri=1):
        self.ev.append((max(0.0, t), pri, ch, msg))

    def n(self, inst, t, dur, pitch, vel):
        ch = CH[inst]
        if isinstance(pitch, str):
            pitch = note(pitch)
        vel = max(1, min(127, int(vel)))
        self.add(t, ch, mido.Message("note_on", channel=ch, note=pitch, velocity=vel), 2)
        self.add(t + dur, ch, mido.Message("note_off", channel=ch, note=pitch, velocity=0), 0)

    def chord(self, inst, t, dur, pitches, vel, roll=0.0):
        if isinstance(pitches, str):
            pitches = notes(pitches)
        for i, p in enumerate(pitches):
            self.n(inst, t + i * roll, dur - i * roll, p, vel)

    def cc(self, inst, t, ctl, val):
        ch = CH[inst]
        self.add(t, ch, mido.Message("control_change", channel=ch, control=ctl, value=max(0, min(127, int(val)))), 1)

    def ramp(self, inst, t0, t1, v0, v1, ctl=11, steps=None):
        steps = steps or max(2, int((t1 - t0) * 8))
        for i in range(steps + 1):
            u = i / steps
            self.cc(inst, t0 + (t1 - t0) * u, ctl, v0 + (v1 - v0) * u)

    def bend(self, inst, t, semis):
        ch = CH[inst]
        self.add(t, ch, mido.Message("pitchwheel", channel=ch, pitch=int(max(-8191, min(8191, semis / 2 * 8191)))), 1)

    def arp(self, inst, t0, t1, pitches, step, vel, hold=1.6, pattern=None):
        if isinstance(pitches, str):
            pitches = notes(pitches)
        order = pattern or list(range(len(pitches)))
        t, i = t0, 0
        while t < t1 - 0.05:
            p = pitches[order[i % len(order)]]
            accent = 6 if i % len(order) == 0 else 0
            self.n(inst, t, min(hold, t1 - t + 0.4), p, vel + accent)
            t += step
            i += 1

    def save(self, path):
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))
        for inst, ch in CH.items():
            tr.append(mido.Message("program_change", channel=ch, program=PROG[inst], time=0))
            tr.append(mido.Message("control_change", channel=ch, control=7, value=100, time=0))
            tr.append(mido.Message("control_change", channel=ch, control=91, value=70, time=0))   # reverb send
            tr.append(mido.Message("control_change", channel=ch, control=11, value=100, time=0))
        self.ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for t, _, _, msg in self.ev:
            tick = int(round(t * TPB))
            tr.append(msg.copy(time=tick - last))
            last = tick
        mid.save(path)


def compose(tl):
    sc = {s["id"]: s for s in tl["scenes"]}
    ln = {l["id"]: l for l in tl["lines"]}
    S = Score()
    W = lambda lid, i: ln[lid]["start"] + (ln[lid]["end"] - ln[lid]["start"]) * i  # fraction through a line

    # ---------------------------------------------------------- 1. the table (D minor, uneasy)
    t0, t1 = sc["table"]["start"], ln["L5"]["start"]
    prog = [("D3 A3 E4 F4", "D2 A2"), ("Bb2 F3 A3 D4", "Bb1 F2"), ("G2 D3 F3 Bb3", "G1 D2"), ("A2 E3 G3 C#4", "A1 E2")]
    S.cc("piano", 0, 11, 92)
    t, k = t0 + 0.2, 0
    while t < t1 - 1.0:
        up, low = prog[k % 4]
        S.arp("piano", t, min(t + 4.0, t1), up, 0.5, 40, hold=1.4, pattern=[0, 1, 2, 3, 2, 1, 2, 3])
        S.chord("strings", t, 4.0, low, 30)
        t += 4.0
        k += 1
    # "I'm not okay": the floor drops out to a low cello and thin strings
    S.n("cello", t1, ln["L9"]["start"] - t1 + 1.0, "D2", 46)
    S.chord("slow", t1 + 0.5, 6.0, "D3 F3 A3", 34)
    S.chord("slow", t1 + 6.5, ln["L9"]["start"] - t1 - 6.0, "Bb2 D3 F3", 36)
    S.n("piano", ln["L10"]["end"] + 0.1, 3.0, "A5", 34)                      # a single cold note after "What does that mean?"
    # the silence: a low drone gathers into the interlude
    q = ln["L13"]["end"]
    S.n("bass", q + 0.5, sc["table"]["end"] - q + 1.0, "D1", 50)
    S.ramp("slow", q, sc["table"]["end"] + 0.5, 30, 100)
    S.chord("slow", q + 0.5, sc["table"]["end"] - q + 0.8, "D3 E3 F3", 40)

    # ---------------------------------------------------------- 2. interlude: the sword
    s0, s1 = sc["sword"]["start"], sc["sword"]["end"]
    nw1 = len(ln["N1"]["text"].split())
    strike = ln["N1"]["start"] + (ln["N1"]["end"] - ln["N1"]["start"]) * 0.97
    S.cc("choir", s0, 11, 70)
    S.ramp("choir", s0, strike, 62, 92)
    seq = [("D3 F3 A3 D4", "D2"), ("Bb2 F3 Bb3 D4", "Bb1"), ("F2 A3 C4 F4", "F1"), ("C3 G3 C4 E4", "C2")]
    t, k = s0, 0
    while t < s1:
        up, low = seq[k % 4]
        dur = 4.6
        S.chord("choir", t, dur + 0.3, up, 54)
        S.chord("strings", t, dur + 0.3, up, 44)
        S.n("bass", t, dur + 0.3, low, 58)
        t += dur
        k += 1
    for i in range(14):                                                       # timpani roll into the strike
        S.n("timp", strike - 1.3 + i * 0.09, 0.2, "D2", 30 + i * 3)
    S.n("timp", strike, 2.5, "D2", 104)
    S.chord("horn", strike, 3.0, "D3 A3 D4", 72)
    S.chord("cello", strike, 4.0, "D2 A2", 80)
    S.ramp("choir", ln["N3"]["start"], s1 + 1, 92, 62)

    # ---------------------------------------------------------- 3. the mask
    m0 = sc["mask"]["start"]
    L14, L15 = ln["L14"], ln["L15"]
    motif = ["C5", "E5", "G5", "E5", "C6", "G5", "E5", "G5"]
    S.cc("celesta", m0, 11, 95)
    t = m0 + 0.2
    i = 0
    while t < L15["start"] - 0.4:
        S.n("celesta", t, 0.4, motif[i % 8], 28)
        t += 0.3 if t < L14["end"] + 0.3 else 0.3 + (t - L14["end"]) * 0.12   # slows as the smile lingers
        i += 1
    for j in range(20):                                                       # and sags out of tune
        S.bend("celesta", L14["end"] + 0.5 + j * 0.12, -1.2 * j / 19)
    S.bend("celesta", L15["end"] + 1.5, 0)
    S.n("slow", L15["start"] - 0.2, 3.0, "B2", 30)
    bed0 = L15["end"] + 0.8
    bed1 = sc["mask"]["end"]
    prog = [("A3 E4 B4 C5", "A2"), ("F3 C4 E4 A4", "F2"), ("C4 E4 G4 D5", "C3"), ("G3 D4 G4 B4", "G2")]
    t, k = bed0, 0
    S.cc("piano", bed0, 11, 88)
    while t < bed1 + 1.0:
        up, low = prog[k % 4]
        S.arp("piano", t, t + 4.4, up, 0.55, 34, hold=1.8, pattern=[0, 1, 2, 3, 1, 2])
        S.chord("pad", t, 4.6, [note(low) + 12, note(up.split()[1])], 36)
        if t > ln["L19"]["start"]:
            S.chord("strings", t, 4.6, up, 28)
        t += 4.4
        k += 1

    # ---------------------------------------------------------- 4. interlude: the cross
    c0, c1 = sc["cross"]["start"], sc["cross"]["end"]
    n4, n5 = ln["N4"], ln["N5"]
    crack = W("N4", 0.42)
    fall = W("N4", 0.62)
    found = W("N4", 0.94)
    S.chord("choir", c0, crack - c0 + 0.5, "A2 E3 A3 C4", 52)
    S.chord("slow", c0, crack - c0 + 0.5, "A2 E3 C4", 40)
    for i in range(10):
        S.n("chime", crack + i * 0.13, 1.5, ["E6", "B6", "F#6", "C7", "G6"][i % 5], 40 + i * 3)
    S.n("timp", fall, 2.0, "A1", 110)
    S.chord("choir", fall, found - fall + 0.4, "F2 C3 F3 A3", 78)
    S.chord("strings", fall, found - fall + 0.4, "F3 A3 C4 F4", 60)
    S.chord("choir", found, n5["start"] - found + 1.5, "C3 G3 C4 E4", 84)        # resolution: "will find it"
    S.chord("strings", found, n5["start"] - found + 1.5, "C3 E3 G3 C4 E4", 70)
    S.chord("horn", found, 3.5, "C3 G3 C4", 60)
    prog = [("F3 C4 A4", "F2"), ("E3 C4 G4", "C2"), ("D3 F3 A3 C4", "D2"), ("C3 G3 E4", "C2")]
    t, k = n5["start"] - 0.3, 0
    while t < c1 + 0.5:
        up, low = prog[k % 4]
        S.chord("slow", t, 3.4, up, 40)
        S.n("bass", t, 3.4, low, 38)
        S.n("piano", t + 0.4, 2.5, note(up.split()[-1]) + 12, 30)
        t += 3.2
        k += 1

    # ---------------------------------------------------------- 5. the office: silence, then overload
    o1 = sc["office"]["end"]
    tover = ln["L26"]["end"] + 0.4
    S.ramp("strings", tover - 0.1, o1, 40, 127)
    for i, p in enumerate(["E4", "F4", "F#4", "G4", "Bb4"]):
        t = tover + i * 0.4
        while t < o1:
            S.n("strings", t, 0.13, p, 40 + (t - tover) * 14)
            t += 0.14
    S.n("bass", tover, o1 - tover, "E1", 70)

    # ---------------------------------------------------------- 6. the park (F major, hopeful)
    p0, p1 = sc["park"]["start"], sc["park"]["end"]
    prog = [("F2 C3 A3 C4", "F3 A3 C4"), ("A2 E3 C4 E4", "A3 C4 E4"), ("Bb2 F3 D4 F4", "Bb3 D4 F4"), ("C3 G3 E4 G4", "C4 E4 G4")]
    t, k = p0 + 0.8, 0
    S.cc("guitar", p0, 11, 100)
    while t < p1 + 0.5:
        g, chd = prog[k % 4]
        S.arp("guitar", t, t + 3.6, g, 0.45, 44, hold=1.5, pattern=[0, 1, 2, 3, 2, 1, 2, 3])
        if t > ln["L28"]["start"]:
            S.chord("strings", t, 3.8, chd, 26)
        t += 3.6
        k += 1
    mel = [("C5", 0.9), ("D5", 0.45), ("F5", 1.35), ("E5", 0.9), ("D5", 0.9), ("C5", 1.8)]
    t = ln["L29"]["start"] + 0.2
    for p, d in mel:
        S.n("piano", t, d * 1.1, p, 38)
        t += d

    # ---------------------------------------------------------- 7. interlude: the sparrows (swell)
    q0, q1 = sc["sparrows"]["start"], sc["sparrows"]["end"]
    prog = [("F3 A3 C4 F4", "F2"), ("E3 G3 C4 E4", "C2"), ("D3 F3 A3 D4", "D2"), ("Bb2 F3 Bb3 D4", "Bb1"),
            ("C3 F3 A3 C4", "F2"), ("C3 E3 G3 C4", "C2"), ("F3 A3 C4 F4", "F2")]
    step = (q1 - q0 + 1.0) / len(prog)
    S.ramp("strings", q0, ln["N7"]["start"], 70, 115)
    for k, (up, low) in enumerate(prog):
        t = q0 + k * step
        S.chord("strings", t, step + 0.3, up, 58)
        S.chord("choir", t, step + 0.3, up, 46 + k * 4)
        S.n("bass", t, step + 0.3, low, 54)
    theme = [("C5", 1.0), ("D5", 0.5), ("F5", 1.5), ("G5", 1.0), ("A5", 1.0), ("G5", 0.5), ("F5", 1.5), ("D5", 1.0), ("F5", 2.5)]
    t = q0 + 0.5
    for p, d in theme:
        S.n("piano", t, d * 1.05, p, 50)
        S.n("piano", t, d * 1.05, note(p) - 12, 36)
        t += d * (q1 - q0) / 13.5

    # ---------------------------------------------------------- 8. the call (heartbeat, then tenderness)
    k0, k1 = sc["call"]["start"], sc["call"]["end"]
    crack_t = ln["L35"]["start"]
    S.chord("slow", k0 + 0.5, crack_t - k0 - 0.3, "D3 A3 D4", 32)
    S.n("bass", k0 + 0.5, crack_t - k0 - 0.3, "D1", 40)
    t = ln["L31"]["start"] - 0.6
    while t < crack_t - 0.6:
        S.n("timp", t, 0.3, "D2", 34)
        S.n("timp", t + 0.28, 0.3, "D2", 26)
        t += 0.92
    tender = [("A4", 1.0), ("G4", 0.5), ("F4", 1.5), ("E4", 1.0), ("F4", 2.0)]
    t = crack_t + 0.2
    for p, d in tender:
        S.n("piano", t, d * 1.1, p, 36)
        t += d
    S.chord("strings", crack_t, 4.5, "Bb2 F3 D4", 34)
    S.chord("strings", crack_t + 4.5, 4.5, "F2 C3 A3", 34)
    prog = [("D3 A3 F4", "D2"), ("Bb2 F3 D4", "Bb1"), ("F3 C4 A4", "F2"), ("C3 G3 E4", "C2")]
    t, k = ln["L36"]["end"] + 1.0, 0
    while t < k1 + 0.5:
        up, low = prog[k % 4]
        if t > ln["L39"]["start"] - 0.5:
            up, low = ("F3 C4 A4", "F2")
        S.arp("piano", t, t + 3.6, up, 0.6, 32, hold=1.8)
        S.chord("pad", t, 3.8, up, 30)
        t += 3.6
        k += 1

    # ---------------------------------------------------------- 9. interlude: the road (toward D major)
    r0, r1 = sc["road"]["start"], sc["road"]["end"]
    prog = [("D3 F3 A3", "D2"), ("Bb2 D3 F3", "Bb1"), ("F3 A3 C4", "F2"), ("A2 C#3 E3 A3", "A1"), ("D3 F#3 A3 D4", "D2")]
    step = (r1 - r0 + 1.4) / len(prog)
    S.ramp("strings", r0, r1, 60, 110)
    for k, (up, low) in enumerate(prog):
        t = r0 + k * step
        S.chord("strings", t, step + 0.3, up, 55 + k * 6)
        S.chord("choir", t, step + 0.3, up, 40 + k * 7)
        S.n("bass", t, step + 0.3, low, 52)
    S.chord("horn", r1 - 0.6, 3.0, "D3 F#3 A3", 56)

    # ---------------------------------------------------------- 10. epilogue (D major, warm)
    e0, e1 = sc["epilogue"]["start"], tl["duration"]
    prog = [("D3 A3 F#4", "D2"), ("C#3 A3 E4", "A1"), ("B2 F#3 D4", "B1"), ("G2 D3 B3", "G1"),
            ("F#2 D3 A3", "D2"), ("E3 G3 B3", "E2"), ("A2 E3 C#4", "A1"), ("D3 A3 F#4", "D2")]
    t, k = e0 + 0.3, 0
    S.cc("piano", e0, 11, 96)
    while t < e1 - 4.5:
        up, low = prog[k % len(prog)]
        S.arp("piano", t, t + 3.2, up, 0.4, 40, hold=1.5, pattern=[0, 1, 2, 1, 2, 1, 2, 1])
        S.chord("strings", t, 3.4, up, 30 + (12 if t > ln["N9"]["start"] else 0))
        S.n("bass", t, 3.4, low, 40)
        t += 3.2
        k += 1
    horn = [("F#4", 1.5), ("E4", 0.5), ("D4", 1.0), ("A4", 2.0), ("G4", 1.0), ("F#4", 2.0)]
    t = ln["N9"]["start"] + 0.5
    for p, d in horn:
        S.n("horn", t, d * 1.05, p, 52)
        t += d
    S.chord("strings", e1 - 4.6, 4.6, "D3 A3 D4 F#4 A4", 52)
    S.chord("choir", e1 - 4.6, 4.6, "D3 A3 F#4", 44)
    S.n("piano", e1 - 4.4, 4.0, "D6", 44)
    S.n("piano", e1 - 4.4, 4.0, "A5", 32)
    S.n("bass", e1 - 4.6, 4.6, "D2", 48)
    for inst in CH:
        S.ramp(inst, e1 - 1.8, e1, 100, 0, ctl=7, steps=10)
    return S


def main():
    tl = json.loads(Path(sys.argv[1]).read_text())
    S = compose(tl)
    S.save(sys.argv[2])
    print("events", len(S.ev))


if __name__ == "__main__":
    main()
