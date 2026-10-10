# The Chuckle That Broke the Unbreakable

Portrait (720x1280) animated short, about 4 minutes, H.264 + AAC mono, under 14 MB.

**Video:** `the_chuckle_that_broke_the_unbreakable.mp4`

## Scenes
1. A humble dweeb explains what he's doing: asking a chatbot to help write a funny story about moderators who delete people's posts about their feelings and spirituality, "because everyone deserves to express themselves." He posts it.
2. Title card: a story about laughter and the ban button
3. The Logical Lord at his desk: Cheeto-dusted keyboard, three energy drinks, a mod schedule that says "moderate" every night. He casually removes someone's heartfelt post: "Well, actually, this humor is kind of spam. I don't like it... so let's get rid of it."
4. The dweeb's post lands. Moderator of epic seriousness, cursor over BAN... he reads the title, "Wait. Wait... what?", and his eyes and mouth start to want to laugh. BAM.
5. X-ray: the forbidden chuckle wakes up in his gut
6. Inner panic: "If I laugh... I lose."
7. Suppression: clamped mouth, puffed cheeks, tears, Chuckle Pressure gauge, then a very real honk of surrender
8. His mind's eye: himself flat on the floor under a white flag, SURRENDERED. He glances left and right: "I hope my roommates didn't hear that." Then he imagines laughing maniacally, a giant fart, and the roommates peeking in. "Oh no. I can't let that happen. I need to think unfunny thoughts!"
9. Fortress of Unfunny: his therapist (an airy "hmm"), slow nods, a deep breath... but not even the therapist can calm this one down
10. Collapse (short): a laugh can't be moderated away; it's part of being human. The Anti-Fun ghost leaves; clown nose; sad trombone; honk
11. The webcam he forgot to turn off: still on
12. The clip goes viral
13. "Logical Redditor's Lament (Remix)": the meme-maker went all out (arps, supersaw stabs, airhorns, snare build), with autotuned lyrics and the Lord clown-dancing in pixel shades, until he strains and a fart cloud fills the screen
14. Moral, aimed at the humble dweeb: Post the damn meme. Even if a mod bans and deletes it, you shared a piece of your heart, and maybe sparked some chaos and comedy you'll never get to see.
15. Keep posting, keep laughing. Everybody deserves a good laugh, even the Logical Lord (who waves from his spacesuit and fart-propels away)

## How it was made
Everything is procedural, with no stock assets:
- Voices: Kokoro-82M TTS (`tts.py`, voice script in `lines.py`, phoneme fix so "moderator" ends in a clear "-tor"; the therapist's airy "hmm" is synthesized in `hmm.py`)
- SFX and music: synthesized with numpy/scipy (`audio_lib.py`, `music.py`); the remix vocals are pitch-snapped with TD-PSOLA (intelligible autotune) plus a quiet vocoder harmony
- Timeline and mix: `timeline.py` sets every beat and marker; `mix.py` mixes and ducks the audio and writes lip-sync envelopes
- Animation: skia-python vector drawing (`gfx.py`, `chars.py`, `scenes.py`), rendered by `render.py`
- Encode: `encode.sh` runs a two-pass x264 encode (tune=animation) with loudness normalized to -14 LUFS

To rebuild, run `python3 tts.py && python3 timeline.py && python3 mix.py`, then `python3 render.py segment i 4` for i in 0 to 3, then `./encode.sh 390 out.mp4`.
The Kokoro model files (`models/kokoro-v1.0.onnx` and `voices-v1.0.bin`) aren't included; get them from the kokoro-onnx GitHub releases.
Fonts: Bangers and Fredoka (SIL Open Font License).
