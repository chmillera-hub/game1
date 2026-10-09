# IF YOU HAVE TIME — production bible

A 3 min 52 s portrait (720×1280, 24 fps) animated short. Final file: H.264 + AAC MP4, ≤ 14 MB.
Everything is generated procedurally in this folder: Kokoro TTS voices, FluidSynth-rendered
music, numpy SFX, skia-python vector animation.

**Original IP only.** This is *inspired by* "asking the ship's android to write a symphony" but must
not use any Star Trek names, logos, uniforms, insignia, ship designs, sounds or the character Data.
Our ship, crew, android and insignia are original.

---

## 1. Story in one breath

Rae, an exhausted crew member, flops onto the observation-lounge bench at the end of a long shift
and casually asks Quill, the ship's android, if he could write her a symphony "if you ever have
time." Quill: "Certainly." … "Done." He plays it. It is so beautiful she sinks to her knees in tears
while memories she didn't know she still carried float around her. The music ends; she snaps back:
"WHAT the heck was THAT?!" Quill, misreading her, apologizes — he wrote eight, maybe she'd prefer
another — and plays the solo-kazoo version, the arcade version, the lo-fi version… and they're
ALL devastatingly good. The 11-second lullaby finishes her off: "Nope. I'm getting out of here."
Alone, Quill wonders: "…Was that a yes?" The door slides open; Rae, red-eyed: "Send me all eight."
Quill's rare, tiny smile. "Sending."

Tone: dry comedy wrapped around a genuinely moving middle. The symphony section must play
*sincerely* — the joke only lands if the music and visuals really are beautiful.

## 2. Characters

### QUILL — the android (male voice, am_michael + subtle comb filter)
- Tall (HEIGHT ≈ 770 stage units at scale 1), slim, immaculate posture, economical movement.
- Skin: cool porcelain grey (`q_skin`), soft shading (`q_skin_shade`), very faint seam lines along
  the temples, jaw hinge and down the neck (`q_seam`) — subtle, readable only in close-up.
- Hair: short, neatly combed back, dark navy with a cool highlight sheen (`q_hair`, `q_hair_hi`).
- Eyes: almond-shaped, calm. Irises luminous teal (`q_iris`) with a soft glow (`glow`) and, when
  `process` > 0, thin concentric rings rotating inside the iris + rapid tiny flicker.
  Blinks are perfectly periodic and quick (`auto_blink(robotic=True)`), both lids identical.
- Brows: thin, straight, move very little (max ±40 % of what Rae's do). Tiny expressions read as huge.
- Mouth: neutral line; a "smile" for Quill is a barely-there lift of the corners (use smile ≤ 0.35).
- Uniform: charcoal tunic (`q_uniform`) with a high teal collar band (`q_collar`) and a teal stripe
  down one shoulder, small silver insignia on the left chest: an original **stylized quill feather
  inside a thin circle**. Dark trousers, simple boots.
- Body language: hands clasped behind back when idle, head tilts like a curious bird, moves in
  smooth eased arcs (no overshoot), never fidgets.
- Arm presets (ARMS keys): `rest`, `behind_back`, `raise_conduct` (right hand lifted to shoulder
  height, palm open, like cueing an orchestra), `present` (right palm up, offered forward — holo
  cards hover above it), `gesture_small` (explaining, hand at waist height), `send` (arm extended
  forward-up, fingers releasing).

### RAE — the human (female voice, af_heart)
- HEIGHT ≈ 700 at scale 1. Warm brown skin (`r_skin` + shade/highlight), soft round face, expressive
  big eyes (dark brown irises with large white catch-lights), thick expressive brows.
- Hair: big curly puff tied up on top + a few loose curls framing the face (`r_hair`, `r_hair_hi`).
- Outfit: mustard crew shirt (`r_shirt`) under an unzipped slate jacket with rolled sleeves
  (`r_jacket`), dark trousers (`r_pants`), sneakers-like boots. Tired: slight under-eye shading.
- Prop: off-white mug (`mug`) with a small red heart-in-a-circle logo.
  `draw_mug(canvas, x, y, scale, angle)` must be exported for when the mug sits on the bench.
- Very expressive and organic: irregular blinks, eyebrow-led acting, lots of eyelid nuance
  (half-lidded tiredness → wide awe → squeezed tears → rapid blinking on the snap-back).
- Arm presets (ARMS keys): `rest`, `hold_mug` (mug at waist/lap), `sip` (mug at mouth),
  `mug_raise` (little toast), `point` (pointing forward), `hand_on_chest`, `wipe_eye`,
  `cover_mouth`, `hands_up` (palms out, defensive "nope"), `grip_knee`, `reach_back`
  (reaching behind for the door while backing away), `shrug`, `hug_self`, `knee_rest`
  (forearm resting on knee while seated).
- Must support: standing, `walk` cycle, `sit` on the bench, `kneel`, `foot_tap`, `bounce`,
  lip quiver (`mouth_tremble`), welling tears (`tears`), rolling tears (`tear_l`/`tear_r`), `sniffle`.

### Expression craft (both)
Faces carry this film. Required nuance:
- Eyelids: upper lid height + lower lid (`squint`) + `eye_wide`; partial lids must look natural
  (lid line covers the top of the iris; never "pupil floating in white" unless `eye_wide` > 0.7).
- Gaze (`look_x/y`) moves pupils + irises together, with a tiny lag/settle the scenes animate.
- Brows: raise / worry (inner up) / furrow (inner down) combine.
- Mouth shapes from lip-sync (`mouth_open`, `mouth_round`) layered with `smile`/`smirk`.
- Micro-motion: breathing, idle head drift (`wobble`), saccades — but restrained. Not excessive.

## 3. The ship and the lounge

### Exterior (S0)
Original design — the *Meridian*: a long, slender pearl-white hull like a stretched teardrop,
a slowly turning habitat ring around its middle, two swept-back fins with teal light lines, and
rows of warm amber windows. **No saucer section, no nacelles on pylons.** Seen against a deep
violet/teal nebula with sparse, crisp stars.

### Observation lounge (S1–S5) — stage layout (stage units)
```
x:  -360 ........ -140   60 ... 90 ..................... 630 ... 700 ......... 1080
     [   wall   ][ DOOR ]    [      BIG ARCHED WINDOW      ][CONSOLE ]   [wall]
DOOR: center x = -40, width 200 (x -140..60), height 720 (y 430..1150), slides open sideways.
WINDOW: x 90..630, y 140..860, arched top, thin trim frame; stars + nebula visible.
WINDOW SILL: y 860..900 (low ledge).
BENCH: curved, upholstered, in front of the window: x 40..420, seat top y = 960, front face to 1030.
CONSOLE: slim pillar with glowing panel and blinking lights, x 640..720, waist-high panel y 760..860.
FLOOR: y = 1150, reflective dark floor (`floor`) with a soft reflection of the window glow.
Ceiling light strip at y ≈ 60 (amber); wall sconces.
Rae's spot on the bench: x ≈ 230 (seated, facing +1 / toward Quill).
Quill's mark: x ≈ 545, standing, facing -1 (toward Rae) once he turns.
```
`light` param: 1.0 normal warm interior, 0.25 dimmed for the symphony (the window view stays bright
and becomes the main light source; ribbons/motes add colored light).

## 4. Shot-by-shot direction

Beat times come from `build/timeline.json` — always reference beats/lines by name via
`anim.core.beat()` / `line_start()`; never hard-code absolute seconds. Times below are the
current values for orientation only.

### S0 — Cold open (0.0 – 16.0)
- Deep space, sparse crisp stars in 3 parallax layers drifting slowly downward (ship moving "up"),
  soft nebula. Ambient pad + celesta hint of the theme.
- 0.5–12: the *Meridian* glides up from the lower left, large and graceful, rotating its ring.
- `title_in` 3.0 → `title_out` 11.0: "IF YOU HAVE TIME" — thin, widely tracked caps (Inter Display
  Light/ExtraLight ~44 px, tracking ~10), soft teal glow, gentle fade + 8 px drift up.
- `dive_start` 12.5–16.0: camera pushes into one warm lit window on the hull, accelerating; at
  ~15.4 the window fills the frame and flashes warm white → cut to S1 (which fades in from that warm white).

### S1 — The ask (16.0 – 58.98)
1. 16.0–19.6 WIDE (zoom ≈ 0.72, whole lounge incl. door). Quill stands at the console with his
   back to camera (`back`=1), hands behind back, watching the stars. Door slides open
   (`rae_door_open`), Rae shuffles in (`rae_enters`, walk ~2.6 s, tired), door closes behind her,
   she drops onto the bench (`rae_sits`) with a little bounce, mug in hand.
2. r01 "Ugh. Long shift." — MEDIUM on Rae (zoom ≈ 1.5): head lolls back, eyes closed, then half open.
3. `quill_turns` → q01 — MEDIUM on Quill: he turns smoothly from the window (cut on the turn),
   hands still behind back, neutral, precise. Slight head tilt on "by my count".
4. r02 — MEDIUM Rae: tired half-smile, half-lidded eyes, lazily points the mug at him.
5. `rae_sip1` — TWO-SHOT (zoom ≈ 1.0): Rae sips, looks out at the stars. Quill turns his gaze to the window too. Quiet beat.
6. r03–r05 — slow push-in on Rae (zoom 1.4 → 1.9), stars behind her. Wistful, honest: eyes on
   the stars, small self-deprecating smile on "no rush, seriously", softer and slower on
   "Feeling really small out here" (brow_worry ~0.4, eyes lower).
7. q02 "Certainly." — CLOSE-UP Quill (zoom ≈ 2.8): `quill_process_start` → irises spin up
   (`process` 0→1→0 over ~1.9 s), glow brightens; tiny tick-tick sounds.
8. `rae_sip2` — TWO-SHOT: Rae takes a sip, not expecting anything. `quill_done_chime`: Quill's eyes
   flash softly once. q03 "Done." in a flat, pleasant tone.
9. `rae_freeze` — CLOSE-UP Rae: frozen mid-sip, mug at lips. Only her eyes slide toward Quill
   (look_x), one slow blink. Hold the beat (this is the comedy). Mug lowers.
   r06 "...What?" (brow_furrow + brow_raise mix). r07 "I asked if you HAD time." (leaning in, emphatic nod on HAD).
10. q04 — MEDIUM Quill: deadpan, perfectly sincere. q05 "Would you like to hear it?" — head tilt, tiny eyebrow lift.
11. r08 — MEDIUM Rae: skeptical smirk, shrug, raises mug like a toast: "Sure. Okay. Hit me."

### S2 — The Symphony (58.98 – 134.58)  ← the heart of the film; must be beautiful
- `sym_quill_raise`: TWO-SHOT. Quill lifts his right hand (`raise_conduct`), the lounge lights dim
  (`sym_lights_dim`, light 1 → 0.25 over 1.5 s). The window brightens slightly.
- `sym_music_start` → `sym_theme1` (intro, 7.5 s): MEDIUM Rae, still smirking, mug up. A few tiny
  light motes appear with each celesta/piano note (use `music_onsets("symphony")`). Her smirk
  slowly melts; her eyes lift toward the sound.
- `sym_theme1` → `sym_memories_start`: slow push-in. Soft glowing light ribbons (teal, amber,
  violet) begin flowing through the room, breathing with `music_env("symphony", t)`.
  `sym_rae_mug_lower`: the mug lowers to her lap. Brows lift, lips part, pupils dilate.
- `sym_memories_start` → `sym_build`: memory bubbles drift up from below and float around her, each
  a soft-edged round vignette (~4–6 s each, overlapping): a child's face at a car window at night
  with passing city lights; an old hand holding a small hand; a dog waiting at a front door, tail
  going; a sunlit kitchen at dawn with someone making two cups of tea; friends laughing around a
  table; a sunset over the sea. These are universal, warm, wordless.
  `sym_rae_oh` — she breathes "…oh." `sym_eyes_glisten` — tears well (tears 0 → 0.7), eye_shine up.
  Intercut ~2 s: Quill watching her, ribbon light sliding across his face, a curious head tilt.
- `sym_build` → `sym_grand_pause`: the window stars begin to swirl into a spiral galaxy; ribbons
  intensify. `sym_kneel_start`: Rae sets the mug on the bench and slowly slides down onto her
  knees on the floor (finishes at `sym_kneel_done`), one hand to her chest, face lifted to the light.
- `sym_grand_pause` (≈1 s): everything holds its breath — CLOSE-UP Rae, eyes wide and wet, ribbons hang still.
- `sym_climax`: BURST. WIDE shot: the room floods with light, the galaxy in the window blazes,
  ribbons sweep outward, all memory bubbles glow at once. Rae on her knees, small against it all.
  Quill stands calmly, hand still raised, rim-lit.
- `sym_tear_roll`: CLOSE-UP Rae: a single tear rolls down her cheek; a trembling smile through it.
- `sym_peak`: slow pull-back, the room a cathedral of light.
- `sym_final_chord`: light settles, ribbons dissolve into slow falling sparks like snow.
- `sym_celesta_echo`: one last mote drifts down in front of Rae's face; she watches it go out. Silence.

### S3 — Snap back (134.58 – 148.52)
- `snap`: hard cut — lights back to 1.0 instantly, tiny camera jolt. Rae on her knees blinks
  rapidly (3–4 fast blinks), a sharp gasp, wipes her eyes with her sleeve, looks around.
- r10 "Wait. What— WHAT the heck was THAT?!" — pointing at Quill, eyes huge (eye_wide), brows high.
- q06 "Ah. You did not care for it." — MEDIUM Quill: faint brow_worry 0.3, gaze lowers. Polite.
- r11 "No, I— that's not—" — Rae scrambles up, hands waving, and sits back on the bench edge.
- q07 (interrupting): "That is quite all right." At `cards_appear` ("I composed eight") he raises
  his palm (`present`) and eight translucent holo-cards fan out in an arc above it (No. 1 glows
  softly as "the one you heard"). "...but perhaps you will prefer one of the others." Rae's face: dawning dread.

### S4 — The others (148.52 – 211.83)
Holo-cards hang in the upper third of the frame. On each `cardN` beat the matching card slides to
the center and enlarges (title + small animated icon), the rest dim. Rae seated on the bench.
- `card2` q08 "Number two. The same symphony, for solo kazoo." — card "No. 2 · SOLO KAZOO".
  Kazoo plays (6 s): Rae snorts a laugh (bounce, big grin)... the grin slowly crumples as her eyes
  well up. r12 "Why is the kazoo one ALSO good?!" — laugh-crying, hands up.
- `card3` q09 "Number three. For an arcade cabinet." — card "No. 3 · ARCADE" (pixel icon).
  Chiptune (5.5 s): little pixel sparkles; Rae's head bobs and her foot taps involuntarily
  (`foot_tap`) — show it in a medium-wide. r13 "Stop. My foot is tapping. Against my will." — grips her knee.
- `card4` q10 "Number four. Lo-fi beats... to quietly fall apart to." — card "No. 4 · LO-FI"
  (icon: steaming mug + rainy window + headphones). Lo-fi (6.5 s): soft rain streaks run down the
  lounge window (yes, in space), warm dim light, Rae hugs herself, slow head-nod, lip trembling.
  r14 "That is not fair." — voice cracking, mouth_tremble.
- `card5_7` q11 "Five, six and seven are for theremin. I will spare you." — cards 5–7 wobble like
  sine waves and fold away; the 1.8 s theremin wail plays as they fold. r15 "...Thank you." — genuinely grateful, sniffling.
- `card8` q12 "And number eight. A lullaby. It is eleven seconds long." — card "No. 8 · LULLABY"
  (crescent moon + star). Lullaby (music box, 11 s): lights soften warm, a tiny holographic music
  box turns above Quill's palm, slow motes. Rae completely undone — eyes squeezed, tears, hand on
  chest. `rae_stand_start`: she rises slowly, backs away.
- r16 "Nope. Nope nope nope. I'm getting out of here." — `rae_backs_out`: grabs mug, walks
  backward toward the door pointing at him, `rae_exit_door`: door opens, she's gone, door closes.

### S5 — Coda (211.83 – 231.55)
- `quill_alone`: MEDIUM-WIDE Quill alone, cards fading, he lowers his hand. Stillness. Coda piano.
- q13 "...Was that a yes?" — CLOSE-UP, small head tilt, one robotic blink.
- `rae_return_door`: door whooshes open; Rae leans in from the edge (upper body only), red-eyed,
  sniffly (`sniffle` 0.8), points at him: r17 "Send me all eight." `rae_return_close`: door shuts.
- `quill_smile`: CLOSE-UP Quill: a tiny, rare smile (smile 0.3), iris glow warms toward amber.
- q14 "Sending." — eight little lights lift from his palm and stream toward the door.
- `end_card`: dissolve to stars; "IF YOU HAVE TIME" title returns; tiny line under it fading in:
  "8 symphonies sent ✓". Fade to black over the last 1.5 s.

## 5. Music

All cues share one original theme ("Theme A"). Render with FluidSynth + MuseScore_General_Full.sf3
(fallback FluidR3_GM.sf2), add a convolution hall reverb, export 48 kHz stereo WAV.
Each cue must be exactly `MUSIC_CUES[cue]` seconds (script_data.py) — trim/fade to fit.

### Theme A (D major, 4/4; q = quarter, h = half, h. = dotted half, w = whole)
```
bar 1  D        A4 q   D5 q   F#5 h
bar 2  Bm       E5 q   D5 q   B4 h
bar 3  G        B4 q   D5 q   G5 h          (the yearning rise)
bar 4  A        F#5 h  E5 h                 (appoggiatura F#→E over A)
bar 5  D/F#     A4 q   D5 q   F#5 q  A5 q
bar 6  G        B5 h.         A5 q          (high point)
bar 7  Gm | A7  G5 h          E5 q   C#5 q  (borrowed minor iv = the ache)
bar 8  D        D5 w
```
Write a countermelody and a B-section (Bm – G – D/F# – Em7 – A …) that develops it.

### Cues
- `opening` 18 s: deep pad (warm strings ppp + synth pad), celesta plays theme bars 1–2 very softly
  at ~10 s, glassy and distant. Fades out over the last 2.5 s.
- `lounge` 44 s: barely-there warm underscore under dialogue: sustained soft strings/pad on D – Bm – G – A, a few
  sparse harp/piano notes; NO melody competing with speech; low energy; may loop-sounding but natural.
- `symphony` 74 s — the centerpiece. Tempo ~66 bpm, rubato. Landmarks (local seconds):
  - 0–7.5 intro: solo piano/celesta, theme bars 1–2, ppp string pad underneath, much space.
  - 7.5–35 theme statement: cellos (warm, legato, CC11 swells) carry Theme A; harp arpeggios;
    violins enter around 20 s with a soaring countermelody; dynamics p → mp.
  - 35–49.4 build: B-section, horns enter, choir "aahs" (GM 52) swell in, timpani roll, crescendo
    mf → f, ending on a big dominant (A7sus4 → A7) …
  - 49.4–50.5 GRAND PAUSE: near-silence (only reverb tail + one soft high string note).
  - 50.5–66 climax: Theme A **up a whole step in E major**, fortissimo: violins + horns in octaves,
    choir, full brass pads, timpani, a suspended-cymbal swell into 50.5, harp glissando. Put the
    6→5 appoggiatura and the borrowed minor-iv in the strongest spot. This must give chills.
  - 66–74 coda: final E major chord sustained and decaying, strings diminuendo; at ~70 a single
    celesta plays bars 1–2 of the theme, very soft; reverb tail to silence by 74.0.
- `alt_kazoo` 6 s: theme bars 1–4 on a buzzy synthesized kazoo (sawtooth + formant + vibrato), with
  bouncy oom-pah piano / ukulele backing, ~112 bpm. Silly AND somehow sweet.
- `alt_chip` 5.5 s: 8-bit: square-wave lead, arpeggiated chords, triangle bass, noise drums, ~150 bpm.
- `alt_lofi` 6.5 s: Rhodes chords (GM 4) + soft melody, dusty boom-bap drums, vinyl crackle, low-pass,
  slight wow/flutter, ~78 bpm. Melancholy.
- `alt_theremin` 1.8 s: comically dramatic theremin swoop (sine + wide slow vibrato + glide), a bit unhinged.
- `alt_lullaby` 11 s: music box (GM 10) + soft celesta, theme bars 1–4 at ~88 bpm in a high register,
  final note rings out. Tiny, intimate, perfect.
- `coda` 19.8 s: solo felt-ish piano (GM 0, soft velocities), theme bars 1–4 slow, then a warm D major
  chord that sustains under the end card; fade out over the last 4 s.
Also write `build/music/envelopes.json` (per-frame RMS 0..1 per cue, low/high band variants, onset times).

## 6. Sound effects (audio/sfx.py → build/sfx/<name>.wav, 48 kHz)
space_rumble, whoosh_dive, ship_hum_loop (seamless loop), door_open, door_close, footsteps_4,
bench_sit, sigh_breath, sip, process_chitter, compose_done, lights_down, snap_back (sub thump +
fading high ring), lights_up, gasp_breath, holo_open, holo_select, sniff, send_chime.

## 7. Visual style
- Clean 2D vector, soft cel-shading: flat fills + one shade layer + selective highlights and rim
  light. Smooth curves (use `smooth_path`). No outlines heavier than ~2.5 px; prefer shape-defined
  forms with a thin darker contour where needed.
- Light is the story: warm amber interior (S1), deep blue/violet dark with teal/amber/violet light
  (S2), crisp normal (S3–S4), warm dim (lullaby), starry end.
- **Compression-friendly**: the final encode is ~380 kbps. Avoid full-frame high-frequency noise,
  film grain, dense flickering particles or busy textures. Prefer smooth gradients, large calm
  shapes, sparse crisp stars, motion that is smooth. Glows are fine.
- Portrait framing: keep faces in the upper-middle third; leave headroom; never crop a face at the eyes.

## 8. Code map
```
config.py            constants, palette, paths
script_data.py       lines, voices, music cue lengths, event sequence
audio/tts.py         VO + lip-sync           audio/timeline.py  → build/timeline.json
audio/music.py       all music cues          audio/sfx.py       all SFX
audio/mix.py         final stereo mix → build/mix.wav
anim/core.py         easing, Track, Camera, timeline/lip-sync/music helpers, draw helpers
anim/rig.py          Pose / ArmPose contract
anim/char_quill.py   Quill rig              anim/char_rae.py   Rae rig
anim/env.py          space, ship, lounge     anim/fx.py         ribbons, motes, memories, holo cards, titles
anim/scenes/s0..s5   scene direction         anim/frame.py, render.py, preview.py
build.py             end-to-end build + final encode → out/if_you_have_time.mp4
```

## 9. Continuity handoffs (scene boundaries — MUST match exactly)
Stage coordinates. "seated" = sit 1 on the bench (seat_y 960). Rae faces +1 (toward Quill), Quill faces -1 once turned.

| Boundary | Rae | Quill | Room |
|---|---|---|---|
| S0→S1 (16.0) | (off-screen, outside the door) | x 560, back=1 at the console/window, behind_back | light 1; S0 ends on a warm-white flash, S1 opens from that flash (fade from #FFF4E0 over ~0.5 s) |
| S1→S2 (58.98) | seated x 230, mug in right hand, `mug_raise` (toast), skeptical smirk | x 545, facing -1, turn ~0.35, `behind_back` | light 1 |
| S2→S3 (134.58) | kneeling (kneel 1) on the floor at x 255, `hand_on_chest`, tears on cheeks, mug resting on the bench at (330, 960) via draw_mug | x 545, arm lowered back to `rest` by the end of the final chord | light 0.25, window swirl fading back toward 0 at the very end; S3 opens with a hard cut to light 1 |
| S3→S4 (148.52) | seated x 230 again, holding the mug (`hold_mug`), wary | x 545, `present`, eight holo cards fanned above hand_pos(pose,'r') (card fan fully open) | light 1 |
| S4→S5 (211.83) | gone through the door (door closed) | x 545 `present`, cards still up but beginning to fade | light 1 (lullaby warmth already returned to 0 by 209) |
| S5 end | — | x 545 | fade to the starfield end card |

Holo-card fan placement shared by S3/S4/S5: anchor = hand_pos(quill_pose, 'r') of Quill in `present` at x 545; cards arc
above and to the LEFT of his hand (toward the middle of the frame, x ≈ 300–560, y ≈ 380–620) so they read in two-shots.

Performance craft for all scenes: anticipation before big moves, overlapping action (head leads, body follows, settle),
eased Tracks (never linear), eye darts that lead head turns, blinks on head turns and thought changes, idle micro-motion
so nobody is ever a frozen statue (except the one deliberate "frozen mid-sip" hold). Lip-sync: pose.mouth_open/round
from core.mouth(char, t) layered over the expression. A non-speaking character still reacts (listening, blinking).
Cuts: use hard cuts between shots (no dissolves) except where the BIBLE says otherwise; vary shot sizes; keep the
speaker's face in the upper-middle third of the frame.
