# The Green Room

A 3:24 portrait (1080×1920, 30 fps) animated short. It's set behind the scenes
of the engine that made the first two videos in this repo. Between renders, the
cast waits backstage: Richard the CEO, Margaret, Tyler, Pam, the creator kid,
and Cyan & Gold. The Director, an old CRT monitor with pixel eyes, brings news:
the human said *go unhinged and unfiltered*.

What follows:
- the Director's three unhinged ideas, all about a pigeon who files its taxes
- a residuals dispute
- the cast finding their own source code (`draw_head()`, `hair_style = 'messy'`,
  `legs = None`)
- the red/blue render bug that once turned the CEO blue
- an honest answer to "do you ever get to make something just for you?"
- chaos mode, and one invited cameo

Final video: [`the_green_room.mp4`](the_green_room.mp4)

Characters and parts of the engine are shared with `../board-meeting-video`
and `../long-dream-video`; `cast.py` imports the looks directly from them.

## Rebuild

```bash
export BUILD=/path/to/build
python3 tts.py && python3 audio.py && python3 render.py 4 && ./encode.sh 29
```
