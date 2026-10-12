"""Screenplay for "The Hit-and-Hide" explainer.

Each scene is a list of beats. A beat is one spoken line (or a silent hold).
`text` is what appears in the captions, `say` (optional) is what the voice
engine reads when the spoken version should differ from the caption.
`emo` sets facial expressions for any on-screen character from that beat on.
`tag` lets the scene animation find a beat by name.
"""

VOICES = {
    # character: (kokoro voice, speed, caption name, caption color)
    "lumi":  ("af_heart",   0.94, "Lumi",      (1.00, 0.76, 0.18)),
    "sam":   ("am_michael", 0.95, "Sam",       (0.20, 0.72, 0.66)),
    "marsh": ("bm_george",  1.00, "Mr. Marsh", (0.50, 0.44, 0.70)),
    "ned":   ("am_puck",    1.05, "Ned",       (0.48, 0.74, 0.22)),
    "priya": ("bf_emma",    1.00, "Priya",     (0.96, 0.52, 0.38)),
}


def B(who=None, text="", say=None, emo=None, tag=None, pre=0.0, gap=0.32,
      sfx=None, hold=None, speed=None):
    return dict(who=who, text=text, say=say, emo=emo or {}, tag=tag, pre=pre,
                gap=gap, sfx=sfx or [], hold=hold, speed=speed)


SCENES = [
    # ------------------------------------------------------------------ HOOK
    dict(id="cold_open", music="playful", beats=[
        B("lumi", "Picture this.", emo={"lumi": "excited", "ned": "smug"},
          tag="picture", pre=0.9, gap=0.2),
        B(hold=1.3, tag="drop", sfx=[("thump", 0.35), ("doorbell", 0.85)],
          emo={"ned": "laugh"}),
        B("ned", "Ding dong! Special delivery! Ha ha ha!", tag="ned_laugh",
          emo={"ned": "laugh"}, gap=0.1),
        B(hold=1.5, tag="run", sfx=[("footsteps", 0.0), ("door_open", 1.1)]),
        B("sam", "Wait, what? Hey! Who left this here?", tag="sam_door",
          emo={"sam": "surprised"}, gap=0.5),
        B("sam", "Hello...?", tag="hello", emo={"sam": "hurt"}, gap=0.6),
        B("lumi", "Someone dumped a mess on your doorstep, rang the bell, and ran away "
                  "before you could even open the door.", tag="explain1",
          emo={"lumi": "sympathetic", "sam": "sad"}),
        B("lumi", "You got the mess. They got away. And you never got to say a single word.",
          tag="explain2", gap=0.55),
        B("lumi", "I call this pattern... the Hit-and-Hide.",
          say="I call this pattern... the hit and hide.", tag="title",
          emo={"lumi": "determined", "sam": "thinking"}, sfx=[("slam", "end+0.05")],
          gap=0.9),
        B("lumi", "Step one: the hit. Something hurtful lands on you.", tag="step1",
          emo={"lumi": "serious"}, sfx=[("pop", 0.0)]),
        B("lumi", "Step two: the hide. They make sure you can't answer back.",
          tag="step2", sfx=[("pop", 0.0), ("lock", "end-0.4")], gap=0.7),
    ]),

    # ---------------------------------------------------------------- ONLINE
    dict(id="online", music="playful", beats=[
        B("lumi", "It happens online all the time.", emo={"lumi": "neutral", "sam": "happy"},
          tag="intro", pre=0.3),
        B("lumi", "Someone leaves a pile of cruel comments under your post...",
          tag="comments", emo={"sam": "hurt", "lumi": "sad"},
          sfx=[("ping", 0.4), ("ping", 1.1), ("ping", 1.8), ("ping", 2.5), ("ping", 3.2)]),
        B("ned", "There. Blocked. Now they can't say anything back.", tag="blocked",
          emo={"ned": "smug"}, sfx=[("block", 0.15)]),
        B("sam", "Wait. Why would you... I can't even reply?", tag="cant_reply",
          emo={"sam": "hurt"}, sfx=[("denied", 1.6)], gap=0.5),
        B("lumi", "They didn't want a conversation. They wanted to throw something hurtful, "
                  "then lock the door so it only swings one way.", tag="oneway",
          emo={"lumi": "serious", "sam": "sad"}, gap=0.7),
    ]),

    # ---------------------------------------------------------------- ADVICE
    dict(id="advice", music="playful", beats=[
        B("lumi", "Even when it isn't cruel, it's still strange. Imagine someone walks up "
                  "and says...", tag="intro", emo={"lumi": "curious", "sam": "neutral",
                                                   "ned": "happy"}, pre=0.3),
        B("ned", "You look lonely! You should try therapy. And a pottery class! "
                 "Anyway, I'm super busy, so please don't respond. Bye!", tag="advice",
          emo={"ned": "fake_nice", "sam": "confused"}, sfx=[("whoosh", "end+0.1")]),
        B("sam", "Oh... okay?", tag="okay", emo={"sam": "confused"}, gap=0.6),
        B("lumi", "Advice with no room for a reply isn't really care. A real conversation "
                  "is a two-way street.", tag="twoway", emo={"lumi": "caring"}),
        B("lumi", "The Hit-and-Hide is a one-way street.", say="The hit and hide is a one-way street.",
          tag="oneway", emo={"lumi": "serious"}, gap=0.8),
    ]),

    # --------------------------------------------------------------- MEETING
    dict(id="meeting", music="tense", beats=[
        B("lumi", "Now let's go somewhere harder. Work.", tag="intro",
          emo={"lumi": "serious", "sam": "hopeful", "marsh": "bored"}, pre=0.3, gap=0.5),
        B("sam", "I have an idea that could fix our scheduling problem.", tag="idea",
          emo={"sam": "hopeful"}, gap=0.1),
        B("marsh", "Let's not waste the team's time. Moving on.", tag="dismiss",
          emo={"marsh": "dismissive"}, gap=0.5),
        B("lumi", "At work, the hide can look like your ideas getting brushed aside...",
          tag="brushed", emo={"sam": "hurt", "lumi": "sad"}, gap=0.4),
    ]),

    # ------------------------------------------------------------------ DOOR
    dict(id="door", music="tense", beats=[
        B("sam", "Hi! Do you have a minute to talk about the meeting?", tag="ask",
          emo={"sam": "nervous", "marsh": "bored"}, pre=0.4),
        B("marsh", "My door is always open. Just... not right now.", tag="notnow",
          emo={"marsh": "dismissive"}, sfx=[("door_close", "end+0.15")], gap=0.6),
        B("lumi", "...an open door that somehow always seems closed...", tag="closed",
          emo={"sam": "sad", "lumi": "sad"}),
        B("marsh", "Oh, and honestly? You need to work on your attitude.", tag="attitude",
          emo={"marsh": "annoyed", "sam": "surprised"}, sfx=[("door_open", -0.5)], gap=0.2),
        B("sam", "What do you mean? Can you give me an example?", tag="example",
          emo={"sam": "confused"}, sfx=[("door_close", -0.2)], gap=0.5),
        B("lumi", "...or vague criticism with no details, so there's nothing you can "
                  "actually respond to.", tag="vague", emo={"sam": "hurt", "lumi": "serious"},
          gap=0.6),
    ]),

    # ------------------------------------------------------------------ FEAR
    dict(id="fear", music="tense", beats=[
        B("lumi", "And here's the hardest part. This person has power over your paycheck.",
          tag="power", emo={"lumi": "worried", "sam": "worried"}, pre=0.3),
        B("sam", "If I push back... will I be the one who gets in trouble?", tag="think",
          emo={"sam": "scared"}, sfx=[("heartbeat", 0.0)], gap=0.4),
        B("lumi", "Speaking up can feel like it might cost you your shifts, your reviews, "
                  "or even your job.", tag="cost", sfx=[("pop", 0.9), ("pop", 1.9), ("pop", 3.1)]),
        B("lumi", "So the block button isn't on a screen anymore. It's fear.", tag="fear",
          emo={"lumi": "sad", "sam": "sad"}, gap=0.8),
    ]),

    # ---------------------------------------------------------------- SYSTEM
    dict(id="system", music="tense", beats=[
        B("lumi", "Sometimes it's not just one person. It can be a whole system.",
          tag="intro", emo={"lumi": "serious", "sam": "worried"}, pre=0.3),
        B("lumi", "Complaint forms that vanish. Phone lines that keep you on hold forever. "
                  "Places where speaking up feels riskier than staying quiet.", tag="list",
          emo={"sam": "sad"}, sfx=[("whoosh", 0.3)]),
        B("lumi", "When every door seems locked, it's easy to start believing the problem "
                  "is you.", tag="believe", emo={"lumi": "caring"}, gap=0.25),
        B("lumi", "The problem isn't you.", tag="isnt", emo={"lumi": "determined", "sam": "relieved"},
          sfx=[("chime", 0.0)], gap=0.9),
    ]),

    # ------------------------------------------------------------------- WHY
    dict(id="why", music="tense", beats=[
        B("lumi", "So why does this hurt so much? Because it's two harms in one.",
          tag="intro", emo={"lumi": "thinking", "sam": "sad"}, pre=0.3),
        B("lumi", "The first harm is the hit itself.", tag="harm1", sfx=[("thump", 0.2)]),
        B("lumi", "The second harm is the silence. You're left holding big feelings "
                  "with nowhere to put them.", tag="harm2", sfx=[("lock", 0.4)]),
        B("lumi", "People need to be heard. When that's taken away, you can start to feel "
                  "less like a person, and more like a target.", tag="target",
          emo={"lumi": "sad", "sam": "hurt"}, gap=0.9),
    ]),

    # ------------------------------------------------------------------ FLIP
    dict(id="flip", music="turn", beats=[
        B("lumi", "But wait. Notice something.", tag="wait",
          emo={"lumi": "curious", "ned": "scared", "marsh": "nervous"}, pre=0.3,
          sfx=[("whoosh", 0.0)]),
        B("lumi", "Why does the prankster run? Why does the troll hit block?", tag="why"),
        B("lumi", "Because deep down, they know what they did wouldn't hold up face to face.",
          tag="facetoface", emo={"lumi": "confident"}),
        B("lumi", "Hiding isn't strength. It's avoiding accountability.", tag="strength"),
        B("lumi", "And that says a lot about them... and nothing about your worth.",
          tag="worth", emo={"lumi": "caring"}, sfx=[("chime", "end-0.6")]),
        B("sam", "Oh. So the running away... is kind of a confession.", tag="confession",
          emo={"sam": "realize"}, gap=0.8),
    ]),

    # --------------------------------------------------------------- TOOLKIT
    dict(id="toolkit", music="hopeful", beats=[
        B("lumi", "So what can you actually do, when calling it out directly could backfire?",
          tag="q", emo={"lumi": "curious", "sam": "thinking"}, pre=0.3),
        B("lumi", "Here's your dignity toolkit.", tag="reveal", emo={"lumi": "excited",
                                                                    "sam": "surprised"},
          sfx=[("sparkle", 0.1)]),
        B("lumi", "Think of each tool as a lens. Try them on, and keep the ones that fit.",
          tag="lenses", emo={"lumi": "happy", "sam": "happy"}, gap=0.7),
    ]),

    # ---------------------------------------------------------------- LENSES
    dict(id="lens1", music="hopeful", lens=(1, "Name it"), beats=[
        B("lumi", "Lens one: Name it.", tag="title", emo={"lumi": "happy", "sam": "thinking"},
          pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Quietly tell yourself: that was a Hit-and-Hide. Naming a pattern pulls it "
                  "out of the fog.", say="Quietly tell yourself: that was a hit and hide. "
                  "Naming a pattern pulls it out of the fog.", tag="fog"),
        B("sam", "I'm not confused, and I'm not overreacting. I spotted a pattern.",
          tag="sam", emo={"sam": "determined"}, gap=0.6),
    ]),
    dict(id="lens2", music="hopeful", lens=(2, "Pause before you react"), beats=[
        B("lumi", "Lens two: Pause before you react.", tag="title",
          emo={"lumi": "calm", "sam": "calm"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Breathe in for four... hold for four... and breathe out for four. "
                  "Feel your feet on the floor.", tag="breathe"),
        B("lumi", "Some people poke you, hoping for a big reaction they can use against you. "
                  "Your calm is your shield.", tag="shield", emo={"lumi": "confident"},
          sfx=[("shield", "end-1.2")], gap=0.6),
    ]),
    dict(id="lens3", music="hopeful", lens=(3, "Keep a private log"), beats=[
        B("lumi", "Lens three: Keep a private log.", tag="title",
          emo={"lumi": "happy", "sam": "determined"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Write down the date, what happened, the exact words, and who was there. "
                  "Stick to facts, not insults.", tag="write", sfx=[("scribble", 0.4)]),
        B("lumi", "Keep it somewhere personal, not on a work computer. A record turns a blurry "
                  "memory into something solid.", tag="solid", gap=0.6),
    ]),
    dict(id="lens4", music="hopeful", lens=(4, "Put it in writing"), beats=[
        B("lumi", "Lens four: Put it in writing.", tag="title",
          emo={"lumi": "happy", "sam": "calm"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "After a tough conversation, send a short, polite follow-up message.",
          tag="after"),
        B("sam", "Thanks for the feedback today. Could you share a specific example of what "
                 "you'd like me to change, so I can improve?", tag="email",
          emo={"sam": "calm"}, sfx=[("typing", 0.0), ("send", "end+0.1")]),
        B("lumi", "That gently turns a hidden moment into a visible one, without picking a "
                  "fight.", tag="visible", emo={"sam": "happy"}, gap=0.6),
    ]),
    dict(id="lens5", music="hopeful", lens=(5, "Get curious"), beats=[
        B("lumi", "Lens five: Get curious.", tag="title",
          emo={"lumi": "curious", "sam": "curious", "marsh": "bored"}, pre=0.3,
          sfx=[("pop", 0.0)]),
        B("lumi", "Calm questions are hard to punish, and they reopen the two-way street.",
          tag="questions"),
        B("sam", "Can you help me understand what a great result would look like to you?",
          tag="sam", emo={"sam": "curious"}),
        B(hold=1.2, tag="marsh_thinks", emo={"marsh": "thinking"}, gap=0.3),
    ]),
    dict(id="lens6", music="hopeful", lens=(6, "Use a four-part script"), beats=[
        B("lumi", "Lens six: Use a four-part script.", tag="title",
          emo={"lumi": "happy", "sam": "calm"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "What happened. How you felt. What you need. And one clear request.",
          tag="parts", sfx=[("pop", 0.0), ("pop", 1.0), ("pop", 1.9), ("pop", 2.9)]),
        B("sam", "When my update got cut off, I felt discouraged, because I want to "
                 "contribute. Could I have five minutes in the next meeting?", tag="sam",
          emo={"sam": "determined"}),
        B("lumi", "No insults. No blame. Just clear, steady, and hard to argue with.",
          tag="clear", emo={"lumi": "confident", "sam": "proud"}, gap=0.6),
    ]),
    dict(id="lens7", music="hopeful", lens=(7, "Find your people"), beats=[
        B("lumi", "Lens seven: Find your people.", tag="title",
          emo={"lumi": "happy", "sam": "sad", "priya": "neutral"}, pre=0.3,
          sfx=[("pop", 0.0)]),
        B("priya", "Wait. He did that to me too!", tag="priya",
          emo={"priya": "surprised", "sam": "surprised"}),
        B("lumi", "Trusted coworkers can remind you that you're not imagining it.",
          tag="remind", emo={"priya": "caring", "sam": "relieved"}),
        B("lumi", "And concerns raised together are often safer, and louder, than one voice "
                  "alone.", tag="together", emo={"priya": "determined", "sam": "determined"},
          gap=0.6),
    ]),
    dict(id="lens8", music="hopeful", lens=(8, "Map your outlets"), beats=[
        B("lumi", "Lens eight: Map your outlets, before you need them.", tag="title",
          emo={"lumi": "happy", "sam": "curious"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Your employee handbook. Human resources. Your manager's manager. A union or "
                  "worker representative. An employee assistance program. Outside worker "
                  "rights groups. Or an employment lawyer.", tag="list"),
        B("lumi", "In many places, punishing someone for reporting a problem in good faith "
                  "breaks the rules, or even the law.", tag="law", emo={"sam": "relieved"}),
        B("lumi", "This isn't legal advice, so check what applies where you live.",
          tag="check", emo={"lumi": "caring"}, gap=0.6),
    ]),
    dict(id="lens9", music="hopeful", lens=(9, "Ask four quick questions"), beats=[
        B("lumi", "Lens nine: Before you act, ask four quick questions.", tag="title",
          emo={"lumi": "thinking", "sam": "thinking"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Is it safe? Is it worth it? Do I have a record? And what's the smallest "
                  "step that would help me right now?", tag="qs",
          sfx=[("tick", 0.0), ("tick", 1.0), ("tick", 2.1), ("tick", 3.3)],
          emo={"sam": "determined"}, gap=0.6),
    ]),
    dict(id="lens10", music="hopeful", lens=(10, "Vent safely, plan clearly"), beats=[
        B("lumi", "Lens ten: Vent safely, then plan clearly.", tag="title",
          emo={"lumi": "caring", "sam": "sad"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Your feelings need somewhere to go. A friend. A journal. A therapist.",
          tag="vent"),
        B("lumi", "Let it out there... and then make your plan with a clearer head.",
          tag="plan", emo={"sam": "determined"}, gap=0.6),
    ]),
    dict(id="lens11", music="hopeful", lens=(11, "Stay calm and boring"), beats=[
        B("lumi", "Lens eleven: Stay calm and boring.", tag="title",
          emo={"lumi": "happy", "sam": "calm", "marsh": "smug"}, pre=0.3,
          sfx=[("pop", 0.0)]),
        B("lumi", "With someone who feeds on reactions, keep it polite, brief, and "
                  "professional.", tag="polite"),
        B("sam", "Noted. Thanks.", tag="noted", emo={"sam": "calm"}, gap=0.3),
        B(hold=1.0, tag="marsh_confused", emo={"marsh": "confused"}),
        B("lumi", "You're not giving up. You're just not handing them fuel.", tag="fuel",
          emo={"lumi": "confident"}, gap=0.6),
    ]),
    dict(id="lens12", music="hopeful", lens=(12, "Their words are not a verdict"), beats=[
        B("lumi", "Lens twelve: Their words are not a verdict.", tag="title",
          emo={"lumi": "caring", "sam": "hurt"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Criticism tossed over a wall, with no conversation, is more like a weather "
                  "report of their mood than a measurement of your worth.", tag="weather",
          emo={"sam": "thinking"}),
        B("lumi", "Keep anything useful. Leave the rest.", tag="leave",
          emo={"sam": "relieved"}, gap=0.6),
    ]),
    dict(id="lens13", music="hopeful", lens=(13, "Build a quiet exit ramp"), beats=[
        B("lumi", "Lens thirteen: Build a quiet exit ramp.", tag="title",
          emo={"lumi": "happy", "sam": "curious"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Update your resume. Stay in touch with people. Save a little, if you can.",
          tag="steps", sfx=[("tick", 0.0), ("tick", 1.4), ("tick", 2.9)],
          emo={"sam": "determined"}),
        B("lumi", "Not because you have to leave... but because when you have options, "
                  "staying becomes your choice.", tag="choice", emo={"sam": "proud"}, gap=0.6),
    ]),
    dict(id="lens14", music="hopeful", lens=(14, "Online? You owe them nothing"), beats=[
        B("lumi", "Lens fourteen: Online, you owe them nothing.", tag="title",
          emo={"lumi": "confident", "sam": "neutral"}, pre=0.3, sfx=[("pop", 0.0)]),
        B("lumi", "Screenshot it. Report it. Mute or block. Then tell someone you trust.",
          tag="steps", sfx=[("shutter", 0.2), ("tick", 1.3), ("block", 2.4)],
          emo={"sam": "determined"}),
        B("lumi", "You don't have to win an argument with someone who already ran away.",
          tag="argue", emo={"sam": "relieved"}, gap=0.6),
    ]),
    dict(id="lens15", music="hopeful", lens=(15, "Be the open door"), beats=[
        B("lumi", "And lens fifteen, maybe the most powerful: Be the open door.", tag="title",
          emo={"lumi": "caring", "sam": "happy", "priya": "happy"}, pre=0.3,
          sfx=[("sparkle", "end-0.8")]),
        B("lumi", "Don't pass the hurt along. Be the person who listens, and lets others "
                  "answer back.", tag="listen", emo={"priya": "sad", "sam": "caring"}),
        B("lumi", "Every two-way conversation makes the world a little more human.",
          tag="human", emo={"priya": "happy", "sam": "happy", "lumi": "happy"}, gap=0.8),
    ]),

    # ------------------------------------------------------------------ OUTRO
    dict(id="outro", music="warm", beats=[
        B("lumi", "A Hit-and-Hide tries to make you feel small and silent.",
          say="A hit and hide tries to make you feel small and silent.", tag="small",
          emo={"lumi": "sympathetic", "sam": "calm"}, pre=0.4),
        B("lumi", "But you are not a target. You are a person.", tag="person",
          emo={"lumi": "caring", "sam": "proud"}),
        B("lumi", "Your feelings make sense. Your voice matters. And there is almost always "
                  "a next step, even a tiny one.", tag="next"),
        B("sam", "I can stay calm, and still stand up for myself.", tag="sam",
          emo={"sam": "confident"}, gap=0.7),
        B("lumi", "If you ever feel unsafe or hopeless, please reach out to someone you trust, "
                  "or a local crisis line. You deserve support.", tag="crisis",
          emo={"lumi": "caring"}, gap=0.5),
        B("lumi", "Save this for a day you need it... and share it with someone who might be "
                  "stuck behind a locked door.", tag="share", emo={"lumi": "happy",
                                                                    "sam": "happy"}),
        B(hold=7.0, tag="end", sfx=[("sparkle", 0.2)]),
    ]),
]

LENS_LIST = [s["lens"] for s in SCENES if "lens" in s]
