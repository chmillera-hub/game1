"""wardrobe.py - period clothing (1st-century Judea / Rome) for MPFB humans.

    from lib import wardrobe as W
    garments = W.dress(person, "robe", colors={"tunic": "cream", "mantle": "brown"}, seed=3, detail="hero")
    W.drape(person, garments, frames=30)          # optional: cloth-sim settle on the CURRENT pose (hero stills)

`person` is anything exposing .rig (MPFB 'default' armature), .body (MPFB basemesh with its vertex
groups + armature modifier) and .height. Every garment is built in the rig's REST pose from the actual
body shape (so it fits any MPFB phenotype), parented to person.rig and deformed by an Armature modifier
with weights transferred from the body / MPFB clothing helpers. See docs/wardrobe.md for the full API.
"""
import bpy, bmesh, math, os, random, time, json, hashlib
import numpy as np
from mathutils import Vector, Matrix, Euler, noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from . import core as C

CACHE = os.path.join(C.WORK, "cache", "wardrobe")

# ----------------------------------------------------------------------------------------------
# Palette (sRGB, natural dyes) - pass names or RGB tuples in `colors`
# ----------------------------------------------------------------------------------------------
PALETTE = {
    "undyed": (0.80, 0.74, 0.62), "cream": (0.84, 0.79, 0.68), "linen": (0.82, 0.78, 0.69),
    "white_linen": (0.90, 0.88, 0.83), "bleached": (0.93, 0.92, 0.88),
    "oatmeal": (0.70, 0.63, 0.52), "sand": (0.68, 0.59, 0.46), "camel": (0.58, 0.45, 0.30),
    "brown": (0.38, 0.27, 0.18), "dark_brown": (0.22, 0.15, 0.10), "umber": (0.30, 0.22, 0.15),
    "grey": (0.47, 0.45, 0.42), "charcoal": (0.17, 0.16, 0.15), "black_wool": (0.08, 0.075, 0.07),
    "indigo": (0.13, 0.18, 0.31), "blue_grey": (0.33, 0.38, 0.44), "woad": (0.27, 0.34, 0.45),
    "tekhelet": (0.10, 0.20, 0.45), "mary_blue": (0.22, 0.31, 0.46),
    "madder": (0.52, 0.15, 0.10), "roman_red": (0.56, 0.09, 0.06), "rust": (0.47, 0.23, 0.13),
    "ochre": (0.64, 0.46, 0.21), "saffron": (0.76, 0.56, 0.19), "olive": (0.38, 0.37, 0.22),
    "purple": (0.28, 0.11, 0.24), "plum": (0.33, 0.17, 0.24), "scarlet": (0.62, 0.10, 0.08),
    "leather": (0.36, 0.22, 0.12), "dark_leather": (0.17, 0.10, 0.06),
    "iron": (0.42, 0.42, 0.43), "bronze": (0.62, 0.42, 0.20), "brass": (0.72, 0.56, 0.28),
    "gold": (0.85, 0.66, 0.30), "thorn": (0.30, 0.24, 0.17),
}

# default colour choices per garment part (seeded random pick) - muted, period plausible
CHOICES = {
    "tunic": ["undyed", "cream", "oatmeal", "linen", "sand", "grey", "camel", "undyed", "brown"],
    "mantle": ["brown", "umber", "camel", "grey", "charcoal", "indigo", "blue_grey", "madder", "olive", "oatmeal",
               "rust", "dark_brown", "woad"],
    "belt": ["dark_brown", "brown", "leather", "charcoal", "madder", "ochre"],
    "headcloth": ["cream", "undyed", "white_linen", "oatmeal", "sand", "grey", "ochre"],
    "veil": ["mary_blue", "blue_grey", "indigo", "grey", "oatmeal", "brown"],
    "hood": ["brown", "umber", "grey", "charcoal", "camel", "olive"],
}

_LIN = lambda c: tuple(x ** 2.2 for x in c[:3])


def color(c, rnd=None, jitter=0.0):
    """Palette name / sRGB tuple -> linear RGB (optional small random jitter in value/hue)."""
    rgb = PALETTE[c] if isinstance(c, str) else tuple(c)
    if rnd is not None and jitter:
        v = 1 + (rnd.random() - 0.5) * 2 * jitter
        rgb = tuple(min(1, max(0, x * v * (1 + (rnd.random() - 0.5) * jitter * 0.5))) for x in rgb)
    return _LIN(rgb)


# ----------------------------------------------------------------------------------------------
# Body analysis
# ----------------------------------------------------------------------------------------------
REGIONS = ["torso", "hips", "neck", "head", "shoulder_L", "shoulder_R", "upperarm_L", "upperarm_R",
           "forearm_L", "forearm_R", "hand_L", "hand_R", "thigh_L", "thigh_R", "shin_L", "shin_R",
           "foot_L", "foot_R"]
RID = {n: i for i, n in enumerate(REGIONS)}
_ROOTS = {"head": "head", "neck01": "neck", "wrist.L": "hand_L", "wrist.R": "hand_R",
          "lowerarm01.L": "forearm_L", "lowerarm01.R": "forearm_R", "upperarm01.L": "upperarm_L",
          "upperarm01.R": "upperarm_R", "shoulder01.L": "shoulder_L", "shoulder01.R": "shoulder_R",
          "clavicle.L": "torso", "clavicle.R": "torso", "foot.L": "foot_L", "foot.R": "foot_R",
          "lowerleg01.L": "shin_L", "lowerleg01.R": "shin_R", "upperleg01.L": "thigh_L",
          "upperleg01.R": "thigh_R", "breast.L": "torso", "breast.R": "torso", "spine05": "torso",
          "spine04": "torso", "spine03": "torso", "pelvis.L": "hips", "pelvis.R": "hips", "root": "hips"}
ARM_L = {RID["upperarm_L"], RID["forearm_L"], RID["hand_L"]}
ARM_R = {RID["upperarm_R"], RID["forearm_R"], RID["hand_R"]}
LEGS = {RID[n] for n in ("thigh_L", "thigh_R", "shin_L", "shin_R")}


def _np_co(me):
    a = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)


def _np_tris(me):
    me.calc_loop_triangles()
    t = np.empty(len(me.loop_triangles) * 3, np.int64)
    me.loop_triangles.foreach_get("vertices", t)
    return t.reshape(-1, 3)


class Body:
    """Rest-pose analysis of an MPFB person (armature space). Cached per person via body_info()."""

    def __init__(self, person):
        t0 = time.time()
        self.person = person
        rig, body = person.rig, person.body
        self.rig, self.body = rig, body
        # armature-space matrix of the body
        self.m_body = rig.matrix_world.inverted() @ body.matrix_world
        co, nrm, tris = self._rest_mesh(body)
        M = np.array(self.m_body)
        co = co @ M[:3, :3].T + M[:3, 3]
        self.co_all = co
        me = body.data
        names = [g.name for g in body.vertex_groups]
        bones = rig.data.bones
        self.bone_names = [b.name for b in bones if b.use_deform]
        bidx = {n: i for i, n in enumerate(self.bone_names)}
        gmap = {gi: bidx.get(n, -1) for gi, n in enumerate(names)}
        special = {n: i for i, n in enumerate(names) if n in ("body", "helper-skirt", "helper-tights")}
        n = len(co)
        W = np.zeros((n, len(self.bone_names)), np.float32)
        isb = np.zeros(n, bool)
        isk = np.zeros(n, bool)
        ist = np.zeros(n, bool)
        sb, sk, st = special.get("body", -9), special.get("helper-skirt", -9), special.get("helper-tights", -9)
        for v in me.vertices:
            i = v.index
            for g in v.groups:
                gi = g.group
                b = gmap.get(gi, -1)
                if b >= 0:
                    W[i, b] = g.weight
                elif gi == sb:
                    isb[i] = g.weight > 0.5
                elif gi == sk:
                    isk[i] = g.weight > 0.5
                elif gi == st:
                    ist[i] = g.weight > 0.5
        s = W.sum(1)
        W[s > 0] /= s[s > 0, None]
        self.W = W
        # regions from the dominant bone
        reg_of_bone = np.zeros(len(self.bone_names), np.int32)
        for i, bn in enumerate(self.bone_names):
            b = bones[bn]
            r = None
            while b is not None and r is None:
                r = _ROOTS.get(b.name)
                b = b.parent
            reg_of_bone[i] = RID[r or "torso"]
        self.reg_of_bone = reg_of_bone
        self.region = reg_of_bone[W.argmax(1)]
        self.is_body, self.is_skirt, self.is_tights = isb, isk, ist
        # surfaces
        self.tris_all = tris
        self.vnormal = nrm @ M[:3, :3].T
        self.bvh = {}
        # 'core' = body without forearms/hands: in the A rest pose the hands hang next to the hips, so hems,
        # belts and skirts must never sample them (upper arms are fine: they sit at shoulder height)
        armreg = np.isin(self.region, [RID[r] for r in ("forearm_L", "forearm_R", "hand_L", "hand_R")])
        self.layers = []             # rest-pose garments already built on this person (outer layers hug them)
        for key, mask in (("body", isb), ("core", isb & ~armreg), ("skirt", isk), ("tights", ist)):
            tm = tris[mask[tris].all(1)]
            self.bvh[key] = (BVHTree.FromPolygons([tuple(p) for p in co], tm.tolist(), all_triangles=True), tm)
        self.bidx = np.nonzero(isb)[0]
        self.bco = co[isb]
        self.breg = self.region[isb]
        self.bnrm = self.vnormal[isb]
        self.kd = KDTree(len(self.bco))
        for i, p in enumerate(self.bco):
            self.kd.insert(p, i)
        self.kd.balance()
        # bones (armature space rest)
        self.bone = {b.name: (np.array(b.head_local), np.array(b.tail_local)) for b in bones}
        # extra meshes (hair etc.) for head garments
        self.hair = np.zeros((0, 3))
        hair_objs = []
        parts = getattr(person, "parts", None) or {}
        if parts.get("hair") is not None:
            hair_objs.append(parts["hair"])
        for o in rig.children_recursive:
            if o.type == "MESH" and o is not body and not o.get("wardrobe") and o not in hair_objs and \
                    (o.get("MPFB_GEN_object_type") == "Hair" or "hair" in o.name.lower()):
                hair_objs.append(o)
        self.hair_objs = hair_objs
        for o in hair_objs:
            if o.type == "MESH":
                hc, _, ht = self._rest_mesh(o)
                Mo = np.array(rig.matrix_world.inverted() @ o.matrix_world)
                hc = hc @ Mo[:3, :3].T + Mo[:3, 3]
                self.hair = np.vstack([self.hair, hc, sample_surface(hc, ht, 1.5e-5)])
        self.height = float(co[isb, 2].max() - co[isb, 2].min())
        self.ground = float(co[isb, 2].min())
        self.build_time = time.time() - t0

    def _rest_mesh(self, ob):
        rig = self.rig
        saved = rig.data.pose_position
        rig.data.pose_position = "REST"
        mods = [(m, m.show_viewport) for m in ob.modifiers]
        for m, _ in mods:
            m.show_viewport = False
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = _np_co(me)
        nr = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("normal", nr)
        tris = _np_tris(me)
        ev.to_mesh_clear()
        for m, s in mods:
            m.show_viewport = s
        rig.data.pose_position = saved
        bpy.context.view_layer.update()
        return co, nr.reshape(-1, 3), tris

    # -- landmarks -------------------------------------------------------------------------
    def head(self, b):
        return self.bone[b][0]

    def tail(self, b):
        return self.bone[b][1]

    def pts(self, regions, zmin=-9, zmax=9):
        m = np.isin(self.breg, list(regions)) & (self.bco[:, 2] >= zmin) & (self.bco[:, 2] <= zmax)
        return self.bco[m]

    def nearest_region(self, P):
        out = np.empty(len(P), np.int32)
        dist = np.empty(len(P))
        for i, p in enumerate(P):
            c, j, d = self.kd.find(p)
            out[i] = self.breg[j]
            dist[i] = d
        return out, dist

    def sample_weights(self, P, surface="body"):
        """Barycentric-interpolated bone weights of the nearest point on a surface."""
        bvh, tm = self.bvh[surface]
        co = self.co_all
        n = len(P)
        L = np.zeros((n, 3))
        FI = np.zeros(n, np.int64)
        dist = np.zeros(n)
        for i, p in enumerate(P):
            loc, nrm, fi, d = bvh.find_nearest(Vector(p))
            if fi is None:
                fi, loc, d = 0, Vector(co[tm[0][0]]), 1.0
            L[i] = loc
            FI[i] = fi
            dist[i] = d
        a, b, c = co[tm[FI, 0]], co[tm[FI, 1]], co[tm[FI, 2]]
        bc = bary_v(L, a, b, c)
        W = (bc[:, 0:1] * self.W[tm[FI, 0]] + bc[:, 1:2] * self.W[tm[FI, 1]] + bc[:, 2:3] * self.W[tm[FI, 2]])
        return W.astype(np.float32), dist


def bary_v(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00 = (v0 * v0).sum(1)
    d01 = (v0 * v1).sum(1)
    d11 = (v1 * v1).sum(1)
    d20 = (v2 * v0).sum(1)
    d21 = (v2 * v1).sum(1)
    den = d00 * d11 - d01 * d01
    den[np.abs(den) < 1e-14] = 1e-14
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    r = np.clip(np.stack([1 - v - w, v, w], 1), 0, 1)
    return r / np.maximum(1e-9, r.sum(1))[:, None]


def sample_surface(co, tris, area_per_point=2e-5, max_pts=60000, seed=1):
    """Random points on a triangle mesh (hair cards are big quads: their vertices alone miss the surface)."""
    if not len(tris):
        return np.zeros((0, 3))
    a, b, c = co[tris[:, 0]], co[tris[:, 1]], co[tris[:, 2]]
    ar = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    n = int(min(max_pts, ar.sum() / area_per_point))
    if n <= 0:
        return np.zeros((0, 3))
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(tris), n, p=ar / ar.sum())
    r1, r2 = rng.random(n), rng.random(n)
    s1 = np.sqrt(r1)
    return a[idx] * (1 - s1)[:, None] + b[idx] * (s1 * (1 - r2))[:, None] + c[idx] * (s1 * r2)[:, None]


def _bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-14:
        return np.array([1.0, 0, 0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    u = 1 - v - w
    r = np.clip(np.array([u, v, w]), 0, 1)
    return r / max(1e-9, r.sum())


_BODY_CACHE = {}


def body_info(person):
    key = person.body.name
    b = _BODY_CACHE.get(key)
    if b is None or b.body != person.body:
        b = Body(person)
        _BODY_CACHE[key] = b
    return b


# ----------------------------------------------------------------------------------------------
# 2D hull / slice utilities
# ----------------------------------------------------------------------------------------------
def hull2d(P):
    P = np.unique(np.round(P, 6), axis=0)
    if len(P) < 3:
        return P
    P = P[np.lexsort((P[:, 1], P[:, 0]))]

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in P:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(tuple(p))
    for p in P[::-1]:
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(tuple(p))
    return np.array(lo[:-1] + up[:-1])


def ray_radii(H, c, ang):
    """Distance from c to the convex polygon H along directions ang (radians)."""
    if len(H) < 3:
        return np.full(len(ang), 0.02)
    A = H
    B = np.roll(H, -1, axis=0)
    d = np.stack([np.cos(ang), np.sin(ang)], 1)          # K,2
    e = B - A                                             # E,2
    ac = A - c                                            # E,2
    den = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]   # K,E
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (ac[None, :, 0] * e[None, :, 1] - ac[None, :, 1] * e[None, :, 0]) / den
        s = (ac[None, :, 0] * d[:, None, 1] - ac[None, :, 1] * d[:, None, 0]) / den
    ok = (s >= -1e-6) & (s <= 1 + 1e-6) & (t > 0) & np.isfinite(t)
    t = np.where(ok, t, 0)
    r = t.max(1)
    return np.maximum(r, 0.01)


def circ_smooth(r, k=2, axis=-1):
    """Circular moving average along the angle axis."""
    if k <= 0:
        return r
    acc = np.zeros_like(r)
    for s in range(-k, k + 1):
        acc += np.roll(r, s, axis=axis)
    return acc / (2 * k + 1)


def zsmooth(R, k=1):
    """Moving average along axis 0 (rings), edges clamped."""
    if k <= 0:
        return R
    P = np.concatenate([R[:1].repeat(k, 0), R, R[-1:].repeat(k, 0)], 0)
    acc = np.zeros_like(R)
    for s in range(2 * k + 1):
        acc += P[s:s + len(R)]
    return acc / (2 * k + 1)


def slice_rings(P, zs, ang, center_fn=None, dz=0.012, min_pts=8):
    """For each z: convex hull of points within the slab -> radii at angles about a centre.
    Returns centers (M,2), radii (M,K) (rows without data are interpolated)."""
    M, K = len(zs), len(ang)
    R = np.full((M, K), np.nan)
    Cs = np.zeros((M, 2))
    for i, z in enumerate(zs):
        dd = dz
        S = P[np.abs(P[:, 2] - z) < dd]
        while len(S) < min_pts and dd < 0.05:
            dd *= 1.6
            S = P[np.abs(P[:, 2] - z) < dd]
        if len(S) < 3:
            Cs[i] = center_fn(z) if center_fn else (0, 0)
            continue
        H = hull2d(S[:, :2])
        c = np.array(center_fn(z)) if center_fn else H.mean(0)
        Cs[i] = c
        R[i] = ray_radii(H, c, ang)
    # fill missing rows
    good = ~np.isnan(R[:, 0])
    if not good.any():
        R[:] = 0.05
    elif not good.all():
        idx = np.arange(M)
        for k in range(K):
            R[:, k] = np.interp(idx, idx[good], R[good, k])
    return Cs, R


# ----------------------------------------------------------------------------------------------
# Mesh construction helpers
# ----------------------------------------------------------------------------------------------
def loft_closed(rings):
    """rings: list of (M) arrays (K,3) -> verts, faces (quads + cap fans), closed solid."""
    M, K = len(rings), len(rings[0])
    V = np.concatenate(rings, 0)
    F = []
    for i in range(M - 1):
        a, b = i * K, (i + 1) * K
        for k in range(K):
            k2 = (k + 1) % K
            F.append((a + k, a + k2, b + k2, b + k))
    c0 = len(V)
    c1 = c0 + 1
    V = np.vstack([V, rings[0].mean(0), rings[-1].mean(0)])
    for k in range(K):
        k2 = (k + 1) % K
        F.append((c0, k2, k))
        F.append((c1, (M - 1) * K + k, (M - 1) * K + k2))
    return V, F


def frame_of(d):
    d = d / np.linalg.norm(d)
    up = np.array([0, 0, 1.0]) if abs(d[2]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(up, d)
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    return u, v


def make_mesh(name, V, F, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in V], [], [tuple(f) for f in F])
    me.validate(clean_customdata=False)
    me.update()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def mesh_arrays(me):
    V = _np_co(me)
    fl = np.empty(len(me.polygons), np.int64)
    me.polygons.foreach_get("loop_total", fl)
    lv = np.empty(len(me.loops), np.int64)
    me.loops.foreach_get("vertex_index", lv)
    F = np.split(lv, np.cumsum(fl)[:-1]) if len(fl) else []
    E = np.empty(len(me.edges) * 2, np.int64)
    me.edges.foreach_get("vertices", E)
    return V, [tuple(f) for f in F], E.reshape(-1, 2)


def voxel_union(parts, voxel, name="tmp_union"):
    """parts: list of (V, F) closed solids -> remeshed union arrays (V, F, E)."""
    Vs, Fs, off = [], [], 0
    for V, F in parts:
        Vs.append(V)
        Fs += [tuple(i + off for i in f) for f in F]
        off += len(V)
    ob = make_mesh(name, np.vstack(Vs), Fs)
    m = ob.modifiers.new("remesh", "REMESH")
    m.mode = "VOXEL"
    m.voxel_size = voxel
    m.adaptivity = 0.0
    m.use_smooth_shade = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    out = mesh_arrays(me)
    bpy.data.meshes.remove(me)
    old = ob.data
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(old)
    return out


def to_bm(V, F):
    bm = bmesh.new()
    vs = [bm.verts.new(tuple(p)) for p in V]
    for f in F:
        try:
            bm.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bm.verts.ensure_lookup_table()
    return bm


def from_bm(bm):
    bm.verts.index_update()
    V = np.array([v.co[:] for v in bm.verts])
    F = [tuple(v.index for v in f.verts) for f in bm.faces]
    E = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges], np.int64).reshape(-1, 2)
    return V, F, E


def bm_cut_plane(bm, co, no, face_filter=None, center_mask=None):
    """Cut along a plane and delete the side the normal points to. Restrict to some faces with
    face_filter(face)->bool or (faster) center_mask(centers (F,3) array)->bool array."""
    co, no = Vector(co), Vector(no).normalized()
    if center_mask is not None:
        fl = list(bm.faces)
        cen = np.array([f.calc_center_median()[:] for f in fl]).reshape(-1, 3)
        m = center_mask(cen)
        faces = [f for f, k in zip(fl, m) if k]
    else:
        faces = [f for f in bm.faces if face_filter is None or face_filter(f)]
    if not faces:
        return
    edges = list({e for f in faces for e in f.edges})
    verts = list({v for f in faces for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=faces + edges + verts, dist=1e-5, plane_co=co, plane_no=no,
                           clear_outer=True)


def dist_polyline(P, pts):
    """Distance of points P (N,3) to a polyline pts (M,3)."""
    best = np.full(len(P), 1e9)
    for a, b in zip(pts[:-1], pts[1:]):
        ab = b - a
        t = np.clip((P - a) @ ab / max(1e-12, ab @ ab), 0, 1)
        d = np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
        best = np.minimum(best, d)
    return best


def bm_keep_largest(bm):
    bm.verts.ensure_lookup_table()
    seen = set()
    islands = []
    for v in bm.verts:
        if v in seen:
            continue
        stack, isl = [v], []
        seen.add(v)
        while stack:
            x = stack.pop()
            isl.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o not in seen:
                    seen.add(o)
                    stack.append(o)
        islands.append(isl)
    islands.sort(key=len, reverse=True)
    for isl in islands[1:]:
        bmesh.ops.delete(bm, geom=isl, context="VERTS")


def bm_remove_loose(bm):
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")


def _face_edges(F):
    a, b = [], []
    for f in F:
        n = len(f)
        for i in range(n):
            a.append(f[i])
            b.append(f[(i + 1) % n])
    a, b = np.array(a, np.int64), np.array(b, np.int64)
    return np.minimum(a, b), np.maximum(a, b)


def boundary_mask(nv, F, E=None):
    """Vertices on open boundaries (edges used by one face)."""
    lo, hi = _face_edges(F)
    key = lo * (nv + 1) + hi
    u, cnt = np.unique(key, return_counts=True)
    be = u[cnt == 1]
    m = np.zeros(nv, bool)
    m[be // (nv + 1)] = True
    m[be % (nv + 1)] = True
    return m


def edges_of(F):
    lo, hi = _face_edges(F)
    nv = int(hi.max()) + 1 if len(hi) else 1
    u = np.unique(lo * (nv + 1) + hi)
    return np.stack([u // (nv + 1), u % (nv + 1)], 1).astype(np.int64)


def laplacian(V, E, iters=4, lam=0.5, mu=-0.53, fixed=None, weight=None):
    """Taubin smoothing (numpy). fixed: bool mask of pinned verts; weight: per-vertex factor 0..1."""
    V = V.copy()
    n = len(V)
    a, b = E[:, 0], E[:, 1]
    deg = np.bincount(a, minlength=n) + np.bincount(b, minlength=n)
    deg = np.maximum(deg, 1)[:, None]
    f = np.ones(n) if weight is None else weight
    if fixed is not None:
        f = f * (~fixed)
    f = f[:, None]
    for _ in range(iters):
        for step in ((lam, mu) if mu else (lam,)):
            S = np.zeros_like(V)
            for k in range(3):
                S[:, k] = np.bincount(a, V[b, k], n) + np.bincount(b, V[a, k], n)
            V += step * f * (S / deg - V)
    return V


def smooth_field(X, E, iters=10, lam=0.5, weight=None):
    """Laplacian smoothing of a per-vertex field (N,) or (N,K)."""
    X = X.astype(np.float64).copy()
    one = X.ndim == 1
    if one:
        X = X[:, None]
    n = len(X)
    a, b = E[:, 0], E[:, 1]
    deg = np.maximum(np.bincount(a, minlength=n) + np.bincount(b, minlength=n), 1)[:, None]
    f = (np.ones(n) if weight is None else weight)[:, None]
    for _ in range(iters):
        S = np.zeros_like(X)
        for k in range(X.shape[1]):
            S[:, k] = np.bincount(a, X[b, k], n) + np.bincount(b, X[a, k], n)
        X += lam * f * (S / deg - X)
    return X[:, 0] if one else X


def tri_fan(F):
    T = []
    for f in F:
        for i in range(1, len(f) - 1):
            T.append((f[0], f[i], f[i + 1]))
    return np.array(T, np.int64).reshape(-1, 3)


def vertex_normals(V, F, T=None):
    T = tri_fan(F) if T is None else T
    fn = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    N = np.zeros_like(V)
    for k in range(3):
        for c in range(3):
            N[:, c] += np.bincount(T[:, k], fn[:, c], len(V))
    ln = np.linalg.norm(N, axis=1)
    ln[ln == 0] = 1
    return N / ln[:, None]


def push_out(V, B, gap=0.005, normals=None, surface="body", layers=True, layer_gap=None):
    """Move vertices that are inside the body (or closer than gap) out along the body normal; then the
    same against garments already built on this person (B.layers) so outer layers never cut inner ones."""
    V = V.copy()
    surfs = [(B.bvh[surface][0], gap, 0.08)]
    if layers:
        lg = layer_gap if layer_gap is not None else max(gap, 0.006)
        surfs += [(bvh, lg, 0.035) for bvh in [L["bvh"] for L in B.layers]]
    moved = 0
    for bvh, g, reach in surfs:
        for i, p in enumerate(V):
            # only nearby surfaces: a far-away nearest point (e.g. an inner garment's neck edge seen from a
            # turban) has a meaningless normal and would yank the vertex into a long spike
            loc, nrm, fi, d = bvh.find_nearest(Vector(p), reach)
            if loc is None:
                continue
            s_ = (Vector(p) - loc).dot(nrm)
            if s_ < g and s_ > -min(reach, 0.06):
                V[i] = np.array(loc + nrm * g)
                moved += 1
    return V, moved


def add_layer(B, V, F, name, W=None, ob=None):
    """Register a built garment (rest verts/faces + bone weights) so later garments are pushed outside it
    and inherit its weights where they lie on top of it (layers then deform together)."""
    T = tri_fan(F)
    L = dict(name=name, V=np.asarray(V), T=T, W=W, ob=ob,
             bvh=BVHTree.FromPolygons([tuple(p) for p in V], T.tolist(), all_triangles=True))
    if W is not None:
        armb = np.isin(B.reg_of_bone, [RID[r] for r in ("forearm_L", "forearm_R", "hand_L", "hand_R")])
        armv = W[:, armb].sum(1) > 0.3
        Tc = T[~armv[T].any(1)]
        L["Tc"] = Tc
        L["bvh_core"] = BVHTree.FromPolygons([tuple(p) for p in V], Tc.tolist(), all_triangles=True) if len(Tc) else None
    B.layers.append(L)


def sample_layers(B, P, maxd=0.05, core=None):
    """Weights interpolated from the nearest inner garment layer (dist 9 where no layer within maxd).
    core: bool mask of P that must ignore the inner layers' sleeve parts (arm-weighted triangles)."""
    n = len(P)
    best = np.full(n, 9.0)
    W = np.zeros((n, len(B.bone_names)), np.float32)
    core = np.zeros(n, bool) if core is None else core
    for L in B.layers:
        if L.get("W") is None:
            continue
        hits = []
        for i, p in enumerate(P):
            if core[i]:
                if L.get("bvh_core") is None:
                    continue
                loc, nrm, fi, d = L["bvh_core"].find_nearest(Vector(p), maxd)
                tri = L["Tc"]
            else:
                loc, nrm, fi, d = L["bvh"].find_nearest(Vector(p), maxd)
                tri = L["T"]
            if loc is None or d >= best[i]:
                continue
            hits.append((i, fi, loc[0], loc[1], loc[2], 1 if core[i] else 0))
            best[i] = d
        if hits:
            H = np.array(hits)
            ii = H[:, 0].astype(np.int64)
            fi = H[:, 1].astype(np.int64)
            loc = H[:, 2:5]
            tri = np.where(H[:, 5:6] > 0, L["Tc"][np.minimum(fi, len(L["Tc"]) - 1)] if len(L.get("Tc", [])) else L["T"][fi], L["T"][np.minimum(fi, len(L["T"]) - 1)])
            bc = bary_v(loc, L["V"][tri[:, 0]], L["V"][tri[:, 1]], L["V"][tri[:, 2]])
            Wl = bc[:, 0:1] * L["W"][tri[:, 0]] + bc[:, 1:2] * L["W"][tri[:, 1]] + bc[:, 2:3] * L["W"][tri[:, 2]]
            # later (closer) hits overwrite earlier ones in order
            W[ii] = Wl
    return W, best


def layer_points(B, step=3):
    if not B.layers:
        return np.zeros((0, 3))
    return np.vstack([L["V"][::step] for L in B.layers])


# ----------------------------------------------------------------------------------------------
# Materials (shared per fabric kind; colour per object via Object Info > Color)
# ----------------------------------------------------------------------------------------------
FABRICS = {
    # kind: (polyhaven asset, repeats per metre (asset is ~0.27 m wide), bump, rough_base, sheen, value_range)
    "linen": ("rough_linen", 3.7, 0.50, 0.82, 0.30, (0.84, 1.10)),
    "fine_linen": ("rough_linen", 6.0, 0.30, 0.72, 0.40, (0.92, 1.05)),
    "wool": ("poly_wool_herringbone", 3.6, 0.55, 0.90, 0.55, (0.82, 1.12)),
    "homespun": ("hessian_380", 3.7, 0.60, 0.92, 0.30, (0.84, 1.12)),
    "sackcloth": ("hessian_230", 3.7, 0.70, 0.94, 0.20, (0.75, 1.18)),
    "leather": ("brown_leather", 2.5, 0.55, 0.55, 0.0, (0.75, 1.20)),
}
_MATS = {}


def _tex(nt, path, vec, noncolor=False):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        t.image.colorspace_settings.name = "Non-Color"
    nt.links.new(vec, t.inputs["Vector"])
    return t


def fabric_material(kind="linen", embroidery=False, stripes=False):
    """Shared fabric material. Colour = object colour (obj.color). Reads vertex attributes
    'wear' (0..1 dust/dirt) and 'hem' (metres from the hem, for embroidered bands)."""
    key = (kind, embroidery, stripes)
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    asset, rep, bump, rough0, sheen, (v0, v1) = FABRICS[kind]
    from . import polyhaven as ph
    maps = ph.texture_maps(asset, "1k")
    m = bpy.data.materials.new("W_%s%s%s" % (kind, "_emb" if embroidery else "", "_str" if stripes else ""))
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    b = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (rep, rep, rep)
    L.new(uv.outputs["UV"], mp.inputs["Vector"])
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    # weave luminance variation x object colour
    col = oi.outputs["Color"]
    if "diff" in maps:
        d = _tex(nt, maps["diff"], mp.outputs["Vector"])
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        L.new(d.outputs["Color"], bw.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.15
        mr.inputs["From Max"].default_value = 0.65
        mr.inputs["To Min"].default_value = v0
        mr.inputs["To Max"].default_value = v1
        L.new(bw.outputs[0], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeVectorMath")
        mul.operation = "MULTIPLY"
        L.new(oi.outputs["Color"], mul.inputs[0])
        L.new(mr.outputs["Result"], mul.inputs[1])
        col = mul.outputs["Vector"]
    # low-frequency dye unevenness
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 2.5
    nz.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    nmr = nt.nodes.new("ShaderNodeMapRange")
    nmr.inputs["To Min"].default_value = 0.93
    nmr.inputs["To Max"].default_value = 1.05
    L.new(nz.outputs["Fac"], nmr.inputs["Value"])
    mul2 = nt.nodes.new("ShaderNodeVectorMath")
    mul2.operation = "MULTIPLY"
    L.new(col, mul2.inputs[0])
    L.new(nmr.outputs["Result"], mul2.inputs[1])
    col = mul2.outputs["Vector"]
    if embroidery:
        col = _embroidery(nt, col, uv, b)
    if stripes:
        col = _stripes(nt, col)
    # wear / dust
    wa = nt.nodes.new("ShaderNodeAttribute")
    wa.attribute_name = "wear"
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 22.0
    nz2.inputs["Detail"].default_value = 5
    L.new(tc.outputs["Generated"], nz2.inputs["Vector"])
    wm = nt.nodes.new("ShaderNodeMath")
    wm.operation = "MULTIPLY"
    L.new(wa.outputs["Fac"], wm.inputs[0])
    L.new(nz2.outputs["Fac"], wm.inputs[1])
    wm2 = nt.nodes.new("ShaderNodeMath")
    wm2.operation = "MULTIPLY"
    wm2.use_clamp = True
    wm2.inputs[1].default_value = 0.9
    L.new(wm.outputs[0], wm2.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (*_LIN((0.60, 0.52, 0.40)), 1)
    L.new(wm2.outputs[0], mix.inputs["Factor"])
    L.new(col, mix.inputs["A"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    # roughness
    if "rough" in maps:
        r = _tex(nt, maps["rough"], mp.outputs["Vector"], True)
        rm = nt.nodes.new("ShaderNodeMapRange")
        rm.inputs["To Min"].default_value = rough0 - 0.12
        rm.inputs["To Max"].default_value = min(1.0, rough0 + 0.12)
        L.new(r.outputs["Color"], rm.inputs["Value"])
        ra = nt.nodes.new("ShaderNodeMath")
        ra.operation = "MULTIPLY_ADD"
        ra.use_clamp = True
        ra.inputs[1].default_value = 0.15
        L.new(wm2.outputs[0], ra.inputs[0])
        L.new(rm.outputs["Result"], ra.inputs[2])
        L.new(ra.outputs[0], b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough0
    if "nor" in maps and bump > 0:
        n = _tex(nt, maps["nor"], mp.outputs["Vector"], True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = bump
        L.new(n.outputs["Color"], nm.inputs["Color"])
        L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Specular IOR Level"].default_value = 0.35 if kind != "leather" else 0.5
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Sheen Roughness"].default_value = 0.45
    if kind in ("linen", "fine_linen"):
        # thin linen: a touch of translucency in backlight
        b.inputs["Subsurface Weight"].default_value = 0.08
        b.inputs["Subsurface Radius"].default_value = (0.02, 0.02, 0.02)
    _MATS[key] = m
    return m


# ---- generated (tileable) textures ------------------------------------------------------------
_IMGS = {}


def _np_image(name, arr, noncolor=False):
    """numpy (H,W,4) float 0..1 -> packed Blender image (cached per session)."""
    im = _IMGS.get(name)
    if im is not None and im.name in bpy.data.images:
        return im
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    if noncolor:   # must be set BEFORE writing pixels (changing it regenerates a generated image)
        im.colorspace_settings.name = "Non-Color"
    im.pixels.foreach_set(np.ascontiguousarray(arr[::-1].astype(np.float32)).ravel())
    im.update()
    im.pack()
    _IMGS[name] = im
    return im


def mail_image(n=256, rings=8):
    """Height (R) + ring mask (G) of riveted ring mail, staggered rows, tileable."""
    y, x = np.mgrid[0:n, 0:n] / n * rings
    h = np.zeros((n, n))
    for ox, oy in ((0, 0), (0.5, 0.5)):
        qx = (x + ox) % 1 - 0.5
        qy = ((y + oy) % 1 - 0.5) * 1.15
        d = np.sqrt(qx * qx + qy * qy)
        ring = np.clip(1 - np.abs(d - 0.36) / 0.10, 0, 1)
        # the overlapping rows: a ring rises where it crosses over its neighbour
        lift = 0.75 + 0.25 * np.sign(qx * qy + 1e-9) * (1 if ox == 0 else -1)
        h = np.maximum(h, np.sqrt(ring) * lift)
    a = np.zeros((n, n, 4))
    a[..., 0] = h
    a[..., 1] = (h > 0.05).astype(float)
    a[..., 3] = 1
    return a


def embroidery_image(w=512, hgt=128, seed=0):
    """Hem band: border lines + a repeating pomegranate / rosette motif (RGBA, alpha = thread)."""
    y, x = np.mgrid[0:hgt, 0:w].astype(float)
    u = x / w * 4            # 4 motifs per tile
    v = y / hgt
    rgb = np.zeros((hgt, w, 3))
    al = np.zeros((hgt, w))
    gold = np.array([0.78, 0.58, 0.22])
    red = np.array([0.55, 0.10, 0.08])
    blue = np.array([0.12, 0.20, 0.48])

    def paint(mask, col):
        m = np.clip(mask, 0, 1)
        for c in range(3):
            rgb[..., c] = rgb[..., c] * (1 - m) + col[c] * m
        al[:] = np.maximum(al, m)
    # border lines
    for v0, wd, col in ((0.08, 0.05, gold), (0.92, 0.05, gold), (0.17, 0.025, red), (0.83, 0.025, red)):
        paint(np.clip(1 - np.abs(v - v0) / wd, 0, 1) * 1.6, col)
    cu = (u % 1) - 0.5
    cv = v - 0.5
    # pomegranates (ovals) alternating with blue-red bells / rosettes
    pom = np.sqrt((cu / 0.20) ** 2 + (cv / 0.24) ** 2)
    paint((1 - pom) * 6, red)
    paint(np.clip(1 - np.abs(pom - 0.9) / 0.12, 0, 1), gold)
    cu2 = ((u + 0.5) % 1) - 0.5
    ros = np.sqrt((cu2 / 0.12) ** 2 + (cv / 0.14) ** 2)
    ang = np.arctan2(cv, cu2)
    petals = ros < (0.75 + 0.25 * np.cos(ang * 6))
    paint(petals * 1.0, blue)
    paint(np.clip(1 - ros / 0.3, 0, 1) * 3, gold)
    # zig-zag
    zz = np.abs(((u * 2) % 1) - 0.5) * 0.28 + 0.14
    paint(np.clip(1 - np.abs(v - zz) / 0.018, 0, 1) * (v < 0.3), gold)
    paint(np.clip(1 - np.abs(v - (1 - zz)) / 0.018, 0, 1) * (v > 0.7), gold)
    a = np.zeros((hgt, w, 4))
    a[..., :3] = rgb ** 2.2
    a[..., 3] = np.clip(al, 0, 1)
    return a


def stripes_image(n=256, stripes=((0.10, 0.022), (0.155, 0.012), (0.20, 0.012), (0.245, 0.022)), length=0.32,
                  col=(0.05, 0.06, 0.10)):
    """1-D stripe ramp along the hem distance (0..length m): RGBA, alpha = stripe."""
    v = np.linspace(0, length, n)
    al = np.zeros(n)
    for c, wd in stripes:
        al = np.maximum(al, np.clip((wd / 2 - np.abs(v - c)) / 0.002 + 0.5, 0, 1))
    a = np.zeros((2, n, 4))
    a[..., 0], a[..., 1], a[..., 2] = col
    a[..., 3] = al
    return a


def _embroidery(nt, col, uv, b, band=(0.025, 0.11)):
    """Embroidered band between hem distances band[0]..band[1] (metres)."""
    L = nt.links
    img = _np_image("W_embroidery", embroidery_image())
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    L.new(uv.outputs["UV"], sep.inputs[0])
    ha = nt.nodes.new("ShaderNodeAttribute")
    ha.attribute_name = "hem"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = band[0]
    mr.inputs["From Max"].default_value = band[1]
    mr.clamp = False
    L.new(ha.outputs["Fac"], mr.inputs["Value"])
    um = nt.nodes.new("ShaderNodeMath")
    um.operation = "MULTIPLY"
    um.inputs[1].default_value = 1.0 / ((band[1] - band[0]) * 4.0)      # tile is 4:1
    L.new(sep.outputs["X"], um.inputs[0])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    L.new(um.outputs[0], cmb.inputs["X"])
    L.new(mr.outputs["Result"], cmb.inputs["Y"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.extension = "REPEAT"
    L.new(cmb.outputs["Vector"], t.inputs["Vector"])
    # in-band mask
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.0
    L.new(mr.outputs["Result"], gt.inputs[0])
    lt = nt.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = 1.0
    L.new(mr.outputs["Result"], lt.inputs[0])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    L.new(gt.outputs[0], m1.inputs[0])
    L.new(lt.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    L.new(m1.outputs[0], m2.inputs[0])
    L.new(t.outputs["Alpha"], m2.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(m2.outputs[0], mix.inputs["Factor"])
    L.new(col, mix.inputs["A"])
    L.new(t.outputs["Color"], mix.inputs["B"])
    nt["emb_mask"] = m2.name
    return mix.outputs["Result"]


def _stripes(nt, col, length=0.32):
    L = nt.links
    img = _np_image("W_stripes", stripes_image(length=length))
    ha = nt.nodes.new("ShaderNodeAttribute")
    ha.attribute_name = "hem"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Max"].default_value = length
    L.new(ha.outputs["Fac"], mr.inputs["Value"])
    cmb = nt.nodes.new("ShaderNodeCombineXYZ")
    cmb.inputs["Y"].default_value = 0.5
    L.new(mr.outputs["Result"], cmb.inputs["X"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.extension = "EXTEND"
    L.new(cmb.outputs["Vector"], t.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    L.new(t.outputs["Alpha"], mix.inputs["Factor"])
    L.new(col, mix.inputs["A"])
    L.new(t.outputs["Color"], mix.inputs["B"])
    return mix.outputs["Result"]


def metal_material(kind="iron"):
    """Hand-worked metal (iron / bronze / brass / gold): hammer dents, tarnish, dirt from 'wear'."""
    key = ("metal", kind)
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    base = {"iron": (0.40, 0.40, 0.41), "bronze": (0.62, 0.43, 0.22), "brass": (0.75, 0.58, 0.30),
            "gold": (0.90, 0.70, 0.32)}[kind]
    rough = {"iron": 0.42, "bronze": 0.36, "brass": 0.33, "gold": 0.28}[kind]
    m = bpy.data.materials.new("W_metal_" + kind)
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 40.0
    nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    vr = nt.nodes.new("ShaderNodeMapRange")
    vr.inputs["To Min"].default_value = 0.55
    vr.inputs["To Max"].default_value = 1.0
    L.new(nz.outputs["Fac"], vr.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    mul.inputs[0].default_value = _LIN(base)
    L.new(vr.outputs["Result"], mul.inputs["Scale"])
    wa = nt.nodes.new("ShaderNodeAttribute")
    wa.attribute_name = "wear"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["B"].default_value = (*_LIN((0.30, 0.26, 0.20)), 1)
    fm = nt.nodes.new("ShaderNodeMath")
    fm.operation = "MULTIPLY"
    fm.inputs[1].default_value = 0.6
    L.new(wa.outputs["Fac"], fm.inputs[0])
    L.new(fm.outputs[0], mix.inputs["Factor"])
    L.new(mul.outputs["Vector"], mix.inputs["A"])
    L.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 1.0
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = rough - 0.12
    rr.inputs["To Max"].default_value = rough + 0.2
    L.new(nz.outputs["Fac"], rr.inputs["Value"])
    L.new(rr.outputs["Result"], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.15
    bp.inputs["Distance"].default_value = 0.002
    nz2 = nt.nodes.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 12.0
    L.new(tc.outputs["Generated"], nz2.inputs["Vector"])
    L.new(nz2.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _MATS[key] = m
    return m


def mail_material():
    """Riveted ring mail (lorica hamata): tileable ring height map at 8 mm ring pitch on the UVs."""
    key = ("mail",)
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    m = bpy.data.materials.new("W_mail")
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    b = nt.nodes["Principled BSDF"]
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    mp = nt.nodes.new("ShaderNodeMapping")
    rpm = 1.0 / 0.0085 / 8          # tiles per metre (8 rings per tile, 8.5 mm pitch)
    mp.inputs["Scale"].default_value = (rpm, rpm, 1)
    L.new(uv.outputs["UV"], mp.inputs["Vector"])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = _np_image("W_mail", mail_image(), noncolor=True)
    t.interpolation = "Cubic"
    L.new(mp.outputs["Vector"], t.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    L.new(t.outputs["Color"], sep.inputs["Color"])
    # gaps between rings are dark; rings are worn bright on the tops
    col = nt.nodes.new("ShaderNodeMapRange")
    col.inputs["To Min"].default_value = 0.10
    col.inputs["To Max"].default_value = 0.50
    L.new(sep.outputs["Red"], col.inputs["Value"])
    wa = nt.nodes.new("ShaderNodeAttribute")
    wa.attribute_name = "wear"
    rust = nt.nodes.new("ShaderNodeMix")
    rust.data_type = "RGBA"
    L.new(col.outputs["Result"], rust.inputs["A"])
    rust.inputs["B"].default_value = (*_LIN((0.30, 0.20, 0.13)), 1)
    fm = nt.nodes.new("ShaderNodeMath")
    fm.operation = "MULTIPLY"
    fm.inputs[1].default_value = 0.35
    L.new(wa.outputs["Fac"], fm.inputs[0])
    L.new(fm.outputs[0], rust.inputs["Factor"])
    L.new(rust.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.85
    rgh = nt.nodes.new("ShaderNodeMapRange")
    rgh.inputs["To Min"].default_value = 0.70
    rgh.inputs["To Max"].default_value = 0.45
    L.new(sep.outputs["Red"], rgh.inputs["Value"])
    L.new(rgh.outputs["Result"], b.inputs["Roughness"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.55
    bp.inputs["Distance"].default_value = 0.003
    L.new(sep.outputs["Red"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _MATS[key] = m
    return m


def thorn_material():
    key = ("thorn",)
    if key in _MATS and _MATS[key].name in bpy.data.materials:
        return _MATS[key]
    m = bpy.data.materials.new("W_thornwood")
    m.use_nodes = True
    nt = m.node_tree
    L = nt.links
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (30, 30, 30)
    L.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 8
    nz.inputs["Distortion"].default_value = 0.6
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (*_LIN((0.11, 0.08, 0.055)), 1)
    cr.color_ramp.elements[1].color = (*_LIN((0.33, 0.27, 0.20)), 1)
    L.new(nz.outputs["Fac"], cr.inputs["Fac"])
    L.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.6
    bp.inputs["Distance"].default_value = 0.001
    L.new(nz.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _MATS[key] = m
    return m


# ----------------------------------------------------------------------------------------------
# Garment object finishing (weights, uv, attributes, modifiers, parenting)
# ----------------------------------------------------------------------------------------------
def _coll_of(person):
    cs = person.body.users_collection
    return cs[0] if cs else bpy.context.scene.collection


def finish_garment(person, B, name, V, F, part, material, rgb, weights=None, uv=None, attrs=None,
                   thickness=0.003, subdiv=0, detail="hero", pin=None, skirt=None):
    """Create the garment object in armature space, parent to rig, armature modifier, solidify."""
    rig = person.rig
    ob = make_mesh("%s_%s" % (person.body.name, name), V, F, _coll_of(person))
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    # UVs (per loop) given per-vertex (u,v) + optional per-face override list
    if uv is not None:
        uvl = me.uv_layers.new(name="UVMap")
        lv = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", lv)
        if isinstance(uv, tuple):        # (per-vertex uv, per-loop fixer)
            UV = uv[1](me, uv[0])
        else:
            UV = uv[lv]
        uvl.data.foreach_set("uv", UV.astype(np.float32).ravel())
    for an, arr in (attrs or {}).items():
        at = me.attributes.new(an, "FLOAT", "POINT")
        at.data.foreach_set("value", np.asarray(arr, np.float32))
    # weights
    if weights is not None:
        names = B.bone_names
        used = np.nonzero(weights.max(0) > 0.001)[0]
        for bi in used:
            g = ob.vertex_groups.new(name=names[bi])
            col = weights[:, bi]
            nz = np.nonzero(col > 0.004)[0]
            q = np.round(col[nz] * 100).astype(np.int32)
            order = np.argsort(q, kind="stable")
            qs = q[order]
            cuts = np.nonzero(np.diff(qs))[0] + 1
            for grp in np.split(order, cuts):
                if len(grp):
                    g.add(nz[grp].tolist(), float(q[grp[0]]) / 100.0, "REPLACE")
    if pin is not None:
        g = ob.vertex_groups.new(name="pin")
        for w in np.unique(np.round(pin, 2)):
            if w <= 0:
                continue
            idx = np.nonzero(np.round(pin, 2) == w)[0]
            g.add(idx.tolist(), float(w), "REPLACE")
    ob.parent = rig
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Identity(4)
    if weights is not None:
        am = ob.modifiers.new("Armature", "ARMATURE")
        am.object = rig
        am.use_deform_preserve_volume = False
    if thickness:
        so = ob.modifiers.new("Solidify", "SOLIDIFY")
        so.thickness = thickness
        so.offset = -1
        so.use_even_offset = False       # even offset explodes on sliver faces at cut edges
        so.use_quality_normals = True
        so.use_rim = True
    if subdiv and detail == "hero":
        sd = ob.modifiers.new("Subdivision", "SUBSURF")
        sd.levels = 0
        sd.render_levels = subdiv
    if material is not None:
        me.materials.append(material)
    ob.color = (*rgb, 1)
    ob["wardrobe"] = part
    ob["wardrobe_person"] = person.body.name
    return ob


# ----------------------------------------------------------------------------------------------
# Folds (procedural)
# ----------------------------------------------------------------------------------------------
def _n1(x, seed):
    return noise.noise(Vector((x, seed * 1.37, 0.5 + seed * 0.11)))


def _n3(p, seed=0.0):
    return noise.noise(Vector((p[0], p[1], p[2] + seed * 13.1)))


# ----------------------------------------------------------------------------------------------
# Garment generators
# ----------------------------------------------------------------------------------------------
K_ANG = 72


def _column_center(B):
    """centre (x,y) of the body column as function of z (spine/legs)."""
    sp = [B.head("spine05"), B.head("spine04"), B.head("spine03"), B.head("spine02"), B.head("spine01"),
          B.head("neck01")]
    zs = np.array([p[2] for p in sp])
    ys = np.array([p[1] for p in sp])

    def f(z):
        return (0.0, float(np.interp(z, zs, ys)))
    return f


def tunic_shell(B, rnd, hem_z, top_z=None, belt_z=None, ease=0.03, flare=0.08, blouse=0.025,
                sleeves="short", sleeve_ease=0.025, sleeve_flare=0.03, voxel=0.014, neck_r=0.012,
                neck_front=0.025, fold_amp=0.012, loose=0.7, include_arms_in_column=False, extra_top=0.0):
    """Generic tunic/robe body: torso column + sleeves, voxel-united, cut and smoothed.
    Returns dict(V, F, E, region, info...)."""
    t0 = time.time()
    ang = np.linspace(-math.pi, math.pi, K_ANG, endpoint=False)
    neck_base = B.head("neck01")
    top_z = top_z if top_z is not None else neck_base[2] + 0.025
    regs = {RID[r] for r in ("torso", "hips", "neck", "shoulder_L", "shoulder_R", "thigh_L", "thigh_R",
                            "shin_L", "shin_R")}
    if include_arms_in_column:
        regs |= ARM_L | ARM_R
    P = B.pts(regs, zmax=top_z + 0.02)
    # neck points only below the neck base (+ a bit)
    neckm = np.isin(B.breg, [RID["neck"], RID["head"]])
    P = P[~((P[:, 2] > neck_base[2] + 0.03) & (np.abs(P[:, 0]) < 0.09))]
    if B.layers:
        Lp = layer_points(B)
        Lreg, _ = B.nearest_region(Lp)
        Lp = Lp[~np.isin(Lreg, list(ARM_L | ARM_R)) & (Lp[:, 2] <= top_z + 0.02)]
        P = np.vstack([P, Lp])
    step = 0.012
    zs = np.arange(hem_z - 0.04, top_z + 1e-6, step)
    cf = _column_center(B)
    Cs, Rh = slice_rings(P, zs, ang, center_fn=cf, dz=0.010)
    Rh = circ_smooth(Rh, 2)
    M = len(zs)
    R = Rh.copy()
    crotch = B.head("upperleg02.L")[2] + 0.02
    chest_z = B.head("spine01")[2]
    if belt_z is None:
        # no belt: fabric falls from the chest/shoulder-blade line (partial running max from the top)
        run = Rh.copy()
        for i in range(M - 2, -1, -1):
            if zs[i] < chest_z + 0.08:
                run[i] = np.maximum(Rh[i], run[i + 1])
        R = Rh + loose * (run - Rh)
    else:
        run = Rh.copy()
        for i in range(M - 2, -1, -1):
            if belt_z + 0.04 < zs[i] < chest_z + 0.08:
                run[i] = np.maximum(Rh[i], run[i + 1])
        Rup = Rh + loose * (run - Rh)
        # below the belt: hang from hips (running max downwards)
        run2 = Rh.copy()
        ib = np.searchsorted(zs, belt_z)
        for i in range(min(ib, M - 1) - 1, -1, -1):
            run2[i] = np.maximum(Rh[i], run2[i + 1])
        R = np.where(zs[:, None] > belt_z, Rup, run2)
    # ease profile
    E = np.full(M, ease)
    if belt_z is not None:
        d = zs - belt_z
        cinch = np.exp(-(d / 0.022) ** 2)
        E = E * (1 - 0.85 * cinch)
        # blouse above the belt (sags over it): front/back more than sides
        bl = np.clip(d / 0.03, 0, 1) * np.clip(1 - (d - 0.03) / 0.10, 0, 1) * (d > 0)
        side = 0.6 + 0.4 * np.abs(np.sin(ang))[None, :]
        R = R + blouse * bl[:, None] * side
    # flare towards the hem
    z_top_skirt = belt_z if belt_z is not None else crotch + 0.12
    fl = np.clip((z_top_skirt - zs) / max(0.05, z_top_skirt - hem_z), 0, 1) ** 1.3
    E = E + flare * fl
    # shoulders: cloth rests on the shoulders -> little horizontal ease on the shoulder slope
    sh_z = B.head("upperarm01.L")[2]
    E = E * np.clip((top_z - zs) / max(0.05, top_z - sh_z + 0.06), 0.12, 1)
    R = R + E[:, None]
    R = zsmooth(R, 2)
    R = circ_smooth(R, 1)
    rings = []
    for i, z in enumerate(zs):
        c = Cs[i]
        rings.append(np.stack([c[0] + R[i] * np.cos(ang), c[1] + R[i] * np.sin(ang), np.full(K_ANG, z)], 1))
    parts = [loft_closed(rings)]
    # sleeves
    sleeve_info = {}
    if sleeves and sleeves != "none":
        for side in ("L", "R"):
            sp = _sleeve_solid(B, side, sleeves, sleeve_ease, sleeve_flare)
            parts.append((sp["V"], sp["F"]))
            sleeve_info[side] = sp
    V, F, E_ = voxel_union(parts, voxel)
    # cuts
    bm = to_bm(V, F)
    bm_cut_plane(bm, (0, 0, hem_z), (0, 0, -1))
    for side, sp in sleeve_info.items():
        bm_cut_plane(bm, sp["end"], sp["dir"], center_mask=lambda C_, sp=sp: dist_polyline(C_, sp["chain"]) < sp["rmax"] + 0.03)
    _cut_neck(bm, B, neck_r, neck_front)
    bm_clean(bm, voxel)
    bm_remove_loose(bm)
    bm_keep_largest(bm)
    V, F, E_ = from_bm(bm)
    bm.free()
    return dict(V=V, F=F, E=E_, zs=zs, Cs=Cs, sleeves=sleeve_info, hem_z=hem_z, belt_z=belt_z, time=time.time() - t0)


def _sleeve_chain(B, side, kind):
    s = "." + side
    pts = [B.head("upperarm01" + s), B.head("upperarm02" + s), B.tail("upperarm02" + s)]
    if kind in ("long", "wrist", "3q"):
        pts += [B.tail("lowerarm01" + s), B.tail("lowerarm02" + s)]
    return [np.array(p) for p in pts]


def _sleeve_solid(B, side, kind, ease, flare):
    """Tube around the arm from inside the shoulder to beyond the sleeve end."""
    s = "." + side
    sh = B.head("upperarm01" + s)
    el = B.tail("upperarm02" + s)
    wr = B.tail("lowerarm02" + s)
    up_dir = (el - sh) / np.linalg.norm(el - sh)
    if kind == "short":
        end = sh + (el - sh) * 0.55
        chain = [sh - up_dir * 0.06, end + up_dir * 0.05]
    elif kind == "elbow":
        end = el + (el - sh) * 0.04
        chain = [sh - up_dir * 0.06, end + up_dir * 0.05]
    elif kind == "3q":
        end = el + (wr - el) * 0.5
        fd = (wr - el) / np.linalg.norm(wr - el)
        chain = [sh - up_dir * 0.06, el, end + fd * 0.05]
    else:  # long
        end = wr - (wr - el) * 0.03
        fd = (wr - el) / np.linalg.norm(wr - el)
        chain = [sh - up_dir * 0.06, el, end + fd * 0.05]
    arm = ARM_L if side == "L" else ARM_R
    P = B.pts(arm | {RID["shoulder_" + side]})
    if B.layers:
        Lp = layer_points(B, 2)
        Lreg, _ = B.nearest_region(Lp)
        P = np.vstack([P, Lp[np.isin(Lreg, list(arm))]])
    # resample chain
    pts = []
    for a, b in zip(chain[:-1], chain[1:]):
        n = max(2, int(np.linalg.norm(b - a) / 0.012))
        for t in np.linspace(0, 1, n, endpoint=False):
            pts.append(a + (b - a) * t)
    pts.append(chain[-1])
    pts = np.array(pts)
    ang = np.linspace(-math.pi, math.pi, 48, endpoint=False)
    L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    total = L[-1]
    rings, radii = [], []
    for i, p in enumerate(pts):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        u, v = frame_of(d)
        rel = P - p
        h = rel @ d
        S = rel[np.abs(h) < 0.012]
        if len(S) >= 6:
            Q = np.stack([S @ u, S @ v], 1)
            H = hull2d(Q)
            r = ray_radii(H, np.zeros(2), ang)
        else:
            r = radii[-1] if radii else np.full(len(ang), 0.05)
        radii.append(r)
    radii = np.array(radii)
    # the first stations sit inside the shoulder: use the radii from the deltoid
    k0 = int(np.searchsorted(L, 0.07))
    radii[:k0] = radii[k0]
    # partial running max along the sleeve (fabric doesn't follow the arm inwards) + ease/flare
    for i in range(1, len(radii)):
        radii[i] = np.maximum(radii[i], radii[i - 1] * 0.93)
    t = L / max(total, 1e-6)
    low = (1 - np.sin(ang)) / 2                          # 0 on top of the arm .. 1 underneath (hangs)
    radii = radii + ease * (0.15 + 0.85 * low)[None, :] + flare * (t[:, None] ** 1.2) * (0.25 + 0.75 * low)[None, :]
    # the part inside the shoulder must not bulge above the shoulder line
    radii[:k0] = np.minimum(radii[:k0], radii[k0])
    radii = circ_smooth(zsmooth(radii, 2), 2)
    for i, p in enumerate(pts):
        d = pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]
        d /= np.linalg.norm(d)
        u, v = frame_of(d)
        r = radii[i]
        rings.append(p + np.outer(r * np.cos(ang), u) + np.outer(r * np.sin(ang), v))
    V, F = loft_closed(rings)
    end_dir = pts[-1] - pts[-2]
    end_dir /= np.linalg.norm(end_dir)
    sx = 1 if side == "L" else -1
    return dict(V=V, F=F, end=end, dir=end_dir, chain=pts, L=L, rmax=float(radii.max()))


def _cut_neck(bm, B, r_add, front):
    """Remove a rounded neck hole (elliptic cylinder around the neck, deeper at the front)."""
    nb = B.head("neck01")
    # neck radius from the body
    P = B.pts({RID["neck"]}, zmin=nb[2] - 0.01, zmax=nb[2] + 0.04)
    if len(P) > 6:
        c = P[:, :2].mean(0)
        rx = (P[:, 0].max() - P[:, 0].min()) / 2
        ry = (P[:, 1].max() - P[:, 1].min()) / 2
    else:
        c, rx, ry = nb[:2], 0.06, 0.06
    rx, ry = rx + r_add + 0.01, ry + r_add
    cy_front = front
    zmin = nb[2] - 0.12

    def inside(co):
        if co.z < zmin:
            return False
        dx = (co.x - c[0]) / rx
        dyv = co.y - c[1]
        dy = dyv / (ry + (cy_front if dyv < 0 else 0))
        return dx * dx + dy * dy < 1.0
    dele = [v for v in bm.verts if inside(v.co)]
    if dele:
        bmesh.ops.delete(bm, geom=dele, context="VERTS")
    # snap boundary verts near the neck onto the ellipse
    for v in bm.verts:
        if v.is_boundary and v.co.z > zmin:
            dx, dyv = v.co.x - c[0], v.co.y - c[1]
            ryy = ry + (cy_front if dyv < 0 else 0)
            q = math.sqrt((dx / rx) ** 2 + (dyv / ryy) ** 2)
            if 0.6 < q < 1.4:
                v.co.x = c[0] + dx / q
                v.co.y = c[1] + dyv / q


# ----------------------------------------------------------------------------------------------
# Post-processing shared by tunic-like garments
# ----------------------------------------------------------------------------------------------
def _cyl_coords(V, B, cf):
    c = np.array([cf(z) for z in V[:, 2]])
    d = V[:, :2] - c
    th = np.arctan2(d[:, 1], d[:, 0])
    r = np.linalg.norm(d, axis=1)
    return th, r, c


def _shape(f, e=0.75):
    return np.sign(f) * np.abs(f) ** e


def garment_post(B, G, rnd, fold_amp=0.014, pleat_amp=0.006, sleeve_fold=0.006, smooth_iters=6, gap=0.006,
                 drag=0.004):
    """Smoothing, procedural folds, push-out. Fills G['region'] (nearest body region), updates G['V']."""
    V, F, E = G["V"], G["F"], G["E"]
    T = tri_fan(F)
    G["T"] = T
    bnd = boundary_mask(len(V), F)
    V = laplacian(V, E, iters=smooth_iters, weight=np.where(bnd, 0.3, 1.0))
    V = smooth_boundary(V, F, 3)
    reg, dist = B.nearest_region(V)
    G["region"] = reg
    is_arm = np.isin(reg, list(ARM_L | ARM_R))
    N = vertex_normals(V, F, T)
    cf = _column_center(B)
    th, r, c = _cyl_coords(V, B, cf)
    seed = rnd.random() * 100
    hem_z = G["hem_z"]
    belt_z = G.get("belt_z")
    chest = B.head("spine01")[2]
    top_skirt = belt_z if belt_z is not None else chest - 0.05
    disp = np.zeros(len(V))
    n1 = _n1
    for i in np.nonzero(~is_arm)[0]:
        p = V[i]
        z = p[2]
        s_ = th[i] * 0.21                               # arc length (m)
        hang = min(1.0, max(0.0, (top_skirt - z) / max(0.1, top_skirt - hem_z)))
        # big hanging folds (wavelength ~10-13 cm), meandering slowly with height
        w1 = s_ / 0.11 + 0.5 * n1(z * 1.6, seed + 3)
        f = n1(w1, seed) + 0.45 * n1(w1 * 2.3 + 5, seed + 1)
        d = fold_amp * (0.15 + 0.85 * hang ** 0.7) * 1.7 * f
        if belt_z is not None:
            dz = z - belt_z
            # gathered pleats under the belt fading downwards, bunching above it
            pa = pleat_amp * (math.exp(-max(0, -dz) / 0.22) if dz < 0 else math.exp(-dz / 0.05))
            w2 = s_ / 0.035 + 0.3 * n1(z * 4, seed + 9)
            d += pa * 1.6 * n1(w2, seed + 5)
            if 0 < dz < 0.12:
                d += 0.004 * (1 - dz / 0.12) * _n3((p[0] * 9, p[1] * 9, z * 35), seed)
        if z > top_skirt:
            # diagonal drag folds on the torso
            d += drag * 1.5 * n1((s_ * 1.0 + (chest + 0.1 - z) * 0.8 * np.sign(p[0])) / 0.06, seed + 13)
        disp[i] = d
    for side, sp in G.get("sleeves", {}).items():
        arm = ARM_L if side == "L" else ARM_R
        for i in np.nonzero(np.isin(reg, list(arm)))[0]:
            p = V[i]
            disp[i] = sleeve_fold * 1.4 * _n3((p[0] * 16, p[1] * 16, p[2] * 10), seed + 11)
    disp = _shape(smooth_field(disp, E, iters=2), 0.8)
    V = V + N * disp[:, None]
    V, moved = push_out(V, B, gap)
    V = laplacian(V, E, iters=1, weight=np.where(bnd, 0.0, 1.0))
    V, moved = push_out(V, B, gap)
    G["V"] = V
    G["bnd"] = bnd
    return G


def garment_weights(B, G, skirt_below=None, smooth=5, skirt_smooth=10, arms=True, only=None, layers=True):
    """Bone weights. Arm-region verts (sleeves) sample the full body; everything else samples the body
    WITHOUT arms ('core'), so hems/belts never follow the hands. Verts below `skirt_below` (z) blend to
    MPFB's helper-skirt weights (no stretching between the legs). only: restrict to a bone-name subset."""
    V, E = G["V"], G["E"]
    reg = G.get("region")
    if reg is None:
        reg, _ = B.nearest_region(V)
    arm = np.isin(reg, list(ARM_L | ARM_R)) if arms else np.zeros(len(V), bool)
    W = np.zeros((len(V), len(B.bone_names)), np.float32)
    if arm.any():
        W[arm], _ = B.sample_weights(V[arm], "body")
    if (~arm).any():
        W[~arm], _ = B.sample_weights(V[~arm], "core")
    if skirt_below is not None:
        sk = (V[:, 2] < skirt_below) & ~arm
        if sk.any():
            Ws, _ = B.sample_weights(V[sk], "skirt")
            t = np.clip((skirt_below - V[sk, 2]) / 0.06, 0, 1)[:, None]
            W[sk] = W[sk] * (1 - t) + Ws * t
        wgt = np.where(V[:, 2] < skirt_below, 1.0, 0.35)
        cols = np.nonzero(W.max(0) > 1e-4)[0]
        W[:, cols] = smooth_field(W[:, cols], E, iters=skirt_smooth, weight=wgt)
    if B.layers and layers:
        # on top of an inner garment: follow it (same weights => no interpenetration when posed)
        bd = np.array([B.bvh["body"][0].find_nearest(Vector(p))[3] or 9.0 for p in V])
        Wl, dl = sample_layers(B, V, core=~arm)
        use = (dl < 0.05) & (dl < bd + 0.01)
        if use.any():
            t = np.clip((0.05 - dl[use]) / 0.02, 0, 1)[:, None]
            W[use] = W[use] * (1 - t) + Wl[use] * t
    if only is not None:
        keep = np.array([n in only for n in B.bone_names])
        W[:, ~keep] = 0
    cols = np.nonzero(W.max(0) > 1e-4)[0]
    W[:, cols] = smooth_field(W[:, cols], E, iters=smooth)
    W[W < 0.01] = 0
    s = W.sum(1)
    s[s == 0] = 1
    return (W / s[:, None]).astype(np.float32)


R_COL, R_SLV = 0.21, 0.07


def _chain_frames(pts):
    n = len(pts)
    D, U, Vv = [], [], []
    for j in range(n):
        d = pts[min(j + 1, n - 1)] - pts[max(j - 1, 0)]
        d = d / np.linalg.norm(d)
        u, v = frame_of(d)
        D.append(d)
        U.append(u)
        Vv.append(v)
    return np.array(D), np.array(U), np.array(Vv)


def sleeve_uv(V, sp, offset=3.0):
    pts, L = sp["chain"], sp["L"]
    Dd, Uu, Vv = _chain_frames(pts)
    j = np.linalg.norm(V[:, None, :] - pts[None, :, :], axis=2).argmin(1)
    rel = V - pts[j]
    a = np.arctan2((rel * Uu[j]).sum(1), (rel * Vv[j]).sum(1)) + math.pi     # seam under the arm
    t = L[j] + (rel * Dd[j]).sum(1)
    return np.stack([a * R_SLV + offset, t + offset], 1)


def uv_builder(Us, kind, pers):
    """Us: list of per-vertex UV arrays (one per projection), kind: per-vertex projection index,
    pers: u-period per projection (wrap seams). Returns (None, fn(me, _) -> per-loop UVs)."""
    Us = np.stack(Us)
    pers = np.asarray(pers, float)

    def build(me, _):
        lv = np.empty(len(me.loops), np.int64)
        me.loops.foreach_get("vertex_index", lv)
        ls = np.empty(len(me.polygons), np.int64)
        lt = np.empty(len(me.polygons), np.int64)
        me.polygons.foreach_get("loop_start", ls)
        me.polygons.foreach_get("loop_total", lt)
        fol = np.repeat(np.arange(len(ls)), lt)
        kl = kind[lv]
        cnt = np.zeros((len(ls), len(Us)))
        np.add.at(cnt, (fol, kl), 1)
        lk = cnt.argmax(1)[fol]
        out = Us[lk, lv].copy()
        per = pers[lk]
        u = out[:, 0]
        umin = np.minimum.reduceat(u, ls)[fol]
        umax = np.maximum.reduceat(u, ls)[fol]
        umean = (np.add.reduceat(u, ls) / lt)[fol]
        fix = ((umax - umin) > per / 2) & (u < umean)
        out[fix, 0] += per[fix]
        return out
    return (None, build)


def garment_uv(B, G):
    """Cylindrical UVs in metres: column around the body axis (seam at the back), sleeves around the
    arm axis (seam underneath)."""
    V = G["V"]
    reg = G["region"]
    cf = _column_center(B)
    th, r, c = _cyl_coords(V, B, cf)
    thb = np.mod(th - math.pi / 2, 2 * math.pi)
    Us = [np.stack([thb * R_COL, V[:, 2]], 1)]
    pers = [2 * math.pi * R_COL]
    kind = np.zeros(len(V), np.int64)
    for side, sp in G.get("sleeves", {}).items():
        arm = ARM_L if side == "L" else ARM_R
        Us.append(sleeve_uv(V, sp))
        pers.append(2 * math.pi * R_SLV)
        kind[np.isin(reg, list(arm))] = len(Us) - 1
    return uv_builder(Us, kind, pers)


def wear_attr(V, hem_z, rnd, amount=1.0, band=0.35):
    """Dust/dirt factor: strong near the hem, random patches elsewhere."""
    seed = rnd.random() * 50
    h = np.clip(1 - (V[:, 2] - hem_z) / band, 0, 1) ** 1.5
    n = np.array([_n3((p[0] * 3, p[1] * 3, p[2] * 3), seed) for p in V])
    return np.clip(0.55 * h + 0.25 * np.clip(n, 0, 1) + 0.08, 0, 1) * amount


# ----------------------------------------------------------------------------------------------
# Bands (belts, sashes, head bands) around an existing garment / body
# ----------------------------------------------------------------------------------------------
def band_rings(B, Vref, z, width, gap=0.003, center_fn=None, tilt=0.0, K=96, rows=5, bulge=0.002):
    """Rings for a band hugging the points Vref (garment verts) at height z (+tilt: dz per unit y)."""
    ang = np.linspace(-math.pi, math.pi, K, endpoint=False)
    cf = center_fn or _column_center(B)
    rings = []
    for j in range(rows):
        t = j / (rows - 1) - 0.5
        zz = z + t * width
        c = np.array(cf(zz))
        S = Vref[np.abs(Vref[:, 2] - (zz + tilt * (Vref[:, 1] - c[1]))) < 0.012]
        if len(S) < 6:
            S = Vref[np.abs(Vref[:, 2] - zz) < 0.03]
        H = hull2d(S[:, :2])
        R = circ_smooth(ray_radii(H, c, ang), 2) + gap + bulge * (1 - (2 * t) ** 2)
        rings.append(np.stack([c[0] + R * np.cos(ang), c[1] + R * np.sin(ang), zz + tilt * R * np.sin(ang)], 1))
    return rings, ang


def loft_open(rings, closed_u=True):
    M, K = len(rings), len(rings[0])
    V = np.concatenate(rings, 0)
    F = []
    for i in range(M - 1):
        a, b = i * K, (i + 1) * K
        for k in range(K if closed_u else K - 1):
            k2 = (k + 1) % K
            F.append((a + k, a + k2, b + k2, b + k))
    return V, F


# ----------------------------------------------------------------------------------------------
# Outfit parts - generic builders
# ----------------------------------------------------------------------------------------------
_DEBUG = bool(os.environ.get("WARDROBE_DEBUG"))
_T0 = [time.time()]
ANG = np.linspace(-math.pi, math.pi, K_ANG, endpoint=False)
MASK_LAYERS = True        # hide inner-garment areas fully covered by outer garments (no poke-through)
CORE = {RID[r] for r in ("torso", "hips", "neck", "shoulder_L", "shoulder_R", "thigh_L", "thigh_R", "shin_L", "shin_R")}


def _tick(label):
    if _DEBUG:
        import resource
        t = time.time()
        print("  [wardrobe] %-28s %.2fs  rss=%dMB" % (label, t - _T0[0], resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024), flush=True)
        _T0[0] = t


def _hem_height(B, length):
    knee = B.head("lowerleg01.L")[2]
    ankle = B.head("foot.L")[2]
    crotch = B.head("upperleg02.L")[2]
    if isinstance(length, (int, float)):
        return float(length)
    return {"thigh": crotch - 0.55 * (crotch - knee), "knee": knee + 0.01, "below_knee": knee - 0.07,
            "calf": knee - 0.45 * (knee - ankle), "ankle": ankle + 0.035, "floor": ankle - 0.01}[length]


def _sc(B):
    return B.height / 1.66


def _merge(parts):
    Vs, Fs, off = [], [], 0
    for Vp, Fp in parts:
        Vs.append(np.asarray(Vp, float))
        Fs += [tuple(i + off for i in f) for f in Fp]
        off += len(Vp)
    return np.vstack(Vs), Fs


def _weights_simple(B, V, F, skirt_below=None, smooth=4, arms=False, only=None):
    E = edges_of(F)
    reg, _ = B.nearest_region(V)
    return garment_weights(B, dict(V=V, E=E, region=reg), skirt_below=skirt_below, smooth=smooth, arms=arms, only=only)


def _surface_radius(Vref, c, z, theta, dz=0.012):
    S = Vref[np.abs(Vref[:, 2] - z) < dz]
    if len(S) < 6:
        S = Vref[np.abs(Vref[:, 2] - z) < 0.04]
    if len(S) < 3:
        return 0.15
    return float(ray_radii(hull2d(S[:, :2]), np.asarray(c), np.array([theta]))[0])


def column_solid(B, P, z0, z1, ease, center_fn=None, drape_below=None, loose=1.0, step=0.012, dz=0.010, zsm=2,
                 asm=1):
    """Closed loft of horizontal hull slices of points P between z0..z1 (+ ease (scalar, fn(zs) or (M,K))).
    drape_below: below this z the fabric falls from the widest part above (running max, * loose)."""
    zs = np.arange(z0, z1 + 1e-6, step)
    cf = center_fn or _column_center(B)
    Cs, Rh = slice_rings(P, zs, ANG, center_fn=cf, dz=dz)
    Rh = circ_smooth(Rh, 2)
    R = Rh.copy()
    if drape_below is not None:
        run = Rh.copy()
        for i in range(len(zs) - 2, -1, -1):
            if zs[i] < drape_below:
                run[i] = np.maximum(Rh[i], run[i + 1])
        R = Rh + loose * (run - Rh)
    E = ease(zs) if callable(ease) else np.full(len(zs), float(ease))
    E = np.asarray(E, float)
    R = R + (E[:, None] if E.ndim == 1 else E)
    R = circ_smooth(zsmooth(R, zsm), asm)
    rings = [np.stack([Cs[i][0] + R[i] * np.cos(ANG), Cs[i][1] + R[i] * np.sin(ANG), np.full(K_ANG, z)], 1)
             for i, z in enumerate(zs)]
    V, F = loft_closed(rings)
    return V, F, dict(zs=zs, Cs=Cs, R=R)


def shell(parts, voxel, cuts=()):
    V, F, E = voxel_union(parts, voxel)
    bm = to_bm(V, F)
    for c in cuts:
        c(bm)
    bm_clean(bm, voxel)
    bm_remove_loose(bm)
    bm_keep_largest(bm)
    V, F, E = from_bm(bm)
    bm.free()
    return dict(V=V, F=F, E=E)


def bm_clean(bm, voxel):
    """Merge near-coincident verts and dissolve degenerate faces left by cuts/snapping."""
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=voxel * 0.2)
    bmesh.ops.dissolve_degenerate(bm, dist=voxel * 0.05, edges=list(bm.edges))


def bm_delete_where(bm, fn):
    vs = list(bm.verts)
    if not vs:
        return
    co = np.array([v.co[:] for v in vs])
    m = fn(co)
    dele = [v for v, k in zip(vs, m) if k]
    if dele:
        bmesh.ops.delete(bm, geom=dele, context="VERTS")


def bm_snap_boundary(bm, fn):
    """fn(co (N,3)) -> new co (N,3) for boundary verts (NaN rows = leave)."""
    vs = [v for v in bm.verts if v.is_boundary]
    if not vs:
        return
    co = np.array([v.co[:] for v in vs])
    new = fn(co)
    for v, c in zip(vs, new):
        if not np.isnan(c[0]):
            v.co = c


def smooth_boundary(V, F, iters=3, lam=0.5):
    from collections import Counter
    cnt = Counter()
    for f in F:
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            cnt[(min(a, b), max(a, b))] += 1
    be = np.array([e for e, c in cnt.items() if c == 1], np.int64).reshape(-1, 2)
    if not len(be):
        return V
    V = V.copy()
    n = len(V)
    deg = np.bincount(be.ravel(), minlength=n)
    m = deg > 0
    for _ in range(iters):
        S = np.zeros_like(V)
        for k in range(3):
            S[:, k] = np.bincount(be[:, 0], V[be[:, 1], k], n) + np.bincount(be[:, 1], V[be[:, 0], k], n)
        V[m] += lam * (S[m] / deg[m, None] - V[m])
    return V


def post_shell(B, G, rnd, folds=(), smooth_iters=4, gap=0.006, bsmooth=2, push=True, layer_gap=None):
    """Generic: Taubin smoothing, boundary smoothing, fold displacement, push outside body + inner layers."""
    V, F, E = G["V"], G["F"], G["E"]
    T = tri_fan(F)
    G["T"] = T
    bnd = boundary_mask(len(V), F)
    V = laplacian(V, E, iters=smooth_iters, weight=np.where(bnd, 0.3, 1.0))
    if bsmooth:
        V = smooth_boundary(V, F, bsmooth)
    reg, _ = B.nearest_region(V)
    G["region"] = reg
    N = vertex_normals(V, F, T)
    disp = np.zeros(len(V))
    for f in folds:
        disp += f(V, N, reg)
    if folds:
        disp = _shape(smooth_field(disp, E, iters=2), 0.8)
        V = V + N * disp[:, None]
    if push:
        V, _ = push_out(V, B, gap, layer_gap=layer_gap)
        V = laplacian(V, E, iters=1, weight=np.where(bnd, 0.0, 1.0))
        V, _ = push_out(V, B, gap, layer_gap=layer_gap)
    G["V"] = V
    G["bnd"] = bnd
    return G


# ---- fold fields: f(V, N, reg) -> displacement along the normal (m) -------------------------------
def fold_hanging(B, rnd, top_z, hem_z, amp, wave=0.11, cf=None, min_frac=0.15):
    seed = rnd.random() * 100
    cf = cf or _column_center(B)

    def f(V, N, reg):
        th, r, c = _cyl_coords(V, B, cf)
        out = np.zeros(len(V))
        for i in range(len(V)):
            z = V[i, 2]
            hang = min(1.0, max(0.0, (top_z - z) / max(0.1, top_z - hem_z)))
            s_ = th[i] * 0.21
            w1 = s_ / wave + 0.5 * _n1(z * 1.6, seed + 3)
            out[i] = amp * 1.7 * (min_frac + (1 - min_frac) * hang ** 0.7) * (_n1(w1, seed) + 0.45 * _n1(w1 * 2.3 + 5, seed + 1))
        return out
    return f


def fold_along(rnd, normal, origin, amp, wave=0.06, zmin=-9.0, zmax=9.0, fade=0.06, warp=0.4):
    """Folds running parallel to a plane (e.g. the diagonal edge of a himation)."""
    seed = rnd.random() * 100
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    o = np.asarray(origin, float)

    def f(V, N, reg):
        t = (V - o) @ n
        out = np.zeros(len(V))
        for i in range(len(V)):
            z = V[i, 2]
            if z < zmin - fade or z > zmax + fade:
                continue
            w = min(1.0, (z - zmin + fade) / fade, (zmax + fade - z) / fade)
            q = t[i] / wave + warp * _n1(V[i, 0] * 3 + V[i, 1] * 2, seed + 2)
            out[i] = amp * 1.6 * w * _n1(q, seed)
        return out
    return f


def fold_radial(rnd, origin, amp, wave=0.30, reach=0.35, axes=((1, 0, 0), (0, 0, 1))):
    """Folds radiating from a point (knot, pin, gathered corner)."""
    seed = rnd.random() * 100
    o = np.asarray(origin, float)
    u = np.asarray(axes[0], float)
    v = np.asarray(axes[1], float)

    def f(V, N, reg):
        d = V - o
        dist = np.linalg.norm(d, axis=1)
        ang = np.arctan2(d @ v, d @ u)
        out = np.zeros(len(V))
        for i in range(len(V)):
            if dist[i] > reach:
                continue
            k = min(1.0, dist[i] / 0.05) * (1 - dist[i] / reach)
            out[i] = amp * 1.6 * k * _n1(ang[i] / wave + 0.3 * _n1(dist[i] * 8, seed + 1), seed)
        return out
    return f


def fold_crumple(rnd, amp, freq=12.0, zmin=-9.0, zmax=9.0):
    seed = rnd.random() * 100

    def f(V, N, reg):
        out = np.zeros(len(V))
        for i in range(len(V)):
            p = V[i]
            if zmin <= p[2] <= zmax:
                out[i] = amp * 1.4 * _n3((p[0] * freq, p[1] * freq, p[2] * freq * 0.7), seed)
        return out
    return f


def column_uv(B, G, cf=None):
    """Cylindrical UVs (metres) around the body (or cf) axis; sleeves (G['sleeves']) around the arm."""
    V = G["V"]
    reg = G.get("region")
    if reg is None:
        reg, _ = B.nearest_region(V)
    cf = cf or _column_center(B)
    th, r, c = _cyl_coords(V, B, cf)
    thb = np.mod(th - math.pi / 2, 2 * math.pi)
    Us = [np.stack([thb * R_COL, V[:, 2]], 1)]
    pers = [2 * math.pi * R_COL]
    kind = np.zeros(len(V), np.int64)
    for side, sp in G.get("sleeves", {}).items():
        arm = ARM_L if side == "L" else ARM_R
        Us.append(sleeve_uv(V, sp))
        pers.append(2 * math.pi * R_SLV)
        kind[np.isin(reg, list(arm))] = len(Us) - 1
    return uv_builder(Us, kind, pers)


def finalize(person, B, G, rnd, name, mat, rgb, detail, skirt_below=None, hem_z=None, wear=1.0, wear_band=0.35,
             thickness=0.003, uv=None, attrs=None, layer=True, only=None, smooth=6, arms=True, weights=None,
             mask_inner=True):
    if weights is None:
        weights = garment_weights(B, G, skirt_below=skirt_below, smooth=smooth, arms=arms, only=only)
    if uv is None:
        uv = column_uv(B, G)
    hz = hem_z if hem_z is not None else float(G["V"][:, 2].min())
    A = {"wear": wear_attr(G["V"], hz, rnd, amount=wear, band=wear_band), "hem": G["V"][:, 2] - hz}
    if attrs:
        A.update(attrs)
    ob = finish_garment(person, B, name, G["V"], G["F"], name, mat, rgb, weights=weights, uv=uv, attrs=A,
                        thickness=thickness, detail=detail)
    if mask_inner and B.layers and MASK_LAYERS:
        mask_inner_layers(B, G)
    if layer:
        add_layer(B, G["V"], G["F"], name, weights, ob)
    return ob


def parent_to_bone(ob, rig, bone):
    """Rigid attachment: object verts are in armature space (rest); keeps them there at rest."""
    b = rig.data.bones[bone]
    for m in list(ob.modifiers):
        if m.type == "ARMATURE":
            ob.modifiers.remove(m)
    ob.vertex_groups.clear()
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = bone
    tail = b.matrix_local @ Matrix.Translation((0, b.length, 0))
    ob.matrix_parent_inverse = tail.inverted()
    ob.matrix_basis = Matrix.Identity(4)
    return ob


# ---- body masking -----------------------------------------------------------------------------
def hide_body(person, idx):
    """Hide body vertices (indices into person.body.data) with a MASK modifier 'WardrobeHide'."""
    idx = [int(i) for i in idx]
    if not idx:
        return
    body = person.body
    g = body.vertex_groups.get("wardrobe_hide") or body.vertex_groups.new(name="wardrobe_hide")
    g.add(idx, 1.0, "REPLACE")
    m = body.modifiers.get("WardrobeHide")
    if m is None:
        m = body.modifiers.new("WardrobeHide", "MASK")
        m.vertex_group = "wardrobe_hide"
        m.invert_vertex_group = True
        # before any subdivision so the hidden area is removed early
        names = [x.name for x in body.modifiers]
        target = next((i for i, x in enumerate(body.modifiers) if x.type == "SUBSURF"), len(names) - 1)
        try:
            body.modifiers.move(len(names) - 1, target)
        except Exception:
            pass


def hide_hair_above(person, B, point, normal):
    """Hide hair vertices on the positive side of a plane (hair under a turban / helmet / tight hood)."""
    p0, n = np.asarray(point, float), np.asarray(normal, float)
    for o in getattr(B, "hair_objs", []):
        if o.type != "MESH":
            continue
        Mo = np.array(person.rig.matrix_world.inverted() @ o.matrix_world)
        co = _np_co(o.data) @ Mo[:3, :3].T + Mo[:3, 3]
        idx = np.nonzero((co - p0) @ n > 0)[0]
        hide_verts(o, idx)


def hide_verts(ob, idx, group="wardrobe_hide"):
    """Hide vertices of a garment (or body) with an inverted MASK modifier placed after the Armature."""
    idx = [int(i) for i in idx]
    if not idx:
        return
    g = ob.vertex_groups.get(group) or ob.vertex_groups.new(name=group)
    g.add(idx, 1.0, "REPLACE")
    m = ob.modifiers.get("WardrobeHide")
    if m is None:
        m = ob.modifiers.new("WardrobeHide", "MASK")
        m.vertex_group = group
        m.invert_vertex_group = True
        n = len(ob.modifiers)
        tgt = next((i for i, x in enumerate(ob.modifiers) if x.type in ("SOLIDIFY", "SUBSURF", "CLOTH")), n - 1)
        try:
            ob.modifiers.move(n - 1, tgt)
        except Exception:
            pass


def mask_inner_layers(B, G, margin=0.07, reach=0.08):
    """Hide the parts of inner garment layers that are covered by the new garment G (kills poke-through
    of e.g. the tunic's shoulders through a veil or mantle when posed)."""
    V, T = G["V"], G.get("T")
    if T is None:
        T = tri_fan(G["F"])
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], T.tolist(), all_triangles=True)
    bnd = G.get("bnd")
    if bnd is None:
        bnd = boundary_mask(len(V), G["F"])
    bv = V[bnd]
    kd = KDTree(max(1, len(bv)))
    for i, p in enumerate(bv):
        kd.insert(p, i)
    kd.balance()
    for L in B.layers:
        ob = L.get("ob")
        if ob is None or L["V"] is V:
            continue
        LV = L["V"]
        LN = vertex_normals(LV, None, L["T"])
        hide = []
        for i in range(len(LV)):
            p, n = Vector(LV[i]), Vector(LN[i])
            hit = bvh.ray_cast(p + n * 0.001, n, reach)
            if hit[0] is None:
                continue
            if len(bv) and kd.find(p)[2] < margin:
                continue
            hide.append(i)
        # only hide if it is a sizeable region (avoid speckle holes)
        if len(hide) > 30:
            hide_verts(ob, hide)


def mask_covered(person, B, G, margin=0.08, reach=0.20, regions=None):
    """Hide body verts that lie well inside garment G (a ray along the body normal hits the garment and the
    vertex is >= margin from any garment opening). Prevents skin poking through and saves render time."""
    V, T = G["V"], G.get("T")
    if T is None:
        T = tri_fan(G["F"])
    bvh = BVHTree.FromPolygons([tuple(p) for p in V], T.tolist(), all_triangles=True)
    bnd = G.get("bnd")
    if bnd is None:
        bnd = boundary_mask(len(V), G["F"])
    bv = V[bnd]
    kd = KDTree(max(1, len(bv)))
    for i, p in enumerate(bv):
        kd.insert(p, i)
    kd.balance()
    hide = []
    for k in range(len(B.bco)):
        if regions is not None and B.breg[k] not in regions:
            continue
        p = Vector(B.bco[k])
        n = Vector(B.bnrm[k])
        hit = bvh.ray_cast(p + n * 0.001, n, reach)
        if hit[0] is None:
            continue
        if len(bv) and kd.find(p)[2] < margin:
            continue
        hide.append(B.bidx[k])
    hide_body(person, hide)
    return len(hide)


# ----------------------------------------------------------------------------------------------
# Outfit parts
# ----------------------------------------------------------------------------------------------
def part_belt(person, B, rnd, rgb, Vref, z, kind="sash", detail="hero", knot_theta=None, name="belt", stripes=False):
    """Belt on top of a garment (Vref = garment rest verts). kind: 'sash' (cloth girdle tied with a knot
    and two hanging ends), 'leather' (strap), 'cord' (thin rope)."""
    width = {"sash": 0.05, "leather": 0.036, "cord": 0.012}[kind]
    cf = _column_center(B)
    Vref = np.asarray(Vref)
    Vref = Vref[np.abs(Vref[:, 2] - z) < 0.12]
    rr, _ = B.nearest_region(Vref)
    Vref = Vref[~np.isin(rr, list(ARM_L | ARM_R))]
    rings, ang = band_rings(B, Vref, z, width, gap=0.0025, bulge=0.003 if kind == "sash" else 0.001)
    V, F = loft_open(rings)
    hemv = [np.full(len(V), 0.0) + np.repeat(np.linspace(0, width, len(rings)), len(rings[0]))]
    parts = [(V, F)]
    if kind in ("sash", "cord"):
        th0 = knot_theta if knot_theta is not None else -math.pi / 2 + rnd.uniform(0.35, 0.8) * rnd.choice((-1, 1))
        c = np.array(cf(z))
        r0 = _surface_radius(Vref, c, z, th0) + 0.012
        kc = np.array([c[0] + r0 * math.cos(th0), c[1] + r0 * math.sin(th0), z])
        ks = []
        for a in np.linspace(0, math.pi, 10):
            ks.append(np.array([[math.sin(a) * math.cos(b_), math.sin(a) * math.sin(b_), math.cos(a)]
                                for b_ in np.linspace(-math.pi, math.pi, 16, endpoint=False)]))
        rad = np.array([0.028, 0.016, 0.022]) if kind == "sash" else np.array([0.014, 0.01, 0.012])
        tdir = np.array([-math.sin(th0), math.cos(th0), 0])
        ndir = np.array([math.cos(th0), math.sin(th0), 0])
        Mk = np.stack([tdir, ndir, [0, 0, 1]], 1)
        Vk, Fk = loft_closed([kc + (row * rad) @ Mk.T for row in ks[1:-1]])
        parts.append((Vk, Fk))
        hemv.append(np.full(len(Vk), width / 2))
        ln = rnd.uniform(0.22, 0.34) if kind == "sash" else rnd.uniform(0.25, 0.4)
        wd = 0.032 if kind == "sash" else 0.008
        for e, dth in enumerate((-0.09, 0.07)):
            rows = []
            nz = 14
            for k in range(nz):
                t = k / (nz - 1)
                zz = z - 0.01 - t * ln * (1 - 0.15 * e)
                th = th0 + dth * (0.3 + t) + 0.05 * math.sin(t * 3 + e)
                cc = np.array(cf(zz))
                rr = _surface_radius(Vref, cc, zz, th) + 0.006 + 0.004 * e
                p0 = np.array([cc[0] + rr * math.cos(th), cc[1] + rr * math.sin(th), zz])
                td = np.array([-math.sin(th), math.cos(th), 0])
                w = wd * (1 - 0.25 * t)
                rows.append(np.array([p0 - td * w / 2, p0 - td * w / 6, p0 + td * w / 6, p0 + td * w / 2]))
            Ve, Fe = loft_open(rows, closed_u=False)
            parts.append((Ve, Fe))
            hemv.append(np.tile(np.linspace(0, width, 4), len(rows)))
    V, F = _merge(parts)
    W = _weights_simple(B, V, F, skirt_below=z - 0.03, smooth=3)
    th, r, c = _cyl_coords(V, B, cf)
    uv = uv_builder([np.stack([np.mod(th - math.pi / 2, 2 * math.pi) * R_COL, V[:, 2]], 1)],
                    np.zeros(len(V), np.int64), [2 * math.pi * R_COL])
    if kind == "leather":
        mat = fabric_material("leather")
    else:
        mat = fabric_material("wool" if kind == "sash" else "homespun", stripes=stripes)
    ob = finish_garment(person, B, name, V, F, name, mat, rgb, weights=W, uv=uv,
                        attrs={"wear": np.full(len(V), 0.3), "hem": np.concatenate(hemv)},
                        thickness=0.004 if kind != "cord" else 0.006, detail=detail)
    return ob


def part_tunic(person, B, rnd, rgb, fabric="linen", length="calf", sleeves="elbow", belt="sash", detail="hero",
               ease=0.03, flare=0.07, name="tunic", voxel=None, fold=0.014, wear=1.0, belt_rgb=None, loose=0.7,
               embroidery=False, mask=True, belt_z=None, thickness=0.0035, layer_gap=None, mat=None):
    voxel = voxel or (0.013 if detail == "hero" else 0.024)
    hem = _hem_height(B, length)
    if belt and belt_z is None:
        belt_z = B.head("spine04")[2] + 0.005
    if not belt:
        belt_z = None
    _tick("start " + name)
    G = tunic_shell(B, rnd, hem, belt_z=belt_z, ease=ease, flare=flare, sleeves=sleeves, voxel=voxel, loose=loose)
    _tick("shell")
    if layer_gap is not None:
        G = garment_post(B, G, rnd, fold_amp=fold, gap=max(0.006, layer_gap))
    else:
        G = garment_post(B, G, rnd, fold_amp=fold)
    _tick("post")
    mat = mat or fabric_material(fabric, embroidery=embroidery)
    G["T"] = tri_fan(G["F"])
    ob = finalize(person, B, G, rnd, name, mat, rgb, detail, skirt_below=(belt_z or B.head("spine05")[2]) - 0.02,
                  hem_z=hem, wear=wear, thickness=thickness, uv=garment_uv(B, G))
    ob["build_time"] = G["time"]
    _tick("finish")
    if mask:
        n = mask_covered(person, B, G, margin=0.09)
        _tick("mask %d" % n)
    out = [ob]
    if belt:
        brgb = belt_rgb or color(rnd.choice(CHOICES["belt"]), rnd, 0.05)
        out.append(part_belt(person, B, rnd, brgb, G["V"], belt_z, kind=belt if isinstance(belt, str) else "sash",
                             detail=detail, name=name + "_belt"))
        _tick("belt")
    return out, G


def _waist_z(B):
    return B.head("spine04")[2] + 0.005


def part_mantle(person, B, rnd, rgb, detail="hero", style="himation", length="calf", fabric="wool", name="mantle",
                voxel=None, fold=0.016, wear=1.0, side="L", embroidery=False, roll=True, mask=True, layer_gap=0.007):
    """Outer mantle. style 'himation' (wrapped diagonally: over the `side` shoulder, under the other arm,
    rolled diagonal edge), 'cloak' (hangs from both shoulders, open at the front), 'cape' (back + shoulders)."""
    voxel = voxel or (0.014 if detail == "hero" else 0.026)
    sc = _sc(B)
    hem = _hem_height(B, length)
    nb = B.head("neck01")
    top = nb[2] + 0.02
    chest = B.head("spine01")[2]
    sh_z = B.head("upperarm01.L")[2]
    waist = _waist_z(B)
    P = B.pts(CORE, zmax=top + 0.02)
    P = P[~((P[:, 2] > nb[2] + 0.03) & (np.abs(P[:, 0]) < 0.09))]
    if B.layers:
        Lp = layer_points(B)
        Lreg, _ = B.nearest_region(Lp)
        P = np.vstack([P, Lp[~np.isin(Lreg, list(ARM_L | ARM_R)) & (Lp[:, 2] < top)]])

    def ease(zs):
        e = 0.016 + 0.045 * np.clip((chest - zs) / max(0.1, chest - hem), 0, 1)
        return e * np.clip((top - zs) / (top - sh_z + 0.06), 0.18, 1)
    _tick("start " + name)
    Vc, Fc, info = column_solid(B, P, hem - 0.06, top, ease, drape_below=chest + 0.06, loose=0.85)
    parts = [(Vc, Fc)]
    sleeves = {}
    sides = [side] if style == "himation" else (["L", "R"] if style == "cloak" else [])
    for sd in sides:
        sp = _sleeve_solid(B, sd, "short", 0.03, 0.05) if style == "himation" else _sleeve_solid(B, sd, "elbow", 0.02, 0.06)
        parts.append((sp["V"], sp["F"]))
        sleeves[sd] = sp
    sx = 1 if side == "L" else -1
    slope = 0.07 if style == "himation" else 0.0
    cuts = [lambda bm: bm_cut_plane(bm, (0, 0, hem), (sx * slope, 0, -1))]
    for sd, sp in sleeves.items():
        cuts.append(lambda bm, sp=sp: bm_cut_plane(bm, sp["end"], sp["dir"],
                                                   center_mask=lambda C_, sp=sp: dist_polyline(C_, sp["chain"]) < sp["rmax"] + 0.03))
    plane = None
    if style == "himation":
        pR = np.array([-sx * 0.21 * sc, 0, waist + 0.06 * sc])
        pL = np.array([sx * 0.065 * sc, 0, nb[2] + 0.035 * sc])
        dx, dz = pL[0] - pR[0], pL[2] - pR[2]
        n = np.array([-dz * sx, 0, abs(dx)])
        n /= np.linalg.norm(n)
        plane = (pR, n)
        cuts.append(lambda bm: bm_cut_plane(bm, pR, n))
    else:
        cuts.append(lambda bm: _cut_neck(bm, B, 0.02, 0.03))
        if style == "cloak":
            # open front: gap widening downwards
            def front_open(co):
                cy = np.array([_column_center(B)(z)[1] for z in co[:, 2]])
                w = 0.035 * sc + np.clip(nb[2] - co[:, 2], 0, 2) * 0.12
                return (co[:, 1] < cy) & (np.abs(co[:, 0]) < w) & (co[:, 2] < nb[2] + 0.01)
            cuts.append(lambda bm: bm_delete_where(bm, front_open))
        elif style == "cape":
            zc = sh_z - 0.03 * sc

            def cape_cut(co):
                cf = _column_center(B)
                cy = np.array([cf(z)[1] for z in co[:, 2]])
                th = np.arctan2(co[:, 1] - cy, co[:, 0])
                below = (np.sin(th) < 0.30) & (co[:, 2] < zc)
                # the front only covers the shoulder tops (no collar across the chest)
                chest = (co[:, 1] < cy - 0.02) & (np.abs(co[:, 0]) < 0.11 * sc)
                return below | chest

            def cape_snap(co):
                out = np.full_like(co, np.nan)
                cf = _column_center(B)
                cy = np.array([cf(z)[1] for z in co[:, 2]])
                th = np.arctan2(co[:, 1] - cy, co[:, 0])
                m = (np.sin(th) < 0.36) & (np.abs(co[:, 2] - zc) < voxel * 1.6)
                out[m] = co[m]
                out[m, 2] = zc
                return out
            cuts.append(lambda bm: bm_delete_where(bm, cape_cut))
            cuts.append(lambda bm: bm_snap_boundary(bm, cape_snap))
    G = shell(parts, voxel, cuts)
    G["sleeves"] = sleeves
    _tick("shell")
    folds = [fold_hanging(B, rnd, waist + 0.05, hem, fold, wave=0.12, min_frac=0.25)]
    if plane is not None:
        folds.append(fold_along(rnd, plane[1], plane[0], 0.008, wave=0.055, zmin=waist - 0.05, zmax=top + 0.05))
    else:
        folds.append(fold_crumple(rnd, 0.003, 10, zmin=waist))
    G = post_shell(B, G, rnd, folds=folds, smooth_iters=5, gap=0.008, layer_gap=layer_gap, bsmooth=4)
    _tick("post")
    extra = []
    if style == "himation" and roll:
        rv = _edge_roll(B, G, plane, radius=0.011 * sc)
        if rv is not None:
            extra.append(rv)
    if extra:
        V, F = _merge([(G["V"], G["F"])] + extra)
        reg, _ = B.nearest_region(V)
        G2 = dict(V=V, F=F, E=edges_of(F), region=reg, sleeves=sleeves)
    else:
        G2 = G
    mat = fabric_material(fabric, embroidery=embroidery)
    G2["T"] = tri_fan(G2["F"])
    ob = finalize(person, B, G2, rnd, name, mat, rgb, detail, skirt_below=waist - 0.03, hem_z=hem - 0.03,
                  wear=wear, thickness=0.0045, uv=column_uv(B, G2))
    _tick("finish")
    if mask:
        mask_covered(person, B, G, margin=0.10)
    return [ob], G


def _edge_roll(B, G, plane, radius=0.011):
    """Tube of bunched fabric along the boundary loop lying on `plane` (himation diagonal edge)."""
    V, F = G["V"], G["F"]
    bnd = boundary_mask(len(V), F)
    o, n = plane
    d = (V - o) @ n
    idx = np.nonzero(bnd & (np.abs(d) < 0.015))[0]
    if len(idx) < 10:
        return None
    cf = _column_center(B)
    P = V[idx]
    c = np.array([cf(z) for z in P[:, 2]])
    th = np.arctan2(P[:, 1] - c[:, 1], P[:, 0] - c[:, 0])
    order = np.argsort(th)
    P = P[order]
    th = th[order]
    N = vertex_normals(V, F, G.get("T"))[idx][order]
    # resample uniformly
    seg = np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1)
    Lc = np.concatenate([[0], np.cumsum(seg)])
    total = Lc[-1]
    m = max(24, int(total / 0.012))
    ts = np.linspace(0, total, m, endpoint=False)
    PP = np.vstack([P, P[:1]])
    NN = np.vstack([N, N[:1]])
    Q = np.stack([np.interp(ts, Lc, PP[:, k]) for k in range(3)], 1)
    QN = np.stack([np.interp(ts, Lc, NN[:, k]) for k in range(3)], 1)
    # smooth the path a bit
    for _ in range(3):
        Q = (np.roll(Q, 1, 0) + 2 * Q + np.roll(Q, -1, 0)) / 4
    QN /= np.maximum(1e-6, np.linalg.norm(QN, axis=1))[:, None]
    rings = []
    for i in range(m):
        tg = Q[(i + 1) % m] - Q[i - 1]
        tg /= max(1e-9, np.linalg.norm(tg))
        nn = QN[i] - tg * (QN[i] @ tg)
        nn /= max(1e-9, np.linalg.norm(nn))
        bb = np.cross(tg, nn)
        rr = radius * (0.85 + 0.3 * _n1(i * 0.21, 4.2))
        cen = Q[i] + nn * rr * 0.55
        ring = [cen + rr * (math.cos(a) * nn + math.sin(a) * bb * 1.25) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
        rings.append(np.array(ring))
    Vt = np.concatenate(rings)
    Ft = []
    K = 8
    for i in range(m):
        a, b_ = i * K, ((i + 1) % m) * K
        for k in range(K):
            k2 = (k + 1) % K
            Ft.append((a + k, a + k2, b_ + k2, b_ + k))
    return Vt, Ft


def _head_axis(B):
    nb, hh, ht = B.head("neck01"), B.head("head"), B.tail("head")
    cfb = _column_center(B)
    zs = np.array([nb[2], hh[2], ht[2] + 0.1])
    ys = np.array([nb[1], hh[1] + 0.012, ht[1] + 0.02])

    def cf(z):
        if z < nb[2]:
            return cfb(z)
        return (0.0, float(np.interp(z, zs, ys)))
    return cf


def _head_points(B, with_hair=True):
    P = B.pts({RID["head"], RID["neck"]})
    if with_hair and len(B.hair):
        P = np.vstack([P, B.hair])
    return P


def part_headcover(person, B, rnd, rgb, kind="veil", detail="hero", length=None, fabric=None, name=None, voxel=None,
                   band=None, fold=0.010, wear=0.6):
    """Head coverings framing the face. kind: 'veil' (long, over shoulders and back), 'headcloth' (to the
    shoulders, with a head band), 'hood' (wool hood with short shoulder cape)."""
    name = name or kind
    fabric = fabric or {"veil": "linen", "headcloth": "linen", "hood": "wool"}[kind]
    length = length or {"veil": "back", "headcloth": "shoulder", "hood": "chest"}[kind]
    voxel = voxel or (0.010 if detail == "hero" else 0.018)
    sc = _sc(B)
    nb = B.head("neck01")
    eye_z = B.head("oculi01.L")[2]
    chin = B.tail("jaw")
    HP = _head_points(B)
    top = float(HP[:, 2].max())
    chest = B.head("spine01")[2]
    sh_z = B.head("upperarm01.L")[2]
    waist = _waist_z(B)
    # hem heights (back / side / front)
    z_back = {"shoulder": sh_z - 0.02, "chest": chest - 0.02, "back": chest - 0.16 * sc, "waist": waist - 0.02}[length]
    z_side = {"shoulder": sh_z + 0.0, "chest": sh_z - 0.05, "back": sh_z - 0.06, "waist": sh_z - 0.09}[length]
    z_front = {"shoulder": sh_z + 0.01, "chest": chest + 0.02, "back": chest - 0.01, "waist": chest - 0.10}[length]
    z_low = min(z_back, z_side, z_front)
    cf = _head_axis(B)
    P = np.vstack([HP, B.pts(CORE, zmax=nb[2] + 0.02)])
    if B.layers:
        Lp = layer_points(B)
        Lreg, _ = B.nearest_region(Lp)
        P = np.vstack([P, Lp[~np.isin(Lreg, list(ARM_L | ARM_R))]])
    P = P[P[:, 2] > z_low - 0.08]
    # include the tops of the shoulders/upper arms so the cloth drapes over the deltoids
    arms = B.pts({RID["upperarm_L"], RID["upperarm_R"], RID["shoulder_L"], RID["shoulder_R"]}, zmin=sh_z - 0.10)
    P = np.vstack([P, arms])
    e_head = 0.010 if kind != "hood" else 0.022

    def ease(zs):
        e = np.where(zs > chin[2], e_head, e_head + 0.010 * np.clip((chin[2] - zs) / 0.15, 0, 1))
        return e
    Vc, Fc, info = column_solid(B, P, z_low - 0.05, top + 0.03, ease, center_fn=cf, drape_below=eye_z, loose=1.0,
                                step=0.010)
    W0 = 0.074 * sc if kind != "hood" else 0.085 * sc
    z_mid = eye_z - 0.01 * sc
    z_open = eye_z + {"veil": 0.058, "headcloth": 0.050, "hood": 0.075}[kind] * sc
    k_open = {"veil": 0.95, "headcloth": 0.9, "hood": 0.35}[kind]

    def w_open(z):
        up = W0 * np.sqrt(np.clip(1 - ((z - z_mid) / (z_open - z_mid)) ** 2, 0, 1))
        dn = W0 + np.clip(chin[2] - z, 0, 9) * k_open
        return np.where(z > z_mid, up, dn)

    def hem_z(th):
        sn = np.sin(th)
        return z_side + (z_back - z_side) * np.clip(sn, 0, 1) ** 1.3 + (z_front - z_side) * np.clip(-sn, 0, 1) ** 1.3

    def cut_face(co):
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        return (co[:, 1] < cy) & (np.abs(co[:, 0]) < w_open(co[:, 2])) & (co[:, 2] < z_open)

    def cut_hem(co):
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        th = np.arctan2(co[:, 1] - cy, co[:, 0])
        return co[:, 2] < hem_z(th)

    def snap(co):
        out = np.full_like(co, np.nan)
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        th = np.arctan2(co[:, 1] - cy, co[:, 0])
        hz = hem_z(th)
        near_hem = np.abs(co[:, 2] - hz) < voxel * 1.6
        out[near_hem] = co[near_hem]
        out[near_hem, 2] = hz[near_hem]
        wf = w_open(co[:, 2])
        near_face = (~near_hem) & (co[:, 1] < cy) & (np.abs(np.abs(co[:, 0]) - wf) < voxel * 1.6) & (co[:, 2] < z_open)
        out[near_face] = co[near_face]
        out[near_face, 0] = np.sign(co[near_face, 0]) * wf[near_face]
        return out
    _tick("start " + name)
    G = shell([(Vc, Fc)], voxel, [lambda bm: bm_delete_where(bm, cut_face), lambda bm: bm_delete_where(bm, cut_hem),
                                  lambda bm: bm_snap_boundary(bm, snap)])
    _tick("shell")
    folds = [fold_hanging(B, rnd, chin[2], z_low, fold, wave=0.09, cf=cf, min_frac=0.1),
             fold_crumple(rnd, 0.0025, 14, zmin=chin[2] - 0.05)]
    if kind == "hood":
        folds.append(fold_crumple(rnd, 0.004, 7))
    G = post_shell(B, G, rnd, folds=folds, smooth_iters=4, gap=0.006, layer_gap=0.007, bsmooth=5)
    if kind == "hood":
        # peaked crown at the back
        V = G["V"]
        hb = np.clip((V[:, 2] - (top - 0.06)) / 0.06, 0, 1) * np.clip((V[:, 1] - cf(top)[1]) / 0.08 + 0.5, 0, 1)
        V[:, 2] += 0.03 * hb ** 2
        V[:, 1] += 0.03 * hb ** 2
    _tick("post")
    mat = fabric_material(fabric)
    G["T"] = tri_fan(G["F"])
    ob = finalize(person, B, G, rnd, name, mat, rgb, detail, hem_z=z_low, wear=wear, wear_band=0.2,
                  thickness=0.003 if fabric != "wool" else 0.005, uv=column_uv(B, G, cf), arms=True)
    out = [ob]
    if kind == "headcloth" or band:
        bz = eye_z + 0.045 * sc
        rings, _ = band_rings(B, G["V"], bz, 0.016, gap=0.002, center_fn=cf, tilt=-0.35, bulge=0.003)
        Vb, Fb = loft_open(rings)
        W = np.zeros((len(Vb), len(B.bone_names)), np.float32)
        W[:, B.bone_names.index("head")] = 1
        th, r, c = _cyl_coords(Vb, B, cf)
        uv = uv_builder([np.stack([np.mod(th, 2 * math.pi) * 0.1, Vb[:, 2] * 3], 1)], np.zeros(len(Vb), np.int64),
                        [2 * math.pi * 0.1])
        bcol = color(band if isinstance(band, (str, tuple)) else rnd.choice(["dark_brown", "charcoal", "madder", "indigo"]), rnd)
        ob2 = finish_garment(person, B, name + "_band", Vb, Fb, name + "_band", fabric_material("homespun"), bcol,
                             weights=W, uv=uv, attrs={"wear": np.full(len(Vb), 0.2), "hem": np.zeros(len(Vb))},
                             thickness=0.006, detail=detail)
        out.append(ob2)
    return out, G


def _loft_torus(rings):
    """rings: list (M) of closed rings (K,3); connects them cyclically (closed tube/torus)."""
    M, K = len(rings), len(rings[0])
    V = np.concatenate(rings)
    F = []
    for i in range(M):
        a, b = i * K, ((i + 1) % M) * K
        for k in range(K):
            k2 = (k + 1) % K
            F.append((a + k, a + k2, b + k2, b + k))
    return V, F


def part_turban(person, B, rnd, rgb, detail="hero", name="turban", fabric="fine_linen", wraps=6, voxel=None,
                hide_hair=True):
    """Priestly wrapped turban (mitznefet): several wraps of linen + a domed crown."""
    voxel = voxel or (0.008 if detail == "hero" else 0.014)
    sc = _sc(B)
    eye_z = B.head("oculi01.L")[2]
    HP = _head_points(B)
    top = float(HP[:, 2].max())
    cf = _head_axis(B)
    z0 = eye_z + 0.028 * sc
    parts = []
    hgt = 0.020 * sc
    for k in range(wraps):
        zk = z0 + k * (top + 0.02 - z0) / wraps * 0.85
        tilt = (0.25 + 0.12 * rnd.uniform(-1, 1)) * (1 if k % 2 == 0 else 0.6)
        c = np.array(cf(zk))
        rr = []
        for a in ANG:
            S = HP[np.abs(HP[:, 2] - (zk - tilt * 0.08 * math.sin(a))) < 0.012]
            rr.append(a)
        Cs, R = slice_rings(HP, np.array([zk]), ANG, center_fn=cf, dz=0.014)
        R = circ_smooth(R[0], 3) + 0.010 + 0.004 * math.sin(math.pi * k / max(1, wraps - 1)) + 0.002 * k
        rings = []
        for j, a in enumerate(ANG):
            radial = np.array([math.cos(a), math.sin(a), 0])
            cen = np.array([c[0], c[1], zk]) + radial * R[j]
            cen[2] += tilt * 0.06 * math.sin(a)                 # lower at the back (+y)
            ring = [cen + radial * 0.010 * math.cos(t) + np.array([0, 0, hgt * 0.8]) * math.sin(t)
                    for t in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
            rings.append(np.array(ring))
        parts.append(_loft_torus(rings))
    # domed crown
    Vd, Fd, _ = column_solid(B, HP, z0 + 0.03, top + 0.035, lambda zs: 0.014 + 0.012 * np.clip((zs - z0) / 0.08, 0, 1),
                             center_fn=cf, step=0.008)
    parts.append((Vd, Fd))
    G = shell(parts, voxel)
    G = post_shell(B, G, rnd, folds=[fold_crumple(rnd, 0.0025, 18)], smooth_iters=2, gap=0.004, push=True)
    W = np.zeros((len(G["V"]), len(B.bone_names)), np.float32)
    W[:, B.bone_names.index("head")] = 1
    G["T"] = tri_fan(G["F"])
    ob = finalize(person, B, G, rnd, name, fabric_material(fabric), rgb, detail, hem_z=z0, wear=0.2, wear_band=0.05,
                  thickness=0, uv=column_uv(B, G, cf), weights=W)
    parent_to_bone(ob, person.rig, "head")
    if hide_hair:
        hide_hair_above(person, B, (0, 0, z0 - 0.005), (0, 0, 1))
    return [ob], G


def part_crown(person, B, rnd, detail="hero", name="crown_of_thorns", strands=4, thorns=None):
    """Crown of twisted thorny vines sized to the head, sitting on the hair, slightly tilted (lower at the back)."""
    sc = _sc(B)
    eye_z = B.head("oculi01.L")[2]
    cf = _head_axis(B)
    HP = _head_points(B)
    zf = eye_z + 0.030 * sc         # front height (forehead, just above the brows)
    zb = eye_z + 0.000 * sc         # back height (occiput)
    c0 = np.array(cf(eye_z + 0.03))
    M = 120
    path = []
    for a in np.linspace(-math.pi, math.pi, M, endpoint=False):
        sn = math.sin(a)                          # +1 back, -1 front
        z = zf + (zb - zf) * (sn + 1) / 2
        S = HP[np.abs(HP[:, 2] - z) < 0.008]
        r = ray_radii(hull2d(S[:, :2]), c0, np.array([a]))[0] if len(S) > 5 else 0.09
        path.append((a, z, r))
    path = np.array(path)
    path[:, 2] = circ_smooth(path[:, 2], 3) + 0.002 * sc
    P = np.stack([c0[0] + path[:, 2] * np.cos(path[:, 0]), c0[1] + path[:, 2] * np.sin(path[:, 0]), path[:, 1]], 1)
    parts = []
    thorn_pts = []
    for s in range(strands):
        ph = s * 2 * math.pi / strands
        turns = 9 + s * 2
        rings = []
        pts_s = []
        for i in range(M):
            t = i / M
            tg = P[(i + 1) % M] - P[i - 1]
            tg /= np.linalg.norm(tg)
            radial = np.array([math.cos(path[i, 0]), math.sin(path[i, 0]), 0])
            up = np.cross(tg, radial)
            up /= np.linalg.norm(up)
            phi = 2 * math.pi * turns * t + ph + 0.6 * _n1(t * 9 + s, 3.3)
            off = 0.008 * sc * (math.cos(phi) * radial * 0.8 + math.sin(phi) * up * 1.3)
            cen = P[i] + off + radial * 0.006
            rad = (0.0042 + 0.0016 * _n1(t * 23 + s * 7, 1.1)) * sc
            nrm2 = np.cross(tg, up)
            ring = [cen + rad * (math.cos(b_) * nrm2 + math.sin(b_) * up) for b_ in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
            rings.append(np.array(ring))
            pts_s.append((cen, tg, radial, up, rad))
        parts.append(_loft_torus(rings))
        thorn_pts.append(pts_s)
    # thorns
    nth = thorns or (170 if detail == "hero" else 60)
    for k in range(nth):
        s = rnd.randrange(strands)
        i = rnd.randrange(M)
        cen, tg, radial, up, rad = thorn_pts[s][i]
        d = radial * rnd.uniform(-0.6, 1.0) + up * rnd.uniform(-1, 1) + tg * rnd.uniform(-0.6, 0.6)
        if rnd.random() < 0.18:
            d = -radial + up * rnd.uniform(-0.3, 0.3)   # some point inwards, into the scalp
        d /= np.linalg.norm(d)
        ln = rnd.uniform(0.010, 0.026) * sc
        base = cen + d * rad * 0.8
        tip = base + d * ln
        u_, v_ = frame_of(d)
        br = rnd.uniform(0.0012, 0.0022) * sc
        Vt = [base + br * (math.cos(a) * u_ + math.sin(a) * v_) for a in np.linspace(0, 2 * math.pi, 5, endpoint=False)]
        Vt.append(tip)
        Ft = [(i2, (i2 + 1) % 5, 5) for i2 in range(5)] + [tuple(range(4, -1, -1))]
        parts.append((np.array(Vt), Ft))
    V, F = _merge(parts)
    W = np.zeros((len(V), len(B.bone_names)), np.float32)
    W[:, B.bone_names.index("head")] = 1
    uv = uv_builder([V[:, :2] * 20], np.zeros(len(V), np.int64), [1e9])
    ob = finish_garment(person, B, name, V, F, name, thorn_material(), color("thorn"), weights=W, uv=uv,
                        attrs={"wear": np.full(len(V), 0.2), "hem": np.zeros(len(V))}, thickness=0, detail=detail)
    parent_to_bone(ob, person.rig, "head")
    return [ob]


def fold_swag(rnd, cy, half_w, sag, amp, wave=0.045, zmin=-9.0, zmax=9.0, front=True):
    """Catenary 'swag' folds: arcs sagging between the hips (front or back of a wrap)."""
    seed = rnd.random() * 100

    def f(V, N, reg):
        out = np.zeros(len(V))
        side = (V[:, 1] < cy) if front else (V[:, 1] >= cy)
        for i in np.nonzero(side)[0]:
            x, z = V[i, 0], V[i, 2]
            if not (zmin <= z <= zmax):
                continue
            u = min(1.0, abs(x) / half_w)
            k = (1 - u * u)
            ph = (z + sag * k) / wave + 0.25 * _n1(x * 9, seed)
            out[i] = amp * (0.25 + 0.75 * k) * math.cos(2 * math.pi * ph) * min(1.0, (zmax - z) / 0.03 + 0.3)
        return out
    return f


def part_loincloth(person, B, rnd, rgb, detail="hero", name="loincloth", knot_side=None, fold=0.006, voxel=None,
                   wear=0.8, flap=True):
    """Linen perizoma: wrapped low around the hips, swag folds sagging between the hips, the wrapped end
    overlapping in front as a flap, a twisted knot at one hip with two hanging ends."""
    voxel = voxel or (0.009 if detail == "hero" else 0.016)
    sc = _sc(B)
    ks = knot_side if knot_side is not None else rnd.choice((-1, 1))
    pel = B.head("spine05")
    crotch = B.head("upperleg02.L")[2]
    knee = B.head("lowerleg01.L")[2]
    ztop = pel[2] + 0.030 * sc
    zbot = crotch - 0.40 * (crotch - knee)
    P = B.pts({RID["hips"], RID["torso"], RID["thigh_L"], RID["thigh_R"]}, zmin=zbot - 0.08, zmax=ztop + 0.05)

    def ease(zs):
        return 0.007 + 0.026 * np.clip((ztop - 0.03 - zs) / (ztop - zbot), 0, 1) ** 1.3
    Vc, Fc, info = column_solid(B, P, zbot - 0.07, ztop + 0.04, ease, drape_below=crotch + 0.05, loose=1.0, step=0.010,
                                zsm=3, asm=2)
    cy = info["Cs"][:, 1].mean()
    ntop = np.array([0, 0.25, 1.0])
    ntop /= np.linalg.norm(ntop)
    w_sw = 0.17 * sc

    def z_hem(co):
        # higher at the knot side, a swag dipping in the centre front and back
        return zbot + 0.03 * sc + 0.10 * ks * co[:, 0] - 0.05 * sc * np.clip(1 - (co[:, 0] / w_sw) ** 2, 0, 1)

    def cut_hem(co):
        return co[:, 2] < z_hem(co)

    def snap_hem(co):
        out = np.full_like(co, np.nan)
        zh = z_hem(co)
        m = np.abs(co[:, 2] - zh) < voxel * 1.6
        out[m] = co[m]
        out[m, 2] = zh[m]
        return out
    G = shell([(Vc, Fc)], voxel, [lambda bm: bm_cut_plane(bm, (0, cy, ztop - 0.005), ntop),
                                  lambda bm: bm_delete_where(bm, cut_hem), lambda bm: bm_snap_boundary(bm, snap_hem)])
    knot = np.array([ks * 0.160 * sc, cy - 0.050 * sc, ztop - 0.050 * sc])
    folds = [fold_swag(rnd, cy, 0.17 * sc, 0.06 * sc, fold * 0.55, wave=0.075 * sc, zmin=zbot - 0.06, zmax=ztop - 0.03),
             fold_swag(rnd, cy, 0.17 * sc, 0.04 * sc, fold * 0.4, wave=0.08 * sc, zmin=zbot - 0.06, zmax=ztop - 0.03,
                       front=False),
             fold_radial(rnd, knot, fold * 0.7, wave=0.30, reach=0.26, axes=((0, -1, 0), (0, 0, 1))),
             fold_hanging(B, rnd, crotch + 0.02, zbot - 0.05, fold * 0.45, wave=0.09, min_frac=0.2)]
    G = post_shell(B, G, rnd, folds=folds, smooth_iters=5, gap=0.005, bsmooth=5)
    parts = [(G["V"], G["F"])]
    if flap:
        # the overlapping end of the wrap: front panel from the centre to the knot, 7 mm outside
        V, F = G["V"], G["F"]
        N = vertex_normals(V, F, G.get("T"))
        x0 = -ks * 0.03 * sc
        keep = (V[:, 1] < cy + 0.02) & (ks * (V[:, 0] - x0) > 0) & (V[:, 2] < ztop - 0.012)
        Ff = [f for f in F if keep[list(f)].all()]
        if len(Ff) > 20:
            used = sorted({i for f in Ff for i in f})
            remap = {o: n for n, o in enumerate(used)}
            Vf = V[used] + N[used] * 0.007
            Ff2 = [tuple(remap[i] for i in f) for f in Ff]
            Vf = smooth_boundary(Vf, Ff2, 10)
            Ef = edges_of(Ff2)
            Vf = laplacian(Vf, Ef, iters=2)
            parts.append((Vf, Ff2))
    # knot: a twisted bunch of cloth (several squashed ellipsoids)
    c = np.array(_column_center(B)(knot[2]))
    th0 = math.atan2(knot[1] - c[1], knot[0] - c[0])
    r0 = _surface_radius(G["V"], c, knot[2], th0) + 0.012
    kc = np.array([c[0] + r0 * math.cos(th0), c[1] + r0 * math.sin(th0), knot[2]])
    tdir = np.array([-math.sin(th0), math.cos(th0), 0])
    ndir = np.array([math.cos(th0), math.sin(th0), 0])
    Mk = np.stack([tdir, ndir, [0, 0, 1]], 1)
    lobes = [(np.zeros(3), (0.026, 0.017, 0.020), 0.0), (np.array([0.016, 0.002, 0.006]), (0.016, 0.012, 0.014), 0.7),
             (np.array([-0.014, 0.003, -0.008]), (0.015, 0.012, 0.016), -0.6), (np.array([0.0, 0.006, -0.018]), (0.012, 0.010, 0.012), 0.3)]
    kparts = []
    for off, rad, rot in lobes:
        rows = []
        Rz = np.array([[math.cos(rot), -math.sin(rot), 0], [math.sin(rot), math.cos(rot), 0], [0, 0, 1]])
        for a in np.linspace(0, math.pi, 9)[1:-1]:
            row = np.array([[math.sin(a) * math.cos(b_), math.sin(a) * math.sin(b_), math.cos(a)]
                            for b_ in np.linspace(-math.pi, math.pi, 14, endpoint=False)])
            row = row * np.array(rad) * sc
            row = row @ Rz.T
            rows.append(kc + (Mk @ off) * sc + row @ Mk.T)
        kparts.append(loft_closed(rows))
    Vk, Fk = _merge(kparts)
    Gk = shell([(Vk, Fk)], 0.004)
    Gk = post_shell(B, Gk, rnd, folds=[fold_crumple(rnd, 0.002, 60)], smooth_iters=2, gap=0.004, push=False)
    parts.append((Gk["V"], Gk["F"]))
    # two hanging ends (tapered, slightly twisted) down the side of the thigh
    cf = _column_center(B)
    thigh = B.pts({RID["thigh_L"], RID["thigh_R"]})
    ref = np.vstack([G["V"], thigh])
    for e, (dth, ln, wd) in enumerate(((-0.12 * ks, 0.22, 0.055), (0.05 * ks, 0.30, 0.065))):
        rows = []
        nseg = 14
        for k in range(nseg):
            t = k / (nseg - 1)
            zz = knot[2] - 0.012 - t * ln * sc
            th = th0 + dth * (0.25 + t) + 0.05 * math.sin(t * 4 + e)
            cc = np.array(cf(zz))
            rr = _surface_radius(ref, cc, zz, th) + 0.010 + 0.005 * e
            p0 = np.array([cc[0] + rr * math.cos(th), cc[1] + rr * math.sin(th), zz])
            td = np.array([-math.sin(th), math.cos(th), 0])
            nd = np.array([math.cos(th), math.sin(th), 0])
            tw = 0.25 * math.sin(t * 2.0 + e)                    # gentle twist
            td2 = td * math.cos(tw) + nd * math.sin(tw)
            w = wd * sc * (1 - 0.35 * t)
            row = [p0 + td2 * w * (j / 4 - 0.5) + nd * 0.003 * math.sin(math.pi * j / 4) for j in range(5)]
            rows.append(np.array(row))
        parts.append(loft_open(rows, closed_u=False))
    V, F = _merge(parts)
    reg, _ = B.nearest_region(V)
    G2 = dict(V=V, F=F, E=edges_of(F), region=reg, T=tri_fan(F))
    ob = finalize(person, B, G2, rnd, name, fabric_material("linen"), rgb, detail, skirt_below=ztop - 0.02, hem_z=zbot,
                  wear=wear, wear_band=0.12, thickness=0.0025, uv=column_uv(B, G2))
    # hide the genitals + the skin well under the cloth
    gi = person.body.vertex_groups.get("genitals")
    hide = []
    if gi is not None:
        gidx = gi.index
        hide = [v.index for v in person.body.data.vertices if any(g.group == gidx and g.weight > 0.3 for g in v.groups)]
    hide_body(person, hide)
    mask_covered(person, B, G, margin=0.05)
    return [ob], G


def part_swaddle(person, B, rnd, rgb, detail="hero", name="swaddle", voxel=None, hood=True):
    """Baby wrapped in linen bands: a cocoon from below the feet up to a collar behind the head, with
    overlapping diagonal band edges. The whole body except head/neck is hidden (arms are inside)."""
    voxel = voxel or (0.006 if detail == "hero" else 0.011)
    sc = _sc(B)
    nb = B.head("neck01")
    eye_z = B.head("oculi01.L")[2]
    P = B.pts(CORE | {RID["foot_L"], RID["foot_R"]}, zmax=nb[2] + 0.01)
    if len(P) < 10:
        P = B.bco[B.bco[:, 2] < nb[2]]
    HP = _head_points(B)
    zlo = float(P[:, 2].min()) - 0.02 * sc
    top = (eye_z + 0.01 * sc) if hood else nb[2] + 0.005
    if hood:
        P = np.vstack([P, HP[HP[:, 2] < top + 0.02]])
    hgt = top - zlo
    sh = B.head("upperarm01.L")[2]

    def ease(zs):
        e = 0.012 + 0.010 * np.sin(np.clip((zs - zlo) / hgt, 0, 1) * math.pi)
        e = e * np.clip((sh + 0.02 - zs) / 0.05, 0.45, 1)            # rounded shoulders
        return e * sc
    cf = _head_axis(B)
    Vc, Fc, info = column_solid(B, P, zlo, top, ease, center_fn=cf, drape_below=None, step=0.006 * sc, zsm=3, asm=2)

    def face_cut(co):
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        return (co[:, 1] < cy + 0.012 * sc) & (co[:, 2] > nb[2] - 0.004)
    cuts = [lambda bm: bm_delete_where(bm, face_cut)] if hood else [lambda bm: _cut_neck(bm, B, 0.004 * sc, 0.006 * sc)]
    G = shell([(Vc, Fc)], voxel, cuts)
    seed = rnd.random() * 10

    def bands(V, N, reg):
        cfb = _column_center(B)
        th, r, c = _cyl_coords(V, B, cfb)
        s_ = th * 0.08 * sc
        out = np.zeros(len(V))
        pitch = 0.05 * sc
        for i in range(len(V)):
            z = (V[i, 2] - zlo) / hgt
            if V[i, 2] > nb[2]:
                continue
            al = 0.5 if z > 0.45 else -0.5
            q = (V[i, 2] * math.cos(al) + s_[i] * math.sin(al)) / pitch + 0.25 * _n1(z * 6, seed)
            fr = q - math.floor(q)
            saw = fr / 0.85 if fr < 0.85 else (1 - fr) / 0.15
            out[i] = 0.0045 * sc * (saw - 0.5) + 0.0012 * _n3(V[i] * 40, seed)
        return out
    G = post_shell(B, G, rnd, folds=[bands], smooth_iters=3, gap=0.004, bsmooth=3)
    ob = finalize(person, B, G, rnd, name, fabric_material("linen"), rgb, detail, skirt_below=B.head("spine05")[2],
                  hem_z=zlo, wear=0.3, wear_band=0.05, thickness=0.002, uv=column_uv(B, G))
    hide = B.bidx[~np.isin(B.breg, [RID["head"], RID["neck"]]) | (B.bco[:, 2] < nb[2] - 0.01)]
    hide_body(person, hide)
    return [ob], G


def _plane_band(P, origin, normal, width, gap, zmin=-9.0, K=40, thick=0.0):
    """Strap around points P cut by a plane: hull of the slab in-plane + gap; keeps the part above zmin."""
    n = np.asarray(normal, float)
    n /= np.linalg.norm(n)
    u, v = frame_of(n)
    rel = P - origin
    S = rel[np.abs(rel @ n) < 0.006]
    if len(S) < 5:
        return None
    Q = np.stack([S @ u, S @ v], 1)
    H = hull2d(Q)
    c2 = H.mean(0)
    ang = np.linspace(-math.pi, math.pi, K, endpoint=False)
    R = circ_smooth(ray_radii(H, c2, ang), 1) + gap
    rings = []
    for t in (-0.5, 0.5):
        pts = origin + np.outer(c2[0] + R * np.cos(ang), u) + np.outer(c2[1] + R * np.sin(ang), v) + n * (t * width)
        rings.append(pts)
    V, F = loft_open(rings)
    keep = [f for f in F if min(V[i][2] for i in f) > zmin]
    return V, keep


def part_sandals(person, B, rnd, rgb, detail="hero", name="sandals", style="sandal", sole=None):
    """Leather sandals (sole + toe loop, instep and ankle straps) or Roman caligae (thick hobnailed sole
    and an openwork lattice of straps up to the ankle)."""
    sc = _sc(B)
    parts = []
    thick = (sole or (0.016 if style == "caligae" else 0.009)) * sc
    for side in ("L", "R"):
        s = "." + side
        F_ = B.pts({RID["foot_" + side]})
        Lw = B.pts({RID["shin_" + side]}, zmax=B.head("foot" + s)[2] + 0.10)
        allp = np.vstack([F_, Lw])
        ground = float(F_[:, 2].min())
        low = F_[F_[:, 2] < ground + 0.02 * sc]
        H = hull2d(low[:, :2])
        c2 = H.mean(0)
        ang = np.linspace(-math.pi, math.pi, 40, endpoint=False)
        R = circ_smooth(ray_radii(H, c2, ang), 2) + 0.005 * sc
        top = np.stack([c2[0] + R * np.cos(ang), c2[1] + R * np.sin(ang), np.full(40, ground + 0.0015)], 1)
        bot = top.copy()
        bot[:, 2] = ground - thick
        mid = top.copy()
        mid[:, 2] = ground - thick * 0.5
        rings = [bot * np.array([1, 1, 1]) + np.array([0, 0, 0]), mid, top]
        rings[0][:, :2] = c2 + (rings[0][:, :2] - c2) * 0.985
        parts.append(loft_closed(rings))
        heel_y = float(F_[:, 1].max())
        toe_y = float(F_[:, 1].min())
        Lf = heel_y - toe_y
        ank = B.head("foot" + s)
        zmin = ground + 0.002
        straps = []
        if style == "sandal":
            straps.append(((0, toe_y + Lf * 0.36, 0), (0, 1, -0.55), 0.016))       # across the instep
            straps.append(((0, toe_y + Lf * 0.58, 0), (0, 1, -0.95), 0.012))       # mid foot
            straps.append(((ank[0], ank[1] + 0.005, ank[2] - 0.010), (0, 0.15, 1), 0.012))  # ankle
        else:
            for k, t in enumerate(np.linspace(0.22, 0.70, 6)):
                straps.append(((0, toe_y + Lf * t, 0), (0.25 * (-1) ** k, 1, -0.7 + 0.05 * k), 0.012))
            for k in range(3):
                straps.append(((ank[0], ank[1] + 0.005, ank[2] - 0.02 + 0.03 * k), (0.15 * (-1) ** k, 0.15, 1), 0.012))
        ankle_pts = np.vstack([F_[F_[:, 1] > toe_y + Lf * 0.55], Lw[Lw[:, 2] < ank[2] + 0.06]])
        for (ox, oy, oz), nrm, w in straps:
            if oz:      # ankle straps wrap the ankle / lower shin
                o = np.array([ox, oy, oz])
                src = ankle_pts
            else:       # straps over the foot use only foot points (no shin => no tall loops)
                o = np.array([float(F_[:, 0].mean()), oy, ground + 0.03])
                src = F_
            b = _plane_band(src, o, nrm, w * sc, 0.0025 * sc, zmin=zmin)
            if b is not None:
                parts.append(b)
        # toe thong between the big toe and second toe up to the instep strap
        t1 = B.head("toe1-1" + s)
        t2 = B.head("toe2-1" + s)
        a = (t1 + t2) / 2
        a[2] = ground + 0.004
        bpt = np.array([a[0] + 0.004 * (1 if side == "L" else -1), toe_y + Lf * 0.36, ground + 0.045 * sc])
        rows = []
        for k in range(6):
            t = k / 5
            p0 = a + (bpt - a) * t
            p0[2] += math.sin(t * math.pi) * 0.006
            rows.append(np.array([p0 - np.array([0.004, 0, 0]), p0 + np.array([0.004, 0, 0])]))
        parts.append(loft_open(rows, closed_u=False))
        # heel strap: vertical band behind the heel up to the ankle strap
        hb = np.array([float(F_[:, 0].mean()), heel_y + 0.004, ground + 0.004])
        he = np.array([ank[0], heel_y + 0.006, ank[2] - 0.01])
        rows = []
        for k in range(6):
            t = k / 5
            p0 = hb + (he - hb) * t
            S = allp[np.abs(allp[:, 2] - p0[2]) < 0.006]
            if len(S):
                p0[1] = float(S[:, 1].max()) + 0.003
            rows.append(np.array([p0 - np.array([0.008, 0, 0]), p0 + np.array([0.008, 0, 0])]))
        parts.append(loft_open(rows, closed_u=False))
    V, F = _merge(parts)
    W = _weights_simple(B, V, F, smooth=2)
    uv = uv_builder([np.stack([V[:, 0] * 3 + V[:, 1] * 1, V[:, 2] * 3 + V[:, 1] * 2], 1)], np.zeros(len(V), np.int64), [1e9])
    ob = finish_garment(person, B, name, V, F, name, fabric_material("leather"), rgb, weights=W, uv=uv,
                        attrs={"wear": np.full(len(V), 0.6), "hem": np.zeros(len(V))}, thickness=0.003, detail=detail)
    return [ob]


def part_helmet(person, B, rnd, detail="hero", metal="iron", name="galea", crest=False, hide_hair=True):
    """Roman galea (Imperial-Gallic style): bowl, brow ridge, flared neck guard, hinged cheek guards."""
    sc = _sc(B)
    eye_z = B.head("oculi01.L")[2]
    chin = B.tail("jaw")
    cf = _head_axis(B)
    HP = _head_points(B)
    top = float(HP[:, 2].max())
    zf, zb = eye_z + 0.032 * sc, eye_z - 0.030 * sc
    Vb, Fb, info = column_solid(B, HP, zb - 0.03, top + 0.012, 0.010 * sc, center_fn=cf, step=0.007, drape_below=None)
    yf = float(HP[:, 1].min())
    yb = float(HP[:, 1].max())
    Fp = np.array([0, yf, zf])
    Bp = np.array([0, yb, zb])
    d = Bp - Fp
    n = np.cross(np.array([1.0, 0, 0]), d)
    if n[2] < 0:
        n = -n
    n /= np.linalg.norm(n)
    G = shell([(Vb, Fb)], 0.006 if detail == "hero" else 0.01, [lambda bm: bm_cut_plane(bm, Fp, -n)])
    G = post_shell(B, G, rnd, smooth_iters=3, gap=0.008, push=True)
    V = G["V"]
    bnd = boundary_mask(len(V), G["F"])
    extra = []
    # neck guard: extend the back part of the rim outwards and down
    rim = V[bnd]
    c = np.array(cf(zb))
    th = np.arctan2(rim[:, 1] - c[1], rim[:, 0] - c[0])
    order = np.argsort(th)
    rim, th = rim[order], th[order]
    back = np.sin(th) > 0.15
    rb = rim[back]
    if len(rb) > 4:
        thb = th[back]
        rows = []
        for t, out_, dn in ((0, 0, 0), (0.5, 0.022, 0.018), (1, 0.05, 0.026)):
            row = []
            for p, a in zip(rb, thb):
                radial = np.array([math.cos(a), math.sin(a), 0])
                w = min(1.0, (math.sin(a) - 0.15) / 0.3)
                row.append(p + radial * out_ * sc * w + np.array([0, 0, -dn * sc * w]))
            rows.append(np.array(row))
        extra.append(loft_open(rows, closed_u=False))
    # brow ridge: tube around the front of the rim
    rf = rim[np.sin(th) < 0.1]
    thf = th[np.sin(th) < 0.1]
    if len(rf) > 4:
        rings = []
        for p, a in zip(rf, thf):
            radial = np.array([math.cos(a), math.sin(a), 0])
            cen = p + radial * 0.004 + np.array([0, 0, 0.012 * sc])
            tg = np.array([-math.sin(a), math.cos(a), 0])
            rings.append(np.array([cen + 0.0045 * (math.cos(b_) * radial + math.sin(b_) * np.array([0, 0, 1])) for b_ in np.linspace(0, 2 * math.pi, 6, endpoint=False)]))
        extra.append(loft_closed(rings))
    # cheek guards
    for sx in (1, -1):
        rows = []
        zt = eye_z + 0.008 * sc
        for z in np.linspace(zt, chin[2] + 0.025 * sc, 7):
            row = []
            for t in np.linspace(0, 1, 6):
                yy = (yf + 0.055 * sc) + t * 0.065 * sc
                # front edge recedes towards the jaw (opening for the eyes/mouth)
                S = HP[(np.abs(HP[:, 2] - z) < 0.01) & (np.abs(HP[:, 1] - yy) < 0.01) & (HP[:, 0] * sx > 0)]
                xx = (np.abs(S[:, 0]).max() if len(S) else 0.07 * sc) + 0.010 * sc
                row.append(np.array([sx * xx, yy, z]))
            rows.append(np.array(row))
        extra.append(loft_open(rows, closed_u=False))
    if crest:
        k = np.array([0, float(cf(top)[1]), top + 0.018])
        ring = [k + 0.008 * np.array([math.cos(a), math.sin(a), 0]) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
        extra.append(loft_closed([np.array(ring) - np.array([0, 0, 0.012]), np.array(ring) + np.array([0, 0, 0.012])]))
    Vall, Fall = _merge([(V, G["F"])] + extra)
    W = np.zeros((len(Vall), len(B.bone_names)), np.float32)
    W[:, B.bone_names.index("head")] = 1
    uv = uv_builder([Vall[:, :2] * 5], np.zeros(len(Vall), np.int64), [1e9])
    ob = finish_garment(person, B, name, Vall, Fall, name, metal_material(metal), color(metal), weights=W, uv=uv,
                        attrs={"wear": np.clip(0.3 + 0.4 * np.array([_n3(p * 8, 2.0) for p in Vall]), 0, 1),
                               "hem": np.zeros(len(Vall))}, thickness=0.0025, detail=detail)
    parent_to_bone(ob, person.rig, "head")
    if hide_hair:
        hide_hair_above(person, B, Fp - n * 0.004, n)
    return [ob]


def part_apron(person, B, rnd, Vref, z, detail="hero", name="apron", straps=6):
    """Cingulum apron: leather straps with bronze studs hanging from the belt front."""
    sc = _sc(B)
    cf = _column_center(B)
    parts = []
    studs = []
    ln = 0.24 * sc
    for k in range(straps):
        th = -math.pi / 2 + (k - (straps - 1) / 2) * 0.115
        rows = []
        for j in range(10):
            t = j / 9
            zz = z - 0.02 - t * ln
            cc = np.array(cf(zz))
            rr = _surface_radius(Vref, cc, zz, th) + 0.007
            p0 = np.array([cc[0] + rr * math.cos(th), cc[1] + rr * math.sin(th), zz])
            td = np.array([-math.sin(th), math.cos(th), 0])
            rows.append(np.array([p0 - td * 0.009 * sc, p0 + td * 0.009 * sc]))
            if j % 2 == 1 or j == 9:
                nd = np.array([math.cos(th), math.sin(th), 0])
                cen = p0 + nd * 0.002
                ring = [cen + 0.0065 * sc * (math.cos(a) * td + math.sin(a) * np.array([0, 0, 1])) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
                studs.append(loft_closed([np.array(ring), np.array(ring) + nd * 0.003]))
        parts.append(loft_open(rows, closed_u=False))
    V, F = _merge(parts)
    W = _weights_simple(B, V, F, skirt_below=z, smooth=3)
    uv = uv_builder([V[:, [0, 2]] * 4], np.zeros(len(V), np.int64), [1e9])
    a = finish_garment(person, B, name, V, F, name, fabric_material("leather"), color("dark_leather"), weights=W, uv=uv,
                       attrs={"wear": np.full(len(V), 0.5), "hem": np.zeros(len(V))}, thickness=0.004, detail=detail)
    V2, F2 = _merge(studs)
    W2 = _weights_simple(B, V2, F2, skirt_below=z, smooth=2)
    uv2 = uv_builder([V2[:, :2] * 4], np.zeros(len(V2), np.int64), [1e9])
    b = finish_garment(person, B, name + "_studs", V2, F2, name + "_studs", metal_material("bronze"), color("bronze"),
                       weights=W2, uv=uv2, attrs={"wear": np.full(len(V2), 0.4), "hem": np.zeros(len(V2))},
                       thickness=0, detail=detail)
    return [a, b]


def outfit_roman_soldier(person, B, rnd, colors, detail="hero", armor="hamata", helmet=True, cloak=True, metal="iron",
                         humeralia=False):
    out = []
    red = _pick(colors, "tunic", rnd, "roman_red")
    gs, G = part_tunic(person, B, rnd, red, fabric="wool", length="knee", sleeves="short", belt=None, detail=detail,
                       ease=0.022, flare=0.05, name="tunic", fold=0.010, wear=0.9)
    out += gs
    sc = _sc(B)
    crotch = B.head("upperleg02.L")[2]
    if armor == "segmentata":
        out += part_segmentata(person, B, rnd, detail, metal=metal)
    else:
        hem = crotch - 0.10 * sc
        gs, Gm = part_tunic(person, B, rnd, color("iron"), length=hem, sleeves="short", belt=None, detail=detail,
                            ease=0.010, flare=0.012, name="lorica_hamata", fold=0.004, wear=0.8, loose=0.35,
                            mat=mail_material(), thickness=0.006, layer_gap=0.009)
        out += gs
    if armor != "segmentata" and humeralia:
        # humeralia (shoulder doubling) as a short cape of mail
        gs2, _ = part_mantle(person, B, rnd, color("iron"), detail=detail, style="cape", length=B.head("spine01")[2] - 0.04,
                             fabric="wool", name="humeralia", fold=0.002, roll=False, mask=False)
        for o in gs2:
            o.data.materials[0] = mail_material()
        out += gs2
    # cingulum (belt) + apron
    zb = B.head("spine05")[2] + 0.035 * sc
    Vref = layer_points(B, 1)
    belt = part_belt(person, B, rnd, color("dark_leather"), Vref, zb, kind="leather", detail=detail, name="cingulum")
    out.append(belt)
    out += part_apron(person, B, rnd, Vref, zb, detail=detail)
    if cloak:
        gs3, Gs = part_mantle(person, B, rnd, _pick(colors, "cloak", rnd, "madder"), detail=detail, style="cape",
                              length="knee", fabric="wool", name="sagum", fold=0.014, roll=False, layer_gap=0.011)
        out += gs3
        out += part_fibula(person, B, Gs, detail=detail)
    if helmet:
        out += part_helmet(person, B, rnd, detail=detail, metal="iron" if metal == "iron" else "bronze")
    out += part_sandals(person, B, rnd, color("leather"), detail=detail, style="caligae", name="caligae")
    return out


def part_fibula(person, B, G, side="R", detail="hero", name="fibula", metal="bronze"):
    """Round brooch pinning a cloak at the front of the shoulder."""
    sc = _sc(B)
    sx = 1 if side == "L" else -1
    sh = B.head("upperarm01." + side)
    cf = _column_center(B)
    target = np.array([sx * 0.12 * sc, cf(sh[2])[1] - 0.08 * sc, sh[2] - 0.01])
    V = G["V"]
    i = int(np.argmin(np.linalg.norm(V - target, axis=1)))
    N = vertex_normals(V, G["F"], G.get("T"))
    p, n = V[i], N[i]
    u, v = frame_of(n)
    rings = []
    for h, r in ((0.0, 0.019), (0.004, 0.019), (0.006, 0.014), (0.008, 0.006)):
        rings.append(np.array([p + n * (h + 0.002) + r * sc * (math.cos(a) * u + math.sin(a) * v)
                               for a in np.linspace(0, 2 * math.pi, 16, endpoint=False)]))
    Vf, Ff = loft_closed(rings)
    W = _weights_simple(B, Vf, Ff, smooth=1)
    uv = uv_builder([Vf[:, :2] * 10], np.zeros(len(Vf), np.int64), [1e9])
    ob = finish_garment(person, B, name, Vf, Ff, name, metal_material(metal), color(metal), weights=W, uv=uv,
                        attrs={"wear": np.full(len(Vf), 0.4), "hem": np.zeros(len(Vf))}, thickness=0, detail=detail)
    return [ob]


def part_segmentata(person, B, rnd, detail="hero", metal="iron", name="lorica_segmentata"):
    """Banded iron armour: girth hoops from the waist to the chest + articulated shoulder guards."""
    sc = _sc(B)
    Vref = layer_points(B, 1)
    cf = _column_center(B)
    waist = B.head("spine05")[2] + 0.03 * sc
    chest = B.head("spine01")[2] + 0.06 * sc
    parts = []
    n = 7
    for k in range(n):
        z = waist + k * (chest - waist) / (n - 1)
        rings, _ = band_rings(B, Vref, z, 0.052 * sc, gap=0.008 + 0.0015 * k, bulge=0.004)
        parts.append(loft_open(rings))
    for sd in ("L", "R"):
        s = "." + sd
        sh = B.head("upperarm01" + s)
        cl = B.head("clavicle" + s)
        for k in range(4):
            t = k / 3
            o = cl + (sh - cl) * (0.4 + 0.6 * t) + np.array([0, 0, 0.0])
            nrm = (sh - cl)
            P = np.vstack([B.pts({RID["shoulder_" + sd], RID["upperarm_" + sd], RID["torso"]}, zmin=sh[2] - 0.12), Vref])
            b = _plane_band(P, o, nrm, 0.045 * sc, 0.012 + 0.003 * k, zmin=sh[2] - 0.05 - 0.02 * k)
            if b is not None:
                parts.append(b)
    V, F = _merge(parts)
    W = _weights_simple(B, V, F, smooth=3, arms=True)
    th, r, c = _cyl_coords(V, B, cf)
    uv = uv_builder([np.stack([th * 0.2, V[:, 2]], 1)], np.zeros(len(V), np.int64), [2 * math.pi * 0.2])
    ob = finish_garment(person, B, name, V, F, name, metal_material(metal), color(metal), weights=W, uv=uv,
                        attrs={"wear": np.full(len(V), 0.5), "hem": np.zeros(len(V))}, thickness=0.003, detail=detail)
    add_layer(B, V, F, name, W)
    return [ob]


def outfit_robe_rich(person, B, rnd, colors, detail="hero"):
    """Priest: fine white linen ankle tunic (embroidered hem), long sleeves, striped sash, open outer robe
    in a rich dye with embroidered edges, and a striped prayer shawl with tzitzit."""
    out = []
    gs, G = part_tunic(person, B, rnd, _pick(colors, "tunic", rnd, "white_linen"), fabric="fine_linen", length="ankle",
                       sleeves="long", belt=None, detail=detail, ease=0.028, flare=0.06, name="tunic", fold=0.012,
                       wear=0.6, embroidery=True)
    out += gs
    zb = _waist_z(B) + 0.01
    out.append(part_belt(person, B, rnd, _pick(colors, "belt", rnd, "madder"), G["V"], zb, kind="sash",
                         detail=detail, name="sash", stripes=True))
    gs, G2 = part_mantle(person, B, rnd, _pick(colors, "mantle", rnd, rnd.choice(["tekhelet", "purple", "indigo", "plum"])),
                         detail=detail, style="cloak", length="calf", fabric="wool", name="robe_outer", fold=0.014,
                         embroidery=True, wear=0.6)
    out += gs
    out += part_tallit(person, B, rnd, _pick(colors, "shawl", rnd, "bleached"), detail=detail)
    return out


def part_tallit(person, B, rnd, rgb, detail="hero", name="prayer_shawl"):
    """Prayer shawl draped over the shoulders: two front panels to the thighs, back to the waist; dark
    stripes near the ends, a short fringe and four tzitzit tassels at the corners."""
    voxel = 0.011 if detail == "hero" else 0.018
    sc = _sc(B)
    nb = B.head("neck01")
    top = nb[2] + 0.02
    chest = B.head("spine01")[2]
    waist = _waist_z(B)
    crotch = B.head("upperleg02.L")[2]
    sh_z = B.head("upperarm01.L")[2]
    z_front = crotch - 0.02 * sc
    z_back = waist - 0.04
    P = B.pts(CORE, zmin=z_front - 0.1, zmax=top + 0.02)
    P = P[~((P[:, 2] > nb[2] + 0.03) & (np.abs(P[:, 0]) < 0.09))]
    if B.layers:
        Lp = layer_points(B)
        Lreg, _ = B.nearest_region(Lp)
        P = np.vstack([P, Lp[~np.isin(Lreg, list(ARM_L | ARM_R)) & (Lp[:, 2] < top) & (Lp[:, 2] > z_front - 0.1)]])
    Vc, Fc, info = column_solid(B, P, z_front - 0.05, top, lambda zs: 0.008 * np.clip((top - zs) / 0.08, 0.3, 1),
                                drape_below=chest, loose=0.9)
    cf = _column_center(B)
    x_in, x_out = 0.045 * sc, 0.205 * sc

    def cut(co):
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        front = co[:, 1] < cy
        ax = np.abs(co[:, 0])
        bad_front = front & ((ax < x_in + np.clip(nb[2] - co[:, 2], 0, 1) * 0.04) | ((ax > x_out) & (co[:, 2] < sh_z - 0.02)))
        bad_back = (~front) & (co[:, 2] < z_back)
        return bad_front | bad_back
    def snap(co):
        out = np.full_like(co, np.nan)
        cy = np.array([cf(z)[1] for z in co[:, 2]])
        front = co[:, 1] < cy
        ax = np.abs(co[:, 0])
        xin = x_in + np.clip(nb[2] - co[:, 2], 0, 1) * 0.04
        m1 = front & (np.abs(ax - xin) < voxel * 1.5) & (co[:, 2] < nb[2])
        out[m1] = co[m1]
        out[m1, 0] = np.sign(co[m1, 0]) * xin[m1]
        m2 = front & (np.abs(ax - x_out) < voxel * 1.5) & (co[:, 2] < sh_z - 0.02) & ~m1
        out[m2] = co[m2]
        out[m2, 0] = np.sign(co[m2, 0]) * x_out
        m3 = (~front) & (np.abs(co[:, 2] - z_back) < voxel * 1.5)
        out[m3] = co[m3]
        out[m3, 2] = z_back
        m4 = front & (np.abs(co[:, 2] - z_front) < voxel * 1.5) & ~m1 & ~m2
        out[m4] = co[m4]
        out[m4, 2] = z_front
        return out
    G = shell([(Vc, Fc)], voxel, [lambda bm: bm_delete_where(bm, cut), lambda bm: _cut_neck(bm, B, 0.025, 0.02),
                                  lambda bm: bm_cut_plane(bm, (0, 0, z_front), (0, 0, -1)),
                                  lambda bm: bm_snap_boundary(bm, snap)])
    G = post_shell(B, G, rnd, folds=[fold_hanging(B, rnd, chest, z_front, 0.006, wave=0.07, min_frac=0.3)],
                   smooth_iters=4, gap=0.007, layer_gap=0.007, bsmooth=4)
    V = G["V"]
    # hem distance for the stripes: front panels measure from their bottom, the back from its bottom
    cy = np.array([cf(z)[1] for z in V[:, 2]])
    hem = np.where(V[:, 1] < cy, V[:, 2] - z_front, V[:, 2] - z_back)
    extra = []
    # fringes and tzitzit at the bottom corners of the front panels and the back
    bnd = boundary_mask(len(V), G["F"])
    corners = []
    for sx in (1, -1):
        for xx in (x_in + 0.01, x_out - 0.01):
            corners.append((sx * xx, z_front, -1))
    for sx in (1, -1):
        corners.append((sx * 0.17 * sc, z_back, 1))
    for (cx, cz, fb) in corners:
        sel = bnd & (np.abs(V[:, 2] - cz) < 0.02) & ((V[:, 1] < cy) if fb < 0 else (V[:, 1] > cy))
        if not sel.any():
            continue
        cand = V[sel]
        p = cand[np.argmin(np.abs(cand[:, 0] - cx))]
        for k in range(6):
            a = k / 6 * 2 * math.pi
            o = p + np.array([0.003 * math.cos(a), 0.003 * math.sin(a), 0])
            ln = (0.11 + 0.03 * rnd.random()) * sc
            rows = [o + np.array([0, 0, -ln * t]) + np.array([0.004 * math.sin(t * 3 + k), 0, 0]) for t in np.linspace(0, 1, 6)]
            rings = [np.array([q + 0.0012 * np.array([math.cos(b_), math.sin(b_), 0]) for b_ in np.linspace(0, 2 * math.pi, 4, endpoint=False)]) for q in rows]
            extra.append(loft_closed(rings))
    # short fringe along the bottom edges
    fr = V[bnd & (np.abs(V[:, 2] - z_front) < 0.012) & (V[:, 1] < cy)]
    for p in fr[::2]:
        ln = 0.025 * sc
        extra.append((np.array([p, p + np.array([0.0015, 0, 0]), p + np.array([0.0015, 0, -ln]), p + np.array([0, 0, -ln])]), [(0, 1, 2, 3)]))
    Vall, Fall = _merge([(V, G["F"])] + extra)
    hem_all = np.concatenate([hem, np.full(len(Vall) - len(V), 0.5)])
    reg, _ = B.nearest_region(Vall)
    G2 = dict(V=Vall, F=Fall, E=edges_of(Fall), region=reg, T=tri_fan(Fall))
    W = garment_weights(B, G2, skirt_below=waist - 0.02, smooth=5)
    ob = finish_garment(person, B, name, Vall, Fall, name, fabric_material("fine_linen", stripes=True), rgb,
                        weights=W, uv=column_uv(B, G2), attrs={"wear": np.full(len(Vall), 0.15), "hem": hem_all},
                        thickness=0.003, detail=detail)
    add_layer(B, V, G["F"], name, W[:len(V)])
    return [ob]


# ----------------------------------------------------------------------------------------------
# Cloth simulation (hero stills / hero shots)
# ----------------------------------------------------------------------------------------------
CLOTH = {   # fabric kind -> (mass kg/m2-ish, tension, bending, air damping)
    "linen": (0.15, 15.0, 0.05, 1.0), "fine_linen": (0.12, 12.0, 0.03, 1.0), "wool": (0.30, 18.0, 0.4, 1.0),
    "homespun": (0.25, 20.0, 0.3, 1.0), "sackcloth": (0.3, 25.0, 0.6, 1.0), "leather": (0.5, 40.0, 3.0, 1.0),
}
RIGID_PARTS = ("crown", "galea", "turban", "sandals", "caligae", "belt", "cingulum", "sash", "apron", "band",
               "studs", "segmentata", "fibula")


def _is_soft(ob):
    n = ob.get("wardrobe", ob.name)
    return not any(k in n for k in RIGID_PARTS) and ob.parent_type != "BONE"


def auto_pin(person, ob, B=None):
    """(Re)create the 'pin' vertex group of a garment: vertices that stay glued to the skinned shape during
    cloth simulation (neck/shoulder band, belt line, head part of head coverings, loincloth waistband)."""
    B = B or body_info(person)
    me = ob.data
    V = _np_co(me)
    part = ob.get("wardrobe", "")
    nb = B.head("neck01")
    sh_z = B.head("upperarm01.L")[2]
    pin = np.zeros(len(V))
    if any(k in part for k in ("veil", "headcloth", "hood")):
        chin = B.tail("jaw")[2]
        pin = np.clip((V[:, 2] - (chin - 0.02)) / 0.05, 0, 1)
    elif "loincloth" in part:
        top = V[:, 2].max()
        pin = np.clip((V[:, 2] - (top - 0.07)) / 0.04, 0, 1)
    else:
        d_neck = np.linalg.norm(V[:, :2] - nb[:2], axis=1)
        pin = np.clip((V[:, 2] - (sh_z - 0.01)) / 0.04, 0, 1) * np.clip((0.20 - d_neck) / 0.05, 0, 1)
        if "tunic" in part or "hamata" in part:
            bz = B.head("spine04")[2] + 0.005
            pin = np.maximum(pin, np.clip(1 - np.abs(V[:, 2] - bz) / 0.025, 0, 1) * float(ob.get("belted", 1)))
        if "mantle" in part or "prayer" in part or "sagum" in part or "robe_outer" in part or "humeralia" in part:
            pin = np.clip((V[:, 2] - (sh_z - 0.04)) / 0.05, 0, 1)
    g = ob.vertex_groups.get("pin")
    if g is not None:
        ob.vertex_groups.remove(g)
    g = ob.vertex_groups.new(name="pin")
    for w in np.unique(np.round(pin, 2)):
        if w <= 0:
            continue
        g.add(np.nonzero(np.round(pin, 2) == w)[0].tolist(), float(w), "REPLACE")
    return g


def _pose_snapshot(rig):
    return {pb.name: (pb.rotation_mode, pb.location.copy(), pb.rotation_quaternion.copy(), pb.rotation_euler.copy(),
                      pb.scale.copy()) for pb in rig.pose.bones}


def _apply_snapshot(rig, snap, t=1.0):
    from mathutils import Quaternion
    for pb in rig.pose.bones:
        mode, loc, q, e, sc = snap[pb.name]
        pb.location = loc * t
        pb.scale = Vector((1, 1, 1)).lerp(sc, t)
        if mode == "QUATERNION":
            pb.rotation_quaternion = Quaternion((1, 0, 0, 0)).slerp(q, t)
        elif mode == "AXIS_ANGLE":
            pass
        else:
            pb.rotation_euler = Euler((e.x * t, e.y * t, e.z * t), mode)


def _add_collision(body):
    m = body.modifiers.get("WardrobeCollision")
    if m is None:
        m = body.modifiers.new("WardrobeCollision", "COLLISION")
        # right after the armature + helper mask, before our hide mask / subdivision
        n = len(body.modifiers)
        tgt = next((i for i, x in enumerate(body.modifiers) if x.name == "WardrobeHide" or x.type == "SUBSURF"), n - 1)
        try:
            body.modifiers.move(n - 1, tgt)
        except Exception:
            pass
    c = body.collision
    c.thickness_outer = 0.004
    c.thickness_inner = 0.01
    c.cloth_friction = 8.0
    c.damping = 0.4
    return m


def _add_cloth(ob, fabric="linen", quality=5, frame_start=1, frame_end=60, self_collision=False):
    mass, tension, bend, air = CLOTH.get(fabric, CLOTH["linen"])
    n = len(ob.modifiers)
    m = ob.modifiers.new("WardrobeCloth", "CLOTH")
    tgt = next((i for i, x in enumerate(ob.modifiers) if x.type == "ARMATURE"), -1) + 1
    try:
        ob.modifiers.move(n, tgt)
    except Exception:
        pass
    st = m.settings
    st.quality = quality
    st.mass = mass
    st.tension_stiffness = st.compression_stiffness = tension
    st.shear_stiffness = tension * 0.5
    st.bending_stiffness = bend
    st.air_damping = air
    st.tension_damping = st.compression_damping = 5
    st.bending_damping = 0.5
    if ob.vertex_groups.get("pin"):
        st.vertex_group_mass = "pin"
        st.pin_stiffness = 1.0
    cs = m.collision_settings
    cs.use_collision = True
    cs.distance_min = 0.004
    cs.collision_quality = 3
    cs.use_self_collision = self_collision
    cs.self_distance_min = 0.003
    m.point_cache.frame_start = frame_start
    m.point_cache.frame_end = frame_end
    return m


def _fabric_of(ob):
    m = ob.data.materials[0] if ob.data.materials else None
    n = m.name if m else ""
    for k in ("fine_linen", "linen", "wool", "homespun", "sackcloth", "leather"):
        if k in n:
            return k
    return "linen"


def _skin_matrices(rig, ob):
    """Per vertex-group 4x4 deform matrices (armature space) for the current pose: pose @ rest^-1."""
    out = {}
    for g in ob.vertex_groups:
        pb = rig.pose.bones.get(g.name)
        if pb is None:
            continue
        out[g.index] = np.array(pb.matrix @ pb.bone.matrix_local.inverted())
    return out


def _unskin(rig, ob, P):
    """Inverse linear-blend skinning: posed armature-space points -> rest-space points for this mesh."""
    mats = _skin_matrices(rig, ob)
    me = ob.data
    R = P.copy()
    for v in me.vertices:
        S = np.zeros((4, 4))
        tw = 0.0
        for g in v.groups:
            M = mats.get(g.group)
            if M is None:
                continue
            S += g.weight * M
            tw += g.weight
        if tw < 1e-6:
            continue
        S /= tw
        try:
            q = np.linalg.solve(S, np.append(P[v.index], 1.0))
            R[v.index] = q[:3] / q[3]
        except np.linalg.LinAlgError:
            pass
    return R


def drape(person, garments, frames=30, ramp=20, quality=5, keep_rig=True, self_collision=False, sequential=True,
          ground=True, verbose=True):
    """Cloth-simulate garments onto the person's CURRENT pose (static drape with body collision).

    The rig is animated from the rest pose to the current pose over `ramp` frames, then held for `frames`
    frames so the cloth settles under gravity. Rigid items (crown, helmet, belts, sandals...) are skipped.
    keep_rig=True bakes the result back into the rest shape by inverse skinning, so the garment still follows
    small pose changes (breathing, head turns) and exactly reproduces the drape at this pose; keep_rig=False
    freezes the garment (Armature modifier removed). Inner layers are simulated first and become colliders
    for the outer ones (sequential=True). ground: True = temporary floor collider under the posed body,
    a float = floor at that world z, None = no floor. Returns the list of draped objects."""
    t0 = time.time()
    rig, body = person.rig, person.body
    sc = bpy.context.scene
    B = body_info(person)
    soft = [g for g in garments if g.type == "MESH" and _is_soft(g)]
    if not soft:
        return []
    f_save, fs_save, fe_save = sc.frame_current, sc.frame_start, sc.frame_end
    ad = rig.animation_data
    act_save = ad.action if ad else None
    snap = _pose_snapshot(rig)
    if ad:
        ad.action = None
    total = ramp + frames
    F0 = 1
    sc.frame_start, sc.frame_end = F0, F0 + total
    _add_collision(body)
    floor = None
    if ground is not None:
        # temporary floor collider at the lowest point of the posed body (or the given world z)
        if ground is True:
            dg = bpy.context.evaluated_depsgraph_get()
            ev = body.evaluated_get(dg)
            me = ev.to_mesh()
            Pw = _np_co(me) @ np.array(body.matrix_world)[:3, :3].T + np.array(body.matrix_world)[:3, 3]
            ev.to_mesh_clear()
            gz = float(Pw[:, 2].min())
            cx, cy = Pw[:, 0].mean(), Pw[:, 1].mean()
        else:
            gz = float(ground)
            cx, cy = rig.matrix_world.translation[:2]
        floor = _floor_collider(gz, (cx, cy), 6.0)
    done = []
    groups = [[g] for g in soft] if sequential else [soft]
    for grp in groups:
        for g in grp:
            if g.vertex_groups.get("pin") is None:
                auto_pin(person, g, B)
            _add_cloth(g, _fabric_of(g), quality, F0, F0 + total, self_collision)
            for m in g.modifiers:
                if m.type in ("SOLIDIFY", "SUBSURF", "MASK"):
                    m.show_viewport = False
        for f in range(F0, F0 + total + 1):
            _apply_snapshot(rig, snap, min(1.0, (f - F0) / max(1, ramp)))
            sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        for g in grp:
            ev = g.evaluated_get(dg)
            me = ev.to_mesh()
            P = _np_co(me)
            ev.to_mesh_clear()
            # cloth output is in object space == armature space (garments sit at identity under the rig)
            m = g.modifiers.get("WardrobeCloth")
            if m:
                g.modifiers.remove(m)
            if keep_rig:
                R = _unskin(rig, g, P)
            else:
                R = P
                am = g.modifiers.get("Armature")
                if am:
                    g.modifiers.remove(am)
            g.data.vertices.foreach_set("co", R.ravel())
            g.data.update()
            for mm in g.modifiers:
                if mm.type in ("SOLIDIFY", "SUBSURF", "MASK"):
                    mm.show_viewport = True
            # it is now a collider for the next layers
            if sequential and g is not soft[-1]:
                cm = g.modifiers.new("WardrobeCollision", "COLLISION")
                g.collision.thickness_outer = 0.003
            done.append(g)
        if verbose:
            print("  [wardrobe] drape %s %.1fs" % ([x.name for x in grp], time.time() - t0), flush=True)
    for g in soft:
        m = g.modifiers.get("WardrobeCollision")
        if m:
            g.modifiers.remove(m)
    m = body.modifiers.get("WardrobeCollision")
    if m:
        body.modifiers.remove(m)
    if floor is not None:
        me = floor.data
        bpy.data.objects.remove(floor)
        bpy.data.meshes.remove(me)
    _apply_snapshot(rig, snap, 1.0)
    if ad:
        ad.action = act_save
    sc.frame_start, sc.frame_end = fs_save, fe_save
    sc.frame_set(f_save)
    print("wardrobe.drape(%s) %d garments %.1fs" % (person.body.name, len(done), time.time() - t0), flush=True)
    return done


def _floor_collider(z, center=(0, 0), size=40.0, name="wardrobe_floor"):
    fm = bpy.data.meshes.new(name)
    cx, cy = center
    h = size / 2
    fm.from_pydata([(cx - h, cy - h, z), (cx + h, cy - h, z), (cx + h, cy + h, z), (cx - h, cy + h, z)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, fm)
    bpy.context.scene.collection.objects.link(ob)
    ob.modifiers.new("col", "COLLISION")
    ob.collision.thickness_outer = 0.004
    ob.collision.cloth_friction = 20
    ob.hide_render = True
    return ob


def cloth_sim(person, garments, ctx=None, preroll=20, frame_end=None, quality=5, self_collision=False, ground=None,
              bake=True):
    """Live cloth simulation for ANIMATED hero shots.

    Adds a Cloth modifier (after the Armature, pinned by the 'pin' group) to every soft garment and a
    Collision modifier to the body. The cloth cache starts `preroll` frames before frame 1 and the rig gets
    rest-pose keys at frame 1-preroll, so the cloth starts from its rest fit and is carried into the first
    pose. ground: None, a world z (temporary invisible floor collider) or a mesh object (gets a Collision
    modifier, e.g. the terrain). bake=True bakes right away (bpy.ops.ptcache.bake_all, in memory), which is
    REQUIRED for the pre-roll (scene.frame_start can't go below 0, so a sequential render from frame 1 would
    never visit it); bake=False only sets ctx.needs_bake. Call AFTER the character's animation is keyed.
    Returns the cloth modifiers."""
    rig, body = person.rig, person.body
    sc = bpy.context.scene
    B = body_info(person)
    f0 = 1 - preroll
    fe = frame_end or sc.frame_end
    for pb in rig.pose.bones:
        mode = pb.rotation_mode
        snap = (pb.location.copy(), pb.rotation_quaternion.copy(), pb.rotation_euler.copy(), pb.scale.copy())
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.keyframe_insert("location", frame=f0)
        pb.keyframe_insert("rotation_quaternion" if mode == "QUATERNION" else "rotation_euler", frame=f0)
        pb.location, pb.rotation_quaternion, pb.rotation_euler, pb.scale = snap
    _add_collision(body)
    if ground is not None:
        if isinstance(ground, bpy.types.Object):
            if not any(m.type == "COLLISION" for m in ground.modifiers):
                ground.modifiers.new("WardrobeCollision", "COLLISION")
        else:
            _floor_collider(float(ground), tuple(rig.matrix_world.translation[:2]))
    mods = []
    for g in garments:
        if g.type != "MESH" or not _is_soft(g):
            continue
        if g.vertex_groups.get("pin") is None:
            auto_pin(person, g, B)
        mods.append(_add_cloth(g, _fabric_of(g), quality, f0, fe, self_collision))
    if bake and mods:
        t = time.time()
        fc = sc.frame_current
        try:
            with bpy.context.temp_override(scene=sc):
                bpy.ops.ptcache.bake_all(bake=True)
        except Exception as e:
            print("wardrobe.cloth_sim bake warning:", e)
        sc.frame_set(fc)
        print("wardrobe.cloth_sim baked %d garments %d frames in %.1fs" % (len(mods), fe - f0 + 1, time.time() - t), flush=True)
    elif ctx is not None:
        ctx.needs_bake = True
    return mods


# ----------------------------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------------------------
OUTFITS = ["loincloth", "tunic", "robe", "robe_rich", "mantle", "veil", "headcloth", "turban", "hood",
           "roman_soldier", "swaddle", "crown_of_thorns", "sandals"]


def _pick(colors, part, rnd, default=None, aliases=()):
    c = None
    if isinstance(colors, dict):
        for k in (part,) + tuple(aliases):
            if k in colors:
                c = colors[k]
                break
    elif colors is not None and part in ("tunic", "main") + tuple(aliases):
        c = colors
    if c is None:
        c = default if default is not None else rnd.choice(CHOICES.get(part, CHOICES["tunic"]))
    return color(c, rnd, 0.05 if isinstance(c, str) else 0.0)


def dress(person, outfit, colors=None, seed=0, detail="hero", **opts):
    """Build `outfit` (name or list of names) on `person`; returns the list of garment objects
    (parented to person.rig, deformed by its armature). See docs/wardrobe.md."""
    if isinstance(outfit, (list, tuple)):
        out = []
        names = list(outfit)
        if "robe" in names and "mantle" in names:
            names.remove("mantle")
        if ("robe" in names or "robe_rich" in names or "roman_soldier" in names) and "tunic" in names:
            names.remove("tunic")
        if "roman_soldier" in names and "sandals" in names:
            names.remove("sandals")
        # build inner layers first
        order = {n: i for i, n in enumerate(["loincloth", "swaddle", "tunic", "robe", "robe_rich", "roman_soldier", "mantle",
                                              "veil", "headcloth", "hood", "turban", "crown_of_thorns", "sandals"])}
        names.sort(key=lambda n: order.get(n, 50))
        for i, o in enumerate(names):
            out += dress(person, o, colors, seed + i * 17, detail, **(opts.get(o, {}) if isinstance(opts.get(o), dict) else {}))
        return out
    t0 = time.time()
    _T0[0] = t0
    rnd = random.Random("%s/%s" % (outfit, seed))
    B = body_info(person)
    _tick("body info")
    if detail not in ("hero", "crowd"):
        detail = "crowd"
    out = []
    o = dict(opts)
    if outfit == "tunic":
        gs, G = part_tunic(person, B, rnd, _pick(colors, "tunic", rnd), detail=detail,
                           belt_rgb=_pick(colors, "belt", rnd) if isinstance(colors, dict) and "belt" in colors else None, **o)
        out += gs
    elif outfit == "robe":
        o.setdefault("length", "ankle")
        o.setdefault("sleeves", "long" if rnd.random() < 0.5 else "elbow")
        gs, G = part_tunic(person, B, rnd, _pick(colors, "tunic", rnd, aliases=("robe",)), detail=detail, **o)
        out += gs
        gs, G = part_mantle(person, B, rnd, _pick(colors, "mantle", rnd), detail=detail, side=rnd.choice(("L", "L", "R")))
        out += gs
    elif outfit == "mantle":
        gs, G = part_mantle(person, B, rnd, _pick(colors, "mantle", rnd, aliases=("main",)), detail=detail, **o)
        out += gs
    elif outfit == "robe_rich":
        out += outfit_robe_rich(person, B, rnd, colors, detail=detail)
    elif outfit in ("veil", "headcloth", "hood"):
        gs, G = part_headcover(person, B, rnd, _pick(colors, outfit, rnd, aliases=("main",)), kind=outfit, detail=detail, **o)
        out += gs
    elif outfit == "turban":
        gs, G = part_turban(person, B, rnd, _pick(colors, "turban", rnd, "bleached", aliases=("main",)), detail=detail, **o)
        out += gs
    elif outfit == "crown_of_thorns":
        out += part_crown(person, B, rnd, detail=detail, **o)
    elif outfit == "loincloth":
        gs, G = part_loincloth(person, B, rnd, _pick(colors, "loincloth", rnd, "linen", aliases=("main",)), detail=detail, **o)
        out += gs
    elif outfit == "swaddle":
        gs, G = part_swaddle(person, B, rnd, _pick(colors, "swaddle", rnd, "white_linen", aliases=("main",)), detail=detail, **o)
        out += gs
    elif outfit == "sandals":
        out += part_sandals(person, B, rnd, _pick(colors, "sandals", rnd, rnd.choice(["leather", "dark_leather", "camel"])),
                            detail=detail, **o)
    elif outfit == "roman_soldier":
        out += outfit_roman_soldier(person, B, rnd, colors, detail=detail, **o)
    else:
        raise ValueError("unknown outfit %r (choose from %s)" % (outfit, OUTFITS))
    for g in out:
        g["outfit"] = outfit
    if hasattr(person, "garments"):
        for g in out:
            if g not in person.garments:
                person.garments.append(g)
    print("wardrobe.dress(%s, %s, %s) %d objects %.2fs" % (person.body.name, outfit, detail, len(out), time.time() - t0), flush=True)
    return out
