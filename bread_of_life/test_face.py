"""Contact sheet renderer for rig development."""
import sys

import numpy as np
import skia

from gfx import fill, hexc
import rig


def sheet(char, variants, out, cols=4, cell=(360, 480), S=95, bg="#9fb7c9"):
    rows = (len(variants) + cols - 1) // cols
    W, H = cols * cell[0], rows * cell[1]
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(*hexc(bg)))
    for i, P in enumerate(variants):
        r, c = divmod(i, cols)
        x = c * cell[0] + cell[0] / 2
        y = r * cell[1] + cell[1] * 0.78
        char.draw(cv, P, x, y, S)
    img = surf.makeImageSnapshot()
    img.save(out, skia.kPNG)


if __name__ == "__main__":
    import chars
    name = sys.argv[1] if len(sys.argv) > 1 else "jesus"
    ch = chars.CHARS[name]
    V = []
    for yaw in (-30, -15, 0, 15, 30):
        V.append(dict(yaw=yaw))
    V += [
        dict(m_open=0.6, m_wide=0.2),
        dict(m_open=0.4, m_round=0.8),
        dict(m_smile=0.7, lo_l=0.5, lo_r=0.5, eo_l=0.75, eo_r=0.75),
        dict(bi_l=0.8, bi_r=0.8, br_l=0.1, br_r=0.1, eo_l=0.75, eo_r=0.75, m_smile=-0.4, wet=1.0, tear_r=0.7, gy=0.4),
        dict(bi_l=-0.6, bi_r=-0.6, bfur=0.8, eo_l=1.05, eo_r=1.05),
        dict(br_l=0.9, br_r=0.9, eo_l=1.2, eo_r=1.2, m_open=0.35, m_round=0.4),
        dict(eo_l=0.0, eo_r=0.0),
        dict(yaw=20, pitch=12, gx=0.6, gy=0.5, eo_l=0.7, eo_r=0.7),
        dict(yaw=-25, pitch=-10, roll=8, m_smile=0.3, lo_l=0.25, lo_r=0.25),
        dict(br_l=0.7, br_r=-0.3, bi_r=-0.3, eo_l=0.85, eo_r=0.7, m_smirk=0.6, yaw=10),
        dict(eo_l=0.1, eo_r=0.1, lo_l=0.9, lo_r=0.9, m_smile=0.9, m_open=0.25, m_teeth=1.0),
    ]
    sheet(ch, V, sys.argv[2] if len(sys.argv) > 2 else "/tmp/sheet.png")
