"""Give the oil-lamp flames a layered, translucent look (blue base, white-gold core, orange tip, soft edges)."""
import bpy
m = bpy.data.materials.new("M_flame_v2")
m.use_nodes = True
m.blend_method = 'BLEND' if hasattr(m, "blend_method") else None
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
ramp = nt.nodes.new("ShaderNodeValToRGB")
cr = ramp.color_ramp
cr.elements[0].position = 0.0; cr.elements[0].color = (0.15, 0.25, 1.0, 1)
cr.elements[1].position = 1.0; cr.elements[1].color = (1.0, 0.25, 0.03, 1)
e = cr.elements.new(0.18); e.color = (1.0, 0.95, 0.85, 1)
e = cr.elements.new(0.45); e.color = (1.0, 0.78, 0.35, 1)
e = cr.elements.new(0.8); e.color = (1.0, 0.45, 0.08, 1)
nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(ramp.outputs["Color"], em.inputs["Color"])
strength = nt.nodes.new("ShaderNodeMapRange")
strength.inputs["From Min"].default_value = 0.0; strength.inputs["From Max"].default_value = 1.0
strength.inputs["To Min"].default_value = 9.0; strength.inputs["To Max"].default_value = 3.0
nt.links.new(sep.outputs["Z"], strength.inputs["Value"])
nt.links.new(strength.outputs["Result"], em.inputs["Strength"])
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.35
tr = nt.nodes.new("ShaderNodeBsdfTransparent")
mix = nt.nodes.new("ShaderNodeMixShader")
pw = nt.nodes.new("ShaderNodeMath"); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.6
nt.links.new(lw.outputs["Facing"], pw.inputs[0])
# fade the tip too
tip = nt.nodes.new("ShaderNodeMapRange")
tip.inputs["From Min"].default_value = 0.65; tip.inputs["From Max"].default_value = 1.0
tip.inputs["To Min"].default_value = 0.0; tip.inputs["To Max"].default_value = 0.9
nt.links.new(sep.outputs["Z"], tip.inputs["Value"])
mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
nt.links.new(pw.outputs[0], mx.inputs[0]); nt.links.new(tip.outputs["Result"], mx.inputs[1])
nt.links.new(mx.outputs[0], mix.inputs["Fac"])
nt.links.new(em.outputs[0], mix.inputs[1])
nt.links.new(tr.outputs[0], mix.inputs[2])
nt.links.new(mix.outputs[0], out.inputs["Surface"])
n = 0
for o in bpy.data.objects:
    if o.name.startswith("FLAME_") and o.type == 'MESH':
        o.data.materials.clear()
        o.data.materials.append(m)
        o.visible_shadow = False
        n += 1
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print("FLAME_OK", n)
