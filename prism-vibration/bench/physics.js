// PHYSICS-BEGIN
// 3D optics for an equilateral SF11 prism whose refracting edge is vertical (z).
// Lab frame: beam travels +x, y is left/right across the beam, z is up. Units: mm, radians.
const DEG = Math.PI / 180;
const SELL_B = [1.73759695, 0.313747346, 1.89878101];
const SELL_C = [0.013188707, 0.0623068142, 155.23629];
function nGlass(lam) {
  const l2 = (lam / 1000) ** 2;
  let s = 0;
  for (let i = 0; i < 3; i++) s += SELL_B[i] * l2 / (l2 - SELL_C[i]);
  return Math.sqrt(1 + s);
}
function lobe(l, mu, s1, s2) { const s = l < mu ? s1 : s2; return Math.exp(-0.5 * ((l - mu) / s) ** 2); }
function cmf(l) {
  return [
    1.056 * lobe(l, 599.8, 37.9, 31.0) + 0.362 * lobe(l, 442.0, 16.0, 26.7) - 0.065 * lobe(l, 501.1, 20.4, 26.2),
    0.821 * lobe(l, 568.8, 46.9, 40.5) + 0.286 * lobe(l, 530.9, 16.3, 31.1),
    1.217 * lobe(l, 437.0, 11.8, 36.0) + 0.681 * lobe(l, 459.0, 26.0, 13.8)];
}
function planck(lamNm, T = 6500) {
  const l = lamNm * 1e-9, h = 6.626e-34, c = 2.998e8, k = 1.381e-23;
  return 1 / (l ** 5 * (Math.exp(h * c / (l * k * T)) - 1));
}
const XYZ2RGB = [[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]];
const WHITE_BAL = (() => {
  const xyz = [0, 0, 0];
  for (let l = 390; l <= 700; l += 1) { const c = cmf(l), p = planck(l); for (let j = 0; j < 3; j++) xyz[j] += c[j] * p; }
  const rgb = XYZ2RGB.map(r => r[0] * xyz[0] + r[1] * xyz[1] + r[2] * xyz[2]);
  const m = Math.max(...rgb);
  return rgb.map(v => v / m);
})();

// light sources: arrays of wavelengths and their XYZ weights (sum of Y = 1)
function makeSource(kind) {
  let lams, w;
  if (kind === 'mercury') {
    lams = [404.7, 435.8, 546.1, 577.0, 579.1];
    w = [0.6, 1.0, 1.0, 0.45, 0.5];
  } else {
    lams = []; w = [];
    const N = 124;
    for (let i = 0; i < N; i++) { const l = 390 + 310 * i / (N - 1); lams.push(l); w.push(planck(l)); }
  }
  const xyz = lams.map((l, i) => cmf(l).map(v => v * w[i]));
  const ysum = xyz.reduce((s, c) => s + c[1], 0);
  return { kind, lams, n: lams.map(nGlass), xyz: xyz.map(c => c.map(v => v / ysum)), continuous: kind !== 'mercury' };
}

// prism cross-section (apex up, centroid at origin) and its three vertical faces
const SIDE = 40, PH = SIDE * Math.sqrt(3) / 2;
const PV = [[0, 2 * PH / 3], [-SIDE / 2, -PH / 3], [SIDE / 2, -PH / 3]];
const FACES = [[0, 1], [1, 2], [2, 0]].map(([a, b]) => {
  const A = PV[a], B = PV[b], e = [B[0] - A[0], B[1] - A[1]], len = Math.hypot(...e);
  let nx = e[1] / len, ny = -e[0] / len;
  const mx = (A[0] + B[0]) / 2, my = (A[1] + B[1]) / 2;
  if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }
  return { a: A, e, n: [nx, ny, 0] };
});
const BEAM_Y = 9.0;           // beam height across the entry face (mm)
const SOURCE_X = -200;        // the light source sits 20 cm before the prism

function poseMatrix(rot, nod) {
  // lab = Ry(nod) * Rz(rot) * prism
  const cr = Math.cos(rot), sr = Math.sin(rot), cn = Math.cos(nod), sn = Math.sin(nod);
  const Rz = [[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]];
  const Ry = [[cn, 0, sn], [0, 1, 0], [-sn, 0, cn]];
  const M = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) for (let k = 0; k < 3; k++) M[i][j] += Ry[i][k] * Rz[k][j];
  return M;
}
const mul = (M, v) => [M[0][0] * v[0] + M[0][1] * v[1] + M[0][2] * v[2], M[1][0] * v[0] + M[1][1] * v[1] + M[1][2] * v[2], M[2][0] * v[0] + M[2][1] * v[1] + M[2][2] * v[2]];
const mulT = (M, v) => [M[0][0] * v[0] + M[1][0] * v[1] + M[2][0] * v[2], M[0][1] * v[0] + M[1][1] * v[1] + M[2][1] * v[2], M[0][2] * v[0] + M[1][2] * v[1] + M[2][2] * v[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

function refract(d, nrm, eta) {
  // nrm faces the incoming side; returns null on total internal reflection
  const cosi = -dot(d, nrm), k = 1 - eta * eta * (1 - cosi * cosi);
  if (k < 0) return null;
  const f = eta * cosi - Math.sqrt(k);
  return [eta * d[0] + f * nrm[0], eta * d[1] + f * nrm[1], eta * d[2] + f * nrm[2]];
}
function hitFace(p, d, F) {
  // ray against the infinite vertical face; returns [t, point] or null
  const den = d[0] * F.n[0] + d[1] * F.n[1];
  if (Math.abs(den) < 1e-12) return null;
  const t = ((F.a[0] - p[0]) * F.n[0] + (F.a[1] - p[1]) * F.n[1]) / den;
  if (t <= 1e-9) return null;
  const q = [p[0] + t * d[0], p[1] + t * d[1], p[2] + t * d[2]];
  const s = ((q[0] - F.a[0]) * F.e[0] + (q[1] - F.a[1]) * F.e[1]) / (F.e[0] ** 2 + F.e[1] ** 2);
  if (s < 0 || s > 1) return null;
  return [t, q];
}

// Trace one ray (lab frame) through a prism with pose {M, T}. Returns {p1,p2,d2} in lab or null.
function traceRay(p0, d0, n, pose) {
  const p = mulT(pose.M, [p0[0] - pose.T[0], p0[1] - pose.T[1], p0[2] - pose.T[2]]);
  const d = mulT(pose.M, d0);
  const F0 = FACES[0];
  if (dot(d, F0.n) >= 0) return null;
  const h1 = hitFace(p, d, F0);
  if (!h1) return null;
  // make sure no other face is hit first
  for (const k of [1, 2]) { const h = hitFace(p, d, FACES[k]); if (h && h[0] < h1[0]) return null; }
  const d1 = refract(d, F0.n, 1 / n);
  if (!d1) return null;
  const hA = hitFace(h1[1], d1, FACES[1]), hB = hitFace(h1[1], d1, FACES[2]);
  if (!hB || (hA && hA[0] < hB[0])) return null;      // must leave through the far face
  const F2 = FACES[2];
  const d2 = refract(d1, [-F2.n[0], -F2.n[1], 0], n);
  if (!d2) return null;
  const toLab = q => { const r = mul(pose.M, q); return [r[0] + pose.T[0], r[1] + pose.T[1], r[2] + pose.T[2]]; };
  return { p1: toLab(h1[1]), p2: toLab(hB[1]), d2: mul(pose.M, d2) };
}

function rotForIncidence(thetaDeg) { return (30 - thetaDeg) * DEG; }
function minDevIncidence(lam) { return Math.asin(nGlass(lam) * Math.sin(30 * DEG)) / DEG; }

// The bench: base prism angle, wall distance. Wall is perpendicular to the still 550 nm ray.
function makeBench(thetaDeg, L) {
  const base = rotForIncidence(thetaDeg);
  const pose = { M: poseMatrix(base, 0), T: [0, 0, 0] };
  const r = traceRay([SOURCE_X, BEAM_Y, 0], [1, 0, 0], nGlass(550), pose);
  const A = r.d2, len = Math.hypot(...A);
  const axis = [A[0] / len, A[1] / len, A[2] / len];
  return { theta: thetaDeg, base, L, axis, origin: axis.map(v => v * L), uh: [-axis[1], axis[0], 0], entry: r.p1 };
}
// Motion state -> lab beam + prism pose.
// m = {target:'prism'|'light', slideH, slideV (mm), turnH, turnV (rad)}
function configure(bench, m) {
  let p0 = [SOURCE_X, BEAM_Y, 0], d0 = [1, 0, 0], pose;
  if (m.target === 'light') {
    p0 = [SOURCE_X, BEAM_Y + m.slideH, m.slideV];
    d0 = [Math.cos(m.turnV) * Math.cos(m.turnH), Math.cos(m.turnV) * Math.sin(m.turnH), Math.sin(m.turnV)];
    pose = { M: poseMatrix(bench.base, 0), T: [0, 0, 0] };
  } else {
    pose = { M: poseMatrix(bench.base + m.turnH, m.turnV), T: [0, m.slideH, m.slideV] };
  }
  return { p0, d0, pose };
}
function wallHit(bench, r) {
  const A = bench.axis, O = bench.origin;
  const den = dot(r.d2, A);
  if (den <= 1e-9) return null;
  const t = dot([O[0] - r.p2[0], O[1] - r.p2[1], O[2] - r.p2[2]], A) / den;
  const q = [r.p2[0] + t * r.d2[0] - O[0], r.p2[1] + t * r.d2[1] - O[1], r.p2[2] + t * r.d2[2] - O[2]];
  return [dot(q, bench.uh), q[2]];
}
// positions on the wall for all wavelengths of a source; out[2i], out[2i+1] (NaN when blocked)
function spectrumOnWall(bench, cfg, src, out) {
  for (let i = 0; i < src.n.length; i++) {
    const r = traceRay(cfg.p0, cfg.d0, src.n[i], cfg.pose);
    const h = r && wallHit(bench, r);
    out[2 * i] = h ? h[0] : NaN; out[2 * i + 1] = h ? h[1] : NaN;
  }
  return out;
}
function wave(kind, ph) {
  if (kind === 'square') return Math.sin(ph) >= 0 ? 1 : -1;
  if (kind === 'triangle') return 2 / Math.PI * Math.asin(Math.sin(ph));
  return Math.sin(ph);
}
// PHYSICS-END
if (typeof module !== 'undefined') module.exports = { nGlass, makeSource, makeBench, configure, spectrumOnWall, traceRay, wallHit, minDevIncidence, DEG, cmf, WHITE_BAL };
