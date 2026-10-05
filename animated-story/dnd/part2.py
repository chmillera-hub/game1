"""DO NOT DISTURB, PART 2: THE RECORDER"""
from .common import new_part, title, tbc, hop_loop, ROOM_FLOOR, CHAIR_Y


def build():
    P = new_part(2, "THE RECORDER", "dnd2-the-recorder")
    title(P, 2, "THE RECORDER")

    # ------------------------------------------------------------------ outside: the vans
    s = P.shot("d_house", cans_down=1, lamp_broken=1, debris=1, vans=0)
    s.music("eerie", gain=0.35, fade=0.6)
    em = s.actor("emb", x=550, y=1450, scale=0.92, arms="hold", hold="cage", cage_full=1, rattle=0.2,
                 eyes="half", looky=0.8, mouth="frown", walk=0.6)
    s.camera(cx=540, cy=1150, zoom=1.35)
    em.to(0, 7.5, "lin", x=380, y=1500)
    s.narr("Previously: Embarrassment broke into his friend's house to catch a thing that should never have "
           "left its cage.")
    s.say(em, "Okay. Okay. Nobody saw anything. Walk home. Nice and normal.", style="mutter")
    em.set(s.t, walk=0)
    s.end()

    s = P.shot("d_house", cans_down=1, lamp_broken=1, debris=1, vans=1)
    em = s.actor("emb", x=380, y=1500, scale=0.92, arms="hold", hold="cage", cage_full=1, eyes="half", looky=0.8,
                 mouth="frown")
    boss = s.actor("boss", x=860, y=1600, scale=0.95, arms="behind", behind=1, mouth="flat", z=1)
    ag1 = s.actor("agent", x=130, y=1640, scale=0.92, arms="behind", behind=1, mouth="flat", z=1)
    ag2 = s.actor("agent", x=1020, y=1640, scale=0.92, arms="behind", behind=1, mouth="flat", z=1)
    s.camera(cx=540, cy=1200, zoom=1.0)
    s.sfx("vandoor", gain=0.9)
    s.wait(0.6)
    em.to(s.t, 0.2, looky=0, eyes="wide", mouth="o")
    s.sfx("dun", gain=0.8)
    s.wait(0.2)
    em.to(s.t, 0.3, mortified=0.7, sweat=2)
    s.think(em, "Oh God. Act natural. Act like I'm in control of the situation.", icon="!!")
    s.end()

    s = P.shot("d_house", cans_down=1, lamp_broken=1, debris=1, vans=1)
    s.camera(cx=60, cy=1100, zoom=1.6)
    s.camera(dur=3.0, ease="inout", cx=1000, cy=1400, zoom=1.6)
    s.cc("[The street is wrecked. Trash cans, lights, debris. He did all of this.]", at=0.2, dur=2.8)
    s.wait(3.1)
    s.end()

    s = P.shot("d_house", cans_down=1, lamp_broken=1, debris=1, vans=1)
    em = s.actor("emb", x=380, y=1500, scale=0.92, arms="hold", hold="cage", cage_full=1, eyes="wide",
                 mouth="grimace", mortified=0.7, sweat=2)
    boss = s.actor("boss", x=860, y=1600, scale=0.95, arms="behind", behind=1, mouth="flat", z=1)
    s.camera(cx=620, cy=1150, zoom=1.3)
    s.wait(0.4)
    s.sfx("dun", gain=0.6)
    s.overlay("glance", at=0.4, dur=1.0, a=boss, b=em, dy1=120, dy2=110)
    s.wait(1.0)
    # snaps to attention
    em.to(s.t, 0.15, arms="salute", hop=20, eyes="open", mouth="grin")
    em.to(s.t + 0.15, 0.15, hop=0)
    s.sfx("click", gain=0.6)
    s.wait(0.3)
    s.say(em, "Hey, boss! How you doing? Yeah, it's all good. Got the thing right here. Nothing to be afraid "
              "of. Hehe.", mouth="grin", gest=1.0, speed=1.05)
    em.set(s.t, arms="hold", hold="cage")
    s.wait(0.6)
    s.end()

    # ------------------------------------------------------------------ the boss decides
    s = P.shot("d_house", cans_down=1, lamp_broken=1, debris=1, vans=1)
    boss = s.actor("boss", x=700, y=1600, scale=1.0, arms="behind", behind=1, mouth="flat")
    aide = s.actor("aide", x=330, y=1600, scale=0.95, arms="hold", hold="clipboard", mouth="flat", look=0.8)
    s.camera(cx=540, cy=1080, zoom=1.35)
    s.say(aide, "Shall I process his termination, Doctor?", style="whisper", pre=0.3)
    s.wait(0.4)
    s.say(boss, "Not yet.", mouth="smirk")
    s.camera(dur=0.8, cx=710, cy=760, zoom=2.4)
    s.say(boss, "He's friends with the one who got bitten. That makes him useful.", mouth="smirk", pre=0.4)
    s.say(aide, "Do we tell him?", style="whisper")
    s.say(boss, "No.", mouth="flat", gap=0.6)
    s.end()

    # ------------------------------------------------------------------ Calm Corp: the tiny chair
    s = P.shot("d_office", tinychair=1)
    s.music("muzak", gain=0.3, fade=0.5)
    boss = s.actor("boss", x=540, y=1260, scale=1.0, arms="behind", behind=1, mouth="flat")
    em = s.actor("emb", x=540, y=1700, scale=0.9, sit=1, arms="wring", rub=0.6, eyes="open", mouth="grimace",
                 mortified=0.4, layer=1, looky=-0.6)
    s.camera(cx=540, cy=1150, zoom=1.0)
    s.overlay("label", at=0.1, dur=1.8, text=["CALM CORP HQ"], x=540, y=1500, size=46)
    s.wait(0.8)
    s.say(em, "Doctor Contempt, I just want to say how sorry I am. I feel terrible about-", gap=0.0)
    s.say(boss, "Your feelings are not relevant here.", mouth="smirk")
    em.to(s.t - 0.6, 0.3, eyes="wide", mouth="o", mortified=0.8)
    s.say(boss, "You lost a level five specimen. You destroyed a street. You broke into a civilian's home.",
          mouth="flat")
    s.say(em, "Technically he's my friend, so it was more of a visit-", gap=0.0, mouth="grimace")
    s.say(boss, "Your friend was in contact with the specimen. That is the only reason you still have a badge.",
          mouth="smirk")
    s.end()

    s = P.shot("d_office", tinychair=1)
    boss = s.actor("boss", x=540, y=1260, scale=1.0, arms="hold", hold="recorder", mouth="flat")
    em = s.actor("emb", x=540, y=1700, scale=0.9, sit=1, arms="wring", eyes="open", mouth="grimace",
                 mortified=0.6, layer=1, looky=-0.6)
    s.camera(cx=540, cy=1080, zoom=1.35)
    s.say(boss, "You'll carry this.", mouth="flat", pre=0.3)
    s.say(em, "A tracker?", mouth="o")
    s.say(boss, "A recorder. Everything he says, we hear.", mouth="smirk")
    s.say(em, "Isn't that a little... shady?", mouth="wobbly", brow=0.8)
    s.say(boss, "You can carry it. Or you can clear out your desk tonight.", mouth="smirk", glint=1)
    s.say(em, "No! No. Recording. I love recording. Big fan.", mouth="grin", sweat=2, mortified=0.9, speed=1.08)
    s.say(boss, "Good. And don't tell him.", mouth="flat", gap=0.6)
    s.end()

    # ------------------------------------------------------------------ the visit
    s = P.shot("d_room", chair=1, rain=1, door=1)
    s.music("muzak", gain=0.2, fade=0.5)
    td = s.actor("tired", x=330, y=CHAIR_Y, scale=1.1, sit=1, arms="cross", eyes="half", mouth="flat", phones=0,
                 bandage=1)
    em = s.actor("emb", x=760, y=ROOM_FLOOR - 20, scale=0.92, arms="hold", hold="snacks", eyes="open",
                 mouth="grin", mortified=0.3, z=1)
    s.camera(cx=560, cy=1080, zoom=1.2)
    s.overlay("label", at=0.3, dur=2.4, text=["REC ●"], x=880, y=1080, size=40, bg="#ff3b3b", color="#efe6d2")
    s.say(em, "HEY, BUDDY! I BROUGHT SNACKS!", style="shout", pre=0.3, look=0.4, looky=0.6)
    s.say(td, "Why are you talking to your pocket?", look=0.8)
    s.say(em, "I'm not! Ha. Haha.", mouth="grimace", look=-0.6, looky=0)
    s.think(em, "Be cool. Be nice. Don't let him say anything weird. They're listening.", icon="REC")
    s.say(td, "So that thing that bit me-", look=0.8, gap=0.0)
    s.say(em, "WHAT A NICE DAY IT IS!", style="shout", arms="out", hold=None, eyes="wide", mouth="grin")
    s.wait(0.3)
    s.camera(dur=0.4, cx=200, cy=760, zoom=1.8)
    s.say(td, "It's raining.", look=-0.6)
    s.camera(dur=0.4, cx=560, cy=1080, zoom=1.2)
    s.think(em, "Don't let him implicate himself. Don't give them anything they can use.", icon="!!",
            mouth="wobbly", sweat=2)
    s.end()

    s = P.shot("d_room", chair=1, rain=1, door=1)
    td = s.actor("tired", x=330, y=CHAIR_Y, scale=1.1, sit=1, arms="cross", eyes="half", mouth="flat", phones=0,
                 bandage=1, look=0.8)
    em = s.actor("emb", x=760, y=ROOM_FLOOR - 20, scale=0.92, arms="wring", eyes="open", mouth="grin",
                 mortified=0.4, z=1, sweat=1)
    s.camera(cx=560, cy=1080, zoom=1.2)
    s.say(em, "So how's the arm? You feel totally normal, right? Normal is good. Say normal.", gest=1.0)
    s.say(td, "I feel weird. I could hear your heartbeat from downstairs.", eyes="open")
    td.to(s.t - 2.0, 0.2, glow=0.7)
    td.to(s.t - 1.2, 0.4, glow=0)
    s.sfx("heartbeat", at=s.t - 2.0, gain=0.5)
    em.to(s.t, 0.2, eyes="wide", mouth="o", mortified=0.9, sweat=3)
    s.wait(0.4)
    s.say(em, "HA! He's joking! Funny guy! Very normal guy!", style="shout", looky=0.6, look=0.4,
          mouth="grin")
    td.to(s.t, 0.3, eyes="squint")
    s.wait(0.6)
    s.end()

    # ------------------------------------------------------------------ the trip
    s = P.shot("d_room", chair=1, rain=1, door=1)
    td = s.actor("tired", x=330, y=CHAIR_Y, scale=1.1, sit=1, arms="cross", eyes="squint", mouth="flat",
                 phones=0, bandage=1, look=0.8)
    em = s.actor("emb", x=760, y=ROOM_FLOOR - 20, scale=0.92, arms="out", eyes="open", mouth="grin",
                 mortified=0.5, z=1)
    imp = s.actor("imp", x=900, y=ROOM_FLOOR + 30, scale=0.7, wall=1, pant=1, z=2)
    rec = s.actor("rec", x=780, y=1440, scale=1.6, visible=0, z=3)
    s.camera(cx=600, cy=1150, zoom=1.15)
    s.say(em, "Well! I should go. Lots of very normal stuff to do-", gap=0.0)
    em.set(s.t, walk=1)
    em.to(s.t, 0.4, x=880)
    s.wait(0.4)
    # trips over the tripwire
    em.set(s.t, walk=0, arms="up", eyes="wide", mouth="scream")
    em.to(s.t, 0.35, "in", rot=-1.5, y=ROOM_FLOOR + 60, x=700)
    s.sfx("thud", at=s.t + 0.35, gain=0.9)
    s.overlay("sfx", at=s.t + 0.35, dur=0.7, text="WHUMP", x=700, y=900, size=100, color="#efe6d2")
    rec.set(s.t + 0.35, visible=1)
    rec.to(s.t + 0.35, 0.6, "out", x=430, y=1500)
    s.sfx("click", at=s.t + 0.7, gain=0.8)
    s.wait(1.2)
    s.camera(dur=0.4, cx=430, cy=1380, zoom=2.4)
    s.cc("[Beep. Beep. A little red light.]", dur=1.8)
    s.wait(1.8)
    s.end()

    s = P.shot("d_room", chair=1, rain=1, door=1)
    td = s.actor("tired", x=330, y=CHAIR_Y, scale=1.1, sit=1, arms="cross", eyes="half", mouth="flat",
                 phones=0, bandage=1, look=0.3, looky=0.8)
    em = s.actor("emb", x=700, y=ROOM_FLOOR + 60, scale=0.92, rot=-1.5, arms="up", eyes="wide",
                 mouth="grimace", mortified=1.0, z=1)
    rec = s.actor("rec", x=430, y=1500, scale=1.6, z=3)
    s.camera(cx=540, cy=1200, zoom=1.3)
    s.say(em, "That's my... pager. It's an old pager. Pagers are back. Very retro.", pre=0.3, speed=1.05)
    s.say(td, "Cool.", eyes="half", look=0.8, looky=0, gap=0.6)
    em.to(s.t, 0.3, rot=0, y=ROOM_FLOOR - 20, x=520, arms="reach")
    rec.set(s.t + 0.3, visible=0)
    em.set(s.t + 0.35, arms="out")
    s.wait(0.4)
    em.set(s.t, walk=1.3)
    em.to(s.t, 1.0, "in", x=1350)
    s.say(em, "Okay bye love you see you later!", speed=1.25, advance=False)
    s.sfx("doorslam", at=s.t + 1.0, gain=0.7)
    s.param(at=s.t + 1.0, dur=0.15, door=0)
    s.wait(1.4)
    s.end()

    # ------------------------------------------------------------------ he knows
    s = P.shot("d_room", chair=1, rain=1, door=0)
    s.music("spy", gain=0.4, fade=0.4)
    td = s.actor("tired", x=330, y=CHAIR_Y, scale=1.1, sit=1, arms="cross", eyes="squint", mouth="flat",
                 phones=0, bandage=1, look=1)
    s.camera(cx=330, cy=940, zoom=2.3)
    s.think(td, "That was a recorder. Somebody wants to hear what I say.", icon="REC", pre=0.3)
    s.think(td, "He's scared of somebody. And it isn't me.", icon="hm")
    td.to(s.t, 0.4, look=0.4, looky=0.9)
    s.think(td, "And it has something to do with that thing.", icon="?")
    s.end()

    s = P.shot("d_screen", query="calm corp", results=[
        ("Calm Corp: Feel Less.", "Official site. Emotional wellness solutions for a quieter world."),
        ("Calm Corp denies sewer incident", "Residents report strange noises beneath the campus..."),
        ("Calm Corp campus: 300 acres, mostly underground", "City records, zoning permits"),
        ("Missing pets reported near Calm Corp", "Local news"),
    ])
    s.sfx("typing", gain=0.7)
    s.wait(3.0)
    s.say("tired", "Calm Corp. 'Feel less.' Great slogan.", style="mutter")
    s.wait(0.6)
    s.end()

    s = P.shot("d_room", chair=1, rain=1, door=0)
    td = s.actor("tired", x=540, y=ROOM_FLOOR - 40, scale=1.15, arms="cross", eyes="half", mouth="flat",
                 phones=0, bandage=1)
    s.camera(cx=540, cy=1050, zoom=1.5)
    s.say(td, "They bugged my friend to spy on me.", pre=0.3)
    s.say(td, "Fine. I'll go see them myself.", eyes="squint")
    s.wait(0.3)
    s.say(td, "I'm not sneaking in. I'm walking in the front door.", arms="hold", hold="clipboard")
    s.say(td, "Nobody stops a guy who looks this tired.", eyes="half", gap=0.8)
    s.end()

    tbc(P, "PART 3: THE HARVEST")
    return P.finalize()
