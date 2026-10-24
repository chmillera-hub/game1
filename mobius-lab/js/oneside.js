/* One Side — the explainer guide as a simulation. The ant's path is the finger, the camera is the eyes.
   Consciousness sees a short window ahead; emotions remember monsters and predict ones it cannot see. */
(function () {
  'use strict';
  const ML = window.ML, C = ML.C, TAU = ML.TAU;
  const R = 1, W = 0.34;                 // core radius, half-width of the strip
  const NU = 360, NV = 6;
  const TEXW = 2048, TEXH = 192;

  const st = {
    n: 1, speed: 0.8, lane: 0, walking: true, emotions: true, quad: false,
    tau: 0, sigma: 0, travelled: 0, stun: 0, legPh: 0,
    monsters: [], memory: [], bumpsOn: 0, bumpsOff: 0, lapsOn: 0, lapsOff: 0, fear: 0, seen: 0,
    visF: new Uint8Array(NU), visB: new Uint8Array(NU), flash: 0,
  };
  let scene, cam, orbit, app, band, frontMesh, backMesh, frontTex, backTex, fctx, bctx, ant, ghost, fan, tape;
  let ro, hud = {}, paintDirty = 0;

  const trackLen = () => (st.n % 2 ? 2 : 1) * TAU;
  // track coordinate (τ, σ) → paper coordinate (t, s, face). Odd strips: the second lap is the other face.
  function paperOf(tau, sigma) {
    const L = trackLen();
    tau = ((tau % L) + L) % L;
    const lap = Math.floor(tau / TAU), t = tau - lap * TAU;
    const flip = st.n % 2 === 1 && lap === 1;
    return { t, s: flip ? -sigma : sigma, face: flip ? -1 : 1 };
  }
  function trackOf(t, s, face) {
    if (face > 0) return { tau: t, sigma: s };
    if (st.n % 2 === 1) return { tau: t + TAU, sigma: -s };
    return null; // the far face of a two-sided strip is not on the ant's path
  }
  const P = [0, 0, 0], N = [0, 0, 0], Tg = [0, 0, 0];
  function surf(t, s, face, lift) {
    ML.band.P(t, s, st.n, R, P); ML.band.normal(t, s, st.n, R, N);
    return new THREE.Vector3(P[0] + N[0] * face * lift, P[1] + N[1] * face * lift, P[2] + N[2] * face * lift);
  }

  // ------------------------------------------------------------------ paper textures
  function paintBase() {
    const g = fctx;
    g.globalCompositeOperation = 'source-over';
    g.fillStyle = '#f39abc'; g.fillRect(0, 0, TEXW, TEXH);
    g.strokeStyle = 'rgba(52,64,170,0.75)'; g.lineWidth = 3;
    const nLines = 52;
    for (let i = 0; i < nLines; i++) { const x = ((i + 0.5) / nLines) * TEXW; g.beginPath(); g.moveTo(x, 6); g.lineTo(x, TEXH - 6); g.stroke(); }
    g.strokeStyle = 'rgba(200,40,70,0.55)'; g.lineWidth = 2; g.beginPath(); g.moveTo(0, 14); g.lineTo(TEXW, 14); g.stroke();
    const b = bctx;
    b.fillStyle = '#e57ea6'; b.fillRect(0, 0, TEXW, TEXH);
    for (const g2 of [g, b]) {
      const img = g2.getImageData(0, 0, TEXW, TEXH), d = img.data;
      for (let i = 0; i < d.length; i += 4) { const k = (Math.random() - 0.5) * 10; d[i] += k; d[i + 1] += k; d[i + 2] += k; }
      g2.putImageData(img, 0, 0);
    }
    if (frontTex) { frontTex.needsUpdate = true; backTex.needsUpdate = true; }
    st.visF.fill(0); st.visB.fill(0);
  }
  function paint(t, s, face) {
    const g = face > 0 ? fctx : bctx;
    const u = t / TAU, v = (s + W) / (2 * W);
    const x = u * TEXW, y = (1 - v) * TEXH;
    g.fillStyle = 'rgba(30,26,60,0.85)';
    g.beginPath(); g.arc(x, y, 6, 0, TAU); g.fill();
    if (x < 8) { g.beginPath(); g.arc(x + TEXW, y, 6, 0, TAU); g.fill(); }
    if (x > TEXW - 8) { g.beginPath(); g.arc(x - TEXW, y, 6, 0, TAU); g.fill(); }
    const bin = Math.min(NU - 1, Math.floor(u * NU));
    (face > 0 ? st.visF : st.visB)[bin] = 1;
    paintDirty++;
  }

  // ------------------------------------------------------------------ meshes
  function buildBand() {
    if (band) { scene.remove(band); band.traverse((o) => o.geometry && o.geometry.dispose()); }
    const pos = new Float32Array((NU + 1) * (NV + 1) * 3), uv = new Float32Array((NU + 1) * (NV + 1) * 2), idx = [];
    for (let i = 0; i <= NU; i++) for (let j = 0; j <= NV; j++) {
      const t = (i / NU) * TAU, s = -W + (2 * W * j) / NV, k = i * (NV + 1) + j;
      ML.band.P(t, s, st.n, R, P);
      pos[3 * k] = P[0]; pos[3 * k + 1] = P[1]; pos[3 * k + 2] = P[2];
      uv[2 * k] = i / NU; uv[2 * k + 1] = j / NV;
    }
    for (let i = 0; i < NU; i++) for (let j = 0; j < NV; j++) {
      const a = i * (NV + 1) + j, b = a + NV + 1;
      idx.push(a, a + 1, b, b, a + 1, b + 1);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setIndex(idx); geo.computeVertexNormals();
    // check winding: make the geometric front face match the parametric normal Pt × Ps
    const nrm = geo.attributes.normal, n0 = ML.band.normal(0.3, 0, st.n, R, [0, 0, 0]);
    const k0 = Math.round((0.3 / TAU) * NU) * (NV + 1) + NV / 2;
    if (nrm.getX(k0) * n0[0] + nrm.getY(k0) * n0[1] + nrm.getZ(k0) * n0[2] < 0) {
      for (let q = 0; q < idx.length; q += 3) { const tmp = idx[q + 1]; idx[q + 1] = idx[q + 2]; idx[q + 2] = tmp; }
      geo.setIndex(idx); geo.computeVertexNormals();
    }
    band = new THREE.Group();
    frontMesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: frontTex, side: THREE.FrontSide, roughness: 0.85, metalness: 0 }));
    backMesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: backTex, side: THREE.BackSide, roughness: 0.9, metalness: 0 }));
    frontMesh.userData.face = 1; backMesh.userData.face = -1;
    band.add(frontMesh, backMesh);
    // the tape joint at t = 0
    const tp = [], ti = [];
    for (const face of [1, -1]) for (let i = 0; i <= 8; i++) for (let j = 0; j <= 1; j++) {
      const t = -0.05 + (0.1 * i) / 8, v = surf((t + TAU) % TAU, -W * 1.02 + 2.04 * W * j, face, 0.004);
      tp.push(v.x, v.y, v.z);
    }
    for (let f = 0; f < 2; f++) for (let i = 0; i < 8; i++) { const a = f * 18 + i * 2; ti.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
    const tg = new THREE.BufferGeometry(); tg.setAttribute('position', new THREE.Float32BufferAttribute(tp, 3)); tg.setIndex(ti); tg.computeVertexNormals();
    tape = new THREE.Mesh(tg, new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.28, roughness: 0.15, metalness: 0.1, side: THREE.DoubleSide, depthWrite: false }));
    band.add(tape);
    scene.add(band);
  }

  function makeAnt(opacity) {
    const g = new THREE.Group();
    const mat = new THREE.MeshStandardMaterial({ color: 0x1d1612, roughness: 0.45, metalness: 0.1, transparent: opacity < 1, opacity });
    const sph = (rx, ry, rz, x) => { const m = new THREE.Mesh(new THREE.SphereGeometry(1, 14, 10), mat); m.scale.set(rx, ry, rz); m.position.set(x, ry * 0.9, 0); g.add(m); return m; };
    sph(0.026, 0.017, 0.018, -0.035); sph(0.016, 0.013, 0.013, 0.0); sph(0.014, 0.012, 0.012, 0.028);
    g.userData.legs = [];
    const legGeo = new THREE.CylinderGeometry(0.0022, 0.0022, 0.045, 5);
    for (let k = 0; k < 6; k++) {
      const side = k < 3 ? 1 : -1, x = -0.012 + (k % 3) * 0.012;
      const pivot = new THREE.Group(); pivot.position.set(x, 0.012, 0);
      const leg = new THREE.Mesh(legGeo, mat); leg.rotation.x = side * 1.05; leg.position.set(0, -0.005, side * 0.02);
      pivot.add(leg); g.add(pivot); g.userData.legs.push([pivot, side, k]);
    }
    const antGeo = new THREE.CylinderGeometry(0.0015, 0.0015, 0.035, 4);
    for (const side of [1, -1]) { const a = new THREE.Mesh(antGeo, mat); a.position.set(0.045, 0.03, side * 0.009); a.rotation.set(side * 0.4, 0, -0.9); g.add(a); }
    // the ant's "left hand": an arrow across the strip, to track orientation round the loop
    const arrow = new THREE.ArrowHelper(new THREE.Vector3(0, 0, 1), new THREE.Vector3(0, 0.03, 0), 0.13, opacity < 1 ? 0x86dcb4 : 0xf3c96e, 0.04, 0.025);
    if (opacity < 1) { arrow.line.material.transparent = true; arrow.line.material.opacity = 0.7; arrow.cone.material.transparent = true; arrow.cone.material.opacity = 0.7; }
    g.add(arrow);
    return g;
  }
  function orient(obj, t, s, face, lift) {
    const p = surf(t, s, face, lift);
    ML.band.Pt(t, s, st.n, R, Tg); ML.band.normal(t, s, st.n, R, N);
    const f = new THREE.Vector3(Tg[0], Tg[1], Tg[2]).normalize();
    const u = new THREE.Vector3(N[0] * face, N[1] * face, N[2] * face);
    const z = new THREE.Vector3().crossVectors(f, u).normalize();
    const m = new THREE.Matrix4().makeBasis(f, u, z);
    obj.position.copy(p); obj.quaternion.setFromRotationMatrix(m);
  }

  // monsters: spiky red blobs drawn on one face of the paper
  const monGeo = (() => {
    const g = new THREE.IcosahedronGeometry(0.045, 1), p = g.attributes.position;
    for (let i = 0; i < p.count; i++) { const k = 1 + (i % 3 === 0 ? 0.55 : 0); p.setXYZ(i, p.getX(i) * k, p.getY(i) * k * 0.7, p.getZ(i) * k); }
    g.computeVertexNormals(); return g;
  })();
  const monMat = new THREE.MeshStandardMaterial({ color: 0xd03b3b, roughness: 0.5, emissive: 0x3a0606 });
  const eyeMat = new THREE.MeshBasicMaterial({ color: 0xffffff }), pupMat = new THREE.MeshBasicMaterial({ color: 0x111111 });
  function addMonster(t, s, face) {
    const m = new THREE.Group();
    m.add(new THREE.Mesh(monGeo, monMat));
    for (const z of [-0.012, 0.012]) {
      const e = new THREE.Mesh(new THREE.SphereGeometry(0.009, 8, 6), eyeMat); e.position.set(0.02, 0.022, z); m.add(e);
      const pp = new THREE.Mesh(new THREE.SphereGeometry(0.0045, 6, 4), pupMat); pp.position.set(0.027, 0.024, z); m.add(pp);
    }
    const mon = { t, s, face, obj: m, lastBump: -99 };
    orient(m, t, s, face, 0.02);
    scene.add(m); st.monsters.push(mon);
    return mon;
  }
  function clearMonsters() { for (const m of st.monsters) scene.remove(m.obj); st.monsters = []; }
  function randomMonsters(k) {
    for (let i = 0; i < k; i++) {
      const face = st.n % 2 ? (Math.random() < 0.5 ? 1 : -1) : 1;
      addMonster(0.6 + Math.random() * (TAU - 1.2), (Math.random() - 0.5) * W * 1.2, face);
    }
  }
  // fear's predictions: translucent red glows where it expects monsters, even on the face you can't see
  const fearMat = new THREE.MeshBasicMaterial({ color: 0xff4d5e, transparent: true, opacity: 0.3, depthWrite: false });
  const fearGeo = new THREE.SphereGeometry(0.07, 14, 10);
  function syncFear() {
    for (const m of st.memory) {
      if (!m.obj) { m.obj = new THREE.Mesh(fearGeo, fearMat.clone()); scene.add(m.obj); }
      const pp = paperOf(m.tau, m.sigma);
      m.obj.position.copy(surf(pp.t, pp.s, pp.face, 0.03));
      m.obj.material.opacity = (st.emotions ? 0.42 : 0.12) * m.conf;
      m.obj.visible = m.conf > 0.08;
    }
  }

  // ------------------------------------------------------------------ the ant's walk
  const dTau = (a, b) => { const L = trackLen(); return (((b - a) % L) + L) % L; };   // how far ahead b is from a
  const SIGHT = 0.5, HORIZON = 3.2;
  function walk(dt) {
    const L = trackLen();
    st.stun = Math.max(0, st.stun - dt);
    const v = st.walking && st.stun === 0 ? st.speed : 0;
    // what consciousness sees: monsters on the ant's own path, a short way ahead
    const threats = [];
    st.seen = 0;
    for (const m of st.monsters) {
      const tr = trackOf(m.t, m.s, m.face); if (!tr) continue;
      const d = dTau(st.tau, tr.tau);
      if (d > 0 && d < SIGHT) { st.seen++; threats.push({ d, sigma: tr.sigma, w: 1 }); remember(tr.tau, tr.sigma, 0.6); }
    }
    // what emotions predict: remembered monsters further ahead, including on the face out of view
    st.fear = 0;
    for (const m of st.memory) {
      const d = dTau(st.tau, m.tau);
      if (d > 0 && d < HORIZON) {
        st.fear += m.conf * (1 - d / HORIZON);
        if (st.emotions && d >= SIGHT) threats.push({ d, sigma: m.sigma, w: m.conf });
      }
    }
    // the same planner either way (consciousness, the CEO): a short dynamic-programming plan over lanes that
    // respects how fast the ant can sidestep. Only the information differs: sight alone, or sight + memory.
    const lat = 0.16;
    let target = st.lane * W;
    if (threats.length && st.speed > 0) {
      const NL = 13, sp = (1.7 * W) / (NL - 1);                     // lanes from −0.85W to +0.85W
      const dTs = Math.max(0.05, (st.speed * sp) / lat);             // track distance per one-lane sidestep
      const K = Math.min(60, Math.ceil(HORIZON / dTs) + 1);
      const laneS = (l) => -0.85 * W + l * sp;
      const home = Math.round((st.lane * W + 0.85 * W) / sp);
      let next = new Float64Array(NL), cur = new Float64Array(NL);
      for (let l = 0; l < NL; l++) next[l] = 0.02 * Math.abs(l - home);
      const choice = new Int8Array(NL);
      for (let k = K - 1; k >= 1; k--) {
        const tk = k * dTs;
        for (let l = 0; l < NL; l++) {
          let dz = 0;
          for (const t of threats) { const a1 = (laneS(l) - t.sigma) / 0.09, a2 = (tk - t.d) / Math.max(0.07, dTs * 0.6); dz += t.w * Math.exp(-a1 * a1 - a2 * a2); }
          let bst = Infinity;
          for (let m = Math.max(0, l - 1); m <= Math.min(NL - 1, l + 1); m++) { const c = next[m] + 0.004 * Math.abs(m - l); if (c < bst) bst = c; }
          cur[l] = dz * 4 + bst;
        }
        const tmp = next; next = cur; cur = tmp;
      }
      const l0 = ML.clamp(Math.round((st.sigma + 0.85 * W) / sp), 0, NL - 1);
      let bl = l0, bc = Infinity;
      for (let m = Math.max(0, l0 - 1); m <= Math.min(NL - 1, l0 + 1); m++) { const c = next[m] + 0.004 * Math.abs(m - l0) + (m === l0 ? -1e-6 : 0); if (c < bc) { bc = c; bl = m; } }
      target = laneS(bl);
    }
    const ds = ML.clamp(target - st.sigma, -lat * dt, lat * dt);
    st.sigma = ML.clamp(st.sigma + (v > 0 ? ds : 0), -0.85 * W, 0.85 * W);

    const pp = paperOf(st.tau, st.sigma);
    ML.band.Pt(pp.t, pp.s, st.n, R, Tg);
    const dtau = (v * dt) / Math.hypot(Tg[0], Tg[1], Tg[2]);
    const before = Math.floor(st.travelled / TAU);
    st.tau = (st.tau + dtau) % L; st.travelled += dtau;
    if (st.emotions) st.lapsOn += dtau / TAU; else st.lapsOff += dtau / TAU;
    if (Math.floor(st.travelled / TAU) !== before) hud.flashLap = 1.4;

    // bumps
    for (const m of st.monsters) {
      const tr = trackOf(m.t, m.s, m.face); if (!tr) continue;
      const d = Math.min(dTau(st.tau, tr.tau), dTau(tr.tau, st.tau));
      if (d < 0.05 && Math.abs(st.sigma - tr.sigma) < 0.085 && st.travelled - m.lastBump > 1) {
        m.lastBump = st.travelled; st.stun = 0.7; st.flash = 0.6;
        if (st.emotions) st.bumpsOn++; else st.bumpsOff++;
        remember(tr.tau, tr.sigma, 1);
      }
    }
    for (const m of st.memory) m.conf *= Math.exp(-dt / 45);
    st.memory = st.memory.filter((m) => { if (m.conf < 0.05) { if (m.obj) scene.remove(m.obj); return false; } return true; });

    const p2 = paperOf(st.tau, st.sigma);
    if (v > 0) paint(p2.t, p2.s, p2.face);
    st.legPh += v * dt * 90;
  }
  function remember(tau, sigma, c) {
    const L = trackLen();
    for (const m of st.memory) {
      const fwd = dTau(m.tau, tau), d = fwd > L / 2 ? fwd - L : fwd;          // shortest signed gap round the loop
      if (Math.abs(d) < 0.25 && Math.abs(m.sigma - sigma) < 0.1) {
        m.tau = (((m.tau + 0.5 * d) % L) + L) % L; m.sigma = ML.lerp(m.sigma, sigma, 0.5); m.conf = Math.max(m.conf, c); return;
      }
    }
    st.memory.push({ tau, sigma, conf: c });
  }

  // ------------------------------------------------------------------ consciousness window (a lit fan ahead of the ant)
  function buildFan() {
    const n = 24, pos = new Float32Array((n + 1) * 2 * 3), col = new Float32Array((n + 1) * 2 * 3), idx = [];
    for (let i = 0; i < n; i++) { const a = 2 * i; idx.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(idx);
    fan = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
    fan.userData.n = n;
    scene.add(fan);
  }
  function updateFan() {
    const n = fan.userData.n, pos = fan.geometry.attributes.position.array, col = fan.geometry.attributes.color.array;
    for (let i = 0; i <= n; i++) {
      const tau = st.tau + (SIGHT * i) / n, half = 0.05 + (0.45 * W * i) / n;
      for (let j = 0; j < 2; j++) {
        const sg = ML.clamp(st.sigma + (j ? half : -half), -W, W), pp = paperOf(tau, sg), v = surf(pp.t, pp.s, pp.face, 0.006), k = i * 2 + j;
        pos[3 * k] = v.x; pos[3 * k + 1] = v.y; pos[3 * k + 2] = v.z;
        const fade = 0.55 * (1 - i / n);
        col[3 * k] = 0.95 * fade; col[3 * k + 1] = 0.79 * fade; col[3 * k + 2] = 0.43 * fade;
      }
    }
    fan.geometry.attributes.position.needsUpdate = true; fan.geometry.attributes.color.needsUpdate = true;
  }

  // ------------------------------------------------------------------ what the eyes see from this camera
  function eyes() {
    const cp = cam.position, K = 180;
    let lined = 0, folds = 0, first = 0, prev = 0;
    for (let i = 0; i < K; i++) {
      const t = (i / K) * TAU;
      ML.band.P(t, 0, st.n, R, P); ML.band.normal(t, 0, st.n, R, N);
      const f = N[0] * (cp.x - P[0]) + N[1] * (cp.y - P[1]) + N[2] * (cp.z - P[2]);
      const sg = f >= 0 ? 1 : -1;
      if (sg > 0) lined++;
      if (i === 0) first = sg; else if (sg !== prev) folds++;
      prev = sg;
    }
    const wrapSign = st.n % 2 ? -first : first;   // at the tape joint the faces swap on a Möbius strip
    if (prev !== wrapSign) folds++;
    return { lined: lined / K, folds };
  }

  // ------------------------------------------------------------------ panel
  const IDEAS = `
    <p class="quote">"It has one side to my finger, but to my eyes it has two sides… so are you saying there are multiple truths?"</p>
    <div><h4>What the sim does</h4><ul>
      <li><b>The ant's path is your finger.</b> It never crosses an edge. On the Möbius strip it paints the ruled face and the blank face in one unbroken line. On the plain loop (0 half-twists) it never reaches the blank face.</li>
      <li><b>The camera is your eyes.</b> The readout counts how much of the loop shows its ruled face to you, and how many places you see it edge-on. Spin the view and those numbers change. The finger's answer doesn't.</li>
      <li><b>720°.</b> The green ghost marks where the ant started. After one lap it is upside-down under the ghost, on the other face, with its arrow pointing the other way. Only after two laps does it match again.</li>
      <li><b>Consciousness vs emotions.</b> The lit fan is what the ant sees: a short way ahead on its own face. Fear remembers monsters it has met (red glows, even under the paper). The ant plans its path the same way in both modes; muting emotions only takes away what fear knows.</li>
      <li><b>What the numbers show:</b> at a slow walk, sight alone is enough and both modes stay clean. Speed the ant up and only the version that listens to fear keeps avoiding bumps. Prediction matters most when the world moves faster than you can see.</li>
    </ul></div>
    <div class="hook"><h4>Where this meets real physics and science</h4><ul>
      <li><b>The finger is right in a precise sense.</b> A Möbius strip is <i>non-orientable</i>: there is no consistent way to label one face "front". That is a theorem, not a matter of opinion. Your eyes aren't wrong either. They report a local view, and both reports fit together.</li>
      <li><b>720° is real physics.</b> Electrons need a 720° turn to return to their starting state. Dirac's belt trick shows the same bookkeeping with a belt. Your ant shows it with a path. It's an analogy, but the counting is the same.</li>
      <li><b>Prediction from memory</b> is close to "predictive processing", a serious research program on emotion and perception (Lisa Feldman Barrett, Karl Friston). In that view feelings are the brain's forecasts about what it can't directly see.</li>
    </ul></div>
    <div><h4>Something the sim shows that's easy to miss</h4><ul>
      <li>Emotions aren't always right. Press <b>Shuffle monsters</b> after fear has learned the old spots: it raises false alarms until its memories fade and it relearns. Good prediction needs updating, not just volume.</li>
    </ul></div>`;

  const mode = {
    id: 'oneside', tab: 'One Side', kind: '3d',
    buildPanel(el) {
      const U = ML.ui;
      U.head(el, 'One side, two truths', 'Your explainer guide on a strip. The ant is the finger, the camera is the eyes, and fear predicts what neither can see yet.');
      const s1 = U.block(el, 'The strip');
      U.seg(s1, { id: 'o-n', label: 'Half-twists before taping', options: [[0, '0 · plain loop'], [1, '1 · Möbius'], [2, '2'], [3, '3']], value: st.n, onChange: (v) => { st.n = v; rebuild(); } });
      U.slider(s1, { id: 'o-speed', label: 'Ant speed', min: 0.2, max: 1.2, step: 0.05, value: st.speed, fmt: (v) => v.toFixed(2) + ' u/s', onInput: (v) => (st.speed = v) });
      U.slider(s1, { id: 'o-lane', label: 'Ant lane (across the strip)', min: -0.7, max: 0.7, step: 0.05, value: st.lane, fmt: (v) => (v === 0 ? 'centre' : v > 0 ? 'right ' + Math.round(v * 100) + '%' : 'left ' + Math.round(-v * 100) + '%'), onInput: (v) => (st.lane = v) });
      const b = U.buttons(s1, [
        { label: 'Pause ant', id: 'o-walk', onClick: () => { st.walking = !st.walking; b[0].textContent = st.walking ? 'Pause ant' : 'Walk'; } },
        { label: 'Erase paint', id: 'o-erase', onClick: () => paintBase() },
      ]);
      const s2 = U.block(el, 'Look with your eyes');
      U.buttons(s2, [
        { label: 'Face-on', id: 'o-v-face', onClick: () => orbit.animateTo({ phi: 0.06, theta: orbit.theta, radius: 3.6 }) },
        { label: 'Edge-on', id: 'o-v-edge', onClick: () => orbit.animateTo({ phi: Math.PI / 2, theta: Math.PI / 2, radius: 3.6 }) },
        { label: 'Three-quarter', id: 'o-v-34', onClick: () => orbit.animateTo({ phi: 1.0, theta: 0.6, radius: 3.6 }) },
      ]);
      U.toggle(s2, { id: 'o-quad', label: 'Four monitors (top, front, side, free)', value: st.quad, onChange: (v) => { st.quad = v; hud.quad.hidden = !v; } });
      const s3 = U.block(el, 'Monsters and emotions');
      U.toggle(s3, { id: 'o-emo', label: 'Listen to emotions (fear steers early)', value: st.emotions, onChange: (v) => (st.emotions = v) });
      U.buttons(s3, [
        { label: 'Add monster', id: 'o-add', onClick: () => randomMonsters(1) },
        { label: 'Shuffle monsters', id: 'o-shuffle', onClick: () => { const k = st.monsters.length; clearMonsters(); randomMonsters(k); } },
        { label: 'Clear', id: 'o-clear', onClick: () => clearMonsters() },
      ]);
      s3.append(ML.el('p', { class: 'tip', text: 'Click anywhere on the strip to draw a monster on that face.' }));
      const s4 = U.block(el, 'Readouts');
      ro = U.readouts(s4, [
        ['laps', 'Laps walked'], ['finger', 'Finger says'], ['faces', 'Paint on ruled · blank face'], ['turn', 'Ant vs start marker'],
        ['eyes', 'Eyes see ruled face on'], ['folds', 'Edge-on spots in view'], ['seen', 'Consciousness sees'], ['fear', 'Fear (predicted danger)'],
        ['bon', 'Bumps per lap, emotions on'], ['boff', 'Bumps per lap, emotions muted'],
      ]);
      U.ideas(el, IDEAS);
    },
    buildHud(el) {
      hud.lap = ML.el('div', { class: 'tag tl big' });
      hud.sub = ML.el('div', { class: 'tag', style: 'top:48px;left:max(12px, env(safe-area-inset-left, 0px))' });
      hud.note = ML.el('div', { class: 'tag hand', style: 'top:82px;left:max(14px, env(safe-area-inset-left, 0px))' });
      hud.tip = ML.el('div', { class: 'tag bl wide-only', text: 'Drag to turn the strip · scroll to zoom · click the strip to draw a monster' });
      hud.quad = ML.quadHud();
      el.append(hud.lap, hud.sub, hud.note, hud.tip, hud.quad);
    },
    init(a) {
      app = a;
      if (!a.getRenderer()) return;
      scene = new THREE.Scene();
      cam = new THREE.PerspectiveCamera(38, 1, 0.05, 100);
      ML.paperLights(scene);
      ML.floorGrid(scene, -0.75);
      const fc = document.createElement('canvas'); fc.width = TEXW; fc.height = TEXH; fctx = fc.getContext('2d', { willReadFrequently: true });
      const bc = document.createElement('canvas'); bc.width = TEXW; bc.height = TEXH; bctx = bc.getContext('2d', { willReadFrequently: true });
      frontTex = new THREE.CanvasTexture(fc); backTex = new THREE.CanvasTexture(bc);
      frontTex.anisotropy = backTex.anisotropy = 4;
      paintBase();
      buildBand();
      ant = makeAnt(1); ghost = makeAnt(0.35);
      scene.add(ant, ghost);
      buildFan();
      orbit = new ML.Orbit(a.gl, { theta: 0.6, phi: 1.0, radius: 3.6, minR: 1.6, maxR: 9 });
      orbit.autoSpin = a.reduced ? 0 : 0.05;
      orbit.onClick = (x, y, w, h) => {
        if (ML.app.current !== mode) return;
        const pk = ML.pickView(cam, st.quad, x, y, w, h);
        const rc = new THREE.Raycaster(); rc.setFromCamera({ x: pk.nx, y: pk.ny }, pk.cam);
        const hit = rc.intersectObjects([frontMesh, backMesh], false)[0];
        if (!hit || !hit.uv) return;
        addMonster(hit.uv.x * TAU, hit.uv.y * 2 * W - W, hit.object.userData.face);
      };
      rebuild(true);
    },
    enter() { if (orbit) orbit.enabled = true; },
    exit() { if (orbit) orbit.enabled = false; },
    resize() {},
    frame(dt) {
      if (!scene) return;
      walk(dt);
      const pp = paperOf(st.tau, st.sigma);
      orient(ant, pp.t, pp.s, pp.face, 0.002);
      for (const [pivot, side, k] of ant.userData.legs) pivot.rotation.y = Math.sin(st.legPh + (k % 2) * Math.PI) * 0.45 * side;
      ant.visible = !(st.flash > 0 && Math.floor(st.flash * 20) % 2);
      st.flash = Math.max(0, st.flash - dt);
      updateFan();
      syncFear();
      for (const m of st.monsters) m.obj.rotation.y += 0; // static
      if (paintDirty > 2) { frontTex.needsUpdate = true; backTex.needsUpdate = true; paintDirty = 0; }
      orbit.update(dt); orbit.apply(cam, app.w / app.h);
      ML.render3D(app.renderer, scene, cam, st.quad, app.w, app.h, 4.6);
      updatePanel(dt);
    },
    _st: st, _walk: (dt) => walk(dt), _rebuild: () => rebuild(), _random: (k) => randomMonsters(k),
  };

  function rebuild(first) {
    st.tau = 0; st.sigma = 0; st.travelled = 0; st.lapsOn = st.lapsOff = 0; st.bumpsOn = st.bumpsOff = 0;
    for (const m of st.memory) if (m.obj) scene.remove(m.obj);
    st.memory = [];
    clearMonsters();
    paintBase();
    buildBand();
    orient(ghost, 0, 0, 1, 0.002);
    randomMonsters(first ? 3 : 3);
  }

  let pt = 0;
  function updatePanel(dt) {
    hud.flashLap = Math.max(0, (hud.flashLap || 0) - dt);
    pt -= dt; if (pt > 0) return; pt = 0.15;
    const laps = st.travelled / TAU, odd = st.n % 2 === 1;
    const lapsWhole = Math.floor(laps);
    hud.lap.textContent = 'Lap ' + (laps + 1).toFixed(2).replace(/\.?0+$/, '') ;
    hud.lap.textContent = 'Laps walked ' + laps.toFixed(2);
    const pp = paperOf(st.tau, st.sigma);
    const onFace = pp.face > 0 ? 'the ruled face' : 'the blank face';
    hud.sub.textContent = 'Ant is on ' + onFace + (odd ? ' · same path, no edge crossed' : '');
    let note = '';
    if (odd) note = lapsWhole % 2 === 1 ? 'one lap (360°): upside-down under the start marker' : lapsWhole >= 2 ? 'two laps (720°): back where it started' : '';
    else note = lapsWhole >= 1 ? 'two-sided loop: it never reaches the blank face' : '';
    hud.note.textContent = note;
    let f = 0, b = 0; for (let i = 0; i < NU; i++) { f += st.visF[i]; b += st.visB[i]; }
    ro.set('laps', laps.toFixed(2));
    ro.set('finger', odd ? '1 side (one unbroken path)' : '2 sides (path stays on one)');
    ro.set('faces', ML.pct(f / NU) + ' · ' + ML.pct(b / NU));
    ro.set('turn', odd ? (lapsWhole % 2 ? 'flipped (other face)' : 'matching') : 'matching');
    const e = eyes();
    ro.meter('eyes', ML.pct(e.lined) + ' of the loop', e.lined);
    ro.set('folds', String(e.folds) + (odd ? ' (always odd)' : ' (always even)'));
    ro.set('seen', st.seen ? st.seen + ' monster' + (st.seen > 1 ? 's' : '') + ' ahead' : 'nothing ahead');
    ro.meter('fear', st.fear.toFixed(2) + (st.emotions ? '' : ' (muted)'), Math.min(1, st.fear / 1.5));
    ro.set('bon', st.lapsOn > 0.2 ? (st.bumpsOn / st.lapsOn).toFixed(2) + ' (' + st.bumpsOn + ' in ' + st.lapsOn.toFixed(1) + ')' : '—');
    ro.set('boff', st.lapsOff > 0.2 ? (st.bumpsOff / st.lapsOff).toFixed(2) + ' (' + st.bumpsOff + ' in ' + st.lapsOff.toFixed(1) + ')' : 'mute emotions to measure');
  }

  ML.register(mode);
})();
