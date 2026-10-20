"""Preview a built character: blender -b /opt/work/chars/NAME.blend -P charpreview.py -- NAME [res] [samples]"""
import bpy, sys, os, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(__file__))
import rigtools as rt

argv = sys.argv[sys.argv.index("--") + 1:]
name = argv[0]
res = int(argv[1]) if len(argv) > 1 else 480
samples = int(argv[2]) if len(argv) > 2 else 12
scn = bpy.context.scene
rig = bpy.data.objects[name]
rt.reset(rig)
rt.arms_down(rig)
body = bpy.data.objects[f"{name}.body"]
for o in [body] + [c for c in rig.children if c.data and getattr(c.data, "shape_keys", None)]:
    kb = o.data.shape_keys.key_blocks
    for k, v in (("mouthSmileLeft", 0.25), ("mouthSmileRight", 0.25), ("browInnerUp", 0.15)):
        if k in kb:
            kb[k].value = v
for o in rig.children:
    if o.name.endswith("robe_legs"):
        o.hide_render = True
eye = rig.matrix_world @ rig.pose.bones["eye.L"].head
head_z = eye.z
# floor + backdrop
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.22, 0.2, 1)
floor.data.materials.append(fm)
w = bpy.data.worlds.new("W"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.12, 0.13, 0.15, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.25


def area(n, loc, e, size, col, target):
    l = bpy.data.lights.new(n, 'AREA'); l.energy = e; l.size = size; l.color = col
    o = bpy.data.objects.new(n, l); scn.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


tgt = (0, eye.y, head_z - 0.1)
area("Key", (1.3, -1.6, head_z + 0.6), 70, 1.0, (1, 0.9, 0.78), tgt)
area("Fill", (-1.6, -1.2, head_z), 15, 2.0, (0.75, 0.85, 1.0), tgt)
area("Rim", (-0.4, 1.4, head_z + 0.5), 70, 0.8, (1, 0.95, 0.9), tgt)
cd = bpy.data.cameras.new("C"); cd.sensor_fit = 'VERTICAL'
cam = bpy.data.objects.new("C", cd); scn.collection.objects.link(cam); scn.camera = cam
scn.render.engine = 'CYCLES'; scn.cycles.device = 'CPU'; scn.cycles.samples = samples
scn.cycles.use_denoising = True
scn.cycles.max_bounces = 4; scn.cycles.diffuse_bounces = 2; scn.cycles.glossy_bounces = 1
scn.cycles.transparent_max_bounces = 8; scn.cycles.transmission_bounces = 3; scn.cycles.max_bounces = 4
scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - Medium High Contrast'
scn.render.resolution_x = res * 9 // 16; scn.render.resolution_y = res
os.makedirs("/opt/work/chars/previews", exist_ok=True)
for label, lens, dist, zoff, xoff in (("cu", 85, 1.05, -0.05, 0.18), ("med", 50, 2.1, -0.35, 0.3), ("full", 35, 4.6, -0.75, 0.5)):
    cd.lens = lens
    t = Vector((0, eye.y, head_z + zoff))
    cam.location = t + Vector((xoff, -dist, 0.02))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scn.render.filepath = f"/opt/work/chars/previews/{name}_{label}.png"
    bpy.ops.render.render(write_still=True)
print("PREVIEW_OK")
