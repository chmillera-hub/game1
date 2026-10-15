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


class _NM:
    """Tiny shader-math builder (scalars / vectors as sockets or constants)."""

    def __init__(self, nt):
        self.nt, self.N, self.L = nt, nt.nodes, nt.links

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, (tuple, list, Vector)):
            sock.default_value = tuple(v)
        else:
            self.L.new(v, sock)

    def m(self, op, a, b=0.0, c=None, clamp=False):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        if c is not None:
            self._in(n.inputs[2], c)
        return n.outputs[0]

    def v(self, op, a, b=None, out=0):
        n = self.N.new("ShaderNodeVectorMath")
        n.operation = op
        self._in(n.inputs[0], a)
        if b is not None:
            self._in(n.inputs[1], b)
        return n.outputs[out]

    def dot(self, a, b):
        return self.v("DOT_PRODUCT", a, b, out="Value")

    def smooth(self, x, lo, hi):
        """smoothstep(lo, hi, x) (lo > hi gives the inverted ramp)."""
        n = self.N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        self._in(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = lo
        n.inputs["From Max"].default_value = hi
        return n.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = blend
        self._in(n.inputs["Factor"], fac)
        self._in(n.inputs[6], a)
        self._in(n.inputs[7], b if isinstance(b, bpy.types.NodeSocket) else (*b, 1.0))
        return n.outputs[2]


def _hand_frame(person, side="R"):
    """Rest-space (body object space) frame of the palm: palm-surface centre S, back-surface centre Sb,
    axis A (wrist -> knuckles), palm normal Np, B (towards the thumb), palm length."""
    import numpy as np
    s = side
    b = person.rig.data.bones
    wr = Vector(b["wrist." + s].head_local)
    kn = Vector(b["metacarpal2." + s].tail_local)
    kn5 = Vector(b["metacarpal4." + s].tail_local)
    th = Vector(b["finger1-1." + s].head_local)
    pc = (wr + (kn + kn5) * 0.5) * 0.5
    A = ((kn + kn5) * 0.5 - wr).normalized()
    an = getattr(person, "_anat", None) or {}
    Np = Vector(an.get("palm" + s, (0, 0, 0)))
    co = person._co
    w = person._w["body"] > 0.5
    rel = co - np.array(pc)
    d = np.linalg.norm(rel, axis=1)
    near = w & (d < 0.05)
    if Np.length < 0.5:      # fallback: principal thinnest axis of the hand verts
        pts = rel[near]
        _, _, vt = np.linalg.svd(pts - pts.mean(0))
        Np = Vector(vt[2])
    Np = (Np - A * Np.dot(A)).normalized()
    npn = np.array(Np)
    along = rel @ npn
    perp = np.linalg.norm(rel - along[:, None] * npn[None, :], axis=1)
    cand = near & (along > 0.0)
    i = int(np.argmin(np.where(cand, perp, 1e9)))
    S = Vector(co[i])
    cand = near & (along < 0.0)
    i = int(np.argmin(np.where(cand, perp, 1e9)))
    Sb = Vector(co[i])
    B = Np.cross(A).normalized()
    if B.dot(th - pc) < 0:
        B = -B
    L = (kn - wr).length
    return S, Sb, A, Np, B, L


def _scar_and_creases(person, side="R"):
    """Per-pixel (rest_position based) palm detail for the hero close-up:
    * the healed nail wound in the palm centre: a pale, slightly shiny, puckered round scar with a raised
      pinkish rim and radiating tension creases (no blood) - plus a smaller matching mark on the back;
    * the main palmar flexion creases (heart/head/life lines, wrist + finger-base creases) so the palm
      reads as a palm."""
    m = person.body.active_material
    if m is None or not m.use_nodes:
        return
    S, Sb, A, Np, B, L = _hand_frame(person, side)
    print("s16b palm frame: S", tuple(round(x, 4) for x in S), "L %.3f" % L)
    nt = m.node_tree
    M = _NM(nt)
    bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    ra = nt.nodes.new("ShaderNodeAttribute")
    ra.attribute_type = "GEOMETRY"
    ra.attribute_name = "rest_position"
    P_ = ra.outputs["Vector"]
    rel = M.v("SUBTRACT", P_, tuple(S))
    u = M.dot(rel, tuple(A))
    v = M.dot(rel, tuple(B))
    w = M.dot(rel, tuple(Np))
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 320.0
    nz.inputs["Detail"].default_value = 3.0
    M._in(nz.inputs["Vector"], P_)
    jit = M.m("MULTIPLY", M.m("SUBTRACT", nz.outputs["Fac"], 0.5), 0.0028)
    palm_side = M.smooth(w, -0.007, -0.002)
    # ---- scar (palm) ----
    ang = nt.nodes.new("ShaderNodeMath")
    ang.operation = "ARCTAN2"
    M._in(ang.inputs[0], v)
    M._in(ang.inputs[1], u)
    d = M.m("ADD", M.m("SQRT", M.m("ADD", M.m("POWER", M.m("DIVIDE", u, 1.15), 2.0), M.m("POWER", v, 2.0))), jit)
    # irregular, slightly star-shaped outline of a healed puncture
    n2 = nt.nodes.new("ShaderNodeTexNoise")              # irregular outline (low frequency)
    n2.inputs["Scale"].default_value = 140.0
    n2.inputs["Detail"].default_value = 2.0
    M._in(n2.inputs["Vector"], P_)
    d = M.m("MULTIPLY", d, M.m("ADD", 1.0, M.m("MULTIPLY", M.m("SUBTRACT", n2.outputs["Fac"], 0.5), 0.9)))
    core = M.m("MULTIPLY", M.smooth(d, 0.0066, 0.0036), palm_side)
    ring = M.m("MULTIPLY", M.m("MULTIPLY", M.smooth(d, 0.0038, 0.0078), M.smooth(d, 0.0135, 0.0078)), palm_side)
    rad = M.m("MULTIPLY", M.m("POWER", M.m("SINE", M.m("ADD", M.m("MULTIPLY", ang.outputs[0], 9.0),
                                                       M.m("MULTIPLY", nz.outputs["Fac"], 9.0))), 4.0),
              M.smooth(d, 0.016, 0.006))
    rad = M.m("MULTIPLY", rad, palm_side)
    # ---- back-of-hand mark ----
    relb = M.v("SUBTRACT", P_, tuple(Sb))
    ub, vb, wb = M.dot(relb, tuple(A)), M.dot(relb, tuple(B)), M.dot(relb, tuple(-Np))
    db = M.m("ADD", M.m("SQRT", M.m("ADD", M.m("POWER", M.m("DIVIDE", ub, 1.15), 2.0), M.m("POWER", vb, 2.0))), jit)
    back_side = M.smooth(wb, -0.007, -0.002)
    coreb = M.m("MULTIPLY", M.smooth(db, 0.0048, 0.0028), back_side)
    ringb = M.m("MULTIPLY", M.m("MULTIPLY", M.smooth(db, 0.0028, 0.0055), M.smooth(db, 0.0095, 0.0055)), back_side)
    core = M.m("MAXIMUM", core, coreb)
    ring = M.m("MAXIMUM", ring, ringb)
    # ---- palmar creases (normalised palm coords) ----
    U = M.m("DIVIDE", u, L)
    V = M.m("DIVIDE", v, L)

    cw = nt.nodes.new("ShaderNodeTexNoise")
    cw.inputs["Scale"].default_value = 60.0
    cw.inputs["Detail"].default_value = 2.0
    M._in(cw.inputs["Vector"], P_)
    wob = M.m("MULTIPLY", M.m("SUBTRACT", cw.outputs["Fac"], 0.5), 0.03)

    def crease(dist, width, lo, hi, x, fade=0.06):
        width *= 1.7
        line = M.smooth(M.m("ABSOLUTE", M.m("ADD", dist, wob)), width, 0.0)
        span = M.m("MULTIPLY", M.smooth(x, lo, lo + fade), M.smooth(x, hi, hi - fade))
        return M.m("MULTIPLY", line, span)
    # heart line: from the pinky edge (V=-0.5, U=0.24) rising towards between index/middle (V=0.1, U=0.38)
    t1 = M.m("DIVIDE", M.m("ADD", V, 0.5), 0.6)
    f1 = M.m("ADD", 0.24, M.m("MULTIPLY", 0.14, M.m("POWER", M.m("MAXIMUM", t1, 0.0), 1.6)))
    c1 = crease(M.m("SUBTRACT", U, f1), 0.012, -0.52, 0.12, V)
    # head line: from the thumb/index side (V=0.36, U=0.26) slanting down to the pinky side (V=-0.38, U=0.02)
    f2 = M.m("ADD", 0.02, M.m("MULTIPLY", 0.24, M.m("DIVIDE", M.m("ADD", V, 0.38), 0.74)))
    c2 = crease(M.m("SUBTRACT", U, f2), 0.011, -0.4, 0.38, V)
    # life line: arc around the thenar eminence, from (U=0.25, V=0.34) to the wrist (U=-0.45, V=0.12)
    t3 = M.m("DIVIDE", M.m("SUBTRACT", 0.25, U), 0.7)
    f3 = M.m("SUBTRACT", 0.34, M.m("MULTIPLY", 0.3, M.m("SINE", M.m("MULTIPLY", M.m("MAXIMUM", t3, 0.0), 1.9))))
    c3 = crease(M.m("SUBTRACT", V, f3), 0.012, -0.46, 0.27, U)
    # wrist creases + finger-base creases
    c4 = crease(M.m("SUBTRACT", U, -0.5), 0.009, -0.5, 0.45, V)
    c5 = crease(M.m("SUBTRACT", U, -0.56), 0.008, -0.45, 0.4, V)
    c6 = crease(M.m("SUBTRACT", U, M.m("ADD", 0.56, M.m("MULTIPLY", V, -0.08))), 0.01, -0.5, 0.2, V)
    cr = M.m("MAXIMUM", M.m("MAXIMUM", M.m("MAXIMUM", c1, c2), M.m("MAXIMUM", c3, c4)), M.m("MAXIMUM", c5, c6))
    cr = M.m("MULTIPLY", cr, M.m("MULTIPLY", palm_side, M.smooth(d, 0.006, 0.011)))   # not across the scar
    # ---- colour ----
    src = bsdf.inputs["Base Color"].links[0].from_socket
    col = M.mix(M.m("MULTIPLY", cr, 0.16), src, (0.72, 0.52, 0.46), "MULTIPLY")
    col = M.mix(M.m("MULTIPLY", ring, 0.5), col, (0.8, 0.56, 0.54), "MULTIPLY")
    col = M.mix(M.m("MULTIPLY", core, 0.42), col, (0.78, 0.55, 0.52))
    col = M.mix(M.m("MULTIPLY", rad, 0.15), col, (0.82, 0.64, 0.6), "MULTIPLY")
    nt.links.new(col, bsdf.inputs["Base Color"])
    # ---- roughness: glossy scar tissue ----
    if bsdf.inputs["Roughness"].is_linked:
        r0 = bsdf.inputs["Roughness"].links[0].from_socket
    else:
        r0 = bsdf.inputs["Roughness"].default_value
    r = M.m("SUBTRACT", r0, M.m("MULTIPLY", M.m("MAXIMUM", core, M.m("MULTIPLY", ring, 0.5)), 0.1))
    nt.links.new(r, bsdf.inputs["Roughness"])
    # ---- relief ----
    h = M.m("SUBTRACT", M.m("MULTIPLY", ring, 0.6), M.m("MULTIPLY", core, 0.45))
    h = M.m("ADD", h, M.m("MULTIPLY", rad, 0.35))
    h = M.m("ADD", h, M.m("MULTIPLY", M.m("MULTIPLY", nz.outputs["Fac"], core), 0.5))
    h = M.m("SUBTRACT", h, M.m("MULTIPLY", cr, 0.9))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.0009
    nt.links.new(h, bump.inputs["Height"])
    if bsdf.inputs["Normal"].is_linked:
        nt.links.new(bsdf.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def _mote_material(name="s16b_mote"):
    """Backlit dust: translucent (glows when the sun is behind it) + faint emission."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1)
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.25, 0.22, 0.18, 1)
    mx = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs[0], mx.inputs[0])
    nt.links.new(df.outputs[0], mx.inputs[1])
    nt.links.new(mx.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    return m


def build(ctx):
    NR = ctx.render_frames
    n = ctx.nframes
    fr = ctx.frame
    p1s, p1e = ctx.phrase_frames(0)
    p2s, p2e = ctx.phrase_frames(1)

    # ---------------- sky / sun (sunrise, behind him, screen left: clears his shoulder) ----------------
    sky = None                     # built below, once the sun direction (behind the hand) is known

    # ---------------- the risen Christ ----------------
    if "s16b_show" not in P.POSES:
        P.POSES["s16b_show"] = _show_pose_fn()
    j = P.make_person("jesus", "JESUS_RISEN", hair_strands=False, pose=None,
                      outfit_opts={"robe": {"sleeves": "3q"}})       # white linen sleeve at the bottom of frame
    j.rig.location = (0, 0, 0)
    j.update()
    sh = j.bone_world("upperarm01.R")
    # blessing: the right hand lifted in front of / above the shoulder, palm towards us (Luke 24:50)
    tgt = sh + Vector((0.06, -0.27, 0.45))            # lifted high, in front of / above the head
    cam_pos = tgt + Vector((-0.05, -0.82, -0.36))     # below and in front: looking up into the palm, sky behind
    face0 = (cam_pos - tgt).normalized()
    up0 = (Vector((0, 0, 1)) - face0 * face0.z).normalized()     # fingers up, perpendicular to the palm normal
    up0 = (up0 + Vector((0.12, 0, 0))).normalized()
    up0 = (up0 - face0 * up0.dot(face0)).normalized()
    t0 = tgt + Vector((0.0, 0.06, -0.2))
    face_in = Vector((0.75, -0.6, -0.1)).normalized()
    P.key_pose(j, 1, "s16b_show", target=t0, side="R", hand="relaxed", curl=0.9, face=face_in,
               up=(0.0, 0.0, 1.0), ground=False)
    f_open = int(p1e - 4)
    P.key_pose(j, f_open, "s16b_show", target=tgt, side="R", hand="relaxed", curl=0.2, face=face0, up=up0,
               ground=False)
    P.key_pose(j, NR, "s16b_show", target=tgt + Vector((0.0, -0.012, 0.008)), side="R", hand="relaxed", curl=0.15,
               face=face0, up=up0, ground=False)
    P.expression(j, "peace")
    _scar_and_creases(j, "R")
    for key in ("teeth", "tongue", "beard"):           # chin/mouth stay below the frame
        o = j.parts.get(key)
        if o is not None:
            o.hide_render = True

    # ---------------- camera ----------------
    aim1 = tgt + Vector((0.0, 0.0, 0.04))
    aim0 = (t0 + tgt) * 0.5 + Vector((0.0, 0.0, 0.02))
    cam = C.camera(loc=cam_pos, target=aim0, lens=70, fstop=2.0, focus=(cam_pos - tgt).length, name="s16b_cam")
    c0, c1 = cam_pos + (cam_pos - tgt) * 0.08, tgt + (cam_pos - tgt) * 0.8

    def path(f):
        u = C.ease_in_out(max(0.0, min(1.0, (f - 1) / float(NR - 1))))
        ua = C.ease_in_out(max(0.0, min(1.0, (f - 1) / float(f_open + 10))))
        loc = c0.lerp(c1, u) + C.shake(f, amp=0.002, freq=0.3, seed=3)
        return loc, aim1 + (aim0 - aim1) * 0.25 * (1.0 - ua)
    C.animate_camera(cam, path)
    for f in range(1, NR + 1, 4):
        loc, t = path(f)
        ua = C.ease_in_out(max(0.0, min(1.0, (f - 1) / float(f_open))))
        cam.data.dof.focus_distance = (t0.lerp(tgt, ua) - loc).length - 0.008
        cam.data.dof.keyframe_insert("focus_distance", frame=f)

    # ---------------- sky: the sun stands just behind the lifted hand ----------------
    axis = (tgt - cam_pos).normalized()
    rgt = axis.cross(Vector((0, 0, 1))).normalized()
    upv = rgt.cross(axis).normalized()
    sdir = (axis + rgt * -0.05 + upv * 0.06).normalized()           # ~4.5 deg up-left of the palm centre
    sun_el = math.degrees(math.asin(sdir.z))
    sun_az = math.degrees(math.atan2(sdir.x, -sdir.y))
    sky = E.sky(mood="sunrise", sun_az=sun_az, ctx=ctx, sun_el=sun_el, strength=0.5, bg=0.75, tint=(1.0, 0.74, 0.5))
    sun = sky["sun"]
    sun.data.energy = 3.0
    # warm halo around the (unseen) sun disc: camera-only emissive billboard far behind the hand
    gc = cam_pos + sdir * 60.0
    halo = C.prim("plane", name="s16b_sunhalo", loc=tuple(gc), size=40.0)
    halo.rotation_euler = C.look_rot(gc, cam_pos)
    halo.visible_shadow = False
    halo.visible_diffuse = False
    halo.visible_glossy = False
    halo.visible_volume_scatter = False
    hm = bpy.data.materials.new("s16b_halo")
    hm.use_nodes = True
    hm.surface_render_method = "BLENDED"
    nt = hm.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    gr = nt.nodes.new("ShaderNodeTexGradient")
    gr.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.05, 0.05, 0.05)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], gr.inputs["Vector"])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 3.0
    nt.links.new(gr.outputs["Fac"], pw.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.6, 0.28, 1)
    sm = nt.nodes.new("ShaderNodeMath")
    sm.operation = "MULTIPLY"
    sm.inputs[1].default_value = 3.5
    nt.links.new(pw.outputs[0], sm.inputs[0])
    nt.links.new(sm.outputs[0], em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    ad = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(em.outputs[0], ad.inputs[0])
    nt.links.new(tr.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    C.assign(halo, hm)

    # ---------------- light ----------------
    # warm bounce (gold reflector) raking the palm from screen right: close + narrow so the robe stays darker
    bl = C.light("AREA", loc=tuple(tgt + Vector((0.38, -0.42, -0.32))), energy=10.0, temp=4300, target=tuple(tgt),
                 size=0.4, name="s16b_bounce", shadow=False)
    bl.data.spread = math.radians(50)
    fl = C.light("AREA", loc=tuple(tgt + Vector((-0.3, -0.6, -0.3))), energy=1.5, temp=5200, target=tuple(tgt),
                 size=0.6, name="s16b_fill", shadow=False)
    fl.data.spread = math.radians(60)
    # dust motes: translucent, so the ones in the sun behind the hand glitter
    mo = S.dust(center=tuple(tgt + Vector((0.02, -0.1, -0.05))), size=(0.5, 0.7, 0.6), count=230, radius=0.0011,
                color=(1.0, 0.9, 0.75), emission=0.0, speed=0.04, amp=0.06, seed=4, name="s16b_motes")
    mm = _mote_material()
    for nd in mo.modifiers[0].node_group.nodes:
        if nd.bl_idname == "GeometryNodeSetMaterial":
            nd.inputs["Material"].default_value = mm

    ctx.samples = 5
    ctx.render_opts = {"volumetrics": "low"}
    ctx.interp = True
    ctx.post = {"grade": "warm", "bloom": 0.36, "bloom_threshold": 0.62, "exposure": -0.08, "contrast": 1.06,
                "saturation": 0.94, "vignette": 0.24}
