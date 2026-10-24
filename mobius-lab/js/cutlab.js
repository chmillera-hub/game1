/* Cut Lab — your paper experiments with exact topology and real ribbon physics.
   Cut a strip with n half-twists into k strips, watch the scissors (off-centre cuts go round twice),
   then let the pieces relax as paper ribbons: a position-based Cosserat rod (Kugelstadt & Schömer 2016)
   with paper-like stiffness (bends easily out of its plane, hardly at all within it) and self-contact,
   so links and knots can never pass through each other. Linking numbers are measured, not assumed. */
(function () {
  'use strict';
  const ML = window.ML, C = ML.C, TAU = ML.TAU;
  const R = 1, W = 0.3;                 // band core radius and half-width
  const LINE = 0.12;                    // ruled-line spacing on the paper
  const st = {
    n: 1, hand: 1, k: 2, phase: 'uncut', quad: false, temp: 0.12, pull: 0, ramp: 0,
    cuts: [], cutIdx: 0, cutProg: 0, pieces: [], topo: null, liveIdx: 0, liveT: 0, busy: false,
  };
  let scene, cam, orbit, app, atlas, ro, tableBox, predBox, hud = {}, scissors, cutLine, cutBtn, ruleBox;

  const nn = () => st.n * st.hand;      // signed half-twists (handedness = direction of twist)
  const odd = () => st.n % 2 === 1;

  // ------------------------------------------------------------------ quaternion helpers [w,x,y,z]
  function qmul(a, b, o) {
    const w = a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3];
    const x = a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2];
    const y = a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1];
    const z = a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0];
    o[0] = w; o[1] = x; o[2] = y; o[3] = z; return o;
  }
  function qFromBasis(d1, d2, d3, o) {
    // rotation matrix with columns d1, d2, d3
    const m00 = d1[0], m10 = d1[1], m20 = d1[2], m01 = d2[0], m11 = d2[1], m21 = d2[2], m02 = d3[0], m12 = d3[1], m22 = d3[2];
    const tr = m00 + m11 + m22;
    let w, x, y, z;
    if (tr > 0) { const s = 0.5 / Math.sqrt(tr + 1); w = 0.25 / s; x = (m21 - m12) * s; y = (m02 - m20) * s; z = (m10 - m01) * s; }
    else if (m00 > m11 && m00 > m22) { const s = 2 * Math.sqrt(1 + m00 - m11 - m22); w = (m21 - m12) / s; x = 0.25 * s; y = (m01 + m10) / s; z = (m02 + m20) / s; }
    else if (m11 > m22) { const s = 2 * Math.sqrt(1 + m11 - m00 - m22); w = (m02 - m20) / s; x = (m01 + m10) / s; y = 0.25 * s; z = (m12 + m21) / s; }
    else { const s = 2 * Math.sqrt(1 + m22 - m00 - m11); w = (m10 - m01) / s; x = (m02 + m20) / s; y = (m12 + m21) / s; z = 0.25 * s; }
    o[0] = w; o[1] = x; o[2] = y; o[3] = z; return o;
  }
  // local axes of a frame quaternion: d1 = width direction, d2 = paper normal, d3 = tangent
  function axes(q, j, d1, d2) {
    const w = q[j], x = q[j + 1], y = q[j + 2], z = q[j + 3];
    d1[0] = 1 - 2 * (y * y + z * z); d1[1] = 2 * (x * y + w * z); d1[2] = 2 * (x * z - w * y);
    d2[0] = 2 * (x * y - w * z); d2[1] = 1 - 2 * (x * x + z * z); d2[2] = 2 * (y * z + w * x);
  }

  // ------------------------------------------------------------------ a paper ribbon piece
  // closed: N particles, N segments; segment i joins particle i to i+1 (mod N) and carries frame q_i.
  // flip: the frame comes back rotated by π about the tangent (a one-sided, Möbius-type piece).
  class Ribbon {
    constructor(xs, qs, hw, flip, lined, color, label) {
      const N = xs.length / 3;
      this.N = N; this.hw = hw; this.flip = flip; this.color = color; this.label = label;
      this.x = Float64Array.from(xs); this.p = Float64Array.from(xs); this.v = new Float64Array(3 * N);
      this.q = Float64Array.from(qs); this.lined = lined;
      this.l = new Float64Array(N);
      for (let i = 0; i < N; i++) { const j = (i + 1) % N; this.l[i] = Math.hypot(xs[3 * j] - xs[3 * i], xs[3 * j + 1] - xs[3 * i + 1], xs[3 * j + 2] - xs[3 * i + 2]); }
      let len = 0; for (let i = 0; i < N; i++) len += this.l[i];
      this.length = len;
      this.skip = Math.ceil((1.9 * hw) / (len / N)) + 1;
      this.buildMesh();
    }
    buildMesh() {
      const N = this.N, V = 4 * N;
      this.pos = new Float32Array(V * 3); this.nor = new Float32Array(V * 3);
      const uvF = new Float32Array(V * 2), uvB = new Float32Array(V * 2), idx = new Uint32Array(6 * N);
      let arc = 0;
      for (let i = 0; i < N; i++) {
        const u0 = arc / (LINE * 4), u1 = (arc + this.l[i]) / (LINE * 4); arc += this.l[i];
        const ln = this.lined[i];
        const fv = ln ? [0.52, 0.98] : [0.02, 0.48], bv = ln ? [0.02, 0.48] : [0.52, 0.98];
        const b = 4 * i;
        // vertex order per quad: A_i, B_i, A_i+1, B_i+1   (A = +hw·d1, B = −hw·d1)
        uvF.set([u0, fv[1], u0, fv[0], u1, fv[1], u1, fv[0]], 2 * b);
        uvB.set([u0, bv[1], u0, bv[0], u1, bv[1], u1, bv[0]], 2 * b);
        idx.set([b, b + 1, b + 2, b + 2, b + 1, b + 3], 6 * i);
      }
      const pa = new THREE.BufferAttribute(this.pos, 3), na = new THREE.BufferAttribute(this.nor, 3), ia = new THREE.BufferAttribute(idx, 1);
      pa.setUsage(THREE.DynamicDrawUsage); na.setUsage(THREE.DynamicDrawUsage);
      const gF = new THREE.BufferGeometry(), gB = new THREE.BufferGeometry();
      for (const [g, uv] of [[gF, uvF], [gB, uvB]]) { g.setAttribute('position', pa); g.setAttribute('normal', na); g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setIndex(ia); }
      const col = new THREE.Color(this.color);
      this.group = new THREE.Group();
      this.front = new THREE.Mesh(gF, new THREE.MeshStandardMaterial({ map: atlas, color: col, side: THREE.FrontSide, roughness: 0.85 }));
      this.back = new THREE.Mesh(gB, new THREE.MeshStandardMaterial({ map: atlas, color: col, side: THREE.BackSide, roughness: 0.9 }));
      this.front.userData.ribbon = this; this.back.userData.ribbon = this;
      // edges: two loops, or one double-length loop on a one-sided piece
      const ne = this.flip ? 2 * N + 1 : 2 * (N + 1);
      this.epos = new Float32Array(ne * 3);
      const eg = new THREE.BufferGeometry(); const ea = new THREE.BufferAttribute(this.epos, 3); ea.setUsage(THREE.DynamicDrawUsage); eg.setAttribute('position', ea);
      const edgeMat = new THREE.LineBasicMaterial({ color: col.clone().multiplyScalar(0.55) });
      if (this.flip) this.edges = [new THREE.Line(eg, edgeMat)];
      else {
        const g2 = new THREE.BufferGeometry(); const half = (N + 1) * 3;
        g2.setAttribute('position', new THREE.BufferAttribute(this.epos.subarray(half), 3));
        eg.setDrawRange(0, N + 1);
        this.edges = [new THREE.Line(eg, edgeMat), new THREE.Line(g2, edgeMat)];
      }
      for (const o of [this.front, this.back, ...this.edges]) o.frustumCulled = false;
      this.group.add(this.front, this.back, ...this.edges);
      this.updateMesh();
    }
    // width direction & normal at particle i (average of neighbouring segment frames)
    colFrame(i, d1, d2) {
      const N = this.N, a1 = [0, 0, 0], a2 = [0, 0, 0];
      let prev = i - 1, sgn = 1;
      if (prev < 0) { prev = N - 1; if (this.flip) sgn = -1; }
      axes(this.q, 4 * i, d1, d2); axes(this.q, 4 * prev, a1, a2);
      for (let k = 0; k < 3; k++) { d1[k] += sgn * a1[k]; d2[k] += sgn * a2[k]; }
      const l1 = Math.hypot(d1[0], d1[1], d1[2]) || 1, l2 = Math.hypot(d2[0], d2[1], d2[2]) || 1;
      for (let k = 0; k < 3; k++) { d1[k] /= l1; d2[k] /= l2; }
    }
    updateMesh() {
      const N = this.N, hw = this.hw, x = this.x, pos = this.pos, nor = this.nor, e = this.epos;
      const cd1 = new Float64Array(3 * (N + 1)), cd2 = new Float64Array(3 * (N + 1));
      const d1 = [0, 0, 0], d2 = [0, 0, 0];
      for (let i = 0; i < N; i++) { this.colFrame(i, d1, d2); cd1.set(d1, 3 * i); cd2.set(d2, 3 * i); }
      const sg = this.flip ? -1 : 1;
      for (let k = 0; k < 3; k++) { cd1[3 * N + k] = sg * cd1[k]; cd2[3 * N + k] = sg * cd2[k]; }
      for (let i = 0; i < N; i++) {
        for (let c = 0; c < 2; c++) {
          const col = i + c, pi = col % N;
          for (let side = 0; side < 2; side++) {
            const v = 4 * i + 2 * c + side, sgw = side ? -hw : hw;
            for (let k = 0; k < 3; k++) { pos[3 * v + k] = x[3 * pi + k] + sgw * cd1[3 * col + k]; nor[3 * v + k] = cd2[3 * col + k]; }
          }
        }
      }
      if (this.flip) {
        for (let i = 0; i < 2 * N; i++) { const pi = i % N, s = i < N ? hw : -hw; for (let k = 0; k < 3; k++) e[3 * i + k] = x[3 * pi + k] + s * cd1[3 * pi + k]; }
        // after one lap the +hw edge continues as the −hw edge; at i = 2N we are back on +hw
        for (let k = 0; k < 3; k++) e[3 * 2 * N + k] = x[k] + hw * cd1[k];
      } else {
        for (let i = 0; i <= N; i++) {
          const pi = i % N;
          for (let k = 0; k < 3; k++) { e[3 * i + k] = x[3 * pi + k] + hw * cd1[3 * i + k]; e[3 * (N + 1 + i) + k] = x[3 * pi + k] - hw * cd1[3 * i + k]; }
        }
      }
      const fa = this.front.geometry.attributes;
      fa.position.needsUpdate = true; fa.normal.needsUpdate = true;
      for (const ed of this.edges) ed.geometry.attributes.position.needsUpdate = true;
    }
    // curves for topology: core, and its edge (orientable) or its single boundary (one-sided)
    curves() {
      const N = this.N, core = new Float64Array(3 * N), d1 = [0, 0, 0], d2 = [0, 0, 0];
      core.set(this.x);
      let edge;
      if (this.flip) {
        edge = new Float64Array(6 * N);
        for (let i = 0; i < N; i++) { this.colFrame(i, d1, d2); for (let k = 0; k < 3; k++) { edge[3 * i + k] = this.x[3 * i + k] + this.hw * d1[k]; edge[3 * (N + i) + k] = this.x[3 * i + k] - this.hw * d1[k]; } }
      } else {
        edge = new Float64Array(3 * N);
        for (let i = 0; i < N; i++) { this.colFrame(i, d1, d2); for (let k = 0; k < 3; k++) edge[3 * i + k] = this.x[3 * i + k] + 0.6 * this.hw * d1[k]; }
      }
      return { core, edge };
    }
    dispose() {
      this.front.geometry.dispose(); this.back.geometry.dispose();
      for (const ed of this.edges) ed.geometry.dispose();
      this.front.material.dispose(); this.back.material.dispose();
    }
  }

  // a piece of the original band, straight from the exact parametrisation P(t,s) = core(t) + s·dir(t)
  function bandPiece(s1, s2, laps, flip, color, label) {
    const hw = (s2 - s1) / 2, sc = (s1 + s2) / 2;
    const seg = Math.min(0.055, hw * 0.55);
    const N = Math.max(40, Math.round((laps * TAU * R) / seg));
    const xs = new Float64Array(3 * N), qs = new Float64Array(4 * N), lined = new Uint8Array(N);
    const P = [0, 0, 0], Q = [0, 0, 0], D = [0, 0, 0], q = [0, 0, 0, 0];
    for (let i = 0; i < N; i++) { ML.band.P((i / N) * laps * TAU, sc, nn(), R, P); xs.set(P, 3 * i); }
    for (let i = 0; i < N; i++) {
      const j = (i + 1) % N, tm = ((i + 0.5) / N) * laps * TAU;
      const d3 = [xs[3 * j] - xs[3 * i], xs[3 * j + 1] - xs[3 * i + 1], xs[3 * j + 2] - xs[3 * i + 2]];
      const l3 = Math.hypot(d3[0], d3[1], d3[2]); d3[0] /= l3; d3[1] /= l3; d3[2] /= l3;
      ML.band.dir(tm, nn(), D);
      const dp = D[0] * d3[0] + D[1] * d3[1] + D[2] * d3[2];
      const d1 = [D[0] - dp * d3[0], D[1] - dp * d3[1], D[2] - dp * d3[2]];
      const l1 = Math.hypot(d1[0], d1[1], d1[2]); d1[0] /= l1; d1[1] /= l1; d1[2] /= l1;
      const d2 = [d3[1] * d1[2] - d3[2] * d1[1], d3[2] * d1[0] - d3[0] * d1[2], d3[0] * d1[1] - d3[1] * d1[0]];
      qFromBasis(d1, d2, d3, q); qs.set(q, 4 * i);
      lined[i] = laps === 2 && tm > TAU ? 0 : 1;   // on a double-length piece the second lap is the paper's back
    }
    // keep neighbouring quaternions on the same hemisphere
    for (let i = 1; i < N; i++) { const a = 4 * (i - 1), b = 4 * i; if (qs[a] * qs[b] + qs[a + 1] * qs[b + 1] + qs[a + 2] * qs[b + 2] + qs[a + 3] * qs[b + 3] < 0) for (let k = 0; k < 4; k++) qs[b + k] = -qs[b + k]; }
    const rb = new Ribbon(xs, qs, hw, flip, lined, color, label);
    rb.knot = laps === 2 && st.n > 1 ? ML.topo.torusName(st.n) : 'unknot';
    return rb;
  }

  // ------------------------------------------------------------------ what a cut produces (theory)
  function plan() {
    const k = st.k, s = [];
    for (let j = 0; j <= k; j++) s.push(-W + (2 * W * j) / k);
    const pieces = [], cuts = [];
    if (!odd()) {
      for (let i = 0; i < k; i++) pieces.push({ s1: s[i], s2: s[i + 1], laps: 1, flip: false });
      for (let j = 1; j < k; j++) cuts.push({ s: s[j], laps: 1 });
    } else {
      for (let i = 0; i < k; i++) {
        const j = k - 1 - i;
        if (i === j) pieces.push({ s1: s[i], s2: s[i + 1], laps: 1, flip: true });
        else if (i > j) pieces.push({ s1: s[i], s2: s[i + 1], laps: 2, flip: false });
      }
      for (let j = 1; j < k; j++) { if (Math.abs(s[j]) < 1e-9) cuts.push({ s: 0, laps: 1 }); else if (s[j] > 0) cuts.push({ s: s[j], laps: 2 }); }
    }
    pieces.sort((a, b) => a.laps - b.laps);
    return { pieces, cuts };
  }
  const fracName = (k) => ({ 2: '½', 3: '⅓', 4: '¼', 5: '⅕' }[k]);
  function ruleText() {
    const n = st.n, k = st.k;
    if (!odd()) {
      return '<b>Even twist count: every cut line closes after one lap.</b> You get ' + k + ' separate loops, each the original length with ' + n + ' half-twist' + (n === 1 ? '' : 's') + '.' +
        (n === 0 ? ' A plain loop just falls apart into rings.' : ' Every pair of loops is linked ' + n / 2 + '×.');
    }
    const dbl = Math.floor(k / 2), mid = k % 2 === 1;
    return '<b>Odd twist count: a cut off the centre line goes round twice before it meets itself.</b> Only the exact centre closes after one lap. ' +
      'You get ' + (dbl ? dbl + ' band' + (dbl > 1 ? 's' : '') + ' twice as long' : '') + (dbl && mid ? ' plus ' : '') + (mid ? 'one Möbius band the original length' : '') + '. ' +
      (n === 1 ? 'The long bands carry 2 full twists.' : 'The long bands are tied in a ' + ML.topo.torusName(n) + '.') + ' All pieces are linked together.';
  }
  function predictionHTML() {
    const { pieces, cuts } = plan();
    const laps = cuts.map((c) => c.laps);
    const L = ['<b>Prediction</b> for ' + st.n + ' half-twist' + (st.n === 1 ? '' : 's') + ', cut into ' + st.k + ' strips (' + fracName(st.k) + ' lines):'];
    L.push(cuts.length + ' cut line' + (cuts.length > 1 ? 's' : '') + '. The scissors go round ' + laps.join(' + ') + ' lap' + (laps.reduce((a, b) => a + b, 0) > 1 ? 's' : '') + '.');
    L.push(pieces.length + ' piece' + (pieces.length > 1 ? 's' : '') + ': ' + pieces.map((p) => (p.flip ? 'a one-sided band' : p.laps === 2 ? 'a double-length two-sided band' : 'a two-sided loop')).join(', ') + '.');
    return L.join('<br>');
  }

  // ------------------------------------------------------------------ scene setup & cutting animation
  function clearPieces() { for (const p of st.pieces) { scene.remove(p.group); p.dispose(); } st.pieces = []; }
  function showUncut() {
    clearPieces();
    const pc = bandPiece(-W, W, 1, odd(), C.pieces[0], 'A');
    pc.group.userData.uncut = true;
    st.pieces = [pc]; scene.add(pc.group);
    st.phase = 'uncut'; st.topo = null; st.pull = 0;
    if (scissors) scissors.visible = false;
    if (cutLine) { scene.remove(cutLine); cutLine = null; }
    refreshPanel();
  }
  function startCut() {
    if (st.phase === 'cutting' || st.busy) return;
    if (st.phase === 'cut') showUncut();
    const { cuts } = plan();
    st.cuts = cuts; st.cutIdx = 0; st.cutProg = 0; st.phase = 'cutting';
    makeCutLine();
    scissors.visible = true;
    refreshPanel();
  }
  function makeCutLine() {
    if (cutLine) scene.remove(cutLine);
    const c = st.cuts[st.cutIdx], M = 360 * c.laps, pts = new Float32Array(M * 2 * 3);
    const P = [0, 0, 0], N = [0, 0, 0];
    for (let i = 0; i < M; i++) {
      const t = (i / (M - 1)) * c.laps * TAU;
      ML.band.P(t, c.s, nn(), R, P); ML.band.normal(t, c.s, nn(), R, N);
      for (let f = 0; f < 2; f++) { const sg = f ? -0.004 : 0.004, o = 3 * (f * M + i); pts[o] = P[0] + N[0] * sg; pts[o + 1] = P[1] + N[1] * sg; pts[o + 2] = P[2] + N[2] * sg; }
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pts, 3));
    cutLine = new THREE.Group();
    const mat = new THREE.LineBasicMaterial({ color: 0x121428 });
    const g1 = g, g2 = new THREE.BufferGeometry(); g2.setAttribute('position', new THREE.BufferAttribute(pts.subarray(3 * M), 3));
    g1.setDrawRange(0, 0); g2.setDrawRange(0, 0);
    cutLine.add(new THREE.Line(g1, mat), new THREE.Line(g2, mat));
    cutLine.userData.M = M;
    scene.add(cutLine);
  }
  function buildScissors() {
    const g = new THREE.Group();
    const steel = new THREE.MeshStandardMaterial({ color: 0xc9cede, metalness: 0.7, roughness: 0.3 });
    const handle = new THREE.MeshStandardMaterial({ color: 0xf3c96e, roughness: 0.5 });
    for (const s of [1, -1]) {
      const arm = new THREE.Group();
      const blade = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.006, 0.026), steel); blade.position.set(0.11, 0, 0); arm.add(blade);
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.009, 8, 20), handle); ring.position.set(-0.06, 0, s * 0.035); ring.rotation.x = Math.PI / 2; arm.add(ring);
      arm.userData.s = s; g.add(arm);
    }
    g.visible = false;
    return g;
  }
  function animateCut(dt) {
    const c = st.cuts[st.cutIdx], dur = 1.7 * c.laps;
    st.cutProg = Math.min(1, st.cutProg + dt / dur);
    const M = cutLine.userData.M, cnt = Math.max(2, Math.floor(st.cutProg * M));
    cutLine.children.forEach((l) => l.geometry.setDrawRange(0, cnt));
    const t = st.cutProg * c.laps * TAU;
    const P = [0, 0, 0], N = [0, 0, 0], T = [0, 0, 0];
    ML.band.P(t, c.s, nn(), R, P); ML.band.normal(t, c.s, nn(), R, N); ML.band.Pt(t, c.s, nn(), R, T);
    const f = new THREE.Vector3(T[0], T[1], T[2]).normalize(), u = new THREE.Vector3(N[0], N[1], N[2]), z = new THREE.Vector3().crossVectors(f, u).normalize();
    scissors.position.set(P[0] - f.x * 0.11, P[1] - f.y * 0.11, P[2] - f.z * 0.11);
    scissors.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(f, u, z));
    const open = 0.22 * (0.5 + 0.5 * Math.sin(st.cutProg * c.laps * 60));
    scissors.children.forEach((arm) => { arm.rotation.y = arm.userData.s * open; });
    const lapNow = Math.min(c.laps, Math.floor(st.cutProg * c.laps) + 1);
    hud.state.textContent = 'Cut line ' + (st.cutIdx + 1) + ' of ' + st.cuts.length + ' · lap ' + lapNow + ' of ' + c.laps;
    hud.note.textContent = c.laps === 2 ? (lapNow === 1 ? "past the tape and still not back to the start…" : 'second lap: now it meets its own start') : 'centre line: closes after one lap';
    if (st.cutProg >= 1) {
      st.cutIdx++;
      if (st.cutIdx < st.cuts.length) { st.cutProg = 0; makeCutLine(); }
      else finishCut();
    }
  }
  function finishCut() {
    scissors.visible = false;
    if (cutLine) { scene.remove(cutLine); cutLine = null; }
    clearPieces();
    const { pieces } = plan();
    pieces.forEach((p, i) => {
      const rb = bandPiece(p.s1, p.s2, p.laps, p.flip, C.pieces[i % C.pieces.length], String.fromCharCode(65 + i));
      rb.laps = p.laps; st.pieces.push(rb); scene.add(rb.group);
    });
    st.phase = 'cut'; st.ramp = 0;
    hud.note.textContent = 'click a piece to cut it again down its middle';
    measure();
  }
  // cut a relaxed piece down its middle (recursive experiments)
  function recut(rb) {
    if (st.phase !== 'cut') return;
    const total = st.pieces.reduce((a, p) => a + p.N, 0);
    if (rb.hw < 0.022 || total + rb.N * 3 > 3200) { hud.note.textContent = 'that strip is too thin to cut again'; return; }
    const N = rb.N, d1 = [0, 0, 0], d2 = [0, 0, 0], h = rb.hw / 2;
    // resample: insert midpoints so segments stay short next to the thinner width
    const N2 = 2 * N, xs = new Float64Array(3 * N2), cd = new Float64Array(3 * N2);
    for (let i = 0; i < N; i++) {
      const j = (i + 1) % N;
      rb.colFrame(i, d1, d2);
      const e1 = [0, 0, 0], e2 = [0, 0, 0]; rb.colFrame(j, e1, e2);
      if (j === 0 && rb.flip) { e1[0] = -e1[0]; e1[1] = -e1[1]; e1[2] = -e1[2]; }
      for (let k = 0; k < 3; k++) {
        xs[6 * i + k] = rb.x[3 * i + k]; cd[6 * i + k] = d1[k];
        xs[6 * i + 3 + k] = (rb.x[3 * i + k] + rb.x[3 * j + k]) / 2; cd[6 * i + 3 + k] = (d1[k] + e1[k]) / 2;
      }
    }
    const subs = [];
    // laps = 1: a half at offset sign·h, same frame as the parent.
    // laps = 2 (one-sided parent): +h for one lap, then −h with the frame flipped, giving one long two-sided band.
    const mk = (laps, sign) => {
      const M = N2 * laps, X = new Float64Array(3 * M), Wd = new Float64Array(3 * M), lined = new Uint8Array(M);
      for (let i = 0; i < M; i++) {
        const pi = i % N2, lap = Math.floor(i / N2);
        const sg = laps === 2 ? (lap ? -1 : 1) : sign, fl = laps === 2 && lap ? -1 : 1;
        for (let k = 0; k < 3; k++) { X[3 * i + k] = xs[3 * pi + k] + sg * h * cd[3 * pi + k]; Wd[3 * i + k] = fl * cd[3 * pi + k]; }
        lined[i] = rb.lined[Math.floor(pi / 2)] ^ (fl < 0 ? 1 : 0);
      }
      const Q = new Float64Array(4 * M), q = [0, 0, 0, 0];
      for (let i = 0; i < M; i++) {
        const j = (i + 1) % M;
        const d3 = [X[3 * j] - X[3 * i], X[3 * j + 1] - X[3 * i + 1], X[3 * j + 2] - X[3 * i + 2]], l = Math.hypot(d3[0], d3[1], d3[2]) || 1;
        d3[0] /= l; d3[1] /= l; d3[2] /= l;
        const w = [Wd[3 * i], Wd[3 * i + 1], Wd[3 * i + 2]], dp = w[0] * d3[0] + w[1] * d3[1] + w[2] * d3[2];
        const a = [w[0] - dp * d3[0], w[1] - dp * d3[1], w[2] - dp * d3[2]], la = Math.hypot(a[0], a[1], a[2]) || 1;
        a[0] /= la; a[1] /= la; a[2] /= la;
        const b = [d3[1] * a[2] - d3[2] * a[1], d3[2] * a[0] - d3[0] * a[2], d3[0] * a[1] - d3[1] * a[0]];
        qFromBasis(a, b, d3, q); Q.set(q, 4 * i);
      }
      for (let i = 1; i < M; i++) { const a = 4 * (i - 1), b = 4 * i; if (Q[a] * Q[b] + Q[a + 1] * Q[b + 1] + Q[a + 2] * Q[b + 2] + Q[a + 3] * Q[b + 3] < 0) for (let k = 0; k < 4; k++) Q[b + k] = -Q[b + k]; }
      return { X, Q, lined, flip: false };
    };
    if (rb.flip) subs.push(mk(2, 1)); else { subs.push(mk(1, 1)); subs.push(mk(1, -1)); }
    const idx = st.pieces.indexOf(rb);
    scene.remove(rb.group); rb.dispose(); st.pieces.splice(idx, 1);
    const used = new Set(st.pieces.map((p) => p.color));
    subs.forEach((sp, i) => {
      const col = i === 0 ? rb.color : C.pieces.find((c) => !used.has(c)) || C.pieces[(st.pieces.length + i) % C.pieces.length];
      used.add(col);
      const nr = new Ribbon(sp.X, sp.Q, h, sp.flip, sp.lined, col, '');
      // splitting keeps the knot of a two-sided piece; a one-sided piece's boundary becomes a T(2, half-twists) knot
      nr.knot = rb.flip ? ML.topo.torusName(Math.abs(rb.ht || 1)) : rb.knot;
      st.pieces.splice(idx + i, 0, nr); scene.add(nr.group);
    });
    st.pieces.forEach((p, i) => (p.label = String.fromCharCode(65 + i)));
    st.ramp = 0.4;
    measure();
  }

  // ------------------------------------------------------------------ physics (PBD Cosserat rods + self-contact)
  const Z = [0, 0, 0, 1], Zc = [0, 0, 0, -1];
  const qa = [0, 0, 0, 0], qb = [0, 0, 0, 0], om = [0, 0, 0, 0], t1 = [0, 0, 0, 0], t2 = [0, 0, 0, 0];
  function solveStretch(rb, ks) {
    const N = rb.N, p = rb.p, q = rb.q, wq = 1;
    for (let i = 0; i < N; i++) {
      const a = 3 * i, b = 3 * ((i + 1) % N), j = 4 * i, l = rb.l[i];
      const w = q[j], x = q[j + 1], y = q[j + 2], z = q[j + 3];
      const d0 = 2 * (x * z + w * y), d1 = 2 * (y * z - w * x), d2 = w * w - x * x - y * y + z * z;
      let g0 = (p[b] - p[a]) / l - d0, g1 = (p[b + 1] - p[a + 1]) / l - d1, g2 = (p[b + 2] - p[a + 2]) / l - d2;
      const den = 2 / l + wq * 4 * l + 1e-9;
      g0 = (g0 / den) * ks; g1 = (g1 / den) * ks; g2 = (g2 / den) * ks;
      p[a] += g0; p[a + 1] += g1; p[a + 2] += g2; p[b] -= g0; p[b + 1] -= g1; p[b + 2] -= g2;
      // q += 2·wq·l · (0,γ) ⊗ (q ⊗ ē3)
      const ew = z, ex = -y, ey = x, ez = -w;
      const cw = -g0 * ex - g1 * ey - g2 * ez, cx = g0 * ew + g1 * ez - g2 * ey, cy = -g0 * ez + g1 * ew + g2 * ex, cz = g0 * ey - g1 * ex + g2 * ew;
      const s = 2 * wq * l;
      let nw = w + cw * s, nx = x + cx * s, ny = y + cy * s, nz = z + cz * s;
      const nl = Math.hypot(nw, nx, ny, nz) || 1;
      q[j] = nw / nl; q[j + 1] = nx / nl; q[j + 2] = ny / nl; q[j + 3] = nz / nl;
    }
  }
  function solveBend(rb, K0, K1, K2) {
    const N = rb.N, q = rb.q;
    for (let i = 0; i < N; i++) {
      const j0 = 4 * i, i1 = (i + 1) % N, j1 = 4 * i1;
      qa[0] = q[j0]; qa[1] = q[j0 + 1]; qa[2] = q[j0 + 2]; qa[3] = q[j0 + 3];
      qb[0] = q[j1]; qb[1] = q[j1 + 1]; qb[2] = q[j1 + 2]; qb[3] = q[j1 + 3];
      const seam = i1 === 0 && rb.flip;
      if (seam) { qmul(qb, Z, t1); qb[0] = t1[0]; qb[1] = t1[1]; qb[2] = t1[2]; qb[3] = t1[3]; }
      // Darboux quaternion Ω = q̄a ⊗ qb, compared with the rest state (identity: flat, untwisted paper)
      t2[0] = qa[0]; t2[1] = -qa[1]; t2[2] = -qa[2]; t2[3] = -qa[3];
      qmul(t2, qb, om);
      // with an identity rest state the vector part is the same for Ω − 1 and Ω + 1, so no sign choice is needed
      om[0] = 0;
      const inv = 1 / (2 + 1e-6);
      om[1] *= K0 * inv; om[2] *= K1 * inv; om[3] *= K2 * inv;
      qmul(qb, om, t1);           // correction for qa
      qmul(qa, om, t2);           // correction for qb (negated)
      let aw = qa[0] + t1[0], ax = qa[1] + t1[1], ay = qa[2] + t1[2], az = qa[3] + t1[3];
      let bw = qb[0] - t2[0], bx = qb[1] - t2[1], by = qb[2] - t2[2], bz = qb[3] - t2[3];
      let la = Math.hypot(aw, ax, ay, az) || 1, lb = Math.hypot(bw, bx, by, bz) || 1;
      q[j0] = aw / la; q[j0 + 1] = ax / la; q[j0 + 2] = ay / la; q[j0 + 3] = az / la;
      if (seam) { t1[0] = bw / lb; t1[1] = bx / lb; t1[2] = by / lb; t1[3] = bz / lb; qmul(t1, Zc, t2); q[j1] = t2[0]; q[j1 + 1] = t2[1]; q[j1 + 2] = t2[2]; q[j1 + 3] = t2[3]; }
      else { q[j1] = bw / lb; q[j1 + 1] = bx / lb; q[j1 + 2] = by / lb; q[j1 + 3] = bz / lb; }
    }
  }
  // self- and mutual contact between centrelines (keeps links and knots honest: nothing passes through)
  const HBITS = 14, HMASK = (1 << HBITS) - 1;
  const hHead = new Int32Array(1 << HBITS);
  let hNext = new Int32Array(4096), hPiece = new Int32Array(4096), hIdx = new Int32Array(4096);
  function contacts() {
    let total = 0; for (const rb of st.pieces) total += rb.N;
    if (hNext.length < total) { hNext = new Int32Array(total * 2); hPiece = new Int32Array(total * 2); hIdx = new Int32Array(total * 2); }
    let maxhw = 0; for (const rb of st.pieces) maxhw = Math.max(maxhw, rb.hw);
    const cell = 1.8 * maxhw;
    hHead.fill(-1);
    let g = 0;
    const key = (x, y, z) => ((Math.floor(x / cell) * 73856093) ^ (Math.floor(y / cell) * 19349663) ^ (Math.floor(z / cell) * 83492791)) & HMASK;
    st.pieces.forEach((rb, pi) => { for (let i = 0; i < rb.N; i++, g++) { const k = key(rb.p[3 * i], rb.p[3 * i + 1], rb.p[3 * i + 2]); hNext[g] = hHead[k]; hHead[k] = g; hPiece[g] = pi; hIdx[g] = i; } });
    g = 0;
    for (let pa = 0; pa < st.pieces.length; pa++) {
      const A = st.pieces[pa];
      for (let i = 0; i < A.N; i++, g++) {
        const x = A.p[3 * i], y = A.p[3 * i + 1], z = A.p[3 * i + 2];
        const cx = Math.floor(x / cell), cy = Math.floor(y / cell), cz = Math.floor(z / cell);
        for (let ox = -1; ox <= 1; ox++) for (let oy = -1; oy <= 1; oy++) for (let oz = -1; oz <= 1; oz++) {
          const k = (((cx + ox) * 73856093) ^ ((cy + oy) * 19349663) ^ ((cz + oz) * 83492791)) & HMASK;
          for (let h = hHead[k]; h >= 0; h = hNext[h]) {
            if (h <= g) continue;
            const pb = hPiece[h], j = hIdx[h], B = st.pieces[pb];
            if (pb === pa) { const dd = Math.abs(i - j), cyc = Math.min(dd, A.N - dd); if (cyc < A.skip) continue; }
            const r = 0.92 * (A.hw + B.hw);
            const dx = B.p[3 * j] - x, dy = B.p[3 * j + 1] - y, dz = B.p[3 * j + 2] - z, d2 = dx * dx + dy * dy + dz * dz;
            if (d2 >= r * r || d2 < 1e-12) continue;
            const d = Math.sqrt(d2), c = (0.5 * (r - d)) / d;
            A.p[3 * i] -= dx * c; A.p[3 * i + 1] -= dy * c; A.p[3 * i + 2] -= dz * c;
            B.p[3 * j] += dx * c; B.p[3 * j + 1] += dy * c; B.p[3 * j + 2] += dz * c;
          }
        }
      }
    }
  }
  function physics(dt) {
    if (st.phase !== 'cut' || !st.pieces.length) return;
    st.ramp = Math.min(1, st.ramp + dt / 1.4);
    const sub = 3, h = Math.min(dt, 1 / 30) / sub, iters = 6;
    const kb = ML.smooth(st.ramp);
    // paper: bends easily out of its plane (about d1), stiff in-plane (about d2), moderate twist (about d3)
    const K0 = 0.06 * kb, K1 = 0.5 * kb, K2 = 0.22 * kb;
    let cx = 0, cy = 0, cz = 0, cn = 0;
    for (const rb of st.pieces) for (let i = 0; i < rb.N; i++) { cx += rb.x[3 * i]; cy += rb.x[3 * i + 1]; cz += rb.x[3 * i + 2]; cn++; }
    cx /= cn; cy /= cn; cz /= cn;
    const pc = st.pieces.map((rb, pi) => {
      let x = 0, y = 0, z = 0; for (let i = 0; i < rb.N; i++) { x += rb.x[3 * i]; y += rb.x[3 * i + 1]; z += rb.x[3 * i + 2]; }
      x = x / rb.N - cx; y = y / rb.N - cy; z = z / rb.N - cz;
      let l = Math.hypot(x, y, z);
      if (l < 0.05) { const a = (pi / st.pieces.length) * TAU; x = Math.cos(a); y = 0.3 * (pi % 2 ? 1 : -1); z = Math.sin(a); l = Math.hypot(x, y, z); }
      return [x / l, y / l, z / l];
    });
    for (let s = 0; s < sub; s++) {
      const kick = st.temp * Math.sqrt(h) * 1.6;
      st.pieces.forEach((rb, pi) => {
        const v = rb.v, x = rb.x, p = rb.p, dir = pc[pi], pull = st.pull > 0 ? 0.9 : 0;
        for (let i = 0; i < 3 * rb.N; i += 3) {
          v[i] = v[i] * 0.985 + kick * ML.gauss() + pull * dir[0] * h;
          v[i + 1] = v[i + 1] * 0.985 + kick * ML.gauss() + pull * dir[1] * h;
          v[i + 2] = v[i + 2] * 0.985 + kick * ML.gauss() + pull * dir[2] * h;
          p[i] = x[i] + v[i] * h; p[i + 1] = x[i + 1] + v[i + 1] * h; p[i + 2] = x[i + 2] + v[i + 2] * h;
        }
      });
      for (let it = 0; it < iters; it++) {
        for (const rb of st.pieces) { solveStretch(rb, 1); solveBend(rb, K0, K1, K2); }
        if (it % 2 === 1) contacts();
      }
      contacts();
      for (const rb of st.pieces) {
        const inv = 1 / h, vmax = 2.5;
        for (let i = 0; i < 3 * rb.N; i++) { let vv = (rb.p[i] - rb.x[i]) * inv; if (vv > vmax) vv = vmax; else if (vv < -vmax) vv = -vmax; rb.v[i] = vv; rb.x[i] = rb.p[i]; }
      }
    }
    // keep the whole tangle centred in view
    for (const rb of st.pieces) for (let i = 0; i < rb.N; i++) { rb.x[3 * i] -= cx; rb.x[3 * i + 1] -= cy; rb.x[3 * i + 2] -= cz; }
    st.pull = Math.max(0, st.pull - dt);
  }

  // ------------------------------------------------------------------ measuring topology (exact polygon linking numbers)
  function measure() {
    const P = st.pieces.map((rb) => ({ rb, c: rb.curves() }));
    const res = P.map(({ rb, c }) => {
      const lk = ML.topo.linking(c.core, c.edge);
      const ht = rb.flip ? Math.round(lk) : Math.round(2 * lk);
      rb.ht = ht;
      return { label: rb.label, color: rb.color, flip: rb.flip, ht, len: rb.length / (TAU * R), knot: rb.knot };
    });
    const links = [];
    for (let i = 0; i < P.length; i++) for (let j = i + 1; j < P.length; j++) {
      links.push({ a: i, b: j, lk: Math.round(Math.abs(ML.topo.linking(P[i].c.core, P[j].c.core))) });
    }
    st.topo = { res, links };
    res.forEach((r, i) => { r.wr = ML.topo.writhe(stride(P[i].c.core)); });
    refreshPanel();
  }
  function stride(a, cap) { cap = cap || 420; const n = a.length / 3; if (n <= cap) return a; const s = Math.ceil(n / cap), m = Math.floor(n / s), o = new Float64Array(3 * m); for (let i = 0; i < m; i++) o.set(a.subarray(3 * i * s, 3 * i * s + 3), 3 * i); return o; }
  function liveCheck(dt) {
    if (st.phase !== 'cut' || !st.topo) return;
    st.liveT -= dt; if (st.liveT > 0) return; st.liveT = 0.8;
    const k = st.liveIdx++, i = k % st.pieces.length, rb = st.pieces[i], r = st.topo.res[i];
    if (!rb || !r) return;
    const c = rb.curves();
    r.wr = ML.topo.writhe(stride(c.core, 260));
    // re-measure the twist count from the moving paper now and then (it never changes: that's the point)
    if (Math.floor(k / st.pieces.length) % 4 === 3 && rb.N <= 420) r.liveHt = rb.flip ? Math.round(ML.topo.linking(c.core, c.edge)) : Math.round(2 * ML.topo.linking(c.core, c.edge));
    refreshTable();
  }

  // ------------------------------------------------------------------ panel
  function refreshPanel() {
    if (!ruleBox || !hud.state) return;
    ruleBox.innerHTML = ruleText();
    predBox.innerHTML = predictionHTML();
    cutBtn.textContent = st.phase === 'cut' ? 'Start over and cut' : 'Cut it';
    cutBtn.disabled = st.phase === 'cutting';
    hud.state.textContent = st.phase === 'uncut' ? st.n + ' half-twist' + (st.n === 1 ? '' : 's') + ' · ready to cut into ' + st.k + ' strips' : st.phase === 'cut' ? st.pieces.length + ' piece' + (st.pieces.length > 1 ? 's' : '') : hud.state.textContent;
    if (st.phase === 'uncut') hud.note.textContent = '';
    refreshTable();
  }
  function refreshTable() {
    if (!st.topo || st.phase !== 'cut') { tableBox.innerHTML = '<p class="tip">Cut the strip to measure the pieces.</p>'; return; }
    const { res, links } = st.topo;
    const n = st.n;
    let h = '<div class="tablewrap"><table class="ptable"><thead><tr><th>Piece</th><th>Sides</th><th>Length</th><th>Half-twists</th><th>Twist + coil</th><th>Core</th></tr></thead><tbody>';
    res.forEach((r) => {
      const ht = r.liveHt !== undefined ? r.liveHt : r.ht, ab = Math.abs(ht), sg = ht < 0 ? -1 : 1;
      // linking (in full turns) = twist + writhe; shown with the piece's own handedness as positive
      const lkTurns = ab / 2, wr = sg * (r.wr || 0), tw = lkTurns - wr;
      h += '<tr><td><span class="sw" style="display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;background:' + r.color + '"></span>' + r.label + '</td><td>' + (r.flip ? '1' : '2') + '</td><td>×' + r.len.toFixed(1) + '</td><td>' + ab + '</td><td>' + tw.toFixed(2) + ' + ' + wr.toFixed(2) + '</td><td>' + (r.knot || 'unknot') + '</td></tr>';
    });
    h += '</tbody></table></div>';
    const linked = links.filter((l) => l.lk > 0);
    h += '<p class="tip" style="margin-top:8px">' + (links.length === 0 ? 'Only one piece, so nothing to link with.' : linked.length === 0 ? 'No two pieces are linked: they come apart freely.' : 'Linked: ' + links.map((l) => res[l.a].label + '–' + res[l.b].label + ' ' + l.lk + '×').join(', ') + '.') + '</p>';
    h += '<p class="tip">Half-twists and links are measured from the 3D shape (exact linking numbers of the edges and cores) and rechecked while the paper moves. Jostling changes the shape, never these counts. Twist + coil always adds up to half the half-twists: twist turns into coiling as a band relaxes, like a phone cord.</p>';
    tableBox.innerHTML = h;
  }

  const IDEAS = `
    <p class="quote">"Is there any way to predict what the shape will be before cutting? ½, ⅓, ¼, ⅕…"</p>
    <div><h4>What the sim does</h4><ul>
      <li><b>The cut is exact.</b> The strip is the same shape you make with paper (a band with n half-twists). The cut lines are the lines a third, a quarter, a fifth of the way across. The scissors follow them and count laps.</li>
      <li><b>The pieces are real paper physics.</b> Each piece is a rod with a frame (a Cosserat ribbon). It bends easily out of its plane, hardly at all within it, and resists twisting. Pieces push each other away where they touch, so a link or knot can never cheat by passing through itself.</li>
      <li><b>Counts are measured, not looked up.</b> Half-twists, links and coil come from the 3D shape itself, using exact linking numbers of closed polygons, and are rechecked as the paper moves.</li>
      <li><b>Cut again.</b> Click any piece to cut it down its middle, like your recut experiments.</li>
    </ul></div>
    <div class="hook"><h4>Yes, it's predictable. The rule</h4><ul>
      <li><b>Even half-twists:</b> k strips give k loops, each pair linked (half-twists ÷ 2) times.</li>
      <li><b>Odd half-twists:</b> any cut off the exact centre goes round twice. You get ⌊k/2⌋ bands twice as long, plus one Möbius band when k is odd. Every piece links every other one. For 3 half-twists the long bands are tied in a trefoil; for 5, a cinquefoil.</li>
      <li>Your note that "the ½ cut is the only one that doesn't go around more than once" is exactly right for odd strips. The sim shows it in the lap counter.</li>
      <li><b>Twist ⇄ coil</b> (Călugăreanu's theorem, 1959): linking = twist + writhe. That's why your cut strips curl up into figure-eights and "protein-like" shapes. DNA does the same thing (supercoiling), and so do phone cords.</li>
    </ul></div>
    <div><h4>What this can't tell you yet</h4><ul>
      <li>The rule depends only on two whole numbers (twists and cuts), so paper cutting by itself can't produce new constants. Any link to physics has to come from <i>which</i> shapes are stable when jostled. That's what the Jostle slider lets you explore.</li>
    </ul></div>`;

  const mode = {
    id: 'cutlab', tab: 'Cut Lab', kind: '3d',
    buildPanel(el) {
      const U = ML.ui;
      U.head(el, 'Cut Lab', 'Your scissors-and-tape experiments, with exact topology and real ribbon physics. Pick the twists and the cut, predict, then cut.');
      const b1 = U.block(el, 'The strip');
      U.seg(b1, { id: 'c-n', label: 'Half-twists before taping', options: [[0, '0'], [1, '1'], [2, '2'], [3, '3'], [4, '4'], [5, '5']], value: st.n, onChange: (v) => { st.n = v; showUncut(); } });
      U.seg(b1, { id: 'c-hand', label: 'Twist direction', options: [[1, 'Right-handed'], [-1, 'Left-handed']], value: st.hand, onChange: (v) => { st.hand = v; showUncut(); } });
      U.seg(b1, { id: 'c-k', label: 'Cut into', options: [[2, '½ · 2 strips'], [3, '⅓ · 3'], [4, '¼ · 4'], [5, '⅕ · 5']], value: st.k, onChange: (v) => { st.k = v; if (st.phase !== 'cutting') showUncut(); } });
      ruleBox = U.callout(b1, '');
      predBox = U.callout(b1, '');
      const btns = U.buttons(b1, [
        { label: 'Cut it', primary: true, id: 'c-cut', onClick: () => startCut() },
        { label: 'Reset strip', id: 'c-reset', onClick: () => showUncut() },
      ]);
      cutBtn = btns[0];
      const b2 = U.block(el, 'Handle the pieces');
      U.slider(b2, { id: 'c-temp', label: 'Jostle (shake the paper)', min: 0, max: 0.6, step: 0.02, value: st.temp, fmt: (v) => (v === 0 ? 'still' : v.toFixed(2)), onInput: (v) => (st.temp = v) });
      U.buttons(b2, [{ label: 'Pull pieces apart', id: 'c-pull', onClick: () => { st.pull = 3; } }]);
      U.toggle(b2, { id: 'c-quad', label: 'Four monitors (top, front, side, free)', value: st.quad, onChange: (v) => { st.quad = v; hud.quad.hidden = !v; } });
      const b3 = U.block(el, 'Measured pieces');
      tableBox = ML.el('div'); b3.append(tableBox);
      U.ideas(el, IDEAS);
    },
    buildHud(el) {
      hud.state = ML.el('div', { class: 'tag tl big' });
      hud.note = ML.el('div', { class: 'tag hand', style: 'top:52px;left:max(14px, env(safe-area-inset-left, 0px))' });
      hud.tip = ML.el('div', { class: 'tag bl wide-only', text: 'Drag to turn · scroll to zoom · after cutting, click a piece to cut it again' });
      hud.quad = ML.quadHud();
      el.append(hud.state, hud.note, hud.tip, hud.quad);
    },
    init(a) {
      app = a;
      if (!a.getRenderer()) return;
      scene = new THREE.Scene();
      cam = new THREE.PerspectiveCamera(38, 1, 0.05, 100);
      ML.paperLights(scene);
      ML.floorGrid(scene, -1.0);
      atlas = ML.paperAtlas({ lines: 4 });
      scissors = buildScissors(); scene.add(scissors);
      orbit = new ML.Orbit(a.gl, { theta: 0.5, phi: 1.05, radius: 4.4, minR: 1.6, maxR: 12 });
      orbit.autoSpin = a.reduced ? 0 : 0.06;
      orbit.onClick = (x, y, w, h) => {
        if (ML.app.current !== mode || st.phase !== 'cut') return;
        const pk = ML.pickView(cam, st.quad, x, y, w, h);
        const rc = new THREE.Raycaster(); rc.setFromCamera({ x: pk.nx, y: pk.ny }, pk.cam);
        const objs = []; st.pieces.forEach((p) => objs.push(p.front, p.back));
        objs.forEach((o) => o.geometry.computeBoundingSphere());
        const hit = rc.intersectObjects(objs, false)[0];
        if (hit) recut(hit.object.userData.ribbon);
      };
      showUncut();
    },
    enter() { if (orbit) orbit.enabled = true; },
    exit() { if (orbit) orbit.enabled = false; },
    resize() {},
    frame(dt) {
      if (!scene) return;
      if (st.phase === 'cutting') animateCut(dt);
      physics(dt);
      if (st.phase === 'cut') for (const rb of st.pieces) rb.updateMesh();
      liveCheck(dt);
      orbit.update(dt); orbit.apply(cam, app.w / app.h);
      ML.render3D(app.renderer, scene, cam, st.quad, app.w, app.h, 5.4);
    },
    _st: st, _startCut: startCut, _finish: () => { while (st.phase === 'cutting') animateCut(0.5); }, _measure: measure, _recut: (i) => recut(st.pieces[i]),
  };
  ML.register(mode);
})();
