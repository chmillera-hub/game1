"""Compose the underscore as MIDI against the dialogue timeline, then render it with FluidSynth.

/opt/tts/bin/python score.py  ->  /opt/work/audio/score.mid, /opt/work/audio/music.wav
Tempo is fixed at 60 BPM so one beat == one second and events can be placed at timeline seconds.
High notes land on hopeful words, low notes on heavy ones (ACCENTS below).
"""
import json, re, subprocess
import mido

TL = json.load(open("/opt/work/timeline.json"))
LINES = {l["id"]: l for l in TL["lines"]}
END = TL["duration"]
TPB = 480
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
        "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
QUAL = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "m7": (0, 3, 7, 10), "maj7": (0, 4, 7, 11),
        "sus4": (0, 5, 7), "7sus4": (0, 5, 7, 10), "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14), "sus2": (0, 2, 7)}

# channel: (program, volume, pan, reverb)
CH = {
    "piano": (0, 0, 92, 60, 70), "pad": (1, 49, 70, 64, 90), "cello": (2, 42, 88, 50, 70),
    "bass": (3, 43, 90, 64, 60), "choir": (4, 52, 72, 70, 100), "celesta": (5, 8, 70, 80, 100),
    "flute": (6, 73, 70, 56, 90), "horn": (7, 60, 70, 60, 80), "harp": (8, 46, 76, 44, 90),
    "timp": (10, 47, 84, 64, 60), "violin": (11, 40, 64, 70, 90), "glock": (12, 9, 52, 76, 100),
    "pizz": (13, 45, 70, 58, 60), "warm": (14, 89, 66, 64, 90),
}

events = []  # (time_sec, order, msg)
bed_events = events
acc_events = []


def ch(name):
    return CH[name][0]


def t_of(anchor):
    if isinstance(anchor, (int, float)):
        return float(anchor)
    m = re.match(r"^(L\d+[a-z]?)(?::([A-Za-z']+)(?:#(\d))?)?(\.e)?([+-]\d+(?:\.\d+)?)?$", anchor)
    lid, word, nth, end, off = m.groups()
    l = LINES[lid]
    if word:
        k = int(nth or 1)
        hits = [w for w in l["words"] if re.sub(r"[^a-z']", "", w["word"].lower()) == word.lower()]
        w = hits[min(k, len(hits)) - 1] if hits else None
        t = (w["end"] if end else w["start"]) if w else l["start"]
    else:
        t = l["end"] if end else l["start"]
    return t + (float(off) if off else 0.0)


def note(name, pitch, t0, dur, vel):
    c = ch(name)
    vel = int(max(1, min(127, vel)))
    events.append((t0, 1, mido.Message("note_on", channel=c, note=int(pitch), velocity=vel)))
    events.append((t0 + max(0.05, dur), 0, mido.Message("note_off", channel=c, note=int(pitch), velocity=0)))


def cc(name, num, t, val):
    events.append((t, 0, mido.Message("control_change", channel=ch(name), control=num, value=int(max(0, min(127, val))))))


def ramp(name, t0, t1, v0, v1, num=11, steps=None):
    steps = steps or max(2, int((t1 - t0) * 10))
    for i in range(steps + 1):
        u = i / steps
        cc(name, num, t0 + (t1 - t0) * u, v0 + (v1 - v0) * u)


def chord_pitches(sym, octave=3):
    m = re.match(r"^([A-G][b#]?)(m7|maj7|7sus4|sus4|sus2|madd9|add9|m|7)?(?:/([A-G][b#]?))?$", sym)
    root, q, bass = m.group(1), m.group(2) or "", m.group(3)
    r = NOTE[root] + 12 * (octave + 1)
    ps = [r + i for i in QUAL[q]]
    b = NOTE[bass or root] + 12 * (octave)
    return ps, b


def pad_chord(sym, t0, t1, vel=50, inst=("pad",), octave=4, bass=True, cello=True, bassvel=None):
    ps, b = chord_pitches(sym, octave)
    for inst_name in inst:
        for p in ps:
            note(inst_name, p, t0, t1 - t0 + 0.25, vel)
    if cello:
        note("cello", b + 12, t0, t1 - t0 + 0.2, (bassvel or vel) - 4)
    if bass:
        note("bass", b, t0, t1 - t0 + 0.2, (bassvel or vel) - 8)


def arpeggio(sym, t0, t1, step=0.5, inst="harp", vel=48, octave=4, pattern=(0, 1, 2, 3, 2, 1)):
    ps, _ = chord_pitches(sym, octave)
    ps = ps + [p + 12 for p in ps]
    t = t0
    i = 0
    while t < t1 - 0.05:
        p = ps[pattern[i % len(pattern)] % len(ps)]
        note(inst, p, t, step * 2.2, vel + (6 if i % len(pattern) == 0 else 0))
        t += step
        i += 1


def melody(inst, seq, t0, vel=60, legato=1.05):
    """seq: list of (pitch_name_with_octave or None, beats)."""
    t = t0
    for nm, d in seq:
        if nm:
            m = re.match(r"([A-G][b#]?)(\d)", nm)
            p = NOTE[m.group(1)] + 12 * (int(m.group(2)) + 1)
            note(inst, p, t, d * legato, vel)
        t += d
    return t


def progression(chords, t0, t1, **kw):
    """chords: list of (symbol, start_anchor) or evenly spread list of symbols."""
    if chords and isinstance(chords[0], str):
        step = (t1 - t0) / len(chords)
        chords = [(c, t0 + i * step) for i, c in enumerate(chords)]
    times = [t_of(a) for _, a in chords] + [t1]
    for (sym, _), a, b in zip(chords, times[:-1], times[1:]):
        pad_chord(sym, a, b, **kw)
    return list(zip([c for c, _ in chords], times[:-1], times[1:]))


def chord_at(prog, t):
    for sym, a, b in prog:
        if a <= t < b:
            return sym
    return prog[-1][0]


# ---------------------------------------------------------------------------- accents
HIGH = [("L007:know", 1), ("L007:follow", 1), ("L008:eternal", 2), ("L008:life", 1), ("L008:never", 1),
        ("L010:greater", 1), ("L012:one", 3), ("L021:believe#2", 1), ("L022:know", 1), ("L022:understand", 2),
        ("L026:eyes", 1), ("L031b:prayed", 1), ("L033:believe", 1), ("L035:me", 2), ("L036:one", 1),
        ("L037:believe", 1), ("L038:glory", 2), ("L038:one", 1), ("L039:unity", 2), ("L044:open", 2),
        ("L045:loved", 1), ("L045:loved#2", 2), ("L046:glory", 1), ("L047:glory", 2), ("L047:loved", 2),
        ("L047:creation", 3), ("L048:know#2", 2), ("L049:know", 1), ("L050:known", 1), ("L050:known#2", 1),
        ("L051:love", 3), ("L052:believe", 1)]
LOW = [("L004:not", 1), ("L006:not", 1), ("L009:snatch", 1), ("L011:snatch", 1), ("L013:stones", 2),
       ("L014:stone", 1), ("L015:blasphemy", 2), ("L019:blasphemy", 1), ("L023:take", 2), ("L024:seize", 2),
       ("L024:grasp", 2), ("L025:stone", 1), ("L026:blind", 1), ("L027:killed", 1), ("L031:cross", 2),
       ("L041:funeral", 1), ("L048:not", 2)]


def accents(prog):
    global events
    events = acc_events
    for name, (c, prg, vol, pan, rev) in CH.items():
        acc_events.append((0.0, -1, mido.Message("program_change", channel=c, program=prg)))
        cc(name, 7, 0.0, vol)
        cc(name, 10, 0.0, pan)
        cc(name, 91, 0.0, rev)
        cc(name, 11, 0.0, 110)
    for anchor, strength in HIGH:
        t = t_of(anchor) + 0.12
        ps, _ = chord_pitches(chord_at(prog, t), 6)
        top = ps[0] if strength < 3 else ps[0] + 12
        for i, inst in enumerate(("celesta", "violin") if strength >= 2 else ("celesta",)):
            note(inst, top - (12 if inst == "violin" else 0), t, 1.6 + strength * 0.6, 48 + strength * 9)
        if strength >= 2:
            note("glock", ps[2] if len(ps) > 2 else top, t + 0.05, 1.2, 44 + strength * 8)
        if strength >= 3:
            note("choir", top - 12, t, 3.5, 70)
    for anchor, strength in LOW:
        t = t_of(anchor)
        _, b = chord_pitches(chord_at(prog, t), 2)
        note("bass", b, t, 1.6 + strength * 0.5, 62 + strength * 10)
        note("cello", b + 12, t, 1.4 + strength * 0.5, 52 + strength * 8)
        note("timp", b + 12, t, 1.2, 46 + strength * 14)


# ---------------------------------------------------------------------------- the score
def compose():
    for name, (c, prog, vol, pan, rev) in CH.items():
        events.append((0.0, -1, mido.Message("program_change", channel=c, program=prog)))
        cc(name, 7, 0.0, vol)
        cc(name, 10, 0.0, pan)
        cc(name, 91, 0.0, rev)
        cc(name, 93, 0.0, 30)
        cc(name, 11, 0.0, 100)
    prog = []
    # --- A: the colonnade, D minor, winter --------------------------------------------------
    A_end = t_of("L012-0.1")
    prog += progression([("Dm", 0.0), ("Dm/C", "L003"), ("Bbmaj7", "L004"), ("Gm7", "L005"), ("A7sus4", "L006"),
                         ("A7", "L006:sheep-0.4"), ("F", "L007"), ("C/E", "L007:know"), ("Bb", "L008"),
                         ("F/A", "L008:never"), ("Gm", "L009"), ("Bb", "L010"), ("C", "L010:greater"),
                         ("Dm", "L011")], 0.0, A_end, vel=40, inst=("pad",), octave=4)
    ramp("pad", 0.0, 6.0, 60, 92)
    melody("piano", [("A4", 1.5), ("F4", 1.0), ("E4", 1.0), ("D4", 2.5), (None, 1.0), ("A3", 1.0), ("D4", 1.0),
                     ("E4", 1.0), ("F4", 2.5)], 0.4, vel=52)
    arpeggio("F", t_of("L007"), t_of("L008"), step=0.36, vel=40)
    arpeggio("Bb", t_of("L008"), t_of("L009"), step=0.4, vel=38)
    melody("flute", [("C5", 0.8), ("D5", 0.8), ("F5", 1.6), ("E5", 1.2)], t_of("L007:know"), vel=48)
    # "I and the Father are one": everything drops to a low drone and one high voice
    prog += [("Dm", A_end, t_of("L013"))]
    note("bass", 38, A_end, t_of("L013") - A_end, 52)
    note("cello", 50, A_end + 0.5, t_of("L013") - A_end - 0.5, 40)
    ramp("cello", A_end, t_of("L013"), 70, 110)
    # --- B: the stones ------------------------------------------------------------------------
    B0, B1 = t_of("L013"), t_of("L016")
    prog += progression([("Dm", B0), ("Bb/D", "L014"), ("Gm/D", "L014:which"), ("Dm", "L015"), ("A7", "L015:claim")],
                        B0, B1, vel=44, inst=("pad",), octave=3)
    t = B0
    while t < B1 - 0.2:  # low tremolo pulse, rising tension
        note("pizz", 38 if int((t - B0) * 2) % 2 == 0 else 39, t, 0.3, 40 + (t - B0) * 1.4)
        t += 0.5
    ramp("timp", t_of("L015"), t_of("L015.e"), 60, 120)
    for k in range(int((t_of("L015.e") - t_of("L015:claim")) / 0.18)):
        note("timp", 50, t_of("L015:claim") + k * 0.18, 0.2, 40 + k * 2)
    # --- C: reasoning, toward light --------------------------------------------------------------
    C0, C1 = t_of("L016"), t_of("L022.e+0.2")
    prog += progression([("Dmadd9", C0), ("Bb", "L017"), ("F/A", "L018"), ("Bb", "L018:sent"), ("Gm", "L019"),
                         ("A7", "L019:said"), ("Dm", "L020"), ("Bb", "L020:works"), ("F", "L021"), ("C", "L021:believe#2"),
                         ("Bb", "L022"), ("C", "L022:understand"), ("F", "L022:Father")], C0, C1, vel=42,
                        inst=("pad", "warm"), octave=4)
    arpeggio("Dmadd9", C0, t_of("L017"), step=0.45, vel=34)
    ramp("pad", t_of("L021"), t_of("L022:Father"), 80, 112)
    melody("violin", [("A5", 1.0), ("C6", 1.0), ("F6", 2.5)], t_of("L022:understand"), vel=50)
    # stone drop: silence, one low piano note on the crack
    drop_t = t_of("L022.e+0.45")
    note("piano", 26, drop_t, 3.0, 70)
    note("piano", 38, drop_t, 3.0, 50)
    prog += [("Dm", C1, t_of("L023"))]
    # --- D: "Take him" / seize / aftermath ------------------------------------------------------
    D0 = t_of("L023")
    note("timp", 38, D0, 1.5, 100)
    note("bass", 26, D0, 1.2, 96)
    prog += progression([("Dm", "L024"), ("Eb/D", "L024:but"), ("Dm", "L024:grasp")], t_of("L024"), t_of("L025"),
                        vel=50, inst=("pad",), octave=3)
    t = t_of("L024")
    while t < t_of("L024:grasp"):
        note("pizz", 50 + [0, 3, 7, 3][int((t - t_of("L024")) / 0.25) % 4], t, 0.2, 70)
        t += 0.25
    prog += progression([("Dmadd9", "L025-0.3"), ("Bbmaj7", "L026"), ("Gm", "L026:eyes")], t_of("L025-0.3"),
                        t_of("L027-0.6"), vel=34, inst=("pad",), octave=4, bass=False)
    melody("piano", [("D5", 1.5), ("C5", 1.0), ("A4", 2.0), (None, 0.5), ("F4", 1.0), ("E4", 2.5)], t_of("L025"), vel=44)
    # --- E: the street ----------------------------------------------------------------------------
    E0, E1 = t_of("L027-0.6"), t_of("L031-0.5")
    prog += progression([("Am", E0), ("F", "L028"), ("C", "L029"), ("Gsus4", "L030"), ("G", "L030:afraid"),
                         ("A", "L030.e+0.8")], E0, E1, vel=38, inst=("pad",), octave=4)
    melody("flute", [("E5", 1.0), ("D5", 0.5), ("C5", 0.5), ("D5", 2.0)], t_of("L030"), vel=50)
    arpeggio("A", t_of("L030.e+0.8"), E1, step=0.18, vel=40, octave=4, pattern=(0, 1, 2, 3, 4, 5, 6, 7))
    # --- F: the upper room, D major ---------------------------------------------------------------
    F0, F1 = t_of("L031-0.5"), t_of("L034-0.2")
    prog += progression([("D", F0), ("A/C#", "L031b"), ("Bm", "L032"), ("G", "L033"), ("A", "L033:believe"),
                         ("D", "L033.e")], F0, F1, vel=40, inst=("pad", "choir"), octave=4)
    ramp("choir", F0, F0 + 4, 40, 85)
    arpeggio("D", F0, t_of("L031b"), step=0.5, inst="piano", vel=40, octave=4)
    arpeggio("Bm", t_of("L032"), t_of("L033"), step=0.5, inst="piano", vel=38, octave=4)
    melody("piano", [("F#5", 1.0), ("E5", 0.5), ("D5", 0.5), ("E5", 1.0), ("A5", 2.0)], t_of("L033"), vel=46)
    # --- G: the apartment, lonely piano -------------------------------------------------------------
    G0, G1 = t_of("L034-0.2"), t_of("L038-0.3")
    prog += progression([("Bm", G0), ("G", "L034:read"), ("D", "L035"), ("A", "L035.e+0.3"), ("Bm", "L036"),
                         ("G", "L036:Father"), ("D", "L037"), ("A", "L037:world")], G0, G1, vel=30,
                        inst=("warm",), octave=4, bass=False, cello=False)
    for sym, a, b in [p for p in prog if G0 <= p[1] < G1]:
        arpeggio(sym, a, b, step=0.55, inst="piano", vel=40, octave=3, pattern=(0, 2, 4, 2))
    melody("piano", [("D5", 1.5), ("C#5", 1.0), ("B4", 2.0), (None, 0.5), ("F#4", 1.0), ("A4", 2.5)], t_of("L036"),
           vel=48)
    # --- H: unity -----------------------------------------------------------------------------------
    H0, H1 = t_of("L038-0.3"), t_of("L040-1.2")
    prog += progression([("D", H0), ("G", "L038:glory"), ("D/F#", "L038:one"), ("Em", "L039"), ("A", "L039:unity"),
                         ("D", "L039.e")], H0, H1, vel=46, inst=("pad", "choir"), octave=4)
    ramp("pad", t_of("L038"), t_of("L039:unity"), 80, 118)
    melody("violin", [("D5", 1.0), ("F#5", 1.0), ("A5", 1.5), ("B5", 1.0), ("A5", 2.0)], t_of("L038:glory"), vel=50)
    # --- I: the call --------------------------------------------------------------------------------
    I0, I1 = t_of("L040-1.2"), t_of("L045-0.4")
    prog += progression([("Bm", I0), ("G", "L041"), ("Em", "L042"), ("A", "L043"), ("D", "L044")], I0, I1, vel=34,
                        inst=("warm", "pad"), octave=4)
    ramp("pad", t_of("L042"), t_of("L044"), 70, 110)
    melody("piano", [("B4", 1.0), ("A4", 1.0), ("F#4", 2.0), ("G4", 1.0), ("E4", 2.5)], t_of("L041"), vel=42)
    # --- J: love ------------------------------------------------------------------------------------
    J0, J1 = t_of("L045-0.4"), t_of("L047")
    prog += progression([("D", J0), ("A/C#", "L045:sent"), ("Bm", "L045:loved"), ("G", "L045:loved#2"),
                         ("D/F#", "L046"), ("Em", "L046:where"), ("A", "L046:glory")], J0, J1, vel=46,
                        inst=("pad", "choir", "warm"), octave=4)
    ramp("choir", J0, J1, 70, 115)
    melody("horn", [("D4", 2.0), ("E4", 1.0), ("F#4", 1.0), ("A4", 3.0)], t_of("L046"), vel=56)
    # --- K: before the creation of the world --------------------------------------------------------
    K0, K1 = t_of("L047"), t_of("L048-0.3")
    prog += progression([("G", K0), ("A", "L047:loved"), ("Bm", "L047:before"), ("D/F#", "L047:creation"),
                         ("G", "L047.e"), ("A", "L047.e+0.5")], K0, K1, vel=54, inst=("pad", "choir", "warm", "horn"),
                        octave=4, bassvel=70)
    ramp("timp", K0, t_of("L047:creation"), 50, 125)
    for k in range(int((t_of("L047:creation") - K0) / 0.16)):
        note("timp", 50, K0 + k * 0.16, 0.18, 30 + k * 1.2)
    melody("violin", [("D6", 1.0), ("E6", 1.0), ("F#6", 1.0), ("A6", 3.0)], t_of("L047:loved"), vel=64)
    arpeggio("D", t_of("L047:creation"), K1, step=0.15, inst="harp", vel=52, octave=5, pattern=(0, 1, 2, 3, 4, 5))
    # --- L: the city ---------------------------------------------------------------------------------
    L0, L1 = t_of("L048-0.3"), t_of("L049-0.1")
    prog += progression([("Bm", L0), ("Bm/A", "L048:world"), ("G", "L048:know#2"), ("D/F#", "L048.e")], L0, L1,
                        vel=36, inst=("pad",), octave=3)
    # --- M: they know ----------------------------------------------------------------------------------
    M0, M1 = t_of("L049-0.1"), t_of("L050-0.3")
    prog += progression([("G", M0), ("D/F#", "L049:sent")], M0, M1, vel=40, inst=("pad", "warm"), octave=4)
    # --- N: the door ---------------------------------------------------------------------------------
    N0, N1 = t_of("L050-0.3"), t_of("L051-0.3")
    prog += progression([("D", N0), ("G", "L050:continue"), ("Bm", "L050b"), ("A", "L050c"), ("D", "L050c.e+0.5")],
                        N0, N1, vel=40, inst=("pad", "warm"), octave=4)
    arpeggio("D", N0, t_of("L050:continue"), step=0.45, inst="piano", vel=40, octave=4)
    arpeggio("G", t_of("L050:continue"), t_of("L050b"), step=0.45, inst="piano", vel=40, octave=4)
    ramp("pad", t_of("L050c.e"), N1, 80, 118)
    melody("violin", [("F#5", 1.0), ("A5", 1.0), ("D6", 2.0)], t_of("L050c.e+0.4"), vel=52)
    # --- O: love, and the ending ---------------------------------------------------------------------
    O0 = t_of("L051-0.3")
    prog += progression([("D", O0), ("G", "L051:love"), ("A", "L051:them"), ("Bm", "L051:myself"), ("G", "L052"),
                         ("A", "L052:everyone"), ("D", "L052.e")], O0, END, vel=44, inst=("pad", "choir"), octave=4)
    melody("piano", [("A4", 1.0), ("D5", 1.0), ("F#5", 1.0), ("E5", 1.0), ("D5", 3.0)], t_of("L052.e"), vel=46)
    ramp("pad", END - 3.0, END, 100, 0)
    ramp("choir", END - 3.0, END, 100, 0)
    ramp("piano", END - 2.5, END, 100, 0)
    accents(sorted(prog, key=lambda p: p[1]))


def write_midi(path, evs=None):
    mid = mido.MidiFile(ticks_per_beat=TPB)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=1_000_000, time=0))
    last = 0
    for t, _, msg in sorted(evs if evs is not None else events, key=lambda e: (e[0], e[1])):
        tick = int(round(max(0.0, t) * TPB))
        msg.time = tick - last
        last = tick
        tr.append(msg)
    tr.append(mido.MetaMessage("end_of_track", time=TPB))
    mid.save(path)


def render(mid, wav):
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.6", "-r", "48000", "-R", "1", "-C", "0",
                    "-o", "synth.reverb.room-size=0.75", "-o", "synth.reverb.width=0.9",
                    "-o", "synth.reverb.level=0.6", "-o", "synth.reverb.damp=0.4",
                    "-F", wav, SF2, mid], check=True)


if __name__ == "__main__":
    compose()
    write_midi("/opt/work/audio/score.mid", bed_events)
    write_midi("/opt/work/audio/score_acc.mid", acc_events)
    render("/opt/work/audio/score.mid", "/opt/work/audio/music.wav")
    render("/opt/work/audio/score_acc.mid", "/opt/work/audio/music_acc.wav")
    print("MUSIC_OK", len(bed_events), "bed events", len(acc_events), "accent events")
