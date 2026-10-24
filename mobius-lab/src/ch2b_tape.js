/* ============================================================
   Experiment 3: Tape.
   Two paper loops taped together, crosswise (|X|) or face to face
   (the butterfly), then cut down their middles. Each loop is a grid
   of square cells. Tape holds the overlapping cells of the two loops
   together, so where the scissors cross the tape they cut through
   both layers. Pieces, sides and edges are counted exactly from the
   cells; the shapes come from paper physics like Scissors'.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const W = 0.62, ROWS = 9, NJ = ROWS + 1, NI = 91, H = W / ROWS, R = NI * H / TAU;   // square cells, so the crosswise tape is square
  const MID = (ROWS - 1) / 2;                       // the middle row of cells, where the scissors go
  const GAP = 0.08, RAD = 0.04, CUT_SPEED = 26, FLOOR = -2.45, SPREAD_PUSH = 6e-5, FREE_PUSH = 3e-4, SPREAD_INFLATE = 1.5e-5;
  const NPS = NI * NJ, CPS = NI * ROWS, NN = 2 * NPS, NC = 2 * CPS;
  const PATCH = { cross: [41, ROWS], par: [40, 12] };   // first column and length of the taped stretch
  const PAL = [['#f27aa2', '#f1b93f', '#ff9668', '#e15c88'], ['#45bdb7', '#5f9bff', '#86cc58', '#9f86f5']];
  const MARKS = ['#1b2140', '#2b8a3e', '#862e9c', '#a61e4d', '#5c3d2e', '#0b7285'];   // dark marker colors, unlike either side paint
  const SIDES = ['#4c6ef5', '#ffa94d'];             // paint for the two faces, when painting by sides
  const CORNER = [[0, 0], [1, 0], [1, 1], [0, 1]];
  const LOOPS = [{ value: 'plain', label: 'Plain ring', n: 0, chi: 1 }, { value: 'left', label: 'Möbius, left', n: 1, chi: 1 },
    { value: 'right', label: 'Möbius, right', n: 1, chi: -1 }, { value: 'full', label: 'Full twist', n: 2, chi: 1 }];
  const loopOf = v => LOOPS.find(l => l.value === v);

  const st = {
    A: 'left', B: 'plain', join: 'cross', mode: 'apart', desk: false, marks: true, paint: 'pieces',
    t: 0, tCut: 0, jiggle: 0, autoJig: true, cutting: null, done: { A: false, B: false }, history: [], lastAnalyze: 0,
    res: null, geo: null, geoOk: null, verifyT: 0, script: null, checks: {}, userCam: false
  };
  const ch = { token: 'tape', gl: true, background: () => Lab.stageBg() };

  /* ---------------- the paper ---------------- */
  const pos = new Float64Array(NN * 3), prev = new Float64Array(NN * 3), inv = new Float32Array(NN);
  const active = new Uint8Array(NC), alive = new Uint8Array(NN), linkCell = new Int32Array(NC), tapeOf = new Int32Array(NN), onTape = new Uint8Array(NN);
  const pieceOfNode = new Int16Array(NN), objOfNode = new Int16Array(NN), markOf = new Int16Array(NC);
  let tapePairs = [], CA, CB, R0, R1, KK, REST, TA, TB, TC, excl = new Set(), blend = -1, gravity = 0, asleep = false, calm = 0, dragId = -1, dragTarget = [0, 0, 0];
  let HT = 1; while (HT < NN * 2) HT <<= 1;
  const hCount = new Int32Array(HT), hStart = new Int32Array(HT + 1), hSorted = new Int32Array(NN), hKey = new Int32Array(NN), hFill = new Int32Array(HT);
  const CX = new Int32Array(NN), CY = new Int32Array(NN), CZ = new Int32Array(NN);
  let meshes = [], deskMesh, sprite, hud = {}, btn = {}, ctl = {}, readout, notebook;

  const nOf = s => loopOf(s ? st.B : st.A).n;
  // Past its last column a loop carries on at column 0, flipped across its width if it has an odd number of half-twists.
  function node(s, i, j) {
    if (i < 0 || i >= NI) { i = (i + NI) % NI; if (nOf(s) % 2) j = ROWS - j; }
    return s * NPS + i * NJ + j;
  }
  function cellAt(s, i, v) {
    if (i < 0 || i >= NI) { i = (i + NI) % NI; if (nOf(s) % 2) v = ROWS - 1 - v; }
    return s * CPS + i * ROWS + v;
  }
  const sivOf = c => { const s = c >= CPS ? 1 : 0, k = c - s * CPS; return [s, (k / ROWS) | 0, k % ROWS]; };
  function corners(c) { const [s, i, v] = sivOf(c); return [node(s, i, v), node(s, i + 1, v), node(s, i + 1, v + 1), node(s, i, v + 1)]; }
  function neighbours(c) {
    const [s, i, v] = sivOf(c), nb = [cellAt(s, i - 1, v), cellAt(s, i + 1, v)];
    if (v > 0) nb.push(cellAt(s, i, v - 1));
    if (v < ROWS - 1) nb.push(cellAt(s, i, v + 1));
    return nb;
  }
  const ekey = (a, b) => (a < b ? a * NN + b : b * NN + a);
  const dist = (a, b) => Math.hypot(pos[b * 3] - pos[a * 3], pos[b * 3 + 1] - pos[a * 3 + 1], pos[b * 3 + 2] - pos[a * 3 + 2]);
  const pt = n => [pos[n * 3], pos[n * 3 + 1], pos[n * 3 + 2]];

  // Loop A stands on the tape and loop B hangs under it, turned 90° (crosswise) or lined up (face to face).
  // The twisting happens away from the tape, so the taped stretch starts out flat.
  function place() {
    for (let s = 0; s < 2; s++) {
      const L = loopOf(s ? st.B : st.A), cross = st.join === 'cross';
      for (let i = 0; i < NI; i++) {
        const th = (i - NI / 2) * TAU / NI, a = Math.abs(th), t0 = 0.75;
        const prof = a <= t0 ? 0 : Math.sign(th) * Lab.smooth(Math.min(1, (a - t0) / (Math.PI - t0)));
        const al = L.chi * L.n * Math.PI / 2 * prof, sn = Math.sin(th), cs = Math.cos(th), ca = Math.cos(al), sa = Math.sin(al);
        let c, nin, side;
        if (s === 0) { c = [R * sn, 0, R * (1 - cs)]; nin = [-sn, 0, cs]; side = [0, 1, 0]; }
        else if (cross) { c = [0, R * sn, -GAP - R * (1 - cs)]; nin = [0, -sn, -cs]; side = [1, 0, 0]; }
        else { c = [R * sn, 0, -GAP - R * (1 - cs)]; nin = [-sn, 0, -cs]; side = [0, 1, 0]; }
        for (let j = 0; j < NJ; j++) {
          const o = (j - ROWS / 2) * H, id = (s * NPS + i * NJ + j) * 3;
          for (let k = 0; k < 3; k++) pos[id + k] = c[k] + (ca * side[k] + sa * nin[k]) * o;
        }
      }
    }
    prev.set(pos);
  }
  function setupTape() {
    linkCell.fill(-1); onTape.fill(0); tapePairs = [];
    const [c0, len] = PATCH[st.join], cross = st.join === 'cross';
    for (let u = 0; u < len; u++) for (let v = 0; v < ROWS; v++) {
      const a = cellAt(0, c0 + u, v), b = cross ? cellAt(1, c0 + v, u) : cellAt(1, c0 + u, v);
      linkCell[a] = b; linkCell[b] = a;
    }
    for (let p = 0; p <= len; p++) for (let q = 0; q <= ROWS; q++) {
      const a = node(0, c0 + p, q), b = cross ? node(1, c0 + q, p) : node(1, c0 + p, q);
      tapePairs.push([a, b]); onTape[a] = onTape[b] = 1;
    }
  }
  // Constraints come from the cells that are still there, so a cut is just cells going missing.
  function rebuild() {
    alive.fill(0);
    for (let c = 0; c < NC; c++) if (active[c]) for (const n of corners(c)) alive[n] = 1;
    const E = new Map(), add = (a, b, r, k) => { const key = ekey(a, b); if (!E.has(key)) E.set(key, [a, b, r, k]); };
    for (let c = 0; c < NC; c++) if (active[c]) {
      const [a, b, c2, d] = corners(c);
      add(a, b, H, 1); add(d, c2, H, 1); add(a, d, H, 1); add(b, c2, H, 1);
      add(a, c2, H * Math.SQRT2, 0.9); add(b, d, H * Math.SQRT2, 0.9);
    }
    const paper = [...E.values()];
    tapeOf.fill(-1);
    for (const [a, b] of tapePairs) if (alive[a] && alive[b]) { tapeOf[a] = b; tapeOf[b] = a; add(a, b, GAP, 1); }
    // tape also stops the two layers sliding over each other
    const dg = Math.hypot(GAP, H);
    for (const [a, b, , k] of paper) {
      if (k !== 1 || a >= NPS || b >= NPS || tapeOf[a] < 0 || tapeOf[b] < 0) continue;
      if (E.has(ekey(tapeOf[a], tapeOf[b]))) { add(a, tapeOf[b], dg, 0.8); add(b, tapeOf[a], dg, 0.8); }
    }
    const list = [...E.values()], n = list.length;
    CA = new Int32Array(n); CB = new Int32Array(n); R0 = new Float64Array(n); R1 = new Float64Array(n); KK = new Float64Array(n); REST = new Float64Array(n);
    list.forEach(([a, b, r, k], c) => { CA[c] = a; CB[c] = b; R1[c] = r; KK[c] = k; R0[c] = dist(a, b); });
    setBlend(blend, true);
    // bending: paper resists curving, along its length and across its width
    const A3 = [], B3 = [], C3 = [];
    for (let s = 0; s < 2; s++) for (let i = 0; i < NI; i++) for (let j = 0; j < NJ; j++) {
      const m = node(s, i, j); if (!alive[m]) continue;
      const l = node(s, i - 1, j), r = node(s, i + 1, j);
      if (E.has(ekey(l, m)) && E.has(ekey(m, r))) { A3.push(l); B3.push(m); C3.push(r); }
      if (j > 0 && j < ROWS) { const d = node(s, i, j - 1), u = node(s, i, j + 1); if (E.has(ekey(d, m)) && E.has(ekey(m, u))) { A3.push(d); B3.push(m); C3.push(u); } }
    }
    TA = Int32Array.from(A3); TB = Int32Array.from(B3); TC = Int32Array.from(C3);
    excl = new Set(E.keys());
    for (let i = 0; i < NN; i++) inv[i] = alive[i] && i !== dragId ? 1 : 0;
  }
  function setBlend(b, force) {
    if (b === blend && !force) return;
    blend = b;
    for (let c = 0; c < REST.length; c++) REST[c] = R0[c] + (R1[c] - R0[c]) * Math.max(0, b);
  }
  function solve() {
    const P = pos, n = CA.length;
    for (let c = 0; c < n; c++) {
      const ia = CA[c], ib = CB[c], wa = inv[ia], wb = inv[ib], ws = wa + wb; if (!ws) continue;
      const a = ia * 3, b = ib * 3, dx = P[b] - P[a], dy = P[b + 1] - P[a + 1], dz = P[b + 2] - P[a + 2];
      const L = Math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-12, s = KK[c] * (L - REST[c]) / (L * ws);
      P[a] += wa * s * dx; P[a + 1] += wa * s * dy; P[a + 2] += wa * s * dz;
      P[b] -= wb * s * dx; P[b + 1] -= wb * s * dy; P[b + 2] -= wb * s * dz;
    }
  }
  // Pull each point toward its neighbours' midpoint: paper wants to be flat.
  function bend() {
    const P = pos, k = 0.12, h = 0.5 * k, n = TA.length;
    for (let t = 0; t < n; t++) {
      const ia = TA[t], ib = TB[t], ic = TC[t], a = ia * 3, b = ib * 3, c = ic * 3;
      const dx = (2 * P[b] - P[a] - P[c]) / 3, dy = (2 * P[b + 1] - P[a + 1] - P[c + 1]) / 3, dz = (2 * P[b + 2] - P[a + 2] - P[c + 2]) / 3;
      if (inv[ib]) { P[b] -= k * dx; P[b + 1] -= k * dy; P[b + 2] -= k * dz; }
      if (inv[ia]) { P[a] += h * dx; P[a + 1] += h * dy; P[a + 2] += h * dz; }
      if (inv[ic]) { P[c] += h * dx; P[c + 1] += h * dy; P[c + 2] += h * dz; }
    }
  }
  // Paper can't pass through paper: keep points that aren't joined at least one paper thickness apart.
  function collide() {
    const P = pos, h = 2 * RAD, h2 = h * h, mask = HT - 1;
    const hk = (x, y, z) => (((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) & mask);
    hCount.fill(0);
    for (let i = 0; i < NN; i++) {
      if (!alive[i]) { hKey[i] = -1; continue; }
      const x = Math.floor(P[i * 3] / h), y = Math.floor(P[i * 3 + 1] / h), z = Math.floor(P[i * 3 + 2] / h);
      CX[i] = x; CY[i] = y; CZ[i] = z; const k = hk(x, y, z); hKey[i] = k; hCount[k]++;
    }
    let acc = 0; for (let k = 0; k < HT; k++) { hStart[k] = acc; acc += hCount[k]; } hStart[HT] = acc;
    hFill.fill(0); for (let i = 0; i < NN; i++) { const k = hKey[i]; if (k >= 0) hSorted[hStart[k] + hFill[k]++] = i; }
    for (let a = 0; a < NN; a++) {
      if (!alive[a]) continue;
      const ax = P[a * 3], ay = P[a * 3 + 1], az = P[a * 3 + 2];
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
        const k = hk(CX[a] + dx, CY[a] + dy, CZ[a] + dz);
        for (let q = hStart[k], qe = hStart[k] + hCount[k]; q < qe; q++) {
          const b = hSorted[q]; if (b <= a) continue;
          const ex = P[b * 3] - ax, ey = P[b * 3 + 1] - ay, ez = P[b * 3 + 2] - az, dd = ex * ex + ey * ey + ez * ez;
          if (dd >= h2 || dd < 1e-14 || excl.has(a * NN + b)) continue;
          const wa = inv[a], wb = inv[b], ws = wa + wb; if (!ws) continue;
          const L = Math.sqrt(dd), corr = (h - L) / (L * ws);
          P[a * 3] -= wa * corr * ex; P[a * 3 + 1] -= wa * corr * ey; P[a * 3 + 2] -= wa * corr * ez;
          P[b * 3] += wb * corr * ex; P[b * 3 + 1] += wb * corr * ey; P[b * 3 + 2] += wb * corr * ez;
        }
      }
    }
  }
  function step(dt, iters) {
    const sub = 2, hdt = dt / sub, P = pos, Q = prev, g = gravity * hdt * hdt, vmax = RAD * 0.45;
    for (let s = 0; s < sub; s++) {
      for (let i = 0; i < NN; i++) {
        if (!alive[i]) continue;
        const a = i * 3;
        let vx = (P[a] - Q[a]) * 0.985, vy = (P[a + 1] - Q[a + 1]) * 0.985, vz = (P[a + 2] - Q[a + 2]) * 0.985;
        const vv = Math.sqrt(vx * vx + vy * vy + vz * vz);
        if (vv > vmax) { const f = vmax / vv; vx *= f; vy *= f; vz *= f; }
        Q[a] = P[a]; Q[a + 1] = P[a + 1]; Q[a + 2] = P[a + 2];
        if (!inv[i]) continue;
        P[a] += vx; P[a + 1] += vy; P[a + 2] += vz - g;
      }
      if (dragId >= 0) { const a = dragId * 3; P[a] = dragTarget[0]; P[a + 1] = dragTarget[1]; P[a + 2] = dragTarget[2]; }
      for (let it = 0; it < iters; it++) { solve(); if (it % 2 === 0) bend(); }
      if (s === sub - 1) collide();
      if (gravity > 0) {
        const fz = FLOOR + RAD;
        for (let i = 0; i < NN; i++) {
          const a = i * 3;
          if (alive[i] && P[a + 2] < fz) { P[a + 2] = fz; Q[a] += (P[a] - Q[a]) * 0.7; Q[a + 1] += (P[a + 1] - Q[a + 1]) * 0.7; if (Q[a + 2] < fz) Q[a + 2] = fz; }
        }
      }
    }
    let vmaxNow = 0;
    for (let i = 0; i < NN * 3; i++) { const d = Math.abs(P[i] - Q[i]); if (d > vmaxNow) vmaxNow = d; }
    calm = vmaxNow < 2.5e-5 ? calm + 1 : 0;
    if (calm > 45 && dragId < 0 && blend >= 1 && !st.cutting) asleep = true;
  }
  function wake() { asleep = false; calm = 0; }
  function recenter() {
    if (gravity > 0 || dragId >= 0) return;
    let x = 0, y = 0, z = 0, m = 0;
    for (let i = 0; i < NN; i++) if (alive[i]) { x += pos[i * 3]; y += pos[i * 3 + 1]; z += pos[i * 3 + 2]; m++; }
    if (!m) return;
    const f = 0.03 / m; x *= f; y *= f; z *= f;
    for (let i = 0; i < NN; i++) if (alive[i]) { pos[i * 3] -= x; pos[i * 3 + 1] -= y; pos[i * 3 + 2] -= z; prev[i * 3] -= x; prev[i * 3 + 1] -= y; prev[i * 3 + 2] -= z; }
  }
  function kick(strength) {
    for (let hh = 0; hh < 3; hh++) {
      let c = -1; for (let tries = 0; tries < 20 && c < 0; tries++) { const k = Math.floor(Math.random() * NN); if (alive[k]) c = k * 3; }
      if (c < 0) return;
      const jx = (Math.random() - 0.5) * strength, jy = (Math.random() - 0.5) * strength, jz = (Math.random() - 0.3) * strength;
      for (let i = 0; i < NN; i++) {
        if (!alive[i]) continue;
        const a = i * 3, d2 = (pos[a] - pos[c]) ** 2 + (pos[a + 1] - pos[c + 1]) ** 2 + (pos[a + 2] - pos[c + 2]) ** 2, f = Math.exp(-d2 / 0.5);
        prev[a] -= jx * f; prev[a + 1] -= jy * f; prev[a + 2] -= jz * f;
      }
    }
  }
  // "Pull apart": like holding the objects away from each other. Objects repel; each one is gently inflated.
  // Objects measured as unlinked get a firm pull so they visibly come apart; linked ones only a gentle one,
  // since paper pulled hard against paper can be forced through itself.
  function spread(push, inflate) {
    const r = st.res; if (!r) return;
    const no = r.objects.length, c = new Float64Array(no * 3), cnt = new Float64Array(no), f = new Float64Array(no * 3);
    for (let i = 0; i < NN; i++) if (alive[i]) { const o = objOfNode[i]; c[o * 3] += pos[i * 3]; c[o * 3 + 1] += pos[i * 3 + 1]; c[o * 3 + 2] += pos[i * 3 + 2]; cnt[o]++; }
    for (let o = 0; o < no; o++) if (cnt[o]) { c[o * 3] /= cnt[o]; c[o * 3 + 1] /= cnt[o]; c[o * 3 + 2] /= cnt[o]; }
    const g = st.geo && st.geo.olinks.length === no * (no - 1) / 2 ? st.geo.olinks : null;
    for (let p = 0; p < no; p++) for (let q = 0; q < no; q++) {
      if (p === q) continue;
      let dx = c[p * 3] - c[q * 3], dy = c[p * 3 + 1] - c[q * 3 + 1], dz = c[p * 3 + 2] - c[q * 3 + 2];
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 > 30) continue;   // far enough apart: let them come to rest
      if (d2 < 1e-4) { dx = (p - q) * 0.01; dz = 0.01; }
      const a = Math.min(p, q), b = Math.max(p, q), free = g && g[a * no - a * (a + 1) / 2 + b - a - 1] === 0;
      const k = (free ? FREE_PUSH : push) / (d2 + 0.3); f[p * 3] += dx * k; f[p * 3 + 1] += dy * k; f[p * 3 + 2] += dz * k;
    }
    for (let i = 0; i < NN; i++) {
      if (!alive[i] || !inv[i]) continue;
      const o = objOfNode[i];
      prev[i * 3] -= f[o * 3] + (pos[i * 3] - c[o * 3]) * inflate;
      prev[i * 3 + 1] -= f[o * 3 + 1] + (pos[i * 3 + 1] - c[o * 3 + 1]) * inflate;
      prev[i * 3 + 2] -= f[o * 3 + 2] + (pos[i * 3 + 2] - c[o * 3 + 2]) * inflate;
    }
  }

  /* ---------------- counting pieces, sides and edges ---------------- */
  // Faces are quads of point ids. Returns the Euler number, whether the faces can be given one consistent
  // side, whether it's a proper surface (no edge shared by three faces), and its free edges.
  function topo(faces, seed = 0) {
    const E = new Map(), V = new Set();
    faces.forEach((f, fi) => {
      for (let k = 0; k < 4; k++) {
        const a = f[k], b = f[(k + 1) & 3], key = ekey(a, b);
        V.add(a);
        let e = E.get(key); if (!e) E.set(key, e = { a: Math.min(a, b), b: Math.max(a, b), f: [] });
        e.f.push(fi, a < b ? 1 : -1);
      }
    });
    let manifold = true;
    const adj = faces.map(() => []), bnd = [];
    for (const e of E.values()) {
      if (e.f.length > 4) manifold = false;
      else if (e.f.length === 4) { const rel = -e.f[1] * e.f[3]; adj[e.f[0]].push(e.f[2], rel); adj[e.f[2]].push(e.f[0], rel); }
      else if (e.f.length === 2) bnd.push([e.a, e.b]);
    }
    // Spread one consistent side outward from the seed. On a one-sided surface the spreading
    // eventually meets itself flipped; that is where painting by sides shows a sharp line.
    const o = new Int8Array(faces.length); let orientable = true;
    for (const s0 of [seed, ...faces.keys()]) {
      if (s0 >= faces.length || o[s0]) continue;
      o[s0] = 1; const queue = [s0];
      for (let h = 0; h < queue.length; h++) {
        const f = queue[h], A = adj[f];
        for (let k = 0; k < A.length; k += 2) { const g = A[k], want = o[f] * A[k + 1]; if (!o[g]) { o[g] = want; queue.push(g); } else if (o[g] !== want) orientable = false; }
      }
    }
    const par = new Map(), find = x => { let r = x; while (par.get(r) !== r) r = par.get(r); while (par.get(x) !== r) { const nx = par.get(x); par.set(x, r); x = nx; } return r; };
    for (const [a, b] of bnd) { if (!par.has(a)) par.set(a, a); if (!par.has(b)) par.set(b, b); const ra = find(a), rb = find(b); if (ra !== rb) par.set(ra, rb); }
    const nB = new Set([...par.keys()].map(find)).size;
    return { chi: V.size - E.size + faces.length, orientable, manifold, bnd, nB, find, o };
  }
  function traceLoops(bnd) {
    const adj = new Map();
    for (const [a, b] of bnd) { if (!adj.has(a)) adj.set(a, []); if (!adj.has(b)) adj.set(b, []); adj.get(a).push(b); adj.get(b).push(a); }
    const seen = new Set(), loops = [];
    for (const v0 of adj.keys()) {
      if (seen.has(v0)) continue;
      const loop = [v0]; seen.add(v0);
      let from = -1, cur = v0;
      for (;;) {
        const nb = adj.get(cur), nxt = nb[0] !== from ? nb[0] : nb[1];
        if (nxt === undefined || seen.has(nxt)) break;
        loop.push(nxt); seen.add(nxt); from = cur; cur = nxt;
      }
      if (loop.length > 2) loops.push(loop);
    }
    return loops;
  }
  function regions(cells) {
    const set = new Set(cells), seen = new Set(); let k = 0;
    for (const c0 of cells) {
      if (seen.has(c0)) continue;
      k++; const stack = [c0]; seen.add(c0);
      while (stack.length) for (const d of neighbours(stack.pop())) if (set.has(d) && !seen.has(d)) { seen.add(d); stack.push(d); }
    }
    return k;
  }
  function analyze() {
    // pieces of paper: cells that are still joined to each other, within one loop
    const pieceOfCell = new Int32Array(NC).fill(-1), pieces = [];
    for (let c0 = 0; c0 < NC; c0++) {
      if (!active[c0] || pieceOfCell[c0] >= 0) continue;
      const id = pieces.length, cells = [c0]; pieceOfCell[c0] = id;
      for (let q = 0; q < cells.length; q++) for (const d of neighbours(cells[q])) if (active[d] && pieceOfCell[d] < 0) { pieceOfCell[d] = id; cells.push(d); }
      pieces.push({ s: c0 >= CPS ? 1 : 0, cells, id });
    }
    pieceOfNode.fill(-1);
    pieces.forEach(p => p.cells.forEach(c => corners(c).forEach(n => { pieceOfNode[n] = p.id; })));
    [0, 1].forEach(s => { const mine = pieces.filter(p => p.s === s); mine.forEach((p, k) => { p.name = 'AB'[s] + (mine.length > 1 ? k + 1 : ''); p.color = PAL[s][k % PAL[s].length]; }); });
    const side = new Int8Array(NC), cross = st.join === 'cross';
    const seedOf = cells => Math.max(0, cells.findIndex(c => linkCell[c] >= 0));
    pieces.forEach(p => {
      const t = topo(p.cells.map(corners), seedOf(p.cells));
      if (!cross) p.cells.forEach((c, k) => { side[c] = t.o[k]; });
      p.oneSided = !t.orientable; p.nB = t.nB; p.loops = traceLoops(t.bnd);
      let along = 0;
      for (const [a, b] of t.bnd) if ((((a % NPS) / NJ) | 0) !== (((b % NPS) / NJ) | 0)) along++;
      p.laps = Math.round(along / NI) / 2;
      p.kind = t.chi === 0 ? 'loop' : t.chi === 1 ? 'strip' : t.chi === -1 && t.nB === (t.orientable ? 3 : 2) ? 'slit' : 'other';
    });
    // objects: pieces held together by tape
    const par = pieces.map((_, i) => i), find = x => (par[x] === x ? x : (par[x] = find(par[x])));
    const contact = new Map();
    for (let c = 0; c < CPS; c++) {
      const o = linkCell[c]; if (o < 0 || !active[c] || !active[o]) continue;
      const p = pieceOfCell[c], q = pieceOfCell[o];
      par[find(p)] = find(q);
      const key = p * 64 + q; if (!contact.has(key)) contact.set(key, []); contact.get(key).push(c);
    }
    for (const [a, b] of tapePairs) if (alive[a] && alive[b]) par[find(pieceOfNode[a])] = find(pieceOfNode[b]);
    const taped = [...contact.entries()].map(([key, cells]) => ({ p: Math.floor(key / 64), q: key % 64, places: regions(cells) }));
    const roots = [...new Set(pieces.map((_, i) => find(i)))];
    const objects = roots.map(rt => ({ pieces: pieces.filter((_, i) => find(i) === rt) }));
    objects.forEach((o, k) => o.pieces.forEach(p => { p.obj = k; }));
    objOfNode.fill(0);
    for (let i = 0; i < NN; i++) if (pieceOfNode[i] >= 0) objOfNode[i] = pieces[pieceOfNode[i]].obj;
    // each object as one glued surface: a taped pair of cells counts once, and taped points are one point
    const vid = n => (n >= NPS && tapeOf[n] >= 0 ? tapeOf[n] : n);
    markOf.fill(-1); let mark = 0;   // per cell: the marker color of the free edge it runs along
    objects.forEach(o => {
      const faces = [], owner = [];
      o.pieces.forEach(p => p.cells.forEach(c => { if (c >= CPS && linkCell[c] >= 0 && active[linkCell[c]]) return; faces.push(corners(c).map(vid)); owner.push(c); }));
      const t = topo(faces, seedOf(owner));
      o.chi = t.chi; o.manifold = t.manifold; o.oneSided = t.manifold ? !t.orientable : null; o.nB = t.nB;
      o.loops = t.manifold ? traceLoops(t.bnd) : [];
      // crosswise tape fuses the layers into one sheet, so sides are the glued surface's sides
      // (B's frame is mirrored against A's there); face to face, each piece keeps its own two sides
      if (cross) owner.forEach((c, k) => { side[c] = t.o[k]; const b = linkCell[c]; if (c < CPS && b >= 0 && active[b]) side[b] = -t.o[k]; });
      // mark each free edge in its own color: the row of cells along it, on both layers where it runs along the tape
      const comp = new Map(), free = new Map();
      for (const [a, b] of t.bnd) { const rt = t.find(a); if (!comp.has(rt)) comp.set(rt, mark++); free.set(ekey(a, b), comp.get(rt)); }
      o.pieces.forEach(p => p.cells.forEach(c => {
        const q = corners(c).map(vid);
        for (let k = 0; k < 4; k++) { const m = free.get(ekey(q[k], q[(k + 1) & 3])); if (m !== undefined) { markOf[c] = m; if (linkCell[c] >= 0) markOf[linkCell[c]] = m; break; } }
      }));
    });
    return { pieces, objects, taped, side };
  }
  // Twists and links, measured from where the simulated paper actually is.
  function measureGeo() {
    const r = st.res, lk = (a, b) => Math.abs(Lab.linking(a.map(pt), b.map(pt)));
    const twist = r.pieces.map(p => (p.kind === 'loop' && !p.oneSided && p.loops.length === 2 ? lk(p.loops[0], p.loops[1]) : null));
    // a closed band glued from several pieces: its twist is how often its two edges wind round each other
    const otwist = r.objects.map(o => (o.manifold && o.chi === 0 && !o.oneSided && o.pieces.length > 1 && o.loops.length === 2 ? lk(o.loops[0], o.loops[1]) : null));
    const outline = o => (o.manifold ? o.loops : o.pieces.filter(p => p.kind === 'loop').map(p => p.loops[0]));
    const olinks = [];
    for (let a = 0; a < r.objects.length; a++) for (let b = a + 1; b < r.objects.length; b++) {
      let m = 0; for (const l1 of outline(r.objects[a])) for (const l2 of outline(r.objects[b])) m = Math.max(m, lk(l1, l2));
      olinks.push(m);
    }
    const links = [];
    for (let a = 0; a < r.pieces.length; a++) for (let b = a + 1; b < r.pieces.length; b++) {
      const P = r.pieces[a], Q = r.pieces[b];
      if (P.kind !== 'loop' || Q.kind !== 'loop' || !P.loops.length || !Q.loops.length) { links.push(0); continue; }
      links.push(lk(P.loops[0], Q.loops[0]));
    }
    return { twist, otwist, links, olinks };
  }
  const sameArr = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
  const sameGeo = (a, b) => !!(a && b) && ['twist', 'otwist', 'links', 'olinks'].every(k => sameArr(a[k], b[k]));

  /* ---------------- describing ---------------- */
  function shapeName(p) {
    if (p.kind === 'loop') return `${p.oneSided ? 'one-sided' : 'two-sided'} loop`;
    if (p.kind === 'strip') return 'strip with two ends';
    if (p.kind === 'slit') return `${p.oneSided ? 'one-sided' : 'two-sided'} loop with a slit`;
    return `piece with ${p.nB} edges`;
  }
  const lengthText = p => (p.kind === 'strip' ? `${p.laps === 1 ? 'one' : p.laps} lap long` : p.laps === 1 ? 'one lap' : p.laps === 2 ? 'twice as long' : `${p.laps} laps`);
  const article = s => (/^(?!one)[aeiou]/i.test(s) ? 'an ' : 'a ') + s;
  function pieceText(p) {
    if (p.kind === 'loop') return `${article(shapeName(p))}${p.laps === 2 ? ' twice as long' : ''}`;
    return article(shapeName(p));
  }
  function objectText(o, r, k) {
    const ps = o.pieces;
    let s;
    if (ps.length === 1) s = `${ps[0].name}, ${pieceText(ps[0])}, on its own.`;
    else {
      const links = r.taped.filter(t => ps.includes(r.pieces[t.p]));
      const names = ps.map(p => `${p.name}, ${pieceText(p)}`);
      const list = names.length === 2 ? names.join(', and ') : names.slice(0, -1).join('; ') + '; and ' + names[names.length - 1];
      const ring = ps.length > 2 && links.length === ps.length && ps.every(p => links.filter(t => t.p === p.id || t.q === p.id).length === 2);
      const places = links.reduce((a, t) => a + t.places, 0);
      s = ps.length === 2 ? `${list}, taped together${places > 1 ? ` in ${places} places` : ''}.` : `${list}${ring ? ', taped end to end in a ring' : ', taped together'}.`;
    }
    const tw = st.geo && st.geo.otwist[k];
    if (o.manifold) s += ` As one surface it is ${o.oneSided ? '<b>one-sided</b>' : 'two-sided'}, with ${o.nB} edge${o.nB === 1 ? '' : 's'}${o.chi === 0 && ps.length > 1 ? `: one closed band${tw == null ? '' : tw === 0 ? ' with no twist' : ` with ${tw} full twist${tw > 1 ? 's' : ''}`}` : ''}.`;
    else s += ' Where it is taped face to face it is two layers, so sides belong to each piece, listed in the table.';
    return s;
  }
  function describe(r) {
    const k = r.objects.length;
    let s = k === 1 ? '1 object: ' + objectText(r.objects[0], r, 0) : `${k} separate objects. ` + r.objects.map((o, i) => `(${i + 1}) ${objectText(o, r, i)}`).join(' ');
    if (k > 1 && st.geo) {
      const linked = st.geo.olinks.filter(v => v > 0).length;
      s += linked ? (k === 2 ? ` The two are linked ${st.geo.olinks[0]}×, so they can't be pulled apart.` : ` ${linked} pairs of them are linked.`) : (k === 2 ? ' They are not linked, so they come apart.' : ' None of them are linked, so they all come apart.');
    }
    if (st.history.length && (nOf(0) % 2 || nOf(1) % 2) && !r.pieces.some(p => p.oneSided)) {
      s += r.objects.some(o => o.oneSided) ? ' Every piece of paper is two-sided on its own; the tape is what keeps the whole thing one-sided.' : ' No one-sided piece of paper is left.';
    }
    return s;
  }
  function renderReadout() {
    const r = st.res; if (!r || !readout) return;
    if (st.cutting) { readout.innerHTML = `<h4>Result</h4><p style="margin:0;color:var(--muted)">Cutting ${st.cutting.sheet} down its middle…</p>`; return; }
    const g = st.geo, k = r.pieces.length;
    let li = 0; const linkOf = {};
    for (let a = 0; a < k; a++) for (let b = a + 1; b < k; b++) { const v = g ? g.links[li] : 0; li++; if (v) { (linkOf[a] = linkOf[a] || []).push(`${r.pieces[b].name} (${v}×)`); (linkOf[b] = linkOf[b] || []).push(`${r.pieces[a].name} (${v}×)`); } }
    const rows = r.pieces.map((p, i) => {
      const tw = !g || g.twist[i] == null ? '–' : g.twist[i] === 0 ? 'no twist' : `${g.twist[i]} full twist${g.twist[i] > 1 ? 's' : ''}`;
      const taped = r.taped.filter(t => t.p === i || t.q === i).map(t => `${r.pieces[t.p === i ? t.q : t.p].name}${t.places > 1 ? ` (${t.places}×)` : ''}`);
      return `<tr><td><span class="swatch" style="background:${p.color}"></span>${p.name}</td><td>${shapeName(p)}</td><td>${p.oneSided ? '<b>one</b>' : 'two'}</td>
        <td>${lengthText(p)}</td><td>${tw}</td><td>${taped.join(', ') || '–'}</td><td>${(linkOf[i] || []).join(', ') || '–'}</td></tr>`;
    }).join('');
    const ver = !g ? '<span style="color:var(--muted)">measuring the simulated paper…</span>'
      : st.geoOk === false ? '<span class="miss">⚠</span> The simulated paper slipped through itself, which real paper can\'t do. Press Reset and try again.'
        : '<span class="ok">✓</span> Twists and links measured from the simulated paper, and re-checked every two seconds.';
    const head = st.history.length ? `After cutting ${st.history.join(', then ')}` : 'Before cutting';
    readout.innerHTML = `<h4>${head}</h4><p style="margin:0 0 8px">${describe(r)}</p>
      <div class="tbl-wrap"><table class="pieces"><thead><tr><th>Piece</th><th>Shape</th><th>Sides</th><th>Length</th><th>Twist</th><th>Taped to</th><th>Linked with</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="verdict-line" style="font-size:.875rem">${ver}</p>
      <p class="verdict-line" style="font-size:.8125rem;color:var(--muted)">${st.paint === 'sides'
        ? `Painted by side: blue on one face, orange on the other, spreading out from the tape without crossing an edge. ${st.join === 'cross' ? 'Crosswise tape fuses the two layers, so paint carries across it.' : 'Face to face, each piece is painted on its own.'} On a one-sided surface the paint comes back around onto the other face, so somewhere blue has to meet orange along a sharp line.`
        : 'Pink pieces came from loop A, blue-green from loop B. The paler patch is the tape.'} ${st.marks ? 'Each separate edge is marked in its own dark color.' : ''} Drag a piece to pull it around.</p>`;
  }

  /* ---------------- your notebook, re-run ---------------- */
  const CHECKS = [
    { key: 'square', label: 'The classic: two plain loops taped crosswise, both cut', setup: 'plain A × plain B, crosswise · cut A, then B', A: 'plain', B: 'plain', join: 'cross', cuts: ['A', 'B'],
      test: r => r.objects.length === 1 && r.objects[0].chi === 0 && r.objects[0].oneSided === false, hit: 'One closed two-sided band: the square frame.' },
    { key: 'step1', quote: 'Mobius + |x| simple (non mobius!) cross cut. Step 1: looks like infinity + arrow', setup: 'our reading: Möbius A taped crosswise to plain loop B · cut A', A: 'left', B: 'plain', join: 'cross', cuts: ['A'],
      test: r => r.objects.length === 1 && r.pieces.some(p => p.kind === 'loop' && p.laps === 2) && r.pieces.some(p => p.kind === 'strip'),
      hit: 'The long loop is your infinity, and plain loop B, cut open by the scissors going through the tape, is the strap across it: your arrow.' },
    { key: 'step2', quote: 'Step2: looks like a skull in a box or a frog in a box', setup: 'the same, then cut B too', A: 'left', B: 'plain', join: 'cross', cuts: ['A', 'B'],
      test: r => r.objects.length === 1 && r.objects[0].chi === 0, hit: 'Everything is one closed band, so “box” fits. Whether it looks like a skull or a frog depends on how it lies.' },
    { key: 'butterfly', quote: 'Left + right mobius taped parallel overlapped = butterfly. Butterfly + half cut = … the tape is holding the sides together … Infinity (non mobius) + nested loop (non mobius)… mobius didn\'t stay together', setup: 'left and right Möbius loops, face to face · cut A, then B', A: 'left', B: 'right', join: 'par', cuts: ['A', 'B'],
      test: r => r.objects.length === 1 && r.pieces.length === 2 && r.pieces.every(p => p.kind === 'loop' && !p.oneSided), hit: 'Two two-sided loops held together only by the tape, and nothing one-sided is left.' }
  ];
  function renderNotebook() {
    if (!notebook) return;
    const rows = CHECKS.map(c => {
      const r = st.checks[c.key] || {};
      let res = '';
      if (r.state === 'running') res = '<span style="color:var(--muted)">Taping and cutting… watch the stage.</span>';
      else if (r.state === 'yes') res = `<span class="ok">✓ Matches.</span> ${c.hit} Simulated: ${r.text}`;
      else if (r.state === 'no') res = `<span class="miss">✗ Doesn't match.</span> Simulated: ${r.text}`;
      return `<li><span class="nb-q">${c.quote ? `“${c.quote}”` : c.label}</span><button type="button" class="btn" data-check="${c.key}" id="t-check-${c.key}"${r.state === 'running' ? ' disabled' : ''}>${r.state && r.state !== 'running' ? 'Run again' : 'Run it'}</button>
        <span class="nb-setup">${c.setup}</span><p class="nb-res">${res}</p></li>`;
    }).join('');
    notebook.innerHTML = `<h4>Your notebook, re-run</h4>
      <p class="cap">Taped constructions from your notes. Run one and the simulation builds it, cuts it the same way, and checks what your notes say.</p>
      <ol class="nb-list">${rows}</ol>`;
  }
  function cancelScript() {
    if (!st.script) return;
    const k = st.script.c.key;
    if (st.checks[k] && st.checks[k].state === 'running') delete st.checks[k];
    st.script = null; renderNotebook();
  }
  function runCheck(key) {
    const c = CHECKS.find(x => x.key === key); if (!c) return;
    cancelScript();
    st.A = c.A; st.B = c.B; st.join = c.join;
    ctl.A.set(c.A); ctl.B.set(c.B); ctl.join.set(c.join);
    reset();
    st.checks[key] = { state: 'running' }; st.script = { c, k: 0 };
    renderNotebook();
    const nav = document.querySelector('.nav'), top = ch.stage.getBoundingClientRect().top + window.scrollY - (nav ? nav.offsetHeight : 0) - 10;
    if (Math.abs(window.scrollY - top) > 40) window.scrollTo({ top, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }
  function tickScript() {
    const S = st.script;
    if (!S || st.cutting || st.t < 2.4 || st.tCut < (S.k ? 2.2 : 0)) return;
    if (S.k < S.c.cuts.length) { if (!startCut(S.c.cuts[S.k])) { cancelScript(); return; } S.k++; return; }
    if (st.tCut < 3 || !st.geo) return;
    st.script = null;
    const ok = S.c.test(st.res);
    st.checks[S.c.key] = { state: ok ? 'yes' : 'no', text: describe(st.res).replace(/<\/?b>/g, '') };
    renderNotebook();
    Lab.toast(ch.stage, ok ? '✓ Your notes match the simulated paper.' : '✗ The simulated paper disagrees with your notes.', 2800);
  }

  /* ---------------- cutting ---------------- */
  function startCut(sheet) {
    if (st.cutting || st.done[sheet]) return false;
    onUp();
    st.cutting = { s: sheet === 'A' ? 0 : 1, sheet, k: 0, f: 0 };
    st.userCam = false; st.geo = null; st.geoOk = null; wake();
    if (sprite) sprite.visible = true;
    if (hud.right) hud.right.textContent = `Scissors: down the middle of ${sheet}`;
    renderReadout(); syncButtons();
    return true;
  }
  function stepCut(dt) {
    const C = st.cutting; C.f += dt * CUT_SPEED;
    let changed = false;
    while (C.k < NI && C.k < C.f) {
      const c = cellAt(C.s, C.k, MID), o = linkCell[c];
      if (active[c]) { active[c] = 0; changed = true; }
      if (o >= 0 && active[o]) { active[o] = 0; changed = true; }   // through the tape: both layers
      C.k++;
    }
    if (changed) { rebuild(); updateIndex(); wake(); }
    if (changed && (st.t - st.lastAnalyze > 0.2 || C.k >= NI)) { st.lastAnalyze = st.t; st.res = analyze(); paint(); }
    const cs = corners(cellAt(C.s, Math.min(NI - 1, C.k), MID));
    if (sprite) sprite.position.set(...[0, 1, 2].map(k => cs.reduce((a, n) => a + pos[n * 3 + k], 0) / 4));
    if (C.k >= NI) {
      st.cutting = null; if (sprite) sprite.visible = false;
      st.done[C.sheet] = true; st.history.push(C.sheet); st.tCut = 0; st.autoJig = false;
      st.res = analyze(); paint(); setHud();
      renderReadout(); syncButtons();
    }
  }
  function hudText() {
    const a = loopOf(st.A), b = loopOf(st.B);
    let t = `A: <b>${a.label}</b> · B: <b>${b.label}</b> · ${st.join === 'cross' ? 'crosswise' : 'face to face'}`;
    if (st.history.length) t += ` · cut <b>${st.history.join(', ')}</b>`;
    return t;
  }
  const plural = (n, w) => `${n} ${w}${n === 1 ? '' : 's'}`;
  function setHud() {
    if (!hud.top) return;
    hud.top.innerHTML = hudText();
    hud.right.textContent = `${plural(st.res.objects.length, 'object')} · ${plural(st.res.pieces.length, 'piece')}`;
  }
  function syncButtons() {
    if (!btn.cutA) return;
    btn.cutA.disabled = !!st.cutting || st.done.A;
    btn.cutB.disabled = !!st.cutting || st.done.B;
  }
  function reset() {
    onUp();
    active.fill(1); st.cutting = null; st.done = { A: false, B: false }; st.history = [];
    st.t = 0; st.tCut = 0; st.autoJig = true; st.jiggle = 0; st.geo = null; st.geoOk = null; st.userCam = false;
    blend = 0; place(); setupTape(); rebuild(); setBlend(0, true);
    st.res = analyze();
    if (meshes.length) { updateIndex(); paint(); syncMeshes(); }
    gravity = st.desk ? 24 : 0; wake();
    if (sprite) sprite.visible = false;
    setHud(); renderReadout(); syncButtons();
  }

  /* ---------------- drawing ---------------- */
  // Each loop is drawn from a hidden grid (for smooth normals) copied into four corners per cell,
  // so a cell can be painted by its own side. Front and back share everything except color.
  function makeSheetMesh(s) {
    const grid = new THREE.BufferGeometry();
    grid.setAttribute('position', new THREE.BufferAttribute(new Float32Array((NI + 1) * NJ * 3), 3));
    const nv = CPS * 4, geoF = new THREE.BufferGeometry(), geoB = new THREE.BufferGeometry();
    const P = new THREE.BufferAttribute(new Float32Array(nv * 3), 3), N = new THREE.BufferAttribute(new Float32Array(nv * 3), 3), U = new THREE.BufferAttribute(new Float32Array(nv * 2), 2);
    for (let i = 0; i < NI; i++) for (let v = 0; v < ROWS; v++) CORNER.forEach(([di, dv], k) => { const q = ((i * ROWS + v) * 4 + k) * 2; U.array[q] = (i + di) * H / (W * 1.6); U.array[q + 1] = (v + dv) / ROWS; });
    [geoF, geoB].forEach(g => { g.setAttribute('position', P); g.setAttribute('normal', N); g.setAttribute('uv', U); g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(nv * 3), 3)); });
    const front = new THREE.Mesh(geoF, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(true, '#ffffff', 'tape-white'), roughness: 0.88, side: THREE.FrontSide, vertexColors: true }));
    const back = new THREE.Mesh(geoB, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(false, '#ffffff', 'tape-white'), roughness: 0.88, side: THREE.BackSide, vertexColors: true }));
    const group = new THREE.Group(); group.add(front, back);
    return { s, grid, geoF, geoB, front, back, group };
  }
  function updateIndex() {
    meshes.forEach(m => {
      const gi = [], ri = [];
      for (let i = 0; i < NI; i++) for (let v = 0; v < ROWS; v++) if (active[m.s * CPS + i * ROWS + v]) {
        const a = i * NJ + v, b = (i + 1) * NJ + v, q = (i * ROWS + v) * 4;
        gi.push(a, b, a + 1, b, b + 1, a + 1); ri.push(q, q + 1, q + 3, q + 1, q + 2, q + 3);
      }
      m.grid.setIndex(gi); m.geoF.setIndex(ri); m.geoB.setIndex(ri);
    });
  }
  function syncMeshes() {
    meshes.forEach(m => {
      const g = m.grid.getAttribute('position').array;
      for (let i = 0; i <= NI; i++) for (let j = 0; j < NJ; j++) { const id = node(m.s, i, j) * 3, v = (i * NJ + j) * 3; g[v] = pos[id]; g[v + 1] = pos[id + 1]; g[v + 2] = pos[id + 2]; }
      m.grid.getAttribute('position').needsUpdate = true;
      m.grid.computeVertexNormals();
      const gn = m.grid.getAttribute('normal').array, P = m.geoF.getAttribute('position'), N = m.geoF.getAttribute('normal');
      for (let i = 0; i < NI; i++) for (let v = 0; v < ROWS; v++) {
        if (!active[m.s * CPS + i * ROWS + v]) continue;
        const q = (i * ROWS + v) * 4;
        for (let k = 0; k < 4; k++) {
          const gv = ((i + CORNER[k][0]) * NJ + v + CORNER[k][1]) * 3, o = (q + k) * 3;
          P.array[o] = g[gv]; P.array[o + 1] = g[gv + 1]; P.array[o + 2] = g[gv + 2];
          N.array[o] = gn[gv]; N.array[o + 1] = gn[gv + 1]; N.array[o + 2] = gn[gv + 2];
        }
      }
      P.needsUpdate = true; N.needsUpdate = true;
      m.geoF.computeBoundingSphere(); m.geoB.boundingSphere = m.geoF.boundingSphere;
    });
  }
  const linCol = hex => new THREE.Color(hex).convertSRGBToLinear();
  function paint() {
    const r = st.res; if (!r || !meshes.length) return;
    const white = linCol('#ffffff'), pc = r.pieces.map(p => linCol(p.color)), mk = MARKS.map(linCol), sd = SIDES.map(linCol);
    meshes.forEach(m => {
      const F = m.geoF.getAttribute('color').array, B = m.geoB.getAttribute('color').array;
      for (let i = 0; i < NI; i++) for (let v = 0; v < ROWS; v++) {
        const c = m.s * CPS + i * ROWS + v; if (!active[c]) continue;
        const q = (i * ROWS + v) * 4, o = r.side[c] >= 0 ? 0 : 1;
        for (let k = 0; k < 4; k++) {
          const n = node(m.s, i + CORNER[k][0], v + CORNER[k][1]);
          let f, b;
          if (st.paint === 'sides') { f = sd[o]; b = sd[1 - o]; }
          else { f = pc[pieceOfNode[n]].clone(); if (onTape[n] && tapeOf[n] >= 0) f.lerp(white, 0.42); b = f; }
          if (st.marks && markOf[c] >= 0) f = b = mk[markOf[c] % mk.length];
          const x = (q + k) * 3;
          F[x] = f.r; F[x + 1] = f.g; F[x + 2] = f.b; B[x] = b.r; B[x + 1] = b.g; B[x + 2] = b.b;
        }
      }
      m.geoF.getAttribute('color').needsUpdate = true; m.geoB.getAttribute('color').needsUpdate = true;
    });
  }

  /* ---------------- dragging pieces ---------------- */
  let ray = null, ndc = null, dragPlane = null;
  function pointerNDC(ev) { const r = Lab.getRenderer().domElement.getBoundingClientRect(); ndc.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1); }
  function onDown(ev) {
    if (Lab.active !== ch || st.cutting) return;
    pointerNDC(ev); ray.setFromCamera(ndc, ch.camera);
    const hits = ray.intersectObjects(meshes.flatMap(m => [m.front, m.back]), false);
    if (!hits.length) return;
    const hp = hits[0].point;
    let best = -1, bd = Infinity;
    for (let i = 0; i < NN; i++) { if (!alive[i]) continue; const d = (pos[i * 3] - hp.x) ** 2 + (pos[i * 3 + 1] - hp.y) ** 2 + (pos[i * 3 + 2] - hp.z) ** 2; if (d < bd) { bd = d; best = i; } }
    if (best < 0) return;
    ev.stopImmediatePropagation(); ev.preventDefault();
    dragId = best; inv[best] = 0; wake();
    dragTarget = pt(best);
    dragPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(ch.camera.getWorldDirection(new THREE.Vector3()).negate(), hp.clone());
    ch.controls.enabled = false;
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp, { once: true });
    window.addEventListener('pointercancel', onUp, { once: true });
  }
  function onMove(ev) {
    if (dragId < 0) return;
    pointerNDC(ev); ray.setFromCamera(ndc, ch.camera);
    const p = new THREE.Vector3();
    if (ray.ray.intersectPlane(dragPlane, p)) { const lim = 4; dragTarget = [Lab.clamp(p.x, -lim, lim), Lab.clamp(p.y, -lim, lim), Lab.clamp(p.z, FLOOR + 0.05, lim)]; }
  }
  function onUp() {
    window.removeEventListener('pointermove', onMove);
    if (dragId >= 0) { inv[dragId] = alive[dragId] ? 1 : 0; dragId = -1; st.verifyT = 0.6; }
    if (Lab.active === ch && ch.controls) ch.controls.enabled = true;
  }
  // Keep everything in view until the person takes over the camera.
  function fitCamera(dt) {
    let cx = 0, cy = 0, cz = 0, m = 0;
    for (let i = 0; i < NN; i++) if (alive[i]) { cx += pos[i * 3]; cy += pos[i * 3 + 1]; cz += pos[i * 3 + 2]; m++; }
    if (!m) return;
    cx /= m; cy /= m; cz /= m;
    let r2 = 0; for (let i = 0; i < NN; i += 3) if (alive[i]) { const d = (pos[i * 3] - cx) ** 2 + (pos[i * 3 + 1] - cy) ** 2 + (pos[i * 3 + 2] - cz) ** 2; if (d > r2) r2 = d; }
    const cam = ch.camera, half = THREE.MathUtils.degToRad(cam.fov / 2), hfov = Math.atan(Math.tan(half) * cam.aspect);
    const want = Math.max(4.6, Math.sqrt(r2) / Math.sin(Math.min(half, hfov)) * 1.06);
    const tgt = ch.controls.target, k = Math.min(1, dt * 1.5);
    tgt.x += (cx - tgt.x) * k; tgt.y += (cy - tgt.y) * k; tgt.z += (cz - tgt.z) * k;
    const dir = cam.position.clone().sub(tgt), d = dir.length();
    cam.position.copy(tgt).add(dir.multiplyScalar((d + (want - d) * k) / d));
  }

  /* ---------------- init ---------------- */
  const POSE = [[5.4, -6.0, 2.2], [0, 0, 0]];
  ch.init = function (section, stage) {
    ray = new THREE.Raycaster(); ndc = new THREE.Vector2();
    const { scene, camera, controls } = Lab.makeScene({ pos: POSE[0] });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    controls.addEventListener('start', () => { st.userCam = true; });
    const wood = Lab.woodTexture().clone(); wood.needsUpdate = true; wood.repeat.set(2, 2);
    deskMesh = new THREE.Mesh(new THREE.PlaneGeometry(14, 14), new THREE.MeshStandardMaterial({ map: wood, roughness: 0.92 }));
    deskMesh.position.z = FLOOR; deskMesh.visible = false; scene.add(deskMesh);
    meshes = [makeSheetMesh(0), makeSheetMesh(1)];
    meshes.forEach(m => scene.add(m.group));
    sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: Lab.scissorsTexture(), depthTest: false, transparent: true }));
    sprite.scale.set(0.3, 0.3, 1); sprite.renderOrder = 10; sprite.visible = false; scene.add(sprite);

    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.top = Lab.el('div', { class: 'chip' }); hud.right = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.top, hud.right);
    const bottom = Lab.el('div', { class: 'hud hud-bottom' });
    bottom.append(Lab.el('div', { class: 'chip', text: 'Drag a piece to pull it. Drag empty space to turn the view.' }));
    stage.append(hud.wrap, bottom);

    const c = section.querySelector('[data-controls]');
    const loopOpts = LOOPS.map(l => ({ value: l.value, label: l.label }));
    ctl.A = Lab.ui.seg(c, { label: 'Loop A (pink, on top)', id: 't-a', value: st.A, options: loopOpts, onChange: v => { cancelScript(); st.A = v; reset(); } });
    ctl.B = Lab.ui.seg(c, { label: 'Loop B (blue-green, underneath)', id: 't-b', value: st.B, options: loopOpts, onChange: v => { cancelScript(); st.B = v; reset(); } });
    ctl.join = Lab.ui.seg(c, { label: 'Tape them', id: 't-join', value: st.join, options: [{ value: 'cross', label: 'Crosswise |X|' }, { value: 'par', label: 'Face to face (butterfly)' }], onChange: v => { cancelScript(); st.join = v; reset(); } });
    const row = Lab.ui.row(Lab.ui.group(c, 'Do it'));
    btn.cutA = Lab.ui.button(row, { label: '✂ Cut A down the middle', id: 't-cuta', primary: true, onClick: () => { cancelScript(); startCut('A'); } });
    btn.cutB = Lab.ui.button(row, { label: '✂ Cut B down the middle', id: 't-cutb', onClick: () => { cancelScript(); startCut('B'); } });
    Lab.ui.button(row, { label: 'Jiggle', id: 't-jiggle', onClick: () => { st.jiggle = 0.9; st.verifyT = 1.6; wake(); } });
    Lab.ui.button(row, { label: 'Reset', id: 't-reset', onClick: () => { cancelScript(); reset(); Lab.tweenCamera(ch, ...POSE); } });
    Lab.ui.seg(c, { label: 'Hands', id: 't-desk', value: 'apart', options: [{ value: 'apart', label: 'Pull apart' }, { value: 'off', label: 'Let it float' }, { value: 'on', label: 'Drop on desk' }],
      onChange: v => { st.mode = v; st.desk = v === 'on'; gravity = st.desk ? 24 : 0; deskMesh.visible = st.desk; st.verifyT = 2.5; wake(); } });
    Lab.ui.seg(c, { label: 'Paint', id: 't-paint', value: st.paint, options: [{ value: 'pieces', label: 'By piece' }, { value: 'sides', label: 'By side' }], onChange: v => { st.paint = v; paint(); renderReadout(); } });
    Lab.ui.seg(c, { label: 'Edges', id: 't-marks', value: 'on', options: [{ value: 'on', label: 'Marked' }, { value: 'off', label: 'Plain' }], onChange: v => { st.marks = v === 'on'; paint(); renderReadout(); } });

    readout = section.querySelector('[data-readout]');
    notebook = section.querySelector('[data-notebook]');
    if (notebook) notebook.addEventListener('click', ev => { const b = ev.target.closest('[data-check]'); if (b && !b.disabled) runCheck(b.dataset.check); });
    const cv = Lab.getRenderer().domElement;
    cv.addEventListener('pointerdown', onDown, { capture: true });
    cv.addEventListener('touchstart', ev => { if (Lab.active === ch && dragId >= 0) ev.stopImmediatePropagation(); }, { capture: true, passive: true });
    reset(); renderNotebook();
  };

  ch.frame = function (dt) {
    if (!Lab.stepTween(ch, dt)) ch.controls.update();
    st.t += dt; st.tCut += dt;
    setBlend(Lab.smooth(Math.min(1, st.t / 2.2)));
    if (st.cutting) stepCut(dt);
    if (!st.autoJig && st.tCut > 0.8 && !st.cutting) { st.autoJig = true; if (st.mode !== 'on') st.jiggle = 0.4; }
    if (st.jiggle > 0) { wake(); kick(0.016 * st.jiggle); st.jiggle = Math.max(0, st.jiggle - dt); }
    if (dragId >= 0) wake();
    if (st.mode === 'apart' && st.t > 2.4 && !asleep) spread(SPREAD_PUSH, SPREAD_INFLATE);
    if (!asleep) { step(Math.min(dt, 1 / 30), blend < 1 ? 6 : 4); recenter(); syncMeshes(); }
    if (!st.userCam && !ch._tween) fitCamera(dt);
    // twists and links: measure once things settle, then keep re-checking
    st.verifyT -= dt;
    if (!st.cutting && st.t > 2.6 && st.tCut > 1.5 && st.jiggle <= 0 && dragId < 0 && st.verifyT <= 0) {
      st.verifyT = 2;
      const g = measureGeo();
      if (!st.geo) { st.geo = g; st.geoOk = true; renderReadout(); }
      else { const ok = sameGeo(st.geo, g); if (ok !== st.geoOk) { st.geoOk = ok; renderReadout(); } }
    }
    tickScript();
  };
  ch.leave = function () { onUp(); };

  Lab.register(ch);
}
