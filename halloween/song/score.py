"""CLICKETY-CLACK (The Skeletons Are Back) - an original spooky Halloween song.

Words, melody and arrangement written for this project.

Token format for sung lines:  SYL|NOTE|BEATS   (BEATS may end with '>' accent or '~' fall-off)
  - a syllable ending in '-' continues the same word ("Click-|B2|.5 e-|B2|.5 ty|B2|.5")
  - "_|-|BEATS" is a rest
"""
BPM = 128
BEAT = 60.0 / BPM
BAR = 4 * BEAT
SWING = 0.58          # swung eighths for the band

# ------------------------------------------------------------------ sections (bars)
# name, first bar, length in bars, chords per bar (or per half bar with '/')
SECTIONS = [
    ("intro", 0, 4, ["Em", "Em", "C", "B7"]),
    ("verse1", 4, 8, ["Em", "Em", "Am", "B7", "Em", "C", "Am/B7", "Em"]),
    ("pre1", 12, 4, ["C", "D", "B7", "B7"]),
    ("chorus1", 16, 8, ["Em", "C", "Am", "B7", "Em", "C", "Am/B7", "Em"]),
    ("verse2", 24, 8, ["Em", "Em", "Am", "B7", "Em", "C", "Am/B7", "Em"]),
    ("pre2", 32, 4, ["C", "D", "B7", "B7"]),
    ("chorus2", 36, 8, ["Em", "C", "Am", "B7", "Em", "C", "Am/B7", "Em"]),
    ("bridge", 44, 8, ["Em", "Em", "Am", "B7", "Em", "Em", "NC", "B7"]),
    ("xylo", 52, 4, ["Em", "C", "Am", "B7"]),
    ("chorus3", 56, 8, ["Fm", "Db", "Bbm", "C7", "Fm", "Db", "Bbm/C7", "Fm"]),
    ("chorus4", 64, 8, ["Fm", "Db", "Bbm", "C7", "Fm", "Db", "Bbm/C7", "Fm"]),
    ("outro", 72, 6, ["Fm", "NC", "NC", "NC", "NC", "Fm"]),
]
TOTAL_BARS = 78

# ------------------------------------------------------------------ cast
SINGERS = {
    "RATTLES": dict(voice="am_puck", label="Rattles", color=(255, 196, 110)),        # lead skeleton
    "FEMURELLA": dict(voice="af_bella", label="Femurella", color=(255, 160, 205)),    # flower skeleton
    "CLATTER": dict(voice="am_fenrir", label="Big Clatter", color=(170, 210, 255)),   # bass skeleton
    "TIBBS": dict(voice="af_kore", label="Tibbs", color=(170, 240, 170)),            # tiny skeleton
    "CAT": dict(voice="af_nicole", label="The Cat", color=(236, 226, 80)),
    "MICE": dict(voice="af_kore", label="The Pencil Mice", color=(140, 210, 255)),
    "ALL": dict(voice=None, label="Everybody", color=(255, 236, 160)),
}
# who sings when "ALL" sings: (voice, semitone shift, gain, pan, delay)
GANG = [("am_puck", 0, 1.0, -0.15, 0.000), ("am_michael", 0, 0.8, 0.2, 0.012),
        ("af_heart", 12, 0.75, -0.3, 0.008), ("af_bella", 12, 0.7, 0.32, 0.018)]
GANG_FINAL = GANG + [("af_kore", 12, 0.5, 0.0, 0.006)]

# ------------------------------------------------------------------ melody lines
CH1 = "Click-|B2|.5 e-|B2|.5 ty|B2|.5 clack!|E3|1.5> _|-|1 Click-|C3|.5 e-|C3|.5 ty|C3|.5 clack!|B2|1.5> _|-|1"
CH2 = ("The|E3|.5 skel-|E3|.5 e-|F#3|.5 tons|G3|.5 are|A3|.5 back|B3|1.5> "
       "with|A3|.5 a|G3|.5 rat-|F#3|.5 tle|E3|.5 and|D#3|.5 a|E3|.5 snap!|F#3|1.5>")
CH3 = "Click-|B2|.5 e-|B2|.5 ty|B2|.5 clack!|E3|1.5> _|-|1 Don't|D3|1> you|C3|.5 be|B2|.5 scared,|C3|2"
CH4 = "grab|A3|.5 a|A3|.5 bo-|C4|.5 ny|B3|.5 hand,|A3|1 if|B3|.5 you|B3|.5 dare!|E3|1.5> _|-|2.5"
RESP = "If|G4|.5 you|G4|.5 dare!|B4|1>"

# (section, bar offset within section, beat offset, singer, tokens, transpose)
LINES = [
    # ---- verse 1 (Rattles)
    ("verse1", 0, 0, "RATTLES", "Down|B2|.5 in|E3|.5 the|F#3|.5 gar-|G3|1 den|F#3|.5 where|E3|.5 the|D#3|.5 pump-|E3|1 kins|F#3|.5 grow,|B2|2", 0),
    ("verse1", 2, 0, "RATTLES", "some-|C3|.5 thing's|C3|.5 knock-|E3|1 ing|C3|.5 on|B2|.5 the|D#3|.5 dirt|F#3|1 be-|A3|.5 low...|F#3|2.5", 0),
    ("verse1", 4, 0, "RATTLES", "Knock,|E3|1> knock!|E3|1> Who's|E3|.5 there?|G3|1.5 Can|G3|.5 you|F#3|.5 guess|E3|.5 who?|D#3|2.5", 0),
    ("verse1", 6, 0, "RATTLES", "A|A2|.5 bo-|C3|.5 ny|E3|.5 lit-|A3|.5 tle|G3|.5 hand,|F#3|1.5 and|B2|.5 it's|D#3|.5 wa-|F#3|.5 ving|A3|.5 at|G3|.5 you!|E3|1.5~", 0),
    # ---- pre-chorus 1
    ("pre1", 0, 0, "RATTLES", "Up|D3|.5 pops|D3|.5 a|D3|.5 foot,|E3|1> then|E3|.5 a|E3|.5 bo-|F#3|.5 ny|F#3|.5 knee,|G3|2.5 _|-|1", 0),
    ("pre1", 2, 0, "RATTLES", "then|D3|.5 a|D3|.5 grin-|E3|.5 ning|F#3|.5 skull,|G3|1> and|F#3|.5 it's|F#3|.5 grin-|G3|.5 ning|A3|.5 at|G3|.5 me!|F#3|2.5>", 0),
    # ---- chorus 1
    ("chorus1", 0, 0, "ALL", CH1, 0), ("chorus1", 2, 0, "ALL", CH2, 0),
    ("chorus1", 4, 0, "ALL", CH3, 0), ("chorus1", 6, 0, "ALL", CH4, 0),
    ("chorus1", 7, 2.0, "TIBBS", RESP, 0),
    # ---- verse 2 (duet)
    ("verse2", 0, 0, "RATTLES", "They|B2|.5 have-|E3|.5 n't|E3|.5 got|F#3|.5 a|G3|.5 tum-|G3|.5 my,|F#3|.5 so|E3|.5 they|D#3|.5 can't|E3|.5 eat|F#3|1 sweets,|B2|2", 0),
    ("verse2", 2, 0, "FEMURELLA", "they|C4|.5 just|C4|.5 rat-|E4|.5 tle|C4|.5 at|B3|.5 the|C4|.5 doors|E4|1 when|B3|.5 you|D#4|.5 shout|F#4|.5 trick|A4|.5 or|G4|.5 treat!|F#4|1.5>", 0),
    ("verse2", 4, 0, "RATTLES", "They|E3|.5 have-|E3|.5 n't|E3|.5 got|G3|.5 a|G3|.5 nose,|B3|1.5 but|B3|.5 they|A3|.5 love|G3|.5 to|F#3|.5 sniff|E3|.5 the|F#3|.5 air,|G3|1", 0),
    ("verse2", 6, 0, "FEMURELLA", "and|A3|.5 they|C4|.5 nev-|E4|.5 er|A4|.5 need|G4|.5 a|F#4|.5 comb,|E4|1 'cause|B3|.5 they|D#4|.5 have-|F#4|.5 n't|A4|.5 an-|G4|.5 y|F#4|.5 hair!|E4|1~", 0),
    # ---- pre-chorus 2
    ("pre2", 0, 0, "RATTLES", "Their|D3|.5 bo-|D3|.5 ny|D3|.5 knees|E3|1> go|E3|.5 knock-|E3|.5 i-|F#3|.5 ty|F#3|.5 knock!|G3|2.5> _|-|1", 0),
    # ---- chorus 2
    ("chorus2", 0, 0, "ALL", CH1, 0), ("chorus2", 2, 0, "ALL", CH2, 0),
    ("chorus2", 4, 0, "ALL", CH3, 0), ("chorus2", 6, 0, "ALL", CH4, 0),
    ("chorus2", 7, 2.0, "TIBBS", RESP, 0),
    # ---- final choruses, up a half step
    ("chorus3", 0, 0, "ALL", CH1, 1), ("chorus3", 2, 0, "ALL", CH2, 1),
    ("chorus3", 4, 0, "ALL", CH3, 1), ("chorus3", 6, 0, "ALL", CH4, 1),
    ("chorus3", 7, 2.0, "MICE", RESP, 1),
    ("chorus4", 0, 0, "ALL", CH1, 1), ("chorus4", 2, 0, "ALL", CH2, 1),
    ("chorus4", 4, 0, "ALL", CH3, 1), ("chorus4", 6, 0, "ALL", CH4, 1),
    ("chorus4", 7, 2.0, "MICE", RESP, 1),
]

# spoken lines: (section, bar offset, beat offset, who, text, speed, max_bars)
SPOKEN = [
    ("intro", 0, 0.5, "CAT", "Psst. It's midnight. |0.4| Listen...", 0.9, 2.2),
    ("pre2", 2, 0.0, "CAT", "Ugh. What's all the clatter?", 0.95, 1.8),
    ("bridge", 0, 0.0, "CLATTER", "Now some folks scream, and some folks run,", 1.0, 2.0),
    ("bridge", 2, 0.0, "CLATTER", "but a skeleton just wants to have some fun!", 1.0, 2.0),
    ("bridge", 4, 0.0, "CLATTER", "So wiggle your fingers, and wobble your knees,", 1.0, 2.0),
    ("bridge", 6, 0.0, "CLATTER", "and... FREEZE!", 1.0, 0.9),
    ("bridge", 7, 2.0, "CLATTER", "Unfreeze!", 1.05, 0.6),
    ("outro", 1, 0.5, "RATTLES", "Uh-oh... |0.3| sunrise.", 0.95, 1.6),
    ("outro", 4, 0.0, "RATTLES", "Same time next year?", 1.0, 1.2),
    ("outro", 5, 0.0, "MICE", "Yeah!", 1.0, 0.6),
]
SPOKEN_PITCH = {"CLATTER": -3.0, "MICE": 3.0, "CAT": -1.0}
