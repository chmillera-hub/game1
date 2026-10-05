"""Staging helpers shared by the three parts."""
from toon.sets import ROW_Y, SEAT_OFF

STAGE_Y = 1235          # feet line on the stage
STOOL_SEAT_Y = 1092     # Cartman origin when sitting on the stool
ROW2 = ROW_Y[2] + SEAT_OFF


def title(part, num, subtitle):
    s = part.shot("card", card="title", part=f"PART {num}", subtitle=subtitle)
    s.sfx("sting")
    s.wait(2.2)
    return s.end()


def text_card(part, lines, d=1.6, sfx="whoosh"):
    s = part.shot("card", card="text", lines=lines)
    if sfx:
        s.sfx(sfx, gain=0.8)
    s.wait(d)
    return s.end()


def stage_duo(s, pc_x=300, chad_x=780, scale=0.95, **kw):
    pc = s.actor("pc", **{**dict(x=pc_x, y=STAGE_Y, scale=scale), **kw.get("pc", {})})
    chad = s.actor("chad", **{**dict(x=chad_x, y=STAGE_Y, scale=scale), **kw.get("chad", {})})
    return pc, chad


def stands_trio(s, cart=None, f1=None, f2=None):
    cart = s.actor("cartman", **{**dict(x=540, y=ROW2, scale=0.78, layer=2, sit=1), **(cart or {})})
    a = s.actor("friend1", **{**dict(x=330, y=ROW2, scale=0.72, layer=2, seated=1), **(f1 or {})})
    b = s.actor("friend2", **{**dict(x=750, y=ROW2, scale=0.72, layer=2, seated=1), **(f2 or {})})
    return cart, a, b


def cam_cartman_stands(s, zoom=1.7, cy=1180, **kw):
    s.camera(cx=540, cy=cy, zoom=zoom, **kw)
