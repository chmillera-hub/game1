"""
Original score for A NEW COMMANDMENT, written as MIDI events on an absolute
clock (seconds) and rendered with FluidSynth + the FluidR3 General MIDI soundfont.

Central idea: one hymn-like "love motif" (D major) that travels through the film:
  flute at the supper -> English horn in D minor under Paul's guilt -> French horn
  when Jesus appears on the Damascus road -> oboe when Asher breaks the bread ->
  full orchestra and choir at the Romans 8 climax -> flute at dawn.

Under the heaviest moments (what Paul did, the arrest, "He never came home", "the worst of
sinners", the sentence, "sheep to be slaughtered", "the old man was no more") deep swells of
low strings and tuba rise and fall, rendered as a separate layer and mixed under the score.
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

    def write(self, path, end, progs=None):
        mid = mido.MidiFile(ticks_per_beat=TPS)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))
        for ch, pg in (progs or PROG).items():
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
    """Every cue is anchored to story events (shots, lines), never to absolute seconds,
    so the score follows the film when dialogue or pacing changes."""
    s = Score()
    cue = {m["cue"]: m["t"] for m in tl["music"]}
    lines = tl["lines"]
    shots = tl["shots"]

    def LN(who, prefix, end=False):
        for ln in lines:
            if ln["who"] == who and ln["text"].startswith(prefix):
                return ln["end"] if end else ln["start"]
        raise KeyError(f"{who}: {prefix}")

    def SH(sid, n=0, end=False):
        hits = [x for x in shots if x["id"] == sid]
        return hits[n]["end"] if end else hits[n]["start"]

    def spread(names, t0, t1):
        """evenly spaced chord changes between two anchors"""
        step = (t1 - t0) / len(names)
        return [(nm, t0 + i * step, t0 + (i + 1) * step) for i, nm in enumerate(names)]

    # ------------------------------------------------------------- PROLOGUE (D major)
    bar = 4 * (60 / 72)
    s.ramp(0, 70, 92, 0, 6)
    pro_end = SH("street_wide")
    nbar = max(4, int((pro_end - 0.5) / bar) - 1)
    prog = (["D", "Bm", "G", "A", "DF", "G", "D", "Bm"] * 2)[:nbar]
    pad(s, 0, prog, 0.0, bar, vel=50, harp=bar / 8, harp_vel=40)
    s.chord(0, ["E3", "B3", "D4", "G4"], nbar * bar, bar * 0.5, 44)
    s.chord(0, CH["A"], (nbar + 0.5) * bar, max(0.5, pro_end - (nbar + 0.5) * bar), 42)
    # flute answers after Jesus speaks; English horn under His sorrowful look at the door
    s.melody(6, [("A4", 0.5), ("D5", 1.5), ("C#5", 0.5), ("B4", 0.5), ("A4", 2)], LN("jesus", "Love one another", True) + 0.05, 60 / 72, vel=48)
    s.melody(14, [("G4", 1.5), ("F#4", 0.5), ("E4", 1), ("D4", 1), ("E4", 3)], SH("upper_jesus_door") + 0.2, 60 / 72, vel=50)

    # ------------------------------------------------------------- STREET (D minor, dark)
    t0 = cue["street"]
    t1 = SH("church_reader")
    s.ramp(1, 60, 85, t0, t0 + 8)
    seg = (t1 - t0) / 3
    for i, (b, c) in enumerate([("D1", ["D2", "A2"]), ("Bb0", ["D2", "F2"]), ("D1", ["D2", "A2"])]):
        s.note(3, b, t0 + i * seg, seg + 0.1, 52)
        s.chord(1, c, t0 + i * seg, seg + 0.1, 42)
    for k, p in enumerate(["D3", "F3", "A3", "Bb2", "D3", "A2", "F3"]):
        tk = t0 + 1.2 + k * 2.9
        if tk < t1 - 1:
            s.note(5, p, tk, 3.2, 38)
    s.melody(2, [("A3", 3), ("Bb3", 2), ("A3", 3)], SH("street_asher_cu") + 0.1, 1.0, vel=48)
    # sad look to the ground after "This is foolish."
    s.note(14, "F4", LN("asher", "Why am I even here", True) + 0.3, 2.2, 40)
    s.note(14, "E4", LN("asher", "Why am I even here", True) + 2.5, 1.5, 36)

    # ------------------------------------------------------------- CHURCH (warm minor -> F)
    t0 = SH("church_reader")
    t1 = SH("street_asher_cu", 1)
    s.ramp(1, 70, 92, t0, t0 + 3)
    for name, a, b in spread(["Dm", "Bb", "F", "C", "Dm"], t0, t1):
        s.chord(1, CH[name], a, b - a + 0.2, 46)
        s.note(3, BASS[name], a, b - a, 40)
        s.chord(4, [P(p) + 12 for p in CH[name]], a, 3.0, 40, roll=0.09)
    t_en = LN("phoebe", "If your enemy")
    s.chord(10, ["F3", "A3", "C4", "F4"], t_en, 5.0, 40)
    s.ramp(10, 40, 90, t_en, t_en + 2.3)
    s.ramp(10, 90, 30, t_en + 3.3, t_en + 5.1)
    t_co = LN("phoebe", "In doing this")
    s.note(2, "Bb2", t_co, 3.0, 50)
    s.note(2, "A2", t_co + 3.0, 2.6, 46)
    # street again, until the knock
    t0 = SH("street_asher_cu", 1)
    s.note(3, "D1", t0, SH("street_knock") - t0, 46)
    s.chord(1, ["D2", "A2"], t0, SH("street_knock") - t0, 40)

    # ------------------------------------------------------------- CELL (warm welcome, then the wound opens)
    t0 = cue["cell"]
    t_rev = LN("asher", "Someone you met")
    s.ramp(1, 40, 70, t0, t0 + 6)
    # Paul's welcome: a soft, warm major colour (he believes the best of the stranger)
    t_w = LN("paul", "Come in, come in")
    for name, a, b in spread(["D", "G", "D", "A"], t_w, LN("asher", "Look, Paul... I need you")):
        s.chord(1, CH[name], a, b - a + 0.2, 32)
    s.chord(1, ["D2", "A2", "F3"], LN("asher", "Look, Paul... I need you"), t_rev - LN("asher", "Look, Paul... I need you"), 32)
    t_yo = LN("asher", "You dragged a man")
    s.ramp(12, 30, 80, t_rev, LN("asher", "I was eight"))
    s.chord(12, ["D3", "Eb3"], t_rev, LN("asher", "I was eight") - t_rev, 40)
    s.note(3, "D1", t_yo, LN("asher", "I was eight") - t_yo, 44)
    t8 = LN("asher", "I was eight")
    t_home = LN("asher", "He never came home")
    s.note(2, "F3", t8 + 0.1, t_home - t8, 52)
    s.note(2, "E3", t_home, 3.5, 46)
    t_sil = LN("asher", "He never came home", True) + 1.2
    s.chord(0, ["D3", "A3", "F4"], t_sil, 2.4, 32)
    s.note(5, "A4", t_sil + 0.9, 2.0, 34)
    # English horn: the love motif in D minor, soft, under Paul's memory
    t_eh = LN("paul", "He looked at me.") + 1.3
    s.ramp(14, 70, 82, t_eh - 0.6, t_eh + 1.4)
    s.melody(14, LOVE_A_MIN[:7], t_eh, 1.05, vel=46)
    s.chord(1, CH["Dm"], t_eh, 6.3, 30)
    s.chord(1, CH["Gm"], t_eh + 6.3, 6.0, 30)

    # ------------------------------------------------------------- JERUSALEM (phrygian, terror)
    t0 = cue["jerusalem"]
    s.ramp(12, 50, 100, t0, t0 + 4)
    s.chord(12, ["D3", "Eb3", "A3"], t0, 5.4, 56)
    beat = 60 / 76
    for k in range(int(5.4 / beat)):
        s.note(11, "D2", t0 + k * beat, 0.3, 74 - k * 3)
    s.chord(2, ["D2", "A2"], SH("jer_child"), 2.0, 70)
    t_y = LN("yosef", "Asher, my son")
    s.chord(1, ["D3", "F#3", "A3", "D4"], t_y - 0.4, LN("saul", "Take him") - t_y + 0.3, 44)
    s.ramp(1, 40, 80, t_y - 0.4, t_y + 2)
    s.melody(14, [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("B4", 1), ("A4", 1), ("F#4", 2)], t_y + 3.2, 0.9, vel=44)
    t_s = LN("saul", "Take him")
    s.silence(t_s - 0.05)
    s.note(11, "D2", t_s, 0.8, 110)
    s.chord(2, ["D2", "D3"], t_s, 0.9, 100)
    s.chord(3, ["D1", "A1"], t_s, 1.2, 100)
    s.chord(8, ["D3", "Eb3", "A3"], t_s, 1.1, 82)
    t_lk = SH("jer_yosef_look")
    s.chord(1, ["A4", "A5"], t_lk + 0.1, SH("jer_saul", 1) - t_lk, 40)
    s.ramp(1, 30, 70, t_lk + 0.1, t_lk + 1.7)
    s.chord(4, ["A5", "E6"], LN("yosef", "May God be the light"), 2.0, 34)
    s.note(2, "D2", SH("jer_saul", 1), 2.0, 44)

    # ------------------------------------------------------------- CELL (Paul answers; the confession)
    t_rm = LN("paul", "I remember him because")
    for name, a, b in spread(["Dm", "Bb", "F", "A"], t_rm, LN("paul", "until it reaches", True)):
        s.chord(1, CH[name], a, b - a + 0.2, 34)
        s.note(3, BASS[name], a, b - a, 32)
    s.note(3, "D1", LN("asher", "They read your letter"), 10.0, 30)
    t_dn = LN("paul", "Then you have done")
    s.chord(1, CH["Bb"], t_dn, 5.0, 34)
    s.chord(1, CH["F"], t_dn + 5.0, 4.2, 30)
    t_kn = LN("paul", "They know.")
    for k, p in enumerate(["D3", "A3", "F4", "E4", "Bb2", "F3", "D4", "C4", "G2", "D3", "Bb3", "A3", "A2", "E3", "C#4", "E4"]):
        s.note(5, p, t_kn + 0.1 + k * 0.95, 2.6, 40 if k % 4 == 0 else 32)
    s.chord(1, ["D2", "A2", "F3"], LN("paul", "I was a blasphemer"), 9.0, 30)
    t_hu = LN("paul", "I was hunting His sheep")
    s.note(5, "E4", t_hu + 0.2, 3.0, 30)
    s.note(5, "Bb2", t_hu + 0.2, 3.0, 30)

    # ------------------------------------------------------------- DAMASCUS
    t0 = cue["damascus"]
    t_cu = SH("dam_saul_cu")
    t_f = SH("dam_flash")
    s.ramp(1, 30, 100, t0, t_f)
    s.chord(1, ["A1", "A2", "E3"], t0, t_f - t0, 48)
    s.ramp(12, 30, 110, t_cu - 2.1, t_f)
    s.chord(12, ["A2", "E3", "A3", "C#4"], t_cu - 2.1, t_f - t_cu + 2.1, 60)
    for k in range(18):
        s.note(11, "A1", t_cu - 1.1 + k * 0.2, 0.18, 40 + k * 3)
    s.note(13, "C5", t_f - 2.55, 2.6, 110)  # reverse cymbal into the flash
    s.ramp(10, 110, 60, t_f, t_f + 8)
    s.chord(10, ["D3", "A3", "D4", "F#4", "A4", "D5"], t_f, 9.0, 96)
    s.chord(0, ["D2", "A2", "D3", "F#3", "A3", "D4", "F#4"], t_f, 6.0, 90)
    s.chord(8, ["D3", "F#3", "A3"], t_f, 3.0, 80)
    s.note(11, "D2", t_f, 1.4, 120)
    s.note(3, "D1", t_f, 9.0, 80)
    s.ramp(0, 100, 60, t_f + 1, t_f + 8)
    s.chord(4, ["D4", "F#4", "A4", "D5", "F#5", "A5", "D6"], SH("dam_saul_kneel"), 3.5, 56, roll=0.07)
    s.chord(10, ["B2", "F#3", "B3", "D4"], SH("dam_jesus") - 1.6, 2.0, 46)
    # the love motif on French horn as Jesus is revealed
    t_j = SH("dam_jesus") + 0.2
    s.cc(8, 11, 85, t_j)
    beatJ = 0.92
    pad(s, 0, ["D", "Bm", "G", "A", "D", "G", "Em", "A"], t_j, 4 * beatJ, vel=44, bass_vel=40)
    s.melody(8, LOVE_A, t_j, beatJ, vel=62)
    t2 = t_j + 16 * beatJ
    s.melody(6, [("F#5", 1.5), ("G5", 0.5), ("A5", 2), ("D6", 1), ("C#6", 1), ("B5", 2), ("A5", 1), ("G5", 1), ("F#5", 1), ("E5", 1)], t2, beatJ, vel=44)
    t_h = SH("dam_hands")
    t_me = LN("paul", "He chose me")
    for name, a, b in spread(["G", "DF", "Em", "A"], t_h, t_me):
        s.chord(0, CH[name], a, b - a + 0.1, 40)
    s.chord(0, CH["D"], t_me, 3.0, 42)
    s.chord(4, ["D4", "F#4", "A4", "D5", "F#5"], t_me + 0.4, 2.0, 48, roll=0.08)

    # ------------------------------------------------------------- CELL 2 (lament bass; mercy; hate that remains)
    t0 = cue["cell2"]
    t_tr = LN("paul", "Here is a trustworthy")
    lam = [("D3", "Dm"), ("C3", "Am"), ("Bb2", "Gm"), ("A2", "A")]
    step = (LN("paul", "of whom I am among the worst") - t0) / len(lam)
    for k, (b, name) in enumerate(lam):
        a = t0 + 0.5 + k * step
        s.note(2, b, a, step, 44)
        s.chord(5, [P(p) + 12 for p in CH[name][1:]], a + 0.6, 3.2, 30)
        s.chord(5, [P(p) + 12 for p in CH[name][1:]], a + step * 0.55, 2.8, 26)
    t_wo = LN("paul", "of whom I am among the worst")
    t_rs = LN("paul", "But for that very reason")
    s.ramp(1, 30, 70, t_wo, t_rs)
    t_el = LN("paul", "as an example", True)
    for name, a, b in spread(["D", "G", "DF", "A"], t_rs, t_el):
        s.chord(1, CH[name], a, b - a + 0.3, 40)
        s.note(3, BASS[name], a, b - a, 34)
    t_ha = LN("asher", "I came here to hate you")
    for k, p in enumerate(["D3", "F3", "E3", "A2"]):
        s.note(2, p, t_ha + 0.4 + k * 3.0, 3.1, 36)
    t_kn2 = LN("paul", "I know.")
    for name, a, b in spread(["F", "C", "Dm", "Bb", "F", "C", "Gm", "A"], t_kn2, LN("paul", "I tell you, the Lord has been patient", True)):
        s.chord(1, CH[name], a, b - a + 0.2, 30)
    s.note(1, "A5", LN("asher", "I brought the bread") - 0.2, 2.6, 30)

    # ------------------------------------------------------------- TURN (the bread)
    t0 = cue["turn"]
    s.chord(15, ["D4", "E4", "A4", "D5"], t0, SH("cell_kneel") - t0, 44)
    s.ramp(15, 40, 80, t0, t0 + 2)
    s.ramp(15, 80, 30, SH("cell_kneel") - 2, SH("cell_kneel"))
    s.arp(4, [P("D4"), P("A4"), P("D5"), P("F#5")], SH("cell_kneel"), SH("cell_break_insert") + 1.0, 0.47, 34)
    t_m = SH("cell_break_insert") + 1.2
    t_end = LN("narrator", "but overcome evil") + 1.2
    beatM = max(0.78, min(1.25, (t_end - t_m) / 24.0))
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
    t_tom = LN("asher", "Tomorrow")
    s.chord(1, ["D2", "A2"], t_tom - 0.3, cue["romans8"] - t_tom + 0.3, 34)
    s.ramp(1, 40, 70, t_tom, cue["romans8"])

    # ------------------------------------------------------------- ROMANS 8 (the build)
    t0 = cue["romans8"]
    s.chord(1, CH["Dm"], t0, 3.6, 40)
    s.note(4, "A4", t0 + 0.5, 2.0, 36)
    beatR = 60 / 76
    t_sh = LN("paul", "Shall trouble")
    t_no = LN("paul", "No! I say to you")
    names = ["Dm", "Bb", "F", "C", "Dm", "Bb"]
    stepm = (t_no - t_sh) / len(names)
    prog_minor = [(nm, t_sh + i * stepm) for i, nm in enumerate(names)]
    s.ramp(2, 60, 100, t_sh, t_no)
    s.ramp(3, 60, 100, t_sh, t_no)
    for i, (name, a) in enumerate(prog_minor):
        b = prog_minor[i + 1][1] if i + 1 < len(prog_minor) else t_no
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
    t_thr = LN("paul", "through Him who loved us")
    t_conv = LN("paul", "For I am convinced")
    t_ang = LN("paul", "neither angels")
    t_hei = LN("paul", "neither height")
    t_fin = LN("paul", "will be able to separate")
    t_last = LN("paul", "from Christ Jesus, who saved me")
    t_last_end = LN("paul", "from Christ Jesus, who saved me", True)
    mid = lambda x, y, f: x + (y - x) * f
    major = [("D", t_no), ("G", mid(t_no, t_thr, 0.55)), ("A", t_thr), ("D", t_conv), ("A", mid(t_conv, t_ang, 0.5)), ("Bm", t_ang),
             ("G", mid(t_ang, t_hei, 0.45)), ("DF", t_hei), ("Em", mid(t_hei, t_fin, 0.4)), ("A", mid(t_hei, t_fin, 0.75)), ("D", t_fin)]
    s.ramp(10, 40, 100, t_conv, t_fin)
    for i, (name, a) in enumerate(major[:-1]):
        b = major[i + 1][1]
        s.chord(0, CH[name], a, b - a + 0.15, 58 + i * 2)
        if a >= t_conv - 0.1:
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
    s.melody(8, [("A4", 1), ("B4", 1), ("C#5", 1), ("D5", 1), ("E5", 2), ("F#5", 3)], mid(t_ang, t_hei, 0.45), beatR, vel=70)
    t_roll = mid(t_hei, t_fin, 0.75)
    for k in range(int(max(0.4, t_fin - t_roll) / 0.08)):
        s.note(11, "A1", t_roll + k * 0.08, 0.07, 60 + k * 3)
    # final line: the love motif in full orchestra and choir, resolving on D as the line ends
    beatF = (t_last_end - t_fin) / 7.0
    fin = [("F#4", 1.5), ("G4", 0.5), ("A4", 2), ("B4", 1), ("A4", 1), ("D5", 4)]
    s.melody(8, fin, t_fin, beatF, vel=80)
    s.melody(10, fin, t_fin, beatF, vel=78)
    s.melody(6, fin, t_fin, beatF, vel=64, transpose=12)
    t_end8 = cue["dawn"] + 2.5
    for name, a, b in [("D", t_fin, t_fin + 2 * beatF), ("Bm", t_fin + 2 * beatF, t_fin + 4 * beatF), ("G", t_fin + 4 * beatF, t_fin + 5 * beatF),
                       ("A", t_fin + 5 * beatF, t_fin + 6 * beatF), ("D", t_fin + 6 * beatF, t_end8)]:
        s.chord(0, CH[name] + [P(CH[name][2]) + 12], a, b - a + 0.1, 74)
        s.note(3, BASS[name], a, b - a, 72)
        s.chord(10, CH[name][1:], a, b - a, 70)
    s.note(11, "D2", t_fin + 6 * beatF, 2.0, 100)
    s.chord(4, ["D3", "A3", "D4", "F#4", "A4", "D5", "F#5", "A5", "D6"], t_fin + 6 * beatF, 4.0, 60, roll=0.05)
    s.ramp(0, 100, 50, t_end8 - 3.5, t_end8)
    s.ramp(10, 100, 30, t_end8 - 3.5, t_end8)

    # ------------------------------------------------------------- DAWN
    t0 = cue["dawn"]
    beatD = 60 / 66
    t_card = SH("end_card")
    s.cc(0, 11, 70, t0)
    nb = max(4, min(8, int((t_card - t0 - 3.5) / (4 * beatD))))
    pad(s, 1, ["D", "G", "D", "A", "Bm", "G", "D", "A"][:nb], t0 + 0.5, 4 * beatD, vel=40, harp=beatD / 2, harp_vel=32, bass_vel=30)
    s.melody(6, [(p[:-1] + str(int(p[-1]) + 1), b) for p, b in LOVE_A], t0 + 0.5 + 4 * beatD, beatD, vel=46)
    s.chord(1, CH["G"], t_card - 3.0, 3.0, 40)
    s.chord(1, CH["D"] + ["A4", "D5"], t_card, tl["duration"] - t_card + 0.2, 44)
    s.note(3, "D2", t_card, tl["duration"] - t_card + 0.2, 36)
    s.chord(4, ["D3", "A3", "D4", "F#4", "A4", "D5"], t_card, 6.0, 44, roll=0.12)
    s.ramp(1, 90, 0, t_card + 3.5, tl["duration"] + 0.3)
    s.ramp(4, 90, 0, t_card + 4.0, tl["duration"] + 0.3)
    return s


# --------------------------------------------------------------------------- deep swells
SWELL_PROG = {0: 43, 1: 42, 2: 48, 3: 58, 4: 47, 5: 43, 6: 42, 7: 48, 8: 58, 10: 47}


def compose_swells(tl):
    """Slow crescendo-decrescendo of low strings, tuba and a soft timpani roll under the heaviest
    lines. Two channel sets alternate so neighbouring swells never fight over the same controls."""
    s = Score()
    lines = tl["lines"]

    def LN(who, prefix, end=False):
        for ln in lines:
            if ln["who"] == who and ln["text"].startswith(prefix):
                return ln["end"] if end else ln["start"]
        raise KeyError(f"{who}: {prefix}")

    # (who, line prefix, root, peak position within the line 0..1, strength 0..1)
    cues = [
        ("narrator", "His name is Paul", "D", 0.75, 0.7),
        ("narrator", "When he was a boy", "Bb", 0.8, 0.75),
        ("phoebe", "If your enemy", "D", 0.6, 0.6),
        ("asher", "You dragged a man", "D", 1.0, 0.8),
        ("asher", "He never came home", "A", 0.6, 0.9),
        ("child", "Father! Don't go", "D", 0.6, 0.85),
        ("asher", "You don't get to remember", "D", 0.7, 0.8),
        ("asher", "but you weren't acting like a saint", "Bb", 0.8, 0.8),
        ("paul", "I was a blasphemer", "D", 0.9, 0.85),
        ("saul", "Who is this? Is this the Lord?", "D", 0.8, 0.85),
        ("asher", "And taking my father out of my life", "D", 0.85, 0.85),
        ("paul", "of whom I am among the worst", "A", 0.7, 0.75),
        ("asher", "but I don't think I will ever love you", "D", 0.8, 0.75),
        ("asher", "I am not your brother", "Bb", 0.7, 0.75),
        ("asher", "I don't forgive you", "A", 0.7, 0.75),
        ("paul", "Burning coals", "D", 0.7, 0.7),
        ("guard", "And you, old man", "D", 0.75, 1.0),
        ("paul", "we are considered as sheep", "D", 0.8, 0.9),
        ("narrator", "At first light, the old man", "D", 0.75, 1.0),
    ]
    sets = [(0, 1, 2, 3, 4), (5, 6, 7, 8, 10)]
    # Romans 8: one long deep swell under the whole passage, from "For I am convinced" to the end of
    # "...the love of the Lord our God", cresting on "neither height nor depth"
    a8, b8 = LN("paul", "For I am convinced"), LN("paul", "will be able to separate", True)
    pk8 = LN("paul", "neither height")
    cb, cc, cs, ct, cti = sets[1]
    for ch in (cb, cc, cs, ct):
        s.cc(ch, 11, 0, a8 - 2.05)
        s.ramp(ch, 10, 112, a8 - 2.0, pk8 + 1.5)
        s.ramp(ch, 112, 70, pk8 + 1.5, b8)
        s.ramp(ch, 70, 0, b8, b8 + 3.0)
    r1, r2 = P("D1"), P("D2")
    s.note(cb, r1, a8 - 2.0, b8 + 3.0 - (a8 - 2.0), 104)
    s.note(cb, r2, a8 - 2.0, b8 + 3.0 - (a8 - 2.0), 88)
    s.chord(cc, [r2, r2 + 7], a8 - 2.0, b8 + 3.0 - (a8 - 2.0), 90)
    s.chord(cs, [r2, r2 + 12], a8 - 2.0, b8 + 3.0 - (a8 - 2.0), 76)
    s.note(ct, r2, a8 - 1.5, b8 + 2.5 - (a8 - 1.5), 70)
    n8 = int(2.6 / 0.08)
    for j in range(n8):
        tt = pk8 + 1.5 - 2.6 + j * 0.08
        s.note(cti, r2, tt, 0.07, int(30 + 70 * (j / n8)))
    for i, (who, pre, root, pk, k) in enumerate(cues):
        a, b = LN(who, pre), LN(who, pre, True)
        t0 = a - 1.6
        tp = a + (b - a) * pk
        t1 = b + 3.2
        cb, cc, cs, ct, cti = sets[i % 2]
        r1, r2 = P(root + "1"), P(root + "2")
        fifth = r2 + 7
        for ch in (cb, cc, cs, ct):
            s.cc(ch, 11, 0, t0 - 0.05)
            s.ramp(ch, 10, int(60 + 50 * k), t0, tp)
            s.ramp(ch, int(60 + 50 * k), 0, tp, t1)
        s.note(cb, r1, t0, t1 - t0, 96)
        s.note(cb, r2, t0, t1 - t0, 80)
        s.chord(cc, [r2, fifth], t0, t1 - t0, 84)
        s.chord(cs, [r2, r2 + 12], t0, t1 - t0, 70)
        s.note(ct, r2, t0 + 0.4, t1 - t0 - 0.4, 62)
        # soft timpani roll into the peak
        n = int(1.8 / 0.09)
        for j in range(n):
            tt = tp - 1.8 + j * 0.09
            s.note(cti, r2, tt, 0.08, int(25 + 55 * k * (j / n)))
    return s


# high swells: violins and a soft choir rising in open fifths over the most hopeful moments
HIGH_PROG = {0: 49, 1: 52, 2: 48, 3: 49, 4: 52, 5: 48}


def compose_high(tl):
    """A slow rise and fall of high strings (with a quiet choir) at the turning points of grace:
    the light on the Damascus road, the remembered new commandment, Romans 8, and the dawn prayer.
    Open fifths only, so they sit over any harmony of the score without clashing."""
    s = Score()
    lines = tl["lines"]

    def LN(who, prefix):
        for ln in lines:
            if ln["who"] == who and ln["text"].startswith(prefix):
                return ln["start"], ln["end"]
        raise KeyError(f"{who}: {prefix}")

    cues = [
        ("jesus", "Open your heart to me", "D", 0.85, 0.8),
        ("jesus", "Asher, here is a new commandment", "D", 0.75, 0.85),
        ("paul", "No! I say to you", "D", 0.55, 0.75),
        ("paul", "will be able to separate us", "D", 0.8, 0.9),
        ("asher", "Lord... I don't know how to love", "A", 0.7, 0.65),
    ]
    sets = [(0, 1, 2), (3, 4, 5)]
    for i, (who, pre, root, pk, k) in enumerate(cues):
        a, b = LN(who, pre)
        t0, tp, t1 = a - 1.2, a + (b - a) * pk, b + 3.6
        cv, cc, cs = sets[i % 2]
        r = P(root + "4")
        for ch in (cv, cc, cs):
            s.cc(ch, 11, 0, t0 - 0.05)
            s.ramp(ch, 6, int(52 + 48 * k), t0, tp)
            s.ramp(ch, int(52 + 48 * k), 0, tp, t1)
        s.chord(cv, [r + 12, r + 19, r + 24], t0, t1 - t0, 78)
        s.chord(cc, [r + 7, r + 12], t0 + 0.3, t1 - t0 - 0.3, 64)
        s.chord(cs, [r, r + 7], t0, t1 - t0, 58)
    return s


def render(work):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    s = compose(tl)
    mid = os.path.join(work, "music.mid")
    s.write(mid, tl["duration"] + 3)
    sw = compose_swells(tl)
    mid2 = os.path.join(work, "swells.mid")
    sw.write(mid2, tl["duration"] + 3, progs=SWELL_PROG)
    raw2 = os.path.join(work, "swells_raw.wav")
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.7", "-r", "48000", "-o", "synth.reverb.active=1",
                    "-o", "synth.reverb.room-size=0.7", "-o", "synth.reverb.level=0.35", "-o", "synth.chorus.active=0",
                    "-F", raw2, SF2, mid2], check=True)
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
    # the deep swells, mixed under the score (kept clear of the voice band, felt more than heard)
    y, sr2 = sf.read(raw2, dtype="float64")
    y = audiofx.butter(y, sr2, "lowpass", 900)
    pk_s = np.max(np.abs(y)) + 1e-9
    pk_m = np.max(np.abs(out)) + 1e-9
    m2 = min(n, len(y))
    out[:m2] += y[:m2] * (0.55 * pk_m / pk_s)
    os.remove(raw2)
    # the high swells: airy, above the voices' warmth (high-passed), softer than the score
    hi = compose_high(tl)
    mid3 = os.path.join(work, "high.mid")
    hi.write(mid3, tl["duration"] + 3, progs=HIGH_PROG)
    raw3 = os.path.join(work, "high_raw.wav")
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.6", "-r", "48000", "-o", "synth.reverb.active=1",
                    "-o", "synth.reverb.room-size=0.85", "-o", "synth.reverb.level=0.55", "-o", "synth.chorus.active=0",
                    "-F", raw3, SF2, mid3], check=True)
    z, sr3 = sf.read(raw3, dtype="float64")
    z = audiofx.butter(z, sr3, "highpass", 260)
    pk_h = np.max(np.abs(z)) + 1e-9
    m3 = min(n, len(z))
    out[:m3] += z[:m3] * (0.36 * pk_m / pk_h)
    os.remove(raw3)
    pk = np.max(np.abs(out))
    out *= 0.9 / max(pk, 1e-6)
    sf.write(os.path.join(work, "music.wav"), out.astype(np.float32), sr)
    print("music rendered", out.shape[0] / sr, "s")


if __name__ == "__main__":
    render(os.environ.get("BFE_WORK", os.path.join(HERE, "..", ".bfe_work")))
