"""Screenplay for "The First Witness".

Each line: (id, speaker, text, pause_before_s, pause_after_s)
Markers inside text drive the score and are stripped for voice/subtitles:
  ^word  -> high, hopeful note lands on this word
  _word  -> low, heavy note lands on this word
"""

# speaker -> (kokoro voice, lang, speed)
VOICES = {
    "N":  ("af_heart",   "en-us", 0.93),   # narrator (the dreamer)
    "Z":  ("am_michael", "en-us", 0.86),   # the conscious zombie (pitched down + grit in post)
    "HA": ("bf_emma",    "en-gb", 0.95),   # human A, crew lead
    "HB": ("am_fenrir",  "en-us", 0.93),   # human B, the one who goes down the rope
}

# scene -> list of lines. Scene order is the film order.
SCENES = [
    ("open", [
        ("o1", "N", "Here's a conscious zombie story.", 0.9, 1.2),
    ]),
    ("horde", [
        ("h1", "N", "I had an idea the other day.", 0.5, 0.4),
        ("h2", "N", "I saw a zombie, and its brothers and sisters were zombies as well... and they were running towards the Fortress of Humanity.", 0.2, 0.5),
        ("h3", "N", "And Humanity was defending itself, tearing those zombies into _dust... to protect themselves from the scariness of the _mindless zombies.", 0.3, 0.9),
    ]),
    ("soul", [
        ("s1", "N", "But then I saw a ^soul descend from the ^heavens...", 0.6, 0.5),
        ("s2", "N", "and it fell into one of the zombies.", 0.2, 1.4),
    ]),
    ("wake", [
        ("w1", "N", "And that zombie started looking around...", 1.4, 0.8),
        ("w2", "Z", "I... I can ^see.", 0.3, 0.9),
        ("w3", "N", "and it froze in place.", 0.3, 1.0),
    ]),
    ("hands", [
        ("c1", "N", "It had control of itself.", 0.5, 0.6),
        ("c2", "Z", "These are... my hands.", 0.4, 0.9),
        ("c3", "N", "But it did not have control of what it could _witness... or what it could _feel.", 0.3, 1.0),
    ]),
    ("witness", [
        ("v1", "N", "Its brothers and sisters, who looked just like it, seemed compelled to run to the battlefield.", 0.4, 0.5),
        ("v2", "Z", "Wait... where are you going?", 0.3, 0.8),
        ("v3", "N", "It saw them being destroyed by the Fortress of Humanity. It saw their _suffering... even though they were not conscious.", 0.4, 0.7),
        ("v4", "N", "And then the _pain started. Because now it could feel their pain. All of their _pain.", 0.5, 0.6),
        ("v5", "Z", "It hurts... it all hurts.", 0.3, 0.8),
        ("v6", "N", "Now that this soul-infused zombie was conscious, it was a ^witness. A witness to the _suffering in the world.", 0.4, 1.0),
    ]),
    ("knees", [
        ("k1", "N", "And the conscious zombie thought it was _alone in its suffering. It fell to its knees, and it covered its face, to try to suppress the pain it had witnessed.", 0.5, 0.8),
        ("k2", "N", "It had no other consciousness to share that suffering with, as far as it knew. So maybe it was the only one giving the suffering around it ^meaning.", 0.4, 0.8),
        ("k3", "N", "Because before that body of flesh was conscious, the suffering had no meaning. But when a soul descended from ^heaven and created a witness... the suffering had ^meaning now.", 0.4, 0.9),
        ("k4", "Z", "Why... why was I picked to witness this? What does it _mean?", 0.4, 1.0),
        ("k5", "N", "What power is there to give meaning to suffering? To be on your knees, with _tears falling from your eyes, as you witness others who cannot share it with you... but you are giving their suffering meaning, by seeing their pain.", 0.4, 1.0),
    ]),
    ("sky", [
        ("y1", "Z", "Is anyone there?", 0.8, 2.0),
        ("y2", "N", "But there is no answer from the heavens. Because the heavens gave their answer when they sent the ^soul, and put it into a body of flesh.", 0.2, 0.6),
        ("y3", "N", "And now that body of flesh needs to find its own answer, to what the suffering means for it.", 0.3, 0.8),
        ("y4", "N", "Maybe heaven's answer and heaven's question were the same thing... your ^existence.", 0.4, 0.9),
        ("y5", "N", "And maybe, if they knew more, they would have already solved it. But your own ability to witness, on a deep level, might give you the details you need to ^help them.", 0.3, 0.8),
        ("y6", "N", "What if heaven sent the soul into a kind of _hell... not to take the highway towards hell, but to better know what to avoid?", 0.4, 0.6),
        ("y7", "N", "Because the staircase to ^heaven is not a simple staircase. It is built by transforming the suffering of hell into ^well-being and ^peace.", 0.3, 1.2),
    ]),
    ("building", [
        ("b1", "N", "And when the conscious zombie had cried all of the tears that it could... it looked around, and it saw a building.", 0.4, 0.6),
        ("b2", "Z", "I have to do something.", 0.3, 0.8),
        ("b3", "N", "It climbed a ladder to the top of the building...", 0.4, 0.9),
        ("b4", "N", "and there, it saw a ^flag.", 0.2, 0.9),
    ]),
    ("flag", [
        ("f1", "N", "It grabbed the flag and started waving it in the air, because it had to do something.", 0.3, 0.4),
        ("f2", "Z", "Stop! Please... stop!", 0.2, 0.7),
        ("f3", "N", "It couldn't watch all of its brothers and sisters die. The pain was _unbearable. The suffering was _unbearable.", 0.3, 1.0),
    ]),
    ("heli", [
        ("r1", "N", "And then, a human helicopter came flying over.", 0.5, 0.8),
        ("r2", "N", "A rope came down, and one of the humans dropped down the rope...", 0.3, 0.5),
        ("r3", "N", "grabbed the conscious zombie by the shirt, and pulled them up into the helicopter.", 0.2, 1.0),
    ]),
    ("cabin", [
        ("i1", "N", "The conscious zombie thought it was going to be shot... _killed, like the others.", 0.8, 1.0),
        ("i2", "N", "But then it saw that the humans were looking at it.", 0.6, 1.0),
        ("i3", "HA", "Who are you?", 0.4, 1.2),
        ("i4", "Z", "I don't know.", 0.3, 0.7),
        ("i5", "Z", "I am a zombie... I think.", 0.2, 2.4),
        ("i6", "HB", "We think you are ^conscious.", 0.3, 1.2),
        ("i7", "Z", "How can you tell?", 0.4, 2.4),
        ("i8", "HA", "Because you can feel the pain of your brothers and sisters...", 0.3, 0.3),
        ("i9", "HB", "and you can feel the weight of the world.", 0.2, 0.6),
        ("i10", "HA", "That's what humans feel. And we think you feel that too.", 0.3, 1.6),
        ("i11", "N", "And the conscious zombie nodded.", 0.3, 1.6),
    ]),
    ("end", [
        ("e1", "N", "Without _hell, which existed before heaven, heaven could not have been formed.", 0.6, 0.6),
        ("e2", "N", "And that is why heaven sent the soul... to turn hell into ^heaven.", 0.3, 3.0),
    ]),
]


def clean(text):
    """Strip score markers for voice + subtitles."""
    out = []
    for w in text.split(" "):
        out.append(w.lstrip("^_"))
    return " ".join(out)


def accents(text):
    """Return [(char_fraction, 'hi'|'lo')] for marked words."""
    res = []
    plain = clean(text)
    pos = 0
    for w in text.split(" "):
        word = w.lstrip("^_")
        idx = plain.find(word, pos)
        if w.startswith("^"):
            res.append(((idx + len(word) * 0.3) / max(1, len(plain)), "hi"))
        elif w.startswith("_"):
            res.append(((idx + len(word) * 0.3) / max(1, len(plain)), "lo"))
        pos = idx + len(word)
    return res
