# The Tether

A 3:51 animated short set inside
Jesus' inner sanctuary: he crawls toward a vast, silent Father, reaches out, and then chooses to
hold his pain instead of handing it over. A golden thread rises from it into the void the Father
is watching.

Two cuts of the same film:

- `the-tether-portrait.mp4` — 1080×1920 (9:16) for phones, with every shot reframed for a tall screen
- `the-tether.mp4` — 1280×720, letterboxed 2.39:1 for widescreen

Everything is generated from code — no stock footage, images or music.

| File | What it does |
| --- | --- |
| `voice.py` | Script, voices (Piper neural TTS) and the timeline every other step keys off |
| `film.html` | The animation: `render(t)` draws any moment of the film onto a canvas. Open `film.html#play=0` (click to start audio) or `film.html#t=120` for a still; add `?portrait` for the phone framing |
| `audio.py` | Synthesized score (pads, choir, piano, bells), thunder, heartbeat, sobs, crawl sounds, reverb, final mix |
| `render.mjs` | Renders frames in headless Chromium in parallel and muxes with the mix into `the-tether.mp4` |
| `stills.mjs`, `sheet.py` | Review helpers: render chosen times to JPEG and tile them into contact sheets |

## Rebuild

```sh
pip install piper-tts scipy numpy pillow
mkdir voices && cd voices
for v in en_US/ryan/high/en_US-ryan-high en_GB/alan/medium/en_GB-alan-medium en_US/lessac/high/en_US-lessac-high; do
  curl -sSLO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/$v.onnx"
  curl -sSLO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/$v.onnx.json"
done
cd ..
python3 voice.py     # build/voice/*.wav, build/timeline.json
python3 audio.py     # build/mix.wav
node render.mjs              # the-tether.mp4 (needs ffmpeg and Playwright's Chromium)
node render.mjs --portrait   # the-tether-portrait.mp4
```
