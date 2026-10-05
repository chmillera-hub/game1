"""PART 2 — FIND OUT"""
from toon.engine import Part
from story.common import title, text_card, stage_duo, STAGE_Y, STOOL_SEAT_Y

TABLE_X = 250


def build():
    P = Part(2, "FIND OUT", "part2-find-out")
    title(P, 2, "FIND OUT")

    # ------------------------------------------------------------------ recap
    s = P.shot("stage", mood="stare", stool=1)
    s.music("tension", gain=0.35, fade=0.3)
    pc, ch = stage_duo(s, pc=dict(x=400, arms="shades", eyes="stare", shades=0.85, autoblink=0),
                       chad=dict(x=780, eyes="stare", mouth="flat"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, arms="shield", eyes="squeeze",
                mouth="grimace", shiver=0.5, sweat=2, z=1)
    s.camera(cx=540, cy=860, zoom=1.35)
    s.narr("Previously: Cartman called the whole school losers. Now he's on the stool, waiting to die.")
    s.end()

    # ------------------------------------------------------------------ the sunglasses come off
    s = P.shot("stage", mood="stare", stool=1)
    pc, ch = stage_duo(s, pc=dict(x=400, arms="shades", eyes="warm", shades=0.85, autoblink=0, mouth="smile"),
                       chad=dict(x=780, eyes="warm", mouth="smile"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, arms="shield", eyes="squeeze",
                mouth="grimace", shiver=0.5, sweat=2, z=1)
    s.camera(cx=400, cy=700, zoom=2.4)
    s.music(None, fade=0.4)
    pc.to(0.3, 0.9, shades=0.0)
    pc.set(1.2, holdshades=1, arms="hold", sparkle=1.0, autoblink=1)
    s.music("warm", at=1.1, gain=0.45, fade=0.8)
    s.sfx("sparkle", at=1.1, gain=0.8)
    s.overlay("sparkles", at=1.1, dur=2.4, x0=180, x1=900, y0=350, y1=900, n=14)
    s.overlay("flash", at=1.1, dur=0.4, alpha=0.5)
    s.cc("[Warm, caring eyes]", dur=2.0, at=1.3)
    s.wait(2.7)
    pc.set(s.t, sparkle=0.4)
    # Cartman peeks
    s.camera(dur=0.5, cx=520, cy=820, zoom=1.9)
    c.to(s.t, 0.5, arms="shield1", eyes="open", look=-0.9, shiver=0.2, mouth="flat", brow=0.6)
    s.wait(0.45)
    s.say(c, "What the hell?", mouth="o", gap=0.4)
    s.camera(dur=0.6, cx=470, cy=760, zoom=1.7)
    s.say(pc, "Hey. We got you, dude. Don't worry. We're not going to do anything weird, okay? You'll see.",
          speed=0.92, eyes="warm", mouth="smile", gest=0.3)
    s.think(c, "What is going on? This is a trick. It has to be a trick.", icon="?!", eyes="half", brow=-0.4,
            look=-0.6)
    s.think(c, "There's no way PC Principal is being nice to me. I literally just called everybody a loser!",
            icon="?!?")
    s.think(c, "How are they going to trick me?", icon="hmm", arms="shield")
    s.end()

    # ------------------------------------------------------------------ the Feelings Restaurant
    s = P.shot("stage", mood="idle", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    s.music("comedy", gain=0.3, fade=0.4)
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="open", mouth="smile", costume="posh", shades=0, arms="hips"),
                       chad=dict(x=400, eyes="warm", costume="waiter", arms="tray", hold="tray", facing=-1))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, arms="shield", eyes="half", mouth="flat",
                brow=-0.4, z=1, look=-0.8)
    s.camera(cx=470, cy=880, zoom=1.15)
    s.say(ch, "Welcome to the Feelings Restaurant!", arms="present", hold=None)
    ch.set(s.t, arms="tray", hold="tray")
    s.say(pc, "Waiter! I ordered Anger, medium rare. This is clearly Sadness!", arms="table", brow=-0.8,
          mouth="frown")
    s.sfx("thud", at=s.t - 1.2, gain=0.4)
    s.say(ch, "I'm so sorry, sir. The chef is going through a lot right now.", eyes="teary", tears=0.6,
          mouth="wobbly", brow=1)
    s.sfx("crowd_laugh", gain=0.35, d=2.0)
    s.param(mood="smile")
    # Cartman lowers his arm and chuckles
    c.to(s.t, 0.8, arms="down", eyes="open", brow=0, look=-0.7)
    s.camera(dur=0.8, cx=540, cy=820, zoom=1.8)
    s.wait(0.6)
    s.say(c, "Heh.", mouth="smirk", gap=0.4)
    s.think(c, "Wait. They're not here to destroy me. This is the bit.", icon="!", eyes="open")
    s.think(c, "I'm supposed to be part of the bit.", icon="oh")
    s.end()

    # ------------------------------------------------------------------ the invitation
    s = P.shot("stage", mood="smile", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="open", mouth="smile", costume="posh", shades=0, arms="hips"),
                       chad=dict(x=720, eyes="warm", costume="waiter", arms="hold", hold="menu"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, eyes="open", mouth="flat", z=1, look=0.8)
    s.camera(cx=600, cy=820, zoom=1.6)
    s.say(ch, "Hey. There's one more seat at the restaurant, if you want it. Totally up to you, bro. No pressure.")
    s.say(pc, "Zero pressure. We're having fun either way.", look=0.9)
    # they go back to their bit, leaving him space
    ch.to(s.t, 1.0, x=400, facing=-1, arms="tray", hold="tray")
    ch.set(s.t, walk=1)
    ch.set(s.t + 1.0, walk=0)
    s.camera(dur=1.0, cx=540, cy=820, zoom=1.9)
    s.wait(0.3)
    s.think(c, "Wait. This might actually be fun.", icon="?", eyes="open", look=-0.6, mouth="smile")
    s.think(c, "No. No! It's a trap. The second I play along, they'll turn on me.", icon="NO",
            eyes="squeeze", arms="face", mouth="grimace")
    s.think(c, "But it does look kind of fun... Ugh!", icon="UGH", eyes="open", look=-0.8, arms="down",
            mouth="wobbly")
    s.end()

    # ------------------------------------------------------------------ something tiny
    s = P.shot("stage", mood="smile", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="open", mouth="smile", costume="posh", shades=0, arms="hips"),
                       chad=dict(x=400, eyes="warm", costume="waiter", arms="tray", hold="tray", facing=-1))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, eyes="half", mouth="flat", z=1, look=-0.6,
                brow=0.6)
    s.camera(cx=540, cy=840, zoom=1.5)
    c.to(0.2, 0.5, aRx=0.35, aRy=-0.6)
    s.wait(0.6)
    s.say(c, "Check, please.", speed=0.9, pitch=0.98, mouth="flat", gap=0.1)
    # flinch, expecting the attack
    c.to(s.t, 0.15, arms="shield", eyes="squeeze", mouth="grimace", shiver=0.6)
    s.wait(0.6)
    pc.to(s.t, 0.2, eyes="happy", mouth="grin", arms="up", hop=20)
    ch.to(s.t, 0.2, eyes="happy", mouth="grin", arms="up", hold=None, hop=20)
    pc.to(s.t + 0.3, 0.2, hop=0)
    ch.to(s.t + 0.3, 0.2, hop=0)
    s.sfx("sparkle", gain=0.5)
    s.say(pc, "Table two wants the check!", gap=0.1)
    s.say(ch, "Excellent choice, sir!", arms="clap", clap=1)
    ch.set(s.t, clap=0)
    c.to(s.t, 0.5, arms="down", eyes="open", shiver=0, mouth="o", brow=0.4, look=-0.5)
    s.wait(0.3)
    s.think(c, "Huh. They're not attacking me. They actually want me in this.", icon="huh", mouth="smile")
    s.end()

    # ------------------------------------------------------------------ the cringe
    s = P.shot("stage", mood="smile", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="open", mouth="smile", costume="posh", shades=0, arms="hips"),
                       chad=dict(x=400, eyes="happy", costume="waiter", mouth="grin", arms="point"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, eyes="open", mouth="smile", z=1, look=-0.6)
    s.camera(cx=430, cy=840, zoom=1.3)
    s.say(ch, "And today's special is... Feelings Soup! Because... soup... has feelings?",
          arms="point", waveR=0.5)
    ch.set(s.t, waveR=0)
    s.say(pc, "Ha. Soup.", mouth="smile", eyes="happy", gap=0.2)
    s.param(mood="cringe")
    s.music(None, fade=0.3)
    s.sfx("crickets", gain=0.9, d=2.4)
    s.cc("[Crickets]", dur=2.0)
    c.to(s.t, 0.3, eyes="squint", mouth="grimace", brow=0.8)
    s.wait(2.0)
    s.say(ch, "Because it's... souper emotional?", eyes="open", mouth="smile", brow=0.6, arms="shrug")
    s.sfx("crowd_groan", gain=0.6, d=2.0)
    pc.to(s.t, 0.3, arms="clap")
    pc.set(s.t, clap=0.6)
    s.cc("[PC Principal slow-claps alone]", dur=1.6)
    s.sfx("applause", gain=0.25, d=1.4)
    s.wait(1.1)
    s.end()

    s = P.shot("stage", mood="cringe", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="happy", mouth="grin", costume="posh", shades=0, arms="clap", clap=0.6),
                       chad=dict(x=400, eyes="happy", costume="waiter", mouth="grin", arms="shrug"))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, eyes="squint", mouth="grimace", brow=0.8,
                z=1, look=-0.6)
    s.camera(cx=540, cy=820, zoom=2.0)
    s.think(c, "Oh my God. This is painful. They're dying up here.", icon="X_X")
    s.think(c, "Incredibly dumb. Incredibly cringe. I can't watch this.", icon="!!!", arms="face")
    c.to(s.t, 0.3, arms="hips", eyes="angry", brow=-0.6, mouth="flat")
    s.think(c, "I have to save these dweebs. They need me. They need my comedy.", icon="!!")
    s.end()

    # ------------------------------------------------------------------ Cartman takes over
    s = P.shot("stage", mood="cringe", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=130, eyes="open", mouth="smile", costume="posh", shades=0, arms="hips"),
                       chad=dict(x=400, eyes="warm", costume="waiter", mouth="smile", arms="tray", hold="tray",
                                 facing=-1))
    c = s.actor("cartman", x=540, y=STOOL_SEAT_Y, scale=0.95, sit=1, eyes="half", mouth="smirk", z=1, arms="hips")
    s.camera(cx=470, cy=860, zoom=1.15)
    # stand up on the stool
    c.to(0.2, 0.35, "back", y=1086, sit=0)
    s.wait(0.6)
    s.say(c, "Alright, alright. Step aside, amateurs.", arms="hips", eyes="half", mouth="smirk", gap=0.15)
    s.music("comedy", gain=0.35, fade=0.1)
    c.set(s.t, costume="bib")
    # jump down to the table
    c.to(s.t, 0.5, "out", x=330, y=STAGE_Y, hop=0)
    c.to(s.t, 0.25, "out", hop=80)
    c.to(s.t + 0.25, 0.25, "in", hop=0)
    ch.to(s.t, 0.4, x=470)
    s.wait(0.6)
    c.set(s.t, arms="table")
    s.sfx("thud", gain=0.6)
    s.camera(dur=0.15, shake=8)
    s.camera(at=s.t + 0.2, dur=0.2, shake=0)
    s.say(c, "WAITER! I ordered Happiness with extra cheese, and you brought me DISAPPOINTMENT!", style="shout",
          eyes="angry", mouth="grin", brow=-0.8, look=0.6, gest=1.2)
    s.param(mood="laugh")
    s.sfx("crowd_laugh", gain=0.7, d=2.6)
    s.wait(0.2)
    s.say(c, "I know what disappointment tastes like! I see it on my mom's face every time she reads my "
             "report card!", eyes="wide", mouth="grin", arms="out", gest=1.2)
    s.param(mood="roar")
    s.sfx("crowd_laugh", gain=0.85, d=3.0)
    s.wait(0.1)
    s.say(ch, "Sir, please! The chef worked very hard on that disappointment!", eyes="teary", tears=0.5,
          mouth="wobbly", brow=1, arms="heart", hold=None)
    s.say(c, "Then get me the MANAGER! The manager of FEELINGS!", style="shout", arms="point", eyes="angry")
    s.say(pc, "I am the manager of feelings, sir. How may I validate you?", eyes="open", mouth="smile",
          arms="present", look=0.8)
    s.say(c, "VALIDATE ME HARDER!", style="shout", arms="up", eyes="squeeze", mouth="scream")
    # dramatic faint, caught by both
    c.to(s.t, 0.5, "in", rot=1.35, y=STAGE_Y - 60, arms="out")
    pc.to(s.t, 0.4, x=220, arms="grab")
    ch.to(s.t, 0.4, x=430, arms="grab")
    s.sfx("whoosh", gain=0.6)
    s.sfx("crowd_laugh", at=s.t + 0.4, gain=1.0, d=3.4)
    s.sfx("applause_big", at=s.t + 0.6, gain=0.6)
    s.overlay("sfx", at=s.t + 0.4, dur=1.2, text="*FAINTS*", x=380, y=640, size=110, color="#ffffff")
    s.wait(2.2)
    s.end()

    # ------------------------------------------------------------------ having fun + the knowing glance
    s = P.shot("stage", mood="roar", stool=1, table=1, table_x=TABLE_X, banner2="FEELINGS RESTAURANT")
    pc, ch = stage_duo(s, pc=dict(x=150, eyes="happy", mouth="grin", costume="posh", shades=0, arms="clap", clap=1),
                       chad=dict(x=760, eyes="happy", costume="waiter", mouth="grin", arms="clap", clap=1))
    c = s.actor("cartman", x=450, y=STAGE_Y, scale=0.95, eyes="happy", mouth="grin", arms="up", costume="bib",
                flail=0.35, z=1)
    for k in range(12):
        c.to(k * 0.45, 0.22, "out", hop=40)
        c.to(k * 0.45 + 0.22, 0.22, "in", hop=0)
    s.say(c, "Hahaha! Bahaha! Hahaha!", gap=0.0, advance=False)
    s.sfx("crowd_laugh", gain=0.6, d=4.0)
    s.camera(cx=450, cy=880, zoom=1.05)
    s.wait(0.7)
    # slow push to the two of them, warm music under
    s.camera(dur=2.5, cx=455, cy=760, zoom=1.15)
    pc.to(s.t, 0.5, look=1.0, eyes="warm", clap=0, arms="down", mouth="smile")
    ch.to(s.t, 0.5, look=-1.0, eyes="warm", clap=0, arms="down", mouth="smile")
    s.music("warm", gain=0.4, fade=1.0)
    s.overlay("glance", at=s.t + 0.4, dur=11.0, a=pc, b=ch, dy1=150, dy2=150)
    s.overlay("hearts", at=s.t + 0.6, dur=11.0, x0=150, x1=930, y=1300, n=12)
    s.wait(0.6)
    s.narr("They knew what was going on the whole time. They had made themselves as cringe as humanly "
           "possible, on purpose, to give Cartman this moment.")
    s.narr("The audience would never know. They didn't care. All that mattered was that the two of them knew.")
    s.say(ch, "Good job, bro.", style="whisper", gap=0.1)
    s.say(pc, "Good job, bro.", style="whisper", gap=0.4)
    s.end()

    # ------------------------------------------------------------------ after the assembly
    s = P.shot("stage", mood="idle", audience=0, spot=0)
    s.music("comedy", gain=0.2, fade=0.5)
    s.overlay("label", at=0.1, dur=1.8, text=["AFTER THE ASSEMBLY"], x=540, y=580, size=50)
    pc, ch = stage_duo(s, pc_x=230, chad_x=850, pc=dict(eyes="open", mouth="smile", shades=1, arms="hips"),
                       chad=dict(eyes="warm", mouth="smile", arms="heart"))
    c = s.actor("cartman", x=540, y=STAGE_Y, scale=1.0, eyes="half", mouth="smirk", arms="hips", puff=1.0,
                sparkle=1, z=1)
    s.camera(cx=540, cy=900, zoom=1.2)
    s.wait(0.4)
    s.say(c, "You're welcome. I just showed you two dweebs how to be funny. Write that down.", look=-0.5)
    s.say(ch, "Bro, you were amazing. Would you help us at the next emotional assembly?", arms="heart")
    s.say(pc, "Seriously, dude. We couldn't do this without you.", arms="present")
    c.to(s.t, 0.4, eyes="roll", looky=-1, look=0)
    s.sfx("whoosh", gain=0.4)
    s.wait(0.6)
    s.say(c, "Ugh. Fine. I guess I'll help you idiots try to be funny. I guess.", eyes="half", looky=0,
          mouth="smirk", arms="cross")
    c.set(s.t, walk=1)
    c.to(s.t, 2.0, "lin", x=1300, puff=1.0)
    s.wait(0.7)
    s.end()

    # ------------------------------------------------------------------ the plan behind the plan
    s = P.shot("stage", mood="idle", audience=0, spot=1, spot_x=540)
    s.music("warm", gain=0.35, fade=0.8)
    pc, ch = stage_duo(s, pc_x=400, chad_x=690, pc=dict(eyes="open", mouth="smile", shades=0, arms="hips", look=0.6),
                       chad=dict(eyes="warm", mouth="smile", arms="cross", look=-0.6))
    s.overlay("vignette", at=0, dur=40, strength=0.55)
    s.camera(cx=545, cy=760, zoom=1.6)
    s.camera(dur=30, ease="lin", zoom=1.85)
    s.say(pc, "He thinks he carried us.", mouth="smirk")
    s.say(ch, "Let him. For now.", mouth="smile")
    s.say(pc, "Boredom is what's really eating him. He picks fights because he's bored out of his mind.",
          mouth="flat", brow=0.4, arms="cross")
    s.say(ch, "It's the most painful feeling he's got. So we give him something better to do with it, "
              "and show him how to carry himself.", eyes="warm", arms="heart")
    s.say(pc, "We let him feel superior for now.", arms="hips")
    s.say(ch, "But eventually, we bring him back down.", brow=0.5)
    s.say(pc, "Gently. At the right time. If we push, he gets defensive.", eyes="warm")
    s.say(ch, "Then we wait for the right time.", mouth="smirk", eyes="half")
    pc.to(s.t, 0.3, "back", aRx=1.25, aRy=-0.1)
    ch.to(s.t, 0.3, "back", aLx=1.25, aLy=-0.1)
    s.sfx("pop", at=s.t + 0.3)
    s.overlay("glance", at=s.t + 0.3, dur=1.2, a=pc, b=ch, dy1=150, dy2=150)
    s.wait(1.3)
    s.end()

    s = P.shot("card", card="tbc", next="PART 3: THE LONG GAME")
    s.sfx("badum", gain=0.9)
    s.wait(2.6)
    s.end()
    return P.finalize()
