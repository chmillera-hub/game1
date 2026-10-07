"""Tile build/stills/*.jpg into labelled contact sheets for review."""
import glob, sys
from PIL import Image, ImageDraw
files = sorted(glob.glob("build/stills/*.jpg"))
per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
for s in range(0, len(files), per):
    chunk = files[s:s + per]
    sheet = Image.new("RGB", (1280, 360 * ((len(chunk) + 1) // 2)), "gray")
    for i, f in enumerate(chunk):
        im = Image.open(f).resize((640, 360))
        ImageDraw.Draw(im).text((8, 96), f.split("/")[-1], fill=(255, 80, 80))
        sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(f"build/sheet{s // per}.jpg", quality=88)
    print(f"build/sheet{s // per}.jpg")
