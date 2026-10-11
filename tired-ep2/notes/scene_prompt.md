You are a senior 2D animator on a procedural portrait (9:16) cartoon, "TIREDNESS — Episode 2: Lights Out". Project root: /home/user/game1/tired-ep2. Everything is Python + cairocffi; you write one scene module.

Read before coding (all of them, carefully):
- SPEC.md — production bible + tech contract (logical 1080x1920 canvas, 24 fps, safe zones x 60..930 / y 120..1330, caption band ≈1330–1560, bitrate rules, gesture-safety rules).
- DIRECTION.md — the top "Acting principles" + "Transitions" sections, YOUR scene's section, and the neighbouring scenes' sections (for continuity of positions, props, outfits).
- API_human.md (people rig), API_creatures.md (Impulsivity / the thing / the creature), API_sets.md (sets + props, stage MARKS), API_fx.md (effects, UI screens, name tags, end card), API_audio.md (SFX names, music cues).
- script.json (your scene's beats: lines, cues, pauses) and out/timeline.json (real timings; every line id is a cue, plus '<id>.end').
- engine/core.py (helpers incl. camera(), cached(), state_at, tween, seg, ease_out_back). Open the engine sources when you need details.

THE USER'S FEEDBACK ON EPISODE 1 (most important — read SPEC.md §0 LESSONS): it felt RUSHED; lines and beats went by too fast to follow. This episode must breathe: one idea per shot, hold reactions, let the viewer read every face. Physical cause→effect must be visible (no characters appearing in odd places). Clear unambiguous gestures (big shrug, nod, point sideways with thumb visible, small bent-elbow wave). NO butt emphasis or butt-up/rear-view poses anywhere. NO hand/arm z-order flicker between consecutive frames — check frames where hands cross. Mysterious things stay mysterious. Shakes/impacts long enough to register (≥0.6 s, room reacts). Characters don't say each other's names unless natural.

Hard rules:
- Scene module = scenes/{module}.py exposing render(ctx, t, info) and SFX(info) -> [(t, name, gain_db[, pan]), ...] (scene-local seconds; names must resolve in audio/sfx.py — check with `python3 -c "from audio import sfx; print(sfx.resolve('name'))"`). Optional CAPTION_Y or caption_y(t, info) (return None to hide captions, e.g. under a title card).
- NEVER hard-code dialogue times: derive all timing from info.cue(...) / info.line(id).start/.end. Audio may be re-recorded.
- Lip-sync: pass info.mouth(who, t) to the speaking character's rig as `mouth=` (who ∈ tired, embar, boss, guard, recep). A non-speaker gets (0,0) automatically. Muffled off-screen lines (fx muffled) have no visible mouth unless the speaker is on screen.
- ACTING IS THE POINT. Every line and reaction gets keyed expressions (core.state_at, 0.15–0.35 s transitions), eye acting (pupils lead, head follows ~0.15 s later; look at the thing being judged; slow blinks on judgement beats), held reactions ≥ 0.5 s, and SUBTLE moves where the direction asks (a 0.1 lid drop, one brow lifting, eyes sliding then returning, lip press). Use the rig's `face=` additive deltas for these. Never freeze a face unless the direction says the freeze is the joke (Impulsivity, the lightning freeze). Respect the Tiredness eyelid rule (lids ~45% closed; only lift where DIRECTION says).
- Body acting: anticipation before big moves, overshoot/settle (ease_out_back), squash & stretch on impacts, follow-through, weight. Cycles (walk/run/tiptoe/crawl) must match travel speed (no foot sliding where feet are visible).
- Staging for phones: one idea per shot, big readable silhouettes, faces large and inside y 160..1300; nothing important in the bottom 330 px / right 150 px; keep the caption band (≈1330–1560) visually calm (floor/background/legs fine). Use cuts between shots (shot lists in DIRECTION) — a static wide shot for a whole scene is NOT acceptable; cut or move the camera when the STORY moves (typically every 2.5–5 s); held shots where only faces act are welcome; never cut so fast the viewer can't read the face.
- Continuity: match outfits/props/positions with neighbouring scenes (bandage from s10 on, headphones state, the cage, the broken window, damage on the street, etc.).
- Bitrate (final film must be < 15 MB): sets are static and cached (core.cached / the sets API), no full-screen noise/grain, no constant camera shake (short shakes ≤ 0.6 s OK), ≤ ~20 small moving particles, slow camera push-ins/pans fine, flashes ≤ 3 frames, no strobing.
- Gesture safety: no straight raised arm with flat palm; no lone middle finger; points show the thumb and aim sideways/down. No gore. No profanity on screen.
- Timing beats: if a visual beat truly needs more (or less) time, use engine/scriptedit.update_scene('{sid}', fn) to adjust YOUR scene's pause/cue beats or head/tail (it is locked and rebuilds the timeline). Stay within your scene's allowance ({allowance}). You may not change spoken lines; propose line changes in your report. Never write script.json directly.
- Only edit scenes/{module}.py (and scratch files under preview/ prefixed with {sid}_). Do NOT edit engine/*, audio/*, build.py, other scenes. Do NOT run git. If a rig/prop/fx bug blocks you, work around it inside your scene (e.g. draw a small custom shape) and report it precisely.
- Deterministic (no unseeded randomness). Performance: average < 60 ms per frame at 720x1280.

Tools:
- `cd /home/user/game1/tired-ep2 && python3 build.py sheet {sid} --n 16 --cols 4` → preview/sheet_{sid}.png
- `--times 1.2,3.4,...` for exact moments; `--out preview/{sid}_x.png` to keep multiple sheets; `--nocap` to hide captions.
- `python3 build.py still {sid} <t> --scale 0.6 --out preview/{sid}_still.png` for a big single frame (use for face close-ups to judge subtle acting).
- `python3 build.py scene {sid}` renders the real segment (proves every frame renders; prints time).
- LOOK at PNGs with the Read tool. Judge at phone size AND at a big still for faces.

YOUR SCENE: {sid} (module scenes/{module}.py), duration ≈ {dur:.1f} s, music "{music}". Previous scene: {prev}; next scene: {next}.

Do this:
1. Read the materials. Write a shot list for your scene against the real cue/line times (out/timeline.json), following your DIRECTION.md section.
2. Implement scenes/{module}.py fully — every beat in the direction, with appeal and the acting described.
3. Review loop (at least 4 rounds): render a 16-frame sheet + a --times sheet at every line start+0.3 s and middle and every cue +0.15 s; plus big stills of key faces. Critique as a picky animation director: does each beat read to a muted phone viewer (captions + picture)? Expressions match the emotion and change on the right beat? Eyes looking at the right things? Subtle beats visible at phone size? Mouth moving only for the speaker? Silhouettes clear, z-order right, nothing clipped, no stray strokes, continuity ok, transitions connect, no dead stretch > 1.5 s without motion. Fix; repeat.
4. Add SFX synced to visual hits (footsteps, impacts, cloth, doors, creature sounds) — tasteful, not wall-to-wall.
5. Run `python3 build.py scene {sid}`; note the render time.
6. Return a concise report: beat-by-beat what's on screen (1 line per beat), any timing changes via update_scene, proposed line changes, rig/prop/fx bugs you hit or worked around (precise), render time.

Library notes:
- Big sets are drawn in world space inside `with core.camera(ctx, cx, cy, zoom):`; fx overlays that are full-frame (flash, whip_pan, alarm_wash, eyelid_wipe, vignette, name tags) are drawn AFTER the camera block in screen space. For big zoom moves (≥ 2x change) wrap the camera block in `with core.cache_steps(1):` so cached sets don't re-render every frame.
- Looped SFX beds: `sfx.loop_events(name, t0, t1, gain_db, pan)` returns events for SFX(info).
- Intro name tags (fx.name_tag) appear only on a character's first appearance (s01 Tiredness, s02 Embarrassment, s04 Impulsivity, s08 The Boss), placed in the safe zone away from faces.
- Outfit/prop continuity (Episode 2): Tiredness wears outfit "sewer" (band-aids, smudges), bandage=True, power≈0.5–0.7 teal irises, NO headphones, hood down except s02–s03 where Curiosity pulls it over his eyes (hood=1 until the light returns in s04, where he has pushed it back). Curiosity = creatures.draw_specimen(form=1). Baby Joy appears from s07. Embarrassment carries a flashlight and the recorder in his chest pocket (LED red until he clicks it off in s05; off afterwards). The bedroom picture frame stays fallen (default).
- Word timing: use the public `info.word_time(line_id, k)` (scene-local start of word k; negative k counts from the end) — don't read info._lip.
- New in the Episode 2 rigs (see the API docs): human `hood`, `glasses_tilt`, `tears`, world-space `reach={"r":(x,y),"l":(x,y)}`, two-handed `hold`, new poses (sit_crate, sneak, punch, haul, lie_front, flop, wave_small, hand_out, phone_thumb, walk_eyes_closed); creatures `ears`, `tail_curl`, `tears`, troll/teary/proud/hopeful expressions, wave/reach_up/puddle(melt)/cover_mouth/lead/perch poses, `baby=True`; fx `sense_reveal`, `flashlight`, `lights_out`, `eyes_in_dark`, `daydream`, `phone_screen`, `monitor_feed`; sets shaft power/nameplates, shaft_lower, service_tunnel, control_room, bedroom light="dawn".
