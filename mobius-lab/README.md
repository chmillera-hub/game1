# The Möbius Lab

Ten interactive experiments built from a Möbius-strip notebook. Each one runs an idea as a
simulation, then sorts it into what holds up (REAL), what lines up with an existing idea in
physics (RHYME), and where it breaks (STRETCH). Only claims the simulations show on screen are
made; math from the notes that the visuals can't demonstrate is left out. Open
`../mobius-lab.html` in a browser.

| # | Experiment | What is simulated |
|---|------------|-------------------|
| 1 | Finger vs. Eyes | An ant paints the face it walks on; its flag flips after one lap (a ℤ₂ twist). Monsters and a learning "fear" predictor. |
| 2 | Scissors | Cutting a strip with 0–5 half-twists at any fractions, then cutting any piece again down its middle. Position-based paper physics (bends, doesn't stretch, can't pass through itself); links and knots are measured from the simulated paper. A list re-runs the cut results recorded in the notes and checks each one. |
| 3 | Keep Halving | A Möbius strip cut down its middle, then every piece cut down its middle, five times (1, 1, 2, 4, 8, 16 pieces). "Inside the original strip" draws each piece exactly where it sits in the uncut strip; "Pulled apart" lays the long loop out as a ring and spreads the pieces across it, optionally thickened. Twists, knots and links are measured on the exact cut geometry. |
| 4 | Tape | Two loops (plain, Möbius left or right, full twist) taped crosswise or face to face, then cut down their middles; where the scissors cross the tape they cut both layers. Pieces, objects, sides and edges are counted exactly from the cells, edges are marked, and the faces can be painted by side. A list re-runs the taped constructions from the notes. |
| 5 | 720° | Dirac's belt trick: a cube with tethers that never tangle, period 720°. |
| 6 | Strip Music | Standing waves on a plain vs. Möbius ring, odd harmonics (audio and spectrum), Hückel 4n+2 vs. Möbius 4n. |
| 7 | Gear Lock | Gear rings and grids with tooth springs and slipping: odd rings lock, a Möbius joint flips the rule, triangular grids are frustrated. |
| 8 | Cosmic Forge | Ginzburg–Landau quench on a grid: full twists (arrows) vs. half twists (headless lines), polarizer view, Kibble–Zurek test. |
| 9 | Spooky Ribbon | Corkscrew billiards (arcsine odds), and a Bell/CHSH test of three ribbon models with a no-signaling check. |
| 10 | Drain Gravity | Moons floating in inflowing space: a drain gives a 1/r⁵ pull, the river model gives Newton's 1/r², plus a horizon for light. |

## Build

```
node mobius-lab/build.mjs              # writes mobius-lab.html at the repo root
node mobius-lab/build.mjs --artifact   # also writes dist/mobius-lab.artifact.html
```

Sources are in `src/`: `shell.html` (markup and all the notes text), `styles.css`, `core.js`
(router, renderer, UI helpers, band geometry, linking numbers and knot determinants), one file
per experiment (`ch2a_halving.js` is experiment 3, `ch2b_tape.js` experiment 4), and `main.js`.
three.js r128 loads from a CDN; experiments 7–10 work without it.

## Checks

Plain Node scripts, no dependencies:

- `tests/topo.mjs`: cutting topology from 3D geometry (pieces, linking numbers, knot determinants).
- `tests/physics.mjs`: CHSH scores for each ribbon model, no-signaling, helix odds, belt-trick quaternions.
- `tests/paper.mjs`: runs the paper simulation on 13 twist/cut cases and checks that links and knots never change.
- `tests/apart.mjs`: the same check with the pull-apart force on.
- `tests/recut.mjs`: cuts, relaxes, cuts a piece again from its relaxed shape, and checks the topology holds.
- `tests/halving.mjs`: for one to five halvings, measures twists, knots and links on the exact cut strip, and checks that the pulled-apart drawing (thickened or not) has the same ones and that no two strips touch.
- `tests/tape.mjs`: builds and cuts eight taped constructions; prints pieces, objects, sides, edges, twists and links, and checks they hold while the paper moves.
- `tests/separate.mjs`: checks that two taped objects reported as unlinked really pull apart.
- `tests/gears.mjs`: which gear rings spin or lock, and slipping.
- `tests/kz.mjs`: Kibble–Zurek trend (faster cooling leaves more defects).
