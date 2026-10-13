"""Face expression contact sheet for a character (run inside Blender)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, character, rigctl, chars

OUT = sys.argv[sys.argv.index('--') + 1]
who = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else 'clown'
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
C = character.Character(chars.SPECS[who])
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.4, 0.45, 0.55, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
bpy.ops.object.light_add(type='AREA', location=(-0.8, -1.4, 2.2))
k = bpy.context.object; k.data.energy = 120; k.data.size = 1.0; k.data.color = (1, 0.92, 0.82)
bpy.ops.object.light_add(type='AREA', location=(1.0, 0.8, 1.9))
r = bpy.context.object; r.data.energy = 80; r.data.size = 0.6; r.data.color = (0.7, 0.8, 1.0)
ho = Vector(C.head_origin)
for L in (k, r):
    L.rotation_euler = (ho - L.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam; cam.data.lens = 85
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
sc.render.resolution_x = 340; sc.render.resolution_y = 400
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
hs = C.s['head_scale']
tgt = ho + Vector((0, 0, -0.02 * hs))
a = math.radians(18)
cam.location = tgt + Vector((math.sin(a), -math.cos(a), 0.05)) * 0.62 * hs
cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
EXPR = [
    ('a_neutral', dict()),
    ('b_talk_ah', dict(jaw=0.55, wide=0.2)),
    ('c_talk_oo', dict(jaw=0.25, round=1.0)),
    ('d_smile', dict(smile=1.0, lidlo_L=0.5, lidlo_R=0.5, brow=0.2)),
    ('e_warm_smile_open', dict(smile=0.9, jaw=0.25, lip_raise=0.4, lidlo_L=0.6, lidlo_R=0.6, brow=0.3, brow_in=0.3)),
    ('f_sad', dict(smile=-0.8, brow_in=1.0, brow=-0.2, lid_L=0.75, lid_R=0.75, gaze_pitch=-12, pout=0.5)),
    ('g_worried', dict(brow_in=1.0, brow=0.4, smile=-0.3, press=0.5, gaze_yaw=15)),
    ('h_angry', dict(brow_in=-1.0, brow=-0.4, smile=-0.5, lid_L=0.8, lid_R=0.8, press=0.6)),
    ('i_surprised', dict(brow=1.0, jaw=0.4, round=0.4, lid_L=1.2, lid_R=1.2)),
    ('j_blink', dict(blink=1.0)),
    ('k_look_down', dict(gaze_pitch=-25, lid_L=0.85, lid_R=0.85)),
    ('l_smirk', dict(smile=0.6, smirk=0.8, brow_asym=0.6, gaze_yaw=-12)),
]
for name, f in EXPR:
    rigctl.apply_face(C, f)
    bpy.context.view_layer.update()
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)
