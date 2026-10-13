# Brindle Cross

**Logline:** A deadpan little documentary about a cold town square (its slow clock, its bakery sign, its strictly silent clown) never gets around to introducing the widow who has sat in frame since the first shot, until a child asks for her first name, nobody can answer, and the clown stops mid-bite and carries his supper over to her.

**Runtime estimate:** 03:28

About 272 spoken words: 81 of narration and 191 of dialogue. Every line was rendered with the cast's Kokoro voices and speeds and measured. Together they run 1:39. Kokoro speaks at about 2.7 words a second, faster than the word target assumed, so the remaining 1:49 goes to silent comedy, the turn, and the looks and breaths in Scene 3. Each shot length below is the measured audio plus at least 0.6 s for each listed reaction.

## Cast

**OSWALD BUNCE** — 46
- **Look:**
  - **Build:** He has the tallest silhouette in the film. He is lanky and long-limbed, with a slight stoop.
  - **Face:** A long oval face and a high forehead. His big, mobile dark-auburn eyebrows do most of his acting. He has a long nose with a cold-pink tip, a wide thin mouth with long smile creases, and freckled light-olive skin.
  - **Hair:** Ginger-auburn curls escape from under a dented charcoal bowler. Use hair.py's "messy" style with the curl value raised.
  - **Costume:**
    - A mustard-yellow wool coat two sizes too small. The cuffs stop mid-forearm. It has three buttons, and the middle one strains.
    - A bottle-green waistcoat with mismatched buttons, over a collarless cream shirt. No bow tie.
    - Baggy trousers in a large brown-and-tan check, with cells at least 4 cm across so they don't moiré at 1080 px. Plain tan tweed is the fallback. They are held up with a rope belt.
    - Enormous scuffed oxblood boots, and a bamboo cane with black tape on the crook.
  - He has no moustache and wears no make-up. He is not Chaplin. He is a local man with a routine.
  - **Asset note:** The current "clown" spec in chars.py (dark coat, bow tie, short dark hair) must be updated to this palette.
- **Personality:** He is physically fearless and socially shy. He keeps a silent act on principle. He notices everything and says nothing. When he does speak, his voice is smaller than his body.
- **Voice:** Warm American male (80%) blended with playful American male (20%), pitch −0.5 st, speed 0.92. In Scene 3, mix him close and quiet, almost off-mic.
- **Arc:** He goes from performing for a crowd to performing for one person. He gives away his supper and then his coat. Then, for once, he lets himself be fed, by someone who gets his name right.

**EDITH LUSK** — 79
- **Look:**
  - **Build:** She is the smallest and lowest figure in every frame: short, round and compact. She sits on the pavement with her back to the bakery's warm brick and her knees drawn up.
  - **Face:** A round face, the full cheeks gone a little hollow, with deep smile lines that haven't been used lately. Her skin is warm deep brown, with ashy knuckles. Her eyes are large, dark and very expressive. She wears no glasses, so the eyes stay clear for performance.
  - **Hair:** Silver-white, in a low bun under a dove-gray knitted cloche (the beanie asset with a short brim added).
  - **Costume:** A thin brick-brown wool coat, a faded rust shawl, gray knit gloves, gray stockings and brown shoes.
  - **How she is hidden:** Her costume and shadow hide her. Her skin never does.
    - The coat and shawl are keyed to the brick. In Scenes 1–2 her face sits in the wall's shadow, just outside the warm light.
    - From Shot 3.6 on she gets a cool rim light and a darker, defocused wall behind her face. Her skin saturation and specular sit slightly above the brick's, so her micro-expressions read.
- **Personality:** She is dry, precise and proud, with a retired schoolteacher's crispness. She deflects with facts and small jokes, and she is polite to the point of vanishing. She has been counting for thirty-one weeks.
- **Voice:** Warm American female, pitch −1 st and no lower (−2 st drifts androgynous), speed 0.88. Her age comes from speed and breath, not pitch. Keep the delivery plain and let the pauses do the acting.
- **Arc:** She starts as part of the wall and becomes a person with a first name. Then she is the one who feeds the clown. She ends the film laughing *before* he falls, the way Walter did.

**TOMAS BRANDT** — 52, the baker
- **Look:**
  - **Build:** He has the widest silhouette: barrel chest, short neck, and thick forearms dusted with flour.
  - **Face:** Square, with small kind eyes under heavy lids and a big black-and-salt beard. His crown is bald with a dark fringe. His skin is ruddy pink-beige.
  - **Costume:** A navy work shirt rolled to the elbow, a long white apron, and a white towel with one broad red stripe over his shoulder. The towel has no fine check, because a fine check would shimmer.
- **Personality:** He is gruff, busy and decent. He has seen Edith nearly every day for decades and has never once used her first name.
- **Voice:** Deeper American male, pitch −1 st, speed 0.95.
- **Arc:** Three "Door"s and a "Good": "Teddy. Door." → "Door!" → "It's..." and then "Door, Teddy." → "Good." The last one comes as he pushes the door wide so the heat reaches her.

**TEDDY BRANDT** — 8 (nearly 9)
- **Look:**
  - **Build and face:** Tiny, with a round apple face, big ears, a gap where a front tooth was, and light skin with bright red cheeks.
  - **Hair:** A black mop.
  - **Costume:** An oversized cherry-red bobble hat and a sky-blue toggle duffel coat with a floury handprint on the back.
- **Personality:** He laughs with his whole body and leans in doorways. He asks the questions grown-ups don't, and he insists that the record be correct.
- **Voice:** Playful American male (50%) and warm American female (50%), blended before any shift. Speed 1.05.
  - Raise the pitch +3 st in two passes. First, +2 st with the formants moving too (tts.pitch_shift with formant=False). Then +1 st with formants preserved (formant=True). This makes a smaller vocal tract, not a squeaky adult.
  - Test totals between +2 and +4 st. Avoid +5, which artifacts.
- **Arc:** He starts in the audience and becomes the one who asks the question. He ends up sitting down beside her and asking her himself.

**NARRATOR (V.O.)**
- **Voice:** British male (60%) blended with older British male (40%), pitch −1 st, speed 0.92. If the blend artifacts, use British male alone at −1.5 st.
  - The delivery is flat, unhurried and faintly bored, like a municipal information film.
  - He never emotes. His last line gets a 0.8 s pause before it and nothing else.
- **Arc:** He labels a clock, a lamp, a baker and a boy, and lets the boy correct him. He skips the woman in frame 1. At the end he corrects the record with one fact the viewer can check.

**Non-speaking extras (3).** All three are desaturated so the principals pop:
- **PLUM-COAT WOMAN:** 40s, carries a wicker basket.
- **FLAT-CAP YOUNG MAN:** 20s, gray scarf. He gets the puzzled glance at the empty patch in 1.6.
- **NEWSPAPER GENTLEMAN:** 60s, long navy-black coat, folded paper.

They laugh, toss coins, and walk past Edith without looking. They never step onto the empty patch.

**WALTER LUSK** is never seen and never voiced. He exists only as four things:
- the small seeded rye
- the "KINDLY PAY BEFORE EATING" card in the window
- the slow clock
- the empty patch: the square metre of cobbles at the curb on the left of the lamppost. Oswald tips his hat to it in 1.6. It is kept clear of extras and props in every shot.

## Script

**Global production notes**

- **Format:** 1080×1920 at 24 fps. Frame 1 is a finished, fully lit image: no fade-in.

- **Geography.** The film is blocked to the set already built in env.py (positions in metres):
  - The street runs along X. The shop row faces the square with its facade at y = 4.0, and the pavement spans y = 2.6–4.0.
  - The bakery door is at x = −0.9. The window spans x = 0–2.2, with the card in its glass.
  - Right of the window is a brick pier with the ovens behind it. Edith sits against it at x ≈ 2.9, y ≈ 3.7.
  - The lamppost stands at the curb at x = 1.9, y = 2.85. The empty patch is at x ≈ 1.3, y ≈ 2.4, so from the square the post always separates the patch from Edith.
  - Crates sit right of Edith. The bench, left of the door, is set dressing only. The clock tower rises behind the roofs above Edith.
  - Oswald's pitch is the open cobbles in front of the lamp.
  - Distances: door to Edith 3.8 m, lamp to Edith 1.3 m.
- **Sightline.** From the foot of the wall the roof blocks the dial, so nobody there can see it. Edith never looks at it; she knows it by heart. The dial appears only in cutaways from across the square.
- **Dial cheat.** The built dial is 1.6 m across at 11.6 m high, which is only about 8% of frame from the square. For 1.1, 1.2/3.11, 4.3 and 5.3, either:
  - scale it to about 3.5–4 m and bring the tower forward to y ≈ 8, or
  - use a per-camera dial card.

- **Text placement:**
  - **Labels:** left-aligned at about 56–58% of frame height. Each has the name in white serif small caps, an italic descriptor below and a thin rule. Each fades in over 8 frames and holds for about 3 s.
  - **Subtitles:** burned in, centered at about 64–66%, at most 2 lines. Narrator lines are in italics. Narration and dialogue never share the subtitle band.
  - **Safe zones:** keep important action out of the bottom 22% of the frame and the right 15% (platform UI).
  - **When labels appear:** a person's label appears on their first featured shot, together with the narrator's introduction.
- **Edith gets no label until Shot 5.3, even though she is in frame 1.** This omission is the spine of the film. Do not "fix" it, and make sure no pipeline auto-labels her.

- **TTS:**
  - Every line has two fields: `subtitle_text` (what is burned in) and `tts_text` (what Kokoro reads).
  - Render every line as its own clip. Build an audio-only animatic from the clips first, and block all animation from the measured durations.
  - Parentheticals in this script are acting notes for animators and edit timing. Kokoro has no style control.
  - Strip leading ellipses before synthesis, and build every pause in the edit.
  - `tts_text` uses "Missus" and "Mister". Subtitles keep "Mrs." and "Mr.".
  - Laughs, breaths and sniffs are separate SFX, never text.
  - Render 2–3 speed variants (±0.05) of every line under four words and pick by ear.
  - Special cases:

    | Line (shot) | `tts_text` to render | Edit |
    |---|---|---|
    | TOMAS "It's..." (3.2) | "It's Margaret, I think." | Cut right after "It's" so the mid-sentence pitch survives |
    | EDITH "Edith." (3.18) | "My name's Edith." at speed 0.82 | Trim to "Edith." |
    | EDITH "Please." (3.18) | "Please. If you would." at 0.82 | Trim to "Please." |
    | OSWALD "Edith." (3.19) | "It's Edith." | Trim to "Edith." |
    | OSWALD "No." (3.13) | "No. Not at all." | Trim to "No." |
    | TOMAS "Good." (5.1) | "Good. Leave it open." | Trim to "Good." |
    | TOMAS "Door!" / TEDDY "Again!" (2.4) | "Door! Now." / "Again! Do it again!" | Trim to the first word |
    | OSWALD "...so—" (3.15) | "Well. He calls me Oscar, so there's that." | Cut on "so" |
    | EDITH "Oh — I'm fine..." (3.7) | "Oh, I'm fine, thank you. The wall's warm. From the ovens." | None |
    | EDITH "It's Edith." (5.2) | as written, at 0.92 | A different waveform from 3.18 |

  - **Hushed lines** are Edith's "That was Walter's." (3.8), Oswald's "Thirty-one Sundays." (3.12) and Edith's "Nobody's said it since April." (3.20). Treat each one this way:
    - render at speed −0.05
    - lower it 8 dB
    - apply a −4 dB high shelf above 6 kHz
    - add a breath SFX 150 ms before the line
    - mix close and dry
  - **Shot 4.2:** a short laugh SFX, then the clean line "There's the lean.", then a bright laugh tail.

- **Face rig.** The controls in rigctl.FACE_DEFAULT are jaw, wide, round, press, pout, lip_raise, smile, smirk, brow, brow_in, brow_asym, lids, blink, sneer and one gaze control shared by both eyes. Every face note in this script maps onto them:
  - The "grief brow" is brow_in up with brow slightly down.
  - A swallow is a 4-frame press with a small head dip.
  - The chin tremble in 3.20 is a 3-frame alternating press/pout flutter with jaw ±0.03. Test it on that shot before committing. A chin shape key is the upgrade if it doesn't read.
  - There are no crossed eyes, tongue, dimple or throat beats.
  - The tear is a droplet mesh with a wet shader, not a rig control.

- **Camera grammar:**
  - Scenes 1–2 are shot at standing eye height (about 1.6 m) or higher, locked-off or with slow mechanical moves.
  - Shot 3.6 is the first time the camera drops to Edith's seated eye level (0.8 m). Lenses get longer and focus gets shallower.
  - 4.1 and 4.3 go back up to standing height. 4.2 stays at her level: from here on she is someone the film looks at straight.
  - 5.2 is at her level, where everyone now is.
  - 5.3 returns to the exact camera of 1.1.
- **Scene 3 setups.** Shot count is not render cost: the scene reuses these setups.
  - **Doorway deep staging** (3.1, 3.4).
  - **Tomas MCU** (3.2).
  - **A: low profile two-shot** from the street side, used only for the approach.
  - **B: the diagonal.** The camera is at 0.8 m, just off Edith's left shoulder and slightly behind her shoulder line, on a long lens. Oswald kneels on the diagonal 0.6 m from her. His head stacks above hers, at about 25–40% and 45–55% down the frame. The window glow sits between and behind them, and her cap and cheek are in soft profile in the foreground.
  - **C:** over Oswald's shoulder, favoring Edith, with the dark wall defocused behind her.
  - **D:** close-up of Edith.
  - **E:** close-up of Oswald.
  - **Dial cutaway:** reuses the 1.2 camera.

- **Light arc:**
  - The bakery's warm pool on the pavement (window and door, carried by one keyframed area light) always ends a hand's width short of Edith's shoes.
  - It dims a notch when the door shuts in 1.4 and 3.4.
  - In 5.2 it spreads along the pavement and reaches her for the first time.
- **Color:** The mustard coat is the most saturated object in the film. It starts on Oswald and ends on her. Teddy's red hat is second. There are no fine patterns anywhere.
- **Clock:** The dial always reads 31 minutes behind real time. It reads 3:29 in 1.1, goes from 3:29 to 3:30 in 1.2, reads 4:27 in 3.11 and 4:29 in 4.3. No gag depends on dial arithmetic.
- **Tower tick:** A heavy tick about once per second, audible whenever the music is out.
- **Render economy:**
  - Use cloth sim only for the coat drape. A cut on action hides the coat coming off.
  - The lamp bloom and the warm pool are keyframed emission and area lights.
  - The bread tear is a mesh swap.
  - The doorway and dial setups are each rendered once and reused.
- **Edit priority:** If the cut runs long, trim the Scene 1 lead-ins and tails first, then 2.4. Never trim the silences in 3.2–3.5 or 3.18–3.21.

---

### SCENE 1 — "This is Brindle Cross" (0:00–0:38)

**Shot 1.1** — 4.5 s.
- **Camera:** Wide, locked-off, from about 21 m back across the square, about 2.4 m high, about 65 mm, with a slight down-tilt so Edith's eye line sits at about 50% of frame height.
- **Light:** Late afternoon, about 4:00 pm real time. An overcast pewter sky, a low gold sun rimming the tower from behind, the bakery window glowing amber, the lamp unlit, first snow.
- **Action:** FRAME 1 is the thumbnail:
  - **Upper third:** The cheated clock dial: cream, with black Roman numerals and a gilt rim catching the gold light. It reads 3:29.
  - **Middle band:**
    - Gold-leaf "BRANDT & SON · BAKERS" over a big amber window stacked with loaves, with a small hand-lettered card in the glass.
    - **At the window's right end, Teddy's cherry-red bobble hat, his nose pressed to the glass, watching the square for the clown.** This is the bold focal point.
    - The door at the window's left end stands ajar and throws a warm wedge onto the snow-dusted pavement.
  - **Lamppost:** The black iron lamppost stands at the curb in front of the window's right end, silhouetted against the amber glass. Bare cobbles lie on its left: the empty patch.
  - **Hidden in plain sight:**
    - Right of the window, low against the brick, is a small round figure in brick-brown and rust, knees up, her face in the wall's shadow. This is Edith, at about 70% of frame width, clear of the right-edge UI.
    - The warm pool stops a hand's width short of her shoes.
    - The red hat a metre away takes the eye.
  - **Caption:** In the label slot, to her left and never on her: "BRINDLE CROSS", with "*A Sunday in November*" in italics below.
  - **Snow:** It hangs mid-air on frame 1 and starts falling on frame 2.
  - **Movement:** From about frame 12, the plum-coat woman crosses left to right along the pavement, passing directly in front of Edith without turning her head. Edith's only movements are one slow blink and one fog of breath.
  - **NO LABEL ON EDITH.**
- **Lines:** NARRATOR (V.O.) (dry, unhurried, municipal): "This is Brindle Cross."
- **Sound/Music:** M1 "Civic" starts on frame 1. It is a plain, slightly plodding solo-piano walking theme in C major, like a 1950s information film. Under it: wind, distant footsteps, and the heavy tower tick.

**Shot 1.2** — 7 s.
- **Camera:** Medium on the dial from across the square, with a slow mechanical push-in.
- **Light:** Gold rim light on the stone.
- **Action:**
  - The dial reads 3:29. In the pause between the two lines, the minute hand clunks to 3:30. Nothing else moves.
  - Label: "THE CLOCK — *Tower, 1871*".
- **Lines:**
  - NARRATOR (V.O.) (matter-of-fact): "The clock runs slow. Thirty-one minutes, at last count."
  - NARRATOR (V.O.) (mild, uninterested): "Nobody's quite sure when that started."
- **Sound/Music:** M1 continues. A heavy mechanical clunk. Tick.

**Shot 1.3** — 8 s.
- **Camera:** Medium, slow lateral truck from left to right along the bakery window at standing height.
- **Light:** Warm interior, cool exterior, faint reflections of the square on the glass.
- **Action:**
  - We glide past shelves of large rye and small seeded rye to the card: "KINDLY PAY BEFORE EATING". Rack focus to it and hold 1 s.
  - Rack through the glass to Tomas, sliding out a tray of small rye. Label: "TOMAS BRANDT — *Baker*".
  - His lids are heavy and his mouth is pressed in concentration. His brows lower at the draught, and he shoots a short, irritated glance at the open door, frame left.
- **Lines:**
  - NARRATOR (V.O.): "Somebody kept eating the rye before he'd paid."
  - NARRATOR (V.O.) (a dry quarter-beat): "Hence, the sign."
  - NARRATOR (V.O.): "This is Tomas Brandt."
- **Sound/Music:** M1. A muffled oven hum and a tray clatter through the glass.

**Shot 1.4** — 8 s.
- **Camera:** Medium close-up on Teddy in the doorway, standing height, angled along the shopfront. The window glow and, beyond it, a small dark shape low against the brick are soft in the background.
- **Action:**
  - Teddy leans in the doorway, one hand on the frame, rocking heel to toe. His mouth is open and his eyes are bright as he scans the square for the clown. Label: "TEDDY BRANDT — *Age 8*".
  - On "eight", his brows pull down, affronted, and his eyes slide sideways to the label.
  - The descriptor types on "*(nearly 9)*". He nods hard, satisfied, as if the record had obeyed him.
  - On Tomas's line he does a huge eye-roll with his whole head, his shoulders slump, and he steps inside. The door swings shut and the bell jingles.
  - **The warm pool dims a notch.**
- **Lines:**
  - NARRATOR (V.O.): "This is his son, Teddy. He is eight."
  - TOMAS (O.S.) (gruff, not unkind, said a thousand times before): "Teddy. Door. You're letting the heat out."
- **Sound/Music:** M1. A soft typewriter tick on the label correction. A two-tone brass shop bell and a door thunk.

**Shot 1.5** — 3.5 s.
- **Camera:** Medium on the lamppost, standing height. Its left side, with the bare empty patch, is in clear view. Behind it, soft, Edith sits against the brick in the wall's shadow.
- **Light:** Cool overcast light; the lamp is unlit.
- **Action:**
  - Snow settles on the empty patch. Edith does not move. Nothing else happens.
  - Label: "THE LAMP — *Automatic, 1926*". The lamp gets a label; the woman a metre behind it does not.
- **Lines:** NARRATOR (V.O.) (flat): "The lamp lights itself at five."
- **Sound/Music:** M1 and wind.

**Shot 1.6** — 7 s.
- **Camera:** Wide, standing height, locked-off, from the square. The lamppost is at center, Edith small against the wall to its right, the pavement and door on the left.
- **Light:** The light is starting to cool.
- **Action:**
  - Oswald enters from frame left with a waddle and a cane twirl. Label: "OSWALD BUNCE — *Entertainer*".
  - He tips his bowler to the flat-cap man, who nods back politely.
  - **Then, with exactly the same courtesy, he tips it to the empty cobbles on the left of the lamppost.** His eyes stay level, at a standing man's head height. The flat-cap man glances at the empty spot, puzzled, and walks on.
  - Oswald drops the bowler upside down at his feet with a flourish.
  - On "silent act" he turns to his public with a big closed-mouth grin, puts a finger to his lips and gives a solemn little shake of the head: no talking.
- **Lines:**
  - NARRATOR (V.O.): "And this is Oswald Bunce."
  - NARRATOR (V.O.): "It's a silent act."
- **Sound/Music:** M1 finishes its phrase. A tinny, slightly out-of-tune honky-tonk upright plinks a two-note pickup.

---

### SCENE 2 — "The Act" (0:38–0:58)

**Shot 2.1** — 6 s.
- **Camera:** Standing height, locked-off, shot from behind the three extras.
  - Their desaturated head-and-shoulder silhouettes line the lower third, at about 60–80% of frame height.
  - Oswald and the tall lamppost fill the middle.
  - In the background: the amber window with Teddy's red hat at the glass, and Edith small against the brick to the right of the post.
- **Light:** Late afternoon.
- **Action:**
  - Oswald pulls three small wooden balls from his coat pockets and juggles, smooth and show-offy, with his lips pressed into a smug smirk.
  - He walks forward toward the lamp, still juggling, glancing back over his shoulder at the crowd, and hits the lamppost face-first: CLONG.
  - The balls drop and bounce away to the right of the post, never onto the empty patch.
  - He staggers in a small circle propped on the cane, head wobbling, blinking rapidly. Then he recovers and bows to the crowd, scooping the balls back into his pockets on the way down.
  - The silhouettes bounce with laughter: the plum-coat woman's glove at her mouth, the flat-cap man slapping his knee, the newspaper gentleman's shoulders shaking. Teddy's giggle fogs the glass.
  - Behind the post, Edith gives one startled blink at the CLONG and does not look up.
- **Lines:** None.
- **Sound/Music:** M2 "Rag" kicks in at full energy on the honky-tonk upright. A hollow, ringing iron CLONG, wooden clacks as the balls land, and laughter SFX.

**Shot 2.2** — 3.5 s.
- **Camera:** Starts at cobble height with a banana peel sharp in the foreground, then tilts up to Oswald.
- **Action:**
  - The huge oxblood boots stride in and stop an inch short of the peel. His brows shoot up and his mouth makes an "O".
  - He points at the peel and wags a finger at the audience, lips pursed smugly: *not today*.
  - He waddles around it in an exaggerated, slow arc, and makes it.
- **Lines:** None.
- **Sound/Music:** The rag drops to a pizzicato tiptoe, then a triumphant cymbal tap.

**Shot 2.3** — 4.5 s.
- **Camera:** Medium full, locked-off, standing height.
- **Action:**
  - He turns to the crowd with his arms wide for applause. **This is the lean:** his shoulders dip forward and he rises onto his toes, a clear and readable tilt held for 16 frames.
  - His next step lands on a second peel. Feet up, backside down. He lands sitting directly behind his own upturned bowler.
  - One beat. He looks at the hat, then at the crowd, and gestures to it grandly, as if the fall had simply been the route to the collection point.
- **Lines:** None.
- **Sound/Music:** A slide whistle down, a THUMP, one beat of stop-time silence, then a woodblock "tok" on the gesture. A big laugh.

**Shot 2.4** — 6.5 s.
- **Camera:** Medium, standing height, looking down slightly at the seated Oswald, with the bakery door in the background left.
- **Light:** The first hint of dusk.
- **Action:**
  - Coins plink into the bowler from all three extras, and he beams at each one with a little bow of the head.
  - Teddy shoves the door open a crack to shout. Tomas's floury arm reaches past him and pulls it shut.
  - **The greed beat:**
    - Oswald tips the coins into his palm and counts them with a gloating head-bob, then rubs his hands together.
    - He claps the bowler back on and looks straight past the lamp to the loaves in the window, lips smacking.
    - He never looks at the wall.
  - The extras drift off in three directions. None of them look at the wall either.
  - In the background, Edith has not looked up once. A thin, unbroken line of snow has settled along her shoulders and cap.
- **Lines:**
  - TEDDY (delighted, through the gap): "Again!"
  - TOMAS (O.S.): "Door!"
  - NARRATOR (V.O.) (deadpan): "He has never once seen the second banana."
- **Sound/Music:** Rag, coin plinks, a door thunk, and laughter tailing off. Across the cut, the rag slows into a lazy two-chord vamp.

---

### SCENE 3 — "The Small Rye" (0:58–2:53)

**Shot 3.1** — 6.5 s.
- **Camera:** Doorway deep staging at standing height. The camera stands on the pavement between the door and Edith, looking back along the shopfront toward the door, on a long lens. Oswald walks toward camera in the foreground; the doorway is in the background.
- **Light:** Dusk is creeping in. The window is now the brightest thing in the square.
- **Action:**
  - The bell rings. Oswald backs out of the door with a small seeded rye in brown paper, his cane hooked over his arm.
  - He waddles toward camera, back toward his pitch by the lamp, peeling back the paper. He raises the loaf, and his jaw opens wide for a big, greedy bite.
  - Behind him, Teddy pops into the doorway and watches him go, head tilting. Tomas comes up behind Teddy, wiping his hands on the striped towel.
  - On "Walter's wife", Oswald's waddle slows half a step.
  - **On "first name" he freezes mid-bite**, his teeth on the crust, his eyes sliding sideways toward the voices behind him.
- **Lines:**
  - TEDDY (calling up over his shoulder, curious): "Papa, who's that lady?"
  - TOMAS (distracted, still wiping): "Mrs. Lusk. Walter's wife."
  - TEDDY (looking straight up at him): "What's her first name?"
- **Sound/Music:** The lazy vamp keeps bouncing under the whole exchange. The shop bell.

**Shot 3.2** — 2.5 s.
- **Camera:** Medium close-up on Tomas, at standing eye level, with the warm doorway behind him.
- **Action:**
  - Tomas is confident for one syllable, then finds nothing. The towel stops.
  - His eyes go out past Oswald to the wall, and for the first time he actually looks at her: upper lids lift, brows draw up and together, a slow blink. Hold.
- **Lines:** TOMAS (starting confidently, then stalling): "It's..."
- **Sound/Music:** **The rag stops dead, mid-bar, on "It's".** The chord is left unresolved. His memory and the music fail on the same syllable. Then silence: wind and the tower tick.

**Shot 3.3** — 2 s.
- **Camera:** Close-up on Edith from standing height, looking down at her, still above her eye line. The line of snow is on her cap and shoulders.
- **Action:** She doesn't turn her head. Her eyes, on the cobbles, go still. One slow blink. **She heard.**
- **Lines:** None.
- **Sound/Music:** Tick.

**Shot 3.4** — 3 s.
- **Camera:** The 3.1 doorway deep staging.
- **Action:**
  - **Background:**
    - Tomas looks away, embarrassed. He puts a big floury hand on Teddy's shoulder and turns him inside.
    - He says the line without looking at the boy, already turning away. It must not land as a gag.
    - The door closes. **The warm pool dims a notch.**
  - **Foreground:** Oswald is still frozen with the crust in his teeth. Slowly he lowers the loaf, unbitten, and folds the paper back over the end.
- **Lines:** TOMAS (quiet, flat, already turning away): "Door, Teddy."
- **Sound/Music:** The bell, small and muffled behind the closed door. Tick.

**Shot 3.5** — 4 s.
- **Camera:** Wide, side angle, standing height.
- **Light:** The square is in blue silence.
- **Action:**
  - Oswald stands a moment with his back to the bakery.
  - Then his body changes. The toes-out clown splay closes and his feet come together. His shoulders drop. The cane goes under his arm, and the loaf goes into both hands.
  - He walks the last two metres with an ordinary walk: no waddle, no bounce. A man, not a clown.
  - This is the most important body-language note in the film.
- **Lines:** None.
- **Sound/Music:** Ordinary footsteps on stone, wind, and the tick.

**Shot 3.6** — 3.5 s.
- **Camera:** Setup A, a low profile two-shot from the street side. **The camera is at 0.8 m, Edith's seated eye level, for the first time in the film.**
- **Light:** Window light warm from frame left, with cool sky fill.
- **Action:**
  - He stops a respectful metre away and takes a breath: his shoulders rise and fall and his breath fogs.
  - He lays the cane on the pavement and kneels on one knee.
  - He shuffles in on the knee until he is about 0.6 m from her, on the diagonal, and holds the wrapped loaf out on a flat, open palm.
- **Lines:** None.
- **Sound/Music:** Silence. A soft knee-on-stone sound, a cane click, the oven's low hum through the brick, and the tick.

**Shot 3.7** — 5.5 s.
- **Camera:** Setup C, over Oswald's shoulder, favoring Edith, at eye level with shallow focus. The wall behind her is dark and soft, and a cool rim separates her from it.
- **Action:**
  - Edith's eyes lift slowly from the cobbles to the loaf to his face. Her lids widen slightly: he has come down to her level.
  - Then the social mask snaps on: her chin tucks, she gives a small polite closed-lip smile, and her brows go up in a "how kind, no thank you" way. She pats the brick behind her as evidence.
- **Lines:** EDITH (polite, automatic, a little too quick): "Oh — I'm fine, thank you. The wall's warm. From the ovens."
- **Sound/Music:** Silence and room tone.

**Shot 3.8** — 11 s.
- **Camera:** Setup C.
- **Action:**
  - Oswald doesn't argue and doesn't withdraw the bread. He folds back a corner of the paper.
  - **These are the first words he has spoken in the film.**
  - Edith's eyes drop to the loaf and she goes still. Her inner brows lift (the grief brow) and her lips part.
  - While he talks about Walter, her eyes come up to his face, searching: *he knew that?* She gives a tiny shake of the head in fond disbelief.
  - On "before he'd paid" he tilts his head toward the card in the window, and her eyes follow it. A breath of a laugh escapes through her nose, and one corner of her mouth lifts.
  - She takes the loaf in both hands and holds it in her lap like something warm.
- **Lines:**
  - OSWALD (soft; his voice smaller than his body): "It's the small rye."
  - EDITH (hushed): "...That was Walter's."
  - OSWALD (half-smile, remembering): "Every day at four. He'd tear the end off before he'd paid."
  - EDITH (the first thaw, amused): "That sign was for him."
- **Sound/Music:** Silence with room tone only. A paper rustle, and a tiny nasal laugh as a separate SFX.

**Shot 3.9** — 10.5 s.
- **Camera:** Setup B, the diagonal.
- **Action:**
  - Oswald's eyes slide, fond, to the empty patch on the far side of the lamp, and he nods toward it.
  - In the foreground, her cap tilts, teasing.
  - **On her first line he freezes and blinks twice, caught.** Then a sheepish grin, a dip of the head, brows up. He concedes without a word.
  - On her last line the grin softens into something else. He looks down, blinks slowly, and breathes out through his nose. His eyes go back to the lamp. A tiny lip press and head dip: a swallow.
- **Lines:**
  - OSWALD (fond): "He stood by the lamp. Laughed before I even fell."
  - EDITH (dry, almost teasing): "He said you lean. Right before."
  - EDITH (warmer, simple): "He loved that you never fixed it."
- **Sound/Music:** Silence and the tick.

**Shot 3.10** — 2.5 s.
- **Camera:** Setup B.
- **Action:**
  - Edith's smile fades.
  - She tips her head back against the brick, eyes up, toward the tower behind the roofs. She can't see it from here and doesn't need to.
  - Oswald's eyes lift to follow.
- **Lines:** EDITH (flat; a fact): "Thirty-one minutes."
- **Sound/Music:** Tick.

**Shot 3.11** — 5.5 s.
- **Camera:** The 1.2 dial camera, from across the square.
- **Light:** Deep dusk. The dial glows faintly with the last of the sky light on its rim, above the roofline and the bakery chimney's smoke.
- **Action:** The dial reads 4:27. Nothing moves but the snow.
- **Lines:**
  - EDITH (O.S.) (matter-of-fact; said to herself many times): "Walter climbed up every Sunday. Set it right."
  - EDITH (O.S.): "It loses a minute a week."
- **Sound/Music:** The tick is loud in the silence. A single low cello note enters underneath, almost subliminal.

**Shot 3.12** — 3 s.
- **Camera:** Setup E, close-up on Oswald at eye level.
- **Light:** Window light on one cheek, blue sky light on the other.
- **Action:** His eyes make tiny flicks as he counts. His brows rise, then fall, and his lips part. He lowers his gaze to her.
- **Lines:** OSWALD (hushed): "...Thirty-one Sundays."
- **Sound/Music:** The cello note holds. Tick.

**Shot 3.13** — 5 s.
- **Camera:** Setup C.
- **Action:**
  - Edith nods once with her lips pressed thin. She says the confession to the loaf in her lap.
  - Then her eyes slide up and sideways to test him, almost defiant.
  - Oswald answers at once, with a small headshake and no smile.
  - She holds his gaze a second longer, and her shoulders drop half an inch.
- **Lines:**
  - EDITH (eyes on the loaf; a confession): "I don't want it fixed."
  - EDITH (eyes up on him): "Isn't that awful?"
  - OSWALD (simply, without hesitation): "No."
- **Sound/Music:** The cello fades to nothing. Tick.

**Shot 3.14** — 5.5 s.
- **Camera:** Setup D, close-up on Edith, three-quarter view.
- **Light:** Amber key, cool fill, and a cool rim off the dark wall.
- **Action:**
  - She looks out at the empty square.
  - She puts on a wry half-smile with one brow lifted, as armor.
  - On "Both times" she gives a tiny shrug, like a weather report.
  - Her eyes stay on the empty square a beat too long.
- **Lines:**
  - EDITH (light, deflecting): "The minister came twice."
  - EDITH (dry): "Called me Ethel. Both times."
- **Sound/Music:** Wind.

**Shot 3.15** — 11 s.
- **Camera:** Setup E (close-up on Oswald), then setup C.
- **Action:**
  - **Close-up, the performer's reflex:** his brows pop up, a grin loads, and two fingers rise toward his hat brim for a tip.
  - Edith cuts him off gently. His fingers stop on the brim, then his hand comes down slowly to his knee.
  - The grin drains away. His eyes drop to the cobbles, with a small lip press and head dip. Then they come back up, steady, with no performance left in them.
  - **Cut to C on his last line:** Edith's face softens. Her lids lower, she exhales a little, and the corners of her mouth forgive him.
- **Lines:**
  - OSWALD (reaching for funny): "Well. He calls me Oscar, so—"
  - EDITH (O.S.) (gently, almost amused): "Oh... you don't have to do that."
  - OSWALD (quiet, honest): "I saw you. Every day."
  - OSWALD: "I didn't know what to say."
  - EDITH (gently, letting him off): "Nobody does."
- **Sound/Music:** Silence. Cut his clip on "so" and overlap her "Oh..." by two frames.

**Shot 3.16** — 5 s.
- **Camera:** Setup B.
- **Action:**
  - Oswald notices the snow on her shoulders and brushes it off with two light strokes. She watches his hand, surprised to be touched.
  - He takes hold of his own lapels with both hands. Edith's brows shoot up and the schoolteacher comes out.
  - He ignores her and gives one two-handed tug. The middle button pings off and he rocks back on his heel.
  - Edith lets out a startled huff of a laugh.
- **Lines:** EDITH (firm, the schoolteacher): "Mr. Bunce. No."
- **Sound/Music:** Wool strain, a button ping, and Edith's huff-laugh SFX.

**Shot 3.17** — 6 s.
- **Camera:** Setup B, **cut on action**. The coat is already off and in his hands.
- **Action:**
  - He swings the mustard coat around her shoulders. It is absurdly bright on her.
  - **As it lands she goes still, eyes on his hands at her collar.**
  - He tucks the collar up under her chin with both hands, the way you'd dress a child. She lowers her chin into the wool.
  - He sits back on his heel in shirtsleeves and green waistcoat, suddenly half his size, and gives a small, pleased eyebrow flourish.
  - On "ridiculous" she gives a one-bounce laugh with her eyes closed.
  - Soft through the window behind them: Teddy's face at the glass, and above it Tomas, his towel stopped.
- **Lines:** OSWALD (dry, pleased with himself): "There. Now we both look ridiculous, Mrs. Lusk."
- **Sound/Music:** Cloth rustle, Edith's one-bounce laugh SFX, and the tick.

**Shot 3.18** — 4.5 s.
- **Camera:** Setup D, close-up on Edith. Her eyes sit at about 35% of frame height and her mouth at about 45%.
- **Action:**
  - Her laugh settles. She looks at his face, and something more exposed shows.
  - After her name, her eyes drop, embarrassed to ask for something so small.
  - Hold a full beat of silence between the two words.
  - She heard the baker fail. This is her answer to the question the town couldn't.
- **Lines:**
  - EDITH (soft): "Edith."
  - EDITH (eyes down, after a full beat): "...Please."
- **Sound/Music:** Silence and the tick.

**Shot 3.19** — 2.5 s.
- **Camera:** Setup E, close-up on Oswald.
- **Action:** He takes it in. The performer is gone. He gives a small, serious nod and says her name carefully, as if setting down something fragile.
- **Lines:** OSWALD (carefully): "Edith."
- **Sound/Music:** No music. The tick.

**Shot 3.20** — 6.5 s.
- **Camera:** Setup D, in the same framing as 3.18, so the tear's whole path stays above the subtitle band. A slow, imperceptible push-in.
- **Light:** Amber window key and blue dusk.
- **Action:**
  - **No label.**
  - Her eyes close. Her chin trembles once, and she presses her lips together to stop it.
  - **A single tear wells in her left eye, catches the bakery's amber light, and runs to the corner of her mouth. She does not wipe it.** This is the only tear in the film.
- **Lines:** EDITH (eyes closed, hushed): "Nobody's said it since April."
- **Sound/Music:** No music: only wind and the tick.

**Shot 3.21** — 9 s.
- **Camera:** Setup B.
- **Action:**
  - Oswald lays his hand on her shoulder, on his own coat, and says nothing. Long beat.
  - She lifts her gloved hand and pats his hand twice. She opens her eyes, sniffs once and sits up straighter: the brisk schoolteacher is back.
  - She folds back the paper, tears the end off the small rye the way Walter did, and holds it out to him.
  - He shows both palms and shakes his head. She doesn't lower her arm, and gives him a level stare over it.
  - **At his own first name he goes still:** inner brows lift, and one slow blink of 8 frames at most. Nobody gets his name right.
  - Then he takes the bread. They sit side by side, looking out at the square, each holding a piece.
- **Lines:**
  - OSWALD (palms up): "That's yours."
  - EDITH (level, soft, certain): "You eat too, Oswald."
- **Sound/Music:**
  - **M3 "Edith" enters the instant his hand lands on her shoulder.** It is four plain, unhurried notes on solo piano.
  - A low string pad slips in under it on her two pats. The music scores the care, not the grief.
  - A close crust-crack foley on the tear.
- **Production notes:**
  - Swap the whole-loaf mesh for loaf-plus-end on the frame her hands cover the break.
  - Hide any bites behind the bread, or skip them. The beat still plays.

---

### SCENE 4 — "Encore" (2:53–3:05)

**Shot 4.1** — 3.5 s.
- **Camera:** Medium wide. **The camera is back at standing height.**
- **Light:** Dusk; the lamp is still dark.
- **Action:**
  - Oswald picks up his cane and stands; his knees crack. He gives one theatrical full-body shiver in his shirtsleeves.
  - He tips his bowler to her. She inclines her head in return, regal in mustard, the bread in her lap.
  - He sets off into the square with the jaunty waddle switched back on, cane twirling, chest puffed out against the cold.
- **Lines:** None.
- **Sound/Music:** A knee-crack SFX. The honky-tonk upright picks up the four-note "Edith" motif, ragged and cheeky.

**Shot 4.2** — 4 s.
- **Camera:** Edith in close-up in the foreground, three-quarter view, at her eye level (up to 1.2 m if needed for the background). Oswald is in the square behind her.
- **Action:**
  - **Focus starts sharp on Edith.** Her eyes narrow slightly as she watches him go.
  - **Rack to Oswald.** He turns back to her and spreads his arms wide: **the lean.** His shoulders dip and he rises onto his toes, held for at least 16 frames. He is placed to read in silhouette against the pale snow or a lit window across the square.
  - Her laugh and line play over him, **before anything has happened.**
  - **Rack back to her** crinkled eyes for the last 20 frames.
- **Lines:** EDITH (laughs first, then under her breath): "There's the lean."
- **Sound/Music:** A short laugh SFX, the clean line, then a bright laugh tail. The rag building.

**Shot 4.3** — 4.5 s.
- **Camera:** Wide, standing height, from the square. The lamppost is at center, with the cheated dial above the roofline behind it and Edith in mustard to the right.
- **Action:**
  - He steps toward her for a bow and his boot catches a cobble. He almost trips, arms windmilling, lurches into the lamppost and catches it with one arm.
  - **At that exact instant, five o'clock real time, the lamp blooms on above him.** The dial behind it reads 4:29.
  - He freezes. He looks up at the lamp, then at his own arm, and lets go very carefully.
  - He turns to Edith and gives a deep, grand bow, as if he had done it on purpose.
- **Lines:** None.
- **Sound/Music:** A soft "fwump" and gas hiss with a celesta "ting". The rag crashes back in, full and bright.

---

### SCENE 5 — "This is Edith Lusk" (3:05–3:28)

**Shot 5.1** — 4 s.
- **Camera:** Medium on the bakery doorway, standing height.
- **Light:** Blue hour, the lamp lit, the snow a little heavier.
- **Action:**
  - The bell rings. Tomas steps into the doorway and looks off toward Edith.
  - He pushes the door wide with a flat palm, and it stays open.
  - Teddy, at his elbow, gapes up at him: this is the man who says "Door".
  - Tomas doesn't look at him. He tips his head toward Edith, and Teddy runs.
- **Lines:**
  - TEDDY (scandalized): "Papa! You're letting the heat out."
  - TOMAS (gruff, not looking at anyone): "Good."
- **Sound/Music:** The bell. The rag softens.

**Shot 5.2** — 8.5 s.
- **Camera:** Low two-shot from the street side at Edith's seated eye level (0.8 m).
- **Action:**
  - **The warm light from the open door spreads along the pavement and, for the first time, reaches Edith.** It climbs over her shoes and her knees and up the mustard coat, which glows.
  - Teddy runs in and plops down beside her against the wall. He copies her posture exactly: knees up, hands in his lap.
  - He looks up at her, direct, and she turns her head to him.
  - On his age he nods, businesslike.
  - Edith holds a perfectly straight face for a beat, then the corners of her mouth go. Teddy beams.
- **Lines:**
  - TEDDY (direct, the way children are): "What's your first name?"
  - EDITH (simply): "It's Edith."
  - TEDDY (businesslike): "I'm Teddy. I'm nearly nine."
  - EDITH (perfectly straight face): "Congratulations."
- **Sound/Music:** The rag resolves into the M1 "Civic" theme, played slower, with the four-note "Edith" motif folded into it.

**Shot 5.3** — 10.5 s, including the last 1.5 s on black.
- **Camera:** **The exact camera position and lens of Shot 1.1,** re-rendered in the present state. Then a slow ease-in push of about 15% settles with Edith's eye line at about 50% of frame height, clear of the right-edge UI.
- **Light:** Blue hour.
- **Action:**
  - It is the thumbnail frame again, changed:
    - The door is open and the warm light covers her.
    - The mustard coat is the brightest thing in the square.
    - Teddy sits beside her, copying her.
    - Under the lit lamp, Oswald in shirtsleeves does a slow cane twirl for an audience of two.
    - The empty patch is still bare.
  - The camera eases toward her and stops.
  - In the label slot where "BRINDLE CROSS" first appeared, "EDITH LUSK" fades in and holds. It uses the same font, size and position as every other label, with no descriptor.
  - Cut to black on the tail of the last word.
  - On black: "BRINDLE CROSS" with "*A Sunday in November*", in exactly frame 1's type and position, so the loop back to frame 1 is seamless.
- **Lines:**
  - NARRATOR (V.O.) (the same dry voice, a fraction slower): "This is Edith Lusk."
  - NARRATOR (V.O.): "She has lived here fifty-three years."
  - NARRATOR (V.O.) (after a 0.8 s pause, no emphasis at all): "She was in the first shot."
- **Sound/Music:** The slowed "Civic" theme continues under the narration. A final warm piano chord sounds under "first shot". On black it decays into wind and one last tower tick.

## Why it lands

- **The film forgets her on purpose, so the viewer does too.**
  - Edith is in frame 1, a metre from a bright red hat, dressed and shadowed like the wall.
  - The narrator labels a clock, a baker and a boy, and lets the boy correct his own age. He labels a lamp with her sitting right behind it.
  - Her label comes only at the very end, in the same type as everyone else's.
  - His last line is a plain fact the viewer can check, not a moral: "She was in the first shot." The feed loops straight back to frame 1. On the second pass the viewer finally sees her, and sees the clown tip his hat to empty cobbles a few steps from a woman he never greets.
- **The uppercut comes from a question, not a music swell.**
  - The clown buys bread for himself and is about to take a big, greedy bite, a pure comedy reward.
  - A child asks the most ordinary question in the world, "What's her first name?" The rag plays straight through it and dies on the baker's confident "It's...". The silence is the answer.
  - Edith, three metres away, blinks once. She heard.
  - Before anyone speaks to her, Oswald's body tells us the comedy is over: the clown waddle closes into an ordinary man's walk.
- **Every boring fact in the intro turns out to be about grief.**
  - "Thirty-one minutes... nobody's quite sure when that started" pays off as "Walter climbed up every Sunday... It loses a minute a week". The viewer works out "thirty-one Sundays" a second before Oswald says it, so the feeling is their own.
  - "Somebody kept eating the rye before he'd paid" turns out to be Walter.
  - "It's a silent act" means the clown's first words go to her.
  - "The lamp lights itself at five" becomes his accidental miracle.
  - The three "Door"s become "Good."
- **Edith deflects in a different way every time she speaks, and each time she gives a little more away.** She starts with a fact ("The wall's warm"), then a joke ("That sign was for him"), then a confession that asks for permission ("Isn't that awful?"), then a wry, specific hurt ("Called me Ethel. Both times."), then an order ("Mr. Bunce. No."). Only then does she ask for something: "Edith. ...Please." It is her answer to the question the town just failed. Oswald's answers keep getting shorter: "No." / "Edith." Nobody makes a speech.
- **The joke reflex fails out loud, and honesty replaces it.** "Well. He calls me Oscar, so—" She sees the bit coming and lets him off: "Oh... you don't have to do that." What replaces it is the most real-life line in the film: "I saw you. Every day. I didn't know what to say." Her answer, "Nobody does.", forgives him and everyone who has ever crossed the street to avoid a grieving neighbor.
- **The tear gets no music, and then care runs both ways.**
  - Her name, the tear and "Nobody's said it since April" play over wind and a clock tick.
  - The piano enters only when his hand lands on her shoulder, so the score is about care, not grief.
  - Then she tears the end off Walter's loaf, the way he did, and hands it to the man who was about to eat the whole thing. "You eat too, Oswald." She gets his name right where the minister didn't, and his only reaction is to go still. Nobody says thank you.
- **The comedy comes back as proof that she is coming back.**
  - She laughs before he falls ("There's the lean"), which takes Walter's place by the lamp. The lamp lights itself as he grabs it. The baker lets the heat out. The boy asks her name himself and gets "Congratulations" for being nearly nine.
  - The clock stays thirty-one minutes slow. The film does not fix her grief.
  - It ends on the narrator's admission, so the last person caught not looking is the viewer.
