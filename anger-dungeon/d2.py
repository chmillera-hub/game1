"""Part 2: The Fall."""
import math
import random

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import dgfx as G
from dcommon import sfx, music, active, hand, walk, base_state, cam_to, apply_cam, ambience
from show import Beat

TOTAL = 0.0
IDX = {}
PIT = (0, 0, 1600, 720)
LIE_X = 640


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
    S["scene"] = "shaft"
    S["anger"] = G.new_warrior(700, itemL=None, itemR="sword", wandR=-60, lid=0.35, mouth="flat",
                               cape_lift=1.0)
    S["anger"]["hl"] = (-120, -260)
    S["anger"]["hr"] = (130, -250)
    S["card"] = 1.0
    S["scroll"] = 0.0
    S["groove"] = None
    S["sparks"] = 0.0
    S["creature"] = None
    S["eyes"] = None
    S["rock"] = None
    S["glove"] = None
    S["blur"] = 0.0
    S["zzz"] = 0.0
    S["amb"] = 0.8
    return S


def lying(a):
    a.update(x=LIE_X, y=E.GROUND, tilt=-math.pi / 2, itemL=None, itemR=None, cape_lift=0, hurt=1.0,
             face=0.0, mouth="frown", mamt=0.4, brow=0.3)
    a["hl"] = (-100, -60)
    a["hr"] = (100, -60)


# ------------------------------------------------------------------ the shaft
def a_title(S, lt, b):
    music(S, T(b), "drone", 0.8)
    sfx(S, T(b, 0.4), "hit", 0.8)
    ambience(S, TOTAL)


def fall_scroll(S, t0, v):
    S["scroll"] = (S["t"] - t0) * v


def a_fall1(S, lt, b):
    S["card"] = tw(lt, 0, 1.0, 1.0, 0.0)
    fall_scroll(S, T(b), 1900)
    sfx(S, T(b, 0.2), "windfall", 0.9)
    sfx(S, T(b, 3.9), "windfall", 0.9)
    music(S, T(b), "tense", 0.6)


def a_fall2(S, lt, b):
    fall_scroll(S, IDX["f1"].start, 1900)
    a = S["anger"]
    a["lid"] = 0.4
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.0, 1.4)]


def a_refuse(S, lt, b):
    fall_scroll(S, IDX["f1"].start, 1900)
    a = S["anger"]
    tl = b.vs + b.vd * 0.5
    if lt > tl:
        a["lid"] = 0.0
        a["brow"] = -1.2
        a["wide"] = 0.3
    S["cam"] = [640, 360, tw(lt, 0, 0.5, 1.4, 1.0)]
    sfx(S, T(b, tl), "clank", 0.6)
    sfx(S, T(b, b.d - 1.0), "windfall", 0.9)
    music(S, T(b, tl), "epic", 1.0)


def a_stab(S, lt, b):
    a = S["anger"]
    t0 = IDX["f1"].start
    stab = b.vs + 0.25
    v0, k = 1900.0, 0.75
    if lt < stab:
        fall_scroll(S, t0, v0)
    else:
        base = (T(b, stab) - t0) * v0
        dt = S["t"] - T(b, stab)
        S["scroll"] = base + v0 / k * (1 - math.exp(-k * dt))
    a["brow"] = -1.4
    a["lid"] = 0
    a["mouth"], a["mamt"] = "laugh", 1.0
    a["x"] = tw(lt, 0, stab, 700, 712)
    hand(a, 1, (150, -200), lt, 0, stab, back_out)
    a["wandR"] = tw(lt, 0, stab, -60, 0)
    hand(a, -1, (-110, -160), lt, 0, stab)
    if lt > stab:
        S["groove"] = T(b, stab)
        S["sparks"] = 1.0
        a["mouth"], a["mamt"] = "tight", 1.0
    sfx(S, T(b, stab), "clank", 1.0)
    sfx(S, T(b, stab), "grind", 1.0)
    sfx(S, T(b, stab + 2.9), "grind", 0.9)
    S["shake"] = 0.5 if lt > stab else 0.1


def a_grind(S, lt, b):
    a = S["anger"]
    bs = IDX["stab"]
    t0 = IDX["f1"].start
    stab_abs = T(bs, bs.vs + 0.25)
    v0, k = 1900.0, 0.75
    base = (stab_abs - t0) * v0
    dt = S["t"] - stab_abs
    S["scroll"] = base + v0 / k * (1 - math.exp(-k * dt))
    S["sparks"] = clamp(1.2 - lt / b.d * 0.6)
    S["shake"] = 0.45 * S["sparks"]
    a["mouth"], a["mamt"] = "tight", 1.0
    S["cam"] = [tw(lt, 0, b.d, 640, 760), tw(lt, 0, b.d, 360, 300), tw(lt, 0, b.d, 1.0, 1.5)]


def a_impact(S, lt, b):
    S["flash"] = clamp(1 - lt / 0.25) if lt < 0.3 else 0
    S["fade"] = 1.0 if lt > 0.15 else 0
    S["sparks"] = 0
    S["shake"] = 0
    sfx(S, T(b, 0.0), "impact", 1.0)
    music(S, T(b), None, 0)


# ------------------------------------------------------------------ the pit
def a_survives(S, lt, b):
    S["scene"] = "pit"
    a = S["anger"]
    lying(a)
    a["lid"] = 0.7
    S["fade"] = tw(lt, 0.3, 2.4, 1, 0)
    S["blur"] = 1.0
    S["cam"] = [LIE_X - 20, 500, 2.0]
    S["dust_t"] = T(b, 0)
    S["amb"] = 0.8


def a_ugh(S, lt, b):
    a = S["anger"]
    a["lid"] = 0.55
    a["brow"] = 0.5
    a["mouth"], a["mamt"] = "frown", 0.8
    S["blur"] = tw(lt, 0, b.d, 1.0, 0.5)


def a_aches(S, lt, b):
    a = S["anger"]
    S["blur"] = tw(lt, 0, b.d, 0.5, 0.25)
    cam_to(S, lt, 0, b.d, 640, 380, 1.15)
    a["lid"] = 0.45
    music(S, T(b), "tense", 0.6)


def a_where(S, lt, b):
    a = S["anger"]
    a["px"] = math.sin(lt * 1.4) * 0.9
    a["py"] = 0.0


def a_eyes_return(S, lt, b):
    a = S["anger"]
    a["px"] = tw(lt, 0, 0.5, a["px"], 0.0)
    ap = 0.6
    e = dict(x=170, y=560, a=0.0, look=1.0)
    if lt > ap:
        e["a"] = tw(lt, ap, ap + 0.5, 0, 1) if lt < b.d - 1.0 else tw(lt, b.d - 1.0, b.d - 0.4, 1, 0)
        e["x"] = tw(lt, ap, b.d, 170, 260)
    S["eyes"] = e if lt < b.d else None
    a["lid"] = tw(lt, 1.5, b.d - 0.5, 0.45, 1.0)
    S["fade"] = tw(lt, b.d - 1.2, b.d, 0, 1)
    sfx(S, T(b, ap), "sting", 0.7)
    sfx(S, T(b, ap + 1.0), "scurry", 0.5)


def a_black(S, lt, b):
    S["fade"] = 1.0
    S["eyes"] = None
    sfx(S, T(b, 0.6), "stoneshift", 0.5)
    sfx(S, T(b, 1.6), "scurry", 0.5)
    music(S, T(b), None, 0)


def a_wakes(S, lt, b):
    a = S["anger"]
    S["fade"] = tw(lt, 0, 0.8, 1, 0)
    S["blur"] = 0.0
    a["lid"] = tw(lt, 0.6, 1.0, 1.0, 0.0)
    a["wide"] = tw(lt, 0.6, 1.0, 0, 0.4)
    a["brow"] = 0.6
    a["px"] = tw(lt, 1.0, 1.6, 0, -0.9)
    S["cam"] = [600, 440, 1.5]


def a_one_arm(S, lt, b):
    a = S["anger"]
    a["wide"] = 0.2
    tr = math.sin(lt * 30) * 3
    hand(a, 1, (60, -230), lt, 0.8, 2.6)
    if lt > 0.8:
        a["hr"] = (a["hr"][0] + tr, a["hr"][1])
    # legs try, do not move
    if 2.8 < lt < 3.6:
        a["footL"] = (0, -4 * math.sin((lt - 2.8) / 0.8 * math.pi))
    a["mouth"], a["mamt"] = "tight", 1.0
    S["cam"] = [tw(lt, 0, b.d, 600, 560), 450, 1.35]


def a_creeps(S, lt, b):
    a = S["anger"]
    tr = math.sin(S["t"] * 30) * 3
    a["hr"] = (60 + tr, -230)
    a["mouth"], a["mamt"] = "frown", 0.6
    a["px"] = -1.0
    a["brow"] = -0.4
    x = tw(lt, 0, b.d, -120, 330, linear)
    S["creature"] = dict(x=x, y=E.GROUND, s=1.0, face=1, walk=0.45 if lt < b.d else 0, glow=1.0,
                         mouth=tw(lt, 1.0, b.d, 0.2, 0.7), tongue=tw(lt, 1.5, b.d, 0, 1), drool=1.0)
    S["cam"] = [tw(lt, 0, b.d, 520, 480), 460, tw(lt, 0, b.d, 1.3, 1.6)]
    sfx(S, T(b, 0.4), "growl", 0.9)
    sfx(S, T(b, 2.5), "growl", 0.9)
    for k in range(4):
        sfx(S, T(b, 1.2 + k * 1.1), "drool", 0.5)


def a_lunge(S, lt, b):
    a = S["anger"]
    c = S["creature"]
    tr = math.sin(S["t"] * 34) * 4
    hand(a, 1, (110, -210), lt, 0, 0.6)
    a["hr"] = (a["hr"][0] + tr, a["hr"][1])
    a["lid"] = tw(lt, 1.0, 1.3, 0, 1.0)
    a["brow"] = 0.4
    a["mouth"], a["mamt"] = "tight", 1.0
    c["x"] = tw(lt, 0.4, 1.4, 330, 372, ease_in)
    c["mouth"] = tw(lt, 0.4, 1.4, 0.7, 1.0)
    c["walk"] = 0
    hit = 1.55
    S["rock"] = dict(t0=T(b, hit - 0.55), t1=T(b, hit), x0=-80, y0=180, x1=372 + 92, y1=E.GROUND - 70)
    S["ko_t"] = T(b, hit)
    if lt > hit:
        c["ko"] = clamp((lt - hit) / 0.35)
        c["mouth"] = 0.4
        c["x"] = tw(lt, hit, hit + 0.4, 372, 350)
    sfx(S, T(b, 0.3), "growl", 1.0)
    sfx(S, T(b, hit - 0.55), "throw", 0.8)
    sfx(S, T(b, hit), "bonk", 1.0)
    sfx(S, T(b, hit + 0.3), "ko", 0.8)
    music(S, T(b), None, 0)
    S["shake"] = clamp(1 - (lt - hit) / 0.3) * 0.5 if lt > hit else 0
    S["cam"] = [tw(lt, 0, 1.2, 480, 500), 470, tw(lt, 0, 1.2, 1.6, 1.9)]


def a_one_eye(S, lt, b):
    a = S["anger"]
    a["lid"] = 0
    a["lidL"] = 1.0
    a["lidR"] = tw(lt, 0.3, 0.8, 1.0, 0.0)
    a["px"] = -1
    hand(a, 1, (112, -110), lt, 1.2, 2.2)
    S["cam"] = [tw(lt, 0, 1.0, 500, 520), 470, tw(lt, 0, 1.0, 1.9, 1.4)]


def a_what(S, lt, b):
    a = S["anger"]
    a["lidL"] = tw(lt, 0, 0.3, 1.0, 0.0)
    a["lidR"] = 0
    a["brow"] = 0.3
    a["mouth"], a["mamt"] = "flat", 0


def a_voice1(S, lt, b):
    a = S["anger"]
    a["px"] = -1
    a["wide"] = 0.6
    a["lidL"], a["lidR"] = None, None
    S["cam"] = [tw(lt, 0, 1.5, 520, 420), 450, tw(lt, 0, 1.5, 1.4, 1.1)]
    music(S, T(b), "quirky", 0.0)


def a_voice2(S, lt, b):
    pass


def a_drag(S, lt, b):
    c = S["creature"]
    tail_x = c["x"] - 215
    g0, grab = 0.0, 0.9
    if lt < grab:
        gx = tw(lt, g0, grab, -120, tail_x - 6)
        S["glove"] = dict(x=gx, y=E.GROUND - 48, grip=False)
    else:
        dx = tw(lt, grab + 0.3, b.d - 0.2, 0, -560, ease_in)
        c["x"] = 350 + dx
        S["glove"] = dict(x=tail_x + dx - 6 + 0, y=E.GROUND - 48, grip=True)
        if c["x"] < -250:
            S["creature"] = None
            S["glove"] = None
    sfx(S, T(b, grab), "chop", 0.5)
    sfx(S, T(b, grab + 0.3), "stoneshift", 0.6)
    sfx(S, T(b, grab + 1.0), "stoneshift", 0.5)
    a = S["anger"]
    a["px"] = -1
    a["wide"] = 0.8


def a_crunch(S, lt, b):
    S["creature"] = None
    S["glove"] = None
    a = S["anger"]
    a["wide"] = 0.9
    a["px"] = -1
    a["mouth"], a["mamt"] = "flat", 0
    a["blink"] = lt > 2.0
    sfx(S, T(b, 0.4), "crunch", 1.0)
    sfx(S, T(b, 3.4), "crunch", 0.8)
    S["cam"] = [tw(lt, 0, b.d, 420, 600), 450, tw(lt, 0, b.d, 1.1, 1.7)]


def a_no_idea(S, lt, b):
    a = S["anger"]
    a["wide"] = 0.9
    a["px"] = tw(lt, 1.0, 1.5, -1, 0.3)
    a["py"] = tw(lt, 1.0, 1.5, 0, -0.6)


def a_scoot(S, lt, b):
    a = S["anger"]
    a["wide"] = 0.0
    a["px"], a["py"] = -0.5, 0
    a["brow"] = -0.5
    a["mouth"], a["mamt"] = "tight", 1.0
    u = ease(clamp((lt - 0.4) / (b.d - 0.8)))
    a["tilt"] = lerp(-math.pi / 2, -0.12, u)
    a["x"] = lerp(LIE_X, 1005, u) + math.sin(lt * 9) * 3 * (1 - u)
    a["yoff"] = lerp(0, 42, u)
    a["face"] = lerp(0, -0.7, u)
    a["footL"] = (lerp(0, -112, u), lerp(0, -40, u))
    a["footR"] = (lerp(0, -96, u), lerp(0, -42, u))
    a["hl"] = (lerp(-100, -120, u), lerp(-60, -30, u))
    a["hr"] = (lerp(100, 60, u), lerp(-60, -40, u))
    S["cam"] = [tw(lt, 0, b.d, 600, 860), 440, tw(lt, 0, b.d, 1.7, 1.2)]
    for k in range(3):
        sfx(S, T(b, 0.6 + k * 0.9), "stoneshift", 0.4)
        sfx(S, T(b, 0.7 + k * 0.9), "clank", 0.25)
    music(S, T(b), None, 0)


def sitting(a):
    a.update(tilt=-0.12, x=1005, yoff=42, face=-0.7, footL=(-112, -40), footR=(-96, -42))


def a_who(S, lt, b):
    a = S["anger"]
    sitting(a)
    a["mouth"], a["mamt"] = "frown", 0.4
    a["brow"] = -0.6
    a["px"] = -1
    hand(a, -1, (-120, -30), lt, 0, 0.1)
    hand(a, 1, (60, -40), lt, 0, 0.1)
    S["cam"] = [tw(lt, 0, 1, 860, 820), 440, tw(lt, 0, 1, 1.2, 1.5)]


def a_silence(S, lt, b):
    a = S["anger"]
    a["px"] = -1
    a["brow"] = tw(lt, 0.5, 2.0, -0.6, 0.2)
    sfx(S, T(b, 0.6), "drip", 0.8)
    sfx(S, T(b, 2.1), "drip", 0.6)
    sfx(S, T(b, 0.4), "cricket", 0.5)


def a_nap(S, lt, b):
    a = S["anger"]
    a["brow"] = 0.2


def a_eyeroll(S, lt, b):
    a = S["anger"]
    t0, t1 = 0.3, 2.1
    if t0 <= lt <= t1:
        u = (lt - t0) / (t1 - t0)
        ang = math.pi - u * 2 * math.pi * 1.1
        a["px"], a["py"] = math.cos(ang), math.sin(ang) - 0.2
        a["lid"] = 0.25
    else:
        a["px"], a["py"] = (-0.3, -0.8) if lt > t1 else (-1, 0)
    a["mouth"], a["mamt"] = "frown", 0.6
    a["brow"] = -0.4
    S["cam"] = [tw(lt, 0, 0.6, S["cam"][0], 930), 420, tw(lt, 0, 0.6, S["cam"][2], 2.0)]


def a_snore(S, lt, b):
    a = S["anger"]
    a["px"], a["py"] = -1, 0
    a["lid"] = 0.3
    S["zzz"] = 1.0
    S["cam"] = [tw(lt, 0, 1.2, 930, 700), 420, tw(lt, 0, 1.2, 2.0, 1.1)]
    k = 0.0
    while k < TOTAL - b.start - 4:
        sfx(S, T(b, 0.2 + k), "snore", 0.75 if k < 8 else 0.5)
        k += 3.6


def a_choices(S, lt, b):
    a = S["anger"]
    a["px"], a["py"] = -0.3, 0.6
    a["lid"] = 0.4
    a["brow"] = 0.5
    a["mouth"], a["mamt"] = "frown", 0.8
    S["cam"] = [tw(lt, 0, b.d, 760, 900), 430, tw(lt, 0, b.d, 1.1, 1.6)]


def a_thought(S, lt, b):
    a = S["anger"]
    a["px"], a["py"] = 0.2, -0.8
    a["lid"] = 0.3


def a_sleep(S, lt, b):
    a = S["anger"]
    a["px"], a["py"] = 0, 0
    tl = b.vs + b.vd * 0.6
    a["lid"] = tw(lt, tl, tl + 1.4, 0.3, 1.0)
    a["blink"] = False
    a["tilt"] = tw(lt, tl, tl + 1.8, -0.12, -0.24)
    a["mouth"], a["mamt"] = "flat", 0
    a["brow"] = tw(lt, tl, tl + 1.4, 0.5, 0.0)
    S["cam"] = [tw(lt, 0, b.d, 900, 960), 440, tw(lt, 0, b.d, 1.6, 1.9)]
    S["fade"] = tw(lt, b.d - 1.0, b.d, 0, 0.6)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 1.0, 0, 1)
    sfx(S, T(b, 0.1), "hit", 0.8)
    music(S, T(b, 0.4), "epic", 0.7)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Anger is falling.", pre=2.0, post=1.6, min=5.0),
    Beat(a_fall1, "narr", "Down. Down. Into the black.", pre=1.0, post=1.8, id="f1", min=5.0),
    Beat(a_fall2, "narr", "He does not scream. He accepts his fate.", post=1.6),
    Beat(a_refuse, "narr", "And then, something inside him refuses.", post=0.8),
    Beat(a_stab, "anger", "Hraaaagh!", tts="Hraaaaaagh!", pre=0.1, post=1.6, id="stab", min=3.2),
    Beat(a_grind, "narr", "The blade tears through rock and soil, slowing his fall. Just enough.",
         post=0.6, min=5.0),
    Beat(a_impact, min=2.4),
    Beat(a_survives, "narr", "He survives. Barely.", pre=2.2, post=1.2, min=5.0),
    Beat(a_ugh, "anger", "Ugh. Can't... feel my legs.", rate="-25%", gain=0.8, post=1.2),
    Beat(a_aches, "narr", "Every part of him aches. His limbs barely answer. Shadows surround him on "
                          "every side.", post=1.0),
    Beat(a_where, "narr", "How long before he can stand? Where is he?", post=1.2),
    Beat(a_eyes_return, "narr", "And then, the glowing eyes return.", pre=0.4, post=2.4, min=5.0),
    Beat(a_black, min=3.0),
    Beat(a_wakes, "narr", "A noise wakes him.", pre=1.2, post=1.0),
    Beat(a_one_arm, "narr", "He can barely move. One arm. That is all he has left.", post=1.6, min=4.4),
    Beat(a_creeps, "narr", "The creature creeps closer. Teeth dripping. Tongue hanging loose.", post=1.0,
         min=5.0),
    Beat(a_lunge, min=3.4),
    Beat(a_one_eye, "narr", "Anger opens one eye.", pre=0.6, post=1.4),
    Beat(a_what, "anger", "...What?", rate="-10%", post=1.2),
    Beat(a_voice1, "stranger", "You've got to watch out for those things. They'll make you their lunch.",
         pre=0.8, post=0.8),
    Beat(a_voice2, "stranger", "But I'm gonna make it my lunch now.", post=0.4),
    Beat(a_drag, min=3.4),
    Beat(a_crunch, min=5.0),
    Beat(a_no_idea, "narr", "Anger has no idea how to react to this.", post=1.4),
    Beat(a_scoot, "anger", "Nngh.", tts="Nnngh.", rate="-10%", gain=0.7, pre=0.6, post=2.8, min=4.4),
    Beat(a_who, "anger", "Who are you? How did you get here?", post=0.6),
    Beat(a_silence, min=3.2),
    Beat(a_nap, "stranger", "The food was good. But now, a nap sounds even better.", post=0.4),
    Beat(a_eyeroll, min=2.6),
    Beat(a_snore, min=4.0),
    Beat(a_choices, "narr", "Anger stares into the dark, and questions every choice that led him here.",
         post=0.8),
    Beat(a_thought, "anger", "How did I manage to get myself into this?", rate="-12%", gain=0.7,
         post=1.4),
    Beat(a_sleep, "narr", "But as the snoring echoes through the cave, he realizes he might as well get "
                          "some sleep too. Who knows what tomorrow will bring.", post=3.0),
    Beat(a_end, "narr", "To be continued.", pre=1.0, post=2.6, min=5.0),
]


# ------------------------------------------------------------------ drawing
def draw_shaft(ctx, S, t):
    E.src(ctx, "#030303")
    ctx.paint()
    ctx.save()
    cx, cy, z = S["cam"]
    ctx.translate(640, 360)
    ctx.scale(z, z)
    ctx.translate(-cx + math.sin(t * 71) * S["shake"] * 10, -cy + math.cos(t * 59) * S["shake"] * 8)
    off = S["scroll"] % 1440
    strip = G.shaft_strip()
    wall_x = 880
    for k in (-1, 0, 1):
        ctx.set_source_surface(strip, wall_x, -off + k * 1440)
        ctx.paint()
    ctx.move_to(wall_x, -400)
    ctx.line_to(wall_x, 1200)
    E.src(ctx, "#000000", 0.6)
    ctx.set_line_width(14)
    ctx.stroke()
    # far wall on the left, barely visible
    for k in (-1, 0, 1):
        ctx.set_source_surface(strip, -300, -(S["scroll"] * 0.6 % 1440) + k * 1440)
        ctx.paint_with_alpha(0.25)
    a = S["anger"]
    gt = S["groove"]
    if gt is not None:
        hx, hy = G.hand_world(a, 1)
        ctx.move_to(wall_x + 6, hy)
        ctx.line_to(wall_x + 6, -400)
        E.src(ctx, "#0A0605")
        ctx.set_line_width(12)
        ctx.stroke()
        g = cairo.LinearGradient(0, hy, 0, hy - 260)
        g.add_color_stop_rgba(0, 1, 0.6, 0.15, 0.9 * S["sparks"])
        g.add_color_stop_rgba(1, 1, 0.4, 0.1, 0)
        ctx.move_to(wall_x + 6, hy)
        ctx.line_to(wall_x + 6, hy - 260)
        ctx.set_source(g)
        ctx.set_line_width(6)
        ctx.stroke()
    # speed streaks
    rnd = random.Random(5)
    v = 1.0 if gt is None else max(0.2, S["sparks"])
    for i in range(30):
        x = rnd.uniform(60, 860)
        y = (rnd.uniform(0, 900) - S["scroll"] * rnd.uniform(0.6, 1.2)) % 900 - 100
        ctx.move_to(x, y)
        ctx.line_to(x, y + 120 * v)
        E.src(ctx, "#8A8F99", 0.25 * v)
        ctx.set_line_width(2)
        ctx.stroke()
    a2 = dict(a)
    a2["y"] = 520
    a2["tilt"] = math.sin(t * 1.3) * 0.08 if gt is None else 0.05
    E.draw_char(ctx, a2, t)
    if gt is not None and S["sparks"] > 0:
        hx, hy = G.hand_world(a2, 1)
        G.sparks(ctx, wall_x + 4, hy, t, n=int(18 * S["sparks"]) + 4, seed=3, a=S["sparks"])
        G.warm_glow(ctx, wall_x, hy, 160, S["sparks"])
    ctx.restore()
    G.darkness(ctx, 0.35, [(640, 300, 600, 1.0)])


def draw_pit(ctx, S, t):
    a = S["anger"]
    ctx.save()
    apply_cam(ctx, S, t, PIT)
    ctx.set_source_surface(G.pit_bg(), 0, 0)
    ctx.paint()
    G.draw_mushrooms(ctx, t)
    dt0 = S.get("dust_t")
    if dt0 is not None:
        G.dust(ctx, LIE_X, 600, dt0, t, n=12, spread=220, dur=3.0, seed=9, rise=90)
    e = S["eyes"]
    c = S["creature"]
    if c:
        G.draw_creature(ctx, c["x"], c["y"], c["s"], c["face"], t, c)
    E.draw_char(ctx, a, t)
    r = S["rock"]
    if r and r["t0"] <= t:
        if t < r["t1"]:
            u = (t - r["t0"]) / (r["t1"] - r["t0"])
            x = lerp(r["x0"], r["x1"], u)
            y = lerp(r["y0"], r["y1"], u) - math.sin(u * math.pi) * 140
        else:
            dt = t - r["t1"]
            x = r["x1"] - 160 * dt
            y = r["y1"] - 260 * dt + 900 * dt * dt
            y = min(y, E.GROUND - 8)
        if t < r["t1"] + 2.5:
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(t * 8)
            E.ellipse(ctx, 0, 0, 16, 12)
            E.fill_stroke(ctx, "#6A615A", "#1A1512", 3)
            ctx.restore()
    kt = S.get("ko_t")
    if kt is not None and kt <= t < kt + 0.5:
        E.draw_burst(ctx, dict(kind="pop", x=r["x1"], y=r["y1"] - 10, t=kt), t)
    lights = [(x, y - 30, 260 * s, 0.8) for x, y, s in G.MUSHROOMS]
    lights.append((a["x"] - 40, a["y"] - 120, 360, 0.55))
    if c:
        lights.append((c["x"] + 60, c["y"] - 60, 220, 0.35))
    G.darkness(ctx, S["amb"], lights, tint=(0.0, 0.01, 0.02))
    # the dark mouth on the left stays black
    g = cairo.LinearGradient(0, 0, 380, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.9)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.rectangle(-200, -200, 580, 1100)
    ctx.set_source(g)
    ctx.fill()
    if S["glove"]:
        gl = S["glove"]
        G.draw_glove_arm(ctx, gl["x"], gl["y"], t, from_x=-260, grip=gl["grip"])
    if e:
        G.glowing_eyes(ctx, e["x"], e["y"], e["a"], t, 0.9, e["look"])
    if c and c.get("glow", 0) > 0 and c.get("ko", 0) < 0.5:
        G.glowing_eyes(ctx, c["x"] + 96, c["y"] - 72, 0.5, t, 0.55)
    if S["zzz"] > 0:
        G.zzz(ctx, 130, 420, t, S["zzz"])
    ctx.restore()
    if S["blur"] > 0:
        g = cairo.RadialGradient(640, 360, 120, 640, 360, 700)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.9 * S["blur"])
        ctx.set_source(g)
        ctx.paint()


def draw(ctx, S, t):
    if S["scene"] == "shaft":
        draw_shaft(ctx, S, t)
    else:
        draw_pit(ctx, S, t)
    if S["flash"] > 0:
        ctx.set_source_rgba(1, 1, 1, S["flash"])
        ctx.paint()
    G.vignette(ctx, 0.55)
    if S["card"] > 0:
        G.title_card(ctx, t, "ANGER", "Part Two: The Fall", S["card"])
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
    if S["endcard"] > 0:
        G.end_card(ctx, t, "To Be Continued", "Part Three: The Roommates", S["endcard"])
        S["subs"] = False
