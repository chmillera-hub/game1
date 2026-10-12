"""Screenplay for "The Bread of Life" (John 6).

Built around the four passages supplied (John 6:26-27, 32-35, 43-45, 51-58),
keeping the requested wording ("not society", "the disciples"), with short
scripture-based bridges so the scene plays as a conversation:
  6:24-25 (the crowd finds him), 6:28-31 (works / sign / manna),
  6:41-42 (the grumbling that "Stop grumbling" answers), 6:60, 6:66-69 (coda).

Each line is a list of segments. A segment is one TTS utterance and is
followed by `pause` seconds of silence. Inside a segment, "/" marks where the
subtitle should break (the voice is not interrupted there).

`gap` is the silence before the line starts (room for reaction beats).
"""

# Voice casting. Values are Kokoro voice ids or {voice: weight} blends.
# `rate` scales a speaker's whole delivery: every segment's speed, and the pauses between
# segments inside a line (gaps between lines, which hold the reactions, are not scaled).
VOICES = {
    "NARRATOR": {"voice": "bm_george", "lang": "en-gb", "speed": 0.86},
    "JESUS": {"voice": "am_michael", "lang": "en-us", "speed": 0.72, "rate": 1.2},
    "PETER": {"voice": {"am_fenrir": 0.5, "am_onyx": 0.5}, "lang": "en-us", "speed": 0.78},
    "ELI": {"voice": {"am_puck": 0.55, "bm_george": 0.45}, "lang": "en-us", "speed": 0.84},
    "MIRIAM": {"voice": "af_heart", "lang": "en-us", "speed": 0.84},
    "MAN2": {"voice": "am_eric", "lang": "en-us", "speed": 0.98},
}

SPEAKER_NAMES = {
    "NARRATOR": "",
    "JESUS": "Jesus",
    "PETER": "Peter",
    "ELI": "Eli",
    "MIRIAM": "Miriam",
    "MAN2": "",
}


def L(id, speaker, segments, gap=0.6, **kw):
    segs = []
    for s in segments:
        if isinstance(s, str):
            segs.append({"text": s, "pause": 0.25})
        else:
            text, pause = s[0], s[1]
            extra = s[2] if len(s) > 2 else {}
            segs.append({"text": text, "pause": pause, **extra})
    return {"id": id, "speaker": speaker, "segments": segs, "gap": gap, **kw}


SCENES = [
    # ------------------------------------------------------------------
    {
        "id": "shore",
        "title": "Capernaum shore, morning",
        "lines": [
            L("L01", "NARRATOR", [
                ("The day after Jesus fed five thousand people / with five small loaves and two fish...", 0.35),
                ("the crowd went looking for him.", 0.5),
            ], gap=2.2),
            L("L02", "NARRATOR", [
                ("They crossed the Sea of Galilee, / and found him on the shore at Capernaum.", 0.3),
            ], gap=0.5),
            L("L03", "ELI", [
                ("Rabbi!", 0.45),
                ("When did you get here?", 0.45),
                ("We watched every boat come ashore... / and you were not on any of them.", 0.45),
                ("Yet here you are! / How is that possible?", 0.2),
            ], gap=1.6),
            L("L03b", "JESUS", [
                ("I am here...", 0.5, {"speed": 0.66}),
                ("because my Father has willed it.", 0.6, {"speed": 0.68}),
                ("He has sent me to tell you something important...", 0.35),
                ("and that is why I stand before you.", 0.2),
            ], gap=2.6),
            L("L04", "JESUS", [
                ("Very truly I tell you, / you are looking for me,", 0.3),
                ("not because you saw the signs I performed,", 0.25),
                ("but because you ate the loaves / and had your fill.", 0.3),
            ], gap=1.9),
            L("L05", "JESUS", [
                ("Do not work for food that spoils,", 0.45),
                ("but for food that endures to eternal life,", 0.3),
                ("which the Son of Man will give you.", 0.35),
            ], gap=1.4),
            L("L06", "JESUS", [
                ("For on him, / God the Father has placed his seal of approval.", 0.2),
            ], gap=0.3),
            L("L07", "PETER", [
                ("Then what must we do...", 0.3),
                ("to do the works God requires?", 0.2),
            ], gap=1.3),
            L("L08", "JESUS", [
                ("The work of God is this:", 0.3),
                ("to believe in the one he has sent,", 0.3),
                ("so that we may glorify Him, / and the Son.", 0.2),
            ], gap=0.9),
            L("L09", "ELI", [
                ("Then what sign will you give us, / so that we may see it and believe you?", 0.4),
                ("Our ancestors ate the manna in the wilderness.", 0.25),
                ("As it is written: / 'He blessed them with bread from heaven to eat.'", 0.2),
            ], gap=1.0),
            L("L10", "JESUS", [
                ("Very truly I tell you,", 0.25),
                ("it is not society who has given you / the bread from heaven,", 0.3),
                ("but it is my Father / who gives you the true bread from heaven.", 0.35),
            ], gap=1.4),
            L("L11", "JESUS", [
                ("For the bread of God is the bread / that comes down from heaven,", 0.15),
                ("and gives life to the world.", 0.2),
            ], gap=0.5),
            L("L12", "MIRIAM", [
                ("Sir...", 0.7, {"speed": 0.78}),
                ("how do we get this bread?", 0.2),
            ], gap=1.8),
            L("L13", "JESUS", [
                ("I am the bread of life.", 0.7, {"speed": 0.60}),
            ], gap=2.0),
            L("L14", "JESUS", [
                ("Whoever comes to me / will never go hungry,", 0.45),
                ("and whoever believes in me / will never be thirsty.", 0.2),
            ], gap=0.4),
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "synagogue",
        "title": "Synagogue at Capernaum",
        "lines": [
            L("L15", "NARRATOR", [
                ("Later, as he taught in the synagogue at Capernaum, / a murmur spread among his followers.", 0.3),
            ], gap=3.2),
            L("L16", "ELI", [
                ("Isn't this Jesus, the son of Joseph?", 0.25),
            ], gap=0.8),
            L("L17", "MAN2", [
                ("We know his father and mother!", 0.2),
            ], gap=0.15),
            L("L18", "ELI", [
                ("How can he now say, / 'I came down from heaven'?", 0.2),
            ], gap=0.25),
            L("L19", "JESUS", [
                ("Stop grumbling among yourselves.", 0.2),
            ], gap=1.5),
            L("L20", "JESUS", [
                ("No one can come to me / unless the Father who sent me draws them,", 0.3),
                ("and I will raise them up at the last day.", 0.2),
            ], gap=1.1),
            L("L21", "JESUS", [
                ("It is written in the Prophets:", 0.25),
                ("'They will all be taught by God.'", 0.45),
                ("Everyone who has heard the Father / and learned from him / comes to me.", 0.2),
            ], gap=0.7),
            L("L22", "JESUS", [
                ("I am the living bread / that came down from heaven.", 0.55, {"speed": 0.64}),
                ("Whoever eats this bread will live forever.", 0.2, {"speed": 0.66}),
            ], gap=1.8),
            L("L23", "JESUS", [
                ("This bread is my flesh...", 0.55),
                ("which I will give for the life of the world.", 0.2),
            ], gap=1.0),
            L("L24", "ELI", [
                ("His flesh?", 0.35),
                ("How can this man give us his flesh to eat?", 0.2),
            ], gap=1.4),
            L("L25", "JESUS", [
                ("Very truly I tell you,", 0.3),
                ("unless you eat the flesh of the Son of Man / and drink his blood,", 0.3),
                ("you have no life in you.", 0.2),
            ], gap=3.4),
            L("L26", "JESUS", [
                ("Whoever eats my flesh and drinks my blood / has eternal life,", 0.3),
                ("and I will raise them up at the last day.", 0.4),
            ], gap=3.6),
            L("L27", "JESUS", [
                ("For my flesh is real food, / and my blood is real drink.", 0.2),
            ], gap=0.4),
            L("L28", "JESUS", [
                ("Whoever eats my flesh and drinks my blood / remains in me...", 0.55),
                ("and I in them.", 0.2, {"speed": 0.62}),
            ], gap=1.2),
            L("L29", "JESUS", [
                ("Just as the living Father sent me, / and I live because of the Father,", 0.3),
                ("so the one who feeds on me / will live because of me.", 0.2),
            ], gap=0.9),
            L("L30", "JESUS", [
                ("This is the bread that came down from heaven.", 0.45),
                ("Your ancestors ate manna, and died...", 0.6),
                ("but whoever feeds on this bread / will live forever.", 0.2, {"speed": 0.64}),
            ], gap=1.1),
        ],
    },
    # ------------------------------------------------------------------
    {
        "id": "dusk",
        "title": "Shore at sunset",
        "lines": [
            L("L31", "NARRATOR", [
                ("On hearing it, many of his disciples said...", 0.2),
            ], gap=3.4),
            L("L32", "ELI", [
                ("This is a hard teaching.", 0.45, {"speed": 0.74}),
                ("Who can accept it?", 0.2, {"speed": 0.74}),
            ], gap=0.5),
            L("L33", "NARRATOR", [
                ("From that time, many of his disciples turned back...", 0.35),
                ("and no longer followed him.", 0.2),
            ], gap=1.6),
            L("L34", "JESUS", [
                ("You do not want to leave too,", 0.45, {"speed": 0.64}),
                ("do you?", 0.2, {"speed": 0.64}),
            ], gap=4.2),
            L("L35", "PETER", [
                ("Lord...", 0.7, {"speed": 0.66}),
                ("to whom shall we go?", 0.45),
                ("You have the words of eternal life.", 0.2),
            ], gap=1.8),
            L("L36", "PETER", [
                ("We have come to believe, / and to know,", 0.35),
                ("that you are the Holy One of God.", 0.2, {"speed": 0.68}),
            ], gap=0.8),
            L("L37", "JESUS", [
                ("Father...", 0.6, {"speed": 0.62}),
                ("I am giving them what you sent me to give.", 0.45, {"speed": 0.66}),
                ("In your holy name, / I glorify you.", 0.5, {"speed": 0.66}),
                ("And even if they leave me...", 0.45, {"speed": 0.64}),
                ("I believe they have left / with a part of me in them.", 0.2, {"speed": 0.64}),
            ], gap=5.6),
        ],
        "tail": 5.0,  # closing image after the last line
    },
]

# Background crowd chatter (walla) under the argument in the synagogue.
WALLA = [
    ("am_echo", "What is he saying?"),
    ("am_liam", "Eat his flesh?"),
    ("bm_daniel", "This is madness."),
    ("af_nicole", "His blood? What does he mean?"),
    ("am_onyx", "Who does he think he is?"),
    ("bm_lewis", "We cannot eat a man!"),
    ("af_sarah", "Let him speak!"),
    ("am_adam", "Did you hear that?"),
]


def all_lines():
    for sc in SCENES:
        for ln in sc["lines"]:
            yield sc["id"], ln
