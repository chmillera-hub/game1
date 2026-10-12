"""Large close-up renders for rig development."""
import sys
import skia
from gfx import hexc
import chars

def cu(name, variants, out, S=150, cell=(540, 720), cols=3, bg="#a9bccb"):
    rows = (len(variants) + cols - 1) // cols
    surf = skia.Surface(cols * cell[0], rows * cell[1])
    cv = surf.getCanvas()
    cv.clear(skia.Color4f(*hexc(bg)))
    ch = chars.CHARS[name]
    for i, P in enumerate(variants):
        r, c = divmod(i, cols)
        cv.save()
        cv.clipRect(skia.Rect.MakeXYWH(c * cell[0], r * cell[1], cell[0], cell[1]))
        ch.draw(cv, P, c * cell[0] + cell[0] / 2, r * cell[1] + cell[1] * 0.80, S)
        cv.restore()
    surf.makeImageSnapshot().save(out, skia.kPNG)

if __name__ == "__main__":
    name = sys.argv[1]
    V = [dict(yaw=0), dict(yaw=22, gx=-0.3), dict(yaw=-22, m_open=0.5, m_wide=0.3),
         dict(yaw=10, bi_l=0.7, bi_r=0.7, eo_l=0.8, eo_r=0.8, wet=1, m_smile=-0.3, gy=0.3),
         dict(yaw=-8, m_smile=0.6, lo_l=0.45, lo_r=0.45, eo_l=0.8, eo_r=0.8),
         dict(yaw=35, pitch=8, eo_l=0.9, eo_r=0.9)]
    cu(name, V, sys.argv[2])
