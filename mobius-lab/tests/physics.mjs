// 1) Bell / CHSH for three ribbon models (spin-1/2 singlet convention, angles in radians)
function rnd() { return Math.random(); }
const models = {
  pretwisted: (a, b) => { const l = rnd() * 2 * Math.PI; const A = Math.cos(l - a) >= 0 ? 1 : -1; const B = Math.cos(l - b) >= 0 ? -1 : 1; return [A, B]; },
  snap: (a, b) => { const A = rnd() < .5 ? 1 : -1; const pAgree = Math.cos((a - b) / 2) ** 2; // Bob's end points opposite to A; agrees with "opposite" w.p. cos^2(half angle)
    const B = rnd() < pAgree ? -A : A; return [A, B]; },
};
function E(m, a, b, N = 400000) { let s = 0; for (let i = 0; i < N; i++) { const [A, B] = m(a, b); s += A * B; } return s / N; }
const d = Math.PI / 180, a0 = 0, a1 = 90 * d, b0 = 45 * d, b1 = 135 * d;
for (const [name, m] of Object.entries(models)) {
  const S = E(m, a0, b0) - E(m, a0, b1) + E(m, a1, b0) + E(m, a1, b1);
  console.log(name, 'S =', S.toFixed(3), ' E(0,45)=', E(m, 0, 45 * d).toFixed(3), ' E(0,0)=', E(m, 0, 0).toFixed(3));
}
console.log('QM: S =', (-Math.cos(a0 - b0) + Math.cos(a0 - b1) - Math.cos(a1 - b0) - Math.cos(a1 - b1)).toFixed(3), ' E(0,45)=', (-Math.cos(45 * d)).toFixed(3));
// no-signaling: Bob's marginal for model snap under Alice a0 vs a1
for (const a of [a0, a1]) { let p = 0, N = 300000; for (let i = 0; i < N; i++) { const [, B] = models.snap(a, b0); if (B > 0) p++; } console.log('snap: P(B=+|alice angle', (a / d).toFixed(0), ') =', (p / N).toFixed(4)); }
// 2) Helix billiard: transverse kick ~ -cos(theta) with uniform theta -> arcsine
{ const N = 400000, bins = new Array(10).fill(0); let left = 0, straight5 = 0;
  for (let i = 0; i < N; i++) { const th = rnd() * 2 * Math.PI; const y = -Math.cos(th); if (y < 0) left++; bins[Math.min(9, Math.floor((y + 1) / 0.2))]++; if (Math.abs(y) < 0.05) straight5++; }
  console.log('helix: P(left)=', (left / N).toFixed(4), ' P(|kick|<5% of max)=', (straight5 / N).toFixed(4), ' (theory 2/pi*asin(0.05)=', (2 / Math.PI * Math.asin(.05)).toFixed(4), ')');
  console.log('helix hist (y from -1 to 1 in 0.2 bins):', bins.map(b => (b / N).toFixed(3)).join(' ')); }
// 3) Antitwister quaternion family: unit norm, endpoints, periodicity
function Q(s, t) { const be = s * Math.PI / 2, sb = Math.sin(be), cb = Math.cos(be), c = Math.cos(t / 2), sn = Math.sin(t / 2);
  return [sb * sb + cb * cb * c, 0, sb * cb * (1 - c), cb * sn]; } // [w, x(i), y(j), z(k)]
let maxErr = 0; for (let s = 0; s <= 1; s += 0.05) for (let t = 0; t < 4 * Math.PI; t += 0.1) { const q = Q(s, t); maxErr = Math.max(maxErr, Math.abs(Math.hypot(...q) - 1)); }
console.log('antitwister: max |q|-1 =', maxErr.toExponential(2), ' Q(1,t)=', Q(1, 2.3).map(v => v.toFixed(3)).join(','), ' Q(0,2pi)=', Q(0, 2 * Math.PI).map(v => v.toFixed(3)).join(','), ' Q(s,0)=', Q(.4, 0).map(v => v.toFixed(3)).join(','));
