import sys, os, math, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, env, props
OUT = sys.argv[sys.argv.index('--') + 1]
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
S = env.build_set()
W = env.setup_world('afternoon')
coll = bpy.data.collections.new('PROPS'); sc.collection.children.link(coll)
props.snowfall(coll)
th = S['tower']['hands']
th['hour'].rotation_euler = (0, math.radians((3 + 29/60) / 12 * 360), 0)
th['minute'].rotation_euler = (0, math.radians(29 / 60 * 360), 0)
hg = S['door_hinge']; hg.rotation_euler = (0, 0, math.radians(-35))
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
sc.render.engine = 'CYCLES'; c_ = sc.cycles; c_.samples = 5; c_.use_denoising = True; c_.denoising_prefilter = 'FAST'
c_.max_bounces = 2; c_.diffuse_bounces = 1; c_.use_fast_gi = True; c_.fast_gi_method = 'REPLACE'; sc.world.light_settings.ao_factor = 1.0; sc.world.light_settings.distance = 3.0
sc.render.resolution_x = 540; sc.render.resolution_y = 960
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
shots = {'s11': ((-6.9, -5.2, 1.6), (-0.8, 6.0, 4.6), 30), 's11b': ((-6.4, -3.0, 1.6), (-0.6, 6.0, 4.4), 26)}
for k, (loc, tgt, lens) in shots.items():
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, k + '.png')
    bpy.ops.render.render(write_still=True)
