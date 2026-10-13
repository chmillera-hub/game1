"""python3 preview/anat/seg_scan.py s01 ... : renders every frame (small) with core.seg patched to log
calls whose bounds are reversed (t1 < t0) and where t falls inside the reversed span (where the
'step' actually bites). Prints each call site with the frames it affects."""
import sys, os, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
from engine import core
_seg = core.seg
hits = {}
cur = {'f': None}
def seg(t, t0, t1):
    if t1 < t0 - 1e-9 and t1 <= t <= t0:
        st = traceback.extract_stack(limit=3)[-2]
        k = (os.path.basename(st.filename), st.lineno, st.line)
        hits.setdefault(k, set()).add(cur['f'])
    return _seg(t, t0, t1)
core.seg = seg
import build
from engine.timeline import Timeline
for sid in sys.argv[1:]:
    hits.clear()
    info = Timeline().scene(sid); mod = build.load_scene(info.module)
    for f in range(build.scene_frames(info)):
        cur['f'] = f
        build.render_frame(info, mod, f / build.FPS, 108, 192, captions=False)
    print(f'== {sid}: {len(hits)} reversed-seg call sites')
    for (fn, ln, line), fs in sorted(hits.items()):
        fs = sorted(x for x in fs if x is not None)
        print(f'   {fn}:{ln}  frames {fs[0]}..{fs[-1]} ({len(fs)})  {line.strip()[:110]}')
