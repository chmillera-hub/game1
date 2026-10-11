# Audio API: music cues and SFX ("TIREDNESS")

Everything is procedural (numpy/scipy, 48 kHz stereo float32). Files:
`audio/music.py` (cues + the DSP toolkit), `audio/sfx.py` (effects), `audio/mix.py` (final mix).

```python
from audio import music, sfx
y = music.render_cue("ominous", 21.0)          # (round(21*48000), 2) float32, -18 LUFS
y = music.render_cue("reveal:awe=0.58", 24.6)   # options after a colon
text, S = music.describe("chill", 20)           # chord/voicing listing (+ the Score: S.chords, S.events)
x = sfx.render("door_bang", seed=2)             # peak -12 dBFS (+ trim), seeds 0..3 vary
sfx.resolve("bite")  -> "chomp"                 # aliases, "sfx_" prefix, trailing digits ("pop2")
sfx.loop_events("pod_hum", 0.0, 12.0, -6)       # SFX() entries tiling a loopable effect
```

## How the mixer uses them (read this first)

* **Music:** each scene's `music` (script.json) is one cue name. Consecutive scenes with the
  **identical string** are rendered as one seamless `render_cue` call (so `"ominous:turn=0.7"` must
  be spelled the same on every scene of the group). The render starts `music_xfade/2` before the
  scene, typically 0.3 s. Cues are normalized to **-18 LUFS** (plus each cue's `level_db`). The
  mixer then sets the bed 10 LU under the dialogue, ducks 7 dB while anyone speaks, and lifts
  4 dB in long gaps. Per-scene `music_gain` (dB) trims further.
* **Loops/extension:** looping cues are 4/8-bar compositions generated for the requested length
  (10–60 s tested, plus 12 s and 40 s spot checks). Nothing is spliced, so a "loop point" is just
  the next bar, with small per-pass variations. The last `fade_out` seconds fade out.
* **SFX:** `SFX(info) -> [(t, name, gain_db[, pan])]`, scene-local seconds. The mixer gives the
  *n*-th use of an effect seed `n % 4`, so repeated knocks and steps vary automatically. Tails may
  spill 0.6 s past the scene end. Loopable effects ignore the seed so that tiles match exactly.

## Music cues

| cue | character | key / BPM | best scenes | options / variants | dialogue notes |
|---|---|---|---|---|---|
| `chill` | Lo-fi gaming bed. Lazy swung (58%) rootless e-piano 9ths with tape wow, a vibraphone **hook** (F-A-C… rising arpeggio with sighs) and a softer call-and-response in the B half, warm sub, soft brushes (kick, brush taps, swishes). Opens on keys + bass with the hook from t=0; brushes enter at bar 2. | F major colour: Bbmaj9, Am7/D7b9, Gm9, C9sus4/C7b9 · 78 | s01 | - | Vocal band only ~28 %. The hook is a soft vibe in 700–1000 Hz, ducked under lines. |
| `panic` | Frantic comedic chase. Galloping pizz bass with chromatic walk-ups, off-beat pizz chops, **xylophone hook** in bars 1–4 (chromatic descents), a pizz-violin answer in bars 5–6, one bar of air, then a chromatic xylo run + snare roll. Woodblock tick-tock on every beat, kick and snare. | E minor: Em Em C B7 / Em Am F#m7b5-B7 Em-B7 · 160 | s02, s03 | - | Busiest cue. The answer bars thin out for lines; `music_gain` -1…-2 under dense dialogue. |
| `sneaky` | (kept) Cartoon tiptoe: pizz bass, plucked melody, bassoon double, woodblock. | A minor · 104 | s04, s05 | - | Unchanged. |
| `awkward` | Cringe comedy. Staccato **bassoon** ditty, tuba "oom" (often missing its "pah"), pizz plinks, a sad little glock echo of the Ab-G sigh. **Bars 3, 4 and 8 are near-silent; a faint clock ticks in the gaps.** Second time round one entry comes in late. | C major with the minor iv (F→Fm), Dm7-G7 · 90 | s06, s10 | `level_db` -2 (built in) | Very light; the silences are where the lines go. |
| `chaos` | Slapstick action. Galloping 16th low-string ostinato, 3+3+2 **brass stabs**, a brass rip into each cycle, rock drums with tom fills, timpani, crash. | D minor: Dm Bb Gm A7 / Dm Bb Eb-Gm A7 · 150 | s07 | internal peak limiter at -3.5 dBFS | Mostly action; dialogue is short shouts. |
| `tension` | (kept) Pulsing 16th ostinato with a rising filter, computing blips. | A minor · 110 | s08, s11 | - | Unchanged. |
| `corporate` | Cold minimal. Clean filtered **pulse bass** in 8ths, sine-blip arpeggio with ping-pong echoes, clinical 16th hat ticks, an icy glass pad. Unease comes from sus chords, an F-against-E **b6 rub** and a #11; a high glass swell every 4 bars. | A: Asus2, Asus2b6, Fmaj7, Fmaj7#11, Dm9, Esus4, Asus2, E7sus4 · 100 | s09 | `level_db` -1.5 (built in) | Dense dialogue scene: bass sits low and the arp is quiet sine. |
| `ominous` | Sewer. D drone, slow low-string swells over a D pedal (Dm(add9) Bb/D Gm/D Eb/D), distant pipe resonances, bowed-metal whines, **pitched drips** (minor pentatonic), a **heartbeat** pulse. **Warm turn** from `turn` (default 0.66 of the render): Bbmaj7 → C/D → D(add9) (bVI-bVII-I). Drips go major, choir "oo" + warm strings enter, the heartbeat slows and fades, and a celesta plays two "questions" then the creature lullaby. | D minor → D major · 56 | s12 | `ominous:turn=0.7` (fraction of the render; 1 = never); `ominous_dark` (no turn); `ominous_warm` (turn 0.5) | Default fits s12 as mixed (21.1 s render): turn ≈ 13.9 s (form/eyesWide), D major ≈ 17.4 s ("Okay. Hi."). |
| `bond` | Tender lullaby. **Celesta** melody (the creature's theme), warm strings, soft harp arpeggio, sub. Second pass: melody an octave up with a soft violin double. | D: Dadd9 A/C# Bm7 Gmaj7 D/F# Em7 Gmaj7 Asus4-A · 66 | optional (s12 end / s13 calm) | - | Gentle. Use it if a scene wants to switch after the turn. |
| `reveal` | s13 arc **scaled to the render**. (1) Curious walk: pizz walking bass down the line cliché (Dm Dm/C# Dm/C Bm7b5 Bbmaj7 Gm6…), light pizz chords, curious "plink-plink-plink", low strings. The tempo is fitted (~84–105 BPM) so the walk ends on A7sus4→A7 exactly at `awe`. (2) Timpani roll + swell, then the **awe**: a deceptive cadence to **Bbmaj7#11** with choir "ah", full strings, harp gliss, boom. (3) **Sorrow**: Gm9, Dm/F, … A7sus4 with slow strings and a solo violin lament. (4) The **"to be continued" sting**: a soft Bbmaj7#11 (the awe chord returning as a question), celesta arpeggio, violin holding the #11. | D minor · fitted | s13 | `reveal:awe=0.575,sad=0.695,sting=3` (fractions; sting in seconds from the end, max 25 % of the render) | Defaults match s13 as mixed (24.6 s): awe 14.2 s (= "reveal" cue), sorrow 17.1 s ("sad"), sting at the last 3 s ("title"). Built-in peak limiter. Awe is ~4 LU above the cue average (no dialogue there). |
| `doom`, `ai_calm`, `beg`, `heart`, `resolve` | Inherited from the previous film; still render. | | | | |

Measured (30 s renders, cold process): render 0.6–2.7 s (60 s renders 3.6–5.5 s); LUFS -18 (awkward -20,
corporate -19.5); peaks -3.5 to -7.9 dBFS for the new cues. Short-term loudness range in the body is 1–3 LU for the
loopers. Share of energy in 300 Hz–3 kHz: chill 28 %, panic 44 %, awkward 45 %, chaos 26 %,
corporate 45 %, ominous 16 %, reveal 26 %; below 120 Hz ≤ 46 %.

**Suggested `music_gain`** (per scene; it cannot change mid-scene): s01 0, s02–s03 -1, s06/s10 0, s07 0…+1, s09 0, s12 0, s13 0. Use `music_xfade` 0.05–0.2 for
comedic hard cuts (already set in script.json).

## SFX

Level column = loudest 200 ms, K-weighted (LUFS), as rendered at gain 0. Typical one-shots
sit at -19…-24, small foley at -25…-28. "Seeds" = variants across seeds 0–3.

### Doors, impacts, glass
| name | description | dur s | level | aliases |
|---|---|---|---|---|
| `door_bang` | Fist pounding a wooden front door, one hit (repeat with seeds for pounding). | 0.80 | -21 | bang, pound, door, door_pound |
| `knock` | Light knuckle knock ×2. | 0.60 | -27 | door_knock, knock_knock, knuckle_knock |
| `glass_smash` | Window pane breaking + shards tinkling down. | 1.70 | -21 | smash, glass, shatter, window_smash, window_break |
| `glass_crash_big` | Crashing *through* a big window: body hit, huge burst, second break, long debris. | 2.80 | -21 | glass_big, window_crash, crash_through, big_glass |
| `house_rumble` | Room-shaking rumble + house groan + rattling dishes/frames/glass (~1.2 s). | 1.30 | -21 | rumble, quake, house_shake |
| `body_thud` | Heavy body hitting floor/wall (soft attack, cloth, board rattle). | 0.95 | -20 | body, body_fall, fall_thud, wall_thud |
| `ceiling_thud` | Head bonk on the ceiling: hollow drywall knock + plaster tick and flakes. | 0.95 | -21 | ceiling, head_ceiling |
| `bonk` | Cartoon head bonk ("tonk" with pitch drop/wobble). | 0.50 | -22 | head_bonk, conk |
| `impact_heavy` | Huge ground impact: sub boom, crunch, debris, short rumble, then it stops (cut to black). | 1.30 | -18 | impact, land, slam, crash |
| `van_door` | Sliding van door: roll along the track, heavy metal slam, latch. | 1.50 | -19 | van, van_slam, sliding_door |

### The thing (critter), the creature, Impulsivity
| name | description | dur s | level | aliases |
|---|---|---|---|---|
| `scratch_wood` | Small claws scratching wood (3–5 stick-slip strokes). | 1.10 | -28 | claws, wood_scratch, scrabble |
| `scurry` | Tiny claws pattering past, panning L→R (~0.8 s). | 0.95 | -25 | patter, skitter, scamper |
| `critter_squeak` | Small squeak (1–2 chirps, seeds vary). | 0.50 | -22 | squeak, eek |
| `critter_hiss` | Small spitty hiss. | 0.55 | -23 | hiss_small, thing_hiss |
| `chomp` | Cartoon bite: teeth clack + "chmp" pop + tiny crunch, no gore. | 0.45 | -22 | bite, nom, snap, chomp_bite |
| `creature_hiss` | Big breathy threat hiss with a rough throat growl (sewer reverb). | 1.50 | -21 | hiss_big, monster_hiss |
| `creature_snarl` | Rough rising snarl. | 1.25 | -19 | snarl, growl |
| `creature_chitter` | Curious clicks/chirps ending on a rising "huh?" chirp. | 1.30 | -21 | chitter, chirp, clicks |
| `creature_purr` | Soft rumbly purr (~25 Hz flutter), exhale + inhale. | 1.60 | -25 | purr |
| `creature_chirp_sad` | Small sad descending coo ×2 with a quiver. | 1.15 | -21 | coo, sad_chirp, whimper |
| `dog_pant` | Goofy big-dog panting, 7 "hah-hih" per 2 s. **Loop 2.0 s.** | 2.08 | -26 | pant, panting |
| `dog_woof` | One goofy "bwoof". | 0.42 | -20 | woof, bark |

### Lab, facility, sewer
| name | description | dur s | level | aliases |
|---|---|---|---|---|
| `cage_creak` | Small metal cage door slowly creaking open, bumping the bars at the end. | 1.90 | -24 | creak, cage_open |
| `cage_rattle` | Wire cage shaken (run of clanks). | 0.95 | -22 | cage, rattle |
| `latch_click` | Metal latch "ch-chk". | 0.32 | -27 | latch, unlatch |
| `alarm` | Facility siren "whoop-whoop". **Loop 2.0 s.** | 2.08 | -22 | siren, klaxon, alert |
| `pod_hum` | Deep containment-pod hum, slow beat, faint whine. **Loop 3.0 s.** | 3.08 | -26 | hum, pods, machine_hum |
| `drip` | One water drip in a tunnel with a long echo (pitch varies per seed). | 2.20 | -23 | water_drip, drop |
| `water_splash` | Body landing in shallow water: thump, splash, bubbles, droplets. | 1.70 | -21 | splash |
| `sewer_ambience` | Sewer room tone: air rumble, faint hum, trickle, two distant drips. **Loop 3.0 s.** | 3.08 | -28 | sewer, ambience, room_tone |
| `squish` | Wet step (thump, squelch, suction pop). | 0.50 | -26 | squelch, wet_step |

### People and house foley
| name | description | dur s | level | aliases |
|---|---|---|---|---|
| `footstep` | One shoe step on a hard floor (heel + toe; seeds vary). | 0.30 | -27 | step |
| `footsteps_run` | Fast running steps (~1 s, 6–7 steps). | 1.15 | -26 | run, running, footsteps, steps |
| `tiptoe` | (kept) Comic pizzicato tiptoe. | 1.60 | -25 | |
| `foot_tap` | Single shoe tap on wood (impatient foot; seeds vary). | 0.25 | -26 | foot, toe_tap |
| `tap_tap` | Two quick fingertip taps on a shoulder. | 0.45 | -28 | tap, shoulder_tap |
| `cloth_rustle` | Sweater rustle (two movements). | 0.75 | -25 | rustle, cloth, sweater |
| `sigh` | Tired exhale "hhhaaah" with a hint of voice. | 0.85 | -24 | exhale |
| `yawn` | Breathy inhale, then a voiced "aaah-oh-mm". | 2.00 | -23 | |
| `cough` | One short cough "kh-uh". | 0.40 | -24 | |
| `drawer_open` | Wooden drawer slide, stop knock, contents shifting. | 0.85 | -26 | drawer |
| `plate_clink` | Ceramic plates touching. | 0.70 | -24 | plate, clink, dish |
| `chair_creak` | Gaming-chair creak. | 0.70 | -25 | chair |
| `heartbeat` | (kept) Lub-dub. | 0.80 | -24 | heart |

### Headphones, game, UI, powers, stingers
| name | description | dur s | level | aliases |
|---|---|---|---|---|
| `anc_on` | Noise-cancel engaging: plastic click, room hush draining away with an ear-pressure "thoom", tiny two-note chime. | 1.30 | -26 | anc, noise_cancel, headphones, headphones_on |
| `game_blips` | Burst of 8-bit sounds (jump, coin, laser, hit, power-up…), different per seed. | 1.60 | -23 | game, 8bit, blips |
| `game_music_leak` | Tinny chiptune leaking from headphones, deliberately quiet. **Loop 2.0 s.** | 2.08 | -32 | chiptune, leak, headphone_leak |
| `mouse_click` | Gaming-mouse click (press + release). | 0.16 | -31 | mouse |
| `typing` | (kept) Keyboard typing. | 1.30 | -29 | type, keyboard |
| `smear_zip` | Super-fast teleport "zip!" panning across. | 0.32 | -22 | zip, teleport, smear |
| `whoosh` | (kept) | 0.60 | -19 | swoosh, swish |
| `wind_fall` | Falling wind rush, building, with cloth flutter. | 1.60 | -21 | wind, falling, fall |
| `eye_open` | Waking: muffled world swelling back, dreamy low tone, ringing ears. | 2.40 | -23 | wake, awaken, tinnitus, ears_ringing |
| `sonar_ping` | The new sense: deep "whoom", cool E6 ping + 2 echoes, glassy shimmer. | 2.40 | -21 | sonar, ping, sense |
| `power_surge` | Powers kicking in: rising hum/whine, crackles, sparkle. | 2.50 | -22 | power, surge, powerup, power_up |
| `stinger_shock` | Orchestral shock hit (dissonant brass, shrieking strings, timpani, cymbal). | 2.40 | -21 | shock, stinger, orchestra_hit |
| `lightning_zap` | Electric crack + buzzing crackle for the freeze flash. | 1.20 | -24 | electric, crackle, electrocute, zap_lightning |
| `sad_chime` | Soft descending minor chime (E6 C6 A5). | 2.40 | -21 | sad_ding, chime_sad |
| `record_scratch`, `boing`, `gulp` | (kept) | 0.6 / 0.95 / 0.5 | -19 / -17 / -22 | scratch, -, - |

Older effects (brick_thud, pop, laser, buzzer_nope, sad_trombone, dun_dun_dun, ta_da, sparkle,
magic_chime, thunder, trumpet, trumpet_muffled, whistle, …) are unchanged. Generic legacy aliases keep
their old targets: `scratch` → record_scratch, `zap` → laser, `lightning` → thunder,
`thud` → brick_thud, `hiss` → snake_hiss, `click` → puzzle_click.

### Loopable effects
`sfx.LOOPS = {dog_pant: 2.0, alarm: 2.0, game_music_leak: 2.0, pod_hum: 3.0, sewer_ambience: 3.0}`.
Each clip is one period plus an 80 ms raised-cosine head and tail. Placed every `period` seconds,
the clips sum back to the periodic signal **exactly**: no seam, no dip. Use
`sfx.loop_events(name, t0, t1, gain_db, pan)` inside `SFX(info)`:

```python
def SFX(info):
    ev = [(info.cue("bite"), "chomp", 0)]
    ev += sfx.loop_events("sewer_ambience", 0.0, info.dur, -4)
    ev += sfx.loop_events("pant", info.cue("open"), info.cue("tug"), -8, 0.3)
    return ev
```

### Gain suggestions (gain_db in SFX entries)
* Big hits (impact_heavy, glass_crash_big, van_door, door_bang): 0 to -3. `door_bang` heard *through*
  the door or a wall: -6 and pan it away. A pounding run: 3–5 hits 0.25–0.35 s apart (seeds rotate).
* Creature vocals: 0. Under a line: -4. `creature_purr`: 0 to +2 (it is soft by design).
* Small foley (taps, clicks, cloth, latch, drawer): 0 to +3 when the action is on camera.
* Beds under dialogue: `sewer_ambience` -2…-6, `pod_hum` -3…-6, `dog_pant` -6…-10,
  `alarm` -6 (behind dialogue) or 0 (alone), `game_music_leak` 0…-3.
* `stinger_shock` + `lightning_zap` together for the freeze. `anc_on` at the headphones beat.

## Analysis tools (scratch, preview/)
* `python3 preview/audio_analyze.py music [cue…] [--dur 30] [--wav]`: render time, LUFS, peak,
  soft-clip %, band shares, short-term range, edge/pop checks. `lengths` renders 10/12/40/60 s;
  `describe <cue>` prints the chords. `sfx [name…] [--wav]`: dur, peak, LUFS, max 200 ms
  loudness, bands, edges, seed correlation, loop-join check. WAVs go to `preview/audio_out/`.
* `python3 preview/audio_spec.py music|sfx names…`: spectrogram sheets (PNG) with a loudness trace.
