THIS IS A REVISION PASS (rev 4). scenes/{module}.py already exists and works. It has been revised several times, and the user watched the rev 3 cut and gave the notes below. READ THE EXISTING FILE FIRST. Keep everything that works EXACTLY as it is and change only what the notes ask.

The user values precise, isolated edits: "even a slight movement of the eye can alter the scene immensely". So do not re-time or re-act beats the notes don't mention, beyond what re-keying to the new cues forces. Use a backup copy of the file and pixel-diff against it to prove the untouched beats are unchanged.

script.json may already be updated for your scene (new or changed lines and pauses, with TTS re-recorded); the current cue times are in out/timeline.json. Re-key to the new cues and fix any KeyError or overlap.

LENGTH: there is NO length limit. Never tighten pauses or cut beats you weren't asked to cut. If a new beat needs more air, lengthen YOUR scene's pause beats, or insert new pause beats, with engine/scriptedit.update_scene('{sid}', fn), and report it. The user found earlier cuts too fast to follow, so give new beats generous holds.

Rig changes being made RIGHT NOW by the lead (don't undo them or work around them):
- Tiredness's wet-hair drips are being removed everywhere. The user reads them as sweat.
- The Boss's lip and mouth outline is being thinned.
- The inside of the mouths (Tiredness, the Boss, everyone) is being brightened a little so speech reads.

Concurrency: other animators are revising other scenes at the same time.
- Do NOT edit engine/* or audio/*, other scenes, or build.py.
- Do NOT write script.json directly (use update_scene for pause beats only).
- Do NOT run git.
- Scratch files go under preview/ prefixed with {sid}_.
- If a rig limitation blocks you, work around it inside your scene and report it precisely.
Gesture safety and staging rules as always: no salute-like raised flat palm, no lone middle finger, NO butt emphasis or rear views of bent-over bodies, no hand z-order flicker, and captions clear of faces.

THE USER'S NOTES FOR YOUR SCENE (satisfy every one):
