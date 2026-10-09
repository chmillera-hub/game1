# "Do You Have a Minute?" — animated short

Portrait (720×1280) animated short, ~3:57, with voice acting, a procedurally
synthesized symphony + ten alternate "symphonies", sound effects and burned-in subtitles.
Final file: `do-you-have-a-minute.mp4` (H.264 + AAC, under 15 MB).

Everything is generated from code:

| file | what it does |
|------|--------------|
| `music.py` | numpy synth: strings, choir, brass, harp, timpani, harpsichord, etc.; the symphony, the 10 snippets, ambience and SFX |
| `build_audio.py` | the script/timeline, Piper TTS voices, lip-sync envelopes, final mix → `mix.wav` + `timeline.json` |
| `anim.html` | canvas renderer: characters (faces, blinks, brows, lids, tears, lip-sync), sets, camera shots, HUDs, subtitles |
| `render.js` | drives headless Chromium (Playwright) to render every frame |
| `encode.sh` | two-pass x264 + AAC encode |

## Rebuild
```bash
pip install piper-tts scipy numpy
python3 -m piper.download_voices --download-dir voices en_US-lessac-high en_GB-alan-medium
VOICES=voices python3 build_audio.py build
node render.js build frames --workers 4
./encode.sh "$PWD/frames" "$PWD/build" "$PWD/do-you-have-a-minute.mp4" 380
```
To change dialogue or timing edit the `S` list in `build_audio.py`; to change acting/camera edit `direct()` in `anim.html`.
