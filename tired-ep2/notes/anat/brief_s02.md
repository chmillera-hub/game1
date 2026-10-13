ANATOMY AND VISUAL-GLITCH PASS on scene s02 (scenes/s02_lights_out.py) of "TIREDNESS - Episode 2: Lights Out" (project root /home/user/game1/tired-ep2; procedural Python + cairocffi animation; read SPEC.md §0–2 and the API_*.md docs as needed).

THE USER'S REQUEST (paraphrased): "run different passes over the entire animation to fix any potential glitches with the hands, the shoulders, the facial movements... only take things that you can meaningfully improve the visual quality... don't be changing the words." The user gave a list of anatomy and visual lessons from another animation. They are in notes/anatomy_checklist.md. READ IT FIRST. It is your checklist. Ignore any item that doesn't apply to this scene.

THE USER'S STANDING PREFERENCE (most important): precise, isolated edits that keep everything else identical. "Even a slight movement of the eye can alter the scene immensely." So:
- Do NOT change any dialogue, captions, script.json, cue or pause timing (no update_scene), or music.
- Do NOT change expressions, eye acting, gestures or staging that are working. Fix glitches and anatomy; don't redesign.
- Make every fix as local as possible (a few frames, one limb), and prove the rest of the scene is pixel-identical to your backup.
- Only fix things that MEANINGFULLY improve visual quality, i.e. something a viewer would notice on a phone. Leave intentional effects alone: camera shakes on impacts (≤0.6 s), deliberate trembles, fast but continuous motion. If unsure, say so in your report rather than change it.
- Do NOT edit engine/*, audio/*, build.py, script.json or other scenes. Do NOT run git. If something can only be fixed in the rig, describe it precisely in your report and the lead will handle it.
- Scratch files go under preview/anat/s02_*. FIRST copy your scene file to preview/anat/s02_backup.py.

Already done by the lead, don't redo:
- Tiredness's hair drips are removed.
- Mouth interiors are brighter and the Boss's lip outline is thinner.
- The creature's tears are now light blue.
- In s04 the 1.67 s arm jump is fixed: the walk-to-stand blend now uses matching arm layers (_STAND_WL).

TOOLS (run from the project root):
- `python3 preview/anat/rig_probe.py s02` renders every frame small and records every character's anchors (head, hands, elbows, shoulders, feet, hip, neck; screen and world coordinates; arm draw layers) to preview/anat/probe_s02.json, in about 10–30 s.
- `python3 preview/anat/rig_analyze.py s02` lists suspicious events per character:
  - pop1/pop2: an anchor twitches out of line for 1 or 2 frames;
  - jump: a one-frame snap or teleport;
  - zflip: the arm draw order or layers flicker.
  The current list from the lead's run is in preview/anat/events_s02.txt. Frames are scene-local, at 24 fps.
- `python3 preview/anat/strips.py s02 preview/anat/s02_x.png FRAME:WHO[:ANCHOR[:RADIUS]] ...` renders frames FRAME-2..FRAME+3 at 720p, cropped around a character's anchor. WHO is tired, embar, boss, guard, guard2, cr (creature) or baby. RADIUS is in 720p px; 9999 shows the whole frame. Use it before and after each fix.
- `python3 build.py still s02 <t> --scale 1.0 --out preview/anat/s02_s.png` gives a big single frame for close-up anatomy checks. `python3 build.py sheet s02 --times ... --cols N --nocap --out ...` gives contact sheets.

A KNOWN ROOT CAUSE, found in s04 (look for it wherever a hand or arm jumps during a pose blend):
- In human.resolve_pose a blend (a, b, k) switches STRING keys (the arm layers al_layer/ar_layer) at k = 0.5.
- The rig's arm "detour" (_detour_flags: an arm travelling behind↔front swings out around the body) is classified from both poses' layers, at a turn quantized to 0.05.
- If one pose has an explicit layer and the other is auto (""), or the turn changes during the blend, the classification can flip mid-blend. The arm then swings out or back by up to ~0.45 rad in ONE frame: a hand jump of 50–110 px.
- Fix in the scene: give both blend targets the same explicit layers, e.g. (walk_with_layers, {"base": "stand", "al_layer": ..., "ar_layer": ...}, k). Or start or end the turn change outside the blend.
- Other typical causes: a pose switch with no blend (a snap); reach= targets switched on or off abruptly instead of weighted; a keyframe list with two keys at the same time; the camera or anchor computed from a different shot for one frame.

DO THESE PASSES over the whole scene, shot by shot:
1. Motion glitches. Go through every event in preview/anat/events_s02.txt, view each with strips.py and decide: real glitch → fix; intended → note why.
   - Then look for what the probe can't see. Sample frame pairs around every shot change and big move for one-frame pops of props or limbs, and hand z-order flicker where hands cross the body.
2. Hands and held objects (flashlight, recorder, keycard, phone, lever, keys, the baby, sleeve...):
   - correct grip; the thumb never shows through an object;
   - hands rest on legs or surfaces when seated, not hanging in the air;
   - palms facing sensibly;
   - no blob hands.
3. Arms, elbows and shoulders: arms not clipping through clothing or the body; elbows natural; shoulders clean.
4. Neck, head, hair and face:
   - the head sits on the neck naturally, with no floating head;
   - the hood or cap sits on the head;
   - hair attached to the head;
   - eyes look at whoever they're talking to or reacting to;
   - gaze and head turns are smooth, with no jumps.
5. Legs, feet and sitting: legs present and plausible; feet pointing the way the body faces; seated poses possible.
6. Liveliness and light:
   - a character standing in a held shot isn't statue-stiff. A tiny breathing or sway is enough; add it only if the character is truly frozen for over ~1.5 s while on screen, and keep it subtle;
   - background characters alive;
   - nobody unnaturally dark next to a light;
   - props resting on surfaces, not floating.

After fixing: re-run rig_probe and rig_analyze to confirm the fixed events are gone and no new ones appeared. Pixel-diff the whole scene against your backup (render both versions in one process, or compare stills) so only the intended frames changed. Run `python3 build.py scene s02`.

REPORT, concisely:
- per pass: what you checked, what you found;
- each fix: time, what was wrong, what you changed, before/after strip file;
- each flagged event judged intentional, and why (one line each);
- rig-level issues for the lead, if any (precise);
- proof that the rest is unchanged (the diff result);
- render time.
