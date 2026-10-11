"""THE KEYHOLE - screenplay as data.

Line text mini-syntax:
  [p0.6]   pause of 0.6 s (separate TTS chunks on either side)
  [B:word] bleeped word: the word is spoken for mouth timing, audio replaced by a bleep
Event tuples:
  ("say", who, text, opts)     blocking dialogue / narration
  ("wait", secs)               beat of silence (animation happens here)
  ("mark", name)               named time marker
  ("sfx", name, opts)          non-blocking sound effect at current time
  ("laugh", who, kind, opts)   laugh audio; blocking unless opts['block'] is False
  ("music", cue)               start a music cue at current time
"""

# speaker -> (kokoro voice or blend, default speed)
VOICES = {
    "narr":    ("af_heart", 0.86),
    "me":      ("af_heart", 0.88),
    "danny":   ({"am_michael": 0.7, "am_onyx": 0.3}, 0.88),
    "teacher": ("bm_george", 0.80),
    "emb":     ("af_bella", 1.0),
    "doubt":   ("bf_emma", 0.86),
    "anger":   ("am_onyx", 0.84),
    "bored":   ("am_puck", 0.84),
}

SHOTS = [
    # ---------------- SCENE 1: CLASSROOM ----------------
    ("class_kids_wide", [
        ("music", "clock"),
        ("wait", 1.6),
        ("mark", "teacher_call"),
        ("say", "teacher", "Eyes forward, everyone.", {}),
        ("wait", 0.5),
    ]),
    ("class_teacher", [
        ("wait", 0.5),
        ("mark", "not_one_sound"),
        ("say", "teacher", "Not.[p0.55]One.[p0.6]Sound.", {"speed": 0.74}),
        ("wait", 0.9),
    ]),
    ("class_kids_close", [
        ("wait", 0.6),
        ("mark", "glance1"),
        ("wait", 1.1),
        ("mark", "glance2"),
        ("wait", 0.9),
        ("mark", "eye_contact"),
        ("wait", 0.5),
        ("say", "narr", "You know that moment.", {}),
        ("wait", 0.5),
        ("mark", "puff_start"),
        ("say", "narr", "Someone tells you not to laugh...", {}),
        ("wait", 0.35),
        ("say", "narr", "and you look at the one person you love most in the room.", {}),
        ("wait", 0.5),
        ("mark", "snort"),
        ("sfx", "snort", {}),
        ("wait", 0.45),
        ("mark", "burst"),
        ("sfx", "kid_laughs", {}),
        ("music", "burst"),
        ("wait", 2.4),
    ]),
    ("class_teacher_react", [
        ("wait", 0.4),
        ("say", "narr", "If my mom had walked in right then, I'd have just hugged her.", {}),
        ("wait", 0.4),
        ("say", "narr", "No one laughs at that. It's allowed.", {}),
        ("wait", 0.6),
    ]),
    ("class_kids_after", [
        ("wait", 0.3),
        ("say", "narr", "But a friend? In class? There's a rule.", {}),
        ("wait", 0.45),
        ("say", "narr", "So the love has to find another way out.", {}),
        ("wait", 0.5),
        ("mark", "peek_again"),
        ("sfx", "kid_giggle", {}),
        ("wait", 0.9),
        ("say", "narr", "Maybe that's what a laugh is.[p0.5]It's love...[p0.35]squeezing through a keyhole.", {}),
        ("wait", 1.2),
        ("mark", "keyhole_wipe"),
        ("sfx", "whoosh", {}),
        ("wait", 0.9),
    ]),
    # ---------------- SCENE 2: BACKYARD ----------------
    ("yard_wide", [
        ("music", "yard"),
        ("wait", 0.5),
        ("say", "narr", "Twenty years later, that kid is still my best friend.[p0.3]Danny.", {}),
        ("wait", 0.4),
        ("say", "narr", "Two tours overseas.[p0.35]He still talks like he never left.", {}),
        ("wait", 0.4),
    ]),
    ("yard_danny", [
        ("wait", 0.3),
        ("mark", "flip"),
        ("sfx", "sizzle_flip", {}),
        ("wait", 0.6),
        ("say", "danny", "You burned the buns again.", {}),
        ("wait", 0.35),
        ("mark", "point"),
        ("say", "danny", "You're a piece of [B:shit], you know that?", {}),
        ("wait", 0.5),
    ]),
    ("yard_table", [
        ("sfx", "friends_chuckle", {}),
        ("wait", 0.4),
        ("say", "narr", "That's the game.[p0.3]He swings, I swing back, bigger and sillier.", {}),
        ("wait", 0.3),
        ("say", "narr", "The exaggeration is how everyone knows it's a joke.", {}),
        ("wait", 0.4),
    ]),
    ("yard_me_close", [
        ("music", "yard_fade"),
        ("wait", 0.3),
        ("say", "narr", "But that night, I was tired...[p0.4]and I forgot to exaggerate.", {}),
        ("wait", 0.8),
        ("mark", "confess"),
        ("say", "me", "Yeah.[p0.55]I guess I am.", {"speed": 0.8}),
        ("wait", 0.6),
    ]),
    ("yard_silence", [
        ("music", "silence"),
        ("sfx", "crickets_short", {}),
        ("mark", "silence"),
        ("wait", 3.4),
    ]),
    ("yard_danny_close", [
        ("wait", 0.4),
        ("say", "narr", "Dead silence.", {}),
        ("wait", 0.5),
        ("say", "narr", "Take the exaggeration out of a joke...[p0.4]and all that's left is the truth.", {}),
        ("wait", 0.7),
    ]),
    # ---------------- SCENE 3: MIND BRIDGE ----------------
    ("bridge_wide", [
        ("music", "bridge"),
        ("sfx", "alarm", {}),
        ("wait", 0.4),
        ("say", "emb", "Oh my God.[p0.15]Oh my God.[p0.15]Oh my God!", {"speed": 1.05}),
        ("wait", 0.3),
        ("say", "emb", "Three people saw that![p0.25]That's, like, triple!", {"speed": 1.0}),
        ("wait", 0.4),
    ]),
    ("bridge_doubt", [
        ("wait", 0.5),
        ("say", "doubt", "Well.[p0.6]That landed.", {}),
        ("wait", 0.6),
    ]),
    ("bridge_anger", [
        ("wait", 0.3),
        ("sfx", "knuckles", {}),
        ("wait", 0.5),
        ("say", "anger", "Want me to handle it?", {}),
        ("wait", 0.5),
    ]),
    ("bridge_bored", [
        ("wait", 0.7),
        ("say", "bored", "Nope.[p0.6]Flip it.", {}),
        ("wait", 0.8),
    ]),
    # ---------------- SCENE 4: ALCHEMY ----------------
    ("yard_me_flip", [
        ("music", "flip"),
        ("wait", 1.2),
        ("say", "me", "I mean...[p0.3]I am a piece of [B:shit].", {}),
        ("wait", 0.5),
        ("mark", "gesture_all"),
        ("say", "me", "But I'm a piece of [B:shit] with you pieces of [B:shit].", {}),
        ("wait", 0.35),
        ("say", "me", "On a [B:shit] planet,[p0.15]in a [B:shit] universe...", {}),
        ("wait", 0.45),
        ("mark", "best_pile"),
        ("say", "me", "and honestly?[p0.4]Best [B:shit] pile I've ever been in.", {}),
        ("wait", 0.5),
    ]),
    ("yard_laugh", [
        ("mark", "friend_snort"),
        ("sfx", "snort_adult", {}),
        ("wait", 0.5),
        ("mark", "all_laugh"),
        ("music", "yard_bright"),
        ("sfx", "group_laugh", {}),
        ("wait", 1.6),
        ("say", "danny", "Oh, you're a poet!", {"speed": 0.95}),
        ("wait", 0.6),
        ("say", "narr", "Same words.[p0.3]I just flipped them up instead of down...[p0.3]and took everybody with me.", {}),
        ("wait", 0.8),
    ]),
    # ---------------- SCENE 5: PORCH ----------------
    ("porch_wide", [
        ("music", "porch"),
        ("sfx", "crickets_long", {}),
        ("wait", 2.2),
        ("say", "me", "Hey.[p0.6]Can I say something real?", {"speed": 0.84}),
        ("wait", 0.4),
    ]),
    ("porch_danny1", [
        ("wait", 0.8),
        ("say", "danny", "Go ahead.", {"speed": 0.82}),
        ("wait", 0.5),
    ]),
    ("porch_me1", [
        ("wait", 0.3),
        ("say", "me", "That one stung tonight.", {"speed": 0.84}),
        ("wait", 0.4),
        ("say", "me", "I flipped it because I didn't want it to.[p0.6]But it did.", {"speed": 0.84}),
        ("wait", 0.6),
    ]),
    ("porch_danny2", [
        ("wait", 0.7),
        ("say", "danny", "It's just how we talk.", {"speed": 0.86}),
        ("wait", 0.6),
    ]),
    ("porch_me2", [
        ("wait", 0.3),
        ("say", "me", "I know.[p0.5]Over there...[p0.3]it probably kept you alive.", {"speed": 0.84}),
        ("wait", 0.8),
    ]),
    ("porch_danny3", [
        ("wait", 1.3),
        ("say", "danny", "Over there, if you didn't laugh at it...[p0.45]you had to feel it.", {"speed": 0.82}),
        ("wait", 0.7),
    ]),
    ("porch_me3", [
        ("wait", 0.3),
        ("say", "me", "And here?", {"speed": 0.84}),
        ("wait", 0.6),
    ]),
    ("porch_danny4", [
        ("wait", 1.6),
        ("say", "danny", "Here...[p0.6]I still don't know how to stop.", {"speed": 0.8}),
        ("wait", 1.0),
    ]),
    # ---------------- SCENE 6: FORTRESS ----------------
    ("fort_hall", [
        ("music", "fortress"),
        ("wait", 0.5),
        ("say", "narr", "I used to joke that people lock up their anger...[p0.3]and I'd glance at Danny.", {}),
        ("wait", 0.5),
        ("say", "narr", "But it was never his anger that was locked up.[p0.4]Anger was the guard.", {}),
        ("wait", 0.4),
    ]),
    ("fort_cell", [
        ("wait", 0.4),
        ("say", "narr", "What he was guarding was...[p0.45]guilt.", {}),
        ("wait", 1.0),
    ]),
    ("fort_open", [
        ("sfx", "echo_laugh", {}),
        ("mark", "echo"),
        ("wait", 1.8),
        ("mark", "door_open"),
        ("sfx", "door_creak", {}),
        ("music", "fortress_warm"),
        ("wait", 0.8),
        ("say", "narr", "Humor is a back door.", {}),
        ("wait", 0.4),
        ("say", "narr", "And I think evolution only hands the key to people who won't hurt what's inside.", {}),
        ("wait", 0.9),
    ]),
    # ---------------- SCENE 7: PORCH RESOLUTION ----------------
    ("porch_two", [
        ("music", "porch2"),
        ("wait", 0.4),
        ("mark", "hand_shoulder"),
        ("wait", 0.8),
        ("say", "me", "You don't have to stop tonight.", {"speed": 0.84}),
        ("wait", 0.35),
        ("say", "me", "Just...[p0.3]don't aim it at me when it's real. Deal?", {"speed": 0.84}),
        ("wait", 0.5),
    ]),
    ("porch_danny5", [
        ("wait", 1.2),
        ("say", "danny", "Okay. Deal.", {"speed": 0.8}),
        ("wait", 0.9),
        ("mark", "smirk"),
        ("sfx", "sniff", {}),
        ("wait", 0.5),
        ("say", "danny", "You're still a piece of [B:shit], you know.", {"speed": 0.86}),
        ("wait", 0.5),
    ]),
    ("porch_me4", [
        ("wait", 0.3),
        ("say", "me", "I know.[p0.5]I'm your piece of [B:shit].", {"speed": 0.84}),
        ("wait", 0.4),
    ]),
    ("porch_two_laugh", [
        ("sfx", "soft_laughs", {}),
        ("mark", "soft_laugh"),
        ("wait", 3.0),
    ]),
    # ---------------- SCENE 8: ENDING ----------------
    ("sky", [
        ("music", "ending"),
        ("wait", 0.6),
        ("say", "narr", "Too little, and a joke misses.[p0.4]Too much...[p0.3]and it's too real.", {}),
        ("wait", 0.6),
        ("say", "narr", "But right in the middle, there's a keyhole.", {}),
        ("wait", 0.6),
        ("say", "narr", "And for one second...[p0.4]everyone gets to come home.", {}),
        ("wait", 1.2),
    ]),
    ("title_end", [
        ("mark", "title_start"),
        ("wait", 3.6),
    ]),
]
