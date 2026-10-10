"""Builds the master timeline (scenes, dialogue, sfx, music, markers) -> timeline.json"""
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

    def mus(self, track, start, end, gain=1.0, fin=0.05, fout=0.6, offset=0.0):
        self.music.append({"track": track, "start": start, "end": end, "gain": gain, "fin": fin, "fout": fout, "offset": offset})

    def done(self):
        self.scenes[-1]["end"] = self.t
        return {"scenes": self.scenes, "lines": self.lines, "sfx": self.sfx, "music": self.music,
                "markers": self.markers, "duration": self.t}


T = TL()
M = T.markers

# ---------------------------------------------------------------- 1. creator intro
T.scene("intro")
T.fx("typing", 0.5, off=0.2)
T.wait(0.6)
T.say("A1", 0.3)
T.mark("prompt_type"); T.fx("typing", 0.5, off=-0.1)
T.say("A2", 0.35)
T.say("A2b", 0.15)
T.mark("post_click"); T.fx("click", 0.9); T.fx("whoosh", 0.7, off=0.1)
T.wait(1.4)
T.mus("creator", 0, T.t + 3.2, 0.8, fout=1.2)

# ---------------------------------------------------------------- 2. title
T.scene("title")
T.fx("vine_boom", 0.55, off=0.05)
T.wait(0.4)
T.say("A3", 0.9)

# ---------------------------------------------------------------- 3. lord intro
T.scene("lord_intro")
lord_start = T.t
T.fx("whoosh", 0.4)
T.wait(0.7)
T.say("B1", 0.35)
T.say("B2", 0.25)
T.fx("can_clank", 0.25, at=M["B2"] + 1.6)
T.mark("plans")
T.fx("pop", 0.4, at=M["plans"] + 0.9)
T.say("B3", 0.5)
T.fx("pop", 0.4, at=M["B3"] + 3.0)
T.mark("type_comment")
T.say("P1", 0.3)
T.fx("typing", 0.5)
T.say("B4", 0.15)
T.mark("queue_removed"); T.fx("click", 0.9); T.fx("thud", 0.35, off=0.05)
T.wait(0.8)
T.say("B8", 0.3)
T.fx("knuckles", 0.9, at=M["B8"] + 0.6)
T.mark("lean_in")
T.wait(0.7)
T.mus("lord", lord_start, T.t, 0.75, fin=0.3, fout=0.15)

# ---------------------------------------------------------------- 4. the post
T.scene("post")
T.wait(0.35)
T.mark("scan_start")
T.say("C2", 0.3)
T.say("C2b", 0.3)
T.mark("stumble"); T.fx("ding", 0.7); T.fx("record_scratch", 0.25, off=0.05)
T.wait(0.7)
T.mark("notif")
T.say("B5", 0.35)
T.say("B6", 0.12)
T.say("B7", 0.25)
T.mark("snort"); T.fx("snort", 0.8)
T.wait(0.6)
T.mark("read_start"); T.fx("click", 0.9)
T.wait(0.2)
T.say("C1", 0.3)
T.mark("read_title")
T.say("C2c", 0.45)
T.say("C3", 0.0)
T.mark("glow", M["C3"] - 0.1); T.fx("angelic", 0.5, at=M["C3"] - 0.3)
T.mark("dart_fire", T.t - 0.55)
T.mark("dart_hit", T.t - 0.3); T.fx("vine_boom", 0.8, at=T.t - 0.3); T.fx("hat_boing", 0.8, at=T.t - 0.25)
T.fx("steam", 0.55, at=T.t + 0.05)
T.wait(1.0)

T.scene("xray")
tension_start = T.t - 0.2
T.fx("gurgle", 0.6, off=0.2)
T.say("C4", 0.3)
T.mark("gremlin_wake", M["C4"] + 1.4); T.fx("tiny_giggle", 0.7, at=M["C4"] + 1.6)
T.say("C5", 0.4)
T.fx("gurgle", 0.5, at=M["C5"] + 1.0)
T.fx("tiny_giggle", 0.6, at=M["C5_end"] - 0.3)

T.scene("panic")
T.fx("gasp", 0.6)
T.fx("steam", 0.4, off=0.3)
T.wait(0.2)
T.say("C6", 0.3)
T.say("C7", 0.5)

# ---------------------------------------------------------------- 5. suppression (real fart, imagined defeat + imagined mess)
T.scene("suppress")
T.fx("heartbeat", 0.5)
T.say("D1", 0.3)
T.fx("muffled_giggle", 0.8)
T.fx("strain_squeak", 0.5, off=1.2)
T.mark("tremble")
T.wait(2.6)
T.say("D2", 0.35)
T.mus("tension", tension_start, T.t - 0.2, 0.7, fin=1.5, fout=0.1)
T.mark("fart"); T.fx("fart_long", 1.0)
T.fx("can_clank", 0.35, off=1.5)
T.wait(3.9)
T.mark("flag_bubble"); T.fx("harp_up", 0.45)
T.wait(0.3)
T.say("D3", 0.35)
T.mark("flag_pop"); T.fx("bubble_pop", 0.5)
T.wait(0.25)
T.say("D4", 0.5)
T.mark("crap_bubble"); T.fx("harp_up", 0.4)
T.wait(0.2)
T.say("D5", 0.2)
T.mark("maniac"); T.fx("maniacal_laugh", 0.7)
T.mark("splort", T.t + 2.0); T.fx("fart_dream", 0.8, off=2.0)
T.mark("roommates", T.t + 2.9); T.fx("pop", 0.5, off=2.9); T.fx("gasp", 0.45, off=3.1)
T.mark("roommates_laugh", T.t + 3.8); T.fx("roommate_laugh", 0.7, off=3.8)
T.wait(5.6)
T.mark("snap_out"); T.fx("gasp", 0.7)
T.wait(0.3)
T.say("D6", 0.6)

# ---------------------------------------------------------------- 6. unfunny defense: the therapist
T.scene("defense")
muzak_start = T.t
T.say("E1", 0.3)
T.mark("bubble1"); T.fx("harp_up", 0.6)
T.wait(0.4)
T.say("E3", 0.3)
T.say("E4", 0.6)
T.say("E4b", 0.3)
T.mark("breath_in"); T.fx("breath_in", 0.8)
T.wait(1.8)
T.mark("breath_out"); T.fx("breath_out", 0.8)
T.wait(1.6)
T.mark("leak"); T.fx("muffled_giggle", 0.7); T.fx("strain_squeak", 0.6, off=1.0)
T.wait(1.6)
T.mus("muzak", muzak_start, T.t + 0.2, 0.7, fin=0.3, fout=0.3)
T.fx("rumble", 0.6, off=0.1)
T.say("E10", 0.15)
T.mark("gauge_break"); T.fx("glass_crack", 0.8); T.fx("bubble_pop", 0.8, off=0.05)

# ---------------------------------------------------------------- 7. collapse
T.scene("collapse")
T.say("F1", 0.0)
T.mark("slide", M["F1"] + 0.3); T.fx("slide_whistle", 0.6, at=M["F1"] + 0.3)
T.mark("thud", M["F1"] + 1.35); T.fx("thud", 0.9, at=M["F1"] + 1.35)
T.wait(0.3)
T.mark("deflate_start"); T.fx("deflate_long", 0.75)
clown_start = T.t + 1.0
T.wait(0.6)
T.say("F2", 0.5)
T.mark("ghost", M["F2"] + 2.4); T.fx("ghost", 0.45, at=M["F2"] + 2.6)
T.say("F4", 0.3)
T.mark("trombone"); T.fx("sad_trombone", 0.85)
T.wait(3.9)
T.mark("honk"); T.fx("clown_honk", 0.8)
T.mus("sad_clown", clown_start, T.t - 0.2, 0.75, fin=1.5, fout=0.5)
T.wait(1.2)

# ---------------------------------------------------------------- 8. webcam reveal
T.scene("webcam")
T.wait(0.4)
T.say("G1", 0.6)
T.say("G2", 0.0)
T.mark("webcam_on", T.t - 0.3); T.fx("vine_boom", 1.0, at=T.t - 0.3)
T.wait(0.9)
T.mark("pov"); T.fx("record_scratch", 0.3, off=-0.15)
T.fx("tiny_squeak", 0.6, off=0.7)
T.wait(1.6)
T.say("G3", 1.0)

# ---------------------------------------------------------------- 9. viral
T.scene("viral")
T.fx("upload_chime", 0.6)
T.fx("ticks", 0.5, off=1.2)
for k in range(7):
    T.fx("notify", 0.5, off=1.5 + k * 0.52)
T.wait(0.3)
T.say("H1", 0.6)
T.wait(0.6)
T.say("H2", 0.5)
T.fx("riser", 0.5, off=-1.6)

# ---------------------------------------------------------------- 10. remix (ends in a fart bomb)
T.scene("remix")
REMIX_BAR = 4 * 60 / 98
REMIX_LEN = 10 * REMIX_BAR
T.mark("remix_bar", REMIX_BAR)
T.mus("remix", T.t, T.t + REMIX_LEN, 0.9, fin=0.01, fout=0.15)
T.mark("strain", T.t + 9 * REMIX_BAR + 0.15); T.fx("strain_squeak", 0.6, at=T.t + 9 * REMIX_BAR + 0.25)
T.mark("cloud", T.t + REMIX_LEN - 1.35); T.fx("fart_big", 1.0, at=T.t + REMIX_LEN - 1.4)
T.wait(REMIX_LEN)

# ---------------------------------------------------------------- 11. moral
T.scene("moral")
outro_start = T.t + 1.0
T.wait(1.6)
T.mark("moral_notif"); T.fx("ding", 0.6)
T.wait(1.0)
T.say("I1", 0.6)
T.say("I2", 0.6)
T.mark("post_again"); T.fx("click", 0.8, off=-0.4); T.fx("whoosh", 0.5, off=-0.2)
T.say("I3", 0.3)
T.mark("removed", M["I3"] + 2.2); T.fx("thud", 0.4, at=M["I3"] + 2.2)
T.mark("heart", M["I3"] + 4.3); T.fx("harp_up", 0.35, at=M["I3"] + 4.3)
T.say("I4", 0.9)

T.scene("end")
T.say("I5", 0.5)
T.mark("wave", T.t)
T.wait(1.2)
T.mark("jet"); T.fx("jet_fart", 0.9)
T.wait(1.4)
T.mark("stinger"); T.fx("heh", 0.6, off=0.2)
T.wait(1.6)
T.mus("outro", outro_start, T.t, 0.75, fin=1.0, fout=1.5)

out = T.done()
json.dump(out, open("timeline.json", "w"), indent=1)
print("duration", round(out["duration"], 2))
for s in out["scenes"]:
    print(f"  {s['name']:12s} {s['start']:7.2f} -> {s['end']:7.2f}  ({s['end']-s['start']:.1f}s)")
