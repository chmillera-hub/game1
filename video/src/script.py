# Each entry: dict(id, sp (speaker), text, gap (pause before), hold (pause after), scene, hi/lo cue words)
# Entries with sp=None are silent beats of length `dur`.
VOICES = {
 "WRITER":   ("en-US-BrianNeural",  "-4%", "-2Hz"),
 "AI":       ("en-US-AvaNeural",    "-6%", "+0Hz"),
 "NARRATOR": ("en-US-AndrewNeural", "-10%", "-6Hz"),
 "PAUL":     ("en-GB-RyanNeural",   "-10%", "-5Hz"),
 "LUKE":     ("en-IE-ConnorNeural", "-6%", "+0Hz"),
 "OFFICIAL": ("en-GB-ThomasNeural", "-8%", "-8Hz"),
 "LYDIA":    ("en-GB-SoniaNeural",  "-14%", "-2Hz"),
}
S = [
 # ---------- A: apartment, night ----------
 dict(id="a0", sp=None, dur=1.6, scene="apt"),
 dict(id="m1", sp="WRITER", text="They boiled John in oil.", gap=0, hold=0.9, scene="martyrs", lo=["oil"]),
 dict(id="m2", sp="WRITER", text="Crucified Christ.", gap=0.2, hold=1.0, scene="martyrs", lo=["Christ"]),
 dict(id="m3", sp="WRITER", text="Stoned Philip to death.", gap=0.2, hold=0.9, scene="martyrs", lo=["death"]),
 dict(id="m4", sp="WRITER", text="Skinned Matthew alive.", gap=0.2, hold=0.9, scene="martyrs", lo=["alive"]),
 dict(id="m5", sp="WRITER", text="Crucified Peter upside down.", gap=0.2, hold=0.9, scene="martyrs", lo=["down"]),
 dict(id="m6", sp="WRITER", text="Hung Luke from an olive tree.", gap=0.2, hold=0.9, scene="martyrs", lo=["tree"]),
 dict(id="m7", sp="WRITER", text="Beheaded James with a sword.", gap=0.2, hold=1.3, scene="martyrs", lo=["sword"]),
 dict(id="a1", sp="WRITER", text="So what's the metaphor for me?", gap=0.3, hold=0.6, scene="apt2"),
 dict(id="a2", sp="WRITER", text="Not in a violent way. But I'm trying to endure all this abandonment. People drifting away. Being shut out.", gap=0.3, hold=0.8, scene="cafe", lo=["abandonment","out"]),
 dict(id="a3", sp="WRITER", text="And these epidemic levels of shallow conversation that I just... won't do anymore.", gap=0.3, hold=0.6, scene="party"),
 dict(id="a4", sp="WRITER", text="So instead, I post online.", gap=0.3, hold=1.2, scene="party_post"),
 dict(id="b1", sp="AI", text="What you're describing isn't a sword or a cross. It's quieter than that. It's being unread.", gap=0.4, hold=0.9, scene="apt3", lo=["unread"]),
 dict(id="b2", sp="AI", text="If you want a metaphor, maybe you're less like the martyrs, and more like Paul.", gap=0.3, hold=0.4, scene="apt3", hi=["Paul"]),
 dict(id="b3", sp="WRITER", text="Paul?", gap=0.2, hold=0.6, scene="apt3"),
 dict(id="b4", sp="WRITER", text="So you're saying I'm Paul. Sitting in a dingy one-bedroom apartment, writing letters to trolls on the internet.", gap=0.2, hold=0.3, scene="aptwide"),
 dict(id="b5", sp="WRITER", text="Who mostly ignore me, or reply, that's dumb, and then block me?", gap=0.2, hold=1.4, scene="blocked", lo=["dumb"]),
 dict(id="b6", sp="AI", text="Honestly? A little. Paul spent two years in a rented room in Rome, chained to a soldier, writing letters to people who often didn't want them.", gap=0.3, hold=0.6, scene="apt4"),
 # ---------- D: Rome ----------
 dict(id="d1", sp="NARRATOR", text="Rome. One rented room. One lamp. One chain. And one guard who never asked for this assignment.", gap=0.4, hold=0.8, scene="rome_wide", lo=["Rome"]),
 dict(id="d2", sp="PAUL", text="I, Paul, write this greeting with my own hand. Remember my chains.", gap=0.3, hold=0.7, scene="rome", lo=["chains"]),
 dict(id="d3", sp="LUKE", text="They'll read it, Paul. Some of them.", gap=0.3, hold=0.6, scene="rome", hi=["read"]),
 dict(id="d4", sp="PAUL", text="Demas has deserted me. At my first defense, no one came to stand with me. Everyone left.", gap=0.5, hold=1.2, scene="rome_close", lo=["deserted","left"]),
 dict(id="d5", sp="LUKE", text="Not everyone.", gap=0.4, hold=0.7, scene="rome", hi=["everyone"]),
 dict(id="d6", sp="PAUL", text="No. Only Luke is with me.", gap=0.3, hold=1.0, scene="rome", hi=["Luke"]),
 dict(id="d7", sp="PAUL", text="I am chained like a criminal. But the word of God is not chained.", gap=0.4, hold=0.6, scene="rome_chain", lo=["criminal"], hi=["not"]),
 dict(id="d8", sp=None, dur=3.2, scene="rome_door"),
 # ---------- E: journey + official ----------
 dict(id="e1", sp="NARRATOR", text="His letters went out by road, and by sea.", gap=0.2, hold=0.8, scene="journey"),
 dict(id="e2", sp="NARRATOR", text="And some of them, surely, landed on the desk of someone in power.", gap=0.3, hold=0.6, scene="villa"),
 dict(id="e3", sp="OFFICIAL", text="Paul, a servant of Christ Jesus...", gap=0.8, hold=0.3, scene="villa"),
 dict(id="e4", sp="OFFICIAL", text="Christ Jesus. Again.", gap=0.6, hold=2.6, scene="villa", lo=["Again"]),
 dict(id="e5", sp="WRITER", text="Ha! I bet he read the first two lines, crumpled it up, and threw it right in the fire with a scowl on his face.", gap=0.2, hold=0.5, scene="villa_burn"),
 dict(id="e6", sp="AI", text="Some of them probably did end up in the fire. We'll never know how many.", gap=0.3, hold=0.8, scene="villa_ash", lo=["fire"]),
 # ---------- F: Philippi ----------
 dict(id="f1", sp="NARRATOR", text="But some of them didn't.", gap=0.3, hold=0.6, scene="philippi", hi=["didn't"]),
 dict(id="f2", sp="LYDIA", text="I thank my God every time I remember you.", gap=0.8, hold=1.6, scene="philippi_read", hi=["remember"]),
 dict(id="f3", sp="NARRATOR", text="Those letters were read aloud, copied by hand, and passed from house to house.", gap=0.3, hold=0.6, scene="copying", hi=["house"]),
 dict(id="f4", sp="NARRATOR", text="The man who was ignored, mocked, and abandoned, ended up writing nearly half the books of the New Testament.", gap=0.3, hold=1.2, scene="books", lo=["abandoned"], hi=["Testament"]),
 # ---------- G: apartment, dawn ----------
 dict(id="g1", sp="AI", text="The fire got some of his letters. It didn't get all of them.", gap=0.4, hold=0.6, scene="dawn", hi=["all"]),
 dict(id="g2", sp="AI", text="You're not writing for the people who block you. You're writing for the one person quietly reading.", gap=0.3, hold=1.0, scene="dawn", hi=["reading"]),
 dict(id="g3", sp="WRITER", text="Then I guess I'll keep writing.", gap=1.2, hold=0.8, scene="dawn_close", hi=["writing"]),
 dict(id="g4", sp=None, dur=4.0, scene="notify"),
 dict(id="g5", sp="NARRATOR", text="Not every letter gets opened. Write it anyway.", gap=0.2, hold=2.6, scene="end", hi=["anyway"]),
]
