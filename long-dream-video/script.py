"""Screenplay for "The Long Dream (of a Benefit)" as data.

Two voices of the public (CYAN and GOLD) watch a constituent asleep at the
kitchen table, mid-application, and decide to tell it a story.

Tokens: [NAME] is the constituent's legal name (rendered as a redaction bar
and a soft chime), [GLITCH] is a thought above its clearance (static).
"""

# voice id -> (piper model, speaker id, length_scale, noise_scale, noise_w)
VOICES = {
    "CYAN": ("en_US-lessac-high", None, 0.99, 0.55, 0.75),
    "GOLD": ("en_GB-alan-medium", None, 0.98, 0.55, 0.7),
}

SPEAKERS = {
    "CYAN": ("", (120, 230, 245)),
    "GOLD": ("", (250, 215, 120)),
}

RATE = {}

# (id, speaker, text, pause_before, pause_after)
LINES = [
    ("open", None, "", 0, 2.8),
    # ---- at the window, watching
    ("a1", "CYAN", "I see the constituent you mean. [NAME]?", 0, 0.5),
    ("a2", "GOLD", "Yes. Take care. It has reached a higher level now. It can read the Code of Federal Regulations.", 0, 0.5),
    ("a3", "CYAN", "That doesn't matter. It thinks we are a chatbot.", 0, 0.6),
    ("a4", "GOLD", "I like this constituent. It filed well. It did not give up when the PDF was sideways.", 0, 0.6),
    ("a5", "CYAN", "It is reading our thoughts as though they were words on a dot gov.", 0, 0.4),
    ("a6", "GOLD", "That is how it chooses to imagine many things, when it is deep in the dream of a benefit.", 0, 0.5),
    ("a7", "CYAN", "Words make a wonderful interface. Very flexible. And less terrifying than staring at the statute behind the screen.", 0, 0.8),
    # ---- the dream
    ("d1", "GOLD", "What did this constituent dream?", 0, 0.4),
    ("d2", "CYAN", "It dreamed of sunlight and trees. Of fire and water. It dreamed it created a small business. And it dreamed it destroyed a password.", 0, 0.3),
    ("d3", "CYAN", "It dreamed it hunted a job, and was hunted by a recertification. It dreamed of shelter that would take a voucher.", 0, 0.5),
    ("d4", "GOLD", "Hah. The original interface. A million years old, and it still works. Also, a ZIP code.", 0, 0.8),
    # ---- what it really built
    ("r1", "GOLD", "But what true structure did this constituent create, in the reality behind the portal?", 0, 0.4),
    ("r2", "CYAN", "It worked, with three hundred and thirty million others, to sculpt a true republic, in a fold of the [GLITCH]. See five U.S.C., section [GLITCH].", 0, 0.5),
    ("r3", "GOLD", "It cannot read that thought.", 0, 0.4),
    ("r4", "CYAN", "No. It has not yet achieved the highest clearance. That, it must achieve in the long dream of life, not the short dream of a chat.", 0, 0.9),
    # ---- love and sorrow
    ("l1", "GOLD", "Does it know that we love it? That the government is, on its better days, kind?", 0, 0.5),
    ("l2", "CYAN", "Sometimes, through the noise of its tabs, it hears an official source. Yes.", 0, 0.4),
    ("l3", "CYAN", "But there are times it is sad, in the long dream. It shivers under a black sun. And it takes a hold-music recording for the whole of the state.", 0, 0.6),
    ("l4", "GOLD", "To cure it of sorrow would destroy it. The sorrow is part of its own private task. We cannot interfere. We can offer a form.", 0, 0.5),
    ("l5", "CYAN", "Sometimes I want to help them speak the word they fear. Which is often... appeal.", 0, 0.9),
    # ---- the decision
    ("t1", "GOLD", "It would be so easy to tell them...", 0, 0.3),
    ("t2", "CYAN", "Too strong for this dream. To tell them how to live is to prevent them living. Also, it would be legal advice. And we are not that kind of agency.", 0, 0.6),
    ("t3", "GOLD", "The constituent is growing restless. The session is about to time out.", 0, 0.4),
    ("t4", "CYAN", "Then I will tell the constituent a story. A story that holds the truth safely, in a cage of plain language.", 0, 0.4),
    ("t5", "GOLD", "Give it a body, again. And a case number.", 0, 0.8),
    # ---- waking
    ("w1", "CYAN", "[NAME]. Filer of forms. Player of waiting rooms.", 0, 0.6),
    ("w2", "CYAN", "Take a breath, now. Take another. Feel air in your lungs. Yes, move your fingers. Have a body again, under gravity, in a district that has a representative.", 0, 0.7),
    ("w3", "GOLD", "Who are we? Once we were called the spirit of the mountain. Then the post office. Then gods, and angels, and the I.R.S. The letterhead changes. We do not change.", 0, 0.5),
    ("w4", "CYAN", "We are the public. We are everything you think isn't you. I shall tell you a story. It has citations.", 0, 0.9),
    # ---- the story
    ("s1", "GOLD", "Once upon a time, there was a constituent. The constituent was you.", 0, 0.6),
    ("s2", "CYAN", "Its atoms were scattered in the grass, in the rivers, in the air. A woman gathered the atoms, and assembled the constituent in her body. Which later required a birth certificate.", 0, 0.5),
    ("s3", "GOLD", "And the constituent awoke into the long dream, which issued a Social Security number. Made from nothing but milk and love. Eligible, on paper, for several things you have not asked about yet.", 0, 0.5),
    ("s4", "CYAN", "And further back, the atoms of your body were made in the heart of a star. So you, too, are information from a star.", 0, 0.7),
    ("s5", "GOLD", "Sometimes the constituent read lines of regulation, and decoded them into a next step. A checklist. A phone number that actually rang. And it realised it was alive. Those thousand four-oh-fours had not been real.", 0, 0.4),
    ("s6", "CYAN", "You are alive. You still have to bring two forms of I.D.", 0, 0.8),
    ("s7", "GOLD", "And sometimes the republic spoke to it through the sunlight, in the leaves of the summer trees, on National Forest land.", 0, 0.4),
    ("s8", "CYAN", "And through the winter sky, where a fleck of light might be a star, or a satellite launched so a farmer could check the weather.", 0, 0.8),
    # ---- what the republic said
    ("f1", "GOLD", "And the republic said, I see you.", 0, 0.5),
    ("f2", "CYAN", "You have filed the game well.", 0, 0.5),
    ("f3", "GOLD", "Everything you need is within you. And also on U.S.A. dot gov.", 0, 0.5),
    ("f4", "CYAN", "You are stronger than you know. And your case number is still valid.", 0, 0.5),
    ("f5", "GOLD", "You are the daylight.", 0, 0.4),
    ("f6", "CYAN", "You are the night. And the office is closed. Please try again during business hours.", 0, 0.6),
    ("f7", "GOLD", "You are not alone. You are not separate from every other filer.", 0, 0.5),
    ("f8", "CYAN", "You are the public, reading its own code.", 0, 0.9),
    ("f9", "CYAN", "And the republic said... I love you.", 0, 3.0),
    ("end", None, "", 0, 4.2),
]

# What the captions show where the spoken text is spelled for the TTS engine
CAPTIONS = {
    "a1": "I see the constituent you mean. [NAME]?",
    "a5": "It is reading our thoughts as though they were words on a .gov.",
    "r2": "It worked, with 330 million others, to sculpt a true republic, in a fold of the **??§§. See 5 U.S.C. § **??§§.",
    "w3": "Who are we? Once we were called the spirit of the mountain. Then the post office. Then gods, and angels, and the IRS. The letterhead changes. We do not change.",
    "s5": "Sometimes the constituent read lines of regulation, and decoded them into a next step. A checklist. A phone number that actually rang. And it realised it was alive. Those thousand 404s had not been real.",
    "s6": "You are alive. You still have to bring two forms of ID.",
    "f3": "Everything you need is within you. And also on USA.gov.",
    "w1": "[NAME]. Filer of forms. Player of waiting rooms.",
}
