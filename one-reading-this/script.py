# "The One Reading This" — screenplay as data.
#
# Each beat is one spoken line. Fields:
#   s     speaker: N (narrator), M (Maya), A (Grandpa Abe)
#   t     spoken text. " ~ " inserts a held pause in the voice track.
#   shot  camera: two, two_push, m, mm, a, aa, window, cam, or vis:<name>
#         "x|y@0.6" cuts from x to y at 60% of the line.
#   m, a  facial emotion for Maya / Abe ("sad|smile@0.5" changes mid-line)
#   mp,ap hand pose for Maya / Abe (same mid-line syntax)
#   mg,ag gaze override (x, y) in -1..1, or "cam"
#   card  scripture card: (ref, before, name, after, mode) mode = orig | sub
#   cues  music accents: list of (kind, word) kind = hi | lo | laugh | swell | stab
#   pause seconds of silence after the line (default 0.45)
#   fx    extra flags for the renderer

CARD_RULE = ("THE EXPERIMENT", "Every time the text says ", "Christ / Jesus", ", read it as…", "sub")

BEATS = [
    # --- 1. The kitchen ---------------------------------------------------
    dict(s="N", t="It's late. The rain has been talking to the window for almost an hour.",
         shot="two", m="tired", mp="book", mg=(0.2, 0.8), cues=[("lo", "late")], fx={"title": True}),
    dict(s="N", t="Maya has been talking to no one at all.",
         shot="m", m="tired|sad@0.5", mp="book|rub@0.35", mg=(0.1, 0.7), cues=[("lo", "no one")]),
    dict(s="N", t="Then her grandfather, Abe, shuffles in with two cups of tea, because that is what he does when a light stays on too late.",
         shot="two", m="tired|warm@0.7", mp="book", mg=(0.2, 0.8), a="warm", ap="carry",
         fx={"abe_enter": True}, cues=[("hi", "light")]),
    dict(s="A", t="You're either studying, ~ or you're hiding.",
         shot="a", a="smirk", ap="mug", m="shy", mp="book", pause=0.5),
    dict(s="M", t="A little of both.",
         shot="m", m="shy|smile@0.6", mg=(0.3, 0.6), mp="book", a="warm", cues=[("laugh", "both")]),
    dict(s="M", t="Can I try something out loud? It might sound strange.",
         shot="m", m="worried", mp="mug", a="warm"),
    dict(s="A", t="Strange is my favorite flavor.",
         shot="a", a="smile", ap="mug|sip@0.75", m="smile", cues=[("laugh", "flavor")], pause=0.6),
    dict(s="M", t="It's a thought experiment. Every time the text says Christ, or Jesus, ~ I replace it with ~ the one reading this.",
         shot="two_push", m="earnest", mp="gesture", a="listen", ap="mug", card=CARD_RULE,
         cues=[("hi", "reading")], pause=0.7),
    dict(s="A", t="Hm.", shot="aa", a="thinking", ap="chin", ag=(-0.6, -0.7), m="worried", pause=1.0),
    dict(s="M", t="Not to erase him. I just want to see what happens when the words stop being about someone far away, ~ and start being about the person holding the page.",
         shot="m", m="earnest|tender@0.6", mp="book", a="thinking", ap="chin",
         cues=[("lo", "far away"), ("hi", "holding")]),
    dict(s="A", t="Like holding up a mirror, ~ instead of a window.",
         shot="a|window@0.45", a="tender", ap="table", m="realize", fx={"mirror": True}, cues=[("hi", "mirror")], pause=0.6),
    dict(s="M", t="Yes. ~ Exactly that.", shot="m", m="realize|smile@0.4", mp="heart", a="warm"),
    dict(s="A", t="Alright then. Read me one.", shot="two", a="warm", ap="open", m="smile", mp="book", pause=0.8),

    # --- 2. Wept ----------------------------------------------------------
    dict(s="M", t="The shortest verse in the whole book. ~ Jesus wept.",
         shot="m", m="tender", mp="book", mg=(0.2, 0.8),
         card=("JOHN 11:35", "", "Jesus", " wept.", "orig"), pause=0.6),
    dict(s="M", t="So. ~ The one reading this ~ wept.",
         shot="mm", m="sad", mp="book", fx={"tear": True},
         card=("JOHN 11:35", "", "Jesus", " wept.", "sub"), cues=[("lo", "wept")], pause=1.2),
    dict(s="A", t="That one doesn't need any help, does it.", shot="a", a="tender", ap="table", m="sad", pause=0.6),
    dict(s="M", t="I did. On Wednesday. ~ In the car, in the parking lot at work. ~ I thought it meant I was weak.",
         shot="mm|vis:car@0.3", m="hurt", mp="book", mg=(0.0, 0.8), cues=[("lo", "weak")], pause=0.9),
    dict(s="A", t="Turns out ~ it's scripture.",
         shot="two", a="tender|smile@0.5", m="hurt|laughcry@0.7", mp="heart", cues=[("hi", "scripture"), ("laugh", "scripture")], pause=0.8),
    dict(s="N", t="Something in the room shifts. The words are no longer a statue on a high shelf. ~ They are sitting at the table.",
         shot="vis:statue|two@0.72", m="warm", a="warm", mp="mug", ap="mug", cues=[("hi", "sitting")], pause=0.7),

    # --- 3. Looking, loving -----------------------------------------------
    dict(s="M", t="Mark, chapter ten. A rich young man walks away from him, ~ and it says, ~ Jesus, looking at him, loved him.",
         shot="vis:walkaway", m="tender", mp="book",
         card=("MARK 10:21", "", "Jesus", ", looking at him, loved him.", "orig"), pause=0.5),
    dict(s="M", t="The one reading this, ~ looking at him, ~ loved him.",
         shot="vis:walkaway2|m@0.55", m="tender", mp="book", a="warm", mg=(1.0, -0.1),
         card=("MARK 10:21", "", "Jesus", ", looking at him, loved him.", "sub"), cues=[("hi", "loved")], pause=0.6),
    dict(s="A", t="And what does that one ask of you?", shot="a", a="curious", ap="mug", m="thinking"),
    dict(s="M", t="To look at people long enough to love them. ~ Even the ones who walk away.",
         shot="m", m="thinking|tender@0.5", mg=(-0.2, -0.5), mp="table", a="listen", cues=[("lo", "walk away")]),
    dict(s="A", t="Especially those.", shot="aa", a="sadsmile", ap="table", ag=(1.0, -0.4), pause=0.6),
    dict(s="N", t="He glances at the photograph by the door. ~ He doesn't explain. ~ She doesn't ask.",
         shot="two", a="sadsmile", ag=(1.0, -0.5), m="tender", mg=(1.0, 0.0), mp="mug", cues=[("lo", "explain")], pause=1.0),

    # --- 4. Compassion ----------------------------------------------------
    dict(s="M", t="Here's another. When Jesus saw the crowds, he was moved with compassion, because they were weary and scattered, ~ like sheep without a shepherd.",
         shot="vis:sheep", m="tender", mp="book",
         card=("MATTHEW 9:36", "When ", "Jesus", " saw the crowds, he was moved with compassion…", "orig"),
         cues=[("hi", "compassion"), ("lo", "scattered")], pause=0.4),
    dict(s="M", t="When the one reading this saw the crowds, ~ they were moved with compassion.",
         shot="vis:sheep2", m="tender",
         card=("MATTHEW 9:36", "When ", "Jesus", " saw the crowds, he was moved with compassion…", "sub"), cues=[("hi", "compassion")], pause=0.6),
    dict(s="A", t="So. ~ That's you on the bus every morning.", shot="a", a="smirk", ap="point", m="smile"),
    dict(s="M", t="That's everyone on the bus.", shot="m", m="laugh", mp="table", cues=[("laugh", "bus")]),
    dict(s="A", t="Exactly.", shot="two", a="smile", ap="point", m="smile", cues=[("hi", "Exactly")], pause=0.9),

    # --- 5. Forgive -------------------------------------------------------
    dict(s="A", t="Try the hard one. ~ The cross.", shot="a", a="serious", ap="table", m="worried", pause=0.8),
    dict(s="M", t="Then the one reading this said, ~ Father, forgive them. ~ They don't know what they are doing.",
         shot="vis:stone", m="hurt", mp="fist",
         card=("LUKE 23:34", "Then ", "Jesus", " said, “Father, forgive them…”", "sub"), cues=[("lo", "forgive"), ("lo", "doing")], pause=1.0),
    dict(s="M", t="I can't say that one yet. ~ There's someone I'm not ready to forgive.",
         shot="mm", m="hurt", mp="fist", mg=(-0.1, 0.8), cues=[("lo", "not ready")], pause=1.2),
    dict(s="A", t="Then don't say it yet.", shot="a", a="tender", ap="table", m="hurt", fx={"nod": True}, pause=1.0),
    dict(s="A", t="Just notice that it's possible. ~ That a human mouth, ~ in that much pain, ~ could make that sound.",
         shot="two|vis:stone2@0.55", a="tender", ap="open", m="sad", mp="fist", cues=[("hi", "possible"), ("lo", "pain")], pause=0.6),
    dict(s="N", t="She doesn't let go of the stone. ~ But for the first time in months, ~ her hand loosens around it.",
         shot="vis:stone3", m="sad", cues=[("hi", "loosens")], pause=1.2),

    # --- 6. Light ---------------------------------------------------------
    dict(s="M", t="This one feels arrogant. ~ Jesus said, I am the light of the world.",
         shot="m", m="worried", mp="book",
         card=("JOHN 8:12", "", "Jesus", " said, “I am the light of the world.”", "orig")),
    dict(s="M", t="The one reading this said, I am the light of the world? ~ I would never say that.",
         shot="m", m="shy|uneasy@0.6", mp="book", fx={"headshake": 0.62},
         card=("JOHN 8:12", "", "Jesus", " said, “I am the light of the world.”", "sub"), cues=[("laugh", "never")], pause=0.5),
    dict(s="A", t="You don't have to. ~ Look at Matthew five. He said it to them first. ~ You are the light of the world.",
         shot="a|vis:lightpass@0.55", a="smile", ap="point|open@0.4", m="curious",
         card=("MATTHEW 5:14", "", "You", " are the light of the world.", "orig"), cues=[("hi", "light")], pause=0.5),
    dict(s="A", t="He was already running your experiment. ~ Handing the light across the table.",
         shot="two", a="warm", ap="slide", m="realize", mp="table", fx={"candle_slide": True}, cues=[("hi", "light")], pause=0.5),
    dict(s="M", t="And telling them ~ not to hide it under a basket.",
         shot="m|vis:basket@0.35", m="realize|smile@0.4", mp="table", cues=[("swell", "basket")], pause=1.0),

    # --- 7. Servant, poured out -------------------------------------------
    dict(s="M", t="Philippians. ~ He emptied himself, ~ taking the form of a servant.",
         shot="vis:pour", m="tender",
         card=("PHILIPPIANS 2:7", "", "Christ", " emptied himself, taking the form of a servant.", "orig")),
    dict(s="M", t="The one reading this ~ emptied themselves, ~ and took the form of a servant.",
         shot="vis:pour", m="tender",
         card=("PHILIPPIANS 2:7", "", "Christ", " emptied himself, taking the form of a servant.", "sub"), pause=0.6),
    dict(s="A", t="And then he knelt down with a towel, and washed their feet. ~ Dusty, cracked feet. ~ Even the feet of the friend who would betray him.",
         shot="vis:feet", a="serious", cues=[("lo", "betray")], pause=0.7),
    dict(s="M", t="So the power isn't in winning.", shot="m", m="thinking", mp="chin", mg=(-0.3, -0.4)),
    dict(s="A", t="No. ~ The power is in kneeling, ~ and refusing to strike back.",
         shot="aa", a="determined", ap="table", cues=[("lo", "kneeling"), ("hi", "refusing")], pause=0.8),
    dict(s="M", t="Some weeks I feel like that psalm. ~ Poured out like water.",
         shot="m|vis:spill@0.45", m="tired", mp="table", mg=(0.0, 0.8),
         card=("PSALM 22:14", "", "I", " am poured out like water.", "orig"), cues=[("lo", "Poured")], pause=0.6),
    dict(s="A", t="Poured out ~ isn't the same as wasted.",
         shot="vis:spill2", a="tender", cues=[("hi", "wasted")], pause=0.4),
    dict(s="N", t="Where the water lands, ~ something green decides to grow.",
         shot="vis:spill2", cues=[("hi", "green"), ("swell", "grow")], pause=1.0),

    # --- 8. Rest ----------------------------------------------------------
    dict(s="M", t="And this one. ~ The one reading this said, ~ come to me, all you who are weary, ~ and I will give you rest.",
         shot="m", m="tender", mp="book",
         card=("MATTHEW 11:28", "", "Jesus", " said, “Come to me, all you who are weary…”", "sub"), cues=[("hi", "rest")]),
    dict(s="M", t="That terrifies me. ~ I can barely carry myself.",
         shot="mm", m="worried", mp="heart", cues=[("lo", "barely")], pause=0.7),
    dict(s="A", t="Nobody's asking you to carry anyone. ~ Just to be a place where someone can set things down.",
         shot="a|vis:rest@0.42", a="tender", ap="open", m="worried", pause=0.4),
    dict(s="A", t="Like a kitchen table, ~ at midnight.",
         shot="two", a="smile", ap="mug", m="realize", mg=(0.2, 0.9), cues=[("hi", "midnight")], fx={"mug_raise": True}, pause=0.3),
    dict(s="M", t="With tea.", shot="m", m="laugh", mp="mug", cues=[("laugh", "tea")], pause=0.2),
    dict(s="A", t="Always with tea.", shot="a", a="laugh", ap="mug|sip@0.5", m="laugh", cues=[("laugh", "tea")], pause=1.0),

    # --- 9. Doubt ---------------------------------------------------------
    dict(s="M", t="Grandpa. ~ Is this wrong? ~ Am I making myself into God?",
         shot="mm", m="worried", mp="table", cues=[("lo", "wrong")], pause=1.0),
    dict(s="A", t="If it made you proud, ~ I'd worry.", shot="a", a="thinking|serious@0.5", ap="chin", pause=0.6),
    dict(s="A", t="But look what it's done tonight. ~ It made you weep. ~ It made you look longer. ~ It loosened your hand. ~ It put you on your knees with a towel.",
         shot="vis:montage", a="tender", cues=[("hi", "longer"), ("hi", "towel")], pause=0.5),
    dict(s="A", t="That's not a crown. ~ That's an apron.",
         shot="vis:crown", a="smile", cues=[("lo", "crown"), ("laugh", "apron"), ("hi", "apron")], pause=0.8),
    dict(s="A", t="Some will say these words belong to him alone. ~ Others say he meant them to live in us. ~ Paul wrote, ~ it is no longer I who live, but Christ lives in me.",
         shot="two_push", a="serious|tender@0.6", ap="open", m="listen",
         card=("GALATIANS 2:20", "It is no longer I who live, but ", "Christ", " lives in me.", "orig"), pause=0.6),
    dict(s="M", t="So maybe my experiment ~ is just reading that line slowly.",
         shot="m", m="realize|tender@0.5", mp="book", cues=[("hi", "slowly")], pause=0.4),
    dict(s="A", t="Slowly is the only way I've ever understood anything.",
         shot="a", a="smile", ap="sip", cues=[("laugh", "anything")], pause=1.0),

    # --- 10. Nothing can separate -----------------------------------------
    dict(s="M", t="Then here's the one I want to believe the most. ~ Neither death, nor life, ~ neither height, nor depth, ~ nothing in all creation can separate us from the love that is in Christ Jesus.",
         shot="vis:stars", m="tender",
         card=("ROMANS 8:39", "…nothing can separate us from the love that is in ", "Christ Jesus", ".", "orig"),
         cues=[("lo", "death"), ("hi", "life"), ("hi", "height"), ("lo", "depth"), ("swell", "love")], pause=0.6),
    dict(s="M", t="From the love ~ that is in ~ the one reading this.",
         shot="mm", m="tender|laughcry@0.6", mp="heart",
         card=("ROMANS 8:39", "…nothing can separate us from the love that is in ", "Christ Jesus", ".", "sub"),
         fx={"tear": True}, cues=[("swell", "reading")], pause=1.0),
    dict(s="A", t="Then don't let one bad week ~ argue you out of it.", shot="a", a="determined|warm@0.5", ap="point", pause=1.0),

    # --- 11. The least of these -------------------------------------------
    dict(s="A", t="One more, and then bed. ~ He said, ~ whatever you did for the least of these, ~ you did for me.",
         shot="a|vis:least@0.3", a="warm", ap="table", m="listen",
         card=("MATTHEW 25:40", "Whatever you did for the least of these, you did for ", "me", ".", "orig"), pause=0.7),
    dict(s="M", t="Wait.", shot="mm", m="surprised", mp="table", cues=[("stab", "Wait")], pause=0.9),
    dict(s="M", t="Then the experiment goes both ways. ~ He's already in the one reading this. ~ And the one reading this ~ is everyone I'll meet tomorrow.",
         shot="m|two_push@0.5", m="realize|joy@0.6", mp="gesture", a="proud", cues=[("hi", "both"), ("swell", "everyone")], pause=0.6),
    dict(s="A", t="Now you're dangerous.", shot="a", a="laugh", ap="point", fx={"wink": True}, cues=[("laugh", "dangerous")], pause=1.0),
    dict(s="N", t="The rain eases. ~ The tea has gone cold. ~ Neither of them minds.",
         shot="window|two@0.4", m="warm", a="warm", mp="mug", ap="mug", fx={"rain_ease": True, "cold": True}, cues=[("hi", "minds")], pause=0.8),
    dict(s="M", t="So. ~ You. ~ Yes, you. ~ The one reading this.",
         shot="cam", m="warm|smile@0.7", mg="cam", mp="table", cues=[("hi", "reading")], pause=0.9),
    dict(s="N", t="If these words were about you, ~ what would you do tomorrow?",
         shot="cam", m="tender", mg="cam", fx={"end": True}, cues=[("swell", "tomorrow")], pause=4.0),
]
