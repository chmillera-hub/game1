"""Cast lineup render (run inside Blender)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
import blib, character, chars, rigctl
OUT = sys.argv[sys.argv.index('--') + 1]
names = sys.argv[sys.argv.index('--') + 2].split(',')
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene
Cs = []
for i, n in enumerate(names):
    C = character.Character(chars.SPECS[n])
    C.arm.location = ((i - (len(names) - 1) / 2) * 0.75, 0, 0)
    pb = C.arm.pose.bones
    Cs.append(C)
bpy.ops.mesh.primitive_plane_add(size=20)
blib.assign(bpy.context.object, blib.principled('g', (0.3, 0.3, 0.3), rough=0.9))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.55, 0.65, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.5
bpy.ops.object.light_add(type='SUN'); s = bpy.context.object; s.rotation_euler = (math.radians(50), 0, math.radians(-30)); s.data.energy = 3; s.data.color = (1, .9, .8)
bpy.ops.object.camera_add(); cam = bpy.context.object; sc.camera = cam
W = len(names) * 0.75
cam.data.lens = 50
cam.location = (0, -max(3.2, W * 1.6), 1.0)
cam.rotation_euler = (Vector((0, 0, 0.85)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
sc.render.engine = 'CYCLES'; sc.cycles.samples = 6; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 2; sc.cycles.diffuse_bounces = 1
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.resolution_x = 1200; sc.render.resolution_y = 700
sc.render.filepath = os.path.join(OUT, 'cast.png')
bpy.ops.render.render(write_still=True)
# face close-ups
sc.render.resolution_x = 360; sc.render.resolution_y = 420
cam.data.lens = 85
for C in Cs:
    ho = C.arm.matrix_world @ Vector(C.head_origin)
    tgt = ho + Vector((0, 0, -0.02))
    cam.location = tgt + Vector((0.25, -0.85, 0.05)) * C.s['head_scale']
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, 'face_%s.png' % C.name)
    bpy.ops.render.render(write_still=True)
