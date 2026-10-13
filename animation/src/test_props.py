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
c = props.cane(coll); c.location = (0.3, 2.0, 0.92)
l = props.loaf(coll); l.location = (0.6, 2.0, 0.2)
p = props.banana_peel(coll); p.location = (0.0, 1.6, 0.0)
r = props.roll(coll); r.location = (0.8, 1.7, 0.04)
s = props.sack(coll); s.location = (1.2, 2.2, 0.3)
b = props.basket(coll); b.location = (-0.4, 2.0, 0.0)
n = props.newspaper(coll); n.location = (-0.2, 1.6, 0.3)
sn = props.snowfall(coll)
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
cam.location = (0.4, -0.4, 0.9); cam.data.lens = 30
cam.rotation_euler = (Vector((0.4, 2.0, 0.3)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; c_ = sc.cycles; c_.samples = 5; c_.use_denoising = True; c_.denoising_prefilter = 'FAST'
c_.max_bounces = 2; c_.diffuse_bounces = 1; c_.use_fast_gi = True; c_.fast_gi_method = 'REPLACE'; sc.world.light_settings.ao_factor = 1.0; sc.world.light_settings.distance = 3.0
sc.render.resolution_x = 540; sc.render.resolution_y = 960
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.fps = 24
for fr in (1, 24):
    sc.frame_set(fr)
    sc.render.filepath = os.path.join(OUT, 'p_%03d.png' % fr)
    t = time.time(); bpy.ops.render.render(write_still=True); print('RT', time.time() - t)
