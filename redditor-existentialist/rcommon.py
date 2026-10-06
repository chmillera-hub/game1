"""Shared helpers for the three parts."""
import math

import engine as E
from engine import clamp, tw, ease, lerp
from dcommon import sfx, music, active, hand, walk, cam_to, apply_cam  # noqa: F401
import rgfx as G

SCREEN = (0, 0, 1280, 720)


def base_state():
    return dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0,
                fade=0.0, card=0.0, endcard=0.0, scene="bedroom", chat=[], flash=0.0, gray=0.0)


def say_chat(S, who, text, t0, dur=1.0):
    S["chat"].append(dict(who=who, text=text, t0=t0, dur=dur))


def chat_msgs(S, t):
    out = []
    for m in S["chat"]:
        if t < m["t0"]:
            continue
        a = clamp((t - m["t0"]) / 0.3)
        frac = clamp((t - m["t0"]) / m["dur"]) if m["who"] == "user" else 1.0
        out.append((m["who"], m["text"], a, frac))
    return out


def sitting_redditor(c, x=720):
    c.update(x=x, y=540, face=-0.7, px=-1.0, footL=(-34, 62), footR=(-14, 64))
    c["hl"] = (-92, -116)
    c["hr"] = (-58, -112)


def draw_chair_flipped(ctx, x):
    ctx.save()
    ctx.translate(x, 0)
    ctx.scale(-1, 1)
    ctx.translate(-x, 0)
    G.draw_chair(ctx, x)
    ctx.restore()


def fade(ctx, a):
    if a > 0:
        ctx.set_source_rgba(0, 0, 0, clamp(a))
        ctx.paint()
