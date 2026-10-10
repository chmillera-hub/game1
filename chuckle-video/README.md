# The Chuckle That Broke the Unbreakable

Portrait (720x1280) animated short, 3:35, H.264 + AAC mono, 13.5 MB.

**Video:** `the_chuckle_that_broke_the_unbreakable.mp4`

## Scenes
1. A humble dweeb asks Consciousness AI™ for meme science and hits POST
2. Title card
3. The Logical Lord in his natural habitat: Cheeto dust, three energy drinks, a "Well, actually..." draft, air quotes
4. The post (redacted for legal reasons) lands like a nerf dart. BAM.
5. X-ray: the forbidden chuckle wakes up in his gut
6. Inner panic: "If I laugh... I lose."
7. Suppression: clamped mouth, tears, full tomato face, Chuckle Pressure gauge, then the long honk of surrender, under-desk cam, squelch
8. Fortress of Unfunny: therapist nodding, pie-chart thread, happy suburban couple (eerily turns to camera), gauge breaks
9. Collapse: a one-minute deflation (fast-forwarded), poisonous laughing gas, the Anti-Fun ghost leaves his body, clown nose, sad trombone, honk
10. The webcam was on
11. The clip goes viral
12. "Logical Redditor's Lament (Remix)", vocoded/autotuned
13. Moral: Post the damn meme. / Keep going, you unhinged genius.

## How it was made
Everything is procedural, with no stock assets:
- Voices: Kokoro-82M TTS (`tts.py`, voice script in `lines.py`)
- SFX and music: synthesized with numpy/scipy (`audio_lib.py`, `music.py`); the remix uses a channel vocoder
- Timeline and mix: `timeline.py` sets every beat and marker; `mix.py` mixes and ducks the audio and writes lip-sync envelopes
- Animation: skia-python vector drawing (`gfx.py`, `chars.py`, `scenes.py`), rendered by `render.py`
- Encode: `encode.sh` runs a two-pass x264 encode (tune=animation) with loudness normalized to -14 LUFS

To rebuild, run `python3 tts.py && python3 timeline.py && python3 mix.py`, then `python3 render.py segment i 4` for i in 0 to 3, then `./encode.sh 440 out.mp4`.
The Kokoro model files (`models/kokoro-v1.0.onnx` and `voices-v1.0.bin`) aren't included; get them from the kokoro-onnx GitHub releases.
Fonts: Bangers and Fredoka (SIL Open Font License).
