"""Screenplay for "The First Witness".

Each line: (id, speaker, text, pause_before_s, pause_after_s[, options])
options: speed (override), ph (exact phonemes for the voice), silent (seconds, no audio),
         thought (shown in a thought bubble instead of a burned-in subtitle)
Markers inside text drive the score and are stripped for voice/subtitles:
  ^word  -> high, hopeful note lands on this word
  _word  -> low, heavy note lands on this word
"""

# speaker -> (kokoro voice, lang, speed)
VOICES = {
    "N":  ("af_heart",   "en-us", 0.744),  # narrator (the dreamer), 20% slower so every word lands
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
        ("w2", "Z", "Wait... I can ^see?", 0.3, 0.9),
        ("w3", "N", "and the conscious zombie froze in place.", 0.3, 1.0),
    ]),
    ("hands", [
        ("c1", "N", "The conscious zombie had control of itself.", 0.5, 0.6),
        ("c2", "Z", "These are... my hands.", 0.4, 0.9),
        ("c3", "N", "But the conscious zombie did not have control of what it could _witness... or what it could _feel.", 0.3, 1.0),
    ]),
    ("witness", [
        ("v1", "N", "The conscious zombie's brothers and sisters, who looked just like it, seemed compelled to run to the battlefield.", 0.4, 0.5),
        ("v2", "Z", "Wait... where are you going?", 0.3, 0.8),
        ("v3", "N", "The conscious zombie saw them being destroyed by the Fortress of Humanity. The conscious zombie saw their _suffering... even though they were not conscious.", 0.4, 0.7),
        ("v4", "N", "And then the _sorrow started, because now the conscious zombie could see the _suffering.", 0.5, 0.6),
        ("v5", "Z", "This hurts... this _loneliness... this destruction... it hurts.", 0.3, 0.8),
        ("v6", "N", "Now that this soul-infused zombie was conscious, it was a ^witness. A witness to the _suffering in its world.", 0.4, 1.0),
    ]),
    ("knees", [
        ("k1", "N", "And the conscious zombie thought it was _alone in its suffering. The conscious zombie fell to its knees, and it covered its face, to try to suppress the pain it was witnessing.", 0.5, 0.8),
        ("k2", "N", "The conscious zombie thought it had no other conscious beings to share the suffering with. So maybe the conscious zombie was the only one giving the suffering around it ^meaning.", 0.4, 0.8),
        ("k3", "N", "Because before his body of flesh was conscious, the suffering had no meaning. But when the soul destined for him descended from ^heaven and created a witness... their suffering gave it ^meaning by showing the conscious zombie their pain.", 0.4, 0.9),
        ("k4", "Z", "Why was I picked to witness all these things? What does it _mean?", 0.4, 1.0),
        ("k5", "N", "What is the power behind giving meaning to suffering? To be on your knees, with _tears falling from your eyes, as you witness others who cannot share it with you...", 0.4, 0.3),
        ("k5b", "N", "but you are giving their suffering meaning, through your reflection and contemplation on what maybe you can do to help yourself and others, with more ^flourishing and ^thriving, potentially.", 0.1, 1.0),
    ]),
    ("sky", [
        ("y1", "Z", "Is anyone there?", 0.8, 2.0),
        ("y2", "N", "But there is no answer from the heavens. Because the heavens gave their answer when they sent the ^soul, and put it into a body of flesh.", 0.2, 0.6),
        ("y3", "N", "And now that body of flesh is looking to find an answer to its _suffering.", 0.3, 0.8),
        ("y4", "N", "Maybe heaven's answer and heaven's question were the same thing... your ^existence could be the meaning needed to help guide you to create more plans and actions to guide your ^life.", 0.4, 0.9),
        ("y5", "N", "And maybe, if the world knew more, maybe the suffering would never have happened, because it would have been solved already. But your own ability to witness, on a deep level, might give you the details you need to ^help them.", 0.3, 0.8),
        ("y6", "N", "What if heaven sent the soul into a kind of _hell... not to keep going on the highway towards hell, but to better know what to avoid?", 0.4, 0.6),
        ("y7", "N", "Because the staircase to ^heaven is not a simple staircase. It is built by transforming the suffering of hell into ^well-being and ^peace, towards the Kingdom of ^Heaven.", 0.3, 1.2),
    ]),
    ("building", [
        ("b1", "N", "And when the conscious zombie had cried all of the tears that it could... the conscious zombie looked around, and it saw a building.", 0.4, 2.3),
        ("b2", "Z", "I have to do something.", 0.3, 0.8),
        ("b3", "N", "The conscious zombie climbed a ladder to the top of the building...", 0.4, 0.9),
        ("b4", "N", "and there, the conscious zombie saw a ^flag.", 0.2, 0.9),
    ]),
    ("flag", [
        ("f1", "N", "The conscious zombie grabbed the flag and started waving it in the air, because it had to do something.", 0.3, 0.4),
        ("f2", "Z", "Stop! Please... stop hurting them!", 0.2, 0.7),
        ("f3", "N", "The conscious zombie couldn't watch all of its brothers and sisters die. The pain was _unbearable. Seeing their pain was _unbearable.", 0.3, 1.0),
    ]),
    ("heli", [
        ("r1", "N", "And then, a human helicopter came flying over.", 0.5, 0.8),
        ("r2", "N", "A rope came down, and one of the humans dropped down the rope...", 0.3, 0.5),
        ("r2a", "HB", "Hey, zombie guy... are you... dangerous?", 0.3, 0.7, {"speed": 0.78}),
        ("r2d", "Z", "Uhmmm... n-no?", 0.3, 1.5, {"ph": "ˈʌːmmm... nə... nˈoʊ?", "speed": 0.72}),
        ("r2b", "HB", "Okay, well then, bud... you're coming with me.", 0.2, 0.25, {"speed": 0.8}),
        ("r2c", "Z", "Wait... what?", 0.1, 0.9),
        ("r3", "N", "The human grabbed the conscious zombie by the shirt, and pulled them up into the helicopter.", 0.2, 1.0),
    ]),
    ("cabin", [
        ("i1", "N", "The conscious zombie thought it was going to be shot... _killed, like the others.", 0.8, 1.0),
        ("i2", "N", "But then the conscious zombie saw that the humans were looking at it.", 0.6, 1.0),
        ("i3", "HA", "Who are you?", 0.4, 1.2),
        ("i4", "Z", "I don't really know...", 0.3, 0.6),
        ("i5", "Z", "but I'm pretty sure I'm a zombie, though.", 0.2, 1.5),
        ("i6", "HB", "That's great...", 0.3, 0.6),
        ("i6b", "HB", "but I also think you are ^conscious, my guy.", 0.2, 1.2),
        ("i7", "Z", "Oh really? How can you tell?", 0.4, 2.4),
        ("i8", "HA", "We saw that it looks like you are able to feel the _pain of your brothers and sisters... symbolized by you waving that flag out there, and having those waterworks as well.", 0.3, 2.6),
        ("i9", "HB", "which means you are feeling, in some kind of way, the _weight of the world that we are currently living in.", 0.2, 0.6),
        ("i10", "HA", "The pain of the world... that's kind of like what humans feel a lot of the time. The pain of _loss, and the pain of losing those that maybe you care for, in some kind of way.", 0.3, 0.8),
        ("i10b", "Z", "You're right. I want to see if I can help ^save them.", 0.3, 2.6),
        ("i11", "N", "And the conscious zombie sighed.", 0.3, 0.9),
        ("i11t", "Z", "How are the humans going to help me? I hope this works out...", 0.3, 0.3, {"silent": 3.8, "thought": True}),
        ("i11b", "HB", "Oh yeah, I hope this works out too.", 0.2, 1.6, {"speed": 0.88}),
    ]),
    ("end", [
        ("e1", "N", "So it seems like, in order for heaven to be built, the raw material of _hell may have been needed... to be transformed into the material of ^heaven... so that maybe this heaven could be built not only for him, but for his brothers and sisters, and maybe even the ^world too.", 0.6, 0.6),
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
