# The Hikers, the Flower, and the Meaning We Create

An animated short film, rendered live in the browser. Everything you see and hear is
generated in code: no images, no video, no audio files. Only the three typefaces are
bundled.

## Watch it

- **Single file:** open [`../the-hikers-and-the-flower.html`](../the-hikers-and-the-flower.html)
  in any modern browser. It works offline.
- **From source:** open `index.html` in this folder.

Press **Begin the film**. Sound is generated live; leave the Sound switch on.

| Key | Action |
| --- | --- |
| Space / K | Play / pause |
| ← / → | Back / forward 5 s |
| Shift+← / Shift+→, P / N | Previous / next scene |
| J / L | Back / forward 10 s |
| 0–9 | Jump to 0 %–90 % |
| M | Mute |
| F (or double-click) | Fullscreen |

The scrubber shows a tick at every scene; hover it to see scene names.

## How it's made

| Path | What it is |
| --- | --- |
| `js/util.js` | Math, easing, keyframes, deterministic noise, colour helpers |
| `js/art.js` | The shared art kit: palettes, skies, mountains and the summit, forests, light, the character rig (IK arms, walk cycle, expressive faces), the emotions, flowers, captions, speech bubbles, film grain and letterbox |
| `js/engine.js` | Timeline, crossfades, post-processing, player controls |
| `js/audio.js` | The procedural score, ambience and sound effects (Web Audio) |
| `scenes/*.js` | One file per scene, each a pure function of time |
| `docs/SCRIPT.md` | The shooting script: every line of the story, shot directions, continuity |
| `docs/SCENE_GUIDE.md` | API reference and house rules for scene code |
| `tools/snap.js` | Headless renderer for frames and contact sheets (Playwright) |
| `tools/lab.html` | Model sheets for the cast, poses, faces, flowers and emotions |
| `tools/build.js` | Bundles everything into the single HTML file |

Because every frame is a pure function of time, you can scrub anywhere and the picture
is exact. To render frames headlessly:

```
node tools/snap.js --list
node tools/snap.js --scene shop --every 2 --sheet shop.png
node tools/build.js          # rebuild ../the-hikers-and-the-flower.html
```

Fonts: Cormorant Garamond, Nunito and Caveat, under the SIL Open Font License (see `fonts/README.md`).
