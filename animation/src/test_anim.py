"""Animation test (run inside Blender)."""
import sys, os, math, json, time
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, env, character, chars, rigctl, perf

OUT = sys.argv[sys.argv.index('--') + 1]
mode = sys.argv[sys.argv.index('--') + 2]
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
C = character.Character(chars.SPECS['clown'])
A = perf.Actor(C, 'clown', seed=3)
perf.RES.actors['clown'] = A
tgt = Vector((0.0, -1.6, 0.55))   # a point to look at / offer to
A.place(0, 1.2, 1.0, 0)
A.posture(0, 'stand', splay=24, knee=0.2)
A.walk(0.5, 3.5, [(1.2, 1.0), (0.0, -0.6)], stride=0.36, splay=24, style='waddle', bob=0.025, sway=0.022, lift=0.06)
A.look_at(0.2, Vector((0, -6, 1.3)), dur=0.4)
A.look_at(3.6, tgt, dur=0.6)
A.posture(4.0, 'kneel', dur=1.1, down='R')
A.gesture(5.0, 'R', ('chest', (-0.12, -0.42, 1.0), (0.1, -1, 0.1), (0, 0, -1)), dur=0.7)
A.fingers(5.0, 'R', 0.08, spread=0.3, thumb=0.0, dur=0.5)
line = json.load(open(OUT + '/../test_line.json'))
A.say(6.0, line['visemes'])
A.expr(5.6, brow_in=0.6, brow=0.2, smile=0.25, dur=0.6)
A.nod(7.4, amt=5)
A.expr(7.6, smile=0.6, lidlo_L=0.4, lidlo_R=0.4, dur=0.8)
T = 9.0
sc.render.fps = 24
sc.frame_start, sc.frame_end = 0, int(T * 24)
t0 = time.time()
perf.bake(A, 0, int(T * 24))
print('BAKE', time.time() - t0)
bpy.ops.mesh.primitive_plane_add(size=10)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
bpy.ops.object.light_add(type='SUN'); bpy.context.object.rotation_euler = (0.8, 0.2, -0.6); bpy.context.object.data.energy = 3
bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam
if mode == 'side':
    cam.location = (3.2, -1.2, 1.0); look = Vector((0.2, -0.5, 0.8)); cam.data.lens = 35
else:
    cam.location = (0.4, -3.6, 1.1); look = Vector((0.2, -0.3, 0.8)); cam.data.lens = 35
cam.rotation_euler = (look - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 2; sc.cycles.diffuse_bounces = 1
sc.render.resolution_x = 270; sc.render.resolution_y = 480
frames = [int(x) for x in sys.argv[sys.argv.index('--') + 3].split(',')]
for fr in frames:
    sc.frame_set(fr)
    sc.render.filepath = os.path.join(OUT, '%s_%04d.png' % (mode, fr))
    bpy.ops.render.render(write_still=True)
