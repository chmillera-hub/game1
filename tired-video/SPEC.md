# Production Bible — "TIREDNESS"

A portrait (9:16) 2D cartoon, **~4:30–4:45, HARD MAX 4:55**. Animated shapes stand in
for feelings:

* **Tiredness** just wants to play his game.
* **Embarrassment** (his old friend, a nervous junior lab scientist) loses a
  lab critter in Tiredness's house.
* **Impulsivity** is the big goofy household creature: a tripwire that never
  goes off, until it does.

The critter bites Tiredness. A cold corporation (**HushCorp**) leans on Embarrassment to
spy on him. Tiredness investigates, falls out of a window, wakes in the sewer
with new senses, and meets the real escaped creature. It leads him to what
HushCorp is hiding.

Tone: dry, deadpan comedy that turns into wonder and sadness. The comedy comes from
faces and timing, never from mean-spiritedness. **Faces carry everything.**
Big takes when the story calls for them, but the hardest-hitting moments are
often **subtle**: a slow half-blink, one brow lifting 5 px, eyes sliding
sideways then back, a lip press, pupils shrinking, a breath held. Tiredness
in particular acts with tiny moves. His lids almost never open fully, so
the few times they do (determination in s10, the shaft reveal in s13) land
hard.

## 0. Hard rules
* Everything is procedural code (Python + cairocffi). No downloaded images.
* Deliverable: **< 15 MB** at 720x1280, 24 fps, H.264 + AAC. Flat colours,
  bold outlines, mostly static backgrounds; characters and props carry the
  motion. No full-screen noise or grain, no constant camera shake, at most about 20
  small moving particles, no big *animated* gradients (static ones are fine).
* **No black first frame.** Scene 1 frame 0 is a bright, readable shot of
  Tiredness gaming (it is the social-media preview).
* Gestures: never a raised straight arm with a flat palm (salute-like), never
  a lone raised middle finger. "Snapping to attention" = straight posture,
  arms at sides, chin up, NOT a hand-to-forehead salute. Pointing uses the
  index finger *with the thumb visible*, aimed sideways or down, not straight up.
* No gore. The bite is a cartoon chomp with little tooth marks and a bandage
  later. Cuts and bruises in the sewer are small band-aids and smudges.
* No profanity on screen: "What the actual—" is cut off by a thud.
* Deterministic rendering: no unseeded randomness (use `hash01/noise1`).

## 1. Tech contract (read engine/core.py — short)
* Logical canvas **1080 x 1920**, origin top-left, y down. `FPS = 24`. Scene-local
  time `t` in seconds.
* **Safe zones:** platform UI covers the bottom 330 px and right 150 px. Faces,
  props that matter and on-screen text stay inside **x 60..930, y 120..1330**.
  Captions are drawn by the engine with baseline y≈1450 (band ≈1330–1560): keep
  that band visually calm (background, floor, legs are fine).
* Scene module `scenes/<module>.py`: `render(ctx, t, info)`; optional
  `SFX(info) -> [(t, name, gain_db[, pan])]`, `CAPTION_Y`, `caption_y(t, info)`.
* `info` (engine/timeline.SceneInfo): `info.dur`, `info.cue(name)`, `info.line(id)`
  (`.start .end .text .who .progress(t)`), `info.talking(who,t)`,
  `info.mouth(who,t) -> (open 0..1, wide -1..1)`, `info.active_line(t)`,
  `info.word_at(t, id)`. Every line id is also a cue (`"s03_l02"`, `"s03_l02.end"`).
  **Never hard-code dialogue times.**
* Speakers (`who`): `tired`, `embar`, `boss`, `guard`, `recep`.
* Helpers in core: `PAL`, `hexc`, `mixc`, easing (`ease_out_back`, `ease_in_out`,
  `pop`, `seg`, `tween`, `state_at`), `blink_amount`, `noise1`, `hash01`, `wobble`,
  shapes (`rrect`, `ellipse`, `circle`, `poly`, `smooth_path`), `fill/stroke/fill_stroke`,
  `text/text_block`, `saved(ctx,x,y,scale,rot,alpha)`, `fade_group`, `shake`,
  `radial_glow`, `vgradient`, and **`camera(ctx, cx, cy, zoom, rot, sx, sy)`**
  (draw a big set in world coordinates and frame it).
* Fonts: "black" (Inter Black — captions), "ui" (Nunito ExtraBold), "round"
  (Fredoka), "comic" (Bangers), "title" (Luckiest Guy), "mono".
* Preview: `python3 build.py sheet s03 --n 16 --cols 4` → `preview/sheet_s03.png`;
  `--times 1.2,3.4`; `python3 build.py still s03 4.2 --scale 0.6`;
  `python3 build.py scene s03` renders every frame (catches exceptions).
  Rig and prop authors: write a small `preview/<name>_test.py` that draws a test
  board PNG, and LOOK at it with the Read tool.

## 2. Look
Flat-colour cartoon with a **dark plum ink outline** (`ink`, 5–6 px at s=1 on
characters, 3–4 px on set details), one shadow tone per material, soft static
light pools. Rounded, appealing shapes (think modern TV animation: Gravity
Falls / Hilda / Owl House). Interiors are warm and cosy, HushCorp is cold
(icy whites, glass, teal accents), and the sewer is deep teal-green but still
readable. Powers and creature eyes are the one **glowing teal** (`power`
`#3ff2e0`). Keep that colour special.

## 3. Characters (rig: `engine/human.py` for people, `engine/creatures.py` for creatures)

### Tiredness (`who="tired"`) — protagonist
Early-20s guy, average height, permanent slouch. Medium-brown skin (`t_skin`).
Messy dark mop of hair (`t_hair`) with one stubborn cowlick, slightly long
over the forehead. **Heavy upper eyelids by default (about 45% closed)**, soft
purple under-eye bags (`t_bags`), brown irises (`t_iris`), thick but low-energy
eyebrows. Navy hoodie (`t_hoodie`, hood down, drawstrings), grey sweatpants,
fuzzy blue slippers. Big over-ear noise-cancelling headphones (`headphones`)
around his neck or on his ears. Voice: low, flat, slow.
Outfits: `default`; `printer` (s11: beige polo `polo`, khaki pants, lanyard,
clipboard, no headphones); `sewer` (s12–13: hoodie, damp hair, two small
band-aids, smudges). Flag `bandage=True` (forearm wrap, s10 onwards).
Powers: `power` 0..1 makes his irises glow teal with a faint eye glow.

### Embarrassment (`who="embar"`) — the friend
Lanky, tall, all elbows and knees, slightly hunched. Pale peachy skin
(`e_skin`) that **flushes**: `blush` 0..1. At 0.3 his cheeks are pink, at
0.7 the whole face is red, and at 1.0 the face is beet red up to the ears with
heat-shimmer lines. Ginger hair (`e_hair`), neat side part, always one tuft
sticking up. Big round glasses (`glasses`) with lens glints: his eyes are big
and very readable behind them. Green irises. White lab coat (`e_coat`) over a
teal sweater vest, dark slacks. Sweats easily (`sweat` 0..1 → beads on the
temple, drops). Voice: fast, high-ish, nervous.

### The Boss (`who="boss"`) — HushCorp lab director
Tall, very still, cold and precise. Pale skin, a sharp silver-white bob
(`b_hair`), charcoal suit (`b_suit`), small teal HushCorp pin, thin dark-red
lips, grey-blue eyes with low, flat lids. She almost never moves her face: a
2 px lid narrowing is her biggest reaction. Voice: British, crisp.

### Guard (`who="guard"`) and Receptionist (`who="recep"`)
* **Guard:** stocky HushCorp security in a navy uniform (`g_uniform`) and cap,
  with a radio. He yawns.
* **Receptionist:** seated behind a counter (upper body only), lavender
  cardigan, headset, a bored half-lidded stare that matches Tiredness.

### Impulsivity (`engine/creatures.draw_impulsivity`) — "it"
Big, round, shaggy, dog-like household creature, about the height of a seated
adult. Gold-orange fur (`imp_fur`) in fluffy tufts, floppy ears, stubby legs,
a fluffy tail that wags. The **dumbest grin**: wide open smile, pink tongue
(`imp_tongue`) lolling to one side, **eyes pointing in different directions**
(independent pupils), panting (tongue and belly bob). Default state is
FROZEN: no blinking, pupils locked, only the pant. It is a tripwire that never
goes off, until s07, when it bursts in and plays tug-of-war with the cage.

### "The thing" (`engine/creatures.draw_thing`)
Small (about 120 px long at s=1) fuzzy violet critter (`thing_fur`) with big
shiny black eyes, small round ears, a long thin tail and two tiny front teeth.
It scurries as a blur with motion lines. It is NOT the real escaped specimen;
it is a "carrier" whose bite passes traits on. States: scurry, sit, peek,
hiss, leap, bite, hidden-under-sweater lump.

### The creature / "Specimen Zero" (`engine/creatures.draw_specimen`)
The real escaped HushCorp creature, living in the sewer.
* **form=0**: a writhing shadow mass (dark wisps, too many teeth, glowing teal
  slits). Scary silhouette, never gory.
* **form=1**: its true shape is a sleek, dog-sized creature with deep indigo
  body (`spec_body`), long fin-like ears, a long tail, a soft glowing teal
  rim, and **huge expressive eyes with teal-glowing irises** (the same glow
  as Tiredness's powers).

Expressions: snarl, wide-eyed realisation, calm, content (eyes closed,
purring), curious head tilt, **eye-roll** (it is a little sassy), pointing
with a paw, pleading, sad. The pods in the s13 shaft hold sleeping creatures
like it (`draw_specimen(..., sleeping=True)`).

## 4. Places (`engine/sets.py`) — all bright enough to read on a phone
* **Bedroom (s01, s05–s07):** Tiredness's messy cosy room.
  * Afternoon light through a window looking onto the street.
  * Gaming desk with a big monitor (animated game screen), a gaming chair,
    an unmade bed, a laundry pile, a closet with a sliding door, posters, a
    ceiling light, and the door to the hallway.
* **House exterior / street (s02, s03, s08):** a two-storey suburban house
  with a front door, three ground-floor windows, an upstairs bedroom window,
  lawn, path, trash cans, a streetlight and a picket fence. Bright day.
  `damage` 0..1 adds knocked-over cans, a shattered streetlight and debris.
  s08 adds black vans.
* **Living room / kitchen (s04):** couch, coffee table with plates, a kitchen
  counter with drawers, a dining table, Impulsivity's giant pet bed, the broken
  window, and the staircase going up.
* **Upstairs hallway (s05):** the top of the stairs and the bedroom door, with
  a light gap under the door.
* **HushCorp office (s09):** glass-walled, icy white and grey, a city skyline
  view, a huge empty desk, and the HushCorp logo on the wall.
* **HushCorp lobby (s11):** reception counter, a glowing logo, turnstiles, a
  guard post, a potted plant, and a sleek cold floor.
* **HushCorp lab (s11):** specimen tanks and the critter terrarium labelled
  "CARRIER — BITE TRANSFERS TRAITS". A wall screen shows "SPECIMEN ZERO —
  STATUS: ESCAPED (SEWER?)" with a silhouette, a console with a big red
  button, and a corridor ending in a tall window.
* **City fall (s11):** the outside of the tower, dusk sky and the city far below.
* **Sewer (s12–s13):** a brick tunnel with a water channel, a walkway, pipes,
  drips, a shaft of daylight through the hole he fell through, and darkness at
  the edges (dark teal, never pitch-black).
* **The Shaft (s13):** an enormous vertical cylindrical chamber. Tiers of glowing
  teal containment pods ring the walls with sleeping creatures inside, plus
  catwalks and a giant HushCorp logo. Epic scale with tiny figures.

## 5. HushCorp
Fictional corporation. The logo is a teal circle containing a stylised keyhole
shape, with the wordmark "HUSHCORP" (font "ui", wide letter-spacing). The tagline
on its website is "We keep secrets so you don't have to."

## 6. Audio
* Voices (Kokoro TTS): tired `am_michael*0.7+am_onyx*0.3` 0.95×,
  embar `am_puck` 1.14×, boss `bf_emma` (en-gb), guard `am_fenrir`,
  recep `af_bella`.
  * Line fx `whisper` is a hushed aside; `muffled` is heard through a wall or window.
* Music is procedural (`audio/music.py`). Each scene sets a cue in script.json,
  and the music is ducked under dialogue.
  * Cues: `chill` (lo-fi gaming bed), `panic` (frantic comedic pizzicato +
    woodblock), `sneaky` (tiptoe), `awkward` (sparse cringe bassoon/pizz with
    long gaps), `chaos` (slapstick action), `tension` (suspense), `corporate`
    (cold minimal synth pulse), `ominous` (sewer drones, drips, low swells),
    `reveal` (awe → sorrow strings and choir, ending sting).
* SFX library `audio/sfx.py`; scenes request SFX via `SFX(info)`.
* Mix ≈ -14 LUFS, true peak ≤ -2 dBTP, 48 kHz stereo.

## 7. Files
* `engine/human.py` — the people rig (`API_human.md` documents it).
* `engine/creatures.py` — Impulsivity, the thing and the creature (`API_creatures.md`).
* `engine/sets.py` — backgrounds, and `engine/props.py` — props (`API_sets.md`).
* `engine/fx.py` — overlays, title tags, UI screens and the end card (`API_fx.md`).
* `audio/music.py`, `audio/sfx.py` (`API_audio.md`).
* `DIRECTION.md` — shot-by-shot animation direction per scene.
