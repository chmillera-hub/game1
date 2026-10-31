# Nursery Rhymes, Examined — animated short

A 5 min 43 s portrait (9:16) animated short in two parts, narrated by a slow documentary voice:
**On "The Wheels on the Bus"** and **On "The Itsy-Bitsy Spider"**. Voiced, scored, subtitled,
drawn entirely in code.

Final file: `output/nursery-rhymes-examined.mp4` — 8.4 MB, 720×1280, 24 fps, HEVC 10-bit
(SSIM 0.988 against the uncompressed master) with 40 kbps Opus mono audio. The first frame is the
opening scene with the part title over it.

## Adaptation notes

- The narration is the script word for word (subtitles keep its exact text, including "wont"; the
  voice says "won't").
- The headings attribute the monologues to a real filmmaker. The film doesn't show his name or likeness,
  and the narrator isn't an imitation of his voice: the titles read *On "The Wheels on the Bus"* and
  *On "The Itsy-Bitsy Spider"*, and the narrator stays off screen.
- The stage directions are realised as sound (wind and a discordant hum; dripping water and a faint
  skittering) and also shown as captions under each part title.
- The passengers' "merry song" is an original wordless hummed melody, not the rhyme's tune or lyrics.
  It stops dead on "…abruptly cease."

## How it is made

| Stage | Where |
|---|---|
| Script → beats (one per sentence, subtitle chunks, pauses) | `script/build_beats.py` |
| Narrator voice (Kokoro `bm_george`, slowed; pitched down 1 semitone in the mix) | `tts/synth.py` |
| Shot-by-shot direction: shots, passenger/child/spider acting, music moods, note cues, sound effects | `render/direction.js` |
| Timeline incl. the hummed song's notes and word-timed cues | `render/timeline.js` |
| Shots (bus, interior with passengers, driver's seat, cliff, waterspout, rain, sun, therapist, wellness pole, cycle) | `render/lib/shots.js` |
| Cast: passengers, the child, the therapist (shared rig from `../the-last-witness`), the spider, the sun | `render/lib/cast.js` |
| Score, sound design and mix (−16 LUFS, speech-first) | `audio/score.py`, `audio/mix.py` |
| Render + encode | `make_video.sh` |
