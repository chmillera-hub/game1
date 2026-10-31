# Rendering the storybook as a video

`render.cjs` plays `hearthdeep-files.html` on a virtual clock and captures every frame, so the
video is smooth and exact no matter how slowly the browser renders. Each page becomes its own
segment (page start through the turn into the next page), which lets segments render in parallel.

The result is `../hearthdeep-files.mp4`: 1920×1080, 30 fps, about ten minutes, with a stereo soundtrack.

Requirements: Node with Playwright (`npm i playwright && npx playwright install chromium`), ffmpeg,
and Python 3 with NumPy.

```bash
# 1. render segments (split the 16 pages across a few processes)
node render.cjs ../hearthdeep-files.html segs 0,1,2,3,4,5 &
node render.cjs ../hearthdeep-files.html segs 6,7,8,9,10 &
node render.cjs ../hearthdeep-files.html segs 11,12,13,14,15 &
wait
# 2. join them, synthesize the soundtrack, encode the final file
./assemble.sh segs ../hearthdeep-files.mp4
```

- `shim.js` replaces timers, `requestAnimationFrame` and smooth scrolling with a virtual clock and
  seeks every CSS animation and transition to it before each frame.
- `video.css` hides the reader controls and enlarges the text for video.
- `soundtrack.py` reads the beat and page-turn times that `render.cjs` logs for each segment and
  synthesizes a matching score: an ambient pad with one chord per page, a bell for each revealed
  line, and a paper whoosh for each page turn.
- `node render.cjs ../hearthdeep-files.html out x --plan` prints each page's length without rendering.
