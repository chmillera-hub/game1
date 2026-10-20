"""Shared helpers for set-building scripts (run inside Blender 4.5, --factory-startup).

Contract every set script follows:
  * Usage: blender -b --factory-startup -P sets/<name>.py -- /opt/work/sets/<name>.blend
  * Builds into an empty scene: geometry in collection SET_<name>, lights in LIGHTS_<name>,
    world named W_<name> (assigned to the scene).
  * Meters, Z up, ground at z=0. Characters are ~1.75 m tall and face -Y in their rest pose.
  * Character marks: Empties named MARK_<ROLE>. A character is placed at the empty's location
    with the empty's Z rotation, so it faces the empty's local -Y axis.
  * Camera hints: cameras named CAMHINT_<label> (9:16 portrait framing, sensor_fit VERTICAL).
  * Procedural materials only (no downloaded textures); no volumetrics; keep < 300k faces.
"""
import bpy, math, os, sys
from mathutils import Vector, Euler


def out_path():
    argv = sys.argv
    return argv[argv.index("--") + 1] if "--" in argv else None


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = 'METRIC'
    return scn


def collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    return col


def link(obj, col):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def mark(role, loc, rot_z_deg=0.0, col=None):
    e = bpy.data.objects.new(f"MARK_{role}", None)
    e.empty_display_type = 'SINGLE_ARROW'
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z_deg))
    (col or bpy.context.scene.collection).objects.link(e)
    return e


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camhint(label, loc, target, lens=50.0, col=None):
    cd = bpy.data.cameras.new(f"CAMHINT_{label}")
    cd.lens = lens
    cd.sensor_fit = 'VERTICAL'
    cd.sensor_height = 24.0
    cam = bpy.data.objects.new(f"CAMHINT_{label}", cd)
    (col or bpy.context.scene.collection).objects.link(cam)
    cam.location = loc
    look_at(cam, target)
    return cam


def principled(name, color=(0.8, 0.8, 0.8), rough=0.5, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


def stand_in_figure(loc, rot_z_deg=0.0, height=1.75, col=None, name="STANDIN"):
    """Grey capsule placeholder used only for preview renders (deleted before saving)."""
    bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=height - 0.25, location=(loc[0], loc[1], (height - 0.25) / 2))
    body = bpy.context.object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(loc[0], loc[1], height - 0.12))
    head = bpy.context.object
    for o in (body, head):
        o.name = name
        if col:
            link(o, col)
    return [body, head]


def render_previews(prefix, res=(270, 480), samples=8):
    """Render every CAMHINT camera to /opt/work/sets/previews/<prefix>_<label>.png."""
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'CPU'
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = 4
    scn.cycles.diffuse_bounces = 2
    scn.cycles.glossy_bounces = 1
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'AgX - Medium High Contrast'
    os.makedirs("/opt/work/sets/previews", exist_ok=True)
    paths = []
    for cam in [o for o in scn.objects if o.name.startswith("CAMHINT_")]:
        scn.camera = cam
        scn.render.filepath = f"/opt/work/sets/previews/{prefix}_{cam.name[8:]}.png"
        bpy.ops.render.render(write_still=True)
        paths.append(scn.render.filepath)
    return paths


def save(path):
    for o in [o for o in bpy.data.objects if o.name.startswith("STANDIN")]:
        bpy.data.objects.remove(o, do_unlink=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
