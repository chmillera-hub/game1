"""Render single frames to PNG for checking: python3 preview.py t1 t2 ..."""
import sys, os
import skia
from common import *
import film

if __name__ == "__main__":
    f = film.Film()
    out = os.environ.get("OUT", "/tmp/claude-0/prev")
    os.makedirs(out, exist_ok=True)
    for a in sys.argv[1:]:
        t = float(a)
        surf = skia.Surface(W, H)
        f.frame(surf.getCanvas(), t)
        surf.makeImageSnapshot().save(f"{out}/f_{t:07.2f}.png", skia.kPNG)
        print(f"{out}/f_{t:07.2f}.png")
