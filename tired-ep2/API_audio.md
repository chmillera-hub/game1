# Audio API: music cues and SFX ("TIREDNESS")

Everything is procedural (numpy/scipy, 48 kHz stereo float32). Files:
`audio/music.py` (cues + the DSP toolkit), `audio/sfx.py` (effects), `audio/mix.py` (final mix).

```python
from audio import music, sfx
y = music.render_cue("ominous", 21.0)          # (round(21*48000), 2) float32, -18 LUFS
y = music.render_cue("reveal:awe=0.58", 24.6)   # options after a colon
y = music.render_cue("lullaby:resolve=0.86", 36.0)   # Episode 2 cues: lonely, lullaby (+ bond/chaos/chill options)
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

## Episode 2 ("Lights Out"): music per scene

Use these strings verbatim in script.json `music` (they are tuned to the current
out/timeline.json). Options are **fractions of the render**, and the render starts
`music_xfade/2` before the scene, so for a one-scene cue:
`frac = (t_scene + xf_in/2) / (scene_dur + xf_in/2 + xf_out/2)` (xf_out = the next
scene's `music_xfade`, default 0.6). Recompute if a scene's length changes by more than ~0.5 s.

| scene | cue string | render | what happens musically | suggested `music_gain` |
|---|---|---|---|---|
| s01 | `bond:cold=0.68,out=0.89` | 33.35 s | Tender wonder (celesta lullaby, strings, harp) from frame 0. **cold** at 22.7 s = `camera`: the lullaby stops, an icy pedal holds under the Boss. **out** at 29.7 s = `click`: a tape-stop (pitch dives to silence in 0.55 s): *the music dies with the lights*; the CHUNK cascade plays in silence. Plain `bond` = tender throughout (Episode 1 behaviour, bit-identical). | -1 (soft voice; worst consonant-band margin 6.5 dB at s01_l03) |
| s02 | `ominous:turn=0.62` (unchanged) | 34.09 s | Dark D-minor drone/strings/heartbeat in the dark; turns warm at 21.1 s (`s02_l05`, "Finally. A superpower..."), D major + celesta by 27.4 s (`walk`). Tune the sonar pings to it: they are E6 + A/D/E shimmer, consonant with both modes. | 0 |
| s03 | `sneaky` (unchanged) | 23.79 s | Pizzicato tiptoe. Busy low end, light in the vocal band (34 %). | -1 (the whispered "Stop that.") |
| s04 | `lonely` (new) | 33.85 s | Solo piano, D minor, 56 BPM (fitted). Phrases sit in the dialogue gaps: motif before/after l01, silence under l02, a small rising "question" at `tug`, the falling ache (G5-F5-E5-D5) right after l04 under `hurt`. **follow** (default 0.76) = 25.4 s scene time, just before `alone`: a low string pad fades in (3 s) and the motif turns upward (Bbmaj7 -> F/A: F5 30.8, G5 31.9, A5 32.4 s, around `follow`). | 0 (it is built -1.5 dB light) |
| s05 | `awkward` (unchanged) | 37.98 s | Cringe comedy with built-in silences. | 0 |
| s06 | `lullaby` (new; default resolve 0.86) | 35.99 s | 2 bars of cold pad on the dominant (doors, the chair turning), the music box enters at 5.0 s and grows sweeter through the offer (choir "oo" from ~14.7 s), runs down like a spring from 25.5 s (ritardando + pitch droop under l07), its last note at 28.9 s (`droop`); the cold pad holds alone, then from **30.75 s** ("But" of l08: the spell breaks) strings/horns/choir swell on F under "for once... I'm not tired" and bloom into **A major at 32.9 s**, right after the last word (`eyes_open` 33.46). | 0 |
| s07 | `chaos:stop=0.74` | 24.72 s | Slapstick action until **18.27 s** (`hatch`): a last Dm tutti hit (sync it with `hatch_slam`), then an icy pedal under "Let them run." Plain `chaos` = full action to the end. | 0 |
| s08 | `chill:sting=3.6` | 19.91 s | The Episode 1 lo-fi bed (tempo nudged to 73.6 BPM so the button lands on a bar line), a C7b9 turnaround, then the soft warm **Fmaj9 button at 16.0 s** (0.3 s after `title`): the hook's F-A-C on vibe, held to the end (the mixer's 1.6 s end fade tapers it). | 0 |

Option reference (all optional; omitted = old behaviour):

* `lonely:follow=f` (0.76; 1 = never): fraction where the string pad enters and the motif turns upward. The tempo (50-66 BPM) is fitted so it falls on a bar line.
* `lullaby:resolve=f` (0.86; 1 = never, pure eerie loop), `rise=s` (seconds from `resolve` to the A-major bloom; default 0.42 of the remaining time, 0.8-3.2 s). The music box winds down over the 2 bars before `resolve`.
* `bond:cold=f` (icy pedal from there), `bond:out=f` (tape-stop to silence at that fraction).
* `chaos:stop=f`: final tutti hit at that fraction, then an icy pedal.
* `chill:sting=N` (seconds): the groove stops N s before the end and the Fmaj9 button rings out; the tempo is nudged up to 8 % so the button falls on a bar line after a C7b9 turnaround.

## Music cues

| cue | character | key / BPM | best scenes | options / variants | dialogue notes |
|---|---|---|---|---|---|
| `chill` | Lo-fi gaming bed. Lazy swung (58%) rootless e-piano 9ths with tape wow, a vibraphone **hook** (F-A-C… rising arpeggio with sighs) and a softer call-and-response in the B half, warm sub, soft brushes (kick, brush taps, swishes). Opens on keys + bass with the hook from t=0; brushes enter at bar 2. | F major colour: Bbmaj9, Am7/D7b9, Gm9, C9sus4/C7b9 · 78 | s01 (Ep1), s08 | `chill:sting=3.6` (Ep2): Fmaj9 end-card button over the last N s | Vocal band only ~28 %. The hook is a soft vibe in 700–1000 Hz, ducked under lines. |
| `panic` | Frantic comedic chase. Galloping pizz bass with chromatic walk-ups, off-beat pizz chops, **xylophone hook** in bars 1–4 (chromatic descents), a pizz-violin answer in bars 5–6, one bar of air, then a chromatic xylo run + snare roll. Woodblock tick-tock on every beat, kick and snare. | E minor: Em Em C B7 / Em Am F#m7b5-B7 Em-B7 · 160 | s02, s03 | - | Busiest cue. The answer bars thin out for lines; `music_gain` -1…-2 under dense dialogue. |
| `sneaky` | (kept) Cartoon tiptoe: pizz bass, plucked melody, bassoon double, woodblock. | A minor · 104 | s04, s05 | - | Unchanged. |
| `awkward` | Cringe comedy. Staccato **bassoon** ditty, tuba "oom" (often missing its "pah"), pizz plinks, a sad little glock echo of the Ab-G sigh. **Bars 3, 4 and 8 are near-silent; a faint clock ticks in the gaps.** Second time round one entry comes in late. | C major with the minor iv (F→Fm), Dm7-G7 · 90 | s06, s10 | `level_db` -2 (built in) | Very light; the silences are where the lines go. |
| `chaos` | Slapstick action. Galloping 16th low-string ostinato, 3+3+2 **brass stabs**, a brass rip into each cycle, rock drums with tom fills, timpani, crash. | D minor: Dm Bb Gm A7 / Dm Bb Eb-Gm A7 · 150 | s07 | internal peak limiter at -3.5 dBFS; `chaos:stop=0.74` (Ep2): last tutti hit, then an icy pedal | Mostly action; dialogue is short shouts. |
| `tension` | (kept) Pulsing 16th ostinato with a rising filter, computing blips. | A minor · 110 | s08, s11 | - | Unchanged. |
| `corporate` | Cold minimal. Clean filtered **pulse bass** in 8ths, sine-blip arpeggio with ping-pong echoes, clinical 16th hat ticks, an icy glass pad. Unease comes from sus chords, an F-against-E **b6 rub** and a #11; a high glass swell every 4 bars. | A: Asus2, Asus2b6, Fmaj7, Fmaj7#11, Dm9, Esus4, Asus2, E7sus4 · 100 | s09 | `level_db` -1.5 (built in) | Dense dialogue scene: bass sits low and the arp is quiet sine. |
| `ominous` | Sewer. D drone, slow low-string swells over a D pedal (Dm(add9) Bb/D Gm/D Eb/D), distant pipe resonances, bowed-metal whines, **pitched drips** (minor pentatonic), a **heartbeat** pulse. **Warm turn** from `turn` (default 0.66 of the render): Bbmaj7 → C/D → D(add9) (bVI-bVII-I). Drips go major, choir "oo" + warm strings enter, the heartbeat slows and fades, and a celesta plays two "questions" then the creature lullaby. | D minor → D major · 56 | s12 | `ominous:turn=0.7` (fraction of the render; 1 = never); `ominous_dark` (no turn); `ominous_warm` (turn 0.5) | Default fits s12 as mixed (21.1 s render): turn ≈ 13.9 s (form/eyesWide), D major ≈ 17.4 s ("Okay. Hi."). |
| `bond` | Tender lullaby. **Celesta** melody (the creature's theme), warm strings, soft harp arpeggio, sub. Second pass: melody an octave up with a soft violin double. | D: Dadd9 A/C# Bm7 Gmaj7 D/F# Em7 Gmaj7 Asus4-A · 66 | Ep2 s01 | `bond:cold=0.68,out=0.89` (Ep2): icy pedal from `cold`, tape-stop to silence at `out` | Gentle; the celesta peak (F#6) is the closest thing to the voice band. |
| `lonely` | **Ep2.** Sparse, sad solo piano (soft additive piano, felt-like top, upright-light bass) in a soft room: a minor-6th/minor-7th "ache" motif with long silences, phrases placed in the s04 gaps; a low string pad from `follow`, where the motif turns upward. Built-in level -1.5 dB. | D minor: Dm(add9) Bbmaj7 Gm A7sus4-A7 / Dm F/C Bbmaj7 Asus4-A; after follow Bbmaj7 F/A Gm7 Bb/C Fadd9 Dm · ~56 (fitted 50-66) | Ep2 s04 | `lonely:follow=0.76` | Very light: 26 dB voice/music margin in 1-4 kHz (worst 16). |
| `lullaby` | **Ep2.** Eerie music-box temptation in 3/4: a sweet melody on a music box (two slightly detuned tines per note, comb partials 1 : 6.27 : 17.55, a mistuned comb ±5 cents, ~7-cent spring warble), over a cold glass pad, a dark low string pad and a breathing A drone; minor-major 7th, augmented and Neapolitan colours, a reversed tine swelling into each phrase, a faint bowed-metal whine; a soft "oo" choir as the pull of sleep grows. Before `resolve` the box runs down (ritardando, -28 cents droop) and stops; strings/horns/choir swell on F (+ timpani roll, cymbal swell) and bloom into a brave, warm A major (horns, choir, timpani, harp, the motif in tune on celesta). Peak limiter -3.5 dBFS. | A minor: Am AmM7/G# Am7/G Am6/F# Fmaj7 Dm6 Eaug E7b9 (2nd time ... Bbmaj7#11 Eaug) -> Fadd9 -> Aadd9 · 69 (3/4) | Ep2 s06 | `lullaby:resolve=0.86,rise=2.1`; `resolve=1` = never | Box is a single sparse line; voice/music in 1-4 kHz 16.5 dB (worst 9.1 at "That does sound nice", the temptation peak). The bloom is ~+4.5 LU over the box body, after the last line. |
| `reveal` | s13 arc **scaled to the render**. (1) Curious walk: pizz walking bass down the line cliché (Dm Dm/C# Dm/C Bm7b5 Bbmaj7 Gm6…), light pizz chords, curious "plink-plink-plink", low strings. The tempo is fitted (~84–105 BPM) so the walk ends on A7sus4→A7 exactly at `awe`. (2) Timpani roll + swell, then the **awe**: a deceptive cadence to **Bbmaj7#11** with choir "ah", full strings, harp gliss, boom. (3) **Sorrow**: Gm9, Dm/F, … A7sus4 with slow strings and a solo violin lament. (4) The **"to be continued" sting**: a soft Bbmaj7#11 (the awe chord returning as a question), celesta arpeggio, violin holding the #11. | D minor · fitted | s13 | `reveal:awe=0.575,sad=0.695,sting=3` (fractions; sting in seconds from the end, max 25 % of the render) | Defaults match s13 as mixed (24.6 s): awe 14.2 s (= "reveal" cue), sorrow 17.1 s ("sad"), sting at the last 3 s ("title"). Built-in peak limiter. Awe is ~4 LU above the cue average (no dialogue there). |
| `doom`, `ai_calm`, `beg`, `heart`, `resolve` | Inherited from the previous film; still render. | | | | |

Measured (30 s renders, cold process): render 0.6–2.7 s (60 s renders 3.6–5.5 s); LUFS -18 (awkward -20,
corporate -19.5); peaks -3.5 to -7.9 dBFS for the new cues. Short-term loudness range in the body is 1–3 LU for the
loopers. Share of energy in 300 Hz–3 kHz: chill 28 %, panic 44 %, awkward 45 %, chaos 26 %,
corporate 45 %, ominous 16 %, reveal 26 %; below 120 Hz ≤ 46 %.

**Episode 2 measurements** (preview/audio_analyze.py; "scene" = rendered exactly as the mixer does, with the
recommended strings; voice/music = processed dialogue vs. the ducked bed in 1-4 kHz while someone speaks, mean / worst 0.5 s):

| cue (scene render) | dur s | render s | LUFS | true peak | <120 / 120-300 / 300-3k / 3k-8k % | short-term range | clicks | voice/music dB |
|---|---|---|---|---|---|---|---|---|
| `bond:cold=0.68,out=0.89` (s01) | 33.35 | 2.4 | -18.0 | -7.0 | 38/21/41/0 | tender -17, cold -22, silent after the stop | 0 | 15.6 / 6.5 |
| `ominous:turn=0.62` (s02) | 34.09 | 2.7 | -18.0 | -5.1 | 40/45/16/0 | 1.5 LU | 0 | 21.8 / 12.9 |
| `sneaky` (s03) | 23.79 | 0.8 | -18.0 | -2.4 | 55/9/34/2 | 1.1 LU | 0 | 16.4 / 11.7 |
| `lonely` (s04) | 33.85 | 2.3 | -19.5 | -5.9 | 37/20/43/0 | 4.6 LU (phrases vs silences) | 0 | 26.3 / 16.4 |
| `awkward` (s05) | 37.98 | 0.8 | -20.1 | -5.3 | 16/40/44/0 | (built-in silences) | 0 | 23.6 / 17.4 |
| `lullaby` (s06) | 35.99 | 4.6 | -18.0 | -3.5 | 28/12/60/0 | intro -25, box -21 -> -17, swell -22 -> -17, bloom -13 | 0 | 16.5 / 9.1 |
| `chaos:stop=0.74` (s07) | 24.72 | 1.7 | -18.1 | -3.5 | 49/27/22/2 | body -18, hit -14, pedal -21 | 0 | 20.5 / 16.1 |
| `chill:sting=3.6` (s08) | 19.91 | 1.1 | -18.1 | -6.4 | 48/23/29/0 | groove -18, button -17 | 0 | 21.2 / 20.1 |

Lengths 10/12/20/33/40/60 s all render seamlessly (no clicks, ±0.4 LU): lonely 0.7-3.8 s, lullaby 1.3-8.3 s
(60 s = 4.2 s per 30 s). Option edge cases (follow 0.2-1, resolve 0.2-1, cold/out 0.1-0.7, stop 0.1-0.97,
sting 1-25 s) render cleanly. All Episode 1 cues without options are **bit-identical** to Episode 1.

**Suggested `music_gain`** (Episode 1 scene numbers; for Episode 2 see the table at the top) (per scene; it cannot change mid-scene): s01 0, s02–s03 -1, s06/s10 0, s07 0…+1, s09 0, s12 0, s13 0. Use `music_xfade` 0.05–0.2 for
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
| `creature_purr` | **Ep2, warmer:** ~25 Hz larynx pulses through a warm chest/throat body (120-780 Hz formants) with a soft voiced core, breath only on top; exhale, then a softer inhale. Ep1 version: `creature_purr_ep1`. | 1.60 | -25 | purr |
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
| `sigh` | **Ep2, more natural:** exhale starting at t=0, airflow through moving formants (open "ah" closing to "h"), breath turbulence, chest air, a breathy voiced "hah" up front. Ep1: `sigh_ep1`. | 1.00 | -23 | exhale |
| `sigh_deep` | **Ep2.** Soft nasal inhale (0-0.45 s), then a long voiced resigned exhale **from 0.55 s** (s04 "sits with that"). | 1.95 | -22.5 | deep_sigh, sigh_long |
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
| `sonar_ping` | **Ep2 signature, rebuilt:** a deep soft "whoom" (62 Hz falling, harmonics for phones, an air-pressure puff), a soft glassy E6 ping with a slow chorus shimmer, two darker returns panning out L/R, and a **teal shimmer tail** of high partials (4 of A6 D7 E7 A7 D8 E8, chosen per seed, drifting up a hair) in a long bright space. Seeds vary the whoom pitch, ping tuning (±6 c), return timing and the shimmer constellation (waveform corr 0.16-0.22, envelope 0.95: "a little"). Consonant with D minor, D major and A minor. Ep1: `sonar_ping_ep1`. | 3.40 | -21 | sonar, ping, sense |
| `sonar_ping_small` | **Ep2.** Small quick sense ping (hiding): lighter whoom, one return, 2 shimmer partials, shorter space. | 1.90 | -23.5 | ping_small, sonar_small, sense_small |
| `power_surge` | Powers kicking in: rising hum/whine, crackles, sparkle. | 2.50 | -22 | power, surge, powerup, power_up |
| `stinger_shock` | Orchestral shock hit (dissonant brass, shrieking strings, timpani, cymbal). | 2.40 | -21 | shock, stinger, orchestra_hit |
| `lightning_zap` | Electric crack + buzzing crackle for the freeze flash. | 1.20 | -24 | electric, crackle, electrocute, zap_lightning |
| `sad_chime` | Soft descending minor chime (E6 C6 A5). | 2.40 | -21 | sad_ding, chime_sad |
| `record_scratch`, `boing`, `gulp` | (kept) | 0.6 / 0.95 / 0.5 | -19 / -17 / -22 | scratch, -, - |

Older effects (brick_thud, pop, laser, buzzer_nope, sad_trombone, dun_dun_dun, ta_da, sparkle,
magic_chime, thunder, trumpet, trumpet_muffled, whistle, …) are unchanged. Generic legacy aliases keep
their old targets: `scratch` → record_scratch, `zap` → laser, `lightning` → thunder,
`thud` → brick_thud, `hiss` → snake_hiss, `click` → puzzle_click.

### Episode 2 effects
Levels as above (loudest 200 ms, K-weighted, at gain 0). "Seeds": envelope / waveform correlation of
seeds 1-3 against seed 0 (1.00 = identical; low waveform corr + high envelope corr = "same sound, natural variation").

**Shaft power, facility, control room**

| name | description | dur s | level | seeds | aliases |
|---|---|---|---|---|---|
| `lights_out` | Heavy power-relay "ka-CHUNK": a trip tick, then 22 ms later the contactor slam (low thump + 110-1600 Hz body + bright snap) with an armature bounce; the 100 Hz hum **sags and fades** (~1.5 s), a ballast whine drops away; sometimes an electric spit, sometimes a lamp tube ticking as it cools. Big shaft reverb. | 2.50 | -19.3 | vary (pitch ±14 %, hum, spit, bounce) | power_cut, power_off, relay, chunk, lights_off, breaker, blackout |
| `lights_out_far` | The same relay far up the shaft: darker (LP 2.4 kHz), soft attack, mostly reverb (3.2 s). Gives a cascade 8 distinct variants with `lights_out`. | 2.90 | -20.9 | vary | chunk_far, relay_far, lights_out_distant |
| `camera_whir` | Security-camera servo pan: accelerating gear whine (300-360 Hz tooth rate + harmonics through a plastic housing), stop tick at 0.93 s, then a short lens-focus whir (1.12-1.36 s) and a tick. | 1.60 | -24.4 | subtle | camera, servo, cctv, camera_pan |
| `keycard_beep` | Card tap, bright rising two-tone chirp (G6 at 0.06 s, C7 at 0.15 s), the lock thunking open at ~0.36 s. | 0.80 | -20.2 | lock timing varies; the chirp is identical (a device) | keycard, card_beep, card_swipe, access_granted |
| `door_slide` | Heavy centre-parting sliding doors: lock clunk + pneumatic hiss at 0, motor + rollers rumbling as the leaves part L/R (0.12-1.67 s), heavy thunk at the end stop (~1.6 s). | 2.40 | -20.7 | vary | doors, sliding_doors, doors_open, blast_door |
| `hatch_slam` | Heavy steel hatch slammed: low boom, damped plate ring, the bolt clacking home at ~0.1 s, a few rattles. | 1.90 | -18.2 | vary | hatch, hatch_close, metal_door_slam |
| `lever_strain` | Metal groaning under load (~1.5 s, crescendo to ~1.35 s): smoothed stick-slip groans through stiff resonances, a wandering bowed tone, a deep stress rumble, little pops. | 1.95 | -22.1 | vary (corr 0.8) | strain, metal_groan, groan |
| `lever_clunk` | The lever slamming into its end stop: heavy clunk, short ring, rattle. Place it right where `lever_strain` peaks. | 1.00 | -18.5 | vary | lever, clunk, lever_stop |
| `shutter_slam` | Heavy shutters: slats rattling down for **0.22-0.42 s (seed)**, then the slam (boom + corrugated metal + crunch) and the curtain settling. The slam is at the end of the rattle, so place it ~0.3 s early. Big shaft reverb. | 2.40 | -18.7 | vary strongly (length, pitch, weight) | shutter, shutters, shutter_down |
| `pod_hiss` | Pneumatic seal: latch clack + suction pop, a burst of hissing air with a falling whistle, a soft pressure whoosh (~1.5 s). Bright by nature (52 % in 3-8 kHz). | 1.90 | -20.8 | envelope varies | seal_hiss, pneumatic, pod_open, airlock |
| `glass_case_smash` | A fist through a small glass case: sharp crack, a tight burst of high shards (HP 900 Hz), a short tinkle on the floor. Smaller and sharper than `glass_crash_big`. | 1.40 | -21.1 | vary | case_smash, glass_case, punch_glass |
| `alarm_soft` | Quieter facility alarm, **loop 2.0 s**: soft hi-lo two-tone (G5 / Eb5, 4 per loop), rounded, low-passed at 1.9 kHz so consonants stay clear, roomy. | 2.08 | -25 | loop (seed-free) | alarm_quiet, siren_soft, soft_alarm |

**Curiosity, baby Joy, the bonk**

| name | description | dur s | level | seeds | aliases |
|---|---|---|---|---|---|
| `pipe_bonk` | Head into a low metal pipe: hollow ringing clang (pipe modes 1 : 2.76 : 5.4 : 8.93 at ~410 Hz, with a wobble) + the cartoon "bonk" (tonk with a pitch drop) + a head thud. Rings ~1 s: the held beat. | 1.60 | -20.8 | vary (pitch ±6 %) | pipe, pipe_hit, head_pipe |
| `baby_giggle` | Tiny creature giggle: 5-8 bright "hee" chirps tumbling down (1.5 -> 1.1 kHz), then a little upward squeak. | 1.10 | -20.0 | vary strongly (count, pitch, timing) | giggle, baby_laugh, tiny_giggle |
| `baby_coo` | Soft round "ooo" rising and falling (690 -> 940 -> 760 Hz) with a quiver. | 0.80 | -19.0 | vary (pitch, length) | baby, joy_coo |
| `creature_melt` | Curiosity melting into a shadow puddle: a soft dark whoosh falling 2.6 kHz -> 170 Hz with a sinking tone, a tiny low "vmm" as the puddle settles (~1.0 s). Not wet. | 1.60 | -23.4 | subtle | melt, shadow_melt, puddle |
| `creature_reform` | The reverse: a rising shadow-whoosh, finished by a small bright "pop" at ~1.08 s (the ears). | 1.60 | -23.3 | subtle | reform, unmelt |
| `ears_perk` | Two tiny upward "bwip"s (one per ear, L then R, 18 ms apart) with a hint of spring. Subtle. | 0.35 | -27.3 | vary | perk, ear_perk, ears_up |

**People, gadgets, home**

| name | description | dur s | level | seeds | aliases |
|---|---|---|---|---|---|
| `flashlight_click` | Tail-switch: hard plastic press "tk" + latch "click" 28 ms later. | 0.25 | -27.4 | vary | flashlight, torch, torch_click |
| `recorder_click` | Small plastic button (press + release) and a tiny falling power-down blip (1.7 kHz -> 480 Hz) at 0.09 s: the LED going dark. | 0.45 | -26.9 | subtle | recorder, recorder_off, button_click |
| `phone_buzz` | Phone vibrating on a wooden nightstand: two buzzes (0-0.48, 0.62-1.1 s) with spin-up/down, wood body and rattle. | 1.30 | -20.2 | subtle | buzz, vibrate, phone_vibrate, phone |
| `text_send` | A soft airy upward whoosh with a faint "fwip" (the "zzz" reply). Softer than `send`. | 0.55 | -25.4 | subtle | text, sms_send, reply |
| `bed_flop` | Face-down onto a mattress: soft heavy "fwump" + duvet puff, box-spring "boing" bounces (0.03 / 0.33 / 0.58 / 0.8 s) dying away, two frame creaks. | 1.90 | -20.8 | vary | flop, bed, mattress, bed_springs |
| `birds_dawn` | Gentle morning birdsong outside the window, **loop 3.0 s**: a robin-like warble (L), sparrow chips (R), a distant "tee-oo" whistle, a faint dawn hush; LP 7.5 kHz. | 3.08 | -23.5 | loop (seed-free) | birds, birdsong, dawn, morning, bird_chirp |

### Loopable effects
`sfx.LOOPS = {dog_pant: 2.0, alarm: 2.0, alarm_soft: 2.0, game_music_leak: 2.0, pod_hum: 3.0, sewer_ambience: 3.0, birds_dawn: 3.0}`.
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

**Episode 2 gain suggestions**
* **Lights-out cascade (s01 `dark`)**: 5 relays 0.4-0.55 s apart from far to near, e.g.
  `[(t, "lights_out_far", -6, 0.5), (t+0.5, "lights_out_far", -4, -0.4), (t+1.0, "lights_out", -4, 0.3),
  (t+1.5, "lights_out", -2, -0.2), (t+1.95, "lights_out", 0, 0)]` (seeds rotate per name, so 5 relays use
  far 0/1 + near 0/1/2: all different). With `bond:...,out=0.89` the music is already silent by then.
* `sonar_ping`: 0 alone (s02), -3 when it follows the head turns; `sonar_ping_small` -2…-6 behind the crate (s03).
  They ring ~3 s: space pings >= 1.2 s apart or drop the later ones by 3 dB.
* `pipe_bonk` 0…+2 (the big comic beat). `glass_case_smash` 0, `lever_strain` 0 then `lever_clunk` 0 at its end,
  `shutter_slam` -2…-6 per tier (far tiers lower, pan them), `hatch_slam` 0 (sync with `chaos:stop`).
* `pod_hiss` -3 (bright), `alarm_soft` 0 under dialogue (loop with `sfx.loop_events("alarm_soft", t0, t1, 0)`),
  `door_slide` 0, `keycard_beep` -2, `camera_whir` 0…+2 (it is small and high on the wall).
* Small foley on camera: `flashlight_click`, `recorder_click`, `ears_perk` 0…+3; `text_send` 0; `phone_buzz` -3.
* Creatures: `baby_giggle` / `baby_coo` -2…0, `creature_melt` / `creature_reform` 0…+2, `creature_purr` +2…+4 in s08
  (soft by design; a purring trio: three purrs with pans -0.3/0/0.3, offset 0.5 s), `creature_chitter` for curious beats.
* Beds: `birds_dawn` -6…-10 under s08 (it repeats every 3 s; keep it low), `pod_hum` -6 in s01, `sewer_ambience`
  is the wrong room for Episode 2 (use `pod_hum` / silence). `drip` -4 for the s04 echoing drip.
* Breath: `sigh` 0…+2, `sigh_deep` +2 (its exhale starts at 0.55 s: place it 0.55 s before the shoulders drop).

## Analysis tools (scratch, preview/)
* `python3 preview/audio_analyze.py music [cue…] [--dur 30] [--wav]`: render time, LUFS, true peak, band shares
  (<120 / 120-300 / 300-3k / 3k-8k / >8k), short-term loudness range, discontinuity (click) candidates, edges.
  `lengths cue…` renders 10/12/20/33/40/60 s. `describe cue…` prints the chords.
* `python3 preview/audio_analyze.py scenes [--cue s01=bond:cold=0.68,out=0.89 …] [--wav]`: every scene's cue rendered
  exactly as the mixer does (durations and fades from out/timeline.json + script.json), plus a voice-over-music
  check (processed lines vs. the ducked bed, 1-4 kHz, while speaking) and `scene_<id>_premix.wav`.
* `python3 preview/audio_analyze.py sfx [name…] [--new] [--wav]`: dur, peak, LUFS, max 200 ms loudness, bands, edges,
  clicks, seed correlation, loop-join check (tiled with `loop_events`).
* `python3 preview/audio_spec.py sfx|music|wav names… [--pps 120] [--range t0:t1] [--out x.png]`: spectrogram sheets
  (PIL) with the 300 Hz / 3 kHz vocal-band lines and a loudness trace. Output: `preview/audio_out/`.
* Click candidates in the creak family (`cage_creak`, `chair_creak`, ~50-100) are the stick-slip texture, not faults.
