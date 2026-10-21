"""Physics + colour engine for the vibrating-prism experiments.

2D exact ray trace (vector Snell's law) through an equilateral SF11 flint-glass
prism, real Sellmeier dispersion, CIE 1931 colour matching (Wyman et al. 2013
analytic fit) and physically additive colour mixing in XYZ space.
All lengths in mm, angles in radians unless noted.
"""
import numpy as np

# ---------------------------------------------------------------- glass
# Schott SF11 Sellmeier coefficients (lambda in micrometres)
_B = (1.73759695, 0.313747346, 1.89878101)
_C = (0.013188707, 0.0623068142, 155.23629)


def n_glass(lam_nm):
    l2 = (np.asarray(lam_nm, float) / 1000.0) ** 2
    s = sum(b * l2 / (l2 - c) for b, c in zip(_B, _C))
    return np.sqrt(1.0 + s)


# ---------------------------------------------------------------- colour
def _g(lam, mu, s1, s2):
    s = np.where(lam < mu, s1, s2)
    return np.exp(-0.5 * ((lam - mu) / s) ** 2)


def cmf(lam):
    lam = np.asarray(lam, float)
    x = 1.056 * _g(lam, 599.8, 37.9, 31.0) + 0.362 * _g(lam, 442.0, 16.0, 26.7) - 0.065 * _g(lam, 501.1, 20.4, 26.2)
    y = 0.821 * _g(lam, 568.8, 46.9, 40.5) + 0.286 * _g(lam, 530.9, 16.3, 31.1)
    z = 1.217 * _g(lam, 437.0, 11.8, 36.0) + 0.681 * _g(lam, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], -1)


XYZ2RGB = np.array([[3.2406, -1.5372, -0.4986],
                    [-0.9689, 1.8758, 0.0415],
                    [0.0557, -0.2040, 1.0570]])


def planck(lam_nm, T=6500.0):
    lam = np.asarray(lam_nm, float) * 1e-9
    h, c, k = 6.626e-34, 2.998e8, 1.381e-23
    return 1.0 / (lam ** 5 * (np.exp(h * c / (lam * k * T)) - 1.0))


LAM = np.linspace(390, 700, 156)            # wavelength samples (2 nm)
N_LAM = n_glass(LAM)
_W = planck(LAM)
# weights so that the full spectrum integrates to the sRGB white point
_xyz_w = (_W[:, None] * cmf(LAM)).sum(0)
_rgb_w = XYZ2RGB @ _xyz_w
SPEC_XYZ = _W[:, None] * cmf(LAM) / _xyz_w[1]     # per-wavelength XYZ (sum Y = 1)
WHITE_BALANCE = _rgb_w / _rgb_w.max()


def xyz_to_srgb(xyz, exposure=1.0):
    """XYZ (..., 3) -> display sRGB in [0,1]. Out-of-gamut spectral colours
    get the minimum white added; over-bright pixels roll off hue-preservingly."""
    rgb = xyz @ XYZ2RGB.T / WHITE_BALANCE
    rgb = rgb * exposure
    # out-of-gamut spectral colours: add just enough white to reach the gamut
    rgb = rgb - np.minimum(rgb.min(-1, keepdims=True), 0)
    mx = rgb.max(-1, keepdims=True)
    knee = 0.75   # soft shoulder, hue preserving
    soft = knee + (1 - knee) * np.tanh((mx - knee) / (1 - knee))
    rgb = np.where(mx > knee, rgb * soft / np.maximum(mx, 1e-12), rgb)
    rgb = np.clip(rgb, 0, 1)
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - 0.055)


def lam_to_srgb(lam):
    return xyz_to_srgb(cmf(np.atleast_1d(lam)) / cmf(np.atleast_1d(lam))[..., 1:2].clip(0.05) * 0.6)


# ---------------------------------------------------------------- geometry
SIDE = 40.0                       # prism side length
APEX = np.radians(60)


def prism_vertices(rot=0.0, shift=(0.0, 0.0)):
    """Equilateral prism, apex up, centroid at origin, rotated by rot."""
    h = SIDE * np.sqrt(3) / 2
    v = np.array([[0, 2 * h / 3], [-SIDE / 2, -h / 3], [SIDE / 2, -h / 3]])
    c, s = np.cos(rot), np.sin(rot)
    R = np.array([[c, -s], [s, c]])
    return v @ R.T + np.asarray(shift)


def _hit(p, d, a, b):
    """Intersect rays p + t d with segment a-b. Returns t (inf if miss)."""
    e = b - a
    den = d[..., 0] * e[1] - d[..., 1] * e[0]
    w = a - p
    t = (w[..., 0] * e[1] - w[..., 1] * e[0]) / den
    u = (w[..., 0] * d[..., 1] - w[..., 1] * d[..., 0]) / den
    ok = (t > 1e-9) & (u >= 0) & (u <= 1)
    return np.where(ok, t, np.inf)


def _refract(d, nrm, eta):
    """Vector Snell. nrm faces the incoming ray's side. Returns (t, TIR mask)."""
    cosi = -(d * nrm).sum(-1, keepdims=True)
    k = 1 - eta ** 2 * (1 - cosi ** 2)
    tir = (k[..., 0] < 0)
    t = eta * d + (eta * cosi - np.sqrt(np.clip(k, 0, None))) * nrm
    return t, tir


def trace(p0, d0, n, rot=0.0, shift=(0.0, 0.0)):
    """Trace rays through the prism. p0, d0: (..., 2); n: (...); rot (...)
    and shift (..., 2) broadcast against n (vectorised by moving the beam
    into the prism frame). Returns entry pt, exit pt, exit dir, valid mask,
    all in the lab frame."""
    n = np.asarray(n, float)
    rot = np.asarray(rot, float)
    shift = np.asarray(shift, float)
    shape = np.broadcast_shapes(n.shape, rot.shape, shift.shape[:-1],
                                np.shape(p0)[:-1], np.shape(d0)[:-1])
    n = np.broadcast_to(n, shape)
    c, s = np.cos(rot)[..., None], np.sin(rot)[..., None]

    def to_prism(v, is_point):
        v = np.asarray(v, float) - (shift if is_point else 0)
        x, y = v[..., :1], v[..., 1:]
        return np.concatenate([c * x + s * y, -s * x + c * y], -1)

    def to_lab(v, is_point):
        x, y = v[..., :1], v[..., 1:]
        out = np.concatenate([c * x - s * y, s * x + c * y], -1)
        return out + (shift if is_point else 0)

    p = np.broadcast_to(to_prism(p0, True), shape + (2,)).copy()
    d = np.broadcast_to(to_prism(d0, False), shape + (2,)).copy()
    V = prism_vertices()
    faces = [(V[0], V[1]), (V[1], V[2]), (V[2], V[0])]
    cen = V.mean(0)

    def outward(a, b):
        e = b - a
        nn = np.array([e[1], -e[0]]) / np.hypot(*e)
        return nn if np.dot(nn, (a + b) / 2 - cen) > 0 else -nn

    NRM = np.stack([outward(a, b) for a, b in faces])
    with np.errstate(divide='ignore', invalid='ignore'):
        ts = np.stack([_hit(p, d, a, b) for a, b in faces], -1)        # entry
        fi = ts.argmin(-1)
        t1 = ts.min(-1)
        valid = np.isfinite(t1)
        p1 = p + np.where(valid, t1, 0)[..., None] * d
        d1, tir1 = _refract(d, NRM[fi], 1.0 / n[..., None])
        ts2 = np.stack([_hit(p1 + 1e-7 * d1, d1, a, b) for a, b in faces], -1)  # exit
        ts2 = np.where(np.arange(3) == fi[..., None], np.inf, ts2)
        fo = ts2.argmin(-1)
        t2 = ts2.min(-1)
        valid &= np.isfinite(t2)
        p2 = p1 + np.where(np.isfinite(t2), t2, 0)[..., None] * d1
        d2, tir2 = _refract(d1, -NRM[fo], n[..., None])               # inward normal
    valid &= ~tir2 & ~tir1
    valid &= (fi == 0) & (fo == 2)        # enter face V0-V1, leave face V2-V0
    return to_lab(p1, True), to_lab(p2, True), to_lab(d2, False), valid


# ---------------------------------------------------------------- the bench
BEAM_Y = 9.0                     # incident beam height (mm): centre of entry face
BEAM_DIR = np.array([1.0, 0.0])
BEAM_START = np.array([-60.0, BEAM_Y])
L_SCREEN = 1000.0                # screen distance from prism centroid


def rot_for_incidence(theta1_deg):
    """Prism rotation giving incidence angle theta1 on the entry face for the
    horizontal beam (the apex-up prism has 30 deg incidence at rot=0)."""
    return np.radians(30.0 - np.asarray(theta1_deg, float))


class Bench:
    """Fixed screen placed perpendicular to the 550 nm exit ray of a
    reference configuration, L mm from the prism."""

    def __init__(self, ref_rot, L=L_SCREEN):
        p1, p2, d2, ok = trace(BEAM_START, BEAM_DIR, n_glass(550.0), ref_rot)
        self.axis = d2 / np.linalg.norm(d2)
        self.origin = L * self.axis
        self.u = np.array([-self.axis[1], self.axis[0]])  # screen coordinate direction
        self.ref_rot = ref_rot
        self.entry = p1

    def screen_pos(self, p2, d2):
        t = ((self.origin - p2) * self.axis).sum(-1) / (d2 * self.axis).sum(-1)
        hit = p2 + t[..., None] * d2
        return ((hit - self.origin) * self.u).sum(-1)

    def positions(self, rot=None, shift=(0.0, 0.0), beam_angle=0.0, beam_pivot=None, n=N_LAM):
        """Screen positions (..., n_lam). rot / beam_angle / shift may carry
        a leading time axis."""
        rot = self.ref_rot if rot is None else rot
        rot = np.asarray(rot, float)[..., None]
        ba = np.asarray(beam_angle, float)[..., None]
        shift = np.asarray(shift, float)
        if shift.ndim > 1:
            shift = shift[..., None, :]
        d0 = np.stack([np.cos(ba), np.sin(ba)], -1)
        if beam_pivot is None:
            p0 = BEAM_START + 0 * d0
        else:  # beam rotates about the pivot point
            p0 = np.asarray(beam_pivot) - 80.0 * d0
        p1, p2, d2, ok = trace(p0, d0, n, rot, shift)
        x = self.screen_pos(p2, d2)
        return np.where(ok, x, np.nan)


# ---------------------------------------------------------------- rendering
def screen_xyz(x_lam, px, sigma=2.0, spec_xyz=None):
    """Instantaneous screen irradiance. x_lam: (n_lam,) positions (mm);
    px: uniformly spaced pixel centres (mm). Returns (n_px, 3) XYZ."""
    return screen_xyz_avg(np.atleast_2d(x_lam), px, sigma, spec_xyz)


def screen_xyz_avg(x_lam, px, sigma=2.0, spec_xyz=None):
    """Time-averaged screen irradiance for positions x_lam: (n_t, n_lam).
    Deposits each wavelength into the pixel grid, then blurs by the slit
    image width. Returns (n_px, 3) XYZ."""
    spec = SPEC_XYZ if spec_xyz is None else spec_xyz
    x = np.atleast_2d(x_lam)
    nt, nl = x.shape
    dx = px[1] - px[0]
    f = (x - px[0]) / dx
    ok = np.isfinite(f) & (f >= 0) & (f < len(px) - 1)
    f = np.where(ok, f, 0)
    i0 = np.floor(f).astype(int)
    w1 = f - i0
    li = np.broadcast_to(np.arange(nl), x.shape)
    dens = np.zeros((len(px), nl))
    np.add.at(dens, (i0[ok], li[ok]), 1 - w1[ok])
    np.add.at(dens, (i0[ok] + 1, li[ok]), w1[ok])
    dens /= nt * dx
    r = int(np.ceil(4 * sigma / dx))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) * dx / sigma) ** 2)
    k /= k.sum()
    img = dens @ spec
    return np.stack([np.convolve(img[:, j], k, mode='same') for j in range(3)], -1)


# mercury lamp lines (nm) and rough relative strengths
HG_LINES = np.array([404.7, 435.8, 546.1, 577.0, 579.1])
HG_STRENGTH = np.array([0.6, 1.0, 1.0, 0.45, 0.5])
HG_XYZ = cmf(HG_LINES) * HG_STRENGTH[:, None]


def min_dev_incidence(lam):
    """Incidence angle (deg) giving minimum deviation for wavelength lam."""
    return np.degrees(np.arcsin(n_glass(lam) * np.sin(APEX / 2)))
