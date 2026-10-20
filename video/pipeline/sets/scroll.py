import sys; sys.path.insert(0, "/home/user/game1/video/pipeline/sets"); from _common import *
import subprocess
TEX = "/opt/work/props/psalm82.png"
W, H = 0.60, 0.30            # parchment visible area (m) at unroll=1
TZ = 0.76                    # table top height
RX = 0.30                    # right roller x
# verse 6 placement in texture (fraction of image), computed by generator below
GEN = r'''
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features
import random, json
random.seed(82)
Wp,Hp=2048,1024
img=Image.new("RGB",(Wp,Hp),(214,190,146))
px=img.load()
noise=Image.effect_noise((Wp//8,Hp//8),40).resize((Wp,Hp),Image.BICUBIC)
base=Image.new("RGB",(Wp,Hp),(222,198,152)); dark=Image.new("RGB",(Wp,Hp),(178,145,98))
img=Image.composite(base,dark,noise.point(lambda v:min(255,v+90)))
d=ImageDraw.Draw(img)
raqm=features.check("raqm")
font=ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerif.ttf",44,layout_engine=ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC)
big=ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSerif.ttf",50,layout_engine=ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC)
import unicodedata
def prep(s):
    if raqm: return s
    s="".join(c for c in s if not unicodedata.combining(c))
    return s[::-1]
v6="אֲנִי־אָמַרְתִּי אֱלֹהִים אַתֶּם וּבְנֵי עֶלְיוֹן כֻּלְּכֶם"
cols=[
["מִזְמוֹר לְאָסָף","אֱלֹהִים נִצָּב בַּעֲדַת־אֵל","בְּקֶרֶב אֱלֹהִים יִשְׁפֹּט","עַד־מָתַי תִּשְׁפְּטוּ־עָוֶל","וּפְנֵי רְשָׁעִים תִּשְׂאוּ־סֶלָה","שִׁפְטוּ־דַל וְיָתוֹם","עָנִי וָרָשׁ הַצְדִּיקוּ","פַּלְּטוּ־דַל וְאֶבְיוֹן","מִיַּד רְשָׁעִים הַצִּילוּ","לֹא יָדְעוּ וְלֹא יָבִינוּ","בַּחֲשֵׁכָה יִתְהַלָּכוּ","יִמּוֹטוּ כָּל־מוֹסְדֵי אָרֶץ","V6A","V6B","אָכֵן כְּאָדָם תְּמוּתוּן","וּכְאַחַד הַשָּׂרִים תִּפֹּלוּ","קוּמָה אֱלֹהִים שָׁפְטָה הָאָרֶץ","כִּי־אַתָּה תִנְחַל בְּכָל־הַגּוֹיִם"],
["שִׁיר מִזְמוֹר לְאָסָף","אֱלֹהִים אַל־דֳּמִי־לָךְ","אַל־תֶּחֱרַשׁ וְאַל־תִּשְׁקֹט אֵל","כִּי־הִנֵּה אוֹיְבֶיךָ יֶהֱמָיוּן","וּמְשַׂנְאֶיךָ נָשְׂאוּ רֹאשׁ","עַל־עַמְּךָ יַעֲרִימוּ סוֹד","וְיִתְיָעֲצוּ עַל־צְפוּנֶיךָ","אָמְרוּ לְכוּ וְנַכְחִידֵם מִגּוֹי","וְלֹא־יִזָּכֵר שֵׁם־יִשְׂרָאֵל עוֹד","כִּי נוֹעֲצוּ לֵב יַחְדָּו","עָלֶיךָ בְּרִית יִכְרֹתוּ","אָהֳלֵי אֱדוֹם וְיִשְׁמְעֵאלִים","מוֹאָב וְהַגְרִים","גְּבָל וְעַמּוֹן וַעֲמָלֵק","פְּלֶשֶׁת עִם־יֹשְׁבֵי צוֹר","גַּם־אַשּׁוּר נִלְוָה עִמָּם","הָיוּ זְרוֹעַ לִבְנֵי־לוֹט סֶלָה"],
["מַה־יְּדִידוֹת מִשְׁכְּנוֹתֶיךָ","יְהוָה צְבָאוֹת","נִכְסְפָה וְגַם־כָּלְתָה נַפְשִׁי","לְחַצְרוֹת יְהוָה","לִבִּי וּבְשָׂרִי יְרַנְּנוּ","אֶל אֵל־חָי","גַּם־צִפּוֹר מָצְאָה בַיִת","וּדְרוֹר קֵן לָהּ","אַשְׁרֵי יוֹשְׁבֵי בֵיתֶךָ","עוֹד יְהַלְלוּךָ סֶּלָה","אַשְׁרֵי אָדָם עוֹז־לוֹ בָךְ","מְסִלּוֹת בִּלְבָבָם","עֹבְרֵי בְּעֵמֶק הַבָּכָא","מַעְיָן יְשִׁיתוּהוּ","יֵלְכוּ מֵחַיִל אֶל־חָיִל","יֵרָאֶה אֶל־אֱלֹהִים בְּצִיּוֹן"],
]
margin=90; colw=(Wp-2*margin)//3; lh=48; top=110
v6box=None
for ci,lines in enumerate(cols):
    right=Wp-margin-ci*colw-30
    y=top
    for ln in lines:
        if ln in("V6A","V6B"):
            parts=v6.split(" ")
            s=" ".join(parts[:3]) if ln=="V6A" else " ".join(parts[3:])
            f=big
        else: s=ln; f=font
        t=prep(s)
        kw={"direction":"rtl"} if raqm else {}
        bb=d.textbbox((0,0),t,font=f,**kw); w=bb[2]-bb[0]
        x=right-w
        ink=random.randint(40,70)
        d.text((x+random.uniform(-2,2),y),t,font=f,fill=(ink+20,ink-5,ink-25),**kw)
        if ln=="V6A": y6a=y
        if ln=="V6B": v6box=(right-colw+60,y6a,right,y+lh)
        y+=lh
img=img.filter(ImageFilter.GaussianBlur(0.7))
# ink unevenness / stains
st=Image.effect_noise((Wp//32,Hp//32),60).resize((Wp,Hp),Image.BICUBIC)
stain=Image.new("RGB",(Wp,Hp),(150,115,70))
img=Image.composite(stain,img,st.point(lambda v:max(0,v-170)*2))
# darken edges
mask=Image.new("L",(Wp,Hp),0); md=ImageDraw.Draw(mask); md.rectangle((25,18,Wp-25,Hp-18),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(30))
img=Image.composite(img,Image.new("RGB",(Wp,Hp),(120,88,52)),mask)
img.save(OUT)
cx=(v6box[0]+v6box[2])/2/Wp; cy=(v6box[1]+v6box[3])/2/Hp
print("V6",cx,cy,raqm)
'''
def make_tex():
    r = subprocess.run(["python3", "-c", "OUT=%r\n" % TEX + GEN], capture_output=True, text=True)
    print(r.stdout, r.stderr)
    for l in r.stdout.splitlines():
        if l.startswith("V6"):
            p = l.split(); return float(p[1]), float(p[2])
    return 0.15, 0.5

def nt(m): return m.node_tree.nodes, m.node_tree.links

def wood_mat(name, col, scale=6.0):
    m = principled(name); n, L = nt(m); b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale*0.15, scale*0.15, scale*3)  # grain along X stretched
    mp.inputs["Scale"].default_value = (scale*0.25, scale*4, scale*0.25)
    L.new(tc.outputs["Object"], mp.inputs[0])
    wv = n.new("ShaderNodeTexWave"); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'
    wv.inputs["Scale"].default_value = 3; wv.inputs["Distortion"].default_value = 14; wv.inputs["Detail"].default_value = 3
    L.new(mp.outputs[0], wv.inputs[0])
    no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 4; L.new(mp.outputs[0], no.inputs[0])
    mx = n.new("ShaderNodeMix"); mx.data_type = 'FLOAT'; L.new(wv.outputs["Fac"], mx.inputs[2]); L.new(no.outputs["Fac"], mx.inputs[3]); mx.inputs[0].default_value = 0.55
    cr = n.new("ShaderNodeValToRGB"); L.new(mx.outputs[0], cr.inputs[0])
    cr.color_ramp.elements[0].color = (*[c*0.45 for c in col], 1); cr.color_ramp.elements[1].color = (*col, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.35; rr.inputs[4].default_value = 0.6
    L.new(no.outputs["Fac"], rr.inputs[0]); L.new(rr.outputs[0], b.inputs["Roughness"])
    bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; bp.inputs["Distance"].default_value = 0.002
    L.new(mx.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def parch_mat(texref, tex=True):
    m = principled("M_parchment", (0.8, 0.7, 0.5), 0.75); n, L = nt(m); b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); tc.object = texref
    no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 60; no.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], no.inputs[0])
    if tex:
        img = n.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(TEX); img.extension = 'CLIP'
        L.new(tc.outputs["Object"], img.inputs[0])  # texref sits at image corner, scaled to W x H
        L.new(img.outputs["Color"], b.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.6; rr.inputs[4].default_value = 0.9
    L.new(no.outputs["Fac"], rr.inputs[0]); L.new(rr.outputs[0], b.inputs["Roughness"])
    bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; bp.inputs["Distance"].default_value = 0.0005
    L.new(no.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Subsurface Weight"].default_value = 0.05
    return m

def wall_mat():
    m = principled("M_wall", (0.55, 0.47, 0.38), 0.9); n, L = nt(m); b = n["Principled BSDF"]
    no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 8; no.inputs["Detail"].default_value = 6
    cr = n.new("ShaderNodeValToRGB"); L.new(no.outputs["Fac"], cr.inputs[0])
    cr.color_ramp.elements[0].color = (0.38, 0.31, 0.24, 1); cr.color_ramp.elements[1].color = (0.6, 0.52, 0.42, 1)
    L.new(cr.outputs[0], b.inputs["Base Color"])
    bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(no.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m

def bevel(o, w=0.004, seg=2):
    md = o.modifiers.new("Bevel", 'BEVEL'); md.width = w; md.segments = seg; md.limit_method = 'ANGLE'

def cube(name, loc, dims, mat, col):
    bpy.ops.mesh.primitive_cube_add(location=loc); o = bpy.context.object; o.name = name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2); bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat); link(o, col); return o

def roller(name, x, mat_wood, mat_parch, col, rad):
    """Roller along Y: rolled parchment cylinder + wooden rod with turned handles."""
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=rad, depth=H, location=(0, 0, 0), rotation=(math.pi/2, 0, 0))
    p = bpy.context.object; p.name = name + "_roll"; p.data.materials.append(mat_parch); bpy.ops.object.shade_smooth(); parts.append(p)
    # turned rod: lathe profile via screw of a polyline
    prof = [(0.006, 0), (0.012, 0.005), (0.015, 0.02), (0.010, 0.035), (0.008, 0.05), (0.016, 0.065), (0.018, 0.08), (0.012, 0.095), (0.004, 0.1)]
    for side in (1, -1):
        me = bpy.data.meshes.new(name + "_handle"); verts = [(r, 0, z) for r, z in prof]
        me.from_pydata(verts, [(i, i+1) for i in range(len(verts)-1)], [])
        h = bpy.data.objects.new(f"{name}_handle_{'R' if side>0 else 'L'}", me); col.objects.link(h)
        s = h.modifiers.new("Lathe", 'SCREW'); s.steps = 24; s.render_steps = 24; s.use_smooth_shade = True
        h.rotation_euler = (-side*math.pi/2, 0, 0); h.location = (0, side*(H/2 - 0.005), 0)
        h.data.materials.append(mat_wood); parts.append(h)
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.007, depth=H+0.01, rotation=(math.pi/2, 0, 0))
    rod = bpy.context.object; rod.name = name + "_rod"; rod.data.materials.append(mat_wood); parts.append(rod)
    root = bpy.data.objects.new("PROP_" + name, None); root.empty_display_type = 'PLAIN_AXES'; col.objects.link(root)
    root.location = (x, 0, TZ + rad)
    for o in parts:
        link(o, col); o.parent = root
    return root

def main():
    scn = reset_scene()
    v6u, v6v = make_tex()
    col = collection("SET_scroll"); lc = collection("LIGHTS_scroll")
    m_table = wood_mat("M_table_wood", (0.16, 0.08, 0.04), 5)
    m_handle = wood_mat("M_handle_wood", (0.30, 0.16, 0.07), 20)
    m_wall = wall_mat()
    # room
    cube("floor", (0, 0, -0.01), (6, 6, 0.02), principled("M_floor_stone", (0.25, 0.22, 0.19), 0.85), col)
    cube("wall_back", (0, 1.6, 1.5), (6, 0.2, 3), m_wall, col)
    # table
    top = cube("PROP_table_top", (0, 0.05, TZ - 0.025), (1.4, 0.85, 0.05), m_table, col); bevel(top, 0.006, 3)
    for sx in (-0.62, 0.62):
        for sy in (-0.3, 0.4):
            lg = cube("table_leg", (sx, sy, (TZ-0.05)/2), (0.07, 0.07, TZ-0.05), m_table, col); bevel(lg)
    cube("table_apron", (0, 0.05, TZ-0.09), (1.3, 0.75, 0.08), m_table, col)
    # texture reference: object coords map 0..1 over W x H, origin at left/bottom of full text area
    texref = bpy.data.objects.new("TEXREF_scroll", None); col.objects.link(texref)
    texref.location = (RX - W, -H/2, TZ); texref.scale = (W, H, 1)
    m_parch = parch_mat(texref); m_rollp = parch_mat(texref, tex=False); m_rollp.name = "M_parchment_rolled"
    m_rollp.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.3, 0.17, 1)
    # parchment sheet: origin at right roller, extends to -X by W*scale.x
    me = bpy.data.meshes.new("parchment")
    me.from_pydata([(0, -H/2, 0), (0, H/2, 0), (-W, H/2, 0), (-W, -H/2, 0)], [], [(0, 1, 2, 3)])
    sheet = bpy.data.objects.new("PROP_parchment", me); col.objects.link(sheet)
    sheet.location = (RX, 0, TZ + 0.0015); sheet.data.materials.append(m_parch)
    rad = 0.022
    rR = roller("roller_R", RX + rad*0.6, m_handle, m_rollp, col, rad)
    rL = roller("roller_L", RX - 0.15*W - rad*0.6, m_handle, m_rollp, col, rad)
    # control
    ctrl = bpy.data.objects.new("SCROLL_CTRL", None); ctrl.empty_display_type = 'CUBE'; ctrl.empty_display_size = 0.03
    col.objects.link(ctrl); ctrl.location = (RX + 0.12, -0.25, TZ)
    ctrl["unroll"] = 0.15
    ui = ctrl.id_properties_ui("unroll"); ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)
    def drv(obj, path, idx, expr):
        fc = obj.driver_add(path, idx); d = fc.driver; d.type = 'SCRIPTED'
        v = d.variables.new(); v.name = "u"; v.targets[0].id = ctrl; v.targets[0].data_path = '["unroll"]'
        d.expression = expr
    drv(sheet, "scale", 0, "max(u,0.001)")
    drv(rL, "location", 0, f"{RX} - u*{W} - {rad*0.6}")
    drv(rL, "rotation_euler", 1, f"-u*{W}/{rad}")   # roll as it travels
    for fr, v in ((1, 0.15), (48, 1.0)):
        ctrl["unroll"] = v; ctrl.keyframe_insert('["unroll"]', frame=fr)
    for fc in ctrl.animation_data.action.fcurves:
        for k in fc.keyframe_points: k.interpolation = 'BEZIER'
    scn.frame_start, scn.frame_end = 1, 48
    # finger mark at verse 6
    fx = RX - W + v6u*W; fy = -H/2 + (1 - v6v)*H
    mark("FINGER", (fx, fy, TZ + 0.002), 0.0, col)
    # lights
    ld = bpy.data.lights.new("WINDOW_KEY", 'AREA'); ld.energy = 90; ld.size = 1.0; ld.size_y = 1.4; ld.shape = 'RECTANGLE'
    ld.color = (1.0, 0.9, 0.75)
    lo = bpy.data.objects.new("WINDOW_KEY", ld); lc.objects.link(lo); lo.location = (1.6, -0.6, 2.6); look_at(lo, (0, 0, TZ))
    bd = bpy.data.lights.new("BOUNCE_FILL", 'AREA'); bd.energy = 15; bd.size = 2.0; bd.color = (1.0, 0.85, 0.7)
    bo = bpy.data.objects.new("BOUNCE_FILL", bd); lc.objects.link(bo); bo.location = (-1.2, -1.2, 1.2); look_at(bo, (0, 0, TZ))
    w = bpy.data.worlds.new("W_scroll"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.045, 0.04, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    scn.world = w
    # camera: 65mm, ~40 deg down, focus on verse
    tgt = Vector((fx, fy, TZ)); dist = 1.05; a = math.radians(40)
    cam = camhint("CU", (fx - 0.05, fy - dist*math.cos(a), TZ + dist*math.sin(a)), tgt, 65.0, col)
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = bpy.data.objects["MARK_FINGER"]; cam.data.dof.aperture_fstop = 4.0
    scn.camera = cam
    scn.render.resolution_x, scn.render.resolution_y = 540, 960
    if "--preview" in sys.argv:
        scn.frame_set(48)
        render_previews("scroll")
    scn.frame_set(1)
    save(out_path())
main()
