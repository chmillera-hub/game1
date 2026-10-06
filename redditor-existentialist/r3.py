"""Part 3: The Punchline."""
import math
import random

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import rgfx as G
import r1
from rcommon import (sfx, music, active, hand, walk, cam_to, apply_cam, base_state, fade, SCREEN,
                     sitting_redditor)
from show import Beat

TOTAL = 0.0
IDX = {}
FLOOR = 650
RS = 1.35
WALLS = (330, 640, 950)


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
    S["r"] = G.new_redditor(640, y=FLOOR, s=RS, mouth="smile", mamt=0.2)
    S["d"] = G.new_doubt(220, y=FLOOR, s=1.25, face=0.3, px=1, mouth="smile", mamt=0.6)
    S["anger"] = E.new_char("anger", 330, mouth="smile", mamt=0.5, visible=True)
    S["boredom"] = E.new_char("boredom", 950, mouth="flat")
    S["sd"] = G.new_doubt(640, mouth="smile", mamt=0.6)   # the stage Doubt
    S["walls_fall"] = 0.0
    S["r_alpha"] = 1.0
    S["hands"] = []
    S["wall"] = None
    S["card"] = 1.0
    S["light"] = 1.2
    S["stars"] = 0.0
    S["clock"] = None
    return S


# ------------------------------------------------------------------ the stage
def a_title(S, lt, b):
    music(S, T(b), "hope", 0.6)


def a_cut(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1.0, 0.0)
    S["cam"] = [520, 400, 1.0]
    sfx(S, VEND(b), "cutclap", 1.0)
    if lt > b.vs + b.vd:
        S["scene"] = "stage"
        S["flash"] = clamp(1 - (lt - b.vs - b.vd) / 0.3)


def a_reveal(S, lt, b):
    S["scene"] = "stage"
    S["cam"] = [640, 380, 1.0]
    S["walls_fall"] = tw(lt, 0.3, 1.3, 0, 1, ease_in)
    S["r_alpha"] = tw(lt, 0.0, 1.0, 1, 0)
    sfx(S, T(b, 1.1), "thud", 0.6)
    sfx(S, T(b, 1.25), "thud", 0.5)
    sfx(S, T(b, 0.1), "sparkle", 0.6)
    music(S, T(b, 0.3), "show", 0.6)
    for c in (S["anger"], S["boredom"], S["sd"]):
        c["mouth"], c["mamt"] = "smile", 0.8


def a_howd_we_do(S, lt, b):
    a = S["anger"]
    hand(a, 1, "wave", lt, 0, 0.4)
    a["face"] = 0.4
    a["brow"] = 0.2


def a_boredom_role(S, lt, b):
    a = S["anger"]
    hand(a, 1, "rest", lt, 0, 0.4)
    o = S["boredom"]
    o["lid"] = 0.6
    o["face"] = -0.4
    cam_to(S, lt, 0, 0.6, 820, 420, 1.3)


def a_great_job(S, lt, b):
    cam_to(S, lt, 0, 0.6, 640, 380, 1.0)
    hs = []
    targets = [(S["anger"], 1.0), (S["sd"], 2.2), (S["boredom"], 3.4)]
    for c, tk in targets:
        tk = b.vs + b.vd + 0.2 + (tk - 1.0)
        hx = c["x"] + 60
        hy = c["y"] - 230
        if tk - 0.6 < lt < tk + 0.6:
            u = clamp((lt - tk + 0.6) / 0.6)
            back = clamp((lt - tk) / 0.6)
            y = lerp(H_OFF, hy, ease_out(u)) if lt < tk else lerp(hy, H_OFF, ease_in(back))
            hs.append((hx + 20, y, -0.2, True))
            hand(c, 1, (60, -230), lt, tk - 0.5, tk - 0.2)
        elif lt >= tk + 0.6:
            hand(c, 1, "rest", lt, tk + 0.6, tk + 1.0)
        sfx(S, T(b, tk), "slap", 0.9)
    S["hands"] = hs if lt < b.d else []


H_OFF = 900


def a_come_here(S, lt, b):
    d = S["sd"]
    tl = b.vs + b.vd
    u = ease(clamp((lt - tl) / 1.2))
    d["y"] = lerp(E.GROUND, 520, u)
    d["s"] = lerp(1.0, 1.5, u)
    d["mouth"], d["mamt"] = "smile", 0.9
    S["hands"] = [(d["x"] - 80 * d["s"], lerp(H_OFF, d["y"] - 70 * d["s"], u), 0.5, False),
                  (d["x"] + 80 * d["s"], lerp(H_OFF, d["y"] - 70 * d["s"], u), -0.5, False)] if lt > tl - 0.4 else []
    cam_to(S, lt, tl, tl + 1.2, 640, 330, 1.6)


def hold_doubt(S):
    d = S["sd"]
    d["y"], d["s"] = 520, 1.5
    S["hands"] = []
    S["cam"] = [640, 330, 1.6]


def a_what_if_never(S, lt, b):
    hold_doubt(S)
    # set her down on the books, then the hands drift back out of frame
    d = S["sd"]
    u = ease(clamp(lt / 0.9))
    if lt < 0.9:
        S["hands"] = [(d["x"] - 120 - 60 * u, lerp(d["y"] - 105, H_OFF, u), 0.5, False),
                      (d["x"] + 120 + 60 * u, lerp(d["y"] - 105, H_OFF, u), -0.5, False)]
    d = S["sd"]
    d["brow"] = 0.4
    d["px"], d["py"] = 0, -0.4


def a_two_and_two(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    d["itemR"] = None
    d["mode"] = "giggle" if lt < 1.0 else None
    if lt > 1.0:
        hand(d, 1, (34, -170), lt, 1.0, 1.4)
        d["mouth"], d["mamt"] = "smile", 0.7
    music(S, T(b), "hope", 0.6)


def a_you_mean(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    hand(d, 1, "rest", lt, 0, 0.4)
    d["brow"] = 0.2


def a_chin(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    hand(d, 1, (8, -132), lt, 0, 0.4)
    d["px"], d["py"] = 0.6, -0.8
    d["mouth"], d["mamt"] = "smirk", 0.6


def a_sorcery(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    hand(d, 1, "rest", lt, 0, 0.3)
    d["px"], d["py"] = 0, 0
    S["shake"] = 0.1 if lt < 0.5 else 0


def a_retro(S, lt, b):
    hold_doubt(S)
    S["shake"] = 0
    d = S["sd"]
    hand(d, -1, "wave", lt, 0, 0.4)
    d["mouth"], d["mamt"] = "smile", 0.8


def a_joke(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    hand(d, -1, "rest", lt, 0, 0.4)
    d["brow"] = 0.3


def a_everything(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    d["brow"] = 0.6
    d["lid"] = 0.2
    S["stars"] = tw(lt, b.vs + b.vd * 0.6, b.d, 0, 1)
    sfx(S, VEND(b), "sparkle", 0.5)


def a_whoa(S, lt, b):
    hold_doubt(S)
    S["stars"] = 1.0
    S["cam"] = [640, 330, tw(lt, 0, b.d, 1.6, 1.45)]
    music(S, T(b), "hope", 0.9)


def a_giggle(S, lt, b):
    hold_doubt(S)
    d = S["sd"]
    d["mode"] = "giggle"
    S["stars"] = tw(lt, 0, b.d, 1, 0)
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


# ------------------------------------------------------------------ the other redditor
def a_different(S, lt, b):
    S["scene"] = "box"
    S["hands"] = []
    S["fade"] = tw(lt, 0, 0.6, 1, 0)
    S["light"] = 0.9
    r = S["r"]
    r.update(x=640, mouth="smirk", mamt=0.5, face=-0.5, px=-1, brow=-0.2, lid=0.5)
    d = S["d"]
    d.update(x=360, face=0.4, px=1, mouth="smile", mamt=0.6, mode=None, itemR="book")
    S["cam"] = [520, 400, tw(lt, 0, b.d, 1.0, 1.1)]
    music(S, T(b), "lofi", 0.5)


def a_full_of_crap(S, lt, b):
    r = S["r"]
    hand(r, -1, (-90, -140), lt, 0.2, 0.6)
    if lt > b.d - 0.6:
        hand(r, -1, "rest", lt, b.d - 0.6, b.d)


def a_sad(S, lt, b):
    d = S["d"]
    d["mouth"], d["mamt"] = "frown", 0.8
    d["lip"] = tw(lt, 0.2, 0.6, 0, 1)
    d["tears"] = tw(lt, 0.6, 1.4, 0, 1)
    d["brow"] = 1.0
    d["wide"] = 0.5
    cam_to(S, lt, 0, 0.8, 380, 420, 1.8)
    sfx(S, T(b, 0.4), "trombone", 0.3)
    music(S, T(b), None, 0)


def a_bub(S, lt, b):
    S["wall"] = dict(x=900, alpha=0.0)
    cam_to(S, lt, 0, 0.8, 560, 400, 1.05)
    r = S["r"]
    r["wide"] = tw(lt, 0.3, 0.6, 0, 0.8)
    r["lid"] = 0.2
    music(S, T(b, 0.2), "quirky", 0.6)


def a_who_said(S, lt, b):
    r = S["r"]
    r["x"] = tw(lt, 0, 0.9, 640, 560)
    r["walking"] = 0.9 if lt < 0.9 else 0
    r["px"] = math.sin(lt * 9) * 1.0
    r["face"] = math.sin(lt * 4) * 0.8
    r["wide"] = 1.0
    r["sweat"] = 1.0
    S["cam"] = [520, 400, 1.05]


def a_behind(S, lt, b):
    r = S["r"]
    r["px"] = math.sin(lt * 6) * 1.0
    r["face"] = math.sin(lt * 3) * 0.8
    w = S["wall"]
    w["alpha"] = tw(lt, 0, 0.8, 0, 1)
    w["x"] = 800
    S["cam"] = [600, 380, 1.0]


def a_spin_fall(S, lt, b):
    r = S["r"]
    r["face"] = tw(lt, 0, 0.3, r["face"], 0.8)
    r["px"] = 1
    r["py"] = -0.8
    r["wide"] = 1.4
    r["mouth"], r["mamt"] = "o", 1.0
    r["sweat"] = 1.0
    if lt > 0.4:
        u = ease(clamp((lt - 0.4) / 0.3))
        r["yoff"] = lerp(0, 40 * RS, u)
        r["footL"] = (lerp(0, 30, u), lerp(0, -50, u))
        r["footR"] = (lerp(0, 60, u), lerp(0, -40, u))
        r["tilt"] = lerp(0, -0.25, u)
    sfx(S, T(b, 0.7), "thud", 0.8)
    S["cam"] = [tw(lt, 0, 0.6, 600, 690), 380, tw(lt, 0, 0.6, 1.0, 1.15)]


def a_im_anger(S, lt, b):
    S["wall"]["facepalm"] = tw(lt, 0, 0.4, 0, 1) if lt < 2.0 else tw(lt, 2.0, 2.4, 1, 0)
    sfx(S, T(b, 0.35), "slap", 0.5)
    cam_to(S, lt, 0, 1.0, 720, 360, 1.05)


def a_sorry(S, lt, b):
    r = S["r"]
    S["wall"]["facepalm"] = 0
    r["face"] = tw(lt, 0, 0.4, 0.8, -0.8)
    r["px"] = tw(lt, 0, 0.4, 1, -1)
    r["py"] = 0
    r["wide"] = 0.6
    r["mouth"], r["mamt"] = "wavy", 1.0
    d = S["d"]
    d["tears"] = 0.6
    d["lip"] = 1.0
    d["wide"] = 0.9
    cam_to(S, lt, 0, 0.8, 520, 420, 1.2)


def a_full_of_it(S, lt, b):
    r = S["r"]
    r["face"] = tw(lt, 0, 0.3, -0.8, 0.8)
    r["px"] = 1
    r["wide"] = 1.0
    w = S["wall"]
    w["x"] = tw(lt, 0, 0.6, 800, 760)
    w["point"] = 1 if lt > 0.6 else 0
    d = S["d"]
    d["tears"] = 0
    d["lip"] = tw(lt, 0, 1, 1, 0)
    d["mouth"], d["mamt"] = "flat", 0
    cam_to(S, lt, 0, 0.8, 700, 380, 1.1)


def a_whatever(S, lt, b):
    r = S["r"]
    w = S["wall"]
    w["point"] = 0
    # stands up, nose in the air
    u = ease(clamp(lt / 0.6))
    r["yoff"] = lerp(40 * RS, 0, u)
    r["footL"] = (lerp(30, 0, u), lerp(-50, 0, u))
    r["footR"] = (lerp(60, 0, u), lerp(-40, 0, u))
    r["tilt"] = lerp(-0.25, -0.08, u)
    r["sweat"] = 0
    r["wide"] = 0
    r["lid"] = 0.6
    r["py"] = -1.0
    r["face"] = -0.3
    r["mouth"], r["mamt"] = "smirk", 0.8
    hand(r, 1, (60, -60), lt, 0.4, 0.8)
    hand(r, -1, (-40, -170), lt, 0.6, 1.0)


def a_solitude(S, lt, b):
    w = S["wall"]
    d = S["d"]
    w["facepalm"] = tw(lt, 0, 0.4, 0, 1)
    d["itemR"] = None
    hand(d, 1, (10, -170), lt, 0, 0.4)
    d["eyes"] = "happy"
    d["mouth"], d["mamt"] = "frown", 0.4
    sfx(S, T(b, 0.3), "slap", 0.5)
    sfx(S, T(b, 0.35), "slap", 0.4)
    S["cam"] = [600, 380, 1.0]


def a_vanish(S, lt, b):
    w = S["wall"]
    d = S["d"]
    d["alpha"] = tw(lt, 0.2, 0.8, 1, 0)
    w["alpha"] = tw(lt, 0.2, 0.8, 1, 0)
    S["light"] = tw(lt, 0.8, 2.0, 0.9, 2.0)
    sfx(S, T(b, 0.2), "poof", 0.9)
    if lt > b.d - 0.6:
        S["fade"] = tw(lt, b.d - 0.6, b.d, 0, 1)
    music(S, T(b), None, 0)


def a_back_to_life(S, lt, b):
    S["scene"] = "bedroom"
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    r = S["r"]
    r.update(s=1.0, y=E.GROUND, x=tw(lt, 0, 2.0, 980, 820), tilt=0, yoff=0, footL=(0, 0), footR=(0, 0),
             mouth="smirk", mamt=0.8, lid=0.5, py=-1.0, face=-0.5, px=-0.6, alpha=1.0)
    r["walking"] = 0.8 if lt < 2.0 else 0
    r["sq"] = tw(lt, 0.4, 1.0, 1.0, 0.92)
    hand(r, -1, "hip", lt, 0, 0.3)
    hand(r, 1, "hip", lt, 0, 0.3)
    if lt > b.d - 1.4:
        sitting_redditor(r)
        r.update(sq=1.0, mouth="smirk", mamt=0.4, py=0.0)
    S["cam"] = [640, 360, 1.0]
    music(S, T(b), "lofi", 0.6)
    sfx(S, T(b, b.d - 1.0), "typing", 0.5)


def a_clock(S, lt, b):
    S["scene"] = "mind"
    S["fade"] = tw(lt, 0, 0.5, 1, 0) if lt < 0.6 else 0
    S["wall"] = dict(x=880, alpha=1.0, facepalm=1.0)
    d = S["d"]
    d.update(x=400, alpha=1.0, y=FLOOR, s=1.25, eyes="happy", mouth="frown", mamt=0.4, tears=0, lip=0,
             itemR=None)
    d["hl"] = (-80, -200)
    d["hr"] = (10, -170)
    S["clock"] = dict(t0=T(b), secs=3 * 86400 + 14 * 3600 + 7 * 60 + 42)
    sfx(S, T(b, 0.4), "ticking", 0.7)
    sfx(S, T(b, 6.4), "ticking", 0.7)
    S["cam"] = [640, 360, 1.0]
    music(S, T(b, 0.3), "quirky", 0.5)


def a_same_time(S, lt, b):
    w = S["wall"]
    w["facepalm"] = tw(lt, 0, 0.4, 1, 0)
    w["point"] = 1
    sfx(S, T(b, 0.1), "ticking", 0.5)


def a_theyll_be_back(S, lt, b):
    d = S["d"]
    d["eyes"] = "open"
    d["mode"] = "giggle"
    d["px"] = 1


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)
    music(S, T(b), "hope", 0.7)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, min=3.2),
    Beat(a_cut, "me", "And... cut!", pre=1.6, post=1.0),
    Beat(a_reveal, "me", "Because that redditor? That was me, role-playing. And the barriers were my "
                         "whole emotional family.", pre=1.4, post=0.8),
    Beat(a_howd_we_do, "anger", "So? How'd we do? Were we convincing walls, or what?", post=0.5),
    Beat(a_boredom_role, "boredom", "I stood perfectly still for forty minutes. Best role I've ever had.",
         post=0.6),
    Beat(a_great_job, "me", "You all did a great job.", post=3.8),
    Beat(a_come_here, "me", "Doubt. Come here.", post=1.6),
    Beat(a_what_if_never, "me", "The giggle was your idea. But what if the redditor never thought of it? "
                                "How would they get out if their doubt never giggled at them?", post=0.5),
    Beat(a_two_and_two, "doubt", "Hee hee. If they read the part where I giggled, they might put two and two "
                                 "together. Their own doubt could giggle. Or do something like it.", post=0.5),
    Beat(a_you_mean, "me", "Wait. So your giggle could give them the idea? They might have been trapped for a "
                           "long time, but now that they know their doubt can giggle, that could be the key to "
                           "understanding their own barriers?", post=0.4),
    Beat(a_chin, "doubt", "Yeah. Sounds about right.", post=0.6),
    Beat(a_sorcery, "me", "What kind of sorcery is this?", post=0.4),
    Beat(a_retro, "doubt", "This universe is weird. But it makes sense retroactively, right?", post=0.4),
    Beat(a_joke, "me", "It does. It feels strange. It's a joke that makes no sense until the punchline, and "
                       "then it's obvious.", post=0.4),
    Beat(a_everything, "doubt", "That applies to more than jokes. It applies to everything.", post=1.2),
    Beat(a_whoa, "me", "Whoa, dude. That could be a shower thought.", rate="-10%", post=0.4),
    Beat(a_giggle, "doubt", "Hee hee.", sub="(Doubt giggles)", post=1.4),
    Beat(a_different, "me", "Now picture a different redditor. One who isn't ready to listen.", pre=0.8,
         post=0.6),
    Beat(a_full_of_crap, "redditor", "Hey, Doubt. I think you're full of crap. Go back to being a barrier "
                                     "or something.", post=0.4),
    Beat(a_sad, min=2.6),
    Beat(a_bub, "anger", "Hey, bub. Treat your doubt with some respect. You know she's just trying to help "
                         "your sorry ass, right?", post=0.3),
    Beat(a_who_said, "redditor", "Who said that?!", rate="+8%", post=0.3, min=1.4),
    Beat(a_behind, "anger", "I'm right behind you, bucko. And you'd better get your attitude in line. I hate "
                            "hearing that crap coming from you, of all people.", post=0.3),
    Beat(a_spin_fall, "redditor", "What the actual... Are you a wall? Talking to me?", pre=0.9, post=0.4),
    Beat(a_im_anger, "anger", "I'm Anger, doofus. And yeah, I can talk. I'm you. So can you take a chill "
                              "pill while you talk to your doubt, or am I gonna have to smack you?", post=0.4),
    Beat(a_sorry, "redditor", "Uh... yeah. Doubt. I'm sorry or whatever.", rate="-6%", gain=0.7, pre=0.6,
         post=0.4),
    Beat(a_full_of_it, "anger", "Dude. I'm you. I know when you're full of it. If you want to keep suffering, "
                                "go ahead. I'm trying to help you.", pre=0.4, post=0.4),
    Beat(a_whatever, "redditor", "Ya, whatever, lol. You're imaginary. I can talk to you however I want, you "
                                 "jerkos.", post=0.6),
    Beat(a_solitude, "anger", "Well, bub. Enjoy your solitude.", pre=0.6, post=0.8),
    Beat(a_vanish, "me", "And just like that, the emotions disappear. The barriers are gone.", pre=0.4,
         post=0.6),
    Beat(a_back_to_life, "me", "The redditor puffs out their chest, and goes right back to their life.",
         pre=0.8, post=1.8, min=5.0),
    Beat(a_clock, "me", "And somewhere in their mind, two very tired emotions point at the clock, counting "
                        "down to the next existential crisis. So they can try again.", pre=1.0, post=0.6),
    Beat(a_same_time, "anger", "Same time next week?", post=0.4),
    Beat(a_theyll_be_back, "doubt", "Hee hee. They'll be back.", post=1.6),
    Beat(a_end, "me", "The End.", pre=0.8, post=4.4, min=6.0),
]


# ------------------------------------------------------------------ drawing
def draw_hands(ctx, S):
    for (x, y, ang, open_) in S["hands"]:
        G.pov_hand(ctx, x, y, ang, open_)


def draw_stage(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    G.stage_room(ctx, t)
    for c in (S["anger"], S["boredom"], S["sd"]):
        if c is S["sd"] and c["y"] < E.GROUND - 1:
            continue
        E.draw_char(ctx, c, t)
    sd = S["sd"]
    if sd["y"] < E.GROUND - 1:
        a_ = clamp((E.GROUND - sd["y"]) / (E.GROUND - 520))
        cols = ["#8E1F2F", "#2E5A9E", "#3E7A3E", "#C9A040", "#6B4E8E", "#8E5A3E"]
        y = 520
        i = 0
        while y < 760:
            wdt = 150 - (i % 3) * 14
            E.rrect(ctx, 640 - wdt / 2 + (i % 2) * 8, y, wdt, 30, 4)
            E.src(ctx, cols[i % len(cols)], a_)
            ctx.fill_preserve()
            E.src(ctx, "#2A1A10", a_)
            ctx.set_line_width(2)
            ctx.stroke()
            ctx.rectangle(640 - wdt / 2 + 12 + (i % 2) * 8, y + 12, wdt - 24, 4)
            E.src(ctx, "#E8D9B8", 0.6 * a_)
            ctx.fill()
            y += 30
            i += 1
        E.draw_char(ctx, sd, t)
    for x, lbl in zip(WALLS, ("WALL", "ALSO A WALL", "WALL")):
        G.draw_cardboard_wall(ctx, x, E.GROUND + 4, t, S["walls_fall"], lbl)
    if S["r_alpha"] > 0:
        r = dict(S["r"])
        r.update(x=640, y=E.GROUND, s=1.0, alpha=S["r_alpha"])
        E.draw_char(ctx, r, t)
        rnd = random.Random(int(t * 10))
        for i in range(14):
            E.sparkle(ctx, 640 + rnd.uniform(-70, 70), E.GROUND - rnd.uniform(0, 200), rnd.uniform(4, 10),
                      "#FFFFFF", 1 - S["r_alpha"])
    if S["stars"] > 0:
        for i in range(10):
            a = t * 0.8 + i * 2 * math.pi / 10
            E.sparkle(ctx, 640 + math.cos(a) * 260, 300 + math.sin(a) * 120, 10, "#FFF6B0", S["stars"])
    draw_hands(ctx, S)
    ctx.restore()


def draw_box(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    G.draw_box_interior(ctx, t, S["light"], 0, 0)
    w = S["wall"]
    if w:
        w["talk"] = S["anger"]["talk"]
    if w and w.get("alpha", 1) > 0:
        G.draw_anger_wall(ctx, w["x"], FLOOR + 10, 1.0, t, w)
    d = S["d"]
    E.draw_char(ctx, d, t)
    E.draw_char(ctx, S["r"], t)
    ctx.restore()


def draw_mind(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    g = cairo.RadialGradient(640, 360, 40, 640, 360, 800)
    g.add_color_stop_rgb(0, *E.rgb("#2A2140"))
    g.add_color_stop_rgb(1, *E.rgb("#0B0814"))
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, FLOOR, 1280, 100)
    E.src(ctx, "#15111F")
    ctx.fill()
    ck = S["clock"]
    if ck:
        secs = ck["secs"] - (t - ck["t0"])
        G.draw_crisis_clock(ctx, 640, 130, t, max(0, secs))
    S["wall"]["talk"] = S["anger"]["talk"]
    G.draw_anger_wall(ctx, S["wall"]["x"], FLOOR + 10, 0.9, t, S["wall"])
    E.draw_char(ctx, S["d"], t)
    ctx.restore()


def draw(ctx, S, t):
    sc = S["scene"]
    if sc == "stage":
        draw_stage(ctx, S, t)
    elif sc == "box":
        draw_box(ctx, S, t)
    elif sc == "bedroom":
        r1.draw_bedroom(ctx, S, t, 0)
    elif sc == "mind":
        draw_mind(ctx, S, t)
    if S["flash"] > 0:
        ctx.set_source_rgba(1, 1, 1, S["flash"])
        ctx.paint()
    if S["card"] > 0:
        G.title_card(ctx, t, "Redditor Existentialist", "Part 3: The Punchline", S["card"])
    fade(ctx, S["fade"])
    if S["endcard"] > 0:
        G.end_card(ctx, t, "The End", "(until the next existential crisis)",
                   note=["If the void ever feels like too much, you don't have to sit in the box alone.",
                         "Talk to someone you trust, or call or text 988 (US) to reach a crisis line."],
                   a=S["endcard"])
        S["subs"] = False
