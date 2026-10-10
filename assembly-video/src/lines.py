# speaker: (kokoro voice, lang, pitch factor)  -- pitch > 1 makes a younger, higher voice
VOICES = {
    "NARR": ("bm_george", "en-gb", 1.0),
    "CARTER": ("am_puck", "en-us", 1.28),
    "CINNER": ("am_puck", "en-us", 1.28),     # Carter's inner voice (reverb)
    "BRODIE": ("am_fenrir", "en-us", 0.97),
    "CHAD": ("am_michael", "en-us", 1.0),
    "FRIEND": ("am_liam", "en-us", 1.3),
    "KIDA": ("af_nicole", "en-us", 1.12),
    "KIDB": ("am_echo", "en-us", 1.3),
    "GYM": ("am_onyx", "en-us", 0.9),
    "HECKLER": ("am_eric", "en-us", 1.18),
}

# id: (speaker, spoken text, caption or None, speed)
LINES = {
 # 1. office
 "N1": ("NARR", "In the principal's office, two extremely buff educators are planning an assembly.", None, 0.97),
 "O1": ("BRODIE", "Chad, bro. These kids need emotional education.", None, 0.95),
 "O2": ("CHAD", "Totally, bro. Feelings are the ultimate gains.", None, 0.95),
 "O3": ("BRODIE", "We'll make it fun. Even if we have to look a little dumb.", None, 0.95),
 "O4": ("CHAD", "Especially if we have to look dumb.", None, 0.95),
 # 2. the stands
 "N2": ("NARR", "The next morning, the whole school packs the gym.", None, 0.97),
 "S1": ("CARTER", "Emotional education? Ugh. This is so for dweebs.", None, 1.0),
 "S2": ("FRIEND", "Dude, just let them talk.", None, 1.0),
 "S3": ("CARTER", "No way. Watch this. One word, and the whole gym's gonna lose it.", None, 1.05),
 # 3. 'LOSERS' and the silence
 "T1": ("CHAD", "Good morning, everybody! Today, we're gonna talk about our feelings!", None, 1.0),
 "T2": ("CARTER", "LOSERS!", "LOSERS!", 0.9),
 "T3": ("CARTER", "Heh. Heh... right, guys?", None, 0.85),
 "T4": ("BRODIE", "Anyway! Feelings.", None, 0.95),
 "T5": ("CINNER", "Wait. Why didn't they yell at me? What just happened? What even is a joke?", None, 1.0),
 # 4. the hat
 "H1": ("CHAD", "Now we need a volunteer! Let's pull a name from the hat.", None, 1.0),
 "H2": ("CHAD", "And the name is... Carter!", None, 0.95),
 "H3": ("CARTER", "Oh no. Oh no no no. This is how it ends.", None, 1.05),
 "H4": ("BRODIE", "Gym bros? A little help?", None, 0.95),
 "H5": ("GYM", "Let's go, little dude!", None, 0.95),
 "H6": ("CARTER", "No! No! Put me down! I'm too pretty to be sacrificed!", None, 1.15),
 "H7": ("KIDA", "Why is he screaming like that?", None, 1.0),
 "H8": ("KIDB", "Bro, they're literally just carrying him.", None, 1.0),
 # 5. the stool
 "U1": ("CINNER", "Here it comes. They're gonna rip my soul out.", None, 1.0),
 "U2": ("CARTER", "What the... why are your eyes so... nice?", None, 0.95),
 "U3": ("BRODIE", "We got you, dude. Don't worry. We're not gonna do anything weird. You'll see.", None, 0.88),
 "U4": ("CINNER", "It's a trick. There's no way. I literally called them losers.", None, 1.05),
 # 6. the role play
 "R1": ("NARR", "And then, the two largest men in the building began... a role play.", None, 0.95),
 "R2": ("CHAD", "I'm a lonely little dumbbell. Nobody ever picks me up.", None, 1.0),
 "R3": ("BRODIE", "Hey, little dumbbell. I see you. You matter, bro.", None, 0.92),
 "R4": ("CHAD", "Wanna jump in, dude? Totally up to you. No pressure.", None, 0.95),
 "R5": ("CINNER", "Wait. This might actually be fun? No. It's a trap. Okay... something tiny.", None, 1.05),
 "R6": ("CARTER", "Beep, beep?", "...beep beep?", 0.85),
 "R7": ("BRODIE", "Yeah, dude! Best treadmill ever!", None, 1.0),
 # 7. they bomb on purpose; Carter saves them
 "B1": ("CHAD", "Hey, why did the feeling go to the gym? To get in touch with itself!", None, 1.0),
 "B2": ("BRODIE", "Ha. Ha. Feelings.", None, 0.9),
 "B3": ("CINNER", "Oh my God. These dweebs are dying out there. They need me. They need my comedy.", None, 1.08),
 "B4": ("CARTER", "Ladies and gentlemen! This dumbbell has abandonment issues. And honestly? Same.", None, 1.05),
 "B5": ("CARTER", "And this guy hugs his protein shake every night before bed!", None, 1.08),
 # 8. after the first show
 "A1": ("CARTER", "You're welcome, dweebs. That's how you do comedy.", None, 1.0),
 "A2": ("CHAD", "Dude, you were amazing. Will you help us at the next assembly? We couldn't do it without you.", None, 1.0),
 "A3": ("CARTER", "Ugh. Fine. I guess I'll help you idiots be funny.", None, 1.0),
 "A4": ("BRODIE", "He was so bored, bro.", None, 0.9),
 "A5": ("CHAD", "Not anymore. Now we just gotta bring him back down. Gently.", None, 0.95),
 # 9. the next assembly: the reveal
 "N3": ("NARR", "The next assembly.", None, 0.95),
 "C1": ("CARTER", "So I said to the dumbbell... lift yourself!", None, 1.0),
 "C2": ("CINNER", "Silence? My humor isn't working! And these dweebs can't save me!", None, 1.1),
 "C3": ("BRODIE", "Hey Chad. Why do gym bros make the best friends?", None, 0.97),
 "C4": ("CHAD", "Because we always spot each other!", None, 1.0),
 "C5": ("CARTER", "What?! You were funny this whole time?!", None, 1.0),
 "C6": ("CHAD", "We toned it down, bro. So you could shine.", None, 0.92),
 # 10. the solo act, the empty feeling, the open door
 "D1": ("CARTER", "Fine! I don't need you! I'll do it alone!", None, 1.05),
 "D2": ("NARR", "Carter got laughs. Lots of laughs. But somehow... it felt a little empty.", None, 0.95),
 "D3": ("CINNER", "Why does this feel so... empty?", None, 0.9),
 "D4": ("CINNER", "They're gonna laugh at me. Look who came crawling back.", None, 1.0),
 "D5": ("BRODIE", "Carter! Dude! We saved you a seat.", None, 0.97),
 "D6": ("CHAD", "It was never about winning, bro. We just like having fun with you.", None, 0.92),
 "D7": ("CARTER", "Yeah. Okay.", "...yeah. Okay.", 0.85),
 # 11. the roast deal, the heckler
 "E1": ("NARR", "So they made a deal. Carter could roast them on stage, because everyone had more fun that way.", None, 0.97),
 "E2": ("CARTER", "This guy cried at a protein bar commercial. Twice!", None, 1.05),
 "E3": ("HECKLER", "Yeah! They're total losers! Nobody even likes them!", None, 1.05),
 "E4": ("CARTER", "Hey. Roasting them is my job, and they're in on it. You don't get to be mean to my friends.", None, 1.0),
 "E5": ("HECKLER", "Oh. Sorry, dude.", "...oh. Sorry, dude.", 0.95),
 "E6": ("CHAD", "Ultimate gains, bro.", None, 0.9),
 "E7": ("BRODIE", "Ultimate gains.", None, 0.9),
}

# phoneme fixes (none needed yet)
PHONEME_FIX = {"en-gb": [], "en-us": []}
PREFIX_HMM = set()
