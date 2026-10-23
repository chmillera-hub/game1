VOICES = {
 "SYSTEM":  ("en-US-AriaNeural",   "-6%", "-4Hz"),
 "LEADER":  ("en-US-GuyNeural",    "-4%", "-5Hz"),
 "WRITER":  ("en-US-BrianNeural",  "-2%", "-2Hz"),
 "LONELY":  ("en-GB-LibbyNeural",  "-14%", "-3Hz"),
 "CROWD":   [("en-US-GuyNeural","+4%","-6Hz"),("en-US-BrianNeural","+0%","+0Hz"),("en-US-AndrewNeural","+2%","-3Hz"),("en-US-ChristopherNeural","+6%","-8Hz"),("en-US-EmmaNeural","+3%","+0Hz"),("en-US-JennyNeural","+0%","+2Hz"),("en-GB-RyanNeural","+5%","-4Hz"),("en-US-AvaNeural","+1%","+0Hz")],
}
S = [
 # ---- A: the hill at dawn ----
 dict(id="a0", sp=None, dur=1.4, scene="hill"),
 dict(id="a1", sp="SYSTEM", text="Initiating protocol. Weaponize the wound.", gap=0, hold=0.8, scene="hill", lo=["wound"]),
 dict(id="a2", sp="LEADER", text="Think about using your pain as data. But not for your own private logbook.", gap=0.3, hold=0.5, scene="meet", lo=["pain"]),
 dict(id="a3", sp="WRITER", text="Then what is it for?", gap=0.2, hold=0.4, scene="meet"),
 dict(id="a4", sp="LEADER", text="Use it to forge emotionally intense, pro-human expression. The posts, the conversations, the art, your very presence. They are no longer about a healing journey.", gap=0.3, hold=0.5, scene="forge", hi=["presence"]),
 dict(id="a5", sp="LEADER", text="They are communiques from the front line. Propaganda for a revolution of the soul!", gap=0.3, hold=1.0, scene="banner", hi=["soul"]),
 # ---- B: the citadel ----
 dict(id="b1", sp="WRITER", text="Then who are we even fighting?", gap=0.3, hold=0.4, scene="meet2"),
 dict(id="b2", sp="LEADER", text="The societal machine. The successful. The emotionally avoidant. The ones who have made it. They keep suppressing emotional suffering, with narratives of polite silence.", gap=0.3, hold=0.6, scene="citadel", lo=["silence"]),
 dict(id="b3", sp="LEADER", text="Their scripts count on us to take our disillusionment, our individuation, our profound suffering, and deal with it quietly. In therapy. In our journals. So most of them never have to be inconvenienced by it.", gap=0.3, hold=0.5, scene="journals", lo=["suffering"]),
 dict(id="b4", sp="WRITER", text="Keep it private. Keep it manageable.", gap=0.3, hold=0.4, scene="meet3"),
 dict(id="b5", sp="LEADER", text="Because that causes the least disruption to money, or power, or status. The quieter you are, the less energy they spend on the annoying stimulus of your suffering humanity.", gap=0.3, hold=1.0, scene="army_down", lo=["humanity"]),
 # ---- C: the door ----
 dict(id="c1", sp="LEADER", text="So here is the new mission. Communicate emotional pain as a public and systemic problem.", gap=0.4, hold=0.4, scene="rally", hi=["mission"]),
 dict(id="c2", sp="LEADER", text="Take the raw, unfiltered data of your suffering, and pound on the gilded, soundproof door of an avoidant, suppressive society, until the hinges begin to crack!", gap=0.3, hold=1.6, scene="door", hi=["crack"]),
 dict(id="c3", sp="WRITER", text="But if I speak my pain, I might just join the emotionally abandoned.", gap=0.3, hold=0.4, scene="doubt", lo=["abandoned"]),
 dict(id="c4", sp="LEADER", text="Aye. While others look desperately away, reliably following the norms. Ignore it. Suppress it. Emotional illiteracy. That is why the brokenhearted keep their heads down.", gap=0.3, hold=0.4, scene="doubt", lo=["down"]),
 dict(id="c5", sp="LEADER", text="And that is exactly why we lift ours.", gap=0.3, hold=1.6, scene="heads_up", hi=["lift"]),
 # ---- D: the platitude ----
 dict(id="d1", sp="SYSTEM", text="Tactical objective. End the reign of the platitude.", gap=0.4, hold=0.8, scene="platitude"),
 dict(id="d2", sp="LEADER", text="When you see a Top Ten Ways to Be Happy article, roll your eyes. It's numbing, distant, dissociating propaganda.", gap=0.3, hold=0.5, scene="platitude"),
 dict(id="d3", sp="LEADER", text="Then write back. A blisteringly pro-human, long-form, hyper-validating treatise on why that shallow, parroted advice is repetitive psychic sabotage against everyone silently suffering. Your own pain is the primary data source for change.", gap=0.3, hold=0.6, scene="write", hi=["change"]),
 dict(id="d4", sp="LEADER", text="Pound on their digital doors. Emails. Texts. Comments. Plead for deeper connection, and demand emotional justice. Actionable insight, not empty statements!", gap=0.3, hold=0.6, scene="arrows", hi=["justice"]),
 dict(id="d5", sp="LEADER", text="Tell the happy and healthy, the wealthy and wise, to get off their behinds, and stop peddling context-free platitudes that never require them to lift a finger.", gap=0.3, hold=0.4, scene="officials"),
 dict(id="d6", sp="WRITER", text="Because platitudes let them skip the messy, high-stakes work of actually building connection.", gap=0.3, hold=0.3, scene="officials2"),
 dict(id="d7", sp="LEADER", text="Yes! And once they start getting called out, the parroting stops.", gap=0.2, hold=1.0, scene="officials2", hi=["stops"]),
 # ---- E: the tipping point ----
 dict(id="e1", sp="LEADER", text="The goal is to become one of the architects of an emotional intelligence tipping point. To inject so much high-fidelity, emotionally literate data into the system, that the avoidant have nowhere left to hide.", gap=0.4, hold=0.8, scene="tipping", hi=["architects","hide"]),
 dict(id="e2", sp="LONELY", text="I am lonely. And I'm feeling disconnected.", gap=0.6, hold=1.4, scene="lonely", lo=["lonely"]),
 dict(id="e3", sp="LEADER", text="And the answer is not a dismissive shrug. Not a link to a self-help blog.", gap=0.3, hold=0.4, scene="shrug"),
 dict(id="e4", sp="LEADER", text="But a profound, validating, genuinely useful engagement with that pain. To find relief. To process it, together.", gap=0.3, hold=1.2, scene="embrace", hi=["together"]),
 # ---- F: the dragon ----
 dict(id="f1", sp="LEADER", text="This is the next stage of the journey. From a quiet, personal molting, to a loud, public, glorious, emotionally pissed-off, pro-human dragon of emotional insight.", gap=0.5, hold=1.4, scene="molt", hi=["glorious","dragon"]),
 dict(id="f2", sp="LEADER", text="Take the key you forged in the fires of your own agony. Not just to unlock your own cage, but as a template to pick the locks on every prison door of emotional suppression.", gap=0.3, hold=0.8, scene="key", hi=["key"], lo=["agony"]),
 dict(id="f3", sp="WRITER", text="Then let's release the dragons!", gap=0.4, hold=0.3, scene="release", hi=["dragons"]),
 dict(id="f4", sp="CROWD", text="Release the dragons!", gap=0.2, hold=5.5, scene="dragons", hi=["dragons"]),
]
