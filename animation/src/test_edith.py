import sys, os, math, json
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, env, character, chars, rigctl, perf
OUT = sys.argv[sys.argv.index('--') + 1]
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
S = env.build_set()
W = env.setup_world('afternoon')
C = character.Character(chars.SPECS['edith'])
A = perf.Actor(C, 'edith', seed=5)
perf.RES.actors['edith'] = A
ex, ey = env.EDITH_XY
A.place(0, ex, ey, 0, z=env.SIDEWALK_Z)
A.posture(0, 'sit_wall', sill=env.SILL_H, knees=0.9, back=0.10, hands='knees')
O = character.Character(chars.SPECS['oswald'])
B = perf.Actor(O, 'oswald', seed=6)
perf.RES.actors['oswald'] = B
B.place(0, ex + 0.25, ey - 0.95, 160, z=env.SIDEWALK_Z)
B.posture(0, 'kneel', down='R')
B.gesture(0, 'R', ('world', (ex + 0.08, ey - 0.45, env.SIDEWALK_Z + 0.62), (0.3, 1, 0.1), (0, 0, -1)), dur=0.01)
B.fingers(0, 'R', 0.1, spread=0.2, thumb=0.0, dur=0.01)
A.look_at(0, ('actor', 'oswald', 'head'), dur=0.01)
B.look_at(0, ('actor', 'edith', 'head'), dur=0.01)
A.expr(0, brow_in=0.5, smile=-0.2, dur=0.01)
B.expr(0, brow_in=0.3, smile=0.2, dur=0.01)
perf.bake(A, 0, 2)
perf.bake(B, 0, 2)
sc.frame_set(1)
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
sc.render.engine = 'CYCLES'; c_ = sc.cycles; c_.samples = 5; c_.use_denoising = True; c_.denoising_prefilter = 'FAST'
c_.max_bounces = 2; c_.diffuse_bounces = 1; c_.use_fast_gi = True; c_.fast_gi_method = 'REPLACE'; sc.world.light_settings.ao_factor = 1.0; sc.world.light_settings.distance = 3.0
sc.render.resolution_x = 540; sc.render.resolution_y = 960
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
shots = {'a_profile': ((ex + 2.0, ey - 0.75, 0.95), (ex + 0.15, ey - 0.55, 0.75), 35),
         'b_front': ((ex + 0.6, ey - 2.6, 1.0), (ex, ey - 0.3, 0.6), 35),
         'c_ots': ((ex + 0.55, ey - 1.55, 1.05), (ex - 0.02, ey - 0.15, 0.85), 50)}
for k, (loc, tgt, lens) in shots.items():
    cam.location = Vector(loc); cam.data.lens = lens
    cam.rotation_euler = (Vector(tgt) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, k + '.png')
    bpy.ops.render.render(write_still=True)
