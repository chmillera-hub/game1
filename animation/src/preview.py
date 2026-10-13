"""Render preview stills from film.blend (run inside Blender).
argv: out_dir mode(sheet|frames) [frames csv] [res_y] [spp]"""
import sys, os, json
import bpy
argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
mode = argv[1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
res_y = int(argv[3]) if len(argv) > 3 else 480
spp = int(argv[4]) if len(argv) > 4 else 3
sc.render.engine = 'CYCLES'
c = sc.cycles
c.samples = spp; c.use_denoising = True; c.denoising_prefilter = 'FAST'; c.use_adaptive_sampling = True
c.adaptive_threshold = 0.1
c.max_bounces = 2; c.diffuse_bounces = 1; c.glossy_bounces = 1; c.transmission_bounces = 1; c.transparent_max_bounces = 3
c.use_fast_gi = True; c.fast_gi_method = 'REPLACE'
sc.world.light_settings.ao_factor = 1.0; sc.world.light_settings.distance = 3.0
c.caustics_reflective = False; c.caustics_refractive = False
sc.render.resolution_y = res_y; sc.render.resolution_x = res_y * 9 // 16
sc.render.use_persistent_data = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
frames = [int(x) for x in argv[2].split(',')]
markers = sorted([(m.frame, m.camera) for m in sc.timeline_markers], key=lambda x: x[0])
for f in frames:
    cam = None
    for (mf, mc) in markers:
        if mf <= f:
            cam = mc
    sc.camera = cam
    sc.frame_set(f)
    sc.render.filepath = os.path.join(out, 'f%05d.png' % f)
    bpy.ops.render.render(write_still=True)
