"""Score for the fantasy version, cue by cue on the fantasy timeline.

Usage: python music.py timeline.json OUT.mid   (render with fluidsynth as in build.sh)
Reuses the MIDI writer from audio/music.py and adds harp, flute and brass to
its orchestra.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "audio"))
import music as M  # noqa: E402

# channels 13-15 are free (9 is General MIDI percussion)
M.CH.update({"harp": 13, "flute": 14, "brass": 15})
M.PROG.update({"harp": 46, "flute": 73, "brass": 61})


def compose(tl):
    sc = {s["id"]: s for s in tl["scenes"]}
    ln = {l["id"]: l for l in tl["lines"]}
    S = M.Score()
    st = lambda i: ln[i]["start"]   # noqa: E731
    en = lambda i: ln[i]["end"]     # noqa: E731

    def words(i):
        return ln[i]["text"].split()

    def wt(i, w):
        """time of the first word of line i starting with w (word timings from ASR when available)"""
        l = ln[i]
        ws = words(i)
        k = next((j for j, x in enumerate(ws) if x.lower().strip(".,;:!?'\"").startswith(w)), 0)
        asr = l.get("words") or []
        if len(asr) >= 2:
            j = min(len(asr) - 1, round(k * (len(asr) - 1) / max(1, len(ws) - 1)))
            return l["start"] + asr[j][0]
        return l["start"] + (l["end"] - l["start"]) * k / max(1, len(ws))

    def pad(inst, t0, t1, chords, vel, step=4.0, roll=0.0):
        t, k = t0, 0
        while t < t1 - 0.3:
            S.chord(inst, t, min(step, t1 - t) + 0.4, chords[k % len(chords)], vel, roll)
            t += step
            k += 1

    # ------------------------------------------------ 1. the city of glass (D minor, glassy, still)
    a, b = sc["glass"]["start"], sc["glass"]["end"]
    S.cc("celesta", 0, 11, 80)
    S.arp("celesta", 0.0, b, "D5 A5 F5 E6 A5 F5", 0.5, 30, hold=1.8)
    pad("slow", 0.0, b, ["D3 A3 F4", "Bb2 F3 D4", "G2 D3 Bb3", "A2 E3 C#4"], 30, 4.0)
    S.n("bass", 0.0, b, "D2", 34)
    for t in [0.2, 4.2, 8.2, 12.2]:
        if t < b:
            S.n("chime", t, 3.0, "A5", 26)
    # "until her face ached": the smile cracks into a held dissonance
    S.chord("strings", wt("N4", "until"), en("N4") - wt("N4", "until") + 1.5, "A3 Bb3 E4", 34)

    # ------------------------------------------------ 2. the feast (warm courtly waltz, then the floor drops)
    a, b = sc["feast"]["start"], sc["feast"]["end"]
    t, k = a, 0
    waltz = [("D3", "F#3 A3 D4"), ("G2", "G3 B3 D4"), ("A2", "G3 C#4 E4"), ("D3", "F#3 A3 D4")]
    while t < st("N6") - 0.5:
        root, up = waltz[k % 4]
        S.n("bass", t, 0.9, root, 40)
        S.chord("harp", t + 0.67, 0.6, up, 34)
        S.chord("harp", t + 1.33, 0.6, up, 30)
        S.chord("strings", t, 2.0, up, 30)
        t += 2.0
        k += 1
    # the truth: only a low cello and a thin pad under her
    S.n("cello", st("N6") - 0.2, en("L4") - st("N6") + 1.0, "D2", 44)
    S.chord("slow", st("L2"), en("L2") - st("L2") + 1.0, "D3 F3 A3", 32)
    S.chord("slow", en("L2") + 1.0, en("L4") - en("L2"), "Bb2 D3 F3", 34)
    S.n("piano", en("L4") + 0.3, 3.0, "A5", 34)                             # a single cold note in the silence
    # the crack: tremolo strings and a low swell
    S.chord("strings", st("N7") - 0.3, b - st("N7") + 1.0, "D3 Eb3 A3", 42)
    S.ramp("strings", st("N7") - 0.3, b + 0.5, 40, 110)
    S.n("timp", wt("N7", "crack"), 1.5, "D2", 70)

    # ------------------------------------------------ 3. the sword (choir, brass, timpani)
    a, b = sc["sword"]["start"], sc["sword"]["end"]
    strike = wt("N8", "sword") + 0.25
    S.cc("choir", a, 11, 70)
    S.ramp("choir", a, strike, 62, 100)
    pad("choir", a, strike, ["D3 F3 A3 D4", "Bb2 F3 Bb3 D4", "F2 A3 C4 F4", "C3 G3 C4 E4"], 44, 3.6)
    pad("strings", a, strike, ["D3 A3 D4 F4", "Bb2 F3 D4 F4", "F2 C4 F4 A4", "C3 G3 E4 G4"], 36, 3.6)
    for t in [a + 0.5, a + 4.1, a + 7.7]:
        if t < strike - 0.8:
            S.n("timp", t, 1.2, "D2", 56)
    for k in range(8):                                                       # timpani roll into the strike
        S.n("timp", strike - 1.0 + k * 0.12, 0.2, "A1", 50 + k * 8)
    S.chord("brass", strike, 2.4, "D3 A3 D4 F4", 100)
    S.chord("choir", strike, 2.8, "D3 A3 D4 F4 A4", 100)
    S.n("timp", strike, 2.5, "D2", 112)
    S.n("bass", strike, 2.8, "D1", 80)
    S.n("chime", strike, 4.0, "D5", 80)
    # the household divided: a driving ostinato under N9
    t = st("N9")
    while t < en("N9"):
        for j, p in enumerate(["D3", "D3", "F3", "D3", "A3", "D3", "G3", "F3"]):
            S.n("strings", t + j * 0.25, 0.22, p, 38 + (6 if j == 0 else 0))
        t += 2.0
    pad("brass", st("N9"), en("N9"), ["D2 A2 D3", "Bb1 F2 Bb2", "C2 G2 C3", "A1 E2 A2"], 42, 2.0)
    for t in [wt("N9", "man"), wt("N9", "daughter"), wt("N9", "enemies")]:
        S.n("timp", t, 1.0, "D2", 76)
    # numb: the choir alone, cold
    pad("choir", st("N10") - 0.3, b + 0.5, ["D3 A3 E4", "Bb2 F3 D4"], 40, 4.0)
    S.ramp("choir", b - 1.5, b + 0.5, 90, 30)

    # ------------------------------------------------ 4. the hall of mirrors (music box, then the Light)
    a, b = sc["mirrors"]["start"], sc["mirrors"]["end"]
    box = [("A5", 1.0), ("F5", 0.5), ("E5", 0.5), ("D5", 1.0), ("E5", 0.5), ("F5", 0.5), ("E5", 1.5), ("C#5", 0.5),
           ("D5", 2.0)]
    t = a + 0.4
    while t < st("N12") - 1.0:
        for p, d in box:
            if t >= st("N12") - 1.0:
                break
            S.n("celesta", t, d * 1.1, p, 34)
            t += d
    pad("slow", a, st("N12"), ["D3 A3 F4", "Bb2 F3 D4"], 26, 4.0)
    # the Light arrives: warm pad, a shimmer, harp
    S.n("chime", wt("N12", "light"), 4.0, "F#5", 34)
    S.arp("harp", wt("N12", "light"), b, "D4 F#4 A4 D5 A4 F#4", 0.5, 26, hold=1.5)
    pad("pad", wt("N12", "light"), b + 1.0, ["D3 F#3 A3 D4", "B2 D3 F#3 B3", "G2 B2 D3 G3", "A2 C#3 E3 A3"], 34, 4.0)
    S.chord("strings", st("L8"), b - st("L8") + 1.5, "D4 F#4 A4", 30)

    # ------------------------------------------------ 5. the cross (hymn rising to the break, then F major)
    a, b = sc["cross"]["start"], sc["cross"]["end"]
    brk = wt("N13", "lose") - 0.1                   # "...will lose it": the mask shatters
    hymn = ["D3 F3 A3 D4", "Bb2 D3 F3 Bb3", "C3 E3 G3 C4", "F2 A2 C3 F3", "G2 Bb2 D3 G3", "A2 C#3 E3 A3"]
    t, k = a, 0
    while t < brk - 0.3:
        S.chord("choir", t, 2.6, hymn[k % len(hymn)], min(64, 42 + k * 3))
        S.chord("strings", t, 2.6, hymn[k % len(hymn)], min(56, 34 + k * 3))
        t += 2.4
        k += 1
    S.chord("choir", brk, 4.5, "F3 A3 C4 F4 A4", 92)
    S.chord("strings", brk, 4.5, "F2 C3 F3 A3 C4", 80)
    S.chord("brass", brk, 3.0, "F3 A3 C4", 70)
    S.n("chime", brk, 4.0, "C6", 70)
    S.n("timp", brk, 2.0, "F2", 90)
    pad("slow", st("N14") - 0.3, b + 1.0, ["F3 A3 C4", "D3 F3 A3", "Bb2 D3 F3", "C3 E3 G3"], 36, 3.4)
    S.arp("harp", st("N14"), b, "F3 C4 F4 A4 C5 A4 F4 C4", 0.4, 24, hold=1.2)

    # ------------------------------------------------ 6. the guildhall (mechanical, dissonant, the storm)
    a, b = sc["guild"]["start"], sc["guild"]["end"]
    storm = en("N16") - 0.2                          # the storm breaks once the narrator has named it
    t = a
    while t < storm:
        for j, p in enumerate(["E2", "E2", "F2", "E2"]):
            S.n("cello", t + j * 0.5, 0.35, p, 40)
        S.n("chime", t, 0.3, "B5", 16)
        t += 2.0
    S.chord("slow", a, storm - a, "E3 F3 B3", 26)
    # the storm: a cluster that keeps climbing, timpani roll, then nothing
    S.chord("strings", storm, b - storm + 0.2, "E3 F3 F#3 G3 B3 C4", 50)
    S.ramp("strings", storm, b, 40, 127)
    S.chord("brass", storm + 0.8, b - storm - 0.6, "E2 F2 B2", 60)
    S.ramp("brass", storm + 0.8, b, 30, 120)
    k = 0
    while storm + k * 0.1 < b - 0.2:
        S.n("timp", storm + k * 0.1, 0.12, "E2", min(110, 40 + k * 3))
        k += 1

    # ------------------------------------------------ 7. the sparrows (D major: harp, flute, strings)
    a, b = sc["sparrows"]["start"], sc["sparrows"]["end"]
    S.arp("harp", a + 0.2, b, "D3 A3 D4 F#4 A4 D5 A4 F#4", 0.35, 30, hold=1.2)
    pad("strings", a, b, ["D3 A3 F#4", "B2 F#3 D4", "G2 D3 B3", "A2 E3 C#4"], 34, 4.0)
    melody = [("F#5", 1.0), ("E5", 0.5), ("D5", 0.5), ("A5", 2.0), ("G5", 1.0), ("F#5", 0.5), ("E5", 0.5), ("D5", 2.0),
              ("B4", 1.0), ("D5", 1.0), ("E5", 2.0)]
    t = st("N18")
    for p, d in melody:
        S.n("flute", t, d * 1.05, p, 44)
        t += d
    care = wt("N18", "outside")
    S.chord("choir", care, 4.0, "D4 F#4 A4 D5", 56)
    S.n("chime", care, 3.0, "A5", 40)
    S.chord("choir", st("N20"), b - st("N20") + 1.0, "D3 A3 D4 F#4 A4", 60)
    S.chord("horn", st("N20") + 0.5, b - st("N20"), "D4 F#4 A4", 50)

    # ------------------------------------------------ 8. the scrying pool (sparse piano over water)
    a, b = sc["pool"]["start"], sc["pool"]["end"]
    pad("pad", a, b, ["B2 F#3 D4", "G2 D3 B3", "D3 A3 F#4", "A2 E3 C#4"], 26, 4.0)
    for t, p in [(st("L11") + 0.2, "B4"), (st("L12") + 0.4, "D5"), (st("L13") + 0.3, "C#5"), (st("L14") + 0.3, "B4"),
                 (st("L15") + 0.2, "A4")]:
        S.n("piano", t, 3.0, p, 34)
    S.chord("strings", st("L15"), b - st("L15") + 1.0, "D3 A3 F#4", 32)
    S.arp("celesta", st("N22") - 0.3, b, "F#5 D5 A4 D5", 0.6, 22, hold=1.4)

    # ------------------------------------------------ 9. the road (journey, building to dawn)
    a, b = sc["flight"]["start"], sc["flight"]["end"]
    dawn = wt("N23", "stands") - 0.3
    t = a
    while t < dawn:
        for j, p in enumerate(["D3", "A3", "D4", "A3"]):
            S.n("strings", t + j * 0.375, 0.34, p, 40 + int(16 * (t - a) / max(1, dawn - a)))
        S.n("timp", t, 0.4, "D2", 44)
        t += 1.5
    S.ramp("strings", a, dawn, 70, 110)
    S.n("horn", wt("N23", "you"), 3.0, "A4", 54)
    S.n("horn", wt("N23", "you") + 3.0, 2.0, "F#4", 54)
    S.chord("choir", dawn, b - dawn + 1.5, "D3 A3 D4 F#4 A4", 66)
    S.chord("strings", dawn, b - dawn + 1.5, "D2 A2 D3 F#3 A3 D4", 60)
    S.chord("brass", dawn, 3.0, "D3 F#3 A3", 80)
    S.n("timp", dawn, 2.0, "D2", 96)
    S.n("chime", dawn, 4.0, "D6", 60)
    S.ramp("choir", st("L16") - 1.5, st("L16") + 0.5, 100, 45)

    # ------------------------------------------------ 10. the next town (pastoral, then the end)
    a, e1 = sc["haven"]["start"], tl["duration"]
    S.arp("harp", a, e1 - 4.0, "D3 A3 D4 F#4 A4 F#4 D4 A3", 0.4, 26, hold=1.3)
    pad("strings", a, e1 - 4.0, ["D3 A3 F#4", "G2 D3 B3", "B2 F#3 D4", "A2 E3 C#4"], 30, 3.2)
    tune = [("A4", 1.0), ("D5", 1.0), ("F#5", 1.5), ("E5", 0.5), ("D5", 1.0), ("B4", 1.0), ("A4", 2.0)]
    t = st("N25") + 0.4
    for p, d in tune:
        S.n("flute", t, d * 1.05, p, 40)
        t += d
    horn = [("F#4", 1.5), ("E4", 0.5), ("D4", 1.0), ("A4", 2.0), ("G4", 1.0), ("F#4", 2.0)]
    t = st("N27") + 0.5
    for p, d in horn:
        S.n("horn", t, d * 1.05, p, 52)
        t += d
    S.chord("strings", e1 - 4.6, 4.6, "D3 A3 D4 F#4 A4", 52)
    S.chord("choir", e1 - 4.6, 4.6, "D3 A3 F#4", 46)
    S.n("harp", e1 - 4.4, 4.0, "D5", 50)
    S.n("bass", e1 - 4.6, 4.6, "D2", 48)
    for inst in M.CH:
        S.ramp(inst, e1 - 1.8, e1, 100, 0, ctl=7, steps=10)
    return S


def main():
    tl = json.loads(Path(sys.argv[1]).read_text())
    S = compose(tl)
    S.save(sys.argv[2])
    print("events", len(S.ev))


if __name__ == "__main__":
    main()
