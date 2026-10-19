# The Ones Who Watch

A 3:13 portrait (1080×1920, 24 fps) animated Halloween short built from a child's marker drawing
(the Eye Flower, two Cloud Eyes, Bee-Eye and the ghost Goste).

Art direction is a gothic stop-motion look built only from generic style traits:
- a huge pale moon over a desaturated teal night with orange accents
- crooked, leaning buildings with curled spire tips; twisted trees whose branches end in spirals; iron fences and gravestones
- sculpted lighting (moonlight rim light, form shadows, cross-hatching) and character poses animated "on twos"

The comic and mysterious cues are macabre 3/4 waltzes.

- `the-ones-who-watch.mp4`: final video. H.264 at 535 kbps plus AAC at 64 kbps, 14.6 MB.
  Its SSIM against the lossless master is 0.979, and loudness is normalized to -14 LUFS.
  The first frame is the drawing itself, with no fade-in.
- `src/`: the generator. Everything is synthesized locally: Piper TTS voices, a numpy-synthesized
  score/SFX and Cairo-rendered animation.

## Where to change things
- `src/story.py`: the script, the acting direction for each line (expressions, looks, gestures),
  camera shots, music moods, and the `hi`/`lo` words that get a high celesta accent or a deep cello swell.
- `src/voices.py`: casting (voice model, pitch, pace) for each character.
- `src/render.py`: character art and subtitles. `src/audio.py`: score, stingers, SFX and mix.

## Rebuild
The scripts expect `../voices/*.onnx` (Piper voices: en_GB-alan-medium, en_US-libritts_r-medium,
en_US-lessac-medium, en_US-amy-medium) and `../photo.png` (the drawing, EXIF-rotated, 1502×2000)
next to the `src` folder. The fonts Patrick Hand and Griffy must also be installed.

    python3 voices.py && python3 sim.py && python3 audio.py && python3 make_video.py
    # then run the two-pass x264 encode of master.mp4 + mix.wav (see the commit message)
