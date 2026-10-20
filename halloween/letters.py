"""Kid handwriting: 'TOO MOM I LOVE YOU' as wobbly strokes, like the drawing."""
import math

import skia

from gfx import GRAPHITE, PAPER, Xf, fill, open_path, pencil, stroke, wobble

# strokes in a 100 x 140 box (y down), each stroke a polyline
GLYPHS = {
    "T": [[(4, 6), (52, 2), (98, 8)], [(50, 4), (49, 72), (51, 138)]],
    "O": [[(50, 4), (16, 24), (4, 70), (16, 118), (50, 136), (84, 118), (96, 70), (84, 22), (50, 4), (40, 8)]],
    "M": [[(6, 138), (8, 4), (50, 84), (92, 2), (96, 138)]],
    "I": [[(48, 2), (50, 136)]],
    "L": [[(10, 2), (8, 134), (92, 136)]],
    "V": [[(4, 4), (48, 136), (96, 2)]],
    "E": [[(90, 4), (10, 4), (8, 136), (92, 134)], [(10, 68), (74, 68)]],
    "Y": [[(4, 2), (50, 70), (96, 4)], [(50, 70), (52, 138)]],
    "U": [[(6, 2), (6, 96), (24, 130), (50, 138), (78, 130), (94, 96), (96, 2)]],
    "B": [[(10, 2), (8, 136)], [(10, 4), (70, 6), (88, 30), (66, 64), (12, 66)], [(12, 66), (78, 70), (94, 104), (70, 134), (8, 134)]],
    "A": [[(4, 138), (50, 2), (96, 138)], [(24, 84), (76, 84)]],
}
ADV = {"I": 40, " ": 60}
# per-letter wobble so it looks hand-made (rot deg, dy, scale)
JITTER = [(-4, 4, 1.0), (3, -3, 0.96), (-2, 2, 1.04), (0, 0, 1.0), (5, 3, 1.02), (-3, -2, 0.98), (2, 4, 1.0),
          (0, 0, 1.0), (-3, 0, 0.95), (0, 0, 1.0), (4, -4, 1.03), (-2, 2, 0.97), (3, 1, 1.05), (-4, -2, 1.0),
          (0, 0, 1.0), (2, 3, 1.0), (-3, -1, 0.98), (4, 2, 1.02)]


def glyph_path(ch):
    p = skia.Path()
    for strokepts in GLYPHS.get(ch, []):
        if len(strokepts) > 2:
            p.addPath(open_path(strokepts))
        else:
            p.moveTo(*strokepts[0])
            p.lineTo(*strokepts[1])
    return p


def layout(text, size=1.0, gap=22):
    """[(ch, x, y, rot, scale)] in a 140-tall line, origin top-left."""
    out = []
    x = 0.0
    for i, ch in enumerate(text):
        rot, dy, sc = JITTER[i % len(JITTER)]
        if ch != " ":
            out.append((ch, x, dy, rot, sc))
        x += (ADV.get(ch, 100) + gap) * sc
    return out, x - gap


def draw_text(c, text, x, y, h, style="paper", seed=0, reveal=1.0, alpha=1.0, weight=1.0, color=None):
    """Draw kid letters with cap height h. style: paper (cut-out), pencil, crayon.
    reveal 0..1 writes the strokes on in order."""
    k = h / 140.0
    items, width = layout(text)
    n = len(items)
    with Xf(c, x, y, sx=k):
        for i, (ch, lx, dy, rot, sc) in enumerate(items):
            r = max(0.0, min(1.0, reveal * n - i))
            if r <= 0:
                break
            gp = glyph_path(ch)
            if r < 1.0:
                from gfx import trim
                gp = trim(gp, 0.0, r)
            with Xf(c, lx + 50 * sc, dy + 70, rot=rot, sx=sc):
                c.translate(-50, -70)
                if style == "paper":
                    c.drawPath(gp, stroke((10, 8, 16), 34 * weight, 0.55 * alpha, blur=6))
                    c.drawPath(gp, stroke(GRAPHITE, 30 * weight, alpha, effect=wobble(10, 1.5, seed + i)))
                    c.drawPath(gp, stroke(color or PAPER, 21 * weight, alpha, effect=wobble(10, 1.2, seed + i + 50)))
                elif style == "crayon":
                    col = color or (200, 120, 230)
                    for j in range(3):
                        c.drawPath(gp, stroke(col, (12 - j * 3) * weight, 0.55 * alpha, effect=wobble(6, 2.4, seed + i * 3 + j)))
                else:
                    pencil(c, gp, 7.0 * weight, color or GRAPHITE, alpha, seed=seed + i, rough=1.6)
    return width * k
