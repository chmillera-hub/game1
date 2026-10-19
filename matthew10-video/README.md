# Not Peace, But a Sword — an animated short (Matthew 10)

A portrait (1080×1920, 9:16) animated short about emotional truth, family, work and
finding safety, built on Matthew 10:34–36, 10:38–39, 10:29–31 and 10:22–23.
The video is [`NotPeaceButASword.mp4`](NotPeaceButASword.mp4); the screenplay is in
[`SCREENPLAY.md`](SCREENPLAY.md).

Everything is generated locally from code: the characters, voices, music and sound.
There is no stock footage, and no copyrighted characters or artwork.

## How it's made

| Piece | How |
|---|---|
| Script | `script.json`: every line, who says it, pauses, and per-line emotion settings |
| Voices | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) gives each character a distinct timbre. [Chatterbox](https://github.com/resemble-ai/chatterbox) re-performs each line with per-line emotional intensity, cloning that timbre. 2–3 takes per line; the best take is picked automatically by speech-recognition accuracy (faster-whisper), voice consistency and timing (`audio/`) |
| Lip-sync | Loudness and sibilance envelopes from each line's audio drive the jaw, mouth width and speech-beat head nods (`audio/prepare.py`) |
| Animation | A custom 2D rig drawn with Skia (`@napi-rs/canvas`): head turns and nods projected through a simple 3D head model, eyelids, gaze and saccades, automatic blinks, brows, lip-synced mouths with emotion, tears, breathing, IK arms with posed elbows, and hair that sways after head motion (`render/lib/`). Each scene's direction (who looks where, when expressions shift, gestures, shots) is in `render/scenes/*.js`, keyed to line and word timings |
| Music | Composed in code as MIDI cues timed to the scenes (`audio/music.py`), rendered with FluidSynth + the FluidR3 GM soundfont |
| Sound design and mix | Clock, cutlery, fire, glass, fluorescent hum, office noise, birdsong and wings, phone buzzes, footsteps, all synthesized. Room reverb per scene, a phone filter on the call, music ducked under speech, loudness at −14 LUFS (`audio/mix.py`, `tools/encode.py`) |
| Encode | Two-pass H.264 (animation tuning) + AAC at a bitrate calculated to stay under 15 MB, with SSIM measured against a near-lossless master (`tools/encode.py`) |

## Changing it

- **Words or pacing**: edit `script.json`, then rebuild from `voices` (`./build.sh voices select prepare music mix frames master final`).
- **Acting and staging**: edit the scene in `render/scenes/`. Expressions live in `render/lib/expressions.js` and character designs in `render/lib/cast.js`. Preview stills with
  `node render/main.js --build /opt/work/build_final --stills 12.5,40 --outdir /tmp/stills`.
- **Music**: edit the cues in `audio/music.py`, then `./build.sh music mix final`.

`build.sh` lists every stage and the tool locations it expects.

## Credits and licences of the tools used

Kokoro-82M (Apache-2.0), Chatterbox (MIT), faster-whisper (MIT), FluidR3 GM soundfont (MIT),
EB Garamond and Inter (SIL OFL), @napi-rs/canvas (MIT), FFmpeg (LGPL/GPL). Scripture quotations
follow the wording supplied for the piece (NIV-style); citations: Matthew 10:34–36, 10:38–39,
10:29–31, 10:22–23.
