"""Turn the timeline into per-frame state (pure numbers), shared by renderer + audio."""
import json, math, os, pickle, re, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from timeline import TL, FPS
from story import build, POS, SHOTS
import voices

CHARS = ('IRIS', 'BEE', 'CLAWD', 'CLAWDIA', 'GOSTE')
SR = voices.SR


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def lerp(a, b, k):
    if isinstance(a, str) or isinstance(b, str):
        return b
    if isinstance(a, tuple) or isinstance(b, tuple):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k


def load_tl():
    meta = json.load(open(os.path.join(HERE, 'voice_meta.json')))
    onsets = {}
    for k, v in meta['onsets'].items():
        key, w = k.split('§')
        onsets[(key, w)] = v
    tl = TL(meta['durs'], onsets)
    build(tl)
    return tl


def sample_tracks(tl, nf):
    tr = {}
    for (ch, p), keys in tl.keys.items():
        keys = sorted(keys, key=lambda k: k[0])
        arr = [keys[0][1]] * nf
        for (tk, v, d) in keys:
            f0 = max(0, int(round(tk * FPS)))
            if f0 >= nf:
                continue
            sv = arr[f0]
            for f in range(f0, nf):
                tt = f / FPS - tk
                if d <= 0 or tt >= d or isinstance(v, str):
                    arr[f] = v
                else:
                    arr[f] = lerp(sv, v, smooth(tt / d))
        tr[(ch, p)] = arr
    return tr


def eye_world(ch, P):
    x, y = P['x'], P['y']
    if ch == 'IRIS':
        return x + P['lean'] * 80, y + abs(P['lean']) * 22 + P['droop'] * 22
    if ch == 'CLAWD':
        return x, y - 8
    if ch == 'CLAWDIA':
        return x, y - 6
    if ch == 'BEE':
        return x - 15 * (-P['face']), y - 5
    if ch == 'GOSTE':
        return x, y - 32
    return x, y


def voice_env(tl, nf):
    """per-character mouth envelope + sibilance from the actual audio."""
    env = {c: np.zeros(nf) for c in CHARS}
    zc = {c: np.zeros(nf) for c in CHARS}
    speaking = [None] * nf
    for ln in tl.lines:
        fn = os.path.join(voices.CACHE, voices.h(ln['key'] + str(ln['whisper'])) + '.npy')
        a = np.load(fn)
        f0 = int(round(ln['start'] * FPS))
        n = int(len(a) / SR * FPS) + 1
        for i in range(n):
            f = f0 + i
            if f >= nf:
                break
            speaking[f] = ln['sp']
        if ln['sp'] not in env:
            continue
        hop = SR // FPS
        rms = []
        z = []
        for i in range(n):
            seg = a[max(0, i * hop - hop // 2): i * hop + hop]
            if len(seg) == 0:
                rms.append(0); z.append(0); continue
            rms.append(np.sqrt(np.mean(seg ** 2)))
            z.append(np.mean(np.abs(np.diff(np.sign(seg)))) / 2)
        rms = np.array(rms)
        ref = np.percentile(rms[rms > 0.01], 90) if np.any(rms > 0.01) else 1
        e = np.clip(rms / ref, 0, 1.2)
        # attack fast, release a bit slower so the mouth doesn't chatter
        sm = np.zeros_like(e)
        for i in range(len(e)):
            prev = sm[i - 1] if i else 0
            sm[i] = prev + (e[i] - prev) * (0.85 if e[i] > prev else 0.45)
        for i in range(len(sm)):
            f = f0 + i
            if f < nf:
                env[ln['sp']][f] = max(env[ln['sp']][f], sm[i])
                zc[ln['sp']][f] = z[i]
    return env, zc, speaking


def resolve_shot(shot, P, look_s):
    if isinstance(shot, str):
        return SHOTS[shot]
    if shot[0] == 'iris_pupil':
        ex, ey = eye_world('IRIS', P['IRIS'])
        lx, ly = look_s['IRIS']
        return (ex + lx * 165 * 0.42, ey + ly * 165 * 0.38, shot[1])
    if shot[0].startswith('@'):
        ch = shot[0][1:]
        return (P[ch]['x'] + shot[2], P[ch]['y'] + shot[3], shot[1])
    return shot


def split_sub(text):
    if len(text) <= 78:
        return [text]
    parts = re.split(r'(?<=[.!?])\s+', text)
    out, cur = [], ''
    for p in parts:
        if cur and len(cur) + len(p) + 1 > 78:
            out.append(cur); cur = p
        else:
            cur = (cur + ' ' + p).strip()
    if cur:
        out.append(cur)
    return out


def simulate():
    tl = load_tl()
    nf = int(math.ceil(tl.end * FPS))
    tr = sample_tracks(tl, nf)
    env, zc, speaking = voice_env(tl, nf)
    rng = np.random.default_rng(7)

    # blink schedules
    blinks = {}
    for c in list(CHARS) + ['PHOTO']:
        b = np.zeros(nf)
        t = rng.uniform(0.5, 2.0)
        curve = [0.55, 1, 1, 0.6, 0.2]
        while t * FPS < nf:
            f = int(t * FPS)
            for i, v in enumerate(curve):
                if f + i < nf:
                    b[f + i] = max(b[f + i], v)
            t += rng.uniform(2.2, 5.0)
        blinks[c] = b

    # subtitles
    subs = [None] * nf
    for li, ln in enumerate(tl.lines):
        chunks = split_sub(ln['sub'])
        tot = sum(len(c) for c in chunks)
        t = ln['start']
        nxt = tl.lines[li + 1]['start'] if li + 1 < len(tl.lines) else tl.end
        for ci, c in enumerate(chunks):
            d = ln['dur'] * len(c) / tot
            s0 = t - 0.08
            s1 = min(t + d + (0.25 if ci == len(chunks) - 1 else 0.0), nxt - 0.06)
            for f in range(max(0, int(s0 * FPS)), min(nf, int(s1 * FPS) + 1)):
                tt = f / FPS
                a = min(1, (tt - s0) / 0.12, (s1 - tt) / 0.12)
                subs[f] = (ln['sp'], c, max(0.0, a))
            t += d

    cams = sorted(tl.cams, key=lambda c: c[0])
    scenes = sorted(tl.scenes, key=lambda s: s[0])
    look_s = {c: np.array([0.0, 0.1]) for c in CHARS}
    sacc = {c: np.zeros(2) for c in CHARS}
    last_other = {c: None for c in CHARS}
    last_target = {c: 'cam' for c in CHARS}
    emph = {c: 0.0 for c in CHARS}
    cam_cur = np.array(SHOTS['wide'], float)
    cam_from = cam_cur.copy()
    cam_idx = -1
    last_cut_t = 0
    prev_speaker = None
    states = []
    for f in range(nf):
        t = f / FPS
        P = {}
        for c in CHARS + ('WORLD', 'PHOTO'):
            P[c] = {}
        for (c, p), arr in tr.items():
            P.setdefault(c, {})[p] = arr[f]
        sp = speaking[f]
        if sp in CHARS and sp != prev_speaker:
            for c in CHARS:
                if c != sp:
                    last_other[c] = sp
        if sp in CHARS:
            prev_speaker = sp
        for c in CHARS:
            Pc = P[c]
            tgt = Pc.get('look', 'auto')
            if tgt == 'auto':
                if sp in CHARS and sp != c:
                    tgt = sp
                elif sp == c:
                    tgt = last_other[c] or last_target[c]
                else:
                    tgt = last_target[c]
                if tgt == c:
                    tgt = 'cam'
            if tgt != last_target[c] and rng.random() < 0.6:
                blinks[c][f:f + 4] = np.maximum(blinks[c][f:f + 4], [0.6, 1, 0.8, 0.3][:len(blinks[c][f:f + 4])])
            last_target[c] = tgt
            ex_, ey_ = eye_world(c, Pc)
            if isinstance(tgt, tuple):
                v = np.array(tgt, float)
            elif tgt == 'cam':
                v = np.array([0.0, 0.08])
            else:
                if tgt in CHARS:
                    tx, ty = eye_world(tgt, P[tgt])
                else:
                    tx, ty = POS[tgt]
                d = np.array([tx - ex_, ty - ey_])
                v = d / max(np.linalg.norm(d), 200.0)
            n = np.linalg.norm(v)
            if n > 1:
                v = v / n
            if f % int(FPS * 0.9 + (hash(c) % 9)) == 0:
                sacc[c] = rng.normal(0, 0.07, 2)
            goal = v + sacc[c]
            look_s[c] = look_s[c] + (goal - look_s[c]) * 0.42
            Pc['lookv'] = tuple(look_s[c])
            e = env[c][f]
            de = e - (env[c][f - 1] if f else 0)
            emph[c] = max(emph[c] * 0.9, de * 1.4 if de > 0.25 else 0)
            Pc['talk'] = float(e)
            Pc['sib'] = float(zc[c][f])
            Pc['emph'] = float(emph[c])
            Pc['blink'] = float(blinks[c][f])
        P['PHOTO']['blink'] = float(blinks['PHOTO'][f])

        # camera
        while cam_idx + 1 < len(cams) and cams[cam_idx + 1][0] <= t + 1e-6:
            cam_idx += 1
            cam_from = cam_cur.copy()
            if cams[cam_idx][2] <= 0:
                last_cut_t = cams[cam_idx][0]
        if cam_idx >= 0:
            ct, shot, d = cams[cam_idx]
            goal = np.array(resolve_shot(shot, P, look_s), float)
            k = 1.0 if d <= 0 else smooth((t - ct) / d)
            lz = math.log(cam_from[2]) + (math.log(goal[2]) - math.log(cam_from[2])) * k
            # zoom-aware center interpolation (keeps a big zoom-out from swinging)
            if d > 0 and abs(math.log(goal[2] / cam_from[2])) > 1.5:
                kc = (1 / math.exp(lz) - 1 / cam_from[2]) / (1 / goal[2] - 1 / cam_from[2] + 1e-9)
                kc = min(max(kc, 0), 1)
            else:
                kc = k
            cam_cur = np.array([cam_from[0] + (goal[0] - cam_from[0]) * kc,
                                cam_from[1] + (goal[1] - cam_from[1]) * kc, math.exp(lz)])
        drift = 1 + 0.012 * min(t - last_cut_t, 6)
        cam = (cam_cur[0] + math.sin(t * 0.37) * 4 / cam_cur[2],
               cam_cur[1] + math.sin(t * 0.29 + 1) * 3 / cam_cur[2], cam_cur[2] * drift)
        scene = 'photo'
        for st, sc in scenes:
            if st <= t:
                scene = sc
        states.append(dict(f=f, t=t, P=P, cam=cam, sub=subs[f], speaking=sp, scene=scene))
    return tl, states


if __name__ == '__main__':
    tl, states = simulate()
    pickle.dump(states, open(os.path.join(HERE, 'states.pkl'), 'wb'))
    print('frames', len(states), 'dur', tl.end)
