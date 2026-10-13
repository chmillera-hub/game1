"""python3 preview/anat/rig_probe.py s04 [s05 ...]
Renders every frame of the scene(s) small and records each character's anchors per frame
(screen + world coords, arm layers) -> preview/anat/probe_<sid>.json. ~10-30 s per scene."""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import build
from engine import human, creatures, core
from engine.timeline import Timeline
W, H = 216, 384
SC = W / core.W
cur = []
KEYS_P = ('head', 'face', 'neck', 'hip', 'shoulder_l', 'shoulder_r', 'hand_l', 'hand_r', 'elbow_l', 'elbow_r',
          'foot_l', 'foot_r', 'eye_l', 'eye_r', 'mouth', 'top')
def _rec(kind, who, ctx, an, keys):
    r = {'k': kind, 'who': who}
    for key in keys:
        v = an.get(key) if isinstance(an, dict) else None
        if not isinstance(v, (tuple, list)) or len(v) < 2:
            continue
        try:
            x, y = float(v[0]), float(v[1])
        except Exception:
            continue
        dx, dy = ctx.user_to_device(x, y)
        r[key] = (round(dx / SC, 1), round(dy / SC, 1), round(x, 1), round(y, 1))
    if isinstance(an, dict):
        o, l = an.get('order'), an.get('layers')
        if o is not None: r['order'] = list(o)
        if l is not None: r['layers'] = list(l)
    m = ctx.get_matrix(); r['m'] = [round(m.xx, 4), round(m.yy, 4), round(m.x0 / SC, 1), round(m.y0 / SC, 1)]
    cur.append(r)
_op = human.draw_person
def wp(ctx, who, *a, **k):
    an = _op(ctx, who, *a, **k)
    try: _rec('P', who, ctx, an, KEYS_P)
    except Exception: pass
    return an
human.draw_person = wp
_oc = creatures.draw_specimen
def wc(ctx, *a, **k):
    an = _oc(ctx, *a, **k)
    try:
        keys = [kk for kk, v in (an.items() if isinstance(an, dict) else []) if isinstance(v, (tuple, list)) and len(v) >= 2 and not isinstance(v[0], (tuple, list))][:14]
        _rec('C', 'baby' if k.get('baby') else 'cr', ctx, an, keys)
    except Exception:
        pass
    return an
creatures.draw_specimen = wc
def run(sid):
    tl = Timeline(); info = tl.scene(sid)
    mod = build.load_scene(info.module)
    n = build.scene_frames(info)
    frames = []
    for f in range(n):
        cur.clear()
        build.render_frame(info, mod, f / build.FPS, W, H, captions=False)
        frames.append(list(cur))
    json.dump(dict(sid=sid, n=n, frames=frames), open(f'preview/anat/probe_{sid}.json', 'w'))
    return sid, n
if __name__ == '__main__':
    for s in sys.argv[1:]:
        print(run(s), flush=True)
