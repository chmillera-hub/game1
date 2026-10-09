export const meta = {
  name: 'iyht-scenes',
  description: 'Direct and animate every scene of "If You Have Time" (4 scene owners), then critique + revise each',
  phases: [
    { title: 'Animate', detail: 'one director-animator per scene group' },
    { title: 'Critique', detail: 'independent art director + editor review of rendered frames' },
    { title: 'Revise', detail: 'fix every finding, re-verify' },
  ],
}

const ROOT = '/home/user/game1/if-you-have-time'

const COMMON = `
You are a director-animator on a small team making a 3m52s portrait (720x1280, 24 fps) animated short, "IF YOU HAVE TIME",
generated entirely with code in ${ROOT}. All assets are finished; your job is DIRECTION + ANIMATION of specific scenes.
FIRST read in full: ${ROOT}/BIBLE.md (especially section 4 shot list and section 9 continuity handoffs), ${ROOT}/anim/core.py,
${ROOT}/anim/rig.py, ${ROOT}/script_data.py, ${ROOT}/build/timeline.json (all beat/line times), and the public APIs of
${ROOT}/anim/char_quill.py, ${ROOT}/anim/char_rae.py, ${ROOT}/anim/env.py, ${ROOT}/anim/fx.py (read their docstrings and
function signatures; read implementation where needed to use them correctly). Also read the asset owners' reports (APIs, usage notes, limitations): ${ROOT}/build/asset_reports.md
How scenes work: anim/scenes/<sid>.py exposes render(canvas, t) for absolute time t inside the scene span (anim/scenes/__init__.py,
anim/frame.py). The canvas arrives cleared to black with identity matrix; you apply Camera(...).apply(canvas, t) for stage drawing
(env.draw_lounge -> characters -> env.draw_lounge_front -> stage fx), then canvas.resetMatrix() for screen-space fx/titles/flash.
Always reference times by name: beat('...'), line_start('q04'), line_end(...), scene_span('s2'); never hard-code absolute seconds
(local offsets relative to beats are fine). Use core.mouth(char, t) for lip-sync (add to the pose's mouth_open/mouth_round).
Use Track for keyframed animation with easing. Module-level caches are fine; render(canvas, t) must be a pure function of t
(frames are rendered out of order in parallel processes).
Rules:
- anim/char_quill.py and anim/char_rae.py are receiving a final visual-polish pass by their owners right now (public API is stable: Pose fields,
  ARMS preset names, draw/head_center/hand_pos). If an import or draw momentarily fails or a frame looks mid-edit, wait ~1 minute and retry;
  do not build workarounds for transient breakage. Likewise build/music/*.wav and envelopes.json may be regenerated (landmark timings are fixed).
- Edit ONLY the scene files assigned to you. Do not edit assets (char_*.py, env.py, fx.py), core.py, rig.py, script_data.py, BIBLE.md.
  If an asset has a bug or missing feature that blocks you, work around it inside your scene file and clearly report it.
- Test renders under ${ROOT}/build/tests/<your-scene>/ (gitignored): python3 -m anim.preview sheet OUT.png t1 t2 ... --cols 6 --scale 0.3
  or anim.preview.sheet_from_fn. LOOK at every sheet with the Read tool, judge it like a film director, and iterate.
- 4 CPU cores shared with another agent: at most 2 heavy processes.
- Do not git commit. Original IP only.
- Compression: the final encode is ~380 kbps; avoid full-frame noise/grain/rapid flicker; smooth camera moves are fine.
- Budget: average <= 150 ms per frame for your scenes (time it).
Craft bar: this should feel like a polished animated short. Performance (acting) is everything: anticipation, overlapping action,
eased motion, eye darts and blinks that read as thought, faces in the upper-middle third of the portrait frame, readable staging,
varied shot sizes with motivated cuts, lip-sync on every line, listeners reacting, no frozen statues, no popping, no characters
clipped awkwardly, nothing floating (mug in hand or on the bench), correct layering (door frame occludes; mug in front of hand when held).
Facial expressions and eyelid/eye movement must be nuanced and frequent but not excessive.
Verification you MUST do: (1) contact sheets covering your whole span every ~0.5 s (several sheets) - look at all of them;
(2) dense sheets (every frame, 12-24 consecutive frames) around each cut, each big move and each line start to check motion
continuity and lip-sync; (3) frames at the first and last frame of your scene(s) to check the continuity handoff in BIBLE section 9;
(4) timing per frame. Fix everything you find.
Final answer: shot list as implemented (time ranges -> shot/camera/action), what you verified (sheet paths), known issues.`

const GROUPS = [
  { key: 's2', files: 'anim/scenes/s2.py', task: `Animate S2 "The Symphony" (scene s2) per BIBLE section 4 S2 and the S1->S2 / S2->S3 handoffs. This is the heart of the
film and must be genuinely beautiful and moving. Sync everything to the sym_* beats and to the music: use music_env("symphony", t)
(rms/low/high) to make light breathe, music_onsets("symphony") for note sparkles. Lights dim at sym_lights_dim; motes with the first notes;
ribbons from sym_theme1; mug lowers at sym_rae_mug_lower; memory bubbles (all six kinds, staggered, drifting up and around her, 4-6 s each,
overlapping, not covering her face) from sym_memories_start; "...oh" at sym_rae_oh (lip-sync r09); tears well from sym_eyes_glisten; a 2 s
intercut of Quill watching; galaxy swirl in the window from sym_build; she sets the mug on the bench and slides to her knees from
sym_kneel_start to sym_kneel_done (slow, natural: shift weight forward, one knee then the other, hand to chest); grand pause hold
(freeze ribbons) at sym_grand_pause; the BURST at sym_climax (wide, light burst, ribbons burst, galaxy blazing, rim light on both characters);
tear roll close-up at sym_tear_roll with a trembling smile; pull back at sym_peak; dissolve to falling sparks at sym_final_chord; final mote
at sym_celesta_echo that she watches go out; Quill lowers his hand. Use rim light + low light on the characters (light ~0.3, tint deep blue,
rim colored by the nearest light). Camera: slow, graceful moves (push-ins, a gentle drift), a few motivated cuts on musical phrase boundaries.` },
  { key: 's1', files: 'anim/scenes/s1.py', task: `Animate S1 "The ask" (scene s1) exactly per BIBLE section 4 S1 (11 numbered shots) and the S0->S1 and S1->S2 handoffs.
Key moments: tired entrance + walk cycle through the door (door opens/closes in sync with the door SFX beats, draw_lounge_front occludes her
at the door), plop onto the bench; Quill's turn from back view (cut on the turn); the wistful push-in on Rae for r03-r05; Quill's processing
close-up (process/glow tracks synced to quill_process_start and quill_done_chime); the comic freeze mid-sip with only the eyes sliding;
deadpan Quill; skeptical toast "Hit me." ending in the mug_raise handoff pose.` },
  { key: 's34', files: 'anim/scenes/s3.py and anim/scenes/s4.py', task: `Animate S3 "Snap back" (scene s3) and S4 "The others" (scene s4) per BIBLE section 4 and the S2->S3, S3->S4, S4->S5
handoffs. S3: hard snap at beat 'snap' (light 1, small camera jolt), rapid blinks, gasp, wiping eyes, the pointing "WHAT the heck was THAT?!",
Quill's polite concern, Rae scrambling up and sitting back down picking up the mug, cards fanning out at cards_appear from Quill's palm
(fx.draw_card_fan). S4: each cardN beat focuses that card (draw_card_fan focus) with a holo_select feel; Rae's escalating reactions exactly as
in the BIBLE: kazoo (snort-laugh -> welling up -> laugh-crying r12), arcade (pixel sparkles, head bob + foot_tap in a medium-wide, grips knee on
r13), lo-fi (rain on the window via draw_lounge(rain=...), warm dim, hugging herself, lip tremble on r14), theremin (cards 5-7 wobble then
fold away during the theremin cue; Rae flinches; grateful "...Thank you."), lullaby (warm=1 dim light, music box hologram above Quill's palm,
Rae undone: eyes squeezed, tears, hand on chest; rises at rae_stand_start), "Nope..." r16 backing to the door pointing at him while grabbing
the mug, exiting at rae_exit_door with the door opening and closing (draw_lounge_front occludes). Use wider shots when needed so the door
(x -140..60) and Quill (x 545) are both readable. Keep comic timing crisp: cut to Rae's reaction while each alternate plays.` },
  { key: 's05', files: 'anim/scenes/s0.py and anim/scenes/s5.py', task: `Animate S0 "Cold open" (scene s0) and S5 "Coda" (scene s5) per BIBLE section 4 and the handoffs.
S0: env.draw_space starfield (screen space) + the Meridian gliding up from the lower left with its ring turning; title "IF YOU HAVE TIME"
via fx.draw_title between title_in and title_out (gentle fade + drift); from dive_start the camera pushes into one warm window
(env.ship_window gives its position; accelerate; the window fills the frame by ~15.4 and flashes warm white #FFF4E0 to the end of S0, which
S1 opens from). The whole thing should feel calm, vast and gorgeous. S5: Quill alone (cards from S4 fading out over the first ~1.5 s,
he lowers his hand to rest), q13 close-up head tilt + robotic blink, door whoosh at rae_return_door: Rae leans in through the door opening
(upper body only, red-eyed sniffle 0.8, pointing) for r17 then withdraws and the door closes at rae_return_close (use a wide or a shot that
shows the door and Quill), quill_smile close-up (tiny smile + warm glow), q14 "Sending." with fx.draw_send_lights from his palm toward the
door, then end_card: dissolve to the starfield with the title returning and the small line "8 symphonies sent ✓" fading in below it, and
fade to black over the last 1.5 s.` },
]

function animPrompt(g) {
  return `${COMMON}
YOUR ASSIGNMENT (files you own: ${g.files}):
${g.task}`
}

function critiquePrompt(g, report) {
  return `${COMMON}
YOUR TASK: you are an exacting animation director + film editor acting as CRITIC for ${g.files}. Do NOT edit any files.
The scene owner reported:
---
${report}
---
Their assignment was:
${g.task}
Render your OWN review sheets under ${ROOT}/build/tests/critic_${g.key}/: the whole span every 0.25-0.5 s, dense consecutive-frame strips
around every cut/line start/big move, and the boundary frames with the neighboring scenes (if the neighbor scene file exists, render the last
frames of the previous scene and first frames of the next to check continuity per BIBLE section 9). LOOK at every sheet.
Judge: does every BIBLE beat happen, on time, readably; acting quality (expressions, eyelids, gaze, blinks, anticipation, settle, listener
reactions, lip-sync visibly moving during every line and closed otherwise); staging/composition in portrait (faces in upper-middle third,
nothing awkwardly cropped, clear silhouettes); camera motion smoothness and cut motivation; glitches (pops, jitter, floating props, wrong
layering, background voids at frame edges, hands through objects); lighting continuity; emotional effect; compression-friendliness; frame time.
Return a prioritized list of concrete defects (most important first): time(s), what is wrong, the sheet path showing it, and the concrete fix.`
}

function revisePrompt(g, report, critique) {
  return `${COMMON}
YOUR TASK: you own ${g.files}. Fix EVERY defect the critic raised (unless factually wrong - then explain), plus anything else you notice,
then re-run the full verification (sheets: whole span, dense strips at cuts/lines, boundary frames; LOOK at them) and iterate until it is
genuinely polished. Assignment:
${g.task}
Owner's report:
---
${report}
---
Critic's findings:
---
${critique}
---
Final answer: updated shot list, what you fixed, verification sheet paths, remaining issues.`
}

const results = await pipeline(
  GROUPS,
  g => agent(animPrompt(g), { label: `animate:${g.key}`, phase: 'Animate' }),
  (report, g) => agent(critiquePrompt(g, report), { label: `critic:${g.key}`, phase: 'Critique' }).then(c => ({ report, critique: c })),
  (r, g) => agent(revisePrompt(g, r.report, r.critique), { label: `revise:${g.key}`, phase: 'Revise' })
    .then(f => ({ key: g.key, report: r.report, critique: r.critique, final: f })),
)
return results
