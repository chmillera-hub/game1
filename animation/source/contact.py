import json, subprocess, os
from PIL import Image, ImageDraw, ImageFont
shots = json.load(open('shots.json')); tl = json.load(open('timeline.json'))
fr = []
for s in shots: fr.append((s['f0'] + (s['f1'] - s['f0']) // 2, f"{s['key']}  [{s['f0']}-{s['f1']}]"))
for a, b in zip(tl['scenes'], tl['scenes'][1:]): fr.append((round(a['end'] * 24) - 5, f"transition {a['id']}->{b['id']}"))
fr.sort()
os.makedirs('frames_cs', exist_ok=True)
sel = '+'.join(f'eq(n\\,{f})' for f, _ in fr)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'out.mp4', '-vf', f"select='{sel}',scale=180:320", '-vsync', '0', 'frames_cs/c_%04d.png'], check=True)
font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 12)
per = 24; sheets = []
for k in range(0, len(fr), per):
    chunk = fr[k:k + per]
    im = Image.new('RGB', (6 * 180, 4 * 340), (20, 18, 24)); d = ImageDraw.Draw(im)
    for i, (f, lab) in enumerate(chunk):
        th = Image.open(f'frames_cs/c_{k + i + 1:04d}.png'); x, y = (i % 6) * 180, (i // 6) * 340
        im.paste(th, (x, y)); d.text((x + 4, y + 322), f"f{f} {lab}"[:30], fill=(240, 230, 200), font=font)
    n = f'prod/contact_sheet_{k // per + 1:02d}.jpg'; im.save(n, quality=80); sheets.append(n)
print(len(fr), 'frames ->', sheets)
