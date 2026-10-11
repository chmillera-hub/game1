"""Render a contact sheet of chosen times: python3 preview.py out.png t1 t2 ..."""
import sys
import skia
import scenes

out = sys.argv[1]
times = [float(x) for x in sys.argv[2:]]
cols = 4 if len(times) > 4 else len(times)
rows = (len(times) + cols - 1) // cols
sc = 0.5
sheet = skia.Surface(int(720 * sc * cols), int(1280 * sc * rows))
cv = sheet.getCanvas()
cv.clear(skia.Color(20, 20, 20))
for i, t in enumerate(times):
    img = scenes.render_frame(t)
    x, y = (i % cols) * 720 * sc, (i // cols) * 1280 * sc
    cv.drawImageRect(img, skia.Rect(x, y, x + 720 * sc, y + 1280 * sc), skia.SamplingOptions(skia.FilterMode.kLinear))
    font = skia.Font(skia.Typeface('Inter'), 18)
    cv.drawString(f'{t:.1f}s {scenes.TL.shot_at(t).name}', x + 8, y + 22, font, scenes.P('#ffff00'))
sheet.makeImageSnapshot().save(out, skia.kPNG)
