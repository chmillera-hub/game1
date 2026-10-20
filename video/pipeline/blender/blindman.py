"""Turn the PH3 character into the man born blind for the flashback inserts: no head covering or shawl,
plain undyed tunic, warmer light."""
import bpy


def apply(rigs, n):
    rig = rigs.get("PH3")
    if rig is None:
        return
    for o in rig.children:
        if o.name.endswith((".tallit", ".headband")):
            o.hide_render = True
            o.hide_viewport = True
        if o.name.endswith(".headcover"):
            for slot in o.material_slots:
                m = slot.material
                if m and m.use_nodes:
                    for nd in m.node_tree.nodes:
                        if nd.type == 'VALTORGB':
                            nd.color_ramp.elements[0].color = (0.16, 0.10, 0.06, 1)
                            nd.color_ramp.elements[1].color = (0.26, 0.17, 0.10, 1)
        if o.name.endswith((".tunic", ".skirt", ".robe_legs")):
            for slot in o.material_slots:
                m = slot.material
                if m and m.use_nodes:
                    for nd in m.node_tree.nodes:
                        if nd.type == 'VALTORGB':
                            nd.color_ramp.elements[0].color = (0.30, 0.24, 0.16, 1)
                            nd.color_ramp.elements[1].color = (0.45, 0.37, 0.25, 1)
