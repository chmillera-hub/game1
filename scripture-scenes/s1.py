"""Four passages, four scenes. Subtitles are the passages exactly as given."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import sgfx as G
from dcommon import sfx, music, hand, walk, cam_to, apply_cam
from show import Beat

TOTAL = 0.0
IDX = {}
SCREEN = (0, 0, 1280, 720)

# people
K_ELI = G.person_kind("eli", "#5E8A4E", "#C68E5E", hair="#2A1E14", style="short", beard=True, sash="#D9C08A")
K_JOR = G.person_kind("jor", "#8A4A3A", "#E0B28A", hair="#5A3A22", style="messy")
K_JESUS = G.person_kind("jesus", "#F2EEE4", "#C68E5E", hair="#4A2E1A", style="long", beard=True,
                        sash="#9E2A2A")
K_D1 = G.person_kind("d1", "#3E5E8E", "#B97A4A", hair="#1A120C", style="short", beard=True)
K_D2 = G.person_kind("d2", "#B9904A", "#E0B28A", hair="#7A4A22", style="short")
K_D3 = G.person_kind("d3", "#6E6A64", "#8A5A3A", hair="#1A120C", style="bald", beard="#3A2A1E")
K_D4 = G.person_kind("d4", "#7A2E4A", "#D2A47A", hair="#3A2A1E", style="messy", beard=True)
K_PAUL = G.person_kind("paul", "#8A6A4A", "#D2A47A", hair="#B8B0A4", style="bald", beard="#C8C0B4",
                       sash="#5A3A22")
K_SAUL = G.person_kind("saul", "#2E2A3A", "#D2A47A", hair="#1A120C", style="short", beard=True,
                       sash="#9E2A2A")
K_TRAV = G.person_kind("trav", "#4A6E9E", "#A8714A", scarf="#E8D2A8")


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
    S = dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0, fade=0.0,
             card=None, scene="village", phase="dusk", tint=0.0, flash=0.0)
    S["eli"] = G.new_person(K_ELI, 520, visible=False)
    S["jor"] = G.new_person(K_JOR, 1450, mouth="smirk", mamt=0.6)
    S["pot_broken"] = None
    S["v"] = dict(dusk=0.0, rain=0.0, door=0.0, watchers=0.0, sunrise=0.0)
    S["coals"] = 0.0
    S["dropped_stone"] = None
    S["jesus"] = G.new_person(K_JESUS, 640, halo=0.6, mouth="smile", mamt=0.4)
    S["disc"] = [G.new_person(k, x, face=f, px=p) for k, x, f, p in
                 ((K_D1, 300, 0.6, 1), (K_D2, 460, 0.5, 1), (K_D3, 820, -0.5, -1), (K_D4, 980, -0.6, -1))]
    S["paul"] = G.new_person(K_PAUL, 560, itemR="quill", mouth="flat", mamt=0)
    S["paul"]["hr"] = (40, -104)
    S["paul"]["hl"] = (-30, -100)
    S["saul"] = G.new_person(K_SAUL, -100, itemL="scroll", mouth="frown", mamt=0.5, brow=-0.8)
    S["fleeing"] = [G.new_person(K_D2, 900), G.new_person(K_TRAV, 1000)]
    S["dawn"] = 0.0
    S["road_light"] = 0.0
    S["grace"] = 0.0
    S["trav"] = G.new_person(K_TRAV, 200, mouth="flat", mamt=0)
    S["sheep"] = False
    S["crowd"] = 0.0
    return S


def card(S, lt, b, ref):
    S["card"] = (ref, clamp(lt / 0.8) * clamp((b.d - lt) / 0.8))


# ------------------------------------------------------------------ Romans 12
def c1_card(S, lt, b):
    card(S, lt, b, "Romans 12:20")
    music(S, T(b), "hymn", 0.8)


def r1(S, lt, b):
    S["scene"] = "village"
    S["card"] = None
    e, j = S["eli"], S["jor"]
    # Jor strolls in, kicks the pot, and walks off
    walk(j, 450, lt, 0.0, 2.2, 0.9)
    j["face"] = -0.6
    j["px"] = -1
    kick = 2.4
    if kick - 0.2 < lt < kick + 0.3:
        j["footL"] = (-40 * math.sin((lt - kick + 0.2) / 0.5 * math.pi), -20)
    S["pot_broken"] = T(b, kick)
    sfx(S, T(b, kick), "splat", 0.8)
    sfx(S, T(b, kick), "chop", 0.7)
    if lt > kick + 0.4:
        j["face"] = 0.6
        j["px"] = 1
        walk(j, 1450, lt, kick + 0.6, kick + 3.0, 0.9)
    # Eli steps out, clenches, then lets it go
    e["visible"] = lt > kick + 0.6
    if e["visible"]:
        e["x"] = tw(lt, kick + 0.6, kick + 1.4, 610, 520)
        e["face"] = 0.5
        e["px"] = 1
        tc = kick + 1.6
        if tc < lt < tc + 2.2:
            e["brow"] = -1.0
            e["mouth"], e["mamt"] = "frown", 0.8
            e["shake"] = 1.2
            hand(e, -1, (-60, -70), lt, tc, tc + 0.2)
            hand(e, 1, (60, -70), lt, tc, tc + 0.2)
        elif lt >= tc + 2.2:
            e["shake"] = 0
            e["sq"] = 1 + 0.05 * math.sin(clamp((lt - tc - 2.2) / 1.6) * math.pi)
            e["brow"] = tw(lt, tc + 2.4, tc + 3.2, -1.0, 0.0)
            e["mouth"], e["mamt"] = ("smile", tw(lt, tc + 2.8, tc + 3.6, 0, 0.4))
            e["lid"] = tw(lt, tc + 2.2, tc + 2.6, 0.08, 0.9) if lt < tc + 3.4 else tw(lt, tc + 3.4, tc + 3.8, 0.9, 0.08)
            hand(e, -1, "rest", lt, tc + 2.6, tc + 3.2)
            hand(e, 1, "rest", lt, tc + 2.6, tc + 3.2)


def r2(S, lt, b):
    v = S["v"]
    e, j = S["eli"], S["jor"]
    v["dusk"] = tw(lt, 0, 1.2, 0, 0.85)
    v["rain"] = tw(lt, 0, 1.2, 0, 1)
    music(S, T(b), "rainamb", 0.0)
    sfx(S, T(b, 0.2), "water", 0.5)
    sfx(S, T(b, 3.0), "water", 0.5)
    sfx(S, T(b, 5.8), "water", 0.5)
    e.update(visible=False, shake=0, sq=1.0)
    # Jor returns, soaked and hungry, by the fence
    j["x"] = tw(lt, 0, 2.0, 1400, 960)
    j["walking"] = 0.5 if lt < 2.0 else 0
    j["face"] = -0.4
    j["px"] = -1
    j["mouth"], j["mamt"] = "frown", 0.6
    j["brow"] = 0.6
    j["shake"] = 1.0 if lt > 2.0 else 0
    hand(j, -1, (-10, -84), lt, 2.0, 2.4)
    hand(j, 1, (10, -80), lt, 2.0, 2.4)
    to = 3.0
    v["door"] = tw(lt, to, to + 0.6, 0, 1)
    if lt > to + 0.4:
        e["visible"] = True
        e.update(itemL="bread", itemR="cup", face=0.6, px=1, brow=0.2, mouth="smile", mamt=0.4, lid=0.08)
        e["hl"] = (-50, -96)
        e["hr"] = (56, -96)
        walk(e, 820, lt, to + 0.6, to + 3.0, 0.7)
        if lt > to + 3.0:
            hand(e, -1, (90, -110), lt, to + 3.0, to + 3.5)
            hand(e, 1, (100, -96), lt, to + 3.0, to + 3.5)
    sfx(S, T(b, to), "door", 0.6)
    cam_to(S, lt, 0, b.d, 820, 400, 1.25)


def r3(S, lt, b):
    e, j = S["eli"], S["jor"]
    e.update(itemL=None, itemR=None)
    hand(e, -1, "rest", lt, 0, 0.4)
    hand(e, 1, (100, -150), lt, 0.6, 1.0)
    j.update(itemL="bread", itemR="cup", shake=0, brow=0.8, mouth="flat", mamt=0, py=0.8, tears=1.0)
    j["hl"] = (-40, -96)
    j["hr"] = (40, -96)
    S["coals"] = tw(lt, 0.6, 1.6, 0, 1)
    cam_to(S, lt, 0, b.d, 900, 380, 1.5)


def r4(S, lt, b):
    e, j = S["eli"], S["jor"]
    S["coals"] = tw(lt, 0, 1.0, 1, 0.4)
    j["tears"] = 0.6
    # a stone in Eli's hand, considered, then let fall
    e["itemR"] = "stone" if lt < 2.2 else None
    hand(e, 1, (60, -130), lt, 0.2, 0.6)
    e["px"], e["py"] = 0.6, 0.6
    e["brow"] = tw(lt, 0.4, 1.0, 0.2, -0.6) if lt < 1.6 else tw(lt, 1.6, 2.2, -0.6, 0.3)
    S["dropped_stone"] = T(b, 2.2)
    sfx(S, T(b, 2.6), "thud", 0.5)
    if lt > 2.2:
        hand(e, 1, "rest", lt, 2.2, 2.6)
        e["px"], e["py"] = 1, 0
        e["mouth"], e["mamt"] = "smile", 0.4
    cam_to(S, lt, 0, 1.0, 820, 400, 1.3)


def r5(S, lt, b):
    S["v"]["watchers"] = tw(lt, 0.3, 1.5, 0, 1)
    S["v"]["rain"] = tw(lt, 0, b.d, 1, 0.3)
    S["coals"] = tw(lt, 0, 1.0, 0.4, 0)
    j = S["jor"]
    j["tears"] = 0
    j["py"] = 0
    j["px"] = -1
    j["mouth"], j["mamt"] = "smile", 0.3
    cam_to(S, lt, 0, 1.4, 640, 360, 1.0)


def r6(S, lt, b):
    v = S["v"]
    e, j = S["eli"], S["jor"]
    v["rain"] = tw(lt, 0, 1.0, 0.3, 0)
    v["dusk"] = tw(lt, 0, 2.5, 0.85, 0)
    v["sunrise"] = tw(lt, 0, 2.5, 0, 1)
    j.update(itemL=None, itemR="bread")
    hand(j, -1, (-90, -110), lt, 1.0, 1.6)
    hand(e, 1, (90, -110), lt, 1.0, 1.6)
    if lt > 1.6:
        bob = math.sin((lt - 1.6) * 8) * 6 if lt < 3.0 else 0
        e["hr"] = (90, -110 + bob)
        j["hl"] = (-90, -110 + bob)
    e["mouth"], e["mamt"] = "smile", 0.8
    j["mouth"], j["mamt"] = "smile", 0.8
    j["brow"] = 0.2
    music(S, T(b, 0.3), "hymn", 0.8)
    cam_to(S, lt, 0, b.d, 860, 400, 1.2)
    S["fade"] = tw(lt, b.d - 0.8, b.d, 0, 1)


# ------------------------------------------------------------------ John 15
def c2_card(S, lt, b):
    S["fade"] = 0
    card(S, lt, b, "John 15:12")


def j1(S, lt, b):
    S["scene"] = "room"
    S["card"] = None
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.05, 1.2)]
    js = S["jesus"]
    hand(js, -1, (-80, -150), lt, b.vs, b.vs + 0.6)
    hand(js, 1, (80, -150), lt, b.vs, b.vs + 0.6)
    for d in S["disc"]:
        d["mouth"], d["mamt"] = "smile", 0.3


def j2(S, lt, b):
    js = S["jesus"]
    hand(js, -1, (-10, -110), lt, 0, 0.6)
    hand(js, 1, (12, -104), lt, 0, 0.6)
    js["halo"] = tw(lt, 0, b.d, 0.6, 1.0)
    cam_to(S, lt, 0, b.d, 640, 380, 1.5)


def j3(S, lt, b):
    js = S["jesus"]
    js["halo"] = 1.0
    hand(js, -1, (-100, -130), lt, 0, 0.6)
    hand(js, 1, (100, -130), lt, 0, 0.6)
    d1, d2, d3, d4 = S["disc"]
    # the disciples turn to each other and embrace
    for d, other_dir in ((d1, 1), (d2, -1), (d3, 1), (d4, -1)):
        d["face"] = tw(lt, 0.3, 0.8, d["face"], 0.6 * other_dir)
        d["px"] = other_dir
        d["mouth"], d["mamt"] = "smile", 0.9
        hand(d, other_dir, (other_dir * 110, -130), lt, 0.8, 1.5)
    cam_to(S, lt, 0, 1.2, 640, 360, 1.05)
    S["fade"] = tw(lt, b.d - 0.8, b.d, 0, 1)


# ------------------------------------------------------------------ 1 Timothy 1
def c3_card(S, lt, b):
    S["fade"] = 0
    card(S, lt, b, "1 Timothy 1:12-16")


def p1(S, lt, b):
    S["scene"] = "prison"
    S["card"] = None
    p = S["paul"]
    p["hr"] = (40 + math.sin(lt * 7) * 8, -104 + abs(math.sin(lt * 5)) * 4) if lt < b.vs + 1.0 else p["hr"]
    p["py"] = 0.8 if lt < b.vs + 1.0 else -0.8
    p["face"] = 0.3
    p["mouth"], p["mamt"] = "smile", tw(lt, b.vs + 1.0, b.vs + 1.8, 0, 0.5)
    S["cam"] = [600, 380, tw(lt, 0, b.d, 1.1, 1.35)]


def p2(S, lt, b):
    S["scene"] = "street"
    S["tint"] = 0.55
    s = S["saul"]
    walk(s, 560, lt, 0, 2.2, 1.0)
    s["face"] = 0.6
    s["px"] = 1
    if lt > 2.0:
        hand(s, 1, (130, -150), lt, 2.0, 2.4)
    for i, f in enumerate(S["fleeing"]):
        f["face"] = 0.7
        f["px"] = -1
        f["mouth"], f["mamt"] = "o", 0.8
        f["brow"] = 0.8
        if lt > 1.6:
            walk(f, 1500 + i * 80, lt, 1.6 + i * 0.2, b.d, 1.6)
            f["face"] = 0.7
    S["cam"] = [640, 360, 1.0]
    sfx(S, T(b, 0.3), "stomp", 0.4)


def p3(S, lt, b):
    S["scene"] = "road"
    S["tint"] = 0.0
    s = S["saul"]
    if lt < 0.1:
        s["x"] = 300
    walk(s, 560, lt, 0.0, 1.6, 0.8)
    s["face"] = 0.4
    s["itemL"] = None
    ts = 1.4
    S["road_light"] = tw(lt, ts, ts + 0.6, 0, 1)
    sfx(S, T(b, ts), "sting", 0.6)
    sfx(S, T(b, ts), "hit", 0.6)
    if lt > ts + 0.3:
        u = ease(clamp((lt - ts - 0.3) / 0.5))
        s["yoff"] = 40 * u
        s["footL"] = (lerp(0, -30, u), lerp(0, -30, u))
        s["footR"] = (lerp(0, 30, u), lerp(0, -30, u))
        hand(s, -1, (-20, -160), lt, ts + 0.3, ts + 0.6)
        hand(s, 1, (20, -165), lt, ts + 0.3, ts + 0.6)
        s["eyes"] = "squeeze"
        s["brow"] = 0.6
        s["mouth"], s["mamt"] = "o", 0.8
    S["cam"] = [600, 380, 1.1]


def p4(S, lt, b):
    s = S["saul"]
    S["road_light"] = tw(lt, 0, b.d, 1, 0.55)
    S["grace"] = 1.0
    s["eyes"] = "open" if lt > 1.0 else "squeeze"
    s["py"] = -1
    s["tears"] = 1.0 if lt > 1.0 else 0
    s["halo"] = tw(lt, 0.8, 2.0, 0, 1)
    s["brow"] = 0.7
    s["mouth"], s["mamt"] = "smile", tw(lt, 1.4, 2.4, 0, 0.6)
    hand(s, -1, (-90, -190), lt, 1.0, 1.8)
    hand(s, 1, (90, -190), lt, 1.0, 1.8)
    sfx(S, T(b, 0.3), "sparkle", 0.6)
    cam_to(S, lt, 0, b.d, 580, 420, 1.5)
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def p5(S, lt, b):
    S["scene"] = "prison"
    S["grace"] = 0
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    p = S["paul"]
    p["py"] = 0.8 if lt < b.vs + b.vd * 0.6 else 0.3
    p["hr"] = (40 + math.sin(lt * 7) * 8, -104) if lt < b.vs + b.vd * 0.6 else p["hr"]
    if lt > b.vs + b.vd * 0.6:
        hand(p, -1, (4, -110), lt, b.vs + b.vd * 0.6, b.vs + b.vd * 0.6 + 0.5)
        p["brow"] = 0.7
        p["mouth"], p["mamt"] = "frown", 0.3
        p["tears"] = 0.6
    S["cam"] = [600, 400, 1.4]


def p6(S, lt, b):
    p = S["paul"]
    S["dawn"] = tw(lt, 0.5, b.d, 0, 1)
    hand(p, -1, (-30, -100), lt, 0, 0.6)
    p["tears"] = tw(lt, 0, 2, 0.6, 0)
    p["brow"] = tw(lt, 0, 2, 0.7, 0.2)
    p["face"] = tw(lt, 1.0, 2.0, 0.3, 0.6)
    p["px"], p["py"] = tw(lt, 1.0, 2.0, 0, 1), tw(lt, 1.0, 2.0, 0.3, -0.8)
    p["mouth"], p["mamt"] = "smile", tw(lt, 2.0, 3.0, 0, 0.7)
    if lt > b.d * 0.7:
        p["itemR"] = None
        hand(p, 1, (60, -96), lt, b.d * 0.7, b.d * 0.7 + 0.4)
    cam_to(S, lt, 0, b.d, 680, 360, 1.1)
    S["fade"] = tw(lt, b.d - 0.8, b.d, 0, 1)


# ------------------------------------------------------------------ Romans 8
def c4_card(S, lt, b):
    S["fade"] = 0
    card(S, lt, b, "Romans 8:35-39")


def q1(S, lt, b):
    S["scene"] = "journey"
    S["phase"] = "dusk"
    S["card"] = None
    tr = S["trav"]
    tr["x"] = 500
    tr["py"] = -0.9
    tr["face"] = 0.2
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.0, 1.15)]


def q2(S, lt, b):
    tr = S["trav"]
    u = clamp((lt - b.vs) / max(b.vd, 0.1))
    S["phase"] = "storm" if u < 0.4 else ("desert" if u < 0.7 else "danger")
    tr["py"] = 0
    tr["face"] = 0.5
    tr["px"] = 1
    tr["x"] = 200 + 800 * u
    tr["walking"] = 0.7
    tr["tilt"] = 0.15 if S["phase"] == "storm" else 0
    tr["brow"] = 0.6
    tr["mouth"], tr["mamt"] = "frown", 0.5
    if S["phase"] == "desert":
        hand(tr, 1, (20, -175), lt, 0, 0.01)
    else:
        hand(tr, 1, "rest", lt, 0, 0.01)
    if S["phase"] == "danger":
        tr["shake"] = 0.8
    S["cam"] = [640, 360, 1.0]
    sfx(S, T(b, b.vs + 0.3), "hit", 0.6)
    sfx(S, T(b, b.vs), "windfall", 0.5)


def q3(S, lt, b):
    S["phase"] = "dusk"
    S["sheep"] = True
    tr = S["trav"]
    tr.update(x=640, walking=0, tilt=0, shake=0, brow=0.4, mouth="flat", mamt=0, py=0.4, px=0, face=0)
    hand(tr, 1, "rest", lt, 0, 0.01)
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.15)]


def q4(S, lt, b):
    S["phase"] = "dawn"
    S["sheep"] = False
    tr = S["trav"]
    tr["py"] = -0.6
    tr["brow"] = 0.2
    tr["mouth"], tr["mamt"] = "smile", tw(lt, 0.5, 1.5, 0, 0.8)
    tr["x"] = 360
    hand(tr, -1, (-110, -230), lt, 0.8, 1.6, back_out)
    hand(tr, 1, (110, -230), lt, 0.8, 1.6, back_out)
    music(S, T(b), "hymn", 1.0)
    sfx(S, T(b, 0.4), "sparkle", 0.5)
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.15, 1.0)]


def q5(S, lt, b):
    S["phase"] = "cosmos"
    tr = S["trav"]
    hand(tr, -1, "rest", lt, 0, 0.6)
    hand(tr, 1, (6, -110), lt, 0, 0.6)
    tr["py"] = -1
    tr["mouth"], tr["mamt"] = "smile", 0.5
    S["cam"] = [640, tw(lt, 0, b.d, 360, 300), 1.0]


def q6(S, lt, b):
    S["phase"] = "glory"
    S["crowd"] = tw(lt, 0.3, 2.5, 0, 1)
    tr = S["trav"]
    tr["x"] = 520
    tr["py"] = 0
    tr["px"] = 0
    tr["mouth"], tr["mamt"] = "smile", 0.9
    hand(tr, 1, "rest", lt, 0, 0.6)
    S["cam"] = [640, 360, 1.0]
    S["fade"] = tw(lt, b.d - 1.2, b.d, 0, 0.0)


def c_end(S, lt, b):
    S["card"] = ("", 0)
    S["endfade"] = tw(lt, 0, 1.5, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(c1_card, min=4.0),
    Beat(r1, "narr", "Do not be overcome by evil, but overcome evil with good.", pre=0.6, post=1.0, min=10.0),
    Beat(r2, "narr", "If your enemy is hungry, feed him; if he is thirsty, give him something to drink.",
         pre=1.6, post=1.4, min=9.0),
    Beat(r3, "narr", "In doing this, you will heap burning coals on his head.", pre=0.4, post=1.4),
    Beat(r4, "narr", "Do not repay anyone evil for evil.", pre=0.6, post=1.2, min=3.6),
    Beat(r5, "narr", "Be careful to do what is right in the eyes of everyone.", pre=0.4, post=1.0),
    Beat(r6, "narr", "If it is possible, as far as it depends on you, live at peace with everyone.", pre=0.6,
         post=3.0, min=6.5),
    Beat(c2_card, min=4.0),
    Beat(j1, "jesus", "A new commandment I give you.", pre=1.4, post=1.0),
    Beat(j2, "jesus", "My command is this: Love each other as I have loved you.", pre=0.3, post=1.2),
    Beat(j3, min=4.5),
    Beat(c3_card, min=4.0),
    Beat(p1, "paul", "I thank Christ Jesus our Lord, who has given me strength, that he considered me "
                     "trustworthy, appointing me to his service.", pre=1.2, post=1.0),
    Beat(p2, "paul", "Even though I was once a blasphemer and a persecutor and a violent man,", pre=0.6,
         post=1.0, min=4.6),
    Beat(p3, "paul", "I was shown mercy because I acted in ignorance and unbelief.", pre=1.6, post=0.8),
    Beat(p4, "paul", "The grace of our Lord was poured out on me abundantly, along with the faith and love "
                     "that are in Christ Jesus.", pre=0.4, post=1.4),
    Beat(p5, "paul", "Here is a trustworthy saying that deserves full acceptance: Christ Jesus came into the "
                     "world to save sinners—of whom I am the worst.", pre=0.8, post=1.0),
    Beat(p6, "paul", "But for that very reason I was shown mercy so that in me, the worst of sinners, Christ "
                     "Jesus might display his immense patience as an example for those who would believe in "
                     "him and receive eternal life.", pre=0.4, post=2.4),
    Beat(c4_card, min=4.0),
    Beat(q1, "narr", "Who shall separate us from the love of Christ?", pre=1.2, post=1.0),
    Beat(q2, "narr", "Shall trouble or hardship or persecution or famine or nakedness or danger or sword?",
         pre=0.4, post=0.8),
    Beat(q3, "narr", "As it is written: “For your sake we face death all day long; we are considered as "
                     "sheep to be slaughtered.”", pre=0.6, post=1.0),
    Beat(q4, "narr", "No, in all these things we are more than conquerors through him who loved us.", pre=0.8,
         post=1.4),
    Beat(q5, "narr", "For I am convinced that neither death nor life, neither angels nor demons, neither the "
                     "present nor the future, nor any powers,", pre=0.6, post=0.3),
    Beat(q6, "narr", "neither height nor depth, nor anything else in all creation, will be able to separate us "
                     "from the love of the Lord our God.", pre=0.2, post=3.0),
    Beat(c_end, min=6.0),
]


# ------------------------------------------------------------------ drawing
def draw_village(ctx, S, t):
    v = S["v"]
    G.village(ctx, t, v["dusk"], 0, v["door"], v["watchers"], v["sunrise"])
    G.draw_pot(ctx, 470, 612, S["pot_broken"], t)
    ds = S["dropped_stone"]
    E.draw_char(ctx, S["eli"], t)
    E.draw_char(ctx, S["jor"], t)
    if ds is not None and t >= ds:
        e = S["eli"]
        dt = min(t - ds, 0.4)
        E.ellipse(ctx, e["x"] + 60, min(612 - 8, 482 + 900 * dt * dt), 15, 12)
        E.fill_stroke(ctx, "#8A8178", "#3A3530", 2.5)
    if S["coals"] > 0:
        j = S["jor"]
        G.draw_coals(ctx, j["x"], j["y"] - 230, S["coals"], t)
    if v["rain"] > 0:
        import random as _r
        rnd = _r.Random(1)
        for i in range(220):
            x = rnd.uniform(-100, 1280)
            sp = rnd.uniform(700, 1000)
            y = (rnd.uniform(0, 720) + t * sp) % 760 - 40
            ctx.move_to(x, y)
            ctx.line_to(x - 6, y + 22)
        E.src(ctx, "#B8C8E0", 0.45 * v["rain"])
        ctx.set_line_width(1.6)
        ctx.stroke()


def draw_room(ctx, S, t):
    G.upper_room(ctx, t)
    for d in S["disc"]:
        E.draw_char(ctx, d, t)
    E.draw_char(ctx, S["jesus"], t)
    G.supper_table(ctx, t)


def draw_prison(ctx, S, t):
    G.prison(ctx, t, S["dawn"])
    E.draw_char(ctx, S["paul"], t)
    G.writing_desk(ctx, t, 600)


def draw_street(ctx, S, t):
    G.city_street(ctx, t)
    for f in S["fleeing"]:
        E.draw_char(ctx, f, t)
    E.draw_char(ctx, S["saul"], t)


def draw_road(ctx, S, t):
    G.damascus_road(ctx, t, 0)
    E.draw_char(ctx, S["saul"], t)
    if S["road_light"] > 0:
        ctx.move_to(500, -20)
        ctx.line_to(700, -20)
        ctx.line_to(760, 640)
        ctx.line_to(360, 640)
        ctx.close_path()
        g = cairo.LinearGradient(0, 0, 0, 640)
        g.add_color_stop_rgba(0, 1, 1, 0.95, 0.85 * S["road_light"])
        g.add_color_stop_rgba(1, 1, 1, 0.9, 0.35 * S["road_light"])
        ctx.set_source(g)
        ctx.fill()
    if S["grace"] > 0:
        import random as _r
        rnd = _r.Random(2)
        for i in range(60):
            x = rnd.uniform(420, 720)
            y = (rnd.uniform(0, 640) + t * rnd.uniform(60, 140)) % 640
            E.sparkle(ctx, x, y, rnd.uniform(3, 8), "#FFE7A8", 0.9)


def draw_journey(ctx, S, t):
    G.journey(ctx, t, S["phase"])
    if S["sheep"]:
        for i, (x, y) in enumerate(((260, 640), (380, 660), (500, 630), (820, 650), (940, 640), (1060, 662),
                                    (720, 668))):
            G.draw_sheep(ctx, x, y, 1.3, t, i)
    if S["crowd"] > 0:
        a = S["crowd"]
        crowd = [(K_ELI, 130), (K_JOR, 250), (K_D1, 370), (K_D3, 900), (K_PAUL, 1020), (K_D2, 1140)]
        for k, x in crowd:
            c = G.new_person(k, x, mouth="smile", mamt=0.8, alpha=a, py=-0.5, face=0.0)
            if k == K_PAUL:
                c["itemR"] = None
            E.draw_char(ctx, c, t)
    E.draw_char(ctx, S["trav"], t)


def draw(ctx, S, t):
    sc = S["scene"]
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    if sc == "village":
        draw_village(ctx, S, t)
    elif sc == "room":
        draw_room(ctx, S, t)
    elif sc == "prison":
        draw_prison(ctx, S, t)
    elif sc == "street":
        draw_street(ctx, S, t)
    elif sc == "road":
        draw_road(ctx, S, t)
    elif sc == "journey":
        draw_journey(ctx, S, t)
    ctx.restore()
    if S["tint"] > 0 and sc == "street":
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_HSL_SATURATION)
        ctx.set_source_rgba(0.5, 0.5, 0.5, S["tint"])
        ctx.paint()
        ctx.restore()
        ctx.set_source_rgba(0.45, 0.3, 0.15, 0.25)
        ctx.paint()
    g = cairo.RadialGradient(640, 360, 300, 640, 360, 820)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(g)
    ctx.paint()
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
    cd = S["card"]
    if cd and cd[0]:
        G.chapter_card(ctx, t, cd[0], cd[1])
    ef = S.get("endfade", 0)
    if ef > 0:
        ctx.push_group()
        E.src(ctx, "#0E0A06")
        ctx.paint()
        refs = ["Romans 12:20", "John 15:12", "1 Timothy 1:12-16", "Romans 8:35-39"]
        for i, r in enumerate(refs):
            E.text(ctx, r, 640, 270 + i * 54, 34, "#F2DCA8")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ef)
