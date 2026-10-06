"""Shared state and camera for the dungeon parts."""
import math

import engine as E
from engine import clamp, tw, ease
from common import sfx, music, active, hand, walk  # noqa: F401


def base_state():
    return dict(sfx=[], music=[], subtitle=None, subs=True, cam=[640.0, 360.0, 1.0], shake=0.0,
                fade=0.0, card=0.0, endcard=0.0, scene="tunnel", amb=0.93, flash=0.0)


def cam_to(S, lt, t0, t1, x, y, z, fn=ease):
    S["cam"] = [tw(lt, t0, t1, S["cam"][0], x, fn), tw(lt, t0, t1, S["cam"][1], y, fn),
                tw(lt, t0, t1, S["cam"][2], z, fn)]


def apply_cam(ctx, S, t, world):
    x0, y0, x1, y1 = world
    cx, cy, z = S["cam"]
    z = max(z, E.W / (x1 - x0), E.H / (y1 - y0))
    cx = clamp(cx, x0 + E.W / 2 / z, x1 - E.W / 2 / z)
    cy = clamp(cy, y0 + E.H / 2 / z, y1 - E.H / 2 / z)
    sh = S["shake"]
    ctx.translate(E.W / 2 + math.sin(t * 71) * sh * 12, E.H / 2 + math.cos(t * 59) * sh * 9)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


def ambience(S, total):
    k = 0.0
    while k < total:
        sfx(S, k, "caveamb", 0.55)
        k += 23.5
