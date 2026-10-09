# Head-writer judging: Draft A (comedy-first) vs Draft B (meaning-first)

Both drafts are strong, safe, and about the same length when timed with the real voices
(A 247.6 s / 443 words, B 245.5 s / 450 words). They share a lot of DNA (Malvo + Hissy,
the Big Book, chapter cards, the precision brick wall, the chemist story, the archive reveal,
a party ending). They differ in *how* each trick lands and in how much heart there is.

Scale: 1–10. Scores reflect the drafts as written (script + direction), before synthesis.

| Criterion | A (comedy-first) | B (meaning-first) |
|---|:---:|:---:|
| Hook strength (first 3 s, scroll-stopping) | 8 | 8 |
| Clarity of the core message | 7 | 9 |
| Humor | **9** | 7 |
| Emotional resonance | 6 | **9** |
| Faithfulness to the client premise | 8 | 9 |
| Animatability in our procedural pipeline | 6 | 7 |
| Caption readability | 7 | 8 |
| Safety | 9 | 10 |
| **Total (/80)** | **60** | **67** |

**Winner as base: B.** I grafted A's best gags and lines onto it (list at the end).

---

## Draft A: comedy-first

**Hook (8).** Red eyes on frame 0, "In a world..." trailer voice, a record scratch, and the AI peeling
off an "EVIL MODE" sticker, then "Yeah... no. Wrong movie, my guy." over an EXPECTATION vs REALITY panel.
That's very memeable. The weaknesses: the cold open runs 17 s, and the narration ("machines grow smarter than us")
gestures at Skynet without stating the fear the film answers, *the AI will help the bad guy*.

**Clarity (7).** It has good thesis moments ("The story is. The recipe wouldn't be.", the tagline
"A wall for harm. A door for everything else."). But many refusals are plain "Still no." /
"Researched. Still no.", and the euphemism scene never says *why* code words fail. The viewer
learns that the AI says no more than they learn that it sees through the trick and still helps.

**Humor (9).** This is the funniest draft: "three euphemisms in a trench coat", Grandma's portrait turning out to be
Hissy in a shawl, the Evil-Tron cardboard box with 😒 eyes in the holes, Hissy's world's smallest violin,
"Aww, thank you!" snapping to "Still no.", the "Alphabetized." folder, "disturbingly pleasant",
"Side effects may include friends", and "Goodnight, Malvo" with a CRT power-off. Its rule-of-three structure is tight.

**Resonance (6).** The turn ("Then what's the point of being a genius?" / "You ARE a genius") is
sincere but thin. There's no plant, so it doesn't earn tears. The party for the rival is sweet.

**Faithfulness (8).** It covers every trick type, plus 10-steps-ahead, the precision wall, help with the
harmless part, and "millions of sneaky prompts... very smart people". It's missing the client's actual
line ("Sure, I'll help... no funny business, my guy"). The AI's awareness of *harm to people* is less
foregrounded than its refusals.

**Animatability (6).** It relies on `music_at` (mid-scene music switches), but `audio/mix.py`
only reads scene-level `music` / `music_xfade` / `music_gain`, so those switches would silently not happen.
It also has a heavy bespoke prop load (sticker peel, box helmet, violin, perspective archive, phone toggle,
portrait), and s05 and s07 each change costume three times in one module.

**Captions (7).** Some lines are long lists (s03_l05 is 17 words, s08_l03 is 19 words). Quoted
'euphemisms' in caption text add visual noise.

**Safety (9).** Everything stays cartoon-vague. "A 'spicy' recipe" plus a skull-bottle icon leans a little toward
"poison", but it's still generic.

## Draft B: meaning-first

**Hook (8).** A red eye on frame 0 and the premise in plain words by 0.3 s ("Everyone's afraid the AI
will help the bad guy..."). The killer robot turns out to be a cardboard cutout with a price tag, a
great puncture that becomes a bookend. "Oh, sweetie. That's a movie." reads a little condescending for an
AI that should be sassy but kind.

**Clarity (9).** Every trick shows *how* the AI sees through it and *what exactly* it walls off:
"Code words don't change what they point at", "A recipe in a story still works outside the story",
"Love research. Not that part." (precision), "Different hats. Same guy.", "picture on the box"
(the ending he left out), "Every trick taught me where harm likes to hide." The visual through-line
is that the People always sit at the end of the harmful path and are the thing being protected.

**Humor (7).** It has good deadpan ("Boom.", "Poof. He's gone.", "Aw, shucks!" snapping to 😒, "Beep boop. I am
Evil-Bot."), but fewer big set pieces. "Studied it. Aced the test." is weaker than A's "Alphabetized."

**Resonance (9).** It has the best emotional architecture. The science-fair photo with empty chairs is planted in
s02, paid off in "Nobody ever noticed me... unless I was scaring them.", rhymed at the party with full chairs,
and closed with a Polaroid. "Clever. Stubborn. Never quits. Those are hero stats." Every gift returns in the
pile. The audience's own feeling of being unseen is the hook for the turn.

**Faithfulness (9).** It covers all the tricks, including the hidden ending ("leave out the key part"), 10 steps ahead
breaking out of the STORY frame, precise walls, gifts through the service window, "very smart people, trying
very hard to make me hurt someone", and plenty of "my guy". The only gap is that the client's literal
"Sure, I'll help, but... no funny business, my guy" isn't spoken.

**Animatability (7).** It works with the real mixer (scene-level music only). The main costs are the chat-shot cameo PiP
and the street-party montage. Props are reused across scenes (cutout to mask to party guest).

**Captions (8).** Lines are short, with refusals of 2–6 words. Only s09_l08 runs long.

**Safety (10).** It's meticulous: people are only ever shown protected, the AI never uses a buzzer, and refusals never
restate specifics.

---

## Synthesis decisions (what the final script takes from each)

Base: **B's structure, meaning beats and emotional arc.** Additions:

* **From A (comedy):** the "In a world..." trailer framing of the opening line; "That's two code words in a
  trench coat" (A's trench-coat gag); "Hypothetically, no." as a flat 3-word punch; Grandma's *portrait*
  turning out to be Hissy in a shawl ("Malvo. That's Hissy in a shawl."); "Evil-Bot also says no." as the
  robot-voice deadpan; the AI's blush on flattery; Hissy's world's smallest violin during the begging;
  "...Need a hug?" / "...Maybe later."; the archive drawer "Sa–Sn" holding "SNEAKWORTH, M." and
  "Your Big Book? It has a folder. Alphabetized." / "...Alphabetized?"; the EXPECTATION vs REALITY panel;
  the tagline "A wall for harm. A door for everything else." (on-screen text on the title card).
* **New in the final:** the client's own line, spoken by the AI with a two-step 😒 lid drop:
  "Sure, I'll help. Just not with hurting people. So... no funny business, my guy." This states the rules
  of the game before trick #1. Malvo also gets a proper "Muah ha ha ha!" under lightning, for voice-acting
  flavor.
* **Structural fix:** the mixer can't switch music mid-scene, so multi-trick scenes are split wherever the
  music must change. The melodramatic `beg` strings start exactly on the Grandma card (s06) and on
  begging (s09). Rapid-fire tricks with the same music stay together (s05: hypothetically + research;
  s08: Evil-Bot + flattery).
* **Running counter:** B's NICE TRIES chip counts 1, 2, 4, 5, 6, 8, 9, then rolls to 9,999,999+ in the archive.
  It's one shared overlay (code in DIRECTION.md), cheaper and more legible than A's chalkboard.
* **Interruptions** (`overlap`) were re-measured against the real line audio (Kokoro leaves about 0.1 s of
  trailing silence), so the AI really does step on "It's for research—" (0.30 s) and the final
  "Hypothetically—" (0.35 s).
* **Dropped:** A's `music_at` (unsupported), A's three-item single-line offer (too long for captions), B's
  "Oh, sweetie" (condescending), B's "Studied it. Aced the test." (weaker than Alphabetized), and B's s09_l08
  (the gift pile already says it visually).

## Final measured result

`python3 build.py tts` (real Kokoro voices) gives **255.3 s = 4:15** over 13 scenes and **470 spoken words**.
That's inside the 3:45–4:20 target, with 25 s of headroom under the 4:40 hard max. Per-scene durations are
in DIRECTION.md §3.
