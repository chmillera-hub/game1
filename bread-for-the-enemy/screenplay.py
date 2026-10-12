"""
BREAD FOR THE ENEMY — screenplay.

A short animated film weaving together:
  Romans 12:17-21, John 13:34 / 15:12, 1 Timothy 1:12-16, Romans 8:35-39 (NIV wording).

The story: Rome, around AD 67. Asher, the son of a man Saul of Tarsus dragged from
his home in Jerusalem 34 years earlier, brings bread to the imprisoned apostle Paul
on the night before Paul's execution, because Paul's own letter said
"If your enemy is hungry, feed him."

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
  T(kind, text, **o)  on-screen text card (title / place / end)
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
L("jesus", "A new command I give you.", speed=0.84, gap=0.55)
E("jesus", look="cam_l", dur=0.9)
L("jesus", "Love each other...", speed=0.84, gap=0.3)
E("jesus", look="cam", emo="tender_smile", ls=0.1, dur=0.8)
L("jesus", "as I have loved you.", speed=0.8, gap=1.3)

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
E("asher", emo="cold", look="door", pose="hold", dur=0)
P(0.9)
L("narrator", "Behind this door, an old man waits to die... for the name of Jesus.", speed=0.9, gap=0.6)
L("narrator", "And the man standing outside it... has hated him for most of his life.", speed=0.9, gap=0.8)

S("street_asher_cu", zoom=(1.0, 1.04))
E("asher", emo="cold", look="door", dur=0)
P(0.9)
E("asher", look="bread", emo="bitter", dur=0.9)
P(0.9)
L("asher", "Bread.", speed=0.9, gap=1.0)
E("asher", look="door_low", emo="conflicted", ls=0.5, dur=1.0)
L("asher", "I came all this way... with bread.", speed=0.9, gap=0.9)

S("church_reader", trans="dissolve", grade="memory_warm")
X("room_murmur", at=0)
L("narrator", "Months earlier, his church had gathered to hear a letter read aloud.", speed=0.9, gap=0.5)
E("elder", emo="calm", look="scroll", dur=0)
L("elder", "Paul, a servant of Christ Jesus... to all in Rome who are loved by God.", speed=0.9, gap=0.2)

S("church_asher", grade="memory_warm")
E("asher", emo="shock", look="reader", dur=0.25, at=0.1)
P(1.1)
E("asher", emo="cold", look="reader", dur=1.2)
L("elder", "Do not repay anyone evil for evil.", speed=0.9, vo=True, gap=0.5)
E("asher", emo="bitter", ls=0.4, dur=0.8)
L("elder", "If it is possible, as far as it depends on you... live at peace with everyone.", speed=0.9, vo=True, gap=0.5)

S("church_reader", grade="memory_warm")
L("elder", "If your enemy is hungry, feed him. If he is thirsty, give him something to drink.", speed=0.9, gap=0.4)
L("elder", "In doing this, you will heap burning coals on his head.", speed=0.88, gap=0.3)

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
# ACT 2 — The cell
# ---------------------------------------------------------------------------
S("cell_wide")
X("door_creak", at=0.0)
X("cell_amb", at=0.0)
M("cell")
E("paul", pose="write", emo="squint", look="parchment", dur=0)
E("asher", pose="hold", emo="cold", look="paul", dur=0)
P(1.6)
E("paul", look="door", emo="squint", dur=0.6)
P(0.7)
L("paul", "Luke? ...Is that you?", speed=0.88, gap=0.8)

S("cell_paul_cu")
E("paul", emo="squint", look="asher", dur=0)
P(0.5)
E("paul", emo="warm", dur=0.8)
L("paul", "No... forgive me. My eyes are not what they were.", speed=0.86, gap=0.4)
E("paul", pose="rest", emo="smile", dur=0.8)
L("paul", "Come in, friend. Come in.", speed=0.86, gap=0.5)
E("paul", look="bread", emo="joy", dur=0.5)
L("paul", "Is that bread? God bless you.", speed=0.88, gap=0.5)
E("paul", look="down", emo="weary", dur=0.9)
L("paul", "Most of the brothers are afraid to come now. I don't blame them.", speed=0.86, gap=0.6)

S("cell_asher_cu")
E("asher", emo="cold", look="paul", dur=0)
P(0.6)
L("asher", "I'm not here because I'm brave.", speed=0.92, gap=0.9)
L("asher", "You don't remember me.", speed=0.88, gap=0.6)

S("cell_paul_cu")
E("paul", emo="puzzled", look="asher", dur=0.6)
P(0.5)
L("paul", "Should I?", speed=0.88, gap=0.9)

S("cell_asher_cu", zoom=(1.0, 1.07))
E("asher", emo="cold_pain", look="paul", dur=0.8)
L("asher", "Jerusalem. The street of the potters.", speed=0.9, gap=0.5)
L("asher", "A house with a blue door.", speed=0.88, gap=0.6)

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
E("paul", emo="grief", dur=0.8, at=-0.5)
L("paul", "Yosef...", speed=0.78, vol=0.7, gap=1.1)

S("cell_asher_cu")
E("asher", emo="cry_anger", tears=0.6, look="paul", dur=0.6)
L("asher", "I was eight years old. I watched it all... through a crack in the door.", speed=0.9, gap=0.9)
E("asher", emo="cry", tears=1.0, dur=0.8, at=-0.3)
L("asher", "He never came home.", speed=0.8, fx="tremble", gap=1.2)

S("cell_paul_cu", zoom=(1.0, 1.05))
E("paul", emo="grief", look="down", tears=0.8, dur=0)
X("chain_tremble", at=0.4)
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
M("jerusalem")
X("jer_amb", at=0)
E("yosef", emo="pained", look="away", pose="bound", dur=0)
E("saul", emo="fury", look="yosef", pose="scroll", dur=0)
E("child", emo="terror", tears=0.7, look="out", dur=0)
P(2.6)

S("jer_child", grade="memory_blue")
E("child", emo="terror", tears=1.0, dur=0.3)
P(0.5)
L("child", "Abba...", speed=0.78, fx="child_whisper", gap=0.8)

S("jer_yosef", grade="memory_blue")
E("yosef", emo="pained", look="back", dur=0)
P(0.6)
E("yosef", emo="tender", look="back", dur=1.0)
P(0.4)
L("yosef", "Asher. Don't be afraid.", speed=0.84, gap=0.6)
L("yosef", "Remember what He taught us.", speed=0.84, gap=0.5)
L("yosef", "Love each other... as He loved us.", speed=0.8, gap=0.4)

S("jer_saul", grade="memory_blue")
E("saul", emo="fury", look="yosef", dur=0)
P(0.2)
L("saul", "Take him!", speed=1.05, gap=0.6)
E("saul", emo="unsettled", look="yosef", dur=0.8)
P(0.6)

S("jer_yosef_look", grade="memory_blue", zoom=(1.0, 1.06))
E("yosef", emo="compassion", look="cam", dur=0.9)
P(3.4)

S("jer_saul", grade="memory_blue")
E("saul", emo="uneasy", look="away_down", dur=0.9)
P(1.8)

# ---------------------------------------------------------------------------
# Back in the cell
# ---------------------------------------------------------------------------
S("cell_asher_cu", trans="memory_out")
E("asher", emo="fury_cry", tears=1.0, look="paul", dur=0.4)
L("asher", "Don't.", speed=0.9, gap=0.5)
L("asher", "You don't get to remember him. He wasn't yours.", speed=0.9, gap=0.7)

S("cell_paul_cu")
E("paul", emo="ashamed", look="down", tears=0.8, dur=0.6)
L("paul", "You're right.", speed=0.8, gap=0.6)
L("paul", "He wasn't mine. I have no right to any of it.", speed=0.84, gap=0.7)

S("cell_two")
E("asher", emo="cold", pose="drop_bread", look="paul", dur=0.9)
X("bread_thud", at=0.75)
P(1.2)
L("asher", "They read your letter in our church.", speed=0.9, gap=0.5)
L("asher", "“If your enemy is hungry, feed him.”", tts="If your enemy is hungry... feed him.", speed=0.88, gap=0.6)
L("asher", "So. I'm feeding you.", speed=0.88, gap=1.0)

S("cell_paul_cu")
E("paul", look="bread", emo="moved", dur=0.8)
P(1.0)
E("paul", look="asher", tears=1.0, dur=0.8)
P(0.4)
L("paul", "Then you have done what I only wrote about.", speed=0.84, gap=0.6)

S("cell_asher_cu")
E("asher", emo="bitter_laugh", look="away", tears=0.6, dur=0.5)
L("asher", "Don't. Don't make me a saint.", speed=0.9, gap=0.5)
E("asher", emo="anger", look="paul", dur=0.6)
L("asher", "They call you a saint. Do they even know what you were?", speed=0.92, gap=0.7)

S("cell_paul_cu")
E("paul", emo="ashamed", look="asher", dur=0.5)
L("paul", "They know.", speed=0.84, gap=0.4)
L("paul", "I put it in my letters, so that no one forgets.", speed=0.84, gap=0.6)
E("paul", look="hands", emo="guilt", dur=1.0)
L("paul", "I was a blasphemer... and a persecutor... and a violent man.", speed=0.8, gap=0.8)
L("paul", "I thought I was defending God.", speed=0.84, gap=0.6)
E("paul", look="asher", emo="haunted", dur=0.7, at=-0.3)
L("paul", "I was hunting Him.", speed=0.8, gap=1.0)

# ---------------------------------------------------------------------------
# ACT 4 — Memory: the road to Damascus
# ---------------------------------------------------------------------------
S("dam_wide", trans="dissolve", grade="memory_gold")
M("damascus")
X("desert_amb", at=0)
E("saul", emo="determined", pose="walk", look="ahead", dur=0)
L("paul", "I carried your father's face all the way to Damascus.", speed=0.86, vo=True, gap=0.5)
L("paul", "I had letters to arrest more of them.", speed=0.86, vo=True, gap=0.5)

S("dam_saul_cu", grade="memory_gold")
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
L("jesus", "Saul... Saul. Why do you persecute me?", speed=0.84, fx="divine", gap=0.7)
L("saul", "Who are you, Lord?", speed=0.82, fx="tremble", gap=0.8)
L("jesus", "I am Jesus... whom you are persecuting.", speed=0.8, fx="divine", gap=0.6)

S("dam_jesus", zoom=(1.0, 1.04))
E("jesus", emo="sorrow_love", pose="reach", look="down", dur=0)
P(1.3)
L("paul", "I knew what I deserved.", speed=0.84, vo=True, gap=0.6)
L("paul", "But He looked at me... the same way your father did.", speed=0.82, vo=True, gap=0.7)

S("dam_saul_up")
E("saul", emo="broken_wonder", tears=1.0, look="up", pose="kneel_up", dur=0)
L("paul", "I was shown mercy, because I acted in ignorance and unbelief.", speed=0.84, vo=True, gap=0.4)
L("paul", "The grace of our Lord was poured out on me abundantly...", speed=0.84, vo=True, gap=0.2)
L("paul", "along with the faith and love that are in Christ Jesus.", speed=0.84, vo=True, gap=0.6)

S("dam_hands")
L("paul", "I thank Christ Jesus our Lord, who has given me strength...", speed=0.84, vo=True, gap=0.3)
L("paul", "that He considered me trustworthy, appointing me to His service.", speed=0.84, vo=True, gap=0.6)
L("paul", "Me.", speed=0.78, vo=True, gap=1.0)

# ---------------------------------------------------------------------------
# ACT 5 — The cell. The worst of sinners. The bread.
# ---------------------------------------------------------------------------
S("cell_asher_cu", trans="memory_out")
M("cell2")
E("asher", emo="anguish", tears=1.0, look="paul", dur=0.3)
L("asher", "So that's it?", speed=0.9, gap=0.5)
L("asher", "You saw a light... and it all washed away?", speed=0.9, gap=0.6)
L("asher", "And my father was just... the price of your conversion?", speed=0.88, gap=0.9)

S("cell_paul_cu")
E("paul", emo="pained", look="asher", dur=0.6)
L("paul", "No.", speed=0.8, gap=0.6)
L("paul", "Nothing washes him away. Not for me.", speed=0.84, gap=0.6)
L("paul", "I see his face every time I write the word “mercy.”", tts="I see his face, every time I write the word... mercy.", speed=0.82, gap=0.9)

S("cell_two")
E("paul", pose="lean", emo="earnest", look="asher", dur=1.2)
X("chains_move", at=0.2)
P(0.6)
L("paul", "Here is a trustworthy saying that deserves full acceptance:", speed=0.84, gap=0.4)
L("paul", "Christ Jesus came into the world to save sinners...", speed=0.84, gap=0.5)

S("cell_paul_cu", zoom=(1.0, 1.06))
E("paul", emo="earnest", look="asher", dur=0)
L("paul", "of whom I am the worst.", speed=0.78, gap=0.9)
L("paul", "But for that very reason, I was shown mercy...", speed=0.84, gap=0.3)
L("paul", "so that in me, the worst of sinners, Christ Jesus might display His immense patience...", speed=0.84, gap=0.3)
E("paul", emo="tender", dur=1.0, ls=0.5)
L("paul", "as an example for those who would believe in Him... and receive eternal life.", speed=0.84, gap=1.0)

S("cell_asher_cu")
E("asher", emo="conflicted", look="away", pose="empty", dur=0.8)
L("asher", "I came here to hate you.", speed=0.88, gap=0.8)
L("asher", "I rehearsed it. For years.", speed=0.86, gap=0.6)
E("asher", emo="anguish", look="away_down", dur=0.6)
L("paul", "I know. And I deserve every word.", speed=0.82, vo=True, gap=0.6)
E("asher", emo="laugh_sob", look="paul", dur=0.5)
L("asher", "That's the worst part. You do deserve it.", speed=0.88, gap=0.7)
E("asher", emo="broken", look="bread", dur=1.0)
L("asher", "And I still...", speed=0.85, gap=0.6)
L("asher", "I still brought the bread.", speed=0.82, gap=1.0)

S("cell_memory")
M("turn")
E("asher", emo="broken", look="bread", tears=1.0, dur=0)
L("yosef", "Love each other...", speed=0.8, vo=True, fx="memory", gap=0.25)
L("jesus", "as I have loved you.", speed=0.8, vo=True, fx="memory", gap=1.2)

S("cell_kneel")
E("asher", pose="kneel", emo="soft", look="bread", dur=2.0)
X("cloth_kneel", at=0.4)
P(2.6)

S("cell_break_insert")
X("bread_break", at=1.1)
P(3.0)

S("cell_offer")
E("asher", pose="kneel_offer", emo="tender_cry", look="paul", dur=0.8)
E("paul", pose="rest", emo="stunned", look="bread", dur=0)
P(0.6)
L("asher", "My father would have broken it with you.", speed=0.84, gap=0.8)
L("asher", "So... I will.", speed=0.8, gap=1.0)

S("cell_paul_cu", zoom=(1.0, 1.05))
E("paul", emo="sob_smile", tears=1.0, look="bread", dur=0.8)
P(1.2)
E("paul", pose="take_bread", dur=1.0)
X("chains_move", at=0.2)
P(1.1)
E("paul", look="asher", dur=0.6)
L("paul", "Burning coals...", speed=0.78, gap=0.8)
L("paul", "I wrote those words. I never knew how much they burn.", speed=0.8, gap=1.0)

S("cell_two_light")
E("paul", pose="eat", emo="peace_tears", look="asher", dur=0.8)
E("asher", pose="kneel_eat", emo="peace_tears", look="paul", dur=0.8)
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
L("guard", "And you, old man... it's tomorrow. First light. The road to Ostia.", speed=0.92, gap=0.7)

S("cell_asher_cu")
E("asher", emo="shock", look="guard", pose="kneel", dur=0.3)
P(0.5)
L("asher", "Tomorrow?", speed=0.84, gap=0.7)

S("cell_paul_cu")
E("paul", emo="calm", look="guard", pose="rest", dur=0.6)
L("paul", "Thank you, soldier.", speed=0.84, gap=0.5)
L("guard", "Say your goodbyes.", speed=0.95, vo=True, gap=0.3)
X("door_close", at=0)
P(0.9)

S("cell_asher_cu")
E("asher", emo="fear_for", look="paul", dur=0.6)
L("asher", "Aren't you afraid?", speed=0.86, gap=0.9)

S("cell_paul_cu")
E("paul", emo="gentle_smile", look="asher", dur=0.8)
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
E("asher", pose="kneel", emo="awe_tears", look="paul", dur=0.6)
L("paul", "For I am convinced that neither death nor life,", speed=0.86, gap=0.15)
L("paul", "neither angels nor demons, neither the present nor the future, nor any powers,", speed=0.86, gap=0.15)
L("paul", "neither height nor depth, nor anything else in all creation...", speed=0.86, gap=0.3)

S("cell_asher_cu", zoom=(1.0, 1.06))
E("asher", emo="awe_tears", look="paul", tears=1.0, dur=0.6)
L("both", "will be able to separate us from the love of God that is in Christ Jesus our Lord.", speed=0.82, gap=2.2)

# ---------------------------------------------------------------------------
# EPILOGUE — Dawn on the road to Ostia
# ---------------------------------------------------------------------------
S("dawn_road", trans="dissolve")
M("dawn")
X("dawn_amb", at=0)
E("asher", emo="peace_tears", look="far", pose="hold_half", dur=0)
P(0.8)
L("narrator", "At first light, the old man was led out along the road to Ostia.", speed=0.88, gap=0.6)
L("narrator", "Among the few who followed him... was the son of Yosef.", speed=0.86, gap=1.2)

S("dawn_asher_cu", zoom=(1.0, 1.05))
E("asher", emo="peace_tears", look="up", dur=0)
P(1.0)
L("asher", "Love each other...", speed=0.8, gap=0.4)
L("asher", "as He loved us.", speed=0.78, gap=1.4)

S("dawn_jesus", trans="dissolve", zoom=(1.0, 1.04))
E("jesus", emo="warm_smile", look="cam", pose="open_arms", dur=0)
P(1.0)
L("jesus", "As I have loved you.", speed=0.8, fx="soft_divine", gap=2.4)

S("end_card", trans="dissolve")
T("end", "Do not be overcome by evil, but overcome evil with good.", sub="Romans 12:21", at=0.3, dur=7.0)
P(7.2)
