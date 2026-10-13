"""python3 preview/anat/face_probe.py s01 ... : record each creature draw's face value per frame;
report crossings of face = 0 (where the head is mirrored) while the creature is on screen."""
import sys, os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import build
from engine import creatures, core
from engine.timeline import Timeline
W, H = 216, 384
SC = W / core.W
cur = []
_oc = creatures.draw_specimen
def wc(ctx, x, y, s, t, *a, **k):
    an = _oc(ctx, x, y, s, t, *a, **k)
    m = ctx.get_matrix()
    if m.xx > 0.05:
        hx, hy = (an.get('head') or (x, y))[:2] if isinstance(an, dict) else (x, y)
        dx, dy = ctx.user_to_device(hx, hy)
        cur.append(dict(baby=bool(k.get('baby')), face=k.get('face', 1.0), x=dx / SC, y=dy / SC, sc=m.xx / SC * s,
                        closed=k.get('blink', None)))
    return an
creatures.draw_specimen = wc
for sid in sys.argv[1:]:
    info = Timeline().scene(sid); mod = build.load_scene(info.module)
    n = build.scene_frames(info); fr = []
    for f in range(n):
        cur.clear(); build.render_frame(info, mod, f / build.FPS, W, H, captions=False); fr.append(list(cur))
    out = []
    for f in range(1, n):
        for a in fr[f - 1]:
            for b in fr[f]:
                if a['baby'] != b['baby'] or math.dist((a['x'], a['y']), (b['x'], b['y'])) > 120: continue
                fa, fb = a['face'], b['face']
                if not isinstance(fa, (int, float)) or not isinstance(fb, (int, float)): continue
                if (fa < 0) != (fb < 0) and 0 <= b['x'] <= 1080 and 0 <= b['y'] <= 1920:
                    out.append((f, round(f / 24, 2), 'baby' if b['baby'] else 'cr', round(fa, 2), round(fb, 2), round(b['sc'], 2)))
    print(f'== {sid}: {len(out)} face-sign crossings on screen')
    for o in out: print('   f%d t%.2f %s face %s -> %s  (head scale %.2f)' % o)
