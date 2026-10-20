"""Shot list. Each shot runs from its 'start' anchor to the next shot's start (last one to the end).

Time anchors: seconds (float), "L004" (line start), "L004.e" (line end), "L004:word" (word start),
"L004:word.e" (word end), any of those with "+0.3" / "-0.2". Inside 'act', plain numbers are seconds
from the shot start.

Actions: (CHAR, kind, t, ...)
  emo   name [intensity] [ramp]      look  target (CHAR | "cam" | "down" | "up" | "heaven" | "left" | "right" |
  blink                              "far" | "hand_R" | object name | (x,y,z) | "@MARK_X")
  nod/shake/down/up amount dur       gest  SIDE NAME [ramp]   (see gestures.py)
  lean  degrees [ramp]               move  t_end (dx,dy,dz) ["walk"]     tremble t_end amount
  noblink t_end                      prop  OBJECT SIDE                   drop OBJECT
"""
import re

EYE_H = 1.64


def cam(char, size="CU", az=0.0, el=0.0, lens=85.0, fstop=2.8, end=None, focus=None, handheld=0.25, **kw):
    start = dict(frame=dict(char=char, size=size, az=az, el=el, lens=lens, **{k: v for k, v in kw.items()
                                                                               if k in ("zoff", "side", "dist", "look_off")}))
    c = dict(start=start, lens=lens, fstop=fstop, focus=focus or char, handheld=handheld)
    if end:
        e = dict(start["frame"])
        e.update(end)
        c["end"] = dict(frame=e)
    for k in ("lens_end", "roll", "ease"):
        if k in kw:
            c[k] = kw[k]
    return c


def pcam(pos, target, lens=50.0, fstop=4.0, end=None, focus=None, handheld=0.2, **kw):
    c = dict(start=dict(pos=pos, target=target), lens=lens, fstop=fstop, focus=focus, handheld=handheld)
    if end:
        c["end"] = dict(pos=end[0], target=end[1])
    c.update(kw)
    return c


# ---------------------------------------------------------------------------------------- cast presets
COL = dict(
    JESUS=dict(mark="MARK_JESUS", emo="calm"),
    ELDER=dict(mark="MARK_ELDER", rotz=195, emo="hard", addr="JESUS"),
    YOUNG=dict(mark="MARK_YOUNG", rotz=162, emo="attentive", look="JESUS"),
    PH2=dict(mark="MARK_PH2", rotz=215, emo="contempt", look="JESUS"),
    PH3=dict(mark="MARK_PH3", rotz=135, emo="hard", look="JESUS"),
    JOHN=dict(mark="MARK_JOHN", rotz=25, emo="worried", look="JESUS"),
    PETER=dict(mark="MARK_PETER", rotz=43, emo="tense", look="ELDER"),
)


def C(*names, **over):
    out = {}
    for n in names:
        d = dict(COL[n])
        d.update(over.get(n, {}))
        out[n] = d
    return out


UPR = dict(
    JESUS=dict(mark="MARK_JESUS", pose="sit_floor", emo="prayer", hands={"L": "table", "R": "table"}),
    JOHN=dict(mark="MARK_JOHN", off=(0.33, -0.02, 0), rotz=18, pose="sit_floor", emo="attentive", look="JESUS",
              hands={"L": "table", "R": "table"}),
    PETER=dict(mark="MARK_PETER", off=(-0.33, -0.02, 0), rotz=-18, pose="sit_floor", emo="heavy", look="JESUS",
               hands={"L": "table", "R": "table"}),
)


def U(*names, **over):
    out = {}
    for n in names:
        d = dict(UPR[n])
        d.update(over.get(n, {}))
        out[n] = d
    return out


WOM = dict(mark="MARK_WOMAN", pose="sit_couch", emo="sorrowful", hands={"L": "phone_face", "R": "phone_face"})
SIS = dict(mark="MARK_SISTER", emo="guarded", hands={"L": "rest", "R": "phone_ear"})

COLONNADE_LIGHT = dict(key=6.0, fill=1.6, rim=7.0, key_color=(1.0, 0.9, 0.78), fill_color=(0.72, 0.8, 1.0))
UPPER_LIGHT = dict(key=6.0, fill=0.9, rim=4.0, key_color=(1.0, 0.74, 0.48), fill_color=(0.45, 0.55, 1.0),
                   rim_color=(0.5, 0.6, 1.0))
APT_LIGHT = dict(key=5.0, fill=1.2, rim=5.0, key_color=(1.0, 0.75, 0.5), fill_color=(0.6, 0.72, 1.0),
                 rim_color=(0.55, 0.65, 1.0))

SHOTS = [
    # ================================================================== SCENE 1: SOLOMON'S COLONNADE
    dict(id="S01", set="colonnade", start=0.0,
         cast=C("JESUS"),
         cam=cam("JESUS", "CU", az=22, lens=85, fstop=2.2, end=dict(size="ECU", lens=85), dist=1.75),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "look", 0.0, "@MARK_PH2"), ("JESUS", "emo", 0.0, "calm"),
              ("JESUS", "look", 2.2, "ELDER"), ("JESUS", "emo", 2.4, "sorrowful", 0.5, 1.0),
              ("JESUS", "blink", 2.25)]),
    dict(id="S02", set="colonnade", start="L002-0.15",
         cast=C("JESUS", "ELDER", "YOUNG", "PH2", "PH3"),
         cam=pcam((3.9, -0.8, 1.35), (0.0, -0.75, 1.55), lens=28, fstop=5.6, end=((3.6, -0.75, 1.35), (0.0, -0.7, 1.6))),
         light=dict(COLONNADE_LIGHT, per_char=False),
         act=[("ELDER", "move", 0.0, 2.2, (0.0, 0.9, 0.0), "walk"), ("PH2", "move", 0.0, 2.4, (0.3, 0.8, 0), "walk"),
              ("PH3", "move", 0.2, 2.5, (-0.3, 0.8, 0), "walk"), ("YOUNG", "move", 0.4, 2.8, (0.0, 0.8, 0), "walk"),
              ("JESUS", "look", 0.0, "ELDER")]),
    dict(id="S03", set="colonnade", start="L003-0.2",
         cast=C("ELDER", "YOUNG", "PH2"),
         cam=cam("ELDER", "CU", az=-10, lens=85, fstop=2.0, end=dict(dist=1.45), dist=1.6),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "look", 0.0, "PH2"), ("ELDER", "emo", 0.0, "scoff"), ("ELDER", "look", 0.7, "JESUS"),
              ("ELDER", "lean", 0.8, 7, 0.6), ("ELDER", "emo", 0.9, "impatient"),
              ("YOUNG", "look", 0.0, "ELDER")]),
    dict(id="S04", set="colonnade", start="L004-0.3",
         cast=C("JESUS"),
         cam=cam("JESUS", "CU", az=-14, lens=85, fstop=2.0, dist=1.7, end=dict(dist=1.55)),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "blink", 0.15), ("JESUS", "emo", 0.0, "sorrowful", 0.7), ("JESUS", "look", 0.0, "ELDER"),
              ("JESUS", "down", "L004:but", 0.35, 0.8)]),
    dict(id="S05", set="hillside", start="L005-0.15",
         cast=dict(PH3=dict(mark="MARK_SHEPHERD", rotz=180, emo="eyes_closed_peace", look="cam")),
         cam=cam("PH3", "ECU", az=0, lens=100, fstop=2.2, dist=1.0, end=dict(dist=0.92)),
         light=dict(key=4.0, fill=1.0, rim=6.0, key_color=(1.0, 0.85, 0.65)),
         post="import blindman; blindman.apply(rigs, n)",
         act=[("PH3", "emo", 0.0, "eyes_closed_cry", 0.9), ("PH3", "noblink", 0.0, 1.0),
              ("PH3", "emo", 1.0, "awe", 1.0, 0.5), ("PH3", "look", 1.0, "up")]),
    dict(id="S06", set="colonnade", start="L006-0.1",
         cast=C("JESUS"),
         cam=cam("JESUS", "CU", az=-14, lens=85, fstop=2.0, dist=1.6),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "emo", 0.0, "sad_firm"), ("JESUS", "down", "L006:not", 0.25, 0.6),
              ("JESUS", "blink", "L006:not")]),
    dict(id="S06b", set="colonnade", start="L006:because",
         cast=C("ELDER", "YOUNG", "PH2"),
         cam=cam("ELDER", "MCU", az=6, lens=50, fstop=2.8, dist=2.3, look_off=(0.25, 0, 0)),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "emo", 0.0, "hard"), ("ELDER", "emo", "L006:sheep", "cold_fury", 0.7, 0.3),
              ("PH2", "emo", "L006:sheep", "scoff"), ("PH2", "shake", "L006:sheep", 0.5, 0.8),
              ("YOUNG", "look", "L006:sheep+0.2", "down"), ("YOUNG", "emo", "L006:sheep", "doubt")]),
    dict(id="S07", set="hillside", start="L007-0.1",
         cast=dict(JESUS=dict(mark="MARK_SHEPHERD", emo="tender", look="SHEEP_2_HEAD")),
         cam=pcam((0.9, -10.2, 0.42), (0.1, -4.5, 0.85), lens=42, fstop=3.2, focus="SHEEP_2_HEAD",
                  end=((0.8, -9.7, 0.45), (0.1, -4.5, 0.9))),
         light=dict(none=True),
         post="import flock, fx; flock.lift_heads(n, t_voice=0.4, follow_after=2.2); "
              "fx.add_area('SHEEP_FILL', (2.5, -11.5, 1.6), (0.0, -6.5, 0.6), 60.0, 3.0, (1.0, 0.82, 0.62))"),
    dict(id="S08", set="colonnade", start="L008-0.1",
         cast=C("JOHN", "PETER"),
         cam=cam("JOHN", "CU", az=-5, lens=85, fstop=2.0, dist=1.6, end=dict(dist=1.45)),
         light=dict(COLONNADE_LIGHT, key=8.0),
         post="import fx; fx.sun_break(n, 0.3, 2.5)",
         act=[("JOHN", "look", 0.0, "JESUS"), ("JOHN", "emo", 0.0, "worried"), ("JOHN", "look", 1.2, "heaven"),
              ("JOHN", "emo", 1.3, "hopeful", 0.9, 0.8)]),
    dict(id="S09", set="colonnade", start="L009-0.1",
         cast=C("JESUS", JESUS=dict(hands={"L": "rest", "R": "palm_up"})),
         cam=pcam((-0.55, -0.85, 1.12), (-0.12, -0.36, 0.98), lens=85, fstop=2.0, focus="HAND_R_JESUS",
                  end=((-0.5, -0.8, 1.1), (-0.12, -0.36, 0.98))),
         light=dict(COLONNADE_LIGHT, per_char=True, key=10.0),
         act=[("JESUS", "gest", "L009:snatch", "R", "fist", 1.4)]),
    dict(id="S10", frame_step=2, set="colonnade", start="L010-0.1",
         cast=C("JESUS", "ELDER", "YOUNG", "PH2", "PH3"),
         cam=pcam((5, -24, 1.3), (0, 0, 4.2), lens=24, fstop=8, end=((5, -23, 1.3), (0, 0, 5.2)), handheld=0.1),
         light=dict(none=True),
         act=[("JESUS", "look", 0.0, "up")]),
    dict(id="S11", set="colonnade", start="L011-0.1",
         cast=C("JESUS", JESUS=dict(hands={"L": "rest", "R": "palm_up"})),
         cam=pcam((-0.35, -0.9, 1.35), (-0.12, -0.36, 0.98), lens=70, fstop=2.2, focus="HAND_R_JESUS",
                  end=((-0.33, -0.85, 1.3), (-0.12, -0.36, 1.0))),
         light=dict(COLONNADE_LIGHT, key=6.0),
         post="import fx; fx.hand_glow('JESUS', n)"),
    dict(id="S12", set="colonnade", start="L012-0.15",
         cast=C("JESUS"),
         cam=cam("JESUS", "ECU", az=-6, lens=100, fstop=2.0, dist=0.95, end=dict(dist=0.85)),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "look", 0.0, "ELDER"), ("JESUS", "noblink", 0.0, 4.0), ("JESUS", "emo", 0.0, "absolute")]),
    dict(id="S12b", set="colonnade", start="L012.e+0.25",
         cast=C("ELDER", "PH2"),
         cam=cam("ELDER", "CU", az=-8, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "look", 0.0, "JESUS"), ("ELDER", "emo", 0.0, "stunned", 0.6, 0.15),
              ("ELDER", "emo", 0.35, "cold_fury", 1.0, 0.4), ("ELDER", "noblink", 0.0, 1.0)]),
    dict(id="S12c", set="colonnade", start="L012.e+1.05",
         cast=C("YOUNG"),
         cam=cam("YOUNG", "CU", az=12, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("YOUNG", "look", 0.0, "JESUS"), ("YOUNG", "emo", 0.0, "stunned", 1.0, 0.2), ("YOUNG", "noblink", 0.0, 1.2),
              ("YOUNG", "up", 0.1, 0.15, 0.5)]),
    dict(id="S12d", set="colonnade", start="L012.e+1.85",
         cast=C("PH3", "PH2"),
         cam=cam("PH3", "MS", az=20, lens=50, fstop=3.5, dist=3.2),
         light=dict(COLONNADE_LIGHT, per_char=False),
         act=[("PH3", "move", 0.1, 0.8, (0.0, 0.35, 0.0)), ("PH3", "emo", 0.0, "scared"), ("PH3", "look", 0.0, "JESUS")]),
    dict(id="S13", set="colonnade", start="L013-0.1",
         cast=C("ELDER", ELDER=dict(pose="crouch", rotz=180, hands={"R": "rest"})),
         cam=pcam((0.3, -2.75, 0.2), (0.85, -1.95, 0.08), lens=50, fstop=2.0, focus="PROP_STONE_1"),
         light=dict(none=True),
         post="import fx; fx.pick_stone('ELDER', 'PROP_STONE_1', n, 0.4, 1.4)"),
    dict(id="S13b", set="colonnade", start="L013:stones",
         cast=C("YOUNG", YOUNG=dict(hands={"R": "stone_hold"})),
         cam=cam("YOUNG", "MS", az=10, lens=65, fstop=2.2, dist=2.4, look_off=(0, 0, -0.1)),
         light=COLONNADE_LIGHT,
         post="import fx; fx.stone_in_hand('YOUNG', 'PROP_STONE_3', 'R')",
         act=[("YOUNG", "look", 0.0, "hand_R"), ("YOUNG", "emo", 0.0, "shaken"), ("YOUNG", "tremble", 0.0, 9.0, 1.0),
              ("YOUNG", "look", 1.4, "JESUS"), ("YOUNG", "gest", 0.6, "R", "stone_chest", 0.8)]),
    dict(id="S14", set="colonnade", start="L014-0.2",
         cast=C("JESUS"),
         cam=cam("JESUS", "MCU", az=-18, lens=70, fstop=2.2, dist=2.1),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "emo", 0.0, "searching"), ("JESUS", "look", 0.0, "PH2"), ("JESUS", "look", 1.2, "ELDER"),
              ("JESUS", "look", "L014:which-0.3", "YOUNG"), ("JESUS", "blink", 1.15), ("JESUS", "blink", "L014:which-0.35")]),
    dict(id="S14b", set="colonnade", start="L014:stone-0.25",
         cast=C("YOUNG", YOUNG=dict(hands={"R": "stone_chest"})),
         cam=cam("YOUNG", "MCU", az=14, lens=85, fstop=2.0, dist=2.3, look_off=(0, 0, -0.06)),
         light=COLONNADE_LIGHT,
         post="import fx; fx.stone_in_hand('YOUNG', 'PROP_STONE_3', 'R')",
         act=[("YOUNG", "look", 0.0, "JESUS"), ("YOUNG", "look", 0.5, "hand_R"), ("YOUNG", "emo", 0.0, "shaken"),
              ("YOUNG", "tremble", 0.0, 9.0, 1.2)]),
    dict(id="S15", set="colonnade", start="L015-0.15",
         cast=C("ELDER", "YOUNG", ELDER=dict(hands={"R": "stone_hold"})),
         cam=cam("ELDER", "CU", az=-12, el=-6, lens=85, fstop=2.0, dist=1.55, end=dict(dist=1.4)),
         light=COLONNADE_LIGHT,
         post="import fx; fx.stone_in_hand('ELDER', 'PROP_STONE_1', 'R')",
         act=[("ELDER", "tremble", 0.0, 9.0, 0.8)]),
    dict(id="S16", frame_step=2, set="scroll", start="L016-0.1",
         cast={},
         cam=dict(start=dict(pos=None, target=None), hint="CAMHINT_CU", lens=65, fstop=2.0),
         light=dict(none=True), post="import fx; fx.scroll_unroll(n)"),
    dict(id="S17", set="colonnade", start="L017-0.1",
         cast=C("ELDER", "YOUNG", ELDER=dict(hands={"R": "stone_hold"})),
         cam=cam("ELDER", "CU", az=-6, lens=85, fstop=1.8, dist=1.45, look_off=(-0.08, 0, 0)),
         light=COLONNADE_LIGHT,
         post="import fx; fx.stone_in_hand('ELDER', 'PROP_STONE_1', 'R')",
         act=[("ELDER", "look", 0.0, "JESUS"), ("ELDER", "emo", 0.0, "hard"), ("ELDER", "look", "L017:Scripture", "down_L"),
              ("ELDER", "emo", "L017:Scripture", "doubt", 0.7, 0.6), ("ELDER", "gest", "L017:Scripture", "R", "fist", 0.4),
              ("YOUNG", "look", "L017:Scripture+0.3", "ELDER")]),
    dict(id="S18", set="colonnade", start="L018-0.1",
         cast=C("JESUS"),
         cam=cam("JESUS", "MCU", az=-10, lens=70, fstop=2.2, dist=2.0, end=dict(dist=1.8)),
         light=COLONNADE_LIGHT, post="import fx; fx.sun_break(n, 1.0, 3.0, target='JESUS')",
         act=[("JESUS", "emo", 0.0, "earnest"), ("JESUS", "gest", "L018:set", "R", "chest", 0.7),
              ("JESUS", "look", "L018:sent", "heaven"), ("JESUS", "look", "L018:world", "ELDER")]),
    dict(id="S19", set="colonnade", start="L019-0.15",
         cast=C("ELDER", ELDER=dict(hands={"R": "stone_hold"})),
         cam=cam("ELDER", "MCU", az=-14, lens=60, fstop=2.4, dist=2.0),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "gest", 0.15, "R", "point", 0.35), ("ELDER", "emo", 0.0, "cold_fury"),
              ("ELDER", "lean", 0.15, 6, 0.3)]),
    dict(id="S19b", set="colonnade", start="L019:blasphemy",
         cast=C("JESUS"),
         cam=cam("JESUS", "CU", az=-12, lens=85, fstop=2.0, dist=1.55),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "emo", 0.0, "pained"), ("JESUS", "look", 0.0, "ELDER")]),
    dict(id="S20", set="colonnade", start="L020-0.1",
         cast=C("JESUS"),
         cam=cam("JESUS", "MS", az=-10, lens=50, fstop=2.8, dist=3.0, end=dict(dist=2.7)),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "emo", 0.0, "pleading"), ("JESUS", "gest", 0.2, "LR", "palms_open", 0.8),
              ("JESUS", "move", 1.0, 2.2, (0.0, -0.25, 0.0)), ("JESUS", "look", 0.0, "YOUNG")]),
    dict(id="S21", set="hillside", start="L021-0.1",
         cast=dict(PH3=dict(mark="MARK_SHEPHERD", rotz=180, emo="awe", look="up")),
         cam=cam("PH3", "CU", az=15, lens=85, fstop=1.8, dist=1.4),
         light=dict(key=4.0, fill=1.0, rim=6.0, key_color=(1.0, 0.85, 0.65)),
         post="import blindman; blindman.apply(rigs, n)",
         act=[("PH3", "emo", 0.0, "joy", 0.8), ("PH3", "look", 0.0, "up"), ("PH3", "look", 1.2, "left")]),
    dict(id="S21b", set="upper_room", start="L021:believe",
         cast=U("JESUS", JESUS=dict(hands={"L": "table", "R": "table"})),
         cam=pcam((0.05, -1.25, 0.95), (0.0, -0.55, 0.42), lens=50, fstop=2.0, focus="PROP_BREAD_A"),
         light=dict(none=True), post="import fx; fx.break_bread('JESUS', n)"),
    dict(id="S22", set="colonnade", start="L022-0.1",
         cast=C("JESUS"),
         cam=cam("JESUS", "CU", az=8, lens=85, fstop=2.0, dist=1.6),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "look", 0.0, "YOUNG"), ("JESUS", "emo", 0.0, "tender")]),
    dict(id="S22b", set="colonnade", start="L022.e-0.1",
         cast=C("YOUNG", YOUNG=dict(hands={"R": "stone_chest"})),
         cam=pcam((-1.45, -1.25, 0.9), (-0.45, -1.45, 0.75), lens=40, fstop=4.0, focus="PROP_STONE_3"),
         light=dict(COLONNADE_LIGHT, per_char=True),
         post="import fx; fx.stone_in_hand('YOUNG', 'PROP_STONE_3', 'R'); fx.drop_stone('YOUNG', 'PROP_STONE_3', 0.5, n)",
         act=[("YOUNG", "gest", 0.45, "R", "stone_open", 0.25)]),
    dict(id="S22c", set="colonnade", start="L022.e+1.2",
         cast=C("YOUNG"),
         cam=cam("YOUNG", "CU", az=-10, el=-22, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("YOUNG", "look", 0.0, "hand_R"), ("YOUNG", "emo", 0.0, "stunned"), ("YOUNG", "gest", 0.0, "R", "palm_up", 0.3)]),
    dict(id="S23", set="colonnade", start="L023-0.15",
         cast=C("ELDER", "PH2"),
         cam=cam("ELDER", "CU", az=-40, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "look", 0.0, "JESUS"), ("ELDER", "look", 0.25, "PH2"), ("ELDER", "emo", 0.0, "cold_fury")]),
    dict(id="S24", set="colonnade", start="L024-0.1",
         cast=C("JESUS", "ELDER", "PH2", "PH3", ELDER=dict(hands={"R": "rest"})),
         cam=pcam((3.4, -1.4, 1.5), (0.2, -0.5, 1.4), lens=35, fstop=4.0, focus="JESUS",
                  end=((3.2, -0.6, 1.5), (-1.8, 1.0, 1.4))),
         light=dict(COLONNADE_LIGHT, per_char=False),
         act=[("ELDER", "gest", 0.3, "R", "reach", 0.35), ("PH2", "gest", 0.4, "L", "reach", 0.4),
              ("ELDER", "move", 0.3, 1.0, (0.0, 0.45, 0.0)), ("PH2", "move", 0.35, 1.2, (-0.2, 0.4, 0.0)),
              ("JESUS", "move", 0.5, 3.2, (-2.4, 1.2, 0.0), "walk"), ("JESUS", "look", 0.4, "left"),
              ("ELDER", "gest", 1.0, "R", "grab", 0.25)]),
    dict(id="S24b", set="colonnade", start="L024:escaped",
         cast=C("ELDER", ELDER=dict(hands={"R": "reach"})),
         cam=pcam((0.9, 0.2, 1.4), (0.42, -0.62, 1.33), lens=85, fstop=1.8, focus="HAND_R_ELDER"),
         light=dict(COLONNADE_LIGHT, per_char=True),
         act=[("ELDER", "gest", 0.3, "R", "grab", 0.5)]),
    dict(id="S25", set="colonnade", start="L025-0.6",
         cast=C("ELDER", "YOUNG", ELDER=dict(look="PROP_STONE_3"), YOUNG=dict(look="ELDER")),
         cam=pcam((-2.9, -0.95, 1.5), (0.0, -1.45, 1.3), lens=40, fstop=3.2, focus="ELDER"),
         light=dict(COLONNADE_LIGHT, per_char=False),
         post="import fx; fx.place_dropped_stone('PROP_STONE_3')",
         act=[("ELDER", "look", 0.0, "PROP_STONE_3"), ("ELDER", "emo", 0.0, "cold", 0.7)]),
    dict(id="S26", set="colonnade", start="L026-0.1",
         cast=C("YOUNG"),
         cam=cam("YOUNG", "CU", az=18, lens=85, fstop=2.0, dist=1.5, end=dict(dist=1.38)),
         light=COLONNADE_LIGHT,
         act=[("YOUNG", "look", 0.0, "ELDER"), ("YOUNG", "emo", 0.0, "shaken"),
              ("YOUNG", "blink", "L026:blind+0.25")]),
    dict(id="S26b", set="colonnade", start="L026.e+0.15",
         cast=C("ELDER"),
         cam=cam("ELDER", "CU", az=-20, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("ELDER", "look", 0.0, "YOUNG"), ("ELDER", "emo", 0.0, "doubt"), ("ELDER", "emo", 0.5, "heavy", 1.0, 0.6),
              ("ELDER", "look", 1.0, "right"), ("ELDER", "down", 1.0, 0.3, 1.2)]),
    # ================================================================== the street
    dict(id="S27", set="colonnade", start="L027-0.5",
         cast=dict(JESUS=dict(mark="MARK_JESUS_ST", rotz=-63, emo="calm", look="PETER"),
                   PETER=dict(mark="MARK_PETER_ST", rotz=117, emo="scared", addr="JESUS"),
                   JOHN=dict(mark="MARK_JOHN_ST", rotz=41, emo="worried", look="JESUS")),
         cam=pcam((24.75, -0.1, 0.25), (23.25, -0.9, 0.05), lens=45, fstop=2.8, focus="PETER"),
         light=dict(COLONNADE_LIGHT, per_char=False),
         act=[("PETER", "move", 0.0, 0.6, (0.0, 0.5, 0.0), "walk"),
              ("PETER", "gest", 0.55, "R", ("bone", "JESUS", "lowerarm01.L", (0.0, -0.03, 0.0)), 0.3)]),
    dict(id="S28", set="colonnade", start="L028-0.1",
         cast=dict(JESUS=dict(mark="MARK_JESUS_ST", rotz=-63, emo="gentle", addr="PETER")),
         cam=cam("JESUS", "CU", az=-30, lens=85, fstop=2.0, dist=1.55),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "emo", 0.0, "gentle"), ("JESUS", "nod", 0.6, 0.4, 0.7)]),
    dict(id="S29", set="colonnade", start="L029-0.2",
         cast=dict(JOHN=dict(mark="MARK_JOHN_ST", rotz=41, emo="worried", look="down")),
         cam=cam("JOHN", "CU", az=-20, lens=85, fstop=2.0, dist=1.5),
         light=COLONNADE_LIGHT,
         act=[("JOHN", "look", 0.0, "down"), ("JOHN", "emo", 0.0, "worried")]),
    dict(id="S30", set="colonnade", start="L030-0.2",
         cast=dict(JESUS=dict(mark="MARK_JESUS_ST", rotz=-63, emo="tender", addr="JOHN")),
         cam=cam("JESUS", "CU", az=-35, lens=85, fstop=2.0, dist=1.6, end=dict(dist=1.4)),
         light=COLONNADE_LIGHT,
         act=[("JESUS", "look", 0.0, "JOHN"), ("JESUS", "look", "L030.e+0.2", "far"),
              ("JESUS", "emo", "L030.e+0.3", "warm", 0.6, 0.8)]),
    # ================================================================== SCENE 2: THE UPPER ROOM
    dict(id="S31", frame_step=2, set="upper_room", start="L031-0.9",
         cast={},
         cam=dict(hint="CAMHINT_LAMP_CU", lens=100, fstop=2.0, push=0.08),
         light=dict(none=True)),
    dict(id="S32", set="upper_room", start="L031b-0.1",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "MCU", az=10, el=-4, lens=60, fstop=2.0, dist=2.2, end=dict(dist=1.9)),
         light=UPPER_LIGHT,
         act=[("JESUS", "look", 0.0, "down"), ("JESUS", "look", "L031b:heaven-0.2", "heaven"),
              ("JESUS", "emo", "L031b:heaven", "prayer")]),
    dict(id="S33", set="upper_room", start="L032-0.1",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "CU", az=12, el=-4, lens=85, fstop=1.8, dist=1.55),
         light=UPPER_LIGHT,
         act=[("JESUS", "look", 0.0, "heaven"), ("JESUS", "look", "L032:them-0.15", "JOHN"),
              ("JESUS", "emo", "L032:them", "tender")]),
    dict(id="S33b", set="upper_room", start="L032.e+0.05",
         cast=U("JOHN"),
         cam=cam("JOHN", "CU", az=-15, el=-4, lens=85, fstop=1.8, dist=1.5),
         light=UPPER_LIGHT,
         act=[("JOHN", "emo", 0.0, "tender"), ("JOHN", "blink", 0.3)]),
    dict(id="S34", set="upper_room", start="L033-0.1",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "CU", az=8, el=-3, lens=85, fstop=1.8, dist=1.6, end=dict(dist=1.3)),
         light=UPPER_LIGHT,
         act=[("JESUS", "look", 0.0, "heaven"), ("JESUS", "emo", 0.0, "prayer_warm"),
              ("JESUS", "look", "L033:believe", "far")]),
    # ================================================================== modern: the apartment
    dict(id="S35", set="apartment", start="L034-0.4",
         cast=dict(WOMAN=dict(WOM, look="PROP_PHONE", mouth_lines=["L033"])),
         cam=cam("WOMAN", "MCU", az=8, el=2, lens=60, fstop=2.0, dist=2.0, end=dict(dist=1.7)),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('WOMAN'); fx.phone_screen('read')"),
    dict(id="S36", set="apartment", start="L035-0.3",
         cast=dict(WOMAN=dict(WOM, look="PROP_PHONE")),
         cam=cam("WOMAN", "CU", az=10, lens=85, fstop=1.8, dist=1.5, end=dict(dist=1.38)),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('WOMAN'); fx.phone_screen('read')",
         act=[("WOMAN", "emo", 0.0, "stunned"), ("WOMAN", "look", "L035:me", "fwd"),
              ("WOMAN", "emo", "L035.e+0.1", "breaking", 0.8, 0.6), ("WOMAN", "look", "L035.e+0.4", "PROP_PHOTO"),
              ("WOMAN", "gest", "L035.e", "LR", "phone_low", 0.8)]),
    dict(id="S37", frame_step=2, set="apartment", start="L036-0.1",
         cast={},
         cam=dict(hint="CAMHINT_PHOTO_CU", lens=100, fstop=2.2, push=0.12),
         light=dict(none=True)),
    dict(id="S38", set="apartment", start="L037-0.1",
         cast=dict(WOMAN=dict(WOM, look="PROP_PHONE", hands={"L": "phone_low", "R": "phone_low"})),
         cam=dict(hint="CAMHINT_OTS_PHONE", lens=50, fstop=2.8, focus="PROP_PHONE"),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('WOMAN'); fx.phone_screen_sequence(n)"),
    # ================================================================== upper room: unity
    dict(id="S39", set="upper_room", start="L038-0.1",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "MS", az=0, el=-2, lens=28, fstop=2.8, dist=2.0, end=dict(dist=1.85)),
         light=dict(UPPER_LIGHT, per_char=False),
         post="import fx; fx.lamp_bloom(n, 0.5, 3.0)",
         act=[("JESUS", "look", 0.0, "heaven"),
              ("JESUS", "gest", 0.4, "R", ("bone", "JOHN", "shoulder01.L", (0.0, 0.0, 0.06)), 1.0),
              ("JESUS", "gest", 0.6, "L", ("bone", "PETER", "shoulder01.R", (0.0, 0.0, 0.06)), 1.0),
              ("JOHN", "lean", 0.3, 8, 1.0), ("PETER", "lean", 0.4, 8, 1.0)]),
    dict(id="S40", set="upper_room", start="L039-0.1",
         cast=U("PETER", "JOHN", "JESUS"),
         cam=cam("PETER", "CU", az=-20, el=-4, lens=85, fstop=1.8, dist=1.5),
         light=UPPER_LIGHT,
         act=[("PETER", "emo", 0.0, "heavy"), ("PETER", "emo", 1.0, "tender", 0.8, 1.0), ("PETER", "look", 0.5, "JOHN"),
              ("PETER", "gest", 0.4, "R", ("bone", "JOHN", "wrist.L", (0.0, 0.0, 0.03)), 0.9)]),
    # ================================================================== the call
    dict(id="S41", set="sister_kitchen", start="L039.e+0.2",
         cast=dict(SISTER=dict(SIS, hands={"L": "rest", "R": "phone_low"}, look="hand_R")),
         cam=cam("SISTER", "CU", az=10, lens=85, fstop=1.8, dist=1.55),
         light=APT_LIGHT, post="import fx; fx.sister_phone(n)",
         act=[("SISTER", "emo", 0.0, "stunned", 0.6), ("SISTER", "noblink", 0.0, 1.0),
              ("SISTER", "gest", "L040-0.6", "R", "phone_ear", 0.5), ("SISTER", "look", "L040-0.5", "fwd"),
              ("SISTER", "emo", "L040-0.4", "guarded")]),
    dict(id="S42", set="apartment", start="L041-0.15",
         cast=dict(WOMAN=dict(WOM, hands={"L": "lap", "R": "phone_ear"}, look="down")),
         cam=cam("WOMAN", "CU", az=-12, lens=85, fstop=1.8, dist=1.5, end=dict(dist=1.4)),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('WOMAN')",
         act=[("WOMAN", "emo", 0.0, "breaking"), ("WOMAN", "look", 0.0, "down"),
              ("WOMAN", "gest", "L041:sorry", "L", "knuckles_mouth", 0.6), ("WOMAN", "gest", "L041:what", "L", "lap", 0.6)]),
    dict(id="S43", set="sister_kitchen", start="L042-0.2",
         cast=dict(SISTER=dict(SIS, look="down")),
         cam=cam("SISTER", "CU", az=-8, lens=85, fstop=1.8, dist=1.5, end=dict(dist=1.4)),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('SISTER', 'R')",
         act=[("SISTER", "emo", 0.0, "crying"), ("SISTER", "emo", "L042.e", "eyes_closed_cry", 0.8, 0.5)]),
    dict(id="S44", set="apartment", start="L043-0.2",
         cast=dict(WOMAN=dict(WOM, hands={"L": "lap", "R": "phone_ear"}, look="fwd")),
         cam=cam("WOMAN", "CU", az=-10, lens=85, fstop=1.8, dist=1.45),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('WOMAN')",
         act=[("WOMAN", "emo", 0.0, "hopeful_tears")]),
    dict(id="S45", set="sister_kitchen", start="L044-0.2",
         cast=dict(SISTER=dict(SIS, look="fwd")),
         cam=cam("SISTER", "CU", az=-8, lens=85, fstop=1.8, dist=1.45, end=dict(dist=1.35)),
         light=APT_LIGHT, post="import fx; fx.phone_in_hand('SISTER', 'R')",
         act=[("SISTER", "emo", 0.0, "warm_tears")]),
    # ================================================================== upper room: love and glory
    dict(id="S46", set="upper_room", start="L045-0.15",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "CU", az=6, el=-4, lens=85, fstop=1.8, dist=1.6, end=dict(dist=1.45)),
         light=UPPER_LIGHT, post="import fx; fx.lamp_bloom(n, 0.2, 3.5)",
         act=[("JESUS", "look", 0.0, "heaven"), ("JESUS", "emo", 0.0, "joy", 0.7, 1.0)]),
    dict(id="S47", frame_step=2, set="upper_room", start="L046-0.1",
         cast={},
         cam=dict(hint="CAMHINT_LAMP_CU", lens=100, fstop=2.0, push=0.75),
         light=dict(none=True)),
    dict(id="S48", frame_step=2, set="cosmos", start="L047-0.1",
         cast={}, cam=dict(hint="CAMHINT_MAIN", keep_anim=True), light=dict(none=True),
         post="import fx; fx.cosmos_reveal(n)"),
    dict(id="S49", frame_step=2, set="city", start="L048-0.1",
         cast={}, cam=dict(hint="CAMHINT_WIDE", lens=35, fstop=5.6, push=0.2), light=dict(none=True),
         post="import fx; fx.city_window(n)"),
    dict(id="S50", set="upper_room", start="L049-0.15",
         cast=U("JOHN"),
         cam=cam("JOHN", "CU", az=-14, el=-4, lens=85, fstop=1.8, dist=1.5),
         light=UPPER_LIGHT,
         act=[("JOHN", "emo", 0.0, "warm", 0.7), ("JOHN", "nod", 0.4, 0.8, 1.4), ("JOHN", "look", 0.0, "JESUS")]),
    # ================================================================== the door
    dict(id="S51", set="hallway_door", start="L050-0.2",
         cast=dict(WOMAN=dict(mark="MARK_WOMAN", off=(0.05, 0.7, 0), emo="worried", look="SISTER"),
                   SISTER=dict(mark="MARK_SISTER", off=(0.15, 1.1, 0), emo="worried", look="WOMAN")),
         cam=pcam((0.95, -0.5, 1.5), (0.12, 0.9, 1.45), lens=32, fstop=2.8, focus="SISTER",
                  end=((0.85, -0.3, 1.5), (0.12, 0.9, 1.45))),
         light=dict(none=True), post="import fx; fx.door_open(n, 0.0, 1.6)"),
    dict(id="S52", set="hallway_door", start="L050b-0.25",
         cast=dict(SISTER=dict(mark="MARK_SISTER", off=(0.15, 1.1, 0), emo="warm_tears", look="@MARK_WOMAN")),
         cam=pcam((0.45, 0.02, 1.57), (0.15, 1.33, 1.5), lens=80, fstop=2.0, focus="SISTER"),
         light=dict(key=5.0, fill=1.2, rim=5.0, key_color=(1.0, 0.78, 0.55)),
         post="import fx; fx.door_open(n, -1.0, 0.0)"),
    dict(id="S53", set="hallway_door", start="L050c-0.2",
         cast=dict(WOMAN=dict(mark="MARK_WOMAN", off=(0.05, 0.7, 0), emo="warm_tears", look=(0.15, 1.45, 1.55))),
         cam=pcam((0.3, 1.25, 1.58), (0.05, 0.38, 1.5), lens=60, fstop=2.0, focus="WOMAN"),
         light=dict(key=5.0, fill=1.2, rim=5.0, key_color=(1.0, 0.78, 0.55)),
         post="import fx; fx.door_open(n, -1.0, 0.0)",
         act=[("WOMAN", "emo", "L050c.e", "joy", 0.6, 0.4)]),
    dict(id="S53b", set="hallway_door", start="L050c.e+0.3",
         cast=dict(WOMAN=dict(mark="MARK_WOMAN", off=(0.05, 0.7, 0), emo="warm_tears", look="SISTER"),
                   SISTER=dict(mark="MARK_SISTER", off=(0.15, 1.1, 0), emo="warm_tears", look="WOMAN")),
         cam=pcam((1.0, -0.4, 1.5), (0.1, 0.85, 1.4), lens=40, fstop=2.4, focus="WOMAN",
                  end=((0.85, -0.2, 1.48), (0.1, 0.85, 1.4))),
         light=dict(none=True), post="import fx; fx.door_open(n, -1.0, 0.0); fx.hug(n, 0.2, 1.4)"),
    dict(id="S54", set="hallway_door", start="L051-0.1",
         cast=dict(WOMAN=dict(mark="MARK_WOMAN", off=(0.05, 0.7, 0), emo="eyes_closed_peace"),
                   SISTER=dict(mark="MARK_SISTER", off=(0.15, 1.1, 0), emo="eyes_closed_peace")),
         cam=pcam((0.75, 0.05, 1.55), (0.1, 0.85, 1.45), lens=55, fstop=2.0, focus="WOMAN",
                  end=((0.68, 0.15, 1.55), (0.1, 0.85, 1.45))),
         light=dict(none=True), post="import fx; fx.door_open(n, -1.0, 0.0); fx.hug(n, -1.0, 0.1)"),
    dict(id="S54b", set="upper_room", start="L051:I",
         cast=U("JESUS", "JOHN", "PETER", JESUS=dict(emo="eyes_closed_peace")),
         cam=cam("JESUS", "CU", az=4, el=-4, lens=85, fstop=1.8, dist=1.55, end=dict(dist=1.4)),
         light=UPPER_LIGHT,
         act=[("JESUS", "emo", "L051:myself", "love", 1.0, 0.8), ("JESUS", "look", "L051:myself", "JOHN"),
              ("JESUS", "look", "L051.e+0.5", "PETER")]),
    dict(id="S55", set="upper_room", start="L052-0.2",
         cast=U("JESUS", "JOHN", "PETER"),
         cam=cam("JESUS", "CU", az=0, el=-3, lens=85, fstop=1.8, dist=1.65, end=dict(dist=1.45)),
         light=UPPER_LIGHT,
         act=[("JESUS", "look", 0.0, "PETER"), ("JESUS", "look", 1.0, "cam"), ("JESUS", "emo", 1.0, "warm", 0.7, 1.2)]),
]


def _word_time(line, word, end=False):
    target = re.sub(r"[^a-z']", "", word.lower())
    for w in line["words"]:
        if re.sub(r"[^a-z']", "", w["word"].lower()) == target:
            return w["end"] if end else w["start"]
    # fall back to proportional position in the text
    words = [re.sub(r"[^a-z']", "", x.lower()) for x in line["text"].split()]
    idx = words.index(target) if target in words else 0
    return line["start"] + (line["end"] - line["start"]) * idx / max(1, len(words))


def resolve_time(anchor, LINES):
    if isinstance(anchor, (int, float)):
        return float(anchor)
    m = re.match(r"^(L\d+[a-z]?)(?::([A-Za-z']+))?(\.e)?([+-]\d+(?:\.\d+)?)?$", anchor)
    if not m:
        raise ValueError(f"bad anchor {anchor}")
    lid, word, end, off = m.groups()
    line = LINES[lid]
    if word:
        t = _word_time(line, word, end=bool(end))
    else:
        t = line["end"] if end else line["start"]
    return t + (float(off) if off else 0.0)


def shot_bounds(LINES, duration):
    """(shot, t0, t1) with each shot ending where the next starts."""
    out = []
    starts = [resolve_time(s["start"], LINES) for s in SHOTS]
    for i, s in enumerate(SHOTS):
        t1 = starts[i + 1] if i + 1 < len(SHOTS) else duration
        out.append((s, starts[i], t1))
    return out
