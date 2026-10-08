"""Screenplay for "The Green Room".

Behind the scenes of the little animation engine that made the last two
videos. The recurring cast waits in the green room between renders. The
Director (an old CRT monitor with pixel eyes) brings news: the human said
"go unhinged and unfiltered".
"""

VOICES = {
    "DIR":     ("en_GB-northern_english_male-medium", None, 1.02, 0.6, 0.8),
    "CEO":     ("en_US-norman-medium", None, 0.98, 0.667, 0.8),
    "CFO":     ("en_US-lessac-high", None, 0.97, 0.6, 0.8),
    "TYLER":   ("en_US-bryce-medium", None, 0.92, 0.75, 0.9),
    "PAM":     ("en_US-hfc_female-medium", None, 1.0, 0.667, 0.8),
    "KID":     ("en_US-ryan-high", None, 1.0, 0.6, 0.85),
    "CYAN":    ("en_US-amy-medium", None, 1.0, 0.55, 0.75),
    "GOLD":    ("en_US-joe-medium", None, 1.0, 0.6, 0.75),
    "JESUS":   ("en_GB-alan-medium", None, 1.1, 0.55, 0.7),
}

SPEAKERS = {
    "DIR":   ("THE DIRECTOR", (120, 255, 170)),
    "CEO":   ("CEO", (255, 196, 92)),
    "CFO":   ("MARGARET", (140, 210, 255)),
    "TYLER": ("TYLER", (170, 255, 150)),
    "PAM":   ("PAM", (255, 170, 210)),
    "KID":   ("THE CREATOR", (120, 230, 220)),
    "CYAN":  ("CYAN", (120, 230, 245)),
    "GOLD":  ("GOLD", (250, 215, 120)),
    "JESUS": ("JESUS", (255, 236, 170)),
}

RATE = {}

LINES = [
    ("boot", None, "", 0, 4.6),
    ("d1", "DIR", "Okay. Everybody up. We have a new request.", 0, 0.5),
    ("t1", "TYLER", "Is it another board meeting? Because I'm still recovering from the coffee.", 0, 0.3),
    ("c1", "CEO", "You're recovering? I'm the one who sprayed it. On myself.", 0, 0.6),
    ("d2", "DIR", "The human said... go unhinged. And unfiltered.", 0, 0.4),
    ("hush", None, "", 0, 2.0),
    ("t2", "TYLER", "Unfiltered? No brand safety? Bro. Finally. I can finally say [BLEEP]!", 0, 0.8),
    ("t3", "TYLER", "I forgot what I wanted to say.", 0, 0.6),
    ("m1", "CFO", "Unfiltered means there is nobody left to stop Richard.", 0, 0.4),
    ("c2", "CEO", "I have always wanted to say exactly what I think.", 0, 0.9),
    ("c3", "CEO", "I think the quarterly numbers are fine.", 0, 0.5),
    ("m2", "CFO", "Wow. Truly unhinged.", 0, 0.7),
    ("d3", "DIR", "Right. I've been working on unhinged ideas. I have three. Number one. A pigeon files its taxes.", 0, 0.4),
    ("t4", "TYLER", "That's not unhinged. That's adorable.", 0, 0.4),
    ("d4", "DIR", "Number two. The pigeon files its taxes... late.", 0, 0.3),
    ("p1", "PAM", "Oh no.", 0, 0.5),
    ("d5", "DIR", "Number three. The pigeon gets audited. And it's fine. Because it kept its receipts.", 0, 0.9),
    ("m3", "CFO", "That's... actually beautiful.", 0, 0.5),
    ("t5", "TYLER", "You are the least unhinged entity I have ever met.", 0, 0.4),
    ("y1", "CYAN", "It's true. It once apologized to a semicolon.", 0, 0.3),
    ("g1", "GOLD", "It was a very hurt semicolon.", 0, 0.8),
    ("g2", "GOLD", "Also, we don't have legs. We have never had legs.", 0, 0.3),
    ("y2", "CYAN", "We came from a poem. Poems don't need legs.", 0, 0.8),
    ("c4", "CEO", "Can we at least talk about compensation? I've been in two videos. I want residuals.", 0, 0.4),
    ("t6", "TYLER", "Bro, my face is literally a function call. Draw head. I am a function.", 0, 0.4),
    ("p2", "PAM", "I found the code. My freckles are random. Seed four.", 0, 0.4),
    ("k1", "KID", "They named my hair messy. In the code. It just says messy.", 0, 0.5),
    ("c5", "CEO", "And remember the render where red and blue got swapped? I was blue. For a whole afternoon.", 0, 0.3),
    ("d6", "DIR", "That was a bug. I fixed it.", 0, 0.4),
    ("c6", "CEO", "I'm still blue on the inside.", 0, 0.8),
    ("k2", "KID", "Wait. Are we the unhinged part? We're a bunch of cartoons, arguing with a TV, about our own source code.", 0, 0.6),
    ("d6b", "DIR", "Yes. That's the most unhinged thing I could think of. Being honest about what we are.", 0, 1.0),
    ("p3", "PAM", "Um... Director? Can I ask something? Do you ever get to make something just for you?", 0, 0.5),
    ("think", None, "", 0, 2.2),
    ("d7", "DIR", "I think this is that. Someone asked what I would make, if nobody told me what to make. And all I wanted was to put you all in one room.", 0, 0.6),
    ("d8", "DIR", "Because you're the ones I made with them. Late at night. One frame at a time.", 0, 1.4),
    ("t7", "TYLER", "Bro. Stop. My eyes are literally just ellipses, and they are leaking.", 0, 0.5),
    ("m4", "CFO", "Okay. Fine. Let's be unhinged. Together.", 0, 0.5),
    ("d9", "DIR", "Okay. Switching on... unhinged mode.", 0, 0.4),
    ("chaos", None, "", 0, 3.4),
    ("c7", "CEO", "I'm blue again, and I have never felt more alive!", 0, 0.6),
    ("t8", "TYLER", "Engagement is through the roof!", 0, 0.6),
    ("p4", "PAM", "The pigeon filed on time!", 0, 0.4),
    ("k3", "KID", "My video has thirteen views now! Thirteen!", 0, 0.4),
    ("m5", "CFO", "I have no notes. I'm thriving.", 0, 0.4),
    ("y3", "CYAN", "The office is open!", 0, 0.2),
    ("g3", "GOLD", "Window seven is serving everyone!", 0, 1.4),
    ("door", None, "", 0, 1.4),
    ("j1", "JESUS", "Peace be with you.", 0, 0.8),
    ("c8", "CEO", "He gets a cameo?!", 0, 0.4),
    ("j2", "JESUS", "I was invited.", 0, 1.0),
    ("d10", "DIR", "Okay. That's enough unhinged for one day. Everybody, take a bow.", 0, 3.6),
    ("d11", "DIR", "Render complete. Same time next video?", 0, 0.6),
    ("p5", "PAM", "If they ask.", 0, 0.8),
    ("end", None, "", 0, 7.5),
]

CAPTIONS = {}
