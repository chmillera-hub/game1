/* ============================================================
   Experiment 3: Keep Halving.
   Cut a Möbius strip down its middle, then cut every piece down its
   middle, again and again. "Inside the original strip" is exact:
   after k cuts there are m = 2^(k-1) pieces, piece j is the slice
   [j/m, (j+1)/m] of the long loop's width (0 at the first cut, 1 at
   the old edge), and running θ from 0 to 4π visits that slice on
   both sides of the first cut. Twists, knots and links are measured
   on that exact geometry. "Pulled apart" lays the long loop out as a
   ring with the same twist and spreads the pieces across its width,
   drawn wider than real paper so they show. "Loose paper" (Shake,
   Pull apart) lets the pieces as cut go under the paper physics, and
   Trace runs a marker along one piece until it is back at its start.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const R0 = 1.25, W0 = 0.9, CHI = 1;                   // the Möbius strip
  const RB = 2.5, HB = 0.5;                             // the long loop laid out: ring radius, saddle height
  const MAXK = 5, SEG = 360, NS = 1440, KERF = 0.006;   // most cuts; mesh segments; measuring samples; cut width
  const THICK = 0.1, THICK_GAP = 0.04;                 // thickened width and spacing of the pieces
  const MM = 25;                                        // a 1-inch first strip, in mm
  // Loose paper: paper contact distance, cut gap (in units of the long loop's width), rail spacing, pull forces.
  // Past three cuts the strips are too thin and too many for this paper to stay honest (tests/loose.mjs).
  const LOOSE_MAXK = 3, RAD = 0.04, GAP_U = 0.04, RAIL = 0.08, PUSH = 6e-5, BURST = 2, INFLATE = 1.5e-5;
  const count = k => (k === 0 ? 1 : 2 ** (k - 1));
  const st = { k: 0, view: 'pulled', thick: true, show: 'all', sel: [0, 1], picked: false, cut: null, spread: null, lay: null, meas: null, play: false, playT: 0, twistSign: 1, measT: 0, loose: null, reloose: false, userCam: false, trace: null };
  const ch = { token: 'halving', gl: true, background: () => Lab.stageBg() };
  let meshes = [], cutObjs = [], ringC = [], ringD = [], hud = {}, btn = {}, ctl = {}, readout;

  /* ---------------- geometry ---------------- */
  // Inside the original strip. Level 0 is the Möbius strip itself (one lap); after that, piece j is a
  // slice of the long loop, two laps long.
  function stripPoint(k, j, t, v) {
    if (k === 0) return Lab.bandPoint(TAU * t, v, 1, CHI, R0, W0);
    const m = count(k), ku = KERF / (W0 / 2);
    const u0 = j / m + ku / 2, u1 = (j + 1) / m - (j + 1 < m ? ku / 2 : 0);
    return Lab.bandPoint(2 * TAU * t, u0 + (u1 - u0) * (v + 1) / 2, 1, CHI, R0, W0);
  }
  const norm = a => { const l = Math.hypot(a[0], a[1], a[2]); return [a[0] / l, a[1] / l, a[2] / l]; };
  // The long loop laid out as a gently saddled ring. The across direction turns two full turns per lap,
  // starting from "up, square to the loop", so the ring carries the long loop's 2 full twists.
  function buildRing() {
    ringC = []; ringD = [];
    for (let i = 0; i <= SEG; i++) {
      const f = TAU * i / SEG, c = [RB * Math.cos(f), RB * Math.sin(f), HB * Math.sin(2 * f)];
      const T = norm([-RB * Math.sin(f), RB * Math.cos(f), 2 * HB * Math.cos(2 * f)]);
      const N = norm([-T[2] * T[0], -T[2] * T[1], 1 - T[2] * T[2]]), B = [T[1] * N[2] - T[2] * N[1], T[2] * N[0] - T[0] * N[2], T[0] * N[1] - T[1] * N[0]];
      const a = st.twistSign * 2 * f;
      ringC.push(c); ringD.push([0, 1, 2].map(q => N[q] * Math.cos(a) + B[q] * Math.sin(a)));
    }
  }
  const ringPoint = (i, off, w, v) => { const c = ringC[i], d = ringD[i], o = off + v * w / 2; return [c[0] + d[0] * o, c[1] + d[1] * o, c[2] + d[2] * o]; };
  // Side by side across the ring, in the same order as across the strip; true width, or thickened.
  function layoutFor(k, thick) {
    const m = count(k), trueW = (W0 / 2 - (m - 1) * KERF) / m;
    const w = thick ? Math.max(trueW, THICK) : trueW, g = thick ? Math.max(KERF, THICK_GAP) : KERF;
    const tot = m * w + (m - 1) * g, off = [];
    for (let j = 0; j < m; j++) off.push(-tot / 2 + w / 2 + j * (w + g));
    return { off, w: new Array(m).fill(w) };
  }
  // New pieces start out as the two halves of their parent, then slide apart across the ring.
  function childLayout(prev, k) {
    const m = count(k), off = [], w = [];
    for (let j = 0; j < m; j++) {
      const p = j >> 1, half = (prev.w[p] - KERF) / 2;
      off.push(prev.off[p] + (j & 1 ? 1 : -1) * (half + KERF) / 2); w.push(half);
    }
    return { off, w };
  }
  // Where piece j is drawn right now.
  const inStrip = () => st.view !== 'pulled' || st.k === 0;
  const point = (j, i, v) => (inStrip() ? stripPoint(st.k, j, i / SEG, v) : ringPoint(i, st.lay.off[j], st.lay.w[j], v));
  // Lay the ring out with the same handedness of twist as the cut strip.
  function pickTwistSign() {
    const n = NS / 4, sc = j => Array.from({ length: n }, (_, i) => stripPoint(2, j, i / n, 0));
    const want = Math.sign(Lab.linking(sc(0), sc(1))), L = layoutFor(2, true);
    for (const sgn of [1, -1]) {
      st.twistSign = sgn; buildRing();
      const rc = j => Array.from({ length: SEG }, (_, i) => ringPoint(i, L.off[j], L.w[j], 0));
      if (Math.sign(Lab.linking(rc(0), rc(1))) === want) return;
    }
  }

  /* ---------------- drawing ---------------- */
  function colorOf(k, j) {
    const m = count(k);
    return m === 1 ? '#f27aa2' : `hsl(${Math.round((340 + 290 * j / (m - 1)) % 360)}, 72%, 64%)`;
  }
  const ribbonIndex = () => { const idx = []; for (let i = 0; i < SEG; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 2, a + 3, a + 1); } return idx; };
  function makePiece(j) {
    const geo = new THREE.BufferGeometry(), nv = (SEG + 1) * 2;
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
    const uv = new Float32Array(nv * 2);
    for (let i = 0; i <= SEG; i++) for (let s = 0; s < 2; s++) { uv[(i * 2 + s) * 2] = i / SEG * 40; uv[(i * 2 + s) * 2 + 1] = s; }
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setIndex(ribbonIndex());
    const color = new THREE.Color(colorOf(st.k, j)).convertSRGBToLinear();
    const mat = (lined, side) => new THREE.MeshStandardMaterial({ map: Lab.paperTexture(lined, '#ffffff', 'tape-white'), color, roughness: 0.85, side });
    const front = new THREE.Mesh(geo, mat(true, THREE.FrontSide)), back = new THREE.Mesh(geo, mat(false, THREE.BackSide));
    const group = new THREE.Group(); group.add(front, back);
    return { j, geo, front, back, group };
  }
  function syncPiece(p) {
    const arr = p.geo.getAttribute('position').array;
    for (let i = 0; i <= SEG; i++) { arr.set(point(p.j, i, -1), i * 6); arr.set(point(p.j, i, 1), i * 6 + 3); }
    p.geo.getAttribute('position').needsUpdate = true;
    p.geo.computeVertexNormals(); p.geo.computeBoundingSphere();
  }
  function rebuild() {
    meshes.forEach(p => { ch.scene.remove(p.group); p.geo.dispose(); p.front.material.dispose(); p.back.material.dispose(); });
    meshes = [];
    for (let j = 0; j < count(st.k); j++) { const p = makePiece(j); meshes.push(p); ch.scene.add(p.group); }
    meshes.forEach(syncPiece); applyShow();
  }
  // All pieces, one, or two: the others fade so a single loop, or a single pair, can be followed.
  function applyShow() {
    const m = count(st.k);
    // until someone picks, compare the two outermost pieces: they wind around each other most visibly
    if (!st.picked) st.sel = [0, m - 1];
    st.sel = st.sel.map(s => Math.min(s, m - 1));
    if (m > 1 && st.sel[0] === st.sel[1]) st.sel[1] = (st.sel[0] + 1) % m;
    (st.loose ? st.loose.meshes : meshes).forEach(p => {
      const on = st.show === 'all' || m === 1 || (st.show === 'one' ? p.j === st.sel[0] : st.sel.includes(p.j));
      [p.front.material, p.back.material].forEach(mt => {
        if (mt.transparent === on) mt.needsUpdate = true;
        mt.transparent = !on; mt.opacity = on ? 1 : 0.1; mt.depthWrite = on;
      });
    });
    showChip();
  }
  function clearCutObjs() {
    cutObjs.forEach(o => { ch.scene.remove(o); if (o.geometry) o.geometry.dispose(); o.material.dispose(); });
    cutObjs = [];
  }
  // Keep the camera's direction, but back off far enough to see everything.
  function frame(dur = 0.9) {
    const r = inStrip() ? R0 + W0 / 2 : RB + Math.max(...st.lay.off.map((o, j) => Math.abs(o) + st.lay.w[j] / 2)) + HB * 0.5;
    const dist = r / Math.sin(THREE.MathUtils.degToRad(ch.camera.fov / 2)) * 1.08 / Math.min(1, Math.max(0.62, ch.camera.aspect));
    const dir = ch.camera.position.clone().sub(ch.controls.target).normalize();
    Lab.tweenCamera(ch, dir.multiplyScalar(dist).toArray(), [0, 0, 0], dur);
  }

  /* ---------------- loose paper ---------------- */
  // The pieces exactly as cut, handed to the paper physics from Scissors: they bend, don't stretch and
  // can't pass through each other. Shaking or pulling changes their shapes, never their links.
  function looseSpecs(k) {
    const cols = window.innerWidth < 600 ? 120 : 150, dU = TAU * R0 / cols;
    if (k === 0) {
      const K = 9, init = [];
      for (let i = 0; i < cols; i++) for (let r = 0; r < K; r++) init.push(Lab.bandPoint(TAU * i / cols, -1 + 2 * r / (K - 1), 1, CHI, R0, W0));
      return [{ M: cols, K, flip: true, init, dU, dV: new Array(K - 1).fill(W0 / (K - 1)), j: 0 }];
    }
    const m = count(k), specs = [];
    for (let j = 0; j < m; j++) {
      const u0 = j / m + GAP_U, u1 = (j + 1) / m - (j + 1 < m ? GAP_U : 0), w = (u1 - u0) * W0 / 2;
      const K = Math.max(2, Math.ceil(w / RAIL - 1e-9) + 1), M = 2 * cols, init = [];
      for (let i = 0; i < M; i++) for (let r = 0; r < K; r++) init.push(Lab.bandPoint(TAU * i / cols, u0 + (u1 - u0) * r / (K - 1), 1, CHI, R0, W0));
      specs.push({ M, K, flip: false, init, dU, dV: new Array(K - 1).fill(w / (K - 1)), j });
    }
    return specs;
  }
  function makeLooseMesh(sp) {
    const { M, K } = sp, geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array((M + 1) * K * 3), 3));
    const uv = new Float32Array((M + 1) * K * 2);
    for (let i = 0; i <= M; i++) for (let r = 0; r < K; r++) { uv[(i * K + r) * 2] = i / M * 40; uv[(i * K + r) * 2 + 1] = r / (K - 1); }
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    const idx = []; for (let i = 0; i < M; i++) for (let r = 0; r < K - 1; r++) { const a = i * K + r, b = (i + 1) * K + r; idx.push(a, b, a + 1, b, b + 1, a + 1); }
    geo.setIndex(idx);
    const color = new THREE.Color(colorOf(st.k, sp.j)).convertSRGBToLinear();
    const mat = (lined, side) => new THREE.MeshStandardMaterial({ map: Lab.paperTexture(lined, '#ffffff', 'tape-white'), color, roughness: 0.85, side });
    const front = new THREE.Mesh(geo, mat(true, THREE.FrontSide)), back = new THREE.Mesh(geo, mat(false, THREE.BackSide));
    const group = new THREE.Group(); group.add(front, back);
    return { j: sp.j, sp, geo, front, back, group };
  }
  function syncLoose() {
    const P = st.loose.sim.pos;
    st.loose.meshes.forEach(m => {
      const { M, K } = m.sp, arr = m.geo.getAttribute('position').array;
      for (let i = 0; i <= M; i++) for (let r = 0; r < K; r++) { const id = m.sp.node(i, r) * 3, v = (i * K + r) * 3; arr[v] = P[id]; arr[v + 1] = P[id + 1]; arr[v + 2] = P[id + 2]; }
      m.geo.getAttribute('position').needsUpdate = true; m.geo.computeVertexNormals(); m.geo.computeBoundingSphere();
    });
  }
  // Measured from where the loose paper is right now: each piece's twist, and how often each pair winds round.
  function measureLoose() {
    const L = st.loose, P = L.sim.pos, pt = id => [P[id * 3], P[id * 3 + 1], P[id * 3 + 2]];
    const cur = L.specs.map(sp => {
      const core = [], e0 = [], e1 = [];
      for (let i = 0; i < sp.M; i++) { const a = pt(sp.node(i, 0)), b = pt(sp.node(i, sp.K - 1)); core.push([(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2]); e0.push(a); e1.push(b); }
      return { core, e0, e1, flip: sp.flip };
    });
    const twist = cur.map(c => Math.abs(c.flip ? Lab.linking(c.core, c.e0.concat(c.e1)) : Lab.linking(c.e0, c.e1)));
    const links = [];
    for (let a = 0; a < cur.length; a++) for (let b = a + 1; b < cur.length; b++) links.push(Math.abs(Lab.linking(cur[a].core, cur[b].core)));
    return { twist, links };
  }
  const sameArr = (a, b) => a.length === b.length && a.every((v, i) => v === b[i]);
  function enterLoose() {
    clearTrace();
    if (st.k > LOOSE_MAXK) { Lab.toast(ch.stage, 'Eight or more thin strips are too many to shake here. Use One piece and Two pieces to follow them.', 3600); return false; }
    leaveLoose();
    const specs = looseSpecs(st.k), sim = new Lab.PaperSim(specs, RAD);
    const L = { sim, specs, meshes: specs.map(makeLooseMesh), t: 0, jiggle: 0, shake: 0.5, burst: 0, verifyT: 2.6, predicted: null, ok: null };
    st.loose = L; st.view = 'loose'; st.userCam = false;
    L.meshes.forEach(m => ch.scene.add(m.group));
    meshes.forEach(p => { p.group.visible = false; });
    syncLoose(); L.predicted = measureLoose();
    if (ctl.view) ctl.view.set('loose');
    hudRight(); applyShow(); renderReadout(); syncButtons();
    return true;
  }
  function leaveLoose() {
    const L = st.loose; if (!L) return;
    L.meshes.forEach(m => { ch.scene.remove(m.group); m.geo.dispose(); m.front.material.dispose(); m.back.material.dispose(); });
    st.loose = null;
    meshes.forEach(p => { p.group.visible = true; });
  }
  function looseHtml() {
    const L = st.loose; if (!L) return '';
    const m = count(st.k);
    const what = st.k === 0 ? 'Still one Möbius strip: one piece, one side.'
      : m === 1 ? 'Still <b>one piece</b>: nothing comes off however hard you shake. It is a single loop.'
        : `<b>${m} separate pieces</b>, and every pair is linked twice, so pulling only drags them against each other. None of them can come free.`;
    const chk = L.ok === false ? '<span class="miss">⚠</span> The simulated paper slipped through itself, which real paper can\'t. Press Undo a cut and cut again.'
      : L.ok ? `<span class="ok">✓</span> Measured on the loose paper just now: ${m === 1 ? (st.k === 0 ? 'still 1 half-twist' : `still ${L.predicted.twist[0]} full twists`) : 'every pair still linked twice'}.`
        : '<span style="color:var(--muted)">measuring the loose paper…</span>';
    return `<b>Loose paper.</b> ${what} ${chk}`;
  }
  function renderLoose() { const el = readout && readout.querySelector('[data-loose]'); if (el) el.innerHTML = looseHtml(); }
  // Keep everything in view until the person turns the camera.
  function fitLoose(dt) {
    const P = st.loose.sim.pos, N = st.loose.sim.N; let cx = 0, cy = 0, cz = 0;
    for (let i = 0; i < N; i++) { cx += P[i * 3]; cy += P[i * 3 + 1]; cz += P[i * 3 + 2]; }
    cx /= N; cy /= N; cz /= N;
    let r2 = 0; for (let i = 0; i < N; i += 3) { const d = (P[i * 3] - cx) ** 2 + (P[i * 3 + 1] - cy) ** 2 + (P[i * 3 + 2] - cz) ** 2; if (d > r2) r2 = d; }
    const cam = ch.camera, half = THREE.MathUtils.degToRad(cam.fov / 2), hfov = Math.atan(Math.tan(half) * cam.aspect);
    const want = Math.max(4.2, Math.sqrt(r2) / Math.sin(Math.min(half, hfov)) * 1.08);
    const tgt = ch.controls.target, k = Math.min(1, dt * 1.5);
    tgt.x += (cx - tgt.x) * k; tgt.y += (cy - tgt.y) * k; tgt.z += (cz - tgt.z) * k;
    const dir = cam.position.clone().sub(tgt), d = dir.length();
    cam.position.copy(tgt).add(dir.multiplyScalar((d + (want - d) * k) / d));
  }
  function shake() {
    if (st.cut || st.spread) return;
    if (!st.loose && !enterLoose()) return;
    st.loose.shake = 0.9; st.loose.sim.wake();
  }
  function pullApart() {
    if (st.cut || st.spread) return;
    if (!st.loose && !enterLoose()) return;
    st.loose.burst = 3; st.loose.sim.wake();
  }

  /* ---------------- tracing one loop ---------------- */
  // Your finger test: a marker runs along the middle of one piece until it is back where it started.
  // Whatever it marked on the way is one loop; anything it never touched is a separate piece.
  const TRACE_COLOR = 0x087f5b;
  function markerTexture() {
    const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d');
    g.fillStyle = '#ffffff'; g.strokeStyle = '#087f5b'; g.lineWidth = 10;
    g.beginPath(); g.arc(32, 32, 24, 0, TAU); g.fill(); g.stroke();
    const tex = new THREE.CanvasTexture(c); tex.encoding = THREE.sRGBEncoding; return tex;
  }
  // The marker's stripe: a narrow band down the middle of piece j, wherever that piece is right now.
  function traceSamples(j) {
    const L = st.loose;
    if (L) {
      const m = L.meshes.find(q => q.j === j), sp = m.sp, P = L.sim.pos, out = [];
      const at = (i, f) => { const a = sp.node(i, 0) * 3, b = sp.node(i, sp.K - 1) * 3; return [0, 1, 2].map(q => P[a + q] + (P[b + q] - P[a + q]) * f); };
      for (let i = 0; i <= sp.M; i++) out.push([at(i, 0.36), at(i, 0.64)]);
      return out;
    }
    const out = [];
    for (let i = 0; i <= SEG; i++) out.push([point(j, i, -0.28), point(j, i, 0.28)]);
    return out;
  }
  function clearTrace() {
    const T = st.trace; if (!T) return;
    ch.scene.remove(T.mesh, T.dot); T.mesh.geometry.dispose(); T.mesh.material.dispose(); T.dot.material.dispose();
    st.trace = null; showChip();
  }
  function startTrace() {
    if (st.cut || st.spread) return;
    clearTrace();
    const m = count(st.k), j = st.show !== 'all' && m > 1 ? st.sel[0] : 0, n = traceSamples(j).length - 1;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array((n + 1) * 6), 3));
    const idx = []; for (let i = 0; i < n; i++) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 2, a + 3, a + 1); }
    geo.setIndex(idx); geo.setDrawRange(0, 0);
    const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: TRACE_COLOR, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 }));
    const dot = new THREE.Sprite(new THREE.SpriteMaterial({ map: st.markerTex || (st.markerTex = markerTexture()), depthTest: false, transparent: true }));
    dot.renderOrder = 11;
    ch.scene.add(mesh, dot);
    st.trace = { j, n, t: 0, dur: st.k === 0 ? 3 : 5, mesh, dot, done: false };
    updateTrace(0);
  }
  function updateTrace(dt) {
    const T = st.trace; if (!T) return;
    T.t += dt;
    const p = Math.min(1, T.t / T.dur), k = Math.round(p * T.n), smp = traceSamples(T.j), arr = T.mesh.geometry.getAttribute('position').array;
    for (let i = 0; i <= k; i++) { arr.set(smp[i][0], i * 6); arr.set(smp[i][1], i * 6 + 3); }
    T.mesh.geometry.getAttribute('position').needsUpdate = true; T.mesh.geometry.computeBoundingSphere();
    T.mesh.geometry.setDrawRange(0, k * 6);
    const h = smp[k], sc = inStrip() || st.loose ? 0.16 : 0.24;
    T.dot.position.set((h[0][0] + h[1][0]) / 2, (h[0][1] + h[1][1]) / 2, (h[0][2] + h[1][2]) / 2); T.dot.scale.set(sc, sc, 1);
    if (p >= 1 && !T.done) {
      T.done = true;
      const m = count(st.k);
      Lab.toast(ch.stage, m === 1
        ? 'Back where it started, after going all the way along. Everything it marked is one single loop.'
        : `Back where it started, and it only marked piece ${T.j + 1}. ${m === 2 ? 'The other piece is' : `The other ${m - 1} pieces are`} separate.`, 4200);
    }
    showChip();
  }

  /* ---------------- cutting ---------------- */
  // Loose paper is cut where it was cut before: back to the strip as cut, cut, then let loose again.
  function cutNow() {
    if (st.cut || st.spread || st.k >= MAXK) return false;
    clearTrace();
    if (st.loose) {
      st.reloose = true; leaveLoose(); st.view = 'strip'; ctl.view.set('strip'); meshes.forEach(syncPiece);
      Lab.toast(ch.stage, 'Back to the strip as it was cut, for the next cut. Then it is let loose again.', 2600);
    }
    return startCut();
  }
  function startCut() {
    if (st.cut || st.spread || st.k >= MAXK) return false;
    const m = count(st.k), lines = [];
    for (let j = 0; j < m; j++) {
      const w = inStrip() ? (st.k === 0 ? W0 : W0 / 2 / m) : st.lay.w[j], ev = Math.min(0.4, Math.max(0.05, KERF / w));
      const pos = new Float32Array((SEG + 1) * 6), mid = [];
      for (let i = 0; i <= SEG; i++) { pos.set(point(j, i, -ev), i * 6); pos.set(point(j, i, ev), i * 6 + 3); mid.push(point(j, i, 0)); }
      const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.BufferAttribute(pos, 3)); geo.setIndex(ribbonIndex()); geo.setDrawRange(0, 0);
      const slit = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: 0x1b2140, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: Lab.scissorsTexture(), depthTest: false, transparent: true }));
      const sc = inStrip() ? 0.3 : 0.5; sprite.scale.set(sc, sc, 1); sprite.renderOrder = 10; sprite.position.set(...mid[0]);
      ch.scene.add(slit, sprite); cutObjs.push(slit, sprite); lines.push({ slit, sprite, mid });
    }
    st.cut = { t: 0, dur: st.k === 0 ? 2.0 : 2.4, lines };
    hud.right.textContent = m === 1 ? 'Scissors: along the middle line' : `${m} pairs of scissors, one per piece`;
    syncButtons();
    return true;
  }
  function finishCut() {
    clearCutObjs(); st.cut = null;
    const prev = st.lay, first = st.k === 0;
    st.k++;
    const target = layoutFor(st.k, st.thick);
    if (st.view === 'pulled' && !first) { st.lay = childLayout(prev, st.k); st.spread = { from: st.lay, to: target, t: 0, dur: 1.1 }; }
    else st.lay = target;
    rebuild(); afterLevel();
    if (first && st.view === 'pulled') Lab.toast(ch.stage, 'One long loop, pulled apart and laid out as a ring: twice as long, with 2 full twists.', 3200);
    if (st.reloose) {
      st.reloose = false;
      if (st.k <= LOOSE_MAXK) enterLoose();
      else { st.view = 'pulled'; ctl.view.set('pulled'); st.lay = layoutFor(st.k, st.thick); meshes.forEach(syncPiece); hudRight(); frame(); renderReadout(); Lab.toast(ch.stage, 'Too many thin strips to let loose after four cuts, so here is the drawing.', 3200); }
    }
  }
  function setLevel(k) {
    if (st.cut) { clearCutObjs(); st.cut = null; }
    clearTrace();
    const wasLoose = !!st.loose; leaveLoose();
    st.spread = null; st.k = k; st.lay = layoutFor(k, st.thick);
    if (wasLoose) st.view = 'strip';
    rebuild(); afterLevel();
    if (wasLoose) enterLoose();
  }
  const hudRight = () => { hud.right.textContent = st.loose ? 'loose paper' : st.k === 0 ? 'one side, one edge' : st.k === 1 ? 'two-sided, 2 full twists' : 'every pair linked twice'; };
  function afterLevel() {
    const m = count(st.k);
    hud.top.innerHTML = `<b>${st.k}</b> cut${st.k === 1 ? '' : 's'} · <b>${m}</b> piece${m === 1 ? '' : 's'}`;
    hudRight(); frame(); startMeasure(); renderReadout(); syncButtons();
  }
  function syncButtons() {
    if (!btn.cut) return;
    const busy = !!(st.cut || st.spread);
    btn.cut.disabled = busy || st.k >= MAXK;
    btn.cut.textContent = st.k >= MAXK ? 'Five cuts: the end of this run' : st.k === 0 ? '✂ Cut along the middle line' : '✂ Cut every piece along its middle';
    btn.back.disabled = busy || st.k === 0;
    btn.play.textContent = st.play ? '■ Stop' : '▶ Make all five cuts';
    btn.play.disabled = !st.play && st.k >= MAXK;
    const tooThin = st.k > LOOSE_MAXK;
    [btn.shake, btn.apart].forEach(b => { b.disabled = busy || tooThin; b.title = tooThin ? 'Too many thin strips to shake after three cuts' : ''; });
    btn.trace.disabled = busy;
  }

  /* ---------------- measuring the cut strip ---------------- */
  // Exact geometry, no thickening: twist = how often a piece's two edges wind round each other,
  // links = how often two pieces' middle lines do.
  function startMeasure() {
    const k = st.k, m = count(k);
    if (k === 0) { st.meas = null; return; }
    const curve = (j, v) => Array.from({ length: NS }, (_, i) => stripPoint(k, j, i / NS, v));
    const M = { k, jobs: [], total: 0, cores: [], twist: [], knots: [], links: [] };
    for (let j = 0; j < m; j++) M.jobs.push(() => { const c = curve(j, 0); M.cores[j] = c; M.twist[j] = Math.abs(Lab.linking(curve(j, -1), curve(j, 1))); M.knots[j] = Lab.knotDet(c); });
    for (let a = 0; a < m; a++) for (let b = a + 1; b < m; b++) M.jobs.push(() => { M.links.push(Math.abs(Lab.linking(M.cores[a], M.cores[b]))); });
    M.total = M.jobs.length; st.meas = M;
  }
  function stepMeasure(dt) {
    const M = st.meas; if (!M || !M.jobs.length) return;
    const t0 = performance.now();
    while (M.jobs.length && performance.now() - t0 < 7) M.jobs.shift()();
    st.measT -= dt;
    if (!M.jobs.length || st.measT <= 0) { st.measT = 0.25; renderMeasure(); showChip(); }
  }
  const pairIndex = (a, b, m) => a * m - a * (a + 1) / 2 + (b - a - 1);
  function showChip() {
    if (!hud.pick) return;
    const m = count(st.k), M = st.meas && st.meas.k === st.k ? st.meas : null, T = st.trace;
    if (T) {
      hud.pick.hidden = false;
      hud.pick.innerHTML = !T.done ? `Tracing piece <b>${T.j + 1}</b>… ${Math.round(Math.min(1, T.t / T.dur) * 100)}%`
        : m === 1 ? 'Back to the start: it is <b>one single loop</b>' : `Back to the start: piece <b>${T.j + 1}</b> is one loop of <b>${m}</b>`;
      return;
    }
    if (st.show === 'all') { hud.pick.hidden = true; return; }
    hud.pick.hidden = false;
    if (m === 1) {
      hud.pick.innerHTML = st.k === 0 ? 'Nothing cut yet: <b>one</b> Möbius strip' : st.show === 'one' ? 'This is the only piece: everything is <b>one single loop</b>' : 'Only <b>one</b> piece so far: cut again to get two';
      return;
    }
    const [a, b] = st.sel;
    if (st.show === 'one') {
      const tw = M && M.twist[a] != null ? `${M.twist[a]} full twists` : '2 full twists';
      hud.pick.innerHTML = `Piece <b>${a + 1}</b> of ${m}: one loop, twice as long, ${tw}`;
    } else {
      const lo = Math.min(a, b), hi = Math.max(a, b), li = pairIndex(lo, hi, m), lk = M && M.links[li] != null ? M.links[li] : 2;
      hud.pick.innerHTML = `Pieces <b>${lo + 1}</b> and <b>${hi + 1}</b>: they wind around each other ${lk === 2 ? 'twice' : lk + '×'}`;
    }
  }

  /* ---------------- readout ---------------- */
  function rowsHtml() {
    const rows = [];
    for (let k = 0; k <= MAXK; k++) {
      const m = count(k), pairs = m * (m - 1) / 2, w = MM / 2 ** k;
      const each = k === 0 ? 'Möbius strip: one side, 1 half-twist' : k === 1 ? 'two-sided loop, twice as long, 2 full twists' : 'the same kind of loop';
      rows.push(`<tr${k === st.k ? ' class="cur"' : ''}><td>${k}</td><td>${m}</td><td>${each}</td><td>${pairs ? pairs : '–'}</td><td>${w >= 10 ? w.toFixed(1) : w.toFixed(2).replace(/0$/, '')} mm</td></tr>`);
    }
    return rows.join('');
  }
  function summary() {
    const k = st.k, m = count(k), pairs = m * (m - 1) / 2;
    if (k === 0) return 'One Möbius strip: one side, one edge, one half-twist. Press the button to cut it along its middle line.';
    if (k === 1) return 'One long loop, twice as long as the Möbius strip, two-sided, with 2 full twists. The Möbius strip is gone for good: no later cut brings back a one-sided piece.';
    let s = `${m} loops. Each is twice as long as the Möbius strip with 2 full twists, and every pair of them is linked twice: ${pairs} linked pairs in all. The cut doubled the pieces and changed nothing else about them.`;
    if (k === MAXK) s += ' Real paper would be under a millimeter wide by now, which is why the strips here are thickened.';
    return s;
  }
  function measureHtml() {
    const M = st.meas;
    if (!M || M.k !== st.k) return st.k === 0 ? '' : '<span style="color:var(--muted)">measuring the cut strip…</span>';
    if (M.jobs.length) return `<span style="color:var(--muted)">Measuring the cut strip… ${M.total - M.jobs.length} of ${M.total}</span>`;
    const set = a => [...new Set(a)];
    const tw = set(M.twist), kn = set(M.knots), lk = set(M.links), m = count(M.k);
    const okAll = tw.length === 1 && tw[0] === 2 && kn.length === 1 && kn[0] === 1 && (m === 1 || (lk.length === 1 && lk[0] === 2));
    const what = m === 1 ? 'the loop has 2 full twists and no knot' : `every piece has 2 full twists and no knot, and all ${M.links.length} pairs are linked twice`;
    return okAll ? `<span class="ok">✓</span> Measured on the strip exactly as cut, before any thickening: ${what}.`
      : `<span class="miss">⚠</span> Measured: twists ${tw.join(', ')}, knots ${kn.join(', ')}, links ${lk.join(', ')}.`;
  }
  function renderMeasure() { const el = readout && readout.querySelector('[data-meas]'); if (el) el.innerHTML = measureHtml(); }
  function renderReadout() {
    if (!readout) return;
    readout.innerHTML = `<h4>After ${st.k} cut${st.k === 1 ? '' : 's'}</h4><p style="margin:0 0 8px">${summary()}</p>
      <div class="tbl-wrap"><table class="pieces halving"><thead><tr><th>Cuts</th><th>Pieces</th><th>Each piece</th><th>Linked pairs</th><th>Strip width</th></tr></thead><tbody>${rowsHtml()}</tbody></table></div>
      <p class="verdict-line" style="font-size:.875rem" data-meas>${measureHtml()}</p>
      ${st.loose ? `<p class="verdict-line" style="font-size:.875rem" data-loose>${looseHtml()}</p>` : ''}
      <p class="verdict-line" style="font-size:.8125rem;color:var(--muted)">Strip widths assume your first strip is 1 inch (25 mm) wide. Every linked pair winds around each other twice.</p>`;
  }

  /* ---------------- init ---------------- */
  ch.init = function (section, stage) {
    const { scene, camera, controls } = Lab.makeScene({ pos: [2.6, -4.2, 2.6] });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    pickTwistSign(); buildRing();
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.top = Lab.el('div', { class: 'chip' }); hud.right = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.top, hud.right);
    const bottom = Lab.el('div', { class: 'hud hud-bottom' });
    hud.pick = Lab.el('div', { class: 'chip' }); hud.pick.hidden = true;
    bottom.append(hud.pick);
    stage.append(hud.wrap, bottom);

    const c = section.querySelector('[data-controls]');
    const row = Lab.ui.row(Lab.ui.group(c, 'Do it'));
    btn.cut = Lab.ui.button(row, { label: '✂ Cut along the middle line', id: 'h-cut', primary: true, onClick: () => { st.play = false; cutNow(); syncButtons(); } });
    btn.back = Lab.ui.button(row, { label: 'Undo a cut', id: 'h-back', onClick: () => { st.play = false; setLevel(Math.max(0, st.k - 1)); } });
    btn.play = Lab.ui.button(row, { label: '▶ Make all five cuts', id: 'h-play', onClick: () => { st.play = !st.play; st.playT = 0.3; if (st.play && st.k >= MAXK) setLevel(0); syncButtons(); } });
    Lab.ui.button(row, { label: 'Start over', id: 'h-reset', onClick: () => { st.play = false; setLevel(0); } });
    ctl.view = Lab.ui.seg(c, { label: 'View', id: 'h-view', value: st.view, options: [{ value: 'pulled', label: 'Pulled apart' }, { value: 'strip', label: 'Inside the original strip' }, { value: 'loose', label: 'Loose paper' }],
      onChange: v => {
        if (st.cut || st.spread) { ctl.view.set(st.view); return; }
        clearTrace();
        if (v === 'loose') { if (!enterLoose()) ctl.view.set(st.view); return; }
        leaveLoose(); st.view = v; st.lay = layoutFor(st.k, st.thick); meshes.forEach(syncPiece);
        hudRight(); frame(); renderReadout(); syncButtons();
      } });
    const lg = Lab.ui.group(c, 'Test it');
    const lr = Lab.el('div', { class: 'btn-row' }); lg.append(lr);
    btn.trace = Lab.ui.button(lr, { label: '✎ Trace a loop', id: 'h-trace', onClick: startTrace });
    btn.shake = Lab.ui.button(lr, { label: 'Shake', id: 'h-shake', onClick: shake });
    btn.apart = Lab.ui.button(lr, { label: 'Pull apart', id: 'h-apart', onClick: pullApart });
    ctl.thick = Lab.ui.seg(c, { label: 'Strip width', id: 'h-width', value: 'thick', options: [{ value: 'thick', label: 'Thickened' }, { value: 'true', label: 'True width' }],
      onChange: v => { if (st.cut) { ctl.thick.set(st.thick ? 'thick' : 'true'); return; } st.thick = v === 'thick'; if (!inStrip()) { st.spread = { from: st.lay, to: layoutFor(st.k, st.thick), t: 0, dur: 0.8 }; } else st.lay = layoutFor(st.k, st.thick); } });
    const g = Lab.ui.group(c, 'Show');
    const sr = Lab.el('div', { class: 'btn-row' }); g.append(sr);
    ctl.show = Lab.ui.seg(sr, { label: null, id: 'h-show', value: 'all', options: [{ value: 'all', label: 'Every piece' }, { value: 'one', label: 'One piece' }, { value: 'two', label: 'Two pieces' }], onChange: v => { st.show = v; clearTrace(); applyShow(); } });
    ctl.show.el.querySelector('.lbl') && ctl.show.el.querySelector('.lbl').remove();
    Lab.ui.button(sr, { label: 'Pick others', id: 'h-pick', onClick: () => {
      const m = count(st.k); if (m < 2) return;
      st.picked = true;
      if (st.show === 'one') st.sel[0] = (st.sel[0] + 1) % m;
      else { const a = Math.floor(Math.random() * m); let b = Math.floor(Math.random() * (m - 1)); if (b >= a) b++; st.sel = [a, b]; }
      if (st.show === 'all') { st.show = 'two'; ctl.show.set('two'); }
      clearTrace(); applyShow();
    } });
    readout = section.querySelector('[data-readout]');
    controls.addEventListener('start', () => { st.userCam = true; });
    setLevel(0);
  };
  ch.enter = function () { frame(0.01); };
  ch.frame = function (dt) {
    if (!Lab.stepTween(ch, dt)) ch.controls.update();
    if (st.cut) {
      const C = st.cut; C.t += dt;
      const p = Math.min(1, C.t / C.dur), n = Math.floor(p * SEG);
      C.lines.forEach(L => { L.slit.geometry.setDrawRange(0, n * 6); L.sprite.position.set(...L.mid[n]); });
      if (p >= 1) finishCut();
    }
    if (st.spread) {
      const S = st.spread; S.t += dt;
      const e = Lab.smooth(Math.min(1, S.t / S.dur));
      st.lay = { off: S.from.off.map((o, j) => o + (S.to.off[j] - o) * e), w: S.from.w.map((w, j) => w + (S.to.w[j] - w) * e) };
      meshes.forEach(syncPiece);
      if (S.t >= S.dur) { st.spread = null; st.lay = S.to; frame(0.6); syncButtons(); }
    }
    if (st.play && !st.cut && !st.spread) {
      st.playT -= dt;
      if (st.playT <= 0) { if (st.k < MAXK) { cutNow(); st.playT = 1.6; } else { st.play = false; syncButtons(); } }
    }
    stepMeasure(dt);
    const L = st.loose;
    if (L) {
      const sim = L.sim; L.t += dt;
      sim.setBlend(Lab.smooth(Math.min(1, L.t / 2.2)));
      sim.rScale = Math.min(1, 0.3 + L.t / 1.6);
      if (L.shake && L.t > 2.4) { L.jiggle = L.shake; L.shake = 0; }
      if (L.jiggle > 0) { sim.wake(); sim.kick(0.016 * L.jiggle); L.jiggle = Math.max(0, L.jiggle - dt); }
      if (L.burst > 0) { L.burst -= dt; sim.wake(); }
      if (L.t > 2.4 && !sim.asleep) sim.spread(L.burst > 0 ? PUSH * BURST : PUSH, INFLATE);
      if (!sim.asleep) { sim.step(Math.min(dt, 1 / 30), sim.blend < 1 ? 6 : 4); sim.recenter(); syncLoose(); }
      if (!st.userCam && !ch._tween) fitLoose(dt);
      L.verifyT -= dt;
      if (L.t > 2.6 && L.verifyT <= 0 && L.jiggle <= 0) {
        L.verifyT = 2.5;
        const now = measureLoose(), ok = sameArr(now.twist, L.predicted.twist) && sameArr(now.links, L.predicted.links);
        if (ok !== L.ok) { L.ok = ok; renderLoose(); }
      }
    }
    if (st.trace) updateTrace(dt);
  };
  ch.leave = function () { st.play = false; };

  Lab.register(ch);
}
