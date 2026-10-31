# Packet Loss

An animated deep dive that treats a person's suffering as information (a report on the conditions they live in) and traces where that information goes.

One packet carries a human need: deeper connection, a village, room to grow emotionally and spiritually. It also carries the conditions behind that need: isolation, work-or-perish hours, rent, food, abuse of power. The packet is sent down thirteen pieces of standard advice ("go to the gym", "try therapy", "just vote"…) and then down five outward channels (telling the truth in public, comparing notes, naming the pattern, organizing, mutual aid). At every hop a delivery report shows who received the packet and whether it ever reached anyone who could change the conditions.

Open `index.html` in a browser. The page needs an internet connection for its fonts; without one it falls back to system fonts.

## The model

Each route is scored on four tests, each 0 or 1:

| Test | Question |
| --- | --- |
| **Out** | Does the information leave the person? |
| **Intact** | Does its meaning survive the trip? |
| **Sideways** | Does it reach others in the same situation? |
| **Upward** | Does it reach whoever controls housing, wages, food and the work-or-perish arrangement? |

Change is possible only if `OUT × INTACT × SIDEWAYS × UPWARD = 1`. A single 0 makes the product 0. The tests are necessary conditions, not sufficient ones.

The scores are judgments about where information flows. They are not measurements, and they say nothing about whether a practice helps the person doing it.

Other math in the animation:

- Speech carries about 39 bits/s (Coupé et al., *Science Advances*, 2019), so a 50-minute session takes in up to ~117,000 bits.
- A two-way vote carries at most log₂ 2 = 1 bit. One bit every four years is about 7.9 × 10⁻⁹ bit/s.
- Averaging N stories shrinks the individual particulars by √N while the shared conditions stay, so the signal-to-noise ratio grows as √N.
- The "at scale" scene is a seeded Monte Carlo run: 1,000 people each take one of the 13 routes at random. The expected count for a bin is n · k / 13.

## Controls

Click the stage or press Space to play or pause. The arrow keys skip 5 seconds. The chapter menu jumps to any route, and the speed button cycles through 1×, 1.25×, 1.5×, 2× and 0.75×. Below the player are the delivery ledger for all 18 routes and the full narration as text.

On narrow screens the stage switches to a portrait layout.

## Files

- `index.html`: the page, its styles, the ledger and the notes
- `engine.js`: the canvas renderer, theme tokens, adaptive layout, drawing primitives and timeline player
- `scenes.js`: the script, the routing data and every scene
- `render-video.cjs`: exports the animation to MP4

Every frame is a pure function of time, so the player can seek anywhere and the exporter renders frame-exact video.

## Export a video

Requires Node 18+, Playwright with Chromium and ffmpeg.

```sh
npm i -D playwright && npx playwright install chromium
node render-video.cjs                  # 1920×1080 → packet-loss-1920x1080.mp4
node render-video.cjs --vertical       # 1080×1920 for Reels, Shorts and TikTok
node render-video.cjs --light          # light theme
node render-video.cjs --from 60 --to 90 --out clip.mp4
```
