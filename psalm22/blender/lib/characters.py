"""People system for "Psalm 22" - every human in the film (Blender 4.5, EEVEE Next, MPFB 2).

    from lib import characters as P
    j = P.make_person("jesus", P.JESUS_CROSS)            # preset (dict) or preset name "JESUS_CROSS"
    P.place_on_cross(j, cross_root, head="up", strain=0.6)
    P.expression(j, "anguish")
    m = P.make_person("m1", "CROWD_MAN", seed=3, age_years=50)
    P.pose(m, "point", target=(0, 2, 3))
    P.key_pose(m, 1, "stand"); P.key_pose(m, 40, "arms_raised")

See psalm22/docs/characters.md for the full API.
Conventions: metres, Z up, a person is built at the origin facing -Y (towards a default core.camera).
.rig (armature object) is the parent of everything; move/rotate the person through .rig / .root.
"""
import bpy, math, os, random, time, json, hashlib
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler, noise
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from . import core as C

MPFB_DATA = os.path.expanduser("~/.config/blender/4.5/extensions/.user/user_default/mpfb/data")
MPFB_SYS = os.path.expanduser("~/.config/blender/4.5/extensions/user_default/mpfb/data")
LOG_PREFIX = "[characters]"

FWD = Vector((0, -1, 0))     # a person faces -Y in its own (rig) space
LEFT = Vector((1, 0, 0))     # character's left (.L bones) is +X
UP = Vector((0, 0, 1))


def _log(*a):
    print(LOG_PREFIX, *a)


# ============================================================================================
# MPFB access
# ============================================================================================
_M = {}


def _mpfb():
    if not _M:
        from bl_ext.user_default.mpfb.services.humanservice import HumanService
        from bl_ext.user_default.mpfb.services.targetservice import TargetService
        from bl_ext.user_default.mpfb.entities.clothes.mhclo import Mhclo
        _M.update(HS=HumanService, TS=TargetService, Mhclo=Mhclo)
        try:  # MPFB is chatty on stdout; keep warnings only
            from bl_ext.user_default.mpfb.services.logservice import LogService
            LogService.set_default_log_level(2)
        except Exception:
            pass
    return _M


def _asset(kind, name):
    """MPFB asset fragment 'name/name.ext' for deserialize_from_dict."""
    ext = {"skins": "mhmat", "proxymeshes": "proxy"}.get(kind, "mhclo")
    if kind == "teeth" and name == "teeth_base":
        return "teeth_base/teeth_base.mhclo"
    return "%s/%s.%s" % (name, name, ext)


def _asset_path(kind, name):
    d = os.path.join(MPFB_DATA, kind, name)
    for f in os.listdir(d):
        if f.endswith((".mhclo", ".proxy")):
            return os.path.join(d, f)
    return None


# ============================================================================================
# Tables
# ============================================================================================
HAIR_COLORS = {   # linear RGB base albedo of a strand
    "black": (0.014, 0.011, 0.009),
    "dark_brown": (0.038, 0.022, 0.013),
    "brown": (0.075, 0.042, 0.020),
    "light_brown": (0.16, 0.10, 0.052),
    "auburn": (0.13, 0.045, 0.018),
    "blonde": (0.38, 0.27, 0.14),
    "grey": (0.26, 0.25, 0.24),
    "white": (0.50, 0.48, 0.44),
}
EYE_COLORS = {    # (major, minor, border)
    "brown": ((0.095, 0.042, 0.014), (0.032, 0.014, 0.006), (0.012, 0.007, 0.004)),
    "dark_brown": ((0.042, 0.019, 0.008), (0.016, 0.008, 0.004), (0.008, 0.005, 0.003)),
    "hazel": ((0.16, 0.10, 0.035), (0.05, 0.045, 0.018), (0.02, 0.015, 0.008)),
    "green": ((0.09, 0.14, 0.06), (0.04, 0.05, 0.02), (0.015, 0.02, 0.01)),
    "blue": ((0.20, 0.34, 0.55), (0.06, 0.11, 0.22), (0.02, 0.03, 0.06)),
    "grey": ((0.30, 0.33, 0.36), (0.10, 0.12, 0.14), (0.04, 0.045, 0.05)),
}
BUILDS = {        # muscle, weight, proportions
    "frail": (0.22, 0.12, 0.45),
    "lean": (0.55, 0.28, 0.65),
    "average": (0.5, 0.5, 0.55),
    "heavy": (0.45, 0.85, 0.5),
    "muscular": (0.9, 0.55, 0.7),
}
# race mix (caucasian, african, asian), skin texture family, tint rgb, tint amount, saturation, value,
# default hair colour, default eye colour
ETHNICITY = {
    "judean": dict(race=(0.80, 0.12, 0.08), skin="caucasian", tint=(0.93, 0.70, 0.46), tint_amt=0.8, sat=0.82, val=0.64, hue=0.515,
                   hair="dark_brown", eyes="brown"),
    "arab": dict(race=(0.78, 0.16, 0.06), skin="caucasian", tint=(0.9, 0.66, 0.43), tint_amt=0.85, sat=0.82, val=0.58, hue=0.515,
                 hair="black", eyes="dark_brown"),
    "african": dict(race=(0.06, 0.90, 0.04), skin="african", tint=(1.0, 0.92, 0.85), tint_amt=0.15, sat=1.0, val=0.95, hue=0.5,
                    hair="black", eyes="dark_brown"),
    "east_asian": dict(race=(0.10, 0.04, 0.86), skin="asian", tint=(1.0, 0.88, 0.70), tint_amt=0.38, sat=0.95, val=0.95, hue=0.505,
                       hair="black", eyes="dark_brown"),
    "south_asian": dict(race=(0.50, 0.38, 0.12), skin="caucasian", tint=(0.86, 0.60, 0.40), tint_amt=0.85, sat=0.95, val=0.62, hue=0.505,
                        hair="black", eyes="dark_brown"),
    "european": dict(race=(0.96, 0.02, 0.02), skin="caucasian", tint=(1.0, 0.93, 0.86), tint_amt=0.15, sat=0.95, val=0.97, hue=0.5,
                     hair="brown", eyes="blue"),
    "latin": dict(race=(0.62, 0.22, 0.16), skin="caucasian", tint=(0.93, 0.72, 0.5), tint_amt=0.75, sat=0.85, val=0.66, hue=0.512,
                  hair="dark_brown", eyes="brown"),
}
HAIR_STYLES = ["long01", "short01", "short02", "short03", "short04", "bob01", "bob02", "ponytail01", "braid01", "afro01", "none"]
BEARDS = {        # length (m), strand count, points per strand, stiffness (0 droopy .. 1 stiff), curl amplitude
    "none": None,
    "stubble": None,
    "short": dict(length=0.012, count=9000, points=5, stiff=0.75, curl=0.0012, lift=0.45),
    "full": dict(length=0.034, count=11000, points=7, stiff=0.45, curl=0.0026, lift=0.35),
    "long": dict(length=0.11, count=14000, points=11, stiff=0.18, curl=0.011, lift=0.3),
}

DEFAULT_SPEC = dict(
    gender=1.0, age_years=30.0, build="average", height_cm=None, ethnicity="judean", skin_tone=None,
    hair="short02", hair_color=None, grey=None, beard="none", beard_color=None, beard_length=None,
    eye_color=None, eyebrows=None, sweat=0.0, dirt=0.0, blood=0.0, scars=0.0, expression="neutral",
    lod="hero", outfit=None, outfit_colors=None, outfit_seed=0, pose="stand_relaxed", face=None, seed=0,
    wrinkles=None, redness=0.35,
)

# --------------------------------------------------------------------------------------------
# The cast
# --------------------------------------------------------------------------------------------
_JESUS = dict(gender=1.0, age_years=33, build="lean", height_cm=176, ethnicity="judean", hair="long01",
              hair_color="dark_brown", beard="full", eye_color="brown", eyebrows="eyebrow001", wrinkles=0.35,
              face={"head/head-oval": 0.35, "nose/nose-hump-decr|incr": 0.25, "nose/nose-scale-vert-decr|incr": 0.15,
                    "cheek/r-cheek-bones-decr|incr": 0.25, "cheek/l-cheek-bones-decr|incr": 0.25,
                    "eyebrows/eyebrows-trans-down|up": -0.2, "chin/chin-width-decr|incr": -0.1,
                    "cheek/l-cheek-inner-decr|incr": 0.3, "cheek/r-cheek-inner-decr|incr": 0.3})
JESUS_CROSS = dict(_JESUS, sweat=0.75, dirt=0.5, blood=0.55, expression="anguish", outfit=["loincloth", "crown_of_thorns"],
                   pose="crucified", redness=0.45)
JESUS_ROBED = dict(_JESUS, sweat=0.35, dirt=0.15, expression="sorrow", outfit=["robe", "sandals"],
                   outfit_colors={"tunic": "cream", "mantle": "madder"}, pose="stand")
JESUS_RISEN = dict(_JESUS, sweat=0.0, dirt=0.0, blood=0.0, scars=1.0, expression="peace", redness=0.3,
                   outfit=["robe", "sandals"], outfit_colors={"tunic": "bleached", "mantle": "white_linen"},
                   pose="stand")
MARY_YOUNG = dict(gender=0.0, age_years=17, build="lean", height_cm=157, ethnicity="judean", hair="braid01",
                  hair_color="dark_brown", eye_color="brown", eyebrows="eyebrow010", expression="peace",
                  outfit=["tunic", "veil"], outfit_colors={"tunic": "linen", "veil": "mary_blue"}, pose="stand", redness=0.4,
                  face={"nose/nose-scale-horiz-decr|incr": -0.15, "mouth/mouth-scale-horiz-decr|incr": -0.1})
MARY_OLD = dict(gender=0.0, age_years=48, build="average", height_cm=156, ethnicity="judean", hair="braid01",
                hair_color="dark_brown", grey=0.2, eye_color="brown", eyebrows="eyebrow010", expression="sorrow",
                outfit=["tunic", "veil"], outfit_colors={"tunic": "umber", "veil": "blue_grey"},
                pose="mourn", dirt=0.15, wrinkles=0.6, redness=0.5)
PRIEST = dict(gender=1.0, age_years=56, build="heavy", height_cm=172, ethnicity="judean", hair="short02",
              hair_color="black", grey=0.55, beard="full", eye_color="dark_brown", eyebrows="eyebrow003",
              expression="sneer", outfit=["robe_rich", "turban"], pose="stand", wrinkles=0.7)
ELDER = dict(gender=1.0, age_years=72, build="frail", height_cm=168, ethnicity="judean", hair="short01",
             hair_color="white", grey=0.9, beard="long", beard_length=0.16, eye_color="brown", eyebrows="eyebrow003",
             expression="neutral", outfit=["robe"], outfit_colors={"tunic": "oatmeal", "mantle": "brown"},
             pose="stand_relaxed", dirt=0.2, wrinkles=1.0)
CHILD = dict(gender=1.0, age_years=7, build="lean", ethnicity="judean", hair="short04", hair_color="dark_brown",
             eye_color="brown", eyebrows="eyebrow009", expression="awe", outfit=["tunic"], pose="stand", redness=0.4)
BABY = dict(gender=0.5, age_years=0.0, build="average", height_cm=52, ethnicity="judean", hair="none", eye_color="dark_brown",
            eyebrows="none", expression="sleep", outfit=["swaddle"], pose="baby", redness=0.6)
SOLDIER = dict(gender=1.0, age_years=28, build="muscular", height_cm=176, ethnicity="european", skin_tone=0.45,
               hair="short02", hair_color="dark_brown", beard="stubble", eye_color="brown", eyebrows="eyebrow002",
               expression="neutral", outfit=["loincloth", "roman_soldier"], outfit_colors={"loincloth": "undyed"},
               pose="stand", dirt=0.25, sweat=0.2)
MOSES = dict(gender=1.0, age_years=80, build="lean", height_cm=174, ethnicity="judean", hair="long01",
             hair_color="white", grey=1.0, beard="long", beard_length=0.24, eye_color="brown", eyebrows="eyebrow003",
             expression="awe", outfit=["robe", "sandals"], outfit_colors={"tunic": "oatmeal", "mantle": "camel"},
             pose="staff", wrinkles=1.0, dirt=0.25, staff=True)
CROWD_MAN = dict(gender=1.0, crowd=True, outfit=["tunic", "mantle"], pose="stand_relaxed")
CROWD_WOMAN = dict(gender=0.0, crowd=True, outfit=["tunic", "veil"], pose="stand_relaxed", hair_strands=False)

PRESETS = dict(JESUS_CROSS=JESUS_CROSS, JESUS_ROBED=JESUS_ROBED, JESUS_RISEN=JESUS_RISEN, MARY_YOUNG=MARY_YOUNG,
               MARY_OLD=MARY_OLD, PRIEST=PRIEST, ELDER=ELDER, CHILD=CHILD, BABY=BABY, SOLDIER=SOLDIER, MOSES=MOSES,
               CROWD_MAN=CROWD_MAN, CROWD_WOMAN=CROWD_WOMAN)


def _crowd_variant(spec, seed):
    """Fill in a seeded random crowd member (CROWD_MAN / CROWD_WOMAN)."""
    r = random.Random(seed * 7919 + 13)
    male = spec.get("gender", 1.0) >= 0.5
    out = {}
    out["age_years"] = r.choice([19, 24, 28, 33, 38, 45, 52, 60, 68]) + r.uniform(-3, 3)
    out["build"] = r.choice(["lean", "average", "average", "heavy", "frail", "muscular"] if male else ["lean", "average", "average", "heavy"])
    out["height_cm"] = (r.gauss(170, 6) if male else r.gauss(157, 5))
    out["ethnicity"] = spec.get("ethnicity") or r.choice(["judean", "judean", "judean", "arab", "judean"])
    out["skin_tone"] = r.uniform(0.35, 0.75)
    age = out["age_years"]
    out["grey"] = max(0.0, min(1.0, (age - 38) / 30.0 + r.uniform(-0.15, 0.15)))
    out["hair_color"] = r.choice(["black", "dark_brown", "dark_brown", "brown"])
    if male:
        out["hair"] = r.choice(["short01", "short02", "short03", "short04"])
        out["beard"] = r.choice(["full", "full", "short", "stubble", "long"] if age > 22 else ["stubble", "short", "none"])
        out["eyebrows"] = r.choice(["eyebrow001", "eyebrow002", "eyebrow003", "eyebrow004", "eyebrow005"])
    else:
        out["hair"] = r.choice(["braid01", "ponytail01", "braid01"])
        out["beard"] = "none"
        out["eyebrows"] = r.choice(["eyebrow008", "eyebrow009", "eyebrow010", "eyebrow011"])
    out["eye_color"] = r.choice(["brown", "dark_brown", "dark_brown", "hazel"])
    out["dirt"] = r.uniform(0.05, 0.35)
    out["wrinkles"] = max(0.0, min(1.0, (age - 25) / 45.0))
    out["face"] = {k: r.uniform(-0.45, 0.45) for k in ["nose/nose-scale-horiz-decr|incr", "nose/nose-hump-decr|incr",
                                                       "head/head-oval", "head/head-square", "chin/chin-width-decr|incr",
                                                       "mouth/mouth-scale-horiz-decr|incr", "eyebrows/eyebrows-trans-down|up",
                                                       "nose/nose-scale-vert-decr|incr", "cheek/l-cheek-bones-decr|incr"]}
    out["face"]["head/head-oval"] = abs(out["face"]["head/head-oval"])
    out["face"]["head/head-square"] = abs(out["face"]["head/head-square"])
    out["expression"] = r.choice(["neutral", "neutral", "sorrow", "neutral"])
    return out


def resolve_spec(preset=None, **spec):
    """Merge DEFAULT_SPEC <- preset <- spec (and crowd randomisation) into one dict."""
    if isinstance(preset, str):
        preset = PRESETS[preset.upper()]
    s = dict(DEFAULT_SPEC)
    if preset:
        s.update(preset)
    if s.get("crowd"):
        s.update(_crowd_variant(dict(s, **spec), spec.get("seed", s.get("seed", 0))))
    s.update(spec)
    eth = ETHNICITY.get(s["ethnicity"], ETHNICITY["judean"])
    if s["hair_color"] is None:
        s["hair_color"] = eth["hair"]
    if s["eye_color"] is None:
        s["eye_color"] = eth["eyes"]
    if s["grey"] is None:
        s["grey"] = max(0.0, min(1.0, (s["age_years"] - 42) / 35.0))
    if s["wrinkles"] is None:
        s["wrinkles"] = max(0.0, min(1.0, (s["age_years"] - 25) / 45.0))
    if s["beard_color"] is None:
        s["beard_color"] = s["hair_color"]
    if s["eyebrows"] is None:
        s["eyebrows"] = "eyebrow001" if s["gender"] >= 0.5 else "eyebrow010"
    return s


def age_to_macro(years):
    """MakeHuman age macro: 0 -> 1 y, 0.1875 -> 11 y, 0.5 -> 25 y, 1 -> 90 y."""
    y = max(1.0, float(years))
    if y < 11:
        return (y - 1) / 10.0 * 0.1875
    if y < 25:
        return 0.1875 + (y - 11) / 14.0 * 0.3125
    return min(1.0, 0.5 + (y - 25) / 65.0 * 0.5)


# ============================================================================================
# Person
# ============================================================================================
class Person:
    """A built human. Attributes: name, rig (armature, parent of everything), body (MPFB basemesh),
    parts {eyes, eyebrows, eyelashes, teeth, tongue, hair, beard}, garments (list, filled by wardrobe),
    props (list), spec (resolved dict), height (m), lm (rest landmarks in rig space)."""

    def __init__(self, name, rig, body, parts, spec):
        self.name = name
        self.rig = rig
        self.body = body
        self.parts = parts
        self.garments = []
        self.props = []
        self.spec = spec
        self.height = 0.0
        self.lm = {}
        self.mats = {}
        self._pose = None           # last _Pose state (static)
        self._expr = {}             # current expression unit weights
        self._jaw = 0.0
        self._ground_offset = 0.0
        self.expr_keys = {}         # unit -> shape key name on body

    # --- transforms -----------------------------------------------------------------------
    @property
    def root(self):
        return self.rig

    def update(self):
        bpy.context.view_layer.update()

    def bone_world(self, name, tail=False):
        """World position of a bone head (or tail) in the CURRENT evaluated pose (call after posing;
        for animated rigs, set the frame first)."""
        pb = self.rig.pose.bones[name]
        return self.rig.matrix_world @ (pb.tail if tail else pb.head)

    def bone_matrix(self, name):
        return self.rig.matrix_world @ self.rig.pose.bones[name].matrix

    def head_pos(self):
        """Centre of the head (between the ears, eye height)."""
        h = self.bone_world("head")
        t = self.bone_world("head", True)
        return h + (t - h) * 0.25

    def eye_pos(self):
        return (self.bone_world("eye.L") + self.bone_world("eye.R")) * 0.5

    def hand_pos(self, side="R"):
        """Palm centre (world) of hand 'L'/'R' (character's left/right)."""
        s = _side(side)
        return (self.bone_world("wrist." + s) + self.bone_world("metacarpal2." + s, True)) * 0.5

    def foot_pos(self, side="R"):
        """Ankle-joint position (world)."""
        return self.bone_world("foot." + _side(side))

    def objects(self):
        out = [self.rig]
        stack = list(self.rig.children)
        while stack:
            o = stack.pop()
            out.append(o)
            stack.extend(o.children)
        return out

    def set_visible(self, visible=True, frame=None):
        for o in self.objects():
            o.hide_render = not visible
            o.hide_viewport = not visible
            if frame is not None:
                o.keyframe_insert("hide_render", frame=frame)
                o.keyframe_insert("hide_viewport", frame=frame)

    def __repr__(self):
        return "<Person %s h=%.2fm>" % (self.name, self.height)


def _side(s):
    s = str(s).upper()
    return "L" if s.startswith("L") else "R"


# ============================================================================================
# Building
# ============================================================================================
def _phenotype(s):
    m, w, p = BUILDS.get(s["build"], BUILDS["average"])
    eth = ETHNICITY.get(s["ethnicity"], ETHNICITY["judean"])
    ca, af, asn = eth["race"]
    ph = {"gender": float(s["gender"]), "age": age_to_macro(s["age_years"]), "muscle": m, "weight": w,
          "proportions": p, "height": 0.5, "cupsize": 0.5, "firmness": 0.5,
          "race": {"caucasian": ca, "african": af, "asian": asn}}
    return ph


def _skin_texture(s):
    eth = ETHNICITY.get(s["ethnicity"], ETHNICITY["judean"])
    a = s["age_years"]
    grp = "young" if a < 32 else ("middleage" if a < 58 else "old")
    g = "male" if s["gender"] >= 0.5 else "female"
    name = "%s_%s_%s" % (grp, eth["skin"], g)
    d = os.path.join(MPFB_DATA, "skins", name)
    pngs = [f for f in os.listdir(d) if f.endswith(".png")]
    return os.path.join(d, pngs[0])


def make_person(name, preset=None, **spec):
    """Build a person. preset: dict or name in PRESETS; spec keys override (see DEFAULT_SPEC).
    Returns Person. Dresses via lib.wardrobe when importable, applies spec['pose'] and expression."""
    t0 = time.time()
    s = resolve_spec(preset, **spec)
    M = _mpfb()
    HS, TS = M["HS"], M["TS"]
    hero = s["lod"] == "hero"
    far = s["lod"] == "far"
    # deselect: MPFB uses operators on the active object
    for o in bpy.context.selected_objects:
        o.select_set(False)
    hi = HS._create_default_human_info_dict()
    hi["phenotype"] = _phenotype(s)
    hi["name"] = name
    hi["rig"] = "default"
    hi["eyes"] = _asset("eyes", "high-poly" if not far else "low-poly")
    if not far:
        if s["eyebrows"] and s["eyebrows"] != "none":
            hi["eyebrows"] = _asset("eyebrows", s["eyebrows"])
        hi["eyelashes"] = _asset("eyelashes", "eyelashes01" if s["gender"] >= 0.5 else "eyelashes02")
        hi["teeth"] = _asset("teeth", "teeth_base")
        hi["tongue"] = _asset("tongue", "tongue01")
    if s["hair"] and s["hair"] != "none":
        hi["hair"] = _asset("hair", s["hair"])
    if far:
        hi["proxy"] = "%s/%s.proxy" % (("male_generic",) * 2 if s["gender"] >= 0.5 else ("female_generic",) * 2)
    hi["skin_material_type"] = "NONE"
    hi["eyes_material_type"] = "PROCEDURAL_EYES"
    ds = HS.get_default_deserialization_settings()
    ds["subdiv_levels"] = 1 if hero else 0
    # Height: measure the macro body first, then rebuild at the scale that hits height_cm
    if s.get("height_cm"):
        probe = HS.create_human(mask_helpers=False, detailed_helpers=True, extra_vertex_groups=True,
                                feet_on_ground=True, scale=0.1, macro_detail_dict=dict(hi["phenotype"]))
        pw = _vgroup_weights(probe, ["body"])["body"] > 0.5
        pc = _coords(probe.data)
        # shape keys hold the macro shape: evaluate the mix
        if probe.data.shape_keys:
            pc = np.zeros(len(probe.data.vertices) * 3, np.float32)
            dg = bpy.context.evaluated_depsgraph_get()
            pe = probe.evaluated_get(dg).to_mesh()
            pe.vertices.foreach_get("co", pc)
            pc = pc.reshape(-1, 3)
            probe.evaluated_get(dg).to_mesh_clear()
        h0 = float(pc[pw, 2].max() - pc[pw, 2].min()) if pw.any() else probe.dimensions.z
        me = probe.data
        bpy.data.objects.remove(probe)
        bpy.data.meshes.remove(me)
        ds["scale"] = 0.1 * (s["height_cm"] / 100.0) / max(0.2, h0)
    T = [("start", time.time())]
    body = HS.deserialize_from_dict(hi, ds)
    T.append(("mpfb", time.time()))
    rig = body.parent
    rig.name = name
    body.name = name + ".body"
    # bake macro shape keys so that Basis == this character (expression keys come on top)
    if s.get("face"):
        _apply_face_targets(body, s["face"])
    TS.bake_targets(body)
    parts = {}
    for ch in rig.children:
        if ch == body:
            continue
        n = ch.name.split(".", 1)[-1]
        for key, tag in (("eyes", "poly"), ("eyebrows", "eyebrow"), ("eyelashes", "eyelashes"), ("teeth", "teeth"),
                         ("tongue", "tongue"), ("proxy", "_generic")):
            if tag in n:
                parts[key] = ch
                break
        else:
            if s["hair"] and s["hair"] in n:
                parts["hair"] = ch
                ch.name = "%s.hair_%s" % (name, s["hair"])   # wardrobe fits head garments over '*hair*' meshes
    for o in [rig, body] + list(parts.values()):
        o.select_set(False)
    rig.data.pose_position = "POSE"
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
    body.add_rest_position_attribute = True
    p = Person(name, rig, body, parts, s)
    _landmarks(p)
    p.height = p.lm["head_top"]
    T.append(("landmarks", time.time()))
    _compute_masks(p)
    T.append(("masks", time.time()))
    _materials(p)
    if not far and "teeth" in parts:
        _mouth_occluder(p)
    T.append(("materials", time.time()))
    if s["beard"] in BEARDS and BEARDS[s["beard"]]:
        if hero:
            make_beard(p)
            T.append(("beard", time.time()))
        elif s["lod"] == "mid":
            make_beard(p, density=0.35)
    covered = any(g in (s.get("outfit") or []) for g in ("veil", "headcloth", "turban", "hood", "roman_soldier"))
    if hero and s.get("hair_strands", (not covered) and s["hair"] in ("long01", "bob01", "bob02", "ponytail01", "braid01")) and "hair" in parts:
        make_hair_strands(p)
        T.append(("strands", time.time()))
    elif hero and s.get("hair_strands", not covered) and s["hair"] in SHORT_HAIR and "hair" in parts:
        make_short_hair(p)
        T.append(("strands", time.time()))
    if s.get("staff"):
        make_staff(p)
    p.build_time = time.time() - t0
    # wardrobe
    if s.get("outfit"):
        dress(p, s["outfit"], s.get("outfit_colors"), s.get("outfit_seed", 0) or s.get("seed", 0),
              "hero" if hero else "crowd", opts=s.get("outfit_opts"))
    if s.get("pose"):
        try:
            pose(p, s["pose"])
        except Exception as e:  # never fail a build on a pose
            _log("pose failed", s["pose"], e)
    if s.get("expression") and s["expression"] != "neutral" and not far:
        expression(p, s["expression"])
    p.build_time = time.time() - t0
    T.append(("dress+pose", time.time()))
    p.timings = {T[i][0]: round(T[i][1] - T[i - 1][1], 3) for i in range(1, len(T))}
    _log("built %s (%s) in %.2fs %s" % (name, preset if isinstance(preset, str) else s.get("ethnicity"), p.build_time, p.timings))
    return p


def dress(person, outfit, colors=None, seed=0, detail="hero", opts=None):
    """Call lib.wardrobe.dress if available (whole outfit list in one call). opts: per-outfit option dicts,
    e.g. {"tunic": {"sleeves": "long"}}. Returns list of garments (also appended to person.garments)."""
    try:
        from . import wardrobe
    except ImportError as e:
        _log("WARNING: lib.wardrobe not importable (%s) - %s stays undressed" % (e, person.name))
        return []
    items = [outfit] if isinstance(outfit, str) else list(outfit)
    g = []
    opts = dict(opts or {})
    try:
        # one call with the whole list: wardrobe resolves duplicates (robe+mantle ...) and builds inner -> outer
        g = list(wardrobe.dress(person, items if len(items) > 1 else items[0], colors=colors, seed=seed, detail=detail,
                                **(opts if len(items) > 1 else opts.get(items[0], {}))) or [])
    except Exception as e:
        _log("WARNING: wardrobe.dress(%s, %r) failed (%s) - retrying item by item" % (person.name, items, e))
        for it in items:
            if any(str(o.get("outfit", "")) == it for o in getattr(person, "garments", [])):
                continue
            try:
                g += list(wardrobe.dress(person, it, colors=colors, seed=seed, detail=detail, **opts.get(it, {})) or [])
            except Exception as e2:
                _log("WARNING: wardrobe.dress(%s, %r) failed: %s" % (person.name, it, e2))
    for o in g:
        if o not in person.garments:
            person.garments.append(o)
    _protect_beard_region(person)
    return g


def _protect_beard_region(p):
    """Wardrobe hides body skin under garments with a MASK modifier (vertex group 'wardrobe_hide').
    Hair curves attached to the body (beard) need their root faces to survive the mask, so the
    beard region (dilated) is removed from that group."""
    g = p.body.vertex_groups.get("wardrobe_hide")
    if g is None or not hasattr(p, "masks"):
        return
    m = p.masks["beard"] > 0.0
    hs = p.parts.get("hair_strands")
    if hs is not None and hs.type == "CURVES" and getattr(hs.data, "surface", None) == p.body:
        m = m | (p.masks["hair"] > 0.0)       # short hair strands are rooted on the scalp too
    keep = np.nonzero(m)[0]
    if len(keep) == 0:
        return
    # dilate by one ring so faces touching the region keep all their vertices
    me = p.body.data
    ks = set(int(i) for i in keep)
    extra = set()
    for pl in me.polygons:
        vs = pl.vertices
        if any(v in ks for v in vs):
            extra.update(vs)
    g.remove(list(ks | extra))


def _apply_face_targets(body, face):
    """face: {'category/target-decr|incr': value(-1..1) or 'category/target': value(0..1)}."""
    TS = _mpfb()["TS"]
    for key, val in face.items():
        if abs(val) < 0.01:
            continue
        cat, tgt = key.split("/", 1)
        if "|" in tgt:
            base, alts = tgt.rsplit("-", 1)
            neg, pos = alts.split("|")
            name = "%s-%s" % (base, pos if val > 0 else neg)
            val = abs(val)
        else:
            name = tgt
        path = os.path.join(MPFB_SYS, "targets", cat, name + ".target.gz")
        if not os.path.exists(path):
            _log("face target missing", path)
            continue
        TS.load_target(body, path, weight=float(val), name="face_" + name)


# ============================================================================================
# Landmarks + masks
# ============================================================================================
def _vgroup_weights(obj, names):
    idx = {obj.vertex_groups[n].index: n for n in names if n in obj.vertex_groups}
    out = {n: np.zeros(len(obj.data.vertices), np.float32) for n in names}
    if not idx:
        return out
    for v in obj.data.vertices:
        for g in v.groups:
            n = idx.get(g.group)
            if n:
                out[n][v.index] = g.weight
    return out


def _coords(me):
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def _landmarks(p):
    """Rest landmarks in rig space (rig built at identity)."""
    b = p.rig.data.bones
    lm = p.lm
    co = _coords(p.body.data)
    p._co = co
    w = _vgroup_weights(p.body, ["body", "lips", "ears", "fingernails", "scalp"])
    p._w = w
    bodym = w["body"] > 0.5
    lm["eyeL"] = Vector(b["eye.L"].head_local)
    lm["eyeR"] = Vector(b["eye.R"].head_local)
    lm["eyes"] = (lm["eyeL"] + lm["eyeR"]) / 2
    lips = co[(w["lips"] > 0.5) & bodym]
    lm["mouth"] = Vector(lips.mean(0))
    lm["mouth_w"] = float(np.abs(lips[:, 0]).max())
    lm["mouth_top"] = float(lips[:, 2].max())
    lm["mouth_bot"] = float(lips[:, 2].min())
    ears = co[(w["ears"] > 0.5) & bodym & (co[:, 0] > 0)]
    lm["ear"] = Vector(ears.mean(0))
    lm["ear_x"] = float(ears[:, 0].min())        # inner (front-ish) edge
    lm["ear_front"] = float(ears[:, 1].min())    # most forward y of the ear
    lm["ear_top"] = float(ears[:, 2].max())
    lm["ear_bot"] = float(ears[:, 2].min())
    lm["head_top"] = float(co[bodym, 2].max())
    lm["height"] = lm["head_top"]
    # midline front profile: most forward y per 2 mm z-slice
    E = lm["eyes"]
    sel = bodym & (np.abs(co[:, 0]) < 0.006) & (co[:, 2] > E.z - 0.22) & (co[:, 2] < E.z + 0.03) & (co[:, 1] < E.y + 0.08)
    pts = co[sel]
    prof = []
    for zz in np.arange(E.z - 0.22, E.z + 0.03, 0.002):
        q = pts[np.abs(pts[:, 2] - zz) < 0.003]
        if len(q):
            prof.append((zz, q[:, 1].min()))
    prof = np.array(prof)
    mb, mt = lm["mouth_bot"], lm["mouth_top"]
    seg = prof[(prof[:, 0] > mb - 0.05) & (prof[:, 0] < mb - 0.012)]
    ci = int(np.argmin(seg[:, 1])) if len(seg) else 0
    chin = seg[ci] if len(seg) else (mb - 0.025, E.y - 0.02)
    lm["chin"] = Vector((0.0, float(chin[1]), float(chin[0])))
    below = prof[(prof[:, 0] < chin[0]) & (prof[:, 1] < chin[1] + 0.02)]
    lm["chin_bot"] = float(below[:, 0].min()) if len(below) else float(chin[0]) - 0.02
    nose = co[bodym & (np.abs(co[:, 0]) < 0.01) & (co[:, 2] > mt) & (co[:, 2] < E.z)]
    lm["nose_tip"] = Vector(nose[np.argmin(nose[:, 1])]) if len(nose) else E + Vector((0, -0.05, -0.04))
    seg2 = prof[(prof[:, 0] > mt) & (prof[:, 0] < lm["nose_tip"].z)]
    lm["subnasale"] = float(seg2[np.argmax(seg2[:, 1])][0]) if len(seg2) else (mt + lm["nose_tip"].z) / 2
    for s in "LR":
        lm["palm" + s] = (Vector(b["wrist." + s].head_local) + Vector(b["metacarpal2." + s].tail_local)) / 2
        lm["foot" + s] = (Vector(b["foot." + s].head_local) * 0.45 + Vector(b["toe3-1." + s].head_local) * 0.55)
    lm["io"] = (lm["eyeL"] - lm["eyeR"]).length   # inter-ocular distance, used as a face scale


def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _compute_masks(p):
    """Per-vertex masks stored as colour attributes on the body (point domain, interpolated):
    cmask_a = (beard, crown/brow blood zone, wounds, dirt), cmask_b = (redness, sweat, lips, scalp)."""
    co, w, lm = p._co, p._w, p.lm
    n = len(co)
    x, y, z = co[:, 0], co[:, 1], co[:, 2]
    lat = np.abs(x)
    f = -y                                   # forward
    sc = lm["io"] / 0.062                    # face scale (1 for an adult)
    E = lm["eyes"]
    mz, mw = lm["mouth"].z, lm["mouth_w"]
    chin = lm["chin"]
    earx, earf, earz = lm["ear_x"], -lm["ear_front"], lm["ear"].z
    head = (z > lm["chin_bot"] - 0.08 * sc) & (w["body"] > 0.5)
    # ---------------- beard -----------------
    sub, menton = lm["subnasale"], lm["chin_bot"]
    ear_bot, ear_top = lm["ear_bot"], lm["ear_top"]
    head = (z > menton - 0.09 * sc) & (w["body"] > 0.5)
    Bx, Bz = mw + 0.006 * sc, sub - 0.001 * sc
    Ax, Az = earx - 0.006 * sc, ear_bot + 0.006 * sc
    t = np.clip((lat - Bx) / max(1e-4, Ax - Bx), 0, 1)
    upper = np.where(lat < Bx, sub - 0.0015 * sc, Bz + (Az - Bz) * t ** 0.8)
    sbw = _smooth(lat, earx - 0.032 * sc, earx - 0.016 * sc) * (1 - _smooth(f, earf + 0.022 * sc, earf + 0.034 * sc))
    upper = np.maximum(upper, Az + (ear_top + 0.006 * sc - Az) * sbw)
    m_up = 1 - _smooth(z, upper - 0.005 * sc, upper + 0.004 * sc)
    tl = np.clip(lat / earx, 0, 1) ** 1.3
    lower = (menton - 0.028 * sc) + ((ear_bot - 0.03 * sc) - (menton - 0.028 * sc)) * tl
    m_lo = _smooth(z, lower - 0.004 * sc, lower + 0.006 * sc)
    m_back = _smooth(f, earf - 0.008 * sc, earf + 0.002 * sc)
    lips_d = _dist_to(co, co[(w["lips"] > 0.4) & (w["body"] > 0.5)], mask=head)
    m_lips = _smooth(lips_d, 0.0012 * sc, 0.0035 * sc)
    beard = m_up * m_lo * m_back * m_lips * head
    # ---------------- crown / brow blood zone (1 at the crown line .. 0 at the brows) -----
    crown_z = E.z + 0.055 * sc
    brow_z = E.z + 0.012 * sc
    zone = np.clip((z - brow_z) / (crown_z - brow_z), 0, 1.0) * (z < crown_z + 0.012 * sc)
    zone *= _smooth(f, earf - 0.02 * sc, earf + 0.02 * sc) * head
    # ---------------- wounds (hands, feet, side) ----------------
    wounds = np.zeros(n, np.float32)
    for s in "LR":
        d = np.linalg.norm(co - np.array(lm["palm" + s]), axis=1)
        wounds = np.maximum(wounds, 1 - _smooth(d, 0.009 * sc, 0.016 * sc))
        d = np.linalg.norm(co - np.array(lm["foot" + s]), axis=1)
        wounds = np.maximum(wounds, 1 - _smooth(d, 0.012 * sc, 0.022 * sc))
    hsc = lm["height"] / 1.76
    side_pt = np.array([-0.125 * hsc, -0.05 * hsc, 1.13 * hsc])
    sp = co[np.argmin(np.linalg.norm(co - side_pt, axis=1) + (w["body"] < 0.5) * 9)]
    d = np.linalg.norm(co - sp, axis=1)
    wounds = np.maximum(wounds, (1 - _smooth(d, 0.008, 0.02)) * 0.85)
    # ---------------- dirt ----------------
    zr = z / lm["height"]
    dirt = 0.18 + 0.82 * (1 - _smooth(zr, 0.05, 0.35))       # feet / shins
    knees = np.exp(-((zr - 0.28) / 0.05) ** 2) * _smooth(f, 0.0, 0.06)
    dirt = np.maximum(dirt, 0.75 * knees)
    for s in "LR":
        d = np.linalg.norm(co - np.array(lm["palm" + s]), axis=1)
        dirt = np.maximum(dirt, 0.65 * (1 - _smooth(d, 0.05, 0.25)))
    dirt = np.maximum(dirt, 0.22 * head)
    # ---------------- redness ----------------
    red = np.zeros(n, np.float32)
    nt = lm["nose_tip"]
    red = np.maximum(red, 1 - _smooth(np.linalg.norm(co - np.array(nt), axis=1), 0.006 * sc, 0.022 * sc))
    for sx in (-1, 1):
        cheek = np.array([sx * 0.038 * sc, E.y - 0.012 * sc, E.z - 0.038 * sc])
        red = np.maximum(red, 0.8 * (1 - _smooth(np.linalg.norm(co - cheek, axis=1), 0.005 * sc, 0.03 * sc)))
    red = np.maximum(red, 0.8 * (w["ears"] > 0.5))
    eyez = np.exp(-(((z - E.z) / (0.012 * sc)) ** 2)) * np.exp(-(((lat - 0.032 * sc) / (0.022 * sc)) ** 2)) * head
    red = np.maximum(red, 0.25 * eyez)
    red = np.maximum(red, 0.5 * np.clip(w["fingernails"] * 0 + (1 - _smooth(zr, 0.0, 0.06)), 0, 1))
    # ---------------- sweat ----------------
    sweat = 0.25 + 0.75 * np.clip(head * (z > E.z + 0.008 * sc) * 1.0, 0, 1)
    sweat = np.maximum(sweat, 0.8 * head * (z > lm["mouth_top"]) * (z < lm["subnasale"] + 0.004 * sc) * (lat < mw + 0.01 * sc))
    chest = np.exp(-(((zr - 0.72) / 0.08) ** 2)) * _smooth(f, 0.02, 0.1)
    sweat = np.maximum(sweat, 0.7 * chest)
    lipsm = (1 - _smooth(lips_d, 0.0, 0.002 * sc)) * (w["lips"] > 0.2)
    # ---------------- hair-bearing scalp (hairline: forehead, temples, above the ears, nape) ---------
    front_line = E.z + 0.076 * sc - 0.018 * sc * np.clip((lat - 0.02 * sc) / (0.045 * sc), 0, 1)
    side_line = lm["ear_top"] - 0.002 * sc
    back_line = lm["ear_bot"] - 0.02 * sc
    wf = _smooth(f, earf + 0.0, earf + 0.03 * sc)                       # 1 = in front of the ear (temples, forehead)
    wb = 1 - _smooth(f, earf - 0.05 * sc, earf - 0.012 * sc)            # 1 = well behind the ear (nape)
    line = wf * front_line + (1 - wf) * side_line
    line = wb * back_line + (1 - wb) * line
    hairm = _smooth(z, line - 0.003 * sc, line + 0.012 * sc) * (z > menton) * (w["body"] > 0.5) * (1 - np.clip(w["ears"] * 3, 0, 1))
    scalp = hairm            # (MPFB's own 'scalp' group stops short of the hairline; the hair mask is used instead)
    p.masks = dict(beard=beard, zone=zone, wounds=wounds, dirt=dirt, red=red, sweat=sweat, lips=lipsm, scalp=scalp,
                   hair=hairm)
    me = p.body.data
    for nm, chans in (("cmask_a", (beard, zone, wounds, dirt)), ("cmask_b", (red, sweat, lipsm, scalp))):
        if nm in me.color_attributes:
            me.color_attributes.remove(me.color_attributes[nm])
        ca = me.color_attributes.new(nm, "FLOAT_COLOR", "POINT")
        arr = np.stack([np.clip(c, 0, 1).astype(np.float32) for c in chans], 1).ravel()
        ca.data.foreach_set("color", arr)


def _dist_to(co, pts, mask=None):
    out = np.full(len(co), 1e3, np.float32)
    if len(pts) == 0:
        return out
    kd = KDTree(len(pts))
    for i, q in enumerate(pts):
        kd.insert(q, i)
    kd.balance()
    idx = np.nonzero(mask)[0] if mask is not None else range(len(co))
    for i in idx:
        out[i] = kd.find(co[i])[2]
    return out


# ============================================================================================
# Materials
# ============================================================================================
class _NT:
    """Tiny node-tree builder."""

    def __init__(self, mat):
        self.m = mat
        self.nt = mat.node_tree
        self.x = 0

    def n(self, kind, **inputs):
        node = self.nt.nodes.new(kind)
        node.location = (self.x, 0)
        self.x += 180
        for k, v in inputs.items():
            if k.startswith("_"):
                setattr(node, k[1:], v)
            else:
                self.set(node.inputs[k], v)
        return node

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
        elif isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], sock)
        else:
            if hasattr(sock, "default_value"):
                dv = sock.default_value
                if hasattr(dv, "__len__") and not isinstance(v, (tuple, list)):
                    v = [v] * len(dv)
                elif hasattr(dv, "__len__") and len(v) < len(dv):
                    v = tuple(v) + (1.0,)
                sock.default_value = v

    def math(self, op, a, b=0.0, clamp=False):
        n = self.n("ShaderNodeMath", _operation=op, _use_clamp=clamp)
        self.set(n.inputs[0], a)
        self.set(n.inputs[1], b)
        return n.outputs[0]

    def mix(self, a, b, fac, blend="MIX"):
        n = self.n("ShaderNodeMix", _data_type="RGBA", _blend_type=blend)
        self.set(n.inputs["Factor"], fac)
        self.set(n.inputs[6], a)
        self.set(n.inputs[7], b)
        return n.outputs[2]

    def vmath(self, op, a, b=(0, 0, 0)):
        n = self.n("ShaderNodeVectorMath", _operation=op)
        self.set(n.inputs[0], a)
        self.set(n.inputs[1], b)
        return n.outputs[0] if op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs[1]

    def sep(self, col):
        n = self.n("ShaderNodeSeparateColor")
        self.set(n.inputs[0], col)
        return n.outputs

    def link(self, a, b):
        self.nt.links.new(a, b)


def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    return m, _NT(m)


def _img(path, noncolor=False):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def skin_material(p, name=None):
    """Lifelike skin: MPFB diffuse map tinted to the ethnicity, regional redness, beard shadow,
    dirt / blood / sweat / scars driven by the cmask_* attributes and person.spec. Re-callable."""
    s = p.spec
    eth = ETHNICITY.get(s["ethnicity"], ETHNICITY["judean"])
    m, T = _new_mat(name or (p.name + ".skin"))
    out = T.n("ShaderNodeOutputMaterial")
    tc = T.n("ShaderNodeTexCoord")
    tex = T.n("ShaderNodeTexImage")
    tex.image = _img(_skin_texture(s))
    T.link(tc.outputs["UV"], tex.inputs["Vector"])
    tone = s.get("skin_tone")
    val = eth["val"]
    tint_amt = eth["tint_amt"]
    if tone is not None:   # 0 light .. 1 dark (around the ethnicity's default at 0.5)
        val *= 1.25 - 0.5 * tone
        tint_amt = min(1.0, tint_amt * (0.7 + 0.6 * tone))
    hs = T.n("ShaderNodeHueSaturation", Hue=eth["hue"], Saturation=eth["sat"], Value=val)
    T.link(tex.outputs["Color"], hs.inputs["Color"])
    col = T.mix(hs.outputs[0], eth["tint"], tint_amt, "MULTIPLY")
    rest = T.n("ShaderNodeAttribute", _attribute_name="rest_position", _attribute_type="GEOMETRY").outputs["Vector"]
    ma = T.sep(T.n("ShaderNodeAttribute", _attribute_name="cmask_a").outputs["Color"])
    mb = T.sep(T.n("ShaderNodeAttribute", _attribute_name="cmask_b").outputs["Color"])
    beard_m, zone_m, wound_m, dirt_m = ma[0], ma[1], ma[2], ma[3] if len(ma) > 3 else None
    ca = T.n("ShaderNodeAttribute", _attribute_name="cmask_a")
    dirt_m = ca.outputs["Alpha"]
    red_m, sweat_m, lips_m = mb[0], mb[1], mb[2]
    # --- large & small variation noise (rest space so it sticks to the skin)
    n_big = T.n("ShaderNodeTexNoise", Scale=9.0, Detail=4.0, Roughness=0.55)
    T.link(rest, n_big.inputs["Vector"])
    n_mid = T.n("ShaderNodeTexNoise", Scale=70.0, Detail=6.0, Roughness=0.6)
    T.link(rest, n_mid.inputs["Vector"])
    # mottling: subtle value variation
    mot = T.n("ShaderNodeMapRange", **{"From Min": 0.35, "From Max": 0.65, "To Min": 0.93, "To Max": 1.05})
    T.link(n_big.outputs["Fac"], mot.inputs["Value"])
    col = T.mix(col, mot.outputs[0], 1.0, "MULTIPLY")
    # --- redness (nose, cheeks, ears, around eyes)
    redf = T.math("MULTIPLY", red_m, float(s.get("redness", 0.35)))
    col = T.mix(col, T.mix(col, (0.86, 0.52, 0.44), 1.0, "MULTIPLY"), redf)
    # --- lips a touch darker / redder
    col = T.mix(col, T.mix(col, (0.86, 0.64, 0.58), 1.0, "MULTIPLY"), T.math("MULTIPLY", lips_m, 0.45))
    # --- beard shadow / stubble dots (shaved follicles), always under real beards too
    beard_style = s.get("beard", "none")
    beard_amt = {"none": 0.10 if s["gender"] >= 0.5 and s["age_years"] > 16 else 0.0, "stubble": 0.85}.get(beard_style, 1.0)
    if beard_amt > 0:
        vor = T.n("ShaderNodeTexVoronoi", Scale=1300.0, Randomness=1.0)
        T.link(rest, vor.inputs["Vector"])
        dots = T.n("ShaderNodeMapRange", **{"From Min": 0.12, "From Max": 0.42, "To Min": 1.0, "To Max": 0.25})
        T.link(vor.outputs["Distance"], dots.inputs["Value"])
        shade = T.n("ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.55, "To Max": 1.0})
        T.link(n_mid.outputs["Fac"], shade.inputs["Value"])
        bf = T.math("MULTIPLY", T.math("MULTIPLY", beard_m, dots.outputs[0]), shade.outputs[0])
        bf = T.math("MULTIPLY", bf, beard_amt * (0.85 if beard_style != "none" else 0.6), True)
        hc = Vector(HAIR_COLORS.get(s["beard_color"], HAIR_COLORS["dark_brown"]))
        g = float(s.get("grey", 0))
        hc = hc.lerp(Vector(HAIR_COLORS["grey"]), g * 0.8)
        col = T.mix(col, tuple(hc * 1.6), bf)
        if beard_style in ("short", "full", "long"):
            # dense beard base: the skin under a real beard reads as hair colour, not skin between strands
            bsh = T.n("ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.75, "To Max": 1.0})
            T.link(n_mid.outputs["Fac"], bsh.inputs["Value"])
            bb = T.math("MULTIPLY", T.math("POWER", beard_m, 0.55), bsh.outputs[0])
            col = T.mix(col, tuple(hc * 0.9), T.math("MULTIPLY", bb, 0.94, True))
    # --- hair-coloured scalp under the hair shell / strands (short hair no longer reads as a cap on skin)
    if s.get("hair") and s["hair"] != "none":
        scalp_m = T.n("ShaderNodeAttribute", _attribute_name="cmask_b").outputs["Alpha"]
        hcs = Vector(HAIR_COLORS.get(s["hair_color"], HAIR_COLORS["dark_brown"])) if isinstance(s["hair_color"], str) \
            else Vector(s["hair_color"][:3])
        hcs = hcs.lerp(Vector(HAIR_COLORS["grey"] if s.get("grey", 0) < 0.75 else HAIR_COLORS["white"]), float(s.get("grey", 0)) * 0.85)
        sbr = T.n("ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.55, "To Max": 1.0})
        T.link(n_mid.outputs["Fac"], sbr.inputs["Value"])
        sf = T.math("MULTIPLY", T.math("POWER", scalp_m, 0.7), sbr.outputs[0])
        col = T.mix(col, tuple(hcs * 1.15), T.math("MULTIPLY", sf, 0.92, True))
    # --- dirt / dust
    dirt = float(s.get("dirt", 0))
    dirtf = None
    if dirt > 0:
        dn = T.n("ShaderNodeMapRange", **{"From Min": 0.38, "From Max": 0.68, "To Min": 0.0, "To Max": 1.0})
        T.link(n_big.outputs["Fac"], dn.inputs["Value"])
        dn2 = T.n("ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.75, "To Min": 0.3, "To Max": 1.0})
        T.link(n_mid.outputs["Fac"], dn2.inputs["Value"])
        dirtf = T.math("MULTIPLY", T.math("MULTIPLY", dirt_m, dn.outputs[0]), dn2.outputs[0])
        dirtf = T.math("MULTIPLY", dirtf, min(1.0, dirt * 1.1), True)
        col = T.mix(col, T.mix(col, (0.62, 0.52, 0.40), 1.0, "MULTIPLY"), dirtf)
    # --- scars (risen Christ): healed wound marks in hands / feet / side
    scars = float(s.get("scars", 0))
    scarf = None
    if scars > 0:
        sc_r = T.n("ShaderNodeMapRange", **{"From Min": 0.45, "From Max": 0.9, "To Min": 0.0, "To Max": 1.0})
        T.link(wound_m, sc_r.inputs["Value"])
        scarf = T.math("MULTIPLY", sc_r.outputs[0], scars, True)
        col = T.mix(col, T.mix(col, (0.72, 0.42, 0.40), 1.0, "MULTIPLY"), T.math("MULTIPLY", scarf, 0.85))
    # --- blood (crown drips, thorn scratches, wounds)
    blood = float(s.get("blood", 0))
    bloodf = None
    if blood > 0:
        # drips: 1D voronoi across the forehead, random length per drip
        sx = T.n("ShaderNodeSeparateXYZ")
        T.link(rest, sx.inputs[0])
        v1 = T.n("ShaderNodeTexVoronoi", _voronoi_dimensions="1D", Scale=75.0, Randomness=0.9)
        T.link(T.math("ADD", sx.outputs[0], T.math("MULTIPLY", n_mid.outputs["Fac"], 0.004)), v1.inputs["W"])
        rnd = T.sep(v1.outputs["Color"])
        # drip extends from the crown (zone=1) down to 1-len
        length = T.math("MULTIPLY", T.math("POWER", rnd[0], 1.3), 1.25 * min(1.0, blood * 1.3))
        reach = T.math("GREATER_THAN", T.math("SUBTRACT", zone_m, T.math("SUBTRACT", 1.0, length)), 0.0)
        width = T.math("MULTIPLY", T.math("ADD", T.math("SUBTRACT", zone_m, T.math("SUBTRACT", 1.0, length)), 0.25), 0.2)
        line = T.math("LESS_THAN", v1.outputs["Distance"], width)
        has = T.math("GREATER_THAN", rnd[1], 0.45)
        drip = T.math("MULTIPLY", T.math("MULTIPLY", T.math("MULTIPLY", reach, line), has), T.math("GREATER_THAN", zone_m, 0.02))
        # punctures along the crown line
        v3 = T.n("ShaderNodeTexVoronoi", Scale=140.0, Randomness=1.0)
        T.link(rest, v3.inputs["Vector"])
        pun = T.math("MULTIPLY", T.math("LESS_THAN", v3.outputs["Distance"], 0.13), T.math("GREATER_THAN", zone_m, 0.86))
        pun = T.math("MULTIPLY", pun, T.math("GREATER_THAN", T.sep(v3.outputs["Color"])[0], 0.35))
        crown = T.math("MAXIMUM", drip, pun)
        # wounds: centre + ragged edge
        wr = T.n("ShaderNodeMapRange", **{"From Min": 0.55, "From Max": 0.8, "To Min": 0.0, "To Max": 1.0})
        T.link(T.math("ADD", wound_m, T.math("MULTIPLY", T.math("SUBTRACT", n_mid.outputs["Fac"], 0.5), 0.5)), wr.inputs["Value"])
        bloodf = T.math("MAXIMUM", T.math("MULTIPLY", crown, min(1.0, blood * 1.6), True), T.math("MULTIPLY", wr.outputs[0], min(1.0, blood * 1.2), True))
        dried = T.n("ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.7, "To Min": 0.0, "To Max": 1.0})
        T.link(n_mid.outputs["Fac"], dried.inputs["Value"])
        bcol = T.mix((0.20, 0.012, 0.010), (0.085, 0.012, 0.008), dried.outputs[0])
        col = T.mix(col, bcol, bloodf)
    # --- roughness
    rough = T.n("ShaderNodeMapRange", **{"From Min": 0.2, "From Max": 0.8, "To Min": 0.40, "To Max": 0.58})
    T.link(n_mid.outputs["Fac"], rough.inputs["Value"])
    r = T.math("SUBTRACT", rough.outputs[0], T.math("MULTIPLY", lips_m, 0.06))
    if dirtf is not None:
        r = T.math("ADD", r, T.math("MULTIPLY", dirtf, 0.25))
    sweat = float(s.get("sweat", 0))
    coat = None
    if sweat > 0:
        drops = T.n("ShaderNodeTexVoronoi", Scale=260.0, Randomness=1.0)
        T.link(rest, drops.inputs["Vector"])
        dr = T.n("ShaderNodeMapRange", **{"From Min": 0.05, "From Max": 0.3, "To Min": 1.0, "To Max": 0.25})
        T.link(drops.outputs["Distance"], dr.inputs["Value"])
        swf = T.math("MULTIPLY", T.math("MULTIPLY", sweat_m, dr.outputs[0]), min(1.0, sweat * 1.2), True)
        r = T.math("SUBTRACT", r, T.math("MULTIPLY", swf, 0.18))
        coat = T.math("MULTIPLY", swf, 0.45)
    if bloodf is not None:
        r = T.mix(r, 0.3, bloodf)
    # --- normal: texture-derived micro relief + pores + fine wrinkles
    bw = T.n("ShaderNodeRGBToBW")
    T.link(tex.outputs["Color"], bw.inputs[0])
    bump1 = T.n("ShaderNodeBump", Strength=0.12 + 0.25 * float(s.get("wrinkles", 0.3)), Distance=0.002)
    T.link(bw.outputs[0], bump1.inputs["Height"])
    pores = T.n("ShaderNodeTexVoronoi", Scale=2100.0, Randomness=1.0, _feature="F1")
    T.link(rest, pores.inputs["Vector"])
    bump2 = T.n("ShaderNodeBump", Strength=0.11, Distance=0.0004)
    T.link(pores.outputs["Distance"], bump2.inputs["Height"])
    T.link(bump1.outputs["Normal"], bump2.inputs["Normal"])
    nfine = T.n("ShaderNodeTexNoise", Scale=420.0, Detail=3.0)
    T.link(rest, nfine.inputs["Vector"])
    bump3 = T.n("ShaderNodeBump", Strength=0.08, Distance=0.0006)
    T.link(nfine.outputs["Fac"], bump3.inputs["Height"])
    T.link(bump2.outputs["Normal"], bump3.inputs["Normal"])
    # --- BSDF
    b = T.n("ShaderNodeBsdfPrincipled")
    T.set(b.inputs["Base Color"], col)
    T.set(b.inputs["Roughness"], r)
    T.set(b.inputs["Specular IOR Level"], 0.42)
    b.inputs["IOR"].default_value = 1.4
    b.inputs["Subsurface Weight"].default_value = 0.4
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.16)
    b.inputs["Subsurface Scale"].default_value = 0.007 * (p.lm.get("height", 1.75) / 1.75)
    b.inputs["Subsurface Anisotropy"].default_value = 0.2
    b.inputs["Sheen Weight"].default_value = 0.08
    b.inputs["Sheen Roughness"].default_value = 0.35
    if coat is not None:
        T.set(b.inputs["Coat Weight"], coat)
        b.inputs["Coat Roughness"].default_value = 0.22
    T.link(bump3.outputs["Normal"], b.inputs["Normal"])
    T.link(b.outputs[0], out.inputs["Surface"])
    return m


def _set_group_input(mat, name, value):
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeGroup" and name in n.inputs:
            n.inputs[name].default_value = value if not isinstance(value, tuple) or len(value) == 4 else (*value, 1.0)


def hair_color_rgb(name, grey=0.0):
    c = Vector(HAIR_COLORS.get(name, HAIR_COLORS["dark_brown"]) if isinstance(name, str) else name)
    return c.lerp(Vector(HAIR_COLORS["grey"] if grey < 0.85 else HAIR_COLORS["white"]), min(1.0, grey * 0.9))


def card_hair_material(p, obj, color, grey=0.0, name=None, alpha_gain=1.0, kind="hair"):
    """Replace an MPFB card material (hair, brows, lashes) with a dark, physically plausible one.
    Keeps the card texture as alpha and as luminance variation."""
    old = obj.data.materials[0] if obj.data.materials else None
    img = None
    if old and old.node_tree:
        for nd in old.node_tree.nodes:
            if nd.bl_idname == "ShaderNodeTexImage" and nd.image and "diffuse" in nd.name.lower():
                img = nd.image
        if img is None:
            for nd in old.node_tree.nodes:
                if nd.bl_idname == "ShaderNodeTexImage" and nd.image:
                    img = nd.image
    m, T = _new_mat(name or (obj.name + ".mat"))
    out = T.n("ShaderNodeOutputMaterial")
    tex = T.n("ShaderNodeTexImage")
    tex.image = img
    base = Vector(color)
    lum = T.n("ShaderNodeRGBToBW")
    T.link(tex.outputs["Color"], lum.inputs[0])
    # strand-to-strand variation from the texture luminance
    var = T.n("ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 1.0, "To Min": 0.55, "To Max": 1.6})
    T.link(lum.outputs[0], var.inputs["Value"])
    col = T.mix(tuple(base), var.outputs[0], 1.0, "MULTIPLY")
    if grey > 0.02 and kind == "hair":
        gcol = Vector(HAIR_COLORS["white"] if grey > 0.75 else HAIR_COLORS["grey"])
        col = T.mix(col, T.mix(tuple(gcol), var.outputs[0], 1.0, "MULTIPLY"), min(1.0, grey * 0.9))
    b = T.n("ShaderNodeBsdfPrincipled")
    T.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.42 if kind == "hair" else 0.55
    b.inputs["Specular IOR Level"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.0
    a = T.math("POWER", tex.outputs["Alpha"], 1.0 / max(0.2, alpha_gain), True)
    T.set(b.inputs["Alpha"], a)
    T.link(b.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "DITHERED"
    m.use_backface_culling = False
    try:
        m.blend_method = "HASHED"
    except Exception:
        pass
    obj.data.materials.clear()
    obj.data.materials.append(m)
    return m


EYE_TEX = {"brown": ("brown", 0.52, 0.85, 0.62), "dark_brown": ("brown", 0.52, 0.8, 0.42), "hazel": ("brownlight", 0.5, 0.85, 0.75),
           "green": ("green", 0.5, 0.8, 0.8), "blue": ("blue", 0.5, 0.85, 0.85), "grey": ("blue", 0.5, 0.25, 0.9)}


def eye_material(name, color="brown"):
    """Photo-textured eyeball (MakeHuman CC0 eye maps) with a separate clear cornea (see _split_cornea)."""
    tex, hue, sat, val = EYE_TEX.get(color, EYE_TEX["brown"])
    m, T = _new_mat(name)
    out = T.n("ShaderNodeOutputMaterial")
    tc = T.n("ShaderNodeTexCoord")
    im = T.n("ShaderNodeTexImage")
    im.image = _img(os.path.join(MPFB_DATA, "eyes", "materials", tex + "_eye.png"))
    T.link(tc.outputs["UV"], im.inputs["Vector"])
    # iris = saturated part of the map; adjust only the iris hue/value, keep the sclera
    hs = T.n("ShaderNodeHueSaturation", Hue=hue, Saturation=sat, Value=val)
    T.link(im.outputs["Color"], hs.inputs["Color"])
    sep = T.n("ShaderNodeSeparateColor", _mode="HSV")
    T.link(im.outputs["Color"], sep.inputs[0])
    irism = T.n("ShaderNodeMapRange", **{"From Min": 0.12, "From Max": 0.3, "To Min": 0.0, "To Max": 1.0})
    T.link(sep.outputs[1], irism.inputs["Value"])
    # sclera: ivory, a little darker than the texture (a pure white sclera glows on screen)
    scl = T.mix(im.outputs["Color"], (0.80, 0.70, 0.62), 1.0, "MULTIPLY")
    col = T.mix(scl, hs.outputs[0], irism.outputs[0])
    b = T.n("ShaderNodeBsdfPrincipled")
    T.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.5
    # the clear cornea shell carries the reflection; a glossy eyeball under it doubled the sky sheen and
    # turned brown irises blue-grey in daylight
    b.inputs["Specular IOR Level"].default_value = 0.0
    # no subsurface: EEVEE's screen-space SSS bleeds the bright sclera into the iris (brown eyes read grey)
    b.inputs["Subsurface Weight"].default_value = 0.0
    T.link(b.outputs[0], out.inputs["Surface"])
    m.surface_render_method = "DITHERED"
    return m


def cornea_material(name="PS22_cornea"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m, T = _new_mat(name)
    out = T.n("ShaderNodeOutputMaterial")
    fr = T.n("ShaderNodeFresnel", IOR=1.38)
    gl = T.n("ShaderNodeBsdfGlossy", Roughness=0.015)
    T.link(T.math("MULTIPLY", fr.outputs[0], 0.4), gl.inputs["Color"])
    tr = T.n("ShaderNodeBsdfTransparent")
    add = T.n("ShaderNodeAddShader")
    T.link(tr.outputs[0], add.inputs[0])
    T.link(gl.outputs[0], add.inputs[1])
    T.link(add.outputs[0], out.inputs["Surface"])
    # DITHERED: visually identical here and far cheaper than BLENDED in EEVEE (big win with many people)
    m.surface_render_method = "DITHERED"
    m.use_backface_culling = True
    return m


def _split_cornea(p, eo):
    """Give the outer (cornea) shells of the MPFB high-poly eyes a clear glossy material so the
    iris shows through without refraction (EEVEE without raytracing refracts the world probe)."""
    me = eo.data
    if len(me.vertices) < 400:      # low-poly eyes: single layer
        return None
    nv = len(me.vertices)
    parent = list(range(nv))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    roots = np.array([find(i) for i in range(nv)])
    co = _coords(me)
    cm = cornea_material()
    me.materials.append(cm)
    idx = len(me.materials) - 1
    corneas = set()
    for side in (1, -1):
        cen = np.array(p.lm["eyeL"] if side > 0 else p.lm["eyeR"])
        ids = [r for r in np.unique(roots) if np.sign(co[roots == r][:, 0].mean()) == side]
        if len(ids) < 2:
            continue
        # cornea = the island that reaches furthest forward (min y)
        corneas.add(min(ids, key=lambda r: co[roots == r][:, 1].min()))
    pm = np.zeros(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", pm)
    for i, pl in enumerate(me.polygons):
        if roots[pl.vertices[0]] in corneas:
            pm[i] = idx
    me.polygons.foreach_set("material_index", pm)
    return cm


def _materials(p):
    s = p.spec
    p.mats["skin"] = skin_material(p)
    body = p.body
    body.data.materials.clear()
    body.data.materials.append(p.mats["skin"])
    hc = hair_color_rgb(s["hair_color"], s.get("grey", 0))
    if "hair" in p.parts:
        p.mats["hair"] = card_hair_material(p, p.parts["hair"], hc, s.get("grey", 0), kind="hair")
    if "eyebrows" in p.parts:
        bc = hair_color_rgb(s["hair_color"], s.get("grey", 0) * 0.8)
        p.mats["brows"] = card_hair_material(p, p.parts["eyebrows"], tuple(bc * 0.9), kind="brow", alpha_gain=1.2)
    if "eyelashes" in p.parts:
        p.mats["lashes"] = card_hair_material(p, p.parts["eyelashes"], (0.012, 0.009, 0.008), kind="lash", alpha_gain=1.4)
    if "eyes" in p.parts and len(p.parts["eyes"].data.vertices) >= 400:
        p.mats["eyes"] = eye_material(p.name + ".eye", s["eye_color"])
        eo = p.parts["eyes"]
        eo.data.materials.clear()
        eo.data.materials.append(p.mats["eyes"])
        p.mats["cornea"] = _split_cornea(p, eo)
    elif "eyes" in p.parts:
        em = p.parts["eyes"].data.materials[0]
        maj, mnr, bor = EYE_COLORS.get(s["eye_color"], EYE_COLORS["brown"])
        _set_group_input(em, "IrisMajorColor", (*maj, 1))
        _set_group_input(em, "IrisMinorColor", (*mnr, 1))
        _set_group_input(em, "IrisSection4Color", (*bor, 1))
        _set_group_input(em, "EyeWhiteColor", (0.80, 0.74, 0.68, 1))
        _set_group_input(em, "PupilSize", 0.34)
        _set_group_input(em, "IrisToEyeWhiteRelation", 0.40)
        _set_group_input(em, "Clearcoat", 0.8)
        _set_group_input(em, "OuterLayerRoughness", 0.0)
        _set_group_input(em, "InnerLayerRoughness", 0.25)
        _set_group_input(em, "OuterLayerTransmission", 0.0)
        em.surface_render_method = "DITHERED"
        p.mats["eyes"] = em
        p.mats["cornea"] = _split_cornea(p, p.parts["eyes"])
    # mouth interior: darker + rougher (the open mouth otherwise shows bright pink gums and sky-blue teeth)
    for key, tint, rough, sss in (("teeth", (0.54, 0.49, 0.41), 0.45, 0.0), ("tongue", (0.42, 0.20, 0.19), 0.6, 0.0)):
        if key in p.parts:
            o = p.parts[key]
            mt = o.data.materials[0]
            b = mt.node_tree.nodes.get("Principled BSDF")
            if b:
                # multiply the diffuse with a darker tint so teeth do not glow inside the mouth
                tex = [n for n in mt.node_tree.nodes if n.bl_idname == "ShaderNodeTexImage"]
                if tex:
                    mx = mt.node_tree.nodes.new("ShaderNodeMix")
                    mx.data_type = "RGBA"
                    mx.blend_type = "MULTIPLY"
                    mx.inputs["Factor"].default_value = 1.0
                    mt.node_tree.links.new(tex[0].outputs["Color"], mx.inputs[6])
                    mx.inputs[7].default_value = (*tint, 1)
                    mt.node_tree.links.new(mx.outputs[2], b.inputs["Base Color"])
                b.inputs["Roughness"].default_value = rough
                b.inputs["Subsurface Weight"].default_value = sss
                b.inputs["Specular IOR Level"].default_value = 0.25
                # opaque: the MPFB texture alpha let the background show through the teeth
                for l in list(b.inputs["Alpha"].links):
                    mt.node_tree.links.remove(l)
                b.inputs["Alpha"].default_value = 1.0
                b.inputs["Subsurface Radius"].default_value = (1.0, 0.5, 0.3)
                b.inputs["Subsurface Scale"].default_value = 0.003
                mt.surface_render_method = "DITHERED"
            p.mats[key] = mt


def _mouth_occluder(p):
    """Dark mouth cavity behind the teeth (bone-parented to the head). The MPFB head is open behind the
    mouth, so an open mouth (anguish, cry_out, laugh, awe) showed the sky through the throat."""
    lm = p.lm
    sc = lm["io"] / 0.062
    m = bpy.data.materials.get("PS22_mouth_cavity")
    if m is None:
        m = C.mat("PS22_mouth_cavity", (0.035, 0.012, 0.010), rough=0.9, spec=0.1)
    me = bpy.data.meshes.new(p.name + ".mouth")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    bm.to_mesh(me)
    bm.free()
    for pl in me.polygons:
        pl.use_smooth = True
    me.materials.append(m)
    ob = bpy.data.objects.new(p.name + ".mouth", me)
    for c in p.body.users_collection:
        c.objects.link(ob)
    mo = Vector(lm["mouth"])
    loc = Vector((0.0, mo.y + 0.036 * sc, mo.z - 0.004 * sc))
    M = Matrix.Translation(loc) @ Matrix.Diagonal((0.019 * sc, 0.025 * sc, 0.016 * sc, 1.0))
    rig = p.rig
    b = rig.data.bones["head"]
    ob.parent = rig
    ob.parent_type = "BONE"
    ob.parent_bone = "head"
    tail = b.matrix_local @ Matrix.Translation((0, b.length, 0))
    ob.matrix_parent_inverse = tail.inverted()
    ob.matrix_basis = M
    ob.visible_shadow = False
    p.parts["mouth"] = ob
    return ob


# ============================================================================================
# Beard (hair curves deformed on the body surface)
# ============================================================================================
def _surface_data(body):
    me = body.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = np.zeros(nt * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", tv)
    tl = np.zeros(nt * 3, np.int32)
    me.loop_triangles.foreach_get("loops", tl)
    area = np.zeros(nt, np.float32)
    me.loop_triangles.foreach_get("area", area)
    uv = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    vn = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("normal", vn)
    return tv.reshape(-1, 3), tl.reshape(-1, 3), area, uv.reshape(-1, 2), vn.reshape(-1, 3)


def _body_bvh(p):
    if getattr(p, "_bvh", None) is None:
        me = p.body.data
        co = p._co
        inb = p._w["body"] > 0.5
        polys = [tuple(pl.vertices) for pl in me.polygons if all(inb[v] for v in pl.vertices)]
        p._bvh = BVHTree.FromPolygons([tuple(c) for c in co], polys, all_triangles=False)
    return p._bvh


def _norm(a):
    return a / np.maximum(1e-9, np.linalg.norm(a, axis=-1, keepdims=True))


def make_beard(p, style=None, length=None, density=1.0, color=None, grey=None, seed=None):
    """Grow a groomed beard as hair curves on the body (Deform Curves on Surface keeps it attached
    through posing and expressions). Returns the curves object (also p.parts['beard'])."""
    s = p.spec
    style = style or s["beard"]
    cfg = dict(BEARDS[style])
    L = float(length or s.get("beard_length") or cfg["length"])
    if length or s.get("beard_length"):
        cfg["points"] = max(cfg["points"], int(5 + L / 0.012))
        cfg["stiff"] = min(cfg["stiff"], 0.25 if L > 0.06 else cfg["stiff"])
    rng = np.random.default_rng(seed if seed is not None else (s.get("seed", 0) * 31 + 7))
    co, lm = p._co, p.lm
    sc = lm["io"] / 0.062
    beard_m = p.masks["beard"]
    tv, tl, area, uv, vn = _surface_data(p.body)
    inb = p._w["body"] > 0.5
    tm = beard_m[tv].mean(1) * inb[tv].all(1)
    sel = np.nonzero(tm > 0.03)[0]
    wts = area[sel] * tm[sel] ** 1.3
    N = int(cfg["count"] * density * sc ** 2 * 1.5)   # denser so it reads as a beard, not strands
    ti = sel[rng.choice(len(sel), N, p=wts / wts.sum())]
    r1, r2 = rng.random(N), rng.random(N)
    s1 = np.sqrt(r1)
    bary = np.stack([1 - s1, s1 * (1 - r2), s1 * r2], 1)
    roots = (co[tv[ti]] * bary[:, :, None]).sum(1)
    ruv = (uv[tl[ti]] * bary[:, :, None]).sum(1)
    nrm = _norm((vn[tv[ti]] * bary[:, :, None]).sum(1))
    rmask = (beard_m[tv[ti]] * bary).sum(1)
    E = np.array(lm["eyes"])
    x, z = roots[:, 0], roots[:, 2]
    lat = np.abs(x)
    mw = lm["mouth_w"]
    # --- growth direction field
    d = np.tile(np.array([0.0, -0.15, -1.0]), (N, 1))
    must = (z > lm["mouth_top"] - 0.003 * sc) & (lat < mw + 0.012 * sc)
    d[must] = np.stack([np.sign(x[must]) * 1.6, np.full(must.sum(), -0.15), np.full(must.sum(), -0.55)], 1)
    under = nrm[:, 2] < -0.35
    d[under] = np.array([0.0, -0.8, -0.6])
    d = _norm(d)
    dt = _norm(d - nrm * (d * nrm).sum(1, keepdims=True))
    lift = cfg["lift"] * 0.6 + rng.normal(0, 0.08, N)
    lift[must] *= 0.8
    d0 = _norm(dt * np.cos(lift)[:, None] + nrm * np.sin(lift)[:, None])
    # --- length field: longest at the chin, short on the cheeks and moustache
    chinc = np.exp(-(lat / (0.028 * sc)) ** 2)
    lenf = np.full(N, 0.55)
    lenf += 0.45 * chinc * (z < lm["mouth_bot"])
    lenf = np.where(z > lm["mouth_bot"], 0.42, lenf)            # cheeks / jaw above the mouth line
    lenf = np.where(must, 0.14, lenf)
    lenf = np.where(under, 0.8, lenf)
    side = np.clip((lat - 0.04 * sc) / (0.03 * sc), 0, 1)
    lenf *= 1 - 0.35 * side
    lenf *= 1 - 0.4 * np.clip((z - lm["ear_bot"]) / (0.03 * sc), 0, 1)  # sideburns short
    if style == "long":
        lenf = np.clip(0.35 + 0.65 * (0.4 + 0.6 * chinc) * (z < lm["mouth_top"]) + 0.2 * must, 0.25, 1.0)
    lenf *= rmask ** 0.5
    # --- guides (clump centres)
    G = max(30, N // 14)
    gi = rng.choice(N, G, replace=False)
    kd = KDTree(G)
    for i, g in enumerate(gi):
        kd.insert(roots[g], i)
    kd.balance()
    owner = np.array([kd.find(r)[1] for r in roots])
    K = cfg["points"]
    bvh = _body_bvh(p)
    grav = np.array([0.0, 0.0, -1.0])
    guides = np.zeros((G, K, 3))
    for i, g in enumerate(gi):
        pos = roots[g].copy()
        dr = d0[g].copy()
        seg = L / (K - 1)
        phase = rng.random() * 6.28
        guides[i, 0] = pos
        for k in range(1, K):
            t = k / (K - 1)
            bend = (1 - cfg["stiff"]) * (0.25 + 0.75 * t)
            dr = dr * (1 - bend) + grav * bend + d0[g] * cfg["stiff"] * 0.35
            dr = dr / np.linalg.norm(dr)
            pos = pos + dr * seg
            # wave (about one period every 3.5 cm of length)
            side = np.cross(dr, nrm[g])
            if np.linalg.norm(side) > 1e-6:
                side = side / np.linalg.norm(side)
                pos = pos + side * math.sin(phase + t * max(7.0, L / 0.035 * 6.283)) * cfg["curl"] * min(1.0, 3 * t)
            loc, nn, _, dist = bvh.find_nearest(Vector(pos))
            if loc is not None:
                off = (0.0012 + 0.0025 * t) * sc
                if pos[2] < lm["chin_bot"] - 0.02 * sc:      # over the chest: clear the robe
                    off += min(0.022, (lm["chin_bot"] - 0.02 * sc - pos[2]) * 0.5) * sc
                dv = Vector(pos) - loc
                if dv.dot(nn) < off:
                    pos = np.array(loc + nn * off)
            guides[i, k] = pos
    # --- children: follow their guide, clumping towards the tip
    q = np.clip(lenf * rng.uniform(0.75, 1.08, N), 0.12, 1.0)
    T = np.linspace(0, 1, K)
    pts = np.zeros((N, K, 3))
    clump = (0.62 if L > 0.06 else 0.45) + 0.3 * rng.random(N)     # long beards fall in locks
    for k in range(K):
        tk = T[k] * q                                   # sample the guide polyline at fraction tk
        fk = tk * (K - 1)
        k0 = np.floor(fk).astype(int).clip(0, K - 2)
        a = (fk - k0)[:, None]
        gpos = guides[owner, k0] * (1 - a) + guides[owner, k0 + 1] * a
        off = (roots - guides[owner, 0]) * (1 - clump * T[k] ** 0.7)[:, None]
        pts[:, k] = gpos + off
    frizz = rng.normal(0, 1, (N, K, 3)) * (0.0009 * sc) * (T ** 1.5)[None, :, None]
    pts += frizz
    if L > 0.06:      # long beards taper to a soft point below the chin
        below = np.clip((lm["chin_bot"] - pts[:, :, 2]) / L, 0, 1)
        pts[:, :, 0] *= 1 - 0.68 * below
    pts[:, 0] = roots
    # cheap collision for the children: keep every point above the tangent plane at its root
    for k in range(1, K):
        off = (0.0008 + 0.0022 * T[k]) * sc
        h = ((pts[:, k] - roots) * nrm).sum(1)
        push = np.maximum(0.0, off - h)
        pts[:, k] += nrm * push[:, None] * (1.0 - 0.6 * T[k])
    # keep moustache hair off the lips: no strand point over the mouth may drop below the upper-lip line
    lipz = lm["mouth_top"] + 0.0012 * sc
    over = (np.abs(pts[:, :, 0]) < mw + 0.004 * sc) & (pts[:, :, 2] < lipz) & (roots[:, None, 2] > lm["mouth_bot"])
    pts[:, :, 2] = np.where(over, lipz, pts[:, :, 2])
    # --- curves datablock
    cv = bpy.data.hair_curves.new(p.name + ".beard")
    cv.add_curves([K] * N)
    cv.position_data.foreach_set("vector", pts.astype(np.float32).ravel())
    rad = np.tile(np.linspace(1.0, 0.45, K), N) * 0.00024 * (0.8 + 0.4 * rng.random(N)).repeat(K)
    if "radius" not in cv.attributes:
        cv.attributes.new("radius", "FLOAT", "POINT")
    cv.attributes["radius"].data.foreach_set("value", rad.astype(np.float32))
    a = cv.attributes.new("surface_uv_coordinate", "FLOAT2", "CURVE")
    a.data.foreach_set("vector", ruv.astype(np.float32).ravel())
    cv.surface = p.body
    cv.surface_uv_map = p.body.data.uv_layers[0].name
    ob = bpy.data.objects.new(p.name + ".beard", cv)
    for c in p.body.users_collection:
        c.objects.link(ob)
    ob.parent = p.rig
    ob.modifiers.new("deform", "NODES").node_group = _deform_on_surface_group()
    hc = hair_color_rgb(color or s["beard_color"], 0.0)
    mat = curve_hair_material(p.name + ".beard_mat", hc, grey if grey is not None else s.get("grey", 0))
    cv.materials.append(mat)
    p.parts["beard"] = ob
    p.mats["beard"] = mat
    return ob


def _deform_on_surface_group():
    ng = bpy.data.node_groups.get("PS22_DeformOnSurface")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("PS22_DeformOnSurface", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    dn = ng.nodes.new("GeometryNodeDeformCurvesOnSurface")
    ng.links.new(gi.outputs[0], dn.inputs[0])
    ng.links.new(dn.outputs[0], go.inputs[0])
    return ng


def curve_hair_material(name, color, grey=0.0, translucency=0.35):
    m, T = _new_mat(name)
    out = T.n("ShaderNodeOutputMaterial")
    hi = T.n("ShaderNodeHairInfo")
    var = T.n("ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 1.0, "To Min": 0.6, "To Max": 1.5})
    T.link(hi.outputs["Random"], var.inputs["Value"])
    tip = T.n("ShaderNodeMapRange", **{"From Min": 0.0, "From Max": 1.0, "To Min": 0.75, "To Max": 1.35})
    T.link(hi.outputs["Intercept"], tip.inputs["Value"])
    col = T.mix(tuple(color), T.math("MULTIPLY", var.outputs[0], tip.outputs[0]), 1.0, "MULTIPLY")
    if grey > 0.01:
        # salt and pepper: every strand is partly grey (a binary white/dark choice per strand rendered as
        # speckle noise at film distance); the per-strand random only spreads the amount around `grey`
        rg = T.math("FRACT", T.math("MULTIPLY", hi.outputs["Random"], 7.31))
        amt = T.math("ADD", T.math("MULTIPLY", T.math("SUBTRACT", rg, 0.5), 0.55), min(0.97, grey), True)
        gcol = HAIR_COLORS["white"] if grey > 0.6 else HAIR_COLORS["grey"]
        col = T.mix(col, T.mix(tuple(Vector(gcol) * 0.9), var.outputs[0], 1.0, "MULTIPLY"), amt)
    b = T.n("ShaderNodeBsdfPrincipled")
    T.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.6       # some sheen (a flat 0.8/0.08 read as a black mass)
    b.inputs["Specular IOR Level"].default_value = 0.18
    # backlit glow: hair is translucent (forward scattering) - EEVEE's Principled alone only sparkles
    tl = T.n("ShaderNodeBsdfTranslucent")
    T.set(tl.inputs["Color"], T.mix(col, (2.5, 2.2, 1.9), 1.0, "MULTIPLY"))
    mx = T.n("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = translucency
    T.link(b.outputs[0], mx.inputs[1])
    T.link(tl.outputs[0], mx.inputs[2])
    T.link(mx.outputs[0], out.inputs["Surface"])
    return m


def make_staff(p, side="R", length=None, seed=5):
    """A gnarled wooden staff (Moses, shepherds). The mesh origin is the foot of the staff, local +Z runs
    to the knob. It is attached to the hand by hold_staff() (called by every pose()/key_pose()):
    use the poses 'staff' (planted beside the feet) or 'staff_raised' (held aloft). Returns the object."""
    L = length or p.height * 1.08
    sc = p.height / 1.75
    verts, faces = [], []
    seg, ring = 44, 10
    rnd = random.Random(seed)
    knots = [(rnd.uniform(0.1, 0.92), rnd.uniform(0, 2 * math.pi), rnd.uniform(0.002, 0.005)) for _ in range(9)]
    for i in range(seg + 1):
        t = i / seg
        z = L * t
        r = (0.0145 + 0.0035 * (1 - t) + 0.0016 * math.sin(t * 23.0)) * sc
        if t > 0.94:                                    # worn knob at the top
            r *= 1.0 + 0.55 * math.sin(min(1.0, (t - 0.94) / 0.06) * math.pi * 0.75)
        if t > 0.995:
            r *= 0.55
        cx = (0.010 * math.sin(t * 5.3 + 1) + 0.004 * math.sin(t * 17.0)) * sc
        cy = (0.010 * math.cos(t * 4.1) + 0.003 * math.cos(t * 13.0)) * sc
        for j in range(ring):
            a = 2 * math.pi * j / ring
            rr = r * (1 + 0.06 * rnd.uniform(-1, 1))
            for kt, ka, kr in knots:                    # knots / branch stubs
                d = abs(t - kt) * L
                if d < 0.03:
                    da = math.cos(a - ka)
                    rr += kr * sc * max(0.0, da) ** 3 * (1 - d / 0.03)
            verts.append((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
    for i in range(seg):
        for j in range(ring):
            a = i * ring + j
            b = i * ring + (j + 1) % ring
            faces.append((a, b, b + ring, a + ring))
    faces.append(tuple(range(ring))[::-1])
    faces.append(tuple(seg * ring + j for j in range(ring)))
    me = bpy.data.meshes.new(p.name + ".staff")
    me.from_pydata(verts, [], faces)
    for pl in me.polygons:
        pl.use_smooth = True
    ob = bpy.data.objects.new(p.name + ".staff", me)
    for c in p.rig.users_collection:
        c.objects.link(ob)
    try:
        ob.data.materials.append(C.wood_material("rough_wood", 3.0, (0.55, 0.45, 0.35)))
    except Exception:
        ob.data.materials.append(C.mat("staff_wood", (0.22, 0.15, 0.09), rough=0.7))
    ob["staff_side"] = _side(side)
    ob["staff_length"] = L
    ob.parent = p.rig
    p.props.append(ob)
    p.staff = ob
    return ob


def _grip_frame(P, s):
    """Fist frame of hand s for pose state P (armature space): (centre of the grip channel, axis from the
    little-finger side to the index side)."""
    k2, k5 = P.head("finger2-1." + s), P.head("finger5-1." + s)
    axis = (k2 - k5).normalized()
    fwd = _perp(((k2 + k5) * 0.5) - P.head("wrist." + s), axis)
    tip = P.tail("finger3-3." + s)
    palm = _perp(tip - (k2 + k5) * 0.5, axis)
    palm = _perp(palm - fwd * palm.dot(fwd) * 0.5, axis)
    sc = P.an["hand_len" + s] / 0.095
    centre = (k2 * 0.45 + k5 * 0.55) + palm.normalized() * 0.019 * sc - fwd * 0.004 * sc
    return centre, axis


def _staff_arm(P, s, T, pole, want, flex=0.0, shrug=0.0):
    """IK the arm to put the fist at T and search forearm pronation / wrist deviation so the fist axis
    (grip channel) lines up with direction `want` (the staff). Returns the angle error (deg)."""
    want = Vector(want).normalized()
    best = None
    snap = {n: m.copy() for n, m in P.rot.items()}
    for pron in range(-40, 181, 20):
        for dev in (-20, 0, 20):
            P.rot = {n: m.copy() for n, m in snap.items()}
            P._c.clear()
            _arm_ik(P, s, T, pole, pron=pron, flex=flex, dev=dev, shrug=shrug)
            _hand(P, s, "grip")
            ang = math.degrees(_grip_frame(P, s)[1].angle(want))
            if best is None or ang < best[0]:
                best = (ang, pron, dev)
    _, pron, dev = best
    for pr in (pron - 10, pron - 5, pron + 5, pron + 10):   # refine
        for dv in (dev - 8, dev, dev + 8):
            P.rot = {n: m.copy() for n, m in snap.items()}
            P._c.clear()
            _arm_ik(P, s, T, pole, pron=pr, flex=flex, dev=dv, shrug=shrug)
            _hand(P, s, "grip")
            ang = math.degrees(_grip_frame(P, s)[1].angle(want))
            if ang < best[0]:
                best = (ang, pr, dv)
    P.rot = {n: m.copy() for n, m in snap.items()}
    P._c.clear()
    _arm_ik(P, s, T, pole, pron=best[1], flex=flex, dev=best[2], shrug=shrug)
    _hand(P, s, "grip")
    return best[0]


def hold_staff(person, grip=None, ground_z=None):
    """Attach person.staff to its hand (bone-parented to the wrist, so it follows later animation).
    The staff runs through the fist along the grip channel. grip: fraction of the staff length below the
    hand (None = planted on the ground when the hand is low enough, else 0.38). Called by pose()."""
    st = getattr(person, "staff", None)
    if st is None or person._pose is None:
        return None
    P = person._pose
    s = st.get("staff_side", "R")
    L = float(st.get("staff_length", person.height * 1.08))
    rig = person.rig
    mw = rig.matrix_world
    c, ax = _grip_frame(P, s)
    cw = mw @ c
    aw = (mw.to_3x3() @ ax).normalized()
    if aw.z < 0:
        aw = -aw
    gz = mw.translation.z if ground_z is None else ground_z
    if grip is None:
        planted = (cw.z - gz) / max(aw.z, 0.2)
        grip = planted / L if (aw.z > 0.6 and planted < 0.7 * L) else 0.38
    base = cw - aw * grip * L
    R = Vector((0, 0, 1)).rotation_difference(aw).to_matrix().to_4x4()
    st.parent = rig
    st.parent_type = "BONE"
    st.parent_bone = "wrist." + s
    st.matrix_parent_inverse = Matrix.Identity(4)
    pbm = mw @ P.pm("wrist." + s) @ Matrix.Translation((0, rig.data.bones["wrist." + s].length, 0))
    st.matrix_basis = pbm.inverted() @ (Matrix.Translation(base) @ R)
    return st


# ============================================================================================
# Pose engine (pure FK math in armature space, written to the rig as quaternions)
# ============================================================================================
FACE_PREFIX = ("jaw", "special", "oris", "levator", "orbicularis", "oculi", "risorius", "temporalis", "tongue", "eye.")
SPINE = ["spine05", "spine04", "spine03", "spine02", "spine01"]
NECK = ["neck01", "neck02", "neck03"]
FINGERS = {1: "thumb", 2: "index", 3: "middle", 4: "ring", 5: "pinky"}


def _perp(v, axis):
    v = Vector(v)
    a = Vector(axis).normalized()
    r = v - a * v.dot(a)
    return r.normalized() if r.length > 1e-8 else r


def _is_face(n):
    return n.startswith(FACE_PREFIX)


class _Pose:
    def __init__(self, p):
        self.p = p
        arm = p.rig.data
        self.bones = arm.bones
        self.names = [b.name for b in arm.bones]
        self.rest = {b.name: b.matrix_local.copy() for b in arm.bones}
        self.rest3 = {n: m.to_3x3().normalized() for n, m in self.rest.items()}
        self.rest3i = {n: m.inverted() for n, m in self.rest3.items()}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.bones}
        self.rel = {n: (self.rest[self.parent[n]].inverted_safe() @ self.rest[n]) if self.parent[n] else None for n in self.names}
        self.rot = {n: Matrix.Identity(3) for n in self.names}
        self.loc = Vector((0, 0, 0))
        self._c = {}
        _anatomy(p, self)

    def copy(self):
        q = _Pose.__new__(_Pose)
        q.__dict__.update(self.__dict__)
        q.rot = {n: m.copy() for n, m in self.rot.items()}
        q.loc = self.loc.copy()
        q._c = {}
        return q

    def pm(self, n):
        c = self._c.get(n)
        if c is not None:
            return c
        par = self.parent[n]
        if par is None:
            M = Matrix.Translation(self.loc) @ self.rest[n] @ self.rot[n].to_4x4()
        else:
            M = self.pm(par) @ self.rel[n] @ self.rot[n].to_4x4()
        self._c[n] = M
        return M

    def head(self, n):
        return self.pm(n).translation.copy()

    def tail(self, n):
        return self.pm(n) @ Vector((0, self.bones[n].length, 0))

    def R(self, n):
        return self.pm(n).to_3x3().normalized()

    def ydir(self, n):
        return self.R(n).col[1].normalized()

    def carry(self, n, v):
        """Rest-space vector attached to bone n, expressed in its current orientation."""
        return (self.R(n) @ self.rest3i[n]) @ Vector(v)

    def set_R(self, n, Rw):
        par = self.parent[n]
        base = self.rest3[n] if par is None else self.R(par) @ (self.rest3i[par] @ self.rest3[n])
        self.rot[n] = base.inverted() @ Rw
        self._c.clear()

    def rotate(self, n, axis, ang):
        axis = Vector(axis)
        if axis.length < 1e-9 or abs(ang) < 1e-9:
            return
        self.set_R(n, Matrix.Rotation(ang, 3, axis.normalized()) @ self.R(n))

    def bend_toward(self, n, direction, ang):
        """Rotate bone n so its Y axis swings by ang (rad) towards direction."""
        ax = self.ydir(n).cross(Vector(direction))
        self.rotate(n, ax, ang)

    def orient(self, n, d, ref_cur, ref_rest):
        d = Vector(d).normalized()
        y0 = self.rest3[n].col[1].normalized()
        r0 = _perp(ref_rest, y0)
        r1 = _perp(ref_cur, d)
        if r1.length < 1e-6:
            r1 = _perp(self.carry(n, ref_rest), d)
        F0 = Matrix((r0, y0, r0.cross(y0))).transposed()
        F1 = Matrix((r1, d, r1.cross(d))).transposed()
        self.set_R(n, (F1 @ F0.transposed()) @ self.rest3[n])

    def aim(self, n, d):
        q = self.ydir(n).rotation_difference(Vector(d).normalized())
        self.set_R(n, q.to_matrix() @ self.R(n))

    def turn(self, n, bend=0.0, side=0.0, twist=0.0, frame_of=None):
        """bend + = forward flexion, side + = towards the character's left, twist + = turn to the left (deg),
        about the character axes carried by bone frame_of (default: the parent)."""
        ref = frame_of or self.parent[n] or n
        L, U, F = self.carry(ref, LEFT), self.carry(ref, UP), self.carry(ref, FWD)
        if bend:
            self.rotate(n, L, math.radians(bend))
        if side:
            self.rotate(n, -F, math.radians(side))
        if twist:
            self.rotate(n, U, math.radians(twist))

    def write(self, frame=None, bones=None, skip_face=True):
        rig = self.p.rig
        pbs = rig.pose.bones
        names = bones or self.names
        for n in names:
            if skip_face and _is_face(n):
                continue
            pb = pbs[n]
            q = self.rot[n].to_quaternion()
            if pb.rotation_quaternion.dot(q) < 0:
                q.negate()
            pb.rotation_quaternion = q
            if frame is not None:
                pb.keyframe_insert("rotation_quaternion", frame=frame, group=n)
        rootn = self.names[0] if "root" not in pbs else "root"
        pbs[rootn].location = self.rest3i[rootn] @ self.loc
        if frame is not None:
            pbs[rootn].keyframe_insert("location", frame=frame, group=rootn)


def _anatomy(p, P):
    """Rest-pose anatomical reference vectors (cached on the person)."""
    if getattr(p, "_anat", None):
        P.an = p._anat
        return
    an = {}
    co, w = p._co, p._w
    nails = co[(w["fingernails"] > 0.5)]
    for s in "LR":
        ua = (P.head("lowerarm01." + s) - P.head("upperarm01." + s))
        fa = (P.head("wrist." + s) - P.head("lowerarm01." + s))
        an["ua_len" + s] = ua.length
        an["fa_len" + s] = fa.length
        an["crease" + s] = _perp(fa, ua)
        # palm normal from the middle-finger nail (nails are on the back of the hand)
        h = P.head("finger3-3." + s)
        t = P.tail("finger3-3." + s)
        side_nails = nails[(nails[:, 0] > 0) if s == "L" else (nails[:, 0] < 0)]
        dd = np.linalg.norm(side_nails - np.array((h + t) / 2), axis=1)
        nc = Vector(side_nails[dd < 0.012].mean(0)) if (dd < 0.012).any() else Vector(side_nails[np.argmin(dd)])
        axis = (t - h).normalized()
        dorsal = _perp(nc - h, axis)
        an["palm" + s] = -dorsal
        an["th_len" + s] = (P.head("lowerleg01." + s) - P.head("upperleg01." + s)).length
        an["sh_len" + s] = (P.head("foot." + s) - P.head("lowerleg01." + s)).length
        an["hand_len" + s] = (P.tail("metacarpal2." + s) - P.head("wrist." + s)).length
        # rest pronation (deg, + = towards medial) in the convention used by _arm
        uan, fan = ua.normalized(), fa.normalized()
        e = uan.angle(fan)
        af = _perp(-uan * math.sin(e) + an["crease" + s] * math.cos(e), fan)
        pl = _perp(an["palm" + s], fan)
        ang = math.degrees(af.angle(pl)) if af.length > 1e-6 and pl.length > 1e-6 else 90.0
        an["rest_pron" + s] = ang
    an["knee"] = Vector(FWD)
    p._anat = an
    P.an = an


def _medial(s):
    return Vector((-1, 0, 0)) if s == "L" else Vector((1, 0, 0))


def _lateral(s):
    return Vector((1, 0, 0)) if s == "L" else Vector((-1, 0, 0))


def _arm(P, s, u, crease, elbow, pron=60.0, flex=0.0, dev=0.0, shrug=0.0, twist_split=0.5):
    """Set an arm from anatomical parameters (character/armature space).
    u: upper-arm direction; crease: direction the elbow crease faces (forearm bends towards it);
    elbow: flexion deg (0 straight); pron: forearm pronation deg (0 = palm faces the crease side,
    ~80 = palm faces the body when hanging); flex: wrist flexion (+ towards the palm); dev: radial deviation."""
    an = P.an
    if shrug:
        P.bend_toward("clavicle." + s, UP, math.radians(shrug))
    u = Vector(u).normalized()
    if crease is None:
        # minimal-twist humerus: swing the rest crease along with the arm (no axial rotation)
        r0 = (P.rest["lowerarm01." + s].translation - P.rest["upperarm01." + s].translation).normalized()
        c = _perp(r0.rotation_difference(u).to_matrix() @ an["crease" + s], u)
    else:
        c = _perp(crease, u)
    if c.length < 1e-6:
        c = _perp(FWD, u)
    for b in ("upperarm01.", "upperarm02."):
        P.orient(b + s, u, c, an["crease" + s])
    e = math.radians(max(0.0, min(150.0, elbow)))
    f = u * math.cos(e) + c * math.sin(e)
    af = -u * math.sin(e) + c * math.cos(e)
    sign = 1.0 if s == "L" else -1.0       # pronation = +rotation about elbow->wrist for the left arm
    pr = math.radians(pron) * sign
    palm = Matrix.Rotation(pr, 3, f) @ af
    rp = an.get("rest_pron" + s, 90.0)
    pr01 = math.radians(rp + (pron - rp) * twist_split) * sign      # spread the twist from rest over both forearm bones
    P.orient("lowerarm01." + s, f, Matrix.Rotation(pr01, 3, f) @ af, an["palm" + s])
    P.orient("lowerarm02." + s, f, palm, an["palm" + s])
    if flex:
        pc = P.carry("wrist." + s, an["palm" + s])
        P.bend_toward("wrist." + s, pc, math.radians(flex))
    if dev:
        pc = P.carry("wrist." + s, an["palm" + s])
        thumb = (P.head("finger1-1." + s) - P.head("finger5-1." + s))
        P.bend_toward("wrist." + s, _perp(thumb, P.ydir("wrist." + s)), math.radians(dev))
    return palm


def _arm_ik(P, s, T, pole, pron=60.0, flex=0.0, dev=0.0, shrug=0.0, palm_target=True, crease_hint=None):
    """Two-bone IK: put the palm centre (palm_target) or the wrist at T (armature space).
    pole: direction the elbow points to."""
    an = P.an
    if shrug:
        P.bend_toward("clavicle." + s, UP, math.radians(shrug))
    T = Vector(T)
    S = P.head("upperarm01." + s)
    a, b = an["ua_len" + s], an["fa_len" + s]
    Tw = T
    for it in range(2 if palm_target else 1):
        if palm_target:
            dirh = (T - S).normalized() if it == 0 else P.ydir("wrist." + s)
            Tw = T - dirh * an["hand_len" + s] * 0.5
        D = Tw - S
        d = max(abs(a - b) + 1e-3, min((a + b) * 0.9995, D.length))
        Dn = D.normalized()
        cosA = max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d)))
        A = math.acos(cosA)
        pp = _perp(pole, Dn)
        if pp.length < 1e-6:
            pp = _perp(-UP, Dn)
        uu = Dn * math.cos(A) + pp * math.sin(A)
        E = S + uu * a
        f = (S + Dn * d - E).normalized()
        el = math.degrees(math.acos(max(-1.0, min(1.0, uu.dot(f)))))
        cr = _perp(f, uu) if el > 2.0 else (_perp(crease_hint, uu) if crease_hint is not None else -pp)
        _arm(P, s, uu, cr, el, pron, flex, dev)
    return P.head("wrist." + s)


def _leg(P, s, t, knee_fwd, knee, ankle=0.0, toes=0.0):
    """thigh direction t, patella direction hint knee_fwd, knee flexion deg, ankle (+ dorsiflex) deg."""
    an = P.an
    t = Vector(t).normalized()
    k = _perp(knee_fwd, t)
    if k.length < 1e-6:
        k = _perp(FWD, t)
    for b in ("upperleg01.", "upperleg02."):
        P.orient(b + s, t, k, an["knee"])
    kk = math.radians(max(0.0, min(165.0, knee)))
    sh = t * math.cos(kk) - k * math.sin(kk)
    ks = k * math.cos(kk) + t * math.sin(kk)
    for b in ("lowerleg01.", "lowerleg02."):
        P.orient(b + s, sh, ks, an["knee"])
    if ankle:
        P.bend_toward("foot." + s, -sh, math.radians(ankle))
    if toes:
        up = P.carry("foot." + s, UP)
        for i in range(1, 6):
            P.bend_toward("toe%d-1.%s" % (i, s), up, math.radians(toes))
    return sh


def _leg_ik(P, s, T, pole, ankle=0.0, foot_flat=True, toes=0.0):
    """Put the ankle at T (armature space); pole = knee direction."""
    an = P.an
    S = P.head("upperleg01." + s)
    a, b = an["th_len" + s], an["sh_len" + s]
    D = Vector(T) - S
    d = max(abs(a - b) + 1e-3, min((a + b) * 0.9995, D.length))
    Dn = D.normalized()
    A = math.acos(max(-1.0, min(1.0, (a * a + d * d - b * b) / (2 * a * d))))
    pp = _perp(pole, Dn)
    tt = Dn * math.cos(A) + pp * math.sin(A)
    K = S + tt * a
    sh = (S + Dn * d - K).normalized()
    kn = math.degrees(math.acos(max(-1.0, min(1.0, tt.dot(sh)))))
    kf = -_perp(sh, tt) if kn > 1 else pp
    _leg(P, s, tt, kf, kn, 0.0, toes)
    if foot_flat:
        # rotate the foot so its sole is level: the foot's toe direction projected to horizontal
        y = P.ydir("foot." + s)
        hz = Vector((y.x, y.y, 0)).normalized()
        cur_pitch = math.atan2(y.z, Vector((y.x, y.y)).length)
        rest_pitch = math.atan2(P.rest3["foot." + s].col[1].z, Vector(P.rest3["foot." + s].col[1][:2]).length)
        P.rotate("foot." + s, y.cross(hz), cur_pitch - rest_pitch)
    if ankle:
        P.bend_toward("foot." + s, -sh, math.radians(ankle))
    return kn


HANDS = {  # thumb, index, middle, ring, pinky: (base, mid, tip) curl degrees; spread deg; thumb opposition deg
    "relaxed": ([(8, 12, 10), (12, 22, 12), (16, 28, 14), (20, 32, 16), (24, 36, 18)], 0, 18),
    "fist": ([(25, 40, 45), (80, 100, 65), (85, 100, 65), (88, 100, 65), (90, 100, 65)], 0, 50),
    "open": ([(0, 0, 0), (2, 3, 2), (2, 3, 2), (2, 3, 2), (2, 4, 2)], 9, 0),
    "palm": ([(0, 0, 0), (1, 2, 1), (1, 2, 1), (1, 2, 1), (1, 2, 1)], 4, 0),
    "grip": ([(20, 30, 30), (58, 72, 45), (62, 74, 45), (66, 74, 45), (70, 74, 45)], 0, 55),
    "clasped": ([(10, 20, 20), (40, 55, 35), (45, 58, 38), (48, 60, 40), (52, 60, 40)], 0, 20),
    "point": ([(25, 35, 35), (0, 3, 2), (80, 100, 65), (85, 100, 65), (88, 100, 65)], 0, 45),
    "cross": ([(15, 20, 18), (28, 50, 35), (32, 56, 40), (38, 62, 42), (42, 64, 44)], 3, 8),
    "cup": ([(10, 10, 10), (8, 14, 8), (10, 16, 10), (12, 18, 10), (14, 20, 10)], 2, 30),
    "claw": ([(15, 30, 30), (20, 60, 55), (22, 64, 58), (25, 66, 60), (28, 66, 60)], 6, 25),
}


def _hand(P, s, shape="relaxed", amount=1.0):
    if shape not in HANDS:
        shape = "relaxed"
    curls, spread, opp = HANDS[shape]
    an = P.an
    palm = P.carry("wrist." + s, an["palm" + s])
    mid = P.head("finger3-1." + s)
    for i in range(1, 6):
        c = curls[i - 1]
        b1 = "finger%d-1.%s" % (i, s)
        if i == 1:
            # thumb: opposition (swing towards the palm), then flex
            P.bend_toward(b1, palm, math.radians(opp * amount))
        elif spread:
            off = _perp(P.head(b1) - mid, palm)
            if off.length > 1e-6:
                P.bend_toward(b1, off, math.radians(spread * amount * (1.0 if i != 3 else 0.0)))
        lat = P.ydir(b1).cross(palm).normalized()
        for j in range(3):
            P.rotate("finger%d-%d.%s" % (i, j + 1, s), lat, math.radians(c[j] * amount))


# --------------------------------------------------------------------------------------------
# Static poses
# --------------------------------------------------------------------------------------------
def _new_pose(p):
    return _Pose(p)


def _hips_shift(P, dx=0.0, dy=0.0, dz=0.0):
    P.loc += Vector((dx, dy, dz))
    P._c.clear()


def _std_legs(P, knee=(3, 3), spread=0.03, out=4.0, pole_out=0.0):
    for s, kn in zip("LR", knee):
        lat = _lateral(s)
        t = Vector((lat.x * spread, 0.01, -1))
        kf = (FWD + lat * math.tan(math.radians(out + pole_out))).normalized()
        _leg(P, s, t, kf, kn, 0.0)
        _flatten_foot(P, s)


def _flatten_foot(P, s, pitch_extra=0.0):
    """Keep the sole level with the ground (rest pitch) after the shin moved."""
    y = P.ydir("foot." + s)
    rest_y = P.rest3["foot." + s].col[1]
    hz = Vector((y.x, y.y, 0))
    if hz.length < 1e-6:
        return
    hz.normalize()
    cur = math.atan2(y.z, Vector((y.x, y.y)).length)
    want = math.atan2(rest_y.z, Vector(rest_y[:2]).length) + math.radians(pitch_extra)
    P.rotate("foot." + s, y.cross(hz), cur - want)
    # remove roll so the sole is flat: align the foot's carried up with the world up
    up = P.carry("foot." + s, UP)
    yy = P.ydir("foot." + s)
    upp = _perp(up, yy)
    wanted = _perp(UP, yy)
    if upp.length > 1e-6 and wanted.length > 1e-6:
        ang = upp.angle(wanted)
        if upp.cross(wanted).dot(yy) < 0:
            ang = -ang
        P.rotate("foot." + s, yy, ang)


def _hang_arms(P, abd=10.0, elbow=12.0, pron=80.0, back=2.0, hand="relaxed"):
    for s in "LR":
        lat = _lateral(s)
        u = Vector((lat.x * math.sin(math.radians(abd)), math.sin(math.radians(back)), -1))
        _arm(P, s, u, FWD, elbow, pron)
        _hand(P, s, hand)


def _apply_head(P, head="level", amount=1.0, tilt=0.0, turn=0.0):
    pitch = {"level": 0, "up": -32, "down": 30, "bowed": 45, "side": 10, "sky": -45}.get(head, 0) * amount
    side = (22 if head == "side" else 0) + tilt
    for i, n in enumerate(NECK + ["head"]):
        wgt = (0.22, 0.24, 0.24, 0.30)[i]
        P.turn(n, bend=pitch * wgt, side=side * wgt, twist=turn * wgt)


def _spine_bend(P, bend=0.0, side=0.0, twist=0.0, weights=(0.15, 0.2, 0.22, 0.22, 0.21)):
    for n, wgt in zip(SPINE, weights):
        P.turn(n, bend=bend * wgt, side=side * wgt, twist=twist * wgt)


def _pose_stand(P, p, relaxed=False, head="level", hands="relaxed", **k):
    if relaxed:
        _hips_shift(P, dx=0.012 * p.height / 1.75)
        _spine_bend(P, bend=3, side=-3)
        _std_legs(P, knee=(2, 14), spread=0.04, out=6)
        for s in "LR":
            lat = _lateral(s)
            u = Vector((lat.x * (0.14 if s == "L" else 0.1), 0.03, -1))
            _arm(P, s, u, FWD, 14 if s == "L" else 22, 78)
            _hand(P, s, hands)
        _apply_head(P, head, tilt=2, turn=k.get("turn", 0))
    else:
        _spine_bend(P, bend=2)
        _std_legs(P, knee=(3, 3), spread=0.035)
        _hang_arms(P, hand=hands)
        _apply_head(P, head, turn=k.get("turn", 0))


def _pose_crucified(P, p, head="up", strain=0.6, hands="cross", hand_targets=None, feet_targets=None, knee_side=1.0, **k):
    st = max(0.0, min(1.0, strain))
    # torso: chest lifted and slightly arched forward from the cross, a gentle S-curve
    _spine_bend(P, bend=-4 + 6 * st, side=3 * knee_side)
    # arms along the beam, V-shaped
    th = math.radians(14 + 16 * st)
    for s in "LR":
        lat = _lateral(s)
        if hand_targets:
            _arm_ik(P, s, hand_targets[s], pole=Vector((0, 1.0, -0.3)), pron=40, flex=-6, shrug=10 + 12 * st)
        else:
            P.bend_toward("clavicle." + s, UP, math.radians(10 + 12 * st))
            u = Vector((lat.x * math.cos(th), 0.03, math.sin(th)))
            _arm(P, s, u, FWD, 6, 40, flex=-6)
        _hand(P, s, hands)
    # legs: knees bent and turned, feet together / overlapping
    if feet_targets:
        for s in "LR":
            pole = (FWD + LEFT * 0.55 * knee_side).normalized()
            _leg_ik(P, s, feet_targets[s], pole, foot_flat=False)
            P.bend_toward("foot." + s, -UP, math.radians(25 + 10 * st))
    else:
        kn = 22 + 22 * st
        for s in "LR":
            lat = _lateral(s)
            t = Vector((-lat.x * 0.03 + 0.18 * knee_side * 0.4, -0.12, -1))
            kf = (FWD + LEFT * 0.6 * knee_side).normalized()
            _leg(P, s, t, kf, kn)
            P.bend_toward("foot." + s, -UP, math.radians(30 + 10 * st))
    _apply_head(P, head, amount=1.0, tilt=(-6 if head != "side" else 0))


def _pose_kneel(P, p, variant="kneel", head=None, hands=None, rock=None, **k):
    h = p.height / 1.75
    # thighs vertical-ish, shins on the ground behind (knee 95-110), toes tucked
    lean = {"kneel": 4, "kneel_pray": 10, "kneel_bow": 70}.get(variant, 4)
    for s in "LR":
        lat = _lateral(s)
        t = Vector((lat.x * 0.06, -0.12 if variant != "kneel_bow" else -0.05, -1))
        sh = _leg(P, s, t, FWD + lat * 0.05, 100 if variant != "kneel_bow" else 120)
        _flatten_foot_to(P, s, sh)
    if variant == "kneel_bow":
        _spine_bend(P, bend=lean * 0.5)
        P.turn("root", bend=lean * 0.5, frame_of="root")
        # undo the root pitch on the legs so knees stay down
        for s in "LR":
            P.turn("upperleg01." + s, bend=-lean * 0.5, frame_of="root")
        for s in "LR":
            lat = _lateral(s)
            u = Vector((lat.x * 0.25, -1.0, -0.45))
            _arm(P, s, u, UP, 40, 175, flex=-30)
            _hand(P, s, "palm")
        _apply_head(P, "down", amount=0.6)
    elif variant == "kneel_pray":
        _spine_bend(P, bend=lean)
        tgt = Vector(rock) if rock is not None else None
        for s in "LR":
            lat = _lateral(s)
            T = tgt + lat * 0.012 if tgt is not None else None
            if T is None:
                chest = P.head("spine01")
                T = chest + Vector((lat.x * 0.015, -0.3 * h, -0.12 * h))
            _arm_ik(P, s, T, pole=(lat * 0.6 - UP + Vector((0, 0.3, 0))).normalized(), pron=95, flex=10)
            _hand(P, s, hands or "clasped")
        _apply_head(P, head or "bowed")
    else:
        _spine_bend(P, bend=lean)
        for s in "LR":
            lat = _lateral(s)
            hip = P.head("upperleg01." + s)
            T = hip + Vector((lat.x * 0.04, -0.3 * h, 0.04 * h))
            _arm_ik(P, s, T, pole=(lat * 0.5 + Vector((0, 0.3, -1))).normalized(), pron=95, flex=-5)
            _hand(P, s, hands or "relaxed")
        _apply_head(P, head or "level")


def _flatten_foot_to(P, s, shin):
    """For kneeling: the foot points back along the ground with toes tucked."""
    P.bend_toward("foot." + s, -shin, math.radians(25))
    for i in range(1, 6):
        P.bend_toward("toe%d-1.%s" % (i, s), P.carry("foot." + s, UP), math.radians(55))


def _pose_prostrate(P, p, **k):
    # lying face down, arms stretched forward, forehead on the ground
    P.turn("root", bend=90, frame_of="root")
    _spine_bend(P, bend=-6)
    for s in "LR":
        lat = _lateral(s)
        t = P.carry("root", Vector((lat.x * 0.05, 0.02, -1)))
        _leg(P, s, t, P.carry("root", FWD), 6)
        P.bend_toward("foot." + s, P.carry("root", -UP), math.radians(35))
        u = P.carry("root", Vector((lat.x * 0.35, -0.1, 1)))
        _arm(P, s, u, P.carry("root", -FWD), 12, 170)
        _hand(P, s, "palm")
    _apply_head(P, "level", turn=0)
    P.turn("head", bend=12)


def _pose_arms_raised(P, p, spread=35.0, head="up", hands="open", **k):
    _spine_bend(P, bend=-5)
    _std_legs(P, knee=(3, 5))
    for s in "LR":
        lat = _lateral(s)
        a = math.radians(spread)
        u = Vector((lat.x * math.sin(a), -0.12, math.cos(a)))
        _arm(P, s, u, None, 18, 35, flex=-10, shrug=18)
        _hand(P, s, hands)
    _apply_head(P, head, amount=0.6)


def _pose_point(P, p, target=None, side="auto", **k):
    _pose_stand(P, p, relaxed=True)
    tgt = Vector(target) if target is not None else P.head("head") + Vector((0, -2, 1))
    if side == "auto":
        side = "L" if tgt.x > 0.15 else "R"
    s = _side(side)
    S = P.head("upperarm01." + s)
    d = (tgt - S).normalized()
    T = S + d * (P.an["ua_len" + s] + P.an["fa_len" + s] + 0.04) * 0.97
    _arm_ik(P, s, T, pole=Vector((_lateral(s).x, 0.4, -1)), pron=85, shrug=6)
    _hand(P, s, "point")
    _look_pose(P, tgt, amount=0.9)


def _pose_reach(P, p, target=None, side="auto", hand="open", **k):
    _pose_stand(P, p, relaxed=True)
    tgt = Vector(target) if target is not None else P.head("spine01") + Vector((0, -0.6, 0))
    if side == "auto":
        side = "L" if tgt.x > 0.15 else "R"
    s = _side(side)
    S = P.head("upperarm01." + s)
    reach = P.an["ua_len" + s] + P.an["fa_len" + s]
    D = tgt - S
    if D.length > reach * 1.05:   # lean towards it
        _spine_bend(P, bend=min(25, (D.length - reach) * 80))
    _arm_ik(P, s, tgt, pole=Vector((_lateral(s).x, 0.6, -1)), pron=60, shrug=8)
    _hand(P, s, hand)
    _look_pose(P, tgt, amount=0.8)


def _pose_cradle(P, p, **k):
    """Holding a baby at the chest: baby's head in the left elbow crook, left forearm under its back,
    right hand on the bundle. Use cradle_anchor(person) to place the swaddled baby."""
    h = p.height / 1.75
    _spine_bend(P, bend=5, side=-2)
    _std_legs(P, knee=(4, 8))
    chest = P.head("spine02")
    TL = chest + Vector((-0.13 * h, -0.26 * h, -0.13 * h))
    TR = chest + Vector((0.03 * h, -0.31 * h, 0.0))
    _arm_ik(P, "L", TL, pole=Vector((1, 0.25, -0.7)), pron=-15, flex=5)
    _arm_ik(P, "R", TR, pole=Vector((-1, 0.2, -0.9)), pron=75, flex=10)
    _hand(P, "L", "cup")
    _hand(P, "R", "cup")
    _apply_head(P, "down", amount=0.9, tilt=-6)
    P.cradle = (chest + Vector((-0.02 * h, -0.24 * h, -0.07 * h)))


def place_baby(baby, holder):
    """Lay a swaddled BABY person in the arms of a holder posed with 'cradle' (head in the holder's
    left elbow crook, face up towards the holder)."""
    loc, rot = cradle_anchor(holder)
    hm = holder.rig.matrix_world.to_3x3()
    head_dir = (hm @ Vector((1, 0.15, 0.12))).normalized()       # towards the holder's left elbow
    face_dir = (hm @ Vector((0, 0.35, 1))).normalized()          # up, slightly towards the holder
    side = face_dir.cross(head_dir).normalized()
    face_dir = head_dir.cross(side).normalized()
    # baby rig space: +Z = head, -Y = face
    R = Matrix((side, -face_dir, head_dir)).transposed()
    centre = baby.height * 0.42
    M = Matrix.Translation(loc - R @ Vector((0, 0, centre))) @ R.to_4x4()
    baby.rig.matrix_world = M
    baby.update()
    return M


def cradle_anchor(person):
    """World (location, rotation_euler) for a swaddled baby held in the 'cradle' pose: the bundle's
    local +X points to its head (towards the holder's left elbow), +Z up."""
    p = person
    P = p._pose
    loc = getattr(P, "cradle", None)
    if loc is None:
        loc = P.head("spine02") + Vector((0, -0.24, -0.07))
    mw = p.rig.matrix_world
    yaw = mw.to_euler().z
    return mw @ loc, Euler((math.radians(-12), 0, yaw + math.radians(12)))


def _pose_baby(P, p, **k):
    _spine_bend(P, bend=8)
    for s in "LR":
        lat = _lateral(s)
        _arm(P, s, Vector((lat.x * 0.3, -0.25, -1)), UP, 120, 40)
        _hand(P, s, "fist", 0.7)
        _leg(P, s, Vector((lat.x * 0.15, -0.35, -1)), FWD + lat * 0.3, 40)


def _pose_mourn(P, p, **k):
    h = p.height / 1.75
    _spine_bend(P, bend=10, side=2)
    _std_legs(P, knee=(5, 10))
    chin = P.head("head") + Vector((0, -0.11 * h, -0.075 * h))
    for s in "LR":
        lat = _lateral(s)
        T = chin + lat * 0.012 + Vector((0, -0.02, -0.03))
        _arm_ik(P, s, T, pole=(lat * 0.4 - UP + Vector((0, 0.3, 0))).normalized(), pron=100, flex=15, shrug=6)
        _hand(P, s, "clasped")
    _apply_head(P, "down", amount=0.5, tilt=8)


def _pose_crouch(P, p, throw=0.0, **k):
    """Deep squat on the balls of the feet (soldier rolling dice). throw 0..1 extends the right hand."""
    h = p.height / 1.75
    _spine_bend(P, bend=30)
    for s in "LR":
        lat = _lateral(s)
        t = Vector((lat.x * 0.45, -0.95, -0.3))
        sh = _leg(P, s, t, (FWD + lat * 0.4), 145)
        _flatten_foot(P, s, pitch_extra=-12)
        for i in range(1, 6):
            P.bend_toward("toe%d-1.%s" % (i, s), P.carry("foot." + s, UP), math.radians(40))
    knee = P.head("lowerleg01.L")
    _arm_ik(P, "L", knee + Vector((-0.02, -0.06, 0.04)), pole=Vector((1, 0.3, -0.3)), pron=90)
    _hand(P, "L", "relaxed")
    T = P.head("spine03") + Vector((-0.05, -0.45 - 0.15 * throw, -0.45 * h))
    _arm_ik(P, "R", T, pole=Vector((-1, 0.4, -0.5)), pron=100 - 60 * throw, flex=-10 * throw)
    _hand(P, "R", "cup" if throw > 0.5 else "fist", 0.8)
    _apply_head(P, "down", amount=0.6)


def _pose_hammer(P, p, phase="raise", **k):
    """Right hand swings a hammer (phase 'raise' | 'strike'); left hand holds a spike low in front."""
    h = p.height / 1.75
    _std_legs(P, knee=(12, 8), spread=0.07)
    sh = P.head("upperarm01.R")
    if phase == "strike":
        _spine_bend(P, bend=28, twist=-10)
        T = sh + Vector((0.18, -0.55 * h, -0.55 * h))
        _arm_ik(P, "R", T, pole=Vector((-1, 0.3, -0.4)), pron=70, flex=10, shrug=4)
    else:
        _spine_bend(P, bend=-8, twist=-22)
        T = sh + Vector((-0.08, 0.05, 0.42 * h))
        _arm_ik(P, "R", T, pole=Vector((-1, 0.1, 0.25)), pron=60, flex=-25, shrug=20)
    _hand(P, "R", "grip")
    T2 = P.head("spine02") + Vector((0.12, -0.42 * h, -0.42 * h))
    _arm_ik(P, "L", T2, pole=Vector((1, 0.2, -0.6)), pron=90)
    _hand(P, "L", "grip", 0.8)
    _apply_head(P, "down", amount=0.5)


def _pose_sit(P, p, seat_z=None, **k):
    h = p.height / 1.75
    _spine_bend(P, bend=8)
    for s in "LR":
        lat = _lateral(s)
        _leg(P, s, Vector((lat.x * 0.12, -1, -0.08)), UP + lat * 0.15, 92)
        _flatten_foot(P, s)
        knee = P.head("lowerleg01." + s)
        _arm_ik(P, s, knee + Vector((0, 0.06, 0.04)), pole=Vector((lat.x, 0.5, -1)), pron=95)
        _hand(P, s, "relaxed")
    _apply_head(P, "level")


def _pose_staff(P, p, head="level", side="R", lean=6.0, **k):
    """Standing, holding the staff (make_staff / spec staff=True) planted on the ground beside the foot."""
    h = p.height / 1.75
    s = _side(side)
    o = "L" if s == "R" else "R"
    lat = _lateral(s)
    _hips_shift(P, dx=-lat.x * 0.010 * h)
    _spine_bend(P, bend=4, side=2 * lat.x)
    _std_legs(P, knee=(4, 9) if s == "R" else (9, 4), spread=0.045, out=6)
    S = P.head("upperarm01." + s)
    T = S + Vector((lat.x * 0.13 * h, -0.20 * h, -0.36 * h))
    want = (UP + lat * math.tan(math.radians(lean)) * 0.4 + FWD * math.tan(math.radians(lean)) * 0.2).normalized()
    _staff_arm(P, s, T, pole=(lat * 1.0 + Vector((0, 0.3, -0.8))).normalized(), want=want)
    lo = _lateral(o)
    _arm(P, o, Vector((lo.x * 0.12, 0.03, -1)), FWD, 16, 80)
    _hand(P, o, k.get("hands", "relaxed"))
    _apply_head(P, head, tilt=2, turn=k.get("turn", 0))


def _pose_staff_raised(P, p, head="up", side="R", reach=1.0, **k):
    """Moses at the sea: staff held high in the right hand, the other hand stretched out, palm down."""
    h = p.height / 1.75
    s = _side(side)
    o = "L" if s == "R" else "R"
    lat, lo = _lateral(s), _lateral(o)
    _hips_shift(P, dy=0.01 * h)
    _spine_bend(P, bend=-7, side=-3 * lat.x, twist=4 * lat.x)
    _std_legs(P, knee=(6, 10), spread=0.07, out=8)
    S = P.head("upperarm01." + s)
    u = Vector((lat.x * 0.32, -0.42 * reach, 0.85)).normalized()
    T = S + u * (P.an["ua_len" + s] + P.an["fa_len" + s]) * 0.93
    want = Vector((lat.x * 0.18, -0.30, 1.0)).normalized()
    _staff_arm(P, s, T, pole=(lat + Vector((0, 0.3, -0.6))).normalized(), want=want, shrug=16)
    uo = Vector((lo.x * 0.55, -0.80, 0.18)).normalized()
    _arm(P, o, uo, None, 12, 175, flex=-18, shrug=8)
    _hand(P, o, "open")
    _apply_head(P, head, amount=0.55)


def _pose_walk_frame(P, p, ph, speed=1.0, lean=4.0, arm_amp=16.0, stride_amp=24.0):
    """One frame of a walk/run cycle at phase ph (radians)."""
    run = speed > 1.6
    _spine_bend(P, bend=lean + (10 if run else 0), twist=-math.sin(ph) * (5 if not run else 9))
    for s, off in (("L", 0.0), ("R", math.pi)):
        lat = _lateral(s)
        q = ph + off
        swing = math.sin(q) * stride_amp * (1.4 if run else 1.0)
        a = math.radians(swing)
        t = Vector((lat.x * 0.03, -math.sin(a), -math.cos(a)))
        # knee: stance ~5-15, swing up to 60 (run 100)
        kn = 6 + 8 * max(0, math.sin(q + 0.9)) + (55 if not run else 95) * max(0.0, math.sin(q - 0.6)) ** 2
        _leg(P, s, t, FWD + lat * 0.06, kn)
        _flatten_foot(P, s, pitch_extra=-12 * max(0.0, math.sin(q - 0.3)))
        ar = math.radians(-math.sin(q) * arm_amp * (1.6 if run else 1.0))
        u = Vector((lat.x * 0.12, math.sin(ar), -math.cos(ar)))
        _arm(P, s, u, FWD, (18 if not run else 85) + 12 * max(0, -math.sin(q)), 80)
        _hand(P, s, "relaxed" if not run else "fist", 0.6 if run else 1.0)
    _apply_head(P, "level", amount=0)
    P.turn("head", bend=-lean * 0.6)


POSES = {
    "rest": lambda P, p, **k: None,
    "stand": lambda P, p, **k: _pose_stand(P, p, False, **k),
    "stand_relaxed": lambda P, p, **k: _pose_stand(P, p, True, **k),
    "crucified": _pose_crucified,
    "kneel": lambda P, p, **k: _pose_kneel(P, p, "kneel", **k),
    "kneel_pray": lambda P, p, **k: _pose_kneel(P, p, "kneel_pray", **k),
    "kneel_bow": lambda P, p, **k: _pose_kneel(P, p, "kneel_bow", **k),
    "prostrate": _pose_prostrate,
    "arms_raised": _pose_arms_raised,
    "point": _pose_point,
    "reach": _pose_reach,
    "cradle": _pose_cradle,
    "baby": _pose_baby,
    "mourn": _pose_mourn,
    "crouch": _pose_crouch,
    "hammer": _pose_hammer,
    "sit": _pose_sit,
    "staff": _pose_staff,
    "staff_raised": _pose_staff_raised,
    "walk": lambda P, p, phase=0.0, **k: _pose_walk_frame(P, p, phase, 1.0),
    "run": lambda P, p, phase=0.0, **k: _pose_walk_frame(P, p, phase, 2.2),
}


def _to_rig_space(p, v):
    if v is None:
        return None
    return p.rig.matrix_world.inverted() @ Vector(v)


def _build_pose(p, name, params):
    P = _Pose(p)
    k = dict(params)
    for key in ("target", "rock"):
        if k.get(key) is not None:
            k[key] = _to_rig_space(p, k[key])
    if k.get("hand_targets"):
        k["hand_targets"] = {s: _to_rig_space(p, v) for s, v in k["hand_targets"].items()}
    if k.get("feet_targets"):
        k["feet_targets"] = {s: _to_rig_space(p, v) for s, v in k["feet_targets"].items()}
    fn = POSES[name]
    fn(P, p, **{kk: vv for kk, vv in k.items() if kk not in ("ground_z", "ground", "look")})
    if k.get("look") is not None:
        _look_pose(P, _to_rig_space(p, k["look"]))
    return P


def _lbs_prep(p, step=3):
    if getattr(p, "_lbs", None) is not None:
        return p._lbs
    me = p.body.data
    idx = np.nonzero(p._w["body"] > 0.5)[0][::step]
    names = [b.name for b in p.rig.data.bones]
    bidx = {n: i for i, n in enumerate(names)}
    gname = {g.index: g.name for g in p.body.vertex_groups}
    W = np.zeros((len(idx), len(names)), np.float32)
    verts = me.vertices
    for r, vi in enumerate(idx):
        for g in verts[vi].groups:
            j = bidx.get(gname.get(g.group))
            if j is not None:
                W[r, j] = g.weight
    W /= np.maximum(W.sum(1, keepdims=True), 1e-6)
    used = np.nonzero(W.sum(0) > 0)[0]
    p._lbs = (idx, W, names, np.c_[p._co[idx], np.ones(len(idx))], used)
    return p._lbs


def lbs_points(p, P=None):
    """Fast linear-blend-skinned body sample points (~1/3 of the body vertices) for pose state P
    (default: last pose), in rig space. Used for grounding and contact queries."""
    P = P or p._pose or _Pose(p)
    idx, W, names, hom, used = _lbs_prep(p)
    out = np.zeros((len(hom), 3))
    for j in used:
        n = names[j]
        M = np.array(P.pm(n) @ P.rest[n].inverted())
        w = W[:, j]
        m = w > 0
        out[m] += w[m, None] * (hom[m] @ M.T)[:, :3]
    return out


def _mesh_min_z(p):
    dg = bpy.context.evaluated_depsgraph_get()
    ob = p.body.evaluated_get(dg)
    me = ob.to_mesh()
    co = np.zeros(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    ob.to_mesh_clear()
    return float(co.reshape(-1, 3)[:, 2].min()) if len(co) else 0.0


GROUNDED = {"stand", "stand_relaxed", "kneel", "kneel_pray", "kneel_bow", "prostrate", "arms_raised", "point", "reach",
            "cradle", "mourn", "crouch", "hammer", "walk", "run", "rest", "sit", "staff", "staff_raised"}


DRAPE_POSES = {"crouch", "sit", "kneel", "kneel_pray", "kneel_bow", "prostrate"}
AUTO_DRAPE = True          # pose(): cloth-settle skirts of hero people in DRAPE_POSES (see pose(drape=...))
_REST_CO = {}


def _skirt_garments(p):
    return [g for g in p.garments if g.type == "MESH" and "skirt_below" in g and
            not any(k in str(g.get("wardrobe", g.name)) for k in ("loincloth", "swaddle", "lorica"))]


def drape_skirts(person, ground_z=None, frames=22, ramp=14):
    """Cloth-settle the person's skirted garments (tunic / robe / mantle / cape) on the CURRENT static pose
    with lib.wardrobe.drape (body + floor collision, result inverse-skinned so it stays rigged).
    pose() calls it automatically for hero people in DRAPE_POSES. ~30-90 s per person on this CPU."""
    p = person
    gs = _skirt_garments(p)
    if not gs:
        return []
    from . import wardrobe as W
    for g in gs:
        k = g.as_pointer()
        if k not in _REST_CO:
            co = np.zeros(len(g.data.vertices) * 3, np.float32)
            g.data.vertices.foreach_get("co", co)
            _REST_CO[k] = co
    gz = p.rig.matrix_world.translation.z if ground_z is None else ground_z
    # wardrobe.drape drops the visibility masks (skin under clothes, inner layers under outer ones) of the
    # body and the draped garments; above the skirts the cloth is pinned, so those masks are restored there
    zcut = max(float(g["skirt_below"]) for g in gs) + 0.03
    saved = {}
    for o in [p.body] + [g for g in p.garments if g.type == "MESH"]:
        vg = o.vertex_groups.get("wardrobe_hide")
        if vg is None or o.modifiers.get("WardrobeHide") is None:
            continue
        gi = vg.index
        idx = np.array([v.index for v in o.data.vertices if any(x.group == gi and x.weight > 0.5 for x in v.groups)], np.int64)
        if len(idx):
            co = p._co if o == p.body else _coords(o.data)
            saved[o] = idx[co[idx, 2] > zcut]
    # only the skirts settle: everything above the skirt line is pinned to its skinned shape (a free upper body
    # let the tunic's sleeves/shoulders drift through the mail shirt or mantle during the settle)
    for g in gs:
        if g.vertex_groups.get("pin") is None:
            W.auto_pin(p, g)
        vg = g.vertex_groups["pin"]
        co = _coords(g.data)
        zb = float(g["skirt_below"])
        w = np.clip((co[:, 2] - (zb - 0.08)) / 0.10, 0.0, 1.0)
        cur = np.zeros(len(co), np.float32)
        gi = vg.index
        for v in g.data.vertices:
            for x in v.groups:
                if x.group == gi:
                    cur[v.index] = x.weight
        w = np.maximum(w, cur)
        q = np.round(w, 2)
        for val in np.unique(q):
            if val > 0:
                vg.add(np.nonzero(q == val)[0].tolist(), float(val), "REPLACE")
    t = time.time()
    out = W.drape(p, gs, frames=frames, ramp=ramp, ground=gz, verbose=False)
    for o, idx in saved.items():
        if o.modifiers.get("WardrobeHide") is not None or not len(idx):
            continue
        vg = o.vertex_groups.get("wardrobe_hide")
        if vg is not None:
            o.vertex_groups.remove(vg)
        if o == p.body:
            W.hide_body(p, idx)
        else:
            W.hide_verts(o, idx)
    if saved:
        _protect_beard_region(p)
    p._draped = True
    _log("drape_skirts %s %d garments %.1fs" % (p.name, len(out), time.time() - t))
    return out


def _undrape(p):
    """Restore the fitted (standing) rest shape of garments draped for an earlier pose."""
    if not getattr(p, "_draped", False):
        return
    for g in _skirt_garments(p):
        co = _REST_CO.get(g.as_pointer())
        if co is not None and len(co) == len(g.data.vertices) * 3:
            g.data.vertices.foreach_set("co", co)
            g.data.update()
    p._draped = False


def pose(person, name, ground_z=None, ground=True, drape="auto", **params):
    """Static pose. name in POSES; params per pose (head, strain, target, side, hands, rock, look...).
    ground: keep the lowest body point on ground_z (world z; default = the rig's own origin height).
    drape: 'auto' = cloth-settle the skirts (drape_skirts) when the person is lod 'hero', dressed and the pose
    is in DRAPE_POSES (crouch / sit / kneel* / prostrate: skinned skirts balloon there); True / False force it.
    A later standing pose restores the fitted garments. Returns the internal pose state."""
    p = person
    p.update()   # refresh matrix_world after the caller moved the rig (grounding reads it)
    P = _build_pose(p, name, params)
    if ground and name in GROUNDED:
        _ground(p, P, ground_z, write=False)
    P.write()
    p._pose = P
    p._pose_name = name
    _apply_face_bones(p)
    if getattr(p, "staff", None) is not None:
        hold_staff(p, ground_z=ground_z)
    p.update()
    if drape == "auto":
        drape = AUTO_DRAPE and name in DRAPE_POSES and p.spec.get("lod") == "hero"
    if getattr(p, "_draped", False):
        _undrape(p)
        p.update()
    if drape and p.garments:
        try:
            drape_skirts(p, ground_z)
        except Exception as e:     # never fail a pose on the cloth settle
            _log("drape failed for %s: %s" % (p.name, e))
        p.update()
    return P


def _ground(p, P, ground_z=None, frame=None, write=True):
    """Shift the root so the lowest skinned body point sits on ground_z (world; default rig origin)."""
    mw = p.rig.matrix_world
    gz_local = 0.0 if ground_z is None else (ground_z - mw.translation.z)
    pts = lbs_points(p, P)
    R = np.array(mw.to_3x3())
    zw = pts @ R[2]                       # world-z component of rig-space points (rotation only)
    mz = float(zw.min())
    dz = gz_local - mz
    P.loc += mw.to_3x3().inverted() @ Vector((0, 0, dz))
    P._c.clear()
    if write:
        P.write(frame=frame, bones=["root"])


def key_pose(person, frame, name, ground_z=None, ground=True, **params):
    """Keyframe a pose at frame (all body bones + root location); poses blend with Bezier easing
    between keys. Returns the pose state."""
    p = person
    sc = bpy.context.scene
    p.update()   # refresh matrix_world after the caller moved the rig (grounding reads it)
    P = _build_pose(p, name, params)
    if ground and name in GROUNDED:
        _ground(p, P, ground_z, write=False)
    P.write(frame=frame)
    p._pose = P
    _pose_cache(p)[int(frame)] = P
    return P


def _pose_cache(p):
    if not hasattr(p, "_pose_at"):
        p._pose_at = {}
    return p._pose_at


def rotate_bone(person, bone, rot_deg, frame=None, mode="LOCAL"):
    """Low-level: set a bone's rotation (Euler XYZ degrees in the bone's local space, relative to rest).
    mode 'ADD' composes with the current rotation."""
    pb = person.rig.pose.bones[bone]
    q = Euler([math.radians(a) for a in rot_deg], "XYZ").to_quaternion()
    if mode.upper() == "ADD":
        q = pb.rotation_quaternion @ q
    pb.rotation_quaternion = q
    if frame is not None:
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=bone)
    return pb


def _look_pose(P, target, amount=1.0, eyes=True):
    """Aim neck + head at target (armature space)."""
    if target is None:
        return
    target = Vector(target)
    chain = NECK + ["head"]
    wts = [0.18, 0.18, 0.22, 0.42]
    for i, n in enumerate(chain):
        hp = (P.head("head") + P.tail("head")) * 0.5
        fwd = P.carry("head", FWD)
        want = (target - hp).normalized()
        q = fwd.rotation_difference(want)
        ang = q.angle * amount * wts[i] / sum(wts[i:])
        # limit: yaw 70, pitch 45 overall
        ax = q.axis
        P.rotate(n, ax, min(ang, math.radians(40)))
    P._look_target = target


def look_at(person, world_point, frame=None, amount=1.0, eyes=True):
    """Turn neck+head (and eyes) towards a world point. Works on top of the last pose (or the pose
    keyed at `frame`)."""
    p = person
    cache = _pose_cache(p)
    base = cache.get(int(frame)) if frame is not None else None
    P = (base or p._pose or _Pose(p)).copy()
    tgt = _to_rig_space(p, world_point)
    _look_pose(P, tgt, amount)
    P.write(frame=frame, bones=NECK + ["head"])
    if frame is not None:
        cache[int(frame)] = P
    p._pose = P
    if eyes:
        p.update()
        eyes_look(p, world_point, frame=frame)
    return P


# --------------------------------------------------------------------------------------------
# Animated helpers
# --------------------------------------------------------------------------------------------
def walk(person, points, f0, f1, speed=None, run=False, ground_z=None, step=1, height_fn=None):
    """Procedural walk (or run) along world points [(x,y[,z]), ...] from frame f0 to f1.
    The person faces along the path. height_fn(x, y) -> ground z (optional terrain)."""
    p = person
    pts = [Vector((q[0], q[1], q[2] if len(q) > 2 else (ground_z or 0.0))) for q in points]
    seg = [(pts[i + 1] - pts[i]).length for i in range(len(pts) - 1)]
    total = sum(seg) or 1e-6
    legl = p.height * 0.5
    stride = legl * (1.35 if not run else 2.4)        # metres per full cycle (2 steps)
    rig = p.rig
    prev_yaw = None
    # ground offset from a standing pose
    P0 = _build_pose(p, "stand", {})
    mz = float(lbs_points(p, P0)[:, 2].min())
    f = f0
    while f <= f1:
        u = (f - f0) / max(1, f1 - f0)
        d = u * total
        i = 0
        while i < len(seg) - 1 and d > seg[i]:
            d -= seg[i]
            i += 1
        a, b = pts[i], pts[min(i + 1, len(pts) - 1)]
        tt = d / seg[i] if seg[i] > 0 else 0
        pos = a.lerp(b, min(1, tt))
        if height_fn:
            pos.z = height_fn(pos.x, pos.y)
        dirv = (b - a)
        yaw = math.atan2(dirv.x, -dirv.y) if dirv.length > 1e-6 else (prev_yaw or 0.0)
        if prev_yaw is not None:
            while yaw - prev_yaw > math.pi:
                yaw -= 2 * math.pi
            while yaw - prev_yaw < -math.pi:
                yaw += 2 * math.pi
        prev_yaw = yaw
        ph = (u * total) / stride * 2 * math.pi
        P = _Pose(p)
        _pose_walk_frame(P, p, ph, 2.2 if run else 1.0)
        bob = (0.012 if not run else 0.035) * abs(math.cos(ph)) - 0.006
        P.loc.z += -mz + bob
        P.write(frame=f)
        rig.location = pos
        rig.rotation_euler = (0, 0, yaw)
        rig.keyframe_insert("location", frame=f)
        rig.keyframe_insert("rotation_euler", frame=f)
        f += step
    C._set_interp(rig, "location", "LINEAR")


def run(person, points, f0, f1, **k):
    return walk(person, points, f0, f1, run=True, **k)


def _osc_keys(person, bones_axes, f0, f1, freq, amp_fn, base=None):
    p = person
    P0 = (base or p._pose or _Pose(p))
    f = f0
    while f <= f1:
        P = P0.copy()
        t = (f - f0) / 24.0
        for n, (bend, side, twist) in bones_axes.items():
            a = amp_fn(f) * math.sin(2 * math.pi * freq * t)
            P.turn(n, bend=bend * a, side=side * a, twist=twist * a)
        P.write(frame=f, bones=list(bones_axes.keys()))
        f += 2


def head_shake(person, f0, f1, amount=1.0, freq=1.6):
    """Animated 'no' head shake (mockery) between frames f0..f1."""
    env = lambda f: amount * math.sin(math.pi * min(1, max(0, (f - f0) / max(1, f1 - f0))))
    _osc_keys(person, {"neck02": (0, 0, 10), "neck03": (0, 0, 10), "head": (0, 2, 14)}, f0, f1, freq, env)


def nod(person, f0, f1, amount=1.0, freq=1.2):
    env = lambda f: amount * math.sin(math.pi * min(1, max(0, (f - f0) / max(1, f1 - f0))))
    _osc_keys(person, {"neck03": (8, 0, 0), "head": (12, 0, 0)}, f0, f1, freq, env)


def laugh(person, f0, f1, amount=1.0, freq=3.2):
    """Laughing body bounce (+ laugh expression keys)."""
    env = lambda f: amount * (0.6 + 0.4 * math.sin(math.pi * min(1, max(0, (f - f0) / max(1, f1 - f0)))))
    _osc_keys(person, {"spine02": (4, 0, 0), "spine01": (5, 0, 0), "neck03": (-4, 0, 0), "head": (-8, 0, 0),
                       "clavicle.L": (0, 3, 0), "clavicle.R": (0, -3, 0)}, f0, f1, freq, env)
    expression(person, "laugh", 0.0, frame=f0 - 4)
    expression(person, "laugh", amount, frame=f0 + 4)
    expression(person, "laugh", amount, frame=f1 - 4)
    expression(person, "laugh", 0.0, frame=f1 + 6)


# ============================================================================================
# Faces: expression units (MakeHuman expression targets) + jaw + eyes
# ============================================================================================
UNITS = ["eye-left-closure", "eye-left-opened-up", "eye-left-slit", "eye-right-closure", "eye-right-opened-up", "eye-right-slit",
         "eyebrows-left-down", "eyebrows-left-extern-up", "eyebrows-left-inner-up", "eyebrows-left-up",
         "eyebrows-right-down", "eyebrows-right-extern-up", "eyebrows-right-inner-up", "eyebrows-right-up",
         "mouth-compression", "mouth-corner-puller", "mouth-depression-retraction", "mouth-depression", "mouth-elevation",
         "mouth-eversion", "mouth-open", "mouth-parling", "mouth-part-later", "mouth-protusion", "mouth-pursing",
         "mouth-retraction", "mouth-upward-retraction", "neck-platysma", "nose-compression", "nose-depression",
         "nose-left-dilatation", "nose-left-elevation", "nose-right-dilatation", "nose-right-elevation"]

# 'both' shorthands: eye-*, eyebrows-*, nose-* without side apply to left and right
EXPRESSIONS = {
    "neutral": {},
    "anguish": {"eyebrows-inner-up": 0.95, "eyebrows-down": 0.3, "eye-slit": 0.35, "nose-elevation": 0.3,
                "mouth-depression": 0.22, "mouth-open": 0.07, "neck-platysma": 0.3, "jaw": 6},
    "sorrow": {"eyebrows-inner-up": 0.8, "eye-slit": 0.12, "eye-closure": 0.12, "mouth-depression": 0.55,
               "mouth-compression": 0.15},
    "crying": {"eyebrows-inner-up": 1.0, "eyebrows-down": 0.2, "eye-slit": 0.55, "nose-elevation": 0.35,
               "mouth-depression-retraction": 0.35, "mouth-depression": 0.3, "mouth-open": 0.08, "neck-platysma": 0.4, "jaw": 4},
    "peace": {"eye-closure": 0.12, "eyebrows-up": 0.08, "mouth-corner-puller": 0.3},
    "smile": {"eye-slit": 0.25, "mouth-corner-puller": 0.6, "mouth-elevation": 0.1},
    "sneer": {"nose-left-elevation": 0.7, "mouth-upward-retraction": 0.22, "eyebrows-down": 0.45, "eye-slit": 0.3,
              "eyebrows-left-extern-up": 0.35, "mouth-corner-puller": 0.1},
    "mock": {"nose-left-elevation": 0.45, "mouth-corner-puller": 0.5, "mouth-upward-retraction": 0.2, "eye-slit": 0.4,
             "eyebrows-left-up": 0.4, "mouth-open": 0.12, "jaw": 4},
    "laugh": {"mouth-corner-puller": 1.0, "mouth-open": 0.35, "eye-slit": 0.55, "nose-elevation": 0.2,
              "eyebrows-up": 0.15, "jaw": 12},
    "cry_out": {"mouth-open": 0.6, "eyebrows-inner-up": 1.0, "eyebrows-down": 0.25, "eye-slit": 0.45,
                "mouth-retraction": 0.25, "nose-elevation": 0.3, "neck-platysma": 0.6, "jaw": 20},
    "awe": {"eyebrows-up": 0.6, "eyebrows-inner-up": 0.3, "eye-opened-up": 0.4, "mouth-open": 0.04, "jaw": 9},
    "anger": {"eyebrows-down": 1.0, "eye-slit": 0.3, "nose-elevation": 0.4, "mouth-compression": 0.5},
    "fear": {"eyebrows-inner-up": 0.8, "eyebrows-up": 0.5, "eye-opened-up": 0.6, "mouth-retraction": 0.3,
             "mouth-open": 0.08, "jaw": 7},
    "pain": {"eyebrows-inner-up": 0.7, "eyebrows-down": 0.6, "eye-closure": 0.45, "eye-slit": 0.5, "nose-elevation": 0.45,
             "mouth-retraction": 0.3, "mouth-open": 0.04, "neck-platysma": 0.5, "jaw": 4},
    "exhausted": {"eye-closure": 0.6, "eyebrows-inner-up": 0.35, "mouth-open": 0.06, "jaw": 7},
    "dead": {"eye-closure": 0.9, "mouth-open": 0.05, "jaw": 9},
    "sleep": {"eye-closure": 1.0, "mouth-corner-puller": 0.1},
}


def _expand_units(d):
    out = {}
    for k, v in d.items():
        if k == "jaw":
            continue
        if k in UNITS:
            out[k] = out.get(k, 0) + v
            continue
        head, rest = k.split("-", 1)
        hits = [u for u in ("%s-left-%s" % (head, rest), "%s-right-%s" % (head, rest)) if u in UNITS]
        if not hits:
            _log("unknown expression unit", k)
        for u in hits:
            out[u] = out.get(u, 0) + v
    return out


def _unit_race(p):
    sk = ETHNICITY.get(p.spec["ethnicity"], ETHNICITY["judean"])["skin"]
    return {"african": "african", "asian": "asian"}.get(sk, "caucasian")


def _proxy_maps(p):
    """mhclo correspondence for proxies that must follow face shape keys (brows, lashes)."""
    if getattr(p, "_pmaps", None) is not None:
        return p._pmaps
    M = _mpfb()
    p._pmaps = {}
    for key, kind in (("eyebrows", "eyebrows"), ("eyelashes", "eyelashes")):
        o = p.parts.get(key)
        if not o:
            continue
        name = p.spec["eyebrows"] if key == "eyebrows" else ("eyelashes01" if p.spec["gender"] >= 0.5 else "eyelashes02")
        path = _asset_path(kind, name)
        mh = M["Mhclo"]()
        mh.load(path)
        n = len(o.data.vertices)
        idx = np.zeros((n, 3), np.int32)
        wt = np.zeros((n, 3), np.float32)
        for vi, mp in mh.verts.items():
            if vi < n:
                idx[vi] = mp["verts"]
                wt[vi] = mp["weights"]
        p._pmaps[key] = (o, idx, wt)
    return p._pmaps


def _ensure_units(p, units):
    TS = _mpfb()["TS"]
    body = p.body
    new = [u for u in units if u not in p.expr_keys]
    if not new:
        return
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis", from_mix=False)
    race = _unit_race(p)
    basis = _coords(body.data)
    pm = _proxy_maps(p)
    for u in new:
        path = os.path.join(MPFB_SYS, "targets", "expression", "units", race, u + ".target.gz")
        kb = TS.load_target(body, path, weight=0.0, name="ex-" + u)
        p.expr_keys[u] = kb.name
        co = np.zeros(len(basis) * 3, np.float32)
        kb.data.foreach_get("co", co)
        delta = co.reshape(-1, 3) - basis
        for key, (o, idx, wt) in pm.items():
            if o.data.shape_keys is None:
                o.shape_key_add(name="Basis", from_mix=False)
            pk = o.shape_key_add(name="ex-" + u, from_mix=False)
            pc = _coords(o.data)
            pd = (delta[idx] * wt[:, :, None]).sum(1)
            pk.data.foreach_set("co", (pc + pd).astype(np.float32).ravel())
            pk.value = 0.0


def _shape_objects(p):
    out = [p.body]
    for key in ("eyebrows", "eyelashes"):
        if key in p.parts and p.parts[key].data.shape_keys:
            out.append(p.parts[key])
    return out


def _set_units(p, weights, frame=None, only=None):
    _ensure_units(p, [u for u, w in weights.items() if w > 0.0])
    for o in _shape_objects(p):
        if o.data.shape_keys is None:
            continue
        kbs = o.data.shape_keys.key_blocks
        for u in p.expr_keys:
            if only is not None and u not in only:
                continue
            kb = kbs.get("ex-" + u)
            if kb is None:
                continue
            kb.slider_min = -1.0
            kb.value = max(-1.0, min(1.0, weights.get(u, 0.0)))
            if frame is not None:
                kb.keyframe_insert("value", frame=frame)


def _jaw_q(p, deg):
    pb = p.rig.pose.bones["jaw"]
    b = pb.bone
    axis_local = b.matrix_local.to_3x3().inverted() @ LEFT
    q = Quaternion(axis_local, math.radians(deg))
    # sign check: the tail (chin) must move down
    t0 = b.matrix_local @ Vector((0, b.length, 0))
    t1 = b.matrix_local @ (q.to_matrix().to_4x4() @ Vector((0, b.length, 0)))
    if t1.z > t0.z and deg > 0:
        q = Quaternion(axis_local, -math.radians(deg))
    return q


def expression(person, name="neutral", weight=1.0, frame=None, extra=None):
    """Set a facial expression (name in EXPRESSIONS or a dict of units, incl. 'jaw': deg).
    weight scales it; frame keys it (blend between keys over time). extra: dict added on top."""
    p = person
    d = dict(EXPRESSIONS.get(name, {}) if isinstance(name, str) else name)
    if extra:
        for k, v in extra.items():
            d[k] = d.get(k, 0) + v
    units = _expand_units(d)
    units = {u: v * weight for u, v in units.items()}
    # keep blink/closure state outside of expressions? expressions own the closure keys too
    _set_units(p, units, frame)
    p._expr = units
    p._jaw = d.get("jaw", 0.0) * weight
    pb = p.rig.pose.bones["jaw"]
    pb.rotation_quaternion = _jaw_q(p, p._jaw)
    if frame is not None:
        pb.keyframe_insert("rotation_quaternion", frame=frame, group="jaw")
    return units


def _apply_face_bones(p):
    pb = p.rig.pose.bones["jaw"]
    pb.rotation_quaternion = _jaw_q(p, getattr(p, "_jaw", 0.0))


def eyes_closed(person, amount=1.0, frame=None):
    """Close both eyelids (0 open .. 1 shut), optionally keyed."""
    p = person
    w = dict(p._expr)
    for u in ("eye-left-closure", "eye-right-closure"):
        w[u] = amount
    _set_units(p, w, frame, only={"eye-left-closure", "eye-right-closure"})
    p._expr = w


def blink(person, frame, duration=5):
    """Key a natural blink centred on frame (lids return to the current expression)."""
    p = person
    base = p._expr.get("eye-left-closure", 0.0)
    eyes_closed(p, base, frame - duration // 2)
    eyes_closed(p, 1.0, frame)
    eyes_closed(p, base, frame + duration - duration // 2)


def eyes_look(person, target, frame=None, limit=28.0, up_limit=12.0, down_limit=22.0):
    """Aim both eyes at a world point (call after posing; uses the evaluated pose). Yaw is clamped to
    `limit`, pitch to up_limit / down_limit degrees (the lids do not follow the eyeball, so looking
    far up would hide the iris - tilt the head instead)."""
    p = person
    p.update()
    mw = p.rig.matrix_world
    tgt = mw.inverted() @ Vector(target)
    for s in "LR":
        pb = p.rig.pose.bones["eye." + s]
        b = pb.bone
        par = pb.parent
        M0 = par.matrix @ (par.bone.matrix_local.inverted() @ b.matrix_local)
        y0 = M0.to_3x3().col[1].normalized()
        want = (tgt - M0.translation).normalized()
        # clamp in the head frame: yaw about the head's up, pitch about its left axis
        Hm = p.rig.pose.bones["head"].matrix.to_3x3().normalized()
        hup, hleft = Hm @ (p.rig.pose.bones["head"].bone.matrix_local.to_3x3().inverted() @ UP), None
        hfwd = y0
        hleft = hup.cross(hfwd).normalized()
        hup = hfwd.cross(hleft).normalized()
        x, yv, z = want.dot(hleft), want.dot(hfwd), want.dot(hup)
        yaw = max(-math.radians(limit), min(math.radians(limit), math.atan2(x, yv)))
        pitch = math.atan2(z, math.hypot(x, yv))
        pitch = max(-math.radians(down_limit), min(math.radians(up_limit), pitch))
        want = (hfwd * math.cos(yaw) + hleft * math.sin(yaw)) * math.cos(pitch) + hup * math.sin(pitch)
        q = y0.rotation_difference(want.normalized())
        R = q.to_matrix() @ M0.to_3x3().normalized()
        basis = M0.to_3x3().normalized().inverted() @ R
        pb.rotation_quaternion = basis.to_quaternion()
        if frame is not None:
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)


# ============================================================================================
# Cross helper
# ============================================================================================
def _box_dims(o):
    co = _coords(o.data)
    return Vector(co.min(0)), Vector(co.max(0))


def place_on_cross(person, cross_root, head="up", strain=0.6, knee_side=1.0, hands="cross", feet_z=None):
    """Hang a person on a core.wooden_cross (root empty returned by C.wooden_cross): hands meet the front
    of the crossbeam, back against the upright, feet together/overlapping against the upright.
    Returns dict of world contact points {'hand_L','hand_R','foot_L','foot_R','nail_feet'}."""
    p = person
    up = beam = None
    for ch in cross_root.children:
        if ch.name.endswith("_upright"):
            up = ch
        elif ch.name.endswith("_beam"):
            beam = ch
    umin, umax = _box_dims(up)
    bmin, bmax = _box_dims(beam)
    y_u = up.location.y + umin.y            # front of the upright (cross-local)
    y_b = beam.location.y + bmin.y          # front of the beam
    z_b = beam.location.z
    half_beam = beam.location.x + bmax.x
    # pass 1: pose in rig space to measure the shoulders
    p.rig.matrix_world = Matrix.Identity(4)
    P1 = _Pose(p)
    _pose_crucified(P1, p, head=head, strain=strain, knee_side=knee_side)
    sc = p.height / 1.75
    th = math.radians(14 + 16 * max(0, min(1, strain)))
    R = {s: P1.an["ua_len" + s] + P1.an["fa_len" + s] + P1.an["hand_len" + s] * 0.5 for s in "LR"}
    S = {s: P1.head("upperarm01." + s) for s in "LR"}
    # the back of the torso (rest mesh) -> distance from the rig origin
    co = p._co
    torso = co[(co[:, 2] > 0.55 * p.height) & (co[:, 2] < 0.8 * p.height) & (np.abs(co[:, 0]) < 0.1 * sc) & (p._w["body"] > 0.5)]
    y_back = float(torso[:, 1].max())
    off_y = y_u - y_back - 0.008
    sz = (S["L"].z + S["R"].z) / 2
    off_z = z_b - (sz + R["L"] * math.sin(th) * 0.97)
    hand_half = 0.016 * sc
    ht = {}
    for s in "LR":
        x = S[s].x + _lateral(s).x * R[s] * math.cos(th) * 0.97
        x = max(-half_beam + 0.06, min(half_beam - 0.06, x))
        ht[s] = Vector((x, y_b - hand_half - off_y, z_b - off_z + 0.005))
    # feet: ankles in front of the upright, knees bent and turned to one side
    ank_rest = (P1.head("foot.L").z + P1.head("foot.R").z) / 2
    raise_ = (0.10 + 0.1 * strain) * sc if feet_z is None else (feet_z - off_z)
    fy = y_u - off_y - 0.07 * sc
    ft = {"L": Vector((0.03 * sc * knee_side, fy, ank_rest + raise_)),
          "R": Vector((0.005 * sc * knee_side, fy - 0.045 * sc, ank_rest + raise_ + 0.03 * sc))}
    P = _Pose(p)
    _pose_crucified(P, p, head=head, strain=strain, knee_side=knee_side, hands=hands,
                    hand_targets=ht, feet_targets=ft)
    p.rig.matrix_world = cross_root.matrix_world @ Matrix.Translation((0, off_y, off_z))
    P.write()
    p._pose = P
    p._pose_name = "crucified"
    _apply_face_bones(p)
    p.update()
    mw = p.rig.matrix_world
    return {"hand_L": mw @ P.head("wrist.L").lerp(P.tail("metacarpal2.L"), 0.5),
            "hand_R": mw @ P.head("wrist.R").lerp(P.tail("metacarpal2.R"), 0.5),
            "foot_L": mw @ P.head("foot.L"), "foot_R": mw @ P.head("foot.R"),
            "nail_feet": mw @ ((P.head("foot.L") + P.head("foot.R")) / 2 + Vector((0, -0.03, -0.04)))}


# ============================================================================================
# Baking & crowds
# ============================================================================================
def _objcolor_material(m):
    """Copy of a material whose Object Info colour (e.g. wardrobe fabrics: colour = obj.color) is
    replaced by the 'obj_rgb' colour attribute written at bake time."""
    if m is None or not m.use_nodes:
        return m
    oi = [n for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeObjectInfo" and n.outputs["Color"].is_linked]
    if not oi:
        return m
    name = m.name + ".baked"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    c = m.copy()
    c.name = name
    nt = c.node_tree
    for n in [n for n in nt.nodes if n.bl_idname == "ShaderNodeObjectInfo"]:
        at = nt.nodes.new("ShaderNodeAttribute")
        at.attribute_name = "obj_rgb"
        for l in list(n.outputs["Color"].links):
            nt.links.new(at.outputs["Color"], l.to_socket)
    return c


def bake_static(person, name=None, delete=True, coll=None, decimate=None):
    """Freeze a posed (and dressed) person into ONE mesh object (pose + modifiers applied, materials
    kept, world transform baked into the object transform = the rig's). Hair curves (beard) are kept
    as a child curves object with the deformation applied. Returns the mesh object."""
    p = person
    p.update()
    dg = bpy.context.evaluated_depsgraph_get()
    rig_mw = p.rig.matrix_world.copy()
    inv = rig_mw.inverted()
    coll = coll or (p.rig.users_collection[0] if p.rig.users_collection else bpy.context.scene.collection)
    temps = []
    curves = []
    for o in p.objects():
        if o.hide_render or o == p.rig:
            continue
        if o.type == "MESH":
            oe = o.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(oe, preserve_all_data_layers=True, depsgraph=dg)
            if len(me.vertices) == 0:
                bpy.data.meshes.remove(me)
                continue
            me.transform(inv @ o.matrix_world)
            # keep per-object colours (wardrobe fabrics use obj.color) as an attribute
            if any(m and m.use_nodes and any(n.bl_idname == "ShaderNodeObjectInfo" for n in m.node_tree.nodes) for m in me.materials):
                ca = me.color_attributes.new("obj_rgb", "FLOAT_COLOR", "POINT")
                ca.data.foreach_set("color", np.tile(np.array(o.color, np.float32), len(me.vertices)))
                for i, m in enumerate(me.materials):
                    me.materials[i] = _objcolor_material(m)
            t = bpy.data.objects.new(o.name + ".tmp", me)
            coll.objects.link(t)
            temps.append(t)
        elif o.type == "CURVES":
            curves.append(o)
    if not temps:
        return None
    base = temps[0]
    with bpy.context.temp_override(active_object=base, object=base, selected_objects=temps,
                                   selected_editable_objects=temps):
        bpy.ops.object.join()
    base.name = name or (p.name + ".baked")
    base.data.name = base.name
    base.matrix_world = rig_mw
    if decimate and decimate < 1.0:
        dm = base.modifiers.new("decimate", "DECIMATE")
        dm.ratio = decimate
        with bpy.context.temp_override(object=base, active_object=base):
            bpy.ops.object.modifier_apply(modifier=dm.name)
    keep = []
    for cobj in curves:
        oe = cobj.evaluated_get(dg)
        try:
            cv = oe.data.copy()
        except Exception:
            cv = None
        if cv is None:
            continue
        cv.surface = None
        nc = bpy.data.objects.new(cobj.name + ".baked", cv)
        coll.objects.link(nc)
        nc.parent = base
        nc.matrix_parent_inverse = Matrix.Identity(4)
        nc.matrix_basis = inv @ cobj.matrix_world
        keep.append(nc)
    if delete:
        delete_person(p)
    return base


def delete_person(person):
    objs = person.objects()
    for o in objs:
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass


def _instance(src, loc, yaw, scale, coll):
    o = src.copy()
    coll.objects.link(o)
    o.location = loc
    o.rotation_euler = (0, 0, yaw)
    o.scale = (scale, scale, scale)
    for ch in src.children:
        c = ch.copy()
        coll.objects.link(c)
        c.parent = o
    return o


class Crowd:
    def __init__(self):
        self.sources = []
        self.instances = []
        self.people = []
        self.collection = None

    def __repr__(self):
        return "<Crowd %d instances of %d variants>" % (len(self.instances), len(self.sources))


def crowd(n, positions=None, area=None, seed=0, variety=6, pose="stand_relaxed", pose_fn=None, lod="mid",
          presets=("CROWD_MAN", "CROWD_WOMAN"), face=None, yaw=None, yaw_jitter=25.0, ground_z=0.0, height_fn=None,
          spacing=0.65, name="Crowd", outfit=None, colors=None, women=0.4, hide_sources=True, **spec):
    """Build `variety` unique dressed people, bake them, and scatter n linked duplicates.
    positions: [(x,y[,z]), ...] or area=(cx, cy, width, depth[, angle_deg]); face: world point every
    instance turns towards (else yaw deg, else random); pose: name or list of names (random per
    variant) or pose_fn(person, i). lod 'near'|'mid'|'far'. Extra spec keys pass to make_person.
    Returns Crowd (.instances, .sources, .collection)."""
    rng = random.Random(seed)
    cr = Crowd()
    coll = C.collection(name)
    cr.collection = coll
    src_coll = C.collection(name + "_src")
    lodmap = {"near": "hero", "mid": "mid", "far": "far"}
    # unique people: a deterministic share of women (round(variety * women)), shuffled by the seed
    nw = int(round(variety * women)) if len(presets) > 1 else 0
    if len(presets) > 1 and women > 0 and variety >= 2:
        nw = max(1, min(variety - 1, nw)) if 0 < women < 1 else nw
    kinds = [1] * nw + [0] * (variety - nw)
    rng.shuffle(kinds)
    for i in range(variety):
        pr = presets[min(kinds[i], len(presets) - 1)]
        sp = dict(spec)
        sp.update(seed=seed * 100 + i, lod=lodmap.get(lod, lod), pose=None, expression=None)
        if outfit:
            sp["outfit"] = outfit
        if colors:
            sp["outfit_colors"] = colors[i % len(colors)] if isinstance(colors, list) else colors
        per = make_person("%s_v%d" % (name, i), pr, **sp)
        if pose_fn:
            pose_fn(per, i)
        else:
            pn = pose[i % len(pose)] if isinstance(pose, (list, tuple)) else pose
            if isinstance(pn, tuple):
                globals()["pose"](per, pn[0], **pn[1])
            elif pn:
                globals()["pose"](per, pn)
        ex = per.spec.get("expression")
        if ex and ex != "neutral" and lod != "far":
            expression(per, ex)
        b = bake_static(per, name="%s_src%d" % (name, i), coll=src_coll, decimate=0.4 if lod == "far" else None)
        if b is None:
            continue
        b.location = (0, 0, -500)   # sources live far below the set
        cr.sources.append(b)
    if hide_sources:
        for o in src_coll.all_objects:
            o.hide_render = True
            o.hide_viewport = True
    # placements
    pts = []
    if positions is not None:
        pts = [tuple(q) for q in positions][:n] if n else [tuple(q) for q in positions]
    elif area is not None:
        cx, cy, w, d = area[:4]
        ang = math.radians(area[4]) if len(area) > 4 else 0.0
        tries = 0
        while len(pts) < n and tries < n * 60:
            tries += 1
            lx, ly = (rng.random() - 0.5) * w, (rng.random() - 0.5) * d
            x = cx + lx * math.cos(ang) - ly * math.sin(ang)
            y = cy + lx * math.sin(ang) + ly * math.cos(ang)
            if all((x - q[0]) ** 2 + (y - q[1]) ** 2 > spacing ** 2 for q in pts):
                pts.append((x, y))
    # balanced use of the variants (every source appears before any repeats), shuffled by the seed
    order = []
    while len(order) < len(pts) and cr.sources:
        blk = list(range(len(cr.sources)))
        rng.shuffle(blk)
        order += blk
    for i, q in enumerate(pts):
        x, y = q[0], q[1]
        z = q[2] if len(q) > 2 else (height_fn(x, y) if height_fn else ground_z)
        if face is not None:
            yw = math.atan2(face[0] - x, -(face[1] - y))
        elif yaw is not None:
            yw = math.radians(yaw)
        else:
            yw = rng.uniform(-math.pi, math.pi)
        yw += math.radians(rng.uniform(-yaw_jitter, yaw_jitter))
        src = cr.sources[order[i]]
        inst = _instance(src, (x, y, z), yw, rng.uniform(0.95, 1.05), coll)
        inst.hide_render = False
        inst.hide_viewport = False
        for c in inst.children:
            c.hide_render = c.hide_viewport = False
        cr.instances.append(inst)
    return cr


def clone(person, loc=(0, 0, 0), yaw=0.0, name=None, action_offset=0):
    """Animated linked copy of a person: new rig object sharing the armature + meshes (cheap), with
    its own transform. The rig action is shared (offset with action_offset frames via NLA)."""
    p = person
    name = name or p.name + "_c"
    coll = p.rig.users_collection[0]
    rig = p.rig.copy()
    rig.name = name
    coll.objects.link(rig)
    rig.location = loc
    rig.rotation_euler = (0, 0, yaw)
    if action_offset and rig.animation_data and rig.animation_data.action:
        act = rig.animation_data.action
        rig.animation_data.action = None
        tr = rig.animation_data.nla_tracks.new()
        st = tr.strips.new(act.name, int(1 + action_offset), act)
    mapping = {p.rig: rig}
    for o in p.objects()[1:]:
        c = o.copy()
        coll.objects.link(c)
        mapping[o] = c
    for o, c in mapping.items():
        if o is p.rig:
            continue
        c.parent = mapping.get(o.parent, rig)
        for m in getattr(c, "modifiers", []):
            if m.type == "ARMATURE":
                m.object = rig
        if c.type == "CURVES":
            c.data = o.data   # shared; surface stays the original body (fine for static distance shots)
    q = Person(name, rig, mapping[p.body], {k: mapping.get(v, v) for k, v in p.parts.items()}, p.spec)
    q.height = p.height
    q.lm = p.lm
    q.garments = [mapping.get(g, g) for g in p.garments]
    return q


# ============================================================================================
# Head hair strands (grown along the MPFB hair shell, bound to it by UV so they follow it)
# ============================================================================================
def _shell_data(shell):
    me = shell.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    tv = np.zeros(nt * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", tv)
    tl = np.zeros(nt * 3, np.int32)
    me.loop_triangles.foreach_get("loops", tl)
    uv = np.zeros(len(me.loops) * 2, np.float32)
    me.uv_layers[0].data.foreach_get("uv", uv)
    co = _coords(me)
    return co, tv.reshape(-1, 3), tl.reshape(-1, 3), uv.reshape(-1, 2)


def _tri_grad_v(P3, UV):
    """Per-triangle 3D gradient of the UV v coordinate (direction of increasing v on the surface)."""
    e1 = P3[:, 1] - P3[:, 0]
    e2 = P3[:, 2] - P3[:, 0]
    du1 = UV[:, 1] - UV[:, 0]
    du2 = UV[:, 2] - UV[:, 0]
    det = du1[:, 0] * du2[:, 1] - du1[:, 1] * du2[:, 0]
    det = np.where(np.abs(det) < 1e-12, 1e-12, det)
    # dP/dv = (-du2.u * e1 + du1.u * e2) / det
    dPdv = (-du2[:, 0:1] * e1 + du1[:, 0:1] * e2) / det[:, None]
    return dPdv


STRAND_VERSION = 6


def _hair_cache_path(key):
    d = os.path.join(C.WORK, "cache", "characters")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "hair_%s.npz" % key)


def make_hair_strands(p, count=None, points=16, length_scale=1.0, depth=(-0.001, 0.006), clump=0.55, frizz=0.0012,
                      seed=None, color=None, grey=None, flyaways=0.006):
    """Hero head hair: hair-curve strands that flow along the MPFB hair shell (root -> tip = UV v
    direction), bound per point to the shell's UV so they follow its armature deformation exactly.
    The shell stays as a dark under-layer. Returns the curves object (p.parts['hair_strands'])."""
    s = p.spec
    shell = p.parts.get("hair")
    if shell is None:
        return None
    rng = np.random.default_rng(seed if seed is not None else s.get("seed", 0) + 101)
    co, tv, tl, uv = _shell_data(shell)
    N = int(count or (11000 if s["hair"] == "long01" else 7000))
    key = hashlib.md5(co.tobytes() + uv.tobytes() + str((STRAND_VERSION, N, points, depth, clump, frizz, length_scale, flyaways)).encode()).hexdigest()[:16]
    cp = _hair_cache_path(key)
    if os.path.exists(cp):
        dat = np.load(cp)
        pts, bidx, bw, pdep, rad = dat["pts"], dat["bidx"], dat["bw"], dat["pdep"], dat["rad"]
    else:
        pts, (bidx, bw), pdep, rad = _grow_shell_strands(p, shell, co, tv, tl, uv, N, points, length_scale, depth, clump, frizz, rng, flyaways)
        np.savez(cp, pts=pts, bidx=bidx, bw=bw, pdep=pdep, rad=rad)
    K = points
    cv = bpy.data.hair_curves.new(p.name + ".hair_strands")
    cv.add_curves([K] * len(pts))
    cv.position_data.foreach_set("vector", pts.astype(np.float32).ravel())
    if "radius" not in cv.attributes:
        cv.attributes.new("radius", "FLOAT", "POINT")
    cv.attributes["radius"].data.foreach_set("value", rad.astype(np.float32).ravel())
    for i in range(3):
        a = cv.attributes.new("bv%d" % i, "INT", "POINT")
        a.data.foreach_set("value", bidx[:, i].astype(np.int32))
        a = cv.attributes.new("bw%d" % i, "FLOAT", "POINT")
        a.data.foreach_set("value", bw[:, i].astype(np.float32))
    a = cv.attributes.new("shell_depth", "FLOAT", "POINT")
    a.data.foreach_set("value", pdep.astype(np.float32).ravel())
    ob = bpy.data.objects.new(p.name + ".hair_strands", cv)
    for c in shell.users_collection:
        c.objects.link(ob)
    ob.parent = p.rig
    mod = ob.modifiers.new("follow_shell", "NODES")
    mod.node_group = _follow_shell_group()
    _set_mod_input(mod, "Shell", shell)
    hc = hair_color_rgb(color or s["hair_color"], 0.0)
    mat = curve_hair_material(p.name + ".strand_mat", hc, grey if grey is not None else s.get("grey", 0))
    cv.materials.append(mat)
    p.parts["hair_strands"] = ob
    p.mats["hair_strands"] = mat
    for m in list(shell.modifiers):          # strands are bound by vertex index: keep the shell topology
        if m.type == "SUBSURF":
            shell.modifiers.remove(m)
    # the shell becomes a darker, matte under-layer that fills the gaps between strands
    _shell_underlayer(p, 0.7, rough=0.6, spec=0.25)
    return ob


def _shell_underlayer(p, value=0.6, rough=0.65, spec=0.2):
    """Make the MPFB hair shell a darker, matte under-layer below hair curves (keeps its alpha)."""
    m = p.mats.get("hair")
    if m is None or m.get("ps22_under"):
        return
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF") or next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if b is None:
        return
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    ln = b.inputs["Base Color"].links
    if ln:
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = "MULTIPLY"
        mx.inputs["Factor"].default_value = 1.0
        nt.links.new(ln[0].from_socket, mx.inputs[6])
        mx.inputs[7].default_value = (value, value, value, 1)
        nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    m["ps22_under"] = 1


SHORT_HAIR = {   # MPFB short shells -> strand length (m), wave amplitude, lift (rad), count
    "short01": dict(length=0.022, wave=0.0010, lift=0.22, count=22000, fringe=0.0, sweep=0.3),
    "short02": dict(length=0.040, wave=0.0018, lift=0.16, count=24000, fringe=-0.15, sweep=0.55),
    "short03": dict(length=0.050, wave=0.0040, lift=0.20, count=24000, fringe=-0.1, sweep=0.5),
    "short04": dict(length=0.030, wave=0.0015, lift=0.18, count=20000, fringe=0.25, sweep=0.35),
    "afro01": dict(length=0.035, wave=0.0060, lift=0.55, count=24000, fringe=0.0, sweep=0.2),
}


def make_short_hair(p, length=None, count=None, points=6, seed=None, color=None, grey=None, part_side=1.0):
    """Short hero hair: hair curves rooted on the scalp (hair-bearing mask), combed along a crown-whorl
    direction field, lying in a layer up to the MPFB hair shell (which stays as a dark under-layer that
    gives the haircut its volume). Deformed with the body (Deform Curves on Surface), like the beard.
    Returns the curves object (p.parts['hair_strands'])."""
    s = p.spec
    shell = p.parts.get("hair")
    cfg = dict(SHORT_HAIR.get(s["hair"], SHORT_HAIR["short02"]))
    L = float(length or cfg["length"]) * (p.lm["io"] / 0.062)
    N = int(count or cfg["count"])
    K = int(points)
    rng = np.random.default_rng(seed if seed is not None else s.get("seed", 0) * 17 + 3)
    co, lm = p._co, p.lm
    sc = lm["io"] / 0.062
    hm = p.masks["hair"]
    tv, tl, area, uv, vn = _surface_data(p.body)
    inb = p._w["body"] > 0.5
    key = hashlib.md5(co.tobytes() + str((STRAND_VERSION, "short2", s["hair"], N, K, L, sorted(cfg.items()),
                                           part_side, seed, s.get("seed", 0))).encode()).hexdigest()[:16]
    cp = _hair_cache_path(key)
    if os.path.exists(cp):
        dat = np.load(cp)
        pts, ruv = dat["pts"], dat["ruv"]
    else:
        tm = hm[tv].mean(1) * inb[tv].all(1)
        sel = np.nonzero(tm > 0.05)[0]
        wts = area[sel] * tm[sel] ** 1.5
        ti = sel[rng.choice(len(sel), N, p=wts / wts.sum())]
        r1, r2 = rng.random(N), rng.random(N)
        s1 = np.sqrt(r1)
        bary = np.stack([1 - s1, s1 * (1 - r2), s1 * r2], 1)
        roots = (co[tv[ti]] * bary[:, :, None]).sum(1)
        ruv = (uv[tl[ti]] * bary[:, :, None]).sum(1)
        nrm = _norm((vn[tv[ti]] * bary[:, :, None]).sum(1))
        rm = (hm[tv[ti]] * bary).sum(1)
        # hair layer thickness at the root: distance from the scalp to the MPFB shell along the normal
        thick = np.full(N, 0.006 * sc)
        if shell is not None:
            sco = _coords(shell.data)
            sbvh = BVHTree.FromPolygons([tuple(c) for c in sco], [tuple(pl.vertices) for pl in shell.data.polygons])
            for i in range(N):
                hit = sbvh.ray_cast(Vector(roots[i]) + Vector(nrm[i]) * 0.0005, Vector(nrm[i]), 0.05)
                if hit[0] is not None:
                    thick[i] = min(0.03 * sc, max(0.002, hit[3]))
        thick = np.minimum(thick, 0.012 * sc) * (0.55 + 0.45 * np.clip(rm, 0, 1))
        # crown whorl + parting: radial from the whorl, combed down by gravity, fringe forward + to the side
        E = np.array(lm["eyes"])
        W = np.array([0.012 * sc * part_side, E[1] + 0.105 * sc, lm["head_top"] - 0.018 * sc])
        rad_ = roots - W
        grav = np.array([0.0, 0.0, -1.0])
        fwd = np.array([0.0, -1.0, 0.0])
        frontness = np.clip((E[1] + 0.06 * sc - roots[:, 1]) / (0.06 * sc), 0, 1)       # 1 = front of the head
        d = _norm(rad_) * 0.7 + grav * (0.45 - 0.3 * frontness * (cfg["fringe"] < 0))[:, None] + \
            fwd * (cfg["fringe"] * frontness)[:, None]
        d[:, 0] += cfg["sweep"] * part_side * frontness
        d = d - nrm * (d * nrm).sum(1, keepdims=True)
        d = _norm(d)
        me = p.body.data
        polys = [tuple(pl.vertices) for pl in me.polygons if all(inb[v] for v in pl.vertices)]
        bvh = BVHTree.FromPolygons([tuple(c) for c in co], polys, all_triangles=False)
        pmask = np.array([hm[list(pv)].mean() for pv in polys])
        stop_at_hairline = cfg["fringe"] < 0.1
        layer = rng.random(N)
        seg = L / (K - 1)
        pts = np.zeros((N, K, 3))
        pts[:, 0] = roots
        pos = roots.copy()
        dirs = d.copy()
        lift = cfg["lift"]
        phase = rng.random(N) * 6.283
        lens = np.clip(rng.normal(1.0, 0.15, N), 0.55, 1.3) * (0.6 + 0.4 * np.clip(rm, 0, 1))
        if cfg["fringe"] < 0.1:      # men: the front is shorter (no curtain over the forehead)
            lens *= 1.0 - 0.35 * frontness
        for k in range(1, K):
            t = k / (K - 1)
            for i in range(N):
                q = pos[i] + dirs[i] * seg * lens[i]
                loc, nn, fi, dist = bvh.find_nearest(Vector(q))
                if loc is None:
                    pos[i] = q
                    continue
                if stop_at_hairline and pmask[fi] < 0.2 and lens[i] > 0.05:
                    lens[i] = 0.04          # reached the forehead / face: stop (no curtain over the brow)
                    q = pos[i] + dirs[i] * seg * lens[i]
                    loc, nn, fi, dist = bvh.find_nearest(Vector(q))
                nn = np.array(nn)
                h = 0.0006 * sc + thick[i] * (0.55 + 0.6 * layer[i]) * min(1.0, t / 0.35) ** 0.8 + lift * 0.004 * t
                newp = np.array(loc) + nn * h
                tdir = newp - pos[i]
                nd = np.linalg.norm(tdir)
                if nd > 1e-9:
                    # keep combing along the field, re-projected to the local tangent plane
                    dd = dirs[i] - nn * dirs[i].dot(nn)
                    dl = np.linalg.norm(dd)
                    if dl > 1e-9:
                        dirs[i] = dd / dl * 0.8 + (grav - nn * grav.dot(nn)) * 0.2
                        dirs[i] /= max(1e-9, np.linalg.norm(dirs[i]))
                side = np.cross(dirs[i], nn)
                newp = newp + side * math.sin(phase[i] + t * 5.0) * cfg["wave"] * t
                pos[i] = newp
                pts[i, k] = newp
        fz = rng.normal(0, 1, pts.shape) * 0.0004 * sc * (np.linspace(0, 1, K) ** 1.5)[None, :, None]
        pts += fz
        pts[:, 0] = roots
        np.savez(cp, pts=pts, ruv=ruv)
    cv = bpy.data.hair_curves.new(p.name + ".hair_strands")
    cv.add_curves([K] * len(pts))
    cv.position_data.foreach_set("vector", pts.astype(np.float32).ravel())
    rad = np.tile(np.linspace(1.0, 0.5, K), len(pts)) * 0.00011 * sc
    if "radius" not in cv.attributes:
        cv.attributes.new("radius", "FLOAT", "POINT")
    cv.attributes["radius"].data.foreach_set("value", rad.astype(np.float32))
    a = cv.attributes.new("surface_uv_coordinate", "FLOAT2", "CURVE")
    a.data.foreach_set("vector", ruv.astype(np.float32).ravel())
    cv.surface = p.body
    cv.surface_uv_map = p.body.data.uv_layers[0].name
    ob = bpy.data.objects.new(p.name + ".hair_strands", cv)
    for c in p.body.users_collection:
        c.objects.link(ob)
    ob.parent = p.rig
    ob.modifiers.new("deform", "NODES").node_group = _deform_on_surface_group()
    hc = hair_color_rgb(color or s["hair_color"], 0.0)
    mat = curve_hair_material(p.name + ".strand_mat", hc, grey if grey is not None else s.get("grey", 0))
    cv.materials.append(mat)
    p.parts["hair_strands"] = ob
    p.mats["hair_strands"] = mat
    if shell is not None:
        # the painted scalp + strands replace the MPFB card shell (it read as a rubber cap); the shell object
        # stays (hidden) because head garments are fitted over it
        shell.hide_render = True
        shell.hide_viewport = True
    return ob


def _set_mod_input(mod, name, value):
    for it in mod.node_group.interface.items_tree:
        if getattr(it, "in_out", None) == "INPUT" and it.name == name:
            mod[it.identifier] = value
            return


def _grow_shell_strands(p, shell, co, tv, tl, uv, N, K, length_scale, depth, clump, frizz, rng, flyaways):
    P3 = co[tv]
    UV = uv[tl]
    gv = _tri_grad_v(P3, UV)                     # +v direction per triangle
    area = 0.5 * np.linalg.norm(np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]), axis=1)
    tn = _norm(np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]))
    # orient normals outwards (away from the head centre)
    hc = np.array(p.lm["eyes"]) + np.array([0, 0.07, 0.02])
    flip = ((P3.mean(1) - hc) * tn).sum(1) < 0
    tn[flip] *= -1
    # root -> tip direction: v decreases from roots (top) to tips; check against gravity statistically
    down = -gv
    if (down[:, 2] * area).sum() > 0:            # majority would point up: flip
        down = -down
    # connected shell islands (layers / strips): strands stay on the island of their root
    par = list(range(len(co)))

    def _f(a):
        while par[a] != a:
            par[a] = par[par[a]]
            a = par[a]
        return a
    for t in tv:
        a, b, c = _f(int(t[0])), _f(int(t[1])), _f(int(t[2]))
        par[b] = a
        par[_f(c)] = a
    tri_isl = np.array([_f(int(t[0])) for t in tv])
    isl_ids = {r: i for i, r in enumerate(np.unique(tri_isl))}
    tri_isl = np.array([isl_ids[r] for r in tri_isl])
    cl = [tuple(c) for c in co]
    bvhs, tmaps = [], []
    for i in range(len(isl_ids)):
        ti = np.nonzero(tri_isl == i)[0]
        bvhs.append(BVHTree.FromPolygons(cl, [tuple(tv[t]) for t in ti]))
        tmaps.append(ti)
    # roots: points on the shell near the top of each UV column = high "v rank".
    vt = UV[:, :, 1].mean(1)
    if (down[:, 2] * area).sum() > 0:
        vt = -vt
    # root region: triangles whose v is within the top 12% of the island's v at that u column
    ucol = np.floor(UV[:, :, 0].mean(1) * 64).astype(int)
    rootw = np.zeros(len(tv))
    for c in np.unique(ucol):
        m = ucol == c
        vv = vt[m]
        lo, hi = vv.min(), vv.max()
        rootw[m] = (vv > hi - 0.12 * (hi - lo)).astype(float)
    wts = area * rootw
    G = max(60, N // 18)
    gi = rng.choice(len(tv), G, p=wts / wts.sum())
    r1, r2 = rng.random(G), rng.random(G)
    s1 = np.sqrt(r1)
    bary = np.stack([1 - s1, s1 * (1 - r2), s1 * r2], 1)
    groots = (P3[gi] * bary[:, :, None]).sum(1)
    gisl = tri_isl[gi]
    sc = p.height / 1.75
    Lmax = {"long01": 0.62, "ponytail01": 0.4, "braid01": 0.45, "bob01": 0.25, "bob02": 0.25}.get(p.spec["hair"], 0.12) * sc * length_scale
    seg = Lmax / (K - 1)
    E = p.lm["eyes"]

    def _in_face(q):   # keep strands off the face (forehead / cheeks in front of the ears)
        return abs(q.x) < 0.064 * sc and q.y < E.y + 0.06 * sc and p.lm["chin_bot"] - 0.04 * sc < q.z < E.z + 0.05 * sc
    guides = np.zeros((G, K, 3))
    gnorm = np.zeros((G, K, 3))
    alive = np.ones((G, K), bool)
    for i in range(G):
        pos = Vector(groots[i])
        bvh, tmap = bvhs[gisl[i]], tmaps[gisl[i]]
        for k in range(K):
            loc, nn, fi, dist = bvh.find_nearest(pos)
            if fi is not None:
                fi = int(tmap[fi])
            if fi is None:
                alive[i, k:] = False
                break
            nrm = Vector(tn[fi])
            guides[i, k] = loc
            gnorm[i, k] = nrm
            dvec = Vector(down[fi])
            if dvec.length < 1e-9:
                alive[i, k + 1:] = False
                break
            dvec = (dvec - nrm * dvec.dot(nrm)).normalized()
            nxt = loc + dvec * seg
            # stop at the shell's boundary (the tip edge): projecting jumps far or v stops changing
            loc2, nn2, fi2, d2 = bvh.find_nearest(nxt)
            if fi2 is None or d2 > seg * 0.8 or _in_face(loc2):
                alive[i, k + 1:] = False
                break
            pos = loc2
    # guide length = number of alive points
    glen = alive.sum(1)
    ok = glen >= 3
    guides, gnorm, alive, glen, gisl = guides[ok], gnorm[ok], alive[ok], glen[ok], gisl[ok]
    G = len(guides)
    # children around guides
    owner = rng.integers(0, G, N)
    kk = np.arange(K)
    T = kk / (K - 1)
    # each child: root offset on the surface (tangent), depth layer, own length fraction
    tang = rng.normal(0, 1, (N, 3))
    n0 = gnorm[owner, 0]
    tang = _norm(tang - n0 * (tang * n0).sum(1, keepdims=True)) * rng.uniform(0, 0.012 * sc, (N, 1))
    dep = rng.uniform(depth[0], depth[1], N) * sc
    fly = rng.random(N) < flyaways
    dep[fly] += rng.uniform(0.003, 0.01, fly.sum()) * sc
    lfrac = np.clip(rng.uniform(0.55, 1.02, N), 0, 1)
    cl = clump * rng.uniform(0.6, 1.2, N)
    pts = np.zeros((N, K, 3))
    surf = np.zeros((N, K, 3))
    pdep = np.zeros((N, K))
    for k in range(K):
        # sample the guide at fraction lfrac * (glen-1)
        fk = T[k] * lfrac * (glen[owner] - 1)
        k0 = np.clip(np.floor(fk).astype(int), 0, K - 2)
        a = (fk - k0)[:, None]
        g = guides[owner, k0] * (1 - a) + guides[owner, np.minimum(k0 + 1, K - 1)] * a
        nn = _norm(gnorm[owner, k0] * (1 - a) + gnorm[owner, np.minimum(k0 + 1, K - 1)] * a)
        t = T[k]
        offs = tang * (1 - cl[:, None] * t ** 0.8)
        d = dep * (1.0 - 0.5 * cl * t) + (fly * (t ** 1.5) * 0.01 * sc)
        pts[:, k] = g + offs + nn * d[:, None]
        surf[:, k] = g + offs
        pdep[:, k] = d
    fz = rng.normal(0, 1, pts.shape) * frizz * sc * (T ** 1.3)[None, :, None]
    pts += fz
    # bind every point to a shell triangle (vertex indices + barycentric weights) on its root's island,
    # found from its surface foot point; depth along the triangle's winding normal
    flat = (surf + fz).reshape(-1, 3)
    fpts = pts.reshape(-1, 3)
    nP = len(flat)
    bidx = np.zeros((nP, 3), np.int32)
    bw = np.zeros((nP, 3), np.float32)
    fdep = pdep.reshape(-1).copy()
    pisl = np.repeat(gisl[owner], K)
    wn = _norm(np.cross(P3[:, 1] - P3[:, 0], P3[:, 2] - P3[:, 0]))
    for i in range(nP):
        loc, nn, fi, dist = bvhs[pisl[i]].find_nearest(Vector(flat[i]))
        if fi is None:
            continue
        fi = int(tmaps[pisl[i]][fi])
        a, b, c = P3[fi]
        bc = np.clip(_bary_np(np.array(loc), a, b, c), 0, 1)
        bc /= max(1e-9, bc.sum())
        bidx[i] = tv[fi]
        bw[i] = bc
        fdep[i] = (fpts[i] - bc @ P3[fi]).dot(wn[fi])
    puv = (bidx, bw)
    pdep = fdep
    rad = np.tile(np.linspace(1.0, 0.55, K), (N, 1)) * 0.00009 * sc * rng.uniform(0.8, 1.25, (N, 1))
    return pts, puv, pdep, rad


def _bary_np(pt, a, b, c):
    v0, v1, v2 = b - a, c - a, pt - a
    d00, d01, d11 = v0.dot(v0), v0.dot(v1), v1.dot(v1)
    d20, d21 = v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01
    if abs(den) < 1e-18:
        return np.array([1.0, 0.0, 0.0])
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.array([1 - v - w, v, w])


def _follow_shell_group():
    """GN: every strand point = barycentric point of its bound shell triangle (by vertex index)
    + depth * triangle normal, evaluated on the deformed shell."""
    ng = bpy.data.node_groups.get("PS22_FollowShell2")
    if ng:
        return ng
    ng = bpy.data.node_groups.new("PS22_FollowShell2", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Shell", in_out="INPUT", socket_type="NodeSocketObject")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, L = ng.nodes, ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    oi = N.new("GeometryNodeObjectInfo")
    oi.transform_space = "RELATIVE"
    L.new(gi.outputs["Shell"], oi.inputs["Object"])
    pos = N.new("GeometryNodeInputPosition")

    def attr(name, kind):
        a = N.new("GeometryNodeInputNamedAttribute")
        a.data_type = kind
        a.inputs["Name"].default_value = name
        return a.outputs["Attribute"]

    def vm(op, a, b=None, scale=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        L.new(a, n.inputs[0])
        if b is not None:
            L.new(b, n.inputs[1])
        if scale is not None:
            L.new(scale, n.inputs["Scale"])
        return n.outputs[0]
    P = []
    for i in range(3):
        si = N.new("GeometryNodeSampleIndex")
        si.data_type = "FLOAT_VECTOR"
        si.domain = "POINT"
        L.new(oi.outputs["Geometry"], si.inputs["Geometry"])
        L.new(pos.outputs[0], si.inputs["Value"])
        L.new(attr("bv%d" % i, "INT"), si.inputs["Index"])
        P.append(si.outputs[0])
    acc = vm("SCALE", P[0], scale=attr("bw0", "FLOAT"))
    acc = vm("ADD", acc, vm("SCALE", P[1], scale=attr("bw1", "FLOAT")))
    acc = vm("ADD", acc, vm("SCALE", P[2], scale=attr("bw2", "FLOAT")))
    nrm = vm("NORMALIZE", vm("CROSS_PRODUCT", vm("SUBTRACT", P[1], P[0]), vm("SUBTRACT", P[2], P[0])))
    final = vm("ADD", acc, vm("SCALE", nrm, scale=attr("shell_depth", "FLOAT")))
    sp = N.new("GeometryNodeSetPosition")
    L.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    L.new(final, sp.inputs["Position"])
    L.new(sp.outputs[0], go.inputs[0])
    return ng
