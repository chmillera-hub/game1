"""Render a contact sheet of frames at given times (for review)."""
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

import render
from gfx import hexc


def sheet(times, out, cols=4, scale=0.25):
    W, H = render.W, render.H
    tw, th = int(W * scale), int(H * scale)
    rows = (len(times) + cols - 1) // cols
    img = Image.new("RGB", (cols * tw, rows * (th + 22)), (20, 20, 28))
    arr = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(arr)
    c = surf.getCanvas()
    d = ImageDraw.Draw(img)
    for i, t in enumerate(times):
        c.save()
        c.clear(hexc("#000000"))
        render.render_frame(c, t)
        c.restore()
        im = Image.fromarray(arr[:, :, :3].copy()).resize((tw, th), Image.LANCZOS)
        x, y = (i % cols) * tw, (i // cols) * (th + 22)
        img.paste(im, (x, y + 22))
        s = render.shot_at(t)
        d.text((x + 4, y + 4), f"{t:.1f}s {s['id']}", fill=(255, 255, 255))
    img.save(out)
    print(out)


if __name__ == "__main__":
    out = sys.argv[1]
    ts = [float(x) for x in sys.argv[2:]]
    sheet(ts, out)
