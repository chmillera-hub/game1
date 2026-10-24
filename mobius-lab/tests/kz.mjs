// TDGL quench on a periodic grid: dψ/dt = ∇²ψ + (μ(t) − |ψ|²)ψ + noise. Count phase windings (vortices).
function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function run(N, tauQ, seed, T = 2e-4, dt = 0.1) {
  const r = rng(seed), gs = () => { let u = 0, v = 0; while (!u) u = r(); v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  let re = new Float64Array(N * N), im = new Float64Array(N * N), re2 = new Float64Array(N * N), im2 = new Float64Array(N * N);
  for (let i = 0; i < N * N; i++) { re[i] = 0.01 * gs(); im[i] = 0.01 * gs(); }
  let t = 0; const amp = Math.sqrt(2 * T * dt);
  const count = () => { let n = 0; const ph = new Float64Array(N * N); for (let i = 0; i < N * N; i++) ph[i] = Math.atan2(im[i], re[i]);
    const w = d => { while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return d; };
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const a = ph[y * N + x], b = ph[y * N + (x + 1) % N], c = ph[((y + 1) % N) * N + (x + 1) % N], d = ph[((y + 1) % N) * N + x];
      const s = w(b - a) + w(c - b) + w(d - c) + w(a - d); if (Math.abs(s) > Math.PI) n++; } return n; };
  const tEnd = tauQ * 1.0 + 30;
  let atRamp = null;
  while (t < tEnd) {
    const mu = Math.min(1, -1 + 2 * t / tauQ);
    for (let y = 0; y < N; y++) { const ym = ((y - 1 + N) % N) * N, yp = ((y + 1) % N) * N, y0 = y * N;
      for (let x = 0; x < N; x++) { const i = y0 + x, xm = y0 + (x - 1 + N) % N, xp = y0 + (x + 1) % N;
        const lr = re[xm] + re[xp] + re[ym + x] + re[yp + x] - 4 * re[i], li = im[xm] + im[xp] + im[ym + x] + im[yp + x] - 4 * im[i];
        const g = mu - (re[i] * re[i] + im[i] * im[i]);
        re2[i] = re[i] + dt * (lr + g * re[i]) + amp * gs(); im2[i] = im[i] + dt * (li + g * im[i]) + amp * gs(); } }
    [re, re2] = [re2, re]; [im, im2] = [im2, im]; t += dt;
    if (atRamp == null && t >= tauQ) atRamp = count();
  }
  return { atRamp, after: count() };
}
const N = +process.argv[2] || 96;
for (const tauQ of [8, 25, 80, 250]) {
  const rs = [1, 2, 3].map(s => run(N, tauQ, s));
  const a = rs.map(r => r.atRamp), b = rs.map(r => r.after);
  console.log(`tauQ=${String(tauQ).padStart(4)}  defects at end of cooling: ${a.join(',')} (mean ${(a.reduce((x, y) => x + y) / 3).toFixed(0)})   30 time units later: ${b.join(',')}`);
}
