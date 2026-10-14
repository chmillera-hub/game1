"""Core helpers shared by every shot script (runs inside Blender 4.5, EEVEE Next).

Conventions
- Units: metres. Z is up. A standing adult is ~1.75 m. Ground at z=0 unless a terrain says otherwise.
- Portrait frame: render 540x960 (final), 270x480 (preview). Compose for 9:16 - keep key subjects in
  the centre square (the social-media preview crop) and leave the lower ~30% calm-ish for captions.
- Animate with explicit per-frame keys (`key_fn`) or a few eased keys (`keys`). Everything must be
  parameterised by ctx.nframes / ctx.render_frames so the timing can change without edits.
- Frames are 1-based: the shot's first frame is 1, last rendered frame is ctx.render_frames.
"""
import bpy, math, os, random, json
from mathutils import Vector, Euler, Matrix, Color, noise
from . import polyhaven as ph

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(BLENDER_DIR)
WORK = os.environ.get("WORK", "/opt/work/psalm22")
ASSETS = "/opt/assets"


# --------------------------------------------------------------------------------------------
# Context
# --------------------------------------------------------------------------------------------
class Ctx:
    """Shot context handed to build(ctx)."""

    def __init__(self, shot, quality="preview", fps=24):
        self.shot = shot
        self.id = shot["id"]
        self.fps = fps
        self.quality = quality
        self.nframes = shot["nframes"]              # frames on the final timeline
        self.render_frames = shot["render_frames"]  # nframes + dissolve tail
        self.phrases = shot.get("phrases", [])      # [{"text","start","end"}] seconds relative to shot start
        self.seed = sum(ord(c) for c in self.id)
        self.samples = None          # override EEVEE samples for final quality
        self.post = {}               # hints for the compositor (grade, bloom, vignette, ...)
        self.needs_bake = False      # set True when physics/particles need baking
        self.render_opts = {}        # passed to configure_render
        random.seed(self.seed)

    @property
    def end(self):
        return self.render_frames

    def frame(self, seconds):
        """Seconds (relative to shot start) -> 1-based frame."""
        return 1 + seconds * self.fps

    def sec(self, frame):
        return (frame - 1) / self.fps

    def phrase_frames(self, i):
        p = self.phrases[i]
        return self.frame(p["start"]), self.frame(p["end"])

    def u(self, frame):
        """Normalised progress 0..1 across the timeline part of the shot (tail continues > 1)."""
        return (frame - 1) / max(1, self.nframes - 1)


# --------------------------------------------------------------------------------------------
# Scene / render
# --------------------------------------------------------------------------------------------
def reset_scene(ctx):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = ctx.fps
    sc.frame_start = 1
    sc.frame_end = ctx.render_frames
    sc.frame_set(1)
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.unit_settings.system = "METRIC"
    return sc


def configure_render(ctx, samples=None, raytracing=False, volumetrics="medium", vol_shadows=True,
                     motion_blur=False, gtao=True, shadow_scale=1.0, film_transparent=False,
                     look=None, exposure=0.0, fast_gi=False):
    """Final render configuration. Called by the runner after build(); shots pass options through
    ctx.render_opts (same keyword names)."""
    sc = bpy.context.scene
    r = sc.render
    if ctx.quality == "final":
        r.resolution_x, r.resolution_y = 540, 960
        n = samples or ctx.samples or 8
    elif ctx.quality == "draft":
        r.resolution_x, r.resolution_y = 540, 960
        n = 3
    else:
        r.resolution_x, r.resolution_y = 270, 480
        n = 3
    r.resolution_percentage = 100
    r.film_transparent = film_transparent
    r.use_motion_blur = motion_blur
    r.motion_blur_shutter = 0.5
    ee = sc.eevee
    ee.taa_render_samples = n
    ee.use_raytracing = raytracing
    if raytracing:
        ee.ray_tracing_method = "SCREEN"
        ee.ray_tracing_options.resolution_scale = "2"
    ee.use_fast_gi = fast_gi
    ee.use_gtao = gtao
    ee.gtao_distance = 0.8
    ee.use_shadows = True
    ee.shadow_ray_count = 1
    ee.shadow_step_count = 6
    ee.shadow_resolution_scale = shadow_scale
    ee.use_volumetric_shadows = vol_shadows
    q = {"low": ("16", 32), "medium": ("8", 48), "high": ("4", 64)}[volumetrics]
    ee.volumetric_tile_size, ee.volumetric_samples = q
    ee.volumetric_shadow_samples = 12
    ee.motion_blur_steps = 1
    r.filter_size = 1.5
    sc.view_settings.view_transform = "AgX"
    if look:
        sc.view_settings.look = look
    sc.view_settings.exposure = exposure
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"
    r.image_settings.compression = 15


# --------------------------------------------------------------------------------------------
# Animation helpers
# --------------------------------------------------------------------------------------------
def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def smootherstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (x * 6 - 15) + 10)


def ease_in_out(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = min(1.0, max(0.0, x))
    return x ** 3


def lerp(a, b, t):
    if isinstance(a, (tuple, list, Vector)):
        return type(a)([a[i] + (b[i] - a[i]) * t for i in range(len(a))]) if not isinstance(a, Vector) else a.lerp(b, t)
    return a + (b - a) * t


def keys(target, path, pairs, interp="BEZIER", index=-1):
    """Insert keyframes: pairs = [(frame, value), ...]. Bezier with auto-clamped handles = eased."""
    for f, v in pairs:
        _set_path(target, path, v, index)
        target.keyframe_insert(data_path=path, frame=f, index=index)
    _set_interp(target, path, interp)


def key_fn(target, path, fn, f0=1, f1=None, step=1, index=-1):
    """Key every `step` frames from f0..f1 with value fn(frame). Linear interpolation."""
    f1 = f1 if f1 is not None else bpy.context.scene.frame_end
    f = f0
    while f <= f1:
        _set_path(target, path, fn(f), index)
        target.keyframe_insert(data_path=path, frame=f, index=index)
        f += step
    _set_interp(target, path, "LINEAR")


def _set_path(target, path, v, index):
    if index >= 0:
        getattr(target, path)[index] = v
    else:
        try:
            setattr(target, path, v)
        except (AttributeError, TypeError):
            # node socket default_value etc. accessed by path_resolve
            target.path_resolve(path)
            exec("target.%s = v" % path)


def _set_interp(target, path, interp):
    ad = target.animation_data if hasattr(target, "animation_data") else None
    if ad is None and hasattr(target, "id_data"):
        ad = target.id_data.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        if fc.data_path.endswith(path):
            for kp in fc.keyframe_points:
                kp.interpolation = interp
                if interp == "BEZIER":
                    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"


def _fcurves(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return action.fcurves
    out = []
    for layer in getattr(action, "layers", []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def shake(f, amp=0.01, freq=0.6, seed=0):
    """Smooth handheld noise vector for frame f (add to a camera location/rotation)."""
    t = f * freq / 24.0
    return Vector((noise.noise(Vector((t, seed, 0.3))), noise.noise(Vector((seed, t, 1.7))),
                   noise.noise(Vector((2.1, seed, t))))) * amp


# --------------------------------------------------------------------------------------------
# Objects / camera / lights
# --------------------------------------------------------------------------------------------
def link(obj, coll=None):
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def look_at(obj, target, roll=0.0):
    d = Vector(target) - obj.location
    q = d.to_track_quat("-Z", "Y")
    obj.rotation_euler = q.to_euler()
    if roll:
        obj.rotation_euler.rotate_axis("Z", math.radians(roll))
    return obj.rotation_euler.copy()


def look_rot(loc, target, roll=0.0):
    e = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if roll:
        e.rotate_axis("Z", math.radians(roll))
    return e


def camera(loc=(0, -6, 1.6), target=(0, 0, 1.5), lens=35, name="Camera", fstop=None, focus=None,
           sensor=36, clip_end=20000):
    """Create + activate a camera. fstop enables DOF; focus = distance (float) or object."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_fit = "VERTICAL"
    cd.sensor_height = sensor   # vertical sensor so lens values feel like full-frame on a portrait frame
    cd.clip_start = 0.02
    cd.clip_end = clip_end
    cam = link(bpy.data.objects.new(name, cd))
    cam.location = loc
    look_at(cam, target)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if isinstance(focus, bpy.types.Object):
            cd.dof.focus_object = focus
        elif focus is not None:
            cd.dof.focus_distance = focus
        else:
            cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    bpy.context.scene.camera = cam
    return cam


def animate_camera(cam, fn, f0=1, f1=None, step=1):
    """fn(frame) -> (location, target[, roll_deg[, lens]]). Keys every frame (smooth, exact)."""
    f1 = f1 or bpy.context.scene.frame_end
    f = f0
    while f <= f1:
        r = fn(f)
        loc, tgt = Vector(r[0]), Vector(r[1])
        roll = r[2] if len(r) > 2 else 0.0
        cam.location = loc
        cam.rotation_euler = look_rot(loc, tgt, roll)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
        if len(r) > 3 and r[3]:
            cam.data.lens = r[3]
            cam.data.keyframe_insert("lens", frame=f)
        if cam.data.dof.use_dof and cam.data.dof.focus_object is None and len(r) > 4 and r[4]:
            cam.data.dof.focus_distance = r[4]
            cam.data.dof.keyframe_insert("focus_distance", frame=f)
        f += step
    _set_interp(cam, "location", "LINEAR")
    _set_interp(cam, "rotation_euler", "LINEAR")
    _unwrap_euler(cam)


def _unwrap_euler(obj):
    ad = obj.animation_data
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        if fc.data_path == "rotation_euler":
            prev = None
            for kp in fc.keyframe_points:
                v = kp.co[1]
                if prev is not None:
                    while v - prev > math.pi:
                        v -= 2 * math.pi
                    while v - prev < -math.pi:
                        v += 2 * math.pi
                kp.co[1] = v
                kp.handle_left[1] = kp.handle_right[1] = v
                prev = v


def kelvin(k):
    """Approximate blackbody colour (linear-ish RGB) for colour temperature k."""
    t = k / 100.0
    if t <= 66:
        r = 255
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * ((t - 60) ** -0.1332047592)
        g = 288.1221695283 * ((t - 60) ** -0.0755148492)
        b = 255
    c = [min(255, max(0, x)) / 255.0 for x in (r, g, b)]
    return tuple(x ** 2.2 for x in c)


def light(kind="AREA", loc=(0, 0, 5), energy=100, color=(1, 1, 1), target=None, size=1.0, name=None,
          spot_size=45, spot_blend=0.3, shadow=True, temp=None, volume=1.0, rot=None):
    """kind: SUN (energy = W/m2 ~1-10), AREA/POINT/SPOT (energy in W)."""
    ld = bpy.data.lights.new(name or kind.lower(), kind)
    ld.energy = energy
    ld.color = kelvin(temp) if temp else color
    ld.use_shadow = shadow
    ld.volume_factor = volume
    if kind == "AREA":
        ld.size = size
    elif kind == "SUN":
        ld.angle = math.radians(size if size != 1.0 else 1.0)
    else:
        ld.shadow_soft_size = size if kind in ("POINT", "SPOT") else ld.shadow_soft_size
    if kind == "SPOT":
        ld.spot_size = math.radians(spot_size)
        ld.spot_blend = spot_blend
    ob = link(bpy.data.objects.new(ld.name, ld))
    ob.location = loc
    if rot is not None:
        ob.rotation_euler = [math.radians(a) for a in rot]
    elif target is not None:
        look_at(ob, target)
    return ob


def sun(elevation=30, azimuth=0, energy=4, color=None, temp=5500, angle=1.0, volume=1.0):
    """Sun light. azimuth 0 = light comes FROM -Y (in front of a camera looking +Y). Degrees."""
    ld = bpy.data.lights.new("Sun", "SUN")
    ld.energy = energy
    ld.color = color if color else kelvin(temp)
    ld.angle = math.radians(angle)
    ld.volume_factor = volume
    ob = link(bpy.data.objects.new("Sun", ld))
    el, az = math.radians(elevation), math.radians(azimuth)
    d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))  # towards the sun
    ob.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    ob.location = d * 50
    return ob


# --------------------------------------------------------------------------------------------
# World
# --------------------------------------------------------------------------------------------
def _world():
    w = bpy.context.scene.world
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    return w, nt, out


def world_color(color=(0.02, 0.025, 0.035), strength=1.0):
    w, nt, out = _world()
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return bg


def world_sky(sun_elevation=20, sun_rotation=0, strength=1.0, air=1.0, dust=1.0, ozone=1.0,
              altitude=0, sun_disc=True, sun_size=0.545, sun_intensity=1.0, tint=None):
    """Nishita physical sky. sun_rotation 0 => sun toward -Y? (Blender: rotation around Z from +Y)."""
    w, nt, out = _world()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(sun_elevation)
    sky.sun_rotation = math.radians(sun_rotation)
    sky.air_density, sky.dust_density, sky.ozone_density = air, dust, ozone
    sky.altitude = altitude
    sky.sun_disc = sun_disc
    sky.sun_size = math.radians(sun_size)
    sky.sun_intensity = sun_intensity
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    if tint:
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1
        mix.inputs[2].default_value = (*tint, 1)
        nt.links.new(sky.outputs[0], mix.inputs[1])
        nt.links.new(mix.outputs[0], bg.inputs[0])
    else:
        nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return sky, bg


def world_hdri(asset, strength=1.0, rotation=0.0, res="2k", tint=None, saturation=1.0, path=None,
               background_strength=None):
    """Poly Haven HDRI as world. rotation in degrees around Z. Optional tint (rgb multiply) and
    saturation. background_strength lets the visible sky differ from the lighting strength."""
    p = path or ph.hdri_path(asset, res)
    w, nt, out = _world()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value[2] = math.radians(rotation)
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(p, check_existing=True)
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
    col = env.outputs["Color"]
    if saturation != 1.0:
        hs = nt.nodes.new("ShaderNodeHueSaturation")
        hs.inputs["Saturation"].default_value = saturation
        nt.links.new(col, hs.inputs["Color"])
        col = hs.outputs["Color"]
    if tint:
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1
        mix.inputs[2].default_value = (*tint, 1)
        nt.links.new(col, mix.inputs[1])
        col = mix.outputs[0]
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    nt.links.new(col, bg.inputs[0])
    if background_strength is not None:
        lp = nt.nodes.new("ShaderNodeLightPath")
        bg2 = nt.nodes.new("ShaderNodeBackground")
        bg2.inputs[1].default_value = background_strength
        nt.links.new(col, bg2.inputs[0])
        ms = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], ms.inputs[0])
        nt.links.new(bg.outputs[0], ms.inputs[1])
        nt.links.new(bg2.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return env, bg, mp


def world_volume(*a, **k):
    raise RuntimeError("Do not use a world volume: in EEVEE Next it is infinite and blacks out the sky "
                       "and sun. Use core.atmosphere(...) or core.fog_box(...) instead.")


def atmosphere(density=0.002, color=(0.8, 0.75, 0.7), anisotropy=0.3, size=(600, 600, 150), center=(0, 0, 60),
               noise_scale=None, name="Atmosphere"):
    """Large finite fog volume for aerial perspective + god rays (with sun volume shadows). Keep
    density small (0.0005-0.01). The sky (world) stays visible through it."""
    return fog_box(center=center, size=size, density=density, color=color, anisotropy=anisotropy,
                   noise_scale=noise_scale, name=name)


# --------------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------------
def mat(name, color=(0.8, 0.8, 0.8), rough=0.5, metal=0.0, spec=0.5, emission=None, emission_strength=0.0,
        alpha=1.0, sss=0.0, sss_radius=(1.0, 0.4, 0.2), transmission=0.0, ior=1.45, coat=0.0, sheen=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color[:3], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["IOR"].default_value = ior
    if emission is not None:
        b.inputs["Emission Color"].default_value = (*emission[:3], 1)
        b.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = sss_radius
    if transmission:
        b.inputs["Transmission Weight"].default_value = transmission
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    return m


def bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF")


def mat_emission(name, color=(1, 0.8, 0.5), strength=10.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*color, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return m


def mat_volume(name, density=0.1, color=(0.8, 0.8, 0.8), anisotropy=0.2, noise_scale=None, noise_contrast=1.0,
               emission=None, emission_strength=0.0):
    """Volume material for fog boxes / smoke. noise_scale adds wispy density variation."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    v = nt.nodes.new("ShaderNodeVolumePrincipled")
    v.inputs["Color"].default_value = (*color, 1)
    v.inputs["Anisotropy"].default_value = anisotropy
    if emission:
        v.inputs["Emission Color"].default_value = (*emission, 1)
        v.inputs["Emission Strength"].default_value = emission_strength
    if noise_scale:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 3
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.35 + 0.1 * (noise_contrast - 1)
        mr.inputs["From Max"].default_value = 0.75
        mr.inputs["To Max"].default_value = density
        nt.links.new(tex.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], v.inputs["Density"])
        m["noise_node"] = tex.name
    else:
        v.inputs["Density"].default_value = density
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    return m


def mat_pbr(asset, scale=1.0, res="1k", projection="BOX", tint=None, rough_mult=1.0, rough_add=0.0,
            bump=1.0, name=None, hue_sat_val=None, blend=0.25):
    """Poly Haven texture set as a material. projection 'BOX' uses object coordinates (no UVs needed,
    `scale` = repeats per metre); 'UV' uses the mesh UVs (scale = UV repeat)."""
    maps = ph.texture_maps(asset, res)
    m = bpy.data.materials.new(name or asset)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object" if projection == "BOX" else "UV"], mp.inputs["Vector"])

    def img(path, noncolor=False):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(path, check_existing=True)
        if noncolor:
            t.image.colorspace_settings.name = "Non-Color"
        if projection == "BOX":
            t.projection = "BOX"
            t.projection_blend = blend
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t

    if "diff" in maps:
        d = img(maps["diff"])
        col = d.outputs["Color"]
        if hue_sat_val:
            hs = nt.nodes.new("ShaderNodeHueSaturation")
            hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value, hs.inputs["Value"].default_value = hue_sat_val
            nt.links.new(col, hs.inputs["Color"])
            col = hs.outputs["Color"]
        if tint:
            mx = nt.nodes.new("ShaderNodeMixRGB")
            mx.blend_type = "MULTIPLY"
            mx.inputs[0].default_value = 1
            mx.inputs[2].default_value = (*tint, 1)
            nt.links.new(col, mx.inputs[1])
            col = mx.outputs[0]
        nt.links.new(col, b.inputs["Base Color"])
    if "rough" in maps:
        r = img(maps["rough"], True)
        mth = nt.nodes.new("ShaderNodeMath")
        mth.operation = "MULTIPLY_ADD"
        mth.inputs[1].default_value = rough_mult
        mth.inputs[2].default_value = rough_add
        mth.use_clamp = True
        nt.links.new(r.outputs["Color"], mth.inputs[0])
        nt.links.new(mth.outputs[0], b.inputs["Roughness"])
    if "nor" in maps and bump > 0:
        n = img(maps["nor"], True)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = bump
        nt.links.new(n.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    m["ph_maps"] = json.dumps(maps)
    return m


def assign(obj, material, slot=None):
    if obj.data.materials and slot is None:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)
    return obj


# --------------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------------
def _new_mesh_obj(name, verts, faces, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return link(bpy.data.objects.new(name, me), coll)


def shade_smooth(obj, angle=None):
    for p in obj.data.polygons:
        p.use_smooth = True
    if angle is not None and hasattr(obj, "modifiers"):
        try:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
        except Exception:
            pass
    return obj


def box(name="Box", size=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0), mat_=None, bevel=0.0, coll=None):
    sx, sy, sz = [s / 2 for s in size]
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz), (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = _new_mesh_obj(name, v, f, coll)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    if bevel:
        bm = o.modifiers.new("bevel", "BEVEL")
        bm.width = bevel
        bm.segments = 2
    if mat_:
        assign(o, mat_)
    return o


def prim(kind, name=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), mat_=None, **kw):
    """bpy.ops primitive wrapper: kind in plane, cube, uv_sphere, ico_sphere, cylinder, cone, torus, circle, grid."""
    fn = getattr(bpy.ops.mesh, "primitive_%s_add" % kind)
    fn(location=loc, rotation=[math.radians(a) for a in rot], **kw)
    o = bpy.context.active_object
    o.scale = scale
    if name:
        o.name = name
    if mat_:
        assign(o, mat_)
    return o


def fbm(x, y, octaves=5, lac=2.0, gain=0.5, seed=0.0):
    a, f, s = 1.0, 1.0, 0.0
    for i in range(octaves):
        s += a * noise.noise(Vector((x * f, y * f, seed + i * 7.31)))
        a *= gain
        f *= lac
    return s


def terrain(name="Terrain", size=200.0, res=160, height=1.5, scale=0.04, seed=0.0, mat_=None,
            height_fn=None, sizey=None, coll=None):
    """Grid terrain. Height = fbm noise * height (+ height_fn(x, y) if given). Returns object with
    .height_at(x, y) helper stored in core.TERRAIN for prop placement."""
    sx, sy = size, (sizey or size)
    nx, ny = res, int(res * sy / sx)
    verts, faces = [], []
    for j in range(ny + 1):
        for i in range(nx + 1):
            x = -sx / 2 + sx * i / nx
            y = -sy / 2 + sy * j / ny
            z = fbm(x * scale, y * scale, seed=seed) * height
            if height_fn:
                z += height_fn(x, y)
            verts.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    o = _new_mesh_obj(name, verts, faces, coll)
    shade_smooth(o)
    if mat_:
        assign(o, mat_)
    TERRAINS[name] = (sx, sy, height, scale, seed, height_fn)
    return o


TERRAINS = {}


def height_at(name, x, y):
    sx, sy, height, scale, seed, height_fn = TERRAINS[name]
    z = fbm(x * scale, y * scale, seed=seed) * height
    if height_fn:
        z += height_fn(x, y)
    return z


def golgotha_hill(peak=9.0, radius=38.0, cx=0.0, cy=0.0):
    """Height function for a rounded rocky hill (add to terrain via height_fn)."""
    def f(x, y):
        d2 = ((x - cx) ** 2 + (y - cy) ** 2) / (radius ** 2)
        return peak * math.exp(-d2 * 2.2)
    return f


def displace(obj, strength=0.2, scale=1.0, texture="CLOUDS", subdiv=0, midlevel=0.5, coords="LOCAL"):
    if subdiv:
        s = obj.modifiers.new("subdiv", "SUBSURF")
        s.levels = s.render_levels = subdiv
    t = bpy.data.textures.new(obj.name + "_disp", texture)
    if hasattr(t, "noise_scale"):
        t.noise_scale = scale
    m = obj.modifiers.new("displace", "DISPLACE")
    m.texture = t
    m.strength = strength
    m.mid_level = midlevel
    m.texture_coords = coords
    return m


def append_blend(path, names=None, kind="objects", coll=None):
    """Append datablocks from a .blend. Returns appended objects (linked to coll / scene)."""
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        avail = getattr(src, kind)
        setattr(dst, kind, [n for n in avail if (names is None or n in names)])
    got = list(getattr(dst, kind))
    if kind == "objects":
        for o in got:
            if o is not None:
                link(o, coll)
    return got


def ph_model(asset, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0, res="1k", coll=None, name=None):
    """Append a Poly Haven model (all its mesh objects), parented to an empty you can move."""
    path = ph.model_blend(asset, res)
    objs = [o for o in append_blend(path, kind="objects", coll=coll) if o is not None]
    root = link(bpy.data.objects.new(name or asset, None), coll)
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot]
    root.scale = (scale, scale, scale)
    return root, objs


def instance(src_root, loc, rot=(0, 0, 0), scale=1.0, coll=None):
    """Cheap linked duplicate of a hierarchy (meshes shared)."""
    root = link(bpy.data.objects.new(src_root.name + "_inst", None), coll)
    for ch in src_root.children:
        d = ch.copy()
        link(d, coll)
        d.parent = root
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot]
    root.scale = (scale, scale, scale) if not isinstance(scale, (tuple, list)) else scale
    return root


# --------------------------------------------------------------------------------------------
# Common props
# --------------------------------------------------------------------------------------------
_WOOD = {}


def wood_material(kind="rough_wood", scale=1.2, tint=(0.75, 0.62, 0.5)):
    key = (kind, scale, tint)
    if key not in _WOOD:
        _WOOD[key] = mat_pbr(kind, scale=scale, tint=tint, name="wood_" + kind)
    return _WOOD[key]


def wooden_cross(loc=(0, 0, 0), height=4.3, beam=2.0, thick=0.2, cross_at=0.78, rot_z=0, name="Cross",
                 material=None, sign=False, coll=None):
    """Rough-hewn cross. loc = base on the ground. Returns root empty; child objects 'upright',
    'beam' (and 'sign'). The crossbeam centre is at z = height*cross_at."""
    material = material or wood_material()
    root = link(bpy.data.objects.new(name, None), coll)
    up = box(name + "_upright", (thick, thick * 0.95, height), (0, 0, height / 2), mat_=material, bevel=0.01, coll=coll)
    bm = box(name + "_beam", (beam, thick * 0.9, thick * 0.85), (0, -thick * 0.05, height * cross_at), mat_=material, bevel=0.01, coll=coll)
    for o in (up, bm):
        o.parent = root
        displace(o, strength=0.012, scale=0.08, subdiv=0)
    parts = [up, bm]
    if sign:
        s = box(name + "_sign", (0.55, 0.03, 0.22), (0, -thick * 0.55, height * cross_at + 0.42),
                mat_=mat_pbr("wood_table_worn", scale=2, tint=(0.9, 0.85, 0.75), name="sign_wood"), coll=coll)
        s.parent = root
        parts.append(s)
    root.location = loc
    root.rotation_euler = (0, 0, math.radians(rot_z))
    return root


def dust_motes(center=(0, 0, 1.5), size=(6, 6, 3), count=400, radius=0.004, color=(1.0, 0.92, 0.8),
               emission=0.0, drift=(0.05, 0.02, 0.01), brownian=0.03, seed=0, coll=None, start=-60):
    """Floating dust particles (backlit specks). Uses a particle system; sets ctx bake need via caller."""
    v = []
    rnd = random.Random(seed)
    cx, cy, cz = center
    for _ in range(count):
        v.append((cx + (rnd.random() - 0.5) * size[0], cy + (rnd.random() - 0.5) * size[1], cz + (rnd.random() - 0.5) * size[2]))
    em = _new_mesh_obj("dust_emitter", v, [], coll)
    sp = prim("ico_sphere", name="dust_speck", subdivisions=1, radius=radius)
    m = mat("dust", color, rough=1.0, emission=color if emission else None, emission_strength=emission)
    assign(sp, m)
    sp.hide_render = False
    sp.location = (0, 0, -1000)
    ps = em.modifiers.new("dust", "PARTICLE_SYSTEM").particle_system
    st = ps.settings
    st.count = count
    st.emit_from = "VERT"
    st.use_emit_random = False
    st.frame_start = st.frame_end = start
    st.lifetime = 100000
    st.normal_factor = 0
    st.object_align_factor = drift
    st.brownian_factor = brownian
    st.effector_weights.gravity = 0
    st.render_type = "OBJECT"
    st.instance_object = sp
    st.particle_size = 1.0
    st.size_random = 0.6
    st.physics_type = "NEWTON"
    em.show_instancer_for_render = False
    return em


def fog_box(center=(0, 0, 2), size=(20, 20, 4), density=0.03, color=(0.8, 0.78, 0.75), anisotropy=0.3,
            noise_scale=None, name="Fog", coll=None):
    o = box(name, size, center, coll=coll)
    assign(o, mat_volume(name + "_vol", density, color, anisotropy, noise_scale))
    return o


def ground_plane(size=400, mat_=None, z=0.0, name="Ground"):
    o = prim("plane", name=name, size=size, loc=(0, 0, z))
    if mat_:
        assign(o, mat_)
    return o


# --------------------------------------------------------------------------------------------
# Baking / misc
# --------------------------------------------------------------------------------------------
def bake_all(ctx):
    """Bake particles / cloth / rigid bodies sequentially so random-access frame renders work."""
    sc = bpy.context.scene
    cache_dir = os.path.join(WORK, "cache", ctx.id)
    os.makedirs(cache_dir, exist_ok=True)
    # Step the timeline once: particle systems and cloth without disk cache get evaluated in memory.
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
    try:
        with bpy.context.temp_override(scene=sc):
            bpy.ops.ptcache.bake_all(bake=True)
    except Exception as e:
        print("bake_all warning:", e)
    sc.frame_set(1)


def save_post(ctx, path):
    data = dict(ctx.post)
    data["id"] = ctx.id
    json.dump(data, open(path, "w"), indent=1)
