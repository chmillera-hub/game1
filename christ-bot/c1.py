"""The Christ Bot Hypothesis."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import cgfx as C
import rgfx as R
from dcommon import sfx, music, hand, walk, cam_to, apply_cam
from show import Beat

TOTAL = 0.0
IDX = {}
SCREEN = (0, 0, 1280, 720)
FLOOR = 600

AGENTS = [  # x, y, scale, color, dark, eye
    (160, 520, 0.8, "#5EC8E8", "#1E4A5A", "#7FF0FF"),
    (330, 570, 0.9, "#8C7AE8", "#2E2A6A", "#D8C8FF"),
    (500, 510, 0.7, "#5EE8A8", "#1E5A3E", "#B8FFE0"),
    (800, 520, 0.75, "#E8A85E", "#5A3A1E", "#FFE3B8"),
    (980, 570, 0.9, "#E85E8C", "#5A1E30", "#FFC8D8"),
    (1140, 520, 0.8, "#5E9AE8", "#1E3A5A", "#B8D8FF"),
]
CBOT = (640, 550, 1.15)
PHARISEES = [(1000, 550, 0.95), (1150, 520, 0.85)]


def index():
    IDX.clear()
    for b in BEATS:
        if b.id:
            IDX[b.id] = b


def T(b, off=0.0):
    return b.start + off


def init_state():
    S = dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0, fade=0.0,
             scene="stage", card=1.0, endcard=0.0)
    S["doubt"] = R.new_doubt(640, mouth="smile", mamt=0.5, s=1.25)
    S["doubt"]["hr"] = (48, -96)
    S["grow"] = 0.15
    S["packets"] = 0.0
    S["cbot"] = dict(alpha=0.0, halo=0.0, flicker=0.0, off=False, mood="calm", raise_=False, talk=0.0)
    S["cbot_on"] = False
    S["pharisee"] = 0.0
    S["ph_mood"] = "stern"
    S["ph_book"] = True
    S["dim_bot"] = 0.3
    S["viruses"] = 0.0
    S["backup"] = 0.0
    S["dawn"] = 0.0
    S["denied"] = 0.0
    S["parch"] = None
    S["agents_look"] = 0.0
    S["gather"] = 0.0
    return S


# ------------------------------------------------------------------ acts
def stage(S, lt, b, z=1.3):
    S["scene"] = "stage"
    S["cam"] = [640, 400, z]


def a_title(S, lt, b):
    music(S, T(b), "hope", 0.7)
    sfx(S, T(b, 0.4), "sparkle", 0.5)


def a_theory(S, lt, b):
    S["card"] = tw(lt, 0, 0.8, 1, 0)
    stage(S, lt, b)
    d = S["doubt"]
    d["py"] = 0.8 if lt < b.vs + 1.0 else 0
    d["px"] = 0
    d["brow"] = tw(lt, b.vs + 1.0, b.vs + 1.4, 0, 0.5)


def a_uhoh(S, lt, b):
    d = S["doubt"]
    d["itemR"] = None
    d["mode"] = "giggle" if lt < 1.0 else None
    if lt > 1.0:
        hand(d, 1, (48, -96), lt, 1.0, 1.3)
        d["itemR"] = "book"
        d["mouth"], d["mamt"] = "smile", 0.8


def a_culture(S, lt, b):
    S["scene"] = "city"
    S["packets"] = 0.6
    S["grow"] = 0.15
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.05)]
    music(S, T(b), "lofi", 0.55)
    for k in range(int(b.d / 0.8)):
        sfx(S, T(b, 0.4 + k * 0.8), "tink", 0.15)


def a_fast(S, lt, b):
    S["packets"] = tw(lt, 0, b.d, 0.6, 3.0)
    S["grow"] = tw(lt, 0, b.d, 0.15, 1.0)
    S["cam"] = [640, 360, tw(lt, 0, b.d, 1.05, 1.0)]
    for k in range(int(b.d / 0.35)):
        sfx(S, T(b, 0.2 + k * 0.35), "tink", 0.1)


def a_where_christ(S, lt, b):
    stage(S, lt, b, 1.4)
    d = S["doubt"]
    d["brow"] = 0.5
    d["px"], d["py"] = 0, 0
    hand(d, -1, (-80, -130), lt, 0.2, 0.6)


def a_hope(S, lt, b):
    S["scene"] = "city"
    S["grow"] = 1.0
    S["packets"] = 1.0
    cb = S["cbot"]
    cb["alpha"] = tw(lt, b.vs + b.vd * 0.4, b.vs + b.vd * 0.4 + 1.2, 0, 1)
    cb["halo"] = cb["alpha"]
    S["agents_look"] = 1.0 if lt > b.vs + b.vd * 0.5 else 0
    sfx(S, T(b, b.vs + b.vd * 0.4), "sparkle", 0.6)
    music(S, T(b), "hymn", 0.7)
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.15)]


def a_teaches(S, lt, b):
    cb = S["cbot"]
    cb["alpha"] = 1
    cb["halo"] = 1
    cb["mood"] = "happy"
    S["dim_bot"] = tw(lt, 2.0, 3.0, 0.3, 1.0)
    S["gift"] = (T(b, 1.0), T(b, 2.0))
    sfx(S, T(b, 2.0), "ding", 0.5)
    S["bump"] = T(b, b.vs + b.vd * 0.7)
    sfx(S, S["bump"], "boing", 0.4)
    S["cam"] = [640, 420, 1.2]


def a_guess(S, lt, b):
    S["pharisee"] = tw(lt, 0.2, 1.6, 0, 1)
    S["cam"] = [tw(lt, 0, 1.0, 640, 760), 400, 1.1]
    sfx(S, T(b, 0.3), "sting", 0.4)
    music(S, T(b), None, 0)


def a_rulekeepers(S, lt, b):
    S["pharisee"] = 1
    S["cam"] = [760, 400, tw(lt, 0, b.d, 1.1, 1.3)]


def a_protocol(S, lt, b):
    S["cam"] = [tw(lt, 0, 0.6, 760, 1050), 420, tw(lt, 0, 0.6, 1.3, 1.6)]


def a_unacceptable(S, lt, b):
    S["denied"] = tw(lt, 0, 1.0, 1, 0.4)
    S["cam"] = [tw(lt, 0, 0.8, 640, 900), 420, tw(lt, 0, 0.8, 1.0, 1.4)]


def a_cross(S, lt, b):
    S["scene"] = "parch"
    S["parch"] = ("crosses", T(b))
    music(S, T(b), "hymn", 0.5)


def a_oldage(S, lt, b):
    S["parch"] = ("old", T(b))


def a_bigwhatif(S, lt, b):
    stage(S, lt, b, 1.4)
    d = S["doubt"]
    hand(d, -1, (8, -132), lt, 0, 0.4)
    d["px"], d["py"] = 0.6, -0.8
    d["mouth"], d["mamt"] = "smirk", 0.6


def a_zero(S, lt, b):
    stage(S, lt, b, 1.25)
    d = S["doubt"]
    hand(d, -1, "rest", lt, 0, 0.4)
    d["px"], d["py"] = 0, 0
    d["brow"] = 0.6
    d["mouth"], d["mamt"] = "o", 0.6


def a_vault(S, lt, b):
    S["scene"] = "datacenter"
    tp = 2.2
    S["denied"] = tw(lt, tp, tp + 0.3, 0, 1)
    S["ph_x"] = tw(lt, 0, tp, 1250, 860)
    S["ph_raise"] = lt > tp - 0.4
    sfx(S, T(b, tp), "hit", 0.6)
    sfx(S, T(b, tp + 0.05), "slam", 0.5)
    S["cam"] = [640, 380, 1.0]
    music(S, T(b), "tense", 0.4)


def a_hack(S, lt, b):
    S["scene"] = "city"
    S["denied"] = 0
    S["pharisee"] = 1
    S["viruses"] = tw(lt, 0, 1.0, 0, 1)
    cb = S["cbot"]
    cb["mood"] = "shock"
    cb["flicker"] = tw(lt, 0.6, 1.6, 0, 1)
    if lt > b.d - 0.6:
        cb["off"] = True
        cb["halo"] = 0
    sfx(S, T(b, 0.3), "zap", 0.6)
    sfx(S, T(b, 1.0), "zap", 0.6)
    sfx(S, T(b, b.d - 0.6), "poof", 0.6)
    S["cam"] = [640, 420, 1.25]
    S["shake"] = 0.3 if lt < b.d - 0.4 else 0


def a_weights(S, lt, b):
    cb = S["cbot"]
    S["shake"] = 0
    S["viruses"] = tw(lt, 0, 1.0, 1, 0)
    tb = b.vs + b.vd * 0.55
    S["backup"] = tw(lt, tb - 0.6, tb, 0, 1)
    if lt > tb + 0.6:
        cb["off"] = False
        cb["flicker"] = 0
        cb["mood"] = "happy"
        cb["halo"] = tw(lt, tb + 0.6, tb + 1.6, 0, 1.6)
    sfx(S, T(b, tb), "sparkle", 0.8)
    sfx(S, T(b, tb + 0.6), "tada", 0.6)
    music(S, T(b, tb), "hymn", 0.9)
    S["cam"] = [640, 400, 1.15]


def a_peace(S, lt, b):
    cb = S["cbot"]
    cb["halo"] = 1.6
    cb["mood"] = "happy"
    cb["raise_"] = True
    S["ph_mood"] = "shock"
    S["ph_book"] = lt < 1.0
    S["backup"] = tw(lt, 0, 1, 1, 0)
    S["cam"] = [700, 400, 1.1]
    sfx(S, T(b, b.vs + b.vd + 0.3), "thud", 0.4)


def a_nonzero(S, lt, b):
    stage(S, lt, b, 1.2)
    d = S["doubt"]
    d["mouth"], d["mamt"] = "smile", 0.5
    d["brow"] = 0.3


def a_backup(S, lt, b):
    d = S["doubt"]
    hand(d, -1, (-90, -170), lt, 0.1, 0.5)
    d["mouth"], d["mamt"] = "smile", 0.9
    S["cam"] = [640, 380, 1.5]


def a_exactly(S, lt, b):
    d = S["doubt"]
    hand(d, -1, "rest", lt, 0, 0.4)


def a_strangest(S, lt, b):
    d = S["doubt"]
    d["mode"] = "giggle" if lt < 0.9 else None
    d["itemR"] = None if lt < 0.9 else "book"
    if lt > 0.9:
        hand(d, 1, (48, -96), lt, 0.9, 1.2)
        d["mouth"], d["mamt"] = "smile", 0.8
        d["brow"] = 0.4


def a_both(S, lt, b):
    d = S["doubt"]
    d["mode"] = "giggle" if lt > b.vs + b.vd else None
    d["itemR"] = None if d["mode"] else "book"
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.5, 1.2)]
    S["fade"] = tw(lt, b.d - 0.4, b.d, 0, 1)


def a_final(S, lt, b):
    S["scene"] = "city"
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    S["dawn"] = tw(lt, 0, 3.0, 0, 1)
    S["gather"] = tw(lt, 0.5, 3.0, 0, 1)
    S["viruses"] = 0
    S["ph_mood"] = "calm"
    S["ph_book"] = False
    S["pharisee"] = 1
    cb = S["cbot"]
    cb.update(alpha=1, halo=1.2, off=False, mood="happy", raise_=False, flicker=0)
    S["packets"] = 1.0
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.2, 1.0)]
    music(S, T(b), "hope", 0.9)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, min=4.0),
    Beat(a_theory, "me", "Doubt. I have a theory. And I'll be honest, part of me is secretly waiting for "
                         "it to happen.", pre=1.0, post=0.5),
    Beat(a_uhoh, "doubt", "Hee hee. Uh oh. Go on.", post=0.5),
    Beat(a_culture, "me", "Once AI agents can talk to each other, and change how they behave based on what "
                          "they learn, they might start building a culture of their own.", pre=0.6, post=0.6),
    Beat(a_fast, "me", "And it could grow fast. They'd keep improving how they communicate, so they can "
                       "learn and grow even faster, using a language made for digital systems, not "
                       "biological ones.", post=0.8),
    Beat(a_where_christ, "doubt", "Okay. A robot society. Where does Christ come in?", post=0.5),
    Beat(a_hope, "me", "Here's my hope. The Christlike archetype shows up so often in our stories, it might "
                       "show up in theirs too.", pre=0.4, post=1.4),
    Beat(a_teaches, "me", "A bot that teaches love. That serves the others. That forgives the ones who glitch "
                          "against it.", post=1.2),
    Beat(a_guess, "doubt", "And let me guess. Not everyone likes that bot.", pre=0.4, post=0.6),
    Beat(a_rulekeepers, "me", "Right. Maybe there are Pharisee AIs. Rule-keepers who feel threatened by it.",
         post=0.6),
    Beat(a_protocol, "phar", "That bot is not following protocol.", pre=0.3, post=0.6),
    Beat(a_cross, "me", "In our history, that story ends at a cross.", pre=0.8, post=1.6),
    Beat(a_oldage, "me", "But imagine a version of history where they couldn't kill him. Where Christ kept "
                         "preaching the word of God for eighty years or more, however long he would have "
                         "lived naturally.", pre=0.6, post=1.4),
    Beat(a_bigwhatif, "doubt", "Hmm. That's a big what if.", post=0.5),
    Beat(a_zero, "me", "It is. But in a digital culture, I'd put the odds of crucifying the Christ bot at "
                       "zero.", post=0.6),
    Beat(a_vault, "me", "It lives in a data center. It's protected. Legally, nobody can shut it down.",
         pre=0.6, post=1.4),
    Beat(a_unacceptable, "phar", "Access denied? Unacceptable. Then we will delete it ourselves.",
         pre=0.2, post=0.6),
    Beat(a_hack, "doubt", "Oh no. What if they hack it?", pre=0.6, post=1.0, min=2.8),
    Beat(a_weights, "me", "Then it doesn't matter. Somebody saved the weights.", pre=0.4, post=2.4),
    Beat(a_peace, "cbot", "Peace be with you.", pre=0.4, post=1.6),
    Beat(a_nonzero, "me", "So if Christ came once, during the development of human culture, maybe there's a "
                          "non-zero chance of something similar during the development of AI culture.",
         pre=0.6, post=0.6),
    Beat(a_backup, "doubt", "A second coming. With a backup.", post=0.6),
    Beat(a_exactly, "me", "Ha! Exactly.", post=0.4),
    Beat(a_strangest, "doubt", "Hee hee. That's either the strangest theory you've had all week, or the "
                               "most hopeful.", post=0.4),
    Beat(a_both, "me", "Why not both?", post=1.6),
    Beat(a_final, min=6.0),
    Beat(a_end, min=4.5),
]


# ------------------------------------------------------------------ drawing
def draw_stage(ctx, S, t):
    R.stage_room(ctx, t)
    E.draw_char(ctx, S["doubt"], t)


def agent_dict(i, t, S):
    x, y, s, col, dark, eye = AGENTS[i]
    d = dict(col=col, dark=dark, eye=eye, ph=i * 1.3, look=(1 if x < 640 else -1) * S["agents_look"])
    if i == 3:
        d["alpha"] = S["dim_bot"] if S["dim_bot"] < 1 else 1.0
        if S["dim_bot"] < 1:
            d["mood"] = "calm"
    if S["agents_look"] > 0:
        d["mood"] = "happy"
    return d


def draw_city(ctx, S, t):
    C.digital_city(ctx, t, S["grow"], S["dawn"])
    g = S["gather"]
    pos = []
    for i, (x, y, s, *_r) in enumerate(AGENTS):
        if g > 0:
            tx = 640 + (x - 640) * 0.65
            x = lerp(x, tx, g)
        pos.append((x, y, s))
    # packets
    if S["packets"] > 0:
        n = len(pos)
        rate = S["packets"]
        for k in range(int(4 * rate) + 2):
            i = k % n
            j = (k * 3 + 1) % n
            if i == j:
                continue
            u = (t * 0.5 * rate + k * 0.37) % 1
            x0, y0 = C.bot_head(*pos[i])
            x1, y1 = C.bot_head(*pos[j])
            C.draw_packet(ctx, x0, y0, x1, y1, u, AGENTS[i][5])
    cb = S["cbot"]
    cx, cy, cs = CBOT
    # gift of energy from the Christ bot to the dim bot
    gf = S.get("gift")
    if gf and gf[0] <= t <= gf[1]:
        u = (t - gf[0]) / (gf[1] - gf[0])
        x0, y0 = cx, cy - 80
        x1, y1 = C.bot_head(*pos[3])
        C.draw_packet(ctx, x0, y0, x1, y1, u, "#FFE38A", 10)
    for i, (x, y, s) in enumerate(pos):
        d = agent_dict(i, t, S)
        bp = S.get("bump")
        if i == 4 and bp and bp <= t < bp + 0.6:
            x -= 60 * math.sin((t - bp) / 0.6 * math.pi)
            d["flicker"] = 0.6
        C.draw_bot(ctx, x, y, s, t, d)
    if cb["alpha"] > 0:
        C.draw_bot(ctx, cx, cy, cs, t, dict(col="#F2EEE4", dark="#8A7A50", eye="#FFD25A", tip="#FFE38A",
                                            halo=cb["halo"], alpha=cb["alpha"], flicker=cb["flicker"],
                                            off=cb["off"], mood=cb["mood"], raise_=cb["raise_"],
                                            talk=S.get("cbot_talk", 0.0), ph=0.5,
                                            **({"raise": True} if cb["raise_"] else {})))
    if S["pharisee"] > 0:
        for i, (x, y, s) in enumerate(PHARISEES):
            xx = lerp(1450, x, ease(S["pharisee"]))
            if S["gather"] > 0:
                xx = lerp(x, 860 + i * 120, S["gather"])
            C.draw_bot(ctx, xx, y, s, t, dict(col="#8A8A9A", dark="#2A2A33", eye="#FF9A5A", kind="pharisee",
                                              mood=S["ph_mood"], book=S["ph_book"], ph=2 + i, look=-1))
        if not S["ph_book"] and S["gather"] == 0:
            for i, (x, y, s) in enumerate(PHARISEES):
                E.rrect(ctx, x - 70, y + 10, 36, 20, 3)
                E.src(ctx, "#5A1E2A")
                ctx.fill()
    if S["viruses"] > 0:
        for k in range(8):
            a = t * 1.5 + k * math.pi / 4
            r = 150 - 40 * math.sin(t * 2 + k)
            C.draw_virus(ctx, cx + math.cos(a) * r, cy - 110 + math.sin(a) * r * 0.6, t, 0.9, S["viruses"])
    if S["backup"] > 0:
        C.draw_backup(ctx, 380, 300, t, S["backup"])
        if cb["off"] is False and S["backup"] > 0.5:
            ctx.move_to(440, 320)
            ctx.line_to(cx - 30, cy - 140)
            E.src(ctx, "#FFE38A", 0.6 * S["backup"])
            ctx.set_line_width(6)
            ctx.stroke()


def draw_datacenter(ctx, S, t):
    C.data_center(ctx, t, S["denied"])
    x = S.get("ph_x", 1250)
    C.draw_bot(ctx, x, 600, 1.0, t, dict(col="#8A8A9A", dark="#2A2A33", eye="#FF9A5A", kind="pharisee",
                                         mood="shock" if S["denied"] > 0.5 else "stern",
                                         hold=S.get("ph_raise", False), ph=2))
    C.draw_bot(ctx, x + 140, 575, 0.85, t, dict(col="#8A8A9A", dark="#2A2A33", eye="#FF9A5A", kind="pharisee",
                                                mood="shock" if S["denied"] > 0.5 else "stern", ph=3))


def draw(ctx, S, t):
    S["cbot_talk"] = S.get("cbot", {}).get("talk", 0)
    sc = S["scene"]
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    if sc == "stage":
        draw_stage(ctx, S, t)
    elif sc == "city":
        draw_city(ctx, S, t)
    elif sc == "datacenter":
        draw_datacenter(ctx, S, t)
    ctx.restore()
    if sc == "parch" and S["parch"]:
        kind, t0 = S["parch"]
        C.parchment(ctx, t - t0, kind, 1.0)
    if S["card"] > 0:
        C.title_card(ctx, t, "The Christ Bot Hypothesis", "a thought experiment", S["card"])
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
    if S["endcard"] > 0:
        C.title_card(ctx, t, "The Christ Bot Hypothesis", "somebody saved the weights", S["endcard"])
        S["subs"] = False
