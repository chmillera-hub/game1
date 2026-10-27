"""Performance notes for Hale and Kai, keyed to the voice timeline.

Keys: (anchor, {...}) with
  e  expression preset (et = blend seconds, ex = extra face params)
  g  gaze target (other, other_hands, hands, down, down_l, away, away_r, cam, or a cast.GAZE_POINTS name)
     gt = eye transition; a gaze shift forces a blink unless gblink=False
  p  pose preset from poses.py (pt = blend seconds)
  x  horizontal offset from the seat in world px (xt)      stand  0..1 (st)
  wet / tear  eye wetness / tear track      talk  0..1 unvoiced chatter (kt)
  gest  nod, nod2, shake, tilt, shrug, laugh, sigh, sniff, flinch, swallow, bounce (gd = duration, ga = amplitude)

Subtext: Kai recognises Hale from the start; she doesn't recognise him until L35.
"""
from anchors import At, L, Wd

BUMP = Wd("L46", "bump", "start", 0.25)
POT_DOWN = Wd("L09", "asked", "end", -0.05)

HALE = [
    # ---- 2 AM: alone with the news, the belt on the table
    (At(0.0), dict(p="rest", pt=0.0, e="wistful", ex=dict(eopen=0.78, binner=0.3, msmile=-0.05), et=0.0, g="tv", gt=0.0)),
    (At(1.3), dict(gest="sigh", gd=1.8, ga=0.5)),
    (At(3.6), dict(blink=True)),
    (Wd("L01", "And", "start", -0.3), dict(e="thinking", ex=dict(eopen=0.8, bfurrow=0.15), et=0.4)),
    (Wd("L01", "locked", "start", -0.4), dict(p="cuffs", pt=0.8, g="cuffs", gt=0.35)),
    (Wd("L01", "cage", "end", 0.2), dict(e="wistful", ex=dict(binner=0.55, msmile=-0.15), et=0.6, gest="swallow", gd=0.6)),
    # ---- Kai with the coffee pot
    (L("L03", "start", -0.9), dict(p="rest", pt=0.0, g="window", gt=0.0, e="wistful", ex=dict(eopen=0.8), et=0.0)),
    (L("L03", "start", 0.05), dict(g="other", gt=0.2, e="content", ex=dict(eopen=0.86, msmile=0.25), et=0.4)),
    (L("L04", "start", 0.0), dict(gest="nod", gd=0.5, ga=0.5)),
    (Wd("L04", "Please", "end", 0.0), dict(g="mug_hale", gt=0.25)),
    (Wd("L05", "those"), dict(g="cuffs", gt=0.3)),
    (L("L06", "start", 0.0), dict(e="wistful", ex=dict(msmile=0.1), et=0.5)),
    (Wd("L06", "all"), dict(g="window", gt=0.4)),
    (L("L06", "end", -0.2), dict(e="wistful", ex=dict(msmile=0.22, masym=0.35), et=0.4)),
    # the car door outside: Kai flinches, she notices
    (L("L06", "end", 0.62), dict(g="other", gt=0.15, gblink=False, e="curious", ex=dict(binner=0.4, msmile=0.0), et=0.3)),
    (L("L07", "start", 0.1), dict(e="thinking", et=0.6)),
    (Wd("L07", "Mind", "start", 0.1), dict(e="surprised", ex=dict(eopen=0.98, braise=0.35, mopen_base=0.0, mround=0.0),
                                          et=0.25)),
    (L("L08", "start", 0.0), dict(gest="shrug", gd=0.7, ga=0.5, e="amused", ex=dict(msmile=0.3), et=0.3)),
    (Wd("L09", "asked"), dict(e="content", ex=dict(msmile=0.42, binner=0.25), et=0.5)),
    (L("L09", "end", 0.3), dict(gest="nod", gd=0.6, ga=0.4)),
    # ---- "Twenty-two years I've carried these."
    (L("L10", "start", -0.4), dict(g="cuffs", gt=0.3, p="cuffs", pt=0.8, e="wistful", ex=dict(eopen=0.8), et=0.5)),
    (Wd("L10", "Tomorrow", "start", -0.1), dict(g="other", gt=0.25, e="skeptical", ex=dict(bfurrow=0.3, msmile=0.05),
                                                et=0.4)),
    (Wd("L10", "Tomorrow", "start", 0.2), dict(p="rest", pt=0.8)),
    (Wd("L10", "Words", "start", -0.1), dict(gest="shrug", gd=0.6, ga=0.6, e="skeptical",
                                             ex=dict(msmile=0.25, masym=0.6), et=0.25)),
    (L("L10", "end", 0.1), dict(gest="laugh", gd=0.45, ga=0.3)),
    (L("L11", "start", 0.0), dict(e="thinking", et=0.5)),
    # "And when someone swings a bottle at somebody's head?"
    (L("L12", "start", -0.2), dict(p="lean_in", pt=0.6, e="determined", ex=dict(bfurrow=0.55, msmile=-0.1), et=0.4,
                                   g="other", gt=0.2)),
    (Wd("L12", "swings", "start", -0.2), dict(p="explain", pt=0.3)),
    (Wd("L12", "head", "end", 0.15), dict(p="lean_in", pt=0.5)),
    # watching Kai draw
    (L("L13", "start", 0.0), dict(p="rest", pt=0.6, g="sketch", gt=0.3, e="skeptical", ex=dict(bfurrow=0.2), et=0.5)),
    (Wd("L13", "If"), dict(e="thinking", et=0.5)),
    (Wd("L13", "stand"), dict(g="other", gt=0.25)),
    (Wd("L13", "yelling"), dict(g="sketch", gt=0.25)),
    (L("L13", "end", 0.2), dict(g="other", gt=0.25, e="thinking", ex=dict(msmile=0.05), et=0.4)),
    # "And when that doesn't work?"
    (L("L15", "start", -0.5), dict(p="rest_low", pt=0.0, g="sketch", gt=0.0, e="worried", ex=dict(eopen=0.86), et=0.0)),
    (L("L15", "start", 0.0), dict(g="other", gt=0.25)),
    (L("L16", "end", 0.3), dict(e="worried", ex=dict(eopen=0.8, binner=0.7), et=0.6, g="down", gt=0.4)),
    # ---- the ones who really hurt people
    (L("L19", "start", -0.4), dict(p="rest", pt=0.0, g="window", gt=0.0, e="worried", ex=dict(eopen=0.85, binner=0.6),
                                   et=0.0)),
    (Wd("L19", "The", "start", -0.1), dict(g="other", gt=0.25)),
    (L("L20", "start", 0.0), dict(gest="nod", gd=0.5, ga=0.4)),
    (Wd("L20", "Me", "start", 0.1), dict(g="window", gt=0.35, e="worried", ex=dict(eopen=0.82), et=0.5)),
    # ---- "So what's my job now?"
    (L("L25", "start", -0.5), dict(p="rest", pt=0.0, g="down", gt=0.0, e="uncomfortable", ex=dict(msmile=0.1), et=0.0)),
    (L("L25", "start", 0.0), dict(g="other", gt=0.25)),
    (L("L25", "start", 0.3), dict(gest="shrug", gd=0.7, ga=0.5)),
    (L("L26", "start", 0.0), dict(e="thinking", et=0.4)),
    (Wd("L26", "shortcut", "end", 0.1), dict(e="skeptical", ex=dict(msmile=0.3), et=0.3)),
    (L("L27", "start", -0.05), dict(g="cuffs", gt=0.25, e="amused", ex=dict(msmile=0.35, masym=0.5), et=0.3)),
    (L("L27", "end", 0.1), dict(gest="laugh", gd=0.5, ga=0.3)),
    (L("L27", "end", 0.6), dict(g="other", gt=0.3)),
    # ---- "And soldiers?"
    (L("L29", "start", -0.5), dict(p="rest", pt=0.0, g="window", gt=0.0, e="worried", ex=dict(bfurrow=0.3), et=0.0)),
    (L("L29", "start", 0.0), dict(g="other", gt=0.25)),
    (Wd("L29", "What", "start", -0.1), dict(p="lean_in", pt=0.5, e="worried", ex=dict(bfurrow=0.45, eopen=1.0), et=0.4)),
    # ---- the turn
    (L("L30", "end", 0.5), dict(p="rest", pt=0.0, g="window", gt=0.0, e="thinking", ex=dict(eopen=0.84), et=0.0)),
    (L("L31", "start", 0.0), dict(g="other", gt=0.2, e="curious", et=0.4)),
    (Wd("L31", "do"), dict(e="uncomfortable", ex=dict(msmile=0.05), et=0.4)),
    (L("L32", "start", -0.3), dict(e="curious", ex=dict(binner=0.45, eopen=0.95, bfurrow=0.15), et=0.3)),
    (L("L32", "start", 0.0), dict(gest="tilt", gd=0.9, ga=0.5)),
    (L("L33", "start", 0.0), dict(e="thinking", ex=dict(eopen=0.95, bfurrow=0.3), et=0.6)),
    # "I was fifteen." -- it starts coming back to her
    (Wd("L33", "I", "start", -0.1), dict(e="worried", ex=dict(eopen=1.0, binner=0.65, bfurrow=0.2, msmile=-0.1), et=0.6,
                                         g="other", gt=0.15, gblink=False)),
    (Wd("L33", "fifteen", "end", 0.1), dict(gest="swallow", gd=0.7, ga=0.8)),
    (Wd("L33", "fifteen", "end", 0.5), dict(g="down", gt=0.35, e="worried", ex=dict(eopen=0.9, binner=0.8), et=0.5)),
    (Wd("L33", "description"), dict(g="other", gt=0.3, e="worried", ex=dict(eopen=1.05), et=0.5)),
    # "I remember."
    (L("L35", "start", -1.0), dict(p="rest", pt=0.0, g="other", gt=0.0, e="worried", ex=dict(eopen=1.1, braise=0.2), et=0.0,
                                   wet=0.3, wt=0.5)),
    (L("L35", "start", -0.6), dict(e="guilty", ex=dict(eopen=0.82, binner=1.0), et=0.5, wet=0.7, wt=0.8)),
    (L("L35", "start", -0.3), dict(g="down", gt=0.45)),
    (L("L35", "end", 0.05), dict(p="hand_mouth", pt=0.6, wet=0.9, wt=0.5)),
    (L("L35", "end", 0.4), dict(tear=1.0, tt=1.4)),
    # "I'm sorry, Kai."
    (L("L38", "start", -0.6), dict(p="sorry", pt=0.0, g="other", gt=0.0, e="sad_deep", ex=dict(eopen=0.8), et=0.0,
                                   wet=0.9, wt=0.1, tear=1.0, tt=0.0)),
    (Wd("L38", "scared", "start", -0.3), dict(g="down", gt=0.4)),
    (Wd("L38", "and"), dict(g="other", gt=0.3, gblink=False)),
    (L("L38", "end", 0.3), dict(gest="sniff", gd=0.6)),
    (L("L40", "start", -0.3), dict(e="honest", ex=dict(binner=0.8, msmile=-0.05, wet=0.85), et=0.3, g="other", gt=0.2)),
    (L("L40", "end", 0.0), dict(gest="nod", gd=0.7, ga=0.45)),
    (L("L42", "start", -0.3), dict(p="lean_in", pt=0.8, e="tender", ex=dict(wet=0.75, msmile=0.15), et=0.5)),
    (L("L42", "end", 0.2), dict(gest="nod", gd=0.6, ga=0.4)),
    # ---- time-lapse to dawn: the long talk
    (At(268.9), dict(p="rest_low", pt=0.0, e="honest", ex=dict(wet=0.4), et=0.0, tear=0.0, tt=0.8, g="other", gt=0.0,
                     talk=0.0, kt=0.0)),
    (At(269.9), dict(gest="nod", gd=0.5, ga=0.5)),
    (At(270.05), dict(p="cuffs", pt=0.2)),
    (At(270.3), dict(p="push_belt", pt=0.7, g="cuffs", gt=0.2)),
    (At(271.1), dict(p="rest", pt=0.3, g="other", gt=0.2)),
    (At(271.3), dict(talk=1.0, p="talk_hand", pt=0.3, e="guilty", ex=dict(msmile=0.0), et=0.3)),
    (At(272.4), dict(talk=0.0, p="rest", pt=0.3)),
    (At(272.7), dict(g="sketch", gt=0.2, e="curious", et=0.3)),
    (At(273.6), dict(g="other", gt=0.2, e="amused", et=0.3)),
    (At(274.0), dict(gest="laugh", gd=0.8, ga=0.8, e="laugh", et=0.15)),
    (At(274.9), dict(e="warm", et=0.3)),
    (At(275.2), dict(talk=1.0, p="talk_hand", pt=0.3, e="honest", ex=dict(msmile=0.2), et=0.3)),
    (At(276.5), dict(talk=0.0, p="chin", pt=0.4)),
    (At(277.3), dict(g="window", gt=0.35, e="hopeful", ex=dict(msmile=0.3), et=0.6, p="rest", pt=0.6)),
    # ---- dawn: "Can I shake your hand?"
    (L("L44", "start", -0.8), dict(g="window", gt=0.0, e="hopeful", ex=dict(msmile=0.3, wet=0.2), et=0.0, p="rest", pt=0.0)),
    (L("L44", "start", -0.35), dict(g="other", gt=0.25)),
    (L("L44", "start", 0.0), dict(e="hopeful", ex=dict(binner=0.55, braise=0.25, msmile=0.25), et=0.4)),
    (Wd("L44", "shake", "start", -0.1), dict(p="offer_hand", pt=0.7)),
    (L("L44", "end", 0.6), dict(gest="swallow", gd=0.6, ga=0.6)),
    (Wd("L45", "bump", "start", 0.1), dict(e="amused", ex=dict(msmile=0.7), et=0.25)),
    (Wd("L45", "bump", "start", 0.2), dict(gest="laugh", gd=0.6, ga=0.5)),
    (L("L46", "start", -0.25), dict(p="fist_ready", pt=0.3)),
    (BUMP, dict(gest="bounce", gd=0.3, ga=0.5)),
    (Wd("L46", "bump", "start", 0.03), dict(p="fist", pt=0.22)),
    (Wd("L46", "bump", "start", 0.35), dict(e="happy", ex=dict(msmile=0.8), et=0.3)),
    # ---- "every touch is a question"
    (L("L47", "start", -0.2), dict(p="fist", pt=0.0, e="happy", ex=dict(msmile=0.7, wet=0.3), et=0.0, g="other", gt=0.0)),
    (L("L47", "start", 0.6), dict(gest="laugh", gd=0.6, ga=0.35)),
    (Wd("L47", "question", "start", -0.2), dict(p="rest", pt=1.1, e="warm", et=0.6)),
    (Wd("L47", "Sometimes"), dict(g="window", gt=0.5, e="hopeful", ex=dict(msmile=0.5), et=0.5)),
    (Wd("L47", "yes", "start", -0.1), dict(g="other", gt=0.3, e="teary_smile", ex=dict(msmile=0.7), et=0.5)),
    (L("L47", "end", 0.5), dict(gest="nod", gd=0.6, ga=0.4)),
]

KAI = [
    # off in the kitchen until the refill
    (At(0.0), dict(x=260.0, xt=0.0, stand=1.0, st=0.0, p="pour_done", pt=0.0, e="content", et=0.0, g="other", gt=0.0)),
    (L("L03", "start", -0.95), dict(x=-110.0, xt=0.95, g="mug_hale", gt=0.0)),
    (L("L03", "start", -0.15), dict(g="other", gt=0.2, e="content", ex=dict(braise=0.2, msmile=0.3), et=0.3)),
    (L("L03", "end", 0.0), dict(gest="tilt", gd=0.6, ga=0.6)),
    (Wd("L04", "Please", "start", 0.1), dict(g="mug_hale", gt=0.2, gblink=False)),
    (Wd("L04", "Please", "end", -0.35), dict(p="pour", pt=0.45)),
    (L("L05", "start", -0.55), dict(p="pour_done", pt=0.45)),
    # "Last night with those?"
    (L("L05", "start", -0.35), dict(g="cuffs", gt=0.25, e="thinking", ex=dict(msmile=0.05, bfurrow=0.15), et=0.3)),
    (Wd("L05", "those"), dict(g="other", gt=0.2, gblink=False, e="curious", ex=dict(bfurrow=0.1, msmile=0.1), et=0.3)),
    (L("L06", "start", 0.2), dict(g="cuffs", gt=0.3, e="thinking", et=0.5)),
    (L("L06", "end", -0.2), dict(gest="nod", gd=0.5, ga=0.4)),
    # car door slam outside (sfx at L06 end + 0.35)
    (L("L06", "end", 0.37), dict(gest="flinch", gd=0.55, ga=1.0, e="alarmed", ex=dict(mopen_base=0.06), et=0.06,
                                 g="street", gt=0.06, gblink=False)),
    (L("L06", "end", 0.9), dict(e="uncomfortable", et=0.4)),
    (L("L06", "end", 1.15), dict(g="other", gt=0.25, e="content", ex=dict(msmile=0.25, binner=0.25), et=0.5)),
    # "It's dead tonight. Mind if I sit?"
    (Wd("L07", "dead"), dict(g="away", gt=0.3)),
    (Wd("L07", "tonight", "end", 0.1), dict(g="other", gt=0.25)),
    (Wd("L07", "Mind", "start", -0.1), dict(e="curious", ex=dict(braise=0.25, msmile=0.2), et=0.3, gest="tilt", gd=0.7,
                                            ga=0.5)),
    (Wd("L08", "diner", "end", 0.1), dict(e="amused", ex=dict(msmile=0.5), et=0.3)),
    # sits down with the pot, sets it on the table
    (Wd("L09", "booth", "start", -0.2), dict(stand=0.0, st=0.75, x=0.0, xt=0.75, p="hold_pot", pt=0.6)),
    (Wd("L09", "So"), dict(p="set_pot", pt=0.45, e="content", ex=dict(msmile=0.45), et=0.4)),
    (POT_DOWN, dict(p="set_pot_rel", pt=0.0)),
    (Wd("L09", "asked", "end", 0.0), dict(p="rest", pt=0.6)),
    # listening to "Twenty-two years..."
    (L("L10", "start", 0.0), dict(g="other", gt=0.2, e="thinking", et=0.5)),
    (Wd("L10", "these"), dict(g="cuffs", gt=0.25)),
    (Wd("L10", "Tomorrow"), dict(g="other", gt=0.25)),
    (Wd("L10", "Words"), dict(e="content", ex=dict(msmile=0.2), et=0.4)),
    # "Words. Witnesses. Your body, if you choose to stand somewhere."
    (L("L11", "start", -0.25), dict(p="explain", pt=0.4, e="determined", ex=dict(msmile=0.15), et=0.3, g="other", gt=0.2)),
    (Wd("L11", "Words"), dict(gest="nod", gd=0.45, ga=0.6)),
    (Wd("L11", "Witnesses", "start", -0.15), dict(p="witness", pt=0.35, g="window", gt=0.2)),
    (Wd("L11", "Witnesses", "end", 0.05), dict(g="other", gt=0.2)),
    (Wd("L11", "Your", "start", -0.1), dict(p="explain", pt=0.4)),
    (Wd("L11", "stand", "start", -0.15), dict(p="plant", pt=0.3, gest="nod", gd=0.4, ga=0.5)),
    (L("L12", "start", 0.2), dict(p="rest", pt=0.6, e="thinking", et=0.4)),
    # sketching the toolkit
    (L("L13", "start", -0.4), dict(p="sketch", pt=0.5, g="sketch", gt=0.25, e="determined", ex=dict(msmile=0.1), et=0.4)),
    (Wd("L13", "hurt"), dict(g="other", gt=0.18, gblink=False)),
    (Wd("L13", "If"), dict(g="sketch", gt=0.2)),
    (Wd("L13", "hand"), dict(g="other", gt=0.15, gblink=False)),
    (Wd("L13", "out", "end", 0.1), dict(g="sketch", gt=0.2)),
    (Wd("L13", "stand", "start", -0.1), dict(g="other", gt=0.2, e="determined", et=0.3)),
    (Wd("L13", "whole"), dict(g="sketch", gt=0.2)),
    (Wd("L13", "stop"), dict(g="other", gt=0.15, gest="nod", gd=0.5, ga=0.6)),
    # "Then sometimes, someone gets hurt."
    (L("L15", "start", -0.5), dict(p="sketch", pt=0.0, g="sketch", gt=0.0, e="content", ex=dict(msmile=0.1), et=0.0)),
    (Wd("L15", "work"), dict(g="other", gt=0.25, e="honest", et=0.6)),
    (Wd("L15", "work", "end", 0.2), dict(p="rest", pt=0.8)),
    (L("L16", "start", -0.3), dict(g="down", gt=0.4, e="honest", ex=dict(binner=0.85, eopen=0.75), et=0.5)),
    (Wd("L16", "someone", "start", -0.15), dict(g="other", gt=0.3, wet=0.35, wt=1.0)),
    (L("L16", "end", 0.2), dict(gest="nod", gd=0.9, ga=0.4)),
    (L("L16", "end", 0.6), dict(gest="swallow", gd=0.6)),
    # "The ones who really hurt people." / "Yeah. Me too."
    (L("L19", "start", -0.4), dict(p="rest", pt=0.0, e="thinking", et=0.0, g="other", gt=0.0, wet=0.0, wt=0.1)),
    (Wd("L19", "hurt", "start", -0.1), dict(g="down", gt=0.35, e="hurt", ex=dict(msmile=-0.3), et=0.5, p="tense", pt=0.7)),
    (Wd("L20", "Me", "start", -0.1), dict(g="other", gt=0.2, gblink=False)),
    (L("L20", "end", 0.15), dict(g="down_l", gt=0.35, wet=0.3, wt=1.0)),
    # the circle
    (L("L23", "start", -0.35), dict(p="sketch", pt=0.5, g="sketch", gt=0.2, e="content", ex=dict(msmile=0.1), et=0.3,
                                    wet=0.0, wt=0.5)),
    (Wd("L23", "circle"), dict(g="other", gt=0.2)),
    (Wd("L23", "Everyone"), dict(g="sketch", gt=0.2)),
    (Wd("L23", "talk"), dict(g="other", gt=0.15)),
    (Wd("L23", "listen", "start", -0.1), dict(e="determined", ex=dict(msmile=0.2), et=0.4, gest="nod", gd=0.5, ga=0.5)),
    # "Same as always. Keep people safe. You just lost the shortcut."
    (L("L25", "start", -0.5), dict(p="rest", pt=0.0, g="other", gt=0.0, e="content", et=0.0)),
    (L("L26", "start", -0.1), dict(e="content", ex=dict(msmile=0.3), et=0.3, gest="tilt", gd=0.6, ga=0.4)),
    (Wd("L26", "Keep"), dict(gest="nod", gd=0.5, ga=0.5)),
    (Wd("L26", "shortcut", "start", -0.2), dict(e="sly", et=0.3)),
    (L("L27", "end", 0.05), dict(gest="laugh", gd=0.6, ga=0.5, e="grin", ex=dict(mopen_base=0.06), et=0.2)),
    (L("L27", "end", 0.8), dict(e="content", et=0.6)),
    # ---- the turn: he has been holding this all night
    (L("L30", "end", 0.5), dict(p="rest", pt=0.0, e="honest", ex=dict(eopen=0.86, msmile=-0.15), et=0.0, g="other", gt=0.0)),
    (L("L31", "start", -0.5), dict(gest="swallow", gd=0.6)),
    (L("L31", "start", 0.0), dict(e="hurt", ex=dict(eopen=0.86, msmile=-0.25), et=0.5)),
    (Wd("L31", "do", "start", -0.1), dict(g="down", gt=0.3)),
    (L("L31", "end", 0.2), dict(g="other", gt=0.25, gblink=False)),
    (L("L33", "start", -0.3), dict(g="other", gt=0.2, e="honest", ex=dict(bfurrow=0.25, msmile=-0.25), et=0.4)),
    (Wd("L33", "I", "start", -0.25), dict(g="down", gt=0.4, wet=0.5, wt=1.5, e="hurt", ex=dict(bfurrow=0.15), et=0.6)),
    (Wd("L33", "You", "start", -0.2), dict(g="other", gt=0.3, e="hurt", ex=dict(bfurrow=0.4, msmile=-0.45, eopen=0.82),
                                          et=0.5, p="tense", pt=0.8)),
    (Wd("L33", "description", "end", 0.2), dict(gest="swallow", gd=0.6)),
    (L("L35", "start", -1.0), dict(g="other", gt=0.0, e="hurt", ex=dict(eopen=0.8), et=0.0, wet=0.7, wt=0.1)),
    # "I still flinch when a car door slams."
    (L("L37", "start", -0.4), dict(p="rest", pt=0.6, g="other", gt=0.2, e="hurt", ex=dict(msmile=0.05, masym=0.35), et=0.3,
                                   wet=0.5, wt=0.4)),
    (Wd("L37", "car", "start", -0.1), dict(g="window", gt=0.25)),
    (Wd("L37", "slams", "end", 0.15), dict(g="other", gt=0.25, e="hurt", ex=dict(msmile=0.15, masym=0.5), et=0.4)),
    # "I don't know if I forgive you."
    (L("L39", "start", -0.5), dict(g="other", gt=0.0, e="hurt", ex=dict(binner=0.9, eopen=0.8, msmile=-0.35), et=0.0,
                                   wet=0.85, wt=0.6)),
    (Wd("L39", "forgive"), dict(tear=1.0, tt=1.6)),
    (L("L39", "end", 0.25), dict(g="down_l", gt=0.35)),
    (L("L39", "end", 0.8), dict(gest="sniff", gd=0.6)),
    (L("L40", "start", 0.0), dict(g="other", gt=0.3)),
    # "Then what happens now?"
    (L("L41", "start", -0.35), dict(g="other", gt=0.25, e="hopeful", ex=dict(binner=0.75, msmile=-0.05, wet=0.7), et=0.4)),
    (L("L41", "end", 0.1), dict(gest="tilt", gd=0.6, ga=0.4)),
    (L("L42", "start", 0.2), dict(e="hopeful", ex=dict(binner=0.6, msmile=0.15, wet=0.7), et=0.8)),
    # ---- time-lapse to dawn: the long talk
    (At(268.9), dict(p="rest", pt=0.0, e="honest", ex=dict(wet=0.4), et=0.0, tear=0.0, tt=0.8, g="other", gt=0.0,
                     talk=0.0, kt=0.0)),
    (At(269.4), dict(talk=1.0, p="talk_hand", pt=0.35)),
    (At(270.4), dict(p="explain", pt=0.3)),
    (At(271.2), dict(talk=0.0, p="rest", pt=0.3, e="thinking", et=0.3)),
    (At(271.6), dict(gest="nod", gd=0.4)),
    (At(272.5), dict(talk=1.0, p="sketch", pt=0.3, g="sketch", gt=0.2)),
    (At(273.6), dict(g="other", gt=0.2, e="amused", et=0.3)),
    (At(274.0), dict(talk=0.0, gest="laugh", gd=0.8, ga=0.8, e="laugh", et=0.15)),
    (At(274.9), dict(e="content", ex=dict(msmile=0.5), et=0.3)),
    (At(275.2), dict(p="rest", pt=0.3)),
    (At(276.2), dict(gest="nod", gd=0.5)),
    (At(276.6), dict(talk=1.0, p="talk_hand", pt=0.3)),
    (At(277.3), dict(talk=0.0, g="window", gt=0.35, e="awe", ex=dict(msmile=0.2), et=0.6, p="rest", pt=0.5)),
    # ---- dawn: the handshake question
    (L("L44", "start", -0.8), dict(g="window", gt=0.0, e="content", ex=dict(msmile=0.3), et=0.0, p="rest", pt=0.0)),
    (L("L44", "start", -0.2), dict(g="other", gt=0.25)),
    (Wd("L44", "hand", "start", 0.1), dict(g="fists", gt=0.2, e="thinking", ex=dict(binner=0.45, msmile=-0.05), et=0.5)),
    (L("L44", "end", 0.7), dict(gest="swallow", gd=0.6)),
    (L("L45", "start", -0.85), dict(g="other", gt=0.25, gblink=False)),
    (L("L45", "start", -0.6), dict(e="content", ex=dict(msmile=0.4, masym=0.3), et=0.4)),
    (L("L45", "start", -0.5), dict(p="fist_wait", pt=0.5)),
    (L("L45", "start", 0.0), dict(e="sly", ex=dict(msmile=0.55), et=0.3)),
    (Wd("L46", "bump", "start", 0.03), dict(p="fist", pt=0.22)),
    (BUMP, dict(gest="bounce", gd=0.3, ga=0.5)),
    (Wd("L46", "bump", "start", 0.35), dict(e="happy", ex=dict(msmile=0.85), et=0.3)),
    # ---- "every touch is a question. Sometimes, the answer is yes."
    (L("L47", "start", -0.2), dict(p="fist", pt=0.0, e="happy", ex=dict(msmile=0.8, wet=0.35), et=0.0, g="other", gt=0.0)),
    (L("L47", "start", 0.6), dict(gest="laugh", gd=0.6, ga=0.35)),
    (Wd("L47", "question", "start", -0.1), dict(p="rest", pt=1.1)),
    (Wd("L47", "Sometimes", "start", -0.1), dict(g="sketch", gt=0.35, e="content", ex=dict(msmile=0.4), et=0.5)),
    (Wd("L47", "Sometimes", "start", 0.6), dict(p="sketch", pt=0.6)),
    (Wd("L47", "yes", "start", -0.1), dict(g="other", gt=0.25, e="warm", ex=dict(msmile=0.8), et=0.5)),
    (L("L47", "end", 0.4), dict(g="sketch", gt=0.3)),
]

KEYS = {"hale": HALE, "kai": KAI}
