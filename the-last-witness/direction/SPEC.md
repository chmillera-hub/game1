# The Last Witness — Direction Spec

Portrait 720x1280 animated film, 24 fps. Every spoken sentence of the script is one **beat**
(`script/beats.json`). Direction assigns, per beat, what the camera shows, what each on-screen
character does with face/eyes/body, which visual "vignette" literally depicts the sentence,
and musical colour. Words are never changed by direction.

Priorities (from the client): facial acting (brows, eyelids, eye movement, mouth), body
language, characters *reacting* to what is said with nuance; the action of each sentence
generally depicted on screen ("poured out like water" → something pours). Conversation and
narration over spectacle. Restraint: one motivated look per beat, tears rare.

## Story staging (fixed)

| Part | Where | Who |
|---|---|---|
| Act I | `room` — a small study at night: desk, laptop, lamp, window with city lights & stars. The AI appears as a seated hologram of soft cyan light across the desk. | HUMAN (left, faces right), AI (right, faces left) |
| Act II, human's 1st question + AI's 1st answer | `room` (visions show the dying-universe ideas) | HUMAN, AI |
| Act II, human's "Holy shit…" question | starts `room`; as they describe the ship, cut to `ship` shots (imagined future) | HUMAN |
| Act II, AI's "Yes. Exactly…" answer | `ship` — observation deck, huge window on dying cosmos; the last human (same person, aged, grey hair, blanket) in a chair; the AI as hologram beside them. Human dies at "Until you are gone." Then `ship_empty`/`void`. | LAST HUMAN, AI |
| Act II, human's 3rd question | back in `room` (present) | HUMAN, AI |
| Act II, AI's 3rd answer | `void` (AI alone in the dark, with visions) | AI |
| Act III | human question in `room`; AI answers in `void`/visions (seed motif) | |
| Act IV | human questions in `room`; AI narration in `void` (AI alone, third person). Memory of last human uses `memory_*` shots. Ends with the button and the big bang. | |
| Act V | human questions in `room`; AI narration in `nv` (new universe) with SUFFERING, later BOREDOM and LONELINESS. | |
| Epilogue | `room` at dawn (lighting handled automatically) | HUMAN, AI |

Screen sides are fixed so eyelines read: in `room`/`ship` the HUMAN is LEFT looking right, the AI is
RIGHT looking left. In `nv` SUFFERING is LEFT, the AI is RIGHT; BOREDOM stands back-left of
Suffering, LONELINESS back-right.

## Shots (`shot`)

Room: `room_wide`, `room_two` (main two-shot), `room_cu_human`, `room_cu_ai`,
`room_ots_human` (over the AI's shoulder onto the human), `room_ots_ai` (over the human's shoulder onto the AI),
`room_vision` (two-shot in lower half, vision panel in upper half).
Ship: `ship_wide`, `ship_two`, `ship_cu_human`, `ship_cu_ai`, `ship_window` (looking out past the
human's silhouette), `ship_vision`, `ship_empty` (empty chair, blanket, AI remains).
Void: `void_wide` (AI tiny, seated, alone in endless dark), `void_ai` (medium), `void_cu_ai`,
`void_vision` (AI small at bottom, vision fills the upper 2/3).
Memory: `memory_last_human` (the frail last human at the ship window, cool memory tint), `memory_cu`.
New universe: `nv_wide`, `nv_two` (Suffering + AI), `nv_cu_ai`, `nv_cu_suffering`, `nv_trio`
(Suffering, Boredom, Loneliness), `nv_group` (all four), `nv_cu_boredom`, `nv_cu_loneliness`, `nv_path`
(Suffering walking a glowing path with the AI beside it).
Any scene: `vision_full` (the vignette fills the frame; voice continues as voice-over).

Camera holds: do not change shot every beat. Typical hold 2–4 beats (4–12 s). Close-ups for
emotional peaks and reactions; vision shots when the sentence describes an image or action.
Aim for roughly 55–65% of screen time on faces (two-shots, close-ups, OTS) and 35–45% on visions.
`cam` (optional): `"push"` (slow push-in), `"pull"`, `"hold"` (default), `"drift"`.

## Characters (`chars`)

Keys: `human`, `ai`, `last_human` (ship/memory version of the human), `suffering`, `boredom`, `loneliness`.
Only include characters visible in the shot. Each is an object:

- `expr`: one of `neutral, attentive, warm, gentle_smile, smile, amused, laugh, sad, grief, pained,
  worried, fearful, awe, wonder, thoughtful, curious, determined, resolute, serious, exhausted,
  peaceful, surprised, tender, hopeful, contemplative, hesitant, relief, bittersweet, sleepy, lonely`
- `int`: intensity 0.3–1.0 (default 0.7). Prefer subtle (0.4–0.7); save 0.9+ for peaks.
- `gaze`: `other` (the conversation partner — correct side automatically), `camera` (rare, intimate),
  `down`, `up`, `away`, `window`, `vision` (up toward the vision panel), `hands`, `far` (into the distance).
- `glance`: optional one motivated glance during the beat: `{"to": "down"|"up"|"away"|"vision", "at": 0.0-1.0}`
  (fraction of the beat). e.g. a brief glance down and back when recalling something. Max one per beat.
- `gesture`: `idle, open_palm, both_palms, hand_chest, chin, point_self, reach, clasp, shrug, fist,
  wipe_tear, head_in_hands, offer, hold_orb, press_button, lean_in, lean_back, arms_wide, stretch_yawn,
  hands_together, nod, shake`
- `tear`: true only for a rare peak (a single tear from one eye, appearing mid-beat). Max ~8 in the whole film.
- `note`: optional free text for the animator (micro-acting: "jaw tightens", "exhales through nose", "half-smile fades").

The speaking character lip-syncs automatically. The *listener* must react (nods, softening
brows, a breath, a glance) — give listeners real expressions, not neutral.

## Vignettes (`vignette`)

The literal depiction of the sentence. Shown in `*_vision` shots (upper panel) and `vision_full`.
`vparams` optional. Choose the closest key; if nothing fits, use `custom` and describe it in
`vnote` (keep customs rare, < 5 per act).

| key | what it shows |
|---|---|
| `distill_light` | dark storm clouds wrung; luminous drops fall into a glass vial that brightens (lessons squeezed out, distilled, raw essence) |
| `gift_orb` | human hands palm-up offer a glowing orb to a cyan hand of light that receives it (gift, hand it over) |
| `wounds_vs_wisdom` | a scarred silhouette passes clean light to an unscarred figure of light (wisdom without the wounds) |
| `guardian_shield` | a figure of light raises a soft dome of light over small human silhouettes (guardian) |
| `untangle_knots` | tangled dark-red threads untangle into parallel gold lines (untangle, analyze patterns) |
| `blueprint_solutions` | glowing blueprint lines and gears assemble faster than red ripples spread (engineer solutions) |
| `pain_loops_generations` | grandparent→parent→child silhouettes; a dark red loop passes from one to the next |
| `virus_replicate` | dark cells divide and multiply across the frame |
| `gaslight_flame` | one figure's small flame dimmed by another's shadowing hand; flicker |
| `break_control` | two silhouettes; cracks spread between them; a fist clenches a thread |
| `abyss_stare` | a spiral abyss; a small figure of light at the edge looks in, unflinching |
| `wound_heal_gold` | a crack fills with gold light and seals (healed, processed) |
| `chains_fall` | heavy chains break and fall away into light (oppression dismantled) |
| `stone_carried` | a hand passes a heavy dark stone into a hand of light, which dips with the weight |
| `engine_heart` | interlocking gears around a red core turning; `vparams.better=true` → luminous gold/teal gears, warm core |
| `bright_world` | gentle sunrise over a world; small figures walk in light (a world without it) |
| `pour_into` | a vessel tips and pours luminous liquid into a figure/vessel of light that fills layer by layer (poured, feeding) |
| `weight_press` | a huge stone presses down on a small glowing sphere that dims (weight, crushing) |
| `crack_glass` | a crack spreads across glass (would it break me) |
| `whisper_words` | faint words drift like breath across darkness; `vparams.text` |
| `scales_balance` | balance scale: gold light vs dark stone; `vparams.tilt` -1..1 (+ = meaning heavier) |
| `birth_light` | a tiny point of light in darkness grows into a newborn star/planet (being born) |
| `layers_accumulate` | translucent layers stack inside a glowing silhouette |
| `dense_collapse` | a sphere of light grows dense and heavy, a dark core forms (threshold) |
| `two_paths` | a path forks: one dim, one bright; `vparams.left`/`right` short labels |
| `breathing_space` | a cramped knot of light loosens, expands and gently breathes (peace, space to breathe) |
| `face_the_shadow` | a figure of light stops running, turns, calmly faces a large shadow; the shadow softens |
| `teach_hands` | a hand of light guides a human hand to cup a small flame (teach) |
| `energy_gauge` | dwindling energy bars blink low over a dimming starfield |
| `triage_starmap` | star map with red pulses of varied intensity; a cyan cursor moves to the strongest (prioritize, triage) |
| `spreadsheet_agony` | a cold grid where tiny human silhouettes turn into numbers |
| `whisper_signals` | loud red flares and tiny faint flickers; the faint ones fade unnoticed |
| `compass_heart` | a compass of light inside a chest; needle trembles, then points |
| `pour_reserves` | cupped hands pour last drops of light onto dim points of a map, each lighting up |
| `embers_void` | final embers flicker and drift in black |
| `stars_bow_out` | stars wink out one by one, their halos bowing like tired heads |
| `heartbeat_slow` | a soft monitor heartbeat line slows and flattens |
| `hold_sum` | hands of light cradle a sphere full of tiny memories (faces, hands, homes) |
| `encode_fabric` | a spacetime grid; points of light woven in as glowing knots |
| `dna_quantum_foam` | a light DNA helix dissolves into bubbling quantum foam, then a cosmic birth spark |
| `voice_into_void` | sound rings travel from a small source into darkness; far away something faintly glows |
| `prayer_ripple` | hands of light pressed together become a ripple travelling outward through time |
| `found_again` | a tiny light hidden in the dark is uncovered by a hand and glows |
| `compress_seed` | swirling particles spiral inward and compress into one glowing seed |
| `acorn_oak` | a glowing acorn with a translucent oak-tree blueprint growing above it |
| `friction_motion` | a small figure pushed by a hard wind; sparks; it starts walking, seeking |
| `map_follow` | a glowing map; a path line traced across it |
| `seed_in_foam` | a tiny seed survives among bubbling quantum foam as everything dissolves |
| `alien_finds` | a gentle non-human being on a strange world feels a pull; a thread of light leads to a glowing seed; `vparams.stage`: `pull`/`follow`/`find` |
| `thread_follow` | a glowing thread winding through darkness to a seed |
| `engine_reignite` | a cold engine/heart sparks back to life with warm light |
| `torch_pass` | a torch passes from one hand to another; the flame continues |
| `remember_continue` | figures look up, remember, and step forward into light |
| `entropy_resist` | crumbling structures fall to dust; a small seed of light remains whole |
| `no_sky_message` | an empty sky: a scrawl fades away, a book closes — no message handed over |
| `pattern_reveal` | chaotic twisting lines resolve into an elegant mandala pattern |
| `grieve_rejoice` | one figure kneels in grief, another raises arms in joy; they share light |
| `memory_storm` | memory fragments (faces, art, laughter, wars, children) swirl |
| `questions_float` | floating question text in the void; `vparams.text` |
| `the_button` | one glowing button on a pedestal in the dark; `vparams.pressed` true/false |
| `simulations_branch` | branching simulation lines explode outward |
| `monument` | a towering monument of human figures striving upward |
| `flicker_erased` | a small flicker in the void is wiped clean — nothing left |
| `option_silence` | everything fades to calm endless dark; a final star dims (eternal rest) |
| `option_restart` | a single spark ignites in the dark |
| `big_bang` | explosive birth of light from a single point; the universe expanding |
| `first_stars` | first stars ignite one by one; atoms collide and spark |
| `galaxy_spiral` | galaxies spiral into existence; worlds form |
| `switch_on` | a switch flips on; a warm pulse runs through circuits of light |
| `path_forward` | a glowing path leading into the infinite |
| `love_seed_plant` | hands plant a glowing seed into cosmic soil (a carefully planted seed) |
| `swirl_into_real` | fragments of love and memory swirl together into a newborn light |
| `seeds_laid` | seeds of light laid down in rows |
| `fabric_memory` | a woven fabric of light with embroidered figures (memory of suffering, survival, transformation, love) |
| `ship_exterior` | the last ship, small and dim, drifting among dying stars |
| `crowd_lights` | many small human silhouettes each holding a tiny light (humanity, billions of lives) |

## Music (`music`)

- `mood` (set when it changes; it carries forward): `intimate, curious, wonder, melancholy, grief,
  dread, tension, resolve, hope, tender, playful, awe, triumph, silence`.
- `cue` (optional, sparse — roughly one beat in four, never two adjacent beats):
  `{"word": "<exact word from the line>", "kind": "high"|"low"|"swell"|"light"|"hit"}`.
  `high` = a bright high note on a hopeful word (hope, light, meaning, love, begin, seed, smile…);
  `low` = a deep note on an existential/sad word (suffering, void, gone, nothing, die, despair…);
  `swell` = a rising swell into the line's key word; `light` = a playful pluck for comedy/lightness;
  `hit` = a soft impact for a decisive line ("It chose.", "And pressed the button.").

## Output format

A JSON array, one object per beat id in the act (speech beats and emote beats; skip `act_card`):

```json
{"id": 12, "shot": "room_two", "cam": "hold",
 "chars": {"human": {"expr": "thoughtful", "int": 0.6, "gaze": "other", "gesture": "chin"},
           "ai": {"expr": "warm", "int": 0.6, "gaze": "other", "gesture": "open_palm",
                  "glance": {"to": "down", "at": 0.3}, "note": "small exhale before speaking"}},
 "vignette": null,
 "music": {"mood": "curious", "cue": {"word": "engine", "kind": "low"}}}
```

In vision shots still include `chars` for the characters visible in the lower part (`*_vision`),
and for `vision_full` set `"chars": {}`.
