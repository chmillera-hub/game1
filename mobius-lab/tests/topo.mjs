// Numerical topology checks for cutting a band with n half-twists at given fractions.
const TAU = Math.PI * 2;
function bandPoint(theta, s, n, chi = 1, R = 1, W = 0.5) {
  const a = chi * n * theta / 2;
  const ux = Math.cos(a) * Math.cos(theta), uy = Math.cos(a) * Math.sin(theta), uz = Math.sin(a);
  const h = s * W / 2;
  return [R * Math.cos(theta) + h * ux, R * Math.sin(theta) + h * uy, h * uz];
}
// curve given by function of phi in [0, laps*2pi), sampled
function sampleCurve(fn, laps, N = 600) {
  const pts = [];
  for (let i = 0; i < N * laps; i++) pts.push(fn((i / (N * laps)) * laps * TAU));
  return pts;
}
// projection with a fixed generic rotation to avoid degeneracies
const ROT = (() => { const a = 0.3123, b = 0.1777; const ca = Math.cos(a), sa = Math.sin(a), cb = Math.cos(b), sb = Math.sin(b);
  return p => { let [x, y, z] = p; let y1 = y * ca - z * sa, z1 = y * sa + z * ca; let x2 = x * cb + z1 * sb, z2 = -x * sb + z1 * cb; return [x2, y1, z2]; }; })();
function segInter(p1, p2, q1, q2) { // 2D intersection params
  const rx = p2[0] - p1[0], ry = p2[1] - p1[1], sx = q2[0] - q1[0], sy = q2[1] - q1[1];
  const den = rx * sy - ry * sx; if (Math.abs(den) < 1e-14) return null;
  const qpx = q1[0] - p1[0], qpy = q1[1] - p1[1];
  const t = (qpx * sy - qpy * sx) / den, u = (qpx * ry - qpy * rx) / den;
  if (t < 0 || t >= 1 || u < 0 || u >= 1) return null;
  return { t, u, sign: Math.sign(den) };
}
function linking(A, B) {
  A = A.map(ROT); B = B.map(ROT); let sum = 0;
  for (let i = 0; i < A.length; i++) { const a1 = A[i], a2 = A[(i + 1) % A.length];
    for (let j = 0; j < B.length; j++) { const b1 = B[j], b2 = B[(j + 1) % B.length];
      const r = segInter(a1, a2, b1, b2); if (!r) continue;
      const za = a1[2] + r.t * (a2[2] - a1[2]), zb = b1[2] + r.u * (b2[2] - b1[2]);
      // sign convention: crossing sign = sign(den) if A over B else -sign(den)... use standard: eps = (dirOver x dirUnder).z sign
      const aOver = za > zb; const eps = aOver ? r.sign : -r.sign; sum += eps; } }
  return sum / 2;
}
function bareissDet(M) { // integer matrix det via BigInt Bareiss
  const n = M.length; if (n === 0) return 1n; const A = M.map(r => r.map(v => BigInt(v))); let prev = 1n, sign = 1n;
  for (let k = 0; k < n - 1; k++) { if (A[k][k] === 0n) { let sw = -1; for (let i = k + 1; i < n; i++) if (A[i][k] !== 0n) { sw = i; break; }
      if (sw < 0) return 0n; [A[k], A[sw]] = [A[sw], A[k]]; sign = -sign; }
    for (let i = k + 1; i < n; i++) for (let j = k + 1; j < n; j++) A[i][j] = (A[i][j] * A[k][k] - A[i][k] * A[k][j]) / prev;
    prev = A[k][k]; }
  return sign * A[n - 1][n - 1];
}
function knotDet(P) {
  P = P.map(ROT); const N = P.length; const events = []; let cid = 0;
  for (let i = 0; i < N; i++) for (let j = i + 2; j < N; j++) { if (i === 0 && j === N - 1) continue;
    const r = segInter(P[i], P[(i + 1) % N], P[j], P[(j + 1) % N]); if (!r) continue;
    const zi = P[i][2] + r.t * (P[(i + 1) % N][2] - P[i][2]), zj = P[j][2] + r.u * (P[(j + 1) % N][2] - P[j][2]);
    events.push({ pos: i + r.t, id: cid, over: zi > zj }); events.push({ pos: j + r.u, id: cid, over: zj > zi }); cid++; }
  const c = cid; if (c === 0) return 1;
  events.sort((a, b) => a.pos - b.pos);
  // arcs split at under events
  const unders = events.filter(e => !e.over); // c of them, in order
  const arcOfPos = pos => { // arc k spans from under k to under k+1
    let k = -1; for (let m = 0; m < unders.length; m++) if (unders[m].pos <= pos) k = m; return (k + unders.length) % unders.length; };
  const M = Array.from({ length: c }, () => new Array(c).fill(0));
  unders.forEach((u, k) => { const overEv = events.find(e => e.id === u.id && e.over); const o = arcOfPos(overEv.pos);
    const inArc = (k - 1 + c) % c, outArc = k; const row = u.id; M[row][o] += 2; M[row][inArc] -= 1; M[row][outArc] -= 1; });
  const minor = M.slice(1).map(r => r.slice(1));
  const d = bareissDet(minor); return Number(d < 0n ? -d : d);
}
function analyze(n, fracs, chi = 1) {
  const cutsS = fracs.map(f => -1 + 2 * f);
  let eff = n % 2 ? [...cutsS, ...cutsS.map(s => -s)] : [...cutsS];
  eff = [...new Set(eff.map(v => +v.toFixed(9)))].sort((a, b) => a - b);
  const bounds = [-1, ...eff, 1]; const ints = []; for (let i = 0; i < bounds.length - 1; i++) ints.push([bounds[i], bounds[i + 1]]);
  const pieces = []; const used = new Set();
  ints.forEach((iv, idx) => { if (used.has(idx)) return; used.add(idx);
    if (n % 2 === 0) { const [a, b] = iv; const m = (a + b) / 2;
      pieces.push({ kind: 'two-sided', laps: 1, core: sampleCurve(t => bandPoint(t, m, n, chi), 1), e1: sampleCurve(t => bandPoint(t, a, n, chi), 1), e2: sampleCurve(t => bandPoint(t, b, n, chi), 1), iv }); return; }
    const [a, b] = iv; const mirrorIdx = ints.findIndex(j => Math.abs(j[0] + b) < 1e-9 && Math.abs(j[1] + a) < 1e-9);
    if (mirrorIdx === idx) { // self-paired: one-sided
      pieces.push({ kind: 'one-sided', laps: 1, core: sampleCurve(t => bandPoint(t, 0, n, chi), 1), boundary: sampleCurve(t => bandPoint(t, b, n, chi), 2), iv }); }
    else { used.add(mirrorIdx); const hi = a > 0 ? iv : ints[mirrorIdx]; const [A, B] = hi; const m = (A + B) / 2;
      const f = s => t => bandPoint(t, s, n, chi); // formula is 4pi-periodic for odd n
      pieces.push({ kind: 'two-sided', laps: 2, core: sampleCurve(f(m), 2), e1: sampleCurve(f(A), 2), e2: sampleCurve(f(B), 2), iv: hi }); }
  });
  const out = pieces.map(p => ({ kind: p.kind, laps: p.laps, interval: p.iv.map(v => +((v + 1) / 2).toFixed(3)),
    knotDet: knotDet(p.core), edgeLk: p.kind === 'two-sided' ? linking(p.e1, p.e2) : null, coreBoundaryLk: p.kind === 'one-sided' ? linking(p.core, p.boundary) : null }));
  const links = []; for (let i = 0; i < pieces.length; i++) for (let j = i + 1; j < pieces.length; j++) links.push(`${i}-${j}:${linking(pieces[i].core, pieces[j].core)}`);
  return { n, fracs, chi, pieces: out, links };
}
const cases = [[0, [0.5]], [1, [0.5]], [1, [1 / 3]], [1, [0.25]], [1, [1 / 3, 2 / 3]], [1, [1 / 3, 0.5]], [2, [0.5]], [2, [1 / 3]], [2, [1 / 3, 2 / 3]], [3, [0.5]], [3, [1 / 3]], [4, [0.5]], [5, [0.5]], [0, [1 / 3, 2 / 3]], [1, [0.2, 0.4]]];
for (const [n, f] of cases) { const r = analyze(n, f); console.log(`n=${n} cuts=${f.map(x => x.toFixed(3))} -> ${r.pieces.length} piece(s)`);
  r.pieces.forEach((p, i) => console.log(`   [${i}] ${p.kind} laps=${p.laps} width=${p.interval} knotDet=${p.knotDet} edgeLk=${p.edgeLk} coreBdLk=${p.coreBoundaryLk}`));
  console.log('   links', r.links.join(' ')); }
console.log('chirality check n=1 cut 1/3 chi=-1:', JSON.stringify(analyze(1, [1 / 3], -1).links), JSON.stringify(analyze(1, [1 / 3], -1).pieces.map(p => [p.edgeLk, p.coreBoundaryLk])));
console.log('chirality check n=3 cut 1/2 chi=-1:', JSON.stringify(analyze(3, [0.5], -1).pieces.map(p => [p.knotDet, p.edgeLk])));
