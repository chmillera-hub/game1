THIS IS A REVISION PASS (rev 3). scenes/{module}.py already exists and works: you (or an earlier animator) built it, and the user watched rev 2 and gave the notes below. READ THE EXISTING FILE FIRST. Keep everything that works EXACTLY as it is and change only what the notes ask. The user values precise, isolated edits: "even a slight movement of the eye can alter the scene immensely". So do not re-time or re-act beats the notes don't mention, beyond what re-keying to the new cues forces.

script.json has ALREADY been updated (new and changed lines, new pause beats) and the TTS is re-recorded; the current cue times are in out/timeline.json. Re-key everything to the new cues and fix any KeyError or overlap the new beats cause.

LENGTH: there is NO length limit any more (user's instruction). Never tighten pauses or cut beats. If a new beat needs more air, lengthen YOUR scene's pause beats with engine/scriptedit.update_scene('{sid}', fn) and report it. Don't rush anything; the user found the old cuts too fast to follow.

Rig changes already made by the lead, which you should not undo:
- The band-aids on Tiredness's face are now foreshortened with the head turn so they sit flat on the skin. The cheek one is drawn only when the face shows enough.
- The Boss's lip outline is thinner and the lip colour softer.
- The corporation is now CALMCORP / CalmCorp everywhere (the engine and sets are already renamed). If your scene draws any company text itself, use CALMCORP on signs and logos and CalmCorp in prose.

Concurrency: other animators are revising other scenes at the same time.
- Do NOT edit engine/* or audio/*, except for the narrowly scoped additive change explicitly granted below (if any). An additive change means a new keyword argument, default off, after which every other scene's output is pixel-identical.
- Do NOT edit other scenes, script.json or build.py.
- Do NOT run git.
- Scratch files go under preview/ prefixed with {sid}_.

THE USER'S NOTES FOR YOUR SCENE (satisfy every one):
