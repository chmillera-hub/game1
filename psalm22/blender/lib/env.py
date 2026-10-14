"""Reusable OUTDOOR environments for Psalm 22 (Blender 4.5, EEVEE Next).

    from lib import env as E
    A = E.golgotha(ctx, mood="golden")          # hill + 3 crosses + Jerusalem + sky; returns anchors dict
    A = E.judean_hills(ctx, timelapse=True)      # day -> dusk -> night time-lapse (s02a)
    A = E.olive_grove(ctx)                        # Gethsemane at night (s02b, s08)
    A = E.plain_dawn(ctx, cross_hill=True)        # vast plain / hillside at sunrise for crowds

Building blocks: sky(mood) / sky_preset(name), night_sky(), clouds_layer(), god_rays(), dust_storm(),
scatter(), olive_tree(), dead_tree(), thorn_bush(), grass_tuft(), jerusalem(), haze controls.
Full API reference: psalm22/docs/env.md

Conventions: metres, Z up, frames 1-based. Everything heavy (decimated Poly Haven props, generated
trees) is cached in /opt/assets/env so repeated shot builds stay fast.
"""
import bpy, bmesh, math, os, json, random, time
import numpy as np
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree
from . import core as C
from . import polyhaven as ph

ENV_CACHE = os.path.join(C.ASSETS, "env")
os.makedirs(ENV_CACHE, exist_ok=True)

# Shared state for the current scene build (reset when a new scene is detected).
_S = {}


def _state():
    """Per-scene build state. A token stored on the scene detects a fresh scene (reset_scene)."""
    sc = bpy.context.scene
    tok = sc.get("env_token")
    if tok is None or _S.get("_token") != tok:
        tok = "%d_%f" % (random.getrandbits(40), time.time())
        sc["env_token"] = tok
        _S.clear()
        _S["_token"] = tok
        _S["haze"] = None
        _S["protos"] = {}
        _S["grounds"] = []
        _S["sky"] = None
    return _S


_T0 = [time.time()]


def _dbg(tag):
    """Debug timing/memory print (set env var ENV_DEBUG=1)."""
    if not os.environ.get("ENV_DEBUG"):
        return
    try:
        cur = int(open("/proc/self/statm").read().split()[1]) * 4096 / 1e6
    except Exception:
        cur = -1
    print("ENVDBG %-18s %6.1fs rss=%.0fMB" % (tag, time.time() - _T0[0], cur), flush=True)
    _T0[0] = time.time()


# =============================================================================================
# Vectorised noise (numpy) - deterministic, used for terrain heights + masks
# =============================================================================================
def _hash2(ix, iy, seed):
    n = (ix.astype(np.uint64) * np.uint64(374761393) + iy.astype(np.uint64) * np.uint64(668265263)
         + np.uint64((seed * 1442695041) & 0xffffffff)) & np.uint64(0xffffffff)
    n = ((n ^ (n >> np.uint64(13))) * np.uint64(1274126177)) & np.uint64(0xffffffff)
    n = n ^ (n >> np.uint64(16))
    return n


def perlin(x, y, seed=0):
    """2D gradient noise, roughly in [-1, 1]. x, y: numpy arrays (or scalars)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    x0 = np.floor(x)
    y0 = np.floor(y)
    xf, yf = x - x0, y - y0
    xi, yi = x0.astype(np.int64), y0.astype(np.int64)
    u = xf * xf * xf * (xf * (xf * 6 - 15) + 10)
    v = yf * yf * yf * (yf * (yf * 6 - 15) + 10)

    def g(ix, iy, dx, dy):
        a = (_hash2(ix, iy, seed) & np.uint64(0xffff)).astype(np.float64) * (2 * np.pi / 65536.0)
        return np.cos(a) * dx + np.sin(a) * dy

    n00 = g(xi, yi, xf, yf)
    n10 = g(xi + 1, yi, xf - 1, yf)
    n01 = g(xi, yi + 1, xf, yf - 1)
    n11 = g(xi + 1, yi + 1, xf - 1, yf - 1)
    a = n00 + (n10 - n00) * u
    b = n01 + (n11 - n01) * u
    return (a + (b - a) * v) * 1.4142


def fbm(x, y, octaves=5, lac=2.0, gain=0.5, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    s = np.zeros(np.broadcast(x, y).shape)
    a, f = 1.0, 1.0
    for i in range(octaves):
        # rotate each octave a bit to kill grid alignment
        c, sn = math.cos(0.5 * i), math.sin(0.5 * i)
        s = s + a * perlin((x * c - y * sn) * f, (x * sn + y * c) * f, seed + 17 * i)
        a *= gain
        f *= lac
    return s


def ridged(x, y, octaves=4, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    s = np.zeros(np.broadcast(x, y).shape)
    a, f = 0.5, 1.0
    for i in range(octaves):
        n = 1 - np.abs(perlin(x * f, y * f, seed + 31 * i))
        s = s + a * n * n
        a *= 0.5
        f *= 2.03
    return s


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=np.float64) - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _scalar(fn):
    """Wrap a vectorised f(X, Y) so it also accepts plain floats (returns float)."""
    def f(x, y):
        if np.isscalar(x) and np.isscalar(y):
            return float(fn(np.array([x], float), np.array([y], float))[0])
        return fn(np.asarray(x, float), np.asarray(y, float))
    f.vec = fn
    return f


# =============================================================================================
# Fast mesh helpers
# =============================================================================================
def mesh_from_numpy(name, verts, faces, coll=None, smooth=True):
    """verts: (N,3) float array; faces: (M,4) or (M,3) int array (uniform arity)."""
    verts = np.asarray(verts, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    k = faces.shape[1]
    me.loops.add(faces.size)
    me.loops.foreach_set("vertex_index", faces.ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", np.arange(0, faces.size, k, dtype=np.int32))
    me.update(calc_edges=True)
    if smooth:
        me.polygons.foreach_set("use_smooth", np.ones(len(faces), dtype=bool))
    me.update()
    return C.link(bpy.data.objects.new(name, me), coll)


def set_attr(obj, name, values, kind="FLOAT", domain="POINT"):
    me = obj.data
    a = me.attributes.get(name) or me.attributes.new(name, kind, domain)
    key = {"FLOAT": "value", "FLOAT_VECTOR": "vector", "INT": "value", "FLOAT_COLOR": "color"}[kind]
    a.data.foreach_set(key, np.asarray(values, dtype=np.int32 if kind == "INT" else np.float32).ravel())
    return a


def _grid_axis(c, core, cell, extent, growth):
    n0 = int(round(core / 2 / cell))
    xs = [i * cell for i in range(-n0, n0 + 1)]
    pos, d, step = [], n0 * cell, cell
    while d < extent:
        step *= growth
        d += step
        pos.append(d)
    return np.array(sorted([-p for p in pos] + xs + pos)) + c


def terrain_grid(name, height_fn, center=(0, 0), core=140.0, cell=0.5, extent=3500.0, growth=1.07,
                 mat_=None, attrs_fn=None, coll=None, core_y=None):
    """Warped-grid terrain: fine `cell` spacing inside the central `core` square (around `center`),
    then cells grow geometrically (factor `growth`) out to +-`extent` metres. height_fn(X, Y) is
    vectorised (numpy). attrs_fn(X, Y, Z) -> {name: array} adds float point attributes (masks)."""
    ax = _grid_axis(center[0], core, cell, extent, growth)
    ay = _grid_axis(center[1], core_y or core, cell, extent, growth)
    gx, gy = np.meshgrid(ax, ay)
    gz = height_fn(gx, gy)
    ny, nx = gx.shape
    verts = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)
    j, i = np.mgrid[0:ny - 1, 0:nx - 1]
    a = (j * nx + i).ravel()
    faces = np.stack([a, a + 1, a + nx + 1, a + nx], axis=1)
    o = mesh_from_numpy(name, verts, faces, coll)
    if attrs_fn:
        for k, v in attrs_fn(gx, gy, gz).items():
            set_attr(o, k, np.asarray(v, dtype=np.float32).ravel())
    if mat_:
        C.assign(o, mat_)
    # register with core so C.height_at(name, x, y) keeps working for shot builders
    C.TERRAINS[name] = (1.0, 1.0, 0.0, 1.0, 0.0, lambda x, y: float(height_fn(np.array([x]), np.array([y]))[0]))
    st = _state()
    st["grounds"].append(o)
    st.pop("bvh", None)
    return o


# =============================================================================================
# Ground raycasting
# =============================================================================================
def _bvh(objs=None):
    st = _state()
    objs = objs or [o for o in st["grounds"] if o.name in bpy.data.objects]
    key = tuple(sorted(o.name for o in objs))
    if st.get("bvh_key") == key and st.get("bvh"):
        return st["bvh"]
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, off = [], [], 0
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        n = len(me.vertices)
        co = np.empty(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        co = (np.c_[co, np.ones(n)] @ np.array(mw).T)[:, :3]
        verts.extend(map(tuple, co))
        me.calc_loop_triangles()
        tri = np.empty(len(me.loop_triangles) * 3, np.int32)
        me.loop_triangles.foreach_get("vertices", tri)
        polys.extend(map(tuple, tri.reshape(-1, 3) + off))
        off += n
        ev.to_mesh_clear()
    bvh = BVHTree.FromPolygons(verts, polys)
    st["bvh"], st["bvh_key"] = bvh, key
    return bvh


def ground_hit(x, y, objs=None, top=5000.0):
    """Raycast straight down at (x, y). Returns (z, normal Vector) or (None, None)."""
    hit = _bvh(objs).ray_cast(Vector((x, y, top)), Vector((0, 0, -1)))
    if hit[0] is None:
        return None, None
    n = hit[1]
    if n.z < 0:
        n = -n
    return hit[0].z, n


def release_bvh():
    """Free the cached raycast BVH (saves ~100 MB during rendering; rebuilt lazily on next use)."""
    st = _state()
    st.pop("bvh", None)
    st.pop("bvh_key", None)


def ground_z(x, y, objs=None, default=0.0):
    z, _ = ground_hit(x, y, objs)
    return default if z is None else z


def add_ground(obj):
    """Register an extra mesh (e.g. a cliff) for ground raycasts / scatter."""
    st = _state()
    st["grounds"].append(obj)
    st.pop("bvh_key", None)
    return obj


# =============================================================================================
# HDRI analysis (sun direction + horizon colours), cached as JSON
# =============================================================================================
def hdri_info(asset, res="2k"):
    """Analyse a Poly Haven HDRI: sun direction (in image space), sun irradiance, horizon colours.
    Cached in /opt/assets/env/hdri_info/. Returns dict with keys:
      sun_az_img (deg, atan2(y,x) of the sun direction with mapping rotation 0), sun_el (deg),
      sun_irr (approx. W/m2 of the sun blob), sun_rgb (normalised colour), peak (max luminance),
      horizon_rgb (mean colour 0.5-4 deg above horizon), horizon_bins (16 azimuth bins, image az),
      zenith_rgb, clamp (suggested lighting clamp value excluding the sun)."""
    path = os.path.join(ENV_CACHE, "hdri_info", "%s_%s.json" % (asset, res))
    if os.path.exists(path):
        return json.load(open(path))
    p = ph.hdri_path(asset, res)
    img = bpy.data.images.load(p, check_existing=True)
    w, h = img.size
    arr = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(arr)
    arr = arr.reshape(h, w, 4)[..., :3].astype(np.float64)
    lum = arr @ np.array([0.2126, 0.7152, 0.0722])
    rows = (np.arange(h) + 0.5) / h
    el = (rows - 0.5) * np.pi                      # elevation per row (row 0 = bottom)
    cols = (np.arange(w) + 0.5) / w
    th = (0.5 - cols) * 2 * np.pi                  # Blender equirect: u = 0.5 - atan2(y, x) / 2pi
    upper = lum.copy()
    upper[: h // 2] = 0
    r, c = np.unravel_index(np.argmax(upper), upper.shape)
    peak = float(lum[r, c])
    sun_el = math.degrees(el[r])
    t = th[c]
    sun_az = math.degrees(t)
    # solid angle per pixel
    dom = (2 * np.pi / w) * (np.pi / h) * np.cos(el)[:, None]
    # sun blob: pixels > max(peak*0.05, 50) within 4 deg
    d_el = np.abs(el[:, None] - el[r])
    d_th = np.abs(((th[None, :] - t + np.pi) % (2 * np.pi)) - np.pi) * np.cos(el[r])
    near = (d_el < math.radians(4)) & (d_th < math.radians(4))
    thr = max(peak * 0.02, 30.0)
    blob = near & (lum > thr)
    if blob.sum() == 0:
        blob = near & (lum >= peak * 0.5)
    irr = float((lum * dom)[blob].sum())
    rgb = (arr * dom[..., None])[blob].sum(axis=0)
    rgb = (rgb / max(rgb.max(), 1e-9)).tolist()
    band = (el > math.radians(0.5)) & (el < math.radians(4))
    hz = arr[band].mean(axis=(0, 1)).tolist()
    bins = []
    for k in range(16):
        sel = (cols >= k / 16) & (cols < (k + 1) / 16)
        bins.append(arr[band][:, sel].mean(axis=(0, 1)).tolist())
    zen = arr[el > math.radians(60)].mean(axis=(0, 1)).tolist()
    # lighting clamp: just above the brightest non-sun sky pixel (99.9 percentile of the sky)
    sky = lum[h // 2:][~blob[h // 2:]]
    clamp = float(max(np.percentile(sky, 99.9) * 1.5, 1.0))
    info = dict(asset=asset, sun_az_img=sun_az, sun_el=sun_el, sun_irr=irr, sun_rgb=rgb, peak=peak,
                horizon_rgb=hz, horizon_bins=bins, zenith_rgb=zen, clamp=clamp, size=[w, h])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part%d" % os.getpid()
    json.dump(info, open(tmp, "w"), indent=1)
    os.replace(tmp, path)
    return info


# =============================================================================================
# Haze (cheap aerial perspective in every env material) - one global node group
# =============================================================================================
HAZE_DEFAULT = dict(color=(0.75, 0.72, 0.68), density=0.0012, falloff=0.012, start=15.0,
                    sun_color=(1.0, 0.8, 0.55), sun_dir=(0, 1, 0.2), sun_mix=0.6, sun_power=6.0, max=1.0)


def scene_prop(name, value=None, frame=None):
    """Get/set a scene custom property used as a *uniform* by env shaders (Attribute node, View Layer
    type). Animating these (frame=...) is cheap: EEVEE updates a uniform buffer instead of
    re-evaluating every material that uses a node group (which costs seconds per frame)."""
    sc = bpy.context.scene
    if value is not None:
        sc[name] = tuple(float(v) for v in value) if isinstance(value, (tuple, list, Vector)) else float(value)
        if frame is not None:
            sc.keyframe_insert(data_path='["%s"]' % name, frame=frame)
    return sc.get(name)


def _lattr(T, name, default):
    """Attribute node reading scene property `name` (VIEW_LAYER lookup); returns the socket
    ('Vector' for 3-tuples, 'Fac' for floats) and initialises the property when missing."""
    sc = bpy.context.scene
    if name not in sc.keys():
        scene_prop(name, default)
    n = T.node("ShaderNodeAttribute")
    n.attribute_type = "VIEW_LAYER"
    n.attribute_name = name
    n.name = n.label = name
    return n.outputs["Vector"] if isinstance(default, (tuple, list)) else n.outputs["Fac"]


def haze_group():
    """The shared 'ENV_Haze' shader group: Shader in -> Shader out (mixes towards haze colour with
    view distance). Parameters are scene properties env_haze_* (see set_haze / get_haze)."""
    st = _state()
    g = st.get("haze")
    if g is not None and g.name in bpy.data.node_groups:
        return g
    g = bpy.data.node_groups.get("ENV_Haze")
    if g is not None:
        st["haze"] = g
        for k, v in HAZE_DEFAULT.items():
            if "env_haze_" + k not in bpy.context.scene.keys():
                scene_prop("env_haze_" + k, v)
        return g
    g = bpy.data.node_groups.new("ENV_Haze", "ShaderNodeTree")
    g.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
    g.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    T = _NT(g)
    gi, go = T.node("NodeGroupInput"), T.node("NodeGroupOutput")
    d = HAZE_DEFAULT
    c_col = _lattr(T, "env_haze_color", d["color"])
    c_den = _lattr(T, "env_haze_density", d["density"])
    c_fall = _lattr(T, "env_haze_falloff", d["falloff"])
    c_start = _lattr(T, "env_haze_start", d["start"])
    c_scol = _lattr(T, "env_haze_sun_color", d["sun_color"])
    c_dir = _lattr(T, "env_haze_sun_dir", d["sun_dir"])
    c_mix = _lattr(T, "env_haze_sun_mix", d["sun_mix"])
    c_pow = _lattr(T, "env_haze_sun_power", d["sun_power"])
    c_max = _lattr(T, "env_haze_max", d["max"])
    cam = T.node("ShaderNodeCameraData")
    geo = T.node("ShaderNodeNewGeometry")
    z = T.sep(geo.outputs["Position"])[2]
    hfac = T.math("EXPONENT", T.math("MULTIPLY", T.math("MULTIPLY", T.math("MAXIMUM", z, 0.0), c_fall), -1.0))
    dist = T.math("MAXIMUM", T.math("SUBTRACT", cam.outputs["View Distance"], c_start), 0.0)
    od = T.math("MULTIPLY", T.math("MULTIPLY", dist, c_den), hfac)
    fac = T.math("MINIMUM", T.math("SUBTRACT", 1.0, T.math("EXPONENT", T.math("MULTIPLY", od, -1.0))), c_max)
    neg = T.vmath("SCALE", geo.outputs["Incoming"], scale=-1.0)
    dot = T.vmath("DOT_PRODUCT", neg, T.vmath("NORMALIZE", c_dir))
    sd = T.math("POWER", T.math("MAXIMUM", dot, 0.0), c_pow)
    sf = T.math("MULTIPLY", sd, c_mix, clamp=True)
    mixc = T.mix(sf, c_col, c_scol)
    em = T.node("ShaderNodeEmission")
    T.link(mixc, em.inputs[0])
    ms = T.node("ShaderNodeMixShader")
    T.link(fac, ms.inputs[0])
    T.link(gi.outputs[0], ms.inputs[1])
    T.link(em.outputs[0], ms.inputs[2])
    T.link(ms.outputs[0], go.inputs[0])
    st["haze"] = g
    return g


def set_haze(color=None, density=None, falloff=None, start=None, sun_color=None, sun_dir=None, sun_mix=None,
             sun_power=None, max=None, frame=None):
    """Set the global aerial-perspective haze (scene properties env_haze_*, read as uniforms by every env
    material). density ~ 1/visibility in metres (0.0002 clear .. 0.002 dusty); falloff = exponential height
    falloff per metre; start = haze-free distance near the camera; sun_dir = world direction TOWARDS the
    sun (haze turns sun_color looking towards it). frame != None also inserts keyframes (animated haze)."""
    haze_group()
    vals = dict(color=color, density=density, falloff=falloff, start=start, sun_color=sun_color,
                sun_dir=(tuple(Vector(sun_dir).normalized()) if sun_dir is not None else None), sun_mix=sun_mix,
                sun_power=sun_power, max=max)
    for k, v in vals.items():
        if v is not None:
            scene_prop("env_haze_" + k, tuple(v[:3]) if isinstance(v, (tuple, list, Vector)) else v, frame)


def get_haze():
    haze_group()
    sc = bpy.context.scene
    return dict(color=tuple(sc["env_haze_color"]), density=sc["env_haze_density"], falloff=sc["env_haze_falloff"],
                start=sc["env_haze_start"], sun_dir=tuple(sc["env_haze_sun_dir"]))


def hazify(material):
    """Route a material's surface output through the global haze group (idempotent)."""
    if material is None or not material.use_nodes:
        return material
    nt = material.node_tree
    if any(n.type == "GROUP" and n.node_tree and n.node_tree.name.startswith("ENV_Haze") for n in nt.nodes):
        return material
    out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None) or \
        next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
    if out is None or not out.inputs["Surface"].is_linked:
        return material
    src = out.inputs["Surface"].links[0].from_socket
    gn = nt.nodes.new("ShaderNodeGroup")
    gn.node_tree = haze_group()
    gn.location = out.location.x - 180, out.location.y - 200
    nt.links.new(src, gn.inputs[0])
    nt.links.new(gn.outputs[0], out.inputs["Surface"])
    return material


# =============================================================================================
# Sky / world
# =============================================================================================
# Mood presets. sun_az = azimuth of the sun in core.sun convention (0 = sun at -Y, i.e. behind a
# camera looking +Y; 180 = sun at +Y, backlight). The HDRI is rotated so its sun matches sun_az.
SKY_PRESETS = {
    "golden": dict(hdri="table_mountain_2_puresky", sun_az=165, strength=1.0, bg=1.0, sun_mult=1.0,
                   tint=(1.0, 0.86, 0.66), sat=1.1, sun_temp=None, sun_tint=(1.0, 0.8, 0.55), sun_angle=1.2,
                   haze_density=0.00035, haze_tint=(1.0, 0.95, 0.88), fog=(1.0, 0.82, 0.62), fog_density=0.0015,
                   exposure=0.0, grade="warm", clouds=0.0),
    "noon": dict(hdri="kloofendal_48d_partly_cloudy_puresky", sun_az=200, strength=1.0, bg=1.0, sun_mult=1.0,
                 tint=(1.0, 0.98, 0.94), sat=0.95, sun_tint=(1.0, 0.97, 0.92), sun_angle=0.8,
                 haze_density=0.0003, haze_tint=(1.0, 1.0, 1.0), fog=(0.9, 0.88, 0.85), fog_density=0.0012,
                 exposure=-0.3, grade="neutral", clouds=0.0),
    "eclipse": dict(hdri="kloppenheim_01_puresky", sun_az=165, strength=0.35, bg=0.35, sun_mult=0.06,
                    tint=(1.0, 0.42, 0.2), sat=0.5, sun_tint=(1.0, 0.35, 0.12), sun_angle=1.0,
                    haze_density=0.0012, haze_tint=(1.0, 0.9, 0.8), fog=(0.65, 0.32, 0.17), fog_density=0.006,
                    exposure=0.3, grade="eclipse", clouds=0.7, sun_disk=dict(el=24, size=2.2, color=(1.0, 0.28, 0.08),
                                                                            strength=6.0)),
    "storm": dict(hdri="kloofendal_overcast_puresky", sun_az=120, strength=0.55, bg=0.55, sun_mult=0.25,
                  tint=(0.78, 0.82, 0.92), sat=0.55, sun_tint=(0.85, 0.88, 1.0), sun_angle=8.0,
                  haze_density=0.0009, haze_tint=(1.0, 1.0, 1.0), fog=(0.55, 0.57, 0.62), fog_density=0.004,
                  exposure=0.2, grade="cold", clouds=0.85),
    "dawn": dict(hdri="qwantani_dawn_puresky", sun_az=100, strength=1.4, bg=1.4, sun_mult=0.0,
                 tint=(1.0, 0.96, 1.0), sat=1.15, sun_tint=(1.0, 0.7, 0.55), sun_angle=2.0,
                 haze_density=0.0005, haze_tint=(1.0, 1.0, 1.0), fog=(0.85, 0.75, 0.8), fog_density=0.004,
                 exposure=0.5, grade="dawn", clouds=0.0),
    "sunrise": dict(hdri="qwantani_sunrise_puresky", sun_az=160, strength=1.0, bg=1.0, sun_mult=1.0,
                    tint=(1.0, 0.95, 0.9), sat=1.1, sun_tint=(1.0, 0.75, 0.5), sun_angle=1.5,
                    haze_density=0.00045, haze_tint=(1.0, 0.97, 0.93), fog=(1.0, 0.8, 0.62), fog_density=0.004,
                    exposure=0.2, grade="warm", clouds=0.0),
    "night": dict(hdri=None, sun_az=210, strength=1.0, bg=1.0, sun_mult=1.0, moon=True, stars=True,
                  haze_density=0.0004, haze_tint=(1.0, 1.0, 1.0), fog=(0.25, 0.32, 0.45), fog_density=0.004,
                  exposure=0.0, grade="night", clouds=0.0),
}


def sky_preset(name, **over):
    """Return a copy of the mood preset dict (optionally with overrides). See SKY_PRESETS."""
    if name not in SKY_PRESETS:
        raise KeyError("unknown sky preset %r (have %s)" % (name, ", ".join(SKY_PRESETS)))
    p = json.loads(json.dumps(SKY_PRESETS[name]))
    p["name"] = name
    p.update(over)
    return p


def _dir_from_az_el(az, el):
    """core.sun convention: direction TOWARDS the sun."""
    a, e = math.radians(az), math.radians(el)
    return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))


def _az_atan(az):
    """core.sun azimuth -> atan2(y, x) angle (degrees) of the horizontal direction."""
    d = _dir_from_az_el(az, 0)
    return math.degrees(math.atan2(d.y, d.x))


class _NT:
    """Tiny node-building helper."""

    def __init__(self, nt):
        self.nt, self.N, self.L = nt, nt.nodes, nt.links

    def node(self, kind, **props):
        n = self.N.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.L.new(a, b)

    def _in(self, n, i, x):
        if x is None:
            return
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        elif isinstance(x, (tuple, list)):
            v = list(x)
            if len(n.inputs[i].default_value) == 4 and len(v) == 3:
                v = v + [1.0]
            n.inputs[i].default_value = v
        else:
            self.L.new(x, n.inputs[i])

    def math(self, op, a, b=None, c=None, clamp=False):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        self._in(n, 0, a)
        self._in(n, 1, b)
        self._in(n, 2, c)
        return n.outputs[0]

    def smooth(self, e0, e1, x):
        """smoothstep(e0, e1, x) via Map Range (works for e0 > e1 too)."""
        n = self.N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        n.clamp = True
        self._in(n, 0, x)
        n.inputs[1].default_value = e0
        n.inputs[2].default_value = e1
        n.inputs[3].default_value = 0.0
        n.inputs[4].default_value = 1.0
        return n.outputs[0]

    def vmath(self, op, a, b=None, scale=None):
        n = self.N.new("ShaderNodeVectorMath")
        n.operation = op
        self._in(n, 0, a)
        self._in(n, 1, b)
        if scale is not None:
            self._in(n, 3, scale)
        return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]

    def mix(self, fac, a, b, blend="MIX", clamp=False):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        n.clamp_result = clamp
        self._in(n, 0, fac)
        self._in(n, 6, a)
        self._in(n, 7, b)
        return n.outputs[2]

    def mixf(self, fac, a, b):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "FLOAT"
        self._in(n, 0, fac)
        self._in(n, 2, a)
        self._in(n, 3, b)
        return n.outputs[0]

    def sep(self, v):
        n = self.N.new("ShaderNodeSeparateXYZ")
        self.L.new(v, n.inputs[0])
        return n.outputs

    def comb(self, x, y, z):
        n = self.N.new("ShaderNodeCombineXYZ")
        for i, a in enumerate((x, y, z)):
            self._in(n, i, a)
        return n.outputs[0]

    def value(self, v, name=None):
        n = self.N.new("ShaderNodeValue")
        n.outputs[0].default_value = v
        if name:
            n.name = n.label = name
        return n

    def rgb(self, c, name=None):
        n = self.N.new("ShaderNodeRGB")
        n.outputs[0].default_value = (*c[:3], 1)
        if name:
            n.name = n.label = name
        return n

    def ramp(self, fac, stops, interp="LINEAR"):
        n = self.N.new("ShaderNodeValToRGB")
        n.color_ramp.interpolation = interp
        els = n.color_ramp.elements
        while len(els) > len(stops):
            els.remove(els[-1])
        while len(els) < len(stops):
            els.new(0.5)
        for e, (p, c) in zip(els, stops):
            e.position = p
            e.color = (*c, 1) if len(c) == 3 else c
        self._in(n, 0, fac)
        return n

    def noise(self, vec, scale=1.0, detail=4.0, rough=0.5, dist=0.0, w=None, dims="3D"):
        n = self.N.new("ShaderNodeTexNoise")
        n.noise_dimensions = dims
        if vec is not None:
            self.L.new(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        n.inputs["Distortion"].default_value = dist
        if w is not None:
            if isinstance(w, (int, float)):
                n.inputs["W"].default_value = w
            else:
                self.L.new(w, n.inputs["W"])
        return n


def sky(mood="golden", sun_az=None, rotation=None, clouds=None, stars=None, moon=None, cfg=None, ctx=None,
        keep_sun=False, **over):
    """Build the world sky + sun light + haze colours for a mood (see SKY_PRESETS):
    'golden' | 'noon' | 'eclipse' | 'storm' | 'dawn' | 'sunrise' | 'night'.
    sun_az: azimuth for the sun in core.sun convention (0 = sun at -Y, 180 = sun at +Y). The HDRI is
    rotated so its own sun matches. Returns a dict: sun (light object), sun_dir (Vector towards the sun),
    sun_el, world nodes (bg, env, mapping, ...), preset, horizon (rgb)."""
    p = cfg or sky_preset(mood, **over)
    if sun_az is not None:
        p["sun_az"] = sun_az
    if clouds is not None:
        p["clouds"] = clouds
    st = _state()
    sc = bpy.context.scene
    w = sc.world
    w.sun_threshold = 1e6           # we place our own sun lamp (no automatic HDRI sun extraction)
    # llvmpipe keeps the virtual shadow-map pool in RAM: 256 MB is plenty at 540x960 (default 512)
    if sc.eevee.shadow_pool_size == "512":
        sc.eevee.shadow_pool_size = "256"
    w.use_sun_shadow = False
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    T = _NT(nt)
    out = T.node("ShaderNodeOutputWorld")
    tc = T.node("ShaderNodeTexCoord")
    view = tc.outputs["Generated"]          # world: view direction
    res = dict(preset=p, nodes={})
    if p.get("hdri"):
        info = hdri_info(p["hdri"])
        rot = rotation if rotation is not None else (info["sun_az_img"] - _az_atan(p["sun_az"]))
        sun_el = info["sun_el"] if p.get("sun_el") is None else p["sun_el"]
        mp = T.node("ShaderNodeMapping")
        mp.inputs["Rotation"].default_value[2] = math.radians(rot)
        T.link(view, mp.inputs["Vector"])
        env = T.node("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(ph.hdri_path(p["hdri"]), check_existing=True)
        T.link(mp.outputs["Vector"], env.inputs["Vector"])
        col = env.outputs["Color"]
        if p.get("sat", 1.0) != 1.0:
            hs = T.node("ShaderNodeHueSaturation")
            hs.inputs["Saturation"].default_value = p["sat"]
            T.link(col, hs.inputs["Color"])
            col = hs.outputs["Color"]
        tint = p.get("tint")
        if tint:
            col = T.mix(1.0, col, tint, blend="MULTIPLY")
        hz = Vector(info["horizon_rgb"])
        hz_avg = hz.copy()
        if tint:
            hz = Vector([hz[i] * tint[i] for i in range(3)])
        # desaturate horizon like the sky
        lum = 0.2126 * hz.x + 0.7152 * hz.y + 0.0722 * hz.z
        hz = Vector([lum + (c - lum) * p.get("sat", 1.0) for c in hz])
        # below the horizon: replace the HDRI's fake ground by the horizon colour (seamless with haze)
        vz = T.sep(view)[2]
        below = T.math("MULTIPLY", T.math("SUBTRACT", 0.01, vz), 60.0, clamp=True)
        col = T.mix(below, col, tuple(hz))
        sky_col = col
        res["nodes"].update(env=env, mapping=mp)
        res["hdri_rotation"] = rot
        sun_irr = info["sun_irr"]
        sun_rgb = info["sun_rgb"]
        clamp_v = info["clamp"]
    else:
        sun_el = p.get("sun_el", 35.0)
        hz = Vector(p.get("horizon", (0.012, 0.018, 0.032)))
        zen = p.get("zenith", (0.0015, 0.0025, 0.006))
        vz = T.sep(view)[2]
        g = T.math("POWER", T.math("MAXIMUM", vz, 0.0), 0.45)
        sky_col = T.mix(g, tuple(hz), tuple(zen))
        sun_irr, sun_rgb, clamp_v = 0.0, (0.6, 0.75, 1.0), 100.0
    res["horizon"] = tuple(hz)
    st["sky_col_socket"] = None

    # --- optional procedural components composited over the sky colour --------------------
    sun_dir = _dir_from_az_el(p["sun_az"], sun_el)
    if p.get("stars") if stars is None else stars:
        sky_col = _stars(T, view, sky_col, p.get("star_strength", 1.0), res)
    if p.get("moon") if moon is None else moon:
        mdir = _dir_from_az_el(p.get("moon_az", p["sun_az"]), p.get("moon_el", 28.0))
        sky_col = _disk(T, view, sky_col, mdir, size=p.get("moon_size", 0.75), color=p.get("moon_color", (0.9, 0.93, 1.0)),
                        strength=p.get("moon_strength", 12.0), glow=p.get("moon_glow", 0.06), res=res, key="moon")
        res["moon_dir"] = mdir
    if p.get("sun_disk"):
        sd = p["sun_disk"]
        ddir = _dir_from_az_el(p["sun_az"], sd.get("el", sun_el))
        sky_col = _disk(T, view, sky_col, ddir, size=sd.get("size", 1.5), color=sd.get("color", (1, 0.3, 0.1)),
                        strength=sd.get("strength", 5.0), glow=sd.get("glow", 0.25), res=res, key="sun_disk")
        res["sun_disk_dir"] = ddir
    cl = p.get("clouds", 0.0)
    if cl:
        sky_col = _cloud_layer(T, view, sky_col, coverage=cl, ctx=ctx, res=res, sun_dir=sun_dir,
                               **p.get("cloud_opts", {}))

    # --- background vs lighting branches ------------------------------------------------------
    lp = T.node("ShaderNodeLightPath")
    bg_cam = T.node("ShaderNodeBackground")
    bg_cam.inputs[1].default_value = p.get("bg", 1.0)
    T.link(sky_col, bg_cam.inputs[0])
    clamp_n = T.node("ShaderNodeMix")
    clamp_n.data_type = "RGBA"
    clamp_n.blend_type = "DARKEN"
    clamp_n.inputs[0].default_value = 1.0
    T.link(sky_col, clamp_n.inputs[6])
    clamp_n.inputs[7].default_value = (clamp_v, clamp_v, clamp_v, 1)
    bg_light = T.node("ShaderNodeBackground")
    bg_light.inputs[1].default_value = p.get("strength", 1.0)
    T.link(clamp_n.outputs[2], bg_light.inputs[0])
    ms = T.node("ShaderNodeMixShader")
    T.link(lp.outputs["Is Camera Ray"], ms.inputs[0])
    T.link(bg_light.outputs[0], ms.inputs[1])
    T.link(bg_cam.outputs[0], ms.inputs[2])
    T.link(ms.outputs[0], out.inputs["Surface"])
    res["nodes"].update(bg=bg_cam, bg_light=bg_light, mix=ms)

    # --- sun / moon lamp ----------------------------------------------------------------------
    old = st.get("sun_obj")
    if old is not None and old.name in bpy.data.objects:
        if keep_sun:
            res["sun"] = old
        bpy.data.objects.remove(old, do_unlink=True) if not keep_sun else None
    sun_obj = None
    if p["name"] == "night" or (p.get("moon") and not p.get("hdri")):
        mdir = res.get("moon_dir", _dir_from_az_el(p["sun_az"], 30))
        az = math.degrees(math.atan2(mdir.x, -mdir.y))
        el = math.degrees(math.asin(max(-1, min(1, mdir.z))))
        sun_obj = C.sun(elevation=el, azimuth=az, energy=p.get("moon_light", 0.35),
                        color=p.get("moon_light_color", (0.55, 0.68, 1.0)), angle=0.6)
        sun_obj.name = "Moon"
        res["sun_dir"] = mdir
        res["sun_el"] = el
    else:
        energy = sun_irr * p.get("strength", 1.0) * p.get("sun_mult", 1.0)
        energy = min(energy, p.get("sun_max", 12.0))
        col = [sun_rgb[i] * p.get("sun_tint", (1, 1, 1))[i] for i in range(3)]
        m = max(col)
        col = [c / m for c in col]
        if energy > 0.001:
            sun_obj = C.sun(elevation=max(sun_el, 0.5), azimuth=p["sun_az"], energy=energy, color=col,
                            angle=p.get("sun_angle", 1.0))
        res["sun_dir"] = sun_dir
        res["sun_el"] = sun_el
        res["sun_energy"] = energy
    if sun_obj is not None:
        sun_obj.data.shadow_maximum_resolution = 0.002
        sun_obj.data.use_shadow_jitter = False
    st["sun_obj"] = sun_obj
    res["sun"] = sun_obj

    # --- haze to match the sky ------------------------------------------------------------------
    ht = p.get("haze_tint", (1, 1, 1))
    bgs = p.get("bg", 1.0)
    hcol = [hz[i] * ht[i] * bgs for i in range(3)]
    scol = [hcol[i] * (0.6 + 1.4 * p.get("sun_tint", (1, 1, 1))[i]) for i in range(3)]
    set_haze(color=hcol, density=p.get("haze_density", 0.0015), sun_color=scol, sun_dir=res["sun_dir"])
    res["haze_color"] = hcol
    if ctx is not None:
        ctx.post.setdefault("grade", p.get("grade", "neutral"))
        if p.get("exposure"):
            ctx.render_opts.setdefault("exposure", p["exposure"])
    st["sky"] = res
    return res


def _stars(T, view, col, strength, res):
    """Add a procedural star field (fades towards the horizon). Keyable: res['nodes']['stars']"""
    vn = T.vmath("NORMALIZE", view)
    vor = T.node("ShaderNodeTexVoronoi")
    vor.feature = "F1"
    vor.voronoi_dimensions = "3D"
    vor.inputs["Scale"].default_value = 160.0
    vor.inputs["Randomness"].default_value = 1.0
    T.link(vn, vor.inputs["Vector"])
    d = vor.outputs["Distance"]
    rnd = T.sep(vor.outputs["Color"])
    # point star (~1 px at 540x960 / 35 mm): only a fraction of cells hold a visible star
    core = T.math("POWER", T.math("SUBTRACT", 1.0, T.math("MULTIPLY", d, 5.0), clamp=True), 3.0)
    sel = T.math("GREATER_THAN", rnd[0], 0.62)
    bright = T.math("POWER", rnd[1], 7.0)
    s = T.math("MULTIPLY", T.math("MULTIPLY", core, sel), T.math("MULTIPLY_ADD", bright, 25.0, 0.6))
    # second, denser layer of faint stars
    vor2 = T.node("ShaderNodeTexVoronoi")
    vor2.inputs["Scale"].default_value = 420.0
    T.link(vn, vor2.inputs["Vector"])
    core2 = T.math("POWER", T.math("SUBTRACT", 1.0, T.math("MULTIPLY", vor2.outputs["Distance"], 4.0), clamp=True), 3.0)
    sel2 = T.math("GREATER_THAN", T.sep(vor2.outputs["Color"])[0], 0.55)
    s = T.math("ADD", s, T.math("MULTIPLY", T.math("MULTIPLY", core2, sel2), 0.35))
    # milky-way-ish band of faint glow
    mw = T.noise(vn, scale=3.0, detail=6, rough=0.6)
    band = T.math("MULTIPLY", T.math("POWER", mw.outputs["Fac"], 4.0), 0.004)
    vz = T.sep(vn)[2]
    hfade = T.math("POWER", T.math("MULTIPLY", vz, 4.0, clamp=True), 1.5)
    scene_prop("env_stars", strength)
    k = _lattr(T, "env_stars", strength)
    amt = T.math("MULTIPLY", T.math("MULTIPLY", T.math("ADD", T.math("MULTIPLY", s, 0.08), band), hfade), k)
    tintc = T.comb(T.math("MULTIPLY", amt, 0.9), T.math("MULTIPLY", amt, 0.95), amt)
    res["nodes"]["stars"] = "env_stars"
    return T.mix(1.0, col, tintc, blend="ADD")


def _disk(T, view, col, direction, size=0.6, color=(1, 1, 1), strength=10.0, glow=0.05, res=None, key="disk"):
    """Add a celestial disk (moon / dim sun) of angular diameter `size` deg + soft glow."""
    vn = T.vmath("NORMALIZE", view)
    d = Vector(direction).normalized()
    dot = T.vmath("DOT_PRODUCT", vn, tuple(d))
    ang = T.math("ARCCOSINE", T.math("MINIMUM", dot, 1.0))            # radians
    r = math.radians(size / 2)
    disk = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", T.math("SUBTRACT", ang, r), 1.0 / max(r * 0.08, 1e-5)), clamp=True)
    halo = T.math("MULTIPLY", T.math("EXPONENT", T.math("MULTIPLY", ang, -1.0 / max(r * 6, 1e-4))), glow)
    k = T.value(strength, key)
    amt = T.math("MULTIPLY", T.math("ADD", disk, halo), k.outputs[0])
    c = T.comb(T.math("MULTIPLY", amt, color[0]), T.math("MULTIPLY", amt, color[1]), T.math("MULTIPLY", amt, color[2]))
    if res is not None:
        res["nodes"][key] = k
    # disk occludes what's behind (moon is opaque): darken background under the disk
    col = T.mix(T.math("MULTIPLY", disk, 0.9), col, (0, 0, 0))
    return T.mix(1.0, col, c, blend="ADD")


def _cloud_layer(T, view, col, coverage=0.5, ctx=None, res=None, sun_dir=None, height=1500.0, scale=0.00035,
                 speed=(6.0, 2.0), color=(1.0, 0.97, 0.94), shadow=(0.35, 0.33, 0.33), opacity=0.92,
                 evolve=0.05, sun_glow=1.5, sharp=0.15, detail=6.0):
    """Flat procedural cloud layer at `height` metres, composited in the world shader.
    coverage 0..1. speed = drift (m/s) in x, y. Animated via the mapping offset over the shot."""
    vn = T.vmath("NORMALIZE", view)
    vx, vy, vz = T.sep(vn)
    t = T.math("DIVIDE", height, T.math("MAXIMUM", vz, 0.03))
    px = T.math("MULTIPLY", vx, t)
    py = T.math("MULTIPLY", vy, t)
    off = _lattr(T, "env_cloud_offset", (0.0, 0.0, 0.0))
    p = T.vmath("ADD", T.comb(px, py, 0.0), off)
    p = T.vmath("SCALE", p, scale=scale)
    tw = _lattr(T, "env_cloud_time", 0.0)
    n = T.noise(p, scale=1.0, detail=detail, rough=0.62, dist=0.15, w=tw, dims="4D")
    lo = 0.68 - 0.36 * coverage
    mr = T.node("ShaderNodeMapRange")
    T.link(n.outputs["Fac"], mr.inputs[0])
    mr.inputs[1].default_value = lo
    mr.inputs[2].default_value = lo + sharp + 0.12 * (1 - coverage)
    mr.inputs[3].default_value = 0.0
    mr.inputs[4].default_value = 1.0
    dens = mr.outputs[0]
    # self shadowing: sample density offset towards the sun
    sd = Vector(sun_dir or (0, 1, 0.3))
    sh_off = (sd.x * 600 * scale, sd.y * 600 * scale, 0.0)
    p2 = T.vmath("ADD", p, sh_off)
    n2 = T.noise(p2, scale=1.0, detail=4.0, rough=0.62, dist=0.15, w=tw, dims="4D")
    mr2 = T.node("ShaderNodeMapRange")
    T.link(n2.outputs["Fac"], mr2.inputs[0])
    mr2.inputs[1].default_value = lo
    mr2.inputs[2].default_value = lo + 0.25
    lit = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", mr2.outputs[0], 0.85), clamp=True)
    ccol = T.mix(lit, tuple(shadow), tuple(color))
    # silver lining / forward scatter near the sun
    dot = T.vmath("DOT_PRODUCT", vn, tuple(sd.normalized()))
    fw = T.math("MULTIPLY", T.math("POWER", T.math("MAXIMUM", dot, 0.0), 12.0), sun_glow)
    ccol = T.mix(T.math("MULTIPLY", fw, T.math("SUBTRACT", 1.0, dens)), ccol, (1.0, 0.85, 0.6), blend="ADD")
    # sky brightness drives cloud brightness (clouds follow the HDRI exposure)
    lum = T.node("ShaderNodeRGBToBW")
    T.link(col, lum.inputs[0])
    lumb = T.math("ADD", T.math("MULTIPLY", lum.outputs[0], 1.1), 0.02)
    ccol = T.mix(1.0, ccol, T.comb(lumb, lumb, lumb), blend="MULTIPLY")
    hf = T.math("MULTIPLY", T.math("SUBTRACT", vz, 0.03), 8.0, clamp=True)
    scene_prop("env_cloud_opacity", opacity)
    k = _lattr(T, "env_cloud_opacity", opacity)
    a = T.math("MULTIPLY", T.math("MULTIPLY", dens, hf), k)
    if res is not None:
        res["nodes"].update(cloud_offset="env_cloud_offset", cloud_time="env_cloud_time", cloud_opacity="env_cloud_opacity")
    # animate drift over the whole scene range (scene props = uniforms, cheap)
    sc = bpy.context.scene
    f0, f1 = sc.frame_start, sc.frame_end
    for f in (f0, f1 + 1):
        tsec = (f - 1) / 24.0
        scene_prop("env_cloud_offset", (speed[0] * tsec, speed[1] * tsec, 0.0), f)
        scene_prop("env_cloud_time", evolve * tsec, f)
    _linear_keys(sc)
    return T.mix(a, col, ccol)


def _linear_keys(idblock, prefix=None):
    """Linear interpolation + extrapolation on an ID's fcurves. For the scene only env-owned curves
    (custom props '["env_...', exposure) are touched unless a prefix is given."""
    ad = getattr(idblock, "animation_data", None)
    if not ad or not ad.action:
        return
    if prefix is None and isinstance(idblock, bpy.types.Scene):
        prefix = ('["env_', "view_settings.exposure")
    for fc in C._fcurves(ad.action):
        if prefix and not fc.data_path.startswith(prefix):
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
        fc.extrapolation = "LINEAR"


# =============================================================================================
# Materials: anti-tiled multi-layer ground, limestone rock, tinting of Poly Haven materials
# =============================================================================================
def _tex(T, path, vec, noncolor=False, proj="FLAT", blend=0.2):
    n = T.node("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        n.image.colorspace_settings.name = "Non-Color"
    n.projection = proj
    if proj == "BOX":
        n.projection_blend = blend
    n.interpolation = "Linear"
    T.link(vec, n.inputs["Vector"])
    return n


def _antitile_maps(T, asset, coord, scale, rot2=1.13, scale2=0.71, mask=None, res="1k", keys=("diff", "rough", "nor"),
                   proj="FLAT"):
    """Sample a Poly Haven texture set twice (different scale/rotation/offset) and blend with a noise
    mask -> breaks visible repetition. Returns dict key -> socket (colour)."""
    maps = ph.texture_maps(asset, res)
    m1 = T.node("ShaderNodeMapping")
    m1.inputs["Scale"].default_value = (scale, scale, scale)
    T.link(coord, m1.inputs["Vector"])
    m2 = T.node("ShaderNodeMapping")
    m2.inputs["Scale"].default_value = (scale * scale2, scale * scale2, scale * scale2)
    m2.inputs["Rotation"].default_value = (0, 0, rot2)
    m2.inputs["Location"].default_value = (0.37, 0.71, 0.0)
    T.link(coord, m2.inputs["Vector"])
    out = {}
    for k in keys:
        if k not in maps:
            continue
        a = _tex(T, maps[k], m1.outputs[0], noncolor=(k != "diff"), proj=proj)
        if mask is None:
            out[k] = a.outputs["Color"]
            continue
        b = _tex(T, maps[k], m2.outputs[0], noncolor=(k != "diff"), proj=proj)
        out[k] = T.mix(mask, a.outputs["Color"], b.outputs["Color"])
    return out


def ground_material(name="EnvGround", style="golgotha", scale=0.33, macro=1.0, res="1k", rock_slope=0.72,
                    tint=None, grass_tint=None, wet=0.0):
    """Layered terrain material (no UVs; uses object XY):
      base soil (anti-tiled), pale cracked crust patches, limestone on steep slopes / 'rock' attribute,
      trodden 'path' attribute, macro colour variation, cavity darkening ('cav' attribute), distance
      fade of fine texture. style: 'golgotha' | 'hills' | 'plain' | 'grove' (palette/ texture choice)."""
    styles = {
        "golgotha": dict(base="dry_ground_rocks", crust="sandstone_cracks", rock="rock_boulder_dry", path="gravelly_sand",
                         base_tint=(1.0, 0.93, 0.8), crust_tint=(0.95, 0.9, 0.8), rock_tint=(1.0, 0.95, 0.86),
                         crust_amt=0.55, far=(0.5, 0.43, 0.33), sat=0.55, val=1.45),
        "hills": dict(base="dry_ground_rocks", crust="dry_ground_01", rock="rock_boulder_dry", path="gravelly_sand",
                      base_tint=(1.0, 0.86, 0.72), crust_tint=(1.0, 0.93, 0.82), rock_tint=(1.0, 0.96, 0.88),
                      crust_amt=0.35, far=(0.45, 0.37, 0.28)),
        "plain": dict(base="dry_ground_rocks", crust="gravelly_sand", rock="rock_boulder_dry", path="gravelly_sand",
                      base_tint=(1.0, 0.9, 0.76), crust_tint=(1.0, 0.92, 0.8), rock_tint=(1.0, 0.96, 0.88),
                      crust_amt=0.4, far=(0.46, 0.38, 0.27)),
        "grove": dict(base="brown_mud_leaves_01", crust="dry_decay_leaves", rock="rock_boulder_dry", path="dry_ground_rocks",
                      base_tint=(0.85, 0.8, 0.72), crust_tint=(0.8, 0.75, 0.65), rock_tint=(0.85, 0.83, 0.8),
                      crust_amt=0.5, far=(0.25, 0.22, 0.18)),
    }
    S = dict(styles[style])
    if tint:
        S["base_tint"] = tuple(S["base_tint"][i] * tint[i] for i in range(3))
        S["crust_tint"] = tuple(S["crust_tint"][i] * tint[i] for i in range(3))
        S["far"] = tuple(S["far"][i] * tint[i] for i in range(3))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    T = _NT(nt)
    bs = nt.nodes["Principled BSDF"]
    out = nt.nodes["Material Output"]
    tc = T.node("ShaderNodeTexCoord")
    co = tc.outputs["Object"]
    geo = T.node("ShaderNodeNewGeometry")
    nz = T.sep(geo.outputs["Normal"])[2]
    # masks -------------------------------------------------------------------------------
    n_at = T.noise(co, scale=0.11, detail=3, rough=0.5, dist=0.4)
    at = T.node("ShaderNodeMapRange")
    T.link(n_at.outputs["Fac"], at.inputs[0])
    at.inputs[1].default_value, at.inputs[2].default_value = 0.44, 0.56
    at_mask = at.outputs[0]
    n_cr = T.noise(co, scale=0.035, detail=5, rough=0.62, dist=0.6)
    crm = T.node("ShaderNodeMapRange")
    T.link(n_cr.outputs["Fac"], crm.inputs[0])
    thr = 0.62 - 0.25 * S["crust_amt"]
    crm.inputs[1].default_value, crm.inputs[2].default_value = thr, thr + 0.08
    crust_mask = crm.outputs[0]
    attr_rock = T.node("ShaderNodeAttribute")
    attr_rock.attribute_name = "rock"
    attr_path = T.node("ShaderNodeAttribute")
    attr_path.attribute_name = "path"
    attr_cav = T.node("ShaderNodeAttribute")
    attr_cav.attribute_name = "cav"
    attr_dust = T.node("ShaderNodeAttribute")
    attr_dust.attribute_name = "dust"
    # slope rock: normal.z below rock_slope -> rock, broken by noise
    n_sl = T.noise(co, scale=0.6, detail=3)
    slope = T.math("SUBTRACT", rock_slope, nz)
    slope = T.math("MULTIPLY", T.math("ADD", slope, T.math("MULTIPLY", T.math("SUBTRACT", n_sl.outputs["Fac"], 0.5), 0.25)), 9.0, clamp=True)
    rock_mask = T.math("MAXIMUM", slope, T.math("MULTIPLY", T.math("SUBTRACT", attr_rock.outputs["Fac"],
                                                                   T.math("MULTIPLY", n_sl.outputs["Fac"], 0.35)), 3.0, clamp=True))
    path_mask = T.math("MULTIPLY", T.math("SUBTRACT", attr_path.outputs["Fac"], T.math("MULTIPLY", n_at.outputs["Fac"], 0.4)), 2.5, clamp=True)
    crust_mask = T.math("MAXIMUM", crust_mask, T.math("MULTIPLY", attr_dust.outputs["Fac"], 0.8))
    # layers ------------------------------------------------------------------------------
    base = _antitile_maps(T, S["base"], co, scale, mask=at_mask, res=res)
    crust = _antitile_maps(T, S["crust"], co, scale * 0.8, rot2=2.1, scale2=0.83, mask=at_mask, res="1k")
    rock = _antitile_maps(T, S["rock"], co, scale * 0.6, mask=None, res="1k", proj="BOX")
    pth = _antitile_maps(T, S["path"], co, scale * 1.4, mask=None, res="1k", keys=("diff", "nor"))
    bcol = T.mix(1.0, base["diff"], S["base_tint"], blend="MULTIPLY")
    ccol = T.mix(1.0, crust["diff"], S["crust_tint"], blend="MULTIPLY")
    rcol = T.mix(1.0, rock["diff"], S["rock_tint"], blend="MULTIPLY")
    pcol = T.mix(1.0, pth["diff"], tuple(c * 1.05 for c in S["crust_tint"]), blend="MULTIPLY")
    col = T.mix(crust_mask, bcol, ccol)
    col = T.mix(path_mask, col, pcol)
    hsv = T.node("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = S.get("sat", 0.6)
    hsv.inputs["Value"].default_value = S.get("val", 1.1)
    T.link(col, hsv.inputs["Color"])
    col = T.mix(rock_mask, hsv.outputs["Color"], rcol)
    nor = T.mix(crust_mask, base["nor"], crust["nor"])
    nor = T.mix(path_mask, nor, pth["nor"])
    nor = T.mix(rock_mask, nor, rock["nor"])
    rgh = T.mix(crust_mask, base.get("rough", (0.85, 0.85, 0.85)), crust.get("rough", (0.85, 0.85, 0.85)))
    rgh = T.mix(rock_mask, rgh, rock.get("rough", (0.8, 0.8, 0.8)))
    # macro variation ----------------------------------------------------------------------
    n_m1 = T.noise(co, scale=0.012, detail=4, rough=0.55)
    n_m2 = T.noise(co, scale=0.0025, detail=3, rough=0.5)
    mv = T.ramp(n_m1.outputs["Fac"], [(0.3, (0.78, 0.74, 0.70)), (0.5, (1.0, 1.0, 1.0)), (0.72, (1.12, 1.08, 1.02))])
    mv2 = T.ramp(n_m2.outputs["Fac"], [(0.3, (0.9, 0.86, 0.8)), (0.7, (1.08, 1.04, 0.98))])
    col = T.mix(macro, col, mv.outputs[0], blend="MULTIPLY")
    col = T.mix(macro, col, mv2.outputs[0], blend="MULTIPLY")
    # cavity darkening + grass tint
    cav = T.math("MULTIPLY", attr_cav.outputs["Fac"], 0.55, clamp=True)
    col = T.mix(cav, col, (0.0, 0.0, 0.0))
    if grass_tint:
        attr_g = T.node("ShaderNodeAttribute")
        attr_g.attribute_name = "grass"
        gm = T.math("MULTIPLY", attr_g.outputs["Fac"], 0.6, clamp=True)
        col = T.mix(gm, col, tuple(grass_tint), blend="MULTIPLY")
    # distance fade of fine detail -> average colour (kills far tiling + shimmering)
    cam = T.node("ShaderNodeCameraData")
    fd = T.smooth(60.0, 400.0, cam.outputs["View Distance"])
    farc = T.mix(1.0, tuple(S["far"]), mv2.outputs[0], blend="MULTIPLY")
    farc = T.mix(macro, farc, mv.outputs[0], blend="MULTIPLY")
    col = T.mix(T.math("MULTIPLY", fd, 0.85), col, farc)
    T.link(col, bs.inputs["Base Color"])
    rg = T.node("ShaderNodeRGBToBW")
    T.link(rgh, rg.inputs[0])
    T.link(T.math("MULTIPLY_ADD", rg.outputs[0], 0.25, 0.72 - 0.4 * wet, clamp=True), bs.inputs["Roughness"])
    nm = T.node("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = 1.0
    T.link(nor, nm.inputs["Color"])
    nstr = T.math("SUBTRACT", 1.0, fd)
    T.link(nstr, nm.inputs["Strength"])
    T.link(nm.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Specular IOR Level"].default_value = 0.3
    hazify(m)
    return m


def tint_material(mat, sat=None, tint=None, value=None, rand=0.0, rough_add=0.0, haze=True, name=None):
    """Colour-correct a (Poly Haven) material in place: insert HSV + multiply tint on Base Color,
    optional per-object/instance random brightness (rand 0..1), roughness offset, haze."""
    if mat is None or not mat.use_nodes:
        return mat
    if name:
        mat.name = name
    nt = mat.node_tree
    T = _NT(nt)
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        return hazify(mat) if haze else mat
    inp = b.inputs["Base Color"]
    if inp.is_linked:
        src = inp.links[0].from_socket
    else:
        rgbn = T.rgb(tuple(inp.default_value[:3]))
        src = rgbn.outputs[0]
    col = src
    if sat is not None or value is not None:
        hs = T.node("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = 1.0 if sat is None else sat
        hs.inputs["Value"].default_value = 1.0 if value is None else value
        T.link(col, hs.inputs["Color"])
        col = hs.outputs["Color"]
    if tint:
        col = T.mix(1.0, col, tuple(tint), blend="MULTIPLY")
    if rand:
        oi = T.node("ShaderNodeObjectInfo")
        r = T.math("MULTIPLY_ADD", oi.outputs["Random"], rand, 1.0 - rand * 0.5)
        col = T.mix(1.0, col, T.comb(r, r, r), blend="MULTIPLY")
    T.link(col, inp)
    if rough_add:
        ri = b.inputs["Roughness"]
        if ri.is_linked:
            s = ri.links[0].from_socket
            T.link(T.math("ADD", s, rough_add, clamp=True), ri)
        else:
            ri.default_value = min(1.0, ri.default_value + rough_add)
    if haze:
        hazify(mat)
    return mat


def limestone_material(name="EnvLimestone", scale=0.5, tint=(1.0, 0.95, 0.86), dark=0.0, streaks=0.5, strata=0.0,
                       cav_dark=0.85):
    """Pale Jerusalem limestone (box-projected, object space) with vertical weathering streaks;
    uses 'cav' point attribute (0..1) when present for crevice darkening."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    T = _NT(nt)
    bs = nt.nodes["Principled BSDF"]
    tc = T.node("ShaderNodeTexCoord")
    co = tc.outputs["Object"]
    a = _antitile_maps(T, "rock_boulder_dry", co, scale, mask=None, res="2k", proj="BOX")
    b = _antitile_maps(T, "rock_face_03", co, scale * 0.7, mask=None, res="1k", proj="BOX", keys=("diff", "nor"))
    nmix = T.noise(co, scale=0.15, detail=3, dist=0.5)
    mk = T.node("ShaderNodeMapRange")
    T.link(nmix.outputs["Fac"], mk.inputs[0])
    mk.inputs[1].default_value, mk.inputs[2].default_value = 0.45, 0.62
    col = T.mix(T.math("MULTIPLY", mk.outputs[0], 0.6), a["diff"], b["diff"])
    nor = T.mix(T.math("MULTIPLY", mk.outputs[0], 0.6), a["nor"], b["nor"])
    col = T.mix(1.0, col, tuple(tint), blend="MULTIPLY")
    if streaks:
        # vertical dark weathering streaks: noise stretched along Z
        mp = T.node("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1.6, 1.6, 0.12)
        T.link(co, mp.inputs["Vector"])
        sn = T.noise(mp.outputs[0], scale=1.0, detail=5, rough=0.6)
        sm = T.node("ShaderNodeMapRange")
        T.link(sn.outputs["Fac"], sm.inputs[0])
        sm.inputs[1].default_value, sm.inputs[2].default_value = 0.5, 0.75
        col = T.mix(T.math("MULTIPLY", sm.outputs[0], streaks * 0.55), col, (0.18, 0.15, 0.12), blend="MULTIPLY")
    if strata:
        sep = T.sep(co)
        wv = T.node("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "Z"
        wv.inputs["Scale"].default_value = 0.9
        wv.inputs["Distortion"].default_value = 6.0
        wv.inputs["Detail"].default_value = 3.0
        T.link(co, wv.inputs["Vector"])
        col = T.mix(T.math("MULTIPLY", wv.outputs["Fac"], strata * 0.35), col, (0.55, 0.5, 0.45), blend="MULTIPLY")
    cav = T.node("ShaderNodeAttribute")
    cav.attribute_name = "cav"
    col = T.mix(T.math("MULTIPLY", cav.outputs["Fac"], cav_dark, clamp=True), col, (0.05, 0.04, 0.03))
    if dark:
        col = T.mix(dark, col, (0.0, 0.0, 0.0))
    oi = T.node("ShaderNodeObjectInfo")
    r = T.math("MULTIPLY_ADD", oi.outputs["Random"], 0.25, 0.88)
    col = T.mix(1.0, col, T.comb(r, r, r), blend="MULTIPLY")
    T.link(col, bs.inputs["Base Color"])
    if "rough" in a:
        rg = T.node("ShaderNodeRGBToBW")
        T.link(a["rough"], rg.inputs[0])
        T.link(T.math("MULTIPLY_ADD", rg.outputs[0], 0.3, 0.65, clamp=True), bs.inputs["Roughness"])
    nm = T.node("ShaderNodeNormalMap")
    T.link(nor, nm.inputs["Color"])
    T.link(nm.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Specular IOR Level"].default_value = 0.35
    hazify(m)
    return m


# =============================================================================================
# Prototypes (decimated Poly Haven models + generated plants), cached to /opt/assets/env/protos
# =============================================================================================
PROTO_DIR = os.path.join(ENV_CACHE, "protos")


def _proto_coll():
    st = _state()
    c = st.get("proto_coll")
    if c is None or c.name not in bpy.data.collections:
        c = bpy.data.collections.new("ENV_Protos")
        c.use_fake_user = True
        st["proto_coll"] = c
    return c


def _load_cached(path, prefix):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith(prefix)]
    objs = [o for o in dst.objects if o is not None]
    _remap_haze(objs)
    return objs


def _remap_haze(objs):
    """Materials loaded from cache files carry their own copy of ENV_Haze: point them at this scene's
    global haze group so set_haze() controls everything."""
    g = haze_group()
    dup = set()
    for o in objs:
        for ms in getattr(o.data, "materials", []):
            if not ms or not ms.use_nodes:
                continue
            for n in ms.node_tree.nodes:
                if n.type == "GROUP" and n.node_tree and n.node_tree.name.startswith("ENV_Haze") and n.node_tree != g:
                    dup.add(n.node_tree)
                    n.node_tree = g
    for d in dup:
        if d.users == 0:
            bpy.data.node_groups.remove(d)


def _save_cached(path, objs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path[:-6] + ".part%d.blend" % os.getpid()
    data = set(objs)
    for o in objs:
        data.add(o.data)
        for ms in o.data.materials:
            if ms:
                data.add(ms)
    bpy.data.libraries.write(tmp, data, fake_user=True, compress=False, path_remap="ABSOLUTE")
    os.replace(tmp, path)


def _bake_object(o, name, decimate=1.0, dg=None):
    """Evaluated + world-transformed copy of mesh object `o`, decimated, origin at bottom centre."""
    dg = dg or bpy.context.evaluated_depsgraph_get()
    if decimate < 0.999:
        md = o.modifiers.new("dec", "DECIMATE")
        md.ratio = decimate
        md.use_collapse_triangulate = True
        dg.update()
    ev = o.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
    me.transform(o.matrix_world)
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mn, mx = co.min(0), co.max(0)
    me.transform(Matrix.Translation((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2])))
    me.name = name
    ob = bpy.data.objects.new(name, me)
    ob["dims"] = [float(x) for x in (mx - mn)]
    return ob


def ph_protos(asset, max_polys=12000, res="1k", min_size=0.0):
    """Load a Poly Haven model as a list of prototype objects (one per distinct mesh in the asset; the
    best LOD with <= max_polys faces is used, else the smallest LOD decimated). Origins at bottom
    centre, not linked to the scene (use place()/scatter()). Cached on disk in /opt/assets/env/protos."""
    import re
    st = _state()
    key = ("ph", asset, max_polys, res)
    if key in st["protos"]:
        return st["protos"][key]
    prefix = "P_%s_%d" % (asset, max_polys)
    path = os.path.join(PROTO_DIR, "%s_%s_%d.blend" % (asset, res, max_polys))
    objs = None
    if os.path.exists(path):
        try:
            objs = _load_cached(path, prefix)
        except Exception as e:
            print("env: proto cache load failed", path, e)
            objs = None
    if not objs:
        src = [o for o in C.append_blend(ph.model_blend(asset, res), kind="objects") if o is not None]
        groups = {}
        for o in src:
            if o.type != "MESH" or o.name.endswith("_geometry_nodes"):
                continue
            base = re.sub(r"_LOD\d+$", "", o.name)
            base = re.sub(r"_geo$", "", base)
            groups.setdefault(base, []).append(o)
        dg = bpy.context.evaluated_depsgraph_get()
        objs = []
        for i, base in enumerate(sorted(groups)):
            cands = sorted(groups[base], key=lambda o: len(o.data.polygons))
            ok = [o for o in cands if len(o.data.polygons) <= max_polys]
            pick = ok[-1] if ok else cands[0]
            dec = 1.0 if ok else max_polys / max(1, len(pick.data.polygons))
            objs.append(_bake_object(pick, "%s_%02d" % (prefix, i), dec, dg))
        for o in src:
            bpy.data.objects.remove(o, do_unlink=True)
        try:
            _save_cached(path, objs)
        except Exception as e:
            print("env: proto cache save failed", e)
    objs = [o for o in objs if max(o.get("dims", [1, 1, 1])) >= min_size]
    st["protos"][key] = objs
    return objs


# =============================================================================================
# Scatter (Geometry Nodes instancing of prototypes on raycast points)
# =============================================================================================
def _scatter_group():
    ng = bpy.data.node_groups.get("ENV_ScatterGN")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("ENV_ScatterGN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Collection", in_out="INPUT", socket_type="NodeSocketCollection")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo")
    ci.transform_space = "ORIGINAL"
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    L.new(gi.outputs[1], ci.inputs["Collection"])
    iop = N.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    L.new(gi.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])

    def na(name, dt):
        n = N.new("GeometryNodeInputNamedAttribute")
        n.data_type = dt
        n.inputs["Name"].default_value = name
        return n

    L.new(na("idx", "INT").outputs["Attribute"], iop.inputs["Instance Index"])
    e2r = N.new("FunctionNodeEulerToRotation")
    L.new(na("rot", "FLOAT_VECTOR").outputs["Attribute"], e2r.inputs[0])
    L.new(e2r.outputs[0], iop.inputs["Rotation"])
    L.new(na("scl", "FLOAT_VECTOR").outputs["Attribute"], iop.inputs["Scale"])
    L.new(iop.outputs[0], go.inputs[0])
    return ng


def instancer(name, protos, pos, rot, scl, idx, coll=None):
    """Create a GN instancer object: points `pos` (N,3) get prototype `idx` (N,) with euler `rot` (N,3)
    and scale `scl` (N,3). protos: list of prototype objects (instanced via a hidden collection)."""
    pc = bpy.data.collections.new(name + "_protos")
    pc.use_fake_user = True
    for i, p in enumerate(protos):
        # collection children are sorted by name for Pick Instance -> make the order explicit
        try:
            pc.objects.link(p)
        except RuntimeError:
            pass
    order = sorted(pc.objects, key=lambda o: o.name)
    remap = {p.name: order.index(p) for p in protos if p in order}
    idx = np.array([remap[protos[i].name] for i in idx], dtype=np.int32)
    pos = np.asarray(pos, np.float32).reshape(-1, 3)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pos))
    me.vertices.foreach_set("co", pos.ravel())
    me.update()
    ob = C.link(bpy.data.objects.new(name, me), coll)
    set_attr(ob, "idx", idx, "INT")
    set_attr(ob, "rot", np.asarray(rot, np.float32).reshape(-1, 3), "FLOAT_VECTOR")
    set_attr(ob, "scl", np.asarray(scl, np.float32).reshape(-1, 3), "FLOAT_VECTOR")
    md = ob.modifiers.new("scatter", "NODES")
    md.node_group = _scatter_group()
    ident = md.node_group.interface.items_tree["Collection"].identifier
    md[ident] = pc
    ob["n_instances"] = len(pos)
    return ob


def _region_points(region, n, rnd):
    """Random XY points in region: (x0, y0, x1, y1) rect | ('circle', cx, cy, r) | ('ring', cx, cy, r0, r1)
    | callable(rnd, n) -> (n,2)."""
    if callable(region):
        return np.asarray(region(rnd, n), float)
    if region[0] == "circle":
        _, cx, cy, r = region
        a = rnd.uniform(0, 2 * np.pi, n)
        d = r * np.sqrt(rnd.uniform(0, 1, n))
        return np.c_[cx + d * np.cos(a), cy + d * np.sin(a)]
    if region[0] == "ring":
        _, cx, cy, r0, r1 = region
        a = rnd.uniform(0, 2 * np.pi, n)
        d = np.sqrt(rnd.uniform(r0 * r0, r1 * r1, n))
        return np.c_[cx + d * np.cos(a), cy + d * np.sin(a)]
    x0, y0, x1, y1 = region
    return np.c_[rnd.uniform(x0, x1, n), rnd.uniform(y0, y1, n)]


def scatter(objects, terrain=None, count=100, region=(-50, -50, 50, 50), seed=0, scale=(0.7, 1.3), align=0.3,
            sink=0.05, max_slope=None, min_slope=None, zrange=None, density=None, exclude=(), min_dist=0.0,
            tilt=0.0, weights=None, name="Scatter", coll=None, zscale=None, yaw=(0, 360), return_points=False):
    """Scatter prototype objects on the ground with raycast placement (GN instances, cheap).
      objects: list of prototype objects, or Poly Haven asset names (decimated automatically), or a mix.
      terrain: object(s) to raycast (default: all env grounds registered so far).
      count: number of attempts (points rejected by masks are dropped).
      region: (x0, y0, x1, y1) | ('circle', cx, cy, r) | ('ring', cx, cy, r0, r1) | callable(rnd, n).
      scale: (min, max) uniform scale (or a float). zscale: optional (min, max) extra Z scale.
      align: 0 = upright, 1 = aligned to the ground normal. tilt: random tilt in degrees.
      sink: metres pushed below the surface (fraction of instance height if < 0: e.g. -0.2 buries 20%).
      max_slope/min_slope: degrees. zrange: (zmin, zmax). density: f(x, y)->0..1 (vectorised) probability.
      exclude: [(x, y, r), ...] keep-out circles. min_dist: Poisson-ish rejection distance.
      weights: per-object selection weights.
    Returns the instancer object (and (pos, idx) when return_points=True)."""
    protos = []
    for o in objects:
        if isinstance(o, str):
            protos.extend(ph_protos(o))
        else:
            protos.append(o)
    rnd = np.random.default_rng(seed)
    pts = _region_points(region, count, rnd)
    if density is not None:
        keep = rnd.uniform(0, 1, len(pts)) < np.clip(density(pts[:, 0], pts[:, 1]), 0, 1)
        pts = pts[keep]
    if len(exclude):
        ex = np.asarray(exclude, float).reshape(-1, 3)
        d2 = (pts[:, None, 0] - ex[None, :, 0]) ** 2 + (pts[:, None, 1] - ex[None, :, 1]) ** 2
        pts = pts[(d2 > ex[None, :, 2] ** 2).all(axis=1)]
    if min_dist > 0 and len(pts):
        cell = {}
        kept = []
        for p in pts:
            k = (int(p[0] // min_dist), int(p[1] // min_dist))
            ok = True
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for q in cell.get((k[0] + dx, k[1] + dy), ()):
                        if (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < min_dist * min_dist:
                            ok = False
                            break
            if ok:
                kept.append(p)
                cell.setdefault(k, []).append(p)
        pts = np.array(kept).reshape(-1, 2)
    terr = [terrain] if isinstance(terrain, bpy.types.Object) else terrain
    bvh = _bvh(terr)
    w = np.asarray(weights if weights is not None else [1.0] * len(protos), float)
    w = w / w.sum()
    P, R, S, I = [], [], [], []
    for x, y in pts:
        hit = bvh.ray_cast(Vector((x, y, 5000.0)), Vector((0, 0, -1)))
        if hit[0] is None:
            continue
        n = hit[1] if hit[1].z >= 0 else -hit[1]
        sl = math.degrees(math.acos(max(-1, min(1, n.z))))
        if max_slope is not None and sl > max_slope:
            continue
        if min_slope is not None and sl < min_slope:
            continue
        z = hit[0].z
        if zrange and not (zrange[0] <= z <= zrange[1]):
            continue
        i = int(rnd.choice(len(protos), p=w))
        s = scale if isinstance(scale, (int, float)) else rnd.uniform(scale[0], scale[1])
        sz = s * (rnd.uniform(*zscale) if zscale else 1.0)
        yaw_ = math.radians(rnd.uniform(*yaw))
        # orientation: blend up with normal, add random tilt
        up = Vector((0, 0, 1)).lerp(n, align).normalized()
        if tilt:
            up = (Matrix.Rotation(math.radians(rnd.normal(0, tilt)), 3, "X") @
                  Matrix.Rotation(math.radians(rnd.normal(0, tilt)), 3, "Y") @ up).normalized()
        q = up.to_track_quat("Z", "Y") @ Euler((0, 0, yaw_)).to_quaternion()
        e = q.to_euler()
        h = protos[i].get("dims", [1, 1, 1])[2] * sz
        sk = sink if sink >= 0 else -sink * h
        P.append((x, y, z - sk))
        R.append(tuple(e))
        S.append((s, s, sz))
        I.append(i)
    if not P:
        P, R, S, I = [(0, 0, -10000)], [(0, 0, 0)], [(0.0, 0.0, 0.0)], [0]
    ob = instancer(name, protos, P, R, S, I, coll)
    if return_points:
        return ob, np.array(P), np.array(I)
    return ob


def place(proto, loc, rot=(0, 0, 0), scale=1.0, name=None, coll=None):
    """Place one linked copy of a prototype object (shares mesh). rot in degrees."""
    o = bpy.data.objects.new(name or proto.name + "_i", proto.data)
    C.link(o, coll)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    o.scale = (scale, scale, scale) if isinstance(scale, (int, float)) else scale
    return o


def rock_protos(kind="boulders", tint=(1.0, 0.95, 0.86), sat=0.35, value=1.15, decimate=None):
    # decimate: optional max_polys override per asset
    """Limestone-tinted Poly Haven rock prototypes. kind: 'boulders' (0.7-3 m), 'rocks' (0.1-0.6 m),
    'stones' (pebbles), 'cliff'. Returns list of prototype objects (materials tinted + hazed)."""
    sets = {"boulders": [("namaqualand_boulder_05", 12000), ("namaqualand_boulder_06", 14000), ("boulder_01", 9000),
                         ("namaqualand_boulder_02", 13000), ("namaqualand_boulder_03", 9000)],
            "rocks": [("namaqualand_rocks_01", 3500), ("namaqualand_boulders_01", 3500), ("stone_01", 1700)],
            "stones": [("namaqualand_stones_01", 1500), ("rock_09", 1600)],
            "cliff": [("rock_face_01", 21000), ("namaqualand_cliff_02", 25000)]}
    st = _state()
    key = ("rocks", kind, tuple(tint), sat, value)
    if key in st["protos"]:
        return st["protos"][key]
    out = []
    mkey = ("rockmat", tuple(tint), value)
    if mkey not in st["protos"]:
        st["protos"][mkey] = limestone_material("EnvRockStone", scale=0.9, tint=tuple(t * value * 0.9 for t in tint),
                                                streaks=0.35)
    rm = st["protos"][mkey]
    for asset, mp in sets[kind]:
        for p in ph_protos(asset, decimate if decimate else mp):
            # one shared (box-projected) limestone material for every rock: fewer shaders to compile
            # (EEVEE on llvmpipe pays ~100 MB + seconds per unique material)
            p.data.materials.clear()
            p.data.materials.append(rm)
            out.append(p)
    st["protos"][key] = out
    return out


# =============================================================================================
# Procedural plants: grass tufts, branching trees (olive / dead tree / thorn bush)
# =============================================================================================
def _cached_proto(key, builder):
    """Build-or-load a generated prototype object (cached in /opt/assets/env/protos/gen_<key>.blend)."""
    st = _state()
    if key in st["protos"]:
        return st["protos"][key]
    name = "G_" + key
    path = os.path.join(PROTO_DIR, "gen_%s.blend" % key)
    obj = None
    if os.path.exists(path):
        try:
            got = _load_cached(path, name)
            obj = next((o for o in got if o.name == name), got[0] if got else None)
        except Exception as e:
            print("env: gen cache load failed", e)
    if obj is None:
        obj = builder(name)
        try:
            _save_cached(path, [obj])
        except Exception as e:
            print("env: gen cache save failed", e)
    st["protos"][key] = obj
    return obj


def grass_material(name="EnvGrass", color=(0.62, 0.5, 0.3), root=(0.25, 0.2, 0.12), var=0.25):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    T = _NT(m.node_tree)
    bs = m.node_tree.nodes["Principled BSDF"]
    at = T.node("ShaderNodeAttribute")
    at.attribute_name = "h"          # 0 at root .. 1 at tip
    oi = T.node("ShaderNodeObjectInfo")
    col = T.mix(T.math("POWER", at.outputs["Fac"], 0.6), tuple(root), tuple(color))
    # per-instance hue/brightness variation (some greener, some bleached)
    r = oi.outputs["Random"]
    col = T.mix(T.math("MULTIPLY", r, var * 0.5), col, (0.4, 0.4, 0.26))
    col = T.mix(T.math("MULTIPLY", T.math("SUBTRACT", 1.0, r), var * 0.8), col, (0.85, 0.76, 0.56))
    T.link(col, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.7
    bs.inputs["Specular IOR Level"].default_value = 0.35
    bs.inputs["Subsurface Weight"].default_value = 0.0
    # translucency for backlight
    tr = T.node("ShaderNodeBsdfTranslucent")
    T.link(col, tr.inputs["Color"])
    ms = T.node("ShaderNodeMixShader")
    ms.inputs[0].default_value = 0.3
    out = m.node_tree.nodes["Material Output"]
    T.link(bs.outputs[0], ms.inputs[1])
    T.link(tr.outputs[0], ms.inputs[2])
    T.link(ms.outputs[0], out.inputs["Surface"])
    hazify(m)
    return m


def grass_tuft(seed=0, blades=60, height=0.4, spread=0.14, width=0.0035, color=(0.62, 0.5, 0.3), droop=0.5,
               name=None, material=None):
    """Procedural dry grass tuft (fine tapered blades, 4 tris/blade). Returns a prototype object."""
    key = "tuft2_%d_%d_%d_%d_%d" % (seed, blades, int(height * 100), int(droop * 100), int(spread * 100))

    def build(nm):
        rnd = random.Random(seed)
        V, F, H = [], [], []
        seg = 2
        for b in range(blades):
            a = rnd.uniform(0, 2 * math.pi)
            r0 = spread * 0.3 * math.sqrt(rnd.random())
            base = Vector((math.cos(a) * r0, math.sin(a) * r0, -0.02))
            out = Vector((math.cos(a + rnd.uniform(-0.4, 0.4)), math.sin(a + rnd.uniform(-0.4, 0.4)), 0))
            hgt = height * (rnd.uniform(0.35, 1.1) if rnd.random() > 0.15 else rnd.uniform(0.12, 0.3))
            lean = rnd.uniform(0.1, 0.8)
            dr = droop * rnd.uniform(0.3, 1.2)
            w = width * rnd.uniform(0.6, 1.4)
            side = out.cross(Vector((0, 0, 1))).normalized()
            i0 = len(V)
            for k in range(seg + 1):
                t = k / seg
                pos = base + out * (hgt * (lean * 0.6 * t + dr * 0.5 * t * t)) + Vector((0, 0, hgt * (t - dr * 0.3 * t * t)))
                ww = w * (1 - t) + 0.0003
                V.append(tuple(pos - side * ww))
                V.append(tuple(pos + side * ww))
                H += [t, t]
            for k in range(seg):
                a0 = i0 + 2 * k
                F.append((a0, a0 + 1, a0 + 3, a0 + 2))
        o = mesh_from_numpy(nm, V, F, smooth=True)
        bpy.context.scene.collection.objects.unlink(o)
        set_attr(o, "h", H)
        o.data.materials.append(material or grass_material(color=color))
        o["dims"] = [spread * 2, spread * 2, height]
        return o
    return _cached_proto(key, build)


def grass_protos(kind="dry", n=4, height=0.4):
    """A few grass tuft variants. kind 'dry' (golden straw), 'green' (spring, grey-green), 'short'."""
    col = {"dry": (0.66, 0.55, 0.36), "green": (0.32, 0.36, 0.18), "short": (0.6, 0.52, 0.36)}[kind]
    h = height * (0.5 if kind == "short" else 1.0)
    st = _state()
    key = ("grassmat", kind)
    if key not in st["protos"]:
        st["protos"][key] = grass_material("EnvGrass_" + kind, color=col,
                                           root=(0.2, 0.18, 0.1) if kind != "green" else (0.12, 0.13, 0.06))
    m = st["protos"][key]
    return [grass_tuft(seed=i + (100 if kind == "green" else 0), blades=50 + 12 * i, height=h * (0.8 + 0.15 * i),
                       droop=0.35 + 0.15 * (i % 3), material=m) for i in range(n)]


def bark_material(name="EnvBark", asset="tree_bark_03", tint=(0.62, 0.6, 0.55), sat=0.5, scale=1.0, dead=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    T = _NT(m.node_tree)
    bs = m.node_tree.nodes["Principled BSDF"]
    uv = T.node("ShaderNodeUVMap")
    maps = ph.texture_maps(asset, "1k")
    mp = T.node("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    T.link(uv.outputs[0], mp.inputs["Vector"])
    d = _tex(T, maps["diff"], mp.outputs[0])
    hs = T.node("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = sat
    T.link(d.outputs["Color"], hs.inputs["Color"])
    col = T.mix(1.0, hs.outputs["Color"], tuple(tint), blend="MULTIPLY")
    oi = T.node("ShaderNodeObjectInfo")
    r = T.math("MULTIPLY_ADD", oi.outputs["Random"], 0.3, 0.85)
    col = T.mix(1.0, col, T.comb(r, r, r), blend="MULTIPLY")
    if dead:
        col = T.mix(0.35, col, (0.55, 0.53, 0.5))
    T.link(col, bs.inputs["Base Color"])
    if "rough" in maps:
        rg = _tex(T, maps["rough"], mp.outputs[0], noncolor=True)
        T.link(T.math("MULTIPLY_ADD", rg.outputs["Color"], 0.3, 0.65, clamp=True), bs.inputs["Roughness"])
    if "nor" in maps:
        nn = _tex(T, maps["nor"], mp.outputs[0], noncolor=True)
        nm = T.node("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 1.4
        T.link(nn.outputs["Color"], nm.inputs["Color"])
        T.link(nm.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Specular IOR Level"].default_value = 0.3
    hazify(m)
    return m


def leaf_material(name="EnvOliveLeaf", top=(0.10, 0.13, 0.065), under=(0.36, 0.40, 0.31), trans=0.25, dry=0.0):
    """Olive leaf: dark grey-green top, silvery underside (Backfacing), slight translucency."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    T = _NT(m.node_tree)
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    geo = T.node("ShaderNodeNewGeometry")
    oi = T.node("ShaderNodeObjectInfo")
    at = T.node("ShaderNodeAttribute")
    at.attribute_name = "lv"      # per-leaf random value
    col = T.mix(geo.outputs["Backfacing"], tuple(top), tuple(under))
    v = T.math("MULTIPLY_ADD", at.outputs["Fac"], 0.5, 0.75)
    col = T.mix(1.0, col, T.comb(v, v, T.math("MULTIPLY", v, 0.9)), blend="MULTIPLY")
    col = T.mix(T.math("MULTIPLY", at.outputs["Fac"], 0.25 + dry), col, (0.42, 0.36, 0.2))
    r = T.math("MULTIPLY_ADD", oi.outputs["Random"], 0.25, 0.88)
    col = T.mix(1.0, col, T.comb(r, r, r), blend="MULTIPLY")
    T.link(col, bs.inputs["Base Color"])
    rough = T.mixf(geo.outputs["Backfacing"], 0.42, 0.7)
    T.link(rough, bs.inputs["Roughness"])
    bs.inputs["Specular IOR Level"].default_value = 0.5
    bs.inputs["Sheen Weight"].default_value = 0.3
    tr = T.node("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.22, 0.26, 0.1, 1)
    ms = T.node("ShaderNodeMixShader")
    ms.inputs[0].default_value = trans
    T.link(bs.outputs[0], ms.inputs[1])
    T.link(tr.outputs[0], ms.inputs[2])
    T.link(ms.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    hazify(m)
    return m


def _twig_geometry(rnd, n_leaves=16, length=0.3, leaf_len=0.075, leaf_w=0.014, droop=0.3):
    """Olive twig along +Y: thin stem + opposite pairs of narrow leaves (each leaf = 2 tris folded
    along the midrib). Returns (verts (N,3), faces, mat index per face (0 stem, 1 leaf), leaf rand)."""
    V, F, M, LV = [], [], [], []
    k = 3
    r = 0.003
    bend = -droop * 0.06
    for i, y in enumerate((0.0, length)):
        for j in range(k):
            a = 2 * math.pi * j / k
            V.append((math.cos(a) * r * (1 - 0.6 * i), y, math.sin(a) * r * (1 - 0.6 * i) + bend * i))
            LV.append(0.0)
    for j in range(k):
        F.append((j, (j + 1) % k, k + (j + 1) % k, k + j))
        M.append(0)
    npairs = max(1, n_leaves // 2)
    for pi in range(npairs):
        t = 0.1 + 0.9 * pi / max(1, npairs - 1)
        y = length * t
        base = Vector((0, y, bend * t * t))
        rot = rnd.uniform(-0.4, 0.4) + (pi % 2) * (math.pi / 2) * 0.6     # decussate-ish
        for side in (1, -1):
            ang = math.radians(rnd.uniform(28, 55)) * (0.75 + 0.25 * t)
            L = leaf_len * rnd.uniform(0.75, 1.2) * (0.65 + 0.35 * t)
            W = leaf_w * rnd.uniform(0.8, 1.2)
            sideways = Vector((side * math.cos(rot), 0, side * math.sin(rot)))
            dirv = (sideways * math.sin(ang) + Vector((0, math.cos(ang), 0))).normalized()
            dirv.z -= droop * 0.25 * rnd.random()
            dirv.normalize()
            up = Vector((0, 0, 1))
            wv = dirv.cross(up)
            if wv.length < 1e-4:
                wv = Vector((1, 0, 0))
            wv.normalize()
            up = wv.cross(dirv).normalized()
            twist = Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, dirv)
            wv, up = twist @ wv, twist @ up
            fold = 0.3 * W
            i0 = len(V)
            lv = rnd.random()
            for p in (base, base + dirv * (L * 0.4) + wv * W + up * fold, base + dirv * L,
                      base + dirv * (L * 0.4) - wv * W + up * fold):
                V.append(tuple(p))
                LV.append(lv)
            F += [(i0, i0 + 1, i0 + 2), (i0, i0 + 2, i0 + 3)]
            M += [1, 1]
    # terminal leaf pair
    return np.array(V, np.float64), F, M, np.array(LV, np.float32)


def _frames(pts):
    """Parallel-transport frames along a polyline. Returns tangents, normals, binormals."""
    n = len(pts)
    T = []
    for i in range(n):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        T.append((b - a).normalized())
    N = []
    t0 = T[0]
    ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    nrm = t0.cross(ref).normalized()
    for i in range(n):
        if i > 0:
            ax = T[i - 1].cross(T[i])
            if ax.length > 1e-8:
                ang = T[i - 1].angle(T[i])
                nrm = Matrix.Rotation(ang, 3, ax.normalized()) @ nrm
        N.append(nrm.copy())
    B = [T[i].cross(N[i]) for i in range(n)]
    return T, N, B


class _TreeBuilder:
    """Generates branch skeletons + tube meshes with UVs + leaf twig placements."""

    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.V, self.F, self.UV, self.MAT = [], [], [], []
        self.twigs = []          # (matrix 4x4)
        self.branches = []

    def tube(self, pts, rads, sides=8, bark_tile=0.6, noise_amp=0.15, mat=0, seed=0, flare=None):
        Tn, Nn, Bn = _frames(pts)
        i0 = len(self.V)
        s = 0.0
        ring = sides + 1
        for i, p in enumerate(pts):
            if i > 0:
                s += (pts[i] - pts[i - 1]).length
            r = rads[i]
            for j in range(ring):
                a = 2 * math.pi * j / sides
                d = Nn[i] * math.cos(a) + Bn[i] * math.sin(a)
                # bark bumps / fluting
                nz = C.noise.noise(Vector((p.x * 3.1 + seed, p.y * 3.1, p.z * 3.1)) + d * 0.6)
                fl = 1.0 + noise_amp * nz
                if flare:
                    fl *= 1.0 + flare(s, a)
                q = p + d * (r * fl)
                self.V.append((q.x, q.y, q.z))
                circ = 2 * math.pi * max(r, 0.01)
                self.UV.append((j / sides * max(1.0, round(circ / bark_tile)), s / bark_tile))
        n = len(pts)
        for i in range(n - 1):
            for j in range(sides):
                a = i0 + i * ring + j
                self.F.append((a, a + 1, a + ring + 1, a + ring))
                self.MAT.append(mat)

    def grow(self, origin, direction, length, radius, level, spec, parent_len=None):
        sp = spec["levels"][min(level, len(spec["levels"]) - 1)]
        nseg = max(2, int(math.ceil(length / sp["seg"])))
        pts, rads = [Vector(origin)], [radius]
        d = Vector(direction).normalized()
        p = Vector(origin)
        rnd = self.rnd
        for i in range(1, nseg + 1):
            t = i / nseg
            jitter = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))) * sp["gnarl"]
            d = (d + jitter + Vector((0, 0, sp["up"])) + Vector((d.x, d.y, 0)) * sp.get("spread", 0.0)).normalized()
            if d.z < spec.get("min_dz", -1.0):
                d.z = spec.get("min_dz", -1.0)
                d.normalize()
            p = p + d * (length / nseg)
            if p.z < spec.get("min_z", -10.0):
                p.z = spec.get("min_z", -10.0)
            pts.append(p.copy())
            rads.append(max(radius * (1 - t * sp["taper"]), sp.get("rmin", 0.003)))
        self.branches.append((pts, rads, level))
        self.tube(pts, rads, sides=sp["sides"], noise_amp=sp.get("bump", 0.1), seed=level * 13.7 + len(self.branches))
        # children
        if level + 1 < len(spec["levels"]):
            cs = spec["levels"][level + 1]
            nch = cs["n"] if isinstance(cs["n"], int) else rnd.randint(*cs["n"])
            for c in range(nch):
                t = rnd.uniform(cs["start"], 0.98)
                fi = t * (len(pts) - 1)
                i = int(fi)
                f = fi - i
                i2 = min(i + 1, len(pts) - 1)
                pos = pts[i].lerp(pts[i2], f)
                pr = rads[i] + (rads[i2] - rads[i]) * f
                pd = (pts[i2] - pts[i]).normalized() if i2 != i else d
                # rotate parent dir by angle around a random perpendicular axis
                ref = Vector((0, 0, 1)) if abs(pd.z) < 0.95 else Vector((1, 0, 0))
                ax = pd.cross(ref).normalized()
                ax = Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 3, pd) @ ax
                ang = math.radians(rnd.uniform(*cs["angle"]))
                cd = Matrix.Rotation(ang, 3, ax) @ pd
                L = length * rnd.uniform(*cs["len"]) * (1.0 - cs.get("len_t", 0.4) * t)
                R = max(pr * rnd.uniform(*cs["rad"]), cs.get("rmin", 0.003))
                self.grow(pos - pd * (pr * 0.3), cd, L, R, level + 1, spec, length)
        # leaf clumps at branch ends (billowy canopy) + along outer parts of branches
        if level in spec.get("clump_levels", ()):
            self.clump(pts[-1], d, spec)
        ca = spec.get("clump_along", {}).get(str(level), 0.0)
        if ca:
            nc = int(length * ca + rnd.random())
            for k in range(nc):
                t = rnd.uniform(0.35, 0.95)
                fi = t * (len(pts) - 1)
                i = int(fi)
                i2 = min(i + 1, len(pts) - 1)
                self.clump(pts[i].lerp(pts[i2], fi - i), d, spec, scale=0.8)
        # leaf twigs on this branch
        lv = spec.get("leaf_levels", ())
        if level in lv:
            dens = spec.get("twig_density", 6.0)   # twigs per metre
            ntw = max(1, int(length * dens))
            for k in range(ntw):
                t = rnd.uniform(0.25, 1.0) if k < ntw - 1 else 1.0
                fi = t * (len(pts) - 1)
                i = int(fi)
                i2 = min(i + 1, len(pts) - 1)
                pos = pts[i].lerp(pts[i2], fi - i)
                pd = (pts[i2] - pts[i]).normalized() if i2 != i else d
                ref = Vector((0, 0, 1)) if abs(pd.z) < 0.95 else Vector((1, 0, 0))
                ax = Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 3, pd) @ pd.cross(ref).normalized()
                td = (Matrix.Rotation(math.radians(rnd.uniform(25, 70)), 3, ax) @ pd)
                td = (td + Vector((0, 0, spec.get("twig_up", 0.1)))).normalized()
                # twig local +Y along td
                yv = td
                xv = yv.cross(Vector((0, 0, 1)))
                if xv.length < 1e-4:
                    xv = Vector((1, 0, 0))
                xv.normalize()
                zv = xv.cross(yv).normalized()
                roll = Matrix.Rotation(rnd.uniform(-0.8, 0.8), 3, yv)
                xv, zv = roll @ xv, roll @ zv
                sc = rnd.uniform(*spec.get("twig_scale", (0.8, 1.25)))
                m = Matrix((
                    (xv.x * sc, yv.x * sc, zv.x * sc, pos.x),
                    (xv.y * sc, yv.y * sc, zv.y * sc, pos.y),
                    (xv.z * sc, yv.z * sc, zv.z * sc, pos.z),
                    (0, 0, 0, 1)))
                self.twigs.append(m)

    def _twig_matrix(self, pos, td, sc):
        yv = td.normalized()
        xv = yv.cross(Vector((0, 0, 1)))
        if xv.length < 1e-4:
            xv = Vector((1, 0, 0))
        xv.normalize()
        zv = xv.cross(yv).normalized()
        roll = Matrix.Rotation(self.rnd.uniform(-0.8, 0.8), 3, yv)
        xv, zv = roll @ xv, roll @ zv
        return Matrix(((xv.x * sc, yv.x * sc, zv.x * sc, pos.x), (xv.y * sc, yv.y * sc, zv.y * sc, pos.y),
                       (xv.z * sc, yv.z * sc, zv.z * sc, pos.z), (0, 0, 0, 1)))

    def clump(self, center, d, spec, scale=1.0):
        """A clump of leaf twigs around a branch end, biased outward + upward from the tree axis."""
        rnd = self.rnd
        n = spec.get("clump_twigs", 14) * scale
        n = max(3, int(n * rnd.uniform(0.7, 1.3)))
        rc = spec.get("clump_radius", 0.45) * rnd.uniform(0.75, 1.25) * scale
        outw = Vector((center.x, center.y, 0))
        outw = outw.normalized() if outw.length > 1e-3 else Vector((0, 0, 0))
        bias = (outw * 0.6 + Vector((0, 0, 0.5)) + d * 0.4)
        for k in range(n):
            v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.7)))
            if v.length < 1e-4:
                continue
            v.normalize()
            v = (v + bias * 0.5).normalized()
            pos = center + v * rc * (rnd.random() ** 0.5) * 0.9
            td = (v + Vector((0, 0, 0.2)) + Vector((rnd.gauss(0, 0.3), rnd.gauss(0, 0.3), rnd.gauss(0, 0.3)))).normalized()
            sc = rnd.uniform(*spec.get("twig_scale", (0.8, 1.2)))
            self.twigs.append(self._twig_matrix(pos - td * 0.05, td, sc))

    def build(self, name, bark_mat, leaf_mat=None, twig_variants=3, twig_kw=None):
        V = np.array(self.V, np.float64)
        F = list(self.F)
        MAT = list(self.MAT)
        UVc = list(self.UV)
        LV = np.zeros(len(V), np.float32)
        if self.twigs and leaf_mat is not None:
            tws = [_twig_geometry(random.Random(1000 + k), **(twig_kw or {})) for k in range(twig_variants)]
            allv, alll = [V], [LV]
            off = len(V)
            for m in self.twigs:
                tv, tf, tm, tl = tws[self.rnd.randrange(twig_variants)]
                M = np.array(m)
                w = np.c_[tv, np.ones(len(tv))] @ M.T
                allv.append(w[:, :3])
                alll.append((tl + self.rnd.random() * 0.3) % 1.0)
                F += [tuple(i + off for i in f) for f in tf]
                MAT += [1 if x == 1 else 0 for x in tm]
                UVc += [(0.0, 0.0)] * len(tv)
                off += len(tv)
            V = np.concatenate(allv)
            LV = np.concatenate(alll)
        me = bpy.data.meshes.new(name)
        me.from_pydata(V.tolist(), [], F)
        me.update()
        uvl = me.uv_layers.new(name="UVMap")
        loops_v = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", loops_v)
        uva = np.array(UVc, np.float32)[loops_v]
        uvl.data.foreach_set("uv", uva.ravel())
        me.polygons.foreach_set("material_index", np.array(MAT, np.int32))
        me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        me.materials.append(bark_mat)
        if leaf_mat is not None:
            me.materials.append(leaf_mat)
        a = me.attributes.new("lv", "FLOAT", "POINT")
        a.data.foreach_set("value", LV)
        # origin at base: (0,0,0) by construction
        ob = bpy.data.objects.new(name, me)
        co = V
        mn, mx = co.min(0), co.max(0)
        ob["dims"] = [float(x) for x in (mx - mn)]
        ob["n_twigs"] = len(self.twigs)
        return ob


OLIVE_SPEC = dict(
    levels=[
        dict(seg=0.22, gnarl=0.12, up=0.0, taper=0.6, sides=10, bump=0.2, spread=0.1),               # main limbs
        dict(n=(2, 4), start=0.25, angle=(30, 60), len=(0.6, 0.85), rad=(0.5, 0.7), seg=0.2, gnarl=0.16,
             up=0.02, taper=0.7, sides=7, bump=0.12, spread=0.08),
        dict(n=(3, 5), start=0.2, angle=(30, 65), len=(0.45, 0.7), rad=(0.45, 0.65), seg=0.16, gnarl=0.2,
             up=0.02, taper=0.8, sides=5, bump=0.08, rmin=0.006),
        dict(n=(2, 5), start=0.2, angle=(30, 70), len=(0.4, 0.65), rad=(0.5, 0.7), seg=0.12, gnarl=0.22,
             up=0.0, taper=0.85, sides=4, bump=0.0, rmin=0.004),
    ],
    leaf_levels=(), twig_density=4.0, twig_up=0.15, twig_scale=(0.85, 1.25),
    clump_levels=(2, 3), clump_along={"1": 1.2, "2": 1.4}, clump_twigs=20, clump_radius=0.58, min_dz=-0.3, min_z=0.9)


def olive_tree(seed=0, age=1.0, size=1.0, leaves=True, name=None, leaf_density=1.0, lod=0):
    """Gnarled olive tree prototype (not linked to the scene; place with place() / scatter()).
    age 0.3 (young, slim single trunk) .. 1.5 (ancient, massive twisted multi-strand trunk).
    size scales the whole tree (1.0 ~ 5-6 m tall, 6-7 m crown). Leaves: real geometry (narrow
    folded leaves on twigs, silvery undersides). Cached on disk per (seed, age, size, density)."""
    key = "olive5_%d_%d_%d_%d_%d_%d" % (seed, int(age * 100), int(size * 100), int(leaves), int(leaf_density * 100), lod)

    def build(nm):
        tb = _TreeBuilder(seed)
        rnd = tb.rnd
        R = (0.1 + 0.28 * age) * size              # trunk radius
        H = (0.8 + 0.7 * age) * size * rnd.uniform(0.85, 1.15)   # trunk height before the split
        nstrand = 1 if age < 0.45 else rnd.randint(3, 4)
        spec = json.loads(json.dumps(OLIVE_SPEC))
        spec["twig_density"] *= leaf_density
        spec["clump_twigs"] = int(spec["clump_twigs"] * leaf_density * (0.5 if lod >= 1 else 1.0))
        if lod >= 1:
            spec["clump_radius"] *= 1.1
            for lv in spec["levels"]:
                lv["sides"] = max(3, lv["sides"] - 3)
        spec["clump_radius"] *= size
        spec["min_z"] = H * 0.75
        for lv in spec["levels"]:
            lv["seg"] *= size
        lean = Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))
        twist = rnd.uniform(0.5, 1.1) * (1 if seed % 2 else -1)
        if nstrand > 1:
            # central core fills the gaps between strands -> reads as one fluted trunk
            cpts = [Vector((0, 0, H * 0.85 * t / 6)) + lean * (H * 0.85 * t / 6) for t in range(7)]
            crad = [R * 0.62 * (1.25 - 0.35 * t / 6) for t in range(7)]
            tb.tube(cpts, crad, sides=12, noise_amp=0.3, seed=3.3)
        for k in range(nstrand):
            a0 = 2 * math.pi * k / nstrand + rnd.uniform(-0.35, 0.35)
            rr = R * (0.42 if nstrand > 1 else 0.0)
            sr = R * (0.55 if nstrand > 1 else 1.0) * rnd.uniform(0.85, 1.1)
            pts, rads = [], []
            n = 10
            for i in range(n + 1):
                t = i / n
                a = a0 + twist * t
                flare = 1.0 + 0.9 * max(0.0, 1 - t * 5) ** 2         # buttress roots
                rad_off = rr * flare * (1.0 + 0.5 * t * t)
                p = Vector((math.cos(a) * rad_off, math.sin(a) * rad_off, H * t - 0.15 * (1 - t) ** 4)) + lean * t * H
                pts.append(p)
                rads.append(sr * (1.0 + 0.5 * max(0.0, 1 - t * 4) ** 2) * (1 - 0.25 * t))
            tb.branches.append((pts, rads, 0))
            tb.tube(pts, rads, sides=10, noise_amp=0.28, seed=k * 7.1)
            out = Vector((math.cos(a0 + twist), math.sin(a0 + twist), 0))
            d = (out * rnd.uniform(0.9, 1.4) + Vector((0, 0, 1)) + lean * 0.5).normalized()
            L = size * rnd.uniform(1.4, 2.0) * (0.85 + 0.25 * age)
            tb.grow(pts[-1] - (pts[-1] - pts[-2]).normalized() * 0.05, d, L, rads[-1] * 0.85, 0, spec)
        bark = bark_material("EnvOliveBark", "bark_willow_02", tint=(0.7, 0.68, 0.64), sat=0.3, scale=1.0)
        leaf = leaf_material() if leaves else None
        if lod >= 1:
            # far version: fewer, bigger leaves per twig + fewer twigs (~1/4 of the polygons)
            ob = tb.build(nm, bark, leaf, twig_variants=2,
                          twig_kw=dict(n_leaves=8, length=0.34, leaf_len=0.13 * max(0.8, size), leaf_w=0.03))
        else:
            ob = tb.build(nm, bark, leaf, twig_kw=dict(n_leaves=18, length=0.32, leaf_len=0.088 * max(0.8, size),
                                                        leaf_w=0.017))
        return ob
    return _cached_proto(key, build)


DEAD_SPEC = dict(
    levels=[
        dict(seg=0.3, gnarl=0.12, up=0.12, taper=0.6, sides=9, bump=0.12),
        dict(n=(3, 4), start=0.3, angle=(30, 60), len=(0.5, 0.75), rad=(0.45, 0.65), seg=0.25, gnarl=0.25,
             up=0.1, taper=0.75, sides=6, bump=0.06),
        dict(n=(2, 4), start=0.3, angle=(25, 55), len=(0.4, 0.7), rad=(0.45, 0.6), seg=0.18, gnarl=0.3,
             up=0.06, taper=0.85, sides=4, rmin=0.006),
        dict(n=(1, 3), start=0.4, angle=(25, 50), len=(0.35, 0.6), rad=(0.5, 0.6), seg=0.12, gnarl=0.3,
             up=0.04, taper=0.9, sides=3, rmin=0.004),
    ])


def dead_tree(seed=0, size=1.0, name=None):
    """Lone dead tree (bleached, leafless, wind-twisted). ~4-6 m tall at size=1."""
    key = "dead_%d_%d" % (seed, int(size * 100))

    def build(nm):
        tb = _TreeBuilder(seed + 500)
        rnd = tb.rnd
        lean = Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 1)).normalized()
        tb.grow(Vector((0, 0, -0.1)), lean, 4.2 * size, 0.2 * size, 0, DEAD_SPEC)
        bark = bark_material("EnvDeadBark", "sakura_bark", tint=(0.85, 0.82, 0.78), sat=0.15, dead=True)
        return tb.build(nm, bark, None)
    return _cached_proto(key, build)


THORN_SPEC = dict(
    levels=[
        dict(seg=0.12, gnarl=0.25, up=0.15, taper=0.7, sides=4, bump=0.0, rmin=0.006),
        dict(n=(4, 7), start=0.1, angle=(30, 70), len=(0.6, 0.9), rad=(0.6, 0.8), seg=0.1, gnarl=0.35,
             up=0.08, taper=0.85, sides=3, rmin=0.004, len_t=0.3),
        dict(n=(3, 6), start=0.2, angle=(35, 80), len=(0.35, 0.6), rad=(0.6, 0.8), seg=0.07, gnarl=0.4,
             up=0.02, taper=0.9, sides=3, rmin=0.003),
    ],
    leaf_levels=(1, 2), twig_density=6.0, twig_up=0.2, twig_scale=(0.35, 0.6))


def thorn_bush(seed=0, size=1.0, leafy=0.5, name=None):
    """Dry thorny shrub (twiggy, few small grey-green leaves). ~0.6-1.0 m tall at size=1."""
    key = "thorn2_%d_%d_%d" % (seed, int(size * 100), int(leafy * 100))

    def build(nm):
        tb = _TreeBuilder(seed + 900)
        rnd = tb.rnd
        spec = json.loads(json.dumps(THORN_SPEC))
        spec["twig_density"] *= leafy
        for k in range(rnd.randint(4, 7)):
            a = rnd.uniform(0, 2 * math.pi)
            d = Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 1)).normalized()
            tb.grow(Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), -0.05)), d,
                    rnd.uniform(0.5, 0.9) * size, 0.014 * size, 0, spec)
        bark = bark_material("EnvThornBark", "bark_willow", tint=(0.45, 0.4, 0.35), sat=0.3, scale=3.0)
        leaf = leaf_material("EnvThornLeaf", top=(0.16, 0.16, 0.08), under=(0.3, 0.3, 0.2), dry=0.3) if leafy > 0 else None
        return tb.build(nm, bark, leaf, twig_kw=dict(n_leaves=8, length=0.12, leaf_len=0.03, leaf_w=0.008))
    return _cached_proto(key, build)


# =============================================================================================
# Atmosphere: fog volumes + god rays, floating dust (no particle bake), dust storm
# =============================================================================================
def fog_volume(center=(0, 0, 20), size=(300, 300, 60), density=0.004, color=(0.9, 0.8, 0.65), anisotropy=0.55,
               noise_scale=None, noise_amount=0.6, height_falloff=0.0, name="EnvFog", wind=(0, 0, 0)):
    """Finite fog box (never a world volume). height_falloff > 0 makes it thinner with height
    (exp(-falloff * (z - bottom))). noise_scale adds wisps; wind (m/s) animates them (no bake)."""
    o = C.box(name, size, center)
    m = bpy.data.materials.new(name + "_vol")
    m.use_nodes = True
    nt = m.node_tree
    T = _NT(nt)
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = T.node("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = anisotropy
    dens = T.value(density, "density").outputs[0]
    tc = T.node("ShaderNodeTexCoord")
    if height_falloff:
        z = T.sep(tc.outputs["Object"])[2]       # object space: -1..1 (box mesh is +-size/2, scale 1)
        zb = T.math("ADD", z, size[2] / 2)
        dens = T.math("MULTIPLY", dens, T.math("EXPONENT", T.math("MULTIPLY", zb, -height_falloff)))
    if noise_scale:
        o["env_wind"] = (0.0, 0.0, 0.0)
        offn = T.node("ShaderNodeAttribute")
        offn.attribute_type = "OBJECT"
        offn.attribute_name = "env_wind"
        p = T.vmath("ADD", tc.outputs["Object"], offn.outputs["Vector"])
        n = T.noise(p, scale=noise_scale, detail=3, rough=0.55, dist=0.3)
        mr = T.node("ShaderNodeMapRange")
        T.link(n.outputs["Fac"], mr.inputs[0])
        mr.inputs[1].default_value, mr.inputs[2].default_value = 0.3, 0.7
        mr.inputs[3].default_value = 1.0 - noise_amount
        mr.inputs[4].default_value = 1.0 + noise_amount * 0.6
        dens = T.math("MULTIPLY", dens, mr.outputs[0])
        if any(wind):
            # object custom property read as a uniform (no per-frame material re-evaluation)
            sc = bpy.context.scene
            for f in (sc.frame_start, sc.frame_end + 1):
                t = (f - 1) / 24.0
                o["env_wind"] = tuple(-wind[i] * t for i in range(3))
                o.keyframe_insert('["env_wind"]', frame=f)
            _linear_keys(o)
    T.link(dens, v.inputs["Density"])
    T.link(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    C.assign(o, m)
    o.visible_shadow = False
    return o


def _set_volume_range(end, start=0.5):
    ee = bpy.context.scene.eevee
    ee.use_volume_custom_range = True
    ee.volumetric_start = start
    ee.volumetric_end = max(ee.volumetric_end if ee.use_volume_custom_range and ee.volumetric_end > end else 0, end)
    ee.volumetric_sample_distribution = 0.8


def cloud_shadows(height=180.0, size=1600.0, coverage=0.45, scale=0.006, center=(0, 0), speed=(3.0, 1.0),
                  softness=0.08, name="EnvCloudShadow", seed=0.0):
    """Invisible-to-camera plane that casts moving cloud shadows (holes = light). With a fog volume and
    a low sun this produces god rays through cloud gaps. coverage 0..1 = fraction of sky blocked."""
    o = C.prim("plane", name=name, size=size, loc=(center[0], center[1], height))
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    nt = m.node_tree
    T = _NT(nt)
    bs = nt.nodes["Principled BSDF"]
    tc = T.node("ShaderNodeTexCoord")
    o["env_drift"] = (0.0, 0.0, 0.0)
    offn = T.node("ShaderNodeAttribute")
    offn.attribute_type = "OBJECT"
    offn.attribute_name = "env_drift"
    p = T.vmath("ADD", tc.outputs["Object"], offn.outputs["Vector"])
    n = T.noise(p, scale=scale * size / 2, detail=5, rough=0.6, dist=0.25, w=seed, dims="4D")
    thr = 0.62 - 0.3 * coverage
    a = T.smooth(thr - softness, thr + softness, n.outputs["Fac"])
    T.link(a, bs.inputs["Alpha"])
    bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    m.surface_render_method = "DITHERED"
    m.use_transparent_shadow = True
    C.assign(o, m)
    o.visible_camera = False
    o.visible_diffuse = False
    o.visible_glossy = False
    o.visible_volume_scatter = False
    sc = bpy.context.scene
    for f in (sc.frame_start, sc.frame_end + 1):
        t = (f - 1) / 24.0
        o["env_drift"] = (-speed[0] * t / (size / 2), -speed[1] * t / (size / 2), 0.0)
        o.keyframe_insert('["env_drift"]', frame=f)
    _linear_keys(o)
    return o


def god_rays(center=(0, 0, 0), size=(220, 220, 70), density=0.006, color=(1.0, 0.85, 0.65), coverage=0.55,
             gobo_height=None, anisotropy=0.6, speed=(2.5, 0.8), seed=0.0, gobo=True):
    """Volumetric crepuscular rays: a fog box around `center` lit by the sun, plus (gobo=True) a moving
    cloud-shadow plane above it so light shafts fan through the gaps. Rays are strongest when the camera
    looks towards a low sun. Returns dict(fog=, gobo=). Costs ~+0.5-1 s/frame (volumetrics)."""
    cx, cy, cz = center
    fog = fog_volume((cx, cy, cz + size[2] / 2 - 5), size, density, color, anisotropy, name="EnvRaysFog",
                     height_falloff=0.02)
    g = None
    if gobo:
        g = cloud_shadows(height=cz + (gobo_height or size[2] + 40), size=max(size[0], size[1]) * 6, coverage=coverage,
                          center=(cx, cy), speed=speed, seed=seed)
    _set_volume_range(max(size[0], size[1]) * 1.6)
    return dict(fog=fog, gobo=g)


def _dust_group(color, emission, size):
    ng = bpy.data.node_groups.new("ENV_DustGN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    for nm in ("drift_x", "drift_y", "drift_z", "turb", "box_x", "box_y", "box_z", "min_x", "min_y", "min_z"):
        s = ng.interface.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
    N, L = ng.nodes, ng.links
    gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
    st = N.new("GeometryNodeInputSceneTime")
    pos = N.new("GeometryNodeInputPosition")

    def vm(op, a, b=None, sc=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        L.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list)):
                n.inputs[1].default_value = b
            else:
                L.new(b, n.inputs[1])
        if sc is not None:
            L.new(sc, n.inputs[3]) if not isinstance(sc, (int, float)) else setattr(n.inputs[3], "default_value", sc)
        return n.outputs[0]

    def comb(a, b, c):
        n = N.new("ShaderNodeCombineXYZ")
        L.new(a, n.inputs[0])
        L.new(b, n.inputs[1])
        L.new(c, n.inputs[2])
        return n.outputs[0]

    drift = comb(gi.outputs["drift_x"], gi.outputs["drift_y"], gi.outputs["drift_z"])
    box = comb(gi.outputs["box_x"], gi.outputs["box_y"], gi.outputs["box_z"])
    mn = comb(gi.outputs["min_x"], gi.outputs["min_y"], gi.outputs["min_z"])
    secs = st.outputs["Seconds"]
    off = vm("SCALE", drift, sc=secs)
    # turbulence: noise of (pos, time)
    nz = N.new("ShaderNodeTexNoise")
    nz.noise_dimensions = "4D"
    nz.inputs["Scale"].default_value = 0.35
    L.new(pos.outputs[0], nz.inputs["Vector"])
    tm = N.new("ShaderNodeMath")
    tm.operation = "MULTIPLY"
    L.new(secs, tm.inputs[0])
    tm.inputs[1].default_value = 0.08
    L.new(tm.outputs[0], nz.inputs["W"])
    turb = vm("SUBTRACT", nz.outputs["Color"], (0.5, 0.5, 0.5))
    turb = vm("SCALE", turb, sc=gi.outputs["turb"])
    p = vm("ADD", vm("ADD", pos.outputs[0], off), turb)
    # wrap into the box
    rel = vm("SUBTRACT", p, mn)
    wr = N.new("ShaderNodeVectorMath")
    wr.operation = "WRAP"
    L.new(rel, wr.inputs[0])
    L.new(box, wr.inputs[1])
    wr.inputs[2].default_value = (0, 0, 0)
    newp = vm("ADD", wr.outputs[0], mn)
    sp = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs[0], sp.inputs["Geometry"])
    L.new(newp, sp.inputs["Position"])
    m2p = N.new("GeometryNodeMeshToPoints")
    L.new(sp.outputs[0], m2p.inputs["Mesh"])
    m2p.inputs["Radius"].default_value = size
    rnd = N.new("FunctionNodeRandomValue")
    rnd.inputs["Min"].default_value = 0.4
    rnd.inputs["Max"].default_value = 1.6
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L.new(rnd.outputs[1], mul.inputs[0])
    mul.inputs[1].default_value = size
    L.new(mul.outputs[0], m2p.inputs["Radius"])
    smat = N.new("GeometryNodeSetMaterial")
    L.new(m2p.outputs[0], smat.inputs["Geometry"])
    m = C.mat("EnvDustSpeck", color, rough=1.0, emission=color, emission_strength=emission)
    hazify(m)
    smat.inputs["Material"].default_value = m
    L.new(smat.outputs[0], go.inputs[0])
    return ng


def dust_motes(center=(0, 0, 2), size=(12, 12, 5), count=1500, radius=0.0025, color=(1.0, 0.9, 0.75),
               emission=0.4, drift=(0.15, 0.05, 0.02), turbulence=0.4, seed=0, name="EnvDust"):
    """Floating dust specks (points rendered as tiny spheres) drifting with the wind + turbulence,
    wrapped inside the box so they never run out. Procedural in time (no bake). Visible mainly when
    backlit; emission adds sparkle in shafts."""
    rnd = np.random.default_rng(seed)
    pts = rnd.uniform(-0.5, 0.5, (count, 3)) * np.array(size) + np.array(center)
    me = bpy.data.meshes.new(name)
    me.vertices.add(count)
    me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
    me.update()
    ob = C.link(bpy.data.objects.new(name, me))
    md = ob.modifiers.new("dust", "NODES")
    md.node_group = _dust_group(color, emission, radius)
    vals = dict(drift_x=drift[0], drift_y=drift[1], drift_z=drift[2], turb=turbulence, box_x=size[0], box_y=size[1],
                box_z=size[2], min_x=center[0] - size[0] / 2, min_y=center[1] - size[1] / 2, min_z=center[2] - size[2] / 2)
    for it in md.node_group.interface.items_tree:
        if it.in_out == "INPUT" and it.name in vals:
            md[it.identifier] = float(vals[it.name])
    ob.visible_shadow = False
    return ob


def dust_storm(ctx, color=(0.55, 0.3, 0.16), density=0.03, speed=6.0, center=(0, 0, 0), size=(160, 160, 40),
               direction=(1, 0.3, 0), motes=True, sheets=True):
    """Red-brown dust storm (s09a): wind-driven noisy fog volume(s) + fast dust specks + low ground
    sheets. density 0.01 (haze) .. 0.06 (choking). speed m/s. Returns dict of created objects."""
    d = Vector(direction).normalized()
    cx, cy, cz = center
    out = {}
    out["fog"] = fog_volume((cx, cy, cz + size[2] / 2), size, density, color, 0.35, noise_scale=0.025,
                            noise_amount=0.85, height_falloff=0.035, name="EnvStorm", wind=tuple(d * speed))
    if sheets:
        out["ground"] = fog_volume((cx, cy, cz + 2.0), (size[0], size[1], 4.0), density * 2.5, color, 0.3,
                                   noise_scale=0.08, noise_amount=1.0, height_falloff=0.5, name="EnvStormLow",
                                   wind=tuple(d * speed * 1.6))
    if motes:
        out["motes"] = dust_motes(center=(cx, cy, cz + 3), size=(40, 40, 8), count=2500, radius=0.004, color=color,
                                  emission=0.0, drift=tuple(d * speed), turbulence=1.5, seed=7, name="EnvStormMotes")
    set_haze(density=max(get_haze()["density"], density * 0.6), color=tuple(c * 0.5 for c in color))
    _set_volume_range(max(size[0], size[1]) * 0.8)
    if ctx is not None:
        ctx.render_opts.setdefault("volumetrics", "low")
    return out


# =============================================================================================
# Skull cliff (Gordon's Calvary style escarpment)
# =============================================================================================
def skull_cliff(center=(0.0, -12.0), width=30.0, base_z=3.0, top_z=10.0, lean=0.22, seed=0, res=0.14,
                eyes=True, curve=0.006, material=None, name="SkullCliff", skull=1.0):
    """Weathered limestone escarpment facing -Y with two eroded eye-like caves, a nose hollow and a
    mouth ledge (subtle, natural). center = (x, y) of the cliff foot line at x; returns (obj, anchors)."""
    cx, cy = center
    hh = top_z - base_z
    cap = 4.0                                  # metres of rock cap reaching back over the plateau edge
    H = hh + 1.0 + cap
    nu, nv = int(width / res), int(H / res)
    u = np.linspace(-width / 2, width / 2, nu + 1)
    v = np.linspace(-1.0, H - 1.0, nv + 1)
    U, Vv = np.meshgrid(u, v)
    # displacement towards the viewer (-Y) in metres
    s = seed * 13.0
    # domain warp for everything (no perfect shapes)
    wu = U + 0.9 * fbm(U * 0.12, Vv * 0.12, 3, seed=seed + 1)
    wv = Vv + 0.6 * fbm(U * 0.12 + 5.2, Vv * 0.12, 3, seed=seed + 2)
    # limestone beds: asymmetric sawtooth ledges (overhang at the top of each bed), varying thickness
    bed = (wv + 0.8 * fbm(U * 0.05, 0 * U, 2, seed=seed + 3)) / (1.3 + 0.4 * fbm(U * 0.03, Vv * 0.05, 2, seed=seed + 14))
    ph_ = bed - np.floor(bed)
    strata = 0.28 * (np.clip(ph_ * 1.25, 0, 1) ** 1.6 - 0.5) * np.clip(0.2 + 0.9 * fbm(U * 0.07, Vv * 0.15, 2, seed=seed + 4), 0, 1.2)
    # blocky fractures: quantised noise
    blk = fbm(U * 0.08 + s, Vv * 0.1, 3, seed=seed + 5)
    blocks = 0.9 * (np.round(blk * 3.0) / 3.0) + 0.5 * blk
    big = 1.3 * fbm(U * 0.045 + s, Vv * 0.06, 3, seed=seed + 6)
    small = 0.1 * fbm(U * 0.7, Vv * 0.7, 3, seed=seed + 7) + 0.04 * fbm(U * 2.2, Vv * 2.2, 2, seed=seed + 12)
    # vertical joints
    jn = np.abs(perlin(wu * 0.22, Vv * 0.035, seed + 8))
    cracks = -0.45 * np.clip(1 - jn * 10, 0, 1) * (0.5 + 0.5 * fbm(U * 0.1, Vv * 0.3, 2, seed=seed + 13))
    D = strata + blocks + big + small + cracks
    cav = np.zeros_like(D)
    anchors = {}
    if eyes:
        def hollow(ux, vy, rx, ry, depth, brow=0.35):
            q = ((wu - ux) / rx) ** 2 + ((wv - vy) / ry) ** 2
            q = q * (1 + 0.25 * fbm(U * 0.6 + ux, Vv * 0.6, 2, seed=seed + 20))
            f = smoothstep(1.0, 0.15, q)
            # deeper under the brow (top), shallow debris-filled floor
            vert = np.clip((Vv - (vy - ry)) / (2 * ry), 0, 1)
            return -depth * f * (0.55 + 0.45 * vert ** 0.7), f ** 0.6 * (0.6 + 0.4 * vert)
        vv = hh * 0.6
        feats = ((-2.8, vv, 1.3, 1.0, 2.4), (2.55, vv + 0.25, 1.15, 0.9, 2.2),       # eye caves
                 (0.1, hh * 0.38, 0.45, 0.85, 1.0),                                    # nose hollow
                 (-0.6, hh * 0.17, 2.4, 0.32, 0.6), (1.6, hh * 0.15, 1.2, 0.26, 0.45))  # broken mouth ledge
        for k, (ux, vy, rx, ry, dp) in enumerate(feats):
            dd, f = hollow(ux, vy, rx * (0.8 + 0.2 * skull), ry, dp * skull)
            D = D + dd
            cav = np.maximum(cav, f * (1.0 if k < 2 else 0.7))
        anchors["eye_l"] = (cx - 2.8, cy, base_z + vv)
        anchors["eye_r"] = (cx + 2.55, cy, base_z + vv)
    # fade out displacement + bury at the ends so it merges into the hill
    endf = smoothstep(width / 2, width / 2 - 5.0, np.abs(U))
    D = D * endf - (1 - endf) * 3.0
    # lean back with height + plan curvature; above hh the sheet folds back horizontally (cap)
    X = cx + U
    hh_u = hh + 0.55 * fbm(U * 0.08, 0 * U + 3.0, 3, seed=seed + 15)      # ragged skyline of the cliff top
    vc = np.minimum(Vv, hh_u)
    over = np.clip(Vv - hh_u, 0, None)
    capf = smoothstep(hh_u - 0.6, hh_u + 0.8, Vv)
    Dc = D * (1 - capf) + capf * (0.15 * fbm(U * 0.3, Vv * 0.3, 3, seed=seed + 9))
    Y = cy + curve * U ** 2 + lean * np.clip(vc, 0, None) - Dc + over * 1.0
    Z = base_z + vc - over * 0.12 + capf * 0.12 * fbm(U * 0.25, Vv * 0.5, 2, seed=seed + 10) - 0.35 * smoothstep(hh + 2.5, hh + cap, Vv)
    cav += 0.35 * np.clip(-cracks, 0, 1) + 0.2 * np.clip(-(big + blocks) * 0.6, 0, 1) + 0.25 * np.clip(-strata * 3, 0, 1)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    nx_ = nu + 1
    j, i = np.mgrid[0:nv, 0:nu]
    a = (j * nx_ + i).ravel()
    faces = np.stack([a, a + nx_, a + nx_ + 1, a + 1], 1)      # normals face -Y
    o = mesh_from_numpy(name, verts, faces)
    set_attr(o, "cav", np.clip(cav, 0, 1).ravel())
    C.assign(o, material or limestone_material("EnvCliffStone", scale=0.18, tint=(0.9, 0.85, 0.76), streaks=1.0, strata=0.12,
                                                cav_dark=0.8))
    add_ground(o)
    anchors["face_center"] = (cx, cy, base_z + hh * 0.5)
    return o, anchors


# =============================================================================================
# Jerusalem (distant city massing: walls, towers, houses, Temple Mount)
# =============================================================================================
def _box_arrays(cx, cy, cz, sx, sy, sz, rz=0.0):
    """Vertices/faces arrays for one or many boxes (bottom-centre at cz). Vectorised."""
    cx, cy, cz, sx, sy, sz, rz = [np.atleast_1d(np.asarray(a, float)) for a in (cx, cy, cz, sx, sy, sz, rz)]
    n = max(len(cx), len(sx), len(rz))
    bx = np.array([-1, 1, 1, -1, -1, 1, 1, -1]) * 0.5
    by = np.array([-1, -1, 1, 1, -1, -1, 1, 1]) * 0.5
    bz = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    lx = bx[None] * sx[:, None] * np.ones((n, 1))
    ly = by[None] * sy[:, None] * np.ones((n, 1))
    c, s = np.cos(rz)[:, None], np.sin(rz)[:, None]
    X = cx[:, None] + lx * c - ly * s
    Y = cy[:, None] + lx * s + ly * c
    Z = cz[:, None] + bz[None] * sz[:, None] * np.ones((n, 1))
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    f = np.array([(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    F = (f[None] + 8 * np.arange(n)[:, None, None]).reshape(-1, 4)
    return V, F


def point_in_poly(x, y, poly):
    """Vectorised even-odd point-in-polygon test. poly: (N, 2) array."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    inside = np.zeros(x.shape, bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cond = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / ((y2 - y1) + 1e-12) + x1)
        inside ^= cond
    return inside


def _merge(parts):
    V, F, off = [], [], 0
    for v, f in parts:
        V.append(v)
        F.append(f + off)
        off += len(v)
    return np.concatenate(V), np.concatenate(F)


def city_material(name="EnvCityStone", base=(0.62, 0.55, 0.44), var=0.35, textured=False, scale=0.25, bright=1.0):
    """Cheap limestone/plaster for distant buildings: per-object random tint, top-lit faces brighter,
    darker base course. textured=True uses large sandstone blocks (walls)."""
    if textured:
        m = C.mat_pbr("large_sandstone_blocks_01", scale=scale, tint=tuple(b * 1.25 * bright for b in base), name=name)
        tint_material(m, sat=0.6, rand=var)
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    T = _NT(m.node_tree)
    bs = m.node_tree.nodes["Principled BSDF"]
    oi = T.node("ShaderNodeObjectInfo")
    tc = T.node("ShaderNodeTexCoord")
    n = T.noise(tc.outputs["Object"], scale=0.4, detail=3)
    r = oi.outputs["Random"]
    col = T.mix(T.math("MULTIPLY", r, 1.0), tuple(c * 0.78 * bright for c in base), tuple(min(1, c * 1.22 * bright) for c in base))
    col = T.mix(T.math("MULTIPLY", n.outputs["Fac"], 0.3), col, (0.4, 0.36, 0.3), blend="MULTIPLY")
    T.link(col, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.85
    hazify(m)
    return m


def jerusalem(center=(170.0, 640.0), rot=0.0, seed=0, detail=1.0, houses=True, name="Jerusalem"):
    """Jerusalem c. AD 30 as distant massing (best seen from >250 m with haze): crenellated walls with
    towers, Herod's three towers, Gennath gate, ~2000 flat-roofed houses, the Temple Mount with
    porticoes, Royal Stoa, Antonia fortress and the white-and-gold sanctuary. Placed on the env ground
    (raycast). Local frame: +Y = away from Golgotha (rot rotates around `center`, degrees).
    Returns dict(objects=[...], temple=(x,y,z), towers=[...], gate=(x,y,z))."""
    cx, cy = center
    rr = math.radians(rot)
    cr, sr = math.cos(rr), math.sin(rr)
    rnd = np.random.default_rng(seed + 77)

    def W(lx, ly):
        lx, ly = np.asarray(lx, float), np.asarray(ly, float)
        return cx + lx * cr - ly * sr, cy + lx * sr + ly * cr

    def gz(x, y):
        return np.array([ground_z(float(a), float(b), default=0.0) for a, b in zip(np.atleast_1d(x), np.atleast_1d(y))])

    coll = C.collection(name)
    objs = []
    # wall outline (local coords), roughly the 1st-century city with the Temple Mount on the far right
    outline = np.array([(-380, -300), (-120, -340), (120, -320), (300, -260), (420, -60), (430, 260),
                        (330, 330), (60, 340), (-250, 300), (-420, 120), (-430, -120)], float)
    stone = city_material("EnvCityStone", base=(0.66, 0.58, 0.46))
    wallm = city_material("EnvCityWall", base=(0.6, 0.52, 0.4), textured=True, scale=0.2)
    parts, tparts, towers = [], [], []
    for i in range(len(outline)):
        a, b = outline[i], outline[(i + 1) % len(outline)]
        L = np.linalg.norm(b - a)
        nseg = max(1, int(L / 25))
        for k in range(nseg):
            p0 = a + (b - a) * k / nseg
            p1 = a + (b - a) * (k + 1) / nseg
            mid = (p0 + p1) / 2
            ang = math.atan2(*(p1 - p0)[::-1])
            wx, wy = W(mid[0], mid[1])
            z = gz(wx, wy)[0] - 2
            seg_len = np.linalg.norm(p1 - p0) + 0.5
            parts.append(_box_arrays(wx, wy, z, seg_len, 3.5, 13.0, ang + rr))
            # crenellations
            nm = int(seg_len / 2.4)
            t = (np.arange(nm) + 0.5) / nm - 0.5
            mx = mid[0] + (p1 - p0)[0] * t
            my = mid[1] + (p1 - p0)[1] * t
            mwx, mwy = W(mx, my)
            parts.append(_box_arrays(mwx, mwy, z + 13.0, 1.2, 3.5, 1.3, np.full(nm, ang + rr)))
        # towers at corners + every ~70 m
        nt_ = max(1, int(L / 70))
        for k in range(nt_):
            p = a + (b - a) * k / nt_
            towers.append((p[0], p[1], 0.0))
    for (lx, ly, _) in towers:
        wx, wy = W(lx, ly)
        z = gz(wx, wy)[0] - 2
        h = rnd.uniform(18, 23)
        tparts.append(_box_arrays(wx, wy, z, 10, 10, h, rr))
        o4 = np.array([(-3.5, -3.5), (-3.5, 3.5), (3.5, -3.5), (3.5, 3.5), (0, -4.2), (0, 4.2), (-4.2, 0), (4.2, 0)])
        tx, ty = W(lx + o4[:, 0], ly + o4[:, 1])
        tparts.append(_box_arrays(tx, ty, z + h, 1.4, 1.4, 1.4, np.full(len(o4), rr)))
    # Gennath gate (near wall, closest to Golgotha) + Herod's three towers (west)
    gate_l = (-150.0, -333.0)
    for dx in (-9, 9):
        wx, wy = W(gate_l[0] + dx, gate_l[1])
        z = gz(wx, wy)[0] - 2
        tparts.append(_box_arrays(wx, wy, z, 9, 11, 21, rr))
    herod = [(-360, -150, 13, 45), (-330, -95, 12, 38), (-300, -135, 10, 30)]
    for lx, ly, s_, h in herod:
        wx, wy = W(lx, ly)
        z = gz(wx, wy)[0] - 2
        tparts.append(_box_arrays(wx, wy, z, s_, s_, h * 0.62, rr))
        tparts.append(_box_arrays(wx, wy, z + h * 0.62, s_ * 0.8, s_ * 0.8, h * 0.38, rr))
    V, F = _merge(parts)
    wall = mesh_from_numpy(name + "_walls", V, F, coll=coll, smooth=False)
    C.assign(wall, wallm)
    V, F = _merge(tparts)
    tw = mesh_from_numpy(name + "_towers", V, F, coll=coll, smooth=False)
    C.assign(tw, wallm)
    objs += [wall, tw]
    # Temple Mount platform + porticoes + sanctuary
    tm_c, tm_s = np.array([250.0, 90.0]), np.array([300.0, 470.0])
    wx, wy = W(*tm_c)
    zt = gz(wx, wy)[0]
    plat_top = zt + 14.0
    pparts = [_box_arrays(wx, wy, zt - 30, tm_s[0], tm_s[1], 44.0, rr)]
    # porticoes along the edges (15 m tall, 14 m deep), royal stoa on the near (south) side
    for (ox, oy, sx_, sy_, hh) in ((0, -tm_s[1] / 2 + 8, tm_s[0], 16, 26), (0, tm_s[1] / 2 - 7, tm_s[0], 14, 15),
                                  (-tm_s[0] / 2 + 7, 0, 14, tm_s[1], 15), (tm_s[0] / 2 - 7, 0, 14, tm_s[1], 15)):
        px, py = W(tm_c[0] + ox, tm_c[1] + oy)
        pparts.append(_box_arrays(px, py, plat_top, sx_, sy_, hh, rr))
    # inner courts wall
    ic = tm_c + np.array([10.0, 40.0])
    px, py = W(*ic)
    for (ox, oy, sx_, sy_) in ((0, -75, 150, 6), (0, 75, 150, 6), (-75, 0, 6, 150), (75, 0, 6, 150)):
        qx, qy = W(ic[0] + ox, ic[1] + oy)
        pparts.append(_box_arrays(qx, qy, plat_top, sx_, sy_, 14, rr))
    # Antonia fortress (NW corner)
    ant = tm_c + np.array([-tm_s[0] / 2 - 20, -tm_s[1] / 2 + 60])
    ax_, ay_ = W(*ant)
    za = gz(ax_, ay_)[0]
    pparts.append(_box_arrays(ax_, ay_, za - 2, 60, 90, 26, rr))
    for ox, oy, h in ((-27, -42, 38), (27, -42, 38), (-27, 42, 38), (27, 42, 50)):
        qx, qy = W(ant[0] + ox, ant[1] + oy)
        pparts.append(_box_arrays(qx, qy, za - 2, 11, 11, h, rr))
    V, F = _merge(pparts)
    tmo = mesh_from_numpy(name + "_templemount", V, F, coll=coll, smooth=False)
    C.assign(tmo, wallm)
    objs.append(tmo)
    # sanctuary: white limestone/marble + gold
    sx_, sy_ = W(*(ic + np.array([12.0, 0.0])))
    white = city_material("EnvTempleWhite", base=(0.92, 0.88, 0.8), var=0.05, bright=1.05)
    gold = C.mat("EnvTempleGold", (0.95, 0.7, 0.3), rough=0.3, metal=1.0)
    hazify(gold)
    sparts = [_box_arrays(sx_, sy_, plat_top + 6, 34, 60, 46, rr + math.pi / 2),       # body (long axis E-W)
              _box_arrays(*W(*(ic + np.array([45.0, 0.0]))), plat_top + 6, 14, 52, 50, rr),   # porch facade
              _box_arrays(sx_, sy_, plat_top, 70, 90, 6, rr)]                          # raised platform
    V, F = _merge(sparts)
    san = mesh_from_numpy(name + "_sanctuary", V, F, coll=coll, smooth=False)
    C.assign(san, white)
    # golden roof spikes / cornice
    gx, gy = W(ic[0] + 12 + np.linspace(-28, 28, 9), np.full(9, ic[1]))
    V, F = _box_arrays(gx, gy, np.full(9, plat_top + 52), 1.0, 1.0, 2.5, np.full(9, rr))
    V2, F2 = _box_arrays(*W(*(ic + np.array([45.0, 0.0]))), plat_top + 54.5, 15, 53, 1.2, rr)
    V, F = _merge([(V, F), (V2, F2)])
    go_ = mesh_from_numpy(name + "_gold", V, F, coll=coll, smooth=False)
    C.assign(go_, gold)
    objs += [san, go_]
    temple = (float(sx_), float(sy_), plat_top + 30)
    # houses (GN instances of 4 cube variants)
    if houses:
        hv = []
        for k, (sx_, sy_, sz_) in enumerate(((1, 1, 1), (1, 0.6, 1.3), (1.4, 1, 0.8), (0.8, 0.8, 1.6))):
            v, f = _box_arrays(0, 0, 0, sx_, sy_, sz_)
            # parapet / upper storey on some
            if k in (1, 3):
                v2, f2 = _box_arrays(-0.2, 0.1, sz_, 0.45, 0.45, 0.45)
                v, f = _merge([(v, f), (v2, f2)])
            o = mesh_from_numpy("%s_house%d" % (name, k), v, f, smooth=False)
            bpy.context.scene.collection.objects.unlink(o)
            o.data.materials.append(stone)
            o["dims"] = [sx_, sy_, sz_]
            hv.append(o)
        sp = 13.0 / max(0.4, detail) ** 0.5
        gx_, gy_ = np.meshgrid(np.arange(-430, 430, sp), np.arange(-340, 340, sp))
        lx = (gx_ + rnd.uniform(-3, 3, gx_.shape)).ravel()
        ly = (gy_ + rnd.uniform(-3, 3, gy_.shape)).ravel()
        # inside outline (polygon test)
        inside = point_in_poly(lx, ly, outline * 0.97)
        tm_box = (np.abs(lx - tm_c[0]) < tm_s[0] / 2 + 15) & (np.abs(ly - tm_c[1]) < tm_s[1] / 2 + 15)
        ant_box = (np.abs(lx - ant[0]) < 50) & (np.abs(ly - ant[1]) < 60)
        herod_box = (lx < -260) & (ly > -200) & (ly < -60)
        streets = (np.abs(ly - (-40 + 0.25 * lx)) < 6) | (np.abs(lx - (-60)) < 5)
        keep = inside & ~tm_box & ~ant_box & ~herod_box & ~streets & (rnd.random(len(lx)) < 0.9)
        lx, ly = lx[keep], ly[keep]
        wx, wy = W(lx, ly)
        zz = gz(wx, wy) - 0.5
        n = len(lx)
        s_xy = rnd.uniform(6, 13, n)
        s_z = rnd.uniform(4.5, 9.5, n) * (1 + 0.4 * (rnd.random(n) < 0.15))
        rotz = rr + rnd.normal(0, 0.06, n)
        S = np.c_[s_xy, s_xy * rnd.uniform(0.7, 1.2, n), s_z]
        R = np.c_[np.zeros(n), np.zeros(n), rotz]
        I = rnd.integers(0, len(hv), n)
        hob = instancer(name + "_houses", hv, np.c_[wx, wy, zz], R, S, I, coll=coll)
        objs.append(hob)
    for o in objs:
        o.visible_shadow = True
    gate = W(*gate_l)
    return dict(objects=objs, temple=temple, gate=(float(gate[0]), float(gate[1]), float(gz(*gate)[0])),
                towers=[tuple(map(float, W(lx, ly))) for lx, ly, _, _ in herod], collection=coll)


# =============================================================================================
# GOLGOTHA
# =============================================================================================
GOLGOTHA = dict(top=11.0, cliff_y=-11.0, cliff_base=3.2, cliff_w=30.0, city=(170.0, 640.0))


def golgotha_height(city=True, seed=0):
    """Vectorised height function H(X, Y) of the Golgotha terrain (hill top ~11 m at the origin,
    skull scarp facing -Y at y~-11, plain at ~0, Jerusalem plateau +Y, mountains far away)."""
    G = GOLGOTHA
    ccx, ccy = G["city"]

    def H(X, Y):
        X = np.asarray(X, float)
        Y = np.asarray(Y, float)
        # plateau-shaped hill (super-gaussian), slightly elongated E-W, centre a bit north
        r2 = (X / 31.0) ** 2 + ((Y - 3.0) / 25.0) ** 2
        dome = G["top"] * np.exp(-np.power(r2 * 1.25, 1.45))
        dome += 0.6 * fbm(X * 0.04, Y * 0.04, 3, seed=seed + 1) * np.exp(-r2)
        # southern scarp: below the cliff line the hill is cut down to a talus slope
        yc = G["cliff_y"] - 0.006 * X ** 2
        w = smoothstep(G["cliff_w"] / 2 + 2, G["cliff_w"] / 2 - 6, np.abs(X))
        below = smoothstep(yc + 3.4, yc + 1.4, Y)
        talus = G["cliff_base"] + 0.32 * (Y - yc) + 0.4 * fbm(X * 0.2, Y * 0.2, 2, seed=seed + 2)
        talus = np.maximum(talus, dome * 0.0 + 0.0)
        cut = np.minimum(dome, np.maximum(talus, 0.4 * dome))
        h = dome + (cut - dome) * below * w
        # plain: gentle undulation + a shallow wadi crossing in front
        r = np.sqrt(X ** 2 + Y ** 2)
        plain = 1.2 * fbm(X * 0.008, Y * 0.008, 4, seed=seed + 3) + 0.25 * fbm(X * 0.05, Y * 0.05, 3, seed=seed + 4)
        wadi = -1.6 * np.exp(-((Y + 70 + 12 * np.sin(X * 0.02)) / 9.0) ** 2) * smoothstep(20, 60, r)
        h = h + plain * smoothstep(8, 40, r) + wadi
        # micro relief everywhere near the hill
        h += 0.12 * fbm(X * 0.35, Y * 0.35, 3, seed=seed + 5)
        # far hills + mountain ring (hide the terrain edge)
        far = smoothstep(220, 1100, r) * (28 + 45 * fbm(X / 650, Y / 650, 4, seed=seed + 6)) \
            + smoothstep(1400, 3600, r) * (90 + 120 * (0.5 + 0.5 * fbm(X / 1400, Y / 1400, 3, seed=seed + 7)))
        h = h + far
        if city:
            lx, ly = X - ccx, Y - ccy
            sdf = np.maximum(np.abs(lx) - 380, np.abs(ly) - 300)
            plateau = smoothstep(90, -30, sdf) * 16.0
            kidron = -38 * np.exp(-((lx - 520) / 70.0) ** 2) * smoothstep(700, 300, np.abs(ly))
            olives = 85 * smoothstep(560, 760, lx) * smoothstep(1500, 900, lx) * smoothstep(900, 400, np.abs(ly))
            # keep far hills from towering over the city: blend them down near it
            near_city = smoothstep(500, 200, np.sqrt((lx * 0.8) ** 2 + ly ** 2))
            h = h + plateau + kidron + olives - near_city * smoothstep(220, 1100, r) * 20
        return h
    return H


def _golgotha_attrs(H):
    G = GOLGOTHA

    def A(X, Y, Z):
        r2 = (X / 31.0) ** 2 + ((Y - 3.0) / 25.0) ** 2
        hill = np.exp(-r2 * 1.5)
        n1 = fbm(X * 0.09, Y * 0.09, 3, seed=11)
        rock = np.clip((n1 - 0.25) * 3.0, 0, 1) * smoothstep(0.15, 0.6, hill) * 0.9
        # path: from the south-west plain, around the west flank, up onto the plateau
        t = np.linspace(0, 1, 200)
        px = -60 + 45 * t + 20 * np.sin(t * 3.0)
        py = -55 + 50 * t + 8 * t ** 2
        d = np.full(X.shape, 1e9)
        Xf, Yf = X.ravel(), Y.ravel()
        near = (np.abs(Xf + 30) < 60) & (np.abs(Yf + 20) < 60)
        dd = np.full(Xf.shape, 1e9)
        if near.any():
            sub = np.c_[Xf[near], Yf[near]]
            m = np.full(len(sub), 1e9)
            for k in range(0, len(px), 4):
                m = np.minimum(m, (sub[:, 0] - px[k]) ** 2 + (sub[:, 1] - py[k]) ** 2)
            dd[near] = np.sqrt(m)
        d = dd.reshape(X.shape)
        path = np.clip(1.6 - d / 1.4, 0, 1)
        # trodden plateau around the crosses + crowd area in front
        plateau = smoothstep(9.5, 5.0, np.sqrt((X / 1.2) ** 2 + ((Y + 3.0) / 1.0) ** 2))
        path = np.maximum(path, plateau * 0.75)
        dust = smoothstep(14, 4, np.sqrt(X ** 2 + (Y + 2) ** 2)) * 0.8
        # cavity from the discrete laplacian
        cav = np.zeros_like(Z)
        lap = (Z[:-2, 1:-1] + Z[2:, 1:-1] + Z[1:-1, :-2] + Z[1:-1, 2:] - 4 * Z[1:-1, 1:-1])
        cav[1:-1, 1:-1] = np.clip(lap * 1.2, 0, 1)
        return dict(rock=rock, path=path, dust=dust, cav=cav)
    return A


def _cross_anchors(root, height, beam, thick, cross_at, base):
    """Anchor points (world) for a core.wooden_cross root empty."""
    M = root.matrix_world.copy()

    def w(x, y, z):
        return tuple(M @ Vector((x, y, z)))
    bz = height * cross_at
    front = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
    return dict(
        base=tuple(base), root=root, top=w(0, 0, height), beam=w(0, 0, bz), beam_z=w(0, 0, bz)[2],
        beam_l=w(-beam / 2, 0, bz), beam_r=w(beam / 2, 0, bz), front=tuple(front),
        hand_l=w(-(beam / 2 - 0.13), -thick / 2 - 0.04, bz + 0.03), hand_r=w(beam / 2 - 0.13, -thick / 2 - 0.04, bz + 0.03),
        head=w(0, -thick / 2 - 0.12, bz + 0.12), chest=w(0, -thick / 2 - 0.14, bz - 0.45),
        feet=w(0, -thick / 2 - 0.06, bz - 1.72), sign=w(0, -thick * 0.55, bz + 0.42), height=height)


def golgotha(ctx, mood="golden", crosses=3, center_occupied=True, sign=True, city=True, seed=0, sun_az=None,
             grass=1.0, rocks=1.0, bushes=1.0, rays=None, dust=None, clouds=None, skull=1.0,
             cross_height=4.4, side_cross_height=4.0, cross_material=None, near_detail=1.0, sky_over=None, fog=True):
    """Golgotha: rocky skull-faced hill outside Jerusalem with up to three crosses (core.wooden_cross,
    centre one with the placard), scattered limestone boulders/rocks, dry grass, thorn bushes, the
    city walls / towers / Temple in the hazy distance, and the sky + light for `mood`
    ('golden' | 'noon' | 'eclipse' | 'storm' | 'dawn' | 'sunrise' | 'night').

    World layout: hill top ~ (0, 0, 11); crosses on the top facing -Y (the default camera side);
    the skull cliff faces -Y below them (y ~ -11 .. -14); Jerusalem lies towards +Y (behind the hill).
    Returns anchors dict (see docs/env.md): crosses {center,left,right}, hill_top, ground(x, y),
    ground_z(x, y), cams {wide, medium, low, from_cross, skull}, crowd_region, sky (sky() result), ..."""
    t0 = time.time()
    st = _state()
    rnd = random.Random(seed)
    p = sky_preset(mood, **(sky_over or {}))
    if sun_az is not None:
        p["sun_az"] = sun_az
    if clouds is not None:
        p["clouds"] = clouds
    _dbg("g:start")
    S = sky(cfg=p, ctx=ctx)
    _dbg("g:sky")
    H = golgotha_height(city=city, seed=seed)
    gm = ground_material("EnvGolgothaGround", style="golgotha",
                         grass_tint=None, wet=0.0)
    terr = terrain_grid("Golgotha", H, center=(0, -5), core=130, cell=0.45, extent=4200, growth=1.075, mat_=gm,
                        attrs_fn=_golgotha_attrs(H), core_y=110)
    G = GOLGOTHA
    _dbg("g:terrain")
    A = dict(sky=S, terrain=terr, mood=mood)
    # skull cliff -------------------------------------------------------------------------------
    cliff = None
    if skull:
        top_at = float(H(np.array([0.0]), np.array([G["cliff_y"] + 3.8]))[0])     # plateau height behind the cut
        cliff, ca = skull_cliff(center=(0.0, G["cliff_y"] - 0.6), width=G["cliff_w"], base_z=G["cliff_base"] - 1.2,
                                top_z=top_at + 0.25, seed=seed, skull=skull)
        A["skull"] = ca
        A["cliff"] = cliff
    _dbg("g:cliff")
    # crosses -------------------------------------------------------------------------------------
    cm = cross_material or C.wood_material("rough_wood", scale=1.2, tint=(0.62, 0.52, 0.42))
    hazify(cm)
    positions = {"center": (0.0, 0.6, 0.0, cross_height), "left": (-4.5, 1.7, 9.0, side_cross_height),
                 "right": (4.7, 1.5, -11.0, side_cross_height)}
    use = ["center"] if crosses == 1 else (["left", "right"] if crosses == 2 else ["left", "center", "right"])
    A["crosses"] = {}
    for k in use:
        x, y, rz, hgt = positions[k]
        gzv = ground_z(x, y)
        base = (x, y, gzv)
        root = C.wooden_cross(loc=(x, y, gzv - 0.45), height=hgt + 0.45, rot_z=rz, name="Cross_" + k,
                              material=cm, sign=(sign and k == "center"))
        for ch in root.children:
            if ch.data and ch.data.materials:
                for ms in ch.data.materials:
                    hazify(ms)
        bpy.context.view_layer.update()
        A["crosses"][k] = _cross_anchors(root, hgt + 0.45, 2.0, 0.2, 0.78, base)
    # rocks + vegetation --------------------------------------------------------------------------
    keep_out = [(x, y, 0.55) for (x, y, _, _) in [positions[k] for k in use]]
    crowd = (-8.0, -9.5, 8.0, -1.0)
    A["crowd_region"] = crowd
    if center_occupied and "center" in use:
        keep_out.append((0.0, -0.4, 1.3))
    _dbg("g:crosses")
    boulders = rock_protos("boulders")
    small = rock_protos("rocks")
    pebbles = rock_protos("stones", tint=(0.9, 0.82, 0.7), value=0.85)
    _dbg("g:rockprotos")
    if rocks:
        # talus at the cliff foot + hill flanks
        scatter(boulders, count=int(70 * rocks), seed=seed + 1, scale=(0.5, 1.4), align=0.6, sink=-0.3, tilt=8,
                region=(-17, -19, 17, -11.5), name="EnvTalus", exclude=[(0, -16, 3.0)])
        hill_mask = lambda X, Y: np.where((Y > -12) & (np.abs(X) < 9) & (Y < 6), 0.12, 1.0) * \
            smoothstep(55, 25, np.sqrt(X ** 2 + Y ** 2))
        scatter(boulders, count=int(90 * rocks), seed=seed + 2, scale=(0.4, 1.2), align=0.7, sink=-0.35, tilt=10,
                region=("circle", 0, 0, 55), density=hill_mask, exclude=keep_out + [(0, -5, 6)], name="EnvBoulders",
                min_dist=2.5)
        scatter(small, count=int(900 * rocks), seed=seed + 3, scale=(0.6, 1.8), align=0.9, sink=-0.3, tilt=12,
                region=("circle", 0, 0, 45), exclude=keep_out, name="EnvRocks",
                density=lambda X, Y: 0.35 + 0.65 * smoothstep(6, 18, np.sqrt(X ** 2 + Y ** 2)))
        if near_detail:
            scatter(pebbles + small[:4], count=int(700 * near_detail), seed=seed + 4, scale=(0.4, 1.1), align=1.0,
                    sink=-0.35, region=("circle", 0, -1, 14), exclude=[(x, y, 0.3) for x, y, _ in keep_out],
                    name="EnvPebbles")
            # wedge stones at each cross foot
            for k in use:
                x, y, _, _ = positions[k]
                scatter(small, count=14, seed=seed + 50 + len(k), scale=(0.9, 1.6), align=0.6, sink=-0.25, tilt=25,
                        region=("ring", x, y, 0.22, 0.75), name="EnvWedges_" + k)
    _dbg("g:rocks")
    if grass:
        gr = grass_protos("dry")
        gmask = lambda X, Y: (0.25 + 0.75 * smoothstep(7, 16, np.sqrt(X ** 2 + (Y + 2) ** 2))) * \
            (0.4 + 0.6 * (fbm(X * 0.05, Y * 0.05, 3, seed=21) > -0.1))
        scatter(gr, count=int(16000 * grass), seed=seed + 5, scale=(0.6, 1.5), align=0.6, sink=0.02,
                region=("circle", 0, -10, 70), density=gmask, max_slope=40, exclude=keep_out + [(0, -2, 3.5)],
                name="EnvGrass")
        scatter(gr, count=int(5000 * grass), seed=seed + 6, scale=(0.7, 1.4), align=0.5, sink=0.02,
                region=("ring", 0, 0, 60, 200), max_slope=35, name="EnvGrassFar",
                density=lambda X, Y: 0.5 + 0.5 * (fbm(X * 0.02, Y * 0.02, 2, seed=22) > 0))
    _dbg("g:grass")
    if bushes:
        th = [thorn_bush(seed=i, size=0.8 + 0.25 * i, leafy=0.4 + 0.2 * (i % 2)) for i in range(4)]
        scatter(th, count=int(70 * bushes), seed=seed + 7, scale=(0.7, 1.4), align=0.3, sink=0.05,
                region=("circle", 0, 0, 60), exclude=keep_out + [(0, -4, 7)], max_slope=40, name="EnvThorns",
                density=lambda X, Y: smoothstep(8, 20, np.sqrt(X ** 2 + Y ** 2)))
        # a few olive trees on the plain + far scattered shrubs for scale
        ol = [olive_tree(seed=i, age=0.6 + 0.3 * i, size=0.9, lod=1) for i in range(2)]
        scatter(ol, count=int(18 * bushes), seed=seed + 8, scale=(0.8, 1.1), align=0.0, sink=0.1,
                region=("ring", 0, 0, 80, 400), name="EnvOlivesFar", max_slope=20,
                density=lambda X, Y: (np.abs(X) > 40) * 1.0)
        scatter(th, count=int(500 * bushes), seed=seed + 9, scale=(1.0, 2.0), align=0.3, sink=0.1,
                region=("ring", 0, 0, 60, 500), name="EnvShrubsFar", max_slope=35)
    _dbg("g:bushes")
    # Jerusalem ----------------------------------------------------------------------------------
    if city:
        A["city"] = jerusalem(center=G["city"], seed=seed)
    _dbg("g:city")
    # atmosphere ----------------------------------------------------------------------------------
    top = ground_z(0, 0)
    A["hill_top"] = (0.0, 0.0, top)
    if rays is None:
        rays = p.get("rays", mood in ("golden", "sunrise", "eclipse", "storm"))
    fog_col = tuple(p.get("fog", (0.9, 0.8, 0.7)))
    if rays:
        A["rays"] = god_rays(center=(0, 20, 0), size=(260, 300, 80), density=p.get("fog_density", 0.004),
                             color=fog_col, coverage=p.get("ray_coverage", 0.5), speed=(2.0, 0.6), seed=seed)
    elif fog:
        A["fog"] = fog_volume((0, 20, 35), (260, 300, 80), p.get("fog_density", 0.002) * 0.6, fog_col, 0.4,
                              height_falloff=0.03, name="EnvAirFog")
        _set_volume_range(400)
    if dust if dust is not None else (mood in ("golden", "eclipse", "storm", "sunrise", "noon")):
        A["dust"] = dust_motes(center=(0, -4, top + 2.0), size=(16, 16, 5), count=900,
                               color=(1.0, 0.9, 0.75) if mood != "eclipse" else (0.9, 0.55, 0.35),
                               emission=0.06 if mood in ("golden", "sunrise") else 0.0, seed=seed)
    # anchors ---------------------------------------------------------------------------------------
    A["ground"] = _scalar(H)
    A["ground_z"] = ground_z
    c = A["crosses"].get("center") or next(iter(A["crosses"].values()))
    cz = c["base"][2]
    A["cams"] = {
        "wide": dict(loc=(-6.0, -64.0, 7.5), target=(0.0, 0.0, cz + 3.0), lens=30),
        "wide_low": dict(loc=(-3.0, -40.0, 3.2), target=(0.0, 0.0, cz + 4.0), lens=26),
        "medium": dict(loc=(-2.6, -8.6, cz + 1.65), target=(0.0, 0.6, cz + 3.0), lens=40),
        "low": dict(loc=(1.4, -4.2, cz + 0.35), target=(0.0, 0.6, cz + 3.7), lens=22),
        "from_cross": dict(loc=c["head"], target=(0.0, -6.5, cz + 0.6), lens=28),
        "skull": dict(loc=(4.0, -36.0, 4.5), target=(0.0, -12.0, 7.5), lens=45),
        "aerial": dict(loc=(-60.0, -140.0, 70.0), target=(0.0, 0.0, cz), lens=35),
    }
    _dbg("g:atmos")
    release_bvh()
    A["build_time"] = time.time() - t0
    if ctx is not None:
        ctx.post.setdefault("grade", p.get("grade", "warm"))
    return A


# =============================================================================================
# Public sky helpers
# =============================================================================================
def night_sky(stars=True, moon=True, moon_az=210.0, moon_el=32.0, moon_light=0.35, strength=1.0, ctx=None,
              horizon=(0.012, 0.018, 0.032), zenith=(0.0015, 0.0025, 0.006), star_strength=1.0, clouds=0.0, **over):
    """Procedural night: deep-blue gradient sky + star field + moon disk with glow + cool moonlight lamp
    (sun object named 'Moon'). Returns the sky() result dict (res['nodes']['stars'] / ['moon'] keyable)."""
    p = sky_preset("night", stars=stars, moon=moon, moon_az=moon_az, moon_el=moon_el, moon_light=moon_light,
                   horizon=horizon, zenith=zenith, star_strength=star_strength, clouds=clouds, sun_az=moon_az, **over)
    p["bg"] = strength
    return sky(cfg=p, ctx=ctx)


def clouds_layer(coverage=0.5, height=1500.0, scale=0.00035, speed=(6.0, 2.0), color=(1.0, 0.97, 0.94),
                 shadow=(0.35, 0.33, 0.33), opacity=0.92, evolve=0.05, ctx=None):
    """Add/replace an animated procedural cloud layer (world shader, flat layer at `height` m) over the
    current sky (rebuilds the world from the last sky() config, keeps the sun lamp). speed in m/s
    (use ~60-200 for time-lapse streaks). Returns the sky() result."""
    st = _state()
    prev = st.get("sky")
    p = dict(prev["preset"]) if prev else sky_preset("noon")
    p["clouds"] = coverage
    p["cloud_opts"] = dict(height=height, scale=scale, speed=speed, color=color, shadow=shadow, opacity=opacity,
                           evolve=evolve)
    sun = prev.get("sun") if prev else None
    r = sky(cfg=p, ctx=ctx, keep_sun=sun is not None)
    if sun is not None:
        r["sun"] = sun
        st["sun_obj"] = sun
    return r


# =============================================================================================
# JUDEAN HILLS (+ day -> dusk -> night time-lapse)
# =============================================================================================
def _hills_height(seed=0, terraces=0.6, view_az=250.0):
    va = math.radians(view_az)
    fx, fy = math.sin(va), math.cos(va)

    def H(X, Y):
        X = np.asarray(X, float)
        Y = np.asarray(Y, float)
        r = np.sqrt(X ** 2 + Y ** 2)
        al = X * fx + Y * fy                 # along the view direction
        pe = -X * fy + Y * fx                # across
        # rounded limestone hills: smooth fbm + a broad ridge system
        h = 34 * fbm(X / 260.0, Y / 260.0, 4, gain=0.45, seed=seed + 1) + 22 * ridged(X / 420.0, Y / 420.0, 3, seed=seed + 2)
        # valley ahead of the camera, rising hills beyond it
        h = h - 26 * np.exp(-((al - 170) / 80.0) ** 2) * smoothstep(500, 100, np.abs(pe)) + 20 * smoothstep(250, 600, al)
        # the knoll the camera stands on: a rocky spur ending in a drop just ahead of the dead tree
        spur = 9.0 * smoothstep(14.0, 2.0, al) * smoothstep(-80.0, -30.0, al) * np.exp(-(pe / 45.0) ** 2)
        flat = np.exp(-((al + 10) / 45.0) ** 2 - (pe / 45.0) ** 2)
        h = h * (1 - 0.85 * flat) + spur
        if terraces:
            step = 1.6
            q = h / step
            fr = q - np.floor(q)
            tread = np.floor(q) * step + step * smoothstep(0.78, 1.0, fr)
            tm = smoothstep(-0.1, 0.35, fbm(X / 180.0, Y / 180.0, 2, seed=seed + 3)) * smoothstep(40, 90, r) * terraces
            h = h + (tread - h) * tm
        h += 0.35 * fbm(X * 0.08, Y * 0.08, 3, seed=seed + 4) + 0.08 * fbm(X * 0.5, Y * 0.5, 2, seed=seed + 5)
        h += smoothstep(1500, 3800, r) * (60 + 80 * fbm(X / 1200, Y / 1200, 3, seed=seed + 6))
        return h
    return H


def _hills_attrs(H, terraces):
    def A(X, Y, Z):
        n1 = fbm(X * 0.05, Y * 0.05, 3, seed=31)
        rock = np.clip((n1 - 0.15) * 2.0, 0, 1) * 0.8
        cav = np.zeros_like(Z)
        lap = (Z[:-2, 1:-1] + Z[2:, 1:-1] + Z[1:-1, :-2] + Z[1:-1, 2:] - 4 * Z[1:-1, 1:-1])
        cav[1:-1, 1:-1] = np.clip(lap * 1.5, 0, 1)
        # terrace risers -> exposed stone walls (high slope relative to neighbours)
        gy, gx = np.gradient(Z)
        riser = np.clip((np.abs(gx) + np.abs(gy)) * 0.8 - 0.5, 0, 1) * (terraces > 0)
        return dict(rock=np.maximum(rock, riser), cav=cav, path=np.zeros_like(Z), dust=np.zeros_like(Z))
    return A


def sun_dir_at(hour, lat=31.8, decl=9.0):
    """Approximate solar (elevation, compass azimuth) in degrees for a local solar hour (Jerusalem, April).
    Compass azimuth: 0 = north, 90 = east."""
    h = math.radians((hour - 12.0) * 15.0)
    la, de = math.radians(lat), math.radians(decl)
    el = math.asin(math.sin(la) * math.sin(de) + math.cos(la) * math.cos(de) * math.cos(h))
    az = math.atan2(-math.sin(h), math.tan(de) * math.cos(la) - math.sin(la) * math.cos(h))
    return math.degrees(el), (math.degrees(az) + 360) % 360


def _compass_to_core(az):
    """Compass azimuth (0 = north = +Y, 90 = east = +X) -> core.sun azimuth (0 = sun at -Y)."""
    return (180.0 - az) % 360


_SKY_PAL = [  # (elevation, zenith, horizon, sun-side glow) linear RGB
    (-90, (0.0012, 0.002, 0.005), (0.006, 0.009, 0.018), (0.0, 0.0, 0.0)),
    (-15, (0.0015, 0.0025, 0.006), (0.01, 0.014, 0.028), (0.0, 0.0, 0.0)),
    (-8, (0.005, 0.009, 0.024), (0.03, 0.032, 0.055), (0.05, 0.022, 0.012)),
    (-3, (0.02, 0.035, 0.09), (0.25, 0.15, 0.13), (0.7, 0.22, 0.06)),
    (1, (0.06, 0.1, 0.24), (0.8, 0.45, 0.24), (2.0, 0.75, 0.2)),
    (6, (0.1, 0.18, 0.4), (0.85, 0.62, 0.42), (1.6, 0.85, 0.35)),
    (15, (0.12, 0.24, 0.52), (0.7, 0.72, 0.75), (0.7, 0.5, 0.25)),
    (35, (0.13, 0.28, 0.62), (0.6, 0.7, 0.85), (0.35, 0.3, 0.2)),
    (90, (0.12, 0.27, 0.62), (0.55, 0.66, 0.84), (0.3, 0.28, 0.2)),
]


def sky_palette(el):
    """Zenith / horizon / sun-glow colours for a solar elevation (deg), used by the analytic sky."""
    P = _SKY_PAL
    for i in range(len(P) - 1):
        if P[i][0] <= el <= P[i + 1][0]:
            t = (el - P[i][0]) / (P[i + 1][0] - P[i][0])
            t = t * t * (3 - 2 * t)
            return tuple(tuple(P[i][k][j] + (P[i + 1][k][j] - P[i][k][j]) * t for j in range(3)) for k in (1, 2, 3))
    return P[-1][1], P[-1][2], P[-1][3]


def timelapse_sky(ctx, hour0=13.0, hour1=21.0, f0=1, f1=None, clouds=0.35, cloud_speed=(90.0, 30.0), stars=True,
                  moon=True, ease=True, sun_max=4.5, exposure_night=1.2, step=1, animate_haze=True, animate_world=True):
    """Animated day -> golden hour -> dusk -> night sky over frames f0..f1 (Nishita sky + star field +
    fast clouds + keyed sun lamp + moonlight + haze + exposure). Returns dict(sun, moon, keys...)."""
    sc = bpy.context.scene
    f1 = f1 or sc.frame_end
    st = _state()
    w = sc.world
    w.sun_threshold = 1e6
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    T = _NT(nt)
    out = T.node("ShaderNodeOutputWorld")
    tc = T.node("ShaderNodeTexCoord")
    view = tc.outputs["Generated"]
    vn = T.vmath("NORMALIZE", view)
    vz = T.sep(vn)[2]
    # analytic sky driven only by keyed socket values (uniforms -> no shader recompiles per frame;
    # animating Nishita properties recompiles the world every frame: 3x slower and +3 GB RAM)
    c_zen = _lattr(T, "env_tl_zenith", (0.1, 0.22, 0.55))
    c_hor = _lattr(T, "env_tl_horizon", (0.55, 0.65, 0.8))
    c_glow = _lattr(T, "env_tl_glow", (0.3, 0.25, 0.15))
    sdir = _lattr(T, "env_tl_sun_dir", (0.0, 1.0, 0.5))
    g = T.math("POWER", T.math("MAXIMUM", vz, 0.0), 0.42)
    col = T.mix(g, c_hor, c_zen)
    dot = T.vmath("DOT_PRODUCT", vn, sdir)
    ang = T.math("ARCCOSINE", T.math("MINIMUM", T.math("MAXIMUM", dot, -1.0), 1.0))
    low = T.math("POWER", T.math("SUBTRACT", 1.0, T.math("MAXIMUM", vz, 0.0)), 5.0)
    glow = T.math("ADD", T.math("MULTIPLY", T.math("EXPONENT", T.math("MULTIPLY", ang, -2.2)), low),
                  T.math("MULTIPLY", T.math("EXPONENT", T.math("MULTIPLY", ang, -9.0)), 0.6))
    col = T.mix(1.0, col, T.mix(1.0, c_glow, T.comb(glow, glow, glow), blend="MULTIPLY"), blend="ADD")
    res = dict(nodes={})
    if stars:
        col = _stars(T, view, col, 0.0, res)
    # sun disk + glow
    r = math.radians(0.6)
    disk = T.math("SUBTRACT", 1.0, T.math("MULTIPLY", T.math("SUBTRACT", ang, r), 1.0 / (r * 0.15)), clamp=True)
    halo = T.math("MULTIPLY", T.math("EXPONENT", T.math("MULTIPLY", ang, -14.0)), 0.8)
    sc_col = _lattr(T, "env_tl_sun_color", (1.0, 0.8, 0.5))
    sk = _lattr(T, "env_tl_sun_disk", 1.0)
    amt = T.math("MULTIPLY", T.math("ADD", T.math("MULTIPLY", disk, 40.0), halo), sk)
    col = T.mix(1.0, col, T.mix(1.0, sc_col, T.comb(amt, amt, amt), blend="MULTIPLY"), blend="ADD")
    if clouds:
        col = _cloud_layer(T, view, col, coverage=clouds, res=res, sun_dir=(0, 1, 0.2), speed=cloud_speed, evolve=0.6,
                           height=1800.0)
    # below horizon -> haze colour
    hz = _lattr(T, "env_tl_below", (0.5, 0.5, 0.5))
    below = T.math("MULTIPLY", T.math("SUBTRACT", 0.01, vz), 60.0, clamp=True)
    col = T.mix(below, col, hz)
    bg = T.node("ShaderNodeBackground")
    T.link(col, bg.inputs[0])
    T.link(bg.outputs[0], out.inputs["Surface"])
    sun = C.sun(elevation=30, azimuth=0, energy=sun_max, temp=5000, angle=1.0)
    sun.data.shadow_maximum_resolution = 0.002
    moon_o = None
    if moon:
        moon_o = C.sun(elevation=35, azimuth=_compass_to_core(110), energy=0.0, color=(0.55, 0.68, 1.0), angle=0.6)
        moon_o.name = "Moon"
    N = f1 - f0
    keys = []
    for f in range(f0, f1 + 2, step):
        u = min(1.0, max(0.0, (f - f0) / max(1, N)))
        if ease:
            u = 0.5 - 0.5 * math.cos(math.pi * u) * 0.25 + (u - 0.5) * 0.75   # mild ease
        hour = hour0 + (hour1 - hour0) * u
        el, az = sun_dir_at(hour)
        caz = _compass_to_core(az)
        d = _dir_from_az_el(caz, el)
        # sky palette for this solar elevation
        day = C.smoothstep((el + 6) / 12.0)                  # 0 at -6 deg (civil dusk) .. 1 at +6
        zc, hc, gc = sky_palette(el)
        kf = f if animate_world else None
        if animate_world or f == f0:
            for nm_, c in (("env_tl_zenith", zc), ("env_tl_horizon", hc), ("env_tl_glow", gc)):
                scene_prop(nm_, c, kf)
        scene_prop("env_tl_sun_dir", tuple(d), kf)
        temp = 1900 + 3600 * C.smoothstep(el / 35.0)
        kc = C.kelvin(temp)
        m = max(kc)
        scene_prop("env_tl_sun_color", [c / m for c in kc], kf)
        scene_prop("env_tl_sun_disk", 1.0 * C.smoothstep((el + 1.0) / 2.0), kf)
        if stars:
            scene_prop("env_stars", 1.6 * (1 - C.smoothstep((el + 9) / 7.0)), kf)
        # sun lamp
        sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        sun.keyframe_insert("rotation_euler", frame=f)
        sun.data.energy = sun_max * C.smoothstep((el + 0.5) / 7.0) * (0.55 + 0.45 * C.smoothstep(el / 25.0))
        sun.data.keyframe_insert("energy", frame=f)
        sun.data.color = [c / m for c in kc]
        sun.data.keyframe_insert("color", frame=f)
        if moon_o:
            moon_o.data.energy = 0.3 * (1 - C.smoothstep((el + 8) / 8.0))
            moon_o.data.keyframe_insert("energy", frame=f)
        # haze + horizon colour follows the sky
        warm = (1 - C.smoothstep(el / 12.0)) * day
        hzc = [hc[i] * 0.85 + gc[i] * 0.15 for i in range(3)]
        scene_prop("env_tl_below", hzc, kf)
        if animate_haze:
            set_haze(color=hzc, density=0.0004, sun_dir=d, sun_color=[hzc[i] * (1 + 2 * warm * kc[i] / m) for i in range(3)],
                     frame=f)
        elif f == f0:
            set_haze(color=hzc, density=0.0004, sun_dir=d)
        if exposure_night:
            sc.view_settings.exposure = exposure_night * (1 - day)
            sc.view_settings.keyframe_insert("exposure", frame=f)
        keys.append((f, hour, el, az))
    for idb in (sun, sun.data, sc):
        _linear_keys(idb)
    if moon_o:
        _linear_keys(moon_o.data)
    res.update(sun=sun, moon=moon_o, keys=keys, sun_dir=_dir_from_az_el(_compass_to_core(sun_dir_at(hour0)[1]),
                                                                        sun_dir_at(hour0)[0]))
    st["sun_obj"] = sun
    st["sky"] = dict(preset=sky_preset("noon"), nodes=res["nodes"], sun=sun)
    if ctx is not None:
        ctx.post.setdefault("grade", "neutral")
    return res


def judean_hills(ctx, mood="noon", timelapse=False, hour0=13.0, hour1=21.0, seed=0, terraces=0.6, olives=1.0,
                 dead_tree_=True, rocks=1.0, grass=1.0, view_az=250.0, sun_az=None, clouds=None):
    """Rolling Judean limestone hills: terraced slopes, sparse olive trees, rocks, dry grass and a lone
    dead tree on a rocky knoll near the origin (camera stands south-east of it looking `view_az`, compass,
    default WSW towards the sunset). timelapse=True animates day -> dusk -> night over the shot
    (hour0 -> hour1, local solar time) for s02a; otherwise the static sky `mood` is used.
    Returns anchors: dead_tree, knoll, ground(x, y), ground_z, cams {wide, low, high}, sky/timelapse."""
    t0 = time.time()
    rnd = np.random.default_rng(seed)
    A = dict(mood=mood)
    if timelapse:
        A["timelapse"] = timelapse_sky(ctx, hour0=hour0, hour1=hour1, f1=ctx.render_frames if ctx else None,
                                       clouds=0.35 if clouds is None else clouds)
    else:
        p = sky_preset(mood)
        if clouds is not None:
            p["clouds"] = clouds
        if sun_az is not None:
            p["sun_az"] = sun_az
        A["sky"] = sky(cfg=p, ctx=ctx)
    H = _hills_height(seed, terraces, view_az)
    gm = ground_material("EnvHillsGround", style="hills")
    terr = terrain_grid("JudeanHills", H, center=(0, 20), core=120, cell=0.5, extent=4200, growth=1.07, mat_=gm,
                        attrs_fn=_hills_attrs(H, terraces))
    A["terrain"] = terr
    va = math.radians(view_az)
    fwd = Vector((math.sin(va), math.cos(va), 0))
    side = Vector((fwd.y, -fwd.x, 0))
    tp = fwd * 0.5 + side * 2.2                       # dead tree near the spur edge, right of frame centre
    if dead_tree_:
        dt = dead_tree(seed=seed + 3, size=1.15)
        z = ground_z(tp.x, tp.y)
        A["dead_tree"] = place(dt, (tp.x, tp.y, z - 0.15), rot=(0, 0, 40))
    A["dead_tree_pos"] = (tp.x, tp.y, ground_z(tp.x, tp.y))
    A["knoll"] = (0.0, 0.0, ground_z(0, 0))
    boulders = rock_protos("boulders")
    small = rock_protos("rocks")
    if rocks:
        scatter(boulders, count=int(60 * rocks), seed=seed + 1, scale=(0.4, 1.3), align=0.7, sink=-0.35, tilt=8,
                region=("circle", 0, 0, 45), name="EnvHillBoulders", exclude=[(tp.x, tp.y, 1.5), (-fwd.x * 8, -fwd.y * 8, 3)],
                min_dist=3)
        scatter(small, count=int(900 * rocks), seed=seed + 2, scale=(0.6, 2.0), align=0.9, sink=-0.3, tilt=12,
                region=("circle", 0, 0, 60), name="EnvHillRocks")
        scatter(boulders, count=int(400 * rocks), seed=seed + 3, scale=(0.6, 1.6), align=0.7, sink=-0.35,
                region=("ring", 0, 0, 45, 400), name="EnvHillBouldersFar", min_dist=6)
    if grass:
        gr = grass_protos("dry")
        scatter(gr, count=int(12000 * grass), seed=seed + 4, scale=(0.5, 1.3), align=0.6, sink=0.02,
                region=("circle", 0, 0, 70), max_slope=35, name="EnvHillGrass", exclude=[(tp.x, tp.y, 0.8)],
                density=lambda X, Y: 0.3 + 0.7 * (fbm(X * 0.04, Y * 0.04, 2, seed=41) > -0.15))
        th = [thorn_bush(seed=i, size=0.8 + 0.3 * i) for i in range(3)]
        scatter(th, count=int(300 * grass), seed=seed + 5, scale=(0.8, 1.6), align=0.3, sink=0.05,
                region=("circle", 0, 0, 400), max_slope=35, name="EnvHillShrubs", exclude=[(0, 0, 8)])
    if olives:
        ol = [olive_tree(seed=10 + i, age=0.5 + 0.35 * i, size=0.9, lod=1) for i in range(3)]
        # sparse olives, mostly on terraces in the valley / slopes
        scatter(ol, count=int(160 * olives), seed=seed + 6, scale=(0.75, 1.15), align=0.0, sink=0.1,
                region=("ring", 0, 0, 35, 650), max_slope=22, name="EnvHillOlives", min_dist=9,
                density=lambda X, Y: 0.25 + 0.75 * (fbm(X / 150, Y / 150, 2, seed=51) > 0.05))
    A["fog"] = fog_volume((0, 150, 30), (500, 600, 70), 0.0012, (0.85, 0.82, 0.8), 0.4, height_falloff=0.03,
                          name="EnvHillAir")
    _set_volume_range(600)
    release_bvh()
    A["ground"] = _scalar(H)
    A["ground_z"] = ground_z
    kz = A["knoll"][2]
    eye = tp - fwd * 8.0 - side * 2.5
    eye.z = ground_z(eye.x, eye.y) + 1.7
    tgt = tp + fwd * 150
    tgt.z = eye.z + 4.0
    A["cams"] = {"wide": dict(loc=tuple(eye), target=tuple(tgt), lens=24),
                 "low": dict(loc=tuple(tp - fwd * 4.0 - side * 1.2 + Vector((0, 0, ground_z(*(tp - fwd * 4.0 - side * 1.2).xy) + 0.4))),
                             target=tuple(tp + Vector((0, 0, A["dead_tree_pos"][2] + 3.0))), lens=20),
                 "high": dict(loc=tuple(tp - fwd * 40 + Vector((0, 0, kz + 30))), target=tuple(tp + fwd * 250), lens=28)}
    A["build_time"] = time.time() - t0
    return A
