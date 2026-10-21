# What happens when you shake a rainbow?

A narrated explainer video (`shake-a-rainbow.mp4`, about 5 minutes) built from a physics simulation of
white light passing through a vibrating prism.

Part 2 (`shake-a-rainbow-part2.mp4`, about 5 minutes) moves the prism or the light in circles, squares, triangles, stars and figure 8s. It compares each pattern side by side at 5, 20, 50 and 100 times a second, using a simple model of the eye's persistence of vision (a three-stage low-pass filter with an 8 ms time constant) and a 30 fps phone-camera model. It is built by `render2.py` with narration from `narration2.py` (`NARRATION=narration2 python3 tts.py ...`).

There is also an interactive simulator, `bench/shake-a-rainbow-bench.html`, a single file you open in any browser. It uses a full 3D ray trace. You can vibrate the prism or the light source left/right and up/down (amount and speed for each) or around a pattern (circle, square, triangle, figure 8, star), and choose the motion shape, white light or a mercury lamp, a round or slit beam, the prism angle and the wall distance. The wall shows a 1 cm grid in three views: what your eye sees (time-averaged), slow motion, and a rolling-shutter phone camera.

## Findings

| Experiment | Result |
|---|---|
| Slide the prism sideways ±5 mm | Almost nothing. Every colour moves 2.5–3.3 mm and the spectrum stays intact. Sliding the prism changes no angles. |
| Rock the prism ±4.5° (sine), viewed at 100 Hz | The colours average together and **pink appears**. Pink is not a spectral colour. A vibrating object spends most of its time at the ends of its swing, so the averaged image is two "ghost" rainbows. Where the red of one ghost lands on the violet of the other, you see pink. |
| Shape of the vibration | At the same amplitude, a constant-speed (triangle) sweep washes the middle out to grey, a sine gives dusky pink, and a square wave (snapping between two positions) gives two crisp rainbows with **vivid magenta** where they overlap. |
| Rock around minimum deviation | The colour whose minimum-deviation angle you rock around **almost freezes**. It quivers by a small amount, one-sided, at **twice** the drive frequency. Violet and red move in **opposite** directions, so the spectrum breathes like an accordion. The tilt you rock around picks which colour freezes (62.4° → 700 nm through 67.1° → 400 nm). |
| Mercury lamp + fast rocking | Each spectral line **splits into a fake doublet** (it lingers at the turning points). The line at minimum deviation (436 nm) stays sharp. |
| Wiggle the beam instead | Every colour moves the same way and none freezes. Violet moves most (24 vs 16 mm per degree). |
| Slide the prism up/down | Nothing at all, exactly 0.0 mm. The prism is identical along its edge. |
| Slide the light up/down ±5 mm | The whole rainbow moves 1:1 up and down into a 10 mm band with bright edges. The colours never mix. |
| Aim the light up/down ±6° | The rainbow curves into a smile. Slanted rays bend more, so every colour slides toward violet as it rises or falls (violet by about 20 mm, red 14 mm). |
| Nod the prism up/down ±6° | The rainbow tilts like a fan: violet rises 150 mm, red 122 mm. |
| Move the prism in a circle (rock ±3° + nod ±1°) near 436 nm's minimum deviation, mercury lamp | The colours disagree about which way round the circle goes. Violet (405 nm) goes clockwise, green and yellow go counter-clockwise (mirror-image D shapes), and 436 nm folds into a curved stroke it traces back and forth. |
| Aim the light around a square or star, mercury lamp | Each spectral line draws its own copy of the shape at a different size. The violet square is about 30% wider than the yellow one. |
| Snap the prism around the corners of a square | Four still rainbows in a 2 × 2 grid. The two in each row overlap into magenta, and the rows slant because nodding lifts violet more than red. |
| Doppler shift from shaking | At 1 m/s the shift is v/c ≈ 3.3×10⁻⁹. On the screen that is about 0.8 nm, which you could never see. |
| Interference between overlapping colours | Different colours beat at about 100 THz, so the beats average out and their intensities simply add. |
| Filming it | A rolling shutter turns the colour bands into snakes. Shaking at 30.5 Hz filmed at 30 fps looks like a slow 0.5 Hz drift. |

## Model

- Exact 2D ray trace using vector Snell's law through an equilateral (60°) prism, including total internal reflection checks.
- Schott SF11 dense flint glass, Sellmeier dispersion (n = 1.85 at 400 nm, 1.77 at 700 nm).
- Screen 1 m away. 6500 K white source. Narrow slit beam (2 mm image).
- CIE 1931 colour matching (Wyman–Sloan–Shirley analytic fit). Light is mixed additively in XYZ, then shown in sRGB.
- "What your eye sees" is the time average over a full vibration cycle (persistence of vision).

## Files

- `prism_sim.py`: optics and colour engine
- `explore.py`: prints the sensitivity tables (how far each colour moves per degree of rocking, per mm of shake, and per degree of beam tilt)
- `narration.py`: the voice-over script
- `tts.py`: narration synthesis (Piper TTS, `en_US-lessac-medium` voice)
- `render.py`: scene animation (matplotlib → ffmpeg)
- `bench/`: interactive simulator. `physics.js` (3D optics), `app.js` and `ui.html` are assembled by `build.sh` into `shake-a-rainbow-bench.html`

Rebuild:

```sh
pip install numpy matplotlib piper-tts
python3 tts.py audio en_US-lessac-medium.onnx
python3 render.py audio video            # or name scenes: render.py audio video rock freeze
```
