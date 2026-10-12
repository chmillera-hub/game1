"""Full-body test sheet for the rig (gestures, rest pose, legs)."""
import sys

import skia

import chars
from gfx import hexc

G = {
    "teach": dict(target=(3.7, 3.4, 1.0), hand="open", palm=(0.1, -1.0, 0.1), wrist=12),
    "reach": dict(target=(4.6, 2.5, 0.8), hand="open", palm=(0.25, -0.85, 0.45), wrist=8),
    "heart": dict(target=(0.1, 2.5, 1.1), hand="flat", palm=(0.0, 0.0, -1.0), wrist=12),
    "up": dict(target=(3.5, -1.3, 0.8), hand="open", palm=(0.15, -0.6, 0.8), wrist=5),
    "self": dict(target=(0.85, 2.45, 1.15), hand="soft", palm=(-0.1, 0.05, -1.0), wrist=8),
    "point": dict(target=(1.5, 1.1, 1.6), hand="point", palm=(-0.5, 0.0, 0.85), wrist=-5),
    "cross_r": dict(target=(-1.2, 3.0, 1.15), hand="relaxed", palm=(0.0, 0.2, -1.0), wrist=10, pole=(0.6, 1.0, -0.15)),
    "cross_l": dict(target=(1.15, 3.2, 0.95), hand="relaxed", palm=(0.0, 0.2, -1.0), wrist=10, pole=(0.6, 1.0, -0.15)),
    "scratch": dict(target=(1.5, -1.5, 0.3), hand="relaxed", palm=(-1.0, 0.3, -0.4)),
    "clutch": dict(target=(-0.15, 2.3, 1.05), hand="soft", palm=(0.0, 0.0, -1.0), wrist=10),
    "mouth": dict(target=(-0.25, 0.45, 1.4), hand="cup", palm=(0.0, 0.0, -1.0), layer="front"),
}

V = [("jesus", {}), ("jesus", dict(arm_r=G["teach"], yaw=12)), ("jesus", dict(arm_r=G["reach"], yaw=18)),
     ("jesus", dict(arm_l=G["heart"], yaw=8)), ("jesus", dict(arm_r=G["up"], yaw=10, pitch=-8)),
     ("peter", {}), ("peter", dict(arm_r=G["scratch"], yaw=15)), ("miriam", {}), ("miriam", dict(arm_l=G["clutch"], yaw=-12)),
     ("eli", dict(arm_r=G["cross_r"], arm_l=G["cross_l"], yaw=-12)), ("eli", dict(arm_r=G["point"], yaw=-15))]

if __name__ == "__main__":
    S = float(sys.argv[2]) if len(sys.argv) > 2 else 36
    cols = 6
    cw, ch_ = int(S * 11.5), int(S * 22.5)
    rows = (len(V) + cols - 1) // cols
    surf = skia.Surface(cw * cols, ch_ * rows)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(*hexc("#b9c8d2")))
    for i, (who, P) in enumerate(V):
        r, c = divmod(i, cols)
        chars.CHARS[who].draw(cv, P, c * cw + cw / 2, r * ch_ + S * 4.0, S)
    surf.makeImageSnapshot().save(sys.argv[1], skia.kPNG)
