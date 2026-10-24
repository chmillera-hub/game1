/* Universe — the Topological Coherence Model run as a set of rules, in a periodic box (the universe wraps
   around like a torus, as in real cosmology codes).
   Flat field (false vacuum) → seed twist → a crystallization front sweeps the box while space inflates →
   reheating → knot forge with a probability barrier → gravity (particle-mesh, mean density subtracted) →
   stars → supernova forges → black holes with ringing surfaces that pay a "Hawking tax". */
(function () {
  'use strict';
  const ML = window.ML, C = ML.C, TAU = ML.TAU;

  // ------------------------------------------------------------------ tunable laws
  const P = {
    timeScale: 1, paused: false,
    G: 22, c: 220,
    mX: 10,            // knot mass per crossing (trefoil = 30)
    mLoop: 3,          // ghost-loop mass (dark matter)
    barrier: 2.4,      // knot-tying barrier E_b (in units of temperature)
    mist: 1.0,         // matter catalysis multiplier
    leftBias: 0.25,    // extra share of left-handed loops
    endless: true,     // flat field refills after inflation
    darkPush: 0.03,    // late expansion rate once loops have piled up (dark energy)
    hInf: 2.2,         // expansion rate while the false vacuum drives inflation
    show: { loops: true, river: true, haze: true, light: true },
  };
  const L = 1200;                 // side of the periodic universe (units of space)
  const MAXK = 1400, MAXL = 3800, MAXP = 700, NTR = 320;
  const F_UNITS = 4900;           // loops the false vacuum can make (≈ enough to fill the box)
  const F_END = 0.3;
  const R_SAT = 20, R_TIE = 24, R_COLL = 5, R_ABS = 5;
  const wrapP = (x) => x - L * Math.floor(x / L);
  const wrapD = (d) => d - L * Math.round(d / L);

  // ------------------------------------------------------------------ particle state
  const kx = new Float64Array(MAXK), ky = new Float64Array(MAXK), kvx = new Float64Array(MAXK), kvy = new Float64Array(MAXK);
  const kn = new Uint8Array(MAXK), kc = new Int8Array(MAXK), kph = new Float32Array(MAXK), kex = new Float32Array(MAXK), kdead = new Uint8Array(MAXK);
  const lx = new Float64Array(MAXL), ly = new Float64Array(MAXL), lvx = new Float64Array(MAXL), lvy = new Float64Array(MAXL);
  const lw = new Float32Array(MAXL), lc = new Int8Array(MAXL), lph = new Float32Array(MAXL), ldead = new Uint8Array(MAXL);
  const px = new Float64Array(MAXP), py = new Float64Array(MAXP), pkx = new Float64Array(MAXP), pky = new Float64Array(MAXP), page = new Float32Array(MAXP);
  const tx = new Float64Array(NTR), ty = new Float64Array(NTR), tpx = new Float64Array(NTR), tpy = new Float64Array(NTR), tl = new Float32Array(NTR);

  const S = {
    t: 0, nk: 0, nl: 0, np: 0, F: 1, T: 0, H: 0, lnA: 0, seeded: false, seedTimer: 1.0, inflating: false, reheated: false, tEnd: 0,
    att: 0, acc: 0, accEma: 1, attAcc: 0,
    bhs: [], stars: [], rings: [], sparks: [],
    stats: { loops: 0, knots: 0, ann: 0, sn: 0, hawk: 0, bhEaten: 0 },
    hist: { mass: [], loops: [], F: [] }, histT: 0, starT: 0, hazeT: 0,
    cam: { x: L / 2, y: L / 2, s: 0.5 },
    tool: 'seed',
  };

  // ------------------------------------------------------------------ periodic cell lists
  class Cells {
    constructor(cap, cell) { this.next = new Int32Array(cap); this.nc = Math.max(3, Math.floor(L / cell)); this.cs = L / this.nc; this.head = new Int32Array(this.nc * this.nc); }
    cellOf(x, y) { const nc = this.nc; let ix = Math.floor(x / this.cs) % nc, iy = Math.floor(y / this.cs) % nc; if (ix < 0) ix += nc; if (iy < 0) iy += nc; return iy * nc + ix; }
    build(xs, ys, n) { this.head.fill(-1); for (let i = 0; i < n; i++) this.insert(i, xs[i], ys[i]); }
    insert(i, x, y) { const c = this.cellOf(x, y); this.next[i] = this.head[c]; this.head[c] = i; }
  }
  const kcells = new Cells(MAXK, R_TIE), lcells = new Cells(MAXL, R_TIE);
  // cb(j, d2, dx, dy) with minimum-image offsets; return false to stop
  function query(cells, xs, ys, x, y, r, cb) {
    const cs = cells.cs, nc = cells.nc, r2 = r * r;
    const span = Math.min(Math.ceil(r / cs), (nc - 1) >> 1);
    const ix0 = Math.floor(x / cs), iy0 = Math.floor(y / cs);
    for (let oy = -span; oy <= span; oy++) {
      let iy = (iy0 + oy) % nc; if (iy < 0) iy += nc;
      for (let ox = -span; ox <= span; ox++) {
        let ix = (ix0 + ox) % nc; if (ix < 0) ix += nc;
        for (let j = cells.head[iy * nc + ix]; j >= 0; j = cells.next[j]) {
          const dx = wrapD(xs[j] - x), dy = wrapD(ys[j] - y), d2 = dx * dx + dy * dy;
          if (d2 <= r2 && cb(j, d2, dx, dy) === false) return;
        }
      }
    }
  }

  // ------------------------------------------------------------------ particle-mesh gravity (FFT, periodic)
  const NG = 128, NG2 = NG * NG, HG = L / NG, EPS = 1.5 * HG;
  const rho = new Float64Array(NG2), lcount = new Float64Array(NG2), re = new Float64Array(NG2), im = new Float64Array(NG2);
  const phi = new Float64Array(NG2), gxg = new Float64Array(NG2), gyg = new Float64Array(NG2), green = new Float64Array(NG2);
  let phiMax = 0, phiMin = 0;
  const fftRev = new Uint32Array(NG), fftCos = new Float64Array(NG / 2), fftSin = new Float64Array(NG / 2);
  (function initFFT() {
    const lv = Math.log2(NG);
    for (let i = 0; i < NG; i++) { let r = 0; for (let b = 0; b < lv; b++) r |= ((i >> b) & 1) << (lv - 1 - b); fftRev[i] = r; }
    for (let i = 0; i < NG / 2; i++) { fftCos[i] = Math.cos((TAU * i) / NG); fftSin[i] = Math.sin((TAU * i) / NG); }
    // 3D gravity confined to the plane: the 2D Fourier transform of 1/r is 2π/k; soften with e^(−kε)
    for (let iy = 0; iy < NG; iy++) for (let ix = 0; ix < NG; ix++) {
      const kxx = (TAU * (ix < NG / 2 ? ix : ix - NG)) / L, kyy = (TAU * (iy < NG / 2 ? iy : iy - NG)) / L, k = Math.hypot(kxx, kyy);
      green[iy * NG + ix] = k > 0 ? (-TAU * Math.exp(-k * EPS)) / k : 0;
    }
  })();
  function fft1(off, stride, inv) {
    const n = NG;
    for (let i = 0; i < n; i++) {
      const j = fftRev[i];
      if (j > i) { const a = off + i * stride, b = off + j * stride; let t = re[a]; re[a] = re[b]; re[b] = t; t = im[a]; im[a] = im[b]; im[b] = t; }
    }
    for (let size = 2; size <= n; size <<= 1) {
      const half = size >> 1, step = n / size;
      for (let i = 0; i < n; i += size) {
        for (let j = 0, k = 0; j < half; j++, k += step) {
          const a = off + (i + j) * stride, b = a + half * stride;
          const wr = fftCos[k], wi = inv ? fftSin[k] : -fftSin[k];
          const tr = re[b] * wr - im[b] * wi, ti = re[b] * wi + im[b] * wr;
          re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] += tr; im[a] += ti;
        }
      }
    }
  }
  function fft2(inv) {
    for (let r = 0; r < NG; r++) fft1(r * NG, 1, inv);
    for (let c = 0; c < NG; c++) fft1(c, NG, inv);
    if (inv) { const s = 1 / NG2; for (let i = 0; i < NG2; i++) { re[i] *= s; im[i] *= s; } }
  }
  function deposit(x, y, m, grid) {
    const fx = x / HG - 0.5, fy = y / HG - 0.5;
    let ix = Math.floor(fx), iy = Math.floor(fy);
    const ax = fx - ix, ay = fy - iy;
    const ix0 = ((ix % NG) + NG) % NG, iy0 = ((iy % NG) + NG) % NG, ix1 = (ix0 + 1) % NG, iy1 = (iy0 + 1) % NG;
    grid[iy0 * NG + ix0] += m * (1 - ax) * (1 - ay); grid[iy0 * NG + ix1] += m * ax * (1 - ay);
    grid[iy1 * NG + ix0] += m * (1 - ax) * ay; grid[iy1 * NG + ix1] += m * ax * ay;
  }
  const SG = [0, 0, 0];
  function sampleGrid(x, y) {
    x = wrapP(x); y = wrapP(y);
    const fx = x / HG - 0.5, fy = y / HG - 0.5;
    let ix = Math.floor(fx), iy = Math.floor(fy);
    const ax = fx - ix, ay = fy - iy;
    const ix0 = ((ix % NG) + NG) % NG, iy0 = ((iy % NG) + NG) % NG, ix1 = (ix0 + 1) % NG, iy1 = (iy0 + 1) % NG;
    const a = iy0 * NG + ix0, b = iy0 * NG + ix1, c = iy1 * NG + ix0, d = iy1 * NG + ix1;
    const w0 = (1 - ax) * (1 - ay), w1 = ax * (1 - ay), w2 = (1 - ax) * ay, w3 = ax * ay;
    SG[0] = gxg[a] * w0 + gxg[b] * w1 + gxg[c] * w2 + gxg[d] * w3;
    SG[1] = gyg[a] * w0 + gyg[b] * w1 + gyg[c] * w2 + gyg[d] * w3;
    SG[2] = phi[a] * w0 + phi[b] * w1 + phi[c] * w2 + phi[d] * w3;
    return SG;
  }
  function solvePM() {
    rho.fill(0); lcount.fill(0);
    const inv = 1 / (HG * HG);
    for (let i = 0; i < S.nk; i++) deposit(kx[i], ky[i], knotMass(kn[i]) * inv, rho);
    for (let i = 0; i < S.nl; i++) { deposit(lx[i], ly[i], lw[i] * P.mLoop * inv, rho); deposit(lx[i], ly[i], lw[i], lcount); }
    re.set(rho); im.fill(0);
    fft2(false);
    for (let i = 0; i < NG2; i++) { const g = green[i] * P.G; re[i] *= g; im[i] *= g; }
    fft2(true);
    phiMax = -Infinity; phiMin = Infinity;
    for (let i = 0; i < NG2; i++) { phi[i] = re[i]; if (re[i] > phiMax) phiMax = re[i]; if (re[i] < phiMin) phiMin = re[i]; }
    const k = 1 / (2 * HG);
    for (let iy = 0; iy < NG; iy++) {
      const up = ((iy + 1) % NG) * NG, dn = ((iy + NG - 1) % NG) * NG, row = iy * NG;
      for (let ix = 0; ix < NG; ix++) {
        const r = (ix + 1) % NG, l = (ix + NG - 1) % NG;
        gxg[row + ix] = -(phi[row + r] - phi[row + l]) * k;
        gyg[row + ix] = -(phi[up + ix] - phi[dn + ix]) * k;
      }
    }
  }

  // ------------------------------------------------------------------ helpers
  const fRes = (n) => 0.16 + 0.065 * n;                 // each knot type's resonant frequency (its absorption line)
  const knotMass = (n) => n * P.mX;
  const rs = (M) => (2 * P.G * M) / (P.c * P.c);        // horizon: where the inflow reaches c
  function chirality() { return Math.random() < 0.5 + P.leftBias / 2 ? -1 : 1; } // -1 = left-handed

  function addLoop(x, y, vx, vy, w, ch) {
    if (S.nl >= MAXL) {
      // full: merge a random loop into a nearby one to free a slot (mass stays where it was)
      const i = (Math.random() * S.nl) | 0;
      let best = -1, bd = 1e18;
      for (let k = 0; k < 24; k++) {
        const j = (Math.random() * S.nl) | 0; if (j === i) continue;
        const dx = wrapD(lx[j] - lx[i]), dy = wrapD(ly[j] - ly[i]), d2 = dx * dx + dy * dy;
        if (d2 < bd) { bd = d2; best = j; }
      }
      if (best < 0) return -1;
      const W = lw[i] + lw[best];
      lvx[best] = (lvx[best] * lw[best] + lvx[i] * lw[i]) / W; lvy[best] = (lvy[best] * lw[best] + lvy[i] * lw[i]) / W;
      lw[best] = W;
      removeLoop(i);
      S.cellsDirty = true;
    }
    const i = S.nl++;
    lx[i] = wrapP(x); ly[i] = wrapP(y); lvx[i] = vx; lvy[i] = vy; lw[i] = w || 1; lc[i] = ch || chirality(); lph[i] = Math.random() * TAU; ldead[i] = 0;
    return i;
  }
  function removeLoop(i) {
    const j = --S.nl;
    if (i !== j) { lx[i] = lx[j]; ly[i] = ly[j]; lvx[i] = lvx[j]; lvy[i] = lvy[j]; lw[i] = lw[j]; lc[i] = lc[j]; lph[i] = lph[j]; ldead[i] = ldead[j]; }
  }
  function addKnot(x, y, vx, vy, n, ch) {
    if (S.nk >= MAXK) return -1;
    const i = S.nk++;
    kx[i] = wrapP(x); ky[i] = wrapP(y); kvx[i] = vx; kvy[i] = vy; kn[i] = n; kc[i] = ch; kph[i] = Math.random() * TAU; kex[i] = 0; kdead[i] = 0;
    return i;
  }
  function removeKnot(i) {
    const j = --S.nk;
    if (i !== j) { kx[i] = kx[j]; ky[i] = ky[j]; kvx[i] = kvx[j]; kvy[i] = kvy[j]; kn[i] = kn[j]; kc[i] = kc[j]; kph[i] = kph[j]; kex[i] = kex[j]; kdead[i] = kdead[j]; }
  }
  function addPhoton(x, y, dx, dy, f) {
    const i = S.np >= MAXP ? (Math.random() * S.np) | 0 : S.np++;
    const l = Math.hypot(dx, dy) || 1;
    px[i] = wrapP(x); py[i] = wrapP(y); pkx[i] = (dx / l) * f; pky[i] = (dy / l) * f; page[i] = 0;
    return i;
  }
  function removePhoton(i) {
    const j = --S.np;
    if (i !== j) { px[i] = px[j]; py[i] = py[j]; pkx[i] = pkx[j]; pky[i] = pky[j]; page[i] = page[j]; }
  }
  function burstPhotons(x, y, n, f0, fs) {
    for (let k = 0; k < n; k++) { const a = Math.random() * TAU; addPhoton(x, y, Math.cos(a), Math.sin(a), Math.max(0.05, f0 + (Math.random() - 0.5) * fs)); }
  }

  // ------------------------------------------------------------------ black holes
  function makeBH(x, y, M, vx, vy) {
    const bh = { x: wrapP(x), y: wrapP(y), vx: vx || 0, vy: vy || 0, M, modes: new Float32Array(32), ph: new Float32Array(32), tax: 0, eat: 0, age: 0 };
    for (let m = 0; m < 32; m++) { bh.ph[m] = Math.random() * TAU; bh.modes[m] = 0.02 * Math.random(); }
    S.bhs.push(bh);
    S.rings.push({ x: bh.x, y: bh.y, r: 0, v: 160, life: 1.2, col: C.tape });
    return bh;
  }
  function ring(bh, mode, e) { bh.modes[mode] = Math.min(4, bh.modes[mode] + e); bh.eat = Math.min(1.5, bh.eat + 0.25); }
  // River of flat space around black holes: inflow speed = escape speed √(2GM/r), pointing inward.
  // For one hole this is Schwarzschild spacetime in Painlevé–Gullstrand form, so light rays below are exact.
  const RV = [0, 0];
  function riverBH(x, y) {
    let ph = 0, gx = 0, gy = 0;
    for (const b of S.bhs) {
      const dx = wrapD(b.x - x), dy = wrapD(b.y - y), r2 = dx * dx + dy * dy + 0.01, r = Math.sqrt(r2);
      ph -= (P.G * b.M) / r; const f = (P.G * b.M) / (r2 * r); gx += f * dx; gy += f * dy;
    }
    const g = Math.hypot(gx, gy);
    if (g < 1e-12) { RV[0] = 0; RV[1] = 0; return RV; }
    const v = Math.sqrt(2 * -ph);
    RV[0] = (v * gx) / g; RV[1] = (v * gy) / g; return RV;
  }
  const BA = [0, 0];
  // feels: 1 = matter (also feels the glow of a feeding hole), 0 = ghost loops / other holes (gravity only)
  function bhAccel(x, y, skip, feelsLight) {
    BA[0] = 0; BA[1] = 0;
    for (const b of S.bhs) {
      if (b === skip) continue;
      const dx = wrapD(b.x - x), dy = wrapD(b.y - y), r2 = dx * dx + dy * dy + 1;
      let f = (P.G * b.M) / (r2 * Math.sqrt(r2));
      // Eddington limit: a feeding hole glows, and its light pushes infalling knots back out
      if (feelsLight && b.eat > 0) { const R = rs(b.M); if (r2 < 36 * R * R + 400) f *= 1 - 1.25 * Math.min(1, b.eat); }
      BA[0] += f * dx; BA[1] += f * dy;
    }
    return BA;
  }

  // ------------------------------------------------------------------ reset / big bang
  function reset() {
    Object.assign(S, { t: 0, nk: 0, nl: 0, np: 0, F: 1, T: 0, H: 0, lnA: 0, seeded: false, seedTimer: 1.0, inflating: false, reheated: false, tEnd: 0, att: 0, acc: 0, accEma: 1, attAcc: 0 });
    S.bhs = []; S.stars = []; S.rings = []; S.sparks = [];
    S.stats = { loops: 0, knots: 0, ann: 0, sn: 0, hawk: 0, bhEaten: 0 };
    S.hist = { mass: [], loops: [], F: [] }; S.histT = 0;
    for (let i = 0; i < NTR; i++) tl[i] = 0;
    kcells.build(kx, ky, 0); lcells.build(lx, ly, 0);
    solvePM();
    fitView();
  }
  function seed(x, y) {
    if (S.reheated) return false;
    const i = addLoop(x, y, 0, 0, 1, chirality());
    lcells.insert(i, lx[i], ly[i]);
    S.seeded = true; S.inflating = true; S.stats.loops += 1;
    S.sparks.push({ x: lx[i], y: ly[i], life: 1.2, max: 1.2, col: C.tape, r: 30 });
    return true;
  }
  function fitView() { S.cam.x = L / 2; S.cam.y = L / 2; S.cam.s = Math.min(S.W || 800, S.H_ || 600) / L; }

  // ------------------------------------------------------------------ physics step
  function step(dt) {
    S.t += dt;
    if (!S.seeded) { S.seedTimer -= dt; if (S.seedTimer <= 0) seed(L / 2, L / 2); }
    S.cellsDirty = false;

    // 1) crystallization front: loops copy themselves into neighbouring flat field while it is fresh
    if (S.inflating) {
      S.attAcc += (250 + 2.2 * S.nl) * dt;
      let att = 0, acc = 0;
      while (S.attAcc >= 1 && S.nl > 0 && S.nl < MAXL) {
        S.attAcc -= 1; att++;
        const back = Math.min(S.nl, 500), p = S.nl - 1 - Math.floor(Math.random() * Math.random() * back);
        const a = Math.random() * TAU, d = 12 + Math.random() * 14;
        const x = wrapP(lx[p] + Math.cos(a) * d), y = wrapP(ly[p] + Math.sin(a) * d);
        let crowd = 0;
        query(lcells, lx, ly, x, y, R_SAT, () => { crowd++; if (crowd >= 3) return false; });
        if (crowd >= 3) continue;
        const i = addLoop(x, y, 0, 0, 1, chirality());
        lcells.insert(i, lx[i], ly[i]);
        acc++; S.stats.loops++;
        S.F = Math.max(F_END, S.F - 1 / F_UNITS);
      }
      if (att > 0) S.accEma = ML.lerp(S.accEma, acc / att, 0.08);
      if ((S.nl > 400 && S.accEma < 0.03) || S.F <= F_END + 1e-4 || S.nl >= MAXL - 1) { S.inflating = false; S.tEnd = S.t; }
    }
    // expansion rate: false-vacuum pressure while inflating; afterwards a decelerating coast plus a late
    // push that grows with the loops piled up (dark energy)
    const loopsFrac = Math.min(1, S.stats.loops / 9000);
    if (S.inflating) S.H = P.hInf;
    else if (S.seeded) S.H = 0.05 / (1 + 0.08 * (S.t - S.tEnd)) + P.darkPush * loopsFrac;
    else S.H = 0;
    S.lnA += S.H * dt;
    // temperature: supercooled while inflating; latent heat is released when it ends (reheating)
    if (S.seeded && !S.inflating && !S.reheated) { S.reheated = true; S.T = 1.35; S.sparks.push({ x: L / 2, y: L / 2, life: 0.8, max: 0.8, col: '#ffe9c2', r: L * 0.7 }); }
    else if (S.reheated) S.T *= 1 - Math.min(0.5, 0.2 * dt);

    // 2) gravity on the mesh (black holes added exactly)
    solvePM();
    const drag = Math.min(0.5, S.inflating ? 1 : S.H * dt), vcap = P.c * 0.85;
    // a hot soup jiggles: thermal kicks (Langevin) that fade as the forge cools
    const jig = S.T > 0.05 ? 34 * Math.sqrt(S.T) * Math.sqrt(2 * 1.5 * dt) : 0, jd = S.T > 0.05 ? 1.5 * dt : 0;
    for (let i = 0; i < S.nk; i++) {
      const g = sampleGrid(kx[i], ky[i]); let ax = g[0], ay = g[1];
      if (jig) { kvx[i] += jig * ML.gauss() - jd * kvx[i]; kvy[i] += jig * ML.gauss() - jd * kvy[i]; }
      if (S.bhs.length) { const b = bhAccel(kx[i], ky[i], null, true); ax += b[0]; ay += b[1]; }
      kvx[i] = (kvx[i] + ax * dt) * (1 - drag); kvy[i] = (kvy[i] + ay * dt) * (1 - drag);
      const sp = Math.hypot(kvx[i], kvy[i]); if (sp > vcap) { kvx[i] *= vcap / sp; kvy[i] *= vcap / sp; }
      kx[i] = wrapP(kx[i] + kvx[i] * dt); ky[i] = wrapP(ky[i] + kvy[i] * dt);
      kph[i] += dt * (1.2 + kn[i] * 0.15) * kc[i];
    }
    for (let i = 0; i < S.nl; i++) {
      const g = sampleGrid(lx[i], ly[i]); let ax = g[0], ay = g[1];
      if (S.bhs.length) { const b = bhAccel(lx[i], ly[i]); ax += b[0]; ay += b[1]; }
      lvx[i] = (lvx[i] + ax * dt) * (1 - drag); lvy[i] = (lvy[i] + ay * dt) * (1 - drag);
      const sp = Math.hypot(lvx[i], lvy[i]); if (sp > vcap) { lvx[i] *= vcap / sp; lvy[i] *= vcap / sp; }
      lx[i] = wrapP(lx[i] + lvx[i] * dt); ly[i] = wrapP(ly[i] + lvy[i] * dt);
      lph[i] += dt * 2.5 * lc[i];
    }
    for (const b of S.bhs) {
      const g = sampleGrid(b.x, b.y), o = bhAccel(b.x, b.y, b);
      b.vx = (b.vx + (g[0] + o[0]) * dt) * (1 - drag); b.vy = (b.vy + (g[1] + o[1]) * dt) * (1 - drag);
      b.x = wrapP(b.x + b.vx * dt); b.y = wrapP(b.y + b.vy * dt);
    }
    kcells.build(kx, ky, S.nk); lcells.build(lx, ly, S.nl);

    // 3) the forge: in the hot soup three loops can tie into a trefoil, at a rate ∝ e^(−barrier/T)
    const boltz = Math.exp(-P.barrier / Math.max(S.T, 1e-3));
    if (S.reheated && S.T > 0.08 && S.nl > 3 && boltz > 1e-7) {
      const picks = Math.min(S.nl, 500), scale = S.nl / picks;
      const nb = [-1, -1], nd = [0, 0], off = [0, 0, 0, 0];
      for (let q = 0; q < picks; q++) {
        const i = (Math.random() * S.nl) | 0;
        if (ldead[i] || Math.random() > 2.6 * boltz * dt * scale) continue;
        nb[0] = nb[1] = -1; nd[0] = nd[1] = 1e9;
        query(lcells, lx, ly, lx[i], ly[i], R_TIE, (j, d2, dx, dy) => {
          if (j === i || ldead[j]) return;
          if (d2 < nd[0]) { nd[1] = nd[0]; nb[1] = nb[0]; off[2] = off[0]; off[3] = off[1]; nd[0] = d2; nb[0] = j; off[0] = dx; off[1] = dy; }
          else if (d2 < nd[1]) { nd[1] = d2; nb[1] = j; off[2] = dx; off[3] = dy; }
        });
        if (nb[1] < 0) continue;
        const a = i, b = nb[0], c = nb[1];
        const ch = Math.sign(lc[a] + lc[b] + lc[c]) || -1;
        addKnot(lx[a] + (off[0] + off[2]) / 3, ly[a] + (off[1] + off[3]) / 3, (lvx[a] + lvx[b] + lvx[c]) / 3, (lvy[a] + lvy[b] + lvy[c]) / 3, 3, ch);
        S.stats.knots++;
        for (const j of [a, b, c]) { lw[j] -= 1; if (lw[j] <= 0.5) ldead[j] = 1; }
      }
      // heavier knots: a knot that catches two more loops braids into one with two more crossings
      const kp = Math.min(S.nk, 200), ks = S.nk / Math.max(1, kp);
      for (let q = 0; q < kp; q++) {
        const i = (Math.random() * S.nk) | 0;
        if (kn[i] >= 13) continue;
        if (Math.random() > 2 * Math.exp((-P.barrier * (kn[i] + 2)) / 3 / Math.max(S.T, 1e-3)) * dt * ks) continue;
        const use = [];
        query(lcells, lx, ly, kx[i], ky[i], R_TIE, (j) => { if (!ldead[j]) use.push(j); if (use.length >= 2) return false; });
        if (use.length < 2) continue;
        kn[i] += 2;
        for (const j of use) { lw[j] -= 1; if (lw[j] <= 0.5) ldead[j] = 1; }
      }
      for (let i = S.nl - 1; i >= 0; i--) if (ldead[i]) removeLoop(i);
      kcells.build(kx, ky, S.nk); lcells.build(lx, ly, S.nl);
    }

    // 4) knot encounters: contact pressure; mirror knots annihilate into light; hard hits snap a loop open
    for (let i = 0; i < S.nk; i++) {
      if (kdead[i]) continue;
      query(kcells, kx, ky, kx[i], ky[i], R_COLL, (j, d2, dx, dy) => {
        if (j <= i || kdead[j] || kdead[i]) return;
        if (kn[i] === kn[j] && kc[i] !== kc[j] && Math.random() < 0.6) {
          kdead[i] = kdead[j] = 1; S.stats.ann++;
          const mx = kx[i] + dx / 2, my = ky[i] + dy / 2;
          burstPhotons(mx, my, 3, 0.95, 0.3);
          S.sparks.push({ x: wrapP(mx), y: wrapP(my), life: 0.5, max: 0.5, col: '#ffffff', r: 8 });
          return;
        }
        const d = Math.sqrt(d2) || 1e-3, nx = dx / d, ny = dy / d;
        const ov = (R_COLL - d) * 0.3;
        kx[i] = wrapP(kx[i] - nx * ov); ky[i] = wrapP(ky[i] - ny * ov); kx[j] = wrapP(kx[j] + nx * ov); ky[j] = wrapP(ky[j] + ny * ov);
        const vn = (kvx[j] - kvx[i]) * nx + (kvy[j] - kvy[i]) * ny;   // negative = closing
        if (vn < -16) {
          const jn = (-(1 + 0.55) * vn) / 2;
          kvx[i] -= jn * nx; kvy[i] -= jn * ny; kvx[j] += jn * nx; kvy[j] += jn * ny;
          const a = Math.random() * TAU;
          addPhoton(kx[i] + dx / 2, ky[i] + dy / 2, Math.cos(a), Math.sin(a), ML.clamp(0.12 + -vn / 140, 0.1, 1.2));
        }
      });
    }
    let dirty = false;
    for (let i = S.nk - 1; i >= 0; i--) if (kdead[i]) { removeKnot(i); dirty = true; }
    if (dirty) kcells.build(kx, ky, S.nk);

    // 5) the mist: matter keeps catalysing flat field into simple loops (but never into new knots)
    const fm = P.endless ? Math.max(S.F, 0.35) : S.F;
    if (S.reheated && fm > 0.001) {
      const base = 0.03 * P.mist * fm * dt;
      for (let i = 0; i < S.nk; i++) {
        if (Math.random() > base * (kn[i] / 3)) continue;
        const a = Math.random() * TAU, v = 10 + Math.random() * 18;
        addLoop(kx[i] + Math.cos(a) * 4, ky[i] + Math.sin(a) * 4, kvx[i] + Math.cos(a) * v, kvy[i] + Math.sin(a) * v, 1, chirality());
        S.stats.loops++;
        if (!P.endless) S.F = Math.max(0, S.F - 1 / F_UNITS);
      }
      if (S.cellsDirty) lcells.build(lx, ly, S.nl);
    }

    // 6) black holes: whatever crosses the horizon melts into the seamless surface and rings a mode
    for (let bi = S.bhs.length - 1; bi >= 0; bi--) {
      const b = S.bhs[bi], R = rs(b.M);
      b.age += dt;
      query(kcells, kx, ky, b.x, b.y, Math.max(R, 1.5), (j) => {
        if (kdead[j]) return;
        const m = knotMass(kn[j]);
        b.vx = (b.vx * b.M + kvx[j] * m) / (b.M + m); b.vy = (b.vy * b.M + kvy[j] * m) / (b.M + m);
        b.M += m; kdead[j] = 1; S.stats.bhEaten++;
        ring(b, (2 + kn[j] * 3 + (kc[j] > 0 ? 7 : 0)) % 32, 0.35); b.eat = Math.min(1.5, b.eat + 0.15);
      });
      query(lcells, lx, ly, b.x, b.y, Math.max(R, 1.5), (j) => {
        if (ldead[j]) return;
        b.M += lw[j] * P.mLoop; ldead[j] = 1; ring(b, 2 + ((lw[j] | 0) % 3), 0.05);
      });
      // Hawking tax: ripples (and, slowly, the mass itself) pay to crystallise nearby flat field into loops
      let E = 0; for (let m = 0; m < 32; m++) E += b.modes[m];
      b.tax += (0.9 * E + 3e6 / (b.M * b.M)) * dt;
      for (let m = 0; m < 32; m++) b.modes[m] *= 1 - 0.35 * dt;
      b.eat = Math.max(0, b.eat - dt);
      let emitted = 0;
      while (b.tax >= 1 && emitted < 40) {
        b.tax -= 1; emitted++;
        // emit from a crest of the loudest mode: (m+2)θ − 2√(m+2)·t + φ = 2πk
        let best = 0, bv = -1;
        for (let m = 0; m < 32; m++) if (b.modes[m] > bv) { bv = b.modes[m]; best = m; }
        const mm = best + 2;
        const ang = bv > 0.05 ? (2 * Math.sqrt(mm) * S.t - b.ph[best] + ((Math.random() * mm) | 0) * TAU) / mm : Math.random() * TAU;
        const r0 = 2.5 * R + 2, ve = (1.15 * P.c) / Math.sqrt(2.5);
        addLoop(b.x + Math.cos(ang) * r0, b.y + Math.sin(ang) * r0, b.vx + Math.cos(ang) * ve, b.vy + Math.sin(ang) * ve, 1, chirality());
        b.M -= 1; S.stats.hawk++; S.stats.loops++;
      }
      if (b.M < 60) {
        S.sparks.push({ x: b.x, y: b.y, life: 1.6, max: 1.6, col: '#ffffff', r: 50 });
        S.rings.push({ x: b.x, y: b.y, r: 0, v: 200, life: 1.4, col: '#ffffff' });
        burstPhotons(b.x, b.y, 40, 1.0, 0.4);
        S.bhs.splice(bi, 1);
      }
    }
    for (let i = 0; i < S.bhs.length; i++) for (let j = i + 1; j < S.bhs.length; j++) {
      const a = S.bhs[i], b = S.bhs[j];
      const dx = wrapD(b.x - a.x), dy = wrapD(b.y - a.y);
      if (Math.hypot(dx, dy) < rs(a.M) + rs(b.M)) {
        const M = a.M + b.M;
        a.vx = (a.vx * a.M + b.vx * b.M) / M; a.vy = (a.vy * a.M + b.vy * b.M) / M;
        a.x = wrapP(a.x + (dx * b.M) / M); a.y = wrapP(a.y + (dy * b.M) / M); a.M = M;
        for (let m = 0; m < 32; m++) a.modes[m] = Math.min(4, a.modes[m] + b.modes[m]);
        a.modes[0] += 2; a.eat = 1.5;
        S.rings.push({ x: a.x, y: a.y, r: 0, v: 260, life: 1.5, col: C.tape });
        S.bhs.splice(j, 1); j--;
      }
    }
    for (let i = S.nl - 1; i >= 0; i--) if (ldead[i]) removeLoop(i);
    for (let i = S.nk - 1; i >= 0; i--) if (kdead[i]) removeKnot(i);
    kcells.build(kx, ky, S.nk); lcells.build(lx, ly, S.nl);

    // 7) light: open strips moving at c relative to the river; excited knots re-emit their own line
    stepPhotons(dt);
    for (let i = 0; i < S.nk; i++) {
      if (kex[i] > 0 && Math.random() < 1.2 * dt) {
        kex[i] -= 1; const a = Math.random() * TAU;
        addPhoton(kx[i] + Math.cos(a) * 3, ky[i] + Math.sin(a) * 3, Math.cos(a), Math.sin(a), fRes(kn[i]));
      }
    }

    // 8) stars and supernova forges
    S.starT += dt;
    if (S.starT > 0.25) { S.starT = 0; findStars(); }
    for (const st of S.stars) {
      const n = (st.mass / 1000) * 1.3 * dt;
      let k = Math.floor(n) + (Math.random() < n % 1 ? 1 : 0);
      while (k-- > 0) {
        const a = Math.random() * TAU, r = Math.random() * st.r * 0.6;
        addPhoton(st.x + Math.cos(a) * r, st.y + Math.sin(a) * r, Math.cos(a), Math.sin(a), ML.clamp(0.3 + st.temp / 110 + (Math.random() - 0.5) * 0.25, 0.08, 1.2));
      }
    }
    for (const r of S.rings) { r.r += r.v * dt; r.life -= dt; }
    S.rings = S.rings.filter((r) => r.life > 0);
    for (const s of S.sparks) s.life -= dt;
    S.sparks = S.sparks.filter((s) => s.life > 0);

    S.histT += dt;
    if (S.histT > 0.5) {
      S.histT = 0;
      push(S.hist.mass, matterMass()); push(S.hist.loops, loopUnits()); push(S.hist.F, S.F * 100);
    }
  }
  function matterMass() { let m = 0; for (let i = 0; i < S.nk; i++) m += knotMass(kn[i]); return m; }
  function loopUnits() { let u = 0; for (let i = 0; i < S.nl; i++) u += lw[i]; return u; }
  function push(a, v) { a.push(v); if (a.length > 240) a.shift(); }

  // ------------------------------------------------------------------ photons: ray equations in a moving medium
  // x' = c·k̂ + v(x),  k' = −(∇v)ᵀk  (Hamiltonian ω = c|k| + v·k). v = the black-hole river.
  function stepPhotons(dt) {
    const c = P.c, hasBH = S.bhs.length > 0, red = S.H * dt;
    for (let i = S.np - 1; i >= 0; i--) {
      page[i] += dt;
      let x = px[i], y = py[i], kxx = pkx[i], kyy = pky[i];
      let sub = 1, swallowed = false;
      if (hasBH) for (const b of S.bhs) { if (Math.hypot(wrapD(b.x - x), wrapD(b.y - y)) < 8 * rs(b.M) + 30) { sub = 8; break; } }
      const h = dt / sub;
      for (let s = 0; s < sub; s++) {
        let vx = 0, vy = 0, dkx = 0, dky = 0;
        if (hasBH) {
          const e = 0.4;
          const v0 = riverBH(x, y); vx = v0[0]; vy = v0[1];
          const a = riverBH(x + e, y), axx = a[0], axy = a[1];
          const b2 = riverBH(x - e, y), bxx = b2[0], bxy = b2[1];
          const cc = riverBH(x, y + e), cyx = cc[0], cyy = cc[1];
          const d = riverBH(x, y - e), dyx = d[0], dyy = d[1];
          dkx = -(kxx * (axx - bxx) + kyy * (axy - bxy)) / (2 * e);
          dky = -(kxx * (cyx - dyx) + kyy * (cyy - dyy)) / (2 * e);
        }
        const kl = Math.hypot(kxx, kyy) || 1e-9;
        x += ((c * kxx) / kl + vx) * h; y += ((c * kyy) / kl + vy) * h;
        kxx += dkx * h; kyy += dky * h;
        if (hasBH) for (const b of S.bhs) {
          const R = rs(b.M), dx = wrapD(b.x - x), dy = wrapD(b.y - y);
          if (dx * dx + dy * dy < R * R) { swallowed = true; ring(b, 2 + (((Math.hypot(kxx, kyy) * 24) | 0) % 30), 0.03); b.M += 0.05; break; }
        }
        if (swallowed) break;
      }
      kxx *= 1 - red; kyy *= 1 - red;          // wavelengths stretch with space: cosmological redshift
      x = wrapP(x); y = wrapP(y);
      px[i] = x; py[i] = y; pkx[i] = kxx; pky[i] = kyy;
      const f = Math.hypot(kxx, kyy);
      if (swallowed || page[i] > 5.5 || f < 0.02) { removePhoton(i); continue; }
      // resonant absorption: a knot grabs only light matching its own line; simple loops ignore light
      if (S.nk > 0 && page[i] > 0.15 && Math.random() < 0.5) {
        let hit = -1;
        query(kcells, kx, ky, x, y, R_ABS, (j) => { hit = j; return false; });
        if (hit >= 0) {
          const df = (f - fRes(kn[hit])) / 0.055;
          if (Math.random() < 0.7 * Math.exp(-df * df)) { kex[hit] = Math.min(6, kex[hit] + 1); removePhoton(i); }
        }
      }
    }
  }

  // ------------------------------------------------------------------ stars & supernovae
  const SC = 46, SCS = L / SC;
  function findStars() {
    const m = new Float64Array(SC * SC), sx = new Float64Array(SC * SC), sy = new Float64Array(SC * SC), n = new Float64Array(SC * SC), v1x = new Float64Array(SC * SC), v1y = new Float64Array(SC * SC), v2 = new Float64Array(SC * SC);
    for (let i = 0; i < S.nk; i++) {
      const ix = Math.floor(kx[i] / SCS) % SC, iy = Math.floor(ky[i] / SCS) % SC, c = iy * SC + ix, w = knotMass(kn[i]);
      m[c] += w; sx[c] += (kx[i] - ix * SCS) * w; sy[c] += (ky[i] - iy * SCS) * w; n[c]++;
      v1x[c] += kvx[i]; v1y[c] += kvy[i]; v2[c] += kvx[i] * kvx[i] + kvy[i] * kvy[i];
    }
    const found = [], M_STAR = 900;
    for (let iy = 0; iy < SC; iy++) for (let ix = 0; ix < SC; ix++) {
      const c = iy * SC + ix;
      if (m[c] < M_STAR * 0.5) continue;
      let peak = true, bm = 0, bx = 0, by = 0;
      for (let dy = -1; dy <= 1 && peak; dy++) for (let dx = -1; dx <= 1; dx++) {
        const jx = (ix + dx + SC) % SC, jy = (iy + dy + SC) % SC, o = jy * SC + jx;
        if ((dx || dy) && (m[o] > m[c] || (m[o] === m[c] && o > c))) { peak = false; break; }
        bm += m[o]; bx += sx[o] + (ix + dx) * SCS * m[o]; by += sy[o] + (iy + dy) * SCS * m[o];
      }
      if (!peak || bm < M_STAR) continue;
      const mvx = v1x[c] / n[c], mvy = v1y[c] / n[c];
      found.push({ x: wrapP(bx / bm), y: wrapP(by / bm), mass: bm, temp: Math.sqrt(Math.max(0, v2[c] / n[c] - mvx * mvx - mvy * mvy)), r: 10 + Math.sqrt(bm) * 0.35, age: 0 });
    }
    for (const f of found) {
      let best = null, bd = 45 * 45;
      for (const o of S.stars) { const d2 = wrapD(o.x - f.x) ** 2 + wrapD(o.y - f.y) ** 2; if (d2 < bd) { bd = d2; best = o; } }
      f.age = best ? best.age + 0.25 : 0;
    }
    S.stars = found;
    for (const st of S.stars) if (st.age > 9 && st.mass > 1600) supernova(st);
  }
  function supernova(st) {
    S.stats.sn++;
    st.age = -6;
    const idx = [];
    query(kcells, kx, ky, st.x, st.y, 60, (j, d2, dx, dy) => { idx.push([j, d2, dx, dy]); });
    idx.sort((a, b) => a[1] - b[1]);
    let core = 0; const coreIdx = [];
    for (const it of idx) { if (core > st.mass * 0.45) break; core += knotMass(kn[it[0]]); coreIdx.push(it[0]); }
    if (core > 1300) {
      // crushed knots unbraid and fuse into one seamless surface: a black hole
      let vx = 0, vy = 0; for (const j of coreIdx) { vx += kvx[j]; vy += kvy[j]; kdead[j] = 1; }
      makeBH(st.x, st.y, core * 0.6, vx / coreIdx.length, vy / coreIdx.length);
    } else {
      // forge: core knots braid together into heavier knots
      for (let q = 0; q + 1 < coreIdx.length; q += 2) {
        const a = coreIdx[q], b = coreIdx[q + 1];
        if (kn[a] + kn[b] <= 16 && Math.random() < 0.7) { kn[a] = Math.min(15, kn[a] + kn[b] - 1); kdead[b] = 1; }
      }
    }
    for (const [j, d2, dx, dy] of idx) {
      if (kdead[j]) continue;
      const d = Math.sqrt(d2) || 1, k = 120 * (1 - d / 70);
      if (k > 0) { kvx[j] += (dx / d) * k; kvy[j] += (dy / d) * k; }
      if (Math.random() < 0.25 && kn[j] < 13) kn[j] += 2;
    }
    burstPhotons(st.x, st.y, 70, 0.95, 0.5);
    S.rings.push({ x: st.x, y: st.y, r: 0, v: 140, life: 1.6, col: C.tape });
    S.sparks.push({ x: st.x, y: st.y, life: 1.2, max: 1.2, col: '#fff3d6', r: 80 });
    for (let i = S.nk - 1; i >= 0; i--) if (kdead[i]) removeKnot(i);
    kcells.build(kx, ky, S.nk);
  }

  // ------------------------------------------------------------------ tools
  function applyTool(wx, wy) {
    wx = wrapP(wx); wy = wrapP(wy);
    if (S.tool === 'seed') {
      if (!seed(wx, wy)) S.flashMsg = { text: 'Seeds only grow in fresh flat field. Pick another tool, or press Big Bang again.', life: 3.5 };
    } else if (S.tool === 'cloud') {
      const rot = (Math.random() < 0.5 ? -1 : 1) * 16;
      for (let k = 0; k < 70; k++) {
        const a = Math.random() * TAU, r = Math.sqrt(Math.random()) * 45;
        addKnot(wx + Math.cos(a) * r, wy + Math.sin(a) * r, -Math.sin(a) * rot * (r / 45) + ML.gauss() * 5, Math.cos(a) * rot * (r / 45) + ML.gauss() * 5, Math.random() < 0.15 ? 5 : 3, Math.random() < 0.85 ? -1 : 1);
      }
      for (let k = 0; k < 40; k++) { const a = Math.random() * TAU, r = Math.sqrt(Math.random()) * 90; addLoop(wx + Math.cos(a) * r, wy + Math.sin(a) * r, ML.gauss() * 5, ML.gauss() * 5, 2, chirality()); }
      kcells.build(kx, ky, S.nk); lcells.build(lx, ly, S.nl);
    } else if (S.tool === 'bh') {
      makeBH(wx, wy, 26000);
    } else if (S.tool === 'minibh') {
      makeBH(wx, wy, 500);
    } else if (S.tool === 'flash') {
      for (let k = 0; k < 120; k++) { const a = (k / 120) * TAU; addPhoton(wx, wy, Math.cos(a), Math.sin(a), 0.85); }
      S.rings.push({ x: wx, y: wy, r: 0, v: P.c, life: 0.4, col: '#ffffff' });
    }
  }

  // ------------------------------------------------------------------ rendering
  let cv, ctx, W = 800, Hh = 600;
  const sprites = {};
  const knotColor = (n) => (n <= 3 ? C.pieces[0] : n <= 5 ? C.pieces[2] : n <= 7 ? C.pieces[3] : n <= 9 ? C.pieces[1] : n <= 11 ? C.pieces[4] : C.pieces[5]);
  function knotSprite(n, ch, fr) {
    const key = n + ':' + ch + ':' + fr;
    if (sprites[key]) return sprites[key];
    const SZ = 48, c = document.createElement('canvas'); c.width = c.height = SZ;
    const g = c.getContext('2d');
    g.translate(SZ / 2, SZ / 2); g.rotate(((fr / 16) * TAU) / Math.max(3, n)); if (ch > 0) g.scale(-1, 1);
    // (2,n) torus-knot diagram: two laps round the centre with n lobes; over-strands drawn with a gap
    const amp = 0.42, R = SZ * 0.3, pts = [];
    for (let i = 0; i <= 400; i++) { const t = (i / 400) * 2 * TAU, r = (R * (1 + amp * Math.cos((n * t) / 2))) / (1 + amp); pts.push([r * Math.cos(t), r * Math.sin(t)]); }
    const strokeAll = (w, col, sel) => {
      g.strokeStyle = col; g.lineWidth = w; g.beginPath();
      let pen = false;
      pts.forEach((p, i) => { if (!sel || sel(i)) { if (pen) g.lineTo(p[0], p[1]); else { g.moveTo(p[0], p[1]); pen = true; } } else pen = false; });
      g.stroke();
    };
    g.lineCap = 'round'; g.lineJoin = 'round';
    strokeAll(7, 'rgba(7,8,13,0.9)'); strokeAll(3.4, knotColor(n));
    const over = (i) => i <= 200 && i % 50 < 22;
    strokeAll(6.5, 'rgba(7,8,13,0.9)', over); strokeAll(3.4, knotColor(n), over);
    sprites[key] = c;
    return c;
  }

  // flat-field haze from the mesh: violet = fresh flat field, deep blue = crystallized, black = deep wells
  const haze = { cv: null, g: null, img: null };
  function hazeUpdate() {
    if (!haze.cv) { haze.cv = document.createElement('canvas'); haze.cv.width = haze.cv.height = NG + 2; haze.g = haze.cv.getContext('2d'); haze.img = haze.g.createImageData(NG + 2, NG + 2); }
    const data = haze.img.data, t = S.t, N2 = NG + 2;
    const flat = 0.22 + 0.78 * Math.max(0, (S.F - F_END) / (1 - F_END)), span = Math.max(1, phiMax - phiMin);
    for (let y = 0; y < N2; y++) for (let x = 0; x < N2; x++) {
      const gx = (x - 1 + NG) % NG, gy = (y - 1 + NG) % NG, i = gy * NG + gx;
      const cr = 1 - Math.exp(-lcount[i] * 1.3);                  // crystallized share of this cell
      const depth = (phiMax - phi[i]) / span;                      // 0 in voids, 1 in the deepest well
      let shimmer = 1;
      if (!S.reheated) shimmer = 0.9 + 0.035 * (Math.sin(0.31 * gx + 0.17 * gy + 1.1 * t) + Math.sin(-0.21 * gx + 0.37 * gy - 1.4 * t) + Math.sin(0.13 * gx - 0.29 * gy + 0.8 * t));
      const fv = flat * (1 - cr) * shimmer, dim = 1 - 0.85 * Math.pow(depth, 1.5);
      const r = (16 + 70 * fv + 8 * cr) * dim, g = (16 + 44 * fv + 18 * cr) * dim, b = (24 + 120 * fv + 34 * cr) * dim;
      const o = (y * N2 + x) * 4;
      data[o] = r; data[o + 1] = g; data[o + 2] = b; data[o + 3] = 255;
    }
    haze.g.putImageData(haze.img, 0, 0);
  }

  function tiles() {
    const s = S.cam.s, x0 = S.cam.x - W / 2 / s, x1 = S.cam.x + W / 2 / s, y0 = S.cam.y - Hh / 2 / s, y1 = S.cam.y + Hh / 2 / s;
    const out = [];
    for (let i = Math.floor(x0 / L); i <= Math.floor(x1 / L); i++) for (let j = Math.floor(y0 / L); j <= Math.floor(y1 / L); j++) out.push([i * L, j * L]);
    return out;
  }

  function draw(dt) {
    const g = ctx, cam = S.cam, s = cam.s;
    const T = tiles();
    g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#07080d'; g.fillRect(0, 0, W, Hh);
    if (P.show.haze) {
      S.hazeT -= dt;
      if (S.hazeT <= 0 || !haze.img) { hazeUpdate(); S.hazeT = 0.06; }
      g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
      for (const [ox, oy] of T) g.drawImage(haze.cv, 1, 1, NG, NG, (ox - cam.x) * s + W / 2, (oy - cam.y) * s + Hh / 2, L * s + 0.5, L * s + 0.5);
    }
    // the box seam: the universe wraps around here
    g.strokeStyle = 'rgba(170,176,196,0.16)'; g.lineWidth = 1; g.setLineDash([3, 6]);
    for (const [ox, oy] of T) { g.strokeRect((ox - cam.x) * s + W / 2, (oy - cam.y) * s + Hh / 2, L * s, L * s); }
    g.setLineDash([]);
    if (P.show.river) drawTracers(dt);

    for (const [ox, oy] of T) {
      const X = (x) => (x + ox - cam.x) * s + W / 2, Y = (y) => (y + oy - cam.y) * s + Hh / 2;
      // ghost loops (dark matter): hidden in telescope view
      if (P.show.loops && S.nl) {
        const r = ML.clamp(3.2 * s, 1.2, 3.2);
        for (const tint of [-1, 1]) {
          g.beginPath();
          for (let i = 0; i < S.nl; i++) {
            if (lc[i] !== tint) continue;
            const x = X(lx[i]), y = Y(ly[i]);
            if (x < -5 || y < -5 || x > W + 5 || y > Hh + 5) continue;
            const rr = r * (lw[i] > 1 ? Math.min(2.2, 1 + Math.log(lw[i]) * 0.25) : 1);
            const e = Math.abs(Math.cos(lph[i] / 2));       // the loop's 720° wobble
            g.moveTo(x + rr, y); g.ellipse(x, y, rr, rr * (0.35 + 0.65 * e), lph[i] * 0.5, 0, TAU);
          }
          g.strokeStyle = tint < 0 ? 'rgba(150,160,230,0.5)' : 'rgba(225,150,195,0.5)'; g.lineWidth = 1; g.stroke();
        }
      }
      // stars
      g.globalCompositeOperation = 'lighter';
      for (const st of S.stars) {
        const x = X(st.x), y = Y(st.y), r = Math.max(12, st.r * s * 2.4);
        if (x < -r || y < -r || x > W + r || y > Hh + r) continue;
        const hot = st.temp > 35;
        const gr = g.createRadialGradient(x, y, 0, x, y, r);
        gr.addColorStop(0, hot ? 'rgba(220,235,255,0.6)' : 'rgba(255,232,195,0.6)');
        gr.addColorStop(0.35, hot ? 'rgba(120,160,255,0.2)' : 'rgba(255,165,95,0.2)');
        gr.addColorStop(1, 'rgba(0,0,0,0)');
        g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill();
      }
      g.globalCompositeOperation = 'source-over';
      // knots (matter)
      const ksz = ML.clamp(16 * Math.sqrt(s), 5, 24);
      for (let i = 0; i < S.nk; i++) {
        const x = X(kx[i]), y = Y(ky[i]);
        if (x < -20 || y < -20 || x > W + 20 || y > Hh + 20) continue;
        const n = kn[i], sz = ksz * (0.8 + 0.08 * n);
        const fr = ((((kph[i] % TAU) + TAU) % TAU) / TAU) * 16 | 0;
        if (kex[i] > 0) { g.fillStyle = 'rgba(255,240,210,0.1)'; g.beginPath(); g.arc(x, y, sz * 0.55, 0, TAU); g.fill(); }
        g.drawImage(knotSprite(Math.min(n, 15) | 1, kc[i], fr), x - sz / 2, y - sz / 2, sz, sz);
      }
      // light
      if (P.show.light && S.np) {
        g.globalCompositeOperation = 'lighter'; g.lineWidth = 1.4; g.lineCap = 'round';
        for (let i = 0; i < S.np; i++) {
          const x = X(px[i]), y = Y(py[i]);
          if (x < -10 || y < -10 || x > W + 10 || y > Hh + 10) continue;
          const f = Math.hypot(pkx[i], pky[i]), ux = pkx[i] / f, uy = pky[i] / f;
          const hue = (ML.clamp(f, 0, 1.15) / 1.15) * 270;
          g.strokeStyle = 'hsla(' + hue.toFixed(0) + ',95%,66%,0.85)';
          g.beginPath();
          for (let k = 0; k <= 6; k++) {
            const u = k / 6, off = Math.sin(u * TAU * 1.5 + page[i] * 30) * 2.2 * (1 - u * 0.3);
            const qx = x - ux * 9 * u - uy * off, qy = y - uy * 9 * u + ux * off;
            if (k) g.lineTo(qx, qy); else g.moveTo(qx, qy);
          }
          g.stroke();
        }
        g.globalCompositeOperation = 'source-over';
      }
      // black holes: seamless surfaces with ringing modes
      for (const b of S.bhs) {
        const R = rs(b.M), x = X(b.x), y = Y(b.y), r = Math.max(3, R * s);
        if (x < -r * 4 || y < -r * 4 || x > W + r * 4 || y > Hh + r * 4) continue;
        if (b.eat > 0) {
          g.globalCompositeOperation = 'lighter';
          const gr = g.createRadialGradient(x, y, r, x, y, r * 3.2);
          gr.addColorStop(0, ML.rgba(C.tape, 0.35 * Math.min(1, b.eat))); gr.addColorStop(1, 'rgba(0,0,0,0)');
          g.fillStyle = gr; g.beginPath(); g.arc(x, y, r * 3.2, 0, TAU); g.fill();
          g.globalCompositeOperation = 'source-over';
        }
        g.setLineDash([2, 5]); g.strokeStyle = 'rgba(243,201,110,0.35)'; g.lineWidth = 1;
        g.beginPath(); g.arc(x, y, r * 1.5, 0, TAU); g.stroke(); g.setLineDash([]);
        g.beginPath();
        for (let k = 0; k <= 160; k++) {
          const th = (k / 160) * TAU;
          let dr = 0;
          for (let m = 0; m < 32; m++) if (b.modes[m] > 0.01) dr += b.modes[m] * Math.cos((m + 2) * th - Math.sqrt(m + 2) * 2 * S.t + b.ph[m]);
          const rr = r * (1 + 0.06 * dr);
          if (k) g.lineTo(x + rr * Math.cos(th), y + rr * Math.sin(th)); else g.moveTo(x + rr, y);
        }
        g.closePath(); g.fillStyle = '#000000'; g.fill();
        g.strokeStyle = C.tape; g.lineWidth = 1.5; g.stroke();
      }
      for (const rg of S.rings) {
        g.strokeStyle = ML.rgba(rg.col, Math.max(0, Math.min(1, rg.life)) * 0.6); g.lineWidth = 1.5;
        g.beginPath(); g.arc(X(rg.x), Y(rg.y), Math.max(1, rg.r * s), 0, TAU); g.stroke();
      }
      g.globalCompositeOperation = 'lighter';
      for (const sp of S.sparks) {
        const k = sp.life / sp.max, r = Math.max(4, sp.r * s * (1.4 - k * 0.4));
        const gr = g.createRadialGradient(X(sp.x), Y(sp.y), 0, X(sp.x), Y(sp.y), r);
        gr.addColorStop(0, ML.rgba(sp.col, 0.9 * k)); gr.addColorStop(1, 'rgba(0,0,0,0)');
        g.fillStyle = gr; g.beginPath(); g.arc(X(sp.x), Y(sp.y), r, 0, TAU); g.fill();
      }
      g.globalCompositeOperation = 'source-over';
    }
    drawScaleBar();
  }

  // river tracers: flat space flowing toward mass at the local escape speed (relative to the voids)
  function drawTracers(dt) {
    const g = ctx, cam = S.cam, s = cam.s, vw = W / s, vh = Hh / s;
    const ts = P.paused ? 0 : P.timeScale, span = Math.max(1e-6, phiMax - phiMin);
    g.lineWidth = 1; g.lineCap = 'round'; g.strokeStyle = 'rgba(214,200,255,0.34)';
    g.beginPath();
    for (let i = 0; i < NTR; i++) {
      if (tl[i] <= 0) {
        tx[i] = cam.x + (Math.random() - 0.5) * vw; ty[i] = cam.y + (Math.random() - 0.5) * vh; tpx[i] = tx[i]; tpy[i] = ty[i];
        tl[i] = 1.5 + Math.random() * 2.5;
        continue;
      }
      const sg = sampleGrid(tx[i], ty[i]);
      let vx = 0, vy = 0;
      const gm = Math.hypot(sg[0], sg[1]);
      if (gm > 1e-9 && span > 1) { const v = Math.sqrt(2 * Math.max(0, phiMax - sg[2])) * 0.6; vx = (v * sg[0]) / gm; vy = (v * sg[1]) / gm; }
      if (S.bhs.length) { const r = riverBH(tx[i], ty[i]); vx += r[0]; vy += r[1]; }
      const sp = Math.hypot(vx, vy), cap = P.c * 1.6;
      if (sp > cap) { vx *= cap / sp; vy *= cap / sp; }
      tpx[i] = tx[i]; tpy[i] = ty[i];
      tx[i] += vx * dt * ts; ty[i] += vy * dt * ts; tl[i] -= dt;
      let gone = false;
      for (const b of S.bhs) if (Math.hypot(wrapD(b.x - tx[i]), wrapD(b.y - ty[i])) < rs(b.M)) gone = true;
      if (gone) { tl[i] = 0; continue; }
      const x1 = (tx[i] - cam.x) * s + W / 2, y1 = (ty[i] - cam.y) * s + Hh / 2;
      let dx = (tx[i] - tpx[i]) * s, dy = (ty[i] - tpy[i]) * s;
      const dl = Math.hypot(dx, dy);
      if (dl < 2) { if (dl > 1e-6) { dx *= 2 / dl; dy *= 2 / dl; } else { dx = 0; dy = 0; } }
      if (dl > 1e-6 || dx) { g.moveTo(x1 - dx * 3, y1 - dy * 3); g.lineTo(x1, y1); }
    }
    g.stroke();
  }

  function drawScaleBar() {
    const g = ctx, s = S.cam.s, target = 110 / s;
    const pow = Math.pow(10, Math.floor(Math.log10(target)));
    const unit = [1, 2, 5, 10].map((k) => k * pow).find((u) => u >= target * 0.6) || pow;
    const pw = unit * s, x = W - 16 - pw, y = Hh - 18;
    g.strokeStyle = C.fg2; g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(x, y - 4); g.lineTo(x, y); g.lineTo(x + pw, y); g.lineTo(x + pw, y - 4); g.stroke();
    g.fillStyle = C.fg2; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'right'; g.textBaseline = 'bottom';
    g.fillText(ML.fmt(unit) + ' units of space', W - 16, y - 6);
  }

  // ------------------------------------------------------------------ panel & HUD
  let ro, specCv, specBlk, playBtn;
  const sparks = {}, hud = {};
  const TOOLS = [
    ['seed', 'Seed twist', 'Drop a twist into the flat field. While the field is fresh it starts a chain reaction.'],
    ['cloud', 'Knot cloud', 'Drop a cloud of 70 knots. Gravity pulls it into a star.'],
    ['bh', 'Black hole', 'Drop a big black hole (26,000 mass).'],
    ['minibh', 'Mini black hole', 'Drop a small black hole. Small ones pay the Hawking tax fast and pop.'],
    ['flash', 'Flash of light', 'Release a ring of light. Watch it bend round black holes.'],
    ['look', 'Look', 'Drag to pan, scroll or pinch to zoom.'],
  ];
  const IDEAS = `
    <p class="quote">"The universe is a singular, continuous, undulating geometric cloth… matter is space itself, beautifully knotted."</p>
    <div><h4>What the sim does with your rules</h4><ul>
      <li><b>Flat field = false vacuum.</b> The violet haze is high-energy flat space. A seed twist makes loops that copy themselves into the fresh field next to them, so a crystal front sweeps the universe like ice through supercooled water. Meanwhile space itself inflates enormously.</li>
      <li><b>Crystallizing releases heat.</b> When the front has filled the universe, the stored heat comes out at once (reheating) and runs the forge. Three loops tie into a trefoil at a rate of e<sup>−barrier/temperature</sup>. As the soup cools that rate collapses, so knots freeze out and their number stops growing.</li>
      <li><b>Mirror knots annihilate.</b> A left trefoil meeting a right trefoil unties into light. A small left-handed bias leaves a left-handed universe.</li>
      <li><b>Matter is a reef.</b> Knots keep turning flat field into simple loops (the mist), but never into new knots. Matter mass stays flat while loops keep growing, which is your answer to why the Earth doesn't gain weight.</li>
      <li><b>Gravity is inflow.</b> The streaks are flat space flowing toward mass at the local escape speed. Light moves at c relative to that river, so near a black hole it bends. Inside the horizon the river outruns it.</li>
      <li><b>Black holes are seamless surfaces.</b> Whatever falls in rings one of 32 surface modes (the bar chart). The ringing slowly crystallizes nearby flat field into loops, your Hawking tax. Small holes pay faster and pop.</li>
      <li><b>The universe wraps around.</b> The dashed square is the whole universe. Whatever leaves one edge comes back in the opposite edge, which is how real cosmology simulations avoid having an edge at all.</li>
    </ul></div>
    <div class="hook"><h4>Where this meets real physics</h4><ul>
      <li><b>Kelvin's vortex atoms (1867):</b> atoms as knots in the aether, the same idea you landed on. It inspired Tait's knot tables, and it died because it couldn't predict spectra.</li>
      <li><b>Skyrmions (Skyrme, 1961):</b> a working model where a proton is a twist in a field that can't be undone without tearing it. Baryon number is literally a topological winding number. It's the closest real cousin of your "topological lock".</li>
      <li><b>False vacuum and inflation</b> (Coleman 1977, Guth 1981): a high-energy flat field drives exponential growth, then decays and reheats the universe. Bubble growth from a seed is the textbook picture.</li>
      <li><b>Freeze-out</b> is how the Big Bang made its hydrogen and helium. The knot count here stalls for the same reason.</li>
      <li><b>The river model of black holes</b> (Hamilton &amp; Lisle, 2008): space flowing inward at escape speed reproduces Schwarzschild exactly. Light here follows those ray equations.</li>
      <li><b>Analog gravity</b> (Unruh 1981; Steinhauer 2016): sound in a flowing fluid has real horizons and Hawking-like radiation. Your "pudding" picture has been built in a lab.</li>
    </ul></div>
    <div><h4>Open questions the sim exposes</h4><ul>
      <li>What refills the flat field? Switch <b>Flat field refills</b> off and the mist stops once the field runs dry. Energy bookkeeping is the first thing a physicist will ask about.</li>
      <li>Kelvin's theory died on specifics. Which knot is the electron, and why does it have exactly its mass and charge? The sim assigns each knot one absorption line by hand. A real theory has to derive them.</li>
      <li>Simple loops here ignore light completely, which is what makes them dark matter. But why would a twist of space not scatter light at all?</li>
    </ul></div>`;

  const mode = {
    id: 'universe', tab: 'Universe', kind: '2d',
    buildPanel(el) {
      const U = ML.ui;
      U.head(el, 'Vacuum crystal universe', 'Your Topological Coherence Model run as rules: a flat field, a seed twist, a forge that ties knots, gravity as inflow, stars, supernovae, and black holes that pay a Hawking tax.');
      const run = U.block(el, 'Run');
      const btns = U.buttons(run, [
        { label: 'Big Bang again', primary: true, id: 'u-restart', onClick: () => reset() },
        { label: 'Pause', id: 'u-pause', onClick: () => { P.paused = !P.paused; playBtn.textContent = P.paused ? 'Play' : 'Pause'; } },
        { label: 'Fit view', id: 'u-fit', onClick: () => fitView() },
      ]);
      playBtn = btns[1];
      U.slider(run, { id: 'u-speed', label: 'Time speed', min: 0.25, max: 3, step: 0.25, value: P.timeScale, fmt: (v) => v.toFixed(2) + '×', onInput: (v) => (P.timeScale = v) });
      U.seg(run, { id: 'u-tool', label: 'Click the universe to', options: TOOLS.map((t) => [t[0], t[1], t[2]]), value: S.tool, onChange: (v) => { S.tool = v; hud.tool.textContent = TOOLS.find((t) => t[0] === v)[2]; } });

      const seen = U.block(el, 'What you are seeing');
      ro = U.readouts(seen, [
        ['phase', 'Phase'], ['age', 'Age'], ['F', 'Flat field left'], ['T', 'Temperature'], ['a', 'Space has grown'],
        ['loops', 'Ghost loops (dark)'], ['knots', 'Knots (matter)'], ['kinds', 'Trefoil · cinquefoil · heavier'], ['hand', 'Left : right knots'],
        ['mass', 'Matter mass'], ['bary', 'Matter share of mass'], ['light', 'Light in flight'], ['stars', 'Stars · supernovae'], ['bh', 'Black holes'],
      ]);

      const hist = U.block(el, 'History');
      const sp = ML.el('div', { class: 'spark' });
      [['mass', 'Matter mass', C.s1], ['loops', 'Ghost loops', C.s2], ['F', 'Flat field left (%)', C.s3]].forEach(([k, lbl, col]) => {
        const val = ML.el('span', { text: '—' });
        const cvs = ML.el('canvas', { class: 'chart', style: 'height:38px', 'aria-label': lbl + ' over time', role: 'img' });
        sp.append(ML.el('figure', null, [ML.el('figcaption', null, [ML.el('span', { text: lbl }), val]), cvs]));
        sparks[k] = { cv: cvs, val, col };
      });
      hist.append(sp);
      hist.append(ML.el('p', { class: 'chartcap', text: 'Last 2 minutes. Matter mass drops while mirror knots annihilate, then holds steady: the reef sheds mist but never gains weight. It only falls again when a supernova crushes knots into a black hole. Ghost loops keep climbing.' }));

      specBlk = U.block(el, 'Black hole surface');
      specCv = ML.el('canvas', { class: 'chart', style: 'height:96px', role: 'img', 'aria-label': 'Ringing modes of the largest black hole' });
      specBlk.append(specCv, ML.el('p', { class: 'chartcap', text: 'Energy in each of the 32 ringing modes of the biggest hole. Everything it swallowed is stored here as vibration, and the ringing pays the Hawking tax.' }));
      ML.attachHover(specCv, (x, y, w) => {
        const b = biggestBH(); if (!b) return null;
        const i = ML.clamp(Math.floor(((x - 6) / (w - 12)) * 32), 0, 31);
        return 'mode ' + (i + 2) + ' · energy ' + b.modes[i].toFixed(2);
      });
      specBlk.hidden = true;

      const lay = U.block(el, 'Layers');
      U.toggle(lay, { id: 'u-loops', label: 'Show ghost loops (off = telescope view)', value: P.show.loops, onChange: (v) => (P.show.loops = v) });
      U.toggle(lay, { id: 'u-river', label: 'River of flat space', value: P.show.river, onChange: (v) => (P.show.river = v) });
      U.toggle(lay, { id: 'u-haze', label: 'Flat-field haze', value: P.show.haze, onChange: (v) => (P.show.haze = v) });
      U.toggle(lay, { id: 'u-light', label: 'Light', value: P.show.light, onChange: (v) => (P.show.light = v) });

      const laws = U.block(el, 'Laws of this universe');
      U.slider(laws, { id: 'u-barrier', label: 'Knot barrier (how hard knots are to tie)', min: 1.2, max: 4, step: 0.1, value: P.barrier, fmt: (v) => v.toFixed(1), onInput: (v) => (P.barrier = v) });
      U.slider(laws, { id: 'u-bias', label: 'Left-handed bias', min: 0, max: 0.6, step: 0.05, value: P.leftBias, fmt: (v) => '+' + Math.round(v * 50) + '%', onInput: (v) => (P.leftBias = v) });
      U.slider(laws, { id: 'u-mist', label: 'Matter catalysis (mist rate)', min: 0, max: 3, step: 0.1, value: P.mist, fmt: (v) => v.toFixed(1) + '×', onInput: (v) => (P.mist = v) });
      U.slider(laws, { id: 'u-c', label: 'Speed of light', min: 140, max: 420, step: 10, value: P.c, fmt: (v) => v + ' u/s', onInput: (v) => (P.c = v) });
      U.toggle(laws, { id: 'u-endless', label: 'Flat field refills', value: P.endless, onChange: (v) => (P.endless = v) });
      laws.append(ML.el('p', { class: 'tip', text: 'Barrier and bias shape the next Big Bang. A slower speed of light makes black-hole horizons bigger.' }));
      U.ideas(el, IDEAS);
    },
    buildHud(el) {
      hud.phase = ML.el('div', { class: 'tag tl big' });
      hud.sub = ML.el('div', { class: 'tag', style: 'top:48px;left:max(12px, env(safe-area-inset-left, 0px))' });
      hud.tool = ML.el('div', { class: 'tag bl wide-only', text: TOOLS[0][2] });
      hud.legend = ML.el('div', { class: 'tag tr wide-only' });
      const sw = (c, t) => '<span style="display:inline-flex;align-items:center;gap:5px;margin-left:10px"><i style="width:8px;height:8px;border-radius:50%;background:' + c + ';display:inline-block"></i>' + t + '</span>';
      hud.legend.innerHTML = sw(C.pieces[0], 'trefoil') + sw(C.pieces[2], '5 crossings') + sw(C.pieces[3], '7+') + sw('#9aa2dd', 'ghost loop') + sw('#000;box-shadow:0 0 0 1px ' + C.tape, 'black hole');
      el.append(hud.phase, hud.sub, hud.tool, hud.legend);
    },
    init(app) {
      cv = app.c2d;
      reset();
      let drag = null;
      const pts = new Map();
      cv.addEventListener('pointerdown', (e) => {
        if (ML.app.current !== mode) return;
        cv.setPointerCapture(e.pointerId);
        pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
        drag = { moved: 0, pinch: 0 };
        if (pts.size === 2) { const p = [...pts.values()]; drag.pinch = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y); }
      });
      cv.addEventListener('pointermove', (e) => {
        if (ML.app.current !== mode || !drag || !pts.has(e.pointerId)) return;
        const prev = pts.get(e.pointerId), dx = e.clientX - prev.x, dy = e.clientY - prev.y;
        pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
        drag.moved += Math.abs(dx) + Math.abs(dy);
        if (pts.size === 1 && drag.moved > 5) { S.cam.x -= dx / S.cam.s; S.cam.y -= dy / S.cam.s; }
        else if (pts.size === 2) {
          const p = [...pts.values()], d = Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y);
          if (drag.pinch) S.cam.s = ML.clamp(S.cam.s * (d / drag.pinch), 0.15, 8);
          drag.pinch = d;
        }
      });
      const up = (e) => {
        if (!pts.has(e.pointerId)) return;
        pts.delete(e.pointerId);
        if (ML.app.current === mode && drag && drag.moved <= 5 && pts.size === 0 && S.tool !== 'look') {
          const r = cv.getBoundingClientRect();
          applyTool((e.clientX - r.left - W / 2) / S.cam.s + S.cam.x, (e.clientY - r.top - Hh / 2) / S.cam.s + S.cam.y);
        }
        if (pts.size === 0) drag = null;
      };
      cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
      cv.addEventListener('wheel', (e) => {
        if (ML.app.current !== mode) return;
        e.preventDefault();
        const r = cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
        const wx = (mx - W / 2) / S.cam.s + S.cam.x, wy = (my - Hh / 2) / S.cam.s + S.cam.y;
        S.cam.s = ML.clamp(S.cam.s * Math.exp(-e.deltaY * 0.0015), 0.15, 8);
        S.cam.x = wx - (mx - W / 2) / S.cam.s; S.cam.y = wy - (my - Hh / 2) / S.cam.s;
      }, { passive: false });
    },
    enter() {},
    exit() { ML.tooltip(null); },
    resize(w, h) {
      const first = !S.W;
      W = w; Hh = h; S.W = w; S.H_ = h; ctx = ML.fitCanvas(cv, w, h);
      if (first) fitView();
    },
    frame(dt) {
      if (!ctx) return;
      if (!P.paused) {
        let sim = dt * P.timeScale, steps = 0;
        while (sim > 1e-6 && steps < 4) { const h = Math.min(sim, 1 / 40); step(h); sim -= h; steps++; }
      }
      draw(dt);
      updatePanel(dt);
    },
    // test hooks
    _S: S, _P: P, _step: step, _reset: reset,
    _dbg() {
      let v2 = 0, maxN = 0;
      for (let i = 0; i < S.nk; i++) v2 += kvx[i] * kvx[i] + kvy[i] * kvy[i];
      for (let i = 0; i < S.nk; i += 7) { let c = 0; query(kcells, kx, ky, kx[i], ky[i], 26, () => { c++; }); maxN = Math.max(maxN, c); }
      let Lh = 0, Rh = 0; const kinds = {};
      for (let i = 0; i < S.nk; i++) { if (kc[i] < 0) Lh++; else Rh++; kinds[kn[i]] = (kinds[kn[i]] || 0) + 1; }
      let bhm = 0; for (const b of S.bhs) bhm += b.M;
      return { sig: Math.sqrt(v2 / Math.max(1, S.nk)), maxN, mass: matterMass(), loops: loopUnits(), LR: Lh + ':' + Rh, kinds: JSON.stringify(kinds), bhm, eaten: S.stats.bhEaten, hawk: S.stats.hawk, made: S.stats.loops, ann: S.stats.ann };
    },
  };

  function biggestBH() { let b = null; for (const o of S.bhs) if (!b || o.M > b.M) b = o; return b; }
  function phaseName() {
    if (!S.seeded) return ['Flat field', 'supercooled, waiting for a twist'];
    if (S.inflating) return ['Crystallizing', 'a crystal front sweeps the flat field while space inflates'];
    if (S.T > 0.3) return ['The forge', 'reheated soup: loops tying into knots'];
    if (S.stars.length) return ['Starlight', 'gravity has gathered knots into stars'];
    return ['Structure', 'freeze-out is over; gravity is gathering knots'];
  }
  let panelT = 0;
  function updatePanel(dt) {
    panelT -= dt; if (panelT > 0) return; panelT = 0.2;
    const [ph, sub] = phaseName();
    hud.phase.textContent = ph; hud.sub.textContent = sub + ' · t = ' + S.t.toFixed(1) + ' s';
    if (S.flashMsg) { S.flashMsg.life -= 0.2; hud.tool.textContent = S.flashMsg.text; if (S.flashMsg.life <= 0) { S.flashMsg = null; hud.tool.textContent = TOOLS.find((t) => t[0] === S.tool)[2]; } }
    const lu = loopUnits();
    let mm = 0, c3 = 0, c5 = 0, c7 = 0, Lh = 0, Rh = 0;
    for (let i = 0; i < S.nk; i++) { mm += knotMass(kn[i]); if (kn[i] <= 3) c3++; else if (kn[i] <= 5) c5++; else c7++; if (kc[i] < 0) Lh++; else Rh++; }
    let bhm = 0; for (const b of S.bhs) bhm += b.M;
    const growth = Math.exp(S.lnA);
    ro.set('phase', ph);
    ro.set('age', S.t.toFixed(1) + ' s');
    ro.meter('F', ML.pct(S.F, 1), S.F);
    ro.set('T', S.T < 0.005 ? 'cold' : S.T.toFixed(2) + (S.T > 0.3 ? ' (forge hot)' : ''));
    ro.set('a', '×' + (growth >= 1e6 ? growth.toExponential(1).replace('e+', '×10^') : ML.fmt(growth, growth < 10 ? 2 : 0)));
    ro.set('loops', ML.fmt(lu));
    ro.set('knots', ML.fmt(S.nk));
    ro.set('kinds', c3 + ' · ' + c5 + ' · ' + c7);
    ro.set('hand', Lh + ' : ' + Rh);
    ro.set('mass', ML.fmt(mm));
    const tot = mm + lu * P.mLoop + bhm;
    ro.set('bary', tot > 0 ? ML.pct(mm / tot) : '—');
    ro.set('light', ML.fmt(S.np));
    ro.set('stars', S.stars.length + ' · ' + S.stats.sn);
    const big = biggestBH();
    ro.set('bh', S.bhs.length ? S.bhs.length + ' · biggest ' + ML.fmt(big.M) : 'none yet');
    for (const k of ['mass', 'loops', 'F']) {
      const a = S.hist[k];
      sparks[k].val.textContent = a.length ? ML.fmt(a[a.length - 1], k === 'F' ? 1 : 0) : '—';
      ML.spark(sparks[k].cv, a, sparks[k].col, k === 'F' ? { min: 0, max: 100 } : { min: 0 });
    }
    specBlk.hidden = !big;
    if (big) ML.hist(specCv, Array.from(big.modes), C.s1, { marks: [[0, 'mode 2'], [1, 'mode 33']] });
  }

  ML.register(mode);
})();
