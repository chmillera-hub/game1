"""Episode 1: The Heist."""
import math

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import mgfx as M
from mcommon import (sfx, hand, walk, cam_to, mus, base_state, T, VEND, place, stare, draw_world,
                     overlays, GROUND)
from show import Beat

TOTAL = 0.0
IDX = {}
PED = 820
STAND = 215
SLOTS = [(-30, "#7CFF5A"), (0, "#FF5AA0"), (30, "#5EC8E8")]
DX = 490  # where Doubt sweeps


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def init_state():
    S = base_state()
    S["boredom"] = M.new_boredom(330)
    S["doubt"] = M.new_doubt(1060, mouth="smile", mamt=0.3, itemR="book")
    S["doubt"]["hr"] = (48, -96)
    S["doubt"]["broomdir"] = -1
    S["vex"] = M.new_char("vex", -200)
    S["props"] = {"@ped": draw_ped, "@stand": draw_stand, "@flasks": draw_flasks}
    S["show"] = ["@stand", "@ped", "boredom", "doubt", "@flasks"]
    S["flasks"] = [dict(), dict(), dict()]
    S["card"] = 1.0
    S["vial"] = dict(mode="ped", x=PED, y=GROUND - 180, ang=0.0)
    return S


def draw_ped(ctx, S, t):
    M.pedestal(ctx, PED)
    v = S["vial"]
    if v["mode"] in ("ped", "air"):
        M.draw_vial(ctx, v["x"], v["y"], v["ang"], t)


def slot_pos(i):
    return STAND + SLOTS[i][0], GROUND - 120


def draw_stand(ctx, S, t):
    M.flask_stand(ctx, STAND)
    for i, f in enumerate(S["flasks"]):
        x, y = slot_pos(i)
        if f.get("ts") is None or t < f["ts"] or (f.get("back") is not None and t >= f["back"] + 0.6):
            M.flask(ctx, x, y, 0.0, SLOTS[i][1])


def draw_flasks(ctx, S, t):
    if S["fx"].get("lean"):
        ctx.save()
        ctx.translate(DX - 75, GROUND)
        ctx.rotate(0.25)
        M._broom_item(ctx, 0, -110, 0, dict(face=0.0, broomdir=1), t)
        ctx.restore()
    for i, f in enumerate(S["flasks"]):
        ts = f.get("ts")
        if ts is None or t < ts:
            continue
        sx, sy = slot_pos(i)
        col = SLOTS[i][1]
        lx = f["land"]
        if t < ts + 0.55:
            u = (t - ts) / 0.55
            M.flask(ctx, lerp(sx, lx, u), lerp(sy, GROUND - 14, u * u) - math.sin(u * math.pi) * 60, u * 6, col)
            continue
        if f["kind"] == "shatter":
            sw0, swd = f.get("sweep", (1e9, 1.0))
            tt = min(t, f.get("freeze", 1e9))
            M.shards(ctx, lx, 1 - clamp((tt - sw0) / swd), seed=i)
            continue
        # bounce -> Doubt catches it without looking -> tosses it back onto the stand
        cx, cy = f["catch"]
        if t < ts + 0.95:
            u = (t - ts - 0.55) / 0.4
            M.flask(ctx, lerp(lx, cx, u), lerp(GROUND - 14, cy, u) - math.sin(u * math.pi) * 50, 6 + u * 3, col)
        elif t < f["back"]:
            d = S["doubt"]
            M.flask(ctx, d["x"] + d["hl"][0] * d["s"], d["y"] + d["yoff"] + d["hl"][1] * d["s"] - 10, 0.0, col)
        elif t < f["back"] + 0.6:
            u = (t - f["back"]) / 0.6
            M.flask(ctx, lerp(cx, sx, u), lerp(cy, sy, u) - math.sin(u * math.pi) * 120, u * 6.28, col)


def knock(S, b, lt, i, off, kind, land):
    """Boredom bumps flask i off the stand at beat offset `off`."""
    f = S["flasks"][i]
    f.update(ts=T(b, off), kind=kind, land=land)
    if off - 0.3 < lt < off + 0.15:
        # an accidental backhand while working the machine: the flask flies off past him
        u = clamp((lt - off + 0.3) / 0.35)
        S["boredom"]["hl"] = (lerp(-130, -30, u), -104 - math.sin(u * math.pi) * 10)
    sfx(S, T(b, off), "tink", 0.6)
    if kind == "shatter":
        sfx(S, T(b, off + 0.55), "shatter", 0.9)
    else:
        sfx(S, T(b, off + 0.55), "boing", 0.7)
        sfx(S, T(b, off + 0.95), "tap", 0.6)
    return f


def sweeping(d, lt, on=True):
    d["itemR"] = "broom"
    if on:
        d["hr"] = (-12 + math.sin(lt * 7) * 18, -92)
        d["hl"] = (-2 + math.sin(lt * 7) * 14, -128)
    d["face"], d["px"] = -0.6, -1
    d["lid"] = 0.35
    d["mouth"], d["mamt"] = "flat", 0.0


def sweep_sfx(S, b, t0, t1):
    k = t0
    while k < t1:
        sfx(S, T(b, k), "sweep", 0.35)
        k += 0.9


def frantic(b_, lt):
    """Boredom yanking levers and twisting knobs."""
    b_["hl"] = (-80 + math.sin(lt * 9) * 30, -120 + math.cos(lt * 7) * 40)
    b_["hr"] = (-60 + math.cos(lt * 8) * 30, -90 + math.sin(lt * 11) * 40)
    b_["face"], b_["px"] = -0.6, -1
    b_["yoff"] = -abs(math.sin(lt * 10)) * 8
    b_["lid"] = 0.0
    b_["wide"] = 0.6
    b_["mouth"], b_["mamt"] = "smile", 0.9


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    mus(S, T(b), "lab", 0.75, 0.6, 0.02)


def a_meet_boredom(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1, 0)
    frantic(S["boredom"], lt)
    S["fx"]["dial"] = 0.5 + 0.5 * clamp(lt / b.d)
    S["cam"] = [400, 380, tw(lt, 0, b.d, 1.0, 1.3)]
    for k in range(int(b.d / 0.6)):
        sfx(S, T(b, 0.3 + k * 0.6), "tink", 0.25)


def a_mutter(S, lt, b):
    frantic(S["boredom"], lt)
    knock(S, b, lt, 0, 1.6, "shatter", 420)
    S["fx"]["dial"] = 1.0
    S["cam"] = [330, 360, 1.5]


def a_dweeb(S, lt, b):
    d = S["doubt"]
    d.update(face=0.0, px=0.0, py=0.0)
    t0, t1 = 0.0, 1.0
    if lt < t1:
        u = lt / t1
        ang = math.pi - u * 2 * math.pi
        d["px"], d["py"] = math.cos(ang), math.sin(ang) - 0.2
    d["lid"] = 0.35
    d["mouth"], d["mamt"] = "smirk", 0.7
    hand(d, -1, (-80, -150), lt, 1.0, 1.4)
    S["cam"] = [1060, 380, 1.6]
    frantic(S["boredom"], lt)


def a_meet_doubt(S, lt, b):
    d, bo = S["doubt"], S["boredom"]
    frantic(bo, lt)
    hand(d, -1, "rest", lt, 0, 0.3)
    d["lid"] = 0.2
    d["face"], d["px"] = -0.6, -1
    d["itemR"] = "broom"
    d["hr"], d["hl"] = (-12, -92), (-2, -128)
    walk(d, DX, lt, 0.4, 2.6, 0.7)
    if lt > 2.6:
        sweeping(d, lt)
        S["flasks"][0]["sweep"] = (T(b, 2.8), 1.8)
        sweep_sfx(S, b, 2.8, 4.6)
    S["cam"] = [tw(lt, 0, 2.5, 1060, 520), 380, tw(lt, 0, 2.5, 1.6, 1.1)]


def a_works(S, lt, b):
    d, bo = S["doubt"], S["boredom"]
    frantic(bo, lt)
    sweeping(d, lt)
    f = knock(S, b, lt, 1, 0.8, "bounce", 430)
    f["catch"] = (d["x"] - 50, GROUND - 130)
    f["back"] = T(b, 2.6)
    if 1.0 < lt < 2.75:
        # catches the flask with her free hand, still looking bored
        hand(d, -1, (-50, -130), lt, 1.0, 1.35)
        if lt > 2.3:
            hand(d, -1, (-60, -170), lt, 2.3, 2.6)
    sfx(S, T(b, 2.6), "whoosh", 0.4)
    sfx(S, T(b, 3.2), "tink", 0.6)
    tb = b.vs + b.vd * 0.7
    if lt > tb:
        bo.update(yoff=0, wide=1.0, mouth="laugh", mamt=0.8)
        bo["hl"] = (-60, -200)
        bo["hr"] = (60, -200)
        S["fx"]["burst"] = T(b, tb)
    sfx(S, T(b, tb), "tada", 0.6)
    sfx(S, T(b, tb), "sparkle", 0.6)
    S["cam"] = [560, 360, 1.0]


def a_hello(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    S["show"] = ["@stand", "@ped", "boredom", "doubt", "vex", "@flasks"]
    frantic(bo, lt)
    sweeping(d, lt)
    f = knock(S, b, lt, 2, 0.6, "shatter", 410)
    f["sweep"] = (T(b, 1.4), 9.0)
    sweep_sfx(S, b, 1.4, b.d)
    place(v, tw(lt, 0, 1.4, 1400, 720), -0.4, -1, mouth="smile", mamt=0.8, brow=-0.6)
    v["walking"] = 1.2 if lt < 1.4 else 0
    if lt > 1.4:
        hand(v, -1, "wave", lt, 1.4, 1.7)
        v["hl"] = (v["hl"][0] - math.sin(lt * 12) * 14, v["hl"][1])
    sfx(S, T(b, 0.1), "door", 0.9)
    S["cam"] = [600, 380, 1.0]


def a_guys(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    frantic(bo, lt)
    sweeping(d, lt)
    sweep_sfx(S, b, 0.0, b.d)
    v["hl"] = (-80 + math.sin(lt * 10) * 20, -200)
    v["hr"] = (80 - math.sin(lt * 10) * 20, -200)
    v["yoff"] = -abs(math.sin(lt * 6)) * 14


def a_stare(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    stare(bo)
    stare(d)
    bo["hl"], bo["hr"] = E.pose("boredom", -1, "rest"), E.pose("boredom", 1, "rest")
    d["hr"], d["hl"] = (-12, -92), (-2, -128)  # frozen mid-sweep
    S["flasks"][2]["freeze"] = T(b)
    mus(S, T(b, 0.0), None, 0)
    sfx(S, T(b, 0.0), "scratch", 0.6)
    v["hl"], v["hr"] = (-80, -200), (80, -200)
    v["yoff"] = 0
    v["wide"] = tw(lt, 0.3, 0.5, 0, 1.0)
    v["mouth"], v["mamt"] = "o", 0.6
    if lt > 1.2:
        v["px"] = math.sin((lt - 1.2) * 4) * 1.0
    S["cam"] = [620, 380, tw(lt, 0, b.d, 1.0, 1.2)]


def frozen(S, lt):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    stare(bo)
    stare(d)
    v["wide"] = 1.0
    v["sweat"] = 1.0


def a_why(S, lt, b):
    frozen(S, lt)
    v = S["vex"]
    v["px"] = math.sin(lt * 3) * 1.0
    hand(S["vex"], -1, "rest", lt, 0, 0.4)
    hand(S["vex"], 1, "rest", lt, 0, 0.4)


def a_here_to(S, lt, b):
    frozen(S, lt)
    v = S["vex"]
    v["px"] = 0
    hand(v, 1, (30, -150), lt, 0, 0.4)
    v["mouth"], v["mamt"] = "wavy", 1.0
    S["cam"] = [700, 360, tw(lt, 0, b.d, 1.2, 1.5)]


def a_silence(S, lt, b):
    frozen(S, lt)
    S["cam"] = [700, 360, 1.5]


def a_steal(S, lt, b):
    frozen(S, lt)


def a_boss(S, lt, b):
    frozen(S, lt)
    v = S["vex"]
    mus(S, T(b, 0.0), "boss", 0.8, 0.02, 0.05)
    v["shake"] = 1.5
    v["mouth"], v["mamt"] = "o", 1.0
    v["px"] = math.sin(lt * 6)
    S["cam"] = [640, 380, tw(lt, 0, 0.6, 1.5, 1.0)]


def a_oh_no(S, lt, b):
    frozen(S, lt)
    S["vex"]["shake"] = 1.5


def a_sidle(S, lt, b):
    frozen(S, lt)
    v = S["vex"]
    v["shake"] = 1.0
    v["face"], v["px"] = 0.5, 1
    walk(v, 760, lt, 0.2, 2.0, 0.4)
    lift = 2.6
    if lt > 2.2:
        hand(v, 1, (70, -170), lt, 2.2, 2.6)
    if lift < lt < lift + 1.4:
        S["vial"]["y"] = GROUND - 180 - 6
        mus(S, T(b, lift), "boss", 1.0, 0.05, 0.05)
        v["shake"] = 3.0
    elif lt >= lift + 1.4:
        S["vial"]["y"] = GROUND - 180
        mus(S, T(b, lift + 1.4), "boss", 0.8, 0.05, 0.05)
        hand(v, 1, "rest", lt, lift + 1.4, lift + 1.8)
    sfx(S, T(b, lift), "sting", 0.6)
    S["cam"] = [740, 400, tw(lt, 0, 2.0, 1.0, 1.4)]


def a_fumble(S, lt, b):
    frozen(S, lt)
    v, vi = S["vex"], S["vial"]
    v["shake"] = 1.2
    hand(v, 1, (70, -170), lt, 0, 0.3)
    up = 0.4
    f0 = IDX["fum"].start
    span = IDX["dive"].start - f0
    lta = S["t"] - f0
    if lta > up:
        vi["mode"] = "air"
        u = clamp((lta - up) / (span - up))
        vi["x"] = lerp(PED, 980, u)
        vi["y"] = GROUND - 180 - math.sin(u * math.pi) * 220 + u * 120
        vi["ang"] = u * 7
        v["mouth"], v["mamt"] = "o", 1.0
        v["wide"] = 1.4
    sfx(S, T(b, up), "whoosh", 0.6)
    S["cam"] = [880, 360, 1.2]


def a_dive(S, lt, b):
    v, vi = S["vex"], S["vial"]
    frozen(S, lt)
    v["sweat"] = 0
    u = clamp(lt / (b.d - 0.6))
    vi["x"] = lerp(980, 1060, u)
    vi["y"] = GROUND - 60 + u * 30 if lt < b.d - 0.6 else GROUND - 70
    vi["ang"] = 7 + u * 2
    v["tilt"] = lerp(0, 1.25, ease(u))
    v["x"] = lerp(760, 940, ease(u))
    v["yoff"] = -math.sin(u * math.pi) * 60
    v["mouth"], v["mamt"] = "laugh", 1.0
    v["hr"] = (150, -120)
    v["hl"] = (-60, -60)
    if lt > b.d - 0.6:
        vi["mode"] = "held"
        v["itemR"] = "vial"
    sfx(S, T(b, 0.1), "whoosh", 0.8)
    sfx(S, T(b, b.d - 0.6), "thud", 0.9)
    S["cam"] = [940, 420, tw(lt, 0, b.d, 1.2, 1.6)]


def a_golfclap(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    v["tilt"] = 1.25
    v["mouth"], v["mamt"] = "smile", 0.6
    for c in (bo, d):
        c["lid"] = 0.2
        c["mouth"], c["mamt"] = "smile", 0.5
        c["brow"] = 0.4
    d["itemR"] = None
    S["fx"]["lean"] = True
    clap = math.sin(lt * 24) * 8
    bo["hl"], bo["hr"] = (-14 - clap, -36), (14 + clap, -36)
    d["hl"], d["hr"] = (-12 - clap, -92), (12 + clap, -92)
    if lt > 1.6:
        bo["face"], bo["px"] = 0.6, 1
        d["face"], d["px"] = -0.6, -1
        bo["yoff"] = math.sin(clamp((lt - 1.6) / 0.4) * math.pi) * 6
        d["yoff"] = math.sin(clamp((lt - 1.6) / 0.4) * math.pi) * 6
    sfx(S, T(b, 0.1), "golfclap", 0.9)
    S["cam"] = [700, 380, tw(lt, 0, 0.6, 1.6, 1.0)]


def a_thanks(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    v["tilt"] = tw(lt, 0, 0.5, 1.25, 0)
    v["x"] = tw(lt, 0, 0.5, 940, 900)
    v["yoff"] = 0
    v["mouth"], v["mamt"] = "smile", 0.9
    v["blush"] = 1.0
    tw_ = b.vs + b.vd * 0.35
    if lt > tw_:
        v["brow"] = -1.4
        v["mouth"], v["mamt"] = "smirk", 1.0
        v["blush"] = 0
    if lt > b.vs + b.vd * 0.85:
        v["brow"] = 0.8
        v["wide"] = 1.0
        v["sweat"] = 1.0
    stare(bo)
    stare(d)
    S["cam"] = [880, 380, 1.3]


def a_put_back(S, lt, b):
    v, vi = S["vex"], S["vial"]
    stare(S["boredom"])
    stare(S["doubt"])
    v["face"], v["px"] = -0.5, -1
    walk(v, 760, lt, 0, 1.0, 0.4)
    if lt > 1.2:
        v["itemR"] = None
        vi.update(mode="ped", x=PED, y=GROUND - 180, ang=0.0)
        v["face"], v["px"] = 0.3, 0
        hand(v, 1, "wave", lt, 1.4, 1.8)
    v["mouth"], v["mamt"] = "wavy", 1.0
    v["sweat"] = 1.0
    S["cam"] = [740, 380, 1.1]


def a_failed(S, lt, b):
    v = S["vex"]
    stare(S["boredom"])
    stare(S["doubt"])
    hand(v, 1, "rest", lt, 0, 0.4)
    v["face"], v["px"], v["py"] = 0.7, 1, 0.8
    v["mouth"], v["mamt"] = "frown", 0.8
    v["brow"] = 0.8
    v["sweat"] = 0
    walk(v, 1120, lt, 0.4, b.d, 0.4)
    mus(S, T(b, 0.2), "sad", 0.6)
    S["cam"] = [740, 380, 1.0]


def a_second(S, lt, b):
    bo, d = S["boredom"], S["doubt"]
    bo.update(lid=0.2, mouth="smile", mamt=0.4, face=0.4, px=1, brow=0.2)
    d.update(lid=0.1, mouth="smile", mamt=0.4, face=-0.4, px=-1, brow=0.2)
    S["vex"]["walking"] = 0.4 if lt < 1.0 else 0
    if lt < 1.0:
        S["vex"]["x"] = tw(lt, 0, 1.0, 1120, 1160)


def a_forums(S, lt, b):
    d = S["doubt"]
    hand(d, -1, (-70, -150), lt, 0, 0.4)
    mus(S, T(b, 0.3), "lab", 0.4)


def a_you_read(S, lt, b):
    v = S["vex"]
    v["face"] = tw(lt, 0, 0.3, 0.7, -0.6)
    v["px"], v["py"] = -1, 0
    v["wide"] = tw(lt, 0.2, 0.4, 0, 1.5)
    v["brow"] = 1.0
    v["mouth"], v["mamt"] = "o", 0.8
    S["cam"] = [1100, 380, tw(lt, 0, 0.5, 1.0, 1.6)]


def a_cool(S, lt, b):
    S["cam"] = [640, 380, 1.0]
    bo = S["boredom"]
    hand(bo, 1, (70, -150), lt, 0, 0.4)


def a_questions(S, lt, b):
    hand(S["boredom"], 1, "rest", lt, 0, 0.4)


def a_shrug(S, lt, b):
    v = S["vex"]
    v["wide"] = 0
    v["brow"] = -0.3
    v["mouth"], v["mamt"] = "smirk", 0.4
    shr = math.sin(clamp(lt / 0.8) * math.pi)
    v["hl"] = (-90, -110 - 40 * shr)
    v["hr"] = (90, -110 - 40 * shr)
    v["yoff"] = -8 * shr
    if lt > b.vs + b.vd * 0.6:
        v["blush"] = 0.6


def a_zoomout(S, lt, b):
    v, bo, d = S["vex"], S["boredom"], S["doubt"]
    v.update(x=tw(lt, 0, 1.5, 1160, 760), walking=0.5 if lt < 1.5 else 0, face=-0.3, px=-1, blush=0.6,
             mouth="smile", mamt=0.6)
    bo.update(x=tw(lt, 0, 1.5, 330, 560), face=0.3, px=1, mouth="smile", mamt=0.7)
    d.update(x=tw(lt, 0, 1.5, DX, 960), face=-0.4, px=-1, mouth="smile", mamt=0.6, itemR="book")
    if lt > 1.6:
        v["hr"] = (70 + math.sin(lt * 5) * 30, -150 + math.cos(lt * 4) * 20)
        bo["hl"] = (-60 + math.sin(lt * 6) * 20, -150)
    S["fx"]["lean"] = False
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.4, 1.0)]
    mus(S, T(b, 0.0), "lab", 0.7)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, min=3.6),
    Beat(a_meet_boredom, "narr", "Meet Boredom, the mad scientist. Every dial goes to eleven.", pre=0.6,
         post=0.6),
    Beat(a_mutter, "boredom", "If the emotional wave function collapses at the speed of sarcasm, then carry "
                              "the feelings, square the vibes... yes. Yes!", rate="+12%", post=0.4),
    Beat(a_dweeb, "doubt", "You see this dweeb over here? I'd better keep an eye on this hyperactive genius.",
         post=0.6),
    Beat(a_meet_doubt, "narr", "And meet Doubt, the librarian. She walks two steps behind him, quietly fixing "
                               "everything.", post=1.0, min=4.6),
    Beat(a_works, "narr", "He can't do it without her. She can't do it without him. And somehow, the craziest "
                          "stuff they build always works.", post=1.6),
    Beat(a_hello, "vex", "Hello! Hello? I'm here! I'm the villain! Hello!", pre=1.4, post=0.4),
    Beat(a_guys, "vex", "Guys? Villain? Very evil? Hello?", post=0.4),
    Beat(a_stare, min=3.0),
    Beat(a_why, "vex", "Why did the music stop?", rate="-10%", gain=0.7, post=1.0),
    Beat(a_here_to, "vex", "Umm. Hey. I'm here to... uhh...", rate="-10%", post=0.2),
    Beat(a_silence, min=2.4),
    Beat(a_steal, "vex", "...steal stuff?", rate="-10%", post=0.2),
    Beat(a_boss, "vex", "Oh. Oh no. Oh, fudge.", pre=0.8, post=0.1),
    Beat(a_oh_no, "vex", "Oh, snap. Oh, snap, snap, snap!", rate="+8%", post=0.2),
    Beat(a_sidle, "narr", "He lifts it one centimeter.", pre=2.4, post=1.8, min=5.0),
    Beat(a_fumble, "vex", "Oh, fiddlesticks!", rate="-30%", pre=0.2, post=0.0, min=1.2, id="fum"),
    Beat(a_fumble, "vex", "If this breaks, I'm toast!", rate="-20%", post=0.0),
    Beat(a_dive, min=2.4, id="dive"),
    Beat(a_golfclap, min=2.6),
    Beat(a_thanks, "vex", "Thank you! ...Wait. What the heck? I'm the villain here!", post=0.8),
    Beat(a_put_back, "vex", "Well then. See you guys later.", pre=1.2, post=0.6),
    Beat(a_failed, "vex", "Darn it. Why am I acting like this? Sorry, guys. I failed at being a villain "
                          "today.", post=0.6),
    Beat(a_second, "boredom", "Well, dude. Actually, do you have a second?", pre=0.4, post=0.3),
    Beat(a_forums, "doubt", "We were impressed by your evil lair. We saw your post on the Evil Lair Forums.",
         post=0.6),
    Beat(a_you_read, "vex", "Wait. You read my post?", pre=0.4, post=1.0),
    Beat(a_cool, "boredom", "Yeah. It was pretty cool, dude.", post=0.2),
    Beat(a_questions, "doubt", "Can you show us what you were designing? We had a couple questions for you, "
                               "bro.", post=0.6),
    Beat(a_shrug, "vex", "Sure, guys. I don't have much time. I'm a villain. But yeah. I'll talk about it for "
                         "a bit, I guess.", post=0.8),
    Beat(a_zoomout, "narr", "He stayed for three hours.", pre=2.6, post=2.4),
    Beat(a_end, min=4.0),
]


# ------------------------------------------------------------------ drawing
def after(ctx, S, t):
    v = S["vial"]
    bt = S["fx"].get("burst")
    if bt is not None and bt <= t < bt + 1.2:
        E.draw_burst(ctx, dict(kind="pop", x=300, y=200, t=bt), t)
        import engine as _e
        for i in range(7):
            _e.sparkle(ctx, 200 + i * 40, 160 + math.sin(t * 6 + i) * 20, 10, ["#FF5A5A", "#FFB85A", "#FFE36A",
                       "#7CFF5A", "#5EC8E8", "#8C7AE8", "#E85EC8"][i], clamp(1 - (t - bt) / 1.2))


def draw(ctx, S, t):
    draw_world(ctx, S, t, extra_after=after)
    overlays(ctx, S, t, "LAB PARTNERS", "Episode 1: The Heist", "To be continued...", "Episode 2: Villain School")
