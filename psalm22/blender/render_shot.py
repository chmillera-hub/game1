"""Render one shot. Run through ./run.sh (wraps xvfb-run + Blender):

    psalm22/blender/run.sh --shot s01a --quality preview --frames sheet6
    psalm22/blender/run.sh --shot s01a --quality final   --frames all
    psalm22/blender/run.sh --shot s01a --quality final   --frames 1-120

--frames: 'all' | 'sheet<N>' (N evenly spaced frames + contact sheet) | '1,40,80' | 'a-b'
          | 'odd' / 'odd:a-b' (odd frames only = 12 fps; fill the evens with comp/interp.py)
          | 'auto' / 'auto:a-b' (= 'odd[:a-b]' if the shot sets ctx.interp = True, else 'all' / 'a-b')
--skip-existing: only render frames whose PNG doesn't exist yet (resume). Writes meta.json (interp, needs_bake).
--quality: preview (270x480, 3 spp) | draft (540x960, 3 spp) | final (540x960, ctx.samples or 8 spp)
--save-blend: also write the built scene to WORK/blend/<shot>.blend for inspection.
Output: WORK/frames/<shot>/<quality>/NNNN.png (NNNN = 1-based shot frame) + post.json (+ sheet.png)
"""
import bpy, sys, os, json, time, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import core  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
opts = {"--quality": "preview", "--frames": "sheet6", "--save-blend": False, "--skip-existing": False}
i = 0
while i < len(argv):
    a = argv[i]
    if a in ("--save-blend", "--skip-existing"):
        opts[a] = True
        i += 1
    else:
        opts[a] = argv[i + 1]
        i += 2
shot_id = opts["--shot"]
quality = opts["--quality"]

tl = json.load(open(os.path.join(core.ROOT, "timeline.json")))
shot = next(s for s in tl["shots"] if s["id"] == shot_id)
ctx = core.Ctx(shot, quality, tl["fps"])
core.reset_scene(ctx)
mod = importlib.import_module("shots." + shot_id)
t0 = time.time()
mod.build(ctx)
core.configure_render(ctx, **ctx.render_opts)
print("BUILD_TIME %.1fs" % (time.time() - t0))

spec = opts["--frames"]
if spec == "auto" or spec.startswith("auto:"):
    # the shot decides: ctx.interp = True -> half-rate render, evens filled by comp/interp.py
    rng = spec[5:] if ":" in spec else ""
    if getattr(ctx, "interp", False):
        spec = "odd:" + rng if rng else "odd"
    else:
        spec = rng if rng else "all"
    print("AUTO_FRAMES", spec)
N = ctx.render_frames
sheet = None
if spec == "all":
    frames = list(range(1, N + 1))
elif spec.startswith("sheet"):
    k = int(spec[5:] or 6)
    frames = sorted(set(max(1, min(N, round(1 + (N - 1) * j / (k - 1)))) for j in range(k)))
    sheet = frames
elif spec == "odd" or spec.startswith("odd:"):
    # half-rate render (odd frames only); comp/interp.py synthesises the even frames afterwards
    a, b = spec[4:].split("-") if ":" in spec else (1, N)
    frames = [f for f in range(int(a), min(N, int(b)) + 1) if f % 2 == 1]
    # in-shot hard cuts: RIFE can't bridge a cut, so a shot lists the even frame(s) next to the cut in
    # ctx.interp_keep and they are rendered too (interp.py only fills frames that are missing)
    frames = sorted(set(frames) | {int(f) for f in getattr(ctx, "interp_keep", ()) if int(a) <= int(f) <= min(N, int(b))})
elif "-" in spec and "," not in spec:
    a, b = spec.split("-")
    frames = list(range(int(a), min(N, int(b)) + 1))
else:
    frames = [int(x) for x in spec.split(",")]

out = os.path.join(core.WORK, "frames", shot_id, quality)
os.makedirs(out, exist_ok=True)
json.dump({"interp": bool(getattr(ctx, "interp", False)), "needs_bake": bool(ctx.needs_bake),
           "interp_keep": sorted(int(f) for f in getattr(ctx, "interp_keep", ())),
           "render_frames": N, "samples": ctx.samples, "render_opts": ctx.render_opts},
          open(os.path.join(out, "meta.json"), "w"), indent=1)
if opts["--skip-existing"]:
    have = lambda f: os.path.exists(os.path.join(out, "%04d.png" % f)) and os.path.getsize(os.path.join(out, "%04d.png" % f)) > 0
    todo = [f for f in frames if not have(f)]
    print("SKIP_EXISTING %d of %d frames already rendered" % (len(frames) - len(todo), len(frames)))
    if not todo:
        core.save_post(ctx, os.path.join(out, "post.json"))
        sys.exit(0)
    if spec.startswith("odd") and todo != frames:
        spec = "list"   # fall back to per-frame renders for the remaining odd frames
    frames = todo
if ctx.needs_bake and (frames != list(range(1, N + 1))):
    tb = time.time()
    core.bake_all(ctx)
    print("BAKE_TIME %.1fs" % (time.time() - tb))
if opts["--save-blend"]:
    os.makedirs(os.path.join(core.WORK, "blend"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(core.WORK, "blend", shot_id + ".blend"), copy=True)

sc = bpy.context.scene
tr = time.time()
if frames == list(range(frames[0], frames[-1] + 1)) and len(frames) > 1:
    sc.frame_start, sc.frame_end = frames[0], frames[-1]
    sc.render.filepath = os.path.join(out, "####")
    bpy.ops.render.render(animation=True)
elif spec.startswith("odd") and len(frames) > 1 and frames == list(range(frames[0], frames[-1] + 1, 2)):
    # every other frame via the animation path (random access -> baked above when ctx.needs_bake)
    sc.frame_start, sc.frame_end, sc.frame_step = frames[0], frames[-1], 2
    sc.render.filepath = os.path.join(out, "####")
    bpy.ops.render.render(animation=True)
else:
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(out, "%04d.png" % f)
        bpy.ops.render.render(write_still=True)
dt = time.time() - tr
print("RENDER_TIME %.1fs for %d frames (%.2fs/frame)" % (dt, len(frames), dt / max(1, len(frames))))
core.save_post(ctx, os.path.join(out, "post.json"))

if sheet:
    import subprocess
    files = [os.path.join(out, "%04d.png" % f) for f in sheet]
    dst = os.path.join(out, "sheet.png")
    labels = []
    for f, p in zip(sheet, files):
        labels += ["-label", "f%d" % f, p]
    subprocess.run(["montage", *labels, "-tile", "%dx" % min(len(files), 6), "-geometry", "+3+3",
                    "-background", "#222", "-fill", "white", "-pointsize", "14", dst], check=False)
    print("SHEET", dst)
