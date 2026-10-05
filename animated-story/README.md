# Animated shorts

Two code-generated, three-part animated stories, each part 3:00 or shorter in vertical 1080×1920 for TikTok, Reels and Shorts:

1. **Emotional Education**: Cartman, PC Principal and Emotional Chad (below). Videos in `out/`.
2. **DO NOT DISTURB**: Tiredness, Embarrassment, Impulsivity and the creature, in a riso-print noir style. See [`dnd/README.md`](dnd/README.md); videos in `out/do-not-disturb/`.

# Emotional Education: an animated short in three parts

Cartman, PC Principal and Emotional Chad, in three vertical (9:16, 1080×1920) videos for TikTok, Reels and Shorts.
Each part is 3:00 or shorter.

| Part | Title | Covers |
|---|---|---|
| 1 | **F\*\*\* Around** | The bros plan the assembly. Cartman rolls his eyes, yells "LOSERS!" from the stands, the music stops and ten seconds of dead silence follow. A cough breaks it and he has an existential crisis. The hat is "100% random", the 35-year-old gym bros haul him down squealing, and he lands on the stool. |
| 2 | **Find Out** | The sunglasses come off to show warm, caring eyes: "We got you, dude." Then the Feelings Restaurant role-play. Cartman's tiny "Check, please" leads to the bros' deliberately cringe bit, and Cartman decides to save the dweebs. He kills it while the bros share a knowing glance. He agrees to help next time, and the bros talk through their plan for his boredom. |
| 3 | **The Long Game** | Cartman bombs to crickets. The bros reveal they were funny all along ("the five stages of grief"). Cartman goes solo and it feels empty. He finds the principal's door open a crack and imagines being called a "little slug", but they're happy to see him. They agree he can roast them on stage. A heckler takes it too far, Cartman defends his co-hosts after the show, and the bros share a knowing look. |

Outputs (after building) go in `out/`: one `.mp4` and one `.srt` caption file per part. `SCREENPLAY.md` is the full timestamped script.

## Style and copyright note

The characters are drawn in an original vector style: outlined shapes, rubber-hose limbs and soft shading. It does not copy *South Park*'s construction-paper look. The character names and basic color cues are still parody or fan use of Paramount/Comedy Central characters. Read each platform's rules before monetizing. To rename anyone, edit `SPEAKERS` in `toon/engine.py` and the lines in `story/part*.py`.

Strong language is bleeped in the audio and starred out in captions (`sh*t`, `f***`).

## How it works

Everything is generated from code, with no stock assets:

- `story/part1.py`, `part2.py`, `part3.py` hold the script as code: dialogue, acting, camera moves, sound cues.
- `toon/characters.py` and `toon/sets.py` are hand-built cairo drawings of the characters and locations.
- `toon/audio.py` does the voices (Kokoro TTS, offline, kid voices pitch-shifted). Music and every sound effect are synthesized: record scratch, cough, pig squeal, drumroll, crickets, layered crowd laughter.
- `toon/engine.py` times every shot to the real voice clips, drives lip-sync from the audio level, and burns in captions. It renders frames on 4 cores and muxes with ffmpeg (loudness-normalized to −14 LUFS).

## Rebuild

```bash
./setup.sh                      # once: packages, voice model, fonts
python3 build.py 1 2 3          # render all parts (≈10 min per part on 4 cores)
python3 build.py 2 --info       # print the shot list and timings
python3 build.py 3 --stills 30,95   # render single frames to build/stills3/
```
