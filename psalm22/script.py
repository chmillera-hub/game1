"""Screenplay for "Why Have You Forsaken Me" — a Psalm 22 short.

Each line: (id, character, text).  Within text, '|' is a short breath pause
and '||' is a longer, weighted pause.  Fragments between pauses are voiced
separately so the delivery stays slow and deliberate.
"""

CAST = {
    # character: (voice, speed, lang, semitone_shift)
    'NARRATOR':  ('af_heart',   0.82, 'en-us', 0.0),
    'JESUS':     ('am_michael', 0.74, 'en-us', -0.5),
    'MARY':      ('bf_emma',    0.78, 'en-gb', 0.0),
    'MAGDALENE': ('af_bella',   0.80, 'en-us', 0.0),
    'JOHN':      ('am_puck',    0.80, 'en-us', 0.0),
    'CENTURION': ('am_fenrir',  0.74, 'en-us', -1.0),
    'MOCKER1':   ('bm_george',  0.88, 'en-gb', -0.5),
    'MOCKER2':   ('bm_lewis',   0.90, 'en-gb', 0.0),
    'YOUNG':     ('af_nicole',  0.84, 'en-us', 0.0),
    'NANA':      ('af_sarah',   0.78, 'en-us', -1.5),
}

LINES = [
    # --- Golgotha, noon ---
    ('N1', 'NARRATOR', "It was noon... | and darkness came over the whole land."),
    # --- The mockers ---
    ('M1', 'MOCKER1', "He trusted in the Lord."),
    ('M2', 'MOCKER2', "Then let the Lord rescue him... | since he delights in him!"),
    ('G1', 'MAGDALENE', "How can they look at him... || and laugh?"),
    ('J1', 'JOHN', "Because if they laugh... | they don't have to feel it."),
    # --- Connection from the cross ---
    ('X1', 'JESUS', "Woman... || here is your son."),
    ('X2', 'JESUS', "Son... || here is your mother."),
    # --- Three hours of darkness ---
    ('N2', 'NARRATOR', "For three hours, | the sky held its breath."),
    ('X3', 'JESUS', "You are my strength... || do not be far from me."),
    ('N3', 'NARRATOR', "Then, | at the ninth hour..."),
    ('XC', 'JESUS', "@CRY"),
    ('X4', 'JESUS', "My God... | my God... || why have you forsaken me?"),
    # --- The women and John ---
    ('G2', 'MAGDALENE', "Mother... | he's crying out. || Everyone can hear him."),
    ('Y1', 'MARY', "Let them hear."),
    ('Y2', 'MARY', "The night he was born, | he cried just like that. || I didn't hush him. | I held him."),
    ('Y3', 'MARY', "I won't ask him to be quiet now."),
    ('J2', 'JOHN', "It's the psalm. || From my mother's womb... | you have been my God."),
    ('Y4', 'MARY', "He's still praying, John. || Out loud."),
    # --- The end ---
    ('X5', 'JESUS', "Father... || into your hands... || I commit my spirit."),
    ('C1', 'CENTURION', "Truly... || this man was the Son of God."),
    # --- Bridge ---
    ('N4', 'NARRATOR', "He didn't whisper it. | He cried it out, | in front of everyone."),
    ('N5', 'NARRATOR', "And the soldier sent to silence him... | was the one who heard him."),
    ('N6', 'NARRATOR', "It was the sacred scream of a soul | refusing to suffer in silence. || Emotional truth, | made public."),
    # --- Now ---
    ('N7', 'NARRATOR', "Two thousand years later, | the world is numb. | Half asleep. || But underneath it all, | the pain is volcanic."),
    ('Q1', 'YOUNG', "Nana? || Do you ever feel like you're screaming... | and everyone just nods politely, | and scrolls past?"),
    ('R1', 'NANA', "Every day of my life, baby."),
    ('Q2', 'YOUNG', "Then what do we do? || Without turning cruel... | and without letting them convince us we're crazy?"),
    ('R2', 'NANA', "We speak close to the heart. || We feel it, all the way through. || And we listen to what the night is trying to teach us."),
    ('R3', 'NANA', "Silence isn't strength, baby. || God didn't stay silent while He suffered. || So why should you?"),
    ('Q3', 'YOUNG', "An acorn?"),
    ('R4', 'NANA', "Plant it. || Tend what grows from the hard places."),
    # --- The garden ---
    ('N8', 'NARRATOR', "When the noise gets too loud, | a parable can hold | what plain words can't."),
    ('N9', 'NARRATOR', "In the place where he was crucified, | there was a garden."),
    ('N10', 'NARRATOR', "Suffering, | tended with care, | can grow into a tree. || And its fruit | is connection."),
    ('N11', 'NARRATOR', "The kind that still cries out in grief, | because it remembers what came before... | and will not let the machine of suppression | tear the garden down."),
    ('N12', 'NARRATOR', "So here we are. || Still breathing. | Still feeling. || Still tending the garden. || That's sacred."),
    ('N13', 'NARRATOR', "Keep the fire lit. | Others are watching. || And maybe the garden in them | is waiting for the Lord of their emotions | to wake them up too."),
]

# The cry is voiced from phonemes (Aramaic, Mark 15:34).
CRY_PHONEMES = ["ɛlˈoʊi!", "ɛlˈoʊi!", "lˈeɪmɑ sɑbɑχtˈɑːni?"]
