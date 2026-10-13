"""Render a contact sheet of the procedural head (run inside Blender)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import importlib
import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler
import blib, headgen
importlib.reload(headgen)

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp/head'
os.makedirs(OUT, exist_ok=True)

blib.clear_scene()
sc = bpy.context.scene
H = headgen.Head()
g = H.build()
p = H.p
skin = blib.skin_material('skin', p['skin'], p['lip_color'], p['blush'], p['blush_amt'])
head = blib.make_mesh('head', g['verts'], g['faces'])
blib.set_color_attr(head, 'mask', g['colors'])
blib.set_shape_keys(head, g['shapes'])
blib.assign(head, skin)
blib.subsurf(head, 1, 2)

# eyes + lids
eyem = blib.eye_material('eye')
lidm = blib.lid_material('lid', p['skin'])
lids = {}
for key, e in g['eyes'].items():
    bpy.ops.mesh.primitive_uv_sphere_add(radius=p['eye_r'], segments=48, ring_count=24, location=tuple(e['c']))
    eo = bpy.context.object
    eo.name = 'eye_' + key
    bpy.ops.object.shade_smooth()
    blib.assign(eo, eyem)
    # orient: eye forward = local -Y
    fwd = Vector(e['fwd'])
    eo.rotation_euler = Vector((0, -1, 0)).rotation_difference(fwd).to_euler()
    for up in (True, False):
        V, F, lash = H.lid(key, upper=up)
        lo = blib.make_mesh('lid_%s_%s' % ('up' if up else 'lo', key), V, F)
        blib.set_color_attr(lo, 'lash', np.stack([lash] * 3, -1))
        blib.assign(lo, lidm)
        lo.location = tuple(e['c'])
        lo.rotation_euler = eo.rotation_euler.copy()
        blib.subsurf(lo, 1)
        lids[(key, up)] = lo
# ears
for side in (1, -1):
    V, F = H.ear(side)
    eo = blib.make_mesh('ear', V, F)
    blib.assign(eo, skin)
    blib.subsurf(eo, 1)
# teeth & tongue
teethm = blib.principled('teeth', (0.93, 0.91, 0.84), rough=0.3)
for up in (True, False):
    V, F = H.teeth(up)
    t = blib.make_mesh('teeth', V, F)
    blib.assign(t, teethm)
    blib.subsurf(t, 1)
c, r = H.tongue()
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=tuple(c))
tg = bpy.context.object
tg.scale = tuple(r)
blib.assign(tg, blib.principled('tongue', (0.6, 0.22, 0.22), rough=0.4))

# brows
def brow_mesh(H, key, head_verts):
    pts = H.brows[key]
    t = np.linspace(0, 1, 22)
    # quadratic through 3 anchors
    P0, P1, P2 = pts
    C = 2 * P1 - 0.5 * (P0 + P2)
    xz = ((1 - t) ** 2)[:, None] * P0 + (2 * (1 - t) * t)[:, None] * C + (t ** 2)[:, None] * P2
    fr = head_verts[head_verts[:, 1] < -0.02]
    verts, faces = [], []
    nside = 8
    for i, (x, z) in enumerate(xz):
        d = (fr[:, 0] - x) ** 2 + (fr[:, 2] - z) ** 2
        y = fr[np.argmin(d), 1] - 0.0018
        h = 0.0085 * (1 - t[i]) + 0.0040 * t[i]
        h *= np.sin(np.pi * np.clip(t[i] * 0.92 + 0.08, 0, 1)) ** 0.35
        th = 0.0034
        for k in range(nside):
            a = 2 * np.pi * k / nside
            verts.append([x, y + th * np.cos(a) * 0.6 - 0.0008, z + h * 0.5 * np.sin(a)])
    n = len(xz)
    for i in range(n - 1):
        for k in range(nside):
            a = i * nside + k
            b = i * nside + (k + 1) % nside
            faces.append((a, b, b + nside, a + nside))
    faces.append(tuple(range(nside))[::-1])
    faces.append(tuple(range((n - 1) * nside, n * nside)))
    return np.array(verts), faces

browm = blib.cloth_material('brow', (0.05, 0.03, 0.02), rough=0.6, scale=900, bump_str=0.4)
for key in ('L', 'R'):
    V, F = brow_mesh(H, key, g['verts'])
    b = blib.make_mesh('brow_' + key, V, F)
    blib.assign(b, browm)
    blib.subsurf(b, 1)

# neck stub
bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=0.15, location=(0, 0.025, -0.15))
nk = bpy.context.object
bpy.ops.object.shade_smooth()
blib.assign(nk, skin)

# lighting
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.35, 0.42, 0.55, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = 0.35
bpy.ops.object.light_add(type='AREA', location=(-0.5, -0.8, 0.5))
k = bpy.context.object; k.data.energy = 60; k.data.size = 0.6; k.data.color = (1, 0.92, 0.82)
k.rotation_euler = (Vector((0, 0, 0)) - k.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='AREA', location=(0.7, 0.6, 0.4))
r_ = bpy.context.object; r_.data.energy = 40; r_.data.size = 0.4; r_.data.color = (0.7, 0.8, 1.0)
r_.rotation_euler = (Vector((0, 0, 0)) - r_.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.camera_add()
cam = bpy.context.object; sc.camera = cam; cam.data.lens = 85

sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.use_denoising = True
sc.render.resolution_x = 520; sc.render.resolution_y = 520

def shoot(name, az, el=5, dist=0.75, keys=None, lidrot=None):
    for kb in head.data.shape_keys.key_blocks[1:]:
        kb.value = 0
    for kname, v in (keys or {}).items():
        head.data.shape_keys.key_blocks[kname].value = v
    for (key, up), lo in lids.items():
        e = g['eyes'][key]
        base = Vector((0, -1, 0)).rotation_difference(Vector(e['fwd'])).to_euler()
        rx = 0.0
        if lidrot:
            rx = math.radians(lidrot.get('up' if up else 'lo', 0))
        lo.rotation_euler = (base.to_matrix() @ Euler((rx, 0, 0)).to_matrix()).to_euler()
    a, e_ = math.radians(az), math.radians(el)
    tgt = Vector((0, 0, -0.01))
    cam.location = tgt + Vector((math.sin(a) * math.cos(e_), -math.cos(a) * math.cos(e_), math.sin(e_))) * dist
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, name + '.png')
    bpy.ops.render.render(write_still=True)

shoot('a_front', 0, dist=0.75)
shoot('b_smile', 25, dist=0.7, keys={'smile_L': 1, 'smile_R': 1}, lidrot={'lo': -8})

shoot('d_side', 90, dist=0.75)
shoot('e_34', 35, dist=0.75)
