"""Procedural stylised head geometry (pure numpy, no bpy).

The head is a sphere whose pole sits at the mouth.  Rings around that pole
give lip topology (like the orbicularis oris loops of a real face), the hole
at the pole becomes the mouth slit, and the slit is extruded inward to form
the mouth cavity.  Expression shape keys are produced by re-evaluating the
same surface with different mouth parameters, so every shape shares topology.

Head space: origin at the cranium centre (roughly eye height), Z up, the
character faces -Y, the character's left side is +X.
"""
import numpy as np


def smoothstep(e0, e1, x):
    t = np.clip((np.asarray(x, dtype=float) - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def bump(x, c, w):
    """Smooth compact bump: 1 at c, 0 beyond |x-c|>=w."""
    t = np.clip(1.0 - ((np.asarray(x) - c) / w) ** 2, 0.0, 1.0)
    return t * t


def norm(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


DEFAULT = dict(
    scale=1.0,
    rx=0.102, ry=0.104, rz_top=0.112, rz_bot=0.094,
    # lower face
    jaw_taper=0.25, jaw_z0=-0.012, jaw_z1=-0.115,
    muzzle=0.015, muzzle_z=-0.055, muzzle_w=0.06,
    chin=0.012, chin_z=-0.100, chin_drop=0.030, chin_w=0.030,
    cheek=0.010, cheek_x=0.055, cheek_z=-0.035, cheek_r=0.035,
    brow_ridge=0.006,
    # mouth
    mouth_elev=-29.0, mouth_halfw=0.27, corner_rest=1.0, mouth_sy0=0.07, mouth_blend=0.42,
    lip_up=0.0042, lip_lo=0.0056, lip_w=0.125, lip_color=None,
    # nose
    nose_z=-0.012, nose_len=0.040, nose_proj=0.022, nose_w=0.017, nose_bulb=0.012,
    nose_bulb_w=0.016, nose_bridge_w=0.010,
    # eyes
    eye_r=0.0225, eye_x=0.039, eye_z=0.010, eye_protrude=0.27, eye_out=7.0,
    eye_open_h=48.0, eye_open_v=44.0,
    # lids (degrees in eye space; elevation above the eye's forward axis)
    lid_up_e=24.0, lid_up_arch=10.0, lid_lo_e=-31.0, lid_lo_arch=6.0, lid_corner_az=62.0,
    canthus_tilt=4.0,
    naso=0.0, tooth_gap=False,
    # ears
    ear_size=1.0, ear_z=-0.012, ear_y=0.010,
    # skin
    skin=(0.62, 0.36, 0.24), blush=(0.70, 0.26, 0.22), blush_amt=0.30,
    # resolution
    NS=72, NR=64,
)


class Head:
    """Builds rest geometry, shape keys and weights for a head."""

    def __init__(self, **kw):
        p = dict(DEFAULT)
        p.update(kw)
        if p['lip_color'] is None:
            sk = np.array(p['skin'])
            p['lip_color'] = tuple(np.clip(sk * np.array([0.84, 0.58, 0.58]) + np.array([0.02, 0.0, 0.0]), 0, 1))
        self.p = p
        a = np.radians(p['mouth_elev'])
        self.u0 = norm(np.array([0.0, -np.cos(a), np.sin(a)]))
        up = np.array([0.0, 0.0, 1.0])
        self.t_up = norm(up - np.dot(up, self.u0) * self.u0)
        self.t_x = np.cross(self.t_up, self.u0)
        if self.t_x[0] < 0:
            self.t_x = -self.t_x
        NS, NR = p['NS'], p['NR']
        th0 = p['mouth_halfw']
        t = np.linspace(0, 1, NR)
        self.theta = th0 + (np.pi - 0.06 - th0) * (t ** 1.30)
        self.phi = np.linspace(0, 2 * np.pi, NS, endpoint=False)
        self.TH, self.PH = np.meshgrid(self.theta, self.phi, indexing='ij')  # (NR, NS)
        self._eyes_ready = False
        self._place_features()

    # ------------------------------------------------------------------
    def _directions(self, mp):
        """Mouth mapping: tangent-plane compression around the pole."""
        p = self.p
        TH, PH = self.TH, self.PH
        th0 = p['mouth_halfw']
        qx = TH * np.sin(PH)
        qy = TH * np.cos(PH)
        s = smoothstep(th0, th0 + p['mouth_blend'], TH)
        sy = mp['sy0'] + (1.0 - mp['sy0']) * s
        sx = mp['sx'] + (1.0 - mp['sx']) * smoothstep(th0, th0 + p['mouth_blend'] * 1.2, TH)
        qx2 = qx * sx
        qy2 = qy * sy
        r = np.sqrt(qx2 ** 2 + qy2 ** 2) + 1e-9
        d = (np.cos(r)[..., None] * self.u0
             + (np.sin(r) / r)[..., None] * (qx2[..., None] * self.t_x + qy2[..., None] * self.t_up))
        return d, qx2, qy2

    def _base_surface(self, d):
        p = self.p
        S = p['scale']
        rz = p['rz_bot'] + (p['rz_top'] - p['rz_bot']) * smoothstep(-0.35, 0.35, d[..., 2])
        P = np.stack([p['rx'] * d[..., 0], p['ry'] * d[..., 1], rz * d[..., 2]], -1)
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        front = smoothstep(0.0, -0.75, d[..., 1])
        # jaw taper (narrower toward the chin)
        taper = 1.0 - p['jaw_taper'] * smoothstep(p['jaw_z0'], p['jaw_z1'], z)
        x = x * taper
        # muzzle: brings the lower face forward so it reads vertical
        y = y - p['muzzle'] * bump(z, p['muzzle_z'], p['muzzle_w']) * front * np.exp(-(x / 0.075) ** 2)
        # chin
        wch = smoothstep(-0.20, -0.80, d[..., 2]) * smoothstep(0.10, -0.55, d[..., 1]) * np.exp(-(x / 0.068) ** 2)
        z = z - p['chin_drop'] * wch
        y = y - p['chin'] * wch * smoothstep(0.0, -0.4, d[..., 1])
        # cheeks
        for side in (1, -1):
            dd = ((x - side * p['cheek_x']) ** 2 + (z - p['cheek_z']) ** 2) / p['cheek_r'] ** 2
            g = np.exp(-dd) * front
            x = x + side * 0.4 * p['cheek'] * g
            y = y - p['cheek'] * g
        # brow ridge
        y = y - p['brow_ridge'] * bump(z, p['eye_z'] + 0.030, 0.022) * front * np.exp(-(x / 0.07) ** 4)
        P = np.stack([x, y, z], -1)
        return P

    def _nose(self, P):
        p = self.p
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        front = smoothstep(-0.02, -0.07, y)
        nz = p['nose_z']
        top = nz + p['nose_len']
        # bridge: narrow ridge from between the eyes down to the tip
        tz = np.clip((top - z) / p['nose_len'], 0, 1.3)          # 0 at top, 1 at tip
        along = smoothstep(-0.05, 0.25, tz) * (1 - smoothstep(1.05, 1.35, tz))
        width = p['nose_bridge_w'] + (p['nose_w'] - p['nose_bridge_w']) * tz
        prof = p['nose_proj'] * (0.25 + 0.75 * np.clip(tz, 0, 1) ** 1.6) * along
        ridge = np.exp(-(x / np.maximum(width, 1e-4)) ** 2)
        dy = prof * ridge
        # bulb at the tip
        bz = nz + 0.004
        bd = (x ** 2 / p['nose_bulb_w'] ** 2 + (z - bz) ** 2 / (p['nose_bulb_w'] * 0.85) ** 2)
        dy = dy + p['nose_bulb'] * np.exp(-bd * 1.2)
        # nostril wings
        for side in (1, -1):
            wd = ((x - side * p['nose_bulb_w'] * 0.85) ** 2 + (z - (nz - 0.002)) ** 2) / (p['nose_bulb_w'] * 0.55) ** 2
            dy = dy + 0.45 * p['nose_bulb'] * np.exp(-wd)
        # underside tuck so the nose has a bottom plane
        under = smoothstep(nz - 0.002, nz - 0.016, z) * np.exp(-(x / (p['nose_w'] * 1.4)) ** 2)
        dy = dy * (1 - 0.65 * under)
        y = y - dy * front
        return np.stack([x, y, z], -1)

    def _naso(self, P):
        """Smile lines: shallow creases from the nose wings to past the mouth corners."""
        p = self.p
        if not p['naso']:
            return P
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        front = smoothstep(-0.03, -0.08, y)
        out = P.copy()
        mz = getattr(self, 'mouth_c', np.array([0, 0, -0.05]))[2]
        for side in (1, -1):
            a = np.array([side * p['nose_bulb_w'] * 1.35, p['nose_z'] + 0.004])
            b = np.array([side * (p['mouth_halfw'] * p['ry'] * 1.25), mz - 0.012])
            ab = b - a
            q = np.stack([x, z], -1)
            tt = np.clip(((q - a) @ ab) / (ab @ ab), 0, 1)
            d = np.linalg.norm(q - (a + tt[..., None] * ab), axis=-1)
            env = np.sin(np.pi * np.clip(tt * 1.05, 0, 1)) ** 0.6
            crease = np.exp(-(d / 0.0035) ** 2) * env
            # cheek side of the line bulges slightly
            sgn = np.sign((q - a) @ np.array([-ab[1], ab[0]]) * side)
            bulge = np.exp(-((d - 0.006) / 0.006) ** 2) * env * (sgn < 0)
            out[..., 1] = out[..., 1] + p['naso'] * (crease - 0.5 * bulge) * front
        return out

    def _lips(self, P, mp):
        p = self.p
        th0 = p['mouth_halfw']
        t = (self.TH - th0) / p['lip_w']
        upper = np.cos(self.PH) > 0
        amp = np.where(upper, p['lip_up'] * mp['lip_up'], p['lip_lo'] * mp['lip_lo'])
        # profile: rolls in at the slit, swells, returns to skin
        prof = np.where(t < 1.0, np.sin(np.pi * np.clip(t, 0, 1) ** 0.75), 0.0)
        prof = prof - 0.25 * np.exp(-(t / 0.08) ** 2)
        # thinner toward the corners
        side = np.abs(np.sin(self.PH))
        corner = 1.0 - 0.55 * side ** 3
        # cupid's bow on the upper lip
        bow = np.where(upper, 1.0 + 0.25 * np.exp(-((np.abs(np.sin(self.PH)) - 0.25) / 0.12) ** 2), 1.0)
        push = (amp * prof * corner * bow + mp['pucker'] * 0.010 * smoothstep(1.6, 0.0, t))
        return P + push[..., None] * self.u0

    def _corners(self, P, mp, qx, qy):
        """Smile / frown / upper-lip raise displacements (additive)."""
        p = self.p
        th0 = p['mouth_halfw']
        out = P.copy()
        for side, key in ((1, 'L'), (-1, 'R')):
            sm = mp['smile_' + key]
            fr = mp['frown_' + key]
            if sm == 0 and fr == 0:
                continue
            g = np.exp(-(((qx - side * th0 * 0.95) / 0.30) ** 2 + (qy / 0.22) ** 2))
            g = g * (side * qx > -0.05)
            S = self.p['scale']
            out[..., 2] += (0.008 * sm - 0.009 * fr) * g
            out[..., 0] += side * (0.007 * sm - 0.002 * fr) * g
            out[..., 1] += (0.006 * sm) * g
            # cheek raise on smile
            cg = np.exp(-(((qx - side * (th0 + 0.30)) / 0.28) ** 2 + ((qy - 0.30) / 0.25) ** 2))
            out[..., 2] += 0.0045 * sm * cg
            out[..., 1] -= 0.0035 * sm * cg
        ul = mp['lip_raise']
        if ul:
            g = np.exp(-((qx / 0.35) ** 2)) * smoothstep(0.0, 0.05, qy) * np.exp(-((qy - 0.08) / 0.2) ** 2)
            out[..., 2] += 0.004 * ul * g
        return out

    # ------------------------------------------------------------------
    def _place_features(self):
        """Eye centres, brow anchors, jaw pivot, mouth centre (rest pose)."""
        p = self.p
        mp = self.mouth_params()
        d, qx, qy = self._directions(mp)
        P = self._nose(self._base_surface(d))
        self._front_ref = P
        # eye centres: sit so a fraction of the eyeball pokes out of the face
        self.eyes = {}
        for side, key in ((1, 'L'), (-1, 'R')):
            ex, ez = side * p['eye_x'], p['eye_z']
            flat = P.reshape(-1, 3)
            m = flat[:, 1] < 0
            dd = (flat[m, 0] - ex) ** 2 + (flat[m, 2] - ez) ** 2
            ysurf = flat[m][np.argmin(dd), 1]
            ey = ysurf + p['eye_r'] * (1 - 2 * p['eye_protrude']) + p['eye_r'] * 0.15
            fwd = np.array([side * np.sin(np.radians(p['eye_out'])), -np.cos(np.radians(p['eye_out'])), 0.0])
            self.eyes[key] = dict(c=np.array([ex, ey, ez]), fwd=fwd, side=side)
        # mouth centre and jaw pivot
        ring0 = P[0]
        self.mouth_c = ring0.mean(0)
        self.jaw_pivot = np.array([0.0, 0.012, self.mouth_c[2] + 0.025])
        # brow anchors (inner, mid, outer) per side
        self.brows = {}
        r = p['eye_r']
        for key, e in self.eyes.items():
            s = e['side']
            c = e['c']
            pts = []
            for fx, fz in ((0.95, 1.30), (0.05, 1.62), (-0.95, 1.38)):
                bx = c[0] - s * fx * r * 1.15
                bz = c[2] + fz * r
                pts.append([bx, bz])
            self.brows[key] = np.array(pts)
        self._eyes_ready = True

    def mouth_params(self, **kw):
        cr = self.p['corner_rest']
        mp = dict(sy0=self.p['mouth_sy0'], sx=1.0, lip_up=1.0, lip_lo=1.0, pucker=0.0,
                  smile_L=0.0, smile_R=0.0, frown_L=0.0, frown_R=0.0, lip_raise=0.0)
        for k_, v_ in kw.items():
            mp[k_] = mp[k_] + v_ if k_ in ('frown_L', 'frown_R', 'smile_L', 'smile_R') else v_
        mp['frown_L'] += cr
        mp['frown_R'] += cr
        return mp

    def _eye_sockets(self, P):
        p = self.p
        r = p['eye_r']
        out = P.copy()
        for key, e in self.eyes.items():
            c, fwd = e['c'], e['fwd']
            v = out - c
            dist = np.linalg.norm(v, axis=-1) + 1e-9
            dv = v / dist[..., None]
            # local eye frame
            up = np.array([0, 0, 1.0])
            sx = np.cross(fwd, up)
            sx /= np.linalg.norm(sx)
            uz = np.cross(sx, fwd)
            a_h = np.degrees(np.arctan2((dv @ sx), (dv @ fwd)))
            a_v = np.degrees(np.arctan2((dv @ uz), (dv @ fwd)))
            # elliptical angular distance normalised to the opening edge
            e_ = np.sqrt((a_h / p['eye_open_h']) ** 2 + (a_v / p['eye_open_v']) ** 2)
            cosang = dv @ fwd
            k = 0.86 + (1.03 - 0.86) * smoothstep(0.85, 1.15, e_)
            target = r * k
            infl = smoothstep(2.1 * r, 1.15 * r, dist) * smoothstep(-0.2, 0.25, cosang)
            infl = np.maximum(infl, smoothstep(1.7, 1.15, e_) * smoothstep(2.0 * r, 1.3 * r, dist))
            newd = dist + (target - dist) * infl
            out = c + dv * newd[..., None]
        return out

    # ------------------------------------------------------------------
    def surface(self, **mkw):
        mp = self.mouth_params(**mkw)
        d, qx, qy = self._directions(mp)
        P = self._base_surface(d)
        P = self._nose(P)
        P = self._naso(P)
        P = self._lips(P, mp)
        P = self._corners(P, mp, qx, qy)
        P = self._eye_sockets(P)
        return P, mp, qx, qy

    def _bag(self, P, mp):
        """Mouth cavity rings extruded inward from the slit."""
        p = self.p
        hw = p['mouth_halfw'] * p['ry'] * mp['sx']
        ring0 = P[0]
        c = ring0.mean(0)
        inward = -self.u0
        specs = [(0.004, 0.92, 0.008), (0.012, 0.88, 0.020), (0.026, 0.80, 0.028),
                 (0.040, 0.66, 0.026), (0.050, 0.42, 0.018)]
        rings = []
        for i, (dep, wf, h) in enumerate(specs):
            xs = np.sin(self.phi) * hw * wf
            zs = np.cos(self.phi) * h
            pts = c + inward * dep + xs[:, None] * self.t_x + zs[:, None] * self.t_up
            if i == 0:
                pts = 0.5 * pts + 0.5 * (ring0 + inward * dep)
            rings.append(pts)
        cap = c + inward * 0.056
        return np.array(rings), cap

    def build(self):
        """Returns dict with verts, faces, shape keys, weights, colours, features."""
        p = self.p
        NR, NS = len(self.theta), len(self.phi)
        P, mp, qx, qy = self.surface()
        bag, cap = self._bag(P, mp)
        back = P[-1].mean(0) + norm(P[-1].mean(0)) * 0.0015
        verts = np.concatenate([P.reshape(-1, 3), [back], bag.reshape(-1, 3), [cap]])
        iback = NR * NS
        ibag0 = iback + 1
        NB = bag.shape[0]
        icap = ibag0 + NB * NS
        faces = []
        for j in range(NR - 1):
            for k in range(NS):
                a = j * NS + k
                b = j * NS + (k + 1) % NS
                c_ = (j + 1) * NS + (k + 1) % NS
                d_ = (j + 1) * NS + k
                faces.append((a, d_, c_, b))
        for k in range(NS):
            a = (NR - 1) * NS + k
            b = (NR - 1) * NS + (k + 1) % NS
            faces.append((a, iback, b))
        # bag: ring0 of head -> bag rings -> cap
        prev = [k for k in range(NS)]
        for i in range(NB):
            cur = [ibag0 + i * NS + k for k in range(NS)]
            for k in range(NS):
                faces.append((prev[k], prev[(k + 1) % NS], cur[(k + 1) % NS], cur[k]))
            prev = cur
        for k in range(NS):
            faces.append((prev[k], prev[(k + 1) % NS], icap))

        def full(Pm, mpm):
            bg, cp = self._bag(Pm, mpm)
            bk = Pm[-1].mean(0) + norm(Pm[-1].mean(0)) * 0.0015
            return np.concatenate([Pm.reshape(-1, 3), [bk], bg.reshape(-1, 3), [cp]])

        shapes = {}
        defs = {
            'wide': dict(sx=1.18, lip_up=0.75, lip_lo=0.8),
            'round': dict(sx=0.62, sy0=0.30, lip_up=1.35, lip_lo=1.35, pucker=0.9),
            'press': dict(sy0=0.0, lip_up=0.7, lip_lo=0.7, pucker=-0.25),
            'smile_L': dict(smile_L=1.0),
            'smile_R': dict(smile_R=1.0),
            'frown_L': dict(frown_L=1.0),
            'frown_R': dict(frown_R=1.0),
            'lip_raise': dict(lip_raise=1.0),
            'pout': dict(lip_lo=1.6, pucker=0.35),
        }
        for name, kw in defs.items():
            Pm, mpm, _, _ = self.surface(**kw)
            shapes[name] = full(Pm, mpm)

        # ---------------- weights ----------------
        nv = len(verts)
        W = {}
        TH = np.concatenate([self.TH.reshape(-1), [np.pi], np.zeros(NB * NS), [0.0]])
        PH = np.concatenate([self.PH.reshape(-1), [0.0], np.tile(self.phi, NB), [np.pi]])
        lower = smoothstep(np.pi / 2 - 0.35, np.pi / 2 + 0.35, np.abs(((PH + np.pi) % (2 * np.pi)) - np.pi))
        # positional jaw region (for vertices away from the mouth)
        x, y, z = verts[:, 0], verts[:, 1], verts[:, 2]
        mc = self.mouth_c
        zline = mc[2] + np.maximum(y - mc[1], 0) * 0.55
        wpos = smoothstep(zline + 0.006, zline - 0.012, z)
        wpos *= smoothstep(0.045, 0.0, y)  # not the back of the head
        wpos *= smoothstep(p['rx'] * 1.05, p['rx'] * 0.55, np.abs(x)) * 0.5 + 0.5 * smoothstep(0.03, -0.04, y)
        near = smoothstep(p['mouth_halfw'] + p['mouth_blend'] * 0.8, p['mouth_halfw'] + 0.05, TH)
        near[iback] = 0
        wj = near * lower + (1 - near) * wpos
        wj[ibag0:icap] = lower[ibag0:icap]
        wj[icap] = 0.5
        W['jaw'] = np.clip(wj, 0, 1)
        # brows: skin around each brow follows the brow bones partially
        for key, pts in self.brows.items():
            for i, nm in enumerate(('in', 'mid', 'out')):
                bx, bz = pts[i]
                dd = ((x - bx) ** 2 + ((z - bz) / 1.15) ** 2) / (p['eye_r'] * 1.0) ** 2
                w = 0.65 * np.exp(-dd) * smoothstep(-0.03, -0.07, y)
                W['brow_%s_%s' % (nm, key)] = w
        tot = sum(W.values())
        over = np.maximum(tot, 1.0)
        for kname in W:
            W[kname] = W[kname] / over
        W['head'] = np.clip(1.0 - sum(W.values()), 0, 1)

        # ---------------- vertex colours ----------------
        # lip mask (R), blush mask (G), mouth interior (B)
        lip_t = (TH - p['mouth_halfw']) / (p['lip_w'] * 1.05)
        lipm = smoothstep(1.0, 0.70, lip_t) * (TH < 2.0)
        lipm *= 1.0 - 0.6 * smoothstep(0.75, 1.0, np.abs(np.sin(PH))) * smoothstep(0.4, 1.0, lip_t)
        bl = np.zeros(nv)
        for side in (1, -1):
            dd = ((x - side * (p['cheek_x'] + 0.005)) ** 2 + (z - (p['cheek_z'] + 0.008)) ** 2) / (0.026 ** 2)
            bl += np.exp(-dd) * smoothstep(-0.02, -0.06, y)
        dd = (x ** 2 + (z - p['nose_z']) ** 2) / 0.014 ** 2
        bl += 0.6 * np.exp(-dd) * smoothstep(-0.05, -0.09, y)
        inner = np.zeros(nv)
        inner[ibag0:] = 1.0
        lipm[ibag0:] = 0
        col = np.stack([np.clip(lipm, 0, 1), np.clip(bl, 0, 1), inner], -1)

        return dict(verts=verts, faces=faces, shapes=shapes, weights=W, colors=col,
                    eyes=self.eyes, brows=self.brows, jaw_pivot=self.jaw_pivot,
                    mouth_c=self.mouth_c, u0=self.u0, t_x=self.t_x, t_up=self.t_up,
                    index=dict(back=iback, bag0=ibag0, cap=icap, NS=NS, NR=NR))

    # ------------------------------------------------------------------
    def teeth(self, upper=True):
        """A curved row of teeth just behind the lips (head space)."""
        p = self.p
        hw = p['mouth_halfw'] * p['ry'] * 0.74
        c = self.mouth_c - self.u0 * 0.011
        n = 24
        xs = np.linspace(-hw, hw, n)
        curve_back = (xs / hw) ** 2 * 0.012
        h = 0.0068
        th = 0.0035
        sgn = 1 if upper else -1
        verts, faces = [], []
        top_off = 0.0035 if upper else 0.0035
        for i, xv in enumerate(xs):
            base = c + xv * self.t_x + (-self.u0) * curve_back[i] + sgn * top_off * self.t_up
            taper = 1.0 - 0.35 * (abs(xv) / hw) ** 2
            if upper and p['tooth_gap'] and 0.002 < xv < 0.010:
                taper = 0.12
            for (dz, dy) in ((0, 0), (sgn * h * taper, 0), (sgn * h * taper, th), (0, th)):
                verts.append(base + dz * self.t_up + (-self.u0) * dy)
        for i in range(n - 1):
            a = i * 4
            b = (i + 1) * 4
            for k in range(4):
                faces.append((a + k, a + (k + 1) % 4, b + (k + 1) % 4, b + k))
        faces.append((0, 1, 2, 3)[::-1])
        e = (n - 1) * 4
        faces.append((e, e + 1, e + 2, e + 3))
        return np.array(verts), faces

    def tongue(self):
        p = self.p
        hw = p['mouth_halfw'] * p['ry'] * 0.55
        c = self.mouth_c - self.u0 * 0.026 - self.t_up * 0.012
        return c, np.array([hw, 0.024, 0.008])

    def lid(self, key, upper=True, nu=48, nv=14):
        """Eyelid shell in EYE-LOCAL space (eye centre at origin, forward -Y, up +Z).

        The rim edge is arched; rotating about local X closes/opens the lid.  The shell is laid
        out in rings around the X axis (the hinge), so its sides stay at the sides of the eyeball
        however far it rotates, and there is no pole on top to show as a seam when the lid is shut."""
        p = self.p
        r = p['eye_r']
        side = self.eyes[key]['side']
        R = r * 1.035
        azc = p['lid_corner_az']
        tilt = p['canthus_tilt']
        # rim edge as elevation over azimuth (the authored lid shape) ...
        a = np.linspace(-azc - 25, azc + 25, 161)
        t = np.clip(np.abs(a) / azc, 0, 1)
        outer = (a * side) > 0
        corner_lift = np.where(outer, tilt, -tilt * 0.3) * smoothstep(0.4, 1.0, t)
        if upper:
            e = p['lid_up_e'] + p['lid_up_arch'] * (1 - t ** 2) - p['lid_up_arch'] * 0.5 + corner_lift
        else:
            e = p['lid_lo_e'] - p['lid_lo_arch'] * (1 - t ** 2) + corner_lift * 0.6
        ar, er = np.radians(a), np.radians(e)
        ex, ey, ez = np.sin(ar) * np.cos(er), -np.cos(ar) * np.cos(er), np.sin(er)
        # ... re-expressed as (angle from the hinge plane, angle about the hinge)
        h_dense = np.degrees(np.arcsin(np.clip(ex, -1, 1)))
        v_dense = np.degrees(np.arctan2(ez, -ey))
        hs_ = np.linspace(-84.0, 84.0, nu)
        verts = []
        for h in hs_:
            e_edge = float(np.interp(h, h_dense, v_dense))
            if upper:
                # runs over the top and down the back so a fully closed lid still covers the eyeball
                elev = np.concatenate([[e_edge - 4, e_edge - 2.5, e_edge - 0.6], np.linspace(e_edge, 185, nv + 6)])
                radii = np.concatenate([[r * 1.004, r * 1.018, r * 1.036], np.full(nv + 6, R)])
            else:
                elev = np.concatenate([[e_edge + 4, e_edge + 2.5, e_edge + 0.6], np.linspace(e_edge, -100, nv)])
                radii = np.concatenate([[r * 1.004, r * 1.018, r * 1.032], np.full(nv, R * 0.995)])
            hh, vv = np.radians(h), np.radians(elev)
            col = np.stack([np.full(len(vv), np.sin(hh)), -np.cos(hh) * np.cos(vv), np.cos(hh) * np.sin(vv)], -1) * radii[:, None]
            verts.append(col)
        V = np.array(verts)  # (nu, nrow, 3)
        nrow = V.shape[1]
        faces = []
        for i in range(nu - 1):
            for j in range(nrow - 1):
                a = i * nrow + j
                b = (i + 1) * nrow + j
                if upper:
                    faces.append((a, b, b + 1, a + 1))
                else:
                    faces.append((a, a + 1, b + 1, b))
        # lash mask: first rows at the rim
        lash = np.zeros((nu, nrow))
        if upper:
            lash[:, 0:2] = 1.0
            lash[:, 2] = 0.5
        else:
            lash[:, 0:2] = 0.25
        return V.reshape(-1, 3), faces, lash.reshape(-1)

    def ear(self, side):
        p = self.p
        s = p['ear_size']
        nu, nv = 24, 16
        verts = []
        for i in range(nv + 1):
            v = np.pi * i / nv
            for j in range(nu):
                u = 2 * np.pi * j / nu
                x = np.sin(v) * np.cos(u)
                y = np.sin(v) * np.sin(u)
                z = np.cos(v)
                verts.append([x, y, z])
        V = np.array(verts)
        # flatten into an ear disc, cup the outward face
        X = V[:, 0] * 0.010 * s
        Y = V[:, 1] * 0.024 * s
        Z = V[:, 2] * 0.034 * s
        cup = np.exp(-((V[:, 1] / 0.55) ** 2 + (V[:, 2] / 0.6) ** 2))
        X = X - 0.010 * s * cup * (V[:, 0] > 0)
        # lobe narrower and lower part thicker
        Y = Y * (1 - 0.25 * smoothstep(0.2, -0.9, V[:, 2]))
        P = np.stack([X * side, Y, Z], -1)
        # tilt back
        a = np.radians(14)
        rot = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
        P = P @ rot.T
        # yaw slightly so it faces forward-out
        b = np.radians(-18 * side)
        roty = np.array([[np.cos(b), -np.sin(b), 0], [np.sin(b), np.cos(b), 0], [0, 0, 1]])
        P = P @ roty.T
        P = P + np.array([side * (p['rx'] * (1 - p['jaw_taper'] * 0.15) + 0.002), p['ear_y'], p['ear_z']])
        faces = []
        for i in range(nv):
            for j in range(nu):
                a_ = i * nu + j
                b_ = i * nu + (j + 1) % nu
                c_ = (i + 1) * nu + (j + 1) % nu
                d_ = (i + 1) * nu + j
                faces.append((a_, b_, c_, d_) if side > 0 else (a_, d_, c_, b_))
        return P, faces
