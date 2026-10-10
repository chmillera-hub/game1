# Script for "Ace and Blueberry" -- voices, lines and scene beats.
# Each scene is a list of beats:
#   ("say", line_id)        speak a line (time advances by its length)
#   ("wait", seconds)       hold / action time
#   ("mark", name)          name the current time so the renderer can sync to it

VOICES = {
    # voice, kokoro speed, pitch ratio (resample; >1 = higher + faster)
    "N":    dict(voice="af_heart",  speed=0.86, pitch=1.00),
    "ACE":  dict(voice="af_bella",  speed=0.98, pitch=1.15),
    "BB":   dict(voice="am_michael", speed=0.80, pitch=1.42),
    "BABY": dict(voice="am_puck",   speed=0.80, pitch=1.55),
}

LINES = {
    "N_title":     ("N",   "Ace and Blueberry."),
    "ACE_hi":      ("ACE", "Hi, Blueberry!"),
    "BB_hi":       ("BB",  "Hi, Ace!"),
    "N_play1":     ("N",   "Ace was playing with her best friend, Blueberry. Blueberry is her hamster."),
    "N_play2":     ("N",   "Blueberry was in his favorite toy, his purple ball."),
    "N_play3":     ("N",   "Blueberry loves to roll and play!"),
    "BB_whee":     ("BB",  "Yahoo!"),

    "N_fast":      ("N",   "Blueberry likes to roll fast..."),
    "BB_zoom":     ("BB",  "Zoom, zoom!"),
    "N_slow":      ("N",   "and Blueberry likes to roll slow."),
    "BB_slow":     ("BB",  "Nice... and... easy..."),
    "N_most":      ("N",   "But most of all, Blueberry loves to roll over and visit with his best friend, Ace."),

    "N_push":      ("N",   "Ace gave Blueberry a little push in his purple ball."),
    "N_tap":       ("N",   "But when Ace tapped the ball with her finger..."),
    "ACE_ooch":    ("ACE", "Ooch!"),
    "N_sore":      ("N",   "Ace had sore fingers."),
    "BB_why":      ("BB",  "Ace, why are your fingers so sore?"),

    "ACE_brother": ("ACE", "My baby brother bites my nails when I am sleeping."),
    "BABY_nom":    ("BABY", "Nom nom nom nom!"),
    "BB_repeat":   ("BB",  "Your baby brother bites your nails when you are sleeping?"),
    "BB_giggle":   ("BB",  "Ha ha! That's so silly!"),
    "ACE_yes":     ("ACE", "Yes! Hee hee!"),
    "BB_hmm":      ("BB",  "Hmmm..."),
    "N_idea":      ("N",   "Blueberry needed an idea, so that Ace's baby brother would stop biting her nails."),
    "N_thought":   ("N",   "Blueberry thought, and thought..."),
    "BB_gloves":   ("BB",  "I know! Wear gloves to bed!"),
    "ACE_ok":      ("ACE", "Gloves? Okay, I'll try it!"),

    "N_gloves":    ("N",   "Ace went to sleep that night, wearing gloves."),
    "BABY_huh":    ("BABY", "Huh??"),
    "N_woke":      ("N",   "When Ace woke up, she took off the gloves,"),
    "N_fine":      ("N",   "and her fingernails were fine."),
    "N_but":       ("N",   "But..."),
    "ACE_hot":     ("ACE", "My hands are too hot!"),
    "ACE_dislike": ("ACE", "I do not like wearing gloves at night."),
    "N_another":   ("N",   "Blueberry had another idea..."),

    "BB_color":    ("BB",  "What is your favorite color, Ace?"),
    "ACE_blue":    ("ACE", "Blue!"),
    "BB_paint":    ("BB",  "Can I paint your nails blue, with blue nail polish?"),
    "BB_taste":    ("BB",  "When your baby brother tries to bite your nails, he won't like the taste. And he'll stop!"),
    "ACE_like":    ("ACE", "I like that idea!"),
    "N_painted":   ("N",   "And so, Ace's nails were painted blue."),
    "ACE_pretty":  ("ACE", "Ooh! So pretty!"),
    "BB_done":     ("BB",  "All done!"),

    "N_blueNight": ("N",   "That night, Ace went to sleep with her fingernails painted blue."),
    "BABY_bleh":   ("BABY", "Yuck! Yucky!"),
    "N_know":      ("N",   "And wouldn't you know it..."),
    "N_nobite":    ("N",   "her nails were fine. No bite marks!"),
    "ACE_yay":     ("ACE", "Hooray! It worked!"),
    "N_grew":      ("N",   "Ace's nails finally grew back, and her fingers were no longer sore."),
    "ACE_noooch":  ("ACE", "Look! No more ooches!"),
    "BB_hooray":   ("BB",  "Yahoo!"),

    "N_tues":      ("N",   "Now, every Tuesday night after dinner,"),
    "N_any":       ("N",   "Blueberry paints Ace's nails any color she wants."),
    "ACE_pink":    ("ACE", "Pink, please!"),
    "ACE_green":   ("ACE", "Green, please!"),
    "ACE_rainbow": ("ACE", "Ooh! All the colors!"),
    "ACE_thanks":  ("ACE", "Thank you for your help, Blueberry!"),
    "BB_welcome":  ("BB",  "Any time, Ace! That's what best friends are for."),
    "N_end":       ("N",   "The End!"),
}

# Caption text overrides (what is shown on screen, if different from what is spoken)
CAPTIONS = {
    "BABY_huh": "Huh?",
    "BB_hmm": "Hmmm...",
    "N_fast": "Blueberry likes to roll fast...",
    "N_slow": "...and Blueberry likes to roll slow.",
    "N_nobite": "...her nails were fine. No bite marks!",
    "N_any": "...Blueberry paints Ace's nails any color she wants.",
}

SCENES = [
    ("title", "title", [
        ("wait", 3.4), ("say", "N_title"), ("wait", 3.2),
    ]),
    ("hello", "theme", [
        ("wait", 1.0), ("mark", "ballIn"), ("wait", 2.2),
        ("say", "ACE_hi"), ("wait", 0.35), ("say", "BB_hi"), ("wait", 0.8),
        ("say", "N_play1"), ("wait", 0.5), ("mark", "shine"), ("say", "N_play2"), ("wait", 0.6),
        ("mark", "spin"), ("say", "N_play3"), ("wait", 0.15), ("say", "BB_whee"), ("wait", 1.8),
    ]),
    ("roll", "playful", [
        ("wait", 0.8), ("say", "N_fast"), ("mark", "fast"), ("wait", 0.3), ("say", "BB_zoom"), ("wait", 2.0),
        ("mark", "slowStart"), ("say", "N_slow"), ("wait", 0.3), ("say", "BB_slow"), ("wait", 1.6),
        ("mark", "visit"), ("say", "N_most"), ("wait", 2.0),
    ]),
    ("ooch", "theme", [
        ("wait", 0.8), ("mark", "push"), ("say", "N_push"), ("wait", 0.9),
        ("mark", "tapLine"), ("say", "N_tap"), ("mark", "tap"), ("wait", 0.12), ("say", "ACE_ooch"), ("wait", 1.3),
        ("mark", "sore"), ("say", "N_sore"), ("wait", 1.6),
        ("mark", "why"), ("say", "BB_why"), ("wait", 0.7),
    ]),
    ("brother", "think", [
        ("wait", 0.4), ("say", "ACE_brother"), ("wait", 0.3),
        ("mark", "flash"), ("wait", 1.2), ("say", "BABY_nom"), ("wait", 1.8), ("mark", "flashEnd"), ("wait", 0.8),
        ("say", "BB_repeat"), ("wait", 0.15), ("mark", "giggle"), ("say", "BB_giggle"), ("wait", 0.15), ("say", "ACE_yes"), ("wait", 1.0),
        ("mark", "hmm"), ("say", "BB_hmm"), ("wait", 0.5), ("say", "N_idea"), ("wait", 0.5),
        ("say", "N_thought"), ("wait", 1.4), ("mark", "bulb"), ("wait", 0.9),
        ("say", "BB_gloves"), ("wait", 0.4), ("say", "ACE_ok"), ("wait", 1.0),
    ]),
    ("night1", "lullaby", [
        ("wait", 1.6), ("say", "N_gloves"), ("wait", 0.8),
        ("mark", "baby"), ("wait", 1.6), ("say", "BABY_huh"), ("wait", 2.4), ("mark", "morning"), ("wait", 2.4),
        ("mark", "wake"), ("say", "N_woke"), ("mark", "glovesOff"), ("wait", 0.3), ("say", "N_fine"), ("wait", 0.6),
        ("say", "N_but"), ("wait", 0.4), ("mark", "hot"), ("say", "ACE_hot"), ("wait", 0.3), ("say", "ACE_dislike"), ("wait", 0.8),
        ("mark", "another"), ("say", "N_another"), ("wait", 1.4),
    ]),
    ("blue", "theme", [
        ("wait", 0.8), ("say", "BB_color"), ("wait", 0.35), ("mark", "blueSay"), ("say", "ACE_blue"), ("wait", 0.9),
        ("mark", "bottle"), ("say", "BB_paint"), ("wait", 0.4), ("mark", "taste"), ("say", "BB_taste"), ("wait", 0.4),
        ("say", "ACE_like"), ("wait", 0.6),
        ("mark", "paint"), ("wait", 0.8), ("say", "N_painted"), ("wait", 2.6), ("say", "BB_done"), ("wait", 0.3),
        ("mark", "pretty"), ("say", "ACE_pretty"), ("wait", 1.4),
    ]),
    ("night2", "lullaby", [
        ("wait", 1.4), ("say", "N_blueNight"), ("wait", 0.6),
        ("mark", "baby"), ("wait", 2.2), ("mark", "bleh"), ("say", "BABY_bleh"), ("wait", 1.8),
        ("say", "N_know"), ("mark", "morning"), ("wait", 2.0),
        ("mark", "check"), ("say", "N_nobite"), ("wait", 0.3), ("say", "ACE_yay"), ("wait", 0.8),
        ("mark", "grow"), ("say", "N_grew"), ("wait", 1.4),
        ("mark", "tap"), ("wait", 1.4), ("say", "ACE_noooch"), ("wait", 0.2), ("say", "BB_hooray"), ("wait", 1.2),
    ]),
    ("tuesday", "finale", [
        ("wait", 0.6), ("mark", "cal"), ("say", "N_tues"), ("wait", 0.3), ("say", "N_any"), ("wait", 0.4),
        ("mark", "c1"), ("say", "ACE_pink"), ("wait", 1.8), ("mark", "c2"), ("say", "ACE_green"), ("wait", 1.8),
        ("mark", "c3"), ("say", "ACE_rainbow"), ("wait", 2.0),
        ("mark", "thanks"), ("say", "ACE_thanks"), ("wait", 0.4), ("say", "BB_welcome"), ("wait", 3.0),
    ]),
    ("end", "end", [
        ("wait", 1.8), ("say", "N_end"), ("wait", 6.0),
    ]),
]
