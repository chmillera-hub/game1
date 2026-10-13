"""Build a test character and render a few poses (run inside Blender)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import bpy
import numpy as np
from mathutils import Vector, Quaternion, Euler
import blib, character

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/char'
os.makedirs(OUT, exist_ok=True)
blib.clear_scene()
sc = bpy.context.scene

spec = dict(name='clown', head=dict(), head_scale=1.32, leg_len=0.66, torso_len=0.44,
            hat='bowler', hair_style='short', bowtie=(0.45, 0.08, 0.08),
            coat=(0.05, 0.05, 0.06), trousers=(0.16, 0.15, 0.13), shoe_scale=1.35, thigh_r=0.08, calf_r=0.07, hem_r=0.072)
C = character.Character(spec)
arm = C.arm

# ground + lights
bpy.ops.mesh.primitive_plane_add(size=6)
g = bpy.context.object
blib.assign(g, blib.principled('ground', (0.3, 0.28, 0.25), rough=0.8))
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.4, 0.45, 0.55, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.4
bpy.ops.object.light_add(type='SUN')
sun = bpy.context.object; sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-35)); sun.data.color = (1, 0.9, 0.78)
sun.data.angle = math.radians(8)
bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam; cam.data.lens = 50
sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True
sc.render.resolution_x = 360; sc.render.resolution_y = 640
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'

def look(tgt, az, el, dist, lens=50):
    cam.data.lens = lens
    a, e = math.radians(az), math.radians(el)
    tgt = Vector(tgt)
    cam.location = tgt + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()

def shoot(name):
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)

pb = arm.pose.bones
look((0, 0, 0.85), 20, 5, 4.2)
shoot('a_rest')
look((0, 0, 0.85), 120, 5, 4.2)
shoot('b_back')
# pose: arms forward (offering), head turned, jaw open, fingers curled on right
pb['hand_ik.L'].location = Vector((0, 0, 0))
def set_ik(side, world_pos, rot=None):
    b = arm.data.bones['hand_ik.' + side]
    rest = arm.matrix_world @ b.matrix_local
    m = rest.copy(); m.translation = Vector(world_pos)
    if rot is not None:
        m = Matrix.Translation(Vector(world_pos)) @ rot.to_matrix().to_4x4()
    pb['hand_ik.' + side].matrix = arm.matrix_world.inverted() @ m
from mathutils import Matrix
bL = arm.data.bones['hand_ik.L'].matrix_local
set_ik('L', (0.20, -0.30, 0.98))
set_ik('R', (-0.16, -0.16, 0.80))
bpy.context.view_layer.update()
pb['head'].rotation_quaternion = Euler((math.radians(-8), math.radians(20), math.radians(6))).to_quaternion()
pb['jaw'].rotation_quaternion = Euler((math.radians(-12), 0, 0)).to_quaternion()
for f in ('index', 'middle', 'ring', 'pinky'):
    for i in (1, 2, 3):
        pb['%s%d.R' % (f, i)].rotation_quaternion = Euler((math.radians(-60), 0, 0)).to_quaternion()
for i in (1, 2, 3):
    pb['thumb%d.R' % i].rotation_quaternion = Euler((math.radians(-25), 0, 0)).to_quaternion()
head = C.head
head.data.shape_keys.key_blocks['smile_L'].value = 0.8
head.data.shape_keys.key_blocks['smile_R'].value = 0.8
pb['brow_in_L'].location = Vector((0, 0, 0.005))
pb['brow_in_R'].location = Vector((0, 0, 0.005))
pb['lid_up_L'].rotation_quaternion = Euler((math.radians(-8), 0, 0)).to_quaternion()
# kneel-ish: lower hips, left foot forward
pb['foot_ik.L'].location = Vector((0, 0, 0))
bpy.context.view_layer.update()
look((0, 0, 0.9), 25, 5, 4.0)
shoot('c_pose')
look(tuple(Vector(C.head_origin) + Vector((0, 0, 0.0))), 15, 3, 1.0, lens=85)
shoot('d_face')
look((0.15, -0.25, 1.0), 40, 10, 0.9, lens=85)
shoot('e_hands')
