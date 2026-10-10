"""Master timeline for 'The Assembly' -> timeline.json"""
import json
from lines import LINES

DUR = {k: v["dur"] for k, v in json.load(open("audio/voice/durations.json")).items()}


class TL:
    def __init__(self):
        self.t = 0.0
        self.scenes, self.lines, self.sfx, self.music, self.markers = [], [], [], [], {}

    def scene(self, name):
        if self.scenes:
            self.scenes[-1]["end"] = self.t
        self.scenes.append({"name": name, "start": self.t, "end": None})
        self.markers[name] = self.t

    def say(self, lid, gap=0.25, at=None):
        st = self.t if at is None else at
        spk, text, cap, speed = LINES[lid]
        d = DUR[lid]
        self.lines.append({"id": lid, "spk": spk, "start": st, "dur": d, "cap": cap or text})
        self.markers[lid] = st
        self.markers[lid + "_end"] = st + d
        if at is None:
            self.t = st + d + gap
        return st

    def wait(self, s):
        self.t += s

    def mark(self, name, at=None):
        self.markers[name] = self.t if at is None else at

    def fx(self, name, gain=1.0, at=None, off=0.0):
        self.sfx.append({"name": name, "start": (self.t if at is None else at) + off, "gain": gain})

    def mus(self, track, start, end, gain=1.0, fin=0.05, fout=0.6, level=-27):
        self.music.append({"track": track, "start": start, "end": end, "gain": gain, "fin": fin, "fout": fout, "level": level})

    def done(self):
        self.scenes[-1]["end"] = self.t
        return {"scenes": self.scenes, "lines": self.lines, "sfx": self.sfx, "music": self.music,
                "markers": self.markers, "duration": self.t}


T = TL()
M = T.markers

# ---------------------------------------------------------------- 1. office: the plan
T.scene("office")
T.wait(2.6)   # title card over the office
T.say("N1", 0.3)
T.say("O1", 0.25)
T.say("O2", 0.3)
T.say("O3", 0.25)
T.say("O4", 0.1)
T.mark("fistbump"); T.fx("thud", 0.5); T.fx("sparkle", 0.3, off=0.1)
T.wait(1.0)
T.mus("office", 0, T.t, 0.8, fout=0.8)

# ---------------------------------------------------------------- 2. the stands
T.scene("stands")
assembly_start = T.t
T.fx("murmur", 0.5)
T.say("N2", 0.3)
T.say("S1", 0.3)
T.say("S2", 0.3)
T.say("S3", 0.4)

# ---------------------------------------------------------------- 3. LOSERS! ... silence
T.scene("losers")
T.fx("mic_feedback", 0.3)
T.say("T1", 0.4)
T.say("T2", 0.1)
T.fx("giggle_few", 0.6, off=0.05)
T.mark("scratch", T.t + 0.55); T.fx("record_scratch", 0.8, at=T.t + 0.55)
T.mus("assembly", assembly_start, T.t + 0.6, 0.7, fin=0.5, fout=0.05)
T.wait(0.7)
T.mark("stare")
T.fx("clock_ticks", 0.6)
T.wait(2.6)
T.say("T3", 0.1)
T.mark("friends_scoot")
T.wait(3.0)
T.mark("cough"); T.fx("cough", 0.7)
T.wait(1.0)
T.mark("resume")
T.say("T4", 0.3)
resume_start = T.t - 0.5

T.scene("crisis")
T.say("T5", 0.5)
T.mus("assembly", resume_start, T.t, 0.55, fin=0.3, fout=0.3)

# ---------------------------------------------------------------- 4. the hat
T.scene("hat")
hat_start = T.t
T.say("H1", 0.3)
T.mark("draw")
T.wait(0.4)
T.say("H2", 0.3)
T.mark("all_carter", M["H2_end"] + 0.1)
T.fx("vine_boom", 0.5, at=M["H2_end"])
T.say("H3", 0.25)
T.say("H4", 0.2)
T.fx("footsteps", 0.6)
T.mus("playful", hat_start, T.t, 0.5, fin=0.3, fout=0.2)

# ---------------------------------------------------------------- 5. carried out of the stands
T.scene("carry")
carry_start = T.t
T.say("H5", 0.15)
T.mark("lift")
T.fx("pig_squeal", 0.75, off=0.1)
T.say("H6", 0.2)
T.fx("pig_squeal", 0.6)
T.fx("murmur", 0.5, off=0.2)
T.say("H7", 0.15)
T.say("H8", 0.3)
T.mark("plop"); T.fx("thud", 0.7)
T.wait(0.8)
T.mus("epic", carry_start, T.t - 0.3, 0.8, fin=0.1, fout=0.2, level=-24)

# ---------------------------------------------------------------- 6. the stool, the eyes
T.scene("stool")
T.say("U1", 0.3)
T.mark("glasses_off"); T.fx("sparkle", 0.6); T.fx("angelic", 0.35, off=0.1)
T.wait(1.4)
T.say("U2", 0.4)
T.say("U3", 0.4)
T.say("U4", 0.4)

# ---------------------------------------------------------------- 7. the role play
T.scene("roleplay")
play_start = T.t
T.say("R1", 0.3)
T.say("R2", 0.3)
T.say("R3", 0.3)
T.mark("carter_chuckle"); T.fx("heh", 0.7); T.fx("giggle_few", 0.4, off=0.2)
T.wait(0.9)
T.say("R4", 0.3)
T.say("R5", 0.3)
T.say("R6", 0.1); T.fx("tiny_beep", 0.5, at=M["R6_end"] + 0.03)
T.wait(0.4)
T.mark("cheer"); T.fx("applause", 0.4)
T.say("R7", 0.5)
T.mus("playful", play_start, T.t, 0.6, fin=0.4, fout=0.3)

# ---------------------------------------------------------------- 8. they bomb (on purpose); Carter saves them
T.scene("bomb")
T.say("B1", 0.1)
T.fx("crickets", 0.6, off=0.1)
T.wait(1.6)
T.fx("cough", 0.4)
T.wait(0.5)
T.say("B2", 0.4)
T.say("B3", 0.3)

T.scene("saves")
funk_start = T.t
T.say("B4", 0.1)
T.fx("laugh_big", 0.8)
T.wait(1.4)
T.say("B5", 0.1)
T.fx("laugh_huge", 0.85)
T.mark("glance1", T.t + 1.0); T.fx("sparkle", 0.25, at=T.t + 1.1)
T.wait(3.2)
T.mus("funk", funk_start, T.t, 0.75, fin=0.2, fout=0.5)

# ---------------------------------------------------------------- 9. afterwards
T.scene("after")
T.say("A1", 0.3)
T.say("A2", 0.3)
T.say("A3", 0.4)
T.mark("carter_leaves"); T.fx("footsteps", 0.4)
T.wait(0.8)
T.say("A4", 0.3)
T.say("A5", 0.6)

# ---------------------------------------------------------------- 10. the next assembly: the reveal
T.scene("assembly2")
T.say("N3", 0.3)
T.say("C1", 0.1)
T.fx("crickets", 0.6, off=0.1)
T.wait(1.5)
T.say("C2", 0.2)
T.mark("now"); T.fx("ding", 0.4)
T.wait(0.8)
reveal_start = T.t
T.say("C3", 0.2)
T.say("C4", 0.05)
T.mark("bigbit"); T.fx("rimshot", 0.7); T.fx("laugh_huge", 0.95, off=0.2); T.fx("applause", 0.5, off=0.8)
T.wait(3.0)
T.say("C5", 0.3)
T.say("C6", 0.4)
T.mus("funk", reveal_start, T.t, 0.7, fin=0.05, fout=0.4)

# ---------------------------------------------------------------- 11. the solo act, the empty feeling
T.scene("solo")
T.say("D1", 0.3)
sad_start = T.t
T.mark("montage")
T.fx("laugh_hollow", 0.55, off=0.2)
T.fx("laugh_hollow", 0.45, off=3.2)
T.wait(0.5)
T.say("D2", 0.5)
T.say("D3", 0.6)

T.scene("door")
T.fx("footsteps", 0.5)
T.wait(1.2)
T.say("D4", 0.2)
T.mark("door_open"); T.fx("door_creak", 0.6)
T.mus("sad_piano", sad_start, T.t + 0.3, 0.7, fin=0.6, fout=0.8, level=-25)
warm_start = T.t
T.wait(0.6)
T.say("D5", 0.3)
T.say("D6", 0.4)
T.say("D7", 0.6)

# ---------------------------------------------------------------- 12. the roast deal; the heckler; Carter has their backs
T.scene("roast")
T.say("E1", 0.3)
T.say("E2", 0.1)
T.fx("laugh_big", 0.8)
T.mark("chad_laughs")
T.wait(1.6)
T.mus("outro", warm_start, T.t, 0.6, fin=0.8, fout=0.6)
T.mark("heckle")
T.say("E3", 0.2)
T.fx("murmur_gasp", 0.6)
T.mark("bros_look", T.t + 0.2)
T.wait(1.8)

T.scene("defend")
sincere_start = T.t
T.wait(0.5)
T.say("E4", 0.4)
T.say("E5", 0.6)
T.mark("knowing")
T.say("E6", 0.2)
T.say("E7", 0.8)

T.scene("end")
T.wait(5.0)
T.mus("sincere", sincere_start, T.t, 0.7, fin=0.8, fout=1.5, level=-25)

out = T.done()
json.dump(out, open("timeline.json", "w"), indent=1)
print("duration", round(out["duration"], 2))
for s in out["scenes"]:
    print(f"  {s['name']:10s} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end']-s['start']:.1f}s)")
