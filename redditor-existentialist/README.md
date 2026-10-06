# Redditor Existentialist (featuring Doubt and Anger)

An animated short in three parts (3 to 4 minutes each) with voiceovers, sound effects, music and subtitles.

| Part | File | Length |
|------|------|--------|
| 1: The Void | `videos/part1-the-void.mp4` | 3:04 |
| 2: The Box | `videos/part2-the-box.mp4` | 3:59 |
| 3: The Punchline | `videos/part3-the-punchline.mp4` | 3:14 |

**Part 1:** At 2:47 AM a redditor from a doomer subreddit tries the emotional-world prompt, skeptical that
any AI can show them something new. They describe an empty void, a silent wall that blocks them from it,
and more emptiness outside, until they are boxed in from every angle.

**Part 2:** Inside the box they reason that if they can see the emptiness, they must be something. Then
they give up and sit down, until a giggle. Doubt, a librarian with an encyclopedia, walks through the
wall, asks hard questions, reveals she is one of the barriers and a part of them, and offers to help, if
they are willing to listen.

**Part 3:** "Cut!" The walls fall over like stage props, and the emotional family asks how they did as
barriers. Doubt explains that her giggle might be the key for a real redditor's own doubt. Then an
alternate ending: a redditor who won't listen gets told off by Anger, who turns out to be a giant talking
wall, and the emotions are left pointing at the countdown to the next existential crisis.

## Rebuilding

Reuses the pipelines in `../magic-show` and `../anger-dungeon`. `rgfx.py` holds the redditor, librarian
Doubt, Anger the wall and the scenes; `raudio.py` adds sounds and music; `r1.py`, `r2.py` and `r3.py` hold
each part's script and choreography.

```bash
python3 build.py r1               # -> build/r1.mp4
python3 build.py r2 --timeline    # print beat timings
python3 build.py r3 --still 120   # render one frame
```
