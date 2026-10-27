"""Screenplay for "What If Earth Shrank (But Kept All Its Mass)?"

Each line is spoken by one of three voices and is split into chunks so that
dramatic pauses are exact. A chunk is (text, pause_after_seconds).

Accent markers for the score live in ACCENTS: a word that gets a high
(hopeful / light) or low (heavy / existential) musical note when it is spoken.

Physics used in the narration (Earth radius R0 = 6371 km, mass 5.97e24 kg):
  * proportional shrink by factor s keeps every shape the same, so an observer
    who shrinks too sees nothing change (the Moon keeps its angular size)
  * surface gravity  g ~ 1/s^2   (s = 0.9 -> +23 %, s = 0.5 -> 4x)
  * day length (angular momentum conserved, I ~ s^2)  T ~ s^2
        s = 0.5 -> 6 h, s = 0.01 -> 8.6 s
  * surface air pressure ~ 1/s^4  (s = 0.9 -> 1.5 atm, ~5 m under water)
  * compression releases ~2.5e32 J by s = 0.5 -> the planet glows
  * s = 0.01  (127 km across): density 5.5e9 kg/m^3 ~ white dwarf;
        a teaspoon (4.9 mL) ~ 27 t  ~ four to five elephants
  * equator reaches orbital speed at s ~ 0.0035 (44 km across): flattens and
        sheds a ring
  * ~300 m across: density ~4e17 kg/m^3 ~ neutron star; teaspoon ~ 1e12 kg
        (about a billion tonnes); circumference ~1 km = ~12 min walk
  * Schwarzschild radius 2GM/c^2 = 8.9 mm -> 1.8 cm across (a marble)
  * at that scale the Moon is 4.8 mm across (a peppercorn), 0.53 m away,
        orbit period 0.12 us (8 million orbits/s) at 9 % of light speed,
        gravitational-wave inspiral time ~5 ms
  * outside the bubble gravity depends only on mass: same orbit, 1 year
  * Sun / Earth mass ratio ~333,000; even the Sun ends as a white dwarf
"""

VOICES = {
    # speaker: (kokoro voice, base speed, pitch shift in semitones)
    "TESS": ("af_heart", 0.97, 0.0),
    "PIP": ("af_bella", 1.0, 2.6),
    "NARRATOR": ("bm_fable", 0.95, 0.0),
}

# (id, speaker, [(text, pause_after)], speed_multiplier, gain_db)
LINES = [
    # --- Rooftop, night -----------------------------------------------------
    ("L01", "TESS", [("Couldn't sleep either?", 0.0)], 0.95, -1.0),
    ("L02", "PIP", [("Your suitcase is by the door.", 0.0)], 0.93, -2.0),
    ("L03", "TESS", [("Yeah.", 0.55), ("My bus leaves at seven.", 0.0)], 0.9, -2.0),
    ("L04", "PIP", [("Tess?", 0.65), ("What if the Earth shrank?", 0.0)], 0.95, -1.0),
    ("L05", "TESS", [("Shrank?", 0.0)], 1.0, 0.0),
    ("L06", "PIP", [("Everything.", 0.3), ("The ground, the oceans, the air,", 0.25),
                    ("even the Moon.", 0.45), ("Smaller and smaller.", 0.35),
                    ("But just as heavy.", 0.0)], 1.0, 0.0),
    ("L07", "TESS", [("Same mass.", 0.35), ("Less space.", 0.75), ("Why?", 0.0)], 0.95, -0.5),
    ("L08", "PIP", [("Then your school wouldn't be so far away.", 0.0)], 0.88, -2.5),
    ("L09", "TESS", [("Okay.", 0.45), ("Let's squeeze the world.", 0.0)], 1.0, 0.0),
    # --- The bubble ---------------------------------------------------------
    ("L10", "NARRATOR", [("Imagine a bubble around the Earth and the Moon.", 0.4),
                         ("Everything inside it begins to shrink, all in perfect proportion.", 0.35),
                         ("Every ocean.", 0.15), ("Every cloud.", 0.15), ("Every person.", 0.45),
                         ("But not a single gram is lost.", 0.0)], 1.0, 0.0),
    ("L11", "TESS", [("Here's the weird part.", 0.3), ("You wouldn't even see it happen.", 0.0)], 1.0, 0.0),
    ("L12", "PIP", [("Why not?", 0.0)], 1.0, 0.0),
    ("L13", "TESS", [("Because you'd shrink too.", 0.3), ("Your ruler, your house, your eyes.", 0.25),
                     ("Everything, together.", 0.4),
                     ("The Moon would look exactly the same size.", 0.0)], 1.0, 0.0),
    ("L14", "PIP", [("So...", 0.55), ("you wouldn't be any closer.", 0.0)], 0.86, -2.5),
    ("L15", "TESS", [("Not to you.", 0.7), ("No.", 0.0)], 0.82, -1.5),
    # --- Heavier ------------------------------------------------------------
    ("L16", "NARRATOR", [("But you would feel it.", 0.4),
                         ("Squeeze the Earth to nine tenths of its size, and gravity at the surface grows by almost a quarter.", 0.4),
                         ("The atmosphere thickens.", 0.2),
                         ("Your ears pop, like at the bottom of a swimming pool.", 0.0)], 1.0, 0.0),
    ("L17", "NARRATOR", [("And somewhere, millions of bathroom scales are being blamed for something that isn't their fault.", 0.0)], 1.0, 0.0),
    ("L18", "PIP", [("Dad would totally blame the scale.", 0.0)], 1.05, 0.0),
    ("L19", "TESS", [("Dad already blames the scale.", 0.0)], 1.0, 0.0),
    # --- Faster -------------------------------------------------------------
    ("L20", "TESS", [("Then, the days get shorter.", 0.0)], 1.0, 0.0),
    ("L21", "PIP", [("Shorter how?", 0.0)], 1.0, 0.0),
    ("L22", "TESS", [("Like a figure skater.", 0.25), ("Arms out, nice and slow.", 0.35),
                     ("Then pull them in!", 0.0)], 1.0, 0.5),
    ("L23", "PIP", [("Don't you dare spin on the roof!", 0.0)], 1.05, 2.0),
    ("L24", "TESS", [("Okay, okay!", 0.35), ("But a smaller Earth spins faster.", 0.3),
                     ("At half its size, a whole day would only last six hours.", 0.0)], 1.0, 0.0),
    ("L25", "PIP", [("So we'd get less time.", 0.0)], 0.84, -2.5),
    ("L26", "TESS", [("Yeah.", 0.55), ("Less time.", 0.0)], 0.84, -3.0),
    # --- Hotter -------------------------------------------------------------
    ("L27", "NARRATOR", [("At half its size, about as big as Mars, gravity is four times stronger.", 0.35),
                         ("Just standing up would feel like carrying three extra copies of yourself.", 0.0)], 1.0, 0.0),
    ("L28", "NARRATOR", [("And squeezing anything heats it up, like a bicycle pump warming in your hand.", 0.4),
                         ("Squeeze an entire planet, and the oceans steam,", 0.2), ("the rocks melt,", 0.25),
                         ("and the ground begins to glow.", 0.0)], 1.0, 0.0),
    ("L29", "PIP", [("What about people?", 0.0)], 0.9, -1.5),
    ("L30", "TESS", [("People wouldn't make it this far, Pip.", 0.0)], 0.85, -2.5),
    ("L31", "TESS", [("So let's watch the rest from somewhere safe.", 0.0)], 0.92, -1.0),
    # --- From outside: white dwarf -------------------------------------------
    ("L32", "NARRATOR", [("From out here, you can finally see it.", 0.35),
                         ("Earth shrinks past the size of the Moon.", 0.3), ("Then a country.", 0.3),
                         ("Then a city.", 0.0)], 1.0, 0.0),
    ("L33", "NARRATOR", [("Just over a hundred kilometers across, it's as dense as a white dwarf,", 0.15),
                         ("the glowing core left behind by a dead star.", 0.45),
                         ("A single teaspoon of it would weigh as much as four elephants.", 0.0)], 1.0, 0.0),
    ("L34", "PIP", [("Four elephants?", 0.0)], 1.05, 0.5),
    ("L35", "TESS", [("In a teaspoon.", 0.0)], 1.0, 0.0),
    ("L36", "NARRATOR", [("And a day now lasts about nine seconds.", 0.0)], 1.0, 0.0),
    ("L37", "TESS", [("Keep going, and it spins so fast it flattens out,", 0.15),
                     ("flinging glowing rock into a ring around itself.", 0.0)], 1.0, 0.0),
    ("L38", "PIP", [("Like pizza dough!", 0.0)], 1.1, 1.5),
    ("L39", "TESS", [("Exactly like pizza dough.", 0.0)], 1.0, 0.0),
    # --- Neutron star --------------------------------------------------------
    ("L40", "NARRATOR", [("Smaller still.", 0.35), ("Now it's about as wide as a stadium.", 0.35),
                         ("Here, atoms stop being atoms.", 0.25),
                         ("Electrons are crushed into protons, and almost everything becomes neutrons.", 0.35),
                         ("Earth is now as dense as a neutron star.", 0.2),
                         ("A teaspoon would weigh about a billion tons.", 0.0)], 1.0, 0.0),
    ("L41", "TESS", [("Every mountain.", 0.2), ("Every ocean.", 0.2), ("Every city.", 0.45),
                     ("In a ball you could walk around before your cocoa gets cold.", 0.0)], 0.9, -1.5),
    # --- Black hole ----------------------------------------------------------
    ("L42", "NARRATOR", [("And then, when the entire planet is squeezed to less than two centimeters across,", 0.0)], 0.92, 0.0),
    ("L43", "TESS", [("about the size of a marble,", 0.0)], 0.9, -1.5),
    ("L44", "NARRATOR", [("gravity wins.", 0.55), ("Not even light can escape.", 0.45),
                         ("Earth becomes a black hole.", 0.0)], 0.88, 0.5),
    ("L45", "TESS", [("We've always called Earth the blue marble.", 0.65), ("It would finally be one.", 0.85),
                     ("It just wouldn't be blue.", 0.0)], 0.85, -2.0),
    ("L46", "PIP", [("And the Moon?", 0.0)], 0.85, -3.0),
    ("L47", "NARRATOR", [("The Moon, now the size of a peppercorn, whips around the black hole from about an arm's length away.", 0.3),
                         ("Eight million times every second, at nearly a tenth of the speed of light.", 0.4),
                         ("Then it spirals in, sending one last chirp of gravitational waves rippling across space.", 0.7),
                         ("And then, {0.9} silence.", 0.0)], 0.97, 0.0),
    # --- Nobody notices -------------------------------------------------------
    ("L48", "NARRATOR", [("And here's the strangest part.", 0.3), ("Nothing else would notice.", 0.35),
                         ("From far away, gravity only cares about mass, not size.", 0.3),
                         ("The Sun would hold on just the same.", 0.25), ("Mars wouldn't feel a thing.", 0.0)], 0.97, 0.0),
    ("L49", "TESS", [("It would just keep going around the Sun.", 0.35), ("Once a year.", 0.35),
                     ("Every year.", 0.0)], 0.88, -2.0),
    ("L50", "PIP", [("Like it's still counting birthdays.", 0.0)], 0.84, -3.0),
    ("L51", "PIP", [("That's the saddest thing I've ever heard.", 0.0)], 0.9, -1.5),
    # --- Push back -------------------------------------------------------------
    ("L52", "TESS", [("Good news, though.", 0.3), ("It can't happen.", 0.0)], 0.95, 0.0),
    ("L53", "PIP", [("Why not?", 0.0)], 1.0, 0.0),
    ("L54", "TESS", [("Earth is way too light to collapse on its own.", 0.3),
                     ("Even the Sun is too light, and it's more than three hundred thousand times heavier than us.", 0.3),
                     ("Only giant stars ever get crushed like that.", 0.45),
                     ("Everything else pushes back.", 0.0)], 0.97, 0.0),
    ("L55", "NARRATOR", [("Every atom resists being squeezed.", 0.3),
                         ("The electrons inside refuse to crowd into the same space.", 0.35),
                         ("It's why the ground holds you up.", 0.2),
                         ("It's why you don't sink through your chair.", 0.0)], 0.97, 0.0),
    ("L56", "PIP", [("So the harder you squeeze it,", 0.3), ("the harder it pushes back?", 0.0)], 0.95, 0.0),
    ("L57", "TESS", [("Pretty much.", 0.3), ("Stubborn little things.", 0.0)], 1.0, 0.0),
    ("L58", "PIP", [("Like you.", 0.0)], 0.95, -1.0),
    ("L59", "TESS", [("Like... us.", 0.0)], 0.98, -1.5),
    # --- Same Moon ---------------------------------------------------------------
    ("L60", "PIP", [("It's still gonna be really far.", 0.0)], 0.84, -3.0),
    ("L61", "TESS", [("Yeah.", 0.4), ("It is.", 0.85),
                     ("But the Moon looks the same size from my dorm as it does from this roof.", 0.0)], 0.9, -1.5),
    ("L62", "TESS", [("So when things get heavy,", 0.45), ("look up.", 0.55),
                     ("I'll be looking at the same one.", 0.0)], 0.88, -1.5),
    ("L63", "NARRATOR", [("The Earth will never be squeezed into a marble.", 0.3),
                         ("It's far too stubborn for that.", 0.9), ("And it turns out,", 0.55),
                         ("so are we.", 0.0)], 0.9, 0.0),
]

# Silence inserted *before* each line (seconds). Default gap otherwise.
DEFAULT_GAP = 0.45
GAP_BEFORE = {
    "L01": 2.2,   # cold open: crickets, Tess climbing out
    "L02": 0.9, "L03": 1.0, "L04": 1.6, "L05": 0.5, "L06": 0.35, "L07": 0.6,
    "L08": 1.0, "L09": 1.5, "L10": 1.2, "L11": 0.9, "L12": 0.3, "L13": 0.3,
    "L14": 0.9, "L15": 0.8, "L16": 1.6, "L17": 0.5, "L18": 0.5, "L19": 0.25,
    "L20": 1.0, "L21": 0.3, "L22": 0.35, "L23": 0.1, "L24": 0.5, "L25": 0.9,
    "L26": 0.9, "L27": 1.6, "L28": 0.6, "L29": 0.9, "L30": 0.9, "L31": 1.1,
    "L32": 2.0, "L33": 0.6, "L34": 0.4, "L35": 0.25, "L36": 0.6, "L37": 0.6,
    "L38": 0.2, "L39": 0.25, "L40": 1.3, "L41": 0.9, "L42": 1.4, "L43": 0.15,
    "L44": 0.25, "L45": 2.4, "L46": 1.4, "L47": 0.7, "L48": 2.6, "L49": 0.9,
    "L50": 1.1, "L51": 1.3, "L52": 0.9, "L53": 0.3, "L54": 0.35, "L55": 0.7,
    "L56": 0.8, "L57": 0.4, "L58": 0.7, "L59": 0.5, "L60": 2.0, "L61": 0.9,
    "L62": 0.9, "L63": 1.8,
}
TAIL = 4.5  # music + final shot after the last word

# Musical accents on spoken words: (line id, word, kind)
#   kind: "hi" bright high note, "lo" deep low note, "boom" sub impact,
#         "comic" playful pluck, "swell" rising string swell
ACCENTS = [
    ("L08", "far", "lo"),
    ("L09", "world", "hi"),
    ("L13", "same", "hi"),
    ("L15", "No", "lo"),
    ("L17", "fault", "comic"),
    ("L19", "scale", "comic"),
    ("L23", "roof", "comic"),
    ("L26", "time", "lo"),
    ("L28", "glow", "swell"),
    ("L30", "far", "lo"),
    ("L31", "safe", "hi"),
    ("L33", "dead", "lo"),
    ("L33", "elephants", "comic"),
    ("L38", "dough", "comic"),
    ("L40", "neutrons", "lo"),
    ("L41", "cold", "hi"),
    ("L44", "black", "boom"),
    ("L45", "blue", "lo"),
    ("L48", "notice", "lo"),
    ("L50", "birthdays", "lo"),
    ("L52", "can't", "hi"),
    ("L54", "back", "hi"),
    ("L59", "us", "hi"),
    ("L61", "same", "hi"),
    ("L62", "up", "hi"),
    ("L62", "same", "hi"),
    ("L63", "we", "swell"),
]
