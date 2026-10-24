# The Möbius Lab

Eight interactive experiments built from a Möbius-strip notebook. Each one runs an idea as a
simulation, then sorts it into what holds up (REAL), what lines up with an existing idea in
physics (RHYME), and where it breaks (STRETCH). Open `../mobius-lab.html` in a browser.

| # | Experiment | What is simulated |
|---|------------|-------------------|
| 1 | Finger vs. Eyes | An ant paints the face it walks on; its flag flips after one lap (a ℤ₂ twist). Monsters and a learning "fear" predictor. |
| 2 | Scissors | Cutting a strip with 0–5 half-twists at any fractions. Position-based paper physics (bends, doesn't stretch, can't pass through itself); links and knots are measured from the simulated paper. |
| 3 | 720° | Dirac's belt trick: a cube with tethers that never tangle, period 720°. |
| 4 | Strip Music | Standing waves on a plain vs. Möbius ring, odd harmonics (audio), Hückel 4n+2 vs. Möbius 4n, zero-point sums → −1/12 vs. +1/24. |
| 5 | Gear Lock | Gear rings and grids with tooth springs and slipping: odd rings lock, a Möbius joint flips the rule, triangular grids are frustrated. |
| 6 | Cosmic Forge | Ginzburg–Landau quench on a grid: full twists (arrows) vs. half twists (headless lines), polarizer view, Kibble–Zurek test. |
| 7 | Spooky Ribbon | Corkscrew billiards (arcsine odds), and a Bell/CHSH test of three ribbon models with a no-signaling check. |
| 8 | Drain Gravity | Moons floating in inflowing space: a drain gives a 1/r⁵ pull, the river model gives Newton's 1/r², plus a horizon for light. |

## Build

```
node mobius-lab/build.mjs              # writes mobius-lab.html at the repo root
node mobius-lab/build.mjs --artifact   # also writes dist/mobius-lab.artifact.html
```

Sources are in `src/`: `shell.html` (markup and all the notes text), `styles.css`, `core.js`
(router, renderer, UI helpers, band geometry, linking numbers and knot determinants), one file
per experiment, and `main.js`. three.js r128 loads from a CDN; experiments 5–8 work without it.

## Checks

Plain Node scripts, no dependencies:

- `tests/topo.mjs`: cutting topology from 3D geometry (pieces, linking numbers, knot determinants).
- `tests/physics.mjs`: zero-point sums, CHSH scores for each ribbon model, no-signaling, helix odds, belt-trick quaternions.
- `tests/paper.mjs`: runs the paper simulation on 13 twist/cut cases and checks that links and knots never change.
- `tests/apart.mjs`: the same check with the pull-apart force on.
- `tests/gears.mjs`: which gear rings spin or lock, and slipping.
- `tests/kz.mjs`: Kibble–Zurek trend (faster cooling leaves more defects).
