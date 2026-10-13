"""Final render of film.blend to a PNG sequence (run inside Blender).

argv: out_dir [first_frame] [last_frame] [spp]
Resumable: frames already on disk are skipped (placeholders let several
processes share one range).
"""
import os
import sys

import bpy

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[0]
sc = bpy.context.scene
f0 = int(argv[1]) if len(argv) > 1 else sc.frame_start
f1 = int(argv[2]) if len(argv) > 2 else sc.frame_end
spp = int(argv[3]) if len(argv) > 3 else 5
os.makedirs(out, exist_ok=True)

sc.render.engine = 'CYCLES'
c = sc.cycles
c.device = 'CPU'
c.samples = spp
c.use_adaptive_sampling = True
c.adaptive_threshold = 0.08
c.use_denoising = True
c.denoiser = 'OPENIMAGEDENOISE'
c.denoising_prefilter = 'FAST'
c.seed = 0
c.use_animated_seed = False
c.max_bounces = 2
c.diffuse_bounces = 1
c.glossy_bounces = 1
c.transmission_bounces = 1
c.transparent_max_bounces = 3
c.caustics_reflective = False
c.caustics_refractive = False
c.use_fast_gi = True
c.fast_gi_method = 'REPLACE'
sc.world.light_settings.ao_factor = 1.0
sc.world.light_settings.distance = 3.0
sc.render.resolution_x = 540
sc.render.resolution_y = 960
sc.render.resolution_percentage = 100
sc.render.use_persistent_data = True
sc.render.use_overwrite = False
sc.render.use_placeholder = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
sc.render.image_settings.color_depth = '8'
sc.render.image_settings.compression = 15
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.frame_start = f0
sc.frame_end = f1
sc.render.filepath = os.path.join(out, 'f#####')
bpy.ops.render.render(animation=True)
