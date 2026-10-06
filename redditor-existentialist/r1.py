"""Part 1: The Void."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp, ease_out, ease_in, back_out, linear
import rgfx as G
from rcommon import (sfx, music, active, hand, walk, cam_to, apply_cam, base_state, say_chat, chat_msgs,
                     sitting_redditor, draw_chair_flipped, fade, SCREEN)
from show import Beat

TOTAL = 0.0
IDX = {}


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
    r = G.new_redditor(720)
    sitting_redditor(r)
    S["r"] = r
    S["card"] = 1.0
    S["barrier"] = 0.0
    S["life_walls"] = [0.0, 0.0, 0.0]
    S["box"] = 0.0
    S["void_text"] = None
    return S


def at_desk(S, lt, b, zoom=1.0, cx=640, cy=360):
    S["scene"] = "bedroom"
    cam_to(S, lt, 0, 0.8, cx, cy, zoom)


def typing(S, b, who_text):
    """Show the redditor's message being typed while the line is spoken."""
    S["scene"] = "chat"
    say_chat(S, "user", who_text, T(b, b.vs), max(0.5, b.vd))
    sfx(S, T(b, b.vs), "typing", 0.6)
    if b.vd > 2.6:
        sfx(S, T(b, b.vs + 2.4), "typing", 0.6)
    if b.vd > 5.0:
        sfx(S, T(b, b.vs + 4.8), "typing", 0.6)


def ai_reply(S, b, txt):
    S["scene"] = "chat"
    say_chat(S, "ai", txt, T(b, 0.5))
    sfx(S, T(b, 0.5), "ding", 0.35)


# ------------------------------------------------------------------ acts
def a_title(S, lt, b):
    music(S, T(b), "void", 0.6)
    S["card"] = 1.0


def a_room(S, lt, b):
    S["card"] = tw(lt, 0, 1.0, 1.0, 0.0)
    S["scene"] = "bedroom"
    S["cam"] = [tw(lt, 0, b.d, 640, 620), 360, tw(lt, 0, b.d, 1.0, 1.15)]
    music(S, T(b, 0.6), "lofi", 0.7)
    sfx(S, T(b, 1.0), "typing", 0.4)


def a_tried(S, lt, b):
    r = S["r"]
    at_desk(S, lt, b, 1.6, 640, 400)
    r["hl"] = (-80 + math.sin(lt * 20) * 4, -62)
    r["hr"] = (-70 - math.sin(lt * 23) * 4, -70)
    sfx(S, T(b, 0.5), "typing", 0.4)


def t1(S, lt, b):
    typing(S, b, "I've tried AI before. It told me to journal and drink water. Groundbreaking.")


def t2(S, lt, b):
    typing(S, b, "I go to work. I come home. I scroll. I sleep. I haven't felt anything in months.")


def t3(S, lt, b):
    typing(S, b, "Someone said this prompt shows you the creatures living inside you. So be honest. "
                 "Is this worth my time, or is it another gimmick?")


def ai1(S, lt, b):
    ai_reply(S, b, "Let's find out. Close your eyes. What's the first thing you notice inside?")


def a_sham(S, lt, b):
    r = S["r"]
    at_desk(S, lt, b, 2.4, 700, 400)
    r["lid"] = tw(lt, 0, 0.5, 0.42, 1.0) if lt < 2.0 else tw(lt, 2.0, 2.3, 1.0, 0.42)
    r["blink"] = False
    r["brow"] = -0.3 if lt > 2.3 else 0
    r["mouth"], r["mamt"] = "frown", 0.4
    r["face"] = -0.4
    r["px"] = 0.3


def a_creature(S, lt, b):
    r = S["r"]
    r["px"], r["py"] = 0.4, 0.6
    r["blink"] = True
    cam_to(S, lt, 0, b.d, 720, 400, 2.0)


def ai2(S, lt, b):
    ai_reply(S, b, "What does the emptiness feel like?")


def a_pain(S, lt, b):
    r = S["r"]
    at_desk(S, lt, b, 2.2, 700, 400)
    hand(r, 1, (-6, -82), lt, 0.3, 0.9)
    r["px"], r["py"] = 0.0, 0.7
    r["brow"] = 0.5
    r["mouth"], r["mamt"] = "frown", 0.5


def a_heart(S, lt, b):
    r = S["r"]
    cam_to(S, lt, 0, b.d, 712, 430, 3.0)
    tl = b.vs + b.vd * 0.6
    r["glow"] = 0
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


def a_void_in(S, lt, b):
    S["scene"] = "void"
    S["fade"] = tw(lt, 0, 0.8, 1, 0)
    r = S["r"]
    r.update(x=260, y=E.GROUND, face=0.5, px=1.0, py=-0.2, footL=(0, 0), footR=(0, 0), lid=0.42,
             brow=0.3, mouth="frown", mamt=0.3)
    r["hl"], r["hr"] = E.pose("redditor", -1, "rest"), E.pose("redditor", 1, "rest")
    S["cam"] = [tw(lt, 0, b.d, 640, 600), 360, tw(lt, 0, b.d, 1.0, 1.08)]
    music(S, T(b), "void", 0.9)
    sfx(S, T(b, 0.2), "sting", 0.4)


def a_cliff(S, lt, b):
    r = S["r"]
    r["px"] = 1.0
    r["brow"] = 0.6
    S["cam"] = [tw(lt, 0, b.d, 600, 330), tw(lt, 0, b.d, 360, 470), tw(lt, 0, b.d, 1.08, 1.8)]


def ai3(S, lt, b):
    S["void_text"] = ("What happens when you move toward it?", T(b, 0.4), T(b, b.d))
    sfx(S, T(b, 0.4), "ding", 0.3)
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], 640), 360, tw(lt, 0, 1.0, S["cam"][2], 1.0)]


def a_stops(S, lt, b):
    r = S["r"]
    walk(r, 470, lt, 0.2, 2.0, 0.6)
    tb = 1.6
    S["barrier"] = tw(lt, tb, tb + 0.9, 0, 1, ease_out)
    if tb < lt < tb + 1.0:
        S["shake"] = 0.5 * (1 - (lt - tb))
    else:
        S["shake"] = 0
    sfx(S, T(b, tb), "rumble", 0.8)
    if lt > tb + 0.3:
        r["wide"] = tw(lt, tb + 0.3, tb + 0.6, 0, 0.8)
        r["py"] = -0.8
    S["void_text"] = None


def a_says(S, lt, b):
    r = S["r"]
    r["wide"] = tw(lt, 0, 1, 0.8, 0.1)
    r["py"] = tw(lt, 0, 1, -0.8, -0.4)
    S["cam"] = [tw(lt, 0, b.d, 640, 560), 380, tw(lt, 0, b.d, 1.0, 1.3)]


def a_push(S, lt, b):
    r = S["r"]
    hand(r, -1, (70, -110), lt, 0.2, 0.6)
    hand(r, 1, (80, -90), lt, 0.2, 0.6)
    if lt > 0.6:
        r["tilt"] = 0.18 + math.sin(lt * 6) * 0.03
        r["footL"] = (-14, 0)
        r["mouth"], r["mamt"] = "tight", 1.0
    for k in range(3):
        sfx(S, T(b, 0.8 + k * 1.1), "thud", 0.5)


def a_quit(S, lt, b):
    r = S["r"]
    r["tilt"] = tw(lt, 0, 0.5, r["tilt"], 0)
    hand(r, -1, "rest", lt, 0, 0.5)
    hand(r, 1, "rest", lt, 0, 0.5)
    r["mouth"], r["mamt"] = "frown", 0.6
    r["face"] = tw(lt, 0.5, 1.2, 0.5, -0.4)
    r["px"] = tw(lt, 0.5, 1.2, 1.0, -0.6)
    r["py"] = 0.6
    S["cam"] = [tw(lt, 0, 1.0, S["cam"][0], 520), 380, tw(lt, 0, 1.0, S["cam"][2], 1.5)]
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


def a_life(S, lt, b):
    S["scene"] = "life"
    S["fade"] = tw(lt, 0, 0.6, 1, 0)
    S["gray"] = 0.85
    r = S["r"]
    sitting_redditor(r)
    r.update(tilt=0, lid=0.55, mouth="frown", mamt=0.3, brow=0.4, px=0.3, py=0.5, face=-0.3)
    S["cam"] = [640, 360, 1.0]
    music(S, T(b), "void", 0.7)


def a_walls_rise(S, lt, b):
    for i, tt in enumerate((0.8, 2.2, 3.6)):
        S["life_walls"][i] = tw(lt, tt, tt + 0.8, 0, 1, ease_out)
        sfx(S, T(b, tt), "rumble", 0.6)
    r = S["r"]
    r["px"] = math.sin(lt * 1.2) * 0.8


def a_surrounded(S, lt, b):
    r = S["r"]
    r["px"], r["py"] = 0, 0.7
    r["lid"] = 0.5
    cam_to(S, lt, 0, b.d, 680, 380, 1.4)
    S["fade"] = tw(lt, b.d - 0.5, b.d, 0, 1)


def a_box(S, lt, b):
    S["scene"] = "boxclose"
    S["fade"] = tw(lt, 0, 0.5, 1, 0)
    r = S["r"]
    r.update(x=640, y=640, face=0, px=0, py=-0.3, footL=(0, 0), footR=(0, 0), tilt=0, lid=0.42,
             wide=0.0, mouth="frown", mamt=0.4)
    r["hl"], r["hr"] = E.pose("redditor", -1, "rest"), E.pose("redditor", 1, "rest")
    S["box"] = tw(lt, 0.6, b.d - 0.4, 0, 1, linear)
    S["cam"] = [640, 400, tw(lt, 0, b.d, 1.0, 1.15)]
    for k, tt in enumerate((0.8, 1.6, 2.2, 3.0)):
        if tt < b.d:
            sfx(S, T(b, tt), "slam", 0.8)
    r["px"] = math.sin(lt * 2) * 0.9


def a_dark(S, lt, b):
    S["fade"] = 1.0
    sfx(S, T(b, 0.1), "slam", 1.0)
    music(S, T(b), None, 0)


def a_end(S, lt, b):
    S["endcard"] = tw(lt, 0, 0.8, 0, 1)
    music(S, T(b, 0.2), "void", 0.7)


# ------------------------------------------------------------------ script
BEATS = [
    Beat(a_title, "narr", "Picture this. It's two forty-seven in the morning.", pre=1.5, post=1.0, min=5.0),
    Beat(a_room, "narr", "Somewhere, a redditor from a doomer subreddit stumbles across a prompt about "
                         "journeying into their emotional world.", pre=0.6, post=0.8),
    Beat(a_tried, "narr", "They've used AI before. It never showed them anything interesting. But tonight, "
                          "they're curious enough to try.", post=0.8),
    Beat(t1, "redditor", "I've tried AI before. It told me to journal and drink water. Groundbreaking.",
         post=0.8),
    Beat(t2, "redditor", "I go to work. I come home. I scroll. I sleep. I haven't felt anything in months.",
         post=0.8),
    Beat(t3, "redditor", "Someone said this prompt shows you the creatures living inside you. So be honest. "
                         "Is this worth my time, or is it another gimmick?", post=0.8),
    Beat(ai1, min=4.2),
    Beat(a_sham, "redditor", "Honestly? I think this whole thing is a sham. There couldn't be a being inside "
                             "me. I just feel nothing.", pre=0.6, post=0.8),
    Beat(a_creature, "redditor", "And if there were a creature in there, it would be one that hurts me. But it "
                                 "doesn't exist. Because I'm empty inside.", post=0.8),
    Beat(ai2, min=3.4),
    Beat(a_pain, "redditor", "There's pain. But it's not physical pain. It's a void. An absence of meaning.",
         pre=0.5, post=0.8),
    Beat(a_heart, "redditor", "It's soul-wrenching. It's not a nail in the heart. It's the absence of a heart.",
         post=1.4),
    Beat(a_void_in, "redditor", "When I think about exploring it, it's like exploring the absence of oxygen. "
                                "The absence of life.", pre=1.4, post=0.8),
    Beat(a_cliff, "redditor", "It just wants to consume me. Why would I step off the cliff to understand the "
                              "cliff?", post=1.4),
    Beat(ai3, min=3.4),
    Beat(a_stops, "redditor", "That's the thing. When I get close, I don't want to step in. Something stops "
                              "me.", pre=2.8, post=0.6),
    Beat(a_says, "redditor", "A barrier. Something that says: do not step into the void, unless the void "
                             "consumes you.", post=0.8),
    Beat(a_push, "redditor", "It doesn't talk. It just sits there. A solid wall. It won't let me move.",
         pre=0.8, post=1.0, min=4.4),
    Beat(a_quit, "redditor", "So I want to quit. I see the void, but when I step near it, a part of me stops "
                             "me. And I don't know why.", post=1.0),
    Beat(a_life, "redditor", "So I go back to my life. And I see even more emptiness.", pre=1.0, post=0.6),
    Beat(a_walls_rise, "redditor", "I can't go toward the void inside me. And outside of me, there's more void. "
                                   "More walls. Because I don't even want to get up.", post=1.2, min=5.0),
    Beat(a_surrounded, "redditor", "I'm surrounded. Where is there to turn? I'm blocked from the inside. I'm "
                                   "blocked from the outside.", post=0.8),
    Beat(a_box, "redditor", "Blocked from every angle. Like I'm in a box.", pre=0.6, post=2.0, min=4.4),
    Beat(a_dark, min=1.6),
    Beat(a_end, "narr", "To be continued.", pre=0.8, post=2.6, min=5.0),
]


# ------------------------------------------------------------------ drawing
def draw_bedroom(ctx, S, t, gray=0.0):
    r = S["r"]
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    ctx.set_source_surface(G.bedroom_bg(), 0, 0)
    ctx.paint()
    if S["scene"] == "life":
        # the window shows the void now
        ctx.save()
        E.rrect(ctx, 820, 90, 340, 240, 6)
        ctx.clip()
        G.draw_void_space(ctx, t, vx=990, vy=210, vr=90)
        ctx.restore()
    draw_chair_flipped(ctx, r["x"] + 40)
    G.draw_monitor(ctx, t, 1.0)
    E.draw_char(ctx, r, t)
    if S["scene"] == "life":
        for (x, w, h), u in zip(((160, 120, 380), (1060, 140, 420), (520, 100, 300)), S["life_walls"]):
            G.draw_barrier(ctx, x, 640, u, t, w=w, h=h)
    ctx.restore()
    # monitor glow on the scene
    g = cairo.RadialGradient(480, 300, 40, 480, 300, 900)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.55)
    ctx.set_source(g)
    ctx.paint()
    if gray > 0:
        G.desaturate(ctx, gray)


def draw_void(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    G.draw_void_space(ctx, t, vx=960, vy=330, vr=180, barrier=S["barrier"], bx=590)
    E.draw_char(ctx, S["r"], t)
    vt = S["void_text"]
    if vt and vt[1] <= t < vt[2]:
        a = clamp((t - vt[1]) / 0.6) * clamp((vt[2] - t) / 0.4)
        E.rrect(ctx, 360, 120, 560, 70, 20)
        E.src(ctx, "#2A3142", 0.85 * a)
        ctx.fill()
        E.text(ctx, vt[0], 640, 166, 26, "#D8E0F0", alpha=a)
    ctx.restore()


def draw_boxclose(ctx, S, t):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    g = cairo.RadialGradient(640, 400, 40, 640, 400, 800)
    g.add_color_stop_rgb(0, *E.rgb("#1A1626"))
    g.add_color_stop_rgb(1, *E.rgb("#050408"))
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, 640, 1280, 80)
    E.src(ctx, "#121018")
    ctx.fill()
    G.draw_box_back(ctx, t, 640, S["box"])
    E.draw_char(ctx, S["r"], t)
    G.draw_box_exterior(ctx, t, 640, S["box"])
    ctx.restore()


def draw(ctx, S, t):
    sc = S["scene"]
    if sc == "chat":
        G.draw_chat(ctx, t, chat_msgs(S, t))
        S["subs"] = False
    elif sc in ("bedroom", "life"):
        draw_bedroom(ctx, S, t, S["gray"] if sc == "life" else 0)
    elif sc == "void":
        draw_void(ctx, S, t)
    elif sc == "boxclose":
        draw_boxclose(ctx, S, t)
    if S["card"] > 0:
        G.title_card(ctx, t, "Redditor Existentialist", "Part 1: The Void", S["card"])
    fade(ctx, S["fade"])
    if S["endcard"] > 0:
        G.end_card(ctx, t, "To be continued...", "Part 2: The Box", a=S["endcard"])
        S["subs"] = False
