"""Render the set with a character for look development (run inside Blender)."""
import sys, os, math, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, env, character, chars, rigctl

OUT = sys.argv[sys.argv.index('--') + 1]
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
S = env.build_set()
W = env.setup_world('afternoon')
C = character.Character(chars.SPECS['clown'])
C.arm.location = (0.6, 2.2, 0)
C.arm.rotation_euler = (0, 0, math.radians(-15))
bpy.ops.object.camera_add()
cam = bpy.context.object
sc.camera = cam
sc.render.engine = 'CYCLES'
c = sc.cycles
c.samples = 5; c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'; c.denoising_prefilter = 'FAST'
c.use_adaptive_sampling = True; c.adaptive_threshold = 0.05
c.max_bounces = 2; c.diffuse_bounces = 1; c.glossy_bounces = 1; c.transmission_bounces = 0; c.use_fast_gi = True; c.fast_gi_method = 'REPLACE'; sc.world.light_settings.ao_factor = 1.0; sc.world.light_settings.distance = 3.0; c.adaptive_threshold = 0.08
c.caustics_reflective = False; c.caustics_refractive = False
sc.render.resolution_x = 540; sc.render.resolution_y = 960
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'

def shot(name, loc, tgt, lens):
    cam.location = Vector(loc)
    cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, name + '.png')
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print('RT', name, time.time() - t)

shot('a_wide', (-0.6, -4.2, 1.1), (0.9, 3.0, 3.2), 22)
shot('b_med', (0.0, -0.6, 1.35), (0.6, 2.2, 1.1), 40)
shot('c_close', (0.3, 0.9, 1.45), (0.55, 2.2, 1.42), 55)
