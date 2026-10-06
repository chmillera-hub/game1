# The Magic Show Inside My Head

A two-part animated short (about 2.5 minutes each) with voiceovers, sound effects, music and subtitles.

| Part | File | Length |
|------|------|--------|
| 1: Abracadabra | `videos/part1-abracadabra.mp4` | 2:33 |
| 2: Sorry, Bro | `videos/part2-sorry-bro.mp4` | 2:30 |

**Part 1:** Anger tries to pull a rabbit out of a hat and gets a turtle. Doubt laughs and gets a side eye.
Boredom pulls out every rabbit in the hat. Then a magic missile duel ends with a face full of glitter.

**Part 2:** The glitter settles and Anger has a full makeover. Everyone laughs, a mirror comes out,
and Anger runs squealing into the subconscious. In the emotional dressing room he checks himself out
before washing it all off.

## Rebuilding

Everything is generated from code: the characters and scenes are drawn with Cairo, the voices come
from neural text-to-speech (edge-tts), and the sound effects and music are synthesized with numpy.

```bash
pip install pycairo numpy scipy edge-tts pillow
# needs ffmpeg and the Fredoka font installed
python3 show.py part1            # -> build/part1.mp4
python3 show.py part2            # -> build/part2.mp4
python3 show.py part1 --timeline # print beat timings
python3 show.py part2 --still 72 # render one frame to PNG
```

- `part1.py`, `part2.py`: the script (lines, voices, timing) and the choreography for each beat
- `engine.py`: characters, props, scenes and effects
- `audio.py`: sound effects and music
- `show.py`: the build pipeline (voices, timeline, audio mix, parallel render, mux)
