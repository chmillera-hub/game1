"""Verse Stories: each quote acted out in its own everyday scene."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import sgfx as SG
import vgfx as V
import rgfx  # noqa: F401  (registers the book item)
from dcommon import sfx, music, hand, walk, cam_to, apply_cam
from show import Beat

TOTAL = 0.0
IDX = {}
SCREEN = (0, 0, 1280, 720)
pk = SG.person_kind

# ------------------------------------------------------------------ cast
CAST = {
    "jamie": (pk("v_jamie", "#E8883A", "#C68E5E", "#2A1E14", "messy"), 0.75),
    "tyler": (pk("v_tyler", "#C83A3A", "#F0C8A0", "#D9B05A", "short"), 0.8),
    "maya": (pk("v_maya", "#8A5AC8", "#8A5A3A", "#1A120C", "long"), 0.75),
    "dana": (pk("v_dana", "#2E8A8A", "#E0B28A", "#6A3A1E", "long"), 1.0),
    "greg": (pk("v_greg", "#6E7480", "#F0C8A0", "#5A3A22", "short"), 1.0),
    "otis": (pk("v_otis", "#3A4A6A", "#6A4428", "#C8C0B4", "bald", beard="#C8C0B4"), 1.0),
    "leo": (pk("v_leo", "#2E6AC8", "#A8714A", "#1A120C", "short"), 0.85),
    "opp": (pk("v_opp", "#C83A3A", "#F0C8A0", "#B9643A", "messy"), 0.85),
    "coach": (pk("v_coach", "#3E7A3E", "#E0B28A", "#5A3A22", "bald", beard="#5A3A22"), 1.0),
    "rosa": (pk("v_rosa", "#E8B64A", "#C68E5E", "#1A120C", "long"), 1.0),
    "lily": (pk("v_lily", "#E87AA4", "#C68E5E", "#1A120C", "long"), 0.7),
    "cashier": (pk("v_cashier", "#3E6AA0", "#F0C8A0", "#7A4A22", "short"), 1.0),
    "bea": (pk("v_bea", "#9A8AC8", "#F0D0B0", "#C8C8C8", "short"), 0.95),
    "frank": (pk("v_frank", "#B9643A", "#8A5A3A", "#1A120C", "bald", beard="#1A120C"), 1.0),
    "dad": (pk("v_dad", "#4A6E9E", "#E0B28A", "#3A2A1E", "short", beard=True), 1.0),
    "ava": (pk("v_ava", "#E85E8C", "#E0B28A", "#6A3A1E", "long"), 0.72),
    "sam": (pk("v_sam", "#5EC88A", "#E0B28A", "#6A3A1E", "messy"), 0.72),
    "marcus": (pk("v_marcus", "#5A5A6A", "#6A4428", "#1A120C", "short", beard="#1A120C"), 1.0),
    "ymarcus": (pk("v_ymarcus", "#2A2A30", "#6A4428", "#1A120C", "messy"), 1.0),
    "danny": (pk("v_danny", "#B9904A", "#F0C8A0", "#7A4A22", "short"), 1.0),
    "chaplain": (pk("v_chap", "#8A6A8A", "#F0D0B0", "#C8C8C8", "long"), 1.0),
    "pastor": (pk("v_pastor", "#F2EEE4", "#8A5A3A", "#1A120C", "bald", beard="#4A3A2A"), 1.0),
    "wmarcus": (pk("v_wmarcus", "#F2F2F2", "#6A4428", "#1A120C", "short", beard="#1A120C"), 1.0),
    "g1": (pk("v_g1", "#5E9AE8", "#A8714A", "#3A2A1E", "long"), 1.0),
    "g2": (pk("v_g2", "#E8A85E", "#F0D0B0", "#B9643A", "short"), 1.0),
    "grace": (pk("v_grace", "#C87A5A", "#A8714A", "#3A2A1E", "long"), 1.0),
    "joe": (pk("v_joe", "#A8C8E8", "#A8714A", "#1A120C", "short", beard="#1A120C"), 1.0),
    "leader": (pk("v_leader", "#6A5A4A", "#C68E5E", "#2A1E14", "short", beard=True), 1.0),
    "b1": (pk("v_b1", "#4A5A3A", "#A8714A", scarf="#8A6A4A"), 1.0),
    "b2": (pk("v_b2", "#5A3A4A", "#E0B28A", scarf="#3A4A6A"), 1.0),
    "b3": (pk("v_b3", "#3A3A4A", "#8A5A3A", "#1A120C", "short", beard=True), 1.0),
    "walter": (pk("v_walter", "#5A6A7A", "#F0D0B0", "#E8E8E8", "bald", beard="#E8E8E8"), 1.0),
}
GROUND = 612


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def T(b, off=0.0):
    return b.start + off


def init_state():
    S = dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0, fade=0.0,
             card=None, scene=None, show=[], fx={})
    for name, (kind, s) in CAST.items():
        S[name] = SG.new_person(kind, -300, s=s, y=GROUND, mouth="smile", mamt=0.3)
    return S


def scene(S, name, show, cam=(640, 360, 1.0)):
    S["scene"] = name
    S["show"] = show
    S["card"] = None
    S["cam"] = list(cam)
    S["fx"] = {}


def place(c, x, face=0.0, px=0.0, **kw):
    base = dict(tilt=0.0, yoff=0.0, y=GROUND, walking=0, wide=0.0, tears=0.0)
    base.update(kw)
    c.update(x=x, face=face, px=px, **base)


def card(S, lt, b, ref):
    S["card"] = (ref, clamp(lt / 0.6) * clamp((b.d - lt) / 0.6))
    S["fade"] = 0


# ------------------------------------------------------------------ Romans 12
def k1(S, lt, b):
    card(S, lt, b, "Romans 12:20")
    music(S, T(b), "hymn", 0.6)


def s1(S, lt, b):
    scene(S, "hallway", ["maya", "jamie", "tyler"], (640, 400, 1.15))
    j, ty, m = S["jamie"], S["tyler"], S["maya"]
    place(m, 380, 0.5, 1)
    place(j, 560, 0.4, 1, itemR=None)
    j["hr"] = (40, -90)
    ty["x"] = tw(lt, 0, 2.0, 1300, 700)
    ty["walking"] = 0.9 if lt < 2.0 else 0
    ty["face"], ty["px"] = -0.6, -1
    ty["mouth"], ty["mamt"] = "smirk", 0.7
    rip = 2.8
    S["fx"]["paper"] = (j["x"] + 50, GROUND - 120, clamp((lt - rip) / 0.3))
    if lt > rip:
        j["mouth"], j["mamt"] = "o", 0.8
        j["wide"] = 0.6
    if lt > rip + 0.6:
        ty["x"] = tw(lt, rip + 0.6, rip + 1.6, 700, 820)
        ty["face"], ty["px"] = 0.3, -1
    sfx(S, T(b, rip), "webtear", 0.9)


def s1b(S, lt, b):
    S["show"] = ["maya", "jamie", "tyler"]
    j, ty, m = S["jamie"], S["tyler"], S["maya"]
    S["fx"]["paper"] = (j["x"] + 50, GROUND - 40, 1.0)
    place(ty, 820, 0.3, -1)
    j["brow"] = -1.0 if lt < 2.5 else tw(lt, 2.5, 3.2, -1, 0.2)
    j["mouth"], j["mamt"] = ("frown", 0.8) if lt < 2.5 else ("smile", 0.4)
    j["wide"] = 0
    hand(j, 1, (60, -70), lt, 0, 0.3)
    hand(m, 1, (90, -110), lt, 0.2, 0.6)
    if lt > b.d - 2.0:
        # Jamie offers Tyler a fresh sheet of paper
        j["face"], j["px"] = 0.6, 1
        hand(j, 1, (110, -110), lt, b.d - 2.0, b.d - 1.4)
        S["fx"]["fresh"] = (j["x"] + j["s"] * 110 + 20, GROUND - 110 * j["s"] - 20)
        ty["wide"] = 0.6
        ty["mouth"], ty["mamt"] = "o", 0.5
        ty["brow"] = 0.6
    cam_to(S, lt, 0, b.d, 600, 400, 1.2)


def s2(S, lt, b):
    scene(S, "breakroom", ["dana", "greg"], (760, 380, 1.1))
    d, g = S["dana"], S["greg"]
    place(g, 980, -0.3, -1, mouth="frown", mamt=0.5, brow=0.5)
    place(d, 420, 0.4, 1, mouth="flat", mamt=0)
    hand(g, -1, (-10, -84), lt, 0, 0.01)
    hand(g, 1, (10, -80), lt, 0, 0.01)
    sfx(S, T(b, b.vs + b.vd * 0.6), "growl", 0.25)
    g["py"] = 0.8


def s2b(S, lt, b):
    d, g = S["dana"], S["greg"]
    d.update(itemL="bread", itemR="cup", mouth="smile", mamt=0.5)
    d["hl"], d["hr"] = (-50, -96), (56, -96)
    walk(d, 830, lt, 0.4, 2.6, 0.7)
    if lt > 2.8:
        hand(d, 1, (96, -110), lt, 2.8, 3.3)
        hand(d, -1, (90, -96), lt, 2.8, 3.3)
        g["py"] = 0
        g["px"] = -1
        g["wide"] = 0.5
        g["mouth"], g["mamt"] = "o", 0.6
    cam_to(S, lt, 0, b.d, 880, 400, 1.3)


def s3(S, lt, b):
    S["show"] = ["dana", "greg", "otis"]
    d, g, o = S["dana"], S["greg"], S["otis"]
    d.update(itemL=None, itemR=None)
    hand(d, -1, "rest", lt, 0, 0.4)
    hand(d, 1, "rest", lt, 0, 0.4)
    g.update(itemL="bread", itemR="cup", wide=0, mouth="wavy", mamt=1, brow=0.8)
    g["hl"], g["hr"] = (-40, -96), (40, -96)
    S["fx"]["blush"] = (g["x"], GROUND - 230, tw(lt, 0.2, 1.0, 0, 1))
    place(o, 300, 0.5, 1, itemR=None, mouth="smirk", mamt=0.7)
    o["hr"] = (40, -150)
    S["fx"]["mop"] = o["x"] + 40
    cam_to(S, lt, 0, 0.8, 640, 380, 1.0)


def s4(S, lt, b):
    scene(S, "soccer", ["coach", "leo", "opp"], (640, 380, 1.0))
    l, o, c = S["leo"], S["opp"], S["coach"]
    place(c, 160, 0.4, 1, mouth="flat", mamt=0)
    l["x"] = tw(lt, 0, 2.2, 300, 640)
    o["x"] = tw(lt, 0, 2.2, 1000, 700)
    l["walking"] = o["walking"] = 1.6 if lt < 2.2 else 0
    l["face"], l["px"] = 0.6, 1
    o["face"], o["px"] = -0.6, -1
    trip = 2.2
    S["fx"]["ball"] = (tw(lt, 0, trip, 420, 900), GROUND - 14)
    if lt > trip:
        o["footL"] = (-30, -10) if lt < trip + 0.4 else (0, 0)
        u = ease(clamp((lt - trip) / 0.3))
        l["tilt"] = lerp(0, 1.3, u)
        l["mouth"], l["mamt"] = "o", 0.9
        o["mouth"], o["mamt"] = "smirk", 0.7
    sfx(S, T(b, trip + 0.2), "thud", 0.8)


def s4b(S, lt, b):
    l, o, c = S["leo"], S["opp"], S["coach"]
    l["tilt"] = tw(lt, 0, 0.5, 1.3, 0)
    l["brow"] = -1.0
    l["mouth"], l["mamt"] = "frown", 0.8
    S["fx"]["ball"] = (900, GROUND - 14)
    c["x"] = tw(lt, 0.2, 1.2, 160, 520)
    c["walking"] = 0.8 if 0.2 < lt < 1.2 else 0
    hand(c, 1, (90, -150), lt, 1.0, 1.4)
    if lt > b.d - 2.0:
        l["brow"] = tw(lt, b.d - 2.0, b.d - 1.4, -1, 0.2)
        l["mouth"], l["mamt"] = "smile", 0.4
        hand(l, 1, (110, -110), lt, b.d - 1.6, b.d - 1.0)
        o["wide"] = 0.5
        o["mouth"], o["mamt"] = "o", 0.5
    cam_to(S, lt, 0, 1.0, 600, 400, 1.2)


def s5(S, lt, b):
    scene(S, "grocery", ["cashier", "rosa", "lily"], (640, 380, 1.1))
    ca, r, li = S["cashier"], S["rosa"], S["lily"]
    place(ca, 640, 0.5, 1, y=GROUND - 95)
    place(r, 950, -0.5, -1)
    place(li, 1080, -0.4, -1)
    hand(ca, 1, (110, -110), lt, 0, 0.6)
    tg = 0.8
    if lt > tg:
        hand(r, -1, (-90, -110), lt, tg, tg + 0.4)
    S["fx"]["money"] = (tw(lt, 0, tg, 760, 860), 492)
    li["wide"] = tw(lt, b.vs, b.vs + 0.3, 0, 0.7)
    li["mouth"], li["mamt"] = "o", 0.6
    hand(li, -1, (-60, -120), lt, b.vs, b.vs + 0.4)


def s5b(S, lt, b):
    ca, r, li = S["cashier"], S["rosa"], S["lily"]
    li["wide"] = 0
    hand(li, -1, "rest", lt, 0, 0.4)
    r["face"] = tw(lt, 0, 0.4, -0.5, 0.4)
    r["px"] = 1
    if lt > b.vs + b.vd * 0.6:
        r["face"], r["px"] = -0.5, -1
        hand(r, -1, (-110, -120), lt, b.vs + b.vd * 0.6, b.vs + b.vd * 0.6 + 0.5)
        S["fx"]["money"] = (tw(lt, b.vs + b.vd * 0.6, b.vs + b.vd * 0.6 + 0.6, 860, 760), 492)
        ca["mouth"], ca["mamt"] = "smile", 0.9
    else:
        S["fx"]["money"] = (860, 492)
    li["mouth"], li["mamt"] = "smile", 0.6
    cam_to(S, lt, 0, b.d, 900, 400, 1.3)


def s6(S, lt, b):
    scene(S, "neighbors", ["bea", "frank"], (640, 360, 1.0))
    be, fr = S["bea"], S["frank"]
    place(be, 380, 0.5, 1, mouth="frown", mamt=0.6, brow=-0.8)
    place(fr, 1000, 0.3, -1, mouth="smile", mamt=0.3)
    hand(be, -1, "hip", lt, 0, 0.01)
    hand(be, 1, "hip", lt, 0, 0.01)
    S["fx"]["music"] = 1.0
    music(S, T(b), None, 0)
    sfx(S, T(b, 0.2), "tink", 0.2)


def s6b(S, lt, b):
    be, fr = S["bea"], S["frank"]
    S["fx"]["music"] = 1.0 if lt < 3.6 else tw(lt, 3.6, 4.0, 1, 0)
    be["brow"] = tw(lt, 0, 1.2, -0.8, 0.2)
    be["mouth"], be["mamt"] = "smile", 0.5
    hand(be, -1, "rest", lt, 0, 0.5)
    hand(be, 1, (70, -96), lt, 0.4, 0.8)
    S["fx"]["cookies"] = 1
    walk(be, 800, lt, 0.8, 3.0, 0.6)
    fr["face"], fr["px"] = -0.5, -1
    if lt > 3.2:
        hand(fr, -1, (-90, -110), lt, 3.2, 3.7)
        fr["mouth"], fr["mamt"] = "smile", 0.9
    music(S, T(b, 3.6), "hymn", 0.6)
    cam_to(S, lt, 0, b.d, 860, 380, 1.15)
    S["fade"] = tw(lt, b.d - 0.6, b.d, 0, 1)


# ------------------------------------------------------------------ John 15
def k2(S, lt, b):
    card(S, lt, b, "John 15:12")


def s7(S, lt, b):
    scene(S, "kitchen", ["dad", "ava", "sam"], (640, 380, 1.1))
    d, a, s = S["dad"], S["ava"], S["sam"]
    place(d, 640, 0, 0, itemR=None, y=GROUND - 60)
    place(a, 470, 0.6, 1, mouth="frown", mamt=0.6, brow=-0.6, y=GROUND - 70)
    place(s, 810, -0.6, -1, mouth="frown", mamt=0.6, brow=-0.6, y=GROUND - 70)
    tug = math.sin(lt * 9) * 8
    a["hr"] = (90 + tug, -120)
    s["hl"] = (-90 + tug, -120)
    S["fx"]["roll"] = (640 + tug * 0.7, 520)
    d["py"] = 0.4
    d["brow"] = 0.4


def s7b(S, lt, b):
    d = S["dad"]
    d["itemR"] = "book"
    d["wandR"] = -10
    hand(d, 1, (40, -96), lt, 0, 0.5)
    d["py"] = 0.8
    a, s = S["ava"], S["sam"]
    a["px"], s["px"] = 1, -1
    a["face"], s["face"] = 0.3, -0.3
    S["fx"]["roll"] = (640, 520)
    a["hr"] = (90, -120)
    s["hl"] = (-90, -120)
    hand(a, 1, "rest", lt, 0.5, 1.0)
    hand(s, -1, "rest", lt, 0.5, 1.0)
    cam_to(S, lt, 0, b.d, 640, 360, 1.3)


def s7c(S, lt, b):
    d, a, s = S["dad"], S["ava"], S["sam"]
    d["py"] = 0
    d["px"] = 0
    tl = b.vs + b.vd + 0.2
    if lt > tl:
        S["fx"]["split"] = clamp((lt - tl) / 0.6)
        a["mouth"], a["mamt"] = "smile", 0.9
        s["mouth"], s["mamt"] = "smile", 0.9
        a["brow"] = s["brow"] = 0.3
        a["x"] = tw(lt, tl + 0.6, tl + 1.4, 470, 560)
        s["x"] = tw(lt, tl + 0.6, tl + 1.4, 810, 720)
        hand(a, 1, (110, -150), lt, tl + 0.8, tl + 1.4)
        hand(s, -1, (-110, -150), lt, tl + 0.8, tl + 1.4)
    else:
        S["fx"]["roll"] = (640, 520)
    d["mouth"], d["mamt"] = "smile", 0.6
    cam_to(S, lt, 0, b.d, 640, 380, 1.1)
    S["fade"] = tw(lt, b.d - 0.6, b.d, 0, 1)


# ------------------------------------------------------------------ 1 Timothy 1
def k3(S, lt, b):
    card(S, lt, b, "1 Timothy 1:12-16")


GROUP = ["g1", "danny", "g2", "dana"]


def basement_cast(S):
    xs = [180, 330, 950, 1100]
    for n, x in zip(GROUP, xs):
        c = S[n]
        place(c, x, 0.5 if x < 640 else -0.5, 1 if x < 640 else -1, yoff=0, itemL=None, itemR=None,
              mouth="smile", mamt=0.3)
    m = S["marcus"]
    place(m, 640, 0, 0, itemR="book", wandR=-10)
    m["hr"] = (40, -96)


def s9(S, lt, b):
    scene(S, "basement", GROUP + ["marcus"], (640, 380, 1.0))
    basement_cast(S)
    music(S, T(b), "hymn", 0.5)


def s9b(S, lt, b):
    basement_cast(S)
    m = S["marcus"]
    m["py"] = -0.4 if lt > b.vs + 1.0 else 0.6
    cam_to(S, lt, 0, b.d, 640, 380, 1.4)


def s10(S, lt, b):
    scene(S, "street", ["ymarcus", "danny"], (640, 380, 1.1))
    y, dn = S["ymarcus"], S["danny"]
    place(y, 520, 0.5, 1, mouth="frown", mamt=0.9, brow=-1.0)
    dn.update(x=760, face=-0.5, px=-1, mouth="o", mamt=0.8, brow=0.8, yoff=0, tilt=0)
    shove = 1.4
    hand(y, -1, (80, -130), lt, shove - 0.3, shove)
    hand(y, 1, (90, -110), lt, shove - 0.3, shove)
    if lt > shove:
        u = ease(clamp((lt - shove) / 0.4))
        dn["x"] = lerp(760, 860, u)
        dn["tilt"] = lerp(0, 1.2, u)
    sfx(S, T(b, shove), "thud", 0.7)
    sfx(S, T(b, 0.1), "rumble", 0.3)
    S["fx"]["gray"] = 0.75


def s11(S, lt, b):
    scene(S, "visiting", ["ymarcus", "chaplain"], (640, 380, 1.15))
    y, ch = S["ymarcus"], S["chaplain"]
    place(y, 520, 0.6, 1, mouth="frown", mamt=0.3, brow=0.5, tilt=0)
    y["py"] = 0.8
    place(ch, 780, -0.5, -1, mouth="smile", mamt=0.6, itemL="book", wandL=200)
    ch["hl"] = (-60, -110)
    hand(ch, -1, (-120, -116), lt, 0.6, 1.4)
    if lt > 2.0:
        ch["itemL"] = None
        S["fx"]["bible"] = (tw(lt, 2.0, 2.6, 660, 610), 470)
        y["py"] = 0
        y["px"] = 1
        y["brow"] = 0.7
        y["tears"] = tw(lt, 3.0, 4.0, 0, 1)
    cam_to(S, lt, 0, b.d, 640, 400, 1.3)


def s12(S, lt, b):
    scene(S, "river", ["pastor", "wmarcus", "g1", "g2"], (640, 380, 1.0))
    p, w = S["pastor"], S["wmarcus"]
    place(S["g1"], 160, 0.4, 1, y=GROUND - 120, mouth="smile", mamt=0.7)
    place(S["g2"], 1120, -0.4, -1, y=GROUND - 120, mouth="smile", mamt=0.7)
    place(p, 720, -0.4, -1, y=GROUND + 40)
    place(w, 560, 0.4, 1, y=GROUND + 40, eyes="open")
    hand(p, -1, (-140, -150), lt, 0.3, 0.8)
    dip0, dip1 = 1.8, 3.4
    if dip0 < lt < dip1:
        u = math.sin((lt - dip0) / (dip1 - dip0) * math.pi)
        w["tilt"] = -1.1 * u
        w["yoff"] = 60 * u
        w["eyes"] = "shut"
    else:
        w["tilt"] = 0
        w["yoff"] = 0
    if lt > dip1:
        w["mouth"], w["mamt"] = "smile", 0.9
        hand(w, -1, (-60, -220), lt, dip1, dip1 + 0.5)
        hand(w, 1, (60, -220), lt, dip1, dip1 + 0.5)
        S["fx"]["grace"] = clamp((lt - dip1) / 0.6)
    sfx(S, T(b, dip1), "splash", 0.8)
    sfx(S, T(b, dip1 + 0.2), "sparkle", 0.6)


def s13(S, lt, b):
    scene(S, "basement", GROUP + ["marcus"], (640, 380, 1.3))
    basement_cast(S)
    m = S["marcus"]
    tl = b.vs + b.vd * 0.75
    if lt > tl:
        hand(m, -1, (6, -110), lt, tl, tl + 0.5)
        m["brow"] = 0.7
        m["py"] = 0.6


def s14(S, lt, b):
    S["show"] = GROUP + ["marcus"]
    basement_cast(S)
    m, dn = S["marcus"], S["danny"]
    m["py"] = 0
    tl = b.vs + b.vd * 0.5
    if lt > tl:
        dn["face"], dn["px"] = 0.6, 1
        walk(dn, 520, lt, tl, tl + 2.4, 0.6)
        m["face"], m["px"] = -0.5, -1
        m["wide"] = 0.5
    if lt > tl + 2.6:
        hand(dn, 1, (110, -150), lt, tl + 2.6, tl + 3.1)
        hand(m, -1, (-110, -150), lt, tl + 2.6, tl + 3.1)
        m["itemR"] = None
        m["tears"] = 0.8
        m["mouth"], m["mamt"] = "smile", 0.8
        dn["mouth"], dn["mamt"] = "smile", 0.8
    cam_to(S, lt, 0, b.d, 560, 380, 1.1)
    S["fade"] = tw(lt, b.d - 0.6, b.d, 0, 1)


# ------------------------------------------------------------------ Romans 8
def k4(S, lt, b):
    card(S, lt, b, "Romans 8:35-39")


def s15(S, lt, b):
    scene(S, "hospital", ["grace"], (600, 380, 1.1))
    gr, jo = S["grace"], S["joe"]
    place(gr, 940, -0.5, -1, itemR="book", wandR=-10)
    gr["hr"] = (40, -96)
    gr["py"] = 0.6
    jo.update(x=500, y=GROUND - 120, tilt=-math.pi / 2, face=0, px=0.6, py=0, lid=0.4, mouth="flat",
              mamt=0)
    S["fx"]["patient"] = True
    music(S, T(b), "hymn", 0.5)
    sfx(S, T(b, 0.5), "water", 0.3)


def s15b(S, lt, b):
    gr, jo = S["grace"], S["joe"]
    S["fx"]["patient"] = True
    gr["py"] = 0.6 if lt < b.vs + b.vd * 0.6 else -0.2
    if lt > b.vs + b.vd * 0.6:
        gr["face"], gr["px"] = -0.5, -1
        jo["mouth"], jo["mamt"] = "smile", 0.5
    cam_to(S, lt, 0, b.d, 760, 400, 1.3)


def s16(S, lt, b):
    u = clamp((lt - b.vs) / max(0.1, b.vd))
    kind = "storm" if u < 0.34 else ("foodbank" if u < 0.67 else "schoolyard")
    S["fx"]["panel"] = kind
    if kind == "storm":
        scene(S, "montage", ["dad", "ava", "sam"], (640, 380, 1.0))
        S["fx"]["panel"] = kind
        place(S["dad"], 300, 0.4, 1, itemR=None, mouth="frown", mamt=0.6, brow=0.7, py=-0.6)
        place(S["ava"], 200, 0.4, 1, mouth="frown", mamt=0.5, brow=0.7)
        place(S["sam"], 420, 0.4, 1, mouth="frown", mamt=0.5, brow=0.7)
    elif kind == "foodbank":
        scene(S, "montage", ["otis", "rosa", "lily"], (640, 380, 1.0))
        S["fx"]["panel"] = kind
        place(S["otis"], 680, 0.5, 1, itemR=None, mouth="flat", mamt=0)
        place(S["rosa"], 520, 0.5, 1, mouth="flat", mamt=0)
        place(S["lily"], 400, 0.5, 1, mouth="flat", mamt=0)
    else:
        scene(S, "montage", ["jamie", "tyler", "opp"], (640, 380, 1.0))
        S["fx"]["panel"] = kind
        place(S["jamie"], 640, 0, 0, mouth="frown", mamt=0.7, brow=0.8, tears=1.0, py=0.8)
        place(S["tyler"], 450, 0.6, 1, mouth="laugh", mamt=0.8)
        place(S["opp"], 830, -0.6, -1, mouth="laugh", mamt=0.8)


def s17(S, lt, b):
    scene(S, "hidden", ["b1", "b2", "leader", "b3"], (640, 380, 1.1))
    place(S["b1"], 380, 0.5, 1, mouth="flat", mamt=0, py=0.4)
    place(S["b2"], 520, 0.4, 1, mouth="flat", mamt=0, py=0.4)
    place(S["leader"], 700, -0.2, -1, itemR="book", wandR=-10, py=0.6)
    S["leader"]["hr"] = (40, -96)
    place(S["b3"], 880, -0.5, -1, mouth="flat", mamt=0, py=0.4)
    kn = 0.6
    if kn < lt < kn + 1.4:
        for n in ("b1", "b2", "b3", "leader"):
            S[n]["px"] = 1
            S[n]["wide"] = 0.5
            S[n]["py"] = 0
    sfx(S, T(b, kn), "door", 0.5)
    sfx(S, T(b, kn + 0.25), "door", 0.4)
    music(S, T(b), "tense", 0.3)


def s18(S, lt, b):
    scene(S, "exit", ["grace", "joe"], (640, 380, 1.0))
    gr, jo = S["grace"], S["joe"]
    jo.update(y=GROUND, tilt=0, lid=0.08, mouth="smile", mamt=0.9, py=0, px=1, face=0.4, eyes="open")
    gr.update(itemR=None, mouth="smile", mamt=0.9, py=0, face=0.4, px=1)
    gr["x"] = tw(lt, 0, b.d, 560, 860)
    jo["x"] = tw(lt, 0, b.d, 440, 740)
    gr["walking"] = jo["walking"] = 0.6
    hand(gr, -1, (-70, -100), lt, 0, 0.01)
    hand(jo, 1, (70, -100), lt, 0, 0.01)
    music(S, T(b), "hymn", 0.9)
    sfx(S, T(b, 0.4), "sparkle", 0.4)


def s19(S, lt, b):
    scene(S, "cemetery", ["walter"], (660, 400, 1.15))
    w = S["walter"]
    place(w, 470, 0.5, 1, mouth="flat", mamt=0, py=0.5)
    S["fx"]["dawn"] = tw(lt, 0, b.d, 0.2, 1.0)
    if lt > b.vs + b.vd * 0.5:
        w["py"] = -0.6
        w["mouth"], w["mamt"] = "smile", tw(lt, b.vs + b.vd * 0.5, b.vs + b.vd * 0.5 + 1, 0, 0.6)


def s20(S, lt, b):
    everyone = ["otis", "greg", "dana", "coach", "leo", "opp", "bea", "frank", "rosa", "lily", "dad", "ava",
                "sam", "marcus", "danny", "chaplain", "grace", "joe", "walter", "jamie", "tyler", "maya"]
    scene(S, "park", everyone, (640, 380, 1.0))
    xs = [60 + i * 55 for i in range(len(everyone))]
    for i, (n, x) in enumerate(zip(everyone, xs)):
        c = S[n]
        back = i % 2 == 0
        c.update(x=x, y=GROUND - (40 if back else 0) + (10 if c["s"] < 0.9 else 0), face=0, px=0, py=-0.3,
                 itemL=None, itemR=None, tilt=0, yoff=0, mouth="smile", mamt=0.8, wide=0, tears=0, brow=0.2,
                 walking=0, alpha=clamp(lt / 1.5), eyes="open", lid=0.08)
        c["hl"] = E.pose(c["kind"], -1, "rest")
        c["hr"] = E.pose(c["kind"], 1, "rest")
    S["cam"] = [640, 380, tw(lt, 0, b.d, 1.1, 1.0)]
    music(S, T(b), "hope", 0.9)
    S["fade"] = 0


def kend(S, lt, b):
    S["endfade"] = tw(lt, 0, 1.2, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(k1, min=3.6),
    Beat(s1, "narr", "In a school hallway, Tyler snatches Jamie's drawing and rips it in half.", pre=0.4,
         post=1.4, min=5.0),
    Beat(s1b, "maya", "Do not be overcome by evil, but overcome evil with good.", pre=0.4, post=2.6),
    Beat(s2, "narr", "At work, Greg took credit for Dana's project. Today, he forgot his lunch.", pre=0.6,
         post=0.8),
    Beat(s2b, "narr", "If your enemy is hungry, feed him; if he is thirsty, give him something to drink.",
         pre=0.4, post=1.4, min=5.0),
    Beat(s3, "otis", "In doing this, you will heap burning coals on his head.", pre=0.8, post=1.6),
    Beat(s4, "narr", "Leo gets tripped on purpose. The ref doesn't see it.", pre=0.4, post=1.0, min=4.0),
    Beat(s4b, "coach", "Do not repay anyone evil for evil.", pre=1.2, post=2.4),
    Beat(s5, "lily", "Mom! She gave us an extra twenty!", pre=1.2, post=0.6),
    Beat(s5b, "rosa", "Be careful to do what is right in the eyes of everyone.", pre=0.4, post=2.0),
    Beat(s6, "narr", "Bea and Frank have argued over the fence for eleven years.", pre=0.8, post=0.8),
    Beat(s6b, "narr", "If it is possible, as far as it depends on you, live at peace with everyone.",
         pre=0.6, post=3.0, min=6.0),
    Beat(k2, min=3.6),
    Beat(s7, "narr", "Sam and Ava both want the last dinner roll.", pre=0.4, post=0.8),
    Beat(s7b, "dad", "A new commandment I give you.", pre=0.6, post=0.6),
    Beat(s7c, "dad", "My command is this: Love each other as I have loved you.", pre=0.3, post=3.0),
    Beat(k3, min=3.6),
    Beat(s9, "narr", "Marcus has been asked to share his story with the group.", pre=0.6, post=0.6),
    Beat(s9b, "marcus", "I thank Christ Jesus our Lord, who has given me strength, that he considered me "
                        "trustworthy, appointing me to his service.", pre=0.4, post=0.8),
    Beat(s10, "marcus", "Even though I was once a blasphemer and a persecutor and a violent man,", pre=0.6,
         post=1.0, min=4.0),
    Beat(s11, "marcus", "I was shown mercy because I acted in ignorance and unbelief.", pre=0.8, post=1.4),
    Beat(s12, "marcus", "The grace of our Lord was poured out on me abundantly, along with the faith and love "
                        "that are in Christ Jesus.", pre=0.6, post=1.4),
    Beat(s13, "marcus", "Here is a trustworthy saying that deserves full acceptance: Christ Jesus came into "
                        "the world to save sinners—of whom I am the worst.", pre=0.6, post=0.8),
    Beat(s14, "marcus", "But for that very reason I was shown mercy so that in me, the worst of sinners, "
                        "Christ Jesus might display his immense patience as an example for those who would "
                        "believe in him and receive eternal life.", pre=0.4, post=3.2),
    Beat(k4, min=3.6),
    Beat(s15, "narr", "The night before Joe's surgery, Grace reads to him from her Bible.", pre=0.6,
         post=0.6),
    Beat(s15b, "grace", "Who shall separate us from the love of Christ?", pre=0.4, post=1.2),
    Beat(s16, "narr", "Shall trouble or hardship or persecution or famine or nakedness or danger or sword?",
         pre=0.4, post=0.8),
    Beat(s17, "leader", "As it is written: “For your sake we face death all day long; we are considered "
                        "as sheep to be slaughtered.”", pre=2.0, post=1.0),
    Beat(s18, "narr", "No, in all these things we are more than conquerors through him who loved us.", pre=0.6,
         post=1.4),
    Beat(s19, "narr", "For I am convinced that neither death nor life, neither angels nor demons, neither the "
                      "present nor the future, nor any powers,", pre=0.8, post=0.4),
    Beat(s20, "narr", "neither height nor depth, nor anything else in all creation, will be able to separate "
                      "us from the love of the Lord our God.", pre=0.4, post=3.4),
    Beat(kend, min=6.0),
]


# ------------------------------------------------------------------ drawing
BG = {
    "hallway": V.hallway, "breakroom": V.breakroom, "soccer": V.soccer, "grocery": V.grocery,
    "kitchen": V.kitchen, "basement": V.basement, "street": V.night_street, "visiting": V.visiting_room,
    "river": V.river, "hospital": V.hospital, "exit": V.hospital_exit, "hidden": V.hidden_room,
    "park": V.park,
}


def draw_scene(ctx, S, t):
    sc = S["scene"]
    fx = S["fx"]
    if sc == "neighbors":
        V.neighbors(ctx, t, fx.get("music", 0))
    elif sc == "cemetery":
        V.cemetery(ctx, t, fx.get("dawn", 1))
    elif sc == "montage":
        V.montage_panel(ctx, fx.get("panel", "storm"), t)
    elif sc in BG:
        BG[sc](ctx, t)
    if sc == "basement":
        for x in (180, 330, 950, 1100):
            V.folding_chair(ctx, x)
    if fx.get("patient"):
        V.patient_in_bed(ctx, 500, t, S["joe"])
    order = list(S["show"])
    if sc == "basement" and "marcus" in order:
        order.remove("marcus")
        order.append("marcus")
    for n in order:
        E.draw_char(ctx, S[n], t)
    if sc == "basement" and "marcus" in S["show"] and S["marcus"]["x"] == 640:
        V.podium(ctx, 640)
    if sc == "kitchen":
        # table front edge hides legs
        E.rrect(ctx, 260, 500, 760, 26, 6)
        E.fill_stroke(ctx, "#8A5A3A", "#4A2E1A", 3)
        ctx.rectangle(270, 526, 740, 90)
        E.src(ctx, "#6A4428")
        ctx.fill()
    if sc == "grocery":
        E.rrect(ctx, 430, 440, 420, 160, 8)
        E.fill_stroke(ctx, "#3A4A5A", "#1A2430", 3)
    if sc == "river":
        V.water_front(ctx, t, 600)
    if "paper" in fx:
        x, y, torn = fx["paper"]
        V.paper(ctx, x, y, torn)
    if "fresh" in fx:
        x, y = fx["fresh"]
        E.rrect(ctx, x - 20, y - 28, 40, 56, 2)
        E.src(ctx, "#FFFFFF")
        ctx.fill()
    if "blush" in fx:
        x, y, a = fx["blush"]
        V.blush_glow(ctx, x, y, a, t)
    if "mop" in fx:
        mx = fx["mop"]
        ctx.move_to(mx, GROUND - 160)
        ctx.line_to(mx + 20, GROUND)
        E.src(ctx, "#8A6A4A")
        ctx.set_line_width(6)
        ctx.stroke()
        E.ellipse(ctx, mx + 22, GROUND - 4, 26, 8)
        E.src(ctx, "#C9C2B4")
        ctx.fill()
    if "ball" in fx:
        V.ball(ctx, fx["ball"][0], fx["ball"][1], t)
    if "money" in fx:
        V.money(ctx, *fx["money"])
    if fx.get("cookies"):
        be = S["bea"]
        V.plate_of_cookies(ctx, be["x"] + 70 * be["s"], GROUND - 96 * be["s"] - 8)
    if "roll" in fx and "split" not in fx:
        x, y = fx["roll"]
        E.ellipse(ctx, x, y - 14, 22, 14)
        E.fill_stroke(ctx, "#D9A35A", "#8A5A24", 2)
    if "split" in fx:
        u = fx["split"]
        for side in (-1, 1):
            E.ellipse(ctx, 640 + side * 80 * u, 506, 12, 12)
            E.fill_stroke(ctx, "#D9A35A", "#8A5A24", 2)
    if "bible" in fx:
        x, y = fx["bible"]
        E.rrect(ctx, x - 24, y - 6, 48, 16, 3)
        E.fill_stroke(ctx, "#8E1F2F", "#3E0A14", 2)
    if fx.get("grace", 0) > 0:
        import random as _r
        rnd = _r.Random(2)
        for i in range(50):
            x = rnd.uniform(440, 680)
            y = (rnd.uniform(0, 600) + t * rnd.uniform(60, 140)) % 600
            E.sparkle(ctx, x, y, rnd.uniform(3, 7), "#FFE7A8", fx["grace"])


def draw(ctx, S, t):
    ctx.save()
    if S["scene"]:
        apply_cam(ctx, S, t, SCREEN)
        draw_scene(ctx, S, t)
    ctx.restore()
    if S["fx"].get("gray"):
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_HSL_SATURATION)
        ctx.set_source_rgba(0.5, 0.5, 0.5, S["fx"]["gray"])
        ctx.paint()
        ctx.restore()
        ctx.set_source_rgba(0.2, 0.25, 0.4, 0.2)
        ctx.paint()
    g = cairo.RadialGradient(640, 360, 320, 640, 360, 820)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.35)
    ctx.set_source(g)
    ctx.paint()
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
    cd = S["card"]
    if cd:
        V.chapter_card(ctx, t, cd[0], cd[1])
    ef = S.get("endfade", 0)
    if ef > 0:
        ctx.push_group()
        E.src(ctx, "#0E0A06")
        ctx.paint()
        for i, r in enumerate(["Romans 12:20", "John 15:12", "1 Timothy 1:12-16", "Romans 8:35-39"]):
            E.text(ctx, r, 640, 270 + i * 54, 34, "#F2DCA8")
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ef)
