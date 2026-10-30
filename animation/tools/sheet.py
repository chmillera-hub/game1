# Contact sheet of stills: python3 tools/sheet.py out.png file1 file2 ... (cols=4)
import sys
from PIL import Image, ImageDraw, ImageFont
out, files = sys.argv[1], sys.argv[2:]
cols = 4 if len(files) > 4 else len(files)
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size
s = 0.6 if w >= 540 else 1
tw, th = int(w * s), int(h * s)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, rows * (th + 24)), (30, 30, 30))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    sheet.paste(im.resize((tw, th)), (x, y + 24))
    d.text((x + 6, y + 2), f.split('/')[-1], fill=(255, 220, 120), font=font)
sheet.save(out)
