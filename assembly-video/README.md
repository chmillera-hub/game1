# The Assembly

Portrait (720x1280) animated short, about 3 minutes 50 seconds, H.264 + AAC mono, under 14 MB.

**Video:** `the_assembly.mp4`

The characters are original designs, not existing cartoon characters:
- **Carter**: a bratty kid in a purple puffer jacket and a green beanie
- **Principal Brodie**: an extremely buff principal in sunglasses
- **Emotional Chad**: an extremely buff, extremely sincere counselor
- Two very ripped 35-year-old gym bros

## Scenes
1. **The plan.** In the principal's office, Brodie and Chad plan an emotional-education assembly: "Feelings are the ultimate gains." They fist bump.
2. **The stands.** Carter mocks the assembly to his friends: "One word, and the whole gym's gonna lose it."
3. **LOSERS!** He yells it. The music record-scratches to a stop and the two bros stare in dead silence while a clock ticks. Carter sweats: "Heh. Heh... right, guys?" His friends scoot away and the whole gym stares. Someone coughs, and then: "Anyway! Feelings."
4. **Existential crisis.** "Why didn't they yell at me? What even is a joke?"
5. **The hat.** A volunteer is drawn "at random" from a hat. It's Carter. Every slip in the hat says CARTER.
6. **Carried down.** Two gym bros carry him down from the stands over their heads (to an epic choir) while he squeals like a pig ("I'm too pretty to be sacrificed!"). Two kids wonder why he's screaming: "They're literally just carrying him."
7. **The stool.** Carter braces with his eyes squeezed shut. Brodie takes off his sunglasses to reveal warm, sparkly eyes: "We got you, dude. We're not gonna do anything weird. You'll see."
8. **The role play.** Chad's dumbbell puppet: "Nobody ever picks me up." Carter chuckles and lowers his arm. They invite him in, no pressure. He's conflicted, then tries something tiny: "...beep beep?" "Best treadmill ever!"
9. **They bomb (on purpose).** Crickets, a tumbleweed, "Ha. Ha. Feelings." Carter: "These dweebs need my comedy."
10. **Carter saves them.** He grabs the mic and the gym roars. The bros share a knowing glance.
11. **Afterwards.** Carter, all fluffed up, agrees to "help you idiots be funny" at the next assembly. "Now we just gotta bring him back down. Gently."
12. **The next assembly.** Carter's joke gets crickets. The bros reveal they were funny all along ("We always spot each other!"): "We toned it down, bro. So you could shine."
13. **Solo.** Carter storms off and does it alone. He gets laughs, but it feels empty.
14. **The door.** He expects "look who came crawling back" (imagining himself as a slug in a beanie), but they saved him a seat: "It was never about winning."
15. **The roast.** Carter roasts the bros on stage, and they're in on it. A heckler goes too far.
16. **Carter has their backs.** After the show: "Roasting them is my job, and they're in on it. You don't get to be mean to my friends." The bros, peeking through the gym doors: "Ultimate gains."
17. End card: FEELINGS ARE THE ULTIMATE GAINS

## How it was made
Everything is procedural, with no stock assets:
- Voices: Kokoro-82M TTS with pitch-shifted kid voices (`tts.py`, script in `lines.py`)
- SFX and music: synthesized with numpy/scipy (`audio_lib.py`, `audio2.py`, `music.py`, `music2.py`), including crowd laughter, crickets, pig squeals, a choir chant, funk and sad piano
- Timeline and mix: `timeline.py` sets every beat; `mix.py` mixes the audio (inner-voice and gym reverb, ducking) and writes lip-sync envelopes
- Animation: skia-python vector drawing (`gfx.py`, `chars.py` face system, `chars2.py` characters, `scenes.py`), rendered by `render.py`
- Encode: `encode.sh` runs a two-pass x264 encode (tune=animation) with loudness normalized to -14 LUFS

To rebuild, run `python3 tts.py && python3 timeline.py && python3 mix.py`, then `python3 render.py segment i 4` for i in 0 to 3, then `./encode.sh 410 out.mp4`.
The Kokoro model files (`models/kokoro-v1.0.onnx` and `voices-v1.0.bin`) aren't included; get them from the kokoro-onnx GitHub releases.
Fonts: Bangers and Fredoka (SIL Open Font License).
