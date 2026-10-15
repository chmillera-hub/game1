"""s05 - The worm: "But I am a worm and not a man, scorned by everyone, despised by the people."

Fade up from black (out of s04b's sunrise) into the dust at the foot of the centre cross, in the
eclipse darkness. Probe-lens macro, 3 cm above the ground: a small crimson worm (the tola'at shani,
the scarlet worm) crawls across a crust of cracked earth and pebbles, in sharp focus; behind it, soft,
the foot of the rough upright with its wedge stones, and sandaled feet striding past, kicking up dust.
On "not a man" a sandal stamps down just behind the worm - it flinches and freezes in the dust puff.
On "scorned by everyone, despised by the people" the camera cranes up and tilts up the upright to the
crucified figure, a dark silhouette against the dim red sky and the dull sun disk, while the passers-by
turn their backs and walk away. Focus racks from the worm to the figure during the rise.

The worm is modelled here: a segmented soft tube with an anterograde peristaltic wave (contraction
pulse travelling tail -> head, contracted segments shorten, fatten and hump up; each segment boundary
steps forward as the pulse passes), searching head, crimson subsurface skin. Per-frame geometry is
stored as shape keys (one per frame, linear 0-1-0 keys -> exact sub-frame motion blur).
"""
import math
import os
import random
import bpy
import numpy as np
from mathutils import Vector, Matrix, noise
from mathutils.bvhtree import BVHTree
from lib import core as C
from lib import env as E
from lib import characters as P
from lib import fx as FX

SUN_AZ = 206.0          # behind the cross (seen from the final camera): the figure is a silhouette
SUN_EL = 47.0           # sixth hour: high, dull red disk sits behind the figure at the end of the tilt
LENS = 32.0
FAST = os.environ.get("S05_FAST", "") == "1"     # layout iterations: no people


# ============================================================================================ helpers
def _smooth(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0))) if e1 != e0 else float(x >= e1)
    return t * t * (3 - 2 * t)


def _hazify_objs(objs):
    seen = set()
    for o in objs:
        if o.type not in ("MESH", "CURVES", "CURVE"):
            continue
        for m in getattr(o.data, "materials", []) or []:
            if m is not None and m.name not in seen:
                seen.add(m.name)
                E.hazify(m)


def _mixrgb(nt, blend, fac, a, b):
    """Legacy MixRGB (unambiguous sockets). fac/a/b: socket or value."""
    m = nt.nodes.new("ShaderNodeMixRGB")
    m.blend_type = blend
    for i, v in ((0, fac), (1, a), (2, b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, m.inputs[i])
        elif isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            m.inputs[i].default_value = tuple(v) if len(v) == 4 else (*v, 1.0)
    return m.outputs[0]


# ============================================================================================ ground
def macro_ground(focus, half=1.4, fine=0.0022, coarse=0.03, lift=0.004, seed=3, mat_src=None):
    """Cracked-earth crust patch following the terrain (world-space verts, object at the origin so the
    env ground material maps identically). Graded grid: `fine` spacing near `focus`, growing to `coarse`.
    Sits `lift` above the terrain (crack grooves cut down to ~terrain level), edges sink below it."""
    fx_, fy_ = focus

    def axis(c):
        xs = [0.0]
        d, step = 0.0, fine
        while d < half:
            d += step
            xs.append(d)
            step = min(coarse, step * (1.0 if d < 0.05 else 1.06))
        xs = np.array(xs)
        return np.concatenate([c - xs[:0:-1], c + xs])

    ax, ay = axis(fx_), axis(fy_)
    X, Y = np.meshgrid(ax, ay)
    # exact terrain height: raycast a 5 cm grid, bilinear interpolation (terrain cells are 0.45 m, linear)
    gx = np.arange(ax[0] - 0.05, ax[-1] + 0.1, 0.05)
    gy = np.arange(ay[0] - 0.05, ay[-1] + 0.1, 0.05)
    GZ = np.array([[E.ground_z(float(x), float(y)) for x in gx] for y in gy])
    fx = (X - gx[0]) / 0.05
    fy = (Y - gy[0]) / 0.05
    ix = np.clip(fx.astype(int), 0, len(gx) - 2)
    iy = np.clip(fy.astype(int), 0, len(gy) - 2)
    tx, ty = fx - ix, fy - iy
    Z = (GZ[iy, ix] * (1 - tx) * (1 - ty) + GZ[iy, ix + 1] * tx * (1 - ty) +
         GZ[iy + 1, ix] * (1 - tx) * ty + GZ[iy + 1, ix + 1] * tx * ty)
    # micro relief (dust ripples, trodden dips) + edge fade below the terrain
    rel = (E.fbm(X * 6.0, Y * 6.0, 4, seed=seed) * 0.004 + E.fbm(X * 22.0, Y * 22.0, 3, seed=seed + 7) * 0.0012 +
           E.fbm(X * 70.0, Y * 70.0, 2, seed=seed + 9) * 0.0005)
    r = np.maximum(np.abs(X - fx_), np.abs(Y - fy_)) / half
    fade = np.clip((1.0 - r) / 0.22, 0.0, 1.0)
    fade = fade * fade * (3 - 2 * fade)
    Z = Z + (lift + rel) * fade - 0.02 * (1 - fade)
    ny, nx = X.shape
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    j, i = np.mgrid[0:ny - 1, 0:nx - 1]
    a = (j * nx + i).ravel()
    faces = np.stack([a, a + 1, a + nx + 1, a + nx], 1)
    ob = E.mesh_from_numpy("MacroGround", verts, faces)
    FX._mod(ob, FX._cracks_tree(), "Cracks", Cell=0.062, Width=0.06, Depth=0.004, Curl=0.0006, Seed=float(seed * 7.3))
    ob.data.materials.append(macro_ground_material(mat_src, focus))
    # freeze the GN relief into a plain mesh (keeps the fx_crack attribute; nothing to evaluate per frame)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old_me = ob.data
    ob.modifiers.clear()
    ob.data = me
    bpy.data.meshes.remove(old_me)
    for poly in me.polygons:
        poly.use_smooth = True
    return ob


def macro_ground_material(src, focus=(0.0, 0.0)):
    """The env Golgotha ground material (far: identical colours at the patch edge) blended near the focus
    into a macro layer: 2k dusty-soil texture at 0.5 m tiles, fine shader-only hairline cracks, dark
    crack interiors (fx_crack from the GN relief), grain specks, grain + pit bump."""
    from lib import polyhaven as ph
    m = src.copy() if src is not None else bpy.data.materials.new("MacroGroundMat")
    m.name = "MacroGroundMat"
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    L = nt.links

    def node(t, **kw):
        n = nt.nodes.new(t)
        for k, v in kw.items():
            n.inputs[k].default_value = v
        return n

    def math_(op, a, b_=None, clamp=False):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                L.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]

    tc = nt.nodes.new("ShaderNodeTexCoord")
    co = tc.outputs["Object"]
    # ---- macro mask: 1 near the focus, 0 beyond ~0.9 m (patch edges keep the env look)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(co, sep.inputs[0])
    dx = math_("SUBTRACT", sep.outputs[0], focus[0])
    dy = math_("SUBTRACT", sep.outputs[1], focus[1])
    dist = math_("SQRT", math_("ADD", math_("MULTIPLY", dx, dx), math_("MULTIPLY", dy, dy)))
    mr = nt.nodes.new("ShaderNodeMapRange")
    L.new(dist, mr.inputs[0])
    mr.inputs[1].default_value, mr.inputs[2].default_value = 0.9, 0.35
    mask = mr.outputs[0]
    # ---- macro texture (dusty soil with grit), tinted like the env base layer
    maps = ph.texture_maps("dry_ground_rocks", "2k")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 2.0, 2.0)
    mp.inputs["Rotation"].default_value = (0, 0, 0.6)
    L.new(co, mp.inputs["Vector"])

    def img(path, noncolor=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            t.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    dif = img(maps["diff"])
    hs = node("ShaderNodeHueSaturation", Saturation=0.55, Value=1.3)
    L.new(dif.outputs["Color"], hs.inputs["Color"])
    mcol = _mixrgb(nt, "MULTIPLY", 1.0, hs.outputs["Color"], (1.0, 0.9, 0.76))
    src_col = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else (0.42, 0.33, 0.25)
    col = _mixrgb(nt, "MIX", mask, src_col, mcol)
    # ---- grain specks
    n1 = node("ShaderNodeTexNoise", Scale=520.0, Detail=3.0, Roughness=0.6)
    L.new(co, n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (0.8, 0.76, 0.7, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (1.12, 1.08, 1.0, 1)
    L.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    col = _mixrgb(nt, "MULTIPLY", mask, col, ramp.outputs["Color"])
    # ---- fine hairline cracks (shader only): distorted voronoi edges, ~2 cm cells
    nd = node("ShaderNodeTexNoise", Scale=18.0, Detail=2.0)
    L.new(co, nd.inputs["Vector"])
    dv = nt.nodes.new("ShaderNodeVectorMath")
    dv.operation = "MULTIPLY_ADD"
    L.new(nd.outputs["Color"], dv.inputs[0])
    dv.inputs[1].default_value = (0.012, 0.012, 0.0)
    L.new(co, dv.inputs[2])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 45.0
    vor.inputs["Randomness"].default_value = 0.95
    L.new(dv.outputs[0], vor.inputs["Vector"])
    fine = nt.nodes.new("ShaderNodeMapRange")
    L.new(vor.outputs["Distance"], fine.inputs[0])
    fine.inputs[1].default_value, fine.inputs[2].default_value = 0.035, 0.0
    # break the hairline network up (not every edge is cracked)
    nb_ = node("ShaderNodeTexNoise", Scale=9.0, Detail=1.0)
    L.new(co, nb_.inputs["Vector"])
    brk = nt.nodes.new("ShaderNodeMapRange")
    L.new(nb_.outputs["Fac"], brk.inputs[0])
    brk.inputs[1].default_value, brk.inputs[2].default_value = 0.42, 0.55
    fine_c = math_("MULTIPLY", math_("MULTIPLY", fine.outputs[0], brk.outputs[0]), mask)
    crack = nt.nodes.new("ShaderNodeAttribute")
    crack.attribute_name = "fx_crack"
    cr = math_("MAXIMUM", math_("MULTIPLY", crack.outputs["Fac"], 0.9), math_("MULTIPLY", fine_c, 0.75))
    col = _mixrgb(nt, "MULTIPLY", cr, col, (0.3, 0.22, 0.17))
    L.new(col, b.inputs["Base Color"])
    # ---- bump: grains + pits + hairline cracks, after the existing (env) normal
    vp = nt.nodes.new("ShaderNodeTexVoronoi")
    vp.inputs["Scale"].default_value = 300.0
    L.new(co, vp.inputs["Vector"])
    h = math_("ADD", math_("MULTIPLY", vp.outputs["Distance"], 0.6), n1.outputs["Fac"])
    h = math_("SUBTRACT", h, math_("MULTIPLY", fine_c, 1.4))
    bump = node("ShaderNodeBump", Strength=0.6, Distance=0.0007)
    L.new(math_("MULTIPLY", h, mask), bump.inputs["Height"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 0.9
    L.new(img(maps["nor"], True).outputs["Color"], nm.inputs["Color"])
    if b.inputs["Normal"].links:
        envn = b.inputs["Normal"].links[0].from_socket
        mixn = nt.nodes.new("ShaderNodeMix")
        mixn.data_type = "VECTOR"
        sock = lambda col, ident: next(x for x in col if x.identifier == ident)
        L.new(mask, sock(mixn.inputs, "Factor_Float"))
        L.new(envn, sock(mixn.inputs, "A_Vector"))
        L.new(nm.outputs["Normal"], sock(mixn.inputs, "B_Vector"))
        L.new(sock(mixn.outputs, "Result_Vector"), bump.inputs["Normal"])
    else:
        L.new(nm.outputs["Normal"], bump.inputs["Normal"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    if "rough" in maps:
        r = img(maps["rough"], True)
        rr = math_("MULTIPLY_ADD", r.outputs["Color"], 0.3)
        nt.nodes[rr.node.name].inputs[2].default_value = 0.68
        L.new(rr, b.inputs["Roughness"])
    return m


# ============================================================================================ worm
N_SEG = 13
L0 = 0.0034            # rest segment length
R0 = 0.0025           # max body radius
RINGS = 6              # rings per segment
AROUND = 20
HEAD_L, TAIL_L = 0.0026, 0.0018


class Worm:
    """Kinematic model. Body coordinate b in [0, N_SEG] (tail -> head boundary indices)."""

    def __init__(self, fps, period=0.62, transit=1.35, delta=0.62 * L0, width=2.6, freeze=None, seed=1):
        self.fps = fps
        self.T = period          # a new wave every T seconds
        self.Tw = transit        # time for a pulse to travel tail -> head
        self.D = delta           # forward step of every boundary per wave
        self.tau = width * transit / N_SEG     # pulse duration at a boundary
        self.freeze = freeze     # (t0, t1): flinch + pause
        self.seed = seed

    def local_time(self, t):
        if not self.freeze:
            return t
        a, b = self.freeze
        # rate: 1 -> 0.05 during the freeze, ease back over 0.5 s
        n = 400
        ts = np.linspace(0, t, n)
        rate = 1.0 - 0.95 * np.array([_smooth(a - 0.08, a, x) * (1 - _smooth(b, b + 0.5, x)) for x in ts])
        return float(np.sum((rate[1:] + rate[:-1]) * 0.5 * np.diff(ts))) if t > 0 else 0.0

    def boundaries(self, t):
        """arc positions (relative to the tail at t=0) of the N_SEG+1 boundaries + contraction per segment."""
        tl = self.local_time(t)
        kmax = int(tl / self.T) + 3
        s = np.zeros(N_SEG + 1)
        for j in range(N_SEG + 1):
            acc = 0.0
            for k in range(-2, kmax + 1):
                x = (tl - k * self.T - (j / N_SEG) * self.Tw) / self.tau
                acc += 0.0 if x <= 0 else (1.0 if x >= 1 else x * x * (3 - 2 * x))
            s[j] = j * L0 + self.D * acc
        lens = np.diff(s)
        c = np.clip(1.0 - lens / L0, 0.0, 0.8)
        # flinch: whole body bunches up (head pulled back)
        if self.freeze:
            a, b = self.freeze
            k = 0.16 * _smooth(a - 0.05, a + 0.12, t) * (1 - _smooth(b - 0.1, b + 0.6, t))
            lens = lens * (1 - k)
            s = s[0] + np.concatenate([[0], np.cumsum(lens)])
            c = np.clip(c + k * 0.8, 0, 0.8)
        return s, c


def _radius_profile(b):
    """b: 0 tail .. 1 head (body)."""
    tail = _smooth(0.0, 0.3, b)
    head = 1.0 - 0.3 * _smooth(0.8, 1.0, b)
    return R0 * (0.36 + 0.64 * tail ** 0.75) * head


def build_worm(ctx, origin, heading, path_len, gbvh, f_stomp, coll=None):
    """origin: world xy of the tail at frame 1; heading: unit xy crawl direction. gbvh: ground BVH."""
    fps = ctx.fps
    NR = ctx.render_frames
    t_st = (f_stomp - 1) / fps
    W = Worm(fps, freeze=(t_st + 0.05, t_st + 0.85))
    hd = Vector((heading[0], heading[1], 0)).normalized()
    side = Vector((-hd.y, hd.x, 0))
    org = Vector((origin[0], origin[1], 0))

    def path_xy(s):
        # gentle S-curve in the crawl plane
        lat = 0.0025 * math.sin(s / 0.05 * math.pi) + 0.0012 * math.sin(s / 0.025 + 0.6)
        return org + hd * s + side * lat

    def path_tan(s):
        e = 0.0005
        d = path_xy(s + e) - path_xy(s - e)
        return d.normalized()

    # stations (body coordinate, radius, crease, part)
    st_b, st_r, st_cr, st_part = [], [], [], []
    # tail cap (pole + small rings)
    for k, u in enumerate([0.0, 0.25, 0.5, 0.72, 0.88, 1.0]):
        st_b.append(-TAIL_L * (1 - u) / L0)
        st_r.append(_radius_profile(0.0) * math.sin(u * math.pi / 2) ** 0.8 if u > 0 else 0.0)
        st_cr.append(0.0)
        st_part.append(0.0)
    for i in range(N_SEG):
        for k in range(RINGS):
            t = k / RINGS
            if i == 0 and k == 0:
                continue
            bb = i + t
            m = 0.92 + 0.08 * math.sin(math.pi * t) ** 0.5
            st_b.append(bb)
            st_r.append(_radius_profile(bb / N_SEG) * m)
            st_cr.append(1.0 - (m - 0.92) / 0.08)
            st_part.append(0.0)
    # head capsule
    rh = _radius_profile(1.0) * 0.92
    for k, u in enumerate([0.0, 0.15, 0.35, 0.55, 0.72, 0.86, 0.95, 1.0]):
        st_b.append(N_SEG + u * HEAD_L / L0)
        prof = 0.78 + 0.22 * math.sin(min(1.0, u / 0.5) * math.pi / 2)
        cap = math.cos(max(0.0, (u - 0.55) / 0.45) * math.pi / 2) ** 0.7
        st_r.append(rh * prof * cap if u < 1.0 else 0.0)
        st_cr.append(1.0 if u < 0.1 else 0.0)
        st_part.append(min(1.0, u / 0.25))
    st_b = np.array(st_b)
    st_r = np.array(st_r)
    NS = len(st_b)
    th = np.linspace(0, 2 * math.pi, AROUND, endpoint=False)

    def frame_geometry(f):
        t = (f - 1) / fps
        s_b, cseg = W.boundaries(t)
        # arc position, contraction per station
        arc = np.zeros(NS)
        cst = np.zeros(NS)
        for n, bb in enumerate(st_b):
            if bb <= 0:
                arc[n] = s_b[0] + bb * L0
                cst[n] = cseg[0]
            elif bb >= N_SEG:
                arc[n] = s_b[-1] + (bb - N_SEG) * L0
                cst[n] = cseg[-1]
            else:
                i = min(N_SEG - 1, int(bb))
                u = bb - i
                arc[n] = s_b[i] + u * (s_b[i + 1] - s_b[i])
                # contraction smoothed across segment borders
                c0 = cseg[i]
                cn = cseg[min(N_SEG - 1, i + 1)] if u > 0.5 else cseg[max(0, i - 1)]
                w = abs(u - 0.5)
                cst[n] = c0 * (1 - w) + cn * w
        rad = st_r * (1.0 + 0.7 * cst)
        # searching head: lateral sway + lift (quiet during the freeze)
        frz = 0.0
        if W.freeze:
            a, b = W.freeze
            frz = _smooth(a - 0.1, a, t) * (1 - _smooth(b, b + 0.6, t))
        sway = (0.0011 * math.sin(2 * math.pi * t / 1.9 + 0.4) + 0.0004 * math.sin(2 * math.pi * t / 0.83)) * (1 - frz)
        lift_h = (0.0011 * max(0.0, math.sin(2 * math.pi * t / 2.6 - 0.8))) * (1 - frz)
        hw = np.array([_smooth(N_SEG - 3.0, N_SEG + 0.8, bb) for bb in st_b])
        pts, tans = [], []
        for n in range(NS):
            p = path_xy(arc[n])
            tg = path_tan(arc[n])
            sd = Vector((-tg.y, tg.x, 0))
            p = p + sd * (sway * hw[n] ** 1.5)
            pts.append(p)
        pts = np.array([tuple(p) for p in pts])
        # ground height under each station (max across the body width, so it bridges cracks)
        zs = np.zeros(NS)
        for n in range(NS):
            p = Vector(pts[n])
            nx_ = n + 1 if n + 1 < NS else n - 1
            tg = Vector(pts[nx_]) - p
            if n + 1 >= NS:
                tg = -tg
            tg.z = 0
            if tg.length < 1e-9:
                tg = hd.copy()
            tg.normalize()
            sd = Vector((-tg.y, tg.x, 0))
            best = -1e9
            for off in (-0.7, 0.0, 0.7):
                q = p + sd * (off * max(rad[n], 0.0012))
                hit = gbvh.ray_cast(Vector((q.x, q.y, q.z + 50.0)), Vector((0, 0, -1)))
                if hit[0] is not None:
                    best = max(best, hit[0].z)
            zs[n] = best if best > -1e8 else 0.0
        # smooth heights along the body (no jitter on grains), then raise by the flattened radius
        # bridge cracks: running max over ~+-4.5 mm of body, then a soft smooth
        w_ = 8
        zp = np.pad(zs, w_, mode="edge")
        zs = np.array([zp[n:n + 2 * w_ + 1].max() for n in range(NS)])
        k = np.exp(-np.linspace(-2, 2, 9) ** 2)
        k /= k.sum()
        zs = np.convolve(np.pad(zs, 4, mode="edge"), k, mode="valid")
        hump = 1.25 * R0 * cst ** 1.2
        cz_ = zs + np.maximum(rad, 0.0006) * 0.74 + 0.00015 + hump + lift_h * hw ** 2
        pts[:, 2] = cz_
        # frames along the body
        V = []
        for n in range(NS):
            a_ = pts[max(0, n - 1)]
            b_ = pts[min(NS - 1, n + 1)]
            tg = Vector(b_ - a_)
            if tg.length < 1e-9:
                tg = hd.copy()
            tg.normalize()
            sd = Vector((0, 0, 1)).cross(tg).normalized()
            up = tg.cross(sd).normalized()
            r = rad[n]
            for a in th:
                ca, sa = math.cos(a), math.sin(a)
                zf = 1.0 if sa >= 0 else 0.74          # flattened belly
                V.append(tuple(Vector(pts[n]) + sd * (r * ca * (1.0 + 0.04 * sa)) + up * (r * sa * zf)))
        return np.array(V, dtype=np.float32)

    # topology
    faces = []
    for n in range(NS - 1):
        for k in range(AROUND):
            a = n * AROUND + k
            b = n * AROUND + (k + 1) % AROUND
            faces.append((a, b, b + AROUND, a + AROUND))
    V1 = frame_geometry(1)
    me = bpy.data.meshes.new("Worm")
    me.from_pydata([tuple(v) for v in V1], [], faces)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    # attributes: dorsal (0 belly .. 1 back), crease, head, uv (body coord, angle)
    dors = np.repeat(np.ones(NS), AROUND) * 0
    dors = np.tile((np.sin(th) + 1) * 0.5, NS).astype(np.float32)
    cre = np.repeat(np.array(st_cr, np.float32), AROUND)
    hea = np.repeat(np.array(st_part, np.float32), AROUND)
    srnd = random.Random(7)
    segv = {i: srnd.random() for i in range(-1, N_SEG + 2)}
    seg = np.repeat(np.array([segv[int(math.floor(bb))] for bb in st_b], np.float32), AROUND)
    for nm, arr in (("dorsal", dors), ("crease", cre), ("headpart", hea), ("segrand", seg)):
        at = me.attributes.new(nm, "FLOAT", "POINT")
        at.data.foreach_set("value", arr)
    uvl = me.uv_layers.new(name="UVMap")
    bcoord = np.repeat(st_b / N_SEG, AROUND)
    ang = np.tile(th / (2 * math.pi), NS)
    uv = np.zeros((len(me.loops), 2), np.float32)
    vi = np.zeros(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", vi)
    uv[:, 0] = bcoord[vi]
    uv[:, 1] = ang[vi]
    # fix the seam (angle wraps): loops on faces spanning the wrap get +1
    for poly in me.polygons:
        li = list(poly.loop_indices)
        us = [uv[l, 1] for l in li]
        if max(us) - min(us) > 0.5:
            for l in li:
                if uv[l, 1] < 0.5:
                    uv[l, 1] += 1.0
    uvl.data.foreach_set("uv", uv.ravel())
    ob = bpy.data.objects.new("Worm", me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.data.materials.append(worm_material())
    # per-frame shape keys
    ob.shape_key_add(name="Basis", from_mix=False)
    last = NR
    keys = ob.data.shape_keys
    for f in range(1, last + 1):
        Vf = V1 if f == 1 else frame_geometry(f)
        kb = ob.shape_key_add(name="f%03d" % f, from_mix=False)
        kb.data.foreach_set("co", Vf.ravel())
        for ff, v in ((f - 1, 0.0), (f, 1.0), (f + 1, 0.0)):
            kb.value = v
            kb.keyframe_insert("value", frame=ff)
    for fc in C._fcurves(keys.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return ob, W


def worm_material():
    m = bpy.data.materials.new("WormSkin")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    L = nt.links

    def attr(n):
        a = nt.nodes.new("ShaderNodeAttribute")
        a.attribute_name = n
        return a.outputs["Fac"]

    uvn = nt.nodes.new("ShaderNodeUVMap")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(uvn.outputs["UV"], sep.inputs[0])
    # fine transverse wrinkles + mottling on the skin (stable in UV space)
    wav = nt.nodes.new("ShaderNodeTexWave")
    wav.wave_type = "BANDS"
    wav.bands_direction = "X"
    wav.inputs["Scale"].default_value = 1.0
    wav.inputs["Distortion"].default_value = 2.0
    wav.inputs["Detail"].default_value = 2.0
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (95.0, 4.0, 1.0)
    L.new(uvn.outputs["UV"], mp.inputs["Vector"])
    L.new(mp.outputs["Vector"], wav.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 30.0
    nz.inputs["Detail"].default_value = 3.0
    L.new(uvn.outputs["UV"], nz.inputs["Vector"])
    # colour: crimson body, darker dorsal line + creases, lighter flanks, dark red-brown head
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.46, 0.045, 0.04, 1)       # belly / flank (light crimson)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.2, 0.012, 0.016, 1)       # back (deep scarlet)
    L.new(attr("dorsal"), ramp.inputs["Fac"])
    c = ramp.outputs["Color"]
    # dorsal vessel line (back centre: dorsal ~1)
    dl = nt.nodes.new("ShaderNodeMapRange")
    L.new(attr("dorsal"), dl.inputs[0])
    dl.inputs[1].default_value, dl.inputs[2].default_value = 0.93, 1.0
    c = _mixrgb(nt, "MULTIPLY", dl.outputs[0], c, (0.45, 0.25, 0.25))
    crm = nt.nodes.new("ShaderNodeMath")
    crm.operation = "MULTIPLY"
    L.new(attr("crease"), crm.inputs[0])
    crm.inputs[1].default_value = 0.4
    c = _mixrgb(nt, "MIX", crm.outputs[0], c, (0.62, 0.2, 0.17))          # paler intersegmental membrane
    sv = nt.nodes.new("ShaderNodeMapRange")
    L.new(attr("segrand"), sv.inputs[0])
    sv.inputs[3].default_value, sv.inputs[4].default_value = 0.82, 1.12
    c = _mixrgb(nt, "MULTIPLY", 1.0, c, sv.outputs[0])
    c = _mixrgb(nt, "OVERLAY", 0.35, c, nz.outputs["Color"])
    c = _mixrgb(nt, "MIX", attr("headpart"), c, (0.11, 0.02, 0.015))
    L.new(c, b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 1.0
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.16, 0.08)
    b.inputs["Subsurface Scale"].default_value = 0.003
    b.inputs["Roughness"].default_value = 0.4
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.12
    # bump: wrinkles + crease grooves
    bh = nt.nodes.new("ShaderNodeMath")
    bh.operation = "MULTIPLY_ADD"
    L.new(wav.outputs["Fac"], bh.inputs[0])
    bh.inputs[1].default_value = 0.35
    L.new(attr("crease"), bh.inputs[2])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0002
    L.new(bh.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ============================================================================================ people
def _key_visible(objs, keys):
    """keys: [(frame, visible)] -> constant-interpolated hide_render keys on every object."""
    for o in objs:
        for f, v in keys:
            o.hide_render = not v
            o.keyframe_insert("hide_render", frame=max(1, f))
        if o.animation_data and o.animation_data.action:
            for fc in C._fcurves(o.animation_data.action):
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"


def _walker(name, preset, seed, colors, pts, f0, f1, gzf, outfit=None, extra=None):
    sp = dict(lod="mid", hair_strands=False, pose=None, expression=None, seed=seed,
              outfit=outfit or (["tunic", "mantle", "sandals"] if preset == "CROWD_MAN" else ["tunic", "veil", "sandals"]),
              outfit_colors=colors)
    sp.update(extra or {})
    p = P.make_person(name, preset, **sp)
    P.walk(p, pts, f0, f1, height_fn=gzf)
    return p


def _strikes(w, f_lo, f_hi, vb=1.25 / 24.0, debug=False):
    """Stance phases of a walking person: [(first frame, side, ankle world pos)] for every run of >= 4
    frames in which the ankle moves < 30 % of the body speed (the foot is planted)."""
    sc = bpy.context.scene
    pos = {"L": [], "R": []}
    for f in range(f_lo, f_hi + 1):
        sc.frame_set(f)
        for sd in "LR":
            pos[sd].append(Vector(w.foot_pos(sd)))
    out = []
    for sd in "LR":
        ps = pos[sd]
        sp = [99.0] + [(Vector((ps[i].x, ps[i].y)) - Vector((ps[i - 1].x, ps[i - 1].y))).length for i in range(1, len(ps))]
        if debug:
            print("S05 speeds", w.name, sd, " ".join("%.0f" % (1000 * v) for v in sp[1:]))
        for i in range(6, len(ps)):
            if sp[i] < 0.8 * vb <= sp[i - 1] and max(sp[i - 6:i]) > 1.8 * vb:
                out.append((f_lo + i, sd, ps[i]))
    sc.frame_set(1)
    print("S05 strikes", w.name, [(q[0], q[1]) for q in out])
    return out


# ============================================================================================ build
def build(ctx):
    N, NR = ctx.nframes, ctx.render_frames
    fps = ctx.fps
    rnd = random.Random(ctx.seed)
    a1, b1 = (int(x) for x in ctx.phrase_frames(0))     # "But I am a worm and not a man,"
    a2, b2 = (int(x) for x in ctx.phrase_frames(1))     # "scorned by everyone, despised by the people."
    sc = bpy.context.scene

    # ------------------------------------------------------------------ geometry anchors
    WORM = Vector((0.62, -0.50))             # worm tail at frame 1 (world xy)
    CAM_DIR = Vector((-0.53, 0.85)).normalized()        # first look: across the worm to the cross foot
    disk = dict(E.SKY_PRESETS["eclipse"]["sun_disk"], el=SUN_EL)
    views = [dict(loc=(0.75, -0.66, 11.05), target=(0.0, 0.6, 11.3), lens=24, margin=30),
             dict(loc=(0.7, -1.15, 12.3), target=(0.0, 0.45, 13.8), lens=24, margin=30)]
    A = E.golgotha(ctx, mood="eclipse", sun_az=SUN_AZ, view=views, near_detail=0.3, grass=0.35, bushes=0.4,
                   sky_over=dict(sun_el=SUN_EL, sun_disk=disk))
    gzf = A["ground_z"]
    c = A["crosses"]["center"]
    cz = c["base"][2]
    print("S05 cross base", c["base"], "feet", c["feet"], "head", c["head"])

    # ------------------------------------------------------------------ macro ground + pebbles
    gmat = A["terrain"].data.materials[0] if A["terrain"].data.materials else None
    focus = (WORM.x - 0.02, WORM.y + 0.02)
    mg = macro_ground(focus, half=1.5, mat_src=gmat)
    E.hazify(mg.data.materials[0])
    bpy.context.view_layer.update()
    # ground BVH (evaluated, with cracks) for the worm and pebbles
    dg = bpy.context.evaluated_depsgraph_get()
    ev = mg.evaluated_get(dg)
    gme = ev.to_mesh()
    gv = np.empty(len(gme.vertices) * 3, np.float32)
    gme.vertices.foreach_get("co", gv)
    gme.calc_loop_triangles()
    tri = np.empty(len(gme.loop_triangles) * 3, np.int32)
    gme.loop_triangles.foreach_get("vertices", tri)
    gbvh = BVHTree.FromPolygons([tuple(v) for v in gv.reshape(-1, 3)], [tuple(t) for t in tri.reshape(-1, 3)])
    ev.to_mesh_clear()
    E.add_ground(mg)
    # crawl direction: across the view, drifting slightly away
    right = Vector((CAM_DIR.y, -CAM_DIR.x))
    heading = (-right + CAM_DIR * 0.25).normalized()
    worm_mid = WORM + heading * 0.025
    # pebbles: a field around the worm (kept off its path), grit close in
    stones = E.rock_protos("stones", tint=(0.92, 0.84, 0.72), value=0.8)
    path_ex = [(float((WORM + heading * d).x), float((WORM + heading * d).y), 0.012) for d in np.linspace(-0.02, 0.1, 13)]
    E.scatter(stones, terrain=mg, count=260, region=("circle", worm_mid.x, worm_mid.y, 0.35), seed=11,
              scale=(0.04, 0.16), align=0.8, sink=-0.35, tilt=20, exclude=path_ex, name="S05Pebbles", min_dist=0.012)
    E.scatter(stones, terrain=mg, count=900, region=("circle", worm_mid.x, worm_mid.y, 0.12), seed=12,
              scale=(0.012, 0.035), align=0.9, sink=-0.3, tilt=30, exclude=path_ex, name="S05Grit", shadows=False)
    E.scatter(stones, terrain=mg, count=180, region=("circle", worm_mid.x + CAM_DIR.x * 0.6, worm_mid.y + CAM_DIR.y * 0.6, 0.9),
              seed=13, scale=(0.1, 0.35), align=0.7, sink=-0.3, tilt=15, exclude=[(0.0, 0.6, 0.15)], name="S05Stones")

    # ------------------------------------------------------------------ timing
    f_stomp = int(round(a1 + 0.62 * (b1 - a1)))          # "...and not a man": a sandal stamps behind the worm
    f_rise0 = int(round(a1 + 0.92 * (b1 - a1)))           # rise starts as the first line ends
    f_rise1 = NR - 4

    # ------------------------------------------------------------------ the worm
    worm, W = build_worm(ctx, WORM, heading, 0.12, gbvh, f_stomp)
    E.hazify(worm.data.materials[0])

    # ------------------------------------------------------------------ the crucified (silhouette at the end)
    if not FAST:
        j = P.make_person("jesus", "JESUS_CROSS", pose=None, lod="mid", hair_strands=False)
        P.place_on_cross(j, c["root"], head="down", strain=0.55)
        P.expression(j, "exhausted")
        _hazify_objs(j.objects())

    # ------------------------------------------------------------------ passers-by
    walkers = []
    if not FAST:
        ahead = CAM_DIR
        cam0 = worm_mid - CAM_DIR * 0.115
        # W1: strides from behind-right across the view, ~0.22 m behind the worm at f_stomp (stance foot planted)
        p0 = cam0 - ahead * 0.2 + right * 1.3
        p1 = cam0 + ahead * 0.95 - right * 1.5
        L1 = (p1 - p0).length
        fr_cross = 1.3 / 2.8
        dur = int(round(L1 / 1.25 * fps))
        w1 = _walker("w1", "CROWD_MAN", 41, {"tunic": "oatmeal", "mantle": "umber", "sandals": "dark_leather"},
                     [tuple(p0), tuple(p1)], f_stomp - int(fr_cross * dur), f_stomp - int(fr_cross * dur) + dur, gzf)
        walkers.append(w1)
        # W2: a woman further back, left -> right
        q0 = cam0 + ahead * 1.6 - right * 2.2
        q1 = cam0 + ahead * 1.3 + right * 2.4
        w2 = _walker("w2", "CROWD_WOMAN", 7, {"tunic": "umber", "veil": "sand", "sandals": "leather"},
                     [tuple(q0), tuple(q1)], 1, 92, gzf)
        walkers.append(w2)
        # W3: walks away past the cross foot during the rise (turns his back)
        r0 = cam0 + ahead * 0.5 + right * 0.9
        r1 = Vector((-1.6, 2.6))
        w3 = _walker("w3", "CROWD_MAN", 18, {"tunic": "linen", "mantle": "charcoal", "sandals": "leather"},
                     [tuple(r0), tuple(r1)], f_rise0 - 10, NR, gzf)
        walkers.append(w3)
        for w in walkers:
            _hazify_objs(w.objects())
        # the stamp: re-time + shift W1 so a heel strike lands just behind the worm on f_stomp
        D = worm_mid + CAM_DIR * 0.17 - right * 0.035
        f0_1, f1_1 = f_stomp - int(fr_cross * dur), f_stomp - int(fr_cross * dur) + dur
        st = _strikes(w1, max(1, f_stomp - 30), min(NR, f_stomp + 30))
        if st:
            fs, sd_, ps = min(st, key=lambda q: abs(q[0] - f_stomp) + 30 * (Vector((q[2].x, q[2].y)) - D).length)
            dt = f_stomp - fs
            dl = D - Vector((ps.x, ps.y))
            w1.rig.animation_data_clear()
            P.walk(w1, [tuple(p0 + dl), tuple(p1 + dl)], f0_1 + dt, f1_1 + dt, height_fn=gzf)
            print("S05 stamp: strike at", fs, "shift", tuple(dl), "dt", dt)
        gD = gzf(D.x, D.y)
        FX.dust_burst((D.x, D.y, gD + 0.01), f_stomp, size=0.14, color=(0.78, 0.64, 0.5), count=60, grains=0,
                      direction=(0, 0, 1), wind=(-right.x * 0.25 - CAM_DIR.x * 0.1, -right.y * 0.25 - CAM_DIR.y * 0.1, 0.02),
                      opacity=1.0, life=3.4, seed=3, name="DustStomp")
        k = 0
        for w, fa, fb in ((w1, 1, min(NR, f_stomp + 40)), (w2, 1, 95)):
            for fr_, sd_, ft in _strikes(w, fa, fb):
                if abs(fr_ - f_stomp) < 3 or fr_ > b1 + 10 or (Vector((ft.x, ft.y)) - cam0).length > 1.8:
                    continue
                FX.dust_burst((ft.x, ft.y, gzf(ft.x, ft.y) + 0.005), fr_, size=0.12, color=(0.7, 0.58, 0.45), count=16,
                              grains=0, wind=(-right.x * 0.3, -right.y * 0.3, 0.02), opacity=0.7, life=2.5, seed=10 + k,
                              name="DustStep%d" % k)
                k += 1
        sc.frame_set(1)

    # ------------------------------------------------------------------ worm light: a soft local bounce
    gw = gbvh.ray_cast(Vector((worm_mid.x, worm_mid.y, cz + 5)), Vector((0, 0, -1)))[0].z
    wl = C.light("AREA", loc=tuple(Vector((worm_mid.x, worm_mid.y, gw)) - Vector((CAM_DIR.x, CAM_DIR.y, 0)) * 0.12 +
                                   Vector((0, 0, 0.14))), energy=0.25, color=(1.0, 0.62, 0.45), size=0.12,
                 target=(worm_mid.x, worm_mid.y, gw), name="WormBounce")
    try:
        wl.data.use_custom_distance = True
        wl.data.cutoff_distance = 0.6
    except AttributeError:
        pass
    wl.data.use_shadow = False

    # ------------------------------------------------------------------ camera
    gw = gbvh.ray_cast(Vector((worm_mid.x, worm_mid.y, cz + 5)), Vector((0, 0, -1)))[0].z
    tgt0 = Vector((worm_mid.x, worm_mid.y, gw + 0.0025))
    cam0 = tgt0 - Vector((CAM_DIR.x, CAM_DIR.y, 0)) * 0.115 + Vector((0, 0, 0.027))
    cam1 = Vector((0.7, -1.15, cz + 1.3))
    tgt1 = Vector((0.0, 0.42, cz + 2.75))
    fig = Vector((0.0, 0.45, cz + 2.8))
    cam = C.camera(loc=tuple(cam0), target=tuple(tgt0), lens=LENS, fstop=9.0, focus=(tgt0 - cam0).length)
    base_pt = Vector((0.03, 0.47, cz + 0.22))     # foot of the upright (front-right edge)
    fA0, fA1 = b1 - 2, b1 + 18                    # focus pull + tilt from the worm to the foot of the cross
    fB0, fB1 = b1 + 8, NR - 4                     # crane up + tilt up the upright to the figure

    def path(f):
        t = (f - 1) / fps
        drift = Vector((heading.x, heading.y, 0)) * (0.0036 * min(t, (fA1 - 1) / fps))
        tA = C.smoothstep(min(1.0, max(0.0, (f - fA0) / (fA1 - fA0))))
        uB = C.smoothstep(min(1.0, max(0.0, (f - fB0) / (fB1 - fB0))))
        loc = (cam0 + drift).lerp(cam1, uB)
        loc.z = cam0.z + (cam1.z - cam0.z) * uB ** 0.9
        tow = (Vector((base_pt.x, base_pt.y, 0)) - Vector((loc.x, loc.y, 0))).normalized()
        loc += tow * (0.08 * math.sin(math.pi * uB))
        climb = C.smootherstep(min(1.0, uB * 1.04))
        tg = (tgt0 + drift).lerp(base_pt, tA) + (tgt1 - base_pt) * climb
        loc = loc + C.shake(f, 0.0004 + 0.005 * uB, 0.5, 11)
        fd = (tg - loc).length
        if uB > 0.7:      # settle focus on the body
            fd = fd + ((fig - loc).length - fd) * _smooth(0.7, 1.0, uB)
        return (loc, tg, 0.0, LENS, fd)

    C.animate_camera(cam, path, 1, NR)
    # ---- render-cost: hide what the camera cannot see
    f_up = NR + 1                      # first frame after which the lower frustum edge stays above the horizon
    half_v = math.atan(18.0 / LENS)
    for f in range(NR, 0, -1):
        loc_, tg_ = path(f)[:2]
        d_ = Vector(tg_) - Vector(loc_)
        pitch = math.atan2(d_.z, Vector((d_.x, d_.y)).length)
        if pitch - half_v < math.radians(2.0):
            break
        f_up = f
    print("S05 ground leaves the frame at", f_up)
    ground_objs = [mg, worm] + [o for o in bpy.data.objects if o.name.startswith(("S05Pebbles", "S05Grit", "S05Stones"))]
    if f_up <= NR:
        _key_visible(ground_objs, [(1, True), (f_up, False)])
    if not FAST:
        _key_visible(j.objects(), [(1, False), (fB0 - 4, True)])
        _key_visible(w1.objects(), [(1, True), (fB0 + 24, False)])
        _key_visible(w2.objects(), [(1, True), (104, False)])
    bl = C.light("AREA", loc=(0.25, -1.3, cz + 0.12), energy=0.0, color=(1.0, 0.72, 0.52), size=1.6,
                 target=(0.0, 0.45, cz + 1.6), name="GroundBounce", shadow=False)
    C.keys(bl.data, "energy", [(fB0, 0.0), (int(fB0 + 0.45 * (fB1 - fB0)), 7.0), (int(fB0 + 0.8 * (fB1 - fB0)), 1.0), (fB1, 0.0)])

    ctx.samples = 5
    ctx.render_opts.update({"volumetrics": "low", "motion_blur": True})
    ctx.interp = False          # striding feet in macro + dust grains + a fast crane-tilt: render 24 fps
    ctx.post.update({"grade": "eclipse", "saturation": 0.82, "vignette": 0.32,
                     "end": {"saturation": 0.62}, "caption": {"y": 0.70, "halo": 1.2}})
