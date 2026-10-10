"""Render frames. Usage:
  python3 render.py preview t1 t2 ...      -> preview/contact.png
  python3 render.py segment i n            -> renders segment i of n into seg_i.mkv
"""
import sys, subprocess, json, math, time
import skia
from gfx import W, H, FPS
import scenes

DUR = scenes.TL["duration"]
NFRAMES = int(math.ceil(DUR * FPS))


def frame(surface, t):
    c = surface.getCanvas()
    c.clear(skia.ColorBLACK)
    scenes.render(c, t)
    return surface.makeImageSnapshot()


def preview(times, out="preview/contact.png", cols=4, scale=0.5):
    s = skia.Surface(W, H)
    rows = (len(times) + cols - 1) // cols
    sheet = skia.Surface(int(W * scale * cols), int(H * scale * rows))
    sc = sheet.getCanvas()
    sc.clear(skia.ColorWHITE)
    for i, t in enumerate(times):
        img = frame(s, t)
        x, y = (i % cols) * W * scale, (i // cols) * H * scale
        sc.drawImageRect(img, skia.Rect.MakeXYWH(x, y, W * scale, H * scale), skia.SamplingOptions(skia.FilterMode.kLinear))
        f = skia.Font(skia.Typeface("DejaVu Sans Mono"), 22)
        sc.drawString("%.2f %s" % (t, scenes.scene_at(t)), x + 8, y + 26, f, skia.Paint(Color=skia.ColorSetARGB(255, 255, 0, 255)))
    sheet.makeImageSnapshot().save(out, skia.kPNG)


def segment(i, n):
    a = NFRAMES * i // n
    b = NFRAMES * (i + 1) // n
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "8", "-pix_fmt", "yuv420p", f"segs/seg_{i:02d}.mkv"]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = skia.Surface(W, H)
    t0 = time.time()
    for k in range(a, b):
        img = frame(s, k / FPS)
        p.stdin.write(img.toarray().tobytes())
        if (k - a) % 240 == 0:
            print(f"seg {i}: {k - a}/{b - a} ({time.time() - t0:.0f}s)", flush=True)
    p.stdin.close()
    p.wait()
    print(f"seg {i} done {b - a} frames in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "preview":
        ts = [float(x) for x in sys.argv[2:]]
        preview(ts)
    elif sys.argv[1] == "segment":
        segment(int(sys.argv[2]), int(sys.argv[3]))
