"""
BREAD FOR THE ENEMY — screenplay.

A short animated film weaving together:
  Romans 12:17-21, John 13:34 / 15:12, 1 Timothy 1:12-16, Romans 8:35-39 (NIV wording).

The story: Rome, around AD 67. Asher, the son of a man Paul (then a persecutor of the
church) dragged from his home in Jerusalem 34 years earlier, brings bread to the
imprisoned apostle on the night before Paul's execution, because Paul's own letter said
"If your enemy is hungry, feed him." Asher's hate does not vanish in one night; Paul
answers it, every time, without hating back.

Speaker ids: narrator, jesus, paul, saul (= Paul as a young man; displayed as "Paul"),
asher, child (= Asher at eight), yosef, phoebe, guard.

Event helpers (all times in seconds):
  S(shot, **p)        start a new shot at the cursor (camera/background are defined in render/shots.js)
  L(who, text, **o)   spoken line; advances the cursor by the clip length + gap
                      o: speed, gap, vo (voice-over, no lip-sync), fx (audio treatment),
                         sub (subtitle override), tts (pronunciation override), vol
  P(sec)              pause (advance cursor)
  E(who, **state)     acting keyframe: emo / look / pose / numeric overrides
                      timing: at (offset from cursor), ls (offset from last line start),
                              lf (fraction of last line), dur (blend time)
  X(sfx, **o)         sound effect cue (same timing keys as E)
  M(cue, **o)         music cue
  T(kind, text, **o)  on-screen text: title / place / end cards, or name="..." tags that
                      float above a character's head (who=<speaker id>)
"""

EVENTS = []


def S(shot, **p):
    EVENTS.append(dict(kind="shot", shot=shot, **p))


def L(who, text, **o):
    EVENTS.append(dict(kind="line", who=who, text=text, **o))


def P(sec):
    EVENTS.append(dict(kind="pause", sec=sec))


def E(who, **state):
    EVENTS.append(dict(kind="act", who=who, **state))


def X(sfx, **o):
    EVENTS.append(dict(kind="sfx", sfx=sfx, **o))


def M(cue, **o):
    EVENTS.append(dict(kind="music", cue=cue, **o))


def T(kind_, text, **o):
    EVENTS.append(dict(kind="text", style=kind_, text=text, **o))


# ---------------------------------------------------------------------------
# PROLOGUE — Jerusalem, the upper room, the night before the cross
# ---------------------------------------------------------------------------
S("upper_jesus", zoom=(1.0, 1.035))
T("title", "BREAD FOR THE ENEMY", sub="Romans 12  ·  John 15  ·  1 Timothy 1  ·  Romans 8", at=0, dur=4.6)
E("jesus", emo="tender", look="bread", pose="hold_bread", dur=0)
M("prologue")
X("lamp_room", at=0)
P(1.7)
E("jesus", pose="break_bread", dur=1.0)
X("bread_break", at=0.55)
P(1.5)
E("jesus", look="cam", emo="warm", dur=0.7)
P(0.8)
L("jesus", "A new commandment I give you.", speed=0.84, gap=0.6)
E("jesus", look="cam_l", dur=0.9)
L("jesus", "My command is this:", speed=0.84, gap=0.45)
E("jesus", look="cam", emo="tender_smile", ls=0.3, dur=0.8)
L("jesus", "Love each other... as I have loved you.", speed=0.8, gap=1.2)

S("upper_hands")
E("jesus", pose="give_bread", dur=0)
L("narrator", "He said this on the night He was betrayed...", speed=0.9, gap=0.35)
L("narrator", "only moments after handing bread to the man who would betray Him.", speed=0.9, gap=0.7)

S("upper_jesus_door", zoom=(1.0, 1.03))
E("jesus", emo="sorrow_love", look="door", pose="rest", dur=0)
P(1.0)
E("jesus", emo="sorrow_love", look="door_down", dur=1.4, at=0.4)
P(2.4)

# ---------------------------------------------------------------------------
# ACT 1 — Rome, night. The prison door.
# ---------------------------------------------------------------------------
S("street_wide", trans="dissolve")
T("place", "ROME  ·  THIRTY-FOUR YEARS LATER", at=0.4, dur=3.6)
M("street")
X("street_amb", at=0)
E("asher", emo="cold", look="door", pose="hold_nervous", dur=0)
P(0.9)
L("narrator", "Behind this door, an old man waits to die... for the name of Jesus.", speed=0.9, gap=0.6)
L("narrator", "And the man standing outside it... has hated him for most of his life.", speed=0.9, gap=0.8)

S("street_asher_cu", zoom=(1.0, 1.04))
T("name", "ASHER", who="asher", at=0.5, dur=3.0)
E("asher", emo="cold", look="door", dur=0)
P(0.9)
E("asher", look="bread", emo="bitter", dur=0.9)
P(0.6)
L("asher", "Bread. I'm bringing him bread.", speed=0.9, gap=0.8)
E("asher", look="door_low", emo="conflicted", ls=0.4, dur=1.0)
L("asher", "I don't even want to be here.", speed=0.9, gap=0.6)
E("asher", emo="bitter_laugh", look="away", ls=0.2, dur=0.6)
L("asher", "Why am I even here? This is foolish.", speed=0.92, gap=0.5)
E("asher", emo="sad", look="down", dur=1.6, at=-0.2)
P(1.9)

S("church_reader", trans="dissolve", grade="memory_warm")
X("room_murmur", at=0)
E("phoebe", emo="calm", look="scroll", dur=0)
L("narrator", "Months earlier, in a house where followers of Jesus gathered...", speed=0.9, gap=0.3)
L("narrator", "a letter from the apostle Paul was read aloud.", tts="a letter from the apostle Paul was red aloud.", speed=0.9, gap=0.5)
T("name", "PHOEBE", who="phoebe", at=-0.3, dur=3.0)
L("phoebe", "Paul, a servant of Christ Jesus... to all in Rome who are loved by God.", speed=0.9, gap=0.2)

S("church_asher", grade="memory_warm")
E("asher", emo="shock", look="reader", dur=0.25, at=0.1)
P(1.1)
E("asher", emo="cold", look="reader", dur=1.2)
L("phoebe", "Do not repay anyone evil for evil.", speed=0.9, vo=True, gap=0.5)
E("asher", emo="bitter", ls=0.4, dur=0.8)
L("phoebe", "If it is possible, as far as it depends on you... live at peace with everyone.",
  tts="If it is possible, as far as it depends on you... liv at peace with everyone.", speed=0.9, vo=True, gap=0.5)

S("church_reader", grade="memory_warm")
L("phoebe", "If your enemy is hungry, feed him. If he is thirsty, give him something to drink.", speed=0.9, gap=0.4)
L("phoebe", "In doing this, you will heap burning coals on his head.", speed=0.88, gap=0.3)

S("church_asher", grade="memory_warm", zoom=(1.0, 1.05))
E("asher", emo="conflicted", look="down", dur=1.2)
P(2.0)

S("street_asher_cu", trans="dissolve")
E("asher", emo="bitter", look="bread", dur=0)
P(0.5)
L("asher", "His own words.", speed=0.88, gap=0.9)
E("asher", look="door", emo="resolve", dur=0.8, at=-0.6)
L("asher", "Let's see if he believes them.", speed=0.92, gap=0.4)

S("street_knock")
E("asher", pose="knock", dur=0)
X("knock3", at=0.3)
P(2.0)

S("street_door_guard")
X("door_unbolt", at=0.0)
E("guard", emo="stern", look="asher", dur=0)
P(0.8)
L("guard", "Food for the old man?", speed=0.98, gap=0.5)
E("guard", emo="weary", ls=0.0, dur=0.6)
L("guard", "You're the first one in a week. Make it quick.", speed=0.98, gap=0.5)

# ---------------------------------------------------------------------------
# ACT 2 — The cell. Paul assumes the best of the stranger.
# ---------------------------------------------------------------------------
S("cell_wide")
X("door_creak", at=0.0)
X("cell_amb", at=0.0)
M("cell")
E("paul", pose="write", emo="squint", look="parchment", dur=0)
E("asher", pose="hold", emo="cold", look="paul", dur=0)
P(1.6)
E("paul", look="door", emo="hopeful", dur=0.6)
P(0.6)
L("paul", "Luke! Is that you, my brother?", speed=0.9, gap=0.6)

S("cell_paul_cu")
T("name", "PAUL", who="paul", at=0.3, dur=3.2)
E("paul", emo="joy", look="asher", pose="rest", dur=0.5)
L("paul", "Come in, come in! Thank you for coming.", speed=0.9, gap=0.4)
E("paul", emo="warm", ls=0.2, dur=0.8)
L("paul", "The Lord provides... He always provides.", speed=0.86, gap=0.5)
E("paul", look="bread", emo="smile", dur=0.5)
L("paul", "And you've brought bread. God bless you.", speed=0.88, gap=0.5)
E("paul", look="down", emo="weary", dur=0.9)
L("paul", "So many are afraid to come now. I don't blame them.", speed=0.86, gap=0.4)
E("paul", look="asher", emo="gentle_smile", dur=0.8)
L("paul", "But you came.", speed=0.84, gap=0.8)

S("cell_asher_cu")
E("asher", emo="conflicted", look="paul", dur=0)
P(0.7)
L("asher", "I'm not Luke.", speed=0.9, gap=0.7)
E("asher", emo="soft", look="down", dur=0.9, at=-0.3)
L("asher", "But... thank you. For thinking I could be someone so dear to you.", speed=0.86, gap=0.6)

S("cell_paul_cu")
E("paul", emo="puzzled", look="asher", dur=0.6)
P(0.3)
L("paul", "Then who are you, my friend?", speed=0.86, gap=0.8)

S("cell_asher_cu", zoom=(1.0, 1.07))
E("asher", emo="cold_pain", look="paul", dur=0.8)
L("asher", "Someone you met once... in Jerusalem. A long time ago.", speed=0.88, gap=0.5)
L("asher", "The street of the potters. A house with a blue door.", speed=0.88, gap=0.6)

S("cell_paul_ecu")
E("paul", emo="dread", look="asher", dur=2.0)
L("asher", "You came at night... with the temple guard.", speed=0.88, vo=True, gap=0.9)

S("cell_two")
E("asher", emo="anger", pose="hold", dur=0.5)
E("paul", emo="dread", look="asher", dur=0)
L("asher", "You dragged a man named Yosef into the street.", speed=0.92, gap=0.4)
E("paul", emo="horror_quiet", look="down", ls=0.6, dur=1.0)
L("asher", "In front of his wife.", speed=0.9, gap=0.3)
L("asher", "In front of his son.", speed=0.86, gap=1.0)
E("paul", emo="grief", tears=0.6, dur=0.8, at=-0.5)
L("paul", "Yosef...", speed=0.78, vol=0.7, gap=1.1)

S("cell_asher_cu")
E("asher", emo="cry_anger", tears=0.6, look="paul", dur=0.6)
L("asher", "I was eight years old. I watched it all... through a crack in the door.", speed=0.9, gap=0.9)
E("asher", emo="cry", tears=1.0, dur=0.8, at=-0.3)
L("asher", "He never came home.", speed=0.8, fx="tremble", gap=1.2)

S("cell_paul_cu", zoom=(1.0, 1.05))
E("paul", emo="grief", look="down", tears=0.8, dur=0)
X("breath_shaky", at=0.5)
P(2.0)
L("paul", "He looked at me.", speed=0.8, gap=0.8)
E("paul", look="far", emo="haunted", dur=1.0)
L("paul", "When we bound his hands... he looked straight at me.", speed=0.84, gap=0.5)
L("paul", "Not with hatred. I knew hatred.", speed=0.84, gap=0.6)
L("paul", "He looked at me as if... as if he was sorry for me.", speed=0.8, gap=0.6)

# ---------------------------------------------------------------------------
# ACT 3 — Memory: Jerusalem, 34 years earlier
# ---------------------------------------------------------------------------
S("jer_crack", trans="memory", grade="memory_blue")
T("place", "JERUSALEM  ·  THIRTY-FOUR YEARS EARLIER", at=0.3, dur=3.4)
M("jerusalem")
X("jer_amb", at=0)
E("yosef", emo="pained", look="away", pose="bound", dur=0)
E("saul", emo="fury", look="yosef", pose="scroll", dur=0)
E("child", emo="terror", tears=0.7, look="out", dur=0)
P(3.0)

S("jer_child", grade="memory_blue")
T("name", "YOUNG ASHER", who="child", at=0.2, dur=2.6)
E("child", emo="terror", tears=1.0, dur=0.3)
P(0.5)
L("child", "Father! Don't go!", speed=0.92, gap=0.8)

S("jer_yosef", grade="memory_blue")
T("name", "YOSEF  ·  ASHER'S FATHER", who="yosef", at=0.3, dur=3.4)
E("yosef", emo="pained", look="back", dur=0)
P(0.6)
E("yosef", emo="tender", look="back", dur=1.0)
P(0.4)
L("yosef", "Asher, my love... don't be afraid for me.", speed=0.84, gap=0.5)
L("yosef", "I am in the hands of God. He will keep me...", speed=0.84, gap=0.3)
L("yosef", "and He will keep you, forever and ever.", speed=0.82, gap=0.5)

S("jer_saul", grade="memory_blue")
T("name", "PAUL", who="saul", at=0.1, dur=2.8)
E("saul", emo="fury", look="yosef", dur=0)
P(0.3)
L("saul", "Take him!", speed=1.05, gap=0.5)
E("saul", emo="unsettled", look="yosef", dur=0.8)
P(0.5)

S("jer_yosef_look", grade="memory_blue", zoom=(1.0, 1.05))
E("yosef", emo="compassion", look="paul", dur=0.9)
P(0.8)
L("yosef", "May God open your eyes, my son.", speed=0.82, gap=1.2)

S("jer_saul", grade="memory_blue")
E("saul", emo="uneasy", look="away_down", dur=0.9)
P(1.8)

# ---------------------------------------------------------------------------
# Back in the cell: Paul answers anger without retreating from grace
# ---------------------------------------------------------------------------
S("cell_asher_cu", trans="memory_out")
E("asher", emo="fury_cry", tears=1.0, look="paul", dur=0.4)
L("asher", "Don't.", speed=0.9, gap=0.5)
L("asher", "You don't get to remember him.", speed=0.9, gap=0.7)

S("cell_paul_cu")
E("paul", emo="earnest", look="asher", tears=0.4, dur=1.0)
L("paul", "I remember him because I must.", speed=0.84, gap=0.5)
L("paul", "Every soul I wounded is a soul the Son came to save...", speed=0.84, gap=0.3)
L("paul", "your father... and you... and even me.", speed=0.82, gap=0.6)
E("paul", emo="fervent", tears=0.2, dur=1.0)
L("paul", "I will spend every breath I have left proclaiming His mercy...", speed=0.84, gap=0.3)
L("paul", "until it reaches all of them. Even the ones I lost.", speed=0.82, gap=0.8)

S("cell_two")
E("asher", emo="cold", pose="drop_bread", look="paul", tears=0.0, dur=0.9)
E("asher", tearFlow=0.0, tears=0.0, dur=3.0, at=0.2)
X("bread_thud", at=0.75)
P(1.2)
L("asher", "They read your letter to us in Rome.", tts="They red your letter to us in Rome.", speed=0.9, gap=0.5)
L("asher", "“If your enemy is hungry, feed him.”", tts="If your enemy is hungry... feed him.", speed=0.88, gap=0.6)
L("asher", "So. I'm feeding you.", speed=0.88, gap=1.0)

S("cell_paul_cu")
E("paul", look="bread", emo="moved", dur=0.8)
P(1.0)
E("paul", look="asher", tears=0.7, dur=0.8)
P(0.4)
L("paul", "Then you have done what I only wrote about.", speed=0.84, gap=0.6)

S("cell_asher_cu")
E("asher", emo="bitter_laugh", look="away", tears=0.3, dur=0.5)
L("asher", "Spare me. Don't make me a saint.", speed=0.9, gap=0.5)
E("asher", emo="anger", look="paul", tears=0.0, dur=0.6)
L("asher", "They call you a saint. Do they even know what you were?", speed=0.92, gap=0.7)

S("cell_paul_cu")
E("paul", emo="ashamed", look="asher", tears=0.3, dur=2.0)
L("paul", "They know.", speed=0.84, gap=0.4)
L("paul", "I put it in my letters, so that no one forgets.", speed=0.84, gap=0.6)
E("paul", look="hands", emo="guilt", tears=0.4, dur=1.0)
L("paul", "I was a blasphemer... and a persecutor... and a violent man.", speed=0.8, gap=0.8)
L("paul", "I thought I was defending God.", speed=0.84, gap=0.6)
E("paul", look="asher", emo="haunted", dur=0.7, at=-0.3)
L("paul", "I was hunting Him.", speed=0.8, gap=1.0)

# ---------------------------------------------------------------------------
# ACT 4 — Memory: the road to Damascus
# ---------------------------------------------------------------------------
S("dam_wide", trans="dissolve", grade="memory_gold")
T("place", "THE ROAD TO DAMASCUS", at=0.3, dur=3.2)
M("damascus")
X("desert_amb", at=0)
E("saul", emo="determined", pose="walk", look="ahead", dur=0)
L("paul", "I carried Yosef's face with me, all the way to Damascus.", speed=0.86, vo=True, gap=0.5)
L("paul", "I had letters to arrest more of them.", speed=0.86, vo=True, gap=0.5)

S("dam_saul_cu", grade="memory_gold")
T("name", "PAUL", who="saul", at=0.1, dur=2.6)
E("saul", emo="determined", look="ahead", dur=0)
P(1.3)
E("saul", look="up", emo="shock", dur=0.35)
X("light_swell", at=-0.4)
P(1.5)

S("dam_flash")
P(0.9)

S("dam_saul_kneel")
E("saul", emo="terror", pose="kneel_shield", look="down", dur=0)
X("divine_rumble", at=0)
L("jesus", "Paul... Paul. Why do you persecute me?", speed=0.84, fx="divine", gap=0.7)
L("saul", "Who are you, Lord?", speed=0.82, fx="tremble", gap=0.8)
L("jesus", "I am Jesus. I came to save those who are not yet saved.", speed=0.82, fx="divine", gap=0.6)

S("dam_jesus", zoom=(1.0, 1.04))
E("jesus", emo="compassion", pose="reach", look="down", dur=0)
P(0.6)
L("jesus", "You are precious to me, Paul.", speed=0.8, fx="divine", gap=0.4)
L("jesus", "Open your heart to me... and carry the Holy Spirit, with me and my Father.", speed=0.8, fx="divine", gap=0.8)
L("paul", "I knew what I deserved.", speed=0.84, vo=True, gap=0.6)
L("paul", "But He looked at me... the same way Yosef had.", speed=0.82, vo=True, gap=0.7)

S("dam_saul_up")
E("saul", emo="broken_wonder", tears=1.0, look="up", pose="kneel_up", dur=0)
L("paul", "I was shown mercy, because I acted in ignorance and unbelief.", speed=0.84, vo=True, gap=0.4)
L("paul", "The grace of our Lord was poured out on me abundantly...", speed=0.84, vo=True, gap=0.2)
L("paul", "along with the faith and love that are in Christ Jesus.", speed=0.84, vo=True, gap=0.6)

S("dam_hands")
L("paul", "I thank Christ Jesus our Lord, who has given me strength...", speed=0.84, vo=True, gap=0.3)
L("paul", "that He considered me trustworthy, appointing me to His service.", speed=0.84, vo=True, gap=0.6)
L("paul", "He chose me... the very one who hunted Him.", speed=0.8, vo=True, gap=1.0)

# ---------------------------------------------------------------------------
# ACT 5 — The cell. The worst of sinners. Hate that does not vanish. The bread.
# ---------------------------------------------------------------------------
S("cell_asher_cu", trans="memory_out")
M("cell2")
E("asher", emo="anguish", tears=0.8, tearFlow=0.5, look="paul", dur=0.3)
L("asher", "So that's it?", speed=0.9, gap=0.5)
L("asher", "You saw a light... and it all washed away?", speed=0.9, gap=0.6)
L("asher", "And my father was just... the price of your conversion?", speed=0.88, gap=0.9)

S("cell_paul_cu")
E("paul", emo="pained", look="asher", tears=0.0, dur=0.6)
L("paul", "No.", speed=0.8, gap=0.6)
L("paul", "Nothing washes him away. Not for me.", speed=0.84, gap=0.6)
L("paul", "I see his face every time I write the word “mercy.”", tts="I see his face, every time I write the word... mercy.", speed=0.82, gap=0.9)

S("cell_two")
E("paul", pose="lean", emo="earnest", look="asher", dur=1.2)
E("asher", emo="cold", look="paul", tears=0.0, tearFlow=0.0, dur=3.0)
X("chains_move", at=0.2)
P(0.6)
L("paul", "Here is a trustworthy saying that deserves full acceptance:", speed=0.84, gap=0.4)
L("paul", "Christ Jesus came into the world to save sinners...", speed=0.84, gap=0.5)

S("cell_paul_cu", zoom=(1.0, 1.06))
E("paul", emo="earnest", look="asher", dur=0)
L("paul", "of whom I am the worst.", speed=0.78, gap=0.9)
L("paul", "But for that very reason, I was shown mercy...", speed=0.84, gap=0.3)
E("paul", emo="fervent", dur=0.8)
L("paul", "by Him, my Lord... the One who saved me...", speed=0.82, gap=0.4)
L("paul", "so that in me, the worst of sinners, Christ Jesus might display His immense patience...", speed=0.84, gap=0.3)
E("paul", emo="tender", dur=1.0, ls=0.5)
L("paul", "as an example for those who would believe in Him... and receive eternal life.", speed=0.84, gap=1.0)

S("cell_asher_cu")
E("asher", emo="conflicted", look="away", pose="empty", dur=0.8)
L("asher", "I came here to hate you.", speed=0.88, gap=0.8)
L("asher", "I rehearsed it. For years.", speed=0.86, gap=0.6)
E("asher", emo="anger", look="paul", dur=0.6)
L("asher", "You say all these beautiful things...", speed=0.88, gap=0.4)
L("asher", "but I still hate you. I hope you know that.", speed=0.86, gap=0.9)

S("cell_paul_cu")
E("paul", emo="calm", look="asher", dur=0.6)
L("paul", "I know.", speed=0.82, gap=0.6)
L("paul", "And I will not hate you back.", speed=0.82, gap=0.6)
E("paul", emo="compassion", dur=1.0)
L("paul", "Hate me, if you must. I will still pray for you, every day I have left...", speed=0.84, gap=0.3)
L("paul", "and I will still call you my brother.", speed=0.82, gap=0.8)

S("cell_asher_cu")
E("asher", emo="cold", look="paul", dur=0.5)
L("asher", "I am not your brother.", speed=0.86, gap=0.9)

S("cell_paul_cu")
E("paul", emo="gentle_smile", look="asher", dur=0.8)
L("paul", "Not yet, perhaps.", speed=0.82, gap=0.5)
L("paul", "But the Lord is patient. He was patient with me.", speed=0.82, gap=1.0)

S("cell_asher_cu")
E("asher", emo="broken", look="bread", tears=0.6, tearFlow=0.3, dur=1.0)
L("asher", "And still...", speed=0.85, gap=0.6)
L("asher", "I brought the bread.", speed=0.82, gap=1.0)

S("cell_memory")
M("turn")
E("asher", emo="broken", look="bread", tears=0.7, tearFlow=0.3, dur=0)
L("jesus", "A new commandment I give you: love one another, as I have loved you.", speed=0.8, vo=True, fx="memory", gap=1.0)

S("cell_kneel")
E("asher", pose="kneel", emo="soft", look="bread", dur=2.0)
X("cloth_kneel", at=0.4)
P(2.6)

S("cell_break_insert")
X("bread_break", at=1.1)
P(3.0)

S("cell_offer")
E("asher", pose="kneel_offer", emo="resolve", tears=0.6, tearFlow=0.2, look="paul", dur=0.8)
E("paul", pose="rest", emo="stunned", look="bread", dur=0)
P(0.6)
L("asher", "I don't forgive you. Not yet.", speed=0.86, gap=0.8)
E("asher", emo="tender_cry", tears=0.8, dur=1.0)
L("asher", "But my father would have shared his bread with you...", speed=0.84, gap=0.4)
L("asher", "so I will.", speed=0.8, gap=1.0)

S("cell_paul_cu", zoom=(1.0, 1.05))
E("paul", emo="sob_smile", tears=1.0, look="bread", dur=0.8)
P(1.2)
E("paul", pose="take_bread", dur=1.0)
X("chains_move", at=0.2)
P(1.1)
E("paul", look="asher", dur=0.6)
L("paul", "Burning coals...", speed=0.78, gap=0.8)
L("paul", "I wrote those words...", speed=0.82, gap=0.4)
L("paul", "I never knew how much the love of Christ would burn me... but for the better.", speed=0.8, gap=1.0)

S("cell_two_light")
E("paul", pose="eat", emo="peace_tears", look="asher", tears=0.5, dur=0.8)
E("asher", pose="kneel_eat", emo="peace_tears", look="paul", tears=0.5, dur=0.8)
L("narrator", "Do not be overcome by evil...", speed=0.88, gap=0.5)
L("narrator", "but overcome evil with good.", speed=0.86, gap=1.6)

# ---------------------------------------------------------------------------
# ACT 6 — The sentence. Romans 8.
# ---------------------------------------------------------------------------
S("cell_door_guard")
X("door_bang", at=0)
M("stop")
E("guard", emo="stern", look="paul", dur=0)
P(0.6)
L("guard", "Time's up.", speed=0.95, gap=0.6)
E("guard", emo="weary", look="paul", dur=0.8)
L("guard", "And you, old man... it's tomorrow. At first light.", speed=0.92, gap=0.7)

S("cell_asher_cu")
E("asher", emo="shock", look="guard", pose="kneel", tears=0.2, dur=0.3)
P(0.5)
L("asher", "Tomorrow?", speed=0.84, gap=0.7)

S("cell_paul_cu")
E("paul", emo="calm", look="guard", pose="rest", tears=0.0, dur=0.6)
L("paul", "Thank you, soldier.", speed=0.84, gap=0.5)
L("guard", "Say your goodbyes.", speed=0.95, vo=True, gap=0.3)
X("door_close", at=0)
P(0.9)

S("cell_asher_cu")
E("asher", emo="fear_for", look="paul", tears=0.5, dur=0.6)
L("asher", "Aren't you afraid?", speed=0.86, gap=0.9)

S("cell_paul_cu")
E("paul", emo="gentle_smile", look="asher", tears=0.3, dur=0.8)
P(0.3)
L("paul", "Afraid?", speed=0.84, gap=0.6)

S("cell_hands_grip")
X("chains_move", at=0.1)
M("romans8")
L("paul", "Who shall separate us from the love of Christ?", speed=0.84, gap=0.5)

S("cell_paul_cu")
E("paul", emo="fervent", look="asher", pose="grip", dur=0.6)
L("paul", "Shall trouble, or hardship, or persecution...", speed=0.86, gap=0.2)
L("paul", "or famine, or nakedness, or danger, or sword?", speed=0.86, gap=0.5)

S("cell_window")
L("paul", "As it is written: “For your sake we face death all day long;", tts="As it is written: For your sake, we face death all day long.", speed=0.86, vo=True, gap=0.2)
L("paul", "we are considered as sheep to be slaughtered.”", tts="We are considered as sheep to be slaughtered.", speed=0.84, vo=True, gap=0.6)

S("cell_paul_cu", zoom=(1.0, 1.08))
E("paul", emo="triumph", look="asher", dur=0.5)
L("paul", "No! In all these things we are more than conquerors...", speed=0.86, gap=0.2)
L("paul", "through Him who loved us.", speed=0.82, gap=0.6)

S("cell_two_light")
E("asher", pose="kneel", emo="awe_tears", look="paul", tears=0.6, tearFlow=0.3, dur=0.6)
L("paul", "For I am convinced that neither death nor life,", speed=0.86, gap=0.15)
L("paul", "neither angels nor demons, neither the present nor the future, nor any powers,", speed=0.86, gap=0.15)
L("paul", "neither height nor depth, nor anything else in all creation...", speed=0.86, gap=0.3)

S("cell_paul_cu", zoom=(1.03, 1.1))
E("paul", emo="triumph", look="asher", tears=0.3, dur=0.5)
L("paul", "will be able to separate us from the love of God...", speed=0.82, gap=0.25)

S("cell_asher_cu", zoom=(1.0, 1.06))
E("asher", emo="awe_tears", look="paul", tears=0.9, tearFlow=0.6, dur=0.6)
E("asher", nod=1, at=0.5)
L("paul", "that is in Christ Jesus our Lord.", speed=0.8, vo=True, gap=0.6)
E("asher", nod=1, at=-0.2)
P(1.6)

# ---------------------------------------------------------------------------
# EPILOGUE — Dawn
# ---------------------------------------------------------------------------
S("dawn_road", trans="dissolve")
M("dawn")
X("dawn_amb", at=0)
E("asher", emo="peace_tears", look="far", pose="hold_half", dur=0)
P(0.8)
L("narrator", "At first light, they led the old man out of the city.", speed=0.88, gap=0.6)
L("narrator", "Among the few who walked with him to the end... was the one who had every reason to hate him.", speed=0.86, gap=1.2)

S("dawn_asher_cu", zoom=(1.0, 1.05))
E("asher", emo="peace_tears", look="up", tears=0.6, tearFlow=0.3, dur=0)
P(1.0)
L("asher", "Lord... I don't know how to love him yet.", speed=0.8, gap=0.7)
E("asher", emo="tender", look="up", dur=1.0)
L("asher", "Teach me.", speed=0.78, gap=1.4)

S("dawn_jesus", trans="dissolve", zoom=(1.0, 1.04))
E("jesus", emo="warm_smile", look="cam", pose="open_arms", dur=0)
P(1.0)
L("jesus", "Learn from me... for I am gentle and humble in heart.", speed=0.8, fx="soft_divine", gap=2.2)

S("end_card", trans="dissolve")
T("end", "A new commandment I give you.\nMy command is this:\nlove one another\nas I have loved you.", at=0.3, dur=7.6)
P(7.8)
