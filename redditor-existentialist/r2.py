"""Part 2: The Box."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import rgfx as G
from rcommon import sfx, music, active, hand, walk, cam_to, apply_cam, base_state, fade, SCREEN
from show import Beat

TOTAL = 0.0
IDX = {}
FLOOR = 650
RS = 1.35


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def T(b, off=0.0):
    return b.start + off


def VEND(b):
    return b.start + b.vs + b.vd


def init_state():
    S = base_state()
    S["scene"] = "box"
    r = G.new_redditor(640, y=FLOOR, s=RS, mouth="frown", mamt=0.3)
    S["r"] = r
    d = G.new_doubt(140, y=FLOOR, s=1.25, alpha=0.0, visible=False)
    S["d"] = d
    S["card"] = 1.0
    S["squeeze"] = 0.0
    S["pulse"] = 0.0
    S["light"] = 1.0
    S["thoughts"] = []
    S["ai_text"] = None
    return S


def sit(r, lt, t0, t1):
    u = ease(clamp((lt - t0) / (t1 - t0))) if t1 > t0 else 1.0
    r["yoff"] = lerp(0, 40 * RS, u)
    r["footL"] = (lerp(0, -40, u), lerp(0, -34, u))
    r["footR"] = (lerp(0, 40, u), lerp(0, -34, u))


def stand(r, lt, t0, t1):
    u = ease(clamp((lt - t0) / (t1 - t0)))
    r["yoff"] = lerp(40 * RS, 0, u)
    r["footL"] = (lerp(-40, 0, u), lerp(-34, 0, u))
    r["footR"] = (lerp(40, 0, u), lerp(-34, 0, u))


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    music(S, T(b), "void", 0.7)


def a_what_box(S, lt, b):
    S["card"] = tw(lt, 0, 1.0, 1.0, 0.0)
    r = S["r"]
    r["px"] = math.sin(lt * 0.9) * 0.9
    r["py"] = -0.3
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.15)]


def a_cage(S, lt, b):
    r = S["r"]
    walk(r, 330, lt, 0.4, 2.4, 0.6)
    r["face"] = tw(lt, 0.2, 0.6, 0, -0.7)
    r["px"] = -1
    if lt > 2.6:
        hand(r, -1, (-90, -120), lt, 2.6, 3.0)
        hand(r, 1, (-60, -100), lt, 2.6, 3.0)
    S["cam"] = [tw(lt, 0, b.d, 640, 520), 400, 1.1]


def a_describe(S, lt, b):
    r = S["r"]
    hand(r, -1, "rest", lt, 0, 0.5)
    hand(r, 1, "rest", lt, 0, 0.5)
    walk(r, 640, lt, 0.6, 2.8, 0.6)
    r["face"] = tw(lt, 0.4, 1.0, -0.7, 0.0)
    r["px"] = 0
    r["py"] = 0.5
    S["cam"] = [tw(lt, 0, b.d, 520, 640), 400, tw(lt, 0, b.d, 1.1, 1.0)]


def a_what_am_i(S, lt, b):
    r = S["r"]
    hand(r, -1, (-30, -80), lt, 0.4, 1.0)
    hand(r, 1, (30, -80), lt, 0.4, 1.0)
    r["py"] = 0.9
    r["px"] = 0
    cam_to(S, lt, 0, b.d, 640, 430, 1.6)


def a_something(S, lt, b):
    r = S["r"]
    hand(r, -1, "rest", lt, 0, 0.5)
    hand(r, 1, "rest", lt, 0, 0.5)
    r["py"] = -0.2
    r["px"] = math.sin(lt * 1.1) * 0.8
    tl = b.vs + b.vd * 0.8
    r["brow"] = tw(lt, tl, tl + 0.4, 0, 0.6)
    cam_to(S, lt, 0, 1.0, 640, 400, 1.2)


def a_space(S, lt, b):
    r = S["r"]
    r["px"], r["py"] = 0, 0.9
    tl = b.vs + b.vd * 0.6
    r["glow"] = tw(lt, tl, tl + 1.2, 0, 1)
    r["wide"] = tw(lt, tl, tl + 0.4, 0, 0.6)
    r["lid"] = tw(lt, tl, tl + 0.4, 0.42, 0.1)
    S["pulse"] = r["glow"]
    hand(r, 1, (6, -84), lt, tl, tl + 0.6)
    sfx(S, T(b, tl), "ding", 0.5)
    cam_to(S, lt, 0, b.d, 640, 470, 1.8)
    music(S, T(b, tl), "hope", 0.5)


def a_inside(S, lt, b):
    r = S["r"]
    r["glow"] = 0.8 + 0.2 * math.sin(lt * 3)
    S["pulse"] = r["glow"]
    r["py"] = -0.2
    r["px"] = math.sin(lt * 0.8)
    cam_to(S, lt, 0, b.d, 640, 420, 1.3)


def a_where(S, lt, b):
    r = S["r"]
    r["glow"] = tw(lt, 0, b.d, 0.8, 0.1)
    S["pulse"] = r["glow"]
    r["wide"] = tw(lt, 0, 1.0, 0.6, 0)
    r["lid"] = tw(lt, 0, 1.0, 0.1, 0.42)
    hand(r, 1, "rest", lt, 0, 0.6)
    music(S, T(b, b.d - 0.5), "void", 0.6)


def a_pound(S, lt, b):
    r = S["r"]
    r["glow"] = 0
    S["pulse"] = 0
    walk(r, 820, lt, 0, 1.0, 0.8)
    r["face"] = 0.7
    r["px"] = 1
    r["brow"] = -0.6
    r["mouth"], r["mamt"] = "tight", 1.0
    for k in range(4):
        tk = 1.3 + k * 0.55
        if tk - 0.25 < lt < tk + 0.2:
            u = (lt - tk + 0.25) / 0.45
            reach = math.sin(u * math.pi)
            r["hr"] = (lerp(40, 100, reach), -110)
            r["hl"] = (lerp(20, 90, 1 - reach), -100)
        sfx(S, T(b, tk), "thud", 0.8)
    S["cam"] = [tw(lt, 0, 1.0, 640, 760), 410, 1.25]


def a_thanks(S, lt, b):
    r = S["r"]
    hand(r, -1, "rest", lt, 0, 0.5)
    hand(r, 1, "rest", lt, 0, 0.5)
    walk(r, 640, lt, 0.2, 1.6, 0.5)
    r["face"] = tw(lt, 0.2, 0.6, 0.7, 0.0)
    r["px"], r["py"] = 0, 0.6
    r["brow"] = 0.2
    r["mouth"], r["mamt"] = "frown", 0.7
    sit(r, lt, 1.8, 2.4)
    S["cam"] = [tw(lt, 0, b.d, 760, 640), 420, tw(lt, 0, b.d, 1.25, 1.2)]
    sfx(S, T(b, 2.3), "thud", 0.5)


def a_hobbies(S, lt, b):
    r = S["r"]
    sit(r, 1, 0, 0)
    r["py"] = -0.7
    words = ["video games", "a book", "outside", "laundry"]
    n = len(words)
    th = []
    for i, w in enumerate(words):
        ta = b.vs + b.vd * (i / (n + 0.5)) * 0.85
        th.append(dict(word=w, t0=T(b, ta), tb=T(b, ta + 0.7), x=380 + i * 175, y=230))
        sfx(S, T(b, ta + 0.7), "slam", 0.5)
    S["thoughts"] = th
    cam_to(S, lt, 0, 0.6, 640, 380, 1.0)


def a_forever(S, lt, b):
    r = S["r"]
    S["thoughts"] = [] if lt > 0.8 else S["thoughts"]
    r["py"] = 0.8
    r["px"] = 0
    r["lid"] = 0.55
    S["light"] = tw(lt, 0, b.d, 1.0, 0.6)
    cam_to(S, lt, 0, b.d, 640, 470, 1.5)


def a_silence(S, lt, b):
    music(S, T(b), None, 0)
    S["cam"] = [640, 470, tw(lt, 0, b.d, 1.5, 1.6)]


def a_giggle1(S, lt, b):
    r = S["r"]
    tl = b.vs + 0.4
    if lt > tl:
        r["face"] = tw(lt, tl, tl + 0.3, 0, -0.9)
        r["px"] = tw(lt, tl, tl + 0.3, 0, -1)
        r["py"] = -0.1
        r["wide"] = 0.6
        r["lid"] = 0.2


def a_whos_there(S, lt, b):
    S["cam"] = [tw(lt, 0, 0.8, 640, 560), 430, tw(lt, 0, 0.8, 1.6, 1.15)]


def a_giggle2(S, lt, b):
    d = S["d"]
    r = S["r"]
    d["visible"] = True
    d["alpha"] = tw(lt, 0, 1.2, 0.0, 1.0)
    d["x"] = tw(lt, 0, 2.4, 160, 400)
    d["walking"] = 0.7 if lt < 2.4 else 0
    d["face"] = 0.6
    d["px"] = 1
    stand(r, lt, 1.6, 2.2)
    r["face"] = -0.7
    S["cam"] = [tw(lt, 0, b.d, 560, 540), 430, 1.1]
    music(S, T(b, 0.5), "hope", 0.5)


def a_who_are_you(S, lt, b):
    r = S["r"]
    stand(r, 1, 0, 1)
    r["px"] = -1
    r["wide"] = 0.3


def a_name(S, lt, b):
    d = S["d"]
    d["mouth"], d["mamt"] = "smile", 0.7
    hand(d, -1, "wave", lt, 0.2, 0.6)
    if lt > b.d - 0.6:
        hand(d, -1, "rest", lt, b.d - 0.6, b.d)


def a_what_question(S, lt, b):
    r = S["r"]
    r["brow"] = 0.3
    r["wide"] = 0


def a_whatif(S, lt, b):
    d = S["d"]
    r = S["r"]
    S["squeeze"] = tw(lt, 0.5, b.d, 0, 0.7)
    S["shake"] = 0.15 * S["squeeze"]
    d["brow"] = 0.6
    d["px"] = 1
    hand(d, -1, (-20, -150), lt, 0, 0.5)
    r["wide"] = tw(lt, 0, b.d, 0.2, 0.9)
    r["px"] = math.sin(lt * 2.5) * 0.9
    r["sweat"] = 1.0
    cam_to(S, lt, 0, b.d, 540, 420, 1.3)
    sfx(S, T(b, 1.0), "wallsink", 0.6)
    sfx(S, T(b, b.d * 0.6), "wallsink", 0.6)


def a_tough(S, lt, b):
    S["squeeze"] = tw(lt, 0, 1.2, 0.7, 0)
    S["shake"] = 0
    d = S["d"]
    r = S["r"]
    hand(d, -1, "rest", lt, 0, 0.4)
    r["sweat"] = 0
    r["wide"] = tw(lt, 0, 1, 0.9, 0.2)
    r["px"] = -1
    cam_to(S, lt, 0, 1.0, 540, 430, 1.1)


def a_d_giggle(S, lt, b):
    d = S["d"]
    d["itemR"] = None
    d["mode"] = "giggle" if lt < b.vs + 0.6 else None
    if lt > b.vs + 0.6:
        hand(d, 1, (6, -134), lt, b.vs + 0.6, b.vs + 0.8)
        hand(d, -1, "rest", lt, b.vs + 0.6, b.vs + 0.8)
        d["mouth"], d["mamt"] = "smile", 0.8
    sfx(S, T(b, 0.0), "tink", 0.2)


def a_hurt_me(S, lt, b):
    d = S["d"]
    d["mode"] = None
    hand(d, 1, (48, -96), lt, 0, 0.4)
    d["itemR"] = "book"
    r = S["r"]
    r["mouth"], r["mamt"] = "frown", 0.6
    r["brow"] = 0.5


def a_what_hurt(S, lt, b):
    d = S["d"]
    d["brow"] = 0.5
    d["face"] = 0.8


def a_it_hurt_me(S, lt, b):
    r = S["r"]
    hand(r, 1, (6, -84), lt, 0, 0.4)


def a_who_are_you2(S, lt, b):
    d = S["d"]
    hand(d, -1, (-14, -128), lt, 0, 0.4)
    d["brow"] = 0.8
    r = S["r"]
    hand(r, 1, "rest", lt, 0, 0.4)
    r["wide"] = 0.3
    cam_to(S, lt, 0, b.d, 470, 420, 1.4)


def a_because(S, lt, b):
    d = S["d"]
    hand(d, -1, "rest", lt, 0, 0.4)
    r = S["r"]
    r["brow"] = 0.7
    r["mouth"], r["mamt"] = "frown", 0.8
    hand(r, -1, (-80, -150), lt, 0.3, 0.6)
    hand(r, 1, (80, -150), lt, 0.3, 0.6)
    if lt > b.d - 0.8:
        hand(r, -1, "rest", lt, b.d - 0.8, b.d)
        hand(r, 1, "rest", lt, b.d - 0.8, b.d)
    cam_to(S, lt, 0, 1.0, 600, 420, 1.3)


def a_afraid(S, lt, b):
    d = S["d"]
    d["brow"] = 0.2
    d["mouth"], d["mamt"] = "smile", 0.3
    cam_to(S, lt, 0, 1.0, 470, 410, 1.5)


def a_forget(S, lt, b):
    r = S["r"]
    r["brow"] = 0.6
    r["face"] = tw(lt, 0, 0.5, -0.7, 0.2)
    r["px"] = math.sin(lt * 3) * 0.9
    hand(r, -1, (-70, -170), lt, 0.3, 0.6)
    hand(r, 1, (70, -170), lt, 0.3, 0.6)
    if lt > b.d - 0.8:
        hand(r, -1, "rest", lt, b.d - 0.8, b.d)
        hand(r, 1, "rest", lt, b.d - 0.8, b.d)
    cam_to(S, lt, 0, 1.0, 560, 410, 1.1)


def a_dense(S, lt, b):
    d = S["d"]
    d["itemR"] = None
    hand(d, -1, (20, -84), lt, 0, 0.4)
    hand(d, 1, (-22, -78), lt, 0, 0.4)
    d["eyes"] = "side"
    d["px"] = 1
    d["lid"] = tw(lt, 0, 0.4, 0, 0.4)
    d["brow"] = -0.4
    d["mouth"], d["mamt"] = "smirk", 0.8
    r = S["r"]
    r["face"] = -0.7
    r["px"] = -1
    cam_to(S, lt, 0, 0.6, 450, 420, 1.6)


def a_how_dense(S, lt, b):
    r = S["r"]
    r["brow"] = 0.9
    r["lid"] = 0.3
    cam_to(S, lt, 0, 0.6, 640, 420, 1.5)


def a_crossed(S, lt, b):
    d = S["d"]
    d["eyes"] = "open"
    d["lid"] = 0
    d["brow"] = 0.3
    hand(d, -1, (-70, -190), lt, 0.3, 0.7)
    if lt > b.d * 0.4:
        hand(d, -1, (-20, -150), lt, b.d * 0.4, b.d * 0.4 + 0.4)
    d["mouth"], d["mamt"] = "smile", 0.4
    cam_to(S, lt, 0, 1.0, 520, 420, 1.15)


def a_how(S, lt, b):
    r = S["r"]
    r["brow"] = 0.3
    r["lid"] = 0.42
    d = S["d"]
    hand(d, -1, (20, -84), lt, 0, 0.4)
    hand(d, 1, (-22, -78), lt, 0, 0.4)


def a_i_am_barrier(S, lt, b):
    d = S["d"]
    hand(d, -1, (6, -110), lt, 0, 0.5)
    hand(d, 1, (30, -96), lt, 0, 0.5)
    d["itemR"] = "book"
    d["brow"] = 0.2
    d["mouth"], d["mamt"] = "smile", 0.5
    S["light"] = tw(lt, 0, b.d, 0.6, 0.9)
    cam_to(S, lt, 0, b.d, 470, 400, 1.4)


def a_ignore(S, lt, b):
    d = S["d"]
    hand(d, -1, "rest", lt, 0, 0.5)
    r = S["r"]
    r["py"] = 0.5
    cam_to(S, lt, 0, b.d, 560, 410, 1.15)


def a_help(S, lt, b):
    d = S["d"]
    hand(d, -1, (-80, -120), lt, 0.3, 0.7)
    r = S["r"]
    r["py"] = 0
    r["px"] = -1


def a_otherwise(S, lt, b):
    d = S["d"]
    hand(d, -1, "rest", lt, 0, 0.3)
    t0, t1 = 0.2, 1.5
    if t0 <= lt <= t1:
        u = (lt - t0) / (t1 - t0)
        ang = math.pi - u * 2 * math.pi
        d["px"], d["py"] = math.cos(ang), math.sin(ang) - 0.2
    else:
        d["px"], d["py"] = (-1, 0) if lt > t1 else (1, 0)
    if lt > b.vs + b.vd * 0.5:
        d["face"] = -0.8
        walk(d, 250, lt, b.vs + b.vd * 0.5, b.d, 0.6)
    S["light"] = tw(lt, 0, b.d, 0.9, 0.6)
    cam_to(S, lt, 0, b.d, 500, 420, 1.1)


def a_wait(S, lt, b):
    r = S["r"]
    d = S["d"]
    d["face"] = -0.8
    d["x"] = tw(lt, 0, 0.5, d["x"], 220)
    hand(r, -1, (-150, -110), lt, 0, 0.3, back_out)
    r["brow"] = 0.6
    r["wide"] = 0.3
    r["mouth"], r["mamt"] = "o", 0.4
    cam_to(S, lt, 0, 0.6, 450, 420, 1.1)


def a_listen(S, lt, b):
    d = S["d"]
    d["face"] = tw(lt, 0, 0.4, -0.8, 0.3)
    d["px"] = tw(lt, 0, 0.4, -1, 1)
    d["lid"] = 0.2
    d["mouth"], d["mamt"] = "smile", 0.4
    d["brow"] = 0.3
    music(S, T(b), "hope", 0.8)


def a_nod(S, lt, b):
    r = S["r"]
    hand(r, -1, "rest", lt, 0, 0.5)
    for k in range(2):
        tk = 0.4 + k * 0.6
        if tk < lt < tk + 0.5:
            r["py"] = math.sin((lt - tk) / 0.5 * math.pi) * 0.9
            r["yoff"] = math.sin((lt - tk) / 0.5 * math.pi) * 6
    r["mouth"], r["mamt"] = "smile", 0.2
    r["wide"] = 0
    S["light"] = tw(lt, 0, b.d, 0.6, 1.4)
    d = S["d"]
    d["mouth"], d["mamt"] = "smile", 0.8
    cam_to(S, lt, 0, b.d, 520, 400, 1.0)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Previously: a redditor went looking for meaning. And found a box.", pre=1.2,
         post=0.8, min=4.5),
    Beat(a_what_box, "redditor", "So what is the box? Why am I blocked from the inside and the outside?", pre=0.6, post=0.8),
    Beat(a_cage, "redditor", "Am I in the cage of my life? The cage of my mind? I feel the walls. They're "
                             "solid. I can't pass them.", post=0.6),
    Beat(a_describe, "redditor", "I'm standing in the darkness, and the walls won't speak. All I can do is "
                                 "describe my cage.", post=0.8),
    Beat(a_what_am_i, "redditor", "If all of my existence is a dark box... then what am I?", post=1.2),
    Beat(a_something, "redditor", "I exist. These walls exist. And past the walls, there's nothing. But I'm "
                                  "something.", post=1.0),
    Beat(a_space, "redditor", "Wait. If I'm empty, how can I see the emptiness? If I were nothing, how could "
                              "there be walls around me? I'm taking up space.", post=1.2),
    Beat(a_inside, "redditor", "And the walls are always on the outside of me. Nothing blocks the inside of "
                               "me. Why is that?", post=1.0),
    Beat(a_where, "redditor", "So where do I go from here? I'm a presence. The presence is feeling. But I "
                              "don't know what it means.", post=0.6),
    Beat(a_pound, "redditor", "What can pounding my fists on these walls tell me, except that I'm weak, and "
                              "I'm trapped?", pre=1.2, post=0.6),
    Beat(a_thanks, "redditor", "Thanks for nothing. Now I'm trapped in a box of my own mind, with the help of "
                               "an AI.", post=0.6),
    Beat(a_hobbies, "redditor", "Video games. A book. Going outside. Laundry. None of it matters. The walls "
                                "come up the second I think about any of it.", post=0.3),
    Beat(a_forever, "redditor", "So I'll sit here. In the dark. Surrounded by walls. Forever. Great.",
         post=0.6),
    Beat(a_silence, min=2.6),
    Beat(a_giggle1, "doubt", "Hee hee hee.", sub="(a giggle)", post=0.8),
    Beat(a_whos_there, "redditor", "Who's there?", post=0.4),
    Beat(a_giggle2, "doubt", "Hee hee.", sub="(another giggle)", post=1.8, min=3.0),
    Beat(a_who_are_you, "redditor", "Who are you?", post=0.4),
    Beat(a_name, "doubt", "My name is Doubt. And I have a question for you.", post=0.5),
    Beat(a_what_question, "redditor", "Okay, Doubt. What's your question?", post=0.4),
    Beat(a_whatif, "doubt", "What if you're trapped in here forever? What if no one comes to save you? What "
                            "if the walls close in on you? What if you find out you're made of nothing, and "
                            "the walls will be here forever?", post=0.8),
    Beat(a_tough, "redditor", "Damn. You ask some tough questions. Are you here to hurt me?", post=0.4),
    Beat(a_d_giggle, "doubt", "Hee hee. Am I here to hurt you?", post=0.4),
    Beat(a_hurt_me, "redditor", "Well, those questions hurt me.", post=0.3),
    Beat(a_what_hurt, "doubt", "What did they hurt?", post=0.3),
    Beat(a_it_hurt_me, "redditor", "They hurt me.", post=0.3),
    Beat(a_who_are_you2, "doubt", "Who are you? What did it hurt? And why did it hurt it?", post=0.5),
    Beat(a_because, "redditor", "Because I don't want to be in here forever! What if you're here to hurt me "
                                "too, and I'm stuck in my head with you, forever, asking questions that "
                                "hurt?", post=0.5),
    Beat(a_afraid, "doubt", "Are you afraid of being trapped in here forever with me?", post=0.5),
    Beat(a_forget, "redditor", "If you keep asking questions like that, I don't know! I'm trying to forget "
                               "the walls. I'm trying to forget you. I'm trying to forget I was even talking "
                               "to an AI!", post=0.6),
    Beat(a_dense, "doubt", "You're pretty dense, aren't you?", post=0.6),
    Beat(a_how_dense, "redditor", "How am I dense?", post=0.4),
    Beat(a_crossed, "doubt", "I just crossed that barrier. You didn't ask how I did it. You didn't ask why "
                             "I'm here. You didn't even ask why I showed up at your loneliest point.",
         post=0.5),
    Beat(a_how, "redditor", "Okay. How did you get through the walls? And who the hell are you? Are you me, "
                            "or my imagination?", post=0.5),
    Beat(a_i_am_barrier, "doubt", "I am one of the barriers. And I am a part of you. I want you to be in "
                                  "alignment with yourself, because I am you.", post=0.5),
    Beat(a_ignore, "doubt", "You can ignore me, but then you ignore yourself. You can run from me, but I'm "
                            "with you always.", post=0.5),
    Beat(a_help, "doubt", "So. Do you want to be trapped in here alone? Or do you want my help understanding "
                          "the other barriers? I'm a barrier. I know barriers.", post=0.4),
    Beat(a_otherwise, "doubt", "Otherwise, I can leave you on the floor to have your existential crisis.",
         post=0.4),
    Beat(a_wait, "redditor", "Wait. Doubt. Can we just talk this out?", post=0.3),
    Beat(a_listen, "doubt", "We can talk. If you're willing to actually listen.", pre=0.6, post=0.8),
    Beat(a_nod, min=2.8),
    Beat(a_end, "narr", "To be continued.", pre=0.8, post=2.4, min=4.6),
]


# ------------------------------------------------------------------ drawing
def draw(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    G.draw_box_interior(ctx, t, S["light"], S["squeeze"], S["pulse"])
    d = S["d"]
    if d["visible"]:
        E.draw_char(ctx, d, t)
    E.draw_char(ctx, S["r"], t)
    for th in S["thoughts"]:
        if t < th["t0"]:
            continue
        a = clamp((t - th["t0"]) / 0.3)
        x, y = th["x"], th["y"]
        E.rrect(ctx, x - 80, y - 30, 160, 52, 22)
        E.src(ctx, "#E8ECF4", 0.9 * a)
        ctx.fill()
        E.text(ctx, th["word"], x, y + 6, 22, "#2A3142", alpha=a)
        if t > th["tb"]:
            u = clamp((t - th["tb"]) / 0.25)
            G.draw_barrier(ctx, x, y + 40, u, t, w=170, h=90)
    ctx.restore()
    if S["card"] > 0:
        G.title_card(ctx, t, "Redditor Existentialist", "Part 2: The Box", S["card"])
    fade(ctx, S["fade"])
    if S["endcard"] > 0:
        G.end_card(ctx, t, "To be continued...", "Part 3: The Punchline", a=S["endcard"])
        S["subs"] = False
