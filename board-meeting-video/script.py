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
    "CFO":   ("HEAD OF MONETIZATION", (140, 210, 255)),
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
    ("open", None, "", 0, 1.6),
    ("n1", "NARR", "You ever pour your whole heart into a video... hit upload... and then just... wait?", 0, 1.0),
    ("n2", "NARR", "Twelve views.", 0, 1.0),
    ("n2b", "NARR", "The app could show it to anyone. Millions of people scroll past every hour. But it chose to show it to twelve. And the advice I get?", 0, 0.8),
    ("c1", "C1", "Bro, just make a new account.", 0, 0.25),
    ("c2", "C2", "The algorithm's just confused, lol.", 0, 0.25),
    ("c3", "C3", "Delete it and upload it again on a clean account!", 0, 0.25),
    ("c4", "C4", "Don't hate the player. Hate the game.", 0, 0.9),
    ("n3", "NARR", "Confused? Sure. The most powerful money-making machine in human history, staffed by some of the smartest people on the planet... is just... confused.", 0, 0.6),
    ("n4", "NARR", "That's [BLEEP] nonsense.", 0, 0.7),
    ("n5", "NARR", "So you start over. Fresh account. Upload it again. Fresh account. Upload it again. Round, and round, and round.", 0, 0.6),
    ("n6", "NARR", "But there is nothing stopping it from showing your videos to more people. Nothing at all...", 0, 0.35),
    ("n7", "NARR", "except for... that.", 0, 1.3),
    ("n8", "NARR", "New accounts are more likely to spend money. Old accounts that never paid? Not so much. It's not dumb. It's counting.", 0, 0.6),
    ("n8b", "NARR", "Every fresh account makes their numbers look better. And people like me pay for it, starting from zero, again and again.", 0, 0.9),
    ("n9", "NARR", "And lying here, I keep thinking about Jesus.", 0, 0.4),
    ("n10", "NARR", "Not that I'm him. But if someone with a heart like his posted online today... would the system bury him too? Leave him alone, like me?", 0, 0.5),
    ("n11", "NARR", "Let's reflect on that.", 0, 0.6),
    ("title", None, "", 0, 3.9),

    # ---------------- ACT 2: the account review ----------------
    ("b1", "CEO", "Alright, people, let's make this quick. Next account review.", 0.6, 0.3),
    ("b2", "CEO", "And... Jesus. Thanks for coming in.", 0, 0.4),
    ("b3", "JESUS", "Peace be with you.", 0, 0.55),
    ("b4", "CEO", "Okay then. Let's see the numbers, Margaret.", 0, 0.4),
    ("b5", "CFO", "Twelve followers. Average watch time, eleven seconds. Engagement rate, basically zero.", 0, 0.4),
    ("b6", "JESUS", "Where two or three gather in my name, there I am with them.", 0, 0.45),
    ("b7", "TYLER", "Okay, real talk, bro. You give everything away for free. No paywall. No merch. No subscriptions. Where is the monetization funnel?", 0, 0.4),
    ("b8", "JESUS", "Freely you have received. Freely give.", 0, 0.45),
    ("b9", "TYLER", "So, like... a free trial?", 0, 0.45),
    ("b10", "CEO", "Let me be direct. What is your growth strategy?", 0, 0.45),
    ("b11", "JESUS", "The kingdom of heaven is like a mustard seed. It is the smallest of all seeds. But when it grows, it becomes a tree, and the birds of the air come and rest in its branches.", 0, 0.4),
    ("silence1", None, "", 0, 2.0),
    ("b12", "TYLER", "Are we... pivoting to gardening content?", 0, 0.35),
    ("b13", "CFO", "Birds don't click on ads.", 0, 0.45),
    ("b14", "CFO", "Audience quality. You spend hours in the comments with lonely people. Sick people. Broke people. People nobody else replies to. These are not high-value users.", 0, 0.4),
    ("b15", "JESUS", "It is not the healthy who need a doctor, but the sick.", 0, 0.45),
    ("b16", "TYLER", "And bro, you refuse rage bait. Someone trolls you, and you just... bless them? Do you know how much reach you are leaving on the table?", 0, 0.4),
    ("b17", "JESUS", "Bless those who curse you. Pray for those who mistreat you.", 0, 0.45),
    ("b18", "CFO", "Also, Brand Safety flagged your last video. You called out our top advertisers for profiting off people's pain.", 0, 0.15),
    ("spit", None, "", 0, 0.9),
    ("b19", "CEO", "You called out the advertisers?!", 0, 0.4),
    ("b20", "JESUS", "No one can serve two masters. You cannot serve both God and money.", 0, 0.9),
    ("b21", "CFO", "Brand sentiment. Your enemies are outgrowing your followers. Trolls flood your account every single day. What exactly is going on?", 0, 0.4),
    ("b22", "JESUS", "The kingdom of God is within you. I may not see it grow with my own eyes. But I hope that everyone, even the ones attacking me, will one day be with me in my Father's kingdom of heaven. There is room for everyone.", 0, 1.0),
    ("b23", "TYLER", "Is this dude... okay?", 0, 0.4),
    ("b24", "CFO", "Honestly? I can't tell if he's broken... or if we are.", 0, 0.55),
    ("b25", "TYLER", "And your video about loving your enemies got flagged as divisive. The comments are a war zone.", 0, 0.4),
    ("b26", "JESUS", "Blessed are the peacemakers, for they will be called children of God.", 0, 0.45),
    ("b27", "CEO", "Enough parables! Just give me one number! One key performance indicator!", 0, 0.65),
    ("b28", "JESUS", "What good is it for a man to gain the whole world... and lose his own soul?", 0, 0.3),
    ("silence2", None, "", 0, 1.9),
    ("b29", "CEO", "That's not a number.", 0, 0.55),
    ("b30", "CEO", "Here's our decision. Your account will continue to be suppressed. You have given us no good argument to boost it, or share it.", 0, 0.4),
    ("b31", "TYLER", "Sorry, bro. The door is over there.", 0, 0.4),
    ("rise", None, "", 0, 1.6),
    ("b32", "JESUS", "A new commandment I give you. Love one another, as I have loved you. Goodbye.", 0, 0.3),
    ("exit", None, "", 0, 3.6),
    ("b33", "TYLER", "Are we... going to hell for this?", 0, 0.4),
    ("b34", "CFO", "Great question. Let's circle back to that later.", 0, 0.45),
    ("b35", "PAM", "Um... should I throw away the seed?", 0, 0.4),
    ("b36", "CEO", "Leave it. It's just a seed.", 0, 1.2),

    # ---------------- ACT 3: the seed ----------------
    ("grow", None, "", 0, 2.6),
    ("e1", "NARR", "They buried him.", 0, 2.2),
    ("e2", "NARR", "But some things grow in ways a spreadsheet can't see.", 0, 3.6),
    ("e3", "NARR", "So... I'm done chasing their numbers. And I'm not starting over.", 0.4, 0.8),
    ("e4", "NARR", "I'm planting seeds.", 0, 2.5),
    ("end", None, "", 0, 4.6),
]

# Per-line speaking rate (Piper length_scale): the opening narration is
# slowed down so the setup lands on a first viewing.
RATE = {k: 1.10 for k in ("n1", "n2", "n2b", "n3", "n4", "n5", "n6", "n7", "n8", "n8b", "n9", "n10", "n11")}

# Caption overrides where the spoken text is spelled for the TTS engine
CAPTIONS = {
    "n4": "That's [BLEEP] nonsense.",
}
