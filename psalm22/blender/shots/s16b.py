"""s16b - Scarred hand: "For he has not despised or scorned the suffering of the afflicted one;"

Close-up (dissolve from the praising multitude at sunrise). The risen Christ (white robe) lifts his
right hand towards us: during the first phrase the hand turns and opens, palm towards the camera, in
low warm sunrise light; on "the suffering of the afflicted one" the camera eases in on the healed
nail wound in the palm - a pale, puckered, long-closed scar (no blood). The sun stands behind him,
rimming fingers, sleeve and shoulder; dust motes glitter in the backlight; his robe and face are a
soft blur behind the hand (85 mm, f/2).
"""
import math
import bpy
from mathutils import Vector
from lib import core as C
from lib import characters as P
from lib import env as E
from lib import sets as S

SIDE = "R"          # character's right hand (screen left of his body)


def _show_pose_fn():
    """Custom pose 's16b_show': stand relaxed + one forearm raised, palm turned to `face` (world dir in
    rig space), fingers along `up`. Searches pronation / wrist flexion so the palm normal matches."""
    _Pose = P._Pose

    def fn(Pp, p, target=None, side="R", hand="open", face=(0, -1, 0), up=(0, 0, 1), pole=None, curl=1.0, **k):
        P._pose_stand(Pp, p, relaxed=True)
        s = side
        base = Pp.copy()
        face = Vector(face).normalized()
        upv = Vector(up).normalized()
        pole = Vector(pole) if pole is not None else Vector((-0.6 if s == "R" else 0.6, 0.4, -1.0))
        best = None
        for pron in range(-40, 200, 8):
            for flex in (-50, -40, -30, -20, -10, 0, 10, 20):
                Q = base.copy()
                P._arm_ik(Q, s, Vector(target), pole=pole, pron=pron, flex=flex, shrug=4)
                pn = Q.carry("wrist." + s, Q.an["palm" + s]).normalized()
                fd = Q.ydir("wrist." + s)
                err = (1 - pn.dot(face)) * 1.0 + (1 - fd.dot(upv)) * 0.6
                if best is None or err < best[0]:
                    best = (err, pron, flex)
        _, pron, flex = best
        # refine
        for dp in (-6, -3, 0, 3, 6):
            for dfl in (-6, -3, 0, 3, 6):
                Q = base.copy()
                P._arm_ik(Q, s, Vector(target), pole=pole, pron=pron + dp, flex=flex + dfl, shrug=4)
                pn = Q.carry("wrist." + s, Q.an["palm" + s]).normalized()
                fd = Q.ydir("wrist." + s)
                err = (1 - pn.dot(face)) * 1.0 + (1 - fd.dot(upv)) * 0.6
                if err < best[0]:
                    best = (err, pron + dp, flex + dfl)
        _, pron, flex = best
        P._arm_ik(Pp, s, Vector(target), pole=pole, pron=pron, flex=flex, shrug=4)
        P._hand(Pp, s, hand, amount=curl)
        print("s16b pose: pron %.0f flex %.0f err %.3f" % (pron, flex, best[0]))
    return fn


def _scar_relief(person):
    """Healed nail-wound look on top of the characters scar tint: slightly raised, puckered, paler
    and smoother (less pores, a touch glossier) with a faint brownish rim. Uses the wound mask."""
    m = person.body.active_material
    if m is None or not m.use_nodes:
        return
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    bsdf = next((n for n in N if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        return
    attr = N.new("ShaderNodeAttribute")
    attr.attribute_name = "cmask_a"
    sep = N.new("ShaderNodeSeparateColor")
    Lk.new(attr.outputs["Color"], sep.inputs[0])
    wound = sep.outputs[2]
    rest = N.new("ShaderNodeAttribute")
    rest.attribute_type = "GEOMETRY"
    rest.attribute_name = "rest_position"
    nz = N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 260.0
    nz.inputs["Detail"].default_value = 4.0
    nz.inputs["Roughness"].default_value = 0.65
    Lk.new(rest.outputs["Vector"], nz.inputs["Vector"])
    # irregular edge: distort the mask with noise
    def math(op, a, b, clamp=False):
        mn = N.new("ShaderNodeMath")
        mn.operation = op
        mn.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if isinstance(v, (int, float)):
                mn.inputs[i].default_value = v
            else:
                Lk.new(v, mn.inputs[i])
        return mn.outputs[0]
    wn = math("ADD", wound, math("MULTIPLY", math("SUBTRACT", nz.outputs["Fac"], 0.5), 0.55))
    core = N.new("ShaderNodeMapRange")
    core.inputs["From Min"].default_value = 0.55
    core.inputs["From Max"].default_value = 0.85
    Lk.new(wn, core.inputs["Value"])
    scar = core.outputs[0]                                      # 0..1 scar tissue
    rim = math("MULTIPLY", math("MULTIPLY", scar, math("SUBTRACT", 1.0, scar), True), 4.0, True)  # edge band
    # colour: paler pink-ivory scar tissue, faint brown rim
    base_link = bsdf.inputs["Base Color"].links[0] if bsdf.inputs["Base Color"].is_linked else None
    if base_link:
        src = base_link.from_socket
        mix1 = N.new("ShaderNodeMix")
        mix1.data_type = "RGBA"
        mix1.blend_type = "MIX"
        Lk.new(math("MULTIPLY", scar, 0.55), mix1.inputs["Factor"])
        Lk.new(src, mix1.inputs[6])
        mix1.inputs[7].default_value = (0.78, 0.55, 0.50, 1.0)
        mix2 = N.new("ShaderNodeMix")
        mix2.data_type = "RGBA"
        mix2.blend_type = "MULTIPLY"
        Lk.new(math("MULTIPLY", rim, 0.35), mix2.inputs["Factor"])
        Lk.new(mix1.outputs[2], mix2.inputs[6])
        mix2.inputs[7].default_value = (0.62, 0.45, 0.38, 1.0)
        Lk.new(mix2.outputs[2], bsdf.inputs["Base Color"])
    # roughness: smoother, slightly shiny scar
    if bsdf.inputs["Roughness"].is_linked:
        rsrc = bsdf.inputs["Roughness"].links[0].from_socket
        Lk.new(math("SUBTRACT", rsrc, math("MULTIPLY", scar, 0.16)), bsdf.inputs["Roughness"])
    # relief: raised puckered ring + slight central dimple + radial-ish creases (noise)
    nz2 = N.new("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 900.0
    nz2.inputs["Detail"].default_value = 2.0
    Lk.new(rest.outputs["Vector"], nz2.inputs["Vector"])
    dimple = math("POWER", scar, 3.0)
    h = math("ADD", math("MULTIPLY", rim, 0.8), math("MULTIPLY", dimple, -0.5))
    h = math("ADD", h, math("MULTIPLY", math("MULTIPLY", nz2.outputs["Fac"], scar), 0.5))
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.55
    bump.inputs["Distance"].default_value = 0.0012
    Lk.new(h, bump.inputs["Height"])
    if bsdf.inputs["Normal"].is_linked:
        Lk.new(bsdf.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    Lk.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def build(ctx):
    NR = ctx.render_frames
    n = ctx.nframes
    fr = ctx.frame
    p1s, p1e = ctx.phrase_frames(0)
    p2s, p2e = ctx.phrase_frames(1)

    # ---------------- sky / sun (sunrise, behind him, screen left: clears his shoulder) ----------------
    sky = E.sky(mood="sunrise", sun_az=212, ctx=ctx)
    sun = sky["sun"]

    # ---------------- the risen Christ ----------------
    if "s16b_show" not in P.POSES:
        P.POSES["s16b_show"] = _show_pose_fn()
    j = P.make_person("jesus", "JESUS_RISEN", hair_strands=False, pose=None)
    j.rig.location = (0, 0, 0)
    j.update()
    sh = j.bone_world("upperarm01.R")
    tgt = sh + Vector((0.06, -0.36, -0.05))          # palm centre: in front of the right shoulder
    cam_pos = tgt + Vector((-0.08, -0.75, 0.02))
    face0 = (cam_pos - tgt).normalized()
    # start: palm turned in (towards his centre line), fingers relaxed; end: palm to camera, open
    face_in = Vector((0.85, -0.35, 0.0)).normalized()
    P.key_pose(j, 1, "s16b_show", target=tgt + Vector((0.0, 0.03, -0.04)), side="R", hand="relaxed",
               face=face_in, up=(0.1, 0.0, 1.0), ground=False)
    f_open = int(p1e - 6)
    P.key_pose(j, f_open, "s16b_show", target=tgt, side="R", hand="open", face=face0, up=(-0.05, 0.05, 1.0),
               ground=False)
    P.key_pose(j, NR, "s16b_show", target=tgt + Vector((0.0, -0.01, 0.005)), side="R", hand="open",
               face=face0, up=(-0.08, 0.05, 1.0), ground=False)
    P.expression(j, "peace")
    _scar_relief(j)

    # ---------------- camera ----------------
    cam = C.camera(loc=cam_pos, target=tgt, lens=85, fstop=2.0, focus=(cam_pos - tgt).length, name="s16b_cam")
    c0, c1 = cam_pos, tgt + (cam_pos - tgt) * 0.82

    def path(f):
        u = C.ease_in_out(max(0.0, min(1.0, (f - 1) / float(NR - 1))))
        loc = c0.lerp(c1, u) + C.shake(f, amp=0.0025, freq=0.35, seed=3)
        return loc, tgt + Vector((0, 0, 0.005))
    C.animate_camera(cam, path)
    for f in range(1, NR + 1, 6):
        loc, t = path(f)
        cam.data.dof.focus_distance = (t - loc).length - 0.01
        cam.data.dof.keyframe_insert("focus_distance", frame=f)

    # ---------------- light ----------------
    # warm soft key raking the palm from screen right / front (sunlight bounced off pale ground)
    C.light("AREA", loc=tuple(tgt + Vector((0.95, -0.45, 0.25))), energy=45, temp=3200, target=tuple(tgt), size=0.9,
            name="s16b_bounce", shadow=True)
    C.light("AREA", loc=tuple(tgt + Vector((-0.6, -0.8, -0.4))), energy=12, temp=4500, target=tuple(tgt), size=1.5,
            name="s16b_fill", shadow=False)
    # dust motes in the backlight
    S.dust(center=tuple(tgt + Vector((0, -0.15, 0.05))), size=(0.7, 0.6, 0.7), count=220, radius=0.0012,
           color=(1.0, 0.9, 0.75), emission=0.0, speed=0.05, amp=0.08, seed=4, name="s16b_motes")

    ctx.samples = 6
    ctx.render_opts = {"volumetrics": "low"}
    ctx.post = {"grade": "warm", "bloom": 0.3}
