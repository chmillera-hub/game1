"""Part 3: The Roommates."""
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
SIT_X = 1005
FACE = (978, 470)       # Anger's face while sitting (world)


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
    S["scene"] = "pit"
    a = G.new_warrior(SIT_X, itemL=None, itemR=None, hurt=0.8, cape_lift=0)
    a.update(tilt=-0.24, yoff=42, face=-0.7, footL=(-112, -40), footR=(-96, -42), lid=1.0, blink=False,
             mouth="flat", mamt=0, brow=0.0)
    a["hl"] = (-120, -30)
    a["hr"] = (60, -40)
    S["anger"] = a
    S["beast"] = dict(x=860, y=E.GROUND, s=0.9, tilt=0.4, mouth="tongue", tongue_len=0.75, tdy=45, eyes="beady",
                      arms="down", visible=False)
    S["drips"] = []
    S["card"] = 1.0
    S["amb"] = 0.78
    S["zzz"] = 0.0
    S["wet"] = 0.0
    S["pebbles"] = []
    return S


def stranger_voice_dir(a):
    a["px"] = -1.0
    a["py"] = 0.0


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    ambience(S, TOTAL)
    sfx(S, T(b, 0.4), "hit", 0.6)
    music(S, T(b), "drone", 0.5)
    S["cam"] = [900, 430, 1.5]


def a_morning(S, lt, b):
    S["card"] = tw(lt, 0, 1.0, 1.0, 0.0)
    cam_to(S, lt, 0, b.d, 960, 450, 2.0)


def drip(S, t_abs, b):
    """A drop falls from the tongue tip to Anger's cheek."""
    S["drips"].append(dict(t0=t_abs, t1=t_abs + 0.55))
    sfx(S, t_abs + 0.55, "drool", 0.9)


def a_drip1(S, lt, b):
    a = S["anger"]
    cam_to(S, lt, 0, 1.0, 975, 455, 2.4)
    td = b.vs + b.vd + 0.2
    drip(S, T(b, td), b)
    hit = td + 0.55
    if lt > hit:
        S["wet"] = 1.0
        hand(a, -1, (-24, -170), lt, hit + 0.2, hit + 0.5)
        if hit + 0.5 < lt < hit + 1.4:
            a["hl"] = (-24 + math.sin((lt - hit) * 16) * 16, -170)
        if lt > hit + 1.4:
            hand(a, -1, (-120, -30), lt, hit + 1.4, hit + 1.8)
        a["brow"] = 0.4 if lt < hit + 1.6 else 0.0
        a["mouth"], a["mamt"] = ("frown", 0.4) if lt < hit + 1.6 else ("flat", 0)


def a_drip2(S, lt, b):
    a = S["anger"]
    drip(S, T(b, 0.3), b)
    hit = 0.85
    if lt > hit:
        hand(a, -1, (-24, -170), lt, hit + 0.1, hit + 0.4)
        if hit + 0.4 < lt < hit + 1.1:
            a["hl"] = (-24 + math.sin((lt - hit) * 16) * 16, -170)
        if lt > hit + 1.1:
            hand(a, -1, (-120, -30), lt, hit + 1.1, hit + 1.5)
        a["brow"] = -0.4
        a["mouth"], a["mamt"] = "frown", 0.7
    # one tired eye cracks open and looks up
    if lt > 2.0:
        a["lidL"] = 1.0
        a["lidR"] = tw(lt, 2.0, 2.6, 1.0, 0.45)
        a["px"], a["py"] = -0.4, -1.0


def a_tongue(S, lt, b):
    a = S["anger"]
    S["beast"]["visible"] = True
    a["lidL"] = 1.0
    a["lidR"] = tw(lt, 0.4, 1.0, 0.45, 0.0)
    a["px"], a["py"] = -0.5, -1.0
    a["wide"] = tw(lt, 0.6, 1.2, 0, 0.5)
    cam_to(S, lt, 0, 1.6, 950, 410, 2.0)
    drip(S, T(b, 0.6), b)
    drip(S, T(b, 2.4), b)


def a_startle(S, lt, b):
    a = S["anger"]
    bb = S["beast"]
    bb["visible"] = True
    a["lidL"], a["lidR"] = None, None
    a["lid"] = 0.0
    a["blink"] = True
    a["wide"] = tw(lt, 0, 0.15, 0.5, 1.5)
    a["brow"] = 1.2
    a["mouth"], a["mamt"] = "o", 1.0
    a["yoff"] = 42 - math.sin(clamp(lt / 0.4) * math.pi) * 40
    a["tilt"] = tw(lt, 0, 0.3, -0.24, -0.05)
    a["px"], a["py"] = -1.0, -0.8
    hand(a, -1, (-110, -200), lt, 0, 0.2)
    hand(a, 1, (90, -190), lt, 0, 0.2)
    cam_to(S, lt, 0.1, 1.2, 860, 380, 1.15, ease_out)
    sfx(S, T(b, 0.0), "hit", 0.8)
    sfx(S, T(b, 0.05), "stoneshift", 0.4)
    music(S, T(b, 1.0), "quirky", 0.8)


def a_reveal_n(S, lt, b):
    a = S["anger"]
    a["wide"] = 1.2
    a["mouth"], a["mamt"] = "o", 0.8
    a["py"] = -1.0
    bb = S["beast"]
    cam_to(S, lt, 0, b.d, 760, 300, 1.5)
    if lt > b.vs + b.vd * 0.55:
        bb["px"] = 0.5
    sfx(S, T(b, b.vs + b.vd * 0.8), "drool", 0.6)


def a_what_hell(S, lt, b):
    a = S["anger"]
    a["wide"] = 1.0
    a["brow"] = 0.6
    a["mouth"] = "frown"
    hand(a, -1, (-110, -150), lt, 0, 0.4)
    hand(a, 1, (60, -80), lt, 0, 0.4)


def a_friend(S, lt, b):
    a = S["anger"]
    bb = S["beast"]
    a["wide"] = tw(lt, 0, 0.6, 1.0, 0.3)
    a["px"] = -1.0
    a["py"] = tw(lt, 0, 0.5, -0.8, -0.3)
    tl = b.vs + b.vd * 0.35
    if lt > tl and lt < b.d - 0.2:
        bb["arms"] = "wave"
    bb["eyes"] = "happy" if lt > tl else "beady"
    sfx(S, T(b, b.vs + b.vd * 0.4), "drool", 0.5)


def a_space(S, lt, b):
    a = S["anger"]
    a["x"] = tw(lt, 0, 0.8, SIT_X, SIT_X + 18)
    a["tilt"] = tw(lt, 0, 0.8, -0.05, -0.22)
    a["lid"] = 0.45
    a["brow"] = -0.7
    a["wide"] = 0
    a["px"], a["py"] = -1.0, -0.6
    hand(a, -1, (-90, -150), lt, 0, 0.5)
    S["beast"]["eyes"] = "beady"
    S["beast"]["arms"] = "down"
    cam_to(S, lt, 0, 1.0, 900, 420, 1.35)


def a_sass(S, lt, b):
    bb = S["beast"]
    a = S["anger"]
    a["lid"] = 0.3
    hand(a, -1, (-120, -30), lt, 0, 0.5)
    bb["eyes"] = "side"
    bb["px"] = 1.0
    bb["mouth"] = "frown"
    t_cross = 0.8
    if lt > t_cross:
        bb["arms"] = "crossed"
    bb["tilt"] = tw(lt, 0, 0.6, 0.4, 0.0)
    steps = [1.6, 2.4, 3.2]
    x = 860
    for k, ts in enumerate(steps):
        if lt > ts - 0.4:
            x = tw(lt, ts - 0.4, ts, 860 - k * 110, 860 - (k + 1) * 110)
            if lt < ts:
                bb["tilt"] = 0.12 * (1 if k % 2 else -1) * math.sin((lt - ts + 0.4) / 0.4 * math.pi)
        if ts <= lt < ts + 0.25:
            bb["sq"] = 1 - 0.06 * math.sin((lt - ts) / 0.25 * math.pi)
            S["shake"] = 0.8 * (1 - (lt - ts) / 0.25)
        sfx(S, T(b, ts), "stompbig", 0.9)
        S["pebbles"].append(T(b, ts))
    bb["x"] = x
    cam_to(S, lt, 0, 1.0, 820, 380, 1.1)


def a_respect(S, lt, b):
    bb = S["beast"]
    bb["x"] = 530
    bb["eyes"] = "side"
    bb["px"] = 1.0
    bb["arms"] = "crossed"
    bb["mouth"] = "frown"
    a = S["anger"]
    stranger_voice_dir(a)
    a["lid"] = 0.2


def a_wipe(S, lt, b):
    a = S["anger"]
    t0, t1 = 0.2, 2.0
    if t0 <= lt <= t1:
        u = (lt - t0) / (t1 - t0)
        ang = math.pi - u * 2 * math.pi
        a["px"], a["py"] = math.cos(ang), math.sin(ang) - 0.2
    else:
        a["px"], a["py"] = (0.2, -0.6) if lt > t1 else (-1, 0)
    a["lid"] = 0.3
    hand(a, -1, (-30, -160), lt, 0.2, 0.6)
    if 0.6 < lt < 2.4:
        a["hl"] = (-30 + math.sin(lt * 14) * 14, -160 + math.cos(lt * 14) * 8)
    if lt > 2.4:
        hand(a, -1, (-120, -30), lt, 2.4, 2.8)
        S["wet"] = tw(lt, 0.6, 2.4, 1.0, 0.0)
    a["mouth"], a["mamt"] = "frown", 0.6
    cam_to(S, lt, 0, 0.6, 960, 450, 1.9)


def a_awkward(S, lt, b):
    a = S["anger"]
    bb = S["beast"]
    S["wet"] = 0
    bb["eyes"] = "squint"
    bb["arms"] = "crossed"
    bb["tap"] = 1.0
    bb["mouth"] = "frown"
    a["px"], a["py"] = 0.9, -0.7
    a["lid"] = 0.2
    a["mouth"], a["mamt"] = "flat", 0
    for k in range(int(b.d / 0.35)):
        sfx(S, T(b, k * 0.35), "tap", 0.6)
    sfx(S, T(b, 0.3), "cricket", 0.7)
    music(S, T(b), None, 0)
    # three shots: wide, the beast's squint, Anger looking anywhere else
    if lt < 2.2:
        S["cam"] = [820, 380, 1.1]
    elif lt < 4.6:
        S["cam"] = [520, 300, 2.2]
    else:
        S["cam"] = [985, 450, 2.4]
    if lt > 5.6:
        a["px"] = tw(lt, 5.6, 5.8, 0.9, -1.0)
        a["py"] = tw(lt, 5.6, 5.8, -0.7, 0.0)
    if lt > 6.0:
        a["px"] = tw(lt, 6.0, 6.2, -1.0, 0.9)
        a["py"] = tw(lt, 6.0, 6.2, 0.0, -0.7)


def a_so(S, lt, b):
    a = S["anger"]
    bb = S["beast"]
    bb["tap"] = 0
    bb["eyes"] = "beady"
    a["px"], a["py"] = -1.0, 0
    a["brow"] = -0.3
    S["cam"] = [tw(lt, 0, 0.4, 985, 860), tw(lt, 0, 0.4, 450, 400), tw(lt, 0, 0.4, 2.4, 1.2)]
    music(S, T(b, 0.2), "quirky", 0.6)


def a_laugh1(S, lt, b):
    a = S["anger"]
    bb = S["beast"]
    bb["eyes"] = "happy"
    bb["px"] = -1
    bb["mouth"] = "grin"
    bb["arms"] = "down"
    bb["shake"] = 3.0
    music(S, T(b), None, 0)
    a["brow"] = tw(lt, 1.0, 1.6, -0.3, 0.6)
    a["lid"] = 0.2
    stranger_voice_dir(a)
    cam_to(S, lt, 0, b.d, 900, 430, 1.4)


def a_laugh2(S, lt, b):
    a = S["anger"]
    hand(a, -1, (30, -70), lt, 0.2, 0.8)
    hand(a, 1, (-40, -60), lt, 0.2, 0.8)
    a["lid"] = 0.35
    a["mouth"], a["mamt"] = "flat", 0
    cam_to(S, lt, 0, b.d, 975, 450, 2.1)


def a_laugh3(S, lt, b):
    S["beast"]["shake"] = 0
    S["beast"]["eyes"] = "beady"
    a = S["anger"]
    a["brow"] = 0.8
    a["lid"] = 0.4


def a_stuck(S, lt, b):
    a = S["anger"]
    a["brow"] = tw(lt, 0, 0.6, 0.8, -0.2)
    a["lid"] = 0.3
    cam_to(S, lt, 0, 1.0, 880, 410, 1.3)


def a_die(S, lt, b):
    a = S["anger"]
    a["lid"] = 0.35
    a["brow"] = 0.0
    a["px"], a["py"] = 0.5, 0.0
    cam_to(S, lt, 0, 0.6, 975, 450, 2.2)


def a_snort(S, lt, b):
    bb = S["beast"]
    a = S["anger"]
    a["px"] = -1
    bb["mouth"] = "snort" if lt < 0.4 else "grin"
    bb["eyes"] = "wide" if lt < 0.4 else "happy"
    if lt > 0.4:
        bb["arms"] = "both_mouth"
        bb["shake"] = 2.5
        bb["blush"] = 1.0
    sfx(S, T(b, 0.1), "snort", 1.0)
    sfx(S, T(b, 0.9), "snort", 0.4)
    sfx(S, T(b, 1.7), "snort", 0.3)
    cam_to(S, lt, 0, 0.5, 600, 300, 1.6)


def a_smirk(S, lt, b):
    a = S["anger"]
    cam_to(S, lt, 0, 0.6, 975, 455, 2.6)
    ts, tn = 0.8, 2.4
    a["mouth"], a["mamt"] = ("smirk", tw(lt, ts, ts + 0.6, 0.0, 0.45)) if lt < tn else ("flat", 0)
    if lt > tn - 0.4:
        a["px"], a["py"] = 0.0, 0.8
        a["wide"] = 0.6
    if lt > tn + 0.3:
        a["wide"] = 0


def a_ahem(S, lt, b):
    a = S["anger"]
    hand(a, -1, (-14, -150), lt, 0, 0.25)
    a["wide"] = 0
    a["px"], a["py"] = 0.6, 0.0
    if lt > b.vs + b.vd + 0.2:
        hand(a, -1, (-120, -30), lt, b.vs + b.vd + 0.2, b.vs + b.vd + 0.6)
        a["brow"] = -0.8
        a["mouth"], a["mamt"] = "frown", 0.4
        a["px"] = -1.0


def a_almost(S, lt, b):
    a = S["anger"]
    a["brow"] = -0.8
    a["mouth"], a["mamt"] = "frown", 0.4
    cam_to(S, lt, 0, b.d, 820, 380, 1.1)
    music(S, T(b, 0.5), "quirky", 0.7)
    bb = S["beast"]
    bb["shake"] = 0
    bb["arms"] = "down"
    bb["eyes"] = "beady"
    bb["blush"] = 0.6


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 1.0, 0, 1)
    music(S, T(b, 0.2), "epic", 0.7)
    sfx(S, T(b, 0.2), "hit", 0.6)


# ------------------------------------------------------------------ script
LAUGH1 = "Ha! Ha ha ha ha! Ha ha ha ha ha ha!"
LAUGH2 = "Ho ho ho! Ha ha ha ha ha ha ha ha!"
LAUGH3 = "Hoo! Oh, wow. Ha ha. Oh, that's a good one."

BEATS = [
    Beat(a_title, "narr", "Somewhere deep underground, morning arrives. Or something close to it.",
         pre=2.0, post=1.0, min=6.0),
    Beat(a_morning, "narr", "Anger sleeps.", pre=0.8, post=2.2, min=4.0),
    Beat(a_drip1, "narr", "Something drips onto his cheek.", post=3.4),
    Beat(a_drip2, min=4.0),
    Beat(a_tongue, "narr", "He looks up.", pre=0.6, post=2.8, min=4.2),
    Beat(a_startle, min=2.6),
    Beat(a_reveal_n, "narr", "Standing over him is the biggest, roundest creature he has ever seen. "
                             "Beady little eyes. And a very dumb grin.", post=1.0),
    Beat(a_what_hell, "anger", "What the hell are you?!", rate="+4%", post=0.8),
    Beat(a_friend, "stranger", "That's my friend. He's saying hi. I think he likes you.", pre=0.4,
         post=0.8),
    Beat(a_space, "anger", "Tell your friend to give me a little space. Please.", post=0.8),
    Beat(a_sass, "narr", "The beast does not appreciate that tone.", pre=0.4, post=2.0, min=4.6),
    Beat(a_respect, "stranger", "Hey! He can hear you, buddy. Treat him with some respect. We go way "
                                "back, okay?", post=0.4),
    Beat(a_wipe, min=3.4),
    Beat(a_awkward, min=7.6),
    Beat(a_so, "anger", "So. How are you two planning to get out of here?", pre=0.3, post=0.8),
    Beat(a_laugh1, "stranger", LAUGH1, rate="+0%", post=0.2),
    Beat(a_laugh2, "stranger", LAUGH2, rate="+0%", post=0.6),
    Beat(a_laugh3, "stranger", LAUGH3, post=0.8),
    Beat(a_stuck, "stranger", "We would have gotten out of here a long time ago if we could have. But now "
                              "it seems you're stuck in here with us. How do you feel about that?",
         post=1.4),
    Beat(a_die, "anger", "Well. I guess I'll die then.", rate="-12%", post=0.6),
    Beat(a_snort, min=2.8),
    Beat(a_smirk, min=3.4),
    Beat(a_ahem, "anger", "Ahem.", post=1.2),
    Beat(a_almost, "narr", "And for just a moment, Anger almost smiled. Almost.", pre=0.4, post=2.2),
    Beat(a_end, "narr", "The End. For now.", pre=1.0, post=2.6, min=5.0),
]


# ------------------------------------------------------------------ drawing
def draw(ctx, S, t):
    a = S["anger"]
    bb = S["beast"]
    ctx.save()
    apply_cam(ctx, S, t, PIT)
    ctx.set_source_surface(G.pit_bg(), 0, 0)
    ctx.paint()
    G.draw_mushrooms(ctx, t)
    if bb["visible"]:
        G.draw_beast(ctx, bb["x"], bb["y"], bb["s"], t, bb)
    for pt in S["pebbles"]:
        G.debris(ctx, 700, E.GROUND - 5, pt, t, n=6, seed=int(pt * 10), vx=(-200, 200), vy=(-260, -120),
                 floor=E.GROUND + 4, size=(3, 7), g=1400)
    E.draw_char(ctx, a, t)
    # drool drops
    tipx, tipy = G.beast_tongue_tip(bb["x"], bb["y"], bb["s"], bb)
    for d in S["drips"]:
        if d["t0"] <= t < d["t1"]:
            u = (t - d["t0"]) / (d["t1"] - d["t0"])
            if not bb["visible"]:
                tipx, tipy = FACE[0] - 30, FACE[1] - 230
            x = lerp(tipx, FACE[0] - 16, u)
            y = lerp(tipy + 8, FACE[1] + 6, u * u)
            E.ellipse(ctx, x, y, 5, 7)
            E.src(ctx, "#BFEFFF", 0.9)
            ctx.fill()
        elif d["t1"] <= t < d["t1"] + 0.4:
            E.draw_burst(ctx, dict(kind="ding", x=FACE[0] - 16, y=FACE[1] + 6, t=d["t1"]), t)
    if S["wet"] > 0:
        E.ellipse(ctx, FACE[0] - 18, FACE[1] + 10, 10, 6)
        E.src(ctx, "#BFEFFF", 0.7 * S["wet"])
        ctx.fill()
    lights = [(x, y - 30, 260 * s, 0.8) for x, y, s in G.MUSHROOMS]
    lights.append((a["x"] - 40, a["y"] - 120, 380, 0.6))
    if bb["visible"]:
        lights.append((bb["x"], bb["y"] - 260, 380, 0.6))
    G.darkness(ctx, S["amb"], lights, tint=(0.0, 0.01, 0.02))
    g = cairo.LinearGradient(0, 0, 380, 0)
    g.add_color_stop_rgba(0, 0, 0, 0, 0.9)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    ctx.rectangle(-200, -200, 580, 1100)
    ctx.set_source(g)
    ctx.fill()
    if S["zzz"] > 0:
        G.zzz(ctx, 130, 420, t, S["zzz"])
    ctx.restore()
    G.vignette(ctx, 0.5)
    if S["card"] > 0:
        G.title_card(ctx, t, "ANGER", "Part Three: The Roommates", S["card"])
    if S["endcard"] > 0:
        G.end_card(ctx, t, "The End", "...for now", S["endcard"])
        S["subs"] = False
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
