"""Screenplay for "Eeyore & the Pasture".

Each scene is a list of beats. A beat is either a spoken line
(speaker, text) or a pause. Labels let the animation and the
sound design hook onto exact moments in the voice track.
"""

# speaker -> voice casting (Piper model, speaker id, pace, pitch shift in semitones)
CAST = {
    "narr":   dict(model="en_GB-cori-high",       spk=None, length=1.08, pitch=0.0),
    "eeyore": dict(model="en_GB-semaine-medium",  spk=2,    length=1.22, pitch=-2.5),
    "pooh":   dict(model="en_GB-vctk-medium",     spk=9,    length=1.12, pitch=0.5),
    "piglet": dict(model="en_GB-vctk-medium",     spk=1,    length=0.95, pitch=4.0),
    "rabbit": dict(model="en_GB-semaine-medium",  spk=1,    length=0.92, pitch=2.0),
    "owl":    dict(model="en_GB-alan-medium",     spk=None, length=1.12, pitch=-1.5),
    "bird":   dict(model="en_GB-semaine-medium",  spk=3,    length=0.95, pitch=3.5),
}

def L(label, speaker, text, gap=0.35, thought=False, caption=None, vol=1.0, length=None):
    return dict(type="line", label=label, speaker=speaker, text=text, gap=gap,
                thought=thought, caption=caption or text, vol=vol, length=length)

def P(label, dur):
    return dict(type="pause", label=label, dur=dur)

SCENES = [
    ("title", None, [
        P("open", 2.6),
        L("n0a", "narr", "In the Hundred Acre Wood, everyone was happy.", gap=0.5),
        L("n0b", "narr", "Well. Almost everyone.", gap=1.8),
    ]),
    ("s1", "1 · The Surface-Level Support", [
        P("s1in", 1.8),
        L("s1a", "pooh", "Come eat with us, Eeyore!", gap=0.4),
        L("s1b", "piglet", "Let's sit under the trees and chat!", gap=1.6),
        L("s1c", "rabbit", "There. Everyone included. Aren't we good friends?", gap=0.3),
        L("s1d", "owl", "Exemplary. Truly exemplary.", gap=0.5),
        L("s1e", "narr", "They were very proud of themselves. But they were missing the point entirely.", gap=0.6),
        L("s1f", "eeyore", "Why won't anyone ask me what I actually want?", thought=True, gap=0.4),
        L("s1g", "eeyore", "Why are they so satisfied with their half-assed solutions?", thought=True, gap=0.8),
    ]),
    ("s2", "2 · The Dismissal of Eeyore's Needs", [
        P("s2in", 0.6),
        L("s2a", "eeyore", "Actually... I want to run in a pasture.", gap=0.2),
        P("crickets", 1.7),
        L("s2b", "pooh", "Oh! Has anyone seen my honey?", gap=0.4),
        L("s2c", "rabbit", "Now, Eeyore. You're just a bit depressed.", gap=0.3),
        L("s2d", "owl", "And rather unreasonable, if I may say so.", gap=0.3),
        L("s2e", "piglet", "But you should stay in the forest! That's where we're happy!", gap=0.6),
        L("s2f", "narr", "What they meant was: why can't you just be content with what we like?", gap=0.3),
        L("s2g", "narr", "Your needs are inconvenient for us, so let's pretend they don't exist.", gap=1.0),
    ]),
    ("s3", "3 · The Pathologization of Joy", [
        P("s3in", 2.4),
        L("s3a", "bird", "Psst. Past the edge of the wood, there's a pasture. Wide and green, as far as you can see.", gap=0.3),
        L("s3b", "bird", "You could run there, someday.", gap=2.2),
        L("s3c", "eeyore", "Someday... I could run.", gap=1.6),
        L("s3d1", "rabbit", "Eeyore?", gap=0.45, caption="Eeyore...", length=1.1),
        L("s3d", "rabbit", "Are you... manic?", gap=0.35, caption="are you... manic?", length=1.15),
        L("s3e", "owl", "Smiling? That's not like you at all.", gap=0.8),
        L("s3f", "eeyore", "You ignored me when I was sad. And now you're gaslighting me when I'm hopeful?", gap=0.25),
        L("s3g", "eeyore", "What the hell?", gap=0.7),
        L("s3h", "narr", "His joy was treated like a symptom, because it didn't fit their comfort zone.", gap=0.3),
        L("s3i", "narr", "They'd rather see him sad but manageable, than joyful, and growing away from them.", gap=0.9),
    ]),
    ("s4", "4 · The Real Conflict: Misaligned Needs", [
        P("s4in", 1.8),
        L("s4a", "narr", "The forest was wonderful for Pooh and his friends. The trees, the honey, the familiar routines.", gap=0.4),
        L("s4b", "narr", "But Eeyore's needs were different. He craved open space, and the freedom to run.", gap=0.3),
        L("s4c", "narr", "Among the trees, he felt stifled, and unseen.", gap=1.4),
        L("s4d", "narr", "He was torn. Stay, so his friends wouldn't be upset. Or follow his needs to the pasture, even if it meant leaving them behind.", gap=1.8),
    ]),
    ("s5", "5 · The Toxic Cycle", [
        P("s5in", 0.6),
        L("s5a", "narr", "And so the cycle went.", gap=0.3),
        L("s5b", "narr", "He stayed in the forest, to keep the peace.", gap=0.3),
        L("s5c", "narr", "His needs went unmet, and he grew sadder.", gap=0.3),
        L("s5d", "pooh", "Have some honey, Eeyore!", gap=0.3),
        L("s5e", "narr", "He felt more misunderstood, and more alone.", gap=0.3),
        L("s5f", "narr", "And the cycle repeated.", gap=2.6),
    ]),
    ("s6", "6 · The Breaking Point", [
        P("s6in", 2.8),
        L("s6a", "pooh", "Eeyore? Would you like some more honey?", gap=0.9),
        L("s6b", "eeyore", "Pooh... I'm miserable. I want to go run in a field!", gap=2.6, length=1.1),
        L("s6c", "narr", "It wasn't selfish. It wasn't irrational. It was the most authentic thing he'd ever said.", gap=0.35),
        L("s6d", "narr", "He was reclaiming his right to listen to his emotional needs, even if it made others uncomfortable.", gap=0.9),
    ]),
    ("s7", "7 · The Hard Truth", [
        P("s7in", 0.8),
        L("s7a0", "pooh", "But...", gap=0.6, length=1.4),
        L("s7a", "pooh", "we love you, Eeyore.", gap=1.6, length=1.3),
        L("s7b", "narr", "And they did. But love that can't understand or respect your needs can still hold you back.", gap=0.35),
        L("s7c", "narr", "If Eeyore wanted to feel fulfilled, he had to stop waiting for them to validate his needs, and start chasing that pasture on his own.", gap=0.8),
    ]),
    ("s8", "The Takeaway", [
        P("s8in", 1.2),
        L("s8a", "eeyore", "This isn't working for me, Pooh. And that's okay.", gap=0.5),
        L("s8b", "eeyore", "I need to find what does.", gap=6.0),
        L("s8c", "narr", "Listening to your needs, in a world that tries to fit everyone into the same mold, takes courage.", gap=0.4),
        L("s8d", "narr", "Eeyore isn't broken. He isn't too much.", gap=0.3),
        L("s8e", "narr", "He's showing a non-sanitized version of humanity.", gap=0.4),
        L("s8f", "narr", "And some people's humanity demands pastures, no matter how much the forest folk don't get it.", gap=1.2),
        P("end", 7.0),
    ]),
]
