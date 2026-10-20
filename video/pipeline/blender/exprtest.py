"""Render a grid of facial expressions/visemes for a character to validate face shape keys."""
import bpy, sys, os
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
import rigtools as rt
name = sys.argv[sys.argv.index("--") + 1]
scn = bpy.context.scene
rig = bpy.data.objects[name]
rt.reset(rig); rt.arms_down(rig)
meshes = [o for o in rig.children if o.type == 'MESH' and o.data.shape_keys]
def setk(d):
    for o in meshes:
        kb = o.data.shape_keys.key_blocks
        for k in kb:
            if not k.name.startswith("$md") and k.name != "Basis":
                k.value = 0
        for k, v in d.items():
            if k in kb: kb[k].value = v
EXPR = {
 "neutral": {},
 "smile": {"mouthSmileLeft": .7, "mouthSmileRight": .7, "cheekSquintLeft": .4, "cheekSquintRight": .4, "eyeSquintLeft": .3, "eyeSquintRight": .3},
 "sad": {"browInnerUp": .8, "mouthFrownLeft": .5, "mouthFrownRight": .5, "eyeSquintLeft": .2, "eyeSquintRight": .2, "mouthPressLeft": .3, "mouthPressRight": .3},
 "angry": {"browDownLeft": .8, "browDownRight": .8, "noseSneerLeft": .5, "noseSneerRight": .5, "mouthPressLeft": .5, "mouthPressRight": .5, "eyeSquintLeft": .4, "eyeSquintRight": .4},
 "surprise": {"browInnerUp": .8, "browOuterUpLeft": .8, "browOuterUpRight": .8, "eyeWideLeft": .7, "eyeWideRight": .7, "jawOpen": .3},
 "blink": {"eyeBlinkLeft": 1, "eyeBlinkRight": 1},
 "aa": {"aa_02": 1.0}, "oh": {"ow_08": 1.0}, "pbm": {"p_b_m_21": 1.0}, "ee": {"y_iy_ih_ix_06": 1.0}, "ff": {"f_v_18": 1.0}, "jaw": {"jawOpen": 0.6},
}
eye = rig.matrix_world @ rig.pose.bones["eye.L"].head
w = bpy.data.worlds.new("W"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.1, 0.1, 0.11, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.3
def area(n, loc, e, size, col):
    l = bpy.data.lights.new(n, 'AREA'); l.energy = e; l.size = size; l.color = col
    o = bpy.data.objects.new(n, l); scn.collection.objects.link(o); o.location = loc
    o.rotation_euler = (eye - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
area("Key", (0.9, -1.2, eye.z + 0.5), 50, 1.0, (1, 0.92, 0.82)); area("Fill", (-1.2, -1.0, eye.z), 12, 2.0, (0.8, 0.88, 1)); area("Rim", (-0.3, 1.2, eye.z + 0.4), 40, 0.8, (1, 1, 1))
cd = bpy.data.cameras.new("C"); cd.lens = 100; cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new("C", cd); scn.collection.objects.link(cam); scn.camera = cam
t = Vector((0, eye.y, eye.z - 0.045)); cam.location = t + Vector((0.12, -0.75, 0.0))
cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
scn.render.engine = 'CYCLES'; scn.cycles.samples = 8; scn.cycles.use_denoising = True; scn.cycles.transparent_max_bounces = 8
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.resolution_x = 220; scn.render.resolution_y = 260
os.makedirs("/opt/work/chars/expr", exist_ok=True)
files = []
for k, d in EXPR.items():
    setk(d)
    scn.render.filepath = f"/opt/work/chars/expr/{name}_{k}.png"
    bpy.ops.render.render(write_still=True); files.append(scn.render.filepath)
print("EXPR_OK")
