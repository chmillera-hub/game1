# "Too tired to create?": an animated explainer, made entirely from code

**Output:** `how-i-make-videos.mp4`. It's portrait 1080×1920 at 24 fps, 3:31 long and about 14.3 MB (H.264 + AAC, loudness −14 LUFS).

The video shows Riley, who is too worn out after work to draw anything. A stranger, Alex, replies to Riley's comment and walks through the process:
1. find a spark
2. ramble to a chatbot until it becomes a script
3. ask an AI coding assistant for the video
4. watch, tweak, repeat

Riley's own video about their grandma is the payoff. At the end, the video reveals that it was made the same way.

Everything is generated: the art is drawn with code (canvas), the voices come from a local open-source TTS model (Kokoro), and the music and sound effects are synthesized in `audio.py`. There are no stock assets, so there's nothing to license.

## Rebuild

```bash
./setup.sh     # once: Python/Node packages, fonts, TTS model (~350 MB)
./build.sh     # ~8 min: voices -> timeline -> music/mix -> frames -> compressed mp4
```

Options: `TARGET_MB=9 ./build.sh` makes a smaller file. `WIDTH=720 ./build.sh` renders at 720p.

## Making changes (or ask Claude Code to make them for you)

| Want to change… | Edit |
|---|---|
| What someone says | `script.json` (`text` is the caption; optional `tts` is how it's pronounced) |
| A voice or speaking speed | `script.json` → `voices` (Kokoro voice names like `af_heart`, `am_michael`, `bf_emma`) or a line's `speed` |
| Pauses / pacing | `script.json` → `pre` (pause before a line), scene `lead` / `tail` |
| What's on screen | `render/scenes.js` (one block per scene) |
| Characters (faces, colors, poses) | `render/characters.js` |
| Rooms, props, UI mockups | `render/props.js` |
| Music, sound effects, mix levels | `audio.py` |
| Captions | `render/helpers.js` → `captions` |

All animation, captions, music changes and sound effects are timed from the voice lines. If you change a line, the whole video re-syncs on the next build.

To preview frames without a full render:

```bash
node render/main.js --stills 12.5,a_s2a+1.5,r_her.end-0.5   # seconds, or line/scene-relative
```
