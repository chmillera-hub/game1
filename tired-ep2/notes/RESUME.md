# Paused mid-revision (Episode 2, rev 2): how to resume

**Status:** the user's second round of notes is being applied.

## Done and committed
- **Script:** script.json lines changed and TTS re-recorded. The timeline is about 4:49:
  - Thing One naming;
  - the s02 demo beats;
  - the s03 "Don't. We'll get caught." line plus the sulk beat;
  - the honest s04 lines;
  - the nonchalant s05 lines, the wink beat and the "pocket calculator" quotes;
  - the numb Boss in s07.
- **Sets:**
  - plates THING n and the "NOTHING TO SEE HERE" signs;
  - the shaft default label THING 38;
  - the pizza box is now a real box.
- **Music:** cue option fractions must be RETUNED after the scenes are final (see the API_audio.md formulas).

## Not done
The scene revisions were interrupted, so each scene file is in a partial or old state (it still imports). For every scene, re-run its brief:
- `notes/rev_s01.md` … `notes/rev_s08.md`: the user's notes per scene, plus the general brief.
- Boss face rig fix in engine/human.py: hair over the face at 3/4 turns (s01 ~t=28.5) and the nose-tip line (s06 ~t=5.6). The rig agent was partway through; check its current state with face boards.

## Then
1. QA sheets per scene.
2. Retune the music fractions.
3. `python3 build.py video` → `audio` → `final --mb 13.7`.
4. Check the size, SSIM and frame 0.
5. Commit and push, then send the MP4.

**Rev 2 complete.** All user notes applied; final cut 4:51, 14.4 MB.
