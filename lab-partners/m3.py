"""Episode 3: Vacation."""
import math

import engine as E
from engine import tw, ease, clamp, lerp
import mgfx as M
from mcommon import (sfx, hand, walk, mus, base_state, T, place, stare, draw_world, overlays, GROUND)
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
    S["boredom"] = M.new_boredom(420)
    S["doubt"] = M.new_doubt(600, mouth="smile", mamt=0.3, itemR="book", face=0.4, px=1)
    S["doubt"]["hr"] = (48, -96)
    S["vex"] = M.new_char("vex", 900, face=-0.5, px=-1)
    S["goon"] = M.new_char("goon1", 300, s=0.85, face=0.5, px=1)
    S["goons"] = [M.new_char(k, x, s=0.85, face=0.5, px=1) for k, x in (("goon2", 440), ("goon3", 560))]
    S["minion"] = M.new_char("minion", 900, s=0.75, face=-0.5, px=-1, mouth="flat", mamt=0.0, brow=0.2)
    S["props"] = {"@goons": draw_goons, "@sign": lambda ctx, S, t: M.lab_wrecked_sign(ctx, t),
                  "@loungers": draw_loungers, "@desk": draw_desk, "@door": draw_door,
                  "@thought": draw_thought}
    S["show"] = ["boredom", "doubt", "vex"]
    S["card"] = 1.0
    return S


def draw_goons(ctx, S, t):
    for g in S["goons"]:
        E.draw_char(ctx, g, t)


def draw_loungers(ctx, S, t):
    M.lounger(ctx, 430)
    M.lounger(ctx, 880)


def draw_desk(ctx, S, t):
    M.office_desk(ctx, 420)
    M.laptop_call(ctx, 575, 472, t, 0.95, S["fx"].get("look", 0.0), S["fx"].get("worry", 0.0))


def draw_thought(ctx, S, t):
    a = S["fx"].get("thought", 0.0)
    if a > 0:
        v = S["vex"]
        M.thought_bubble(ctx, v["x"] + 230, 210, t, a)


def draw_door(ctx, S, t):
    u = S["fx"].get("door", 0.0)  # 0 closed, 1 open
    if u <= 0:
        return
    E.rrect(ctx, 1060, 260, 150, 340, 6)
    E.src(ctx, "#0A0610")
    ctx.fill()
    w = 150 * (1 - 0.8 * u)
    ctx.move_to(1210, 260)
    ctx.line_to(1210 - w, 250)
    ctx.line_to(1210 - w, 610)
    ctx.line_to(1210, 600)
    ctx.close_path()
    E.fill_stroke(ctx, "#5A3A22", "#1A0E06", 4)


def draw_news(ctx, S, t):
    def img(c):
        v = M.new_char("vex", 640, y=520, s=1.3, mouth="smirk", mamt=0.8, brow=-0.8, crown=True)
        E.draw_char(c, v, t)
        for i in range(8):
            a = t * 1.5 + i * math.pi / 4
            E.sparkle(c, 640 + math.cos(a) * 220, 330 + math.sin(a) * 120, 10, "#FFE36A", 0.8)
        E.text(c, "MASTER VILLAIN", 640, 150, 54, "#E8C84A", outline="#1A0E2A", olw=8)
    M.news_screen(ctx, t, "LORD VEX NAMED MASTER VILLAIN", "Lab of Boredom and Doubt destroyed... "
                  "Council celebrates... Lab reportedly 'mostly empty'... ", S["fx"]["news"], img)


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    mus(S, T(b), "sneaky", 0.55)


def a_plot(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1, 0)
    S["scene"] = "hall"
    S["show"] = ["goon", "@goons", "vex"]
    g, v = S["goon"], S["vex"]
    place(g, 300, 0.5, 1, s=0.85, mouth="smirk", mamt=0.8, brow=-0.8)
    for i, o in enumerate(S["goons"]):
        place(o, 440 + i * 120, 0.5 if i else -0.4, 1 if i else -1, s=0.85, mouth="smirk", mamt=0.8, brow=-0.8)
    place(v, 860, -0.5, -1, mouth="smirk", mamt=0.5, brow=-0.5)
    S["cam"] = [600, 380, 1.05]


def a_goon_plan(S, lt, b):
    g = S["goon"]
    hand(g, 1, (80, -170), lt, 0, 0.3)
    g["hr"] = (80, -170 + math.sin(lt * 9) * 12)
    for i, o in enumerate(S["goons"]):
        o["mode"] = "laugh" if lt > b.vs + b.vd - 1.2 else None
    if lt > b.vs + b.vd - 1.2:
        g["mode"] = "laugh"


def a_vex_great(S, lt, b):
    v = S["vex"]
    for o in [S["goon"]] + S["goons"]:
        o["mode"] = None
        o.update(face=0.6, px=1)
    v.update(sweat=1.0, mouth="smile", mamt=0.9, brow=0.6, wide=0.6)
    v["shake"] = 0.5
    hand(v, 1, (60, -150), lt, 0, 0.3)
    v["hr"] = (60, -150 + math.sin(lt * 10) * 8)
    S["cam"] = [820, 380, tw(lt, 0, 1.0, 1.05, 1.45)]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_warn(S, lt, b):
    S["scene"] = "lab"
    S["show"] = ["boredom", "doubt", "vex"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    place(bo, 420, 0.4, 1, mouth="flat", mamt=0.0)
    place(d, 600, 0.4, 1, s=1.0)
    place(v, 900, -0.5, -1, mouth="frown", mamt=0.6, brow=0.9, sweat=0.8)
    walk(v, 820, lt, 0, 0.6, 1.2)
    hand(v, -1, (-90, -150), lt, 0.3, 0.6)
    hand(v, 1, (90, -150), lt, 0.3, 0.6)
    v["hl"] = (v["hl"][0] + math.sin(lt * 7) * 10, v["hl"][1])
    v["hr"] = (v["hr"][0] - math.sin(lt * 7) * 10, v["hr"][1])
    S["cam"] = [660, 380, 1.1]
    mus(S, T(b), "sad", 0.45)


def a_scared(S, lt, b):
    v = S["vex"]
    hand(v, -1, (-10, -116), lt, 0, 0.4)
    hand(v, 1, (10, -112), lt, 0, 0.4)
    v.update(sweat=0.4, tears=0.6, py=0.6)
    S["cam"] = [820, 380, tw(lt, 0, b.d, 1.1, 1.4)]


def a_straight_to_work(S, lt, b):
    bo, d = S["boredom"], S["doubt"]
    for c in (bo, d):
        c.update(brow=0.9, lid=0.0, mouth="flat", mamt=0.0)
    bo.update(face=0.6, px=1)
    d.update(face=-0.6, px=-1)
    d["x"] = tw(lt, 0.6, 1.4, 600, 540)
    d["walking"] = 0.5 if 0.6 < lt < 1.4 else 0
    S["cam"] = [600, 380, tw(lt, 0, b.d, 1.2, 1.5)]
    mus(S, T(b), "hope", 0.4)


def a_bahamas(S, lt, b):
    bo = S["boredom"]
    bo["mouth"], bo["mamt"] = "smile", tw(lt, 1.5, 2.5, 0, 0.6)
    hand(bo, 1, (60, -150), lt, 0.4, 0.8)
    S["cam"] = [520, 380, 1.5]


def a_lol(S, lt, b):
    d = S["doubt"]
    d["mouth"], d["mamt"] = "smirk", 0.7
    d["brow"] = 0.3
    hand(S["boredom"], 1, "rest", lt, 0, 0.4)
    if lt > b.vs + b.vd - 1.2:
        d["mode"] = "giggle"
    S["cam"] = [560, 380, 1.5]


def a_overhear(S, lt, b):
    v, d = S["vex"], S["doubt"]
    d["mode"] = None
    v.update(tears=0.0, wide=0.9, mouth="o", mamt=0.6, brow=0.4, py=0.0)
    hand(v, -1, "rest", lt, 0, 0.3)
    hand(v, 1, "rest", lt, 0, 0.3)
    S["cam"] = [tw(lt, 0, 0.6, 560, 760), 380, 1.25]


def a_pack(S, lt, b):
    d, bo = S["doubt"], S["boredom"]
    d.update(face=0.5, px=1, mouth="smile", mamt=0.6)
    bo.update(face=0.5, px=1)
    S["vex"]["wide"] = 0.2
    S["cam"] = [660, 380, 1.15]


def a_look_good(S, lt, b):
    bo = S["boredom"]
    bo["mouth"], bo["mamt"] = "smile", 0.8
    hand(bo, 1, (70, -190), lt, 0, 0.3)  # thumbs up height
    v = S["vex"]
    if lt > b.vs + b.vd:
        v["mouth"], v["mamt"] = "smile", 0.7
        v["blush"] = 0.6
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_wreck(S, lt, b):
    S["scene"] = "lab"
    S["fx"] = {"wreck": 0.8, "dial": 0.0}
    S["show"] = ["@sign", "goon", "@goons", "vex"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    g, v = S["goon"], S["vex"]
    place(g, 300, 0.4, 1, s=0.85, mouth="laugh", mamt=0.9, brow=-0.8)
    for i, o in enumerate(S["goons"]):
        place(o, 460 + i * 160, 0.4, 1, s=0.85, mouth="laugh", mamt=0.9, brow=-0.8)
        o["yoff"] = -abs(math.sin(lt * 7 + i)) * 16
        o["hr"] = (60, -150 + math.sin(lt * 12 + i) * 30)
    g["yoff"] = -abs(math.sin(lt * 7)) * 16
    g["hr"] = (60, -160 + math.sin(lt * 12) * 30)
    place(v, 820, -0.4, -1, mouth="smirk", mamt=0.6, brow=-0.6)
    S["shake"] = 0.3 * abs(math.sin(lt * 5))
    for k in range(int(b.d / 0.9)):
        sfx(S, T(b, 0.2 + k * 0.9), ("crumble", "hit", "slam", "crunch")[k % 4], 0.6)
    S["cam"] = [640, 360, 1.0]
    mus(S, T(b), "boss", 0.45)


def a_nothing_left(S, lt, b):
    g = S["goon"]
    g["hr"] = (80, -180)
    S["shake"] = 0


def a_empty_victory(S, lt, b):
    v = S["vex"]
    S["show"] = ["@sign", "goon", "@goons", "vex", "@thought"]
    # turns to the camera, totally agreeing, while picturing the duo on the beach
    v.update(face=0.0, px=0.0, py=0.0, brow=0.5, mouth="smile", mamt=0.6, lid=0.3, blush=0.4)
    hand(v, 1, "rest", lt, 0, 0.4)
    hand(v, -1, (-40, -130), lt, 0.2, 0.6)
    S["fx"]["thought"] = tw(lt, 0.8, 1.4, 0, 1)
    for o in [S["goon"]] + S["goons"]:
        o["mouth"], o["mamt"] = "laugh", 0.9
        o["hr"] = (60, -170)
        o["yoff"] = -abs(math.sin(lt * 7 + o["x"])) * 10
    sfx(S, T(b, 0.8), "sparkle", 0.4)
    sfx(S, T(b, 1.0), "water", 0.15)
    S["cam"] = [tw(lt, 0, 0.8, 700, 900), 330, tw(lt, 0, 0.8, 1.0, 1.25)]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_beach(S, lt, b):
    S["scene"] = "beach"
    S["fx"] = {}
    S["show"] = ["@loungers", "boredom", "doubt"]
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    bo, d = S["boredom"], S["doubt"]
    place(bo, 420, 0.3, 1, mouth="smile", mamt=0.6, lid=0.4, shades=True, tilt=-0.12)
    place(d, 870, -0.3, -1, mouth="smile", mamt=0.6, shades=True, itemR=None, tilt=0.12)
    bo["itemR"] = "cocktail"
    bo["hr"] = (60, -110)
    d["itemL"] = "cocktail"
    d["hl"] = (-60, -110)
    d["hr"] = E.pose("doubt", 1, "rest")
    S["cam"] = [640, 400, 1.0]
    mus(S, T(b), "beach", 0.6)
    sfx(S, T(b, 0.2), "water", 0.25)


def a_check_news(S, lt, b):
    d = S["doubt"]
    d["itemR"] = "phone"
    hand(d, 1, (40, -150), lt, 0, 0.4)


def a_news(S, lt, b):
    S["fx"]["news"] = tw(lt, 0, 0.3, 0, 1)
    sfx(S, T(b), "sting", 0.6)


def a_news_out(S, lt, b):
    S["fx"]["news"] = tw(lt, 0, 0.4, 1, 0)
    bo, d = S["boredom"], S["doubt"]
    d["itemR"] = None
    hand(d, 1, "rest", lt, 0, 0.4)
    for c in (bo, d):
        c.update(mouth="smile", mamt=0.9, brow=0.5)


def a_toast(S, lt, b):
    bo, d = S["boredom"], S["doubt"]
    hand(bo, 1, (90, -170), lt, 0, 0.5)
    hand(d, -1, (-90, -170), lt, 0, 0.5)
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.15)]


def a_clink(S, lt, b):
    bo, d = S["boredom"], S["doubt"]
    bo["x"] = tw(lt, 0, 0.8, 420, 560)
    d["x"] = tw(lt, 0, 0.8, 870, 720)
    bo["walking"] = d["walking"] = 0.5 if lt < 0.8 else 0
    bo["tilt"] = d["tilt"] = 0
    hand(bo, 1, (90, -170), lt, 0, 0.1)
    hand(d, -1, (-90, -170), lt, 0, 0.1)
    sfx(S, T(b, 1.0), "clink", 1.0)
    S["cam"] = [640, 400, tw(lt, 0, 1.2, 1.15, 1.35)]


def a_love(S, lt, b):
    bo, d = S["boredom"], S["doubt"]
    bo["eyes"] = d["eyes"] = "happy"
    S["fx"]["heart"] = ease(clamp(lt / 2.0))
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.35, 1.1)]
    S["fade"] = tw(lt, b.d - 0.6, b.d, 0, 1)


def a_harder(S, lt, b):
    S["scene"] = "hall"
    S["fx"] = {}
    S["show"] = ["goon", "@goons", "vex"]
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    g, v = S["goon"], S["vex"]
    place(v, 900, -0.4, -1, s=1.0, crown=True, mouth="smirk", mamt=0.5, brow=-0.6, shades=False)
    place(g, 300, 0.5, 1, s=0.85, mouth="laugh", mamt=0.9, brow=-1.0)
    g["hr"] = (70, -170 + math.sin(lt * 9) * 20)
    for i, o in enumerate(S["goons"]):
        place(o, 440 + i * 130, 0.5, 1, s=0.85, mouth="laugh", mamt=0.9, brow=-1.0)
        o["hr"] = (70, -170 + math.sin(lt * 9 + i) * 20)
        o["yoff"] = -abs(math.sin(lt * 8 + i)) * 10
    S["cam"] = [640, 380, 1.0]
    mus(S, T(b), "lab", 0.45)


def a_cant_say(S, lt, b):
    v = S["vex"]
    v["sweat"] = 0.8
    v["mouth"], v["mamt"] = "flat", 0.0
    v["px"] = 1
    S["cam"] = [860, 380, tw(lt, 0, b.d, 1.0, 1.5)]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_office(S, lt, b):
    S["scene"] = "office"
    S["show"] = ["vex", "@desk", "@door", "minion"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    v, m = S["vex"], S["minion"]
    place(v, 340, 0.5, 1, crown=True, mouth="frown", mamt=0.8, brow=0.9, sweat=0.0, y=GROUND - 120)
    v.update(face=-0.6, px=-1)  # ranting at the wall, away from the door
    place(m, 1135, -0.5, -1, s=0.75, mouth="flat", mamt=0.0, brow=0.2, lid=0.4)
    m["visible"] = False
    flail(v, lt)
    S["cam"] = [480, 400, 1.25]
    mus(S, T(b), "quirky", 0.4)


def flail(v, lt, amt=1.0):
    v["hl"] = (-90 - 30 * math.sin(lt * 11) * amt, -170 + 40 * math.cos(lt * 9) * amt)
    v["hr"] = (90 + 30 * math.sin(lt * 10 + 1) * amt, -170 + 40 * math.cos(lt * 8 + 2) * amt)
    v["tilt"] = 0.08 * math.sin(lt * 6) * amt
    v["yoff"] = -abs(math.sin(lt * 7)) * 6 * amt


def a_whine(S, lt, b):
    v, m = S["vex"], S["minion"]
    flail(v, lt)
    if b.id == "enter":
        # the minion slips in quietly; the duo on the laptop notice, Vex does not
        S["fx"]["door"] = tw(lt, 0.3, 0.7, 0, 1) if lt < 2.6 else tw(lt, 3.6, 4.0, 1, 0)
        m["visible"] = lt > 0.6
        m["x"] = tw(lt, 0.8, 4.0, 1135, 900)
        m["walking"] = 0.35 if 0.8 < lt < 4.0 else 0
        m["face"], m["px"] = -0.5, -1
        sfx(S, T(b, 0.3), "door", 0.25)
        S["fx"]["look"] = tw(lt, 1.0, 1.6, 0, 1)
        S["fx"]["worry"] = tw(lt, 1.4, 2.4, 0, 1)
        S["cam"] = [tw(lt, 0, 1.2, 480, 640), 400, tw(lt, 0, 1.2, 1.25, 1.0)]
    elif b.id in ("rule", "madeup"):
        m.update(x=900, walking=0)
        S["fx"]["look"] = 1.0
        S["fx"]["worry"] = 1.0
        S["cam"] = [740, 440, 1.45] if b.id == "rule" else [640, 400, 1.0]


def a_sir(S, lt, b):
    v, m = S["vex"], S["minion"]
    m.update(x=900, walking=0, visible=True)
    flail(v, lt, tw(lt, 0, 0.3, 1, 0))
    if lt > b.vs + b.vd:
        # slowly turns around and sees him
        v.update(face=tw(lt, b.vs + b.vd, b.vs + b.vd + 0.6, -0.6, 0.6), px=1, wide=1.0, mouth="o",
                 mamt=0.6, blush=0.9, brow=0.6)
    S["fx"]["worry"] = 1.0
    S["cam"] = [640, 400, 1.0]


def a_cough(S, lt, b):
    v = S["vex"]
    v.update(tilt=0, yoff=0, mouth="smirk", mamt=0.4, brow=-0.9, face=0.6, px=1, wide=0.0,
             blush=tw(lt, 0, 2.0, 0.9, 0.3))
    S["fx"]["look"] = tw(lt, 0, 0.6, 1, 0)
    S["fx"]["worry"] = tw(lt, 0, 0.6, 1, 0)
    hand(v, -1, (-10, -120), lt, 0, 0.2)
    hand(v, 1, (90, -100), lt, 0, 0.2)
    if lt > 1.2:
        hand(v, -1, "rest", lt, 1.2, 1.5)
    S["cam"] = [500, 400, 1.35]


def a_late(S, lt, b):
    S["cam"] = [880, 420, 1.4]


def a_right_there(S, lt, b):
    S["cam"] = [520, 400, 1.35]


def a_stare(S, lt, b):
    v, m = S["vex"], S["minion"]
    v["mouth"], v["mamt"] = "flat", 0.0
    S["cam"] = [640, 400, 1.0]
    sfx(S, T(b, 0.5), "cricket", 0.4)


def a_go_now(S, lt, b):
    S["cam"] = [640, 400, 1.0]


def a_oh_yeah(S, lt, b):
    m = S["minion"]
    if lt > b.vs + b.vd:
        m.update(face=0.5, px=1)
        walk(m, 1300, lt, b.vs + b.vd, b.d, 0.6)
        S["fx"]["door"] = tw(lt, b.vs + b.vd, b.vs + b.vd + 0.3, 0, 1)
    sfx(S, VEND_(b), "door", 0.4)


def a_door_open(S, lt, b):
    m = S["minion"]
    m["visible"] = False
    S["cam"] = [tw(lt, 0, 1.0, 640, 900), 400, tw(lt, 0, 1.0, 1.0, 1.3)]


def a_close_it(S, lt, b):
    v = S["vex"]
    hand(v, 1, (120, -160), lt, 0, 0.3)
    S["cam"] = [640, 400, 1.0]


def a_sigh(S, lt, b):
    m = S["minion"]
    m.update(visible=True, x=1135, face=-0.5, px=-1, lid=0.7, mouth="frown", mamt=0.4)
    hand(S["vex"], 1, "rest", lt, 0, 0.3)
    if lt > b.vs + b.vd:
        S["fx"]["door"] = tw(lt, b.vs + b.vd, b.vs + b.vd + 0.3, 1, 0)
        m["visible"] = lt < b.vs + b.vd + 0.2
    sfx(S, VEND_(b) + 0.15, "slam", 0.6)
    S["cam"] = [1000, 420, 1.3]


def VEND_(b):
    return b.start + b.vs + b.vd


def a_back_to_whine(S, lt, b):
    v = S["vex"]
    v.update(face=-0.6, px=-1, mouth="frown", mamt=0.8, brow=0.9, blush=0.0)
    flail(v, lt)
    S["cam"] = [tw(lt, 0, 0.5, 1000, 520), 400, tw(lt, 0, 0.5, 1.3, 1.2)]


def a_end(S, lt, b):
    flail(S["vex"], lt)
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)


HI = dict(rate="+16%", pitch="+55Hz")

BEATS = [
    Beat(a_title, min=3.6),
    Beat(a_plot, "narr", "Then came the day every villain dreads. His friends wanted a big score. And they "
                         "picked a target.", pre=0.4, post=0.4),
    Beat(a_goon_plan, "goon", "Tonight, we wreck that nerd lab! Every beaker! Every book!", post=0.5),
    Beat(a_vex_great, "vex", "Ha. Ha ha. Great. Love that. So evil.", rate="-4%", post=1.0),
    Beat(a_warn, "vex", "Guys. They're coming. Tonight. My friends are going to destroy your lab, and I can't "
                        "stop them without blowing my cover.", pre=0.6, post=0.4),
    Beat(a_scared, "vex", "I want to impress them. But I don't want anything to happen to you. I'm scared.",
         rate="-6%", post=1.0),
    Beat(a_straight_to_work, "narr", "Boredom and Doubt didn't tell him to calm down. They didn't tell him it "
                                     "was no big deal. They went straight to work.", post=0.4),
    Beat(a_bahamas, "boredom", "Well. If they're going to destroy our lab... we've always wanted to take a "
                               "vacation to the Bahamas. I think now is the perfect time.", post=0.3),
    Beat(a_lol, "doubt", "Yes. This is the perfect way to go on vacation. Everyone will think we were "
                         "destroyed. L, O, L.", sub="Yes. This is the perfect way to go on vacation. Everyone "
                                                "will think we were destroyed. LOL.", post=0.8),
    Beat(a_overhear, "vex", "Wait. You're... okay with this?", post=0.3),
    Beat(a_pack, "doubt", "We'll pack the important stuff. Leave the rest for the show.", post=0.3),
    Beat(a_look_good, "boredom", "Make it look good, buddy.", post=1.4),
    Beat(a_wreck, "narr", "That night, the villains tore the lab apart. Nobody noticed the sign.", pre=0.8,
         post=0.6),
    Beat(a_nothing_left, "goon", "Ha ha! We destroyed all their important stuff!", post=0.3),
    Beat(a_empty_victory, "vex", "Oh, yes. You guys totally destroyed everything.", rate="-6%", post=2.4),
    Beat(a_beach, "narr", "Meanwhile, Boredom and Doubt had already taken everything they wanted. And they "
                          "were relaxing in the Bahamas.", pre=0.8, post=0.6),
    Beat(a_check_news, "doubt", "Ooh. We made the news.", post=0.4),
    Beat(a_news, "anchor", "Breaking news. The lab of Boredom and Doubt has been destroyed. And tonight, the "
                           "villain council has named Lord Vex... the new Master Villain.", pre=0.4, post=0.8),
    Beat(a_news_out, min=1.2),
    Beat(a_toast, "boredom", "To the Master Villain.", post=0.3),
    Beat(a_clink, "doubt", "The only one we'd want. One who could love us.", post=1.4),
    Beat(a_love, "narr", "Because Boredom and Doubt wouldn't want any other villain on that throne. Only one "
                         "they knew could love them.", post=1.2),
    Beat(a_harder, "narr", "But being Master Villain was harder than it looked. His villains wanted chaos. "
                           "He wanted them safe from themselves.", pre=0.6, post=0.3),
    Beat(a_cant_say, "narr", "Chaos hurt them too. But a villain can't say that out loud.", post=0.8),
    Beat(a_office, "vex", "Why does everyone want to burn everything down? Do you know what burning "
                          "everything costs? The insurance alone!", pre=0.6, post=0.2, **HI),
    Beat(a_whine, "vex", "And now Gary wants to release the bees on the city. The bees, you guys! Do you know "
                         "how many villain permits that takes?", id="whine2", post=0.2, **HI),
    Beat(a_whine, "vex", "And Carl wants to flood the subway! I told him, if the subway's flooded, how are "
                         "people supposed to ride it to come and fear us? Where's the domination in that?",
         id="enter", post=0.2, **HI),
    Beat(a_whine, "vex", "And I can't just say, please don't hurt anybody. They'd take my crown! So instead I have to "
                         "say, it's bad for the evil budget. It breaks rule forty-seven of the "
                         "villain code.", id="rule", post=0.2, **HI),
    Beat(a_whine, "vex", "Rule forty-seven isn't even real! I made it up! I've made up thirty rules this week!",
         id="madeup", post=0.3, **HI),
    Beat(a_sir, "minion", "Uhh... sir?", pre=0.3, post=1.0),
    Beat(a_cough, "vex", "Ahem. Ahem. Yes, minion. What do you want?", rate="-8%", pitch="-8Hz", post=0.4),
    Beat(a_late, "minion", "Well, we're late for the evil plan today, sir.", post=0.4),
    Beat(a_right_there, "vex", "Oh. Yes, yes. I'll be right there.", rate="-6%", post=0.2),
    Beat(a_stare, min=2.6),
    Beat(a_go_now, "vex", "You can go now.", post=0.3),
    Beat(a_oh_yeah, "minion", "Oh. Yeah.", post=1.4),
    Beat(a_door_open, min=1.4),
    Beat(a_close_it, "vex", "Hey. Dude. Come on, minion. You forgot to close the door. Okay?", post=0.3),
    Beat(a_sigh, "minion", "Ugh. Fine.", pre=0.4, post=0.8),
    Beat(a_back_to_whine, "vex", "Okay. Where was I? The bees, guys! The bees!", pre=0.2, post=0.2, **HI),
    Beat(a_end, min=4.0),
]


def draw(ctx, S, t):
    def after(ctx, S, t):
        h = S["fx"].get("heart", 0)
        if h > 0:
            M.heart(ctx, 640, 330, 0.5 + 1.5 * h, h)
            for i in range(6):
                a = t * 2 + i * math.pi / 3
                E.sparkle(ctx, 640 + math.cos(a) * 90, 330 + math.sin(a) * 60, 8, "#FFE7F0", h)
    draw_world(ctx, S, t, extra_after=after)
    if S["fx"].get("news", 0) > 0:
        draw_news(ctx, S, t)
    overlays(ctx, S, t, "LAB PARTNERS", "Episode 3: Vacation", "To be continued...", "Episode 4: The Comedy Show")
