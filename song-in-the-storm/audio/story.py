# Script + timing for both parts. All times in seconds.
BEAT = 60 / 66  # 66 bpm
TRANSPOSE = -5

# Original song: "Little Light" (words, midi notes, beats per note)
VERSE = [
    [("Cold",[76],[2]),("is",[74],[1]),("the",[72],[1]),("rain",[71],[2]),("on",[69],[1]),("the",[71],[1]),("street",[72],[2]),("where",[71],[1]),("I",[69],[1]),("stay",[64],[4])],
    [("no",[69],[1]),("one",[72],[1]),("has",[71],[1]),("stopped",[69],[3]),("they",[67],[1]),("all",[69],[1]),("look",[71],[2]),("a",[72],[1]),("way",[71],[5])],
    [("Still",[76],[2]),("in",[74],[1]),("my",[72],[1]),("chest",[71],[2]),("there's",[69],[1]),("a",[71],[1]),("song",[72],[2]),("I",[74],[1]),("keep",[76],[5])],
    [("sing",[77],[2]),("it",[76],[1]),("to",[74],[1]),("stars",[72],[2]),("while",[71],[1]),("the",[69],[1]),("whole",[71],[1]),("world",[72],[1]),("sleeps",[69],[6])],
]
VERSE_TEXT = ["Cold is the rain on the street where I stay,", "no one has stopped, they all look away.",
              "Still in my chest there's a song I keep,", "sing it to stars while the whole world sleeps."]
VERSE_CHORDS = ["Am","Em","F","E", "Am","F","G","E", "Am","Em","F","C", "Dm","Am","E","Am"]
CHORUS = [
    [("Oh",[72],[2]),("little",[76,74],[1,1]),("light",[79],[4]),("don't",[77],[1]),("go",[76],[1]),("out",[74],[6])],
    [("burn",[72],[2]),("through",[74],[1]),("the",[76],[1]),("dark",[77],[2]),("and",[76],[1]),("the",[74],[1]),("doubt",[76],[8])],
    [("if",[72],[1]),("no",[76],[1]),("one",[77],[2]),("comes",[76],[2]),("if",[72],[1]),("no",[76],[1]),("one",[77],[2]),("stays",[79],[6])],
    [("I'll",[77],[1]),("sing",[76],[1]),("to",[74],[2]),("you",[72],[2]),("all",[71],[1]),("of",[72],[1]),("my",[71],[2]),("days",[69],[6])],
]
CHORUS_TEXT = ["Oh, little light, don't go out,", "burn through the dark and the doubt.",
               "If no one comes, if no one stays,", "I'll sing to you all of my days."]
CHORUS_CHORDS = ["F","C","Dm","G", "Am","Dm","Am","E", "F","C","Dm","G", "Dm","Am","E","Am"]

# speakers -> (voice, speed, fx)
SPEAKERS = {
    "him":     ("am_michael", 0.92, "inner"),
    "him_out": ("am_michael", 0.95, "room"),
    "rage":    ("am_michael", 1.0, "inner_hot"),
    "demon":   ("am_michael", 0.85, "demon"),
    "christ":  ("am_michael", 0.84, "warm"),
    "her":     ("af_heart", 0.86, "room"),
    "v_george":("bm_george", 0.95, "echo"),
    "v_nicole":("af_nicole", 1.0, "echo"),
    "v_onyx":  ("am_onyx", 0.95, "echo"),
    "v_isab":  ("bf_isabella", 0.95, "echo"),
    "v_adam":  ("am_adam", 0.95, "echo"),
    "v_sky":   ("af_sky", 1.0, "echo"),
}
# speaker -> which face's mouth it drives
MOUTH = {"him_out":"him", "christ":"him", "her":"her", "rage":"him"}

PART1 = dict(
    name="part1", title="THE SONG IN THE STORM", subtitle="Part One — The Storm", dur=186.0,
    lines=[
        (11.5, "him", "Another double shift. Another notice taped to the door."),
        (18.0, "him", "Rent's up again. Groceries are up again. Everybody's tired. Everybody's scared."),
        (25.5, "him", "Keep your head down. Get home. Don't look at anything."),
        (77.0, "him", "How... how is she singing like that? Here?"),
        (90.0, "v_george", "Not my problem."),
        (92.4, "v_nicole", "There's a waitlist. Eighteen months."),
        (95.4, "v_onyx", "Should've worked harder."),
        (98.0, "v_isab", "If you help them, who's going to help you?"),
        (101.6, "v_adam", "Keep walking."),
        (103.6, "v_sky", "We just don't have the resources."),
        (113.0, "rage", "They let her freeze, and call it freedom."),
        (118.0, "rage", "They let her starve, and call it the market."),
        (123.0, "rage", "And they punish anyone who tries to help. So nobody does."),
        (133.0, "him", "And she still sings."),
        (137.0, "him", "How dare anything be this beautiful... in a world like this."),
        (145.0, "demon", "Let it burn. Let all of it burn."),
    ],
    song=[  # (start, kind, section)
        (44.0, "intro", None),
        (44.0 + 8*BEAT, "sing", "verse"),
        (44.0 + 8*BEAT + 64*BEAT, "sing", "chorus"),
    ],
    sfx=[],
)
P1_SONG_END = 44.0 + 8*BEAT + 128*BEAT

PART2 = dict(
    name="part2", title="THE SONG IN THE STORM", subtitle="Part Two — The Spark", dur=222.0,
    lines=[
        (14.0, "demon", "Nobody's coming. Nobody ever comes."),
        (21.0, "demon", "Why should I care... when no one ever cared?"),
        (27.5, "v_george", "Not my problem."),
        (28.6, "v_adam", "Keep walking."),
        (29.8, "v_onyx", "Should've worked harder."),
        (52.0, "him", "...What is that?"),
        (60.0, "him", "It's so small. Why does it feel so... warm?"),
        (73.0, "him", "They tried to put it out. The cold. The hunger. The 'not my problem'."),
        (82.0, "him", "And it's still here."),
        (87.5, "him", "It was always here. In her. In me."),
        (111.0, "her", "I'll go. I know. I'm not supposed to be in here."),
        (117.5, "christ", "No. Please. Don't stop singing."),
        (122.5, "christ", "You were never too much. You were never the problem."),
        (129.0, "her", "Nobody stops. Nobody ever stops."),
        (134.0, "christ", "I know. I'm sorry it took me so long."),
        (141.0, "christ", "Here. It's still warm. It's yours."),
        (146.5, "her", "...Thank you."),
    ],
    song=[
        (44.0, "hum", "chorus"),
        (152.0, "sing", "chorus"),
    ],
)
P2_REPRISE_END = 152.0 + 64*BEAT
