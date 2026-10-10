"""Preview helpers for checking work visually.

    python3 -m anim.preview sheet  OUT.png  t1 t2 t3 ...   [--cols 4] [--scale 0.35]
        Contact sheet of full-film frames at the given absolute times (labelled).
    python3 -m anim.preview frame  OUT.png  t
        One full-resolution frame.

From Python, use  sheet_from_fn(fn, times, out, cols, scale, labels)  to make a contact sheet
from any function fn(canvas, t) that draws a 720x1280 frame (e.g. a character test).
"""
import sys

import numpy as np
import skia
from PIL import Image, ImageDraw

from config import H, W


def _surface_to_pil(surface):
    arr = surface.makeImageSnapshot().toarray()  # BGRA on little-endian? -> handle below
    img = Image.fromarray(arr[:, :, :3][:, :, ::-1] if _is_bgra() else arr[:, :, :3])
    return img


_BGRA = None


def _is_bgra():
    global _BGRA
    if _BGRA is None:
        s = skia.Surface(1, 1)
        s.getCanvas().clear(skia.Color(255, 0, 0))
        a = s.makeImageSnapshot().toarray()
        _BGRA = bool(a[0, 0, 2] == 255 and a[0, 0, 0] == 0)
    return _BGRA


def frame_rgb(surface) -> np.ndarray:
    arr = surface.makeImageSnapshot().toarray()
    rgb = arr[:, :, :3]
    if _is_bgra():
        rgb = rgb[:, :, ::-1]
    return np.ascontiguousarray(rgb)


def sheet_from_fn(fn, times, out, cols=4, scale=0.35, labels=None):
    surf = skia.Surface(W, H)
    tiles = []
    for i, t in enumerate(times):
        c = surf.getCanvas()
        c.resetMatrix()
        c.clear(skia.ColorBLACK)
        c.save()
        fn(c, t)
        c.restore()
        img = Image.fromarray(frame_rgb(surf)).resize((int(W * scale), int(H * scale)), Image.LANCZOS)
        d = ImageDraw.Draw(img)
        lab = labels[i] if labels else f"{t:.2f}s"
        d.rectangle([0, 0, 8 + 7 * len(lab), 16], fill=(0, 0, 0))
        d.text((4, 2), lab, fill=(255, 255, 0))
        tiles.append(img)
    rows = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (cols * tw + (cols - 1) * 4, rows * th + (rows - 1) * 4), (40, 40, 40))
    for i, im in enumerate(tiles):
        sheet.paste(im, ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
    sheet.save(out)
    return out


def film_fn(c, t):
    from anim.frame import scene_at
    from anim import scenes
    scenes.get(scene_at(t)).render(c, t)


if __name__ == "__main__":
    args = sys.argv[1:]
    mode, out = args[0], args[1]
    cols, scale = 4, 0.35
    if "--cols" in args:
        i = args.index("--cols"); cols = int(args[i + 1]); del args[i:i + 2]
    if "--scale" in args:
        i = args.index("--scale"); scale = float(args[i + 1]); del args[i:i + 2]
    times = [float(x) for x in args[2:]]
    if mode == "frame":
        sheet_from_fn(film_fn, times[:1], out, cols=1, scale=1.0)
    else:
        sheet_from_fn(film_fn, times, out, cols=cols, scale=scale)
    print(out)
