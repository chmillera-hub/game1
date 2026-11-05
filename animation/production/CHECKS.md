# Completed checks and remaining gaps

Only work that was actually done is listed here.

## Completed

1. **Story and shot plan.** The shot list is generated frame by frame from the renderer itself (`SHOT_LIST.md`): 102 shots across 20 scenes. Each shot entry lists its purpose, light, sound and dialogue.
2. **Design lock.** All characters share one definition. Reference sheets: `cast_lineup.jpg` (19 characters) and `expression_sheet.jpg` (14 expressions × 5 principals).
3. **Style frames and representative frames.**
   - A frame from the middle of every shot, plus every scene transition: 121 frames in `contact_sheet_01–06.jpg`, taken from the final MP4.
   - I reviewed them all. One composition defect was found and fixed: Jesus was hidden behind the subtitle box in the campfire shots.
4. **Motion test.** Strips of consecutive frames were checked for four moments:
   - Noa's close-up: lip sync and a blink.
   - The peak of David's dance.
   - Abigail's sword-lowering moment.
   - A scene cross-dissolve.

   The result is `motion_test_strips.jpg`. One defect was found and fixed: subtitles dipped for a frame between consecutive chunks.
5. **Defect fixes from the quality passes.**
   - Two flash cuts (2 frames and 12 frames) were removed.
   - Petals, smoke and the stone loop popped when they repeated; they now fade instead.
   - The walking procession jumped every 2.5 s; it now moves continuously.
   - David's sword popped out of his hand in the Abigail scene; it now stays in his hand.
   - Two low-motion holds (2.0 s and 2.7 s) were flagged by the freeze detector. They now have motivated movement: the rebel army marches with banners, and the people around the campfire shift and gesture.
   - Three sound effects were tied to the frame of their visible action.
   - True peak measured +1.6 dBFS; it is now −1.0 dBTP.
   - Six voices were slowed after their speaking rates were measured.
6. **Licensing.** The non-commercial and research-only voices were replaced with CC0, public domain, CC BY and CC BY-SA voices. Credits are in `AUDIO.md`.
7. **Export verification** (`source/checks.sh`, output in `checks_output.txt`):
   - frame count, resolution, frame rate and codecs are correct
   - no decode errors
   - no black segments (≥ 0.5 s)
   - no frozen segments (≥ 2 s)
   - no audio dropouts (no silence ≥ 3 s)
   - loudness and true peak are measured
   - SSIM against the master is 0.9948
   - the first frame is bright
   - the file is under 15 MB

## Not done or not verifiable here (gaps)

- **Real-time playback review.** I can't play video at normal speed in this environment. Motion was judged from consecutive-frame strips, contact sheets and automated freeze and flash-cut detection. None of these proves the motion feels right in real time.
- **Listening review.** Audio playback isn't available, so the voices, music balance and pronunciation are **unreviewed by ear**. This matters most for the new cast: the LibriTTS-R speakers were chosen by license and measured pitch, not by listening.
- **Lip sync** is driven by loudness, not phonemes. It reads as talking, but mouth shapes don't match specific sounds.
- **Word-accent timing** is estimated from character position in the sentence (±0.2 s). It hasn't been checked against actual word timing.
- **Resolution** is 720 × 1280. The 15 MB size limit you asked for was the reason. A 1080 × 1920 version would need the renderer to scale its drawing by 1.5×. It isn't implemented. At 15 MB, a larger frame would also lower the quality of each pixel.

**Status:** all delivery and technical criteria pass. Because the by-ear and real-time reviews could not be done, treat this as a **release candidate pending your watch-through and listen**.
