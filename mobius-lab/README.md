# Möbius Universe Lab

A set of browser simulations that explore the Möbius-strip model of the universe from the
"Mobius strip explainer guide" and "Mobius strips 2" notes. Open `index.html` in a browser
(it loads three.js and the fonts from a CDN, so it needs an internet connection).

| Tab | What it simulates |
| --- | --- |
| **Universe** | The Topological Coherence Model as rules in a periodic 2D universe. A seed twist crystallizes the flat field (inflation), reheating runs a knot forge with a probability barrier (freeze-out), mirror knots annihilate, gravity is shown as an inflowing "river", stars and supernovae forge heavier knots, and black holes ring and pay a Hawking tax. Gravity is particle-mesh (FFT, mean density subtracted). Light follows ray equations in a moving medium (exact Schwarzschild bending for one black hole). |
| **One Side** | The explainer guide. An ant (the finger) walks a strip while the camera (the eyes) watches. It shows the 720° return and counts edge-on spots. In the monster game, consciousness sees a short window ahead and emotions remember and predict. |
| **Cut Lab** | Paper cutting with exact topology. Choose half-twists and ½, ⅓, ¼ or ⅕ cuts. The scissors show off-centre cuts going round twice. Pieces relax as Cosserat paper ribbons with self-contact. Half-twists, links, knots and twist + writhe are measured from the 3D shape, and you can click a piece to cut it again. |
| **Stretched Strip** | The entanglement idea as a Bell (CHSH) test. "Halves set at stretching" (local) scores ≤ 2. "One ribbon" (the cut sets both ends) scores 2.83, which matches quantum mechanics. |
| **Helix Shot** | A spinning helix tip strikes a billiard ball. It uses rigid-body impulse with friction and Monte Carlo over the tip's phase: left/right is 50/50, straight ahead is the least likely, and the handedness shows up as spin. |

Code: `js/core.js` (shared math, topology, UI, charts, camera), one file per tab, `js/main.js` (app shell).
