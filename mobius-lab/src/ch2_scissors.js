/* ============================================================
   Experiment 2: Scissors
   A paper-strip cutting lab. The pieces come from the fold rule;
   the shapes come from a position-based paper simulation
   (bends, doesn't stretch, can't pass through itself). Links and
   knots are measured from the simulated paper and checked.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const R = 1.25, W = 0.62;
  const RAIL_STEP = 0.25, GAP_S = 0.06, RAD = 0.04, SPREAD_PUSH = 6e-5, SPREAD_INFLATE = 1.5e-5;
  const COLORS = ['#f27aa2', '#45bdb7', '#f1b93f', '#9f86f5', '#86cc58', '#ff9668', '#5f9bff'];
  const NAMES = 'ABCDEFG';
  const FRACS = [{ v: 1 / 2, l: '½' }, { v: 1 / 3, l: '⅓' }, { v: 2 / 3, l: '⅔' }, { v: 1 / 4, l: '¼' }, { v: 1 / 5, l: '⅕' }, { v: 2 / 5, l: '⅖' }, { v: 1 / 6, l: '⅙' }];
  const fracLabel = f => (FRACS.find(x => Math.abs(x.v - f) < 1e-6) || { l: f.toFixed(2) }).l;
  const near = (a, b) => Math.abs(a - b) < 1e-7;

  const st = {
    n: 1, chi: 1, fracs: [1 / 3], phase: 'ready', guessN: null, guessOne: null, desk: false, mode: 'apart', autoJig: false,
    plan: null, predicted: null, measured: null, t: 0, cutT: 0, verifyT: 0, jiggle: 0
  };
  const ch = { token: 'scissors', gl: true, background: () => Lab.stageBg() };
  let colsPerLap = 150;
  let sim = null, meshes = [], cutObjs = [], scissorSprites = [], deskMesh, hud = {}, btn = {}, readout, diagram;

  /* ---------------- the fold rule ---------------- */
  function planPieces(n, fracs) {
    const odd = n % 2 === 1;
    let cuts = fracs.map(f => -1 + 2 * f);
    if (odd) cuts = cuts.concat(cuts.map(c => -c));
    cuts = cuts.map(c => (Math.abs(c) < 1e-9 ? 0 : c)).sort((a, b) => a - b).filter((c, i, a) => i === 0 || !near(c, a[i - 1]));
    const bounds = [-1, ...cuts, 1], ints = [];
    for (let i = 0; i < bounds.length - 1; i++) ints.push([bounds[i], bounds[i + 1]]);
    const pieces = [], used = new Set(), owner = new Array(ints.length);
    ints.forEach((iv, idx) => {
      if (used.has(idx)) return;
      used.add(idx);
      if (!odd) { owner[idx] = pieces.length; pieces.push({ laps: 1, oneSided: false, s0: iv[0], s1: iv[1] }); return; }
      const m = ints.findIndex(j => near(j[0], -iv[1]) && near(j[1], -iv[0]));
      if (m === idx) { owner[idx] = pieces.length; pieces.push({ laps: 1, oneSided: true, s0: iv[0], s1: iv[1] }); }
      else { used.add(m); owner[idx] = owner[m] = pieces.length; const hi = iv[0] >= 0 ? iv : ints[m]; pieces.push({ laps: 2, oneSided: false, s0: hi[0], s1: hi[1] }); }
    });
    // stable order: one-sided first, then by distance from the middle
    return { odd, cuts, ints, owner, pieces };
  }

  /* ---------------- paper simulation (PBD) ---------------- */
  class PaperSim {
    constructor(specs, r) {
      this.r = r; this.specs = specs;
      let N = 0; specs.forEach(p => { p.offset = N; N += p.M * p.K; });
      this.N = N;
      this.pos = new Float64Array(N * 3); this.prev = new Float64Array(N * 3); this.inv = new Float32Array(N).fill(1);
      this.piece = new Int16Array(N); this.col = new Int32Array(N);
      const ca = [], cb = [], r0 = [], r1 = [], kk = [], ta = [], tb = [], tc = [];
      specs.forEach((p, pi) => {
        for (let i = 0; i < p.M; i++) for (let j = 0; j < p.K; j++) {
          const id = p.offset + i * p.K + j;
          this.pos.set(p.init[(i * p.K + j)], id * 3);
          this.piece[id] = pi; this.col[id] = i;
        }
      });
      this.prev.set(this.pos);
      const P = this.pos;
      const dist = (a, b) => Math.hypot(P[b * 3] - P[a * 3], P[b * 3 + 1] - P[a * 3 + 1], P[b * 3 + 2] - P[a * 3 + 2]);
      const add = (a, b, rest, k) => { ca.push(a); cb.push(b); r0.push(dist(a, b)); r1.push(rest); kk.push(k); };
      specs.forEach(p => {
        const node = (i, j) => { if (i >= p.M) { i -= p.M; if (p.flip) j = p.K - 1 - j; } return p.offset + i * p.K + j; };
        p.node = node;
        for (let i = 0; i < p.M; i++) for (let j = 0; j < p.K; j++) {
          const a = node(i, j);
          add(a, node(i + 1, j), p.dU, 1);
          ta.push(a); tb.push(node(i + 1, j)); tc.push(node(i + 2, j));
          if (j < p.K - 1) {
            const dv = p.dV[j];
            add(a, node(i, j + 1), dv, 1);
            const dg = Math.hypot(p.dU, dv);
            add(a, node(i + 1, j + 1), dg, 0.9);
            add(node(i + 1, j), node(i, j + 1), dg, 0.9);
          }
          if (j < p.K - 2) add(a, node(i, j + 2), p.dV[j] + p.dV[j + 1], 0.25);
        }
      });
      this.ca = Int32Array.from(ca); this.cb = Int32Array.from(cb);
      this.ta = Int32Array.from(ta); this.tb = Int32Array.from(tb); this.tc = Int32Array.from(tc); this.kBend = 0.12;
      this.r0 = Float64Array.from(r0); this.r1 = Float64Array.from(r1); this.k = Float64Array.from(kk); this.rest = Float64Array.from(r0); this._bl = 0;
      this.T = 1; while (this.T < N * 2) this.T <<= 1;
      this.cellCount = new Int32Array(this.T); this.cellStart = new Int32Array(this.T + 1); this.sorted = new Int32Array(N); this.keys = new Int32Array(N); this.fillBuf = new Int32Array(this.T);
      this.cx = new Int32Array(N); this.cy = new Int32Array(N); this.cz = new Int32Array(N); this.asleep = false; this.calm = 0;
      this.blend = 0; this.gravity = 0; this.floorZ = -0.92; this.dragId = -1; this.dragTarget = [0, 0, 0]; this.rScale = 0.3;
    }
    solve() {
      const P = this.pos, ca = this.ca, cb = this.cb, RS = this.rest, K = this.k, nc = ca.length, drag = this.dragId;
      for (let c = 0; c < nc; c++) {
        const ia = ca[c], ib = cb[c], a = ia * 3, b = ib * 3;
        const dx = P[b] - P[a], dy = P[b + 1] - P[a + 1], dz = P[b + 2] - P[a + 2];
        const L = Math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-12;
        let s = K[c] * (L - RS[c]) / L;
        if (ia === drag) { P[b] -= s * dx; P[b + 1] -= s * dy; P[b + 2] -= s * dz; continue; }
        if (ib === drag) { P[a] += s * dx; P[a + 1] += s * dy; P[a + 2] += s * dz; continue; }
        s *= 0.5;
        P[a] += s * dx; P[a + 1] += s * dy; P[a + 2] += s * dz;
        P[b] -= s * dx; P[b + 1] -= s * dy; P[b + 2] -= s * dz;
      }
    }
    // Curvature bending: pull each rail point toward its neighbours' centroid (paper wants to be flat).
    bend() {
      const P = this.pos, A = this.ta, B = this.tb, C = this.tc, k = this.kBend, drag = this.dragId, n = A.length;
      for (let t = 0; t < n; t++) {
        const ia = A[t], ib = B[t], ic = C[t], a = ia * 3, b = ib * 3, c = ic * 3;
        const dx = (2 * P[b] - P[a] - P[c]) / 3, dy = (2 * P[b + 1] - P[a + 1] - P[c + 1]) / 3, dz = (2 * P[b + 2] - P[a + 2] - P[c + 2]) / 3;
        if (ib !== drag) { P[b] -= k * dx; P[b + 1] -= k * dy; P[b + 2] -= k * dz; }
        const h = 0.5 * k;
        if (ia !== drag) { P[a] += h * dx; P[a + 1] += h * dy; P[a + 2] += h * dz; }
        if (ic !== drag) { P[c] += h * dx; P[c + 1] += h * dy; P[c + 2] += h * dz; }
      }
    }
    setBlend(bl) {
      if (bl === this._bl) return;
      this._bl = bl; this.blend = bl;
      const r0 = this.r0, r1 = this.r1, RS = this.rest;
      for (let c = 0; c < RS.length; c++) RS[c] = r0[c] + (r1[c] - r0[c]) * bl;
    }
    collide() {
      const P = this.pos, N = this.N, inv = this.inv, T = this.T, mask = T - 1;
      const r = this.r * this.rScale, h = 2 * r, d2max = h * h;
      const cc = this.cellCount, cs = this.cellStart, sorted = this.sorted, keys = this.keys;
      cc.fill(0);
      const key = (x, y, z) => (((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) & mask);
      const CX = this.cx, CY = this.cy, CZ = this.cz;
      for (let i = 0; i < N; i++) { const x = Math.floor(P[i * 3] / h), y = Math.floor(P[i * 3 + 1] / h), z = Math.floor(P[i * 3 + 2] / h); CX[i] = x; CY[i] = y; CZ[i] = z; const k = key(x, y, z); keys[i] = k; cc[k]++; }
      let acc = 0; for (let k = 0; k < T; k++) { cs[k] = acc; acc += cc[k]; } cs[T] = acc;
      const fill = this.fillBuf; fill.fill(0); for (let i = 0; i < N; i++) { const k = keys[i]; sorted[cs[k] + fill[k]++] = i; }
      const piece = this.piece, col = this.col, specs = this.specs;
      for (let a = 0; a < N; a++) {
        const ax = P[a * 3], ay = P[a * 3 + 1], az = P[a * 3 + 2];
        const cx = CX[a], cy = CY[a], cz = CZ[a];
        for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
          const k = key(cx + dx, cy + dy, cz + dz);
          for (let q = cs[k], qe = cs[k] + cc[k]; q < qe; q++) {
            const b = sorted[q];
            if (b <= a) continue;
            if (piece[a] === piece[b]) {
              const M = specs[piece[a]].M; let d = Math.abs(col[a] - col[b]); if (d > M - d) d = M - d;
              if (d <= 2) continue;
            }
            const ex = P[b * 3] - ax, ey = P[b * 3 + 1] - ay, ez = P[b * 3 + 2] - az;
            const dd = ex * ex + ey * ey + ez * ez;
            if (dd >= d2max || dd < 1e-14) continue;
            const L = Math.sqrt(dd), wa = inv[a], wb = inv[b], ws = wa + wb; if (!ws) continue;
            const corr = (h - L) / (L * ws);
            P[a * 3] -= wa * corr * ex; P[a * 3 + 1] -= wa * corr * ey; P[a * 3 + 2] -= wa * corr * ez;
            P[b * 3] += wb * corr * ex; P[b * 3 + 1] += wb * corr * ey; P[b * 3 + 2] += wb * corr * ez;
          }
        }
      }
    }
    step(dt, iters = 7) {
      const sub = 2, hdt = dt / sub, P = this.pos, Q = this.prev, N = this.N, g = this.gravity * hdt * hdt;
      const vmax = this.r * 0.45;
      for (let s = 0; s < sub; s++) {
        for (let i = 0; i < N; i++) {
          const a = i * 3;
          let vx = (P[a] - Q[a]) * 0.985, vy = (P[a + 1] - Q[a + 1]) * 0.985, vz = (P[a + 2] - Q[a + 2]) * 0.985;
          const vv = Math.sqrt(vx * vx + vy * vy + vz * vz);
          if (vv > vmax) { const f = vmax / vv; vx *= f; vy *= f; vz *= f; }
          Q[a] = P[a]; Q[a + 1] = P[a + 1]; Q[a + 2] = P[a + 2];
          if (this.inv[i] === 0) continue;
          P[a] += vx; P[a + 1] += vy; P[a + 2] += vz - g;
        }
        if (this.dragId >= 0) { const a = this.dragId * 3; P[a] = this.dragTarget[0]; P[a + 1] = this.dragTarget[1]; P[a + 2] = this.dragTarget[2]; }
        for (let it = 0; it < iters; it++) { this.solve(); if (it % 2 === 0) this.bend(); }
        if (s === sub - 1) this.collide();
        if (this.gravity > 0) {
          const fz = this.floorZ + this.r;
          for (let i = 0; i < N; i++) {
            const a = i * 3;
            if (P[a + 2] < fz) { P[a + 2] = fz; Q[a] += (P[a] - Q[a]) * 0.7; Q[a + 1] += (P[a + 1] - Q[a + 1]) * 0.7; if (Q[a + 2] < fz) Q[a + 2] = fz; }
          }
        }
      }
      // fall asleep when nothing is moving, so a resting sculpture costs nothing
      let vmaxNow = 0;
      for (let i = 0; i < N * 3; i++) { const d = Math.abs(P[i] - Q[i]); if (d > vmaxNow) vmaxNow = d; }
      this.calm = vmaxNow < 2.5e-5 ? this.calm + 1 : 0;
      if (this.calm > 45 && this.dragId < 0 && this.blend >= 1) this.asleep = true;
    }
    wake() { this.asleep = false; this.calm = 0; }
    recenter() {
      if (this.gravity > 0 || this.dragId >= 0) return;
      const P = this.pos, Q = this.prev, N = this.N; let x = 0, y = 0, z = 0;
      for (let i = 0; i < N; i++) { x += P[i * 3]; y += P[i * 3 + 1]; z += P[i * 3 + 2]; }
      x /= N; y /= N; z /= N;
      const f = 0.03;
      for (let i = 0; i < N; i++) { P[i * 3] -= x * f; P[i * 3 + 1] -= y * f; P[i * 3 + 2] -= z * f; Q[i * 3] -= x * f; Q[i * 3 + 1] -= y * f; Q[i * 3 + 2] -= z * f; }
    }
    kick(strength) {
      const P = this.pos, Q = this.prev, N = this.N;
      for (let h = 0; h < 3; h++) {
        const c = Math.floor(Math.random() * N) * 3;
        const jx = (Math.random() - 0.5) * strength, jy = (Math.random() - 0.5) * strength, jz = (Math.random() - 0.3) * strength;
        for (let i = 0; i < N; i++) {
          const a = i * 3, d2 = (P[a] - P[c]) ** 2 + (P[a + 1] - P[c + 1]) ** 2 + (P[a + 2] - P[c + 2]) ** 2;
          const f = Math.exp(-d2 / 0.5);
          Q[a] -= jx * f; Q[a + 1] -= jy * f; Q[a + 2] -= jz * f;
        }
      }
    }
    // "Pull apart": like holding the pieces away from each other. Pieces repel; each loop is gently inflated.
    spread(push, inflate) {
      const specs = this.specs, P = this.pos, Q = this.prev;
      const cents = specs.map(sp => { let x = 0, y = 0, z = 0; const m = sp.M * sp.K; for (let q = 0; q < m; q++) { const id = (sp.offset + q) * 3; x += P[id]; y += P[id + 1]; z += P[id + 2]; } return [x / m, y / m, z / m]; });
      specs.forEach((sp, p) => {
        let fx = 0, fy = 0, fz = 0;
        specs.forEach((sq, q) => {
          if (q === p) return;
          let dx = cents[p][0] - cents[q][0], dy = cents[p][1] - cents[q][1], dz = cents[p][2] - cents[q][2];
          const d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < 1e-4) { dx = (p - q) * 0.01; dz = 0.01; }
          const f = push / (d2 + 0.3); fx += dx * f; fy += dy * f; fz += dz * f;
        });
        const m = sp.M * sp.K, c = cents[p];
        for (let q = 0; q < m; q++) {
          const id = (sp.offset + q) * 3;
          if (sp.offset + q === this.dragId) continue;
          Q[id] -= fx + (P[id] - c[0]) * inflate; Q[id + 1] -= fy + (P[id + 1] - c[1]) * inflate; Q[id + 2] -= fz + (P[id + 2] - c[2]) * inflate;
        }
      });
    }
    p(id) { return [this.pos[id * 3], this.pos[id * 3 + 1], this.pos[id * 3 + 2]]; }
  }

  /* ---------------- building pieces ---------------- */
  function pieceSpec(pc, n, chi) {
    const s0 = pc.s0 + (pc.s0 > -1 + 1e-9 ? GAP_S : 0), s1 = pc.s1 - (pc.s1 < 1 - 1e-9 ? GAP_S : 0);
    let K = Math.max(2, Math.ceil((s1 - s0) / RAIL_STEP) + 1);
    const M = colsPerLap * pc.laps;
    const sv = []; for (let j = 0; j < K; j++) sv.push(s0 + (s1 - s0) * j / (K - 1));
    const init = [];
    for (let i = 0; i < M; i++) { const th = i * TAU / colsPerLap; for (let j = 0; j < K; j++) init.push(Lab.bandPoint(th, sv[j], n, chi, R, W)); }
    const dU = TAU * R / colsPerLap;
    const dV = []; for (let j = 0; j < K - 1; j++) dV.push((sv[j + 1] - sv[j]) * W / 2);
    return { M, K, flip: pc.oneSided, init, dU, dV, s0, s1, laps: pc.laps, oneSided: pc.oneSided };
  }
  function makeMesh(spec, color) {
    const { M, K } = spec;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array((M + 1) * K * 3), 3));
    const uv = new Float32Array((M + 1) * K * 2);
    for (let i = 0; i <= M; i++) for (let j = 0; j < K; j++) { uv[(i * K + j) * 2] = i * spec.dU / (W * 1.6); uv[(i * K + j) * 2 + 1] = j / (K - 1); }
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    const idx = [];
    for (let i = 0; i < M; i++) for (let j = 0; j < K - 1; j++) { const a = i * K + j, b = (i + 1) * K + j, c = (i + 1) * K + j + 1, d = i * K + j + 1; idx.push(a, b, d, b, c, d); }
    geo.setIndex(idx);
    const front = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(true, color), roughness: 0.88, side: THREE.FrontSide }));
    const back = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(false, color), roughness: 0.88, side: THREE.BackSide }));
    const group = new THREE.Group(); group.add(front, back);
    return { group, geo, spec, front, back };
  }
  function syncMeshes() {
    meshes.forEach(m => {
      const { M, K } = m.spec, arr = m.geo.getAttribute('position').array, P = sim.pos;
      for (let i = 0; i <= M; i++) for (let j = 0; j < K; j++) {
        const id = m.spec.node(i, j) * 3, v = (i * K + j) * 3;
        arr[v] = P[id]; arr[v + 1] = P[id + 1]; arr[v + 2] = P[id + 2];
      }
      m.geo.getAttribute('position').needsUpdate = true;
      m.geo.computeVertexNormals();
      m.geo.computeBoundingSphere();
    });
  }
  function clearScene() {
    meshes.forEach(m => { ch.scene.remove(m.group); m.geo.dispose(); m.front.material.dispose(); m.back.material.dispose(); });
    meshes = [];
    cutObjs.forEach(o => { ch.scene.remove(o); if (o.geometry) o.geometry.dispose(); });
    cutObjs = [];
    scissorSprites.forEach(s => ch.scene.remove(s)); scissorSprites = [];
    sim = null;
  }

  /* ---------------- measuring ---------------- */
  function curves(spec) {
    const { M, K, node } = spec, P = sim.pos;
    const pt = id => [P[id * 3], P[id * 3 + 1], P[id * 3 + 2]];
    const core = [], e0 = [], e1 = [];
    for (let i = 0; i < M; i++) {
      const a = pt(node(i, 0)), b = pt(node(i, K - 1));
      core.push([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]); e0.push(a); e1.push(b);
    }
    return spec.oneSided ? { core, boundary: e0.concat(e1) } : { core, e0, e1 };
  }
  function measure() {
    const cs = sim.specs.map(curves);
    const pieces = sim.specs.map((sp, i) => {
      const c = cs[i];
      return { knot: Lab.knotDet(c.core), twist: sp.oneSided ? Lab.linking(c.core, c.boundary) : Lab.linking(c.e0, c.e1) };
    });
    const links = [];
    for (let a = 0; a < cs.length; a++) for (let b = a + 1; b < cs.length; b++) links.push({ a, b, lk: Lab.linking(cs[a].core, cs[b].core) });
    return { pieces, links };
  }
  function sameTopology(p, q) {
    if (!p || !q) return false;
    for (let i = 0; i < p.pieces.length; i++) if (p.pieces[i].knot !== q.pieces[i].knot || p.pieces[i].twist !== q.pieces[i].twist) return false;
    for (let i = 0; i < p.links.length; i++) if (p.links[i].lk !== q.links[i].lk) return false;
    return true;
  }

  /* ---------------- describing ---------------- */
  function twistText(sp, m) {
    if (sp.oneSided) return `${Math.abs(m.twist)} half-twist${Math.abs(m.twist) === 1 ? '' : 's'}`;
    const t = Math.abs(m.twist);
    if (m.knot !== 1) return `edges link ${t}×`;
    if (t === 0) return 'no twist';
    return `${t} full twist${t === 1 ? '' : 's'} (${2 * t} half)`;
  }
  function linkName(lk, total) {
    const a = Math.abs(lk);
    if (a === 1 && total === 2) return 'linked once (a Hopf link)';
    if (a === 1) return 'linked once';
    return `linked ${a}×`;
  }
  function renderReadout() {
    if (st.phase === 'ready' || st.phase === 'cutting') {
      readout.innerHTML = `<h4>Result</h4><p style="margin:0;color:var(--muted)">${st.phase === 'ready' ? 'Make a guess above if you like, then press Cut. The rule is in the diagram below if you want a hint.' : 'Cutting…'}</p>`;
      return;
    }
    const pr = st.predicted, specs = sim.specs, k = specs.length;
    const rows = specs.map((sp, i) => {
      const m = pr.pieces[i];
      const lk = pr.links.filter(l => (l.a === i || l.b === i) && l.lk !== 0).map(l => `${NAMES[l.a === i ? l.b : l.a]} (${Math.abs(l.lk)}×)`);
      return `<tr><td><span class="swatch" style="background:${COLORS[i % COLORS.length]}"></span>${NAMES[i]}</td>
        <td>${sp.laps === 2 ? '2× the original' : 'same as original'}</td>
        <td>${sp.oneSided ? '<b>one</b> (Möbius-type)' : 'two'}</td>
        <td>${twistText(sp, m)}</td>
        <td>${Lab.knotName(m.knot)}</td>
        <td>${lk.length ? lk.join(', ') : '–'}</td></tr>`;
    }).join('');
    // summary sentence
    const one = specs.filter(s => s.oneSided).length, longs = specs.filter(s => s.laps === 2).length, knotted = pr.pieces.filter(p => p.knot !== 1).length;
    const linked = pr.links.filter(l => l.lk !== 0);
    let sum = `${k} piece${k === 1 ? '' : 's'}`;
    const bits = [];
    if (one) bits.push(`${one === 1 ? 'a' : one} one-sided Möbius-type strip${one > 1 ? 's' : ''} the same length as the original`);
    if (longs) bits.push(`${longs === 1 ? 'a' : longs} two-sided loop${longs > 1 ? 's' : ''} twice as long`);
    if (k - one - longs) bits.push(`${k - one - longs === 1 ? 'a' : k - one - longs} two-sided loop${k - one - longs > 1 ? 's' : ''} the same length as the original`);
    sum += ': ' + bits.join(', ') + '.';
    if (knotted) sum += ` ${knotted === 1 ? 'One is' : knotted + ' are'} tied in a ${Lab.knotName(pr.pieces.find(p => p.knot !== 1).knot)}.`;
    if (k > 1) sum += linked.length ? ` ${linked.length === k * (k - 1) / 2 && k > 2 ? 'Every pair is linked.' : linked.length === 1 ? 'They are ' + linkName(linked[0].lk, k) + '.' : linked.length + ' pairs are linked.'}` : ' None of them are linked; they just fall apart.';
    // guess
    let guess = '';
    if (st.guessN != null || st.guessOne != null) {
      const okN = st.guessN == null ? null : (st.guessN === 4 ? k >= 4 : st.guessN === k);
      const okO = st.guessOne == null ? null : (st.guessOne === 'yes') === (one > 0);
      const part = [];
      if (okN != null) part.push(`pieces <span class="${okN ? 'ok' : 'miss'}">${okN ? '✓' : '✗'}</span>`);
      if (okO != null) part.push(`one-sided piece <span class="${okO ? 'ok' : 'miss'}">${okO ? '✓' : '✗'}</span>`);
      guess = `<p class="verdict-line">Your guess: ${part.join(' · ')}</p>`;
    }
    const ver = st.measured == null ? '<span style="color:var(--muted)">measuring the simulated paper…</span>'
      : sameTopology(st.predicted, st.measured) ? '<span class="ok">✓</span> Measured from the relaxed simulated paper: same twists, knots and links as the rule predicts.'
        : '<span class="miss">⚠</span> The simulated paper slipped through itself, which real paper can\'t do. Press Reset and cut again.';
    readout.innerHTML = `<h4>Result</h4><p style="margin:0 0 8px">${sum}</p>
      <div class="tbl-wrap"><table class="pieces"><thead><tr><th>Piece</th><th>Length</th><th>Sides</th><th>Twist</th><th>Knot</th><th>Linked with</th></tr></thead><tbody>${rows}</tbody></table></div>
      ${guess}<p class="verdict-line" style="font-size:.875rem">${ver}</p>
      <p class="verdict-line" style="font-size:.8125rem;color:var(--muted)">Colors are added so you can tell the pieces apart. Drag a piece to pull it around.</p>`;
  }

  /* ---------------- diagram ---------------- */
  function renderDiagram() {
    const plan = planPieces(st.n, st.fracs), odd = plan.odd;
    const narrow = (diagram.parentElement.clientWidth || 600) < 520;
    const Wd = narrow ? 420 : 600, Hd = narrow ? 186 : 172, x0 = narrow ? 64 : 96, x1 = Wd - x0, y0 = 22, y1 = 122;
    const yOf = s => y1 - (s + 1) / 2 * (y1 - y0);
    const ink = 'var(--ink)', muted = 'var(--muted)';
    let svg = `<svg viewBox="0 0 ${Wd} ${Hd}" role="img" aria-label="Gluing diagram of the strip with the cut lines">`;
    plan.ints.forEach((iv, idx) => {
      const pi = plan.owner[idx];
      svg += `<rect x="${x0}" y="${yOf(iv[1])}" width="${x1 - x0}" height="${yOf(iv[0]) - yOf(iv[1])}" fill="${COLORS[pi % COLORS.length]}" opacity="0.88"/>`;
      svg += `<text x="${(x0 + x1) / 2}" y="${(yOf(iv[0]) + yOf(iv[1])) / 2 + 5}" text-anchor="middle" font-family="var(--font-mono)" font-size="13" font-weight="700" fill="#1b2140">${NAMES[pi]}</text>`;
    });
    svg += `<rect x="${x0}" y="${y0}" width="${x1 - x0}" height="${y1 - y0}" fill="none" stroke="${ink}" stroke-width="1.5"/>`;
    const chosen = st.fracs.map(f => -1 + 2 * f);
    plan.cuts.forEach(c => {
      const isChosen = chosen.some(x => near(x, c));
      const y = yOf(c);
      svg += `<line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="#1b2140" stroke-width="2" ${isChosen ? '' : 'stroke-dasharray="6 5"'}/>`;
      const f = (c + 1) / 2;
      svg += `<text x="${x0 - 6}" y="${y + 4}" text-anchor="end" font-family="var(--font-mono)" font-size="11" fill="${muted}">${fracLabel(+f.toFixed(6))}</text>`;
      if (!isChosen) svg += `<text x="${x1 - 6}" y="${y - 5}" text-anchor="end" font-family="var(--font-mono)" font-size="10.5" font-weight="700" fill="#1b2140">2nd lap</text>`;
    });
    // gluing arrows
    const arrow = (x, up) => { const ya = up ? y1 - 8 : y0 + 8, yb = up ? y0 + 8 : y1 - 8, hd = up ? -1 : 1;
      return `<line x1="${x}" y1="${ya}" x2="${x}" y2="${yb}" stroke="var(--pink)" stroke-width="3"/><path d="M${x - 7} ${yb - hd * 10} L${x} ${yb} L${x + 7} ${yb - hd * 10}" fill="none" stroke="var(--pink)" stroke-width="3" stroke-linejoin="round"/>`; };
    svg += arrow(x0 - (narrow ? 40 : 64), true) + arrow(x1 + (narrow ? 40 : 66), !odd);
    const l1 = odd ? 'Glue the ends with a flip (arrows opposite): x meets 1 − x.' : 'Glue the ends with no flip (arrows match): x meets x.';
    if (narrow) {
      svg += `<text x="${Wd / 2}" y="${Hd - 38}" text-anchor="middle" font-family="var(--font-body)" font-size="14" fill="${ink}">${odd ? 'Glue with a flip: x meets 1 − x.' : 'Glue straight: x meets x.'}</text>`;
      svg += `<text x="${Wd / 2}" y="${Hd - 18}" text-anchor="middle" font-family="var(--font-mono)" font-size="11" fill="${muted}">solid = your cuts · dashed = 2nd lap</text>`;
    } else {
      svg += `<text x="${(x0 + x1) / 2}" y="${Hd - 20}" text-anchor="middle" font-family="var(--font-body)" font-size="13.5" fill="${ink}">${l1}</text>`;
      svg += `<text x="${(x0 + x1) / 2}" y="${Hd - 2}" text-anchor="middle" font-family="var(--font-mono)" font-size="10.5" fill="${muted}">bottom edge = 0 · top edge = 1 · solid = your cuts · dashed = 2nd lap</text>`;
    }
    svg += '</svg>';
    const k = plan.pieces.length, one = plan.pieces.some(p => p.oneSided);
    let txt;
    if (!st.fracs.length) txt = 'Pick at least one place to cut.';
    else if (!odd) txt = `${st.n === 0 ? 'No twist' : 'An even number of half-twists'}: no flip at the joint, so each stripe closes on itself after one lap. ${st.fracs.length} cut${st.fracs.length > 1 ? 's' : ''} → ${k} loops, each as long as the original${st.n ? `, and every pair links ${st.n / 2}×` : ', and none of them link'}.`;
    else txt = `An odd number of half-twists: the joint flips the strip, so the stripe at x continues at 1 − x. Same color means same piece. A stripe joined to its mirror becomes one loop twice as long.${one ? ' The middle stripe is its own mirror, so it stays one-sided.' : ' Nothing is left in the middle, so no piece stays one-sided.'}${st.n >= 3 ? ` With ${st.n} half-twists the long loops come out knotted.` : ''}`;
    diagram.innerHTML = `<h4>The rule, drawn as a gluing diagram</h4>${svg}<p class="cap">${txt}</p>`;
  }

  /* ---------------- phases ---------------- */
  function buildUncut() {
    clearScene();
    const spec = pieceSpec({ laps: 1, oneSided: st.n % 2 === 1, s0: -1, s1: 1 }, st.n, st.chi);
    sim = new PaperSim([spec], RAD);
    meshes.push(makeMesh(spec, COLORS[0]));
    ch.scene.add(meshes[0].group);
    syncMeshes();
    // cut guides
    const lines = [];
    const seen = [];
    st.fracs.forEach(f => {
      const c = -1 + 2 * f;
      if (seen.some(x => near(x, c) || (st.n % 2 && near(x, -c)))) return;
      seen.push(c);
      const laps = (st.n % 2 && !near(c, 0)) ? 2 : 1;
      lines.push({ c, laps });
    });
    st.cutLines = lines;
    lines.forEach(L => {
      const steps = 260 * L.laps;
      [1, -1].forEach(side => {
        const pts = [];
        for (let i = 0; i <= steps; i++) {
          const th = i / steps * TAU * L.laps, fr = Lab.bandFrame(th, L.c, st.n, st.chi, R, W);
          pts.push(fr.p.clone().add(fr.normal.clone().multiplyScalar(0.006 * side)));
        }
        const g = new THREE.BufferGeometry().setFromPoints(pts);
        const dashed = new THREE.Line(g, new THREE.LineDashedMaterial({ color: 0x1b2140, dashSize: 0.06, gapSize: 0.045 }));
        dashed.computeLineDistances();
        ch.scene.add(dashed); cutObjs.push(dashed);
      });
      // slit ribbon revealed behind the scissors
      const slitGeo = Lab.bandGeometry({ n: st.n, chi: st.chi, R, W, segU: 220 * L.laps, segV: 1, s0: L.c - 0.045, s1: L.c + 0.045, phi0: 0, phi1: TAU * L.laps });
      const slit = new THREE.Mesh(slitGeo, new THREE.MeshBasicMaterial({ color: 0x1b2140, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      slitGeo.setDrawRange(0, 0);
      slit.userData = { L, segU: 220 * L.laps };
      ch.scene.add(slit); cutObjs.push(slit);
      L.slit = slit;
      const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: scissorsTexture(), depthTest: false, transparent: true }));
      sp.scale.set(0.26, 0.26, 1); sp.renderOrder = 10; sp.visible = false;
      ch.scene.add(sp); scissorSprites.push(sp); L.sprite = sp;
    });
    st.phase = 'ready';
    st.predicted = st.measured = null;
    hud.top.innerHTML = `<b>${st.n}</b> half-twist${st.n === 1 ? '' : 's'} · cut at <b>${st.fracs.map(fracLabel).join(', ') || 'nowhere'}</b>`;
    hud.right.textContent = st.n % 2 ? 'One-sided strip' : 'Two-sided strip';
    hud.tip.hidden = true;
    renderReadout(); renderDiagram(); syncButtons();
  }
  let _sciTex = null;
  function scissorsTexture() {
    if (_sciTex) return _sciTex;
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    g.translate(64, 64); g.rotate(-0.5);
    g.lineCap = 'round'; g.strokeStyle = '#1b2140'; g.fillStyle = '#ffffff';
    g.lineWidth = 9;
    g.beginPath(); g.moveTo(-6, 4); g.lineTo(52, -22); g.stroke();
    g.beginPath(); g.moveTo(-6, -4); g.lineTo(52, 22); g.stroke();
    g.lineWidth = 8;
    [[-30, -18], [-30, 18]].forEach(([x, y]) => { g.beginPath(); g.arc(x, y, 15, 0, TAU); g.fill(); g.stroke(); });
    g.fillStyle = '#e8457a'; g.beginPath(); g.arc(-4, 0, 6, 0, TAU); g.fill();
    _sciTex = new THREE.CanvasTexture(c); _sciTex.encoding = THREE.sRGBEncoding;
    return _sciTex;
  }
  function startCut() {
    st.userCam = false;
    if (!st.fracs.length) { Lab.toast(ch.stage, 'Pick at least one place to cut first.'); return; }
    st.phase = 'cutting'; st.cutT = 0;
    st.cutLines.forEach(L => { L.sprite.visible = true; });
    hud.right.textContent = 'Scissors: lap 1';
    renderReadout(); syncButtons();
  }
  function finishCut() {
    const plan = planPieces(st.n, st.fracs);
    st.plan = plan;
    clearScene();
    const specs = plan.pieces.map(pc => pieceSpec(pc, st.n, st.chi));
    sim = new PaperSim(specs, RAD);
    specs.forEach((sp, i) => { const m = makeMesh(sp, COLORS[i % COLORS.length]); meshes.push(m); ch.scene.add(m.group); });
    syncMeshes();
    st.predicted = measure();
    st.measured = null;
    st.phase = 'relaxing'; st.t = 0; st.verifyT = 0; st.autoJig = false;
    sim.gravity = st.desk ? 24 : 0;
    hud.right.textContent = `${specs.length} piece${specs.length === 1 ? '' : 's'}`;
    hud.tip.hidden = false;
    renderReadout(); syncButtons();
  }
  function syncButtons() {
    btn.cut.disabled = st.phase !== 'ready';
    btn.jiggle.disabled = st.phase !== 'relaxing';
  }

  /* ---------------- dragging pieces ---------------- */
  let ray = null, ndc = null;
  let dragPlane = null;
  function pointerNDC(ev) { const r = Lab.getRenderer().domElement.getBoundingClientRect(); ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1); }
  function onDown(ev) {
    if (Lab.active !== ch || st.phase !== 'relaxing' || !sim) return;
    pointerNDC(ev); ray.setFromCamera(ndc, ch.camera);
    const hits = ray.intersectObjects(meshes.flatMap(m => [m.front, m.back]), false);
    if (!hits.length) return;
    const hp = hits[0].point;
    let best = -1, bd = Infinity;
    for (let i = 0; i < sim.N; i++) { const d = (sim.pos[i * 3] - hp.x) ** 2 + (sim.pos[i * 3 + 1] - hp.y) ** 2 + (sim.pos[i * 3 + 2] - hp.z) ** 2; if (d < bd) { bd = d; best = i; } }
    if (best < 0) return;
    ev.stopImmediatePropagation(); ev.preventDefault();
    sim.dragId = best; sim.inv[best] = 0;
    sim.dragTarget = [sim.pos[best * 3], sim.pos[best * 3 + 1], sim.pos[best * 3 + 2]];
    dragPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(ch.camera.getWorldDirection(new THREE.Vector3()).negate(), hp.clone());
    ch.controls.enabled = false;
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp, { once: true });
    window.addEventListener('pointercancel', onUp, { once: true });
  }
  function onMove(ev) {
    if (!sim || sim.dragId < 0) return;
    pointerNDC(ev); ray.setFromCamera(ndc, ch.camera);
    const p = new THREE.Vector3();
    if (ray.ray.intersectPlane(dragPlane, p)) {
      const lim = 3.2; sim.dragTarget = [Lab.clamp(p.x, -lim, lim), Lab.clamp(p.y, -lim, lim), Lab.clamp(p.z, sim.floorZ + 0.05, lim)];
    }
  }
  function onUp() {
    window.removeEventListener('pointermove', onMove);
    if (sim && sim.dragId >= 0) { sim.inv[sim.dragId] = 1; sim.dragId = -1; }
    if (Lab.active === ch) ch.controls.enabled = true;
    st.verifyT = 0.6; st.measured = null; renderReadout();
  }

  // Keep every piece in view until the person takes over the camera.
  function fitCamera(dt) {
    const P = sim.pos, N = sim.N; let cx = 0, cy = 0, cz = 0;
    for (let i = 0; i < N; i++) { cx += P[i * 3]; cy += P[i * 3 + 1]; cz += P[i * 3 + 2]; }
    cx /= N; cy /= N; cz /= N;
    let r2 = 0; for (let i = 0; i < N; i += 3) { const d = (P[i * 3] - cx) ** 2 + (P[i * 3 + 1] - cy) ** 2 + (P[i * 3 + 2] - cz) ** 2; if (d > r2) r2 = d; }
    const cam = ch.camera, half = THREE.MathUtils.degToRad(cam.fov / 2), hfov = Math.atan(Math.tan(half) * cam.aspect);
    const want = Math.max(4.2, Math.sqrt(r2) / Math.sin(Math.min(half, hfov)) * 1.08);
    const tgt = ch.controls.target, k = Math.min(1, dt * 1.5);
    tgt.x += (cx - tgt.x) * k; tgt.y += (cy - tgt.y) * k; tgt.z += ((st.desk ? cz - 0.2 : cz) - tgt.z) * k;
    const dir = cam.position.clone().sub(tgt); const d = dir.length();
    cam.position.copy(tgt).add(dir.multiplyScalar((d + (want - d) * k) / d));
  }

  /* ---------------- init ---------------- */
  const POSE = [[2.7, -3.6, 2.7], [0, 0, 0]], POSE_DESK = [[0.6, -2.4, 4.6], [0, 0, -0.6]];
  ch.init = function (section, stage) {
    colsPerLap = window.innerWidth < 600 ? 120 : 150;
    ray = new THREE.Raycaster(); ndc = new THREE.Vector2();
    const { scene, camera, controls } = Lab.makeScene({ pos: POSE[0] });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    controls.addEventListener('start', () => { st.userCam = true; });
    const wood = Lab.woodTexture().clone(); wood.needsUpdate = true; wood.repeat.set(2, 2);
    deskMesh = new THREE.Mesh(new THREE.PlaneGeometry(12, 12), new THREE.MeshStandardMaterial({ map: wood, roughness: 0.92 }));
    deskMesh.position.z = -0.92; scene.add(deskMesh);

    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.top = Lab.el('div', { class: 'chip' }); hud.right = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.top, hud.right);
    const bottom = Lab.el('div', { class: 'hud hud-bottom' });
    hud.tip = Lab.el('div', { class: 'chip', text: 'Drag a piece to pull it. Drag empty space to turn the view.' });
    bottom.append(hud.tip);
    stage.append(hud.wrap, bottom);

    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Half-twists', id: 's-n', value: st.n, options: [0, 1, 2, 3, 4, 5].map(v => ({ value: v, label: String(v) })), onChange: v => { st.n = v; buildUncut(); } });
    Lab.ui.seg(c, { label: 'Handedness', id: 's-chi', value: st.chi, options: [{ value: 1, label: 'Left' }, { value: -1, label: 'Right' }], onChange: v => { st.chi = v; buildUncut(); } });
    Lab.ui.chips(c, { label: 'Cut at (fraction of the width)', id: 's-cut', options: FRACS.map(f => ({ value: f.v, label: f.l })), values: st.fracs,
      onChange: vals => {
        const odd = st.n % 2 === 1;
        if (odd && vals.some(a => vals.some(b => a !== b && near(a + b, 1)))) Lab.toast(ch.stage, 'On an odd strip, x and 1 − x are the same cut line. Watch.');
        st.fracs = vals.slice().sort((a, b) => a - b); buildUncut();
      } });
    const g1 = Lab.ui.group(c, 'Your guess');
    const gr = Lab.el('div', { class: 'btn-row' }); g1.append(gr);
    const gN = Lab.ui.seg(gr, { label: null, id: 's-gn', value: null, options: [1, 2, 3, 4].map(v => ({ value: v, label: v === 4 ? '4+ pieces' : v + (v === 1 ? ' piece' : '') })), onChange: v => { st.guessN = v; } });
    const gO = Lab.ui.seg(gr, { label: null, id: 's-go', value: null, options: [{ value: 'yes', label: 'one-sided piece' }, { value: 'no', label: 'none one-sided' }], onChange: v => { st.guessOne = v; } });
    gN.el.querySelector('.lbl') && gN.el.querySelector('.lbl').remove();
    const row = Lab.ui.row(Lab.ui.group(c, 'Do it'));
    btn.cut = Lab.ui.button(row, { label: '✂ Cut', id: 's-cutbtn', primary: true, onClick: startCut });
    btn.jiggle = Lab.ui.button(row, { label: 'Jiggle', id: 's-jiggle', onClick: () => { st.jiggle = 0.9; st.measured = null; st.verifyT = 1.6; renderReadout(); } });
    Lab.ui.button(row, { label: 'Reset', id: 's-reset', onClick: () => { st.userCam = false; st.guessN = st.guessOne = null; gN.set(null); gO.set(null); buildUncut(); Lab.tweenCamera(ch, ...(st.desk ? POSE_DESK : POSE)); } });
    Lab.ui.seg(c, { label: 'Hands', id: 's-desk', value: 'apart', options: [{ value: 'apart', label: 'Pull apart' }, { value: 'off', label: 'Let it float' }, { value: 'on', label: 'Drop on desk' }],
      onChange: v => { st.mode = v; st.desk = v === 'on'; if (sim && st.phase === 'relaxing') { sim.gravity = st.desk ? 24 : 0; sim.wake(); st.measured = null; st.verifyT = 2.5; renderReadout(); } Lab.tweenCamera(ch, ...(st.desk ? POSE_DESK : POSE)); } });

    readout = section.querySelector('[data-readout]');
    diagram = section.querySelector('[data-diagram]');
    const cv = Lab.getRenderer().domElement;
    cv.addEventListener('pointerdown', onDown, { capture: true });
    cv.addEventListener('touchstart', ev => { if (Lab.active === ch && sim && sim.dragId >= 0) { ev.stopImmediatePropagation(); } }, { capture: true, passive: true });
    buildUncut();
  };

  ch.frame = function (dt) {
    if (!Lab.stepTween(ch, dt)) ch.controls.update();
    if (!sim) return;
    if (st.phase === 'cutting') {
      st.cutT += dt;
      const lapTime = 2.1;
      let done = true;
      st.cutLines.forEach(L => {
        const prog = Math.min(1, st.cutT / (lapTime * L.laps));
        if (prog < 1) done = false;
        const segs = Math.floor(prog * L.slit.userData.segU);
        L.slit.geometry.setDrawRange(0, segs * 6);
        const th = prog * TAU * L.laps, fr = Lab.bandFrame(th, L.c, st.n, st.chi, R, W);
        L.sprite.position.copy(fr.p.clone().add(fr.normal.clone().multiplyScalar(0.05)));
      });
      const maxLaps = Math.max(...st.cutLines.map(L => L.laps));
      const lapNow = Math.min(maxLaps, 1 + Math.floor(st.cutT / lapTime));
      hud.right.textContent = maxLaps === 2 ? `Scissors: lap ${lapNow} of 2` : 'Scissors: lap 1 of 1';
      if (done) { st.cutLines.forEach(L => (L.sprite.visible = false)); finishCut(); }
      return;
    }
    if (st.phase !== 'relaxing') return;
    st.t += dt;
    sim.setBlend(Lab.smooth(Math.min(1, st.t / 2.2)));
    sim.rScale = Math.min(1, 0.3 + st.t / 1.6);
    if (st.jiggle > 0) { sim.wake(); sim.kick(0.016 * st.jiggle); st.jiggle = Math.max(0, st.jiggle - dt); }
    if (sim.dragId >= 0) sim.wake();
    if (st.mode === 'apart' && st.t > 2.4) { if (!sim.asleep) sim.spread(SPREAD_PUSH, SPREAD_INFLATE); }
    if (!st.autoJig && st.t > 2.4) { st.autoJig = true; if (st.mode !== 'on') { st.jiggle = 0.5; } }
    if (!sim.asleep) {
      sim.step(Math.min(dt, 1 / 30), sim.blend < 1 ? 6 : 4);
      sim.recenter();
      syncMeshes();
      if (!st.userCam && !ch._tween) fitCamera(dt);
    }
    st.verifyT -= dt;
    if (st.t > 2.6 && st.verifyT <= 0 && st.jiggle <= 0 && sim.dragId < 0) {
      st.verifyT = 2.0;
      const m = measure();
      const changed = !st.measured || !sameTopology(m, st.measured);
      st.measured = m;
      if (changed) renderReadout();
    }
  };
  ch.leave = function () { onUp(); };

  Lab.register(ch);
}
