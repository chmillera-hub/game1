"""Episode 4: The Comedy Show."""
import math

import engine as E
from engine import tw, ease, clamp, lerp, PI
import mgfx as M
from mcommon import (sfx, hand, walk, mus, base_state, T, bleep, place, stare, draw_world, overlays, GROUND)
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
    S["doubt"] = M.new_doubt(600, mouth="smile", mamt=0.3, face=0.4, px=1)
    S["vex"] = M.new_char("vex", 900, face=-0.5, px=-1, crown=True)
    S["heir"] = M.new_char("heir", 1000, face=-0.5, px=-1, mouth="smile", mamt=0.7, brow=0.5, cape=True)
    S["council"] = M.new_char("council", 640, mouth="flat", mamt=0.0, brow=-0.4)
    S["elders"] = [M.new_char("council", x, s=0.8, mouth="flat", mamt=0.0, brow=-0.4) for x in (90, 210, 330)]
    S["elders"][1] = S["council"]  # the council member who speaks also sits in the middle at the show
    S["council2"] = S["elders"][0]
    S["council3"] = S["elders"][2]
    S["goon"] = M.new_char("goon1", 300, s=0.85, face=0.5, px=1)
    S["goons"] = [M.new_char(k, x, s=0.85, face=0.5, px=1) for k, x in (("goon2", 440), ("goon3", 560))]
    S["props"] = {"@goons": draw_goons, "@elders": draw_elders, "@car": lambda ctx, S, t: M.evil_car(ctx, 520, 600, t),
                  "@money": lambda ctx, S, t: M.money_pile(ctx, 640, 600, t), "@desk": draw_desk,
                  "@peel": draw_peel, "@duo_back": draw_duo_back, "@plan": draw_plan,
                  "@flying": draw_flying}
    S["show"] = ["boredom", "doubt", "vex"]
    S["card"] = 1.0
    return S


def draw_goons(ctx, S, t):
    for g in S["goons"]:
        E.draw_char(ctx, g, t)


def draw_elders(ctx, S, t):
    for g in S["elders"]:
        E.draw_char(ctx, g, t)
    M.council_table(ctx)


def draw_duo_back(ctx, S, t):
    if S["fx"].get("duo_back"):
        for n in ("boredom", "doubt"):
            E.draw_char(ctx, S[n], t)


def draw_desk(ctx, S, t):
    M.office_desk(ctx, 420)
    if S["fx"].get("laptop", 1.0) > 0:
        M.laptop_call(ctx, 560, 472, t, 0.85)
    else:
        E.rrect(ctx, 450, 456, 220, 16, 4)
        E.fill_stroke(ctx, "#1A1A22", "#000", 3)


def draw_peel(ctx, S, t):
    p = S["fx"].get("peel")
    if p:
        M.banana(ctx, p[0], p[1] - 4, p[2] if len(p) > 2 else 0.0, 1.5)


def draw_flying(ctx, S, t):
    for (x, y, r, kind) in S["fx"].get("flying", []):
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(r)
        if kind == 0:
            M.banana_peel(ctx, 0, 0, t)
        elif kind == 1:
            E.rrect(ctx, -14, -26, 28, 52, 6)
            E.fill_stroke(ctx, "#8FD8FF", "#2E6A8A", 3)
        else:
            E.star_path(ctx, 0, 0, 18, 8)
            E.src(ctx, "#FFE36A")
            ctx.fill()
        ctx.restore()


def draw_plan(ctx, S, t):
    x, y = 940, 300
    E.rrect(ctx, x - 230, y - 140, 460, 280, 8)
    E.fill_stroke(ctx, "#F8F8F4", "#8A8A84", 5)
    E.text(ctx, "EVIL PLAN #47", x, y - 96, 30, "#C41E3A")
    lines = ["1. Replace every statue with a duck", "2. Rename Monday \"Sunday 2\"", "3. Rubber chickens.",
             "    Everywhere."]
    p = S["fx"].get("plan", 1.0)
    for i, ln in enumerate(lines):
        if p > i / len(lines):
            E.text(ctx, ln, x - 205, y - 40 + i * 44, 22, "#2A2A2A", align="left")


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    mus(S, T(b), "sneaky", 0.55)


def a_council(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1, 0)
    S["scene"] = "hall"
    S["show"] = ["council", "vex", "heir"]
    c, v, h = S["council"], S["vex"], S["heir"]
    place(c, 300, 0.5, 1, s=1.15, mouth="flat", mamt=0.0, brow=-0.5)
    place(v, 760, -0.4, -1, mouth="smirk", mamt=0.4, brow=-0.4)
    place(h, 1000, -0.4, -1, s=0.9, mouth="smile", mamt=0.8, brow=0.5)
    h["visible"] = False
    S["cam"] = [640, 380, 1.0]


def a_voted(S, lt, b):
    c, h = S["council"], S["heir"]
    hand(c, 1, (90, -150), lt, 0, 0.4)
    if lt > b.vs + 2.2:
        h["visible"] = True
        h["x"] = tw(lt, b.vs + 2.2, b.vs + 3.4, 1300, 960)
        h["walking"] = 0.7 if lt < b.vs + 3.4 else 0


def a_heir_hi(S, lt, b):
    h = S["heir"]
    h["x"] = 960
    h["walking"] = 0
    h["yoff"] = -abs(math.sin(lt * 9)) * 14
    h["hr"] = (60, -150 + math.sin(lt * 14) * 16)
    h["mouth"], h["mamt"] = "laugh", 0.8
    S["cam"] = [860, 380, 1.3]


def a_wonderful(S, lt, b):
    v, h = S["vex"], S["heir"]
    h["yoff"] = 0
    v.update(face=0.0, px=0, lid=0.5, mouth="flat", mamt=0, sweat=0.7)
    S["cam"] = [760, 380, 1.5]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_everywhere(S, lt, b):
    S["scene"] = "hall"
    S["show"] = ["vex", "heir"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    v, h = S["vex"], S["heir"]
    place(v, 0, 0.5, 1, mouth="flat", mamt=0.0, brow=-0.6, sweat=0.5)
    place(h, 0, 0.5, 1, s=0.9, mouth="smile", mamt=0.8, brow=0.5)
    v["x"] = -100 + lt * 190
    h["x"] = v["x"] - 170
    v["walking"] = h["walking"] = 0.8
    v["px"] = -1 if (lt % 3) > 2 else 1
    S["fx"]["ev_d"] = b.d
    S["cam"] = [640, 380, 1.0]


def a_one_slip(S, lt, b):
    v, h = S["vex"], S["heir"]
    v["x"] = -100 + (lt + S["fx"]["ev_d"]) * 190
    h["x"] = v["x"] - 170
    v["walking"] = h["walking"] = 0.8
    v["px"] = -1 if (lt % 3) > 2 else 1
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_call_caught(S, lt, b):
    S["scene"] = "office"
    S["show"] = ["vex", "@desk", "heir"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    v, h = S["vex"], S["heir"]
    place(v, 340, 0.5, 1, y=GROUND - 120, mouth="smile", mamt=0.7, brow=0.5)
    place(h, 1135, -0.5, -1, s=0.9, mouth="smile", mamt=0.6, brow=0.5)
    h["visible"] = lt > 1.0
    S["fx"]["laptop"] = 1.0 if lt < 1.3 else 0.0
    if lt > 1.3:
        v.update(wide=1.0, mouth="o", mamt=0.6, sweat=1.0)
        hand(v, 1, (130, -60), lt, 1.2, 1.35)
    sfx(S, T(b, 1.3), "slam", 0.8)
    S["cam"] = [640, 400, 1.0]


def a_who(S, lt, b):
    S["cam"] = [900, 420, 1.3]


def a_dentist(S, lt, b):
    v = S["vex"]
    v.update(wide=0.4, mouth="smile", mamt=0.9)
    S["cam"] = [520, 400, 1.35]


def a_tired(S, lt, b):
    v, h = S["vex"], S["heir"]
    # the heir wanders off; Vex slumps behind the desk, fed up with hiding
    h.update(face=0.5, px=1)
    walk(h, 1300, lt, 0, 1.6, 0.7)
    h["visible"] = lt < 1.6
    v.update(wide=0.0, sweat=0.0, mouth="frown", mamt=0.6, brow=0.8, lid=0.4, py=0.4)
    hand(v, -1, (-20, -120), lt, 1.0, 1.4)
    S["cam"] = [tw(lt, 0, 1.6, 640, 420), 400, tw(lt, 0, 1.6, 1.0, 1.4)]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_screw(S, lt, b):
    S["scene"] = "dark"
    S["show"] = ["vex"]
    v = S["vex"]
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    place(v, 640, 0.0, 0, mouth="frown", mamt=0.7, brow=-1.0, lid=0.15, py=0.0)
    v["mode"] = "stomp" if lt < 1.4 else None
    hand(v, 1, (80, -170), lt, 1.4, 1.8)
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.1, 1.4)]
    mus(S, T(b), "tense", 0.45)


def a_car(S, lt, b):
    S["scene"] = "road"
    S["show"] = ["@car", "vex"]
    v = S["vex"]
    place(v, 860, -0.3, -1, mouth="laugh", mamt=1.0, brow=0.6, eyes="happy", shades=True)
    v["mode"] = None
    hand(v, -1, (-90, -170), lt, 0, 0.01)
    S["cam"] = [640, 360, 1.0]
    mus(S, T(b), "show", 0.5)


def a_money(S, lt, b):
    S["scene"] = "vault"
    S["show"] = ["@money", "vex"]
    v = S["vex"]
    place(v, 640, 0, 0, y=GROUND - 150, mouth="smile", mamt=0.6, brow=0.3, eyes="open", shades=False)
    hand(v, -1, (-110, -160), lt, 0, 0.01)
    hand(v, 1, (110, -160), lt, 0, 0.01)
    sfx(S, T(b, 0.3), "bling", 0.5)


def a_sitcom(S, lt, b):
    S["scene"] = "sitcom"
    S["show"] = ["goon", "vex", "@goons"]
    v, g = S["vex"], S["goon"]
    place(v, 540, 0.2, 1, y=GROUND - 60, mouth="smile", mamt=0.25, brow=0.0)
    place(g, 380, 0.4, 1, y=GROUND - 60, s=0.85, mouth="laugh", mamt=0.9)
    for i, o in enumerate(S["goons"]):
        place(o, 700 + i * 130, -0.4, -1, y=GROUND - 60, s=0.85, mouth="laugh", mamt=0.9)
    sfx(S, T(b, 0.6), "crowdlaugh", 0.5)


def a_medals(S, lt, b):
    S["scene"] = "medals"
    S["show"] = ["vex"]
    v = S["vex"]
    place(v, 640, 0, 0, py=-0.6, mouth="frown", mamt=0.6, brow=-1.0, lid=0.35)
    S["cam"] = [640, 380, tw(lt, 0, b.d, 1.0, 1.3)]


def a_all_lost(S, lt, b):
    S["scene"] = "dark"
    S["show"] = ["vex"]
    S["fade"] = tw(lt, 0, 0.6, 1, 0)
    v = S["vex"]
    place(v, 640, 0, 0, y=GROUND, yoff=30, mouth="frown", mamt=0.8, brow=0.9, tears=0.8, py=0.8)
    v["footL"], v["footR"] = (-30, -26), (30, -26)
    S["cam"] = [640, 420, 1.3]
    mus(S, T(b), "sad", 0.55)


def a_curse(S, lt, b):
    v = S["vex"]
    v.update(tears=0.4, brow=-1.0, mouth="frown", py=-0.4)
    hand(v, -1, (-110, -190), lt, 0, 0.3)
    hand(v, 1, (110, -190), lt, 0, 0.3)
    v["shake"] = 1.0


def a_curse2(S, lt, b):
    S["vex"]["shake"] = 1.0


def a_number(S, lt, b):
    v = S["vex"]
    v.update(shake=0, tears=0.7, brow=0.8, mouth="o", mamt=0.3, py=0.6)
    v["itemR"] = "phone"
    hand(v, -1, "rest", lt, 0, 0.4)
    hand(v, 1, (40, -150), lt, 0, 0.6)
    sfx(S, T(b, b.d - 1.0), "ding", 0.4)


def a_pickup(S, lt, b):
    S["scene"] = "beach"
    S["show"] = ["boredom", "doubt"]
    bo, d = S["boredom"], S["doubt"]
    place(bo, 520, 0.3, 1, mouth="smile", mamt=0.5, shades=True)
    place(d, 760, -0.3, -1, mouth="smile", mamt=0.6, shades=True, itemR="phone")
    d["hr"] = (40, -150)
    bo["itemR"] = "cocktail"
    bo["hr"] = (60, -110)
    S["cam"] = [640, 400, 1.15]
    sfx(S, T(b, 0.1), "water", 0.25)


def a_vex_phone(S, lt, b):
    S["scene"] = "dark"
    S["show"] = ["vex"]
    S["cam"] = [640, 420, 1.35]


def a_beach_back(S, lt, b):
    S["scene"] = "beach"
    S["show"] = ["boredom", "doubt"]
    S["cam"] = [640, 400, 1.15]


def a_blessed(S, lt, b):
    S["scene"] = "dark"
    S["show"] = ["vex"]
    v = S["vex"]
    v.update(tears=0.4, mouth="smile", mamt=tw(lt, 0, 3, 0.1, 0.6), brow=0.6, py=-0.2, blush=0.4)
    S["cam"] = [640, 420, tw(lt, 0, b.d, 1.35, 1.1)]
    mus(S, T(b), "hope", 0.5)


def a_idea_q(S, lt, b):
    a_beach_back(S, lt, b)
    bo = S["boredom"]
    bo["shades"] = False
    bo["mouth"], bo["mamt"] = "smirk", 0.6


def a_humor(S, lt, b):
    S["scene"] = "dark"
    S["show"] = ["vex"]
    v = S["vex"]
    v.update(tears=0.0, wide=tw(lt, 0, 0.3, 0, 1), mouth="o", mamt=0.6, brow=0.8, py=-0.6, yoff=0)
    v["footL"], v["footR"] = (0, 0), (0, 0)
    v["itemR"] = None
    hand(v, 1, (60, -220), lt, 0, 0.3)
    sfx(S, T(b, 0.05), "ding", 0.8)
    S["flash"] = tw(lt, 0, 0.3, 0.5, 0)
    S["cam"] = [640, 380, 1.2]


def a_plan(S, lt, b):
    S["scene"] = "hall"
    S["show"] = ["@plan", "goon", "@goons", "vex"]
    S["fade"] = 0
    v, g = S["vex"], S["goon"]
    place(v, 520, 0.5, 1, mouth="smirk", mamt=0.8, brow=-0.8, wide=0, shades=False)
    hand(v, 1, (110, -170), lt, 0, 0.4)
    S["fx"]["plan"] = clamp(lt / 3.0)
    place(g, 160, 0.5, 1, s=0.85, mouth="o", mamt=0.6)
    for i, o in enumerate(S["goons"]):
        place(o, 270 + i * 110, 0.5, 1, s=0.85, mouth="o", mamt=0.6)
    if lt > 3.0:
        for o in [g] + S["goons"]:
            o["mode"] = "laugh"
        sfx(S, T(b, 3.0), "crowdlaugh", 0.35)
    S["cam"] = [640, 380, 1.0]
    mus(S, T(b), "quirky", 0.5)


def a_key(S, lt, b):
    S["cam"] = [640, 380, tw(lt, 0, b.d, 1.0, 1.1)]
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


def setup_stage(S):
    S["scene"] = "stage"
    S["show"] = ["@duo_back", "@elders", "vex", "@peel", "@flying"]
    for i, e in enumerate(S["elders"]):
        place(e, 90 + i * 120, 0.5, 1, s=0.8, mouth="flat", mamt=0.0, brow=-0.5, lid=0.5)
    bo, d = S["boredom"], S["doubt"]
    place(bo, 150, 0.4, 1, s=0.6, y=GROUND - 120, disguise=True, shades=False, itemR=None, mouth="flat", mamt=0)
    place(d, 300, 0.4, 1, s=0.6, y=GROUND - 120, disguise=True, shades=False, itemR=None, mouth="flat", mamt=0)
    bo["hr"] = E.pose("boredom", 1, "rest")
    d["hr"] = E.pose("doubt", 1, "rest")
    S["fx"]["duo_back"] = True


def a_show(S, lt, b):
    setup_stage(S)
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    v = S["vex"]
    place(v, 1400, -0.5, -1, mouth="smile", mamt=0.8, brow=0.4, eyes="open")
    v["visible"] = False
    S["fx"]["spot"] = 0.6
    S["cam"] = [640, 360, 1.0]
    mus(S, T(b), "lounge", 0.35)


def a_stoneface(S, lt, b):
    S["cam"] = [220, 440, tw(lt, 0, b.d, 1.5, 1.8)]


def a_enter(S, lt, b):
    v = S["vex"]
    v["visible"] = True
    walk(v, 900, lt, 0, 1.6, 0.8)
    S["cam"] = [640, 360, 1.0]
    sfx(S, T(b, 0.0), "applause", 0.15)


def a_pun(S, lt, b):
    v = S["vex"]
    v["x"] = 900
    v["walking"] = 0
    hand(v, 1, (70, -150), lt, 0, 0.3)
    v["itemR"] = "mic"
    S["cam"] = [820, 380, 1.3]


def a_pun_silence(S, lt, b):
    sfx(S, T(b, 0.1), "cymbal", 0.6)
    sfx(S, T(b, 0.9), "cricket", 0.6)
    v = S["vex"]
    v.update(mouth="smile", mamt=0.6, sweat=0.4)
    S["cam"] = [lerp(220, 820, 0.0 if lt < 1.0 else 1.0), 430 if lt < 1.0 else 380, 1.6 if lt < 1.0 else 1.3]


REST = 1120  # where the banana ends up (and where he slips later)
CENTER = 860  # where his tumble ends


def a_banana(S, lt, b):
    v = S["vex"]
    v["itemR"] = None
    v["itemL"] = "banana"
    hand(v, -1, (-120, -160), lt, 0, 0.4)
    v["hl"] = (v["hl"][0], v["hl"][1] + math.sin(lt * 6) * 6)
    v.update(mouth="smile", mamt=0.8, brow=0.5)
    S["cam"] = [820, 380, 1.2]


def banana_path(lt):
    """Thrown over his shoulder at 0.5s, then a few sad little bounces."""
    if lt < 1.2:
        u = clamp((lt - 0.5) / 0.7)
        return lerp(930, 1060, u), lerp(400, GROUND - 6, u) - math.sin(u * PI) * 160, u * 8
    hops = [(1.2, 1.6, 1060, 1090, 34), (1.6, 1.9, 1090, 1110, 14), (1.9, 2.1, 1110, REST, 5)]
    for t0, t1, x0, x1, h in hops:
        if lt < t1:
            u = (lt - t0) / (t1 - t0)
            return lerp(x0, x1, u), GROUND - 6 - math.sin(u * PI) * h, 8 + u
    return REST, GROUND - 6, 9.0


def a_eat(S, lt, b):
    v = S["vex"]
    es = S["elders"]
    if lt < 0.5:
        hand(v, -1, (40, -230), lt, 0, 0.5)  # wind up over the shoulder
    else:
        v["itemL"] = None
        hand(v, -1, (-110, -150), lt, 0.5, 0.7)
        S["fx"]["peel"] = banana_path(lt)
    v.update(mouth="smile" if lt < 2.3 else "flat", mamt=0.9 if lt < 2.3 else 0.0,
             wide=0.5 if lt > 2.3 else 0.0, sweat=0.5 if lt > 2.3 else 0.0)
    if 2.4 < lt < 3.6:
        # the council side-eyes each other, then straight back to stone
        for i, e in enumerate(es):
            e["px"] = (1, -1, 1)[i] if lt < 3.2 else 0
            e["face"] = (0.5, -0.5, 0.5)[i] if lt < 3.2 else 0.5
            e["lid"] = 0.6
    sfx(S, T(b, 0.5), "throw", 0.5)
    for k, (tt, g) in enumerate(((1.2, 0.5), (1.6, 0.3), (1.9, 0.15))):
        sfx(S, T(b, tt), "tap", g)
    sfx(S, T(b, 2.6), "cricket", 0.6)
    S["cam"] = [tw(lt, 0, 1.0, 820, 820), 400, 1.1] if lt < 2.4 else [tw(lt, 2.4, 2.8, 820, 220), 440,
                                                                      tw(lt, 2.4, 2.8, 1.1, 1.8)]


def a_tough(S, lt, b):
    S["fx"]["peel"] = (REST, GROUND - 6, 9.0)
    for e in S["elders"]:
        e["px"] = 0
    v = S["vex"]
    v.update(mouth="smile", mamt=0.5, sweat=0.8, brow=0.6)


def a_for_nothing(S, lt, b):
    S["cam"] = [lerp(220, 640, clamp(lt / b.d)), 420, tw(lt, 0, b.d, 1.6, 1.0)]
    v = S["vex"]
    v["wide"] = 0
    v.update(mouth="frown", mamt=0.5, brow=0.9, py=0.6, sweat=0.3)
    hand(v, 1, "rest", lt, 0, 0.5)
    hand(v, -1, "rest", lt, 0, 0.5)
    mus(S, T(b), "sad", 0.3, 0.6, 0.1)


def a_water(S, lt, b):
    v = S["vex"]
    if lt < 2.0:
        v.update(face=0.5, px=1)
        walk(v, 1340, lt, 0, 2.0, 0.6)
    else:
        # walks back on from the wings, straight toward the banana
        v.update(face=-0.5, px=-1, itemR="bottle", py=0.4, x=1340)
        walk(v, REST + 10, lt, 2.2, b.d, 0.6)
    S["cam"] = [940, 380, 1.1]


def a_slip(S, lt, b):
    v = S["vex"]
    # feet fly out, a full flip in the air, then a tumble roll back to center stage
    u = clamp(lt / 1.1)
    r = clamp((lt - 1.1) / 0.6)
    v["x"] = lerp(REST + 10, 960, u) if lt < 1.1 else lerp(960, CENTER, ease(r))
    v["walking"] = 0
    v["yoff"] = -math.sin(u * PI) * 180 if lt < 1.1 else -abs(math.sin(r * PI)) * 14
    v["tilt"] = -u * (2 * PI + PI / 2) - ease(r) * 2 * PI
    v["wide"] = 1.0
    v["mouth"], v["mamt"] = "o", 1.0
    S["fx"]["peel"] = (tw(lt, 0, 0.6, REST, REST + 70), GROUND - 6, 9.0 + lt * 4 if lt < 0.6 else 11.4)
    hand(v, -1, (-120, -200), lt, 0, 0.1)
    hand(v, 1, (120, -200), lt, 0, 0.1)
    sfx(S, T(b), "slip", 1.0)
    sfx(S, T(b, 0.15), "squeal", 1.0)
    sfx(S, T(b, 1.1), "crashland", 1.0)
    sfx(S, T(b, 1.7), "thud", 0.7)
    S["shake"] = tw(lt, 1.1, 1.6, 1.0, 0) if lt > 1.1 else 0
    S["cam"] = [lerp(1000, 900, clamp((lt - 1.1) / 0.6)), 400, 1.15]


def a_silence(S, lt, b):
    v = S["vex"]
    v["tilt"] = -PI / 2 + tw(lt, 3.0, 5.0, 0, PI / 2)
    v["yoff"] = 0
    v["wide"] = 0
    v["mouth"], v["mamt"] = "frown", 0.4
    v["lid"] = 0.5
    v["brow"] = 0.9
    v["py"] = 0.6
    S["shake"] = 0
    v["x"] = CENTER
    S["cam"] = [lerp(CENTER, 360, ease(clamp((lt - 1) / 2))), 420, 1.2]
    sfx(S, T(b, 1.5), "cricket", 0.5)


def a_tiny_chuckle(S, lt, b):
    e = S["elders"][1]
    e["mouth"], e["mamt"] = "smile", 0.2 + 0.2 * abs(math.sin(lt * 10))
    e["shake"] = 0.4
    sfx(S, T(b, 0.2), "chuckle", 0.5)
    S["cam"] = [210, 440, 1.8]


def a_spread(S, lt, b):
    for i, e in enumerate(S["elders"]):
        if lt > i * 0.6:
            e["mode"] = "giggle" if lt < 1.8 + i * 0.4 else "laugh"
    sfx(S, T(b, 0.4), "chuckle", 0.6)
    sfx(S, T(b, 1.4), "crowdlaugh", 0.7)
    S["cam"] = [tw(lt, 0, b.d, 210, 400), 420, tw(lt, 0, b.d, 1.8, 1.0)]


def a_realize(S, lt, b):
    v = S["vex"]
    v.update(tilt=0, lid=0.15, py=0, px=-1, face=-0.5, wide=0.8, mouth="o", mamt=0.5, brow=0.6)
    if lt > 1.2:
        v.update(mouth="smirk", mamt=0.9, brow=-0.8, wide=0)
    S["cam"] = [640, 380, 1.3]


def a_ham(S, lt, b):
    v = S["vex"]
    u = (lt % 1.4) / 1.4
    v["x"] = CENTER - 240 * (0.5 - 0.5 * math.cos(lt * 0.9))
    v["tilt"] = math.sin(u * PI) * 1.4 * (1 if int(lt / 1.4) % 2 else -1)
    v["yoff"] = -math.sin(u * PI) * 50
    v["mouth"], v["mamt"] = "laugh", 0.9
    v["eyes"] = "happy"
    v["hl"] = (-100, -200 + math.sin(lt * 9) * 20)
    v["hr"] = (100, -200 + math.cos(lt * 9) * 20)
    fl = []
    for i in range(7):
        k = (lt * 0.8 + i / 7) % 1
        fl.append((v["x"] + (i - 3) * 90 * k, 520 - math.sin(k * PI) * 360, lt * 5 + i, i % 3))
    S["fx"]["flying"] = fl
    for k in range(int(b.d / 1.4)):
        sfx(S, T(b, 0.2 + k * 1.4), ("slip", "boing", "squeal")[k % 3], 0.7)
    sfx(S, T(b, 0.3), "crowdlaugh", 0.9)
    sfx(S, T(b, 2.6), "crowdlaugh", 1.0)
    for e in S["elders"]:
        e["mode"] = "laugh"
    for n in ("boredom", "doubt"):
        S[n]["mode"] = "laugh"
    S["cam"] = [640, 380, 1.0]
    mus(S, T(b), "show", 0.5)


def a_ovation(S, lt, b):
    v = S["vex"]
    S["fx"]["flying"] = []
    v.update(x=tw(lt, 0, 0.5, v["x"], 860), tilt=0, yoff=0, mouth="smile", mamt=0.9, eyes="happy", brow=0.6)
    v["hl"] = (-100, -150)
    v["hr"] = (100, -150)
    if lt > 0.8:
        v["tilt"] = 0.25 * math.sin(clamp((lt - 0.8) / 1.0) * PI)
    for i, e in enumerate(S["elders"]):
        e["mode"] = None
        e.update(mouth="laugh", mamt=0.8, eyes="happy", yoff=-abs(math.sin(lt * 8 + i)) * 10 - 20)
        e["hl"] = (-30, -140 + math.sin(lt * 18 + i) * 8)
        e["hr"] = (30, -140 - math.sin(lt * 18 + i) * 8)
    for n in ("boredom", "doubt"):
        c = S[n]
        c["mode"] = None
        c.update(mouth="smile", mamt=0.9, yoff=-abs(math.sin(lt * 8)) * 10 - 20)
        c["hl"] = (-30, -150 + math.sin(lt * 18) * 8)
        c["hr"] = (30, -150 - math.sin(lt * 18) * 8)
    sfx(S, T(b, 0.1), "ovation", 1.0)
    S["fx"]["spot"] = 1.0
    S["cam"] = [640, 360, 1.0]


def a_heart(S, lt, b):
    # the middle council member, still clapping, lets it slip
    a_ovation(S, lt + 3, b)
    c = S["council"]
    c.update(eyes="open", mouth="smile", mamt=0.5, brow=0.6, lid=0.2)
    S["cam"] = [210, 440, 1.7]


def a_what_hearts(S, lt, b):
    es = S["elders"]
    for i, e in enumerate(es):
        e.update(eyes="open", yoff=0, mode=None)
        e["hl"], e["hr"] = E.pose("council", -1, "rest"), E.pose("council", 1, "rest")
    l, c, r = es
    l.update(px=1, face=0.4, brow=-1.0, mouth="frown", mamt=0.6, lid=0.35)
    r.update(px=-1, face=-0.4, brow=-1.0, mouth="frown", mamt=0.6, lid=0.35)
    c.update(px=0, wide=1.0, sweat=1.0, mouth="o", mamt=0.5, brow=0.8, lid=0.0)
    for n in ("boredom", "doubt"):
        S[n].update(mode=None, yoff=0, mouth="o", mamt=0.4)
    sfx(S, T(b, 0.0), "scratch", 0.5)
    S["cam"] = [210, 440, tw(lt, 0, 0.4, 1.7, 1.9)]


def a_nothing(S, lt, b):
    S["cam"] = [210, 440, 1.9]


def a_scheme(S, lt, b):
    v = S["vex"]
    v.update(x=860, face=0.0, px=-1, tilt=0, itemR=None, itemL=None, yoff=0, eyes="open", mouth="smirk", mamt=1.0, brow=-1.0, lid=0.35,
             blush=0.0)
    rub = math.sin(lt * 14) * 10
    v["hl"] = (-14 + rub, -120)
    v["hr"] = (14 - rub, -116)
    S["fx"]["spot"] = tw(lt, 0, 0.5, 1.0, 0.5)
    S["cam"] = [860, 380, tw(lt, 0, b.d, 1.3, 1.6)]
    sfx(S, T(b, 0.2), "sting", 0.5)


def a_pitch(S, lt, b):
    v = S["vex"]
    v.update(face=-0.6, px=-1, lid=0.15, mouth="smile", mamt=0.8, brow=0.4)
    hand(v, -1, (-120, -170), lt, 0, 0.4)
    hand(v, 1, (110, -150), lt, 0.2, 0.6)
    walk(v, 860, lt, 0, 1.2, 0.6)
    S["cam"] = [tw(lt, 0, 1.2, 860, 520), 400, tw(lt, 0, 1.2, 1.3, 1.0)]


def grudging(e, lt, side):
    e.update(face=-0.5 * side, px=-side, lid=0.5, brow=-0.8, mouth="flat", mamt=0.0, sweat=0)
    e["hl"], e["hr"] = E.pose("council", -1, "cross"), E.pose("council", 1, "cross")


def a_only_if(S, lt, b):
    l, c, r = S["elders"]
    grudging(l, lt, 1)
    r.update(px=1, face=0.3)
    S["cam"] = [210, 440, 1.7]


def a_try(S, lt, b):
    l, c, r = S["elders"]
    grudging(r, lt, -1)
    c.update(wide=0.0, sweat=tw(lt, 0, 1.0, 1.0, 0.0), mouth="smile", mamt=tw(lt, 0.5, 1.5, 0.0, 0.5),
             lid=0.15, brow=0.4)
    S["cam"] = [210, 440, 1.7]


def a_curtain(S, lt, b):
    S["fx"]["curtain"] = clamp(lt / 2.2)
    sfx(S, T(b, 0.1), "curtain", 0.7)
    a_scheme(S, lt + 3, b)
    S["vex"]["x"] = 860
    S["cam"] = [640, 360, 1.0]


def a_outro(S, lt, b):
    S["fx"]["curtain"] = 1.0
    S["endcard"] = tw(lt, b.d - 4.0, b.d - 3.2, 0, 1)


BEATS = [
    Beat(a_title, min=3.6),
    Beat(a_council, "narr", "The Master Villain had one more problem. The evil council.", pre=0.4, post=0.3),
    Beat(a_voted, "council", "Lord Vex. The council has voted. This is your heir. Teach him everything.",
         post=0.4),
    Beat(a_heir_hi, "heir", "Hi! I'm so excited! I'm going to follow you everywhere!", post=0.4),
    Beat(a_wonderful, "vex", "Wonderful.", rate="-12%", post=1.2),
    Beat(a_everywhere, "narr", "And he did. Everywhere. Vex had to teach him to be evil, without looking too "
                               "kind.", id="ev", pre=0.6, post=0.2),
    Beat(a_one_slip, "narr", "One slip, and the heir could tell the council everything.", post=0.6),
    Beat(a_call_caught, min=2.4),
    Beat(a_who, "heir", "Who were you talking to?", post=0.3),
    Beat(a_dentist, "vex", "Nobody! My dentist. My evil... dentist.", post=1.0),
    Beat(a_tired, "vex", "Ugh. I'm so tired of hiding every time I talk to Boredom and Doubt.", rate="-4%",
         pre=0.4, post=0.6),
    Beat(a_screw, "vex", "You know what? I've learned enough. Screw Boredom and Doubt. I don't need them anymore. "
                         "Time to try this evil thing on my own.", pre=0.5, post=0.6),
    Beat(a_car, "narr", "So he chased everything a villain is supposed to want. The evil car.", pre=0.4,
         post=0.6),
    Beat(a_money, "narr", "Piles of money, stolen from citizens.", post=0.6),
    Beat(a_sitcom, "narr", "The evilest sitcom on television. But you'd notice something. His smile was "
                           "getting smaller.", post=0.6),
    Beat(a_medals, "narr", "Even his medals got a scowl.", post=1.2),
    Beat(a_all_lost, "narr", "And then one night, he thought all was lost.", pre=0.6, post=0.8),
    Beat(a_curse, "vex", "This stupid world! This rotten, stupid...", post=0.0),
    bleep(0.6),
    Beat(a_curse2, "vex", "And you know what else?", post=0.0),
    bleep(0.9),
    Beat(a_number, "narr", "But he still had their number.", pre=0.8, post=1.6),
    Beat(a_pickup, "doubt", "Hey, buddy. We were wondering when you'd call.", post=0.4),
    Beat(a_vex_phone, "vex", "I tried to do it without you. I got everything. And I've never been more "
                             "miserable.", rate="-6%", post=0.5),
    Beat(a_beach_back, "boredom", "We know. We watched the sitcom.", post=0.8),
    Beat(a_blessed, "narr", "He had cursed the world. There was no need. The world had cursed him, sure. But it "
                            "had blessed him too. With Boredom and Doubt.", pre=0.4, post=0.6),
    Beat(a_idea_q, "doubt", "So. You have to stay the scariest villain around. But you hate hurting anyone. "
                            "What's the one thing a villain can't fight?", post=0.6),
    Beat(a_humor, "vex", "Humor.", post=0.8),
    Beat(a_plan, "narr", "His new plans were so absurd, the minions laughed too hard to hurt anyone.", pre=0.4,
         post=0.4),
    Beat(a_key, "narr", "Humor was the key. It opened their eyes to a way of living with well-being, and peace "
                        "for all. Now he just had to convince the council.", post=0.8),
    Beat(a_show, "narr", "The Villain Comedy Night. The council came. And they did not laugh. At anything.",
         pre=0.6, post=0.4),
    Beat(a_stoneface, "narr", "If the council didn't laugh, all of it was for nothing. And the last act was "
                              "Lord Vex.", post=0.6),
    Beat(a_enter, min=1.8),
    Beat(a_pun, "vex", "Why did the villain bring a ladder to the heist? He heard the stakes were high!",
         post=0.2),
    Beat(a_pun_silence, min=2.2),
    Beat(a_banana, "vex", "Behold! I shall make this banana... disappear!", post=0.2),
    Beat(a_eat, min=3.8),
    Beat(a_tough, "vex", "Tough crowd. Okay.", post=0.6),
    Beat(a_for_nothing, "narr", "Puns. Tricks. Everything he had. Not one twitch.", post=0.6),
    Beat(a_water, min=4.0),
    Beat(a_slip, min=2.0),
    Beat(a_silence, min=5.0),
    Beat(a_tiny_chuckle, min=2.2),
    Beat(a_spread, min=3.6),
    Beat(a_realize, "vex", "Oh. Oh!", post=0.8),
    Beat(a_ham, min=5.6),
    Beat(a_ovation, min=3.2),
    Beat(a_heart, "council", "That was the stupidest thing I've ever seen. But he's got heart.", post=0.4),
    Beat(a_what_hearts, "council2", "What did you just say about... hearts?", rate="-8%", pre=0.6, post=0.8),
    Beat(a_nothing, "council", "Nothing.", pitch="+10Hz", post=0.8),
    Beat(a_scheme, "vex", "Heh heh heh. The plan... is working.", rate="-10%", pre=0.3, post=1.0),
    Beat(a_pitch, "vex", "Council! Let's use this heart idea to make us even more evil. More evil bucks. More "
                         "evil power. Right, guys?", pre=0.2, post=0.5),
    Beat(a_only_if, "council2", "Fine. Only if this heart thing makes us lots of money. And power.", rate="-6%",
         post=0.5),
    Beat(a_try, "council3", "Hmph. I guess we can try.", post=1.0),
    Beat(a_curtain, min=2.2),
    Beat(a_outro, "narr", "And that's how the most villainous villain became the least conflicted one. With a "
                          "little help from his lab partners.", pre=0.4, post=3.6),
]


def draw(ctx, S, t):
    draw_world(ctx, S, t)
    cu = S["fx"].get("curtain", 0)
    if cu > 0:
        M.curtain_drop(ctx, cu)
    overlays(ctx, S, t, "LAB PARTNERS", "Episode 4: The Comedy Show", "THE END", "Lab Partners")
