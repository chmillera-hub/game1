"""Screenplay for "Kingdom of Heaven, Inc." as data.

Each entry is either a spoken line or a silent beat. The timeline builder
lays them end to end (with the given pauses) so every visual cue can be
anchored to a line id instead of a hard-coded timestamp.
"""

# voice id -> (piper model, speaker id, length_scale, noise_scale, noise_w)
VOICES = {
    "NARR":  ("en_US-ryan-high", None, 1.02, 0.60, 0.85),
    "CEO":   ("en_US-norman-medium", None, 0.98, 0.667, 0.8),
    "CFO":   ("en_US-lessac-high", None, 0.97, 0.60, 0.8),
    "TYLER": ("en_US-bryce-medium", None, 0.90, 0.75, 0.9),
    "JESUS": ("en_GB-alan-medium", None, 1.12, 0.55, 0.7),
    "PAM":   ("en_US-hfc_female-medium", None, 1.02, 0.667, 0.8),
    "C1":    ("en_US-joe-medium", None, 0.92, 0.7, 0.9),
    "C2":    ("en_US-kristin-medium", None, 0.95, 0.7, 0.9),
    "C3":    ("en_US-libritts_r-medium", 20, 0.95, 0.7, 0.9),
    "C4":    ("en_GB-northern_english_male-medium", None, 1.0, 0.7, 0.9),
}

# Speaker display names / caption colors
SPEAKERS = {
    "NARR":  ("", (255, 255, 255)),
    "CEO":   ("CEO", (255, 196, 92)),
    "CFO":   ("CFO", (140, 210, 255)),
    "TYLER": ("HEAD OF GROWTH", (170, 255, 150)),
    "JESUS": ("JESUS", (255, 236, 170)),
    "PAM":   ("INTERN", (255, 170, 210)),
    "C1":    ("@grindset_bro", (200, 200, 200)),
    "C2":    ("@just_vibes", (200, 200, 200)),
    "C3":    ("@growthhacks101", (200, 200, 200)),
    "C4":    ("@realist", (200, 200, 200)),
}

# (id, speaker, text, pause_before, pause_after)
# speaker None = silent beat whose length is pause_after.
# A text containing "[BLEEP]" is split and a censor tone is inserted.
LINES = [
    # ---------------- ACT 1: the hamster wheel ----------------
    ("open", None, "", 0, 2.2),
    ("n1", "NARR", "You ever pour your whole heart into something... hit upload... and then just... wait?", 0, 0.9),
    ("n2", "NARR", "Twelve views.", 0, 0.9),
    ("c1", "C1", "Bro, just make a new account.", 0, 0.25),
    ("c2", "C2", "The algorithm's just confused, lol.", 0, 0.25),
    ("c3", "C3", "Delete it and upload it again on a clean account!", 0, 0.25),
    ("c4", "C4", "Don't hate the player. Hate the game.", 0, 0.9),
    ("n3", "NARR", "Confused? Sure. The most powerful money-making machine in human history, staffed by some of the smartest people on the planet... is just... confused.", 0, 0.35),
    ("n4", "NARR", "That's [BLEEP] nonsense.", 0, 0.7),
    ("n5", "NARR", "So you start over. Fresh account. Upload it again. Fresh account. Upload it again. Round, and round, and round.", 0, 0.6),
    ("n6", "NARR", "But there is nothing stopping it from showing your videos to more people. Nothing at all...", 0, 0.35),
    ("n7", "NARR", "except for... that.", 0, 1.3),
    ("n8", "NARR", "New accounts are more likely to spend money. Old accounts that never paid? Not so much. It's not dumb. It's counting.", 0, 0.9),
    ("n9", "NARR", "And honestly? I think Jesus would have been fired at every single board meeting.", 0, 0.6),
    ("title", None, "", 0, 4.2),

    # ---------------- ACT 2: the board meeting ----------------
    ("b1", "CEO", "Alright, people, let's make this quick. Next item. The Kingdom of Heaven division.", 0.6, 0.3),
    ("b2", "CEO", "And... Jesus. Thanks for coming in.", 0, 0.5),
    ("b3", "JESUS", "Peace be with you.", 0, 0.7),
    ("b4", "CEO", "Okay then. Let's see the numbers, Margaret.", 0, 0.5),
    ("b5", "CFO", "Three years of operations. Twelve core followers. And one of them is currently negotiating with a competitor. For thirty pieces of silver.", 0, 0.6),
    ("b6", "JESUS", "I know.", 0, 0.5),
    ("b7", "CFO", "You... know?", 0, 0.7),
    ("b8", "TYLER", "Okay, okay, positives! Huge engagement event. Five thousand attendees. That's viral, bro! But the catering was free. Bread, fish, all of it. Where is the monetization funnel?", 0, 0.5),
    ("b9", "JESUS", "Man shall not live by bread alone.", 0, 0.6),
    ("b10", "TYLER", "So, like... upsell to a premium bread?", 0, 0.6),
    ("b11", "CEO", "Let me be direct. What is your growth strategy?", 0, 0.6),
    ("b12", "JESUS", "The kingdom of heaven is like a mustard seed. It is the smallest of all seeds. But when it grows, it becomes a tree, and the birds of the air come and rest in its branches.", 0, 0.4),
    ("silence1", None, "", 0, 2.6),
    ("b13", "TYLER", "Are we... pivoting to agriculture?", 0, 0.35),
    ("b14", "CFO", "Birds don't have credit cards.", 0, 0.6),
    ("b15", "CFO", "Customer acquisition. Fishermen. Tax collectors. Lepers. These are not high-value demographics.", 0, 0.5),
    ("b16", "JESUS", "It is not the healthy who need a doctor, but the sick.", 0, 0.6),
    ("b17", "TYLER", "And then the whale. Rich young guy, ready to commit. And you told him to sell everything... and give it to the poor.", 0, 0.15),
    ("spit", None, "", 0, 0.9),
    ("b18", "CEO", "You told the whale to give his money away?!", 0, 0.5),
    ("b19", "JESUS", "It is easier for a camel to go through the eye of a needle than for a rich man to enter the kingdom of God.", 0, 1.4),
    ("b20", "CEO", "Legal also wants a word about the temple incident. You flipped the tables of our top vendors.", 0, 0.6),
    ("b21", "JESUS", "My house shall be called a house of prayer. But you have made it a den of thieves.", 0, 1.6),
    ("b22", "TYLER", "Bro... read the room.", 0, 0.6),
    ("b23", "CFO", "Brand sentiment. Your enemies are growing faster than your followers.", 0, 0.4),
    ("b24", "JESUS", "Love your enemies. Pray for those who persecute you.", 0, 0.5),
    ("b25", "TYLER", "Is that... a retention strategy?", 0, 0.5),
    ("b26", "CEO", "Enough parables! Just give me one number! One key performance indicator!", 0, 0.8),
    ("b27", "JESUS", "What good is it for a man to gain the whole world... and lose his own soul?", 0, 0.3),
    ("silence2", None, "", 0, 2.4),
    ("b28", "CEO", "That's not a number.", 0, 0.9),
    ("b29", "CEO", "Look. We have to let you go.", 0, 0.8),
    ("b30", "JESUS", "Peace I leave with you.", 0, 0.3),
    ("exit", None, "", 0, 3.4),
    ("b31", "TYLER", "Dude just dug himself deeper.", 0, 0.3),
    ("b32", "CFO", "Kingdom of Heaven. Projected outcome... doomed.", 0, 0.7),
    ("b33", "PAM", "Um... should I throw away the seed?", 0, 0.4),
    ("b34", "CEO", "Leave it. It's just a seed.", 0, 1.6),

    # ---------------- ACT 3: the seed ----------------
    ("grow", None, "", 0, 3.0),
    ("e1", "NARR", "They called it doomed.", 0, 3.2),
    ("e2", "NARR", "But some things grow in ways a spreadsheet can't see.", 0, 4.2),
    ("e3", "NARR", "So... I'm not hating the player. And I'm not starting over.", 0.4, 0.8),
    ("e4", "NARR", "I'm planting seeds.", 0, 2.5),
    ("end", None, "", 0, 5.5),
]

# Caption overrides where the spoken text is spelled for the TTS engine
CAPTIONS = {
    "n4": "That's [BLEEP] nonsense.",
}
