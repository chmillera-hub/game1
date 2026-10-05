"""Shared staging for DO NOT DISTURB."""
from toon.engine import Part
from .style import THEME

ROOM_FLOOR = 1560      # feet line for people standing in Tiredness's room
CHAIR_Y = 1470         # Tiredness's origin when he sits in the gaming chair
KITCHEN_FLOOR = 1480


def new_part(num, subtitle, slug):
    return Part(num, subtitle, slug, theme=THEME)


def title(P, num, subtitle):
    s = P.shot("d_card", card="title", part=f"PART {num}", subtitle=subtitle)
    s.sfx("creak", gain=0.6)
    s.sfx("dun", at=0.5, gain=0.8)
    s.wait(2.4)
    return s.end()


def tbc(P, nxt):
    s = P.shot("d_card", card="tbc", next=nxt)
    s.sfx("dun", gain=0.7)
    s.wait(2.6)
    return s.end()


def hop_loop(a, t0, n, period=0.5, h=10):
    for k in range(n):
        a.to(t0 + k * period, period / 2, "out", hop=h)
        a.to(t0 + k * period + period / 2, period / 2, "in", hop=0)
