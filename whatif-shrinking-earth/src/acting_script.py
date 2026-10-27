"""Performance notes for Pip and Tess, keyed to the voice timeline.

Keys: (anchor, {...}) with
  e  expression preset (et = blend seconds, ex = extra face params)
  g  gaze target (other, moon, mug, mug_roof_pip, hands, other_hands, sky, sky_hi,
     icon1..icon4, down, down_l, away, window, cam)   gt = eye transition
  p  pose preset (pt = blend seconds)
  x  horizontal scoot in world px (xt)      stand  0..1 (st)
  wet / tear  eye wetness / tear track      gest  nod, nod2, shake, tilt, shrug, laugh,
  sigh, sniff, flinch, swallow, bounce (gd = duration, ga = amplitude)
"""
from anchors import L, Wd, At

S = {
    "S03": L("L03", "start", -0.6), "S07": L("L06", "start", -0.1), "S08": L("L07", "start", -0.2),
    "S12": L("L11", "start", -0.5), "S18": Wd("L16", "atmosphere", "start", -0.3),
}

PIP = [
    # opening: alone on the roof, hugging her knees, staring at the Moon
    (At(0.0), dict(e="wistful", g="moon", p="hug", pt=0.0)),
    (At(1.15), dict(gest="sniff", gd=0.7, ga=0.6)),
    (At(2.55), dict(g="window", gt=0.09, gblink=False)),
    (At(2.95), dict(g="moon", gt=0.25, e="hurt", et=0.6)),
    # she already holds her mug when we come back; won't look at Tess
    (S["S03"], dict(p="mug_low", pt=0.0, g="mug", gt=0.0, e="hurt", et=0.0)),
    (Wd("L03", "seven", "start", -0.1), dict(e="hurt", ex=dict(msmile=-0.5, eopen=0.6), et=0.5, gest="swallow", gd=0.7)),
    (Wd("L03", "seven", "end", 0.25), dict(blink=True)),
    (L("L04", "start", -0.45), dict(g="moon", gt=0.0, e="wistful", et=0.0, p="mug", pt=0.0)),
    (L("L04", "start", 0.0), dict(ex=dict(braise=0.25), e="wistful", et=0.3)),
    (Wd("L04", "What"), dict(e="curious", ex=dict(binner=0.3), et=0.4)),
    # listing everything that shrinks: eyes follow each chalk icon
    (S["S07"], dict(e="curious", g="sky", gt=0.0, p="mug", pt=0.0)),
    (Wd("L06", "ground"), dict(g="icon1", gt=0.12)),
    (Wd("L06", "oceans"), dict(g="icon2", gt=0.12)),
    (Wd("L06", "air"), dict(g="icon3", gt=0.12)),
    (Wd("L06", "Moon"), dict(g="icon4", gt=0.12, e="awe", et=0.5)),
    (Wd("L06", "Smaller"), dict(g="sky", gt=0.3, gest="tilt", gd=1.2, ga=0.6)),
    (Wd("L06", "But"), dict(g="other", gt=0.2, e="hopeful", et=0.4)),
    # Tess's squeeze gesture; "Why?" makes her look away
    (S["S08"], dict(g="other_hands", gt=0.0, e="curious", et=0.0)),
    (Wd("L07", "Why"), dict(g="mug", gt=0.18, e="hurt", et=0.4)),
    (Wd("L07", "Why", "end", 0.2), dict(gest="shrug", gd=0.8, ga=0.7)),
    # the vulnerable line
    (L("L08", "start", -0.5), dict(e="sad", et=0.3, g="mug", gt=0.0, wet=0.45, wt=1.2)),
    (Wd("L08", "far"), dict(g="other", gt=0.18, gblink=False)),
    (L("L08", "end", 0.3), dict(e="sad", ex=dict(msmile=-0.55), et=0.5)),
    (L("L09", "start", -0.2), dict(e="hopeful", et=0.8)),
    # back from space: mug is set down on the roof
    (S["S12"], dict(p="hands_lap", pt=0.0, e="curious", et=0.0, g="other", gt=0.0, wet=0.15, wt=0.1)),
    (L("L12", "start", -0.15), dict(gest="tilt", gd=0.8, ga=0.8, e="curious", ex=dict(bfurrow=0.25))),
    (L("L13", "start", 0.2), dict(e="content", et=0.4)),
    (Wd("L13", "ruler", "start", 0.15), dict(g="icon1", gt=0.12, e="awe", et=0.4)),
    (Wd("L13", "house", "start", 0.15), dict(g="icon2", gt=0.12)),
    (Wd("L13", "eyes", "start", 0.15), dict(g="icon3", gt=0.12)),
    (Wd("L13", "together"), dict(g="sky", gt=0.25)),
    # "So... you wouldn't be any closer."
    (L("L14", "start", -0.35), dict(e="wistful", et=0.0, g="moon", gt=0.0)),
    (L("L14", "start", 0.0), dict(e="sad", et=0.8, g="down", gt=0.35)),
    (Wd("L14", "closer", "start", -0.1), dict(g="other", gt=0.15, gblink=False, wet=0.55, wt=1.0)),
    (Wd("L14", "closer", "end", 0.25), dict(g="down_l", gt=0.3)),
    (L("L15", "start", 0.0), dict(e="hurt", et=0.6)),
    # heavier: ears pop
    (S["S18"], dict(p="heavy", pt=0.0, e="uncomfortable", et=0.0, g="sky", gt=0.0, wet=0.0, wt=0.1)),
    (Wd("L16", "ears", "start", -0.3), dict(p="pinch_nose", pt=0.3, e="strain", et=0.25, g="down", gt=0.2)),
    (Wd("L16", "pop"), dict(e="surprised", et=0.08, gest="flinch", gd=0.45, g="other", gt=0.1)),
    (Wd("L16", "like"), dict(p="hands_lap", pt=0.6, e="content", et=0.5)),
    # Dad and the scale
    (L("L18", "start", -0.3), dict(p="hands_lap", pt=0.0, e="grin", et=0.0, g="other", gt=0.0, gest="laugh", gd=0.6, ga=0.5)),
    (L("L19", "end", -0.05), dict(e="laugh", et=0.2, gest="laugh", gd=1.1)),
    # days get shorter
    (L("L20", "start", -0.6), dict(e="content", et=0.0, g="other", gt=0.0)),
    (Wd("L20", "days"), dict(g="sky", gt=0.25, e="curious", et=0.4)),
    (L("L21", "start", -0.1), dict(g="other", gt=0.15, gest="tilt", gd=0.7)),
    (Wd("L22", "Arms"), dict(e="worried", et=0.5, g="other", gt=0.2)),
    (Wd("L22", "pull"), dict(e="alarmed", et=0.2)),
    (L("L23", "start", -0.1), dict(p="reach", pt=0.25, e="alarmed", et=0.1)),
    (L("L24", "start", 0.2), dict(p="hands_lap", pt=0.8, e="relieved", et=0.4)),
    (Wd("L24", "smaller"), dict(g="sky", gt=0.25, e="curious", et=0.4)),
    (Wd("L24", "six"), dict(e="awe", et=0.4)),
    # "So we'd get less time."
    (L("L25", "start", -0.4), dict(e="sad", et=0.0, g="mug_roof_pip", gt=0.0)),
    (L("L25", "end", 0.3), dict(blink=True, e="sad", ex=dict(msmile=-0.55), et=0.4)),
    # people
    (L("L29", "start", -0.5), dict(e="worried", et=0.0, g="other", gt=0.0, p="hands_lap", pt=0.0)),
    (L("L30", "end", 0.2), dict(e="sad", et=0.6, g="down", gt=0.3)),
    (L("L31", "start", -0.8), dict(x=-28.0, xt=1.2, e="wistful", et=0.8)),
    (Wd("L31", "watch", "start", 0.3), dict(g="sky_hi", gt=0.3, e="hopeful", et=0.6)),
    # elephants
    (L("L34", "start", -0.2), dict(x=0.0, xt=0.0, p="hands_lap", pt=0.0, g="other", gt=0.0, e="excited", et=0.0,
                                   gest="laugh", gd=0.7, ga=0.5)),
    (L("L35", "end", 0.0), dict(e="laugh", et=0.2, gest="laugh", gd=0.9)),
    # pizza dough
    (L("L38", "start", -0.15), dict(p="spin_hand", pt=0.25, e="excited", et=0.1, g="other", gt=0.0)),
    (L("L39", "start", 0.2), dict(e="laugh", et=0.2, gest="laugh", gd=1.0)),
    (L("L39", "end", 0.3), dict(p="hands_lap", pt=0.7, e="grin", et=0.5)),
    # cocoa gets cold
    (Wd("L41", "cocoa", "start", -0.6), dict(p="hands_lap", pt=0.0, g="mug_roof_pip", gt=0.0, e="awe", et=0.0)),
    (L("L41", "end", -0.1), dict(g="other", gt=0.2, e="surprised", ex=dict(mopen_base=0.12), et=0.3)),
    # "And the Moon?"
    (L("L46", "start", -0.9), dict(g="moon", gt=0.0, e="worried", ex=dict(eopen=1.08, moonref=1.0), et=0.0,
                                   wet=0.5, wt=0.1)),
    # birthdays
    (L("L50", "start", -0.6), dict(e="sad_deep", ex=dict(moonref=0.0), et=0.0, g="moon", gt=0.0, wet=0.9, wt=0.1)),
    (Wd("L50", "counting"), dict(tear=1.0, tt=1.8)),
    (L("L50", "end", 0.2), dict(g="down", gt=0.35)),
    (L("L51", "start", -0.5), dict(e="teary_smile", ex=dict(binner=0.9, msmile=0.25), et=0.0, g="down_l", gt=0.0,
                                   tear=1.0, tt=0.0)),
    (Wd("L51", "saddest"), dict(gest="laugh", gd=0.6, ga=0.4)),
    (L("L51", "end", -0.4), dict(p="wipe_eye", pt=0.35, gest="sniff", gd=0.6, gdel=0.3)),
    (L("L51", "end", 0.45), dict(p="hands_lap", pt=0.5, tear=0.0, tt=0.6)),
    # nudge, "Why not?"
    (L("L52", "start", -0.2), dict(gest="bounce", gd=0.4, ga=0.6, g="other", gt=0.15, e="hopeful", et=0.4,
                                   wet=0.5, wt=0.4)),
    (L("L53", "start", -0.3), dict(gest="sniff", gd=0.5, e="curious", ex=dict(binner=0.4), et=0.3)),
    (Wd("L54", "light"), dict(g="icon1", gt=0.2, e="curious", et=0.4)),
    (Wd("L54", "Sun"), dict(g="icon2", gt=0.2)),
    (Wd("L54", "giant"), dict(g="icon4", gt=0.25, e="awe", et=0.4)),
    (Wd("L54", "Everything"), dict(g="other", gt=0.2, e="hopeful", et=0.5, wet=0.1, wt=1.0)),
    # pushing back
    (L("L56", "start", -0.5), dict(p="look_hands", pt=0.5, g="hands", gt=0.2, e="thinking", et=0.4)),
    (Wd("L56", "harder", "start", 0.0, 1), dict(g="other", gt=0.18, e="hopeful", ex=dict(msmile=0.3), et=0.5)),
    (L("L57", "start", 0.6), dict(p="hands_lap", pt=0.6, e="content", et=0.5)),
    (Wd("L57", "Stubborn"), dict(g="sky", gt=0.25)),
    (L("L58", "start", -0.45), dict(g="other", gt=0.2, e="sly", et=0.35)),
    (L("L59", "end", 0.1), dict(e="happy", et=0.5)),
    # still far
    (L("L60", "start", -1.0), dict(g="moon", gt=0.5, e="wistful", et=0.8)),
    (L("L61", "start", 0.3), dict(g="other", gt=0.25)),
    (L("L62", "start", -0.4), dict(g="other", gt=0.0, e="wistful", et=0.0)),
    (Wd("L62", "look", "start", 0.3), dict(g="moon", gt=0.3, e="hopeful", et=0.5)),
    (Wd("L62", "same", "start", -0.8), dict(e="teary_smile", et=0.6, x=-62.0, xt=1.6, p="lean_on", pt=1.5,
                                            gblink=False)),
    (L("L62", "end", 0.7), dict(e="peaceful", et=1.2)),
]

TESS = [
    # at the window with two mugs
    (At(0.0), dict(e="tender", ex=dict(binner=0.35), g="other", p="window", pt=0.0)),
    (L("L01", "start", 0.0), dict(e="tender", ex=dict(braise=0.3), et=0.3)),
    (L("L01", "end", 0.0), dict(gest="tilt", gd=0.8, ga=0.7)),
    # sits down beside Pip
    (S["S03"], dict(p="mug", pt=0.0, stand=0.3, st=0.0, e="guilty", et=0.0, g="other", gt=0.0)),
    (L("L03", "start", -0.55), dict(stand=0.0, st=0.7)),
    (Wd("L03", "Yeah"), dict(gest="nod", gd=0.5, ga=0.7)),
    (Wd("L03", "Yeah", "end", 0.3), dict(g="mug", gt=0.25, e="honest", et=0.5)),
    (Wd("L03", "seven", "end", 0.2), dict(g="other", gt=0.2)),
    # "Shrank?"
    (L("L05", "start", -0.15), dict(e="skeptical", et=0.0, g="other", gt=0.0, gest="tilt", gd=0.9, ga=0.9)),
    (S["S07"], dict(e="content", et=0.0, g="other", gt=0.0)),
    (Wd("L06", "Moon"), dict(e="curious", et=0.5, p="hands_lap", pt=0.9)),
    # Same mass. Less space. Why?
    (S["S08"], dict(p="squeeze", pt=0.0, g="hands", gt=0.0, e="thinking", et=0.0)),
    (Wd("L07", "Less", "start", -0.15), dict(p="squeeze_close", pt=0.35)),
    (Wd("L07", "Why", "start", -0.25), dict(g="other", gt=0.18, e="curious", ex=dict(binner=0.35), et=0.3,
                                             p="hands_lap", pt=0.8)),
    (Wd("L07", "Why"), dict(gest="tilt", gd=0.9)),
    # she melts at "so far away"
    (L("L09", "start", -0.7), dict(e="tender", ex=dict(binner=0.6), et=0.9, wet=0.3, wt=1.0, g="other", gt=0.0)),
    (L("L09", "start", -0.35), dict(blink=True)),
    (Wd("L09", "Okay"), dict(gest="nod", gd=0.55)),
    (Wd("L09", "Okay", "end", 0.1), dict(gest="sigh", gd=0.9, ga=0.8)),
    (Wd("L09", "Let's"), dict(e="determined", ex=dict(msmile=0.55, braise=0.25), et=0.4)),
    (Wd("L09", "squeeze", "start", -0.3), dict(p="cup_sky", pt=0.5, g="sky_hi", gt=0.3)),
    # you wouldn't see it
    (S["S12"], dict(p="explain", pt=0.0, e="curious", ex=dict(msmile=0.4), et=0.0, g="other", gt=0.0, wet=0.0, wt=0.1)),
    (Wd("L11", "weird"), dict(ex=dict(braise=0.5), e="curious", et=0.2)),
    (Wd("L11", "wouldn't"), dict(gest="shake", gd=0.7, ga=0.5)),
    (L("L13", "start", 0.0), dict(e="grin", et=0.3, gest="nod", gd=0.5)),
    (Wd("L13", "ruler"), dict(p="point", pt=0.4, g="icon1", gt=0.15)),
    (Wd("L13", "house"), dict(g="icon2", gt=0.12)),
    (Wd("L13", "eyes"), dict(g="icon3", gt=0.12)),
    (Wd("L13", "together"), dict(g="sky", gt=0.2, p="explain", pt=0.6)),
    # "Not to you. No."
    (L("L15", "start", -0.3), dict(p="hands_lap", pt=0.0, e="guilty", et=0.0, g="other", gt=0.0)),
    (Wd("L15", "you", "end", 0.25), dict(g="down", gt=0.3, blink=True)),
    (Wd("L15", "No", "start", -0.2), dict(g="other", gt=0.25, e="sad", ex=dict(msmile=0.1), et=0.5, wet=0.35, wt=0.8)),
    (Wd("L15", "No"), dict(gest="shake", gd=1.0, ga=0.55)),
    # ears pop: amused big sister
    (S["S18"], dict(e="amused", et=0.0, g="other", gt=0.0, wet=0.0, wt=0.1)),
    # Dad
    (L("L18", "start", -0.3), dict(e="grin", et=0.0, g="other", gt=0.0)),
    (Wd("L19", "already"), dict(g="sky_hi", gt=0.15, gblink=False)),
    (Wd("L19", "scale"), dict(g="other", gt=0.2)),
    (L("L19", "end", -0.05), dict(e="laugh", et=0.2, gest="laugh", gd=1.1)),
    # figure skater
    (L("L20", "start", -0.4), dict(e="curious", et=0.3, p="explain", pt=0.5, g="sky", gt=0.2)),
    (L("L21", "end", 0.1), dict(g="other", gt=0.15, e="grin", et=0.3)),
    (L("L22", "start", -0.25), dict(stand=1.0, st=0.6, p="stand_out", pt=0.6, e="grin", et=0.3)),
    (Wd("L22", "pull", "start", -0.1), dict(p="stand_in", pt=0.25, e="excited", et=0.2)),
    (L("L24", "start", -0.3), dict(stand=0.0, st=0.9, p="hands_up", pt=0.35, e="sheepish", et=0.2, g="other", gt=0.1)),
    (Wd("L24", "But"), dict(p="explain", pt=0.6, e="curious", ex=dict(msmile=0.35), et=0.4)),
    (Wd("L24", "spins"), dict(g="sky", gt=0.25)),
    (Wd("L24", "six"), dict(g="other", gt=0.2)),
    # "Yeah. Less time."
    (L("L26", "start", -0.5), dict(p="hands_lap", pt=0.0, e="honest", et=0.0, g="other", gt=0.0)),
    (Wd("L26", "Yeah", "end", 0.2), dict(g="moon", gt=0.45, e="sad", ex=dict(msmile=0.05), et=0.6, wet=0.5, wt=1.0)),
    (L("L26", "end", 0.15), dict(gest="swallow", gd=0.7)),
    # people wouldn't make it
    (L("L30", "start", -0.5), dict(e="honest", et=0.0, g="other", gt=0.0, wet=0.3, wt=0.1)),
    (Wd("L30", "Pip"), dict(gest="nod", gd=0.6, ga=0.6)),
    (L("L30", "end", 0.25), dict(blink=True)),
    (L("L31", "start", -0.8), dict(x=32.0, xt=1.1, p="arm_around", pt=0.9, e="tender", et=0.6)),
    (Wd("L31", "watch"), dict(g="sky_hi", gt=0.3, e="determined", ex=dict(msmile=0.5), et=0.5)),
    # elephants
    (L("L34", "start", -0.2), dict(x=0.0, xt=0.0, p="hands_lap", pt=0.0, e="grin", et=0.0, g="other", gt=0.0, wet=0.0, wt=0.1)),
    (L("L35", "start", 0.0), dict(gest="nod", gd=0.5)),
    (L("L35", "end", 0.0), dict(e="laugh", et=0.2, gest="laugh", gd=0.9)),
    # pizza dough
    (L("L38", "start", -0.15), dict(e="grin", et=0.0, g="other", gt=0.0)),
    (L("L39", "start", 0.0), dict(e="laugh", et=0.2, gest="laugh", gd=1.0)),
    # blue marble
    (L("L45", "start", -1.6), dict(e="wistful", et=0.0, g="sky", gt=0.0, p="hands_lap", pt=0.0)),
    (Wd("L45", "finally"), dict(e="wistful", ex=dict(msmile=0.3), et=0.5)),
    (Wd("L45", "wouldn't"), dict(e="sad", et=0.6, g="down", gt=0.4, wet=0.6, wt=1.2)),
    # nudge
    (L("L52", "start", -0.5), dict(e="warm", et=0.0, g="other", gt=0.0, x=14.0, xt=0.3, p="nudge", pt=0.25, wet=0.0, wt=0.1)),
    (L("L52", "start", 0.25), dict(x=0.0, xt=0.6, p="hands_lap", pt=0.6)),
    (Wd("L52", "can't"), dict(gest="nod2", gd=0.8)),
    (L("L54", "start", -0.25), dict(p="explain", pt=0.5, g="sky", gt=0.2, e="curious", ex=dict(msmile=0.4), et=0.4)),
    (Wd("L54", "giant"), dict(g="sky_hi", gt=0.2, e="awe", ex=dict(msmile=0.2), et=0.4)),
    (Wd("L54", "Everything"), dict(g="other", gt=0.2, e="warm", et=0.4)),
    (Wd("L54", "pushes", "start", -0.3), dict(p="push", pt=0.35)),
    # stubborn
    (L("L56", "start", -0.5), dict(p="hands_lap", pt=0.4, e="tender", et=0.5, g="other", gt=0.2)),
    (L("L57", "start", 0.0), dict(gest="nod", gd=0.55, e="warm", et=0.3)),
    (Wd("L57", "Stubborn"), dict(g="sky", gt=0.25, e="amused", et=0.4)),
    (L("L58", "start", -0.3), dict(g="other", gt=0.2, e="content", et=0.3)),
    (L("L58", "end", 0.05), dict(e="surprised", ex=dict(mopen_base=0.0), et=0.15)),
    (L("L59", "start", -0.15), dict(e="tender", ex=dict(msmile=0.6), et=0.3)),
    (L("L59", "end", -0.2), dict(gest="nod", gd=0.6, ga=0.6)),
    # still far
    (L("L60", "start", -1.2), dict(g="other", gt=0.0, e="tender", et=0.0)),
    (L("L61", "start", -0.4), dict(g="other", gt=0.0, e="honest", et=0.0)),
    (Wd("L61", "Yeah"), dict(gest="nod", gd=0.55)),
    (Wd("L61", "is"), dict(e="tender", ex=dict(msmile=0.3), et=0.4)),
    (Wd("L61", "But", "start", -0.2), dict(g="moon", gt=0.4)),
    # look up
    (L("L62", "start", -0.4), dict(g="other", gt=0.0, e="tender", ex=dict(wet=0.4), et=0.0)),
    (Wd("L62", "look"), dict(g="moon", gt=0.3)),
    (Wd("L62", "I'll"), dict(g="other", gt=0.3, e="teary_smile", et=0.5)),
    (L("L62", "end", 1.0), dict(e="tender", ex=dict(roll=0.16, eopen=0.55, msmile=0.55), et=1.4)),
    (L("L63", "start", 0.6), dict(g="moon", gt=0.9)),
    (Wd("L63", "so"), dict(e="warm", ex=dict(roll=0.16, eopen=0.7), et=1.0)),
]

KEYS = {"pip": PIP, "tess": TESS}
