# FLEECED

*A parable about tokens.* A cartoon of just under 4 minutes with voiceover. A farmer gives his sheep "tokens" for food and shelter, the sheep start herding themselves, and then the Pharisee sheep come for the Jesus sheep. It closes with one way to fix it: food and shelter for everyone, tokens or no tokens, while luxuries cost whatever the farmer wants.

- **Watch:** [`FLEECED.mp4`](FLEECED.mp4) (1080p, 30 fps, 3:49, burned-in captions)
- **Interactive player:** open [`web/index.html`](web/index.html) in a browser. It draws the same animation live on a canvas, synced to the soundtrack, with chapters and a captions toggle. It also works from `file://`.

Contains some strong language. The narration follows the original rant closely, with filler phrases trimmed.

## How it's made

Everything except the speech model is generated in code. There are no image files, stock audio or video assets.

| Piece | Where | What it does |
| --- | --- | --- |
| Screenplay | `script.json` | Every line of dialogue with its speaker, voice, gaps between lines, and named cues (`doorSlam`, `stomp1`, `finalCrack`, …) that trigger sound effects and visuals |
| Voices | `build/build.py` | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) neural TTS. The sheep get pitch-shifted, bleating voices (vibrato plus tremolo); a small IPA lexicon fixes words the TTS mispronounced |
| Music | `build/music.py` | A tiny sequencer with synthesized instruments: Karplus-Strong banjo, whistle, pizzicato, chiptune arps, formant "choir", strings, taiko. Nine cues, from a farm hoedown down to a dark drone and back up to a hopeful dawn |
| Sound effects | `build/sfx.py` | ~50 procedural effects: coins, door slam, padlock, rain, wind, thunder, crickets, birdsong, cash register, formant-synthesized sheep bleats and mobs, record scratch, church bell |
| Mix | `build/build.py` | Lays everything on the timeline, ducks music and ambience under speech, and runs a dialogue guard that holds every other sound at least 14 dB under the voice while someone is talking. Masters to −16 LUFS and writes `web/audio/soundtrack.mp3` and `web/js/timeline.js` |
| Animation | `web/js/*.js` | Canvas 2D drawing as a pure function of time `t`: characters (IK-posed farmer, lip-synced sheep), sets, weather, camera moves, captions. Every beat keys off the cue and line times in `timeline.js` |
| Video | `render/render.cjs` | Headless Chromium renders each frame and parallel workers pipe PNGs into x264, then the result is muxed with the soundtrack |

Because the visuals look up cue times instead of hard-coding them, you can edit a line in `script.json`, rebuild, and the animation re-times itself.

## Rebuilding

Requirements: Python 3.10+, Node 18+, ffmpeg (with librubberband), and Playwright with Chromium.

```bash
cd fleeced
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Kokoro TTS model (~350 MB, Apache-2.0)
mkdir -p .models
curl -L -o .models/kokoro-v1.0.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -L -o .models/voices-v1.0.bin  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

python build/build.py --report      # voices (cached in .cache/), music, sfx, mix, timeline;
                                    # --report also prints how far each line sits above the background
node render/render.cjs              # -> FLEECED.mp4 (about 9 minutes on 4 cores)
```

Useful extras:

```bash
node render/render.cjs --stills 13.9,37.9,169.7   # render single frames to .cache/stills/
node render/render.cjs --from 150 --to 170 --out clip.mp4
python build/qa_asr.py                             # Whisper check that every line is intelligible
python build/embed_fonts.py                        # re-embed fonts into web/js/fonts.js
```

To change a voice, edit `speakers` in `script.json`. Kokoro voice names include `am_michael`, `am_puck`, `af_heart`, `bm_george` and `bm_fable`.

## Credits

- Story: the original voice-note rant this was adapted from.
- Voices: Kokoro-82M (Apache-2.0), via `kokoro-onnx` (MIT).
- Fonts: Fredoka (SIL OFL 1.1) and Luckiest Guy (Apache-2.0). Their license texts are in `assets/fonts/`.
