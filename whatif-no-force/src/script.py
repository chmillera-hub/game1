"""Screenplay for "What If No One Could Use Force?"

A 24-hour diner at 2 AM, the night before the No-Force Law takes effect.
Officer Dana Hale (late 40s) sits alone with her duty belt on the table.
Kai (18), the night cook, draws in a sketchbook between orders. The rule:
nobody (police, soldiers, citizens) may touch another person without consent
or cage anyone, and breaking the rule is answered the same way: never with
force or cages, only with words, distance, calling it out, and repair.

Facts the narrator states (checked):
  * > 11 million people are in prison worldwide (World Prison Population List, 2024 ed.)
  * restorative-justice conferences: victims more satisfied, less desire for revenge
    (Strang et al., Campbell Systematic Review 2013)
  * nonviolent campaigns 1900-2006 succeeded 53 % vs 26 % for violent ones
    (Stephan & Chenoweth 2008; Chenoweth & Stephan 2011)
"""

VOICES = {
    # speaker: (kokoro voice, base speed, pitch shift in semitones)
    "HALE": ("af_heart", 0.95, -2.0),
    "KAI": ("am_fenrir", 0.98, 0.0),
    "NARRATOR": ("bm_fable", 0.95, 0.0),
    "ANCHOR": ("am_michael", 1.0, 0.0),
}

# (id, speaker, [(text, pause_after)], speed_multiplier, gain_db)
LINES = [
    # --- 2 AM, the TV --------------------------------------------------------
    ("L01", "ANCHOR", [("At sunrise, the No-Force Law begins.", 0.35),
                       ("No one, not police, not soldiers, not anyone, may touch another person without consent.", 0.35),
                       ("And no one, for any reason, may be locked in a cage.", 0.0)], 1.0, -1.0),
    ("L02", "NARRATOR", [("Imagine a world where force is off the table.", 0.3), ("For everyone.", 0.55),
                         ("And if someone breaks that rule, the answer still can't be force.", 0.35),
                         ("Only words, distance, and the people around you.", 0.0)], 0.97, 0.0),
    # --- Kai with the coffee pot --------------------------------------------------
    ("L03", "KAI", [("Refill?", 0.0)], 1.0, 0.0),
    ("L04", "HALE", [("Please.", 0.0)], 0.9, -2.0),
    ("L05", "KAI", [("Last night with those?", 0.0)], 0.93, -1.0),
    ("L06", "HALE", [("Last night with all of it.", 0.0)], 0.88, -2.0),
    ("L07", "KAI", [("It's dead tonight.", 0.3), ("Mind if I sit?", 0.0)], 0.97, 0.0),
    ("L08", "HALE", [("It's your diner.", 0.0)], 0.95, -1.0),
    ("L09", "KAI", [("It's your booth.", 0.25), ("So I asked.", 0.0)], 0.95, 0.0),
    # --- the toolkit -------------------------------------------------------------------
    ("L10", "HALE", [("Twenty-two years I've carried these.", 0.35),
                     ("Tomorrow I'm supposed to keep people safe with what?", 0.3), ("Words?", 0.0)], 0.93, 0.0),
    ("L11", "KAI", [("Words.", 0.2), ("Witnesses.", 0.2), ("Your body, if you choose to stand somewhere.", 0.0)],
     0.97, 0.0),
    ("L12", "HALE", [("And when someone swings a bottle at somebody's head?", 0.0)], 0.97, 0.5),
    ("L13", "KAI", [("You reach for the person getting hurt.", 0.25), ("If they take your hand, you get them out.", 0.25),
                    ("You stand in the way.", 0.2), ("You get the whole room yelling stop.", 0.0)], 1.0, 0.0),
    ("L14", "NARRATOR", [("You can't grab the person causing harm.", 0.25),
                         ("But you can reach for the person being harmed, if they reach back.", 0.3),
                         ("And a lot of violence depends on not being seen.", 0.0)], 0.97, 0.0),
    ("L15", "HALE", [("And when that doesn't work?", 0.0)], 0.9, -1.0),
    ("L16", "KAI", [("Then sometimes,", 0.45), ("someone gets hurt.", 0.0)], 0.88, -2.0),
    ("L17", "NARRATOR", [("That's the honest cost.", 0.3), ("Some harm that force could have stopped will happen anyway.", 0.35),
                         ("But force has its own victims, too.", 0.35), ("This world bets that the trade is worth it.", 0.0)],
     0.97, 0.0),
    # --- sunrise: the cells open ----------------------------------------------------------
    ("L18", "NARRATOR", [("So at sunrise, every cell door opens.", 0.4), ("More than eleven million people walk out.", 0.3),
                         ("Many were never convicted.", 0.2), ("Many are sick, or addicted, or poor.", 0.35),
                         ("And some did terrible things.", 0.0)], 0.97, 0.0),
    ("L19", "HALE", [("That's what scares me.", 0.25), ("The ones who really hurt people.", 0.0)], 0.92, -1.0),
    ("L20", "KAI", [("Yeah.", 0.3), ("Me too.", 0.0)], 0.9, -1.5),
    ("L21", "NARRATOR", [("They still exist in this world.", 0.25),
                         ("The rule only changes what everyone else is allowed to do about them.", 0.0)], 0.97, 0.0),
    # --- distance and circles ------------------------------------------------------------
    ("L22", "NARRATOR", [("If someone keeps hurting people, the community can step back.", 0.3),
                         ("Distance isn't a cage.", 0.2), ("It's a boundary.", 0.3), ("And the door stays open.", 0.0)],
     0.97, 0.0),
    ("L23", "KAI", [("And when they're ready, there's a circle.", 0.25), ("Everyone they hurt gets to talk.", 0.2),
                    ("And they have to listen.", 0.0)], 0.97, 0.0),
    ("L24", "NARRATOR", [("Where circles like this are already used, victims report feeling more satisfied, "
                          "and less hungry for revenge, than after court.", 0.0)], 0.97, 0.0),
    # --- the new job ------------------------------------------------------------------------
    ("L25", "HALE", [("So what's my job now?", 0.0)], 0.95, 0.0),
    ("L26", "KAI", [("Same as always.", 0.2), ("Keep people safe.", 0.3), ("You just lost the shortcut.", 0.0)], 0.97, 0.0),
    ("L27", "HALE", [("The shortcut.", 0.0)], 0.9, -1.0),
    ("L28", "NARRATOR", [("Most police calls aren't violent anyway.", 0.25), ("Noise.", 0.15), ("Car crashes.", 0.15),
                         ("Someone in crisis on a bridge.", 0.3),
                         ("Here, those calls go to people trained to talk, to treat, and to stay.", 0.35),
                         ("And the money once spent on cages goes into what stops harm before it starts.", 0.0)],
     0.97, 0.0),
    # --- soldiers ------------------------------------------------------------------------------
    ("L29", "HALE", [("And soldiers?", 0.25), ("What if someone rolls in with tanks?", 0.0)], 0.97, 0.0),
    ("L30", "NARRATOR", [("Then the only defense left is refusal.", 0.3), ("Strikes.", 0.15), ("Empty streets.", 0.15),
                         ("No one obeying.", 0.35),
                         ("In a study of a century of uprisings, nonviolent campaigns succeeded about twice as often "
                          "as violent ones.", 0.0)], 0.97, 0.0),
    # --- the turn ------------------------------------------------------------------------------
    ("L31", "KAI", [("You don't remember me,", 0.15), ("do you?", 0.0)], 0.9, -1.0),
    ("L32", "HALE", [("Should I know you?", 0.0)], 0.95, 0.0),
    ("L33", "KAI", [("Fourth Street.", 0.3), ("Three years ago.", 0.3), ("I was fifteen.", 0.45),
                    ("You told me I matched a description.", 0.0)], 0.88, -0.5),
    ("L34", "KAI", [("I didn't.", 0.45), ("You held my face against the hood of your car.", 0.4),
                    ("The metal was so cold.", 0.0)], 0.88, -1.0),
    ("L35", "HALE", [("I remember.", 0.0)], 0.82, -3.0),
    ("L36", "NARRATOR", [("In the old world, this is where it ends.", 0.3), ("She drives home.", 0.2), ("He carries it.", 0.5),
                         ("In this world, he can call it out.", 0.3), ("And she can listen.", 0.0)], 0.95, 0.0),
    ("L37", "KAI", [("I still flinch when a car door slams.", 0.35),
                    ("I've drawn that night a hundred times, trying to make it smaller.", 0.0)], 0.9, -1.0),
    ("L38", "HALE", [("I'm sorry, Kai.", 0.45), ("I was scared,", 0.2), ("and I made you pay for it.", 0.0)], 0.85, -2.0),
    ("L39", "KAI", [("I don't know if I forgive you.", 0.0)], 0.88, -1.5),
    ("L40", "HALE", [("You don't have to.", 0.0)], 0.88, -2.0),
    ("L41", "KAI", [("Then what happens now?", 0.0)], 0.9, -1.0),
    ("L42", "HALE", [("Now I listen.", 0.35), ("As long as you want to talk.", 0.0)], 0.88, -1.5),
    ("L43", "NARRATOR", [("No cage.", 0.25), ("No fist.", 0.35), ("Just the truth, out loud, and someone who stays to hear it.", 0.0)],
     0.93, 0.0),
    # --- sunrise ------------------------------------------------------------------------------------
    ("L44", "HALE", [("Can I shake your hand?", 0.0)], 0.92, -1.0),
    ("L45", "KAI", [("Fist bump.", 0.0)], 0.95, 0.0),
    ("L46", "HALE", [("Fist bump it is.", 0.0)], 0.93, 0.0),
    ("L47", "NARRATOR", [("In a world without force, every touch is a question.", 0.4), ("Sometimes, the answer is yes.", 0.0)],
     0.93, 0.0),
    ("L48", "NARRATOR", [("Would it work?", 0.35), ("No society this big has ever tried.", 0.5),
                         ("But if no one can be forced, the only power left is the kind you have to earn.", 0.4),
                         ("The power to protect.", 0.25), ("To persuade.", 0.3), ("And to care.", 0.0)], 0.92, 0.0),
]

DEFAULT_GAP = 0.45
GAP_BEFORE = {
    "L01": 1.6,   # cold open: rain, neon hum, TV glow
    "L02": 0.9, "L03": 1.2, "L04": 0.6, "L05": 1.6, "L06": 0.7, "L07": 1.2, "L08": 0.4, "L09": 0.3,
    "L10": 1.3, "L11": 0.5, "L12": 0.5, "L13": 0.4, "L14": 0.6, "L15": 0.8, "L16": 1.0, "L17": 0.9,
    "L18": 1.4, "L19": 0.9, "L20": 0.5, "L21": 0.6, "L22": 1.0, "L23": 0.6, "L24": 0.5, "L25": 1.1,
    "L26": 0.5, "L27": 0.5, "L28": 0.8, "L29": 1.0, "L30": 0.6, "L31": 2.2, "L32": 0.6, "L33": 0.7,
    "L34": 1.2, "L35": 1.6, "L36": 1.2, "L37": 1.0, "L38": 1.4, "L39": 1.6, "L40": 0.9, "L41": 1.2,
    "L42": 0.9, "L43": 1.4, "L44": 2.4, "L45": 1.3, "L46": 0.4, "L47": 1.0, "L48": 1.2,
}
TAIL = 4.5

# Musical accents on spoken words: (line id, word, kind) hi / lo / boom / comic / swell
ACCENTS = [
    ("L02", "words", "hi"),
    ("L09", "asked", "hi"),
    ("L16", "hurt", "lo"),
    ("L17", "victims", "lo"),
    ("L18", "opens", "hi"),
    ("L18", "terrible", "lo"),
    ("L22", "open", "hi"),
    ("L23", "listen", "hi"),
    ("L26", "shortcut", "comic"),
    ("L30", "twice", "hi"),
    ("L34", "cold", "lo"),
    ("L35", "remember", "lo"),
    ("L38", "sorry", "lo"),
    ("L42", "listen", "hi"),
    ("L47", "yes", "hi"),
    ("L48", "care", "swell"),
]
