"""Hillside flock: heads lift at the shepherd's voice, then the sheep drift toward him."""
import bpy, math
import numpy as np
from mathutils import Vector
import perform as pf

FPS = 24


def lift_heads(n, t_voice=0.4, follow_after=2.2):
    from shotbuild import fcurve_set
    rng = np.random.default_rng(7)
    shep = bpy.data.objects.get("MARK_SHEPHERD")
    sp = shep.location if shep else Vector((0, 0, 0))
    t = np.arange(n) / FPS
    frames = np.arange(n) + 1
    sheep = [o for o in bpy.data.objects if (o.name.startswith("SHEEP_") and not o.name.endswith("_HEAD"))
             or o.name == "PROP_LAMB"]
    for s in sheep:
        head = bpy.data.objects.get(s.name + "_HEAD")
        delay = t_voice + rng.uniform(0.0, 0.7)
        if head:
            x0 = math.radians(-60) if s.get("grazing") else head.rotation_euler.x
            up = math.radians(rng.uniform(-8, 4))
            u = pf.smoothstep((t - delay) / 0.45)
            vals = x0 + (up - x0) * u
            # a small ear-flick / look-around wobble once up
            vals += np.where(u > 0.99, pf.value_noise(n, FPS, 0.8, rng.integers(1000)) * 0.06, 0.0)
            fcurve_set(head, "rotation_euler", 0, frames, vals)
        # walk toward the shepherd
        d = (sp - s.location)
        d.z = 0
        dist = d.length
        step = min(1.2, max(0.0, dist - 1.5)) * rng.uniform(0.5, 1.0)
        dn = d.normalized()
        start_walk = follow_after + rng.uniform(0.0, 0.6)
        u = pf.smoothstep((t - start_walk) / 2.5)
        P = np.array([(s.location + dn * step * k)[:] for k in u])
        walking = (u > 0.01) & (u < 0.99)
        P[walking, 2] += np.abs(np.sin(t[walking] * 2 * math.pi * 1.6)) * 0.01
        for i in range(3):
            fcurve_set(s, "location", i, frames, P[:, i])
        # turn toward the shepherd as they start walking
        yaw0 = s.rotation_euler.z
        yaw1 = math.atan2(-dn.x, dn.y) + math.pi
        dy = (yaw1 - yaw0 + math.pi) % (2 * math.pi) - math.pi
        fcurve_set(s, "rotation_euler", 2, frames, yaw0 + dy * u * 0.8)
