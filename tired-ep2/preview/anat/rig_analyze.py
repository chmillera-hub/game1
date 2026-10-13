"""python3 preview/anat/rig_analyze.py s04   (after rig_probe.py s04)
Flags, per character track (screen coords, logical 1080x1920 px):
  pop1  an anchor deviates >6 px from its neighbours for ONE frame (a twitch / shake / pop)
  pop2  the same over TWO frames
  jump  a single-frame move >28 px, 3x bigger than the motion around it (a snap / teleport)
  zflip the arm draw order / layers change and change back within 4 frames (z-order flicker)
Camera cuts (big camera-matrix jumps, or cut frames from scan.json) are excluded.
Not every flag is a bug: camera shakes, intended trembles and very fast motions also flag.
Look at each one (strips.py) and judge."""
import json, math, sys, os
import numpy as np
from collections import defaultdict
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sid = sys.argv[1]
d = json.load(open(f'{ROOT}/preview/anat/probe_{sid}.json')); n = d['n']; fr = d['frames']
cutf = set()
sp = f'{ROOT}/preview/anat/scan_cuts.json'
if os.path.exists(sp):
    for i in json.load(open(sp)).get(sid, []): cutf.update((i - 1, i, i + 1))
ANCH = ('head', 'hand_l', 'hand_r', 'foot_l', 'foot_r', 'hip', 'neck', 'shoulder_l', 'shoulder_r', 'elbow_l', 'elbow_r')
inst = []
for recs in fr:
    seen = set(); L = []
    for r in recs:
        if 'head' not in r or r['m'][0] < 0.05: continue
        key = (r['k'], r['who'], round(r['head'][2]), round(r['head'][3]))
        if key in seen: continue
        seen.add(key); L.append(r)
    inst.append(L)
tracks = []; active = []
for i, L in enumerate(inst):
    new_active = []; used = set()
    for r in L:
        best = None; bd = 1e9
        for ti in active:
            t = tracks[ti]; lr = t[max(t)]
            if lr['k'] != r['k'] or lr['who'] != r['who'] or ti in used: continue
            dd = math.dist(lr['head'][:2], r['head'][:2])
            if dd < bd: bd, best = dd, ti
        if best is not None and bd < 90 and (i - 1) in tracks[best]:
            tracks[best][i] = r; used.add(best); new_active.append(best)
        else:
            tracks.append({i: r}); new_active.append(len(tracks) - 1); used.add(len(tracks) - 1)
    active = new_active
out = []
for ti, F in enumerate(tracks):
    idx = sorted(F)
    if len(idx) < 6: continue
    who = F[idx[0]]['who']
    mat = {i: F[i]['m'] for i in idx}
    def camjump(i):
        a, b = mat.get(i - 1), mat.get(i)
        if not a or not b: return False
        return abs(b[0] / a[0] - 1) > 0.03 or math.dist(a[2:], b[2:]) > 60
    cj = set(i for i in idx if camjump(i))
    bad = lambda S: bool(S & cutf) or bool(S & cj)
    for a in ANCH:
        P = {i: np.array(F[i][a][:2]) for i in idx if a in F[i]}
        for i in P:
            a0, b, c, e = P.get(i - 1), P[i], P.get(i + 1), P.get(i + 2)
            if a0 is None or c is None or bad({i - 1, i, i + 1}): continue
            dev = float(np.linalg.norm(b - (a0 + c) / 2)); span = float(np.linalg.norm(c - a0))
            if dev > 6 and span < dev * 0.6: out.append((i, 'pop1', who, ti, a, round(dev, 1)))
            if e is not None and not bad({i + 2}):
                d1 = float(np.linalg.norm(b - a0)); d2 = float(np.linalg.norm(c - e)); s2 = float(np.linalg.norm(e - a0))
                if min(d1, d2) > 6 and s2 < min(d1, d2) * 0.5 and np.linalg.norm(c - b) < min(d1, d2):
                    out.append((i, 'pop2', who, ti, a, round(min(d1, d2), 1)))
            j = float(np.linalg.norm(b - a0)); pv = P.get(i - 2)
            nb = max(float(np.linalg.norm(a0 - pv)) if pv is not None else 0.0, float(np.linalg.norm(c - b)))
            if j > 28 and j > 3 * max(nb, 4): out.append((i, 'jump', who, ti, a, round(j, 1)))
    L = [(i, (tuple(F[i].get('order') or ()), tuple(F[i].get('layers') or ()))) for i in idx]
    for k in range(1, len(L) - 1):
        i, v = L[k]
        if L[k - 1][1] != v and L[k - 1][0] == i - 1 and not bad({i}):
            for q in range(k + 1, min(len(L), k + 5)):
                if L[q][1] == L[k - 1][1]:
                    out.append((i, 'zflip', who, ti, f'{L[k - 1][1]}->{v}', q - k)); break
cl = defaultdict(list)
for o in out: cl[(o[3], o[2])].append(o)
events = []
for (ti, who), L in cl.items():
    L.sort(); cur = [L[0]]
    for x in L[1:]:
        if x[0] - cur[-1][0] <= 4: cur.append(x)
        else: events.append((who, ti, cur)); cur = [x]
    events.append((who, ti, cur))
events.sort(key=lambda e: e[2][0][0])
print(f'{sid}: {len(events)} events  (frame = scene-local frame, t = scene-local seconds)')
for who, ti, c in events:
    types = sorted(set(x[1] for x in c)); an = sorted(set(str(x[4]) for x in c))
    vals = [x[5] for x in c if isinstance(x[5], (int, float))]
    print(f'  f{c[0][0]:5d} t{c[0][0] / 24:6.2f}  {who:6s} track{ti:<4d} {",".join(types):16s} {",".join(an)[:70]:70s} max={max(vals) if vals else ""} n={len(c)}')
