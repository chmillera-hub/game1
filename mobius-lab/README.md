# Möbius Lab

A paper-free way to run Möbius strip experiments. You twist strips, tape them together (crossed or parallel), cut along a line at any fraction of the width, and see what comes out. Each piece is listed with whether it's one-sided, how many edges and half-twists it has, how long it is, whether it's knotted, and whether it's interlocked with the other pieces.

Open `index.html` in a browser. It needs an internet connection the first time to load Three.js from a CDN. Nothing needs to be built.

Run the checks against known paper results:

```
node test/core.test.js
```

## What you can do

- **Strips:** 1 to 4 strips, each with −6 to +6 half-twists. 0 is a plain loop, 1 is a Möbius strip, and the sign sets the handedness.
- **Cuts:** ½, ⅓, ¼, ⅕, or any fraction you type in (for example `2/5`, `0.3` or `30%`). A strip can have more than one cut. On a one-sided strip, a ⅓ cut goes around twice and comes back along ⅔, the same as with real scissors.
- **Tape:** each strip is taped to the next one, either **orthogonal** (crossed at right angles and taped where they overlap in a square) or **parallel** (laid on top of each other going the same way and taped along the overlap).
- **Spread cuts** opens the cut lines so you can see the pieces apart. **Hide** and the piece cards let you pull out one piece at a time.

## Results it reproduces (all covered by the tests)

| Experiment | Result |
|---|---|
| Möbius strip, cut in half | 1 two-sided loop, twice as long, 4 half-twists |
| Möbius strip, cut at ⅓ or ¼ | a Möbius strip interlocked with a loop twice as long |
| Plain loop, cut in half | 2 separate plain loops |
| Full twist, cut in half | 2 loops linked together |
| 3 half-twists, cut in half | 1 loop tied in a trefoil knot |
| Two plain loops crossed, both halved | 1 square frame |
| Two Möbius strips with opposite twists, crossed, both halved | 2 interlocked loops (the "Möbius hearts") |
| Two Möbius strips with the same twist, crossed, both halved | 2 separate loops |

## How it works

All the maths is in `src/core.js`. It doesn't draw anything, so you can run it in Node.

1. **Paper as a mesh.** Each strip is a grid of small quads following a stadium-shaped loop. The straight parts are flat, and all the twisting happens on the curved parts. The straight parts are exactly one strip-width long, so two crossed strips overlap in a square.
2. **Tape.** The overlapping patches of two strips are merged into one sheet, the way tape holds them together.
3. **Cutting.** Mesh edges along a cut line are split. Faces on either side of the cut stop sharing vertices.
4. **Pieces.** After cutting, the connected groups of faces are the pieces.
5. **Measuring each piece:**
   - **One- or two-sided:** checked by trying to give every face a consistent orientation.
   - **Edges:** loops of boundary edges.
   - **Shape:** the Euler characteristic (V − E + F) tells a loop from a flat sheet or something more complicated.
   - **Half-twists:** the linking number of a paper edge with a copy of itself pushed slightly into the paper.
   - **Interlocked:** the linking number between pieces.
   - **Knotted:** the knot determinant, |Δ(−1)| from a Fox colouring matrix. 1 means no knot was found, 3 means a trefoil.

`src/app.js` handles the controls and the 3D view (Three.js r128).

### Limits

- A knot determinant of 1 means no knot was detected. A few rare knots also have determinant 1. Determinant 5 can't tell a cinquefoil from a figure-eight knot.
- Two pieces can be tangled with a linking number of 0 (for example the Whitehead link). That case would show as "come apart freely".
- On a knotted loop, the half-twist count is the linking number of its two edges, which also includes how the knot itself curls.
- With parallel taping, the layers stay stuck together where they're taped, and the pieces branch apart at the ends of the tape. These show up as a "Taped bundle".

## Ideas for building on it

- Tape strips side by side, edge to edge, instead of overlapping.
- More than one tape joint per strip, so you can build rings and chains (an Olympic-rings layout).
- Cuts that run at an angle, or that stop partway around.
- A physics relaxation step so long loops spread out the way real paper does.
- A full Alexander polynomial to name knots exactly.
