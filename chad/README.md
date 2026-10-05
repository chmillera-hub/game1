# EMOTIONAL CHAD

*vs. the Super Saiyan.* A cartoon of about 3 minutes 40 seconds with voiceover. Goku spends all day powering up to the Omega God level to impress Emotional Chad, who is busy enlightening the village. Chad jogs over, catches his breath, and respects Goku's boundary so hard that Goku feels a pang of sadness. The next day Chad's friend, a martial artist from across the universe, turns up and knocks Goku into a mountain. Then it's dinner time.

- **Watch:** [`EMOTIONAL-CHAD.mp4`](EMOTIONAL-CHAD.mp4) (1080p, 30 fps, 3:42, burned-in captions)
- **Interactive player:** open [`web/index.html`](web/index.html) in a browser. It draws the same animation live on a canvas, synced to the soundtrack, with chapters and a captions toggle. It also works from `file://`.

Contains some strong language. Goku is a fan-parody design drawn for this film.

## From story to script

The original story was a spoken voice note. The script keeps its beats and most of its jokes, and changes three things:

- **Filler removed.** "Like", "you know", restarts and repeated phrases are gone from the narration and the dialogue.
- **Beats tied together.** The power-up is intercut with Chad in the village, so "by the time Goku hits the fifth level, Chad has reached the village" plays as one sequence, and long run-on sentences are split into clean lines.
- **One gap filled.** The voice note jumps straight to Goku asking "where's this universe martial artist?", so a narrator line now introduces Chad's friend first.

## How it's made

The engine is shared with [`../fleeced`](../fleeced). Everything except the speech model is generated in code. There are no image files, stock audio or video assets.

| Piece | Where | What it does |
| --- | --- | --- |
| Screenplay | `script.json` | Every line with its speaker, voice, gaps, and named cues (`hair1`, `level5`, `heartPang`, `smash1`, `boom2`, …) that trigger sound effects and visuals |
| Voices | `build/build.py` | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) neural TTS: narrator `am_michael`, Goku `am_fenrir` pitched down slightly, Chad `am_puck`, villager `af_bella` |
| Music | `build/music.py` | Synthesized cues: an epic taiko-and-strings power-up theme, a chill village groove, a sneaky pizzicato, a tender one for Goku's pang |
| Sound effects | `build/sfx.py` | Procedural power-up yell and aura hum, punches, explosions, panting, phone dial and voicemail beep, mini-golf putt, record scratch |
| Mix | `build/build.py` | Ducks music and ambience under speech and holds every other sound at least 14 dB under the voice while someone talks. Masters to −16 LUFS |
| Animation | `web/js/art-dbz.js`, `web/js/scenes.js` | A 2-bone IK character rig (Goku, Chad, villagers, the universe martial artist) with hair that grows and turns gold, auras, explosions, canyon and village sets. Every beat keys off the cue and line times in `timeline.js` |
| Video | `render/render.cjs` | Headless Chromium renders each frame and parallel workers pipe them into x264, then the soundtrack is muxed in |

## Rebuilding

Requirements: Python 3.10+, Node 18+, ffmpeg (with librubberband), and Playwright with Chromium.

```bash
cd chad
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Kokoro TTS model (~350 MB, Apache-2.0)
mkdir -p .models
curl -L -o .models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o .models/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

python build/build.py --report      # voices, music, sfx, mix, timeline
node render/render.cjs              # -> EMOTIONAL-CHAD.mp4
```

Useful extras:

```bash
node render/render.cjs --stills 31,72.9,176.6   # render single frames to .cache/stills/
node render/render.cjs --from 160 --to 182 --out clip.mp4
python build/qa_asr.py                           # Whisper check that every line is intelligible
```

## Credits

- Story: the original voice note this was adapted from. Goku and Super Saiyan are from *Dragon Ball* by Akira Toriyama; this is an unofficial fan parody.
- Voices: Kokoro-82M (Apache-2.0), via `kokoro-onnx` (MIT).
- Fonts: Fredoka (SIL OFL 1.1) and Luckiest Guy (Apache-2.0). Their license texts are in `assets/fonts/`.
