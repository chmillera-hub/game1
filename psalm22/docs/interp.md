# Frame interpolation (`comp/interp.py`)

Render slow shots at 12 fps (odd frames only), then synthesise the even frames with RIFE on the CPU.
Halves the EEVEE render cost of a shot for about 1 s of CPU per synthesised frame.

```
psalm22/blender/run.sh --shot s05 --quality final --frames odd      # renders 1,3,5,...
/opt/venv/bin/python psalm22/comp/interp.py --shot s05 --quality final   # writes 2,4,6,... (+ N if even)
```

The output is `WORK/frames/<shot>/<quality>/NNNN.png`, the same names and 8-bit RGB PNG format as the renderer
produces, so the compositor needs no change. Writes are atomic (temp file plus rename).

## Model
- **RIFE v4.26** (Practical-RIFE, IFNet_HDv3, 2024-09-21) by Zhewei Huang (hzwer) et al.; the code and
  weights are MIT licensed. The weights come from the author's HuggingFace repo `hzwer/RIFE` (`RIFEv4.26_0921.zip`).
  They are cached at `/opt/assets/rife/v4.26/flownet.pkl` (sha256 `45c7f741…6f53f`) and downloaded and
  checksum-verified automatically if missing (`RIFE_DIR` overrides `/opt/assets/rife`).
- The network is re-implemented in `interp.py` (no repo code is imported). Inference is torch 2.14 CPU
  (`/opt/venv`), bf16 convolutions (AMX on this Xeon) with fp32 flow and warping. Use `--precision fp32` if
  you suspect a precision problem; it is about 1.3x slower and visually identical (62 dB apart).
- `OMP_WAIT_POLICY=PASSIVE` is set before torch loads. On this shared box with Blender running, the default
  spinning OpenMP threads made inference **15x slower** (20 s vs 1.3 s per frame at load ~20).

## CLI
| flag | meaning |
|---|---|
| `--shot ID --quality Q` | fill `WORK/frames/ID/Q/` (default quality `final`) |
| `--n N` | shot length (default: `render_frames` from `timeline.json`, else the last frame present) |
| `--max-gap 2` | largest spacing between rendered frames that will be bridged. 2 = odd frames; 3 = render 1,4,7… (t=1/3, 2/3), lower quality |
| `--edge extrapolate\|hold` | a missing trailing frame N (N even) or leading frame: motion-extrapolated from the last two rendered frames (default) or duplicated |
| `--force` | regenerate every frame this tool generated before |
| `--dry-run` | print the plan only |
| `--validate` | treat the dir as a **full-rate** render, use its odd frames as input, write evens to `WORK/dev/interp/validate/<shot>_<q>/`, and report PSNR/SSIM/detail against the real evens |
| `--threads K` | torch threads (default: all 4 cores) |
| `--src DIR --out DIR` | arbitrary dirs |
| `--pair A.png B.png --out C.png [--t 0.5]` | single pair |

Safety and bookkeeping:
- Generated PNGs carry a tEXt chunk `Interp` (for example `rife-v4.26 t=0.5000 0011 0013`).
  **Rendered frames are never overwritten.** A generated frame is regenerated automatically when one of its
  source frames is newer, so re-rendering odd frames and re-running interp is enough. If you later render the
  shot at full rate (`--frames all`), the real renders replace the generated ones.
- `interp.json` in the frame dir records per-frame `warp_err` (the mean |difference| of the two warped inputs,
  0–255). This is a confidence signal that needs no ground truth. A NOTE is printed when a frame exceeds 6.
- Exit code 1 if frames remain unfillable (missing odd frames / gaps > `--max-gap`).
- Run it **after** the shot's Blender render finishes (it uses all cores; ~0.5 GB RAM).

## Python API
```python
import sys; sys.path.insert(0, "psalm22/comp")
from interp import Interpolator, fill_shot
ip = Interpolator(threads=4, precision="bf16")      # loads weights once
mid = ip.interpolate(a, b, t=0.5)                   # uint8 HxWx3 RGB numpy in/out
r = ip.run(a, b, [0.25, 0.5, 0.75])                  # batch of timesteps -> r["merged"], r["flow"], r["err"]
nxt, err = ip.extrapolate(prev, last, d=0.5)        # predict half an interval beyond `last`
summary = fill_shot("s05", "final")                 # what the CLI does; returns the manifest dict
```

## Results
All tests used 540x960 draft renders (3 spp EEVEE). The odd frames were the input and the real even frames were
the reference (`--validate`). PSNR and SSIM are full-frame. `detail` is the Laplacian energy of the synthesised
frame relative to the real one (1.0 = equally sharp/noisy). Baselines: *blend* = average of the two neighbours,
*dup* = repeat the previous frame. Scratch outputs, crops and logs are in `/opt/work/psalm22/dev/interp/`
(`viz/*.png`: prev | RIFE | truth | next | 4x error | 4x blend error).

| test (24 frames) | motion between rendered frames (2 frame steps) | RIFE PSNR / SSIM | blend | dup | detail |
|---|---|---|---|---|---|
| **s00 prototype** (slow dolly over Golgotha) | ~2–4 px | **42.97 dB / 0.984** | 35.56 | 34.09 | 0.91 |
| s00 at final quality (frames 1–4 only, near-static start) | <1 px | 47.7 dB / 0.996 | 50.1 | 50.8 | 0.93 |
| fast accelerating pan + thin foreground spears | 28 → 140 px | 28.9 dB / 0.82 | 25.3 | 23.6 | 0.80–0.89 |
| spinning wheel/cross, swaying ropes, dust, **random per-frame light flicker** | wheel rim ~26 px | 23.1 dB / 0.88 | 22.5 | 22.3 | 0.89 |
| same, steady light | wheel rim ~26 px | 29.9 dB / 0.92 | 27.4 | 25.7 | 0.89 |
| same, steady light, half speed | wheel rim ~13 px | 32.2 dB / 0.95 | 28.8 | 27.0 | – |

By region in the spin scene (steady light, full speed → half speed), RIFE vs blend:
- spoked wheel: 26.1 dB → 28.5 dB (blend 24.8 / 25.1)
- cross rotating in depth: 29.2 → 32.8 (27.3 / 30.6)
- thin ropes: 26.3 → 30.6 (23.2 / 26.0)
- wall with drifting dust motes: 32.5 → 32.5 (31.9 / 32.0)
- static floor: 42.6 (EEVEE draft noise floor)

Other checks:
- **Trailing even frame** (extrapolation): 40.8 dB at the end of the s00 test, against 30.5 dB for a hold.
  It never scored below a hold in any test.
- **1-of-3 rendering** (`--max-gap 3`, frames 1,4,7,…; t = 1/3, 2/3) on s00: 39–52 dB, mean 42.8.
  This is viable for the very slowest shots. Render with a comma list, e.g. `--frames $(seq -s, 1 3 N)`
  (then interp with `--max-gap 3`).
- `--frames odd` + bake: odd frames rendered through `render_shot.py --frames odd` (and with a particle bake
  in the test scene) are **bit-identical** to the same frames from a contiguous render. End to end on s00
  (120 frames, 60 rendered, 60 synthesised including the extrapolated frame 120), the generated evens score
  42.9 dB against the real ones.
- bf16 vs fp32: 62 dB apart. `--scale 0.5` gave no gain on the fast pan (28.99 vs 28.93 dB).
- `warp_err` (no ground truth needed) tracks problems: about 1.2 on s00, 2.3–5.6 on the pan, 2.8 on steady spin,
  and 12–20 on flicker frames.

### What it handles badly
1. **Lighting flicker / random per-frame changes** (torches, fire, lightning, strobing). The synthesised frame
   is a blend of the two neighbours, so the flicker effectively becomes a smooth 12 Hz flicker. It is not wrong to
   look at, but it isn't the rendered flicker. Fix in the shot instead: key flicker only on odd frames with
   linear interpolation (or ≤ 12 Hz noise), then interpolation is exact.
2. **Small particles** (dust motes, sparks, embers, glitter, stars, rain) that drift randomly or move more
   than their own size: RIFE cannot match them, so they **fade out or vanish on the even frames** and
   visibly twinkle at 12 Hz. Slow, large, smoothly moving particles are fine.
3. **Fast rotation of thin, repetitive structures** (spokes, fence posts, hair strands, sword blades
   spinning): at ~13 px/frame spokes bend, break or double (wagon-wheel ambiguity). At ~6 px/frame it is clean.
4. **Rotation in depth / self-occlusion** (an object turning around its own vertical axis): at 8°/frame the
   crossbeam ghosted (cross-dissolve of the two poses); 4°/frame was acceptable.
5. **Fast pans** (tested 14–70 px/frame): the geometry is placed correctly, but fine textures are about 10–20% softer
   and thin edges are off by a few px, so you see a slight alternating soft/sharp shimmer and judder.
   Acceleration is not modelled (linear midpoint).
6. **Detail/noise**: synthesised frames carry ~10% less high-frequency energy (they average two noise
   patterns), so heavy grain or noise can "breathe" at 12 Hz. This is minor at final quality, and the
   compositor's grain or bloom masks it.
7. **Non-motion changes** (heat haze, time-lapse sky/stars, caustics, water spray, smoke/fog evolving fast,
   cuts inside a shot). A cut or impact frame inside a shot must land on a rendered frame.

### Recommendation per shot
Rule of thumb: use `--frames odd` when the camera moves smoothly at under ~15 px/frame, nothing thin spins
faster than ~3°/frame, and there is no per-frame flicker and no small fast particles. After interp, check
`interp.json`: `warp_err_p90` above ~4 → look at the frames, and above ~6 → render 24 fps (or re-render just the
bad range at full rate: interp only fills frames that are *missing*, so `--frames odd` plus a full-rate range
`--frames 80-120` mix freely).

Preliminary, based on `text/shots.json` (verify per shot):

| use | shots | frames |
|---|---|---|
| **odd (12 fps)** | s00, s01a, s01b, s02b, s03, s07b, s13a, s14a, s15, s16c, s18a (1-of-3 viable), s18b, s19b*, s20c | 2282 |
| check first (`--validate` on a short full-rate test, or warp_err) | s06a, s06b, s07a†, s10a, s10b†, s11a (heat haze ✗), s16a, s16b*, s17a†, s17b, s19a, s20b† | 2076 |
| **render 24 fps** | s02a (time-lapse), s04a, s04b (water/spray), s05, s08 (torches, embers), s09a, s09b, s11b (dust stream), s12a (handheld dogs), s12b (impact), s13b (tumbling dice), s14b, s14c (particle disintegration), s20a (fire, sparks) | 2051 |

\* dust motes in the shot: OK if they are sparse, slow and large; otherwise render 24 fps or have dust added by the compositor.
† flames: OK if flicker is keyed on odd frames (see 1).

Savings: the "odd" group alone halves 2282 frames, which is ~1140 renders or **~1.3–1.6 h** at 4–5 s/frame.
The "check" group could add as much again.

## Performance
- Inference CPU cost is **~0.8 CPU-seconds per synthesised frame** (bf16, 540x960 padded to 576x960;
  fp32 ~1.0 CPU-s). The pipeline overlaps PNG decode/encode, so it adds little.
- Measured wall time per synthesised frame, end to end, 4 threads: **1.2 s** at load 8–9 (60-frame s00 run);
  0.74 s inference at load ~11; 1.3 s inference at load ~20. An earlier near-idle measurement gave
  0.32–0.36 s inference (fp32 0.42–0.52 s). **Estimate on an idle machine: ~0.35–0.5 s per frame end to end**,
  so a 180-frame shot needs ~90 synthesised frames, about 45 s. That is ~10x cheaper than rendering those frames.
- Memory ~0.5 GB RSS. Startup ~2 s (torch import 1.8 s, weights 0.1 s).
- Every benchmark during development ran while 3–7 other Blender jobs shared the 4 cores (load 8–25), so the
  wall times above are inflated relative to an idle machine.
- If you `import torch` before `interp` in your own script, OpenMP spin-waits stay on. interp then drops to
  1 thread when the box is busy and prints a note. Import `interp` first or export `OMP_WAIT_POLICY=PASSIVE`.
