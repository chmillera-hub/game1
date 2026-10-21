"""Vectorised 3D ray trace through the vibrating prism (numpy port of bench/physics.js).

Lab frame: beam travels +x, y is left/right across the beam, z is up. The prism's
refracting edge is vertical, so up/down tilts send rays through it at a slant.
Arrays broadcast: motion parameters typically carry a time axis (Nt, 1) and the
refractive index a wavelength axis (1, Nl).
"""
import numpy as np
from prism_sim import n_glass, cmf, planck, XYZ2RGB, SPEC_XYZ, xyz_to_srgb, APEX

DEG = np.pi / 180
SIDE = 40.0
PH = SIDE * np.sqrt(3) / 2
PV = np.array([[0, 2 * PH / 3], [-SIDE / 2, -PH / 3], [SIDE / 2, -PH / 3]])
BEAM_Y = 9.0
SOURCE_X = -200.0


def _faces():
    out = []
    for a, b in [(0, 1), (1, 2), (2, 0)]:
        A, B = PV[a], PV[b]
        e = B - A
        n = np.array([e[1], -e[0]]) / np.hypot(*e)
        if n @ ((A + B) / 2) < 0:
            n = -n
        out.append((A, e, np.array([n[0], n[1], 0.0])))
    return out


FACES = _faces()


def pose_matrix(rot, nod):
    """lab = Ry(nod) @ Rz(rot) @ prism, for arrays of rot/nod -> (..., 3, 3)."""
    rot, nod = np.broadcast_arrays(np.asarray(rot, float), np.asarray(nod, float))
    cr, sr, cn, sn = np.cos(rot), np.sin(rot), np.cos(nod), np.sin(nod)
    z, o = np.zeros_like(rot), np.ones_like(rot)
    Rz = np.stack([np.stack([cr, -sr, z], -1), np.stack([sr, cr, z], -1), np.stack([z, z, o], -1)], -2)
    Ry = np.stack([np.stack([cn, z, sn], -1), np.stack([z, o, z], -1), np.stack([-sn, z, cn], -1)], -2)
    return Ry @ Rz


def _hit(p, d, face):
    A, e, n = face
    den = d[..., 0] * n[0] + d[..., 1] * n[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        t = ((A[0] - p[..., 0]) * n[0] + (A[1] - p[..., 1]) * n[1]) / den
        q = p + t[..., None] * d
        s = ((q[..., 0] - A[0]) * e[0] + (q[..., 1] - A[1]) * e[1]) / (e @ e)
    ok = (t > 1e-9) & (s >= 0) & (s <= 1) & np.isfinite(t)
    return np.where(ok, t, np.inf), q


def _refract(d, nrm, eta):
    cosi = -(d * nrm).sum(-1, keepdims=True)
    k = 1 - eta ** 2 * (1 - cosi ** 2)
    out = eta * d + (eta * cosi - np.sqrt(np.clip(k, 0, None))) * nrm
    return out, k[..., 0] >= 0


def trace(p0, d0, n, M, T):
    """p0, d0: (..., 3) lab; n: (...); M: (..., 3, 3); T: (..., 3). Returns p2, d2, ok."""
    n = np.asarray(n, float)
    shape = np.broadcast_shapes(n.shape, p0.shape[:-1], d0.shape[:-1], M.shape[:-2], T.shape[:-1])
    MT = np.swapaxes(M, -1, -2)
    p = np.broadcast_to((MT @ (p0 - T)[..., None])[..., 0], shape + (3,))
    d = np.broadcast_to((MT @ d0[..., None])[..., 0], shape + (3,))
    n = np.broadcast_to(n, shape)
    F0, F1, F2 = FACES
    ok = (d @ F0[2]) < 0
    t0, q0 = _hit(p, d, F0)
    t1, _ = _hit(p, d, F1)
    t2, _ = _hit(p, d, F2)
    ok &= np.isfinite(t0) & (t0 <= t1) & (t0 <= t2)
    d1, ok1 = _refract(d, F0[2], 1 / n[..., None])
    ok &= ok1
    p1 = q0
    tA, _ = _hit(p1, d1, F1)
    tB, qB = _hit(p1, d1, F2)
    ok &= np.isfinite(tB) & (tB <= tA)
    d2, ok2 = _refract(d1, -F2[2], n[..., None])
    ok &= ok2
    p2 = (M @ qB[..., None])[..., 0] + T
    d2 = (M @ d2[..., None])[..., 0]
    return p2, d2, ok


def rot_for_incidence(theta_deg):
    return (30.0 - np.asarray(theta_deg, float)) * DEG


def min_dev_incidence(lam):
    return np.degrees(np.arcsin(n_glass(lam) * np.sin(APEX / 2)))


class Bench3D:
    """Wall perpendicular to the still 550 nm ray, L mm from the prism."""

    def __init__(self, theta_deg, L=1000.0):
        self.base = float(rot_for_incidence(theta_deg))
        M = pose_matrix(self.base, 0.0)
        p2, d2, ok = trace(np.array([SOURCE_X, BEAM_Y, 0.0]), np.array([1.0, 0, 0]), n_glass(550.0), M, np.zeros(3))
        self.axis = d2 / np.linalg.norm(d2)
        self.origin = L * self.axis
        self.uh = np.array([-self.axis[1], self.axis[0], 0.0])

    def wall(self, n, target='prism', slideH=0.0, slideV=0.0, turnH=0.0, turnV=0.0):
        """Wall coordinates (u, v) in mm, shape broadcast(motion params, n); NaN where blocked.
        turnH/turnV in radians: rock/nod for the prism, aim for the light."""
        # a trailing axis lines the motion parameters up against the wavelength axis of n
        sH, sV, tH, tV = np.broadcast_arrays(*[np.asarray(x, float)[..., None] for x in (slideH, slideV, turnH, turnV)])
        if target == 'light':
            p0 = np.stack([np.full_like(sH, SOURCE_X), BEAM_Y + sH, sV], -1)
            d0 = np.stack([np.cos(tV) * np.cos(tH), np.cos(tV) * np.sin(tH), np.sin(tV)], -1)
            M = pose_matrix(self.base, 0.0)
            T = np.zeros(3)
        else:
            p0 = np.array([SOURCE_X, BEAM_Y, 0.0])
            d0 = np.array([1.0, 0.0, 0.0])
            M = pose_matrix(self.base + tH, tV)
            T = np.stack([np.zeros_like(sH), sH, sV], -1)
        p2, d2, ok = trace(p0, d0, n, M, T)
        A = self.axis
        with np.errstate(divide='ignore', invalid='ignore'):
            t = ((self.origin - p2) @ A) / (d2 @ A)
        q = p2 + t[..., None] * d2 - self.origin
        u, v = q @ self.uh, q[..., 2]
        bad = ~ok | ~(t > 0)
        return np.where(bad, np.nan, u), np.where(bad, np.nan, v)
