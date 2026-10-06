"""Shared state, bleeps, music cuts and drawing for Lab Partners."""
import math

import cairo

import engine as E
from engine import tw, ease, clamp, lerp
from dcommon import sfx, hand, walk, cam_to, apply_cam  # noqa: F401
from show import Beat
import mgfx as M

SCREEN = (0, 0, 1280, 720)
GROUND = M.GROUND


def mus(S, t, mood, vol=1.0, fin=0.6, fout=0.6):
    """Music schedule entry with explicit fades (tiny fades = hard cut)."""
    S["music"].append((t, mood, vol, (fin, fout)))


def base_state():
    return dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0, fade=0.0,
                card=None, endcard=None, scene="lab", show=[], fx={}, flash=0.0)


def T(b, off=0.0):
    return b.start + off


def VEND(b):
    return b.start + b.vs + b.vd


def bleep(dur=0.55, who="vex"):
    def act(S, lt, b):
        sfx(S, T(b, 0.02), "bleep", 1.0)
        if lt < b.d:
            S["subtitle"] = ("[BLEEP]", who)
            if who in S:
                S[who]["talk"] = 0.9
    return Beat(act, min=dur)


def place(c, x, face=0.0, px=0.0, **kw):
    base = dict(tilt=0.0, yoff=0.0, y=GROUND, walking=0, wide=0.0, sweat=0.0, shake=0.0)
    base.update(kw)
    c.update(x=x, face=face, px=px, **base)


def stare(c):
    c.update(face=0.0, px=0.0, py=0.0, lid=0.45, mouth="flat", mamt=0.0, brow=-0.2, mode=None)


BG = {
    "lab": lambda ctx, S, t: M.lab(ctx, t, S["fx"].get("dial", 0.5), 1.0, S["fx"].get("wreck", 0.0)),
    "city": lambda ctx, S, t: M.city(ctx, t, S["fx"].get("smash")),
    "beach": lambda ctx, S, t: M.beach(ctx, t),
    "office": lambda ctx, S, t: M.office(ctx, t),
    "stage": lambda ctx, S, t: M.comedy_stage(ctx, t, S["fx"].get("spot", 1.0)),
    "sitcom": lambda ctx, S, t: M.sitcom_set(ctx, t),
    "medals": lambda ctx, S, t: M.medal_wall(ctx, t),
    "dark": lambda ctx, S, t: M.dark_room(ctx, t),
    "hall": lambda ctx, S, t: M.hallway(ctx, t),
    "road": lambda ctx, S, t: _road(ctx, t),
    "vault": lambda ctx, S, t: _vault(ctx, t),
}


def _road(ctx, t):
    g = cairo.LinearGradient(0, 0, 0, 500)
    g.add_color_stop_rgb(0, *E.rgb("#4A2A6A"))
    g.add_color_stop_rgb(1, *E.rgb("#E86A5A"))
    ctx.set_source(g)
    ctx.paint()
    ctx.rectangle(0, 520, W_, 200)
    E.src(ctx, "#2A2A30")
    ctx.fill()
    for i in range(10):
        x = (i * 160 - t * 600) % 1600 - 160
        ctx.rectangle(x, 600, 80, 10)
        E.src(ctx, "#E8E4DA")
        ctx.fill()


def _vault(ctx, t):
    E.src(ctx, "#2A1E10")
    ctx.paint()
    ctx.rectangle(0, 600, W_, 120)
    E.src(ctx, "#1A1208")
    ctx.fill()


W_ = E.W


def draw_world(ctx, S, t, extra_before=None, extra_after=None):
    ctx.save()
    apply_cam(ctx, S, t, SCREEN)
    BG[S["scene"]](ctx, S, t)
    if extra_before:
        extra_before(ctx, S, t)
    for n in S["show"]:
        if n.startswith("@"):
            S["props"][n](ctx, S, t)
        else:
            E.draw_char(ctx, S[n], t)
    if extra_after:
        extra_after(ctx, S, t)
    ctx.restore()


def overlays(ctx, S, t, card_title, card_sub, end_title="To be continued...", end_sub=""):
    if S["flash"] > 0:
        ctx.set_source_rgba(1, 1, 1, S["flash"])
        ctx.paint()
    g = cairo.RadialGradient(640, 360, 320, 640, 360, 820)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.3)
    ctx.set_source(g)
    ctx.paint()
    if S["fade"] > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(S["fade"]))
        ctx.paint()
    if S["card"]:
        M.title_card(ctx, t, card_title, card_sub, S["card"])
    if S["endcard"]:
        M.title_card(ctx, t, end_title, end_sub, S["endcard"])
        S["subs"] = False
