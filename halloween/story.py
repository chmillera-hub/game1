"""TOO MOM - a spooky Halloween tale, built from a child's pencil drawing.

The screenplay as data. Everything else (voices, timeline, music, shots)
is derived from this file.

Line markup
-----------
  " | "        split the line into separately voiced chunks with a pause
  " |0.8| "    ...with an explicit pause length in seconds
  "^word"      hopeful word  -> soft high note in the score
  "_word"      heavy word    -> low note in the score
  {"tts": ...} optional spoken text when it must differ from the subtitle
"""

# who: voice, speed, pitch shift (semitones), subtitle colour, label
CAST = {
    "NARRATOR": dict(voice="bm_george", speed=0.90, pitch=0.0, color=(214, 196, 255), label="Narrator"),
    "WEDGE":    dict(voice="am_michael", speed=0.88, pitch=-1.0, color=(255, 214, 128), label="Wedge"),
    "BISCUIT":  dict(voice="am_puck", speed=1.03, pitch=0.0, color=(150, 230, 170), label="Biscuit"),
    "PIP":      dict(voice="af_bella", speed=0.94, pitch=0.5, color=(255, 176, 200), label="Pip"),
    "CRUMB":    dict(voice="af_kore", speed=1.02, pitch=3.0, color=(140, 210, 255), label="Crumb"),
    "CAT":      dict(voice="af_nicole", speed=0.86, pitch=-1.5, color=(236, 226, 80), label="The Cat"),
    "MOM":      dict(voice="af_heart", speed=0.90, pitch=0.0, color=(255, 160, 96), label="Mom"),
    "SUN":      dict(voice="bf_emma", speed=0.92, pitch=-1.0, color=(196, 150, 255), label="Purple Sun"),
    "GHOST":    dict(voice="bm_fable", speed=1.00, pitch=0.0, color=(220, 232, 244), label="Scribble Ghost"),
    "TILT":     dict(voice="am_fenrir", speed=0.84, pitch=-2.0, color=(200, 200, 200), label="Tilt"),
}

# The script, in order. ("line", id, who, text, opts) or ("beat", id, seconds)
# opts: gap = silence before the line (s), tts = alternate spoken text.
SCRIPT = [
    # ---------------------------------------------------------------- PROLOGUE
    ("line", "n1", "NARRATOR", "On the last night of October, with the lanterns all lit... | and the wind at the keyhole, a-whistling through it...", dict(gap=0.45)),
    ("beat", "wind1", 1.4),
    ("line", "n2", "NARRATOR", "a little girl drew, with her tongue poking out, | a present for Mom. |0.5| The best ever, no doubt.", dict(gap=0.2)),
    ("line", "n3", "NARRATOR", "Five pencil mice. |0.45| Three pumpkins. |0.45| One flower. |0.55| And a note at the top... that took nearly an hour.", dict(gap=0.5)),
    ("beat", "letters", 1.6),
    ("line", "n4", "NARRATOR", "She left it downstairs, by the pumpkin's warm light, | and climbed up to bed, with a yawn, and goodnight.", dict(gap=0.3)),
    ("beat", "stairs", 1.6),
    ("line", "n5", "NARRATOR", "But a drawing left out on All Hallows' Eve... |0.6| when the old clock strikes twelve... |0.7| has a trick up its sleeve.", dict(gap=0.4)),
    ("beat", "chimes", 5.6),

    # ---------------------------------------------------------------- WAKING
    ("line", "w1", "WEDGE", "Hmm...? |0.6| Oh. |0.5| Oh, my. |0.7| I appear to have a tail.", dict(gap=0.3)),
    ("line", "b1", "BISCUIT", "I've got corners! Look at me, I'm a square! |0.4| Is that bad? I feel like it's good.", dict(gap=0.5)),
    ("line", "c1", "CRUMB", "We're ^alive! |0.3| We're actually, really ^alive!", dict(gap=0.35)),
    ("line", "p1", "PIP", "It's so _dark out there. |0.5| Is it always this dark... outside the paper?", dict(gap=0.7)),
    ("line", "w2", "WEDGE", "Only on Halloween, little one. |0.5| Stay close to me.", dict(gap=0.6)),
    ("beat", "popup", 2.2),
    ("line", "c2", "CRUMB", "Look! Words! |0.5| T... |0.35| O... |0.35| O... |0.5| Too... Mom?", dict(gap=0.2)),
    ("line", "b2", "BISCUIT", "She spelled it wrong. |0.35| It's one O. Everybody knows it's one O.", dict(gap=0.45)),
    ("line", "c3", "CRUMB", "Maybe the extra O is a ghost! |0.3| Oooo!", dict(gap=0.5)),
    ("beat", "oooo", 3.4),
    ("line", "b3", "BISCUIT", "That wasn't me.", dict(gap=0.2)),
    ("line", "p2", "PIP", "That wasn't me, either.", dict(gap=0.5)),
    ("line", "c4", "CRUMB", "It was the O.", dict(gap=0.7)),

    # ---------------------------------------------------------------- THE CAT
    ("beat", "eyes", 2.6),
    ("line", "k1", "CAT", "Well, well, well. |0.6| Mice. |0.6| On my table.", dict(gap=0.0)),
    ("beat", "catrise", 1.0),
    ("line", "w3", "WEDGE", "We're not real mice, cat. We're only pencil. |0.4| You can't eat pencil.", dict(gap=0.4)),
    ("line", "k2", "CAT", "Eat you? |0.3| Oh, darling, no. |0.5| I only came to tell you how this story ends.", dict(gap=0.6)),
    ("line", "k3", "CAT", "Tomorrow, she'll look at you for one minute. |0.45| Then a drawer. |0.4| Then a box. |0.6| And one gray morning... the _recycling bin. |0.4| Right on top of the pumpkin guts.", dict(gap=0.5)),
    ("line", "p3", "PIP", "Is... |0.3| is that true?", dict(gap=0.9)),
    ("line", "k4", "CAT", "Pencil _fades, little one. |0.8| Everything... _fades.", dict(gap=0.7)),
    ("beat", "silence", 1.6),
    ("line", "w4", "WEDGE", "She did draw me... very lightly. |0.6| At the edges.", dict(gap=0.2)),
    ("beat", "crumbwalks", 1.8),
    ("line", "c5", "CRUMB", "But look how hard she pressed on these. |0.4| You can see the dents from the back of the page.", dict(gap=0.2)),
    ("line", "c6", "CRUMB", "Even if the pencil fades... |0.6| the paper ^remembers.", dict(gap=0.6)),
    ("line", "p4", "PIP", "Maybe it isn't a mistake at all. |0.7| Too. |0.5| Like... I love you, ^too. |0.6| Because her mom always says it ^first.", dict(gap=1.0)),
    ("line", "b4", "BISCUIT", "Okay. |0.5| That's... |0.4| that's the best spelling mistake I've ever heard.", dict(gap=0.9)),
    ("line", "k5", "CAT", "Nobody ever draws the cat, you know. |0.6| Not the black one. |0.6| We're supposed to be bad _luck.", dict(gap=1.0)),
    ("line", "c7", "CRUMB", "There's room in our picture. |0.5| Right next to the flower.", dict(gap=0.9)),
    ("line", "k6", "CAT", "Humph.", dict(gap=1.0)),

    # ---------------------------------------------------------------- THE MONSTER
    ("beat", "thumps", 4.2),
    ("line", "b5", "BISCUIT", "Something's coming down the stairs!", dict(gap=0.0)),
    ("line", "p5", "PIP", "It's _huge! |0.4| It has... _horns!", dict(gap=0.25)),
    ("line", "w5", "WEDGE", "Everyone, back on the page! Quick! |0.35| And don't you dare blink.", dict(gap=0.2)),
    ("beat", "scramble", 2.6),
    ("beat", "momenter", 3.0),
    ("line", "m1", "MOM", "Who left the pumpkin burning...?", dict(gap=0.0)),
    ("beat", "pickup", 2.4),
    ("line", "m2", "MOM", "Too... |0.4| Mom... |0.6| I love you.", dict(gap=0.3)),
    ("line", "m3", "MOM", "Two O's. |0.8| Last year, it was just a heart... and a squiggle.", dict(gap=0.9)),
    ("line", "m4", "MOM", "Someday you'll spell it right... |0.7| and I'm going to _miss this so much.", dict(gap=1.0)),
    ("beat", "hug", 1.4),
    ("line", "m5", "MOM", "I ^love you ^too, baby. |0.6| With two O's.", dict(gap=0.2)),
    ("beat", "fridge", 3.4),
    ("line", "m6", "MOM", "And you, mister. |0.4| No eating my drawings.", dict(gap=0.2)),
    ("beat", "mrrp", 1.2),
    ("line", "m7", "MOM", "Was that one always upside down?", dict(gap=0.6)),
    ("beat", "momleave", 2.6),

    # ---------------------------------------------------------------- THE FRIDGE
    ("beat", "wake2", 2.2),
    ("line", "g1", "GHOST", "Boo! |0.7| Sorry. Habit.", dict(gap=0.0)),
    ("line", "s1", "SUN", "Welcome to the fridge, little ones.", dict(gap=0.5)),
    ("line", "p6", "PIP", "Does this mean... |0.4| we get to ^stay?", dict(gap=0.6)),
    ("line", "s2", "SUN", "Sweetheart, look at me. I'm purple, and one of my eyes is bigger than the other. |0.6| Nobody gets taken off the fridge. |0.5| Especially not the wonky ones.", dict(gap=0.5)),
    ("line", "b6", "BISCUIT", "Great. Love that. |0.4| Could somebody flip me over?", dict(gap=0.5)),
    ("beat", "catcurl", 1.6),
    ("line", "k8", "CAT", "Goodnight, pencil mice.", dict(gap=0.0)),
    ("line", "c8", "CRUMB", "Goodnight, cat. |0.6| Tomorrow, we draw him.", dict(gap=0.6)),
    ("line", "t1", "TILT", "Hmm...? |0.5| Did I miss anything?", dict(gap=0.8)),
    ("line", "b7", "BISCUIT", "Nope! Nothing! |0.3| Go back to sleep.", dict(gap=0.5)),

    # ---------------------------------------------------------------- EPILOGUE
    ("beat", "exterior", 1.8),
    ("line", "m8", "MOM", "Love you too, pumpkin.", dict(gap=0.0)),
    ("line", "n6", "NARRATOR", "Now pencil will fade, as all pencil lines do... |0.5| and someday she'll spell it with one O, not two.", dict(gap=0.9)),
    ("line", "n7", "NARRATOR", "But a mom is like paper, and this much is true: |0.6| she ^remembers how hard you pressed... |0.6| I ^love you.", dict(gap=0.6)),
    ("beat", "morning", 1.4),
    ("line", "n8", "NARRATOR", "Happy Halloween.", dict(gap=0.0)),
    ("beat", "end", 4.5),
]
