"""Render the childhood photo of the two sisters used in the apartment (PROP_PHOTO).

blender -b -P kidsphoto.py   ->  /opt/work/props/sisters_photo.png
"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigtools as rt


def append(name):
    with bpy.data.libraries.load(f"/opt/work/chars/{name}.blend", link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == f"CHAR_{name}"]
    bpy.context.scene.collection.children.link(dst.collections[0])
    return bpy.data.objects[name]


def setk(rig, d):
    for o in rig.children:
        if o.type == 'MESH' and o.data.shape_keys and not o.name.endswith(".high-poly"):
            kb = o.data.shape_keys.key_blocks
            for k, v in d.items():
                if k in kb:
                    kb[k].value = v


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    big = append("KID2")
    small = append("KID1")
    big.location = (0.115, 0, 0)
    big.rotation_euler = (0, 0, math.radians(-12))
    small.location = (-0.115, -0.02, 0.0)
    small.rotation_euler = (0, 0, math.radians(14))
    bpy.context.view_layer.update()
    for r in (big, small):
        rt.reset(r)
        rt.arms_down(r, out=0.08, forward=0.1, elbow=0.2)
    # holding hands between them
    rt.aim(big, "upperarm01.R", Vector((-0.35, -0.05, -0.94)))
    rt.aim(big, "upperarm02.R", Vector((-0.35, -0.05, -0.94)))
    rt.aim(big, "lowerarm01.R", Vector((-0.45, -0.1, -0.88)))
    rt.aim(big, "lowerarm02.R", Vector((-0.45, -0.1, -0.88)))
    rt.aim(small, "upperarm01.L", Vector((0.45, -0.05, -0.89)))
    rt.aim(small, "upperarm02.L", Vector((0.45, -0.05, -0.89)))
    rt.aim(small, "lowerarm01.L", Vector((0.55, -0.1, -0.6)))
    rt.aim(small, "lowerarm02.L", Vector((0.55, -0.1, -0.6)))
    rt.rotate_world(small, "head", Vector((0, 1, 0)), math.radians(-10))
    rt.rotate_world(big, "head", Vector((0, 1, 0)), math.radians(8))
    # beach at sunset: dark sand, glossy sea, sun low behind the girls
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    sand = bpy.context.object
    m = bpy.data.materials.new("sand"); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.35, 0.27, 0.18, 1)
    b.inputs["Roughness"].default_value = 0.6
    sand.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 210, 0.01))
    sea = bpy.context.object
    sm = bpy.data.materials.new("sea"); sm.use_nodes = True
    sb = sm.node_tree.nodes["Principled BSDF"]; sb.inputs["Base Color"].default_value = (0.02, 0.04, 0.06, 1)
    sb.inputs["Roughness"].default_value = 0.08
    sea.data.materials.append(sm)
    w = bpy.data.worlds.new("sky"); scn.world = w; w.use_nodes = True
    nt = w.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = 'NISHITA'
    sky.sun_elevation = math.radians(1.8); sky.sun_rotation = math.radians(180.0); sky.sun_intensity = 0.6
    sky.air_density = 2.0; sky.dust_density = 4.0
    nt.links.new(sky.outputs["Color"], nt.nodes["Background"].inputs[0])
    nt.nodes["Background"].inputs[1].default_value = 0.35
    eye = (big.matrix_world @ big.pose.bones["eye.L"].head + small.matrix_world @ small.pose.bones["eye.L"].head) / 2
    cd = bpy.data.cameras.new("C"); cd.lens = 50; cd.sensor_fit = 'VERTICAL'
    cam = bpy.data.objects.new("C", cd); scn.collection.objects.link(cam); scn.camera = cam
    t = Vector((0, 0, 0.75))
    cam.location = Vector((0.1, -4.2, 0.55))
    cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
    for r in (big, small):
        r.rotation_euler = (0, 0, r.rotation_euler.z + math.pi)  # facing the sea, backs to camera
    scn.render.engine = 'CYCLES'; scn.cycles.samples = 32; scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = 512, 640
    scn.view_settings.view_transform = 'AgX'; scn.view_settings.look = 'AgX - High Contrast'
    scn.view_settings.exposure = -1.6
    scn.render.filepath = "/opt/work/props/sisters_photo_raw.png"
    bpy.ops.render.render(write_still=True)
    print("PHOTO_OK")


main()
