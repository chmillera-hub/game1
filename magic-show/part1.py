"""Part 1: Abracadabra."""
import math

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, back_out, linear
from common import (sfx, music, active, hand, walk, set_, base_state, draw_stage, draw_fade,
                    RABBIT_SPOTS)
from show import Beat

TOTAL = 0.0
IDX = {}


def B(i):
    return IDX[i]


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
    S["anger"] = E.new_char("anger", 470, itemR="wand", mouth="frown", brow=-0.3)
    S["doubt"] = E.new_char("doubt", 250, mouth="smile", mamt=0.3)
    S["boredom"] = E.new_char("boredom", 1010, mouth="flat", itemL="wand", wandL=200)
    S["curtain"] = 0.0
    S["card"] = 1.0
    S["cones"] = 1.0
    return S


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    music(S, T(b), "show", 0.9)
    sfx(S, T(b, 0.3), "sparkle", 0.7)


def a_open(S, lt, b):
    S["card"] = tw(lt, 0.0, 0.8, 1.0, 0.0)
    S["curtain"] = tw(lt, 0.6, 3.4, 0.0, 1.0)
    sfx(S, T(b, 0.6), "curtain", 0.8)


def a_intro_anger(S, lt, b):
    a = S["anger"]
    S["dim"] = tw(lt, 0, 0.5, S["dim"], 0.65)
    S["spot_x"] = tw(lt, 0, 0.5, S["spot_x"], a["x"])
    if VEND(b) - b.start - 0.1 < lt < VEND(b) - b.start + 1.2:
        u = (lt - (VEND(b) - b.start - 0.1)) / 1.3
        a["tilt"] = math.sin(u * math.pi) * 0.35
    sfx(S, VEND(b) - 0.05, "tada", 0.8)
    sfx(S, VEND(b), "applause", 0.5)


def a_anger_hmph(S, lt, b):
    a = S["anger"]
    hand(a, -1, "cross", lt, 0, 0.4)
    hand(a, 1, (-10, -48), lt, 0, 0.4)
    a["brow"] = tw(lt, 0, 0.3, a["brow"], -0.8)
    a["face"] = tw(lt, 0, 0.4, a["face"], 0.15)


def a_intro_doubt(S, lt, b):
    d = S["doubt"]
    S["spot_x"] = tw(lt, 0, 0.6, S["spot_x"], d["x"])
    if VEND(b) - b.start - 0.2 < lt:
        hand(d, 1, "wave", lt, VEND(b) - b.start - 0.2, VEND(b) - b.start + 0.2)
    d["mouth"], d["mamt"] = "smile", 0.8
    sfx(S, VEND(b) - 0.05, "tada", 0.6)
    sfx(S, VEND(b), "applause", 0.4)


def a_doubt_unsure(S, lt, b):
    d = S["doubt"]
    hand(d, 1, "cheek", lt, 0, 0.5)
    hand(d, -1, "belly", lt, 0, 0.5)
    d["brow"] = tw(lt, 0, 0.4, d["brow"], 0.6)
    d["px"] = math.sin(lt * 2.5) * 0.7 if active(lt, b) else 0.0
    d["sweat"] = 1.0 if active(lt, b) else 0.0
    d["mouth"], d["mamt"] = "wavy", 1.0


def a_intro_boredom(S, lt, b):
    o = S["boredom"]
    d = S["doubt"]
    hand(d, 1, "rest", lt, 0, 0.5)
    d["mouth"], d["mamt"] = "smile", 0.4
    S["spot_x"] = tw(lt, 0, 0.6, S["spot_x"], o["x"])
    sfx(S, VEND(b) - 0.05, "tink", 0.4)


def a_boredom_yay(S, lt, b):
    o = S["boredom"]
    # a limp little wave
    hand(o, 1, (o["hr"][0] + 8, -150), lt, 0.1, 0.6)
    o["lid"] = 0.62
    o["mouth"] = "flat"
    if lt > b.d - 0.6:
        hand(o, 1, "rest", lt, b.d - 0.6, b.d)


def a_anger_goes(S, lt, b):
    a = S["anger"]
    o = S["boredom"]
    o["lid"] = 0.48
    S["dim"] = tw(lt, 0, 0.6, S["dim"], 0.0)
    hand(a, -1, "rest", lt, 0, 0.4)
    walk(a, 548, lt, 0.3, 1.8)
    a["face"] = tw(lt, 0.2, 0.6, a["face"], 0.5)
    # tap tap on the hat
    t_tap = max(1.9, b.vd * 0.75)
    hand(a, 1, (110, -136), lt, 1.8, 2.2)
    a["wandR"] = tw(lt, 1.8, 2.2, a["wandR"], 25)
    for k in range(2):
        tk = t_tap + k * 0.35
        if tk <= lt < tk + 0.3:
            a["hr"] = (a["hr"][0], a["hr"][1] - 10 * math.sin((lt - tk) / 0.3 * math.pi))
        sfx(S, T(b, tk + 0.15), "tink", 0.7)
    a["brow"] = tw(lt, 0, 0.4, a["brow"], -0.4)


def a_behold(S, lt, b):
    a = S["anger"]
    hand(a, 1, "up", lt, 0, 0.5, back_out)
    a["wandR"] = tw(lt, 0, 0.5, a["wandR"], -75)
    hand(a, -1, "out", lt, 0.2, 0.7)
    a["glow"] = tw(lt, 0.3, 0.8, 0, 1)
    a["brow"] = tw(lt, 0, 0.3, a["brow"], 0.2)
    a["mouth"], a["mamt"] = "smile", 0.6
    a["face"] = tw(lt, 0, 0.5, a["face"], 0.0)
    S["cam"][2] = tw(lt, 0, b.d, 1.0, 1.12)
    S["cam"][0] = tw(lt, 0, b.d, 640, 600)
    S["cam"][1] = tw(lt, 0, b.d, 360, 400)
    sfx(S, T(b, 0.3), "sparkle", 0.5)


def a_drumroll(S, lt, b):
    a = S["anger"]
    S["dim"] = tw(lt, 0, 0.5, S["dim"], 0.7)
    S["spot_x"] = tw(lt, 0, 0.5, S["spot_x"], 600)
    hand(a, 1, (112, -150), lt, 0, 0.5)
    a["wandR"] = tw(lt, 0, 0.5, a["wandR"], 40)
    hand(a, -1, (-40 + math.sin(lt * 20) * 6, -150), lt, 0, 0.4)
    a["glow"] = 0.6 + 0.4 * math.sin(lt * 12)
    a["mouth"], a["mamt"] = "smirk", 0.6
    S["hat_wobble"] = 1.5 if active(lt, b) else 0
    music(S, T(b), None, 0)
    sfx(S, T(b, 0.1), "drumroll", 0.9)
    S["cam"][2] = tw(lt, 0, b.d, S["cam"][2], 1.3)


def a_abra(S, lt, b):
    a = S["anger"]
    a["glow"] = tw(lt, 0, 0.3, 1.0, 0.0) if lt > 0.6 else 1.0
    hand(a, 1, (106, -128), lt, 0.6, 1.0)
    a["wandR"] = tw(lt, 0, 0.6, a["wandR"], -90)
    hand(a, -1, "rest", lt, 0.0, 0.4)
    S["bursts"].append(dict(kind="pop", x=E.HAT_X, y=E.HAT_TOP - 10, t=T(b, 0.5)))
    sfx(S, T(b, 0.45), "sparkle", 0.6)


def a_reach(S, lt, b):
    a = S["anger"]
    S["hat_wobble"] = 0
    # arm dives into the hat and rummages
    a["itemR"] = "wand" if lt < 0.4 else None
    a["itemL"] = "wand" if lt >= 0.4 else None
    a["wandL"] = 230
    hand(a, -1, "rest", lt, 0.1, 0.4)
    hand(a, 1, (110, -96), lt, 0.4, 1.0)
    if 1.0 < lt < b.d - 0.4:
        a["hr"] = (110 + math.sin(lt * 9) * 6, -96 + math.sin(lt * 13) * 8)
        a["tilt"] = 0.12 + math.sin(lt * 9) * 0.04
        a["mouth"], a["mamt"] = "tight", 1.0
        S["hat_wobble"] = 2.2
    else:
        a["tilt"] = tw(lt, b.d - 0.4, b.d, a["tilt"], 0.0)
    a["px"], a["py"] = 0.6, 0.6
    S["cam"][2] = tw(lt, 0, b.d, S["cam"][2], 1.45)
    S["cam"][0] = tw(lt, 0, b.d, S["cam"][0], 620)
    S["cam"][1] = tw(lt, 0, b.d, S["cam"][1], 430)
    # yank!
    hand(a, 1, "up", lt, b.d - 0.35, b.d, back_out)
    if lt > b.d - 0.25:
        a["itemR"] = "turtle"
        a["hr"] = (22, -182)
    sfx(S, T(b, b.d - 0.3), "pop", 1.0)
    sfx(S, T(b, b.d - 0.3), "whoosh", 0.5)


def a_turtle_reveal(S, lt, b):
    a = S["anger"]
    a["itemR"] = "turtle"
    a["hr"] = (22, -182)
    a["mouth"], a["mamt"] = "smile", 0.9
    a["px"], a["py"] = 0.5, -0.9
    a["brow"] = 0.4
    S["dim"] = tw(lt, 0.3, 0.8, S["dim"], 0.0)
    if lt > 0.7:
        a["mouth"], a["mamt"] = "flat", 0.0
        a["wide"] = 0.6
    sfx(S, T(b, 0.6), "trombone", 0.9)
    S["cam"][2] = tw(lt, 0, 0.6, S["cam"][2], 1.6)
    S["cam"][1] = tw(lt, 0, 0.6, S["cam"][1], 380)


def a_a_turtle(S, lt, b):
    a = S["anger"]
    a["wide"] = 0.9
    a["brow"] = 0.8
    a["shake"] = 1.5 if active(lt, b) else 0.0


def a_doubt_laughs(S, lt, b):
    a = S["anger"]
    a["shake"] = 0
    a["wide"] = tw(lt, 0, 0.5, a["wide"], 0.0)
    a["brow"] = tw(lt, 0, 0.5, a["brow"], -0.6)
    a["mouth"], a["mamt"] = "frown", 0.8
    a["px"], a["py"] = -0.3, 0.0
    S["cam"] = [tw(lt, 0, 0.6, S["cam"][0], 640), tw(lt, 0, 0.6, S["cam"][1], 360),
                tw(lt, 0, 0.6, S["cam"][2], 1.0)]
    d = S["doubt"]
    d["mode"] = "laugh" if lt < b.d else "laugh"
    d["talk"] = 0
    music(S, T(b, 0.5), "show", 0.7)


def a_side_eye(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    a["face"] = tw(lt, 0.2, 1.4, 0.0, -0.45)
    a["px"] = tw(lt, 0.2, 1.4, a["px"], -1.0)
    a["py"] = 0.0
    a["lid"] = tw(lt, 0.2, 1.4, 0.0, 0.42)
    a["brow"] = tw(lt, 0.2, 1.4, a["brow"], -1.0)
    a["mouth"], a["mamt"] = "flat", 0
    a["blink"] = False
    if lt > 1.6:
        d["mode"] = None
        d["px"] = 1.0
        d["eyes"] = "open"
        d["mouth"], d["mamt"] = "wavy", 1
        d["sweat"] = 1.0
        d["brow"] = 0.6
    if 1.6 < lt < 2.0:
        d["yoff"] = -8 * math.sin((lt - 1.6) / 0.4 * math.pi)
    S["cam"] = [tw(lt, 0, b.d, 640, 420), tw(lt, 0, b.d, 360, 430), tw(lt, 0, b.d, 1.0, 1.5)]
    music(S, T(b), None, 0)
    sfx(S, T(b, 1.0), "slideupdown", 0.3)


def a_keep_laughing(S, lt, b):
    a = S["anger"]
    a["mouth"], a["mamt"] = "frown", 0.4
    a["blink"] = True
    # set the turtle down on the table
    hand(a, 1, (70, -112), lt, 0.6, 1.3)
    if lt > 1.3:
        a["itemR"] = None
        S["turtle"] = "table"
        S["turtle_xy"] = (602, 505)
        hand(a, 1, "rest", lt, 1.3, 1.7)
        hand(a, -1, "rest", lt, 1.3, 1.7)
        a["itemL"] = "wand"
        a["wandL"] = 200
    S["cam"] = [tw(lt, b.d - 0.6, b.d, S["cam"][0], 640), tw(lt, b.d - 0.6, b.d, S["cam"][1], 360),
                tw(lt, b.d - 0.6, b.d, S["cam"][2], 1.0)]


def a_move_over(S, lt, b):
    a = S["anger"]
    o = S["boredom"]
    d = S["doubt"]
    d["sweat"] = 0
    d["px"] = tw(lt, 0, 0.5, 1.0, 0.6)
    d["mouth"], d["mamt"] = "smile", 0.3
    a["lid"] = tw(lt, 0, 0.4, a["lid"], 0.0)
    a["px"] = tw(lt, 0.4, 0.8, a["px"], 0.8)
    a["face"] = tw(lt, 0.4, 0.8, a["face"], 0.4)
    music(S, T(b), "show", 0.7)
    o["face"] = -0.5
    walk(o, 772, lt, 0.4, max(1.8, b.vd))
    walk(a, 420, lt, 1.0, 2.0)
    a["layer"] = 0


def a_rabbit1(S, lt, b):
    o = S["boredom"]
    a = S["anger"]
    a["face"] = 0.4
    a["px"] = 0.8
    o["itemL"] = None
    o["itemR"] = "wand"
    o["wandR"] = -40
    hand(o, -1, (-104, -110), lt, 0.0, 0.6)
    tp = b.vs + b.vd - 0.2
    if lt > tp - 0.3:
        hand(o, -1, (-110, -170), lt, tp - 0.3, tp)
    S["rabbits"].append(dict(t0=T(b, tp), x=RABBIT_SPOTS[0][0], y=RABBIT_SPOTS[0][1]))
    sfx(S, T(b, tp + 0.1), "pop", 0.9)


def _pop_series(S, lt, b, idx, times):
    o = S["boredom"]
    for k, (i, tp) in enumerate(zip(idx, times)):
        S["rabbits"].append(dict(t0=T(b, tp), x=RABBIT_SPOTS[i][0], y=RABBIT_SPOTS[i][1]))
        sfx(S, T(b, tp + 0.1), "pop", 0.8)
        if tp - 0.25 <= lt < tp + 0.25:
            u = (lt - tp + 0.25) / 0.5
            o["hl"] = (-106, lerp(-104, -170, math.sin(u * math.pi)))


def a_rabbits_more(S, lt, b):
    o = S["boredom"]
    hand(o, -1, (-106, -104), lt, 0, 0.3)
    n = 5
    times = [b.vs + b.vd * (0.25 + 0.75 * k / n) for k in range(n)]
    _pop_series(S, lt, b, range(1, 6), times)


def a_rabbits_words(S, lt, b):
    o = S["boredom"]
    o["lid"] = 0.62
    n = 5
    times = [b.vs + b.vd * (k + 0.3) / n for k in range(n)]
    _pop_series(S, lt, b, range(6, 11), times)


def a_how_many(S, lt, b):
    d = S["doubt"]
    d["wide"] = tw(lt, 0, 0.3, 0, 0.8)
    d["brow"] = 0.9
    hand(d, -1, "cheek", lt, 0, 0.4)
    hand(d, 1, "cheek", lt, 0, 0.4)
    d["px"] = 0.8
    d["mouth"], d["mamt"] = "o", 0.8
    times = [0.4, 1.0, 1.6]
    _pop_series(S, lt, b, range(11, 14), times)


def a_all_of_them(S, lt, b):
    d = S["doubt"]
    d["wide"] = tw(lt, 0, 0.5, d["wide"], 0.3)
    _pop_series(S, lt, b, [14], [b.vs + b.vd + 0.2])
    o = S["boredom"]
    o["px"] = -0.6
    o["face"] = tw(lt, 0, 0.4, o["face"], 0.3)


def a_eyeroll(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    hand(d, -1, "rest", lt, 0, 0.5)
    hand(d, 1, "rest", lt, 0, 0.5)
    d["mouth"], d["mamt"] = "smile", 0.6
    o = S["boredom"]
    hand(o, -1, "rest", lt, 0, 0.5)
    S["cam"] = [tw(lt, 0, 0.6, S["cam"][0], 420), tw(lt, 0, 0.6, S["cam"][1], 420),
                tw(lt, 0, 0.6, S["cam"][2], 1.7)]
    t0, t1 = 0.5, max(2.6, b.d - 0.3)
    if t0 <= lt <= t1:
        u = (lt - t0) / (t1 - t0)
        ang = -math.pi * 0.0 - u * 2 * math.pi * 1.25
        a["px"], a["py"] = math.cos(ang), math.sin(ang)
        a["face"] = 0.3 * math.cos(ang)
        a["tilt"] = math.sin(u * math.pi) * -0.12
    elif lt > t1:
        a["px"], a["py"] = 0.0, -1.0
        a["tilt"] = 0
    a["mouth"], a["mamt"] = "frown", 0.6
    sfx(S, T(b, 0.5), "slideupdown", 0.4)


def a_show_off(S, lt, b):
    a = S["anger"]
    a["py"] = tw(lt, 0, 0.3, a["py"], 0.0)
    a["px"] = tw(lt, 0, 0.3, a["px"], 0.8)
    a["face"] = tw(lt, 0, 0.3, a["face"], 0.4)
    a["brow"] = -0.8
    S["cam"] = [tw(lt, b.d - 0.4, b.d, S["cam"][0], 640), tw(lt, b.d - 0.4, b.d, S["cam"][1], 360),
                tw(lt, b.d - 0.4, b.d, S["cam"][2], 1.0)]


def a_points(S, lt, b):
    a = S["anger"]
    o = S["boredom"]
    a["itemL"] = None
    a["itemR"] = "wand"
    hand(a, -1, "rest", lt, 0, 0.3)
    hand(a, 1, "out", lt, 0.4, 0.9, back_out)
    a["wandR"] = tw(lt, 0.4, 0.9, a["wandR"], -8)
    a["face"] = tw(lt, 0.2, 0.6, a["face"], 0.8)
    a["brow"] = -1.0
    a["glow"] = tw(lt, 0.8, 1.4, 0, 0.8)
    o["px"] = -1.0
    o["face"] = tw(lt, 0, 0.5, o["face"], -0.5)
    o["lid"] = tw(lt, 0.8, 1.2, 0.48, 0.0)
    o["wide"] = tw(lt, 0.8, 1.2, 0, 0.7)
    S["dim"] = tw(lt, 0, 0.6, S["dim"], 0.35)
    S["spot_x"] = 640
    S["spot_r"] = 420
    music(S, T(b), None, 0)


def a_magic_missile(S, lt, b):
    a = S["anger"]
    o = S["boredom"]
    a["glow"] = 1.0 if lt < b.vs + b.vd else 0.2
    launch = VEND(b) - 0.05
    lt_l = launch - b.start
    S["missiles"].append(dict(t0=launch, t1=launch + 1.0, x0=a["x"] + 200, y0=515,
                              x1=1196, y1=470, arc=50, col="#FF5A2C"))
    sfx(S, launch, "zap", 1.0)
    # Boredom dives flat just in time
    o["mouth"], o["mamt"] = "o", 1.0
    if lt > lt_l + 0.1:
        u = (lt - lt_l - 0.1) / 0.35
        o["tilt"] = lerp(0, math.pi / 2, ease_out(u))
        o["x"] = tw(lt, lt_l + 0.1, lt_l + 0.45, 772, 900)
        o["yoff"] = -math.sin(clamp(u) * math.pi) * 40
    S["shake"] = 0.4 if lt_l < lt < lt_l + 0.3 else 0


def a_barely(S, lt, b):
    o = S["boredom"]
    a = S["anger"]
    hit = B("mm1").start + B("mm1").vs + B("mm1").vd - 0.05 + 1.0
    S["bursts"].append(dict(kind="fire", x=1196, y=470, t=hit, seed=3))
    sfx(S, hit, "boom", 1.0)
    lh = hit - b.start
    if lt > lh:
        S["scorch"] = 1.0
    S["shake"] = clamp(1 - (lt - lh) / 0.6) * 1.2 if lt > lh else 0.0
    o["tilt"] = math.pi / 2
    o["eyes"] = "open"
    o["lid"] = 0.0
    o["wide"] = 1.0
    o["px"] = 1.0
    a["glow"] = 0
    a["mouth"], a["mamt"] = "smirk", 0.8
    S["dim"] = tw(lt, 0, 0.5, S["dim"], 0.0)
    S["spot_r"] = 230


def a_rude(S, lt, b):
    o = S["boredom"]
    o["tilt"] = tw(lt, 0.0, 0.7, math.pi / 2, 0.0)
    o["x"] = tw(lt, 0.0, 0.7, 900, 960)
    o["wide"] = tw(lt, 0.6, 1.2, 1.0, 0.0)
    o["lid"] = tw(lt, 0.6, 1.2, 0.0, 0.55)
    o["px"] = tw(lt, 0.6, 1.2, 1.0, -0.8)
    o["face"] = -0.5
    o["mouth"], o["mamt"] = "flat", 0
    a = S["anger"]
    a["mouth"] = "frown"


def a_my_turn(S, lt, b):
    o = S["boredom"]
    o["itemR"] = None
    o["itemL"] = "wand"
    o["wandL"] = 180
    hand(o, -1, "out", lt, 0.2, 0.8)
    hand(o, -1, (-150, -86), lt, 0.2, 0.8)
    o["face"] = -0.7
    o["glow"] = tw(lt, 0.5, 1.0, 0, 0.6)
    a = S["anger"]
    a["px"] = 0.9
    a["brow"] = 0.2


def a_mm2(S, lt, b):
    o = S["boredom"]
    a = S["anger"]
    launch = VEND(b) - 0.05
    hit = VEND(B("slowest")) + 0.05
    S["missiles"].append(dict(t0=launch, t1=hit, x0=960 - 196, y0=526, x1=a["x"] + 6, y1=500,
                              arc=40, col="#FF6FD8", wobble=28, trail=2.2))
    sfx(S, launch, "lazyzap", 0.8)
    o["glow"] = 1.0 if lt < b.vs + b.vd else 0.0


def a_drifts(S, lt, b):
    o = S["boredom"]
    a = S["anger"]
    o["lid"] = 0.6
    hand(o, -1, "rest", lt, 0.3, 0.9)
    a["px"] = 0.9
    a["mouth"], a["mamt"] = "smirk", 0.8
    S["cam"] = [tw(lt, 0, b.d, 640, 560), tw(lt, 0, b.d, 360, 400), tw(lt, 0, b.d, 1.0, 1.15)]


def a_slowest(S, lt, b):
    a = S["anger"]
    hand(a, -1, "belly", lt, 0, 0.3)
    hand(a, 1, "out", lt, 0, 0.3)
    a["wandR"] = 0
    a["mouth"], a["mamt"] = "laugh", 0.7
    a["eyes"] = "happy" if lt < b.vs + 0.6 else "open"
    a["brow"] = 0.3


def a_hit(S, lt, b):
    a = S["anger"]
    S["cloud"] = dict(x=a["x"] + 4, y=505, a=tw(lt, 0, 0.25, 0, 1.0), size=1.05)
    hit = b.start - 0.0
    S["bursts"].append(dict(kind="glitter", x=a["x"] + 6, y=500, t=hit, seed=9, dur=5.0))
    sfx(S, hit, "glitterhit", 1.0)
    S["shake"] = clamp(1 - lt / 0.6) * 1.4
    a["makeup"] = 1.0  # hidden inside the cloud until part 2
    a["glitter"] = 0.6
    a["mouth"], a["mamt"] = "o", 1.0
    a["eyes"] = "squeeze"
    a["itemR"] = None
    S["cam"] = [tw(lt, 0, 0.4, S["cam"][0], 460), tw(lt, 0, 0.4, S["cam"][1], 440),
                tw(lt, 0, 0.4, S["cam"][2], 1.35)]


def a_cough(S, lt, b):
    a = S["anger"]
    S["cloud"]["x"] = a["x"] + 4 + math.sin(lt * 20) * 4 * (1 if active(lt, b) else 0)
    # a hand pops out of the cloud, wiping
    hand(a, 1, "face", lt, 0.2, 0.5)
    hand(a, -1, "face", lt, 0.2, 0.5)
    if active(lt, b):
        a["hr"] = (a["hr"][0] + math.sin(lt * 14) * 14, a["hr"][1])
    a["layer"] = 0


def a_wipes(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    S["cloud"]["a"] = 1.0
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], 640), tw(lt, 0, 1.0, S["cam"][1], 360),
                tw(lt, 0, 1.0, S["cam"][2], 1.0)]
    if active(lt, b):
        a["hr"] = (a["hr"][0] + math.sin(lt * 10) * 16, a["hr"][1])
    # Doubt starts cracking up
    tl = b.vs + b.vd * 0.55
    if lt > tl:
        d["mode"] = "laugh"
    d["px"] = 0.0
    d["sweat"] = 0


def a_floor_laugh(S, lt, b):
    d = S["doubt"]
    d["mode"] = "floorlaugh"
    d["x"] = tw(lt, 0, 0.4, d["x"], 215)
    if lt < 0.4:
        d["mode"] = "laugh"
        d["tilt"] = -math.pi / 2 * ease(lt / 0.4)
    sfx(S, T(b, 0.4), "thud", 0.8)
    for k in range(int(b.d / 0.35)):
        sfx(S, T(b, 0.6 + k * 0.35), "thud", 0.35)
    a = S["anger"]
    hand(a, 1, "rest", lt, 0, 0.6)
    hand(a, -1, "rest", lt, 0, 0.6)


def a_floor_narr(S, lt, b):
    S["doubt"]["mode"] = "floorlaugh"
    for k in range(int(b.d / 0.35)):
        sfx(S, T(b, 0.2 + k * 0.35), "thud", 0.3)
    S["rabbit_giggle"] = 1.0
    S["cam"] = [tw(lt, 0, b.d, 640, 520), tw(lt, 0, b.d, 360, 420), tw(lt, 0, b.d, 1.0, 1.2)]


def a_wrong(S, lt, b):
    a = S["anger"]
    d = S["doubt"]
    d["mode"] = "floorlaugh"
    S["rabbit_giggle"] = 0.0
    music(S, T(b), None, 0)
    S["dim"] = tw(lt, 0, 1.0, S["dim"], 0.75)
    S["spot_x"] = a["x"]
    S["spot_y"] = 500
    S["spot_r"] = 200
    S["cam"] = [tw(lt, 0, b.d, S["cam"][0], a["x"]), tw(lt, 0, b.d, S["cam"][1], 480),
                tw(lt, 0, b.d, S["cam"][2], 2.3)]
    S["cloud"]["a"] = 1.0
    hand(a, 1, "rest", lt, 0, 0.5)
    hand(a, -1, "rest", lt, 0, 0.5)
    a["eyes"] = "open"
    a["mouth"], a["mamt"] = "frown", 0.5
    a["px"], a["py"] = 0, 0
    a["glitter"] = 0.4
    # a single long eyelash flutters out of the cloud
    tl = b.d - 1.4
    if lt > tl:
        S["lash_peek"] = clamp((lt - tl) / 0.5)
    sfx(S, T(b, b.d - 1.0), "bling", 0.9)


def a_continued(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)
    music(S, T(b, 0.2), "show", 0.8)
    sfx(S, T(b, 0.3), "sparkle", 0.6)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Welcome to the inside of my head.", pre=1.4, post=0.6, min=4.0),
    Beat(a_open, "narr", "Tonight, my emotions are putting on a magic show.", pre=0.4, post=1.6, min=4.8),
    Beat(a_intro_anger, "narr", "Please welcome our first performer. Give it up for... Anger!",
         post=1.4, id="ia"),
    Beat(a_anger_hmph, "anger", "Hmph. Let's get this over with.", post=0.6),
    Beat(a_intro_doubt, "narr", "Next up, the one and only... Doubt!", post=1.2),
    Beat(a_doubt_unsure, "doubt", "Oh! Wait. Are we sure this is a good idea? I'm not sure this is a good idea.",
         post=0.5),
    Beat(a_intro_boredom, "narr", "And finally... Boredom.", post=0.7),
    Beat(a_boredom_yay, "boredom", "Yay. Magic. Woo.", rate="-30%", post=0.9),
    Beat(a_anger_goes, "narr", "Anger goes first. He steps up to the table and taps the hat with his wand.",
         post=0.9, min=3.4),
    Beat(a_behold, "anger", "Behold! For my first trick, I will pull a rabbit out of this hat!",
         rate="+2%", post=0.5),
    Beat(a_drumroll, min=3.0),
    Beat(a_abra, "anger", "Abracadabra!", pre=0.1, post=0.7, rate="-8%"),
    Beat(a_reach, "narr", "He reaches in deep. Deeper. Deeper still. And he pulls out...", post=0.5, min=5.0),
    Beat(a_turtle_reveal, min=2.6),
    Beat(a_a_turtle, "anger", "A turtle?!", post=0.6, rate="+0%"),
    Beat(a_doubt_laughs, "doubt", "Ha! A turtle! Ha ha ha! I knew that wasn't going to work!", post=0.8),
    Beat(a_side_eye, "narr", "Anger gives Doubt a long, slow side eye.", post=1.6, min=3.6),
    Beat(a_keep_laughing, "anger", "Keep laughing.", rate="-12%", pitch="-10Hz", post=1.4, min=2.6),
    Beat(a_move_over, "boredom", "Ugh. Move over. Watch this.", post=1.0, min=2.6),
    Beat(a_rabbit1, "narr", "Boredom reaches into the hat, and pulls out a rabbit.", post=0.8),
    Beat(a_rabbits_more, "narr", "Then another. And another. And another.", post=0.5),
    Beat(a_rabbits_words, "boredom", "Rabbit. Rabbit. Rabbit. Rabbit. Rabbit.", post=0.5),
    Beat(a_how_many, "doubt", "Whoa! How many rabbits are in there?", post=0.5, min=2.2),
    Beat(a_all_of_them, "boredom", "All of them.", post=1.0),
    Beat(a_eyeroll, "narr", "Anger rolls his eyes so hard they almost do a full lap.", post=0.6, min=3.2),
    Beat(a_show_off, "anger", "Show off.", post=0.6),
    Beat(a_points, "narr", "Then Anger points his wand straight at Boredom.", post=0.6, min=2.6),
    Beat(a_magic_missile, "anger", "Magic missile!", post=0.4, id="mm1", rate="+10%"),
    Beat(a_barely, "narr", "Boredom barely jumps out of the way!", pre=0.6, post=0.9),
    Beat(a_rude, "boredom", "Whoa. Okay. Rude.", pre=0.5, post=0.6),
    Beat(a_my_turn, "boredom", "My turn.", post=0.6),
    Beat(a_mm2, "boredom", "Magic missile.", rate="-30%", post=0.4),
    Beat(a_drifts, "narr", "Boredom's missile drifts across the stage. Slow. Lazy. Bored.", post=0.4),
    Beat(a_slowest, "anger", "Ha! That is the slowest missile I have ever seen! You can't even...",
         post=0.0, id="slowest"),
    Beat(a_hit, min=2.2),
    Beat(lambda S, lt, b: None, "narr", "Right in the face. Glitter. Everywhere.", pre=0.0, post=0.6),
    Beat(a_cough, "anger", "Pfft! Ptoo! Glitter? Seriously?", post=0.5),
    Beat(a_wipes, "narr", "Anger wipes the glitter off his face. He thinks it was only glitter.", post=0.3),
    Beat(a_floor_laugh, "doubt", "Ha ha ha ha ha! Ha ha ha ha!", post=0.6, rate="+12%"),
    Beat(a_floor_narr, "narr", "Doubt laughs so hard, she falls to the floor, pounding it with her fist "
                               "and kicking her legs in the air.", post=0.6),
    Beat(a_wrong, "narr", "But Anger is wrong. It was not only glitter.", pre=0.8, post=2.2),
    Beat(a_continued, "narr", "To be continued.", pre=1.0, post=2.4, min=5.0),
]


# ------------------------------------------------------------------ render
def draw(ctx, S, t):
    chars = [S["doubt"], S["boredom"], S["anger"]]
    draw_stage(ctx, S, t, chars)
    lp = S.get("lash_peek", 0)
    if lp > 0:
        ctx.save()
        from common import apply_camera
        apply_camera(ctx, S, t)
        a = S["anger"]
        bx, by = a["x"] + 50, 470
        flick = math.sin(t * 14) * 0.25
        ctx.translate(bx, by)
        ctx.rotate(-0.5 + flick)
        ctx.move_to(0, 0)
        ctx.curve_to(10 * lp, -18 * lp, 26 * lp, -22 * lp, 40 * lp, -16 * lp)
        E.src(ctx, "#1d1420")
        ctx.set_line_width(4)
        ctx.stroke()
        E.sparkle(ctx, 40 * lp, -16 * lp, 10 * lp, "#FFFFFF")
        ctx.restore()
    if S["card"] > 0:
        E.draw_title_card(ctx, t, "The Magic Show", "Inside My Head", "PART 1: ABRACADABRA", S["card"])
    if S["endcard"] > 0:
        E.draw_end_card(ctx, t, "To be continued...", "Part 2: Sorry, Bro", S["endcard"])
        S["subs"] = False
    draw_fade(ctx, S["fade"])
