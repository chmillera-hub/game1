# ANGER: a dungeon story in three parts

An animated short in three parts (2 to 2.5 minutes each) with voiceovers, sound effects, music and subtitles.

| Part | File | Length |
|------|------|--------|
| 1: Into the Dark | `videos/part1-into-the-dark.mp4` | 2:11 |
| 2: The Fall | `videos/part2-the-fall.mp4` | 2:38 |
| 3: The Roommates | `videos/part3-the-roommates.mp4` | 2:08 |

**Part 1:** Anger, an armored warrior with a torch, cuts through vines and webs, smashes through a locked
door, and searches a vast cavern. Glowing eyes watch him. A loose stone sends his torch into a pool, and
in the dark the floor gives way. He hangs from the ledge, then falls, without a sound.

**Part 2:** Anger drives his sword into the shaft wall to slow his fall and survives, barely. A creature
creeps up on him, a thrown rock knocks it out, and a voice in the dark drags it away for lunch.
The voice then falls asleep, snoring, and so does Anger.

**Part 3:** Anger wakes up to drool on his cheek and a huge, round beast grinning over him. The stranger
says the beast likes him; Anger asks for some space; the beast is offended. The stranger laughs at the
idea of escape, and Anger decides he will die then. The beast snorts, and Anger almost smiles.

## Rebuilding

This reuses the pipeline in `../magic-show` (voices, timeline, audio mix, parallel render).
`dgfx.py` adds the warrior, the creature, the beast, the cave scenes and torch lighting; `daudio.py` adds
the dungeon sound effects and music; `d1.py`, `d2.py` and `d3.py` hold each part's script and choreography.

```bash
pip install pycairo numpy scipy edge-tts pillow   # plus ffmpeg, and the Fredoka and Cinzel fonts
python3 build.py d1               # -> build/d1.mp4
python3 build.py d2 --timeline    # print beat timings
python3 build.py d3 --still 40    # render one frame
```
