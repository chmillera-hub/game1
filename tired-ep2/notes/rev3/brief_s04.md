THIS IS A REVISION PASS (rev 3). scenes/s04_not_my_problem.py already exists and works: you (or an earlier animator) built it, and the user watched rev 2 and gave the notes below. READ THE EXISTING FILE FIRST. Keep everything that works EXACTLY as it is and change only what the notes ask. The user values precise, isolated edits: "even a slight movement of the eye can alter the scene immensely". So do not re-time or re-act beats the notes don't mention, beyond what re-keying to the new cues forces.

script.json has ALREADY been updated (new and changed lines, new pause beats) and the TTS is re-recorded; the current cue times are in out/timeline.json. Re-key everything to the new cues and fix any KeyError or overlap the new beats cause.

LENGTH: there is NO length limit any more (user's instruction). Never tighten pauses or cut beats. If a new beat needs more air, lengthen YOUR scene's pause beats with engine/scriptedit.update_scene('s04', fn) and report it. Don't rush anything; the user found the old cuts too fast to follow.

Rig changes already made by the lead, which you should not undo:
- The band-aids on Tiredness's face are now foreshortened with the head turn so they sit flat on the skin. The cheek one is drawn only when the face shows enough.
- The Boss's lip outline is thinner and the lip colour softer.
- The corporation is now CALMCORP / CalmCorp everywhere (the engine and sets are already renamed). If your scene draws any company text itself, use CALMCORP on signs and logos and CalmCorp in prose.

Concurrency: other animators are revising other scenes at the same time.
- Do NOT edit engine/* or audio/*, except for the narrowly scoped additive change explicitly granted below (if any). An additive change means a new keyword argument, default off, after which every other scene's output is pixel-identical.
- Do NOT edit other scenes, script.json or build.py.
- Do NOT run git.
- Scratch files go under preview/ prefixed with s04_.

THE USER'S NOTES FOR YOUR SCENE (satisfy every one):
The script was extended (see out/timeline.json); the scene is now 62.35 s. The new or changed beats, in order:
- s04_l02c, NEW, tired, right after "I have to take care of me first... before I can take care of anyone else.": "...But I don't want to abandon you."
  - Poignant. He turns to look at the creature (pupils lead, head follows); his voice is quiet.
  - The creature's ears lift slightly with a flicker of hope. That hope makes the following 'tug' (the creature tugging him to come) and its later hurt reaction land harder.
- s04_l04b, CHANGED: "Maybe even me. ...I need time to think." It's slower; he's processing that his own life could be on the line. A small, scared inward look: eyes drop and go unfocused, a swallow, his hand tightens. Hold it.
- 'hurt', 'leave', 'alone' and s04_l05 "...Ugh." (the groan) stay as they are.
- 'follow' is now 0.8 s. CHANGE: he does NOT get up and walk off here any more. Still sitting on the crate, he lifts his head and looks toward the dark side tunnel where the creature went. Its two teal eyes glow in the dark a little way down the tunnel (fx.eyes_in_dark, as now): it waited for him, hoping. The creature STAYS in the tunnel (eyes only) until the end of the scene; this matters for s05.
- s04_l06, NEW, tired: "Okay. I'll help. Hell or high water." He commits to the eyes in the dark. It's quiet resolve, not heroic; he's tired but sure.
- 'glance' (1.2 s): a sad glance, down at his hands or bandage and then back to the eyes in the dark. Subtle and readable.
- s04_l06b, NEW, tired: "...I hope we make it out of this." It's sad and honest, a quiet fear. The teal eyes in the dark answer with a slow blink and drift a little closer (a comfort beat at a distance).
- 'hush' (0.9 s): a quiet moment; they share the look across the dark.
- s04_l07, NEW, embar, OFF-SCREEN, terrified: "Oh my God! What IS that thing?!" It's loud and clear and comes from deeper in that same tunnel: Emb, coming from the other end, has just stumbled on the creature.
  - Tiredness's head snaps toward the tunnel, and the creature's eyes whip away from him toward the voice.
  - A shaky flashlight beam can flick across the tunnel's depth.
  - An SFX of a far-off startled stumble or flashlight clatter is fine if it helps.
- 'sighup' (1.0 s): Tiredness SIGHS (a visible exhale, his shoulders drop) and GETS UP (anticipation lean-forward, the push up off his knees, standing). He can't let the creature get hurt or let Emb panic.
- 'go' (2.2 s): he walks into the dark side tunnel after the voice. A walk cycle matched to travel speed.
- At the start of s05 he arrives where Emb has his flashlight on the creature; the s05 animator is building that, so end s04 with him walking into the dark tunnel.
- The music cue is 'lonely' with follow= at the old 'follow'. The lead will retune it; ignore it.
- Also check every frame of the get-up and the walk: both of his hands must ALWAYS be visible (or clearly occluded by his own body in a natural way). The user saw a hand go missing near here in the old cut.
Every other beat stays exactly as it is. Then re-check the scene with sheets and run `python3 build.py scene s04`.

The project's general brief follows (it was written for the first build; the revision notes above take precedence).
------------------------------------------------------------------------
You are a senior 2D animator on a procedural portrait (9:16) cartoon, "TIREDNESS — Episode 2: Lights Out". Project root: /home/user/game1/tired-ep2. Everything is Python + cairocffi; you write one scene module.

Read before coding (all of them, carefully):
- SPEC.md — production bible + tech contract (logical 1080x1920 canvas, 24 fps, safe zones x 60..930 / y 120..1330, caption band ≈1330–1560, bitrate rules, gesture-safety rules).
- DIRECTION.md — the top "Acting principles" + "Transitions" sections, YOUR scene's section, and the neighbouring scenes' sections (for continuity of positions, props, outfits).
- API_human.md (people rig), API_creatures.md (Impulsivity / the thing / the creature), API_sets.md (sets + props, stage MARKS), API_fx.md (effects, UI screens, name tags, end card), API_audio.md (SFX names, music cues).
- script.json (your scene's beats: lines, cues, pauses) and out/timeline.json (real timings; every line id is a cue, plus '<id>.end').
- engine/core.py (helpers incl. camera(), cached(), state_at, tween, seg, ease_out_back). Open the engine sources when you need details.

THE USER'S FEEDBACK ON EPISODE 1 (most important — read SPEC.md §0 LESSONS): it felt RUSHED; lines and beats went by too fast to follow. This episode must breathe: one idea per shot, hold reactions, let the viewer read every face. Physical cause→effect must be visible (no characters appearing in odd places). Clear unambiguous gestures (big shrug, nod, point sideways with thumb visible, small bent-elbow wave). NO butt emphasis or butt-up/rear-view poses anywhere. NO hand/arm z-order flicker between consecutive frames — check frames where hands cross. Mysterious things stay mysterious. Shakes/impacts long enough to register (≥0.6 s, room reacts). Characters don't say each other's names unless natural.

Hard rules:
- Scene module = scenes/s04_not_my_problem.py exposing render(ctx, t, info) and SFX(info) -> [(t, name, gain_db[, pan]), ...] (scene-local seconds; names must resolve in audio/sfx.py — check with `python3 -c "from audio import sfx; print(sfx.resolve('name'))"`). Optional CAPTION_Y or caption_y(t, info) (return None to hide captions, e.g. under a title card).
- NEVER hard-code dialogue times: derive all timing from info.cue(...) / info.line(id).start/.end. Audio may be re-recorded.
- Lip-sync: pass info.mouth(who, t) to the speaking character's rig as `mouth=` (who ∈ tired, embar, boss, guard, recep). A non-speaker gets (0,0) automatically. Muffled off-screen lines (fx muffled) have no visible mouth unless the speaker is on screen.
- ACTING IS THE POINT. Every line and reaction gets keyed expressions (core.state_at, 0.15–0.35 s transitions), eye acting (pupils lead, head follows ~0.15 s later; look at the thing being judged; slow blinks on judgement beats), held reactions ≥ 0.5 s, and SUBTLE moves where the direction asks (a 0.1 lid drop, one brow lifting, eyes sliding then returning, lip press). Use the rig's `face=` additive deltas for these. Never freeze a face unless the direction says the freeze is the joke (Impulsivity, the lightning freeze). Respect the Tiredness eyelid rule (lids ~45% closed; only lift where DIRECTION says).
- Body acting: anticipation before big moves, overshoot/settle (ease_out_back), squash & stretch on impacts, follow-through, weight. Cycles (walk/run/tiptoe/crawl) must match travel speed (no foot sliding where feet are visible).
- Staging for phones: one idea per shot, big readable silhouettes, faces large and inside y 160..1300; nothing important in the bottom 330 px / right 150 px; keep the caption band (≈1330–1560) visually calm (floor/background/legs fine). Use cuts between shots (shot lists in DIRECTION) — a static wide shot for a whole scene is NOT acceptable; cut or move the camera when the STORY moves (typically every 2.5–5 s); held shots where only faces act are welcome; never cut so fast the viewer can't read the face.
- Continuity: match outfits/props/positions with neighbouring scenes (bandage from s10 on, headphones state, the cage, the broken window, damage on the street, etc.).
- Bitrate (final film must be < 15 MB): sets are static and cached (core.cached / the sets API), no full-screen noise/grain, no constant camera shake (short shakes ≤ 0.6 s OK), ≤ ~20 small moving particles, slow camera push-ins/pans fine, flashes ≤ 3 frames, no strobing.
- Gesture safety: no straight raised arm with flat palm; no lone middle finger; points show the thumb and aim sideways/down. No gore. No profanity on screen.
- Timing beats: if a visual beat truly needs more (or less) time, use engine/scriptedit.update_scene('s04', fn) to adjust YOUR scene's pause/cue beats or head/tail (it is locked and rebuilds the timeline). Stay within your scene's allowance (no length limit; lengthen your own pause beats if needed and report it). You may not change spoken lines; propose line changes in your report. Never write script.json directly.
- Only edit scenes/s04_not_my_problem.py (and scratch files under preview/ prefixed with s04_). Do NOT edit engine/* (except the explicit grant in the revision notes above, if any), audio/*, build.py, other scenes. Do NOT run git. If a rig/prop/fx bug blocks you, work around it inside your scene (e.g. draw a small custom shape) and report it precisely.
- Deterministic (no unseeded randomness). Performance: average < 60 ms per frame at 720x1280.

Tools:
- `cd /home/user/game1/tired-ep2 && python3 build.py sheet s04 --n 16 --cols 4` → preview/sheet_s04.png
- `--times 1.2,3.4,...` for exact moments; `--out preview/s04_x.png` to keep multiple sheets; `--nocap` to hide captions.
- `python3 build.py still s04 <t> --scale 0.6 --out preview/s04_still.png` for a big single frame (use for face close-ups to judge subtle acting).
- `python3 build.py scene s04` renders the real segment (proves every frame renders; prints time).
- LOOK at PNGs with the Read tool. Judge at phone size AND at a big still for faces.

YOUR SCENE: s04 (module scenes/s04_not_my_problem.py), duration ≈ 62.4 s, music "lonely". Previous scene: s03 (stealth); next scene: s05 (calculator).

Do this:
1. Read the materials. Write a shot list for your scene against the real cue/line times (out/timeline.json), following your DIRECTION.md section.
2. Implement scenes/s04_not_my_problem.py fully — every beat in the direction, with appeal and the acting described.
3. Review loop (at least 4 rounds): render a 16-frame sheet + a --times sheet at every line start+0.3 s and middle and every cue +0.15 s; plus big stills of key faces. Critique as a picky animation director: does each beat read to a muted phone viewer (captions + picture)? Expressions match the emotion and change on the right beat? Eyes looking at the right things? Subtle beats visible at phone size? Mouth moving only for the speaker? Silhouettes clear, z-order right, nothing clipped, no stray strokes, continuity ok, transitions connect, no dead stretch > 1.5 s without motion. Fix; repeat.
4. Add SFX synced to visual hits (footsteps, impacts, cloth, doors, creature sounds) — tasteful, not wall-to-wall.
5. Run `python3 build.py scene s04`; note the render time.
6. Return a concise report: beat-by-beat what's on screen (1 line per beat), any timing changes via update_scene, proposed line changes, rig/prop/fx bugs you hit or worked around (precise), render time.

Library notes:
- Big sets are drawn in world space inside `with core.camera(ctx, cx, cy, zoom):`; fx overlays that are full-frame (flash, whip_pan, alarm_wash, eyelid_wipe, vignette, name tags) are drawn AFTER the camera block in screen space. For big zoom moves (≥ 2x change) wrap the camera block in `with core.cache_steps(1):` so cached sets don't re-render every frame.
- Looped SFX beds: `sfx.loop_events(name, t0, t1, gain_db, pan)` returns events for SFX(info).
- Intro name tags (fx.name_tag) appear only on a character's first appearance (s01 Tiredness, s02 Embarrassment, s04 Impulsivity, s08 The Boss), placed in the safe zone away from faces.
- Outfit/prop continuity (Episode 2): Tiredness wears outfit "sewer" (band-aids, smudges), bandage=True, power≈0.5–0.7 teal irises, NO headphones, hood down except s02–s03 where Curiosity pulls it over his eyes (hood=1 until the light returns in s04, where he has pushed it back). Curiosity = creatures.draw_specimen(form=1). Baby Joy appears from s07. Embarrassment carries a flashlight and the recorder in his chest pocket (LED red until he clicks it off in s05; off afterwards). The bedroom picture frame stays fallen (default).
- Word timing: use the public `info.word_time(line_id, k)` (scene-local start of word k; negative k counts from the end) — don't read info._lip.
- New in the Episode 2 rigs (see the API docs): human `hood`, `glasses_tilt`, `tears`, world-space `reach={"r":(x,y),"l":(x,y)}`, two-handed `hold`, new poses (sit_crate, sneak, punch, haul, lie_front, flop, wave_small, hand_out, phone_thumb, walk_eyes_closed); creatures `ears`, `tail_curl`, `tears`, troll/teary/proud/hopeful expressions, wave/reach_up/puddle(melt)/cover_mouth/lead/perch poses, `baby=True`; fx `sense_reveal`, `flashlight`, `lights_out`, `eyes_in_dark`, `daydream`, `phone_screen`, `monitor_feed`; sets shaft power/nameplates, shaft_lower, service_tunnel, control_room, bedroom light="dawn".
