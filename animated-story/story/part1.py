"""PART 1 — F*** AROUND"""
from toon.engine import Part
from story.common import (title, text_card, stage_duo, stands_trio, cam_cartman_stands, STAGE_Y,
                          STOOL_SEAT_Y, ROW2)


def build():
    P = Part(1, "F*** AROUND", "part1-f-around")
    title(P, 1, "F*** AROUND")

    # ------------------------------------------------------------------ the plan (office)
    s = P.shot("office")
    s.music("comedy", gain=0.22, fade=0.6)
    pc = s.actor("pc", x=320, y=1470, scale=1.15, arms="hips", gest=0.8)
    ch = s.actor("chad", x=780, y=1470, scale=1.15, eyes="warm", gest=0.8)
    s.camera(cx=540, cy=1000, zoom=1.08)
    s.camera(dur=14, ease="lin", zoom=1.18)
    s.narr("Monday morning. The principal's office.")
    s.say(pc, "Alright, Chad. Emotional education assembly. Friday. The whole school.", arms="present")
    s.say(ch, "Bro. I have been waiting for this my entire life.", arms="heart", eyes="teary", brow=0.8)
    ch.to(s.t - 1.0, 0.8, tears=0.7)
    s.say(pc, "Problem is, the kids think feelings are lame.", arms="shrug", brow=0.5)
    ch.set(s.t, tears=0, eyes="warm", brow=0)
    s.say(ch, "Then we don't lecture them. We show them. Feelings are reps, bro. You train them out loud.",
          arms="flex", mouth="grin")
    s.say(pc, "So we make it fun. Music. Volunteers. We pull a name out of a hat.", arms="holdup", brow=0)
    s.say(ch, "And whoever comes up, we make them feel safe. Nobody gets roasted.", arms="heart", mouth="smile")
    s.say(pc, "Nobody gets roasted.", arms="point")
    # fist bump
    pc.to(s.t, 0.35, "back", aRx=1.3, aRy=-0.1)
    ch.to(s.t, 0.35, "back", aLx=1.3, aLy=-0.1)
    s.sfx("pop", at=s.t + 0.33)
    s.overlay("sfx", at=s.t + 0.33, dur=0.7, text="BUMP!", x=540, y=930, size=90, color="#ffffff")
    s.wait(0.9)
    s.say(ch, "Sorry. I just love a good plan.", arms="face", eyes="teary", tears=0.8, mouth="wobbly", brow=1)
    s.wait(0.4)
    s.end()

    # ------------------------------------------------------------------ Cartman reads the flyer
    s = P.shot("hallway")
    c = s.actor("cartman", x=540, y=1600, scale=1.25, eyes="half", looky=-0.6, mouth="flat", arms="down")
    s.camera(cx=540, cy=430, zoom=1.7)
    s.wait(1.2)
    s.camera(dur=1.2, cx=540, cy=1130, zoom=1.25)
    s.wait(1.3)
    # the eye roll
    c.to(s.t, 0.25, eyes="roll", looky=-1.0, look=-0.8, brow=-0.3)
    c.to(s.t + 0.25, 0.35, look=0.8)
    c.to(s.t + 0.6, 0.3, look=0.0, looky=0.0)
    s.sfx("whoosh", at=s.t, gain=0.5)
    s.overlay("sfx", at=s.t + 0.1, dur=0.9, text="*EYE ROLL*", x=540, y=760, size=80, color="#ffffff", rot=0.06)
    s.wait(1.1)
    c.set(s.t, eyes="half", mouth="smirk")
    s.think(c, "Emotional education. Oh, this is going to be beautiful.", icon="heh", arms="rub", rub=1)
    s.think(c, "Two giant dweebs doing woo-woo feelings garbage in front of the whole school?", icon="lol")
    s.think(c, "I'm going to crap all over it. It's going to be so easy.", icon="$_$", mouth="grin", eyes="happy")
    s.say(c, "Mwahahaha.", mouth="grin", eyes="half", rub=1.5)
    s.wait(0.3)
    s.end()

    text_card(P, ["FRIDAY."], d=1.4)

    # ------------------------------------------------------------------ the assembly begins
    s = P.shot("stage", mood="idle")
    s.music("assembly", gain=0.5, fade=0.1)
    pc, ch = stage_duo(s, pc=dict(arms="mic", hold="mic", gest=0.2), chad=dict(arms="up", eyes="happy", mouth="grin"))
    for a, ph in ((pc, 0), (ch, 0.3)):
        for k in range(10):
            a.to(k * 0.48 + ph, 0.24, "out", hop=18)
            a.to(k * 0.48 + ph + 0.24, 0.24, "in", hop=0)
    ch.set(0, waveR=1, waveL=1)
    s.camera(cx=540, cy=900, zoom=1.0)
    s.camera(dur=4, ease="lin", zoom=1.1)
    s.narr("Friday. The assembly.", gap=0.1)
    s.say(pc, "Good morning, school! Everybody breathe in!", arms="up", hold=None)
    ch.set(s.t, waveR=0, waveL=0, arms="out")
    s.say(ch, "And out! Let it out, bros!", eyes="closed", arms="out")
    s.wait(0.4)
    s.end()

    # ------------------------------------------------------------------ the stands: the setup
    s = P.shot("stands", mood="idle")
    c, f1, f2 = stands_trio(s, cart=dict(eyes="half", mouth="smirk"))
    cam_cartman_stands(s)
    s.say(c, "Guys. Guys. This emotion stuff is for dweebs.", style="whisper", look=-0.8)
    s.say(c, "Watch this. I'm going to yell something so funny, the whole gym is going to lose it.",
          style="whisper", look=0.8, mouth="grin")
    s.say(f1, "Cartman, don't.", brow=1, look=0.8)
    s.say(f2, "Dude. They're right there.", brow=1, look=-0.8)
    s.say(c, "Relax. Comedy is all about timing.", look=0, mouth="smirk", eyes="half")
    # stand up and cup hands
    c.to(s.t, 0.3, "back", y=ROW2 - 70, sit=0)
    c.to(s.t, 0.3, arms="cup", eyes="open")
    s.camera(dur=0.3, zoom=2.0, cy=1080)
    s.wait(0.4)
    s.overlay("sfx", dur=1.0, text="LOSERS!", x=540, y=640, size=170, color="#ffe14a")
    s.camera(dur=0.2, shake=10)
    s.say(c, "LOSERS!", style="shout", mouth="scream", eyes="wide", gap=0.0)
    s.end()

    # ------------------------------------------------------------------ the music stops
    s = P.shot("stage", mood="stare", spot=0)
    s.music(None, fade=0.02)
    s.sfx("scratch", gain=0.9)
    s.overlay("sfx", dur=0.9, text="SCRRRATCH!", x=540, y=560, size=130, color="#ff5a5a")
    s.cc("[The music stops]", dur=1.6, at=0.2)
    pc, ch = stage_duo(s, pc=dict(arms="up", hop=20, eyes="happy", mouth="grin", autoblink=0),
                       chad=dict(arms="out", hop=20, eyes="closed", mouth="grin", autoblink=0))
    pc.set(0.15, hop=0, eyes="stare", mouth="flat", arms="down", brow=-0.3)
    ch.set(0.15, hop=0, eyes="stare", mouth="flat", arms="down", brow=-0.3)
    s.overlay("bars", at=0.2, dur=2.9)
    s.camera(cx=540, cy=900, zoom=1.0)
    s.camera(at=0.3, dur=2.6, ease="inout", cx=540, cy=720, zoom=1.65)
    pc.to(1.6, 0.5, glint=1.0)
    s.sfx("sparkle", at=1.65, gain=0.5)
    s.wait(3.1)
    s.end()

    # ------------------------------------------------------------------ awkward: "right, guys?"
    s = P.shot("stands", mood="stare", target_x=540)
    c, f1, f2 = stands_trio(s, cart=dict(y=ROW2 - 70, sit=0, arms="cup", mouth="scream", eyes="wide"),
                            f1=dict(eyes="open", look=0.0, mouth="flat"), f2=dict(eyes="open", mouth="flat"))
    cam_cartman_stands(s, zoom=1.6, cy=1150)
    c.to(0.3, 0.5, arms="down", mouth="flat", eyes="open")
    c.to(1.0, 0.6, y=ROW2, sit=1)
    c.to(1.1, 1.2, shiver=0.6, sweat=1.0)
    s.wait(1.8)
    s.say(c, "Heh. Haha. Right, guys?", mouth="grimace", look=-0.9, brow=0.8)
    c.to(s.t - 0.5, 0.3, look=0.9)
    # friends slowly scoot away, eyes front
    f1.to(s.t, 2.4, "inout", x=245)
    f2.to(s.t, 2.4, "inout", x=835)
    c.to(s.t, 0.4, look=0.0, mouth="wobbly")
    s.cc("[Dead silence]", dur=2.5)
    s.sfx("tick", at=s.t + 0.5, gain=0.3)
    s.sfx("tock", at=s.t + 1.5, gain=0.3)
    s.sfx("gulp", at=s.t + 2.0, gain=0.8)
    c.to(s.t + 1.0, 1.0, sweat=2.0)
    s.wait(2.6)
    s.end()

    s = P.shot("clock")
    s.cc("[Dead silence]", dur=1.8)
    for k in range(2):
        s.sfx("tick" if k % 2 == 0 else "tock", at=0.1 + k, gain=0.45)
    s.camera(cx=540, cy=820, zoom=1.0)
    s.camera(dur=2.0, ease="lin", zoom=1.12)
    s.wait(2.0)
    s.end()

    s = P.shot("stage", mood="stare", spot=0)
    pc, ch = stage_duo(s, pc_x=410, chad_x=680, pc=dict(eyes="stare", mouth="flat", autoblink=0, brow=-0.3, bob=0),
                       chad=dict(eyes="stare", mouth="flat", autoblink=0, brow=-0.3, bob=0))
    s.camera(cx=545, cy=720, zoom=1.75)
    s.camera(dur=2.2, ease="lin", zoom=1.9)
    s.cc("[Still silent]", dur=2.0)
    s.sfx("tick", at=0.3, gain=0.3)
    s.sfx("tock", at=1.3, gain=0.3)
    s.wait(2.2)
    s.end()

    s = P.shot("stands", mood="stare", target_x=540)
    c, f1, f2 = stands_trio(s, cart=dict(mouth="wobbly", sweat=2, shiver=0.4),
                            f1=dict(x=245, eyes="open", mouth="flat"), f2=dict(x=835, eyes="open", mouth="flat"))
    s.camera(cx=540, cy=960, zoom=1.0)
    s.camera(dur=2.0, ease="lin", zoom=1.05)
    s.cc("[Every single kid is staring at Cartman]", dur=2.0)
    s.sfx("tick", at=0.2, gain=0.3)
    s.sfx("tock", at=1.2, gain=0.3)
    s.wait(2.0)
    s.end()

    s = P.shot("stands", mood="stare", target_x=540)
    c, f1, f2 = stands_trio(s, cart=dict(mouth="wobbly", sweat=3, shiver=0.3, eyes="open"),
                            f1=dict(x=245), f2=dict(x=835))
    for k in range(6):
        c.to(k * 0.3, 0.12, look=(-0.9 if k % 2 else 0.9))
    s.camera(cx=540, cy=1150, zoom=2.7)
    s.sfx("tick", at=0.2, gain=0.3)
    s.sfx("tock", at=1.2, gain=0.3)
    s.wait(1.9)
    s.sfx("cough", gain=0.9)
    s.cc("[Somebody coughs]", dur=1.2)
    s.wait(0.9)
    s.end()

    # ------------------------------------------------------------------ back to normal like nothing happened
    s = P.shot("stage", mood="idle")
    s.music("assembly", gain=0.5, fade=0.02)
    pc, ch = stage_duo(s, pc=dict(arms="up", eyes="happy", mouth="grin", hold="mic"),
                       chad=dict(arms="up", eyes="happy", mouth="grin"))
    for a, ph in ((pc, 0), (ch, 0.3)):
        for k in range(6):
            a.to(k * 0.48 + ph, 0.24, "out", hop=18)
            a.to(k * 0.48 + ph + 0.24, 0.24, "in", hop=0)
    s.say(pc, "Okay! Who's ready to feel some feelings?!", arms="mic", gap=0.05)
    s.say(ch, "Wooo!", arms="up", gap=0.3)
    s.end()

    # ------------------------------------------------------------------ existential crisis
    s = P.shot("stands", mood="idle")
    c, f1, f2 = stands_trio(s, cart=dict(eyes="dots", mouth="flat", sweat=1, bob=0),
                            f1=dict(x=245), f2=dict(x=835))
    s.camera(cx=540, cy=1150, zoom=2.2)
    s.camera(dur=5, ease="lin", zoom=2.6)
    s.think(c, "What just happened? Nobody laughed. Why did nobody laugh?", icon="?")
    s.end()

    s = P.shot("void", void_words=["LOSER?", "WHO AM I?", "WHAT IS FUNNY?", "AM I THE LOSER?", "WHY?"])
    s.music("tension", gain=0.35, fade=0.6)
    c = s.actor("cartman", x=540, y=1150, scale=1.1, eyes="spiral", mouth="wobbly", arms="out", bob=0)
    c.to(0, 9, "lin", rot=1.2, y=1100)
    c.set(0, flail=0.15)
    s.camera(cx=540, cy=950, zoom=0.9)
    s.camera(dur=9, ease="lin", zoom=1.15)
    s.think(c, "Am I the loser? Is everyone the loser? What even is a loser?", icon="???")
    s.narr("Eric Cartman had officially [bleep] around.", caption="Eric Cartman had officially f***ed around.")
    s.narr("And he was about to find out.")
    s.end()

    # ------------------------------------------------------------------ the totally random name
    s = P.shot("stage", mood="idle")
    s.music("assembly", gain=0.3, fade=0.3)
    pc, ch = stage_duo(s, pc=dict(x=380, arms="mic", hold="mic"), chad=dict(x=700, facing=-1, arms="hold", hold="hat"))
    s.camera(cx=540, cy=820, zoom=1.25)
    s.say(pc, "Alright, school! Time to pick our first volunteer! Totally random!", arms="holdup")
    # they look at each other... then straight at Cartman
    pc.to(s.t, 0.3, look=0.9, eyes="half", mouth="smirk")
    ch.to(s.t, 0.3, look=-0.9, eyes="half", mouth="smirk")
    s.overlay("glance", at=s.t + 0.2, dur=1.1, a=pc, b=ch, dy1=150, dy2=150)
    s.wait(1.3)
    pc.to(s.t, 0.25, look=0.0, eyes="stare")
    ch.to(s.t, 0.25, look=0.0, eyes="stare")
    s.wait(0.8)
    s.music(None, fade=0.3)
    roll = s.t
    s.sfx("drumroll", gain=0.8)
    pc.to(s.t, 0.4, arms="reach", hold=None)
    s.wait(1.0)
    s.end()

    s = P.shot("hat")
    s.camera(cx=540, cy=960, zoom=1.0)
    s.camera(dur=2.0, ease="lin", zoom=1.15)
    s.overlay("label", at=0.4, dur=1.4, text=["100% RANDOM"], x=540, y=330, size=64, bg="#ffffff", rot=-0.1)
    s.wait(1.6)
    s.end()

    s = P.shot("stage", mood="idle")
    pc, ch = stage_duo(s, pc=dict(x=380, arms="reach", eyes="stare", autoblink=0),
                       chad=dict(x=700, facing=-1, arms="hold", hold="hat", eyes="stare"))
    s.camera(cx=540, cy=820, zoom=1.25)
    pc.to(0.0, 0.35, arms="holdup", hold="slip", slip_text="CARTMAN")
    s.wait(0.6)
    s.music("assembly", gain=0.45, fade=0.05)
    s.say(pc, "Eric Cartman! Come on down, bro!", eyes="stare", mouth="grin")
    s.sfx("crowd_ooh", gain=0.7, d=2.2)
    s.end()

    # ------------------------------------------------------------------ "oh no"
    s = P.shot("stands", mood="shock", target_x=540)
    c, f1, f2 = stands_trio(s, cart=dict(eyes="wide", mouth="o", sweat=1), f1=dict(x=245, eyes="wide", mouth="o"),
                            f2=dict(x=835, eyes="wide", mouth="o"))
    s.param(at=1.2, mood="stare")
    cam_cartman_stands(s, zoom=2.2, cy=1150)
    s.think(c, "Oh [bleep]. Oh God. This is bad. This is very bad.", icon="!!!",
            caption="Oh sh*t. Oh God. This is bad. This is very bad.", mouth="wobbly", shiver=0.8, sweat=2)
    s.think(c, "They're going to destroy me in front of the entire school.", icon="X_X", eyes="sad", brow=1)
    s.say(c, "I'm good! I'm good right here!", arms="cross", eyes="squeeze", mouth="grimace", pitch=1.05)
    s.wait(0.2)
    s.end()

    s = P.shot("stage", mood="idle")
    pc, ch = stage_duo(s, pc=dict(x=380, arms="hips", eyes="open", mouth="smile"),
                       chad=dict(x=700, facing=-1, arms="hold", hold="hat", eyes="warm"))
    s.camera(cx=380, cy=800, zoom=1.6)
    s.say(pc, "No worries, bro. We'll bring you down.", mouth="smile")
    pc.to(s.t, 0.2, arms="fistup")
    s.sfx("pop", at=s.t + 0.2)
    s.overlay("sfx", at=s.t + 0.2, dur=0.6, text="*SNAP*", x=600, y=560, size=80, color="#ffffff")
    s.wait(0.9)
    s.end()

    # ------------------------------------------------------------------ the gym bros arrive (they climb up into the stands)
    s = P.shot("stands", mood="wtf", target_x=540)
    c, f1, f2 = stands_trio(s, cart=dict(eyes="wide", mouth="o", shiver=0.8, sweat=2, z=2),
                            f1=dict(x=245, eyes="wide", mouth="o"), f2=dict(x=835, eyes="wide", mouth="o"))
    ba = s.actor("broA", x=400, y=ROW2 + 650, scale=0.78, layer=2, arms="down", eyes="half", mouth="flat", z=1)
    bb = s.actor("broB", x=680, y=ROW2 + 650, scale=0.78, layer=2, arms="down", eyes="half", mouth="flat", z=1)
    cam_cartman_stands(s, zoom=1.3, cy=1000)
    for k, a in enumerate((ba, bb)):
        for j in range(3):
            t = 0.2 + k * 0.15 + j * 0.45
            a.to(t, 0.3, "out", y=ROW2 + 650 - (j + 1) * 197)
            s.sfx("thud", at=t + 0.3, gain=0.35)
    s.camera(at=0.5, dur=1.4, shake=4)
    s.camera(at=1.9, dur=0.2, shake=0)
    s.overlay("label", at=1.0, dur=3.0, text=["GYM BROS", "AGE: 35", "BODY FAT: 0%"], x=270, y=470, size=46, rot=-0.06)
    c.to(0.4, 0.3, look=-0.8)
    c.to(1.2, 0.3, look=0.8)
    s.wait(2.0)
    s.say(ba, "Up we go, little man.", eyes="half", mouth="flat", arms="grab")
    bb.to(s.t - 0.8, 0.4, arms="grab")
    c.to(s.t - 0.8, 0.3, look=0, eyes="wide", mouth="scream")
    # lift!
    ba.to(s.t, 0.5, arms="carry")
    bb.to(s.t, 0.5, arms="carry")
    c.to(s.t, 0.5, "back", y=ROW2 - 400, rot=-1.57, sit=0)
    c.set(s.t, flail=1.0, kick=1.0, mouth="scream", eyes="squeeze", shiver=0)
    s.sfx("squeal_long", at=s.t + 0.2, gain=0.8)
    s.sfx("choir", at=s.t + 0.3, gain=0.7)
    s.overlay("sfx", at=s.t + 0.3, dur=2.0, text="SQUEEEEE!", x=540, y=430, size=140, color="#ff8fb0")
    s.overlay("lines", at=s.t + 0.3, dur=3.6, x=540, y=820, color="#ffffff")
    s.wait(0.5)
    s.say(c, "SQUEEEEEEEE! NOOOOO! NOT LIKE THIS! I'M TOO YOUNG! TELL MY MOM I LOVE HER!", style="shout",
          pitch=1.1, speed=1.05, gap=0.0, advance=False)
    s.wait(1.4)
    # carry him off to the right
    for a in (ba, bb):
        a.to(s.t, 2.0, "in", x=a.get("x", s.t) + 900)
        a.set(s.t, walk=1)
    c.to(s.t, 2.0, "in", x=540 + 900)
    s.wait(2.2)
    s.end()

    # ------------------------------------------------------------------ the crowd reacts
    s = P.shot("stands", mood="wtf", target_x=1100)
    c, f1, f2 = stands_trio(s, cart=dict(visible=0), f1=dict(x=245, eyes="wide", mouth="o", look=1),
                            f2=dict(x=835, eyes="wide", mouth="o", look=1))
    s.camera(cx=540, cy=1000, zoom=1.0)
    s.sfx("crowd_murmur", gain=0.22, d=7.0)
    s.sfx("squeal", at=0.0, gain=0.15)
    s.say("kid1", "What the actual [bleep] is he doing?", pre=0.6, caption="What the actual f*** is he doing?", pitch=1.0)
    s.say("kid2", "Why is he freaking out?")
    s.say(f2, "It looks like his soul is leaving his body.", look=1)
    s.wait(0.2)
    s.end()

    # ------------------------------------------------------------------ the delivery
    s = P.shot("stage", mood="wtf", stool=1)
    s.music("assembly", gain=0.25, fade=0.3)
    pc, ch = stage_duo(s, pc=dict(x=150, arms="hips", eyes="open", mouth="smile"),
                       chad=dict(x=930, arms="heart", eyes="warm", mouth="smile"))
    pc.set(4.0, x=300)
    ch.set(4.0, x=780)
    ba = s.actor("broA", x=1250, y=STAGE_Y, scale=0.9, arms="carry", eyes="half", mouth="flat", walk=1, z=1)
    bb = s.actor("broB", x=1550, y=STAGE_Y, scale=0.9, arms="carry", eyes="half", mouth="flat", walk=1, z=1)
    c = s.actor("cartman", x=1400, y=STAGE_Y - 530, scale=0.95, rot=-1.57, flail=1, kick=1, mouth="scream",
                eyes="squeeze", z=2)
    s.camera(cx=540, cy=880, zoom=1.0)
    ba.to(0, 1.6, "out", x=390)
    bb.to(0, 1.6, "out", x=690)
    c.to(0, 1.6, "out", x=540)
    s.say(c, "AAAAAAAAAAAH!", style="shout", gap=0.0, advance=False)
    s.sfx("squeal", at=0.1, gain=0.6)
    s.wait(1.6)
    ba.set(s.t, walk=0)
    bb.set(s.t, walk=0)
    # plop
    c.to(s.t, 0.35, "in", y=STOOL_SEAT_Y, rot=0.0, sit=1)
    c.set(s.t + 0.35, flail=0, kick=0, sy=0.8, sx=1.15, mouth="grimace", arms="shield", eyes="squeeze", shiver=0.6)
    c.to(s.t + 0.35, 0.5, "elastic", sy=1.0, sx=1.0)
    ba.to(s.t, 0.35, arms="down")
    bb.to(s.t, 0.35, arms="down")
    s.sfx("thud", at=s.t + 0.35)
    s.camera(at=s.t + 0.35, shake=14)
    s.camera(at=s.t + 0.35, dur=0.5, shake=0)
    s.overlay("sfx", at=s.t + 0.35, dur=0.7, text="PLOP!", x=540, y=760, size=120, color="#ffe14a")
    s.wait(1.0)
    # bros leave, brushing hands
    ba.set(s.t, walk=1)
    bb.set(s.t, walk=1)
    ba.to(s.t, 1.4, "in", x=-400)
    bb.to(s.t, 1.4, "in", x=1500)
    s.wait(1.2)
    s.end()

    # ------------------------------------------------------------------ bracing for impact
    s = P.shot("stage", mood="stare", stool=1, spot_x=540)
    s.music("tension", gain=0.4, fade=0.3)
    pc, ch = stage_duo(s, pc=dict(x=300, arms="down", eyes="stare", mouth="flat", autoblink=0),
                       chad=dict(x=780, arms="down", eyes="stare", mouth="flat"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, arms="shield", eyes="squeeze",
                mouth="grimace", shiver=0.5, sweat=2, z=1)
    s.camera(cx=540, cy=880, zoom=1.7)
    s.think(c, "Here it comes. Total public humiliation.", icon="X_X")
    s.think(c, "They're going to rip my soul out in front of everybody.", icon="RIP")
    # PC steps up and reaches for his sunglasses
    pc.to(s.t, 1.0, "inout", x=400, walk=1)
    pc.set(s.t + 1.0, walk=0)
    s.camera(dur=1.6, cx=430, cy=720, zoom=2.1)
    s.wait(1.1)
    pc.to(s.t, 0.6, arms="shades")
    pc.to(s.t + 0.5, 0.4, shades=0.85)
    s.sfx("heartbeat", at=s.t, gain=0.9)
    s.sfx("heartbeat", at=s.t + 0.9, gain=0.9)
    s.wait(1.6)
    s.music(None, fade=0.05)
    s.end()

    s = P.shot("card", card="tbc", next="PART 2: FIND OUT")
    s.sfx("badum", gain=0.9)
    s.wait(2.6)
    s.end()
    return P.finalize()
