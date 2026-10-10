# DIRECTION — "TIREDNESS" (shot by shot)

Read SPEC.md first. Real timings are in `out/timeline.json` (cue names below are
the script's pause cues and line ids). Scene durations listed are current;
each scene may grow by its **allowance** using `engine/scriptedit.update_scene`
(pause beats only) if the action truly needs it — the film must stay under 4:50.

## Acting principles (all scenes)
* **Subtle beats out big.** A take is earned by stillness first. Favour:
  * eyes moving BEFORE the head (pupils slide, 0.15 s later the head follows);
  * slow blinks on judgement beats (close over 0.3–0.5 s, hold, open);
  * one brow lifting slightly;
  * a 0.1 lid drop of disbelief;
  * lip presses and swallowed words;
  * pupils shrinking on fear and widening on wonder;
  * a held breath (shoulders rise and freeze).
  Big takes (the lightning freeze, the ceiling leap, the scream) are rare and
  land BECAUSE everything around them is quiet.
* **Never freeze a face** unless the freeze is the joke (Impulsivity; the
  lightning freeze). Rigs blink automatically. Add tiny idle drift.
* **Eyes always look at something:** the thing being judged, the speaker, the object
  in question, the viewer (rarely, for a punchline).
* Expression transitions: 0.15–0.35 s with ease (core.state_at); hold
  reactions ≥ 0.5 s; anticipate the big moves (squash before a leap).
* **Tiredness's lids** rest at about 45% closed. They lift only for:
  * small surprises (+10–15%);
  * determination in s10 (+25%);
  * the powers moments in s11 and s12;
  * the shaft reveal in s13 (fully open — the biggest single facial move in the film).
  Protect that payoff: when he screams in s07 his eyes squeeze SHUT.
* **Embarrassment** is a nervous system with legs: tiny frequent eye darts,
  blush rising and falling with every lie (0.2 at ease → 0.6 lying → 1.0
  caught), sweat beads, glasses glints, fidgeting hands. His fake-cool face
  is a stiff smile with frantic eyes.
* **The Boss** barely moves. Her biggest move is a 2 px lid narrowing, or her
  eyes sliding to one side and back. Stillness = menace.
* **Impulsivity** is frozen: grin, tongue, wall-eyed, panting. It never blinks.
  That stillness is the joke until s07.
* Staging for phones: one idea per shot, big readable silhouettes, faces large
  (medium shots s≈1.3–1.8; close-ups s≈2.4–3). Keep faces in y 160..1300.

## Transitions
Hard cuts by default, with a whip pan where noted. s11 ends on **black**
(0.8 s) and s12 opens with an **eyelid-opening wipe** out of that black. No other
black frames anywhere, and frame 0 of s01 is bright.

---------------------------------------------------------------------------
## s01 — bedroom (≈18.6 s, allowance +2 s) — music "chill"
**Opening frame:** bright afternoon. A warm sun patch on the wall, the monitor
glow, the cosy messy room. Tiredness sits at his gaming desk, angled 3/4 toward
the camera (turn ≈ +0.4, facing screen-right toward the monitor), so we see
his face and part of the game screen. The window behind him on the left shows the
sunny street. Name tag **TIREDNESS** — *"just wants to play his game"* pops
in at ~0.3 s, upper-left, out by ~3 s.
* **gaming:** game pose, thumbs mashing. Bored-content face, monitor light on
  his face, a tiny lean into a jump in the game. game_blips SFX.
* **commotion + s01_l01** (muffled yelling outside): a crash SFX (trash cans), then the muffled line.
  * His pupils slide toward the window. The head does NOT turn. Hold 0.4 s.
  * The pupils slide back to the screen.
* **eyeroll / s01_l02 "Ugh.":** a slow eye roll (up and around, lids lowering),
  then a sigh: shoulders rise and fall, sigh SFX.
* **headphones:** he lifts the headphones from his neck onto his ears (headphones_on
  pose, headphones 0→1). anc_on SFX; a tiny "ANC" glow on the ear cup.
* **bliss:** lids lower further, the faintest content smile, a gentle head-bob.
* **shake:** the room shakes 0.5 s (house_rumble). Posters tilt, a figurine
  wobbles, dust sifts from the ceiling light. His lids lift +15% and his pupils
  shrink. Subtle — he is annoyed, not scared.
* **s01_l03 "What the actual—":** he half-rises, annoyed.
* **thud2:** a bigger thump cuts him off. A picture frame falls (body_thud).
* **window:** cut to an outside view looking IN through his bedroom window. He
  leans to the glass. Eyes scan left, right, left (pupil darts with tiny head
  follows).
* **nothing:** reverse shot: an empty sunny street, one leaf drifting, a bird hopping.
  Back on him: one slow blink.
* **s01_l04 / s01_l05:** back in the room, he flops into the chair (chair_creak),
  mutters to himself and resumes the game, deadpan.

## s02 — outside (≈13.4 s, +1 s) — "panic"
* **peel:** the side of the house. Embarrassment is flattened against the
  siding (there's a dent — he caused the rumble), peels off and staggers.
  Glasses askew, open EMPTY cage in hand, its door swinging. Name tag
  **EMBARRASSMENT** — *"junior lab scientist"*.
* **s02_l01 / l02:** panic face, sweat, blush 0.3.
  * He looks into the empty cage (pupils down). Beat.
  * Then he looks frantically around. run_panic in place.
* **scurry:** a violet blur (the thing, scurry + motion) zips past his feet,
  across the lawn and under the front door gap. Whip pan to the door. Double
  take: his head snaps first, then his body.
* **s02_l03:** he runs to the door. **bang + s02_l04:** bang_door cycle with
  door_bang SFX on each hit.
* **inside:** cut to the bedroom. Tiredness has headphones on, is oblivious and
  bopping slightly. The bangs are faint and muffled (low gain). He scratches his nose.
* **s02_l05:** outside, Emb has his forehead on the door and slides down it: "…He can't hear me."

## s03 — windows (≈14.5 s, +1.5 s) — "panic"
* The front of the house, wide. He runs to window 1 and pushes: locked (s03_l01),
  window 2 (l02, more frantic), window 3 (l03, wailing). Each try is a
  quick push-shove, then a run to the next window.
* **panic:** wring_hands → shake_arms. Blush 0.6, sweat drops flying.
* **rock:** his eyes lock on a rock (pupils widen). He picks it up and looks left,
  then right — guilty, head tucked into his shoulders.
* **s03_l04 "Sorry, sorry, sorry!":** wind-up with his eyes squeezed shut, then the throw.
* **smash:** glass_smash, ≤15 shards. He flinches, hands up, and peeks with one eye.
* **tiptoe + s03_l05** (whisper): exaggerated anxious tiptoe to the window,
  stepping around the glass.
* **climb:** he pulls himself up into the window: legs kicking, coat tails
  flapping, butt in the air (seen from outside).
* **heap:** his legs vanish inside. Thud + a tiny "oof" (body_thud).

## s04 — Impulsivity (≈16.1 s, +2 s) — "sneaky"
* **lift:** inside the living room, low angle. Emb is in a heap under the broken
  window (glass bits) and lifts his head, glasses crooked. Two enormous furry
  paws sit right in front of his face.
* **reveal:** the camera tilts up. Impulsivity is sitting, staring: the dumbest
  grin, tongue out, wall-eyed, panting (dog_pant). Name tag **IMPULSIVITY** —
  *"a tripwire that never goes off"*.
* **s04_l01** (whisper): Emb's eyes widen and his pupils shrink. His blush drains to 0.
* **s04_l02:** cover_eyes.
* **peek:** peek pose, one eye visible between his fingers.
* **derp:** close-up on Impulsivity, frozen, panting, wall-eyed. Hold the comedy.
  (A fly lands on its nose; it does not react.)
* **s04_l03 "Okay. Nobody move.":** Emb slowly rises.
* **tiptoe:** wide shot as he tiptoes past. Gag: ONE of Impulsivity's eyes slowly
  tracks him while the other stays put. Its head does not move.
* **plates / drawer / table:** he lifts the plates on the coffee table
  (plate_clink, tiny), slides a kitchen drawer open, peeks in and closes it, then
  crouches to look under the dining table. Everything is delicate; he disturbs nothing.
* **scratch:** scratch_wood from upstairs. His head snaps up.
* **stairs:** the camera turns to the stairs. A small shadow with a long tail
  slides along the wall at the top.
* **s04_l04 "Upstairs."** (whisper), and he gulps.

## s05 — burst in (≈15.5 s, +2 s) — "sneaky"
* **music:** the bedroom. Tiredness is at the desk, back toward the door (door on
  screen-left), headphones on. Music notes (♪) leak from the cups
  (game_music_leak, quiet), and a light gap shows under the door.
* **crawl:** the hallway. Emb scurries up the stairs on all fours (crawl cycle)
  and sees a tail slip under the bedroom door.
* **burst:** the door bursts open.
* **freeze:** Emb freezes in the doorway as if struck by lightning:
  * a white flash frame, then jagged shock lines around him;
  * blush 1.0, eyes huge, pupils tiny, hair on end;
  * stinger_shock + lightning_zap.
  Hold ≈1 s.
* **notice:** his pupils slide to the headphones. Relief: his lids lower,
  blush 1.0→0.5, shoulders drop.
* **s05_l01** (whisper) "He can't hear me. Perfect."
* **search:**
  * He crouches under the bed (butt up) and lifts the laundry pile.
  * He opens the closet and rummages; a few clothes (≤6) fly out gently.
* **reveal:** the camera pulls back. Tiredness stands RIGHT behind him: arms
  crossed, squinting, headphones now around his neck. The gaming chair behind
  them is empty and still slowly spinning.
* **tap:** two shoulder taps (tap_tap).
* **s05_l02 "AAAH!":** Emb leaps straight up (leap_scared) — squash first.
* **ceiling:** his head bonks the ceiling (ceiling_thud, plaster dust).
  Tiredness's pupils track him up, then down. Only his eyes move.
* **land:** he lands on his butt (sit_floor, body_thud), dazed, with dizzy stars.
* **s05_l03 "Hi."** — flat.
* **footTap:** tap_foot cycle (foot_tap SFX). One brow lifts slightly.

## s06 — sweater (≈24.5 s, +1.5 s) — "awkward"
* **spot:** Emb, still on the floor, glances past Tiredness. The thing sits on the
  desk by the keyboard, grooming. His eyes widen a hair, then he forces a smile.
* **teleport:** smear_zip. Emb is suddenly at the desk (smear lines from the floor
  to the desk), with a sweater draped over the thing. Tiredness's head turns
  to follow, LATE and slowly — that lag is the joke.
* **s06_l01 / l02:**
  * Emb leans on the desk, both hands pressing the sweater lump.
  * Nervous smile, blush 0.5, eyes darting, sweat.
* **rollEyes / rollHand:** Tiredness gives a slow eye roll, then roll_hand ("go on").
* **s06_l03:** Tiredness, deadpan. One brow up a hair. His eyes flick to the sweater
  on "research" and back.
* **s06_l04:** Emb's face flips: nervous_smile → panic ("No— wait") → fake_cool.
* **s06_l05:** frantic-natural. He tries a casual lean and gestures with one hand
  while the other keeps the lump down; blush 0.7.
* **shift / jerk:**
  * The lump shifts (wiggle).
  * His arms jerk unnaturally to hold it (arm_jerk): eyes wide, grin frozen.
    cloth_rustle.
  * **Tiredness's pupils slide down to the sweater, hold, then slide back up to
    Emb's face. His head never moves.** This is the hardest-hitting subtle
    beat of the scene.
* **s06_l06:** Emb breaks: pleading face, blush 0.85, one hand still on the lump.
* **stare:** Tiredness: a long look, then one very slow blink (close 0.4 s, hold
  0.2 s, open 0.4 s) and a tiny exhale.
* **s06_l07 "…Sure."**

## s07 — tug & bite (≈17.6 s, +2.5 s) — "chaos"
* **scoop:** Emb scoops the sweater bundle into the cage and shuts the door. Close
  insert: the latch only half-catches and wiggles.
* **s07_l01:** back_away toward the door with a small wave (elbow bent, hand at chest
  height — no raised flat palm).
* **doorClose:** his butt bumps the door and it clicks shut. He freezes.
* **s07_l02:** sheepish laugh, scratching his head. Blush 0.6.
* **open → burst:** he opens the door and Impulsivity lunges in, clamping the cage
  handle in its grin. The tripwire finally went off.
* **tug:** tug-of-war.
  * Emb strains, glasses askew. Impulsivity grins, wall-eyed, tail wagging.
  * cage_rattle.
  * Tiredness watches, unimpressed.
* **squint:** Tiredness leans in (lean_in) and squints into the cage bars. Inside,
  two big shiny eyes look back at him.
* **creak:** the cage door creaks open (cage_creak). His lids lift +10%.
* **bite:** the thing launches onto his forearm and chomps (chomp). Freeze for
  2 frames.
* **s07_l03 screech:** EYES SQUEEZED SHUT, mouth huge, arm shaking. The thing drops off.
* **runout:** he scream_runs out of the room and the door slams. Cut to the window
  view: he runs across the lawn outside, arms flailing (smaller, muffled).
* **catch:** Emb pounces on the thing, puts it back in the cage and latches it firmly
  (latch_click). Impulsivity has let go and sits.
* **stare:** Emb and Impulsivity stare at each other. Its grin is frozen and it
  pants; Emb's face slowly falls. Hold.
* **s07_l04:** facepalm.

## s08 — street & boss (≈17.9 s, +1.5 s) — "tension"
* **walk + s08_l01:** Emb steps out of the front door with the cage, muttering, eyes
  on the cage.
* **vans:** he looks up. Two black HushCorp vans, a couple of still agents and the Boss
  standing in front with her hands behind her back. Name tag **THE BOSS** —
  *"HushCorp"*. Music sting.
* **jawDrop:** his jaw drops comically low and his pupils shrink.
* **s08_l02** (whisper, to himself): fake-cool assembles on his face; blush rising.
* **debris:** his eyes slide around (short pans or inserts):
  * knocked-over trash cans, a shattered streetlight, debris, the broken window;
  * far in the background, Tiredness is still running around the lawn holding his
    arm (small, silent).
* **eyeContact:** their eyes meet. He snaps to attention (attention pose — arms at
  his sides, NO salute).
* **s08_l03 / l04:** he holds up the cage. Nervous smile, sweat, blush 0.8.
* **consider:**
  * The Boss does not react. A pink slip appears between her fingers.
  * Her eyes slide to Tiredness in the background (who trips into a hedge) and back.
  * Her tablet glows: "SUBJECT: TIREDNESS — KNOWN ASSOCIATE: EMBARRASSMENT ✓".
  * A 2 px lid narrowing, then she tucks the slip away. The viewer gets it; he doesn't.
* **s08_l05 "Get in the van."** **s08_l06 "Yes, ma'am!"** — he scurries into the
  van (van_door slam).

## s09 — office (≈23.7 s, +1 s) — "corporate"
* **office:** the cold glass office with a city view. The Boss sits behind a huge desk.
  Emb sits in a comically low chair, looking up.
* **s09_l01:** Emb starts explaining with his hands. **l02** (she interrupts, flat)
  **/ l03:** she does not blink.
* **sweat:** Emb looks down. A sweat drop falls to the carpet (tiny "plip"), and
  he looks back up.
* **s09_l04:** she taps the tablet and a photo of Tiredness appears on the
  glass wall.
* **s09_l05:** Emb, protective, leans forward (he cares about his friend).
* **slide + l06:** she slides the tiny recorder across the desk: black, red LED,
  HushCorp logo.
* **l07 / l08:** a pink slip appears under her finger on the desk as she says
  "clean out your desk".
* **l09:** Emb, quiet and conflicted, eyes down. **l10 "Feelings aren't data.":**
  she doesn't even look up; she is already reading the tablet.
* **gulp:** he gulps, takes the recorder and pockets it. The red LED blinks
  through his coat.

## s10 — the visit (≈21.2 s, +1.5 s) — "awkward"
* **knock:** the front porch. Tiredness opens the door (bandage on his forearm,
  deadpan). Emb has a stiff smile; a red LED blinks through his coat pocket.
* **s10_l01:** Emb, too loud, angled toward his pocket.
* **l02:** protective panic; his eyes dart to the pocket.
* **look:** Tiredness's pupils go down to the bandage, then up to Emb, followed by
  a slight head tilt. **l03 "…Okay."**
* **trip:** Emb turns, trips on the doormat, and the recorder clatters onto the
  porch, LED blinking.
* **both:** both stare at it. Hold. Tiredness's lids lower 5%: he gets it.
* **l04 "Pocket calculator!"** — Emb snatches it.
* **pretend + l05 "…Cool."** — flat. He is pretending.
* **leave:** Emb walks off stiffly and glances back twice. Tiredness's eyes
  narrow as the door slowly closes.
* **search:**
  * Tiredness at his computer, typing (typing SFX) "HUSHCORP" (he saw the logo).
  * The site appears: "HUSHCORP — We keep secrets so you don't have to.", plus a
    "Research Campus — visitor entrance" link and a map pin.
* **l06:** monitor-lit face.
* **resolve:** a slow push-in. His lids LIFT (determined), the first time we have
  seen his eyes this open. Hold.

## s11 — infiltration (≈22.9 s, allowance +6 s) — "tension"
* **lobby:**
  * The HushCorp lobby. Tiredness is in a beige polo with a lanyard and a
    clipboard, at the reception counter.
  * The Receptionist (headset) has the same half-lidded stare.
* **l01–l03, stare:** a deadpan mirror. Hold the stare. **l04 "…Godspeed."**: a
  turnstile beep.
* **walk:** he walks past the Guard, who yawns and never looks at him. He's so
  boring he's invisible.
* **lab:**
  * Specimen tanks, and a terrarium of critters that look like the thing, labelled
    "CARRIER — BITE TRANSFERS TRAITS".
  * A wall screen reads "SPECIMEN ZERO — STATUS: ESCAPED — LAST SEEN: SEWER LINE 7",
    with a big creature silhouette.
* **realize:** his eyes go label → bandage → label and his lids lift +15%.
* **lean:** he leans on the console to steady himself and his hand lands on the
  big red button.
* **alarm:** the alarm, with red light washes pulsing over the walls (moderate, not
  strobing). **l05 "Oh no."**: flat.
* **l06:** guards burst in.
* **chase:** the corridor. Tiredness runs (a tired, flailing run that still somehow
  stays ahead), guards behind him, and a tall window at the end.
* **window:** he crashes through (glass_crash_big). Shards.
* **fall + l07:**
  * Outside the tower: dusk sky, the city far below, wind_fall.
  * He tumbles, deadpan: "Great. This is how I go."
* **powers:**
  * His irises flash teal, a teal glow outlines him and time slows (power_surge).
  * He twists like a cat to land feet-first (flip pose).
* **impact:** the ground rushes up, white flash, impact_heavy, then **black**
  (0.8 s, true black allowed here only).

## s12 — sewer (≈20.6 s, allowance +3 s) — "ominous" (warming at the end)
* **eyesOpen:** from black, eyelids part (two dark lid shapes opening, blurry,
  blink twice). His POV: a hole high above with daylight, broken bricks, a drip
  (eye_open SFX).
* **sit:** he lies in shallow water in a little crater on the walkway and sits up
  groggy (sit_up). Band-aids, smudges, damp hair (outfit "sewer").
* **l01, l02:** "Why am I wet?" — he lifts a dripping sleeve and looks at it.
* **stumble:** he gets up and stumbles along the walkway (squish steps).
* **watched:** behind him in the dark, two teal slits open and blink. He stops:
  his shoulders rise, and his eyes slide sideways, not his head. A low drone.
* **sense:** a new sense.
  * Teal ripple rings pulse out from him (sonar_ping) and his irises flash teal
    (power 0→0.8).
  * The ripple outlines the shadow-shape behind him.
  * He turns his head slowly.
* **leap:** the shadow creature (form 0) lunges from the dark (creature_hiss).
* **grab:** he catches it midair: catch, then struggle_hold.
* **writhe:**
  * It thrashes, tendrils whipping; he holds firm with surprising strength, feet
    sliding.
  * His face shows strain but stays steady, eyes teal.
* **form:** it takes form (form 0→1). The wisps pull in and the sleek creature
  appears in his arms.
* **eyesWide:**
  * Its eyes go wide: it sees his teal eyes, the same glow. Both glows pulse in sync.
  * His lids lift a little too, mirroring it.
* **calm:**
  * It goes limp, then nuzzles into his chest (cradle / held). creature_purr,
    and two heartbeats fall into sync.
  * His face softens into the faintest smile: rare!
* **l03 "…Okay. Hi."**, then **bond:** hold, glows pulsing together.

## s13 — the shaft (≈24.3 s, allowance +3 s) — "reveal"
* **walk + l01:** a tunnel. Tiredness trudges and the creature trots at his heels,
  looking up at him adoringly. "Oh God. Why me." He is weary, not angry.
* **tunnels + l02:** every junction looks the same. He slumps against the wall.
* **point:** the creature points a paw down a dark side tunnel. **l03:** deadpan.
* **roll:** the creature rolls its eyes (a sassy, slow eyeroll).
* **annoy:** it chitters, tugs his hoodie hem, headbutts his leg and pokes him. His
  resistance crumbles. **l04 "Fine."**
* **enter:** they walk into the side tunnel. Teal light grows ahead and they come
  out onto a catwalk.
* **reveal:**
  * Pull out wide: an enormous vertical shaft lined with tiers of glowing teal
    containment pods. Each pod holds a sleeping creature like it.
  * A giant HushCorp logo. Two tiny figures on the catwalk. pod_hum.
* **wide:** a close-up on Tiredness: his lids open FULLY (the payoff), irises
  reflecting teal. Hold.
* **sad + l05:** he looks down at the creature with sadness: inner brows up, soft
  lids. The creature looks up at the pods, ears drooping.
* **nod:** it gives a small nod and a sad chirp, and leans against his leg. His hand
  rests on its head.
* **title:**
  * Pull back to a wide silhouette of the two on the catwalk against the pods.
  * "TIREDNESS" title, then a small "to be continued…".
  * Captions hidden.
