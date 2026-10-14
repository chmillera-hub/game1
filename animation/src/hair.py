"""Procedural hair grooming -> Blender Curves (hair) objects."""
import numpy as np
from headgen import smoothstep


def _sample_surface(V, F, n, rng, mask_fn):
    V = np.asarray(V)
    tri = []
    for f in F:
        if len(f) == 3:
            tri.append(f)
        else:
            tri.append((f[0], f[1], f[2]))
            tri.append((f[0], f[2], f[3]))
    T = np.array(tri)
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    cr = np.cross(B - A, C - A)
    area = np.linalg.norm(cr, axis=1)
    nrm = cr / np.maximum(area[:, None], 1e-12)
    cen = (A + B + C) / 3
    keep = mask_fn(cen, nrm) > 0.5
    if keep.sum() == 0:
        return None, None
    p = area * keep
    p = p / p.sum()
    idx = rng.choice(len(T), size=n, p=p)
    r1 = np.sqrt(rng.random(n))
    r2 = rng.random(n)
    P = (1 - r1)[:, None] * A[idx] + (r1 * (1 - r2))[:, None] * B[idx] + (r1 * r2)[:, None] * C[idx]
    N = nrm[idx]
    # make normals point outward from the head centre
    flip = np.sum(N * (P - np.array([0, 0.0, -0.01])), 1) < 0
    N[flip] *= -1
    return P, N


def _shell(P, H, off):
    """Project points onto the cranium ellipsoid + offset (head space)."""
    p = H.p
    u = P / np.linalg.norm(P, axis=-1, keepdims=True)
    rz = np.where(u[..., 2] > 0, p['rz_top'], p['rz_bot'])
    rr = 1.0 / np.sqrt((u[..., 0] / p['rx']) ** 2 + (u[..., 1] / p['ry']) ** 2 + (u[..., 2] / rz) ** 2)
    return u * (rr + off)[..., None]


STYLES = {
    # count, length, segs, lift, clump, offset, radius root
    'short': dict(n=5000, L=0.045, segs=7, clumps=140, clump=0.55, off=0.006, r=0.00065, curl=0.25),
    'messy': dict(n=5500, L=0.055, segs=8, clumps=110, clump=0.6, off=0.008, r=0.0007, curl=0.5),
    'old_sides': dict(n=5200, L=0.034, segs=7, clumps=160, clump=0.65, off=0.002, r=0.0007, curl=0.06),
    'bun': dict(n=5000, L=0.16, segs=10, clumps=90, clump=0.65, off=0.004, r=0.0006, curl=0.02),
    'bob': dict(n=6500, L=0.11, segs=9, clumps=120, clump=0.6, off=0.007, r=0.0006, curl=0.05),
    'stubble': dict(n=3500, L=0.006, segs=3, clumps=0, clump=0.0, off=0.0, r=0.00035, curl=0.0),
    'beard': dict(n=9000, L=0.026, segs=4, clumps=200, clump=0.4, off=0.0, r=0.00045, curl=0.15),
}


def groom(H, hg, style, seed=0, under_hat=False, bun=None, keep_top=False):
    rng = np.random.default_rng(seed)
    st = dict(STYLES[style])
    if under_hat:
        st['off'] = 0.0025
        st['L'] *= 0.8
    p = H.p
    NR, NS = hg['index']['NR'], hg['index']['NS']
    V = hg['verts'][:NR * NS]
    F = [f for f in hg['faces'] if max(f) < NR * NS]
    lipmask = hg['colors'][:, 0]
    mc = hg['mouth_c']

    # under a hat the temples come lower, so some hair still shows below the brim
    hl_z = [0.072, 0.048, 0.015, -0.030, -0.055, -0.068] if under_hat else [0.072, 0.064, 0.030, -0.030, -0.055, -0.068]

    def hairline(y):
        return np.interp(y, [-0.12, -0.05, -0.01, 0.03, 0.06, 0.12], hl_z)

    if style in ('stubble', 'beard'):
        def mask(c, n):
            x, y, z = c[:, 0], c[:, 1], c[:, 2]
            m = (y < 0.01) & (z < mc[2] + 0.024) & (z > mc[2] - 0.075)
            m &= ~((np.abs(x) < 0.042) & (np.abs(z - mc[2]) < 0.011) & (y < -0.06))  # keep lips clear
            m &= (z < mc[2] - 0.010) | (z > mc[2] + 0.008) | (np.abs(x) > 0.045)
            m &= ~((z > mc[2] + 0.004) & (np.abs(x) > 0.035))  # cheeks above the mouth line stay clean
            m &= ~((z < mc[2] - 0.05) & (y > -0.03))  # under the jaw toward the neck
            return m.astype(float)
    else:
        def mask(c, n):
            x, y, z = c[:, 0], c[:, 1], c[:, 2]
            hl = hairline(y)
            m = z > hl
            # keep clear of the ears and the face
            m &= ~((np.abs(x) > 0.07) & (np.abs(z - p['ear_z']) < 0.03) & (np.abs(y - p['ear_y']) < 0.03))
            if under_hat and not keep_top:
                m &= z < 0.040
            if style == 'old_sides':
                m &= (z < 0.05 + 0.03 * smoothstep(0.0, 0.1, y)) & (y > -0.05)
            return m.astype(float)

    P0, N0 = _sample_surface(V, F, st['n'], rng, mask)
    if P0 is None:
        return None, None
    n = len(P0)
    segs = st['segs']
    L = st['L'] * (0.75 + 0.5 * rng.random(n))
    pts = np.zeros((n, segs, 3))
    down = np.array([0, 0, -1.0])
    for i in range(n):
        r, nr = P0[i], N0[i]
        x, y, z = r
        if style in ('stubble', 'beard'):
            comb = down - nr * np.dot(down, nr)
            comb += np.array([0, -0.4, 0]) * (z < mc[2] - 0.02)
        elif style == 'bun':
            target = np.array([0, bun[0], bun[1]]) if bun else np.array([0, 0.09, 0.07])
            comb = target - r
        elif style == 'bob':
            part_x = 0.02
            away = np.array([np.sign(x - part_x) * 1.0, 0.15, -0.2])
            comb = away * smoothstep(0.05, 0.11, z) + down * (1 - smoothstep(0.05, 0.11, z))
            if y < -0.05:
                comb = comb + np.array([0, -0.6, -0.5])  # bangs fall forward/down
        elif style == 'old_sides':
            comb = np.array([0, 0.5, -1.0])
        elif under_hat:
            comb = np.array([np.sign(x) * 0.2, 0.5, -1.0]) + rng.normal(0, 0.12, 3)
        else:
            comb = np.array([np.sign(x) * 0.3, 0.6, -0.6])
            comb = comb + rng.normal(0, 0.35, 3)
        comb = comb - nr * np.dot(comb, nr)
        comb /= max(np.linalg.norm(comb), 1e-6)
        q = r - nr * 0.0012
        pts[i, 0] = q
        if under_hat and keep_top and z > 0.035:
            L[i] *= 0.35
        if style == 'beard' and z > mc[2] - 0.004:
            L[i] *= 0.4   # moustache stays a band above the lip instead of curtaining the mouth
        if style == 'bun':
            tb = np.array([0, bun[0], bun[1]]) if bun else np.array([0, 0.09, 0.07])
            L[i] = min(L[i], np.linalg.norm(tb - r) * 1.05)
        step = L[i] / (segs - 1)
        d = nr.copy()
        for k in range(1, segs):
            t = k / (segs - 1)
            lift = (1 - t) ** 2 * (0.15 if style in ('bun', 'old_sides') else (0.2 if under_hat else 0.6))
            d = comb * (1 - lift) + nr * lift
            if style == 'bun':
                # re-aim every step at the bun so strands wrap the skull instead of leaving it on a tangent
                to = tb - q
                dist = np.linalg.norm(to)
                if dist < step:
                    step = max(dist, 1e-5)
                d = to / max(dist, 1e-6) * (1 - lift) + nr * lift
            if style in ('bob', 'messy', 'old_sides'):
                d = d + down * t * (0.6 if style == 'bob' else 0.25)
            if st['curl']:
                d = d + rng.normal(0, st['curl'], 3) * t
            d /= np.linalg.norm(d)
            q = q + d * step
            pts[i, k] = q
        if style not in ('stubble', 'beard'):
            # keep strands outside the scalp shell
            off = st['off'] * np.sin(np.linspace(0, 1, segs) * np.pi * 0.5 + 0.1)
            if under_hat and keep_top and r[2] > 0.035:
                off = off * 0.4
            sh = _shell(pts[i], H, off)
            rad_now = np.linalg.norm(pts[i], axis=-1)
            rad_sh = np.linalg.norm(sh, axis=-1)
            above_line = pts[i][:, 2] > hairline(pts[i][:, 1]) - 0.03
            fix = (rad_now < rad_sh) & above_line
            pts[i][fix] = sh[fix]
    # clumping
    if st['clumps']:
        cidx = rng.choice(n, size=min(st['clumps'], n), replace=False)
        roots = P0[cidx]
        d2 = ((P0[:, None, :] - roots[None]) ** 2).sum(-1)
        own = np.argmin(d2, 1)
        guide = pts[cidx][own]
        rel = pts[:, :1] - guide[:, :1]
        t = np.linspace(0, 1, segs)[None, :, None]
        target = guide + rel * (1 - st['clump'] * t)
        pts = pts * (1 - t) + target * t
    rad = np.ones((n, segs)) * st['r'] * np.linspace(1.0, 0.35, segs)[None]
    return pts, rad


def make_curves(name, pts, rad, coll):
    import bpy
    n, segs, _ = pts.shape
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([segs] * n)
    cv.position_data.foreach_set('vector', pts.reshape(-1).astype(np.float32))
    if 'radius' not in cv.attributes:
        cv.attributes.new('radius', 'FLOAT', 'POINT')
    cv.attributes['radius'].data.foreach_set('value', rad.reshape(-1).astype(np.float32))
    ob = bpy.data.objects.new(name, cv)
    coll.objects.link(ob)
    return ob
