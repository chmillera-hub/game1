"""Part 2: Sorry, Bro."""
import math
import random

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, back_out, linear
from common import (sfx, music, active, hand, walk, set_, base_state, draw_stage, draw_fade,
                    apply_camera, RABBIT_SPOTS)
from show import Beat

TOTAL = 0.0
IDX = {}


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def T(b, off=0.0):
    return b.start + off


def VEND(b):
    return b.start + b.vs + b.vd


def cam(S, lt, t0, t1, x, y, z, fn=ease):
    S["cam"] = [tw(lt, t0, t1, S["cam"][0], x, fn), tw(lt, t0, t1, S["cam"][1], y, fn),
                tw(lt, t0, t1, S["cam"][2], z, fn)]


def init_state():
    S = base_state()
    S["anger"] = E.new_char("anger", 420, makeup=1.0, glitter=0.4, eyes="squeeze", mouth="o",
                            mamt=1.0)
    S["anger"]["hl"] = E.pose("anger", -1, "rest")
    S["doubt"] = E.new_char("doubt", 215, mode="floorlaugh")
    S["boredom"] = E.new_char("boredom", 960, mouth="flat", lid=0.55, face=-0.5, px=-0.8)
    S["rabbits"] = [dict(t0=-10, x=x, y=y) for x, y in RABBIT_SPOTS]
    S["turtle"] = "table"
    S["turtle_xy"] = (602, 505)
    S["scorch"] = 1.0
    S["cloud"] = dict(x=424, y=505, a=1.0, size=1.05)
    S["card"] = 1.0
    S["door"] = 0.0
    S["water"] = 0.0
    S["wash"] = 0.0
    S["kiss"] = 0.0
    S["heart"] = None
    S["bulbs"] = 1.0
    S["turtle_room"] = dict(blink=0.0, smile=0.0, blush=0.0)
    return S


# ------------------------------------------------------------------ acts: stage
def a_title(S, lt, b):
    music(S, T(b), "show", 0.9)
    sfx(S, T(b, 0.3), "sparkle", 0.7)


def a_recap(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1.0, 0.0)
    for k in range(int(b.d / 0.5)):
        sfx(S, T(b, 0.9 + k * 0.5), "thud", 0.2)


def a_settle(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    S["cloud"]["a"] = tw(lt, 0.3, 2.6, 1.0, 0.0)
    S["cloud"]["size"] = tw(lt, 0.3, 2.6, 1.05, 1.4)
    sfx(S, T(b, 0.3), "sparkle", 0.6)
    music(S, T(b), None, 0)
    # Doubt winds down and sits up
    if lt > 0.8:
        d["mode"] = None
        d["tilt"] = tw(lt, 0.8, 1.6, -math.pi / 2, 0.0)
        d["eyes"] = "open"
        d["mouth"], d["mamt"] = "smile", 0.6
        d["px"] = 1.0
        hand(d, -1, "rest", lt, 0.8, 1.4)
        hand(d, 1, "rest", lt, 0.8, 1.4)
    a["eyes"] = "squeeze" if lt < 2.2 else "shut"
    cam(S, lt, 1.8, b.d, 420, 490, 2.3)


def a_makeover(S, lt, b):
    a = S["anger"]
    a["eyes"] = "shut" if lt < 0.6 else "open"
    a["mouth"], a["mamt"] = "frown", 0.4
    a["glitter"] = tw(lt, 0, 1.0, 0.4, 0.15)
    a["brow"] = -0.4
    # brushing off the last of it
    hand(a, 1, "face", lt, 0.0, 0.3)
    if lt < 1.4:
        a["hr"] = (a["hr"][0] + math.sin(lt * 14) * 16, a["hr"][1] + 20)
    else:
        hand(a, 1, "rest", lt, 1.4, 1.8)
    S["cloud"] = None
    sfx(S, T(b, 0.7), "blink", 1.0)


def a_details(S, lt, b):
    a = S["anger"]
    x = a["x"]
    v0, vd = b.vs, b.vd
    spots = [(x + 2, 612 - 70, 0.08), (x + 44, 612 - 78, 0.38), (x + 30, 612 - 136, 0.72)]
    for k, (px, py, f) in enumerate(spots):
        tt = T(b, v0 + vd * f)
        S["bursts"].append(dict(kind="ding", x=px, y=py, t=tt))
        sfx(S, tt, "ding" if k < 2 else "bling", 0.6)
    tl = v0 + vd * 0.72
    if tl < lt < tl + 0.6:
        a["lid"] = 1.0 if int((lt - tl) * 12) % 2 == 0 else 0.0
    else:
        a["lid"] = 0.0


def a_all_gone(S, lt, b):
    a = S["anger"]
    cam(S, lt, 0.0, 0.7, 640, 360, 1.0)
    hand(a, -1, (-8, -60), lt, 0.1, 0.4)
    hand(a, 1, (8, -60), lt, 0.1, 0.4)
    if 0.4 < lt < 1.4:
        w = math.sin((lt - 0.4) * 22) * 10
        a["hl"] = (-8 - w, -60)
        a["hr"] = (8 + w, -60)
    if lt > 1.4:
        hand(a, -1, "rest", lt, 1.4, 1.8)
        hand(a, 1, "rest", lt, 1.4, 1.8)
    a["mouth"], a["mamt"] = "smirk", 0.6
    a["face"] = 0.1


def a_doubt_sees(S, lt, b):
    d = S["doubt"]
    d["px"] = 1.0
    d["wide"] = tw(lt, 0.0, 0.3, 0, 1.0)
    d["mouth"], d["mamt"] = "o", 1.0
    tl = b.vs + b.vd * 0.45
    if lt > tl:
        d["mode"] = "giggle"
        d["wide"] = 0
    for k in range(int((b.d - tl) / 0.22)):
        sfx(S, T(b, tl + k * 0.22), "stomp", 0.3)


def a_doubt_hee(S, lt, b):
    S["doubt"]["mode"] = "giggle"
    for k in range(int(b.d / 0.22)):
        sfx(S, T(b, k * 0.22), "stomp", 0.3)


def a_what(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    d["mode"] = "giggle" if lt < 1.0 else None
    if lt >= 1.0:
        d["eyes"] = "open"
        d["mouth"], d["mamt"] = "tight", 1.0
        d["cheeks"] = 1.0
        hand(d, -1, "mouth", lt, 1.0, 1.0)
        hand(d, 1, "mouth", lt, 1.0, 1.0)
    a["face"] = tw(lt, 0, 0.3, a["face"], -0.6)
    a["px"] = tw(lt, 0, 0.3, a["px"], -1.0)
    a["brow"] = -0.8
    hand(a, -1, "hip", lt, 0, 0.4)
    hand(a, 1, "hip", lt, 0, 0.4)


def a_turns(S, lt, b):
    a = S["anger"]
    o = S["boredom"]
    a["face"] = tw(lt, 0, 0.6, a["face"], 0.6)
    a["px"] = tw(lt, 0, 0.6, a["px"], 1.0)
    o["face"] = -0.5
    o["px"] = -1.0
    o["lid"] = tw(lt, 0.4, 1.0, o["lid"], 0.1)
    o["wide"] = tw(lt, 0.4, 1.0, 0, 0.4)


def a_nothing(S, lt, b):
    o = S["boredom"]
    o["mouth"], o["mamt"] = "tight", 1.0
    o["lid"] = 0.3
    o["wide"] = 0.0
    o["px"] = tw(lt, 0, 0.6, -1.0, 0.6)
    o["py"] = -0.5
    cam(S, lt, 0, b.d, 900, 470, 1.8)


def a_holdin(S, lt, b):
    o = S["boredom"]
    o["mode"] = "holdin"
    o["shake"] = 0.8 + 2.5 * lt / max(b.d, 0.1)
    o["cheeks"] = clamp(lt / 1.0)


def a_burst(S, lt, b):
    o = S["boredom"]
    o["mode"] = "laugh"
    o["shake"] = 0
    o["cheeks"] = 0
    S["rabbit_giggle"] = 1.0 if lt > 0.3 else 0.0
    sfx(S, T(b, 0.05), "splat", 0.5)
    cam(S, lt, 0.0, 0.6, 640, 360, 1.0)
    d = S["doubt"]
    if lt > 0.4:
        d["mode"] = "giggle"
        d["cheeks"] = 0
    music(S, T(b, 0.3), "show", 0.6)


def a_never(S, lt, b):
    S["turtle_smile"] = tw(lt, 0.5, 1.2, 0, 1)
    S["rabbit_giggle"] = 1.0


def a_stomp1(S, lt, b):
    a = S["anger"]
    a["mode"] = "stomp"
    path = [420, 560, 380, 520]
    seg = b.d / len(path)
    k = min(int(lt / seg), len(path) - 1)
    x0 = path[k - 1] if k > 0 else 420
    x1 = path[k]
    a["x"] = tw(lt - k * seg, 0, seg, x0, x1)
    a["face"] = 0.6 if x1 >= x0 else -0.6
    for i in range(int(b.d / 0.31)):
        sfx(S, T(b, i * 0.31), "stomp", 0.7)
    S["shake"] = 0.15 if active(lt, b) else 0.0


def a_stomp2(S, lt, b):
    a = S["anger"]
    a["mode"] = "stomp"
    path = [380, 540, 470, 545]
    seg = b.d / len(path)
    k = min(int(lt / seg), len(path) - 1)
    x0 = path[k - 1] if k > 0 else 520
    x1 = path[k]
    a["x"] = tw(lt - k * seg, 0, seg, x0, x1)
    a["face"] = 0.6 if x1 >= x0 else -0.6
    if lt > b.vs + b.vd * 0.6:
        a["px"], a["py"] = 1.0, -0.4
    for i in range(int(b.d / 0.31)):
        sfx(S, T(b, i * 0.31), "stomp", 0.7)
    S["shake"] = 0.15 if active(lt, b) else 0.0


def reflect_small(S, t):
    a = S["anger"]

    def fn(ctx):
        c = dict(a)
        c.update(x=0, y=62, s=0.55, yoff=0, tilt=0, mode=None, face=0.6, px=-1.0, py=0.0,
                 steam=0, hl=E.pose("anger", -1, "rest"), hr=E.pose("anger", 1, "rest"),
                 footL=(0, 0), footR=(0, 0), shake=0, walking=0, itemR=None, itemL=None)
        ctx.save()
        ctx.scale(-1, 1)
        E.draw_char(ctx, c, t)
        ctx.restore()
    return fn


def a_step_in(S, lt, b):
    a = S["anger"]
    a["mode"] = None
    S["shake"] = 0
    a["x"] = 545
    a["face"] = tw(lt, 0, 0.5, 0.6, 0.7)
    a["px"], a["py"] = tw(lt, 0.4, 1.0, 1.0, 0.6), 0.0
    hand(a, -1, "hip", lt, 0, 0.1)
    hand(a, 1, "hip", lt, 0, 0.1)
    a["brow"] = -0.6
    a["mouth"], a["mamt"] = "frown", 0.5
    x = tw(lt, 0.3, 1.4, 1450, 700, ease_out)
    S["mirror"] = dict(x=x, y=470, ang=-0.08, reflect=reflect_small(S, S["t"]))
    S["rabbit_giggle"] = 0.0
    music(S, T(b), None, 0)
    sfx(S, T(b, 0.3), "whoosh", 0.5)


def a_sorry(S, lt, b):
    S["mirror"]["reflect"] = reflect_small(S, S["t"])
    S["mirror"]["ang"] = -0.08 + math.sin(lt * 3) * 0.02
    o = S["boredom"]
    o["mode"] = None
    o["eyes"] = "open"
    o["mouth"], o["mamt"] = "smile", 0.4
    o["lid"] = 0.4
    d = S["doubt"]
    d["mode"] = None
    d["eyes"] = "open"
    d["mouth"], d["mamt"] = "tight", 1.0
    d["cheeks"] = 1.0
    hand(d, -1, "mouth", lt, 0, 0.01)
    hand(d, 1, "mouth", lt, 0, 0.01)


def a_looks(S, lt, b):
    a = S["anger"]
    S["mirror"]["reflect"] = reflect_small(S, S["t"])
    cam(S, lt, 0, 1.2, 615, 500, 2.6)
    hand(a, -1, "rest", lt, 0.2, 0.6)
    hand(a, 1, "rest", lt, 0.2, 0.6)
    a["brow"] = tw(lt, 0.4, 1.2, -0.6, 0.2)
    a["mouth"], a["mamt"] = "flat", 0
    a["blink"] = False
    for k, tb in enumerate((1.3, 1.75)):
        if tb < lt < tb + 0.14:
            a["lid"] = 1.0
        sfx(S, T(b, tb), "blink", 0.9)
    if lt > 1.9:
        a["lid"] = 0.0


def a_jaw(S, lt, b):
    a = S["anger"]
    S["mirror"]["reflect"] = reflect_small(S, S["t"])
    a["mouth"] = "jaw"
    a["mamt"] = tw(lt, 0.1, 0.9, 0.0, 1.0, back_out)
    a["wide"] = tw(lt, 0.1, 0.4, 0, 1.6)
    a["brow"] = tw(lt, 0.1, 0.4, 0.2, 1.4)
    sfx(S, T(b, 0.1), "slidedown", 1.0)
    cam(S, lt, 0.2, 1.2, 600, 540, 2.2)


def a_squeal(S, lt, b):
    a = S["anger"]
    a["mouth"], a["mamt"] = "jaw", 0.6
    a["wide"] = 1.4
    a["brow"] = 1.4
    a["blink"] = True
    S["mirror"]["reflect"] = reflect_small(S, S["t"])
    sfx(S, T(b, b.vs), "squeal", 0.8)
    cam(S, lt, 0.0, 0.5, 640, 360, 1.0)
    S["mirror"]["x"] = tw(lt, 0.3, 1.2, 700, 1500, E.ease_in)
    if lt > 0.25:
        a["mode"] = "run"
        a["face"] = -1.0
        a["x"] = tw(lt, 0.25, 1.6, 545, -220, linear)
        a["px"] = -1.0
    for k in range(4):
        S["bursts"].append(dict(kind="dust", x=545 - k * 180, y=612, t=T(b, 0.3 + k * 0.33)))
    sfx(S, T(b, 0.25), "whoosh", 0.7)


def a_runs_off(S, lt, b):
    a = S["anger"]
    a["visible"] = False
    S["mirror"] = None
    d, o = S["doubt"], S["boredom"]
    d["px"] = tw(lt, 0, 0.4, d["px"], -1.0)
    o["px"] = tw(lt, 0, 0.4, o["px"], -1.0)
    o["face"] = -0.7
    d["face"] = tw(lt, 0, 0.4, d["face"], -0.4)
    S["rabbit_look"] = -1
    # then they look at each other
    if lt > b.d * 0.55:
        d["px"] = tw(lt, b.d * 0.55, b.d * 0.6, -1.0, 1.0)
        o["px"] = tw(lt, b.d * 0.55, b.d * 0.6, -1.0, -1.0)
        d["face"] = 0.4
        d["mode"] = "giggle"
        o["mode"] = "laugh"
    music(S, T(b, 0.3), "show", 0.5)


# ------------------------------------------------------------------ acts: subconscious
def a_swirl(S, lt, b):
    S["swirl"] = tw(lt, 0, 1.1, 0, 1, ease) if lt < 1.3 else tw(lt, 1.3, 2.4, 1, 0, ease)
    if lt >= 1.2:
        S["scene"] = "subcon"
    sfx(S, T(b), "swirl", 0.8)
    music(S, T(b), None, 0)
    music(S, T(b, 1.2), "dream", 1.0)
    a = S["anger"]
    a.update(visible=True, x=-120, y=596, s=0.8, mode="run", face=1.0, px=1.0, layer=0,
             mouth="jaw", mamt=0.5, wide=1.0)


def a_subcon(S, lt, b):
    a = S["anger"]
    arrive = min(b.d - 1.0, 3.6)
    a["x"] = tw(lt, 0.0, arrive, -120, 1110, linear)
    a["y"] = 596 + math.sin(lt * 3) * 4
    S["door"] = tw(lt, arrive - 0.6, arrive - 0.2, 0, 1)
    if lt > arrive:
        a["alpha"] = tw(lt, arrive, arrive + 0.3, 1, 0)
        S["door"] = tw(lt, arrive + 0.3, arrive + 0.5, 1, 0)
    sfx(S, T(b, arrive + 0.5), "door", 0.9)
    sfx(S, T(b, 0.3), "squeal", 0.25)


# ------------------------------------------------------------------ acts: dressing room
def a_room(S, lt, b):
    S["fade"] = tw(lt, 0, 0.35, 1, 0) if lt < 0.4 else 0
    if lt >= 0:
        S["scene"] = "room"
    a = S["anger"]
    a.update(alpha=1.0, s=1.0, y=E.GROUND, mode="run", face=1.0, mouth="o", mamt=1.0, wide=0.5,
             brow=0.6)
    a["x"] = tw(lt, 0.0, 1.0, -120, 470, ease_out)
    if lt > 1.0:
        a["mode"] = None
        a["sq"] = 1 + 0.05 * math.sin(lt * 9)
        a["sweat"] = 1.0
        hand(a, -1, (-50, -40), lt, 1.0, 1.3)
        hand(a, 1, (50, -40), lt, 1.0, 1.3)
        a["tilt"] = tw(lt, 1.0, 1.3, 0, 0.12)
        a["px"] = -0.6
    music(S, T(b), "lounge", 0.8)
    sfx(S, T(b, 0.1), "door", 0.6)


def a_okay(S, lt, b):
    a = S["anger"]
    a["sq"] = 1 + 0.05 * math.sin(lt * 9)
    a["sweat"] = 1.0
    a["px"] = math.sin(lt * 3) * 0.9
    a["wide"] = 0.3
    a["brow"] = 0.6


def a_wash(S, lt, b):
    a = S["anger"]
    a["sq"] = 1.0
    a["sweat"] = 0.0
    a["tilt"] = tw(lt, 0, 0.4, a["tilt"], 0)
    walk(a, 600, lt, 0.2, 1.0)
    a["px"] = 1.0
    a["face"] = tw(lt, 0, 0.5, a["face"], 0.5)
    a["brow"] = -0.5
    a["wide"] = 0.0
    hand(a, -1, "rest", lt, 0, 0.4)
    hand(a, 1, (132, -136), lt, 1.2, 1.8)


def reflect_big(S, t):
    a = S["anger"]
    mx, my, mw, mh = E.MIRROR
    rx = mx + mw / 2 + 30 - (a["x"] - 600) * 0.4

    def fn(ctx):
        c = dict(a)
        c.update(x=rx, y=470, s=0.95)
        ctx.save()
        ctx.translate(rx, 0)
        ctx.scale(-1, 1)
        ctx.translate(-rx, 0)
        E.draw_char(ctx, c, t)
        ctx.restore()
    return fn


def a_pause(S, lt, b):
    a = S["anger"]
    tl = b.vs + b.vd * 0.45
    if lt > tl:
        hand(a, 1, "rest", lt, tl, tl + 0.6)
        a["face"] = tw(lt, tl, tl + 0.8, a["face"], 0.85)
        a["py"] = -0.2
    cam(S, lt, 0.5, b.d, 760, 380, 1.45)


def a_huh(S, lt, b):
    a = S["anger"]
    a["brow"] = tw(lt, 0, 0.4, a["brow"], 0.4)
    a["mouth"], a["mamt"] = "flat", 0
    a["x"] = tw(lt, 0, 0.8, a["x"], 618)
    a["tilt"] = tw(lt, 0, 0.8, 0, 0.1)


def a_admire(S, lt, b):
    a = S["anger"]
    a["face"] = 0.85 + math.sin(lt * 2.6) * 0.15
    a["tilt"] = 0.1 + math.sin(lt * 2.6) * 0.1
    a["mouth"], a["mamt"] = "smile", tw(lt, 0, 1.5, 0.2, 0.9)
    hand(a, 1, (40, -100), lt, 0.6, 1.2)
    a["brow"] = 0.5
    S["bursts"].append(dict(kind="ding", x=880, y=270, t=T(b, 1.2)))
    sfx(S, T(b, 1.2), "ding", 0.5)
    music(S, T(b), "lounge", 1.0)


def a_pretty(S, lt, b):
    a = S["anger"]
    a["mouth"], a["mamt"] = "smirk", 1.0
    a["brow"] = 0.7
    a["tilt"] = tw(lt, 0, 0.3, a["tilt"], 0.05)
    tl = b.vs + b.vd + 0.05
    if tl < lt < tl + 0.6:
        a["lid"] = 1.0 if int((lt - tl) * 12) % 2 == 0 else 0.0
    else:
        a["lid"] = 0.0
    sfx(S, T(b, tl), "bling", 0.8)
    hand(a, 1, "rest", lt, 0, 0.4)


def a_shoulder(S, lt, b):
    a = S["anger"]
    music(S, T(b), "sneaky", 0.9)
    a["mouth"], a["mamt"] = "flat", 0
    a["brow"] = -0.3
    a["tilt"] = 0
    a["lid"] = 0.35
    seq = [(0.3, -1.0, -1.0), (1.3, -1.0, -1.0), (1.7, 0.2, 1.0), (2.6, 0.2, 1.0), (3.0, -1.0, -1.0)]
    f, p = a["face"], a["px"]
    for (tk, ff, pp) in seq:
        if lt >= tk:
            f = tw(lt, tk, tk + 0.3, f, ff)
            p = tw(lt, tk, tk + 0.25, p, pp)
    a["face"], a["px"] = f, p
    cam(S, lt, 0, 0.8, 640, 360, 1.0)


def a_nobody(S, lt, b):
    a = S["anger"]
    a["face"] = tw(lt, 0, 0.4, a["face"], 0.85)
    a["px"] = tw(lt, 0, 0.4, a["px"], 1.0)
    a["lid"] = tw(lt, 0, 0.4, a["lid"], 0.0)
    a["mouth"], a["mamt"] = "smirk", 0.8


def a_final(S, lt, b):
    a = S["anger"]
    music(S, T(b), "lounge", 1.0)
    cam(S, lt, 0, 1.0, 760, 380, 1.45)
    hand(a, -1, "hip", lt, 0.2, 0.7)
    hand(a, 1, (30, -175), lt, 0.2, 0.7)
    a["tilt"] = tw(lt, 0.2, 0.7, 0, 0.12)
    a["mouth"], a["mamt"] = "smile", 0.9
    a["brow"] = 0.6
    sfx(S, T(b, 0.5), "sparkle", 0.4)


def a_mwah(S, lt, b):
    a = S["anger"]
    hand(a, 1, "mouth", lt, 0, 0.25)
    a["mouth"] = "kiss" if lt < b.vs + b.vd + 0.2 else "smile"
    if lt > b.vs + b.vd:
        hand(a, 1, (150, -110), lt, b.vs + b.vd, b.vs + b.vd + 0.3, back_out)
    t0 = T(b, b.vs + b.vd)
    S["heart"] = dict(t0=t0, t1=t0 + 1.0, x0=a["x"] + 50, y0=540, x1=860, y1=275)
    sfx(S, t0, "heart", 0.8)
    if lt > b.vs + b.vd + 1.0:
        S["kiss"] = 1.0
    sfx(S, t0 + 1.0, "ding", 0.5)


def a_washoff(S, lt, b):
    a = S["anger"]
    music(S, T(b), "lounge", 0.6)
    cam(S, lt, 0, 0.8, 690, 450, 1.7)
    hand(a, -1, "rest", lt, 0, 0.3)
    hand(a, 1, (132, -136), lt, 0, 0.4)
    if lt > 0.5:
        S["water"] = 1.0
    sfx(S, T(b, 0.5), "water", 0.8)
    a["mouth"], a["mamt"] = "flat", 0
    a["tilt"] = 0
    if lt > 0.9:
        a["x"] = tw(lt, 0.9, 1.3, a["x"], 625)
        a["tilt"] = tw(lt, 0.9, 1.3, 0, 0.32)
        a["eyes"] = "shut"
        scrub = math.sin(lt * 16) * 14
        a["hl"] = (-6 + scrub, -112)
        a["hr"] = (18 - scrub, -92)
        S["wash"] = 1.0 if active(lt, b) else 0.0
        a["makeup"] = tw(lt, 1.2, b.d - 0.2, 1.0, 0.0)
        a["glitter"] = tw(lt, 1.2, b.d - 0.2, 0.15, 0.0)
    for k in range(int((b.d - 1.0) / 0.45)):
        sfx(S, T(b, 1.0 + k * 0.45), "splash", 0.4)


def a_never_happened(S, lt, b):
    a = S["anger"]
    a["makeup"] = 0
    a["glitter"] = 0
    S["wash"] = 0
    cam(S, lt, 0, 0.6, 640, 360, 1.0)
    S["water"] = 0 if lt > 0.3 else 1
    a["tilt"] = tw(lt, 0, 0.4, 0.32, 0)
    a["eyes"] = "open"
    a["x"] = tw(lt, 0, 0.4, 625, 600)
    hand(a, -1, "cross", lt, 0.2, 0.6)
    hand(a, 1, (-10, -48), lt, 0.2, 0.6)
    a["face"] = tw(lt, 0, 0.4, a["face"], 0.0)
    a["px"] = 0
    a["brow"] = -0.8
    a["mouth"], a["mamt"] = ("frown", 0.6) if lt > b.vs else ("flat", 0)
    tl = b.vs + b.vd + 0.2
    if lt > tl:
        hand(a, -1, "rest", lt, tl, tl + 0.3)
        hand(a, 1, "rest", lt, tl, tl + 0.3)
        a["face"] = -0.7
        walk(a, -160, lt, tl, tl + 2.2)
    music(S, T(b), None, 0)


def a_almost(S, lt, b):
    a = S["anger"]
    a["visible"] = a["x"] > -150
    tr = S["turtle_room"]
    cam(S, lt, 0.4, 2.4, 1110, 455, 3.0)
    tl = b.vs + b.vd * 0.55
    if lt > tl:
        tr["blink"] = math.sin(clamp((lt - tl) / 1.2) * math.pi)
    if lt > tl + 1.3:
        tr["smile"] = tw(lt, tl + 1.3, tl + 1.8, 0, 1)
        tr["blush"] = tw(lt, tl + 1.3, tl + 1.8, 0, 0.9)
    sfx(S, T(b, tl + 0.6), "blink", 1.0)
    sfx(S, T(b, tl + 1.5), "tink", 0.6)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)
    music(S, T(b, 0.1), "show", 0.9)
    sfx(S, T(b, 0.3), "tada", 0.6)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Previously, inside my head.", pre=1.4, post=0.8, min=4.0),
    Beat(a_recap, "narr", "One turtle. A lot of rabbits. And one magic missile full of glitter, "
                          "right in Anger's face.", pre=0.6, post=0.8),
    Beat(a_settle, "narr", "Now, the glitter settles.", post=2.4, min=4.6),
    Beat(a_makeover, "narr", "Anger thinks he got hit with glitter. He did not. He got a full makeover.",
         post=0.6),
    Beat(a_details, "narr", "Red lipstick. Powder on his cheeks. And eyelashes done to perfection.",
         post=1.0),
    Beat(a_all_gone, "anger", "Hmph. There. All gone.", post=0.6, min=2.2),
    Beat(a_doubt_sees, "narr", "The second Doubt sees him, she covers her mouth and starts giggling, "
                               "stomping her feet.", post=0.4),
    Beat(a_doubt_hee, "doubt", "Hee hee hee! Oh no. Oh no no no. Hee hee!", post=0.4),
    Beat(a_what, "anger", "What? What are you laughing at?", post=0.6),
    Beat(a_turns, "narr", "He turns to Boredom.", post=0.6),
    Beat(a_nothing, "boredom", "Nothing. Nothing at all.", post=0.6),
    Beat(a_holdin, "narr", "Boredom tries to hold it in. He holds it in. He holds it in...", post=0.3),
    Beat(a_burst, "boredom", "Pfft! Ha! Ha ha ha ha!", pre=0.0, post=0.6, rate="+0%"),
    Beat(a_never, "narr", "Even Boredom is laughing. And Boredom never laughs.", post=0.6),
    Beat(a_stomp1, "anger", "What?! What is so funny?", post=0.5),
    Beat(a_stomp2, "anger", "Somebody tell me what's going on! Is it the hat? It's the hat, isn't it?",
         post=0.4),
    Beat(a_step_in, "narr", "That's when I step in.", post=0.8, min=2.4),
    Beat(a_sorry, "me", "Sorry, bro.", rate="-8%", post=0.9),
    Beat(a_looks, min=2.4),
    Beat(a_jaw, min=2.0),
    Beat(a_squeal, "anger", "Eeeeeeeeeeeeeee!", tts="Eeeeeeeeeeeeeee!", pitch="+40Hz", post=0.4,
         min=2.2, gain=0.8),
    Beat(a_runs_off, "narr", "And Anger runs off into the subconscious, squealing at a pitch only pigs "
                             "can reach, wearing bright red lipstick.", post=1.0),
    Beat(a_swirl, min=2.4),
    Beat(a_subcon, "narr", "Deep in the subconscious, there is a quiet place where emotions go to "
                           "get ready.", post=0.6, min=5.0),
    Beat(a_room, "narr", "The emotional dressing room.", pre=1.2, post=0.6, min=3.4),
    Beat(a_okay, "anger", "Okay. Okay. Nobody saw. Nobody saw anything.", rate="+10%", post=0.5),
    Beat(a_wash, "anger", "Wash it off. Wash it off right now.", post=0.6, min=2.4),
    Beat(a_pause, "narr", "But before he turns on the water, he takes one look in the mirror.",
         post=0.8),
    Beat(a_huh, "anger", "Huh.", rate="-15%", post=0.6, min=1.6),
    Beat(a_admire, min=2.6),
    Beat(a_pretty, "anger", "Damn. I look pretty good.", rate="-8%", post=1.0),
    Beat(a_shoulder, "narr", "He looks over his shoulder to make sure nobody is watching.", post=1.2,
         min=3.6),
    Beat(a_nobody, "anger", "Nobody.", rate="-10%", gain=0.75, post=0.6),
    Beat(a_final, "narr", "One final look.", post=1.0, min=2.4),
    Beat(a_mwah, "anger", "Mwah!", post=1.6),
    Beat(a_washoff, "narr", "Then he washes it all off.", post=2.6, min=4.4),
    Beat(a_never_happened, "anger", "Hmph. That never happened.", post=2.4),
    Beat(a_almost, "narr", "Nobody saw a thing. Well... almost nobody.", pre=0.8, post=2.8),
    Beat(a_end, "narr", "The End.", pre=1.0, post=2.6, min=5.0),
]


# ------------------------------------------------------------------ render
def draw_heart(ctx, x, y, s, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(0, 8)
    ctx.curve_to(-22, -6, -12, -24, 0, -12)
    ctx.curve_to(12, -24, 22, -6, 0, 8)
    E.src(ctx, "#FF3D7F", a)
    ctx.fill()
    ctx.restore()


def draw_room(ctx, S, t):
    ctx.save()
    apply_camera(ctx, S, t)
    ctx.set_source_surface(E.dressing_bg(), 0, 0)
    ctx.paint()
    a = S["anger"]
    E.draw_mirror_glass(ctx, t, reflect_big(S, t) if a["visible"] else None, S["kiss"])
    E.draw_bulbs(ctx, t, S["bulbs"])
    E.draw_sink(ctx, t, S["water"])
    tr = S["turtle_room"]
    E.draw_turtle(ctx, 1110, 492, 0.6, -1, t, blink_slow=tr["blink"], smile=tr["smile"],
                  blush=tr["blush"])
    E.draw_char(ctx, a, t)
    if S["wash"] > 0:
        rnd = random.Random(int(t * 12))
        fx, fy = a["x"] + 40, 500
        for i in range(10):
            px = fx + rnd.uniform(-50, 50)
            py = fy + rnd.uniform(-40, 30)
            E.ellipse(ctx, px, py, rnd.uniform(4, 10), rnd.uniform(4, 10))
            E.src(ctx, "#FFFFFF", 0.85)
            ctx.fill_preserve()
            E.src(ctx, "#9AD7F5", 0.9)
            ctx.set_line_width(1.5)
            ctx.stroke()
        for i in range(12):
            ang = rnd.uniform(-2.8, -0.3)
            r = rnd.uniform(30, 90)
            E.ellipse(ctx, E.SINK_X + math.cos(ang) * r, 470 + math.sin(ang) * r * 0.8, 3, 4)
            E.src(ctx, "#7FD3FF", 0.8)
            ctx.fill()
    h = S["heart"]
    if h and h["t0"] <= t <= h["t1"]:
        u = (t - h["t0"]) / (h["t1"] - h["t0"])
        x = lerp(h["x0"], h["x1"], u)
        y = lerp(h["y0"], h["y1"], u) - math.sin(u * math.pi) * 60
        draw_heart(ctx, x, y, 1.0 + 0.3 * math.sin(t * 20), 1.0)
    for e in S["bursts"]:
        E.draw_burst(ctx, e, t)
    ctx.restore()


def draw_subcon(ctx, S, t):
    E.draw_subconscious(ctx, t, S["door"])
    E.draw_char(ctx, S["anger"], t)


def draw(ctx, S, t):
    sc = S["scene"]
    if sc == "stage":
        chars = [S["doubt"], S["boredom"], S["anger"]]
        draw_stage(ctx, S, t, chars)
    elif sc == "subcon":
        draw_subcon(ctx, S, t)
    else:
        draw_room(ctx, S, t)
    E.draw_swirl(ctx, t, S["swirl"])
    if S["card"] > 0:
        E.draw_title_card(ctx, t, "The Magic Show", "Inside My Head", "PART 2: SORRY, BRO", S["card"])
    if S["endcard"] > 0:
        E.draw_end_card(ctx, t, "The End", "The Magic Show Inside My Head", S["endcard"])
        S["subs"] = False
    draw_fade(ctx, S["fade"])
