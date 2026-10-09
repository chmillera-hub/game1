export const meta = {
  name: 'iyht-assets',
  description: 'Build character rigs, environments, FX and music for the "If You Have Time" animated short, each with critique + revision',
  phases: [
    { title: 'Author', detail: 'one agent per asset module' },
    { title: 'Critique', detail: 'independent critic inspects renders / score' },
    { title: 'Revise', detail: 'author-level fix pass on every critic finding' },
  ],
}

const ROOT = '/home/user/game1/if-you-have-time'
const COMMON = `
You are part of a small production team making a 3m52s portrait (720x1280, 24 fps) animated short called
"IF YOU HAVE TIME", generated entirely with code in ${ROOT}.
FIRST read, in full: ${ROOT}/BIBLE.md (story, characters, set layout, shot list, style, music spec),
${ROOT}/config.py (palette + paths), ${ROOT}/anim/core.py (shared helpers: col, paint, smooth_path, Track, Camera,
Layer, light_filter, glow, draw_text, beat/line/mouth/music_env helpers), ${ROOT}/anim/rig.py (Pose / ArmPose contract),
${ROOT}/script_data.py and skim ${ROOT}/build/timeline.json.
Rules:
- Run everything from ${ROOT} with python3 (packages available: skia-python, numpy, scipy, PIL, soundfile, mido, pretty_midi, pyloudnorm; fluidsynth CLI; ffmpeg).
- Do NOT edit shared files (config.py, script_data.py, anim/core.py, anim/rig.py, BIBLE.md, audio/tts.py, audio/timeline.py). Put any extra helpers inside your own module. If you believe a shared contract must change, say so in your final answer instead.
- Only edit the files your task names. Other agents are concurrently writing other modules.
- Put test renders/scripts under ${ROOT}/build/tests/<your-module>/ (gitignored). Look at your PNG renders with the Read tool - actually inspect them and iterate. Contact sheets via anim.preview.sheet_from_fn(fn, times, out, cols, scale, labels) are handy (fn(canvas, t) draws a 720x1280 frame).
- The machine has 4 cores shared with another agent: keep heavy jobs to <= 2 processes.
- Do not git commit. Original IP only - no Star Trek names, insignia, uniforms, sounds or ship designs.
- The final video is encoded at ~380 kbps, so prefer clean shapes and smooth gradients over noise/grain/dense flicker.
Your final answer must be a concise report: what you built, the exact public API (names + signatures + param meanings), how you verified it, and known limitations.`

const CHAR_RULES = `
Quality bar: this must look like appealing, professional 2D animated-series character design (think modern
cartoon feature quality, soft cel shading), not programmer art. Faces carry the film, so expressions, eyelids and
gaze must be nuanced and readable at medium shots AND hold up in extreme close-ups (camera zoom ~3: head ~450px).
Requirements:
- Implement the full rig contract in anim/rig.py: draw(canvas, pose, t), head_center(pose), hand_pos(pose, side), ARMS (all
  presets named in BIBLE.md for this character), HEIGHT. Every Pose field relevant to the character must visibly work.
- Organic construction: smooth_path curves, no gaps or seams at joints (shoulder/elbow/hip/knee/neck), limbs layered
  correctly (far arm behind torso, near arm in front; arms crossing the torso when across>0; behind>0 hides forearms behind body).
- facing=+1/-1 mirror correctly, turn 0..0.7 shifts features/torso convincingly (three-quarter view), head_turn/head_tilt/head_nod work.
- Lighting params: light/tint/tint_amt via a Layer with light_filter; rim>0 adds a soft colored glow around the silhouette (e.g. draw the
  silhouette blurred in rim_color behind the character, plus a thin bright edge). Must look great in the dark symphony scene (light 0.25, rim 0.6).
- Auto blink when lid_* is None; auto breathing when breath is None (subtle chest/shoulder rise).
- Performance: one draw() call should take <= 20 ms at scale 1.
Verification you MUST do (render and LOOK at each, iterate until they are genuinely good):
  1. expression sheet (12+ expressions from the BIBLE list) as close-ups (Camera zoom ~2.6 on head_center),
  2. pose/body sheet (all ARMS presets + the body states listed in the BIBLE for this character) full body,
  3. turn/facing sheet (turn 0, 0.3, 0.6 x facing +1/-1) and head_tilt/nod,
  4. lighting sheet (light 1, light 0.25 + tint + rim 0.6),
  5. markers: draw small dots at head_center(pose) and hand_pos(pose, 'l'/'r') to verify they're accurate in several poses,
  6. lip-sync strip: mouth_open 0..1 x mouth_round 0..1 grid,
  7. time it.`

const ITEMS = [
  {
    key: 'rae',
    file: 'anim/char_rae.py',
    author: `${COMMON}
YOUR TASK: write ${ROOT}/anim/char_rae.py - the full rig for RAE, the human crew member (see BIBLE section 2).
Also export draw_mug(canvas, x, y, scale=1.0, angle=0.0) for the mug when it rests on the bench, and make pose.mug='r'/'l' draw it in that hand (correctly in the 'sip', 'hold_mug', 'mug_raise' poses).
Rae-specific must-haves: walk cycle (pose.walk = phase in cycles; tired shuffle), sit (on bench seat_y=960, legs bent, feet on floor), kneel (0..1 blend; kneeling on the floor, works with hand_on_chest), foot_tap (animated from t), bounce, shoulders_up, mouth_tremble (lip quiver), tears (welling: glossy lower-lid line + larger catch-lights), tear_l/tear_r (a droplet rolling down the cheek with a shiny trail), sniffle (reddish nose tip and puffy lower lids), blush, squint, eye_wide, brows (raise/worry/furrow), smile/smirk.
Required expression sheet entries: neutral, tired half-lidded, skeptical smirk, frozen mid-sip with eyes sliding sideways, confused "what?", shocked eye_wide, awe (pupil 1.3, eye_shine, lips parted), moved to tears (tears 0.7, brow_worry 0.8), tear rolling + trembling smile, laugh-crying, sobbing squeeze (squint 0.8, worry 1), rapid-blink mid-frame, red-eyed sniffly pointing ("send me all eight").
${CHAR_RULES}`,
  },
  {
    key: 'quill',
    file: 'anim/char_quill.py',
    author: `${COMMON}
YOUR TASK: write ${ROOT}/anim/char_quill.py - the full rig for QUILL, the android (see BIBLE section 2).
Quill-specific must-haves: back view (pose.back > 0.5: back of head with neat hair, back of tunic, hands clasped behind back visible; used while he looks out the window), glow (iris luminance + soft bloom around the eyes; at glow 1 the glow lightly spills on the cheeks), process (0..1: thin concentric rings rotating inside the irises + faint flicker, driven by t), restrained brows (max ~40% of a human's range), a "smile" that is barely-there, faint seam lines (temples, jaw hinge, neck) visible mostly in close-up, original insignia (stylized quill feather inside a thin circle) on the left chest, teal collar band + shoulder stripe. Robotic blink via auto_blink(t, robotic=True) when lids are None. Posture: perfectly upright.
Required expression sheet entries: neutral, attentive head tilt, processing (process=1, glow=0.8), "done" glow flash (glow=1), deadpan sincere, faint concern (brow_worry 0.3, gaze down), curious tilt watching (look_x toward Rae), tiny rare smile (smile 0.3, glow 0.5), mid-speech 'oo' and 'ah' shapes, closed-eye blink frame.
Body sheet must include: rest, behind_back, raise_conduct, present (palm up - something will hover above hand_pos), gesture_small, send; and back view with behind_back.
${CHAR_RULES}`,
  },
  {
    key: 'env',
    file: 'anim/env.py',
    author: `${COMMON}
YOUR TASK: write ${ROOT}/anim/env.py - all environments (BIBLE sections 3 and 7). Required public API (keep these exact names/signatures; add optional kwargs if useful):
  Constants: FLOOR_Y=1150, DOOR_CX=-40, DOOR_W=200, DOOR_TOP=430, WINDOW=(90,140,630,860) (x0,y0,x1,y1), SILL_Y=(860,900), BENCH=(40,420) x-range, BENCH_SEAT_Y=960, BENCH_FRONT_Y=1030, CONSOLE_X=(640,720).
  draw_space(canvas, t, drift=1.0, brightness=1.0, offset=(0.0,0.0), zoom=1.0) -> None
      SCREEN SPACE (identity matrix), fills the whole 720x1280 frame: deep space gradient, soft nebula (violet/teal/magenta, smooth),
      3 parallax star layers drifting downward at 'drift' speed (sparse, crisp, a few bright stars with tiny glints; NO dense twinkle noise).
      offset/zoom let a scene push the camera (parallax scales by layer).
  draw_ship(canvas, t, x, y, scale=1.0, angle=0.0, glow=1.0) -> None   and   ship_window(x, y, scale=1.0, angle=0.0) -> (wx, wy)
      The ORIGINAL ship "Meridian" (pearl-white stretched teardrop hull, rotating habitat ring around the middle, two swept-back fins with teal
      light lines, rows of warm amber windows, soft engine glow at the rear). Nose points "up" (toward -y) at angle 0. Must look good from scale 0.3
      to scale 6 (the opening camera dives into one warm window - ship_window returns that window's center so a scene can zoom into it; at large
      scale that window must still look clean: a warm glowing rounded window with a frame).
  draw_lounge(canvas, t, light=1.0, door=0.0, swirl=0.0, window_bright=1.0, rain=0.0, warm=0.0) -> None
      STAGE coordinates (scene applies a Camera; must look right for cameras from zoom 0.7 (wide: x -170..830 visible) to zoom 3.0 close-ups,
      and for vertical cy between 300 and 1100). Draw the whole set BEHIND the characters: walls extending x -400..1120 and y -200..1400 (so no
      void appears at any framing), ceiling light strip, sconces, big arched window x 90..630 y 140..860 showing deep space (reuse your star/nebula
      code, clipped to the window; stars drift very slowly), sill, curved upholstered bench (x 40..420, seat 960, front face to 1030), console
      pillar with glowing panel + softly blinking lights, the sliding door at x -140..60 (door=0 closed .. 1 fully open, showing a lit corridor
      behind), reflective dark floor (y >= 1150) with soft window glow reflection.
      light: 1 = warm amber interior; 0.25 = dark blue symphony lighting where the window becomes the main light source (the window must stay bright).
      swirl 0..1: the stars in the window gradually swirl into a gorgeous spiral galaxy with a bright core (climax of the film - make it beautiful).
      window_bright: multiplier for the window view. rain 0..1: soft rain streaks/droplets running down the window glass (lo-fi gag).
      warm 0..1: shifts the whole room toward cozy warm dim lighting (lullaby).
  draw_lounge_front(canvas, t, light=1.0, door=0.0) -> None
      STAGE coords, drawn AFTER characters: the door frame jambs/wall edge so a character walking through the door at x~-40 is occluded
      correctly by the frame (door opening region shows the character inside the frame; wall left of x=-140 occludes), plus any subtle foreground depth element (keep it minimal and off the main action).
Verification you MUST do (render, LOOK, iterate): space at t=0,5,10; ship at scales 0.4, 1, 3, 6 incl. ship_window marker; lounge at camera
zoom 0.72 (center 330,700), 1.0 (380,760), 1.6 on the bench (230,800), 2.8 near the window top (360,350); light 1 / 0.25; door 0 / 0.5 / 1;
swirl 0 / 0.5 / 1; rain 1; warm 1; a test that draw_lounge_front occludes a placeholder rectangle "person" walking through the door.
Time each function (draw_lounge should be <= 25 ms; cache static layers as skia Pictures or Images where possible, keyed by params).`,
  },
  {
    key: 'fx',
    file: 'anim/fx.py',
    author: `${COMMON}
YOUR TASK: write ${ROOT}/anim/fx.py - light effects, memories, holo-cards and titles (BIBLE section 4: S0, S2, S4, S5). Required public API (exact names; optional kwargs allowed):
  draw_motes(canvas, t, area=(x0,y0,x1,y1), density=1.0, env=0.0, color='amber_soft', seed=0, rise=20.0, alpha=1.0)
      soft floating light dust; env (0..1 music loudness) gently pulses size/brightness. Sparse and smooth (compression-friendly).
  draw_note_sparkles(canvas, t, onsets, area, seed=0, life=1.4, color='teal_glow', alpha=1.0)
      a small sparkle is born at each onset time (absolute seconds list) at a pseudo-random spot in area, blooms and fades over 'life'.
  draw_ribbons(canvas, t, intensity=1.0, env=0.0, area=(x0,y0,x1,y1), seed=0, palette=('teal_glow','amber_soft','#B79CFF'), freeze=0.0, burst=0.0)
      3-6 flowing luminous ribbons (soft-edged, additive, layered glow cores) sweeping through the area along slowly evolving curves; intensity scales
      count/opacity; env makes them breathe; freeze 0..1 slows motion to a hold (grand pause); burst 0..1 sweeps them outward and brightens (climax).
      This is the visual of the symphony: it must look gorgeous and graceful.
  draw_memory(canvas, t, kind, cx, cy, r, alpha=1.0, age=0.0)
      a round soft-edged "memory bubble" (glowing rim, gentle inner vignette, warm desaturated storybook palette) containing a simple, readable,
      wordless illustrated vignette with subtle internal animation driven by age (seconds since it appeared). Kinds (all required):
      'car_window' (a child's face at a car window at night, city lights sliding past), 'hands' (an old hand holding a small child's hand),
      'dog_door' (a dog waiting at a front door, tail wagging), 'kitchen_dawn' (sunlit kitchen at dawn, someone pouring two cups of tea, steam),
      'friends_table' (friends laughing around a table under a warm lamp, silhouettes), 'sea_sunset' (sunset over the sea, gentle waves).
      These must be legible at r=110 and lovely at r=200.
  draw_holo_card(canvas, t, cx, cy, scale=1.0, number=1, title='', icon='symphony', state=0.0, alpha=1.0, wobble=0.0, fold=0.0)
      translucent teal hologram card (~170x230 at scale 1): number "No. N" + title in caps + an animated vector icon; state 0 = idle/dim,
      1 = selected (brighter, glow, slight scale-up); wobble 0..1 makes it ripple like a sine wave (theremin gag); fold 0..1 folds it away into a line and vanishes.
      icons: 'symphony' (sheet-music swirl / violin scroll), 'kazoo', 'arcade' (pixel heart / joystick), 'lofi' (steaming mug + rainy window + headphones),
      'theremin' (antenna + wavy line), 'lullaby' (crescent moon + star).
  draw_card_fan(canvas, t, cx, cy, progress, alpha=1.0, numbers=range(1,9), titles=None, icons=None, wobble_set=(), fold_set=(), fold=0.0, wobble=0.0, focus=None, focus_amt=0.0)
      convenience: fans eight cards in an arc above (cx, cy) (progress 0..1 = spreading out from the palm); 'focus' = number of a card to pull to
      center-front and enlarge by focus_amt (0..1) while others dim.
      Default titles: 1 'SYMPHONY', 2 'SOLO KAZOO', 3 'ARCADE', 4 'LO-FI', 5 'THEREMIN I', 6 'THEREMIN II', 7 'THEREMIN III', 8 'LULLABY'.
  draw_music_box(canvas, t, cx, cy, scale=1.0, alpha=1.0)   small holographic music box with a turning cylinder/tiny dancer star.
  draw_title(canvas, t, text, cy, alpha=1.0, size=44, sub=None, sub_alpha=0.0)   SCREEN space, thin widely-tracked caps (Inter Display weight 200-300) with soft teal glow.
  draw_flash(canvas, amount, color='#FFF4E0')   SCREEN space full-frame flash.
  draw_vignette(canvas, amount=0.5)   SCREEN space soft dark edges (smooth radial gradient).
  draw_light_burst(canvas, t, cx, cy, amount, color='#FFF1D6')   soft god-rays + bloom radiating from a point (climax). Smooth, no harsh stripes.
  draw_falling_sparks(canvas, t, area, amount, seed=0)   slow drifting/falling glowing sparks like snow (end of symphony).
  draw_send_lights(canvas, t, progress, src, dst, n=8)   eight small warm lights lifting from src and streaming in gentle arcs to dst, staggered.
  draw_pixel_sparkles(canvas, t, area, amount, seed=0)   chunky 8-bit style sparkles/pluses (arcade gag).
  draw_rain_streaks(canvas, t, area, amount)   (optional if env does rain; can be used in front of the window).
Verification you MUST do (render, LOOK, iterate): a contact sheet of each memory kind at r=110 and r=200 at a few ages; ribbons over a dark
blue background at intensity 0.3/0.7/1.0, freeze 1, burst 1, across ~8 seconds; motes + note sparkles; the card fan at progress 0/0.5/1, with focus,
with wobble and fold; music box; title; light burst; falling sparks; send lights. Time them (ribbons <= 15 ms, memories <= 8 ms each; cache static
illustration parts as skia Pictures).`,
  },
  {
    key: 'music',
    file: 'audio/music.py',
    author: `${COMMON}
YOUR TASK: write ${ROOT}/audio/music.py - composes AND renders every music cue in BIBLE section 5 (see MUSIC_CUES in script_data.py for exact lengths).
Running "python3 audio/music.py" must produce build/music/<cue>.wav for every cue (48 kHz, stereo, float32, EXACTLY MUSIC_CUES[cue] seconds),
build/music/envelopes.json  ({cue: {"rms": [per-frame 0..1 at 24 fps], "low": [...], "high": [...], "onsets": [local seconds of melody/celesta/piano note onsets]}}),
and build/music/score_<cue>.txt - a human-readable score dump (per bar: chord symbol, then each instrument's notes with beat positions & velocities).
Also support "python3 audio/music.py symphony alt_kazoo" to render only selected cues.
Approach:
- Compose with code as MIDI (mido or pretty_midi). Render orchestral/GM cues with the fluidsynth CLI using /usr/share/sounds/sf3/MuseScore_General_Full.sf3
  (fallback /usr/share/sounds/sf2/FluidR3_GM.sf2). First list the soundfont presets (e.g. fluidsynth with a script, or parse) and pick the best
  ones (Strings ensemble / slow strings / solo cello / violins / French horns / brass section / choir aahs / timpani / harp / celesta / piano /
  music box / Rhodes / glockenspiel / suspended cymbal on the GM drum channel).
- Synthesize in numpy what GM lacks: kazoo (bright sawtooth + nasal formant filters + vibrato + buzzy amplitude jitter), chiptune (band-limited
  square/pulse lead with duty changes, arpeggios, triangle bass, noise-channel drums), theremin (sine with wide expressive vibrato + portamento).
- Make it MUSICAL, not mechanical: use Theme A exactly as written in the BIBLE, good voice leading (no parallel 5ths/8ves in outer voices,
  resolve leading tones/7ths, sensible chord voicings spaced wider in the bass), idiomatic ranges for every instrument, humanized timing
  (+-8 ms), velocity shaping following phrase arcs, legato overlaps for strings, CC11/CC7 expression swells (crescendo into phrase peaks),
  rubato via tempo map (slight ritardando into cadences and into the grand pause). Orchestrate so the climax in E major is huge but not muddy.
  Effective "chills" devices: the appoggiatura, the borrowed minor iv, the sudden pianissimo before the swell, the entrance of choir and new
  register, the key change up a whole step, the long suspension resolving late. The symphony's dynamic landmarks (local seconds) must match
  the BIBLE exactly because the animation is locked to them: intro 0-7.5, theme 7.5-35, build 35-49.4, GRAND PAUSE 49.4-50.5 (near-silent),
  climax 50.5-66 (loudest), coda 66-74 (celesta echo at ~70, decaying to silence by 74).
- Post: convolution hall reverb (synthesize a stereo decaying-noise impulse response, ~2.6 s for the symphony, smaller rooms for the alternates,
  lo-fi gets low-pass + wow/flutter + vinyl crackle), gentle bus compression, peak <= -1 dBFS. Symphony integrated loudness ~ -18 LUFS with
  the climax ~ -12 LUFS short-term; alternates ~ -16 LUFS. Fade tails cleanly so no cue is chopped.
- The alternates must be immediately recognizable as Theme A in a new genre, and each should be genuinely good (that's the joke).
Verification you MUST do: assert exact durations; print peak/LUFS per cue; render a spectrogram + RMS-envelope PNG per cue (matplotlib may not be
installed - use PIL/numpy) and LOOK at it to confirm the symphony landmarks (quiet intro, growth, grand-pause dip at 49.4-50.5, loudest climax,
decay); read back your score dumps and check harmony against the melody bar by bar; check no notes outside instrument ranges. Fix anything wrong.`,
  },
]

function critiquePrompt(item, authorReport) {
  if (item.key === 'music') {
    return `${COMMON}
YOUR TASK: you are an exacting orchestrator/composer acting as CRITIC for ${ROOT}/audio/music.py (the music for the film). You cannot listen,
so review it the way a conductor reads a score, plus measurements. The author reported:
---
${authorReport}
---
Do: (1) read audio/music.py fully; (2) run it if outputs are missing; (3) read build/music/score_*.txt and check bar by bar: does the melody
match Theme A from the BIBLE exactly; are chords correct under the melody; unresolved/unintended clashes (melody vs harmony semitone rubs not
intended as appoggiaturas), parallel 5ths/8ves in outer voices, muddy low voicings (close thirds below ~C3), instruments out of range,
mechanical uniform velocities/timings, missing expression swells; (4) check the symphony form/dynamics against the landmarks (intro 0-7.5,
theme 7.5-35, build 35-49.4, grand pause 49.4-50.5 near silent, climax 50.5-66 loudest in E major, coda 66-74 with celesta echo ~70) using the
RMS envelope in build/music/envelopes.json and the spectrogram PNGs (view them with Read); (5) check exact cue lengths, peaks <= -1 dBFS,
loudness targets, no clicks at cue start/end (check first/last 20 ms), stereo not collapsed, reverb tails not truncated; (6) judge whether each
alternate (kazoo, chip, lofi, theremin, lullaby) is recognizably Theme A and stylistically convincing given its synthesis method.
Do NOT edit files. Return a prioritized list of concrete, actionable defects (most important first), each with location (cue, bar/time,
instrument, code function) and the specific fix.`
  }
  return `${COMMON}
YOUR TASK: you are a demanding animation art director acting as CRITIC for ${ROOT}/${item.file}. The author reported:
---
${authorReport}
---
Do: read the module; then write your OWN test renders under ${ROOT}/build/tests/critic_${item.key}/ that stress it (don't just reuse the author's
sheets): every API function/param listed in the task spec below, extreme-but-valid params, combinations used by the shot list in BIBLE section 4 for this
asset, cameras from wide (zoom 0.72) to extreme close-up (zoom 3), both facings, low light + rim. LOOK at every render with Read.
Judge against: BIBLE design spec; appeal and professional polish; anatomy/construction (gaps, seams, broken joints, wrong layering, limbs bending
the wrong way, floating parts); expression readability and nuance (eyelids!); consistency of proportions across poses; correctness of anchors
(head_center/hand_pos markers etc.); compression-friendliness; performance (time it).
The original task spec was:
=== SPEC ===
${item.author}
=== END SPEC ===
Do NOT edit ${item.file}. Return a prioritized list of concrete defects (most important first). For each: what is wrong, exact params/camera to
reproduce, the path of the PNG showing it, and the concrete fix.`
}

function revisePrompt(item, authorReport, critique) {
  return `${COMMON}
YOUR TASK: you own ${ROOT}/${item.file} now. Another agent wrote it and an independent critic reviewed it. Fix EVERY defect the critic raised
(unless it is factually wrong - then explain why), and anything else you notice, while keeping the public API intact. Then re-run the full
verification (render and LOOK at the sheets / re-check the measurements) and iterate until it is genuinely high quality.
Original task spec:
=== SPEC ===
${item.author}
=== END SPEC ===
Author's report:
---
${authorReport}
---
Critic's findings:
---
${critique}
---
Final answer: the updated public API, what you fixed, verification evidence (paths of final sheets), and remaining limitations.`
}

const NEEDS_CRITIC = new Set(['rae', 'quill', 'music'])

const results = await pipeline(
  ITEMS,
  item => agent(item.author, { label: `author:${item.key}`, phase: 'Author' }),
  (report, item) => NEEDS_CRITIC.has(item.key)
    ? agent(critiquePrompt(item, report), { label: `critic:${item.key}`, phase: 'Critique' }).then(c => ({ report, critique: c }))
    : { report, critique: null },
  (r, item) => r.critique
    ? agent(revisePrompt(item, r.report, r.critique), { label: `revise:${item.key}`, phase: 'Revise' }).then(f => ({ key: item.key, report: r.report, critique: r.critique, final: f }))
    : { key: item.key, report: r.report, critique: null, final: r.report },
)
return results
