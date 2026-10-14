# Psalm 22 — production pipeline (developer notes)

Goal: a lifelike 3D-animated portrait (9:16) short film of the crucifixion that visualises Psalm 22
(NIV) block by block — flashbacks and symbolic scenes, not talking heads. Style target: realistic
CG like *The Polar Express* / *Final Fantasy: The Spirits Within*. Narration (AI voice) + captions
+ score. Final file: MP4 under 15 MB. The first frame must be a bright, readable shot (it's the
social-media thumbnail), never black.

## Layout
```
psalm22/
  text/psalm22.json      caption blocks/phrases (exact NIV text)
  text/shots.json        creative blueprint: 40 shots, description per shot
  timeline.json          generated: frame ranges per shot + phrase timings (python3 psalm22/timeline.py)
  audio/tts.py           narration (Kokoro, voice am_michael) -> $WORK/audio/narration.wav, phrases.json
  blender/
    run.sh               headless render wrapper (xvfb + Blender 4.5 EEVEE Next)
    render_shot.py       shot runner
    lib/core.py          shared helpers (camera, lights, sky, materials, terrain, cross, fog, dust)
    lib/polyhaven.py     CC0 asset downloader/cache (HDRIs, textures, models)
    lib/*.py             feature modules (characters, wardrobe, assets, env, sets, ...)
    shots/<id>.py        one script per shot: def build(ctx)
  comp/                  compositor: grading, transitions, captions, encode
```
Large/derived data lives outside git: `$WORK=/opt/work/psalm22` (frames, audio, caches),
`/opt/assets` (Poly Haven cache, TTS model, downloaded models).

## Tools on this machine
- Blender 4.5 LTS: `/opt/tools/blender-4.5.14-linux-x64/blender` (CPU only; EEVEE runs on Mesa llvmpipe under xvfb).
- MPFB 2 (MakeHuman for Blender) installed as extension `bl_ext.user_default.mpfb` with the CC0 MakeHuman
  system assets in `~/.config/blender/4.5/extensions/.user/user_default/mpfb/data` (skins, hair long01/short*,
  eyebrows, eyelashes, eyes, teeth, proxies). Python API: `from bl_ext.user_default.mpfb.services.humanservice import HumanService`.
- Python venv for non-Blender tools: `/opt/venv/bin/python` (numpy, scipy, pillow, soundfile, kokoro_onnx, faster_whisper).
- ffmpeg, ImageMagick (`convert`, `montage`), apt-get, pip. Network: PyPI, HuggingFace, GitHub releases,
  raw.githubusercontent.com, Poly Haven, download.blender.org are reachable.
- 4 CPU cores, 15 GB RAM, no GPU. Be considerate: run at most ONE Blender render at a time per agent.

## Rendering a shot
```
psalm22/blender/run.sh --shot s01a --quality preview --frames sheet6   # 270x480, 3 spp, 6 frames + contact sheet
psalm22/blender/run.sh --shot s01a --quality draft   --frames 1,60       # 540x960, 3 spp
psalm22/blender/run.sh --shot s01a --quality final   --frames 1-4        # 540x960, 8 spp (or ctx.samples)
```
Output: `$WORK/frames/<shot>/<quality>/NNNN.png` (+ `sheet.png`). Look at the PNGs with the Read tool.

## Shot script contract (`shots/<id>.py`)
```python
from lib import core as C
def build(ctx):
    # ctx.nframes (timeline frames), ctx.render_frames (incl. dissolve tail), ctx.fps = 24
    # ctx.phrases: [{"text","start","end"}] seconds relative to shot start; ctx.phrase_frames(i)
    # ctx.u(frame) -> 0..1 progress; ctx.frame(sec); ctx.seed
    # ctx.samples = 6            # final-quality EEVEE samples override (default 8)
    # ctx.render_opts = {...}    # kwargs for core.configure_render (raytracing, volumetrics, motion_blur, look, exposure)
    # ctx.post = {...}           # hints for the compositor (see comp/)
    # ctx.needs_bake = True      # if it uses particles / cloth / rigid bodies
```
Frames are 1-based. Animate with `C.animate_camera(cam, fn)` / `C.key_fn` / `C.keys`; always parameterise
timing by `ctx.nframes` / phrase times so timing changes don't require edits.

## Render budget (important)
Final quality on this CPU costs ~3–6 s/frame. The whole film is ~6400 frames. Target ≤ 4 s/frame
(measure with `--quality final --frames 1-3`, ignore the first frame which includes shader compile).
Levers: `ctx.samples` (6 is usually fine), `ctx.render_opts["volumetrics"]="low"`, fewer/larger fog volumes,
avoid `raytracing=True` unless reflections matter, decimate distant meshes, keep subdivision levels low.

## Look
- Colour management: AgX, look "AgX - Medium High Contrast" (default). Compositor adds bloom, vignette, grade.
- Portrait composition: subject in the centre square (thumbnail crop); captions sit in the lower third, so
  keep critical detail out of the bottom ~25% where possible.
- Lifelike: real-world scale, PBR textures (Poly Haven), soft area/sun light, atmospheric depth (fog boxes),
  shallow DOF for close-ups (`C.camera(..., fstop=2.0)`), slow motivated camera moves, subtle handheld noise.
- NEVER use a world volume (EEVEE Next makes it infinite → black sky). Use `C.atmosphere()` / `C.fog_box()`.
- Taste: reverent, no gore. Suggest violence (shadows, cut-aways, a single drop of blood).

## Ownership
Each module/shot belongs to one agent. Only make backwards-compatible bug fixes to `lib/core.py` /
`render_shot.py` and mention them in your report. Don't commit or push — the lead integrates.
