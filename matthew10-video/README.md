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

## The realistic version

[`NotPeaceButASword_realistic.mp4`](NotPeaceButASword_realistic.mp4) is the same film (same soundtrack,
timing, shots, scripture and subtitles) with photographic images:

| Piece | How |
|---|---|
| Photographs | One generated still per shot (`realistic/shots.py`): [RealVisXL V5.0 Lightning](https://huggingface.co/SG161222/RealVisXL_V5.0_Lightning) (SDXL) on CPU with long-prompt encoding. Maya and Mom keep one face across scenes through an [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) Plus-Face reference portrait. Group shots are photo-realized from the 2D frames (img2img keeps the staging), then each person is repainted on their own so they keep their age, look and clothes; the call close-ups and the closing window shot take their framing from the 2D frames the same way (`realistic/gen_images.py`) |
| Faces | [LivePortrait](https://github.com/KwaiVGI/LivePortrait) used as a face rig: every frame of every face is re-rendered from the 2D performance (head turns relative to the photo, gaze, blinks and lids, brows, lip-sync shapes, and emotion blends measured from generated expression photos). Lids go through LivePortrait's eye retargeting, which measures each eye, so both close alike on a turned head. Faces re-render only when their pose moves; the compositor crossfades small steps and holds before blinks (`realistic/lp_engine.py`, `realistic/render_faces.py`) |
| Compositing | `render/main_real.js`: slow push-ins on the faces, light effects for the interludes, phone screens over blurred photos, and the 2D version's transitions, title, scripture and subtitles (`render/lib/project.js` is shared) |
| Encode | Same soundtrack and budget; photographic frames measured better at 720×1280 than 1080×1920 at this bitrate (SSIM 0.967 against the full-resolution master), 14.5 MB |

Bodies and backgrounds are still photographs; the acting is in the faces and the camera. Where a
photograph could not be made to match the 2D staging, the realistic version adapts: the phone call
plays as a split screen with a call badge rather than phones at ears, and the sparrows are in the
sky shots rather than on Maya's shoulder.

## The fantasy version

[`NotPeaceButASword_fantasy.mp4`](NotPeaceButASword_fantasy.mp4) retells the story as a narrated fantasy
allegory (screenplay: [`fantasy/SCREENPLAY.md`](fantasy/SCREENPLAY.md)): a city of glass where no one may say
what hurts, a sword of light that splits the feast hall in two, a Hall of Mirrors where a small Light made by
human hands keeps her company, sparrows caught by a hand of light, a scrying pool, and the road to a town where
the lanterns burn low. The narrator tells it; the screen shows what the words say.

| Piece | How |
|---|---|
| Script and voices | `fantasy/script.json`, voiced with the same cast and pipeline as the 2D film |
| Stills | 43 photoreal fantasy images (`fantasy/shots.py`), generated like the realistic version; the people keep their faces from it |
| Direction | `fantasy/direction.js`: every cut lands on a word of the narration, with its camera move, effects and the faces' performances |
| Motion | Depth parallax (Depth Anything V2: near layers move faster during push-ins), animated faces (LivePortrait), and effects in `fantasy/vfx.js`: snow, aurora, embers, god rays, the Light, cracks spreading, the hall splitting, a shockwave, shattering glass, sensory-overload glare, a rising flock, water |
| Sound | A new score (`fantasy/music.py`: choir, brass, harp, flute) and sound design (`fantasy/mix.py`) |

Rebuild with `fantasy/build.sh` (stages: voices select prepare music mix images faces depth frames final).

## Changing it

- **Words or pacing**: edit `script.json`, then rebuild from `voices` (`./build.sh voices select prepare music mix frames master final`).
- **Acting and staging**: edit the scene in `render/scenes/`. Expressions live in `render/lib/expressions.js` and character designs in `render/lib/cast.js`. Preview stills with
  `node render/main.js --build /opt/work/build_final --stills 12.5,40 --outdir /tmp/stills`.
- **Music**: edit the cues in `audio/music.py`, then `./build.sh music mix final`.
- **Realistic shots**: edit a prompt in `realistic/shots.py`, delete that image from `/opt/work/real/img`
  (and its `plates/` folder), then `./build.sh real-images real-faces real-frames real-final`.

`build.sh` lists every stage and the tool locations it expects.

## Credits and licences of the tools used

Kokoro-82M (Apache-2.0), Chatterbox (MIT), faster-whisper (MIT), FluidR3 GM soundfont (MIT),
EB Garamond and Inter (SIL OFL), @napi-rs/canvas (MIT), FFmpeg (LGPL/GPL). Realistic version:
RealVisXL V5.0 Lightning (CreativeML Open RAIL++-M), IP-Adapter (Apache-2.0), LivePortrait (MIT), whose
face detector comes from InsightFace (models licensed for non-commercial research use). Fantasy version:
also Depth Anything V2 Small (Apache-2.0). Scripture quotations
follow the wording supplied for the piece (NIV-style); citations: Matthew 10:34–36, 10:38–39,
10:29–31, 10:22–23.
