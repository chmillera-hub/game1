# Brindle Cross: how the faces, eyes and bodies are animated

*Brindle Cross* is a 213-second portrait 3D short film. A deadpan narrator introduces a town. Oswald, a silent clown, does slapstick, and then he quietly kneels and gives his supper and coat to Edith, an elderly widow whose first name nobody knows. The other speakers are Teddy, a child, and Tomas, the baker.

Nothing was keyed by hand. Python code (Kokoro for the voices, Blender 4.5 for everything else) generates every voice, mouth shape, glance, blink, expression and posture. This page explains the rules behind that acting: how the mouth follows the audio, how the eyes and lids move, how expressions are built and timed against the words, and how bodies listen. Each technique comes with the numbers we used and where to see it.

## The conversation loop

A single line of dialogue passes through six stages:

1. **Voice.** Each line is one Kokoro voice, or a blend of several, at a chosen speed. It is rendered long and then cut to the words. `film.py:Film.say` places it at a start time that the shot writes relative to the previous line, and returns its start and end, so every other key can be written against the words.
2. **Mouth.** The phoneme timings become overlapping mouth shapes. Loudness sets their size, and p, b and m are forced shut (*Voice acting and lip-sync*).
3. **Eyes.** The eyes move before the sound. A look target is shared down the chest, neck and head, a blink comes with the shift, and saccades and lid coupling run underneath (*Eyes, eyelids and gaze*).
4. **Face.** The expression starts 0.25–1 s before the audio. Speech is added on top of it, so the character talks through the feeling, and the face settles after the line ends (*Facial expression, brows and micro-acting*).
5. **Body.** The body holds an attitude, adds beats such as nods and shrugs, and keeps breathing. The listener reacts when the speaker says something that matters (*Body language and staging for conversation*).
6. **Camera.** The camera setup and the eyeline cheats decide what the audience can read (the staging notes at the end of that section).

`perf.py:evaluate` combines the mouth, eye, face and body layers on every frame.

*How to read this page.* Every shot is a function in `shots.py`. For example, shot 3.20 is `shots.py:s3_20`, and shots 3.15a and 3.15b share `s3_15`. All times are seconds on the film timeline.

## Voice acting and lip-sync

Every line is synthetic speech, and all of the lip-sync is computed from that audio. The acting on top of it is written as code in `shots.py`: parted lips before a line, a swallow, a trembling chin. There are three stages:

- Cast a voice that fits the body.
- Turn the audio into overlapping mouth shapes.
- Layer those shapes on the acting.

### Casting: a voice that fits the body

A voice belongs to a body when its size, tempo and texture match what we see. `tts.py:make_line` builds every line in the same order. It blends the voices and synthesises at the chosen speed, then shifts the pitch a little.

- **Blend.** Kokoro voices are style vectors. `tts.py:style_vec` takes their weighted mean, so "80% warm, 20% playful" is meant literally.
- **Speed** carries age and mood. Everyone except Teddy runs below 1.0.
- **Pitch** moves last, and only slightly. `tts.py:pitch_shift` runs Rubber Band with `-p <semitones> --fine`, plus `-F` to keep formants. Keeping formants changes the note but not the apparent size of the throat.

The cast (`make_voices.py:VOICES`):

- **Narrator:** `bm_lewis` 0.6 + `bm_george` 0.4, speed 0.92, −1 semitone. He has no body: `film.py:SPEAKER` maps him to `None`, so no mouth moves.
- **Oswald:** `am_michael` 0.8 + `am_puck` 0.2, speed 0.92, −0.5 st.
  - The screenplay says "his voice is smaller than his body", so it is barely lowered.
  - It also says to mix him "close and quiet" in Scene 3. In `shots.py` his normal lines are placed with `gain=-2.0`, and his "Edith." in 3.19 with `gain=-3.0`.
- **Edith:** `af_heart`, speed 0.88, −1 st. The screenplay says "−1 st and no lower (−2 st drifts androgynous)", and "Her age comes from speed and breath, not pitch."
- **Tomas:** `am_fenrir` 0.85 + `am_onyx` 0.15, speed 0.95, −1 st.
- **Teddy:** `am_puck` 0.5 + `af_heart` 0.5, speed 1.05.
  - He is shifted +2 st with the formants moving (`formant=False`), then +1 st with formants kept (`pitch2`).
  - Moving the formants shrinks the apparent throat, so he sounds like a child, not a sped-up adult.

Per-line direction lives in `script/lines.txt`:

- **Speed overrides.**
  - `E0.83` slows "That was Walter's."
  - Edith's two lines in 3.18 ("Edith." and "...Please.") run at 0.82.
  - Her plain "It's Edith." to Teddy in 5.2 is a separate take at 0.92. The screenplay says "simply".
- **Render long, cut short.** `tts.py:cut_words` keeps the first or last N words and shifts the timings to match.
  - A first-N cut ends 45 ms after the last kept word, with a 30 ms fade-out.
  - A last-N cut starts 30 ms before the first kept word, with a 15 ms fade-in.
  - Tomas's "It's..." is "It's Margaret, I think." cut after one word, so the unfinished, mid-sentence pitch survives.
  - Edith's "Edith." is the end of "My name's Edith."
- **Hushed lines** (E02, O04, E18) need four things: less air, a lower level, no room and a breath first.
  - They run 0.05–0.06 slower than the character's default.
  - They get a −4 dB high shelf at 6 kHz (`tts.py:high_shelf`).
  - `film.py:say` places them 8 dB down, with an exhale sound 0.35 s before at −14 dB.
  - They skip the street reflections that other character lines get at −20 dB wet (`mix.py:build_voices`, `STREET_WET_DB`).
- **Pauses live in the edit.** `film.say` returns a line's start and end, and the next line is placed relative to them. For example, "That was Walter's." starts 1.1 s after Oswald stops (`F.say('E02', b + 1.1)`).
- **Clean edges.** `tts.py:trim` trims silence from both ends (threshold 1% of peak, 60 ms pad) and shifts the timings to match. `tts.py:make_line` then peak-normalises the clip to 0.9.

### From audio to mouth shapes

**Timings.** Our Kokoro model returns a duration for each phoneme symbol. `tts.py:synth` adds these up, then rescales them so the last edge lands on the end of the audio. That gives `(phoneme, start, end)` for every symbol, including stress marks and spaces.

Across the 59 generated lines, the median symbol lasts 54 ms, about 1.3 frames at 24 fps. That is why one shape per phoneme chatters.

**Visemes.** `tts.py:CH` sorts the symbols into 17 mouth classes, and `tts.py:VIS` gives each class a target on five channels:

| Viseme | IPA | jaw | wide | round | press | lip_raise |
|---|---|---|---|---|---|---|
| AA | a ɑ æ ʌ ɐ | .62 | .15 | | | |
| EH | ɛ e | .42 | .40 | | | |
| IY | i | .18 | .70 | | | |
| IH | ɪ ᵻ | .25 | .45 | | | |
| AH | ə ɜ | .36 | .05 | | | |
| AO | ɔ o ɒ | .50 | | .55 | | |
| UW | u ʊ | .18 | | .95 | | |
| ER | ɚ | .28 | | .35 | | |
| MBP | p b m | | | | 1.0 | |
| FV | f v | .06 | | | .45 | .20 |
| TH | θ ð | .16 | .20 | | | |
| T | t d n l s z ɾ | .16 | .30 | | | |
| SH | ʃ ʒ ʧ ʤ | .14 | | .55 | | |
| K | k g ɡ ŋ h x | .28 | .10 | | | |
| W | w | .08 | | 1.0 | | |
| R | ɹ r | .20 | | .40 | | |
| Y | j | .14 | .50 | | | |

A blank cell means 0. Spaces, punctuation and the length mark ː add nothing. A diphthong is two symbols, so "rye" (`ɹˈaɪ`) glides from AA to IH on its own.

`tts.py:visemes` turns those targets into per-frame curves:

- **Coarticulation.** A real mouth is already moving toward the next sound.
  - Each phoneme adds a gaussian bump at its midpoint, with sigma `max(0.045 s, 0.75 × duration)`. Sigma sits at the 45 ms floor for about 70% of phonemes.
  - Each bump mainly overlaps the phoneme on either side. The median is one neighbour per side at 13% weight or more.
  - The sum is divided by `max(total weight, 0.6)`. Inside a word that is a true weighted average. In a gap the weight falls below 0.6, so the mouth relaxes instead of freezing on the last shape.
- **Stress.** After a ˈ or ˌ mark, the jaw of the next vowel (AA, EH, IY, IH, AH, AO, UW or ER) is multiplied by 1.25. Stressed syllables open wider, which reads as emphasis.
- **Closures.** If the lips don't meet on p, b and m, the line looks mumbled. Across the phoneme, padded 15 ms before and 10 ms after, `press` is forced to 1.0 whatever the loudness, and the jaw is cut by 85%.
- **Loudness.** Quiet sounds get a smaller mouth.
  - RMS over ±30 ms is divided by the 90th percentile of the line's non-silent frames, then clipped to 1.3.
  - The jaw is scaled by `0.55 + 0.6 × loudness`, with loudness capped at 1 in that term. So loud frames can open up to 15% past the target.
  - Jaw, wide and round are also multiplied by a gate, `clip(1.6 × loudness, 0, 1)^0.7`. Press is gated as well, before the closure override. Lip_raise is not gated.
  - Above 0.625 the gate is fully open. At 0.3 the jaw reaches 44% of its target, at 0.1 it reaches 17%, and in silence the mouth closes.
  - Soft words and trailing syllables shrink on their own.
- **Smoothing.** A [0.25, 0.5, 0.25] filter removes single-frame pops.

Three problems turned up when we checked the generated data against the code, and all three are now fixed. They are common traps, so they are worth knowing about:

- **Smoothing softened the closures.** The closure rule originally ran before the smoothing filter, so the filter blurred short p/b/m sounds. Across the 53 p/b/m in the 59 lines, `press` peaked at a median of 0.82 and only 14 reached 1.0: the lips often stopped just short of meeting. `tts.py:visemes` now applies the closure again after smoothing (`press = max(press, closure)`, jaw cut by 85%), and all 53 closures reach 1.0.
- **Hushed lines looked as loud as normal ones.** Loudness is normalised per line, and the hushed lines' −8 dB is applied later in the mix, so the mouth moved as much as on a normal line. `film.py:say` now scales jaw, wide and round by 0.75 on hushed lines, so a whisper uses less mouth.
- **The /g/ sound had no shape.** `CH` mapped the ASCII letter `g`, but the phonemizer emits the IPA `ɡ` (U+0261), which looks identical. Four takes contain it ("Again!", "Good.", "Congratulations." and the "It's Margaret, I think." take behind Tomas's "It's...", though that cut keeps only "It's"). `CH` now maps both. Check your phoneme inventory against your mapping table; look-alike characters fail silently.

`revisemes.py` recomputes every line's mouth curves from the stored audio and timings, so changes like these do not need the voices to be synthesised again.

### Layering speech on the acting

Shots set the acting directly in code, such as a smile, a grief brow or pressed lips. Speech is added on top, so the character talks *through* the expression. `perf.py:evaluate` combines them every frame:

- `jaw` = acting + 0.95 × speech; `round` = acting + 0.8 × speech; `lip_raise` = acting + 0.5 × speech.
- `wide` = max(acting, 0) + 0.7 × speech.
- `press` = max(acting, speech). A closure always wins, but so does a held acting press, so shots release presses as a line starts.
- `brow` = acting + 0.10 × speech jaw. This gives an eyebrow beat for free.
  - The mid brow bone rises 0.007 × 2.4 × head scale metres per unit of `brow` (`rigctl.py:face_to_channels`).
  - At typical line peaks that is about 0.4–1 mm. The widest line, E05, reaches about 1.35 mm.
  - Stressed vowels open the jaw wider, so they lift the brow a little more.
- smile, smirk, brow_in, brow_asym, pout, the lids and the gaze are untouched, so the emotion holds through the line.

`rigctl.py:face_to_channels` maps these channels onto the rig. The jaw bone rotates 18° per unit. From speech alone, a line's widest frame is typically about 7.5°. The most is 12.3°, on E05 "He loved that you never fixed it."

The other channels drive shape keys of the same names, built in `headgen.py:build`:

- *wide* widens the mouth 18% (`sx=1.18`) and thins the lips (75% upper, 80% lower).
- *round* narrows the mouth to 62% and opens the slit from 0.07 to 0.30. It also thickens the lips (×1.35) and pushes them forward (`pucker=0.9`).
- *press* seals the slit (`sy0=0`), thins the lips to 70%, and draws them back (`pucker=-0.25`).

The jaw opens the mouth; the shape keys shape the lips.

### Where to see it

- **3.8 (starts 88.3 s):**
  - At ~89.1 s Oswald's inner brows lift (brow_in 0.35, brow 0.15). That is 0.2 s before "It's the small rye." starts at 89.3 s.
  - At ~90.6 s Edith's eyes drop to the loaf and her lips part (jaw 0.08) under a grief brow (brow_in 0.95, brow −0.15).
  - At ~91.3 s comes the automatic exhale. At ~91.7 s she says the hushed "...That was Walter's."
  - The speech jaw adds onto the parted lips. The grief brow holds; speech adds only its small brow lift.
- **3.9 (starts 99.9 s):** Edith's "He loved that you never fixed it." ends at ~109.1 s.
  - Oswald does a slow blink, a breath out, and looks back to the lamp.
  - At ~110.2 s he swallows (press 0.7) with a 4° head dip. The timings are under *Micro-acting*.
- **3.12 (starts 119.1 s):** From ~120.1 s Oswald's lips part (jaw 0.06 over 0.35 s). That is about half a second before the hushed "...Thirty-one Sundays." starts at ~120.6 s.
- **3.13 (starts 122.3 s):** At ~122.4 s Edith presses her lips (0.6) with a slight frown and nods 7°. The press releases over 0.2 s just as "I don't want it fixed." starts at ~122.9 s.
- **3.15a (starts 132.8 s):** Oswald's "Well. He calls me Oscar, so—" is cut mid-sentence. Edith's "Oh... you don't have to do that." starts at ~135.1 s, 2 frames before his clip ends (`b - 2 / 24.0`), so she interrupts him.
- **3.19 (starts 158.9 s):** At ~159.7 s Oswald starts a 6° nod. 0.45 s later he says "Edith." The head moves before the voice.
- **3.20 (starts 161.4 s):** Edith's chin trembles at ~162.4 s and she presses it still. She starts releasing at ~162.97 s, just before the hushed "Nobody's said it since April." starts at ~163.0 s. The full sequence is under *Micro-acting*.

### Try this in your own animation

- Give each sound a soft influence (sigma at least ~45 ms) that overlaps its neighbours, and blend them. Let the mouth relax in the gaps rather than holding one shape per sound.
- Make p/b/m hard rules that override everything else. Apply them after any smoothing so the lips really meet.
- Size the mouth by loudness. To make whispers look whispered, use the level the audience hears, not each clip's own level (we scale hushed lines' mouths by 0.75).
- Check that every symbol your speech engine emits is in your mouth-shape table. Look-alike characters such as `g` and `ɡ` fail without any error.
- Let speech drive only the jaw and lips, and leave the brows, lids and mouth corners to the emotion. Release any held lip press on the first syllable.
- Start the face 0.2–0.5 s before the sound: a brow, parted lips, a breath or a nod. Let a swallow or a pressed mouth answer a line after it ends.
- When casting, adjust speed and pauses before pitch. Keep formants when you lower a voice, and move them only to change body size. Render whole sentences and cut words out to keep a natural cadence.

## Eyes, eyelids and gaze

Viewers look at the eyes first, so most of the life in these faces comes from small rules running under the authored looks. On every frame, `perf.py:evaluate` works out where the eyes point by adding up four things:

- the aim at the current look target
- the authored `gaze_yaw` and `gaze_pitch` face channels
- the authored `gaze_off` track
- automatic saccades

Both eyes get the same angles. They are computed once, from the left eye, so the eyes do not converge. `rigctl.py:face_to_channels` then works out the eyelids from four inputs: the lid values, the blink value, the final gaze pitch and the smile.

### A look is a target, shared down the spine

`Actor.look_at(t, target, dur=0.4, weight=1.0)` (perf.py) can aim at three kinds of target:

- a fixed point
- a live reference such as `('actor', 'oswald', 'eyes')`
- a function of time

A live reference is looked up again on every frame (`perf.py:world_point`). `'head'` is a point 9 cm along the head bone, scaled by head size, and `'eyes'` is that point plus 2 cm up.

The point comes from `perf.py:_actor_head_world`, which uses only the other actor's position, walks and posture. So if Oswald walks, kneels or sits back on his heel, Edith's look follows him. His nods, head turns and look rotations do not move the point, which keeps the two looks from feeding back into each other.

If one joint did all the turning, the head would swivel like an owl's. To avoid that, `perf.py:evaluate` splits the turn down the spine:

- **Yaw:** chest 18%, neck 32%, head 45%.
- **Pitch:** neck 35%, head 60%. The chest never pitches for a look.
- **Limits:** these apply to the look angle before it is split, measured from where the head points in the current posture. They are ±80° of yaw, 40° down, and `look_up_max` up (35° by default).

That adds up to 95% of the angle. The eyes are then aimed from the *posed* head exactly at the target, within ±35° of yaw and ±30° of pitch, so they cover the last 5% plus whatever the limits cut off.

The eyes are solved after nods, tilts, idle head sway and breathing are applied. So they turn against the head and stay locked on the target. For example, in 3.19 (~159.7 s), before "Edith.", Oswald nods with `amt=6`. The nod peaks at about 5°, and his eyes stay on hers the whole time.

How far the head may look up is a character choice (`shots.py:build`):

- **Edith** sits with her head against the brick, so her `look_up_max` is 14°. The code comment reads "looks up are mostly eyes".
  - `shots.py` stores a face point for each of them in Scene 3 (`ED_FACE`, `OS_FACE`). By those points, Oswald's kneeling face is about 22° above hers.
  - Her head stops at the 14° limit, and her eyes and lifting lids do the rest. She looks up from under her brows.
- **An explicit head move is not limited.** `head()` adds to the look instead of going through it. In 3.10 (~111.1 s) she tips her head back 17° toward the tower, on top of her look up at it.
- **Teddy** gets 50°. The code comment reads: "Teddy tips his head back to grown-ups instead of rolling his eyes up under the lids".
- **Big sideways looks get a chest turn, added by hand.** At the end of 3.21 (~177 s), Oswald looks out at the square (weight 0.8).
  - As he does, he gets `chest(yaw=-25)`, a 25° upper-body turn to his right, split 40% spine and 60% chest.
  - The code comment reads: "his shoulders turn with the look so the head is not owl-like" (`shots.py:s3_21`).

A `weight` below 1 scales down both the head's share and the eye correction, so the look stops short of the target. The film uses weights from 0.5 to 0.9. Ignoring the limits and treating each turn as a simple fraction of the angle, that stops roughly 25% short at 0.5, 10% short at 0.7, 5% short at 0.8 and about 1.5% short at 0.9.

That reads as looking *toward* something, and the film uses it for memory and half-attention. One example is Oswald's look drifting to the empty patch by the lamp where Walter stood (3.9, ~100.1 s, weight 0.6).

`dur` sets how long the look takes to travel. Target and weight both blend with a smooth ease in and out (smootherstep). Typical values in `shots.py`:

- 0.2–0.3 s for a glance
- 0.4–0.5 s for a shift in conversation
- 0.6–0.8 s for a heavy look

The engine does not make the eyes move before the head, because both follow the same look track. The shots add that by hand where it matters:

- In 3.1 (~66.7 s), Oswald freezes on "What's her first name?".
  - His look target is set again to the same point, and only `gaze_yaw=28` moves, over 0.25 s.
  - His eyes slide sideways toward the voices behind him while his head and body stay frozen, with the loaf at his open mouth.
- In 3.4 (~73.0 s), his eyes move first. `gaze_yaw` eases back from 28° to 10° over 0.8 s. 0.4 s later, a new `look_at` starts turning his head toward the wall where Edith sits.

### Saccades: the eyes never stand still

A saccade is the quick jump real eyes make from one point to the next. An eye that never jumps reads as a doll's.

- **How often:** `perf.py:_auto_blinks` schedules a jump every 0.5–1.7 s, at random.
- **How far:** each jump goes to a new random offset. The standard deviation is 1.6° for yaw and 0.9° for pitch, so about two-thirds of jumps stay within those amounts.
- **How fast:** `perf.py:_sacc_val` makes the jump in 0.05 s, about one frame, then holds it.

Each offset is drawn fresh, not added to the last one, so the eyes jitter around where they are aimed instead of drifting away. Each actor has its own random seed (`film.py:Film.__init__`, `seed=11 + i`), so the characters' flicks and blinks are not in sync.

Saccades can also be keyed by hand on the `gaze_off` track. In 3.12 (~119.3 s), Oswald silently counts the Sundays:

- His eyes flick −4°, +3°, −3°, +4° and −2°, one every 0.2 s, each taking 0.05 s.
- The offset returns to zero at ~120.3 s.
- His look goes to Edith's eyes at ~120.4 s, before "...Thirty-one Sundays." at ~120.6 s.

### Blinks: a steady rhythm plus accents

Every automatic blink has the same shape (`perf.py:_blink_val`): 0.07 s to close, 0.04 s shut and 0.19 s to open, 0.30 s in all. It closes fast and opens slowly.

Blinks come from four rules:

- **Automatic:** the first comes 0.3–2.0 s into the film, then one every 2.2–5.0 s (`blink_rate`), about 17 a minute.
- **On every look change:** each `look_at` call adds a blink 0.02 s after it starts, the way people blink during a big shift of gaze. This includes small looks and a `look_at` that sets the same target again. Oswald's freeze in 3.1 starts with one (~66.7 s). The one exception is 3.2: the shot takes back the blink Tomas's look adds (`To.blinks.pop()`), so his slow blink is the only one.
- **On a story beat:** `blink(t)`.
  - At the CLONG (2.1, ~42.4 s), Edith gives one startled blink and a 3° head flinch, and she still doesn't look up.
  - At "He said you lean" (3.9), Oswald gives a caught double blink at ~105.0 s and ~105.35 s.
- **Minimum gap:** `perf.py:_auto_blinks` keeps a blink only if it starts more than 0.35 s after the last one it kept. This applies to all blinks, so a random blink just before a keyed one can cancel the keyed one.
  - Oswald's five blinks keyed 0.22 s apart after the CLONG (`shots.py:s2_1`) cannot all play. Every other one is dropped, and they read as about three blinks.
  - Oswald's double blink is keyed exactly 0.35 s apart. The second one survives only because floating-point rounding makes the gap a hair over 0.35 s.
  - Key blinks at least 0.4 s apart.

Slow blinks are keyed on the `blink` channel with `expr`, closing over 0.15–0.3 s and opening over 0.18–0.45 s. They show a thought landing:

- **Tomas,** after failing to remember her name (3.2, ~69.1 s): 0.22 s to close, 0.35 s to open.
- **Edith,** hearing him fail (3.3, ~70.8 s): 0.3 s to close, 0.45 s to open. Before it, only her lids and brows move: from ~70.2 s her lids ease to 0.98 and her inner brows lift (`brow_in=0.35`). Her gaze stays on the cobbles.
- **Oswald,** hearing his own first name (3.21, ~175.7 s): 0.15 s to close, a moment shut, 0.18 s to open. That is 0.35 s from first movement to fully open, about 8 frames. The screenplay asks for "one slow blink of 8 frames at most".

`hold_eyes(t0, t1)` drops only the *automatic* blinks in a window. Examples:

- Oswald: 4 s starting at his freeze in 3.1.
- Edith in 3.18 ("Edith. ...Please."): 4.5 s, longer than the 4.1 s shot.
- Edith in 3.17, covered under the conversation rules below.

Saccades keep going, so a held stare keeps its tiny movements. Forced blinks still play, unless the 0.35 s rule drops them. When Edith's eyes drop after "Edith." in 3.18 (~156.4 s), that look change still brings its blink.

### Eyelids: driven by the eyes, then acted

`rigctl.py:face_to_channels` works out each upper lid from its openness, which is the lid value times (1 − blink):

- At openness 1 the lid is in its neutral open position.
- At openness 0 it has rotated 46° closed (`UP_CLOSE`).
- For each unit the lid value goes above 1, the lid opens 30° wider.

On top of the lid value set in the shot, four things happen automatically:

- **The lids follow the gaze, so the iris stays framed.** For each degree the eyes look down, the upper lid moves 0.50°; for each degree up, it moves 0.65°. The lower lid moves 0.3° per degree down and 0.2° per degree up.
  - Example: in Scenes 1–2, Edith looks down with `gaze_pitch=-16` and lid 0.85. Her upper lid ends up about 14° below neutral: 6.9° from the lid value and 6.8° from the gaze.
  - The two effects add up, which is why the pose reads as heavy.
- **This link fades as the lid closes.** It is scaled by the openness, so a blink looks the same wherever the eyes are pointing.
- **A closing eye seals.** The lids meet in the middle:
  - When the openness drops below 0.25, the upper lid eases up to 11° further down. That happens in the last quarter of any close, from a blink or from a very low lid value.
  - The blink channel also lifts the lower lid by 8° times the blink value, and it fades out any authored lower-lid raise.
- **A smile lifts the lower lid** 5° per unit of positive smile, as the cheeks push up. So a smile reaches the eyes without extra keys.

A lowered lid and a closed eye read differently. For "Nobody's said it since April" (3.20), Edith holds `blink=1.0`. It starts closing at ~161.7 s and takes 0.6 s, and she opens her eyes again at ~170.7 s in 3.21. Because it is the blink channel, the lower lid rises and the gaze link is off. That reads as a sealed, chosen closing of the eyes, not as heavy lids.

| Upper-lid value | Lid moves | Reads as | In the film |
|---|---|---|---|
| 0.55–0.7 | 21–14° lower | heavy, bored, irritated | Tomas at work at 0.7 (1.1). In 1.3 he slides the tray onto the window shelf at 0.62, then drops to 0.55 for his glare at the open door (~19.1 s) |
| 0.82–0.86 | 8.3–6.4° lower | tired, sad, turned inward | Edith in Scenes 1–2 (0.85, then 0.82 in 2.4). Edith softening to 0.86 while Oswald says "I didn't know what to say" (3.15b, ~140.9 s) |
| 0.88–0.95 | 5.5–2.3° lower | soft, paying attention | most of the listening in Scene 3. Oswald easing to 0.88 before "Edith." (3.19, ~159.3 s) |
| 1.05–1.15 | 1.5–4.5° higher | interest, really seeing someone | Edith at 1.05 searching his face on "Every day at four..." (3.8, ~94.0 s). Edith at 1.12 as her eyes reach Oswald's face (3.7, ~83.7 s). Edith at 1.15 just before "Mr. Bunce. No." (3.16, ~145.4 s) |
| 1.25–1.4 | 7.5–12° higher | shock | Oswald at the CLONG at 1.25 (2.1, ~42.3 s). Spotting the first peel at 1.25 (2.2, ~46.3 s). Falling on the second at 1.3 (2.3, ~50.8 s). Tomas finally looking toward her at 1.4 (3.2, ~68.4 s) |
| 0.6, lower lid 0.7–1.0 | upper lid 18° lower; lower lid 10–14° up, plus up to 5° from the smile | laughing, crinkled eyes | the crowd's laugh at 0.6 / 0.7 with smile 1.0 (2.1, ~42.5 s). Edith at 0.6 / 1.0 with smile 0.9 after "There's the lean" (4.2, ~184.8 s) |
| `blink` held at 1 | 57° down, lower lid 8° up | closed: pulling inward | Edith, 3.20–3.21 |

### Eyeline cheats

When two people sit side by side facing the camera, a true eyeline puts both faces in profile. In 5.2, each looks at a point in front of the other's eyes. The offsets run mostly along world −Y, which in this setup points toward the lens:

- Teddy at ~195.8 s: `('actor', 'edith', 'eyes', (0, -0.30, 0))`, 0.30 m in front of her eyes, weight 0.9.
- Edith at ~195.9 s: `('actor', 'teddy', 'eyes', (0.05, -0.60, 0.05))`, 0.60 m in front of his eyes and a few centimetres across and up. Her head also lifts 5° (`head(pitch=-5)`).

Their faces open toward the camera instead of turning to profile.

In Scene 3 part of the cheat is in the camera (`shots.py:SETUP`). Setup C sits "over Oswald's shoulder, close to her eyeline", so Edith's eye contact with him plays close to the lens. In the street-side two-shot (setup B), her look itself is cheated. When she looks at his eyes in 3.9, 3.16, 3.17 and 3.21, she aims at `('actor', 'oswald', 'eyes', ED_B)`, where `ED_B = (0.35, -0.40, 0.0)` is a world offset "cheated toward the lens". Her looks at his hands in 3.16 and 3.17 get a smaller offset, `(0.15, -0.20, 0.0)`.

In 1.4 (~22.8 s), on "He is eight", Teddy glances at his own name label. His look target is built from the camera's position: 1.2 m in front of the lens, 0.35 m to screen-left and 0.25 m down, toward the left-aligned label. So he appears to look at the on-screen text. He glances again at ~24.1 s, after the label corrects itself to "Age 8 (nearly 9)".

### The conversation rules the shots follow

- **Save eye contact until it means something.** Edith has no `look_at` until 3.7.
  - For the first 82 s, her gaze is a fixed offset down to the cobbles (`gaze_pitch` −16° to −18°), with her head pitched down 10°. Only saccades and blinks move her eyes.
  - Her first look goes to the loaf in Oswald's hand (~82.7 s, over 0.7 s), then to his eyes (~83.6 s), and her lids widen to 1.12.
- **One look change per beat, each with a reason.** Look changes are timed off the dialogue. Most reactions start 0.05–0.45 s after the line they answer ends, for example:
  - 3.8: +0.05 s, then +0.45 s
  - 3.13: +0.12 s
  - 3.7 and 3.18: +0.15 s
  - 3.2: +0.35 s

  A change of thought comes partway into a line. Between changes the target holds, and the eyes move only by saccades, blinks and the occasional authored offset.
- **Listen to what is said; glance away to remember.** On "Every day at four..." (3.8, ~93.7 s), Oswald lowers his eyes 4° (`gaze_pitch=-4`) and looks toward Walter's empty patch at weight 0.5.
  - He comes back to her eyes 1.3 s later.
  - Edith's eyes come up to his 0.4 s into the line (~94.0 s), lids at 1.05, searching his face.
- **Look away to deflect.** Edith looks out at the empty square (3.14, ~127.5 s) just before "The minister came twice". Her eyes don't come back for the rest of the shot.
- **Look down to confess, up to test.** She says "I don't want it fixed" looking down toward the loaf in her lap. Just before "Isn't that awful?" (3.13, ~124.3 s), her eyes come up toward his, at weight 0.8. Her head turns 8°, and her lids are uneven (0.95 and 0.9).
- **Share attention.**
  - In 3.10, Oswald's look follows hers to the tower 0.6 s later, at weight 0.7.
  - In 3.8, Oswald turns his head toward the sign in the window (~96.5 s), and Edith's look follows 0.25 s later (~96.7 s).
- **When someone touches you, watch their hands.**
  - In 3.16 (~144.2 s), Edith watches Oswald's hand as he brushes the snow off her.
  - In 3.17 she watches his hands again as he puts the coat around her and tucks her collar. `hold_eyes` turns off her automatic blinks for 1.5 s. The only blink is the one her look change brings as her eyes drop to his hands (~149.5 s).

### Try this in your own animation

- Turn the body and head about 95% of the way, shared between chest, neck and head. Aim the eyes last, from the final head pose, so they stay locked through nods.
- Blink on big shifts of gaze. Close in about 2 frames and open in 4–5. Keep keyed blinks at least 0.4 s apart.
- Never leave the eyes completely still. Add jumps of 1–2° every 0.5–1.7 s, each taking about one frame.
- Make the upper lid follow the eyes up and down, about half a degree per degree. On a blink, make the lids meet in the middle.
- Decide for each character how much the head may do. A slumped or guarded person looks up with the eyes; a child looks up with the whole head.
- Use eye contact sparingly. Each look change should answer a beat in the dialogue, with stillness in between.

## Facial expression, brows and micro-acting

Nobody sculpted the expressions in *Brindle Cross*. Each look is a mix of the 19 face channels listed in `rigctl.py:FACE_DEFAULT`, set with a one-line call in `shots.py`. For example: `Ed.expr(b + 0.05, brow_in=0.95, brow=-0.15, jaw=0.08, smile=0.0, dur=0.5)`.

### The channels

Each channel is one number per character, with its own track:

- `perf.py:Actor.__init__` builds one `Track` per `FACE_DEFAULT` entry.
- `perf.py:Actor.expr` keys them.
- `rigctl.py:face_to_channels` turns those numbers into bone moves and shape keys.

**Mouth**
- `smile` lifts and widens the corners. There is no frown slider: a negative `smile` is the frown.
- `smirk` makes the smile lopsided. The left side gets smile × (1 + smirk) and the right gets smile × (1 − smirk). On a frown the split is half as strong: × (1 ± 0.5·smirk).
- `press` seals and thins the lips. `pout` pushes the lower lip out.
- `wide` (the EE shape) is driven only by the lip sync; no shot sets it.
- `round` (the O shape) mostly comes from the lip sync too. Shots also use it for a surprised "O", for example Oswald spotting the peel in 2.2 at 46.33 s (`round` 0.9).
- `jaw` opens the mouth 18° per unit.
- `sneer` feeds the `lip_raise` shape, but no shot uses it. `lip_raise` is driven only by the lip sync (the F/V viseme).

**Brows** (three bones per brow: inner, middle and outer; every value is scaled by 2.4 × head scale)
- Each unit of `brow` raises the bones 6.0, 7.0 and 5.0 mm, which makes an arch.
- Each unit of `brow_in` moves them +6.0, +1.8 and −3.2 mm: the inner end goes up and the outer end comes down.
- `brow_asym` adds to the left brow and subtracts from the right.

**Lids**
- Each side has its own channel: `lid_L`/`lid_R` and `lidlo_L`/`lidlo_R`. Shots almost always set both sides to the same value, so "lid 0.95" below means both are 0.95.
- `lidlo` raises the lower lid 14° per unit.
- The upper-lid angles and `blink` are covered under *Eyelids* above.

**Couplings**
- A positive `smile` lifts the lower lids 5° per unit, and the smile shape also raises the cheek (`headgen.py:Head._corners`). Together they make every smile reach the eyes a little.
- During speech, 0.10 × the viseme jaw is added to `brow` (see *Layering speech on the acting*). Loud, open syllables lift the brows slightly.

### Combining channels into readable expressions

A readable expression is three to six channels moving together. The brows show what the character feels, the mouth shows what they choose to show, and the lids show whether they mean it.

One slider can do a lot. Edith's grief brow is mostly `brow_in`: 0.95, with `brow` at −0.15. That moves the inner, middle and outer bones +4.8, +0.7 and −3.8 mm (before scaling), which gives the slanted, worried brow of a real face. Make `brow_in` negative and you get Teddy's affronted frown (`brow −0.3, brow_in −0.75`): inner −6.3 mm, outer +0.9 mm.

| Read | Channels (shots.py) | Where |
|---|---|---|
| Grief | brow_in 0.95, brow −0.15, jaw 0.08, smile 0 (over 0.5 s) | 3.8, 90.6 s, right after Oswald's "It's the small rye." |
| Social mask | smile 0.38, press 0.35, brow 0.5, brow_in 0.35, lid 0.95, lidlo 0.3, head pitch +6 (chin tucks down) | 3.7, 84.1 s, just before "Oh — I'm fine, thank you." |
| Felt laugh | smile 0.75, lidlo 0.8, blink 1.0, jaw 0.12, plus a one-bounce `bounce` | 3.17, 153.0 s, during Oswald's "ridiculous" |
| Wry armour, one brow | smile 0.35, smirk 0.8, brow 0.15, brow_asym 0.8, brow_in 0.2, lid 0.92 | 3.14, 127.8 s, just before "The minister came twice." |
| Puzzled | brow_in 0.5, brow_asym 0.5, smile 0 | 1.6, 36.8 s, the flat-cap man looks at the empty cobbles (no line) |
| Affronted | brow −0.3, brow_in −0.75, press 0.5, smile −0.3, lid 0.85 | 1.4, 22.8 s, Teddy on the narrator's "He is eight." |
| Stern | brow 1.0, brow_in −0.3, lid 1.15, press 0.4, smile −0.1 | 3.16, 145.4 s, just before "Mr. Bunce. No." |
| Startle | brow 0.9, lid 1.25, jaw 0.25, smile −0.2, in 0.06 s | 2.1, 42.3 s, the CLONG |

The mask and the laugh both smile, and viewers judge sincerity by the eyes:

- The mask keeps the lids nearly open (0.95), seals the lips and *raises* the brows ("how kind, no thank you").
- The laugh closes the eyes.

In the wry look, the smirk sends the smile to one side: the `smile_L` key gets 0.63 and `smile_R` gets 0.07. The brow asymmetry puts one brow at +0.95 and the other at −0.65.

### Keeping neutral from reading as a smile

**The neutral leans down.**
- `headgen.py:Head.mouth_params` adds `corner_rest` (1.0; no character changes it) to both frown sides. It does this for every surface it builds, including the rest mesh and all shape keys.
- In head space (before head scale), a corner drops 9 mm per unit of frown and rises 8 mm per unit of smile. So smile = 1 only brings the corners back to about level.
- A smile still reads, because the corners also widen 7 mm and the cheeks and lower lids rise.

**Speech never smiles.** The speech code in `perf.py:evaluate` never touches `smile`. The `wide` key only stretches the mouth sideways and thins the lips (`sx 1.18, lip_up 0.75, lip_lo 0.8` in `Head.build`). An "ee" sound stretches the mouth without turning into a grin.

**Smiles are zeroed on purpose.**
- A track holds its last value until a new key arrives (`perf.py:Track`), even across cuts. Without a reset, a smile from an earlier beat would linger into the next one.
- So story turns set `smile=0.0` explicitly: for example Edith in 3.8 and 3.18, and Oswald in 3.19 and 3.21.
- Faces that must read as not smiling get small negative values: Edith is at −0.15 in 1.1 and −0.25 in 3.20.

### Timing against the line

The face moves first, the words confirm it, and the face settles afterwards:

- Keys lead the audio by roughly 0.25–1 s.
- Changes land on the word that matters.
- Settles come 0.1–0.35 s after the line ends.

`film.py:Film.say` returns each line's (start, end), so every key is written relative to the words.

**Anticipation**
- 3.7: the mask snaps on at 84.11 s over 0.2 s. The audio starts at 84.36 s and "Oh" comes at 84.54 s.
- 3.8: the grief brow starts at 90.62 s, about a second (1.05 s) before the audio of "...That was Walter's."

**On the word**
- 1.4: the affronted brow is keyed at `b − 0.45` = 22.80 s. With its 0.25 s ease, it lands inside "eight" (22.92–23.48 s).
- 3.9: Oswald freezes at 104.85 s (smile 0, brow 0.3, lid 1.12, over 0.12 s). It lands on "you", just before Edith's "lean".
- 3.9: his grin (smile 0.7) starts to soften at 108.49 s, as "never" ends and "fixed it" begins. Over 0.6 s it goes to smile 0.25, brow_in 0.65.

**Hold, then slip**
- 3.14: a 9° shrug starts on "Both" (131.48 s).
- 0.1 s after "Both times" ends, the armour drops over 0.6 s:
  - The smile falls from 0.35 to 0.1.
  - The smirk and the brow asymmetry both fall from 0.8 to 0.2.
  - `brow_in` rises from 0.2 to 0.5.
- The shot ends just as the slip finishes.

**Listener lag**
- 5.2: Edith's smile (0.55, smirk 0.3) starts at 202.06 s, at the tail of her own "Congratulations". Teddy beams 0.25 s (6 frames) later.

**Clearing the lip seal**
- Because `perf.py:evaluate` takes the larger of the expression's press and the lip-sync press, a held press would keep the lips shut through the line.
- Shots release it as the line starts (3.13, 3.18).
- They leave it on when the character should talk through tight lips:
  - Edith's mask (0.35)
  - her stern "Mr. Bunce" (0.4)
  - "You eat too, Oswald." in 3.21 (0.25)
  - "Congratulations." in 5.2 (0.15)
  - Teddy's "I'm Teddy. I'm nearly nine.", keyed with press 0.2

### Easing: one curve, many durations

`Actor.expr` eases with smootherstep (6u⁵ − 15u⁴ + 10u³), which starts and stops at zero speed. Each new key blends from wherever the face is at that moment (`Track._sort` stores start values), so an interrupted change never pops.

No `expr` call in `shots.py` changes the curve. The duration carries the meaning:

- **0.05–0.12 s, involuntary:** the CLONG (0.06), the fall (0.08), the tremble (0.05), the swallow press (0.08–0.1).
- **0.15–0.35 s, social choices:** the mask (0.2), the eyebrow flourish in 3.17 (0.15), the sheepish grin in 3.9 (0.35).
- **0.5–1.0 s, feelings seeping in:** the grief brow (0.5 in 3.8, 0.8 in 3.20), the leftover laugh giving way to the grief brow at the start of 3.18 (0.7), the grin draining in 3.15a (1.0).

### Micro-acting

**The chin tremble and the tear (3.20, from 161.42 s)**

1. At 161.72 s her eyes close (blink 1.0 over 0.6 s). The grief brow comes in (brow_in 0.95, brow −0.1, smile −0.25 over 0.8 s). Over the same 0.8 s her look settles on a spot about a metre in front of her at knee height, and `head` pitch goes to −4, which lifts the chin a little against the downward look. `hold_eyes` stops auto-blinks for the whole shot, and the blink that a `look_at` normally adds is removed (`Ed.blinks.pop()`), so the slow close is the only lid movement.
2. At 162.42, 162.54 and 162.67 s, three keys 3 frames apart go press 0.5, then pout 0.6 with jaw 0.03 (0.5°), then press 0.5 again. Each change takes 0.05 s.
   - `pout` pushes the lower lip out (`lip_lo 1.6`) and `press` pulls it in.
   - Alternating them reads as a trembling chin, although the rig has no chin control.
3. At 162.80 s she stops it: press 0.65 with pout 0.15, reached in 0.12 s.
4. At 162.97 s it releases over 0.12 s, 0.05 s before the hushed line starts at 163.02 s. The breath that `Film.say` places 0.35 s before every hushed line plays here at 162.67 s, on the last tremble.

The tear follows rules:

- It is the only tear in the film, and she never wipes it.
- No music plays under it: no cue runs between 123.1 s and 168.6 s.
- The framing (setup D) keeps its whole path above the subtitles.

In code (`shots.py:tear_fn`, `make_tear`):

- **Shape and path.** The tear is a droplet with half-axes of 2.6 × 1.8 × 3.6 mm. It follows 12 points snapped just in front of the skin, from under her left eye to the corner of her mouth. The head bone carries it every frame.
- **Welling.** It starts at 164.27 s, on "since", and grows from 5% to full size over 0.9 s. It is full at 165.17 s, as "April" ends.
- **Running.** It runs down with an ease-in-out over about 2 s (165.17–167.22 s) and stretches to 1.3× along its length. Over its last 0.6 s it shrinks to 40%.
- **Material.** Roughness 0.02, transmission 0.6, a clear coat and a faint emission of 0.25.

**The swallow** (the screenplay asks for "a 4-frame press with a small head dip")
- In 3.9 at 110.24 s, 1.15 s after "He loved that you never fixed it.", press goes to 0.7 in 0.08 s.
- It holds about 0.09 s, then releases over 0.12 s from 110.41 s.
- A 4° head dip plays with it as a 0.35 s pulse.

**The two-stage drain (3.15a)**
- At 135.21 s, Oswald's performer grin drops about halfway in 0.3 s: smile 0.75 to 0.35, brow 0.85 to 0.4.
- From 135.56 s it drains to zero over 1.0 s (brow_in rises to 0.55) while his hand comes down from the hat brim.
- Faces seldom let go in one move.

**Thinking (3.12)**
- From 119.28 s his eyes make the five counting darts described under *Saccades*.
- At 119.52 s his brows rise (brow 0.55, brow_in 0.4).
- At 120.07 s they fall into grief (brow −0.1, brow_in 0.75) and his lips part (jaw 0.06). That is 0.55 s before "...Thirty-one Sundays."

**The held breath**
- There is no breath-hold control. The idle breath keeps cycling every 4.3 s (`perf.py:evaluate`).
- Stillness does the work instead: parted lips, no idle blinks, no new keys.
  - In 3.8 that is jaw 0.08 plus `hold_eyes` for 1.2 s after "It's the small rye."
  - `hold_eyes` blocks only the random blinks. The blink that every `look_at` adds still fires, so she blinks once as her eyes drop to the loaf (90.64 s), then holds still.
- Then comes a release:
  - In 3.8 you hear it: the breath sound before her hushed "...That was Walter's." plays at 91.32 s.
  - Oswald in 3.9 gets a visible one: a `breath_pulse` at 109.19 s and an exhale sound at 109.44 s.
  - Edith gets a `breath_pulse` at 165.21 s, after her hushed line in 3.20.

### Try this in your own animation

- Decide every smile with the eyes. A smiling mouth with raised brows and open lids reads as polite. The same mouth with the lower lids up and the eyes closing reads as felt.
- Bias the neutral mouth slightly down and check it with the sound off. If neutral looks pleasant, every sad beat will look faintly happy.
- Key the face 0.25–1 s before the line, land the change on the one word that matters, and settle after the audio ends. Let a listener's reaction trail the speaker by a few frames (Teddy trails Edith by 6 frames in 5.2).
- Keep one ease curve and let duration carry the meaning: 1–3 frames for involuntary moves, 4–8 for social choices, 12–24 for feelings.
- At the emotional peak, remove motion: no idle blinks, no new keys, lips slightly parted. Release it with a breath.
- Release lip-seal controls as the line starts so they don't fight the lip sync, unless the character should talk through tight lips.

## Body language and staging for conversation

Oswald says nothing until 89.3 s ("It's the small rye."), so for most of the film his body does the talking. Every acting choice below is a call on an `Actor` (perf.py) made inside a shot function. The staging notes at the end are camera calls. There are two kinds of motion:

- **Attitudes that hold.** `head()`, `chest()`, `tilt()` and `shoulders()` write to a `Track`. The value eases to the new pose (smootherstep, the default `'inout'` curve in `perf.py:ease`) and stays there. `posture()` works the same way for the whole body: it adds an entry to a posture list, and `Actor.body_pose` cross-fades into it with the same easing. A tilt is a state of mind, so it holds.
- **Beats that return.** `nod()`, `shake()`, `bounce()` and `breath_pulse()` add a `Pulse`, a one-off curve that starts and ends at zero, layered on top of the attitude. `shrug()` is also a beat. It uses the collarbone track instead: up over 40% of its duration, a hold, then down over the remaining 60%.

### Postures: the silhouette reads before the face

- **Clown stand** (`perf.py:P_stand`, toes splayed 24–26°, knee 0.2–0.25): toes out, knees soft.
  - A stoop is added only for his entrance (stoop 6 in 1.6) and for the encore (stoop 4 in 4.1).
  - This is his default from 1.6 (32.5 s) until 3.5, and again from 4.1. He is sitting on the cobbles after his fall in 2.3–2.4.
- **Plain stand** (splay 4, knee 0, stoop 0): toes almost straight ahead and legs straight, an ordinary man. First seen in 3.5 (75.7 s).
  - The foot `width` is 0 in both stands, so "feet together" here means the toes turn in, not that the feet move closer.
- **Lean, keep the eyeline.** `P_stand` spreads `lean` as hips −0.3, spine +0.5, chest +0.5, neck −0.4, head −0.3.
  - These sum to zero, so the torso tips while the head stays level.
  - Oswald's signature lean uses it: lean 16, toes 0.8, held 16 frames (2.3 at 49.8 s, 4.2 at 183.3 s).
- **Against the wall** (`P_sit_wall`, pelvis −62°, collarbones dropped 4°; `shots.py:edith_base` passes knees 0.95 and hands on knees): small, closed, holding herself together.
  - Edith never leaves it, and her breathing is scaled to 0.8 (`film.py:Film.__init__`).
  - Her head rests on the brick, so her upward looks are carried mostly by the eyes (`look_up_max` 14°; see *A look is a target*).
  - When the script wants her head up anyway, it adds the pitch explicitly: `head(pitch=−17)` in 3.10.
- **Kneel** (`P_kneel`, right knee down, lean 8): coming down to her level reads as respect.
  - It takes 0.95 s (3.6, 80.3 s).
  - Then he shuffles in on the knee, a 0.65 s glide from 81.3 s, to about 0.6 m from her, on the diagonal.
- **Back on the heel** (`P_sit_heel`: the kneel at lean 2, hips 10 cm back and 12 cm lower, spine −4°): smaller and off duty. The code comment says "suddenly half his size".
  - He rocks back into it just after his button pings off (3.16, 147.4 s) and returns to the kneel 0.5 s later.
  - He settles into it once the coat is on her (3.17, 150.9 s) and stays there until 3.21, where he comes back up onto the knee (167.9 s) to reach for her shoulder.

### Never a statue: breathing and idle sway

Every frame, `perf.py:evaluate` adds three motions to everyone:

- **Breath:** a 4.3 s cycle, scaled by the actor's `breath` value. The chest pitches ±0.9°. The neck counter-rotates 0.5°, cancelling about half of that so the head moves less. The collarbones lift 0.8° on the in-breath.
- **Hip drift:** ±4 mm side to side, on a 6.7 s period.
- **Head drift:** about ±0.3° of yaw and ±0.2° of roll, on a 5.3 s period.

The periods share no simple ratio, so the loop never shows.

Hip and head drift are offset by the length of each character's name: the hip phase is `len(name)` radians and the head phase is `1.3 × len(name)`. This trick has two flaws:

- "edith", "teddy" and "tomas" all have five letters, so those three drift in exact step, including Edith and Teddy sitting side by side in 5.2.
- The breath phase is effectively not offset at all (a random 0–0.01 rad), so everyone breathes in unison.

In your own rig, give each character an independent random phase.

`breath_pulse()` adds a deliberate breath: 2.5°×`amt` of upper-body lift, split 40% spine and 60% chest. In 3.6 (79.1 s), Oswald braces himself before kneeling with a breath of amt 2.2. Separate `shoulders()` calls take his shoulders from −9° up to +6° and back to −9°, and an exhale sound plays at 79.6 s.

### Head and shoulders: size sets the register

- **Size.** Teddy nods 13°, twice, after the label corrects his age (24.3 s). That size reads as a child insisting. In the quiet scene (3.7–3.19), nods are 3–7°.
- **Shrugs.** Edith's shrug on "Called me Ethel. Both times." is amt 9 with a 0.15 s hold, starting at 131.5 s (3.14). The screenplay asks for it to be "like a weather report".
- **Shakes.** `shake` is windowed by `sin(πu)`, so it starts and ends at rest.
- **The head answers before the voice.** Oswald's "No." starts at 126.07 s, and his single 5° shake starts 0.05 s earlier. Edith's shoulders then drop 7° and stay there (126.9 s), which reads as relief (3.13).
- **Point with the head when the hands are busy.** On "before he'd paid", his right hand is still holding the loaf out to her. His head turns 18° (roll 8°) toward the bakery card, and she looks there 0.25 s later (3.8, 96.5 s).
- **Shoulders join big looks.** Every `look_at` already turns the chest 18% of the yaw. For the widest looks, add a chest turn by hand, like Oswald's `chest(yaw=−25)` in 3.21 (see *A look is a target*).

### Hands: choose what the hand is attached to

`gesture(t, side, (space, pos, fingers_dir, back_dir))` accepts world, chest, head, neck, spine or hips, or raw armature coordinates. The film uses four of them:

- **world** is for touching people or the set.
  - Oswald offers the bread palm up (back of the hand pointing down, curl 0.22) at a fixed point in front of Edith (3.6, 81.7 s).
  - His hand lands on her shoulder at 168.6 s, the moment the piano enters (3.21).
- **chest** is for carried things: the loaf in both hands, the lapels, juggling. They ride along with breaths, bows and walks.
- **head** is for anything at the face. His finger to his lips (1.6, 38.1 s) stays on the lips through the head shake that follows at 38.5 s. The hat tip also uses it.
- **hips** is for resting. `osw_rest` puts both hands on his raised knee while he listens.

The hat tip (`shots.py:tip_hat`) is a timed combination:

1. The hand reaches the brim at 30% of the duration.
2. The hat lifts 3.5 cm and dips 18°, reaching the full lift at 50%, and a 7° nod rides on the lift.
3. The hand lets go from 80%. The hat comes back down from 75%.

He tips it to the flat-cap man (35.0 s), then to the empty cobbles where Walter stood (36.5 s). For the second one he looks at a point 1.62 m up: a standing man's head height.

Rise fast, fall slow. In 3.15a ("He calls me Oscar, so—"), two fingers rise to the brim in 0.55 s. Edith's line starts 2 frames before his ends (`say('E13', b − 2/24)`), so she cuts him off. His hand then sinks to his knee over 1.0 s while the smile drains over the same 1.0 s.

### The turn: clown waddle vs "a man, not a clown" (3.5)

The screenplay calls this "the most important body-language note in the film." In `perf.py:Walk.body`, the walk's side-sway (in metres) drives a side-to-side hip roll. With `style='waddle'`:

- The roll factor is 3.0 instead of 1.2, so the same sway produces 2.5 times the roll.
- The hip twist is halved, to 3° instead of 6°.

| | Clown waddle (1.6, 32.6 s) | Man's walk (3.5, 76.9 s) |
|---|---|---|
| Stance | splay 26°, knee 0.25, stoop 6 | splay 4°, knee 0, stoop 0 |
| Step length / time | 0.38 m / 0.24 s | 0.45 m / 0.42 s |
| Bob / side sway | 0.028 / 0.024 m | 0.012 / 0.008 m |
| Peak hip roll | ~4.1° | ~0.55° |
| Hip twist (chest counters ×1.4) | 3° | 6° |
| Arm swing | 0.10 m (left hand; the right hand holds the twirling cane) | 0 (hands on the loaf) |
| Footstep sound spacing | 0.36 s | 0.48 s |

3.5 changes one part at a time, with the face nearly still:

1. He looks toward Edith (75.0 s): head and eyes together at look weight 0.7 over 0.8 s. His brows draw in (brow_in 0.45), and the sideways eye offset resets to 0. That offset was 28° from 3.1, already eased down to 10° in 3.4.
2. His toes turn in from 26° to 4° and his knees straighten (0.2 → 0) over 1.1 s (75.7 s).
3. His shoulders drop 9° (75.9 s).
4. The loaf goes into both hands and the cane goes under his arm (76.0–76.1 s).
5. Then he walks (76.9 s).

The change starts earlier, in 3.1:

- On "Walter's wife", his waddle shrinks before it stops. From 65.3 s the stride goes 0.30→0.26, the sway 0.022→0.014 and the bob 0.026→0.018.
- On "first name" he freezes mid-bite (66.7 s). His jaw closes halfway onto the crust, and only his eyes move (see *A look is a target*).

In 4.1 the waddle comes back with his chest puffed out (`chest(pitch=−8)`, walk from 180.3 s). The screenplay says it is "switched back on": the clown is now something he chooses to be.

### Listening is acting

- **React to content, not constantly.** While Oswald talks about Walter (3.8), Edith:
  - looks up to his eyes (94.0 s)
  - gives a 4° double shake with a small smile (94.9 s)
  - follows his head to the card (96.7 s)
  - laughs through her nose (97.5 s)
- **Freeze, then let go.** Caught out by "He said you lean" (3.9), Oswald freezes: smile gone, lids wide (104.9 s). He blinks twice (105.0 and 105.35 s), then breaks into a sheepish grin and dips his head (pitch 10, roll −5, 106.1 s).
- **A speaker's body leads their own line.** Edith's teasing −9° tilt comes 0.3 s before her "He said you lean". Oswald's 6° nod comes 0.45 s before "Edith." (3.19, 159.7 s).
- **Mirror.** Teddy sits beside Edith in `sit_wall` with her exact parameters (5.2, 195.1 s). Only his hands differ: a `gesture` places them separately.

### Staging and camera

- **Camera height is relationship.** 3.3 shows Edith from 1.45 m above the pavement, looking down at her. 3.6 (setup A) drops to 0.80 m. Per the screenplay, this is the first time the camera sits at her seated eye level. Setups B–E sit at 0.90–0.95 m.
- **Setups** (`shots.py:SETUP`, `cam_setup`):
  - **B:** two-shot, both faces three-quarter, 22 mm at f/4. Used for 3.9 and 3.10, and for the touches: snow brushed off (3.16), the coat (3.17), the hand on her shoulder and the crust handed back (3.21). The loaf handover itself (3.8) is on C.
  - **C:** over Oswald's shoulder, 60 mm at f/2.2. Used for her reactions with him in frame (3.7, 3.8, 3.13, 3.15b).
  - **D:** her close-up, 78 mm at f/2.2 (3.14, 3.18, 3.20).
  - **E:** his close-up, 60 mm at f/2.4 (3.12, 3.15a, 3.19).
  - D and E together carry the exchange of names (3.18–3.20).
- **Heads placed, mouths clear.** Setups C, D and E aim 10, 15 and 12 cm below the eyes.
  - That puts the eyes high in frame and keeps the mouth above the subtitles, which sit between 68% and 74% of the way down the frame (subs.py).
  - Setup E is also aimed 10 cm toward her, to leave lead room.
- **Cheat eyelines.** In 5.2 both faces open to the lens and it still reads as eye contact. Teddy looks 30 cm toward the camera from her eyes, and Edith looks about 60 cm toward it from his (see *Eyeline cheats*).

### Try this in your own animation

- For each move, decide whether it is an attitude that holds (tilt, lean, dropped shoulders) or a beat that returns (nod, shake, shrug, sigh).
- Show an inner change in the walk before the face. Turn the toes in, cut the side sway by two-thirds, lengthen the step and slow the cadence, and keep the hands still.
- Attach each hand to the right thing: the world when touching, the chest when carrying, the head at the face.
- Animate listeners when the speaker says something that matters, and start a speaker's nod, shake or tilt 0.05–0.5 s before their own line.
- Use idle cycles with unrelated periods (breath around 4 s, sway around 5–7 s), and give every cycle an independent random phase per character. Here, phases taken from name length made three characters sway in unison.
- Put the camera at the eye level of the person the scene is about, and cheat two-shot eyelines a few tens of centimetres toward the lens.

## Cheat sheet

| Area | Parameter | Value |
|---|---|---|
| Voice | Speaking speed | 0.82–1.05 (defaults 0.88–1.05; only Teddy above 1.0) |
| Voice | Adult pitch shift (formants kept) | −0.5 to −1 semitone |
| Voice | Hushed line | 0.05–0.06 slower; −4 dB shelf at 6 kHz; placed −8 dB; exhale 0.35 s before at −14 dB; mouth ×0.75 |
| Lip-sync | Median phoneme symbol | 54 ms (≈1.3 frames at 24 fps) |
| Lip-sync | Coarticulation width (gaussian sigma) | max(45 ms, 0.75 × phoneme duration) |
| Lip-sync | Relax in gaps | divide by max(total weight, 0.6) |
| Lip-sync | Stressed-vowel jaw | ×1.25 |
| Lip-sync | p/b/m closure | press 1.0, jaw −85%, 15 ms before to 10 ms after; applied again after smoothing |
| Lip-sync | Loudness gate | clip(1.6 × loudness, 0, 1)^0.7; fully open above 0.625 |
| Lip-sync | Speech added to acting | jaw 0.95, round 0.8, wide 0.7, lip_raise 0.5; brow +0.10 × jaw |
| Face | Jaw rotation | 18° per unit; typical line peak ≈7.5°, max 12.3° |
| Face | Brow per unit (inner / mid / outer) | 6.0 / 7.0 / 5.0 mm, × 2.4 × head scale |
| Face | brow_in per unit (inner / mid / outer) | +6.0 / +1.8 / −3.2 mm, × 2.4 × head scale |
| Face | Neutral corner bias | corner_rest 1.0; 9 mm drop per frown unit, 8 mm rise per smile unit |
| Gaze | Look split, yaw | chest 18%, neck 32%, head 45%; eyes do the rest |
| Gaze | Look split, pitch | neck 35%, head 60% |
| Gaze | Eye range from the posed head | ±35° yaw, ±30° pitch |
| Gaze | Head look-up limit | 35° default; Edith 14°, Teddy 50° |
| Gaze | Look travel time | glance 0.2–0.3 s; conversational shift 0.4–0.5 s; heavy 0.6–0.8 s |
| Gaze | "Looking toward" weight | 0.5–0.8 |
| Saccades | Interval / size / duration | every 0.5–1.7 s; SD 1.6° yaw, 0.9° pitch; 0.05 s |
| Blinks | Shape | close 0.07 s, shut 0.04 s, open 0.19 s (0.30 s total) |
| Blinks | Rate | every 2.2–5.0 s (≈17/min), plus one 0.02 s into every look change (3.2 drops Tomas's by hand) |
| Blinks | Minimum gap | 0.35 s (key at least 0.4 s apart) |
| Blinks | Slow "thought" blink | close 0.15–0.3 s, open 0.18–0.45 s |
| Lids | Upper lid follows gaze | 0.50° per degree down, 0.65° per degree up, × openness (0–1) |
| Lids | Lower lid follows gaze | 0.3° per degree down, 0.2° per degree up, × openness (0–1) |
| Lids | Upper-lid travel | 46° closed at openness 0; +30° per unit above 1; +11° seal below openness 0.25 |
| Lids | Lower-lid raise | lidlo 14° per unit; blink +8°; smile +5° per unit |
| Timing | Face leads the audio | 0.25–1 s |
| Timing | Settle after the line | 0.1–0.35 s |
| Timing | Listener reaction after the line it answers | mostly 0.05–0.45 s |
| Timing | Speaker's nod, shake or tilt before their own line | 0.05–0.45 s |
| Timing | Listener lag behind speaker's smile | 0.25 s (6 frames) |
| Easing | Expression durations (smootherstep) | involuntary 0.05–0.12 s; social 0.15–0.35 s; feeling 0.5–1.0 s |
| Body | Breath | 4.3 s cycle; chest ±0.9°, neck −0.5°, collarbones +0.8° |
| Body | Idle sway | hips ±4 mm on 6.7 s; head ±0.3° yaw, ±0.2° roll on 5.3 s |
| Body | Nod size | 3–7° in the quiet scene; 13° for a child insisting |
| Body | Walk: clown vs man | step 0.38 m / 0.24 s vs 0.45 m / 0.42 s; sway 0.024 vs 0.008 m |
| Staging | Camera height at her eye level | 0.80 m (vs 1.45 m looking down) |
| Staging | Close-up aim | 10–15 cm below the eyes; subtitles at 68–74% down the frame (the final shot's narration sits high, bottom at 37.5%) |
| Staging | Two-shot eyeline cheat | toward the lens: in 5.2, 0.30 m for Teddy and 0.60 m for Edith; 0.53 m for Edith in setup B (`ED_B`) |

## Where to look in the film

1. **2.1, ~42.3 s: the CLONG.**
   - Oswald's startle hits in 0.06 s (brow 0.9, lid 1.25, jaw 0.25).
   - At ~42.4 s Edith gives one startled blink and a 3° head flinch, without looking up.
   - The crowd laughs with crinkled eyes (lid 0.6, lower lid 0.7, smile 1.0) at ~42.5 s.
   - *Techniques:* involuntary timing; saving eye contact.
2. **3.1, ~66.7 s: the freeze.**
   - On "What's her first name?" Oswald freezes mid-bite. His head stays on its target, and only his eyes slide 28° toward the voices behind him, in 0.25 s.
   - Auto-blinks are off for 4 s, but the look reset still brings one blink.
   - *Techniques:* eyes before the head; stillness.
3. **3.3, ~70.2–71.3 s: a thought landing.**
   - Tomas fails to remember her name. Edith's lids ease to 0.98 and her inner brows lift (brow_in 0.35).
   - At ~70.8 s she gives a slow blink (0.3 s to close, 0.45 s to open). Her gaze never leaves the cobbles.
   - The camera looks down at her from 1.45 m.
   - *Techniques:* slow blink; camera height.
4. **3.5, ~75.0–76.9 s: "a man, not a clown".**
   - He looks toward her (75.0 s), his toes turn in from 26° to 4° (75.7 s), his shoulders drop 9° (75.9 s) and the loaf goes into both hands.
   - Only then does he walk: 0.45 m steps, 0.42 s each, almost no sway.
   - *Technique:* the inner change shows in the body before the face.
5. **3.7, ~82.7–84.5 s: Edith's first look.**
   - Her first `look_at` of the film goes to the loaf (82.7 s, over 0.7 s), then to his eyes (83.6 s), with her lids widening to 1.12.
   - At 84.11 s her social mask snaps on (smile 0.38, press 0.35, raised brows, lids 0.95) before "Oh — I'm fine, thank you." at 84.36 s.
   - *Techniques:* saving eye contact; a polite smile versus a felt one.
6. **3.8, ~89.1–91.7 s: first words, then grief.**
   - Oswald's inner brows lift 0.2 s before "It's the small rye." (89.3 s).
   - At 90.6 s Edith's eyes drop to the loaf (one look-change blink), and the grief brow and parted lips come in.
   - She holds still with no idle blinks, a breath is heard at 91.3 s, and the hushed "...That was Walter's." follows at 91.7 s.
   - *Techniques:* anticipation; the held breath; speech layered over a held expression.
7. **3.9, ~104.85–110.4 s: caught out, then the swallow.**
   - Edith tilts −9° 0.3 s before "He said you lean". Oswald freezes on "you" (smile 0, lids 1.12), double-blinks at 105.0 and 105.35 s, and breaks into a sheepish grin with a head dip at 106.1 s.
   - His grin softens on "fixed it" (108.49 s). After the line he swallows (press 0.7, 4° dip) at 110.24 s.
   - *Techniques:* listening; reacting after the line ends.
8. **3.12, ~119.3–120.6 s: counting.**
   - His eyes make five keyed darts 0.2 s apart (−4°, +3°, −3°, +4°, −2°) while his brows rise.
   - His brows then fall into grief and his lips part (jaw 0.06), and his look goes to her eyes (~120.4 s) before "...Thirty-one Sundays." (~120.6 s).
   - *Techniques:* hand-keyed saccades; face before the voice.
9. **3.13, ~122.4–126.9 s: confess, test, relief.**
   - Edith presses her lips (0.6) and nods 7°. She releases the press as "I don't want it fixed." starts (~122.9 s), looking down.
   - Her eyes come up to his before "Isn't that awful?" (~124.3 s), with uneven lids (0.95 / 0.9).
   - His single 5° shake starts 0.05 s before his "No." (126.07 s), and her shoulders drop 7° in relief (126.9 s).
   - *Techniques:* look down to confess, up to test; head before the voice; releasing the lip seal.
10. **3.14, ~127.5–132.8 s: armour, then the slip.**
    - She looks away to the empty square (127.5 s) and puts on the wry one-brow look (smirk 0.8, brow_asym 0.8) before "The minister came twice."
    - A 9° shrug starts on "Both" (131.48 s). Then the armour slips over 0.6 s (smile 0.35→0.1, brow_in 0.2→0.5) as the shot ends.
    - *Techniques:* looking away to deflect; hold, then slip.
11. **3.20, ~161.7–167.2 s: the closed eyes and the tear.**
    - Her eyes close on the blink channel, so the lids seal.
    - Her chin trembles in three beats 3 frames apart (162.42–162.67 s), she presses it still (162.80 s), and releases at 162.97 s, just before "Nobody's said it since April." (163.02 s).
    - The tear wells from 164.27 s and runs from 165.17 to 167.22 s, with no music.
    - *Techniques:* micro-acting; removing motion at the peak.
12. **5.2, ~195.8–202.3 s: the bench.**
    - Teddy (195.8 s, weight 0.9) looks 0.30 m, and Edith (195.9 s) 0.60 m, in front of the other's eyes, so both faces open to the camera. Teddy mirrors her `sit_wall` pose.
    - She says "Congratulations." through slightly tight lips (press 0.15). Her smile starts at 202.06 s, and Teddy beams 6 frames later.
    - *Techniques:* eyeline cheat; mirroring; listener lag.
