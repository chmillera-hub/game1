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
RESULTS_PLACEHOLDER
