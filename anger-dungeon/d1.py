"""Part 1: Into the Dark."""
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

TUNNEL = (0, 0, 3400, 720)
CAVERN = (0, -360, 2600, 900)
VINES = (900, 1300)
WEBS = (1900, 2250)
DOOR_X = 3000
HOLE = (2010, 2260)


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
    S["anger"] = G.new_warrior(-160)
    S["card"] = 1.0
    S["vine_cut"] = [None, None]
    S["web_torn"] = [None, None]
    S["door"] = dict(burst=None, rattle=0.0)
    S["torch_lit"] = 1.0
    S["torch_proj"] = None
    S["eyes"] = None
    S["creature"] = None
    S["slab"] = 0.0
    S["collapse"] = None
    S["fall"] = None
    S["far_glow"] = 0.0
    S["steam"] = None
    return S


def follow(S, a, lead=160, y=420, z=1.0):
    S["cam"] = [a["x"] + lead, y, z]


# ------------------------------------------------------------------ tunnel
def a_title(S, lt, b):
    music(S, T(b), "epic", 0.8)
    ambience(S, TOTAL)
    sfx(S, T(b, 0.5), "hit", 0.7)


def a_enter(S, lt, b):
    a = S["anger"]
    S["card"] = tw(lt, 0, 1.0, 1.0, 0.0)
    walk(a, 360, lt, 0.4, 4.6, 0.8)
    a["face"] = 0.6
    a["px"] = 0.8
    follow(S, a, 200)
    for k in range(int(4.2 / 0.62)):
        sfx(S, T(b, 0.6 + k * 0.62), "step", 0.6)


def a_face(S, lt, b):
    a = S["anger"]
    a["face"] = tw(lt, 0, 0.6, 0.6, 0.2)
    a["px"] = tw(lt, 0, 0.6, 0.8, 0.1)
    cam_to(S, lt, 0, 1.2, a["x"] + 10, 470, 2.3)
    hand(a, 1, (110, -150), lt, 0.8, 1.4)
    a["wandR"] = tw(lt, 0.8, 1.4, -55, -95)
    tg = b.vs + b.vd * 0.35
    a["glint"] = math.sin(clamp((lt - tg) / 0.6) * math.pi) if lt > tg else 0
    sfx(S, T(b, tg), "slash", 0.4)


def a_vines_n(S, lt, b):
    a = S["anger"]
    hand(a, 1, (112, -110), lt, 0, 0.5)
    a["wandR"] = tw(lt, 0, 0.5, a["wandR"], -55)
    a["face"] = 0.5
    a["px"] = 0.8
    walk(a, 730, lt, 0.5, b.d - 0.2, 0.8)
    cam_to(S, lt, 0, 1.0, a["x"] + 200, 420, 1.0)
    if lt > 1.0:
        follow(S, a, 200)
    for k in range(int((b.d - 0.7) / 0.62)):
        sfx(S, T(b, 0.7 + k * 0.62), "step", 0.5)


def slash_arm(a, lt, t0, dur=0.45):
    """Overhead slash: wind up then cut down."""
    if lt < t0 - 0.3:
        return
    if lt < t0:
        hand(a, 1, (40, -250), lt, t0 - 0.3, t0)
        a["wandR"] = tw(lt, t0 - 0.3, t0, a["wandR"], -120)
    elif lt < t0 + dur:
        u = (lt - t0) / dur
        a["hr"] = (lerp(40, 140, ease_out(u)), lerp(-250, -60, ease_out(u)))
        a["wandR"] = lerp(-120, 40, ease_out(u))
    else:
        hand(a, 1, (112, -110), lt, t0 + dur, t0 + dur + 0.4)
        a["wandR"] = tw(lt, t0 + dur, t0 + dur + 0.4, 40, -55)


def a_chop(S, lt, b):
    a = S["anger"]
    follow(S, a, 200)
    slash_arm(a, lt, 0.5)
    S["vine_cut"][0] = T(b, 0.62)
    sfx(S, T(b, 0.45), "slash", 0.8)
    sfx(S, T(b, 0.6), "chop", 0.8)
    sfx(S, T(b, 0.7), "rustle", 0.7)
    walk(a, 1130, lt, 1.4, 3.0, 0.8)
    for k in range(3):
        sfx(S, T(b, 1.5 + k * 0.55), "step", 0.5)
    slash_arm(a, lt, 3.5)
    S["vine_cut"][1] = T(b, 3.62)
    sfx(S, T(b, 3.45), "slash", 0.8)
    sfx(S, T(b, 3.6), "chop", 0.8)
    sfx(S, T(b, 3.7), "rustle", 0.7)
    a["brow"] = -0.6


def a_webs_n(S, lt, b):
    a = S["anger"]
    walk(a, 1740, lt, 0.2, b.d - 0.2, 0.8)
    follow(S, a, 200)
    for k in range(int((b.d - 0.4) / 0.62)):
        sfx(S, T(b, 0.4 + k * 0.62), "step", 0.5)


def swipe(a, lt, t0):
    if lt < t0 - 0.25:
        return
    if lt < t0:
        hand(a, 1, (-20, -190), lt, t0 - 0.25, t0)
        a["wandR"] = tw(lt, t0 - 0.25, t0, a["wandR"], 120)
    elif lt < t0 + 0.35:
        u = (lt - t0) / 0.35
        a["hr"] = (lerp(-20, 150, ease_out(u)), lerp(-190, -150, ease_out(u)))
        a["wandR"] = lerp(120, 70, u)
    else:
        hand(a, 1, (112, -110), lt, t0 + 0.35, t0 + 0.75)
        a["wandR"] = tw(lt, t0 + 0.35, t0 + 0.75, 70, -55)


def a_swipe(S, lt, b):
    a = S["anger"]
    follow(S, a, 200)
    swipe(a, lt, 0.4)
    S["web_torn"][0] = T(b, 0.5)
    sfx(S, T(b, 0.45), "webtear", 0.8)
    walk(a, 2090, lt, 1.2, 2.6, 0.8)
    for k in range(3):
        sfx(S, T(b, 1.3 + k * 0.5), "step", 0.5)
    swipe(a, lt, 3.0)
    S["web_torn"][1] = T(b, 3.1)
    sfx(S, T(b, 3.05), "webtear", 0.8)


def a_door_n(S, lt, b):
    a = S["anger"]
    walk(a, 2830, lt, 0.2, b.d - 0.2, 0.8)
    follow(S, a, 160)
    for k in range(int((b.d - 0.4) / 0.62)):
        sfx(S, T(b, 0.4 + k * 0.62), "step", 0.5)


def a_try(S, lt, b):
    a = S["anger"]
    follow(S, a, 160)
    hand(a, 1, (112, -190), lt, 0.1, 0.5)
    a["itemR"] = "sword" if lt < 0.1 else None
    a["blade"] = 128
    S["door"]["rattle"] = 1.0 if 0.5 < lt < 1.7 else 0.0
    if 0.5 < lt < 1.7:
        a["hr"] = (112 + math.sin(lt * 40) * 5, -190)
    if lt > 1.8:
        hand(a, 1, (112, -110), lt, 1.8, 2.2)
        a["itemR"] = "sword"
    sfx(S, T(b, 0.5), "rattle", 0.9)
    a["brow"] = -0.8


def a_backup(S, lt, b):
    a = S["anger"]
    a["x"] = tw(lt, 0.8, b.d - 0.2, 2830, 2470, linear)
    if 0.8 < lt < b.d - 0.2:
        a["walking"] = 0.6
    for k in range(3):
        sfx(S, T(b, 1.0 + k * (b.d - 1.2) / 3), "step", 0.6)
    a["brow"] = tw(lt, 0, 1, -0.8, -1.2)
    cam_to(S, lt, 0, 1.5, 2700, 440, 1.25)


def a_charge(S, lt, b):
    a = S["anger"]
    hit = 1.15
    if lt < 0.35:
        a["sq"] = tw(lt, 0, 0.35, 1.0, 0.93)
        a["tilt"] = tw(lt, 0, 0.35, 0, 0.2)
    elif lt < hit:
        a["sq"] = 1.0
        a["tilt"] = 0.32
        a["x"] = tw(lt, 0.35, hit, 2470, 2870, ease_in)
        a["walking"] = 2.2
        hand(a, -1, (-30, -170), lt, 0.35, 0.6)
    else:
        a["x"] = tw(lt, hit, hit + 1.4, 2870, 3250, ease_out)
        a["tilt"] = tw(lt, hit, hit + 0.8, 0.32, 0.0)
        a["walking"] = 1.2 if lt < hit + 1.3 else 0
    for k in range(4):
        sfx(S, T(b, 0.4 + k * 0.19), "step", 0.8)
    S["door"]["burst"] = T(b, hit)
    sfx(S, T(b, hit), "explosion", 1.0)
    music(S, T(b, hit), "epic", 1.0)
    S["shake"] = clamp(1 - (lt - hit) / 0.9) * 1.6 if lt > hit else 0
    S["flash"] = clamp(1 - (lt - hit) / 0.35) if lt > hit else 0
    S["burst_t"] = T(b, hit)
    cam_to(S, lt, 0, hit, 2760, 430, 1.1)
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


# ------------------------------------------------------------------ cavern
def a_reveal(S, lt, b):
    a = S["anger"]
    S["scene"] = "cavern"
    S["amb"] = tw(lt, 0, b.d, 0.6, 0.72)
    S["fade"] = tw(lt, 0, 0.6, 1, 0)
    S["shake"] = 0
    a.update(x=tw(lt, 0, 3.0, 40, 240), tilt=0, face=0.6, px=0.6, py=-0.6)
    a["walking"] = 0.8 if lt < 3.0 else 0
    a["brow"] = 0.2
    S["cam"] = [tw(lt, 0, b.d, 1300, 1200), tw(lt, 0, b.d, 180, 200), 0.667]
    sfx(S, T(b, 0.2), "sting", 0.5)


def a_search(S, lt, b):
    a = S["anger"]
    a["py"] = 0
    a["brow"] = -0.3
    S["amb"] = tw(lt, 0, 2.0, 0.72, 0.84)
    cam_to(S, lt, 0, 1.6, a["x"] + 150, 420, 1.0)
    if lt > 1.6:
        S["cam"] = [a["x"] + 150, 420, 1.0]
    walk(a, 700, lt, 0.6, 2.8, 0.7)
    seq = [(2.8, -0.7, -1.0), (3.8, 0.6, 1.0)]
    for tk, f, p in seq:
        if lt > tk:
            a["face"] = tw(lt, tk, tk + 0.4, a["face"], f)
            a["px"] = tw(lt, tk, tk + 0.4, a["px"], p)
    walk(a, 1000, lt, 4.4, b.d - 0.1, 0.7)
    hand(a, -1, (-40, -250), lt, 2.8, 3.2)
    for k in range(int(b.d / 0.7)):
        sfx(S, T(b, 0.7 + k * 0.7), "step", 0.45)


def a_eyes(S, lt, b):
    a = S["anger"]
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], 1350), 400, 1.0]
    a["face"] = tw(lt, 0, 0.5, a["face"], -0.8)
    a["px"] = tw(lt, 0, 0.5, a["px"], -1.0)
    hand(a, -1, (-90, -230), lt, 0, 0.5)
    ap, gone = 1.0, 3.2
    e = dict(x=1760, y=300, a=0.0, look=0.0)
    if ap < lt < gone + 0.6:
        e["a"] = tw(lt, ap, ap + 0.4, 0, 1) if lt < gone else tw(lt, gone, gone + 0.5, 1, 0)
        e["look"] = -1 if lt < 2.2 else 1
        if lt > 2.6:
            e["x"] = tw(lt, 2.6, gone + 0.5, 1760, 1830)
        if 1.9 < lt < 2.05:
            e["a"] *= 0.1
    S["eyes"] = e if lt < b.d else None
    music(S, T(b), None, 0)
    sfx(S, T(b, ap), "sting", 0.7)
    sfx(S, T(b, 2.7), "scurry", 0.6)


def a_sees_him(S, lt, b):
    a = S["anger"]
    S["eyes"] = None
    a["face"] = tw(lt, 0.4, 0.9, a["face"], 0.6)
    a["px"] = tw(lt, 0.4, 0.9, a["px"], 0.8)
    hand(a, -1, (-64, -250), lt, 0.4, 0.9)
    walk(a, 1280, lt, 1.0, b.d - 0.1, 0.7)
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], a["x"] + 150), 420, 1.0]
    if lt > 1.0:
        S["cam"] = [a["x"] + 150, 420, 1.0]
    music(S, T(b), "tense", 0.8)
    for k in range(int((b.d - 1.0) / 0.7)):
        sfx(S, T(b, 1.1 + k * 0.7), "step", 0.45)


def a_shift(S, lt, b):
    a = S["anger"]
    S["cam"] = [a["x"] + 150, 420, 1.0]
    walk(a, 1340, lt, 0, 0.8, 0.6)
    ts = b.vs + b.vd + 0.1
    if lt > ts:
        S["slab"] = tw(lt, ts, ts + 0.2, 0, 1)
        a["tilt"] = math.sin(clamp((lt - ts) / 1.2) * math.pi) * 0.28
        a["mouth"], a["mamt"] = "o", 0.5
        hand(a, 1, (140, -230), lt, ts, ts + 0.2)
        a["wide"] = tw(lt, ts, ts + 0.2, 0, 0.6)
        if lt > ts + 0.15:
            a["itemL"] = None
            hand(a, -1, (-120, -200), lt, ts, ts + 0.2)
    x0, y0 = G.torch_world(G.new_warrior(1340, hl=(-64, -250), wandL=-80))
    S["torch_proj"] = dict(t0=T(b, ts + 0.15), t1=T(b, ts + 1.15), x0=x0 - 40, y0=y0, x1=1560, y1=636)
    S["splash_t"] = T(b, ts + 1.15)
    sfx(S, T(b, ts), "stoneshift", 0.9)
    sfx(S, T(b, ts + 0.15), "torchwhoosh", 0.8)
    sfx(S, T(b, ts + 1.15), "splashbig", 0.9)
    sfx(S, T(b, ts + 1.2), "hiss", 0.9)
    music(S, T(b, ts + 1.15), None, 0)
    if lt > ts + 1.15:
        S["torch_lit"] = 0.0
        S["amb"] = 0.9
    cam_to(S, lt, ts, ts + 1.1, 1450, 440, 1.0)


def a_dark(S, lt, b):
    a = S["anger"]
    a["tilt"] = 0
    a["mouth"], a["mamt"] = "flat", 0
    a["wide"] = tw(lt, 0, 0.5, 0.6, 0.2)
    hand(a, 1, (112, -110), lt, 0, 0.6)
    hand(a, -1, "rest", lt, 0, 0.6)
    a["itemL"] = None
    seq = [(1.0, -0.7, -1.0), (2.6, 0.7, 1.0), (4.0, 0.0, 0.0)]
    for tk, f, p in seq:
        if lt > tk:
            a["face"] = tw(lt, tk, tk + 0.8, a["face"], f)
            a["px"] = tw(lt, tk, tk + 0.8, a["px"], p)
    cam_to(S, lt, 0, b.d, a["x"], 470, 1.6)


def a_behind(S, lt, b):
    a = S["anger"]
    a["face"], a["px"] = 0.5, 0.9
    cam_to(S, lt, 0, 1.0, a["x"] - 60, 440, 1.25)
    c0, c1 = 0.6, 2.8
    if c0 < lt < c1:
        u = (lt - c0) / (c1 - c0)
        S["creature"] = dict(x=lerp(a["x"] - 520, a["x"] + 360, u), y=560, s=0.55, face=1, walk=1.0,
                             shadow=True, glow=0.9)
    else:
        S["creature"] = None
    sfx(S, T(b, c0 + 0.2), "scurry", 0.5)
    sfx(S, T(b, c0 + 1.2), "scurry", 0.4)


def a_look(S, lt, b):
    a = S["anger"]
    S["creature"] = None
    a["face"] = tw(lt, 0.2, 0.7, 0.5, -0.9)
    a["px"] = tw(lt, 0.2, 0.6, 0.9, -1.0)
    a["brow"] = -0.8
    a["lid"] = tw(lt, 0.6, 1.2, 0, 0.3)
    sfx(S, T(b, 0.2), "clank", 0.4)


def a_nothing(S, lt, b):
    a = S["anger"]
    a["face"] = tw(lt, b.d - 1.0, b.d - 0.4, a["face"], 0.5)
    a["px"] = tw(lt, b.d - 1.0, b.d - 0.4, a["px"], 0.9)
    a["lid"] = tw(lt, b.d - 1.0, b.d - 0.4, 0.3, 0.0)


def a_continue(S, lt, b):
    a = S["anger"]
    S["far_glow"] = tw(lt, 0, 1.5, 0, 1)
    walk(a, 1990, lt, 0.4, b.d, 0.45)
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], a["x"] + 220), 430, tw(lt, 0, 1.0, S["cam"][2], 1.0)]
    if lt > 1.0:
        S["cam"] = [a["x"] + 220, 430, 1.0]
    for k in range(int((b.d - 0.6) / 0.9)):
        sfx(S, T(b, 0.6 + k * 0.9), "step", 0.35)
    music(S, T(b), "tense", 0.6)


def a_wrong(S, lt, b):
    a = S["anger"]
    walk(a, 2075, lt, 0.0, 0.6, 0.45)
    S["cam"] = [a["x"] + 150, 430, 1.0]
    tc = b.vs + b.vd + 0.2
    S["collapse"] = T(b, tc)
    sfx(S, T(b, tc - 0.15), "stoneshift", 0.7)
    sfx(S, T(b, tc), "crumble", 1.0)
    music(S, T(b, tc), None, 0)
    if lt > tc:
        u = clamp((lt - tc) / 0.35)
        a["y"] = lerp(E.GROUND, 606 + 275, ease_in(u))
        a["face"] = 0.0
        a["px"], a["py"] = 0.0, -1.0
        a["wide"] = 1.0
        a["itemR"] = None
        a["hl"] = (-60, -275)
        a["hr"] = (54, -275)
        a["x"] = tw(lt, tc, tc + 0.35, 2075, 2058)
        S["shake"] = clamp(1 - (lt - tc) / 1.0) * 1.2
    cam_to(S, lt, tc, tc + 0.8, 2060, 620, 1.5)


def a_heavy(S, lt, b):
    a = S["anger"]
    a["y"] = 881
    a["wide"] = tw(lt, 0, 1, 1.0, 0.0)
    a["py"] = -0.6
    a["brow"] = -1.0
    a["mouth"], a["mamt"] = "tight", 1.0
    S["shake"] = 0
    # fingers slip, one hand loses grip and grabs again
    slip = [(1.2, -1), (3.4, 1), (5.4, -1)]
    a["hl"], a["hr"] = (-60, -275), (54, -275)
    a["y"] = 881 + min(lt, b.d) * 4
    for ts, side in slip:
        if ts < lt < ts + 0.6:
            u = (lt - ts) / 0.6
            off = math.sin(u * math.pi) * 40
            if side < 0:
                a["hl"] = (-60, -275 + off)
            else:
                a["hr"] = (54, -275 + off)
        sfx(S, T(b, ts), "stoneshift", 0.35)
    S["slip_dust"] = [T(b, ts) for ts, _ in slip]
    cam_to(S, lt, 0, b.d, 2040, 640, 1.8)


def a_letgo(S, lt, b):
    a = S["anger"]
    a["mouth"], a["mamt"] = "flat", 0
    a["brow"] = 0.0
    a["lid"] = tw(lt, 0.8, 1.8, 0, 0.35)
    a["py"] = -0.8
    tg = 2.2
    if lt > tg:
        a["y"] = 905 + (lt - tg) ** 2 * 900
        a["hl"] = (-60, -240)
        a["hr"] = (54, -240)
    sfx(S, T(b, tg), "stoneshift", 0.5)
    sfx(S, T(b, tg + 0.2), "windfall", 0.6)
    S["shake"] = 0
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_falltop(S, lt, b):
    S["scene"] = "falltop"
    S["fade"] = tw(lt, 0, 0.4, 1, 0)
    a = S["anger"]
    a.update(lid=0.35, wide=0, mouth="flat", mamt=0, brow=0.0, py=-1.0, px=0.0, face=0.0)
    S["fall"] = dict(u=clamp(lt / (b.d + 4.0)))
    music(S, T(b), "drone", 0.7)


def a_falltop2(S, lt, b):
    pb = IDX["ft"]
    S["fall"] = dict(u=clamp((S["t"] - pb.start) / (pb.d + b.d)))
    a = S["anger"]
    a["lid"] = tw(lt, 0.5, 2.0, 0.35, 1.0)


def a_continued(S, lt, b):
    S["endcard"] = tw(lt, 0, 1.0, 0, 1)
    sfx(S, T(b, 0.1), "hit", 0.9)
    music(S, T(b, 0.5), "epic", 0.7)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Deep beneath the mountain, where no light has touched the stone for a "
                          "thousand years...", pre=1.6, post=0.6, min=6.5),
    Beat(a_enter, "narr", "...one warrior walks alone.", pre=1.6, post=1.8, min=5.0),
    Beat(a_face, "narr", "His name is Anger. Armor of iron. A sword that has never lost a fight. "
                         "And a face that has never once smiled.", post=1.2),
    Beat(a_vines_n, "narr", "The path ahead is choked with vines.", post=0.6, min=3.6),
    Beat(a_chop, min=5.0),
    Beat(a_webs_n, "narr", "Spider webs, thick as curtains.", post=0.8, min=3.4),
    Beat(a_swipe, min=4.0),
    Beat(a_door_n, "narr", "At last, a door.", pre=0.4, post=0.8, min=3.4),
    Beat(a_try, min=2.6),
    Beat(a_backup, "narr", "Locked. Anger takes three steps back.", post=0.8, min=3.6),
    Beat(a_charge, min=3.4),
    Beat(a_reveal, "narr", "Beyond the door lies a cavern so vast, the torchlight cannot find "
                           "the ceiling.", pre=1.0, post=1.6),
    Beat(a_search, "narr", "Anger searches the cavern. Every shadow. Every stone.", post=1.5, min=6.5),
    Beat(a_eyes, min=4.4),
    Beat(a_sees_him, "narr", "He does not see it. But something sees him.", post=0.8, min=4.0),
    Beat(a_shift, "narr", "Then, a stone shifts beneath his feet.", post=2.6),
    Beat(a_dark, "narr", "Darkness. And silence.", pre=2.2, post=2.4, min=6.0),
    Beat(a_behind, "narr", "Something moves behind him.", pre=0.4, post=1.6, min=3.2),
    Beat(a_look, min=2.2),
    Beat(a_nothing, "narr", "Nothing there.", post=1.2, min=2.6),
    Beat(a_continue, "narr", "Slowly, carefully, he moves toward the door on the far side.", post=0.8,
         min=5.0),
    Beat(a_wrong, "narr", "One wrong step.", pre=0.3, post=2.4),
    Beat(a_heavy, "narr", "He is a big man. His armor is heavy. And the stone is slick with dust.",
         post=1.6, min=7.0),
    Beat(a_letgo, "anger", "Hm.", rate="-20%", post=3.0, min=3.8),
    Beat(a_falltop, "narr", "He does not scream. He does not struggle.", pre=1.0, post=0.6, id="ft"),
    Beat(a_falltop2, "narr", "He only falls.", post=2.6),
    Beat(a_continued, "narr", "To be continued.", pre=1.2, post=2.6, min=5.0),
]


# ------------------------------------------------------------------ drawing
def draw_vines(ctx, x, t, tc):
    rnd = random.Random(int(x))
    for i in range(9):
        sx = x + (i - 4) * 16 + rnd.uniform(-5, 5)
        sway = math.sin(t * 1.3 + i) * 6
        cut_y = 330 + rnd.uniform(-40, 40)
        dt = (t - tc) if tc is not None and t >= tc else None
        # upper part (always)
        ytop, ybot = 50, (cut_y if dt is not None else 606)
        ctx.move_to(sx, ytop)
        ctx.curve_to(sx + sway, ytop + 120, sx - sway, ybot - 120, sx + sway * 0.5, ybot)
        E.src(ctx, "#2F5A26")
        ctx.set_line_width(6)
        ctx.stroke()
        for j in range(int((ybot - ytop) / 34)):
            ly = ytop + 14 + j * 34 + rnd.uniform(-10, 10)
            side = 1 if (j + i) % 2 else -1
            ctx.save()
            ctx.translate(sx + side * 6 + sway * (ly - ytop) / 600, ly)
            ctx.rotate(side * 0.7 + rnd.uniform(-0.3, 0.3))
            ctx.move_to(0, 0)
            ctx.curve_to(6, -8, 18, -6, 22, 0)
            ctx.curve_to(18, 6, 6, 8, 0, 0)
            E.src(ctx, rnd.choice(["#4E8A3A", "#3E7A2E", "#5E9A44"]))
            ctx.fill()
            ctx.restore()
        if dt is not None and dt < 1.6:
            fall = 0.5 * 1400 * dt * dt
            a = clamp(1 - dt / 1.6)
            y0, y1 = cut_y + fall, 606 + fall * 0.2
            y1 = min(606 + 10, cut_y + (606 - cut_y) + fall)
            ctx.move_to(sx + dt * 40 * (1 if i % 2 else -1), min(y0, 600))
            ctx.line_to(sx + dt * 60 * (1 if i % 2 else -1), min(y1, 620))
            E.src(ctx, "#2F5A26", a)
            ctx.set_line_width(6)
            ctx.stroke()
        elif dt is not None:
            ctx.move_to(sx - 20, 612)
            ctx.line_to(sx + 30, 616)
            E.src(ctx, "#2F5A26", 0.8)
            ctx.set_line_width(5)
            ctx.stroke()


def draw_web(ctx, x, t, tt):
    cx, cy = x, 340
    dt = (t - tt) if tt is not None and t >= tt else None
    if dt is not None and dt > 1.6:
        # tatters at the edges
        for k in range(4):
            ctx.move_to(x - 40 + k * 26, 64)
            ctx.line_to(x - 46 + k * 26 + math.sin(t + k) * 6, 110)
            E.src(ctx, "#E8E8F0", 0.4)
            ctx.set_line_width(1.5)
            ctx.stroke()
        return
    a = 0.75 if dt is None else 0.75 * (1 - dt / 1.6)
    off = 0 if dt is None else dt * 120
    ctx.save()
    if dt is not None:
        ctx.translate(off, dt * 60)
        ctx.rotate(dt * 0.3)
    for k in range(14):
        ang = k * 2 * math.pi / 14
        ctx.move_to(cx, cy)
        ctx.line_to(cx + math.cos(ang) * 260, cy + math.sin(ang) * 270)
    for r in range(30, 270, 28):
        for k in range(15):
            ang = k * 2 * math.pi / 14
            px, py = cx + math.cos(ang) * r, cy + math.sin(ang) * r
            (ctx.move_to if k == 0 else ctx.line_to)(px, py)
    E.src(ctx, "#E8E8F0", a)
    ctx.set_line_width(1.6)
    ctx.stroke()
    ctx.restore()


def draw_slab(ctx, t, s):
    ctx.save()
    ctx.translate(1340, 606)
    ctx.rotate(-0.18 * s)
    E.rrect(ctx, -60, -6, 120, 18, 4)
    E.fill_stroke(ctx, "#4A4242", "#1A1512", 3)
    ctx.restore()


def draw_hole(ctx, S, t):
    tc = S["collapse"]
    if tc is None or t < tc:
        return
    x0, x1 = HOLE
    ctx.move_to(x0, 604)
    for i in range(9):
        ctx.line_to(x0 + (x1 - x0) * i / 8, 604 + (6 if i % 2 else -4))
    ctx.line_to(x1, 740)
    ctx.line_to(x0, 740)
    ctx.close_path()
    E.src(ctx, "#000000")
    ctx.fill()
    G.debris(ctx, (x0 + x1) / 2, 610, tc, t, n=26, seed=7, vx=(-120, 120), vy=(-120, 60), floor=900,
             size=(10, 26), g=1400)


def draw_tunnel(ctx, S, t):
    a = S["anger"]
    ctx.save()
    apply_cam(ctx, S, t, TUNNEL)
    ctx.set_source_surface(G.tunnel_bg(), 0, 0)
    ctx.paint()
    G.draw_door(ctx, DOOR_X, t, S["door"])
    for i, vx in enumerate(VINES):
        draw_vines(ctx, vx, t, S["vine_cut"][i])
    for i, wx in enumerate(WEBS):
        draw_web(ctx, wx, t, S["web_torn"][i])
    E.draw_char(ctx, a, t)
    bt = S.get("burst_t")
    if bt is not None:
        G.dust(ctx, DOOR_X, 560, bt, t, n=14, spread=260, dur=2.4, seed=4, rise=120)
        G.debris(ctx, DOOR_X, 450, bt, t, n=20, seed=3, vx=(100, 900), vy=(-500, -50), floor=650)
    tx, ty = G.torch_world(a)
    fl = 1 + 0.06 * math.sin(t * 13) + 0.04 * math.sin(t * 31)
    lights = [(tx, ty + 20, 430 * fl, 1.0)]
    if bt is not None and t > bt:
        lights.append((DOOR_X + 120, 380, 500, clamp(1 - (t - bt) / 1.5)))
    G.darkness(ctx, S["amb"], lights)
    G.warm_glow(ctx, tx, ty + 10, 300 * fl, 1.0)
    ctx.restore()


def draw_cavern(ctx, S, t):
    a = S["anger"]
    ctx.save()
    apply_cam(ctx, S, t, CAVERN)
    ctx.set_source_surface(G.cavern_bg(), 0, -360)
    ctx.paint()
    G.draw_pool(ctx, t, S["torch_lit"])
    if S["far_glow"] > 0:
        E.rrect(ctx, 2455, 420, 8, 186, 3)
        E.src(ctx, "#9FE4C8", 0.8 * S["far_glow"])
        ctx.fill()
    draw_slab(ctx, t, S["slab"])
    e = S["eyes"]
    if e:
        G.glowing_eyes(ctx, e["x"], e["y"], e["a"], t, 0.9, e["look"])
    c = S["creature"]
    if c:
        G.draw_creature(ctx, c["x"], c["y"], c["s"], c["face"], t, c)
    draw_hole(ctx, S, t)
    if S["collapse"] is not None and t >= S["collapse"]:
        E.rrect(ctx, HOLE[0] - 210, 598, 216, 16, 5)
        E.fill_stroke(ctx, "#4A4242", "#1A1512", 3)
    E.draw_char(ctx, a, t)
    if S["collapse"] is not None:
        x0, x1 = HOLE
        for ts in S.get("slip_dust", []):
            G.dust(ctx, x0, 610, ts, t, n=5, spread=30, dur=1.2, seed=int(ts * 10), rise=-80, col="#BBB0A2")
    tp = S["torch_proj"]
    lights = []
    if tp and tp["t0"] <= t < tp["t1"]:
        u = (t - tp["t0"]) / (tp["t1"] - tp["t0"])
        px = lerp(tp["x0"], tp["x1"], u)
        py = lerp(tp["y0"], tp["y1"], u) - math.sin(u * math.pi) * 220
        ctx.save()
        ctx.translate(px, py)
        ctx.rotate(u * 9)
        ctx.move_to(-30, 0)
        ctx.line_to(30, 0)
        E.src(ctx, "#5A3A22")
        ctx.set_line_width(10)
        ctx.stroke()
        ctx.restore()
        G.flame(ctx, px, py, t, 0.9)
        lights.append((px, py, 400, 1.0))
        G.warm_glow(ctx, px, py, 280, 1.0)
    elif S["torch_lit"] > 0:
        tx, ty = G.torch_world(a)
        fl = 1 + 0.06 * math.sin(t * 13) + 0.04 * math.sin(t * 31)
        lights.append((tx, ty + 20, 460 * fl, 1.0))
    st = S.get("splash_t")
    if st is not None and st <= t < st + 2.5:
        dt = t - st
        G.dust(ctx, 1560, 630, st, t, n=8, spread=60, col="#DDE6EE", dur=2.5, seed=8, rise=160)
        for i in range(10):
            ang = -math.pi * (0.15 + 0.7 * i / 9)
            sp = 260
            x = 1560 + math.cos(ang) * sp * dt
            y = 636 + math.sin(ang) * sp * dt + 900 * dt * dt
            if y < 650:
                E.ellipse(ctx, x, y, 4, 6)
                E.src(ctx, "#9FE4FF", 0.8)
                ctx.fill()
    # faint cold light so silhouettes still read in the dark
    crystals = [(x_, y_, 320, 0.32) for x_, y_ in ((300, 200), (700, -100), (1180, 330), (1500, 40),
                                                    (1900, 250), (2300, 0), (2450, 420))]
    if S["torch_lit"] <= 0 and not lights:
        lights.append((a["x"], a["y"] - 140, 320, 0.5))
        if S["far_glow"] > 0:
            lights.append((2460, 520, 260, 0.5 * S["far_glow"]))
    G.darkness(ctx, S["amb"], lights + crystals, tint=(0.0, 0.01, 0.03))
    for (x, y, r, k) in lights[:1]:
        if S["torch_lit"] > 0 or (tp and tp["t0"] <= t < tp["t1"]):
            G.warm_glow(ctx, x, y - 10, 300, 1.0)
    # eyes glow through the darkness
    if e:
        G.glowing_eyes(ctx, e["x"], e["y"], e["a"], t, 0.9, e["look"])
    if c:
        G.glowing_eyes(ctx, c["x"] + 92 * c["s"] * c["face"], c["y"] - 70 * c["s"], 0.8, t, 0.5)
    ctx.restore()


def draw_falltop(ctx, S, t):
    u = S["fall"]["u"] if S["fall"] else 0
    E.src(ctx, "#000000")
    ctx.paint()
    # rock rings rushing away (looking down the shaft)
    for i in range(10):
        k = (i / 10 + u * 3) % 1
        r = 900 * (1 - k) ** 2 + 30
        E.ellipse(ctx, 640, 380, r, r * 0.8)
        E.src(ctx, "#2C2622", 0.5 * (1 - k))
        ctx.set_line_width(40 * (1 - k) + 2)
        ctx.stroke()
    a = S["anger"]
    s = lerp(1.5, 0.05, ease_in(clamp(u * 1.05)) ** 0.7)
    c = dict(a)
    c.update(x=640, y=380 + 120 * s, s=s, tilt=math.sin(t * 0.7) * 0.25, yoff=0, itemL=None,
             itemR=None, hl=(-120, -230), hr=(120, -230), footL=(-20, -6), footR=(20, -6))
    E.draw_char(ctx, c, t)
    g = cairo.RadialGradient(640, 380, 40, 640, 380, 700)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(0.5, 0, 0, 0, 0.3)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.95)
    ctx.set_source(g)
    ctx.paint()


def draw(ctx, S, t):
    sc = S["scene"]
    if sc == "tunnel":
        draw_tunnel(ctx, S, t)
    elif sc == "cavern":
        draw_cavern(ctx, S, t)
    else:
        draw_falltop(ctx, S, t)
    if S["flash"] > 0:
        ctx.set_source_rgba(1, 0.95, 0.85, 0.8 * S["flash"])
        ctx.paint()
    G.vignette(ctx, 0.55)
    if S["card"] > 0:
        G.title_card(ctx, t, "ANGER", "Part One: Into the Dark", S["card"])
    if S["endcard"] > 0:
        G.end_card(ctx, t, "To Be Continued", "Part Two: The Fall", S["endcard"])
        S["subs"] = False
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
