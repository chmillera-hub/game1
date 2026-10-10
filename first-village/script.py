"""The First Village: beat sheet.

Every spoken line, pause and scene marker, in order. make_voices.py turns this
into audio clips and build/timeline.json, which both the mixer and the renderer
read, so the picture is always timed to the actual voice performance.
"""

# speaker -> (kokoro voice or blend, speed, caption style)
VOICES = {
    "narrator": ("af_heart", 0.94, "narration"),
    "moses":    ("am_michael", 0.86, "dialogue"),
    "moses_w":  ("am_michael", 0.86, "dialogue"),   # the prayer: his plain, steady voice
    "elder":    ("bm_george", 0.93, "dialogue"),
    "potter":   ("am_puck", 0.95, "dialogue"),
    "fear":     ("am_fenrir", 0.82, "fear"),
    "god":      ("am_onyx", 0.82, "god"),           # low, booming, comforting
}


def L(id, speaker, text, gap=0.5, caption=None, speed=None):
    return {"kind": "line", "id": id, "speaker": speaker, "text": text,
            "gap": gap, "caption": caption, "speed": speed}


def Gap(sec):
    return {"kind": "gap", "dur": sec}


def Mark(id):
    return {"kind": "mark", "id": id}


def Sfx(id, dur, gap=0.0):
    """A non-speech beat that occupies time (e.g. the shared sigh)."""
    return {"kind": "sfx", "id": id, "dur": dur, "gap": gap}


SEQ = [
    Mark("opening"),
    Gap(4.2),                                        # title over the dawn desert
    L("n1", "narrator", "The dust of the wilderness still clung to Moses's cloak. "
                        "But the fire of the Lord was a furnace in his heart.", 0.7),
    L("g0", "god", "I will be with you, Moses.", 0.8),
    L("n2", "narrator", "Those words still echoed in his soul. A promise that felt more real "
                        "than the hard-packed earth beneath his sandals.", 1.0),

    Mark("village"),
    Gap(0.6),
    L("n3", "narrator", "The village was a place of straight lines, and rigid customs.", 0.5),
    L("n3b", "narrator", "At its center, a stone-faced Elder spoke to a small crowd. His voice, "
                         "a hammer, shaping the air into hard certainties.", 0.5),
    Mark("elder1"),
    L("e1a", "elder", "The wanderers in the desert are as beasts.", 0.45),
    L("e1b", "elder", "They have no laws. No walls. Their souls are as barren as the rock "
                      "they sleep on.", 0.45),
    L("e1c", "elder", "We are secure here because we are not like them. We are orderly. "
                      "We are clean.", 0.9),

    Mark("fear"),
    L("n4", "narrator", "Moses felt the old fear rise. The familiar ghost, whispering.", 0.3),
    L("f1", "fear", "They will not believe you.", 0.25),
    L("f2", "fear", "You are slow of speech.", 0.9),
    L("n5", "narrator", "But the fire in his heart was hotter than the fear. He stepped forward.", 0.6),
    L("n5b", "narrator", "He did not argue about the wanderers. He spoke of the terror, and the "
                         "glory, of being seen by God.", 0.7),

    Mark("speech"),
    Sfx("cough", 1.25, 0.3),
    L("m0", "moses", "Some...", 0.45, caption="Some—"),
    L("m1", "moses", "Sometimes, a truth lands in your heart that is too big for your mouth.", 0.7),
    L("m2", "moses", "You fear that when you speak it, the world will call you a liar.", 0.6),
    L("m3", "moses", "You fear your own tongue is too slow... too clumsy, to carry its weight.", 0.9),
    L("m4", "moses", "You feel like a cracked vessel. Unworthy of the water it's meant to hold.", 0.9),
    L("m5", "moses", "But what if the cracks are how the light gets in?", 1.2),
    L("m6", "moses", "What happens if the voice that wavers, is the one speaking the truest note?", 1.0),
    L("m7", "moses", "When I told the Lord I was slow of speech, He said to me: "
                     "I will be with your mouth.", 1.0),

    Mark("elder2"),
    L("n6", "narrator", "The Elder's face tightened. Moses had not attacked his words. But he had "
                        "offered a truth that made the Elder's own truth feel small. And brittle.", 0.4),
    L("e2a", "elder", "This man is unhinged. He speaks in riddles to confuse the simple.", 0.35),
    L("e2b", "elder", "He is disruptive. Look at him.", 0.45),
    L("e2c", "elder", "Go away, bro. You're creeping us out.", 0.6),

    Mark("expel"),
    L("n7", "narrator", "There was no struggle. He was led past the stunned faces of the villagers, "
                        "through the gate he had just entered, and thrown to the ground.", 0.4),
    Sfx("throw", 2.6),

    Mark("alone"),
    L("n8", "narrator", "And there he was. Moses. The man who had spoken with God. On his knees in "
                        "the dirt, with the taste of dust and humiliation in his mouth.", 0.5),
    L("n8b", "narrator", "The divine fire felt like a cruel joke. A distant, dying ember.", 1.0),
    L("mp1", "moses_w", "Is this it, Lord?", 0.8),
    L("mp2", "moses_w", "Is this what I'm supposed to do?", 0.9),
    L("mp3", "moses_w", "You promised you would be with me... and I spoke... and I was exiled.", 1.0),
    L("mp4", "moses_w", "Is this what you wanted for me?", 1.6),
    L("n9", "narrator", "The world was silent.", 3.2),
    L("n9b", "narrator", "He felt utterly, completely alone.", 2.4),

    Mark("presence"),
    L("n10", "narrator", "And then... it came.", 0.8),
    L("n10b", "narrator", "Not a shout from the sky. Not a sign. A presence. A warmth that settled "
                          "over his shaking shoulders, like a heavy, comforting hand.", 0.6),
    L("n10c", "narrator", "And in the deepest part of his soul, a sound that was not a sound. "
                          "A whisper, like the turning of stars.", 0.8),
    L("g1", "god", "Moses...", 0.8),
    L("g1b", "god", "Moses...", 1.5),
    L("n11", "narrator", "It did not offer answers. It did not promise victory. It simply said...", 0.5),
    L("g2", "god", "I see you", 2.0, caption="I see you.", speed=0.76),
    L("n12", "narrator", "And as Moses knelt there, it was as if the universe itself was kneeling "
                         "beside him.", 0.6),
    L("n12b", "narrator", "Together, the man covered in dirt, and the Lord of his emotions, let out "
                          "a single, shared, weary sigh.", 0.2),
    Sfx("sigh", 3.6, 1.0),

    Mark("village2"),
    L("n13", "narrator", "Moses could not see it. But back inside the village, a weaver had stopped "
                         "her work. She looked at the potter, who was staring at the closed gate.", 0.6),
    L("p1", "potter", "He... he was just talking about being afraid.", 0.4),
    L("p2", "potter", "He was talking about what God means to him...", 0.5),
    L("p3", "potter", "Why did the Elder throw him out for talking about the Lord?", 1.3),
    L("n14", "narrator", "The weaver had no answer. But for the first time in years, the straight "
                         "lines of the village felt like a cage.", 1.0),
    L("n14b", "narrator", "The seed was planted.", 1.6),
    L("n14c", "narrator", "The miracle had begun.", 5.0),
    Mark("end"),
]
