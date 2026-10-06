"""Episode 2: Villain School."""
import math

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import mgfx as M
from mcommon import (sfx, hand, walk, cam_to, mus, base_state, T, VEND, bleep, place, stare, draw_world,
                     overlays, GROUND)
from show import Beat

TOTAL = 0.0
IDX = {}


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def init_state():
    S = base_state()
    S["boredom"] = M.new_boredom(380)
    S["doubt"] = M.new_doubt(560, mouth="smile", mamt=0.3, itemR="book", face=0.4, px=1)
    S["doubt"]["hr"] = (48, -96)
    S["vex"] = M.new_char("vex", 860, face=-0.5, px=-1)
    S["goons"] = [M.new_char(k, x, s=0.8, face=0.5, px=1) for k, x in (("goon1", 120), ("goon2", 230), ("goon3", 340))]
    S["pilot"] = M.new_char("vex", 0, y=-300, s=0.7)
    S["props"] = {"@board": lambda ctx, S, t: M.whiteboard(ctx, 980, 330, t, S["fx"].get("plan", 0.0)),
                  "@robot": draw_robot, "@goons": draw_goons, "@heart": draw_heart_fx}
    S["show"] = ["boredom", "doubt", "vex"]
    S["card"] = 1.0
    return S


def draw_goons(ctx, S, t):
    for g in S["goons"]:
        E.draw_char(ctx, g, t)


def draw_robot(ctx, S, t):
    r = S["fx"]["robot"]
    M.draw_robot(ctx, r["x"], GROUND, t, 0.9, r.get("step", 0), r.get("arm", 0), S["pilot"])


def draw_heart_fx(ctx, S, t):
    h = S["fx"].get("heart", 0)
    if h > 0:
        v = S["vex"]
        M.heart(ctx, v["x"], GROUND - 110, 0.6 + 1.6 * h, 1.0)
        for i in range(6):
            a = t * 2 + i * math.pi / 3
            E.sparkle(ctx, v["x"] + math.cos(a) * 70 * (0.5 + h), GROUND - 110 + math.sin(a) * 50 * (0.5 + h), 7,
                      "#FFE7F0", h)


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    mus(S, T(b), "lab", 0.6)


def a_pacing(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1, 0)
    v = S["vex"]
    v["x"] = 860 + math.sin(lt * 1.4) * 120
    v["walking"] = 0.6
    v["face"] = 0.5 if math.cos(lt * 1.4) > 0 else -0.5
    hand(v, -1, (-20, -110), lt, 0, 0.01)
    hand(v, 1, (30, -150), lt, 0, 0.01)
    S["cam"] = [700, 380, 1.05]


def a_badass(S, lt, b):
    v = S["vex"]
    v["x"] = tw(lt, 0, 0.6, v["x"], 820)
    v["face"], v["px"] = -0.5, -1
    hand(v, 1, (90, -170), lt, 0.2, 0.6)
    v["hr"] = (v["hr"][0], v["hr"][1] + math.sin(lt * 8) * 10)
    v["brow"] = -0.6


def a_identity(S, lt, b):
    v = S["vex"]
    hand(v, -1, (-10, -120), lt, 0, 0.4)
    hand(v, 1, (10, -116), lt, 0, 0.4)
    v["brow"] = 0.5
    v["mouth"], v["mamt"] = "smile", 0.4
    v["blush"] = 0.5
    S["cam"] = [820, 380, 1.35]


def a_eyebrow(S, lt, b):
    d, bo = S["doubt"], S["boredom"]
    d["brow"] = 0.9
    d["eyes"] = "open"
    d["mouth"], d["mamt"] = "smirk", 0.6
    bo["mode"] = "holdin"
    bo["shake"] = 2.0
    S["cam"] = [470, 400, 1.4]


def a_too_far(S, lt, b):
    bo = S["boredom"]
    bo["mode"] = None
    bo["shake"] = 0
    bo["cheeks"] = 0
    S["doubt"]["brow"] = 0.2
    S["cam"] = [600, 380, 1.1]


def a_best_villain(S, lt, b):
    bo = S["boredom"]
    bo["mouth"], bo["mamt"] = "smile", 0.6
    hand(bo, 1, (70, -170), lt, 0, 0.4)


def a_cool(S, lt, b):
    hand(S["boredom"], 1, "rest", lt, 0, 0.4)
    d = S["doubt"]
    d["mouth"], d["mamt"] = "smile", 0.7


def a_dumb_smile(S, lt, b):
    v = S["vex"]
    hand(v, -1, "rest", lt, 0, 0.3)
    hand(v, 1, "rest", lt, 0, 0.3)
    if lt < 2.0:
        v["mouth"], v["mamt"] = "laugh", 1.0
        v["eyes"] = "happy"
        v["blush"] = 1.0
        v["brow"] = 0.8
        v["yoff"] = -abs(math.sin(lt * 6)) * 6
    else:
        v["eyes"] = "open"
        v["mouth"], v["mamt"] = "flat", 0
        v["brow"] = -1.0
        v["blush"] = 0.4
        v["yoff"] = 0
        v["wide"] = tw(lt, 2.0, 2.2, 0.8, 0)
    S["cam"] = [820, 380, 1.5]


def a_acceptable(S, lt, b):
    v = S["vex"]
    v["brow"] = -1.0
    v["face"], v["px"] = 0.7, 1
    walk(v, 1250, lt, b.vs + b.vd * 0.6, b.d, 0.6)
    if lt > b.vs + b.vd:
        v["mouth"], v["mamt"] = "smile", 0.9
        v["eyes"] = "happy"
    S["cam"] = [tw(lt, 0, b.d, 820, 900), 380, tw(lt, 0, b.d, 1.5, 1.1)]


def a_mentors(S, lt, b):
    S["show"] = ["@board", "boredom", "doubt", "vex"]
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    place(v, 640, 0.5, 1, mouth="smile", mamt=0.5, brow=0.2, blush=0.3)
    place(bo, 460, 0.5, 1)
    place(d, 820, 0.5, 1, mouth="smile", mamt=0.4)
    S["fx"]["plan"] = clamp(lt / b.d)
    hand(d, 1, (110, -160), lt, 0.4, 0.8)
    d["hr"] = (110 + math.sin(lt * 6) * 10, -160)
    S["cam"] = [760, 380, 1.0]
    mus(S, T(b), "hope", 0.55)


def a_enough(S, lt, b):
    S["fx"]["plan"] = 1.0
    v = S["vex"]
    v["mouth"], v["mamt"] = "smile", 0.7
    S["cam"] = [760, 380, tw(lt, 0, b.d, 1.0, 1.15)]


def a_robot(S, lt, b):
    S["scene"] = "city"
    S["show"] = ["@goons", "@robot", "boredom", "doubt"]
    bo, d = S["boredom"], S["doubt"]
    place(bo, 1050, -0.6, -1, mouth="smile", mamt=0.5, s=0.8, lid=0.2)
    place(d, 1170, -0.6, -1, mouth="smile", mamt=0.5, s=0.8)
    r = dict(x=tw(lt, 0, b.d, 480, 700), step=lt * 4, arm=max(0, math.sin(lt * 2.4)))
    S["fx"]["robot"] = r
    S["fx"]["smash"] = (680, T(b, 2.2))
    S["shake"] = 0.4 * abs(math.sin(lt * 4))
    for k in range(int(b.d / 0.8)):
        sfx(S, T(b, 0.3 + k * 0.8), "mechstep", 0.7)
    sfx(S, T(b, 2.2), "explosion", 0.8)
    for i, g in enumerate(S["goons"]):
        g["yoff"] = -abs(math.sin(lt * 8 + i)) * 12
        g["mouth"], g["mamt"] = "laugh", 0.9
        g["hr"] = (60, -150)
    p = S["pilot"]
    p.update(x=0, y=-300, face=0.4, px=1, brow=-1.0, mouth="smirk", mamt=0.8)
    S["cam"] = [640, 360, 1.0]
    mus(S, T(b), "boss", 0.5)


def a_goon_cheer(S, lt, b):
    S["fx"]["robot"]["step"] = S["t"] * 4
    S["fx"]["robot"]["arm"] = max(0, math.sin(S["t"] * 2.4))
    for i, g in enumerate(S["goons"]):
        g["yoff"] = -abs(math.sin(lt * 8 + i)) * 12
        g["mouth"], g["mamt"] = "laugh", 0.9
        g["hr"] = (60, -150)


def a_glance(S, lt, b):
    r = S["fx"]["robot"]
    p = S["pilot"]
    r["step"] = 0
    S["shake"] = 0
    if lt < 1.4:
        p["px"] = 1
        p["mouth"], p["mamt"] = "smile", tw(lt, 0.3, 0.8, 0, 0.8)
        p["brow"] = 0.4
        p["blush"] = 0.7
    elif lt < 1.8:
        p["mouth"], p["mamt"] = "flat", 0
        p["brow"] = -1.0
        p["wide"] = 0.8
        p["blush"] = 0
    else:
        p["wide"] = 1.0
        p["mouth"], p["mamt"] = "o", 1.0
    if lt > 1.8:
        r["x"] = 700 + math.sin((lt - 1.8) * 9) * 30
        S["shake"] = 0.6
    bo, d = S["boredom"], S["doubt"]
    bo["lid"] = d["lid"] = 0.3
    bo["mouth"], bo["mamt"] = "smile", 0.7
    S["cam"] = [tw(lt, 0, 0.6, 640, 760), 300, tw(lt, 0, 0.6, 1.0, 1.4)]
    sfx(S, T(b, 1.9), "mechstep", 1.0)
    sfx(S, T(b, 2.3), "mechstep", 1.0)


def a_recover(S, lt, b):
    r = S["fx"]["robot"]
    r["x"] = 700
    S["shake"] = 0
    p = S["pilot"]
    p["wide"] = 0.6
    S["cam"] = [640, 360, tw(lt, 0, 0.6, 1.4, 1.0)]
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


def a_night(S, lt, b):
    S["scene"] = "lab"
    S["fx"] = {"wreck": 0.55, "dial": 0.1}
    S["show"] = ["boredom", "doubt", "vex"]
    S["fade"] = tw(lt, 0, 0.6, 1, 0)
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    place(v, 700, -0.2, 0, mouth="frown", mamt=0.8, brow=0.9, tears=1.0, py=0.8, yoff=30)
    v["footL"], v["footR"] = (-30, -26), (30, -26)
    hand(v, -1, (-20, -120), lt, 0, 0.01)
    hand(v, 1, (20, -116), lt, 0, 0.01)
    place(bo, 420, 0.4, 1, s=1.0)
    place(d, 960, -0.4, -1, s=1.25)
    S["cam"] = [700, 400, 1.2]
    mus(S, T(b), "sad", 0.7)


def a_lie(S, lt, b):
    v = S["vex"]
    v["shake"] = 0.6
    v["py"] = 0.8


def a_serious(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    v["shake"] = 0
    for c in (bo, d):
        c.update(lid=0.0, brow=0.9, mouth="frown", mamt=0.2, wide=0.4)
    bo.update(face=0.6, px=1, x=tw(lt, 0, 1.5, 420, 520))
    d.update(face=-0.6, px=-1, x=tw(lt, 0, 1.5, 960, 860))
    bo["walking"] = d["walking"] = 0.5 if lt < 1.5 else 0
    S["cam"] = [690, 400, tw(lt, 0, b.d, 1.2, 1.35)]


def a_suffering(S, lt, b):
    d = S["doubt"]
    hand(d, -1, (-100, -140), lt, 0, 0.5)
    S["vex"]["py"] = 0.3


def a_afraid(S, lt, b):
    hand(S["doubt"], -1, "rest", lt, 0, 0.4)


def a_think(S, lt, b):
    bo = S["boredom"]
    hand(bo, 1, (30, -150), lt, 0, 0.4)
    bo["mouth"], bo["mamt"] = "flat", 0


def a_plan(S, lt, b):
    S["show"] = ["@board", "boredom", "doubt", "vex", "@heart"]
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    v.update(py=-0.3, px=1, face=0.4, tears=0.5, mouth="o", mamt=0.5, brow=0.6)
    bo.update(x=tw(lt, 0, 1.2, 520, 880), face=0.5, px=1, walking=0.6 if lt < 1.2 else 0)
    d.update(x=tw(lt, 0, 1.2, 860, 1100), face=-0.5, px=-1, walking=0.6 if lt < 1.2 else 0)
    S["fx"]["plan"] = clamp((lt - 1.2) / (b.d - 1.4))
    d["itemR"] = None
    d["hr"] = (-110 + math.sin(lt * 8) * 10, -170)
    S["cam"] = [820, 380, 1.0]
    mus(S, T(b, 0.2), "hope", 0.7)


def a_heart(S, lt, b):
    v = S["vex"]
    S["fx"]["plan"] = 1.0
    S["fx"]["heart"] = ease(clamp(lt / 2.0))
    v.update(tears=0.3, mouth="smile", mamt=tw(lt, 0.5, 2.0, 0.2, 0.7), brow=0.7, blush=0.6)
    sfx(S, T(b, 0.2), "heartgrow", 0.8)
    S["cam"] = [740, 400, tw(lt, 0, b.d, 1.0, 1.4)]


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, min=3.6),
    Beat(a_pacing, "vex", "Okay. So. I went to villain school, and my villain friends are coming into town.",
         pre=0.6, post=0.4),
    Beat(a_badass, "vex", "We have to convince them I'm a total badass. Okay? You guys have to stop making me "
                          "feel guilty about being a villain when I'm around you.", post=0.4),
    Beat(a_identity, "vex", "Because I really like you guys and stuff. But I want you to support my identity "
                            "as a villain.", post=0.6),
    Beat(a_eyebrow, min=2.6),
    Beat(a_too_far, "doubt", "Okay. We'll let you know if you go too far.", post=0.3),
    Beat(a_best_villain, "boredom", "But we'll make sure you look like the best villain ever to your friends.",
         post=0.3),
    Beat(a_cool, "doubt", "You've only been cool to us, dude. So we'll be cool to you.", post=0.6),
    Beat(a_dumb_smile, min=3.0),
    Beat(a_acceptable, "vex", "Ahem. Good. Yes. That is... acceptable. Goodbye.", rate="-6%", post=1.8),
    Beat(a_mentors, "narr", "And so, Boredom and Doubt became something unexpected. Mentors. "
                            "Caregivers. The villain's secret support team.", pre=0.6, post=0.6),
    Beat(a_enough, "narr", "They made sure he did just enough evil to keep his reputation, without hurting "
                           "anybody.", post=1.0),
    Beat(a_robot, "narr", "Take the giant robot rampage. Every building pre-approved for demolition.",
         pre=0.6, post=0.6),
    Beat(a_goon_cheer, "goon", "Yeah! Smash it, Vex! You're the worst!", post=0.6),
    Beat(a_glance, min=3.0),
    Beat(a_recover, "vex", "Whoa! Whoa, whoa, whoa! Totally meant to do that!", pre=0.0, post=1.0),
    Beat(a_night, "narr", "But one night, it all came crashing down.", pre=1.0, post=1.0),
    Beat(a_lie, "vex", "My whole life is a lie. I'm lying to my friends about being villainous. I'm hiding "
                       "you two behind their backs. I don't know how long I can keep doing this.", rate="-6%",
         post=1.2),
    Beat(a_serious, min=2.6),
    Beat(a_suffering, "doubt", "Hey. Look at us. When we think about you, we can see that your embarrassment is "
                               "suffering.", post=0.4),
    Beat(a_afraid, "boredom", "It's afraid your friends will find out you've been getting help.", post=0.4),
    Beat(a_afraid, "doubt", "And it's afraid that if you cut ties with us, you won't have any help impressing "
                            "them at all.", post=0.5),
    Beat(a_think, "boredom", "So. Let's think really hard about this.", post=0.8),
    Beat(a_plan, "narr", "He expected them to shame him. Or to tell him not to worry about it. Instead, they "
                         "were already writing a master plan.", pre=0.6, post=1.0),
    Beat(a_heart, "narr", "And the villain felt something he didn't have a word for. But he felt it.",
         pre=0.8, post=2.6),
    Beat(a_end, min=4.0),
]


def draw(ctx, S, t):
    draw_world(ctx, S, t)
    overlays(ctx, S, t, "LAB PARTNERS", "Episode 2: Villain School", "To be continued...", "Episode 3: Vacation")
