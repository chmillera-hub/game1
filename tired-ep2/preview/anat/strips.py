"""python3 preview/anat/strips.py s04 OUT.png FRAME:WHO[:ANCHOR[:RADIUS]] ...
Renders scene-local frames FRAME-2 .. FRAME+3 at 720p straight from the scene code and lays
them side by side, cropped around WHO's ANCHOR (default head) with RADIUS (720p px, default
200; 9999 = whole frame). Use it before AND after a fix."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import build
from engine import human, creatures, core
from engine.timeline import Timeline
from PIL import Image, ImageDraw
sid, out = sys.argv[1], sys.argv[2]
info = Timeline().scene(sid); mod = build.load_scene(info.module)
W, H = 720, 1280; SC = W / core.W
last = {}
_op = human.draw_person
def wp(ctx, who, *a, **k):
    an = _op(ctx, who, *a, **k)
    if isinstance(an, dict) and ctx.get_matrix().xx > 0.05:
        last.setdefault(who, an_dev(ctx, an))
    return an
def an_dev(ctx, an):
    o = {}
    for kk, v in an.items():
        if isinstance(v, (tuple, list)) and len(v) >= 2 and isinstance(v[0], (int, float)):
            o[kk] = ctx.user_to_device(float(v[0]), float(v[1]))
    return o
human.draw_person = wp
_oc = creatures.draw_specimen
def wc(ctx, *a, **k):
    an = _oc(ctx, *a, **k)
    if isinstance(an, dict) and ctx.get_matrix().xx > 0.05:
        last.setdefault('baby' if k.get('baby') else 'cr', an_dev(ctx, an))
    return an
creatures.draw_specimen = wc
def frame(f):
    last.clear()
    s = build.render_frame(info, mod, f / build.FPS, W, H, captions=False)
    im = Image.frombuffer('RGBA', (W, H), bytes(s.get_data()), 'raw', 'BGRA', 0, 1).convert('RGB')
    return im, dict(last)
rows = []
for spec in sys.argv[3:]:
    p = spec.split(':'); f0, who = int(p[0]), p[1]
    anc = p[2] if len(p) > 2 else 'head'; rad = int(p[3]) if len(p) > 3 else 200
    ims = []; cxy = None
    for k in (-2, -1, 0, 1, 2, 3):
        im, an = frame(f0 + k)
        if cxy is None or k == 0:
            pt = (an.get(who) or {}).get(anc)
            if pt: cxy = pt
        ims.append(im)
    tiles = []
    for k, im in zip((-2, -1, 0, 1, 2, 3), ims):
        if rad >= 9999 or not cxy:
            tile = im.resize((180, 320))
        else:
            cx, cy = cxy
            tile = im.crop((int(cx - rad), int(cy - rad), int(cx + rad), int(cy + rad))).resize((260, 260))
        d = ImageDraw.Draw(tile); d.rectangle((0, 0, 132, 13), fill=(0, 0, 0))
        d.text((2, 1), f'{sid} f{f0 + k} {(f0 + k) / 24:.2f}s', fill=(255, 255, 0))
        tiles.append(tile)
    tw, th = tiles[0].size
    row = Image.new('RGB', (6 * (tw + 4), th + 4), (30, 30, 30))
    for i, t_ in enumerate(tiles): row.paste(t_, (i * (tw + 4), 2))
    rows.append(row)
b = Image.new('RGB', (max(r.size[0] for r in rows), sum(r.size[1] for r in rows)), (10, 10, 10))
y = 0
for r in rows: b.paste(r, (0, y)); y += r.size[1]
b.save(out); print(out, b.size)
