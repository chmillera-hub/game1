/* ============================================================
   Experiment 1: Finger vs. Eyes
   An ant paints whichever face it walks on. Its flag shows the
   local "up" (the surface normal), which flips after one lap on
   a Möbius strip: the Z2 twist.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const R = 1.25, W = 0.62, SEGU = 240, SEGV = 8, NV = SEGV + 1;
  const BINS_PER_LAP = 12;
  const PAINT = '#16a6c9';

  const st = {
    n: 1, phi: 0, speed: 0.9, view: 'eyes', paused: false,
    painted: [new Uint8Array(SEGU + 1), new Uint8Array(SEGU + 1)],
    lastCol: -1, lastFace: 0,
    monsters: false, sens: 1, fear: [], truth: [], present: [], prepared: [], monsterMeshes: [],
    stats: { ouch: 0, dodged: 0, alarms: 0 }, sAnt: 0, slow: 1, lastBin: -1, hitFlash: 0
  };

  const ch = { token: 'finger', gl: true, background: () => Lab.stageBg() };
  let band = null, ant = null, flag = null, legs = [], startFlag = null, hud = {}, readout, fearCanvas;

  function routeLaps() { return st.n % 2 ? 2 : 1; }
  function binsTotal() { return BINS_PER_LAP * routeLaps(); }

  function buildBand() {
    if (band) { ch.scene.remove(band.group); band.geoF.dispose(); band.geoB.dispose(); }
    const geoF = Lab.bandGeometry({ n: st.n, chi: 1, R, W, segU: SEGU, segV: SEGV, tile: W * 1.6 });
    const geoB = new THREE.BufferGeometry();
    ['position', 'normal', 'uv'].forEach(k => geoB.setAttribute(k, geoF.getAttribute(k)));
    geoB.setIndex(geoF.getIndex());
    const cnt = (SEGU + 1) * NV;
    geoF.setAttribute('color', new THREE.BufferAttribute(new Float32Array(cnt * 3), 3));
    geoB.setAttribute('color', new THREE.BufferAttribute(new Float32Array(cnt * 3), 3));
    const mF = new THREE.Mesh(geoF, Lab.paintMaterial(Lab.paperTexture(true), PAINT, THREE.FrontSide));
    const mB = new THREE.Mesh(geoB, Lab.paintMaterial(Lab.paperTexture(false), PAINT, THREE.BackSide));
    const group = new THREE.Group(); group.add(mF, mB);
    ch.scene.add(group);
    band = { group, geoF, geoB };
    resetPaint();
  }
  function resetPaint() {
    st.painted[0].fill(0); st.painted[1].fill(0);
    if (!band) return;
    [band.geoF, band.geoB].forEach(g => { g.getAttribute('color').array.fill(0); g.getAttribute('color').needsUpdate = true; });
    st.lastCol = -1;
  }
  function paintColumn(face, i) {
    const odd = st.n % 2 === 1;
    const mark = (f, c) => {
      if (st.painted[f][c]) return;
      st.painted[f][c] = 1;
      const g = f === 0 ? band.geoF : band.geoB;
      const arr = g.getAttribute('color').array;
      for (let j = 0; j < NV; j++) arr[(c * NV + j) * 3] = 1;
      g.getAttribute('color').needsUpdate = true;
    };
    mark(face, i);
    // the seam column is shared with the start of the next lap's face
    if (i === 0) mark(odd ? 1 - face : face, SEGU);
    if (i === SEGU) mark(odd ? 1 - face : face, 0);
  }
  function paintFraction() {
    let c = 0;
    for (let i = 0; i < SEGU; i++) c += st.painted[0][i] + st.painted[1][i];
    return c / (2 * SEGU);
  }

  function makeAnt() {
    const g = new THREE.Group();
    const ink = new THREE.MeshStandardMaterial({ color: 0x1b2140, roughness: 0.55, metalness: 0.1 });
    const sph = (r, z, y, sx = 1, sy = 1, sz = 1) => { const m = new THREE.Mesh(new THREE.SphereGeometry(r, 14, 10), ink); m.position.set(0, y, z); m.scale.set(sx, sy, sz); g.add(m); return m; };
    sph(0.021, 0.055, 0.03);
    sph(0.018, 0.02, 0.028, 1, 1, 1.3);
    sph(0.03, -0.035, 0.034, 0.95, 0.9, 1.35);
    const legGeo = new THREE.CylinderGeometry(0.0035, 0.0035, 0.06, 5);
    for (let k = 0; k < 6; k++) {
      const side = k < 3 ? 1 : -1, row = k % 3;
      const pivot = new THREE.Group();
      pivot.position.set(0.012 * side, 0.026, 0.035 - row * 0.022);
      const leg = new THREE.Mesh(legGeo, ink);
      leg.position.set(0.024 * side, -0.012, 0);
      leg.rotation.z = side * 1.05;
      pivot.add(leg); g.add(pivot);
      legs.push({ pivot, phase: (k % 2 ? Math.PI : 0) + row * 0.6 });
    }
    const antGeo = new THREE.CylinderGeometry(0.0025, 0.0025, 0.05, 4);
    [-1, 1].forEach(s => { const a = new THREE.Mesh(antGeo, ink); a.position.set(0.012 * s, 0.05, 0.085); a.rotation.set(1.0, 0, -0.35 * s); g.add(a); });
    // flag shows the ant's local "up"
    const f = new THREE.Group();
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.0035, 0.0035, 0.2, 6), ink);
    pole.position.y = 0.13;
    const clothGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0.23, 0), new THREE.Vector3(0, 0.16, 0), new THREE.Vector3(0, 0.195, -0.1)]);
    clothGeo.computeVertexNormals();
    const cloth = new THREE.Mesh(clothGeo, new THREE.MeshStandardMaterial({ color: 0xffc83d, side: THREE.DoubleSide, roughness: 0.5, emissive: 0x3a2a00 }));
    f.add(pole, cloth);
    f.position.z = -0.03;
    g.add(f);
    g.scale.setScalar(1.55);
    return { group: g, flag: f };
  }
  function makeStartFlag() {
    // a ghost of the ant's flag, left where the ant started
    const g = new THREE.Group();
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x1b2140, transparent: true, opacity: 0.55 });
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.31, 6), poleMat); pole.position.y = 0.155;
    const clothGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0.31, 0), new THREE.Vector3(0, 0.2, 0), new THREE.Vector3(0, 0.255, -0.15)]);
    clothGeo.computeVertexNormals();
    const cloth = new THREE.Mesh(clothGeo, new THREE.MeshStandardMaterial({ color: 0xffc83d, side: THREE.DoubleSide, transparent: true, opacity: 0.45 }));
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.05, 0.075, 24), new THREE.MeshBasicMaterial({ color: 0x1b2140, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
    ring.rotation.x = -Math.PI / 2; ring.position.y = 0.004;
    g.add(pole, cloth, ring);
    return g;
  }
  function makeMonster() {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new THREE.IcosahedronGeometry(0.055, 1), new THREE.MeshStandardMaterial({ color: 0x8e2bd6, roughness: 0.6, flatShading: true }));
    g.add(body);
    const spikeMat = new THREE.MeshStandardMaterial({ color: 0xd8306b, roughness: 0.5 });
    const spikeGeo = new THREE.ConeGeometry(0.014, 0.05, 6);
    const dirs = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, -1], [.7, .7, 0], [-.7, .7, 0], [0, .7, .7], [0, .7, -.7]];
    dirs.forEach(d => { const s = new THREE.Mesh(spikeGeo, spikeMat); const v = new THREE.Vector3(...d).normalize(); s.position.copy(v).multiplyScalar(0.058); s.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v); g.add(s); });
    const eyeW = new THREE.MeshBasicMaterial({ color: 0xffffff }), eyeB = new THREE.MeshBasicMaterial({ color: 0x111111 });
    [-1, 1].forEach(s => { const e = new THREE.Mesh(new THREE.SphereGeometry(0.016, 10, 8), eyeW); e.position.set(0.02 * s, 0.02, 0.045); const p = new THREE.Mesh(new THREE.SphereGeometry(0.008, 8, 6), eyeB); p.position.set(0.02 * s, 0.02, 0.059); g.add(e, p); });
    return g;
  }

  function antPose(phi, s) {
    const f = Lab.bandFrame(phi, s, st.n, 1, R, W);
    return f; // normal is continuous in phi; for odd n it flips after 2π
  }
  function orient(obj, pos, fwd, up) {
    const z = fwd.clone().normalize(), y = up.clone().sub(z.clone().multiplyScalar(up.dot(z))).normalize(), x = new THREE.Vector3().crossVectors(y, z);
    const m = new THREE.Matrix4().makeBasis(x, y, z);
    obj.quaternion.setFromRotationMatrix(m);
    obj.position.copy(pos);
  }

  /* ---------------- monsters ---------------- */
  function resetMonsters() {
    const B = binsTotal();
    st.fear = new Array(B).fill(0.15);
    st.truth = new Array(B).fill(0.03);
    const hot = st.n % 2 ? [4, 5, 16, 17] : [4, 5];
    hot.forEach(b => { st.truth[b] = 0.85; });
    st.present = new Array(B).fill(false);
    st.prepared = new Array(B).fill(false);
    st.monsterMeshes.forEach(m => m && ch.scene.remove(m));
    st.monsterMeshes = new Array(B).fill(null);
    st.stats = { ouch: 0, dodged: 0, alarms: 0 };
    st.lastBin = -1;
    updateReadout();
  }
  function binCenterPhi(b) { return (b + 0.5) * TAU / BINS_PER_LAP; }
  function spawnFor(b) {
    const B = binsTotal();
    b = ((b % B) + B) % B;
    if (st.monsterMeshes[b]) { ch.scene.remove(st.monsterMeshes[b]); st.monsterMeshes[b] = null; }
    st.present[b] = Math.random() < st.truth[b];
    if (!st.present[b]) return;
    const m = makeMonster();
    const f = antPose(binCenterPhi(b), 0);
    const pos = f.p.clone().add(f.normal.clone().multiplyScalar(0.075));
    orient(m, pos, f.tangent.clone().negate(), f.normal);
    ch.scene.add(m);
    st.monsterMeshes[b] = m;
  }
  function onEnterBin(b) {
    const B = binsTotal();
    spawnFor(b + 3);
    const next = (b + 1) % B;
    st.prepared[next] = st.sens * st.fear[next] > 0.5;
  }
  function resolveBin(b) {
    const was = st.present[b], prep = st.prepared[b];
    if (was && prep) { st.stats.dodged++; }
    else if (was && !prep) { st.stats.ouch++; st.hitFlash = 1; Lab.toast(ch.stage, 'Ouch. Fear was quiet here.', 1400); }
    else if (!was && prep) { st.stats.alarms++; }
    st.fear[b] += 0.5 * ((was ? 1 : 0) - st.fear[b]);
    if (st.monsterMeshes[b]) { ch.scene.remove(st.monsterMeshes[b]); st.monsterMeshes[b] = null; }
    st.present[b] = false;
    updateReadout();
  }
  function drawFearMap() {
    if (!fearCanvas || fearCanvas.hidden) return;
    const { ctx, w, h } = Lab.fitCanvas(fearCanvas);
    ctx.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, B = binsTotal(), laps = routeLaps();
    const ink = Lab.cssVar('--ink'), pink = Lab.cssVar('--pink'), rule = Lab.cssVar('--rule');
    for (let b = 0; b < B; b++) {
      const lap = Math.floor(b / BINS_PER_LAP), k = b % BINS_PER_LAP;
      const r0 = 18 + lap * 22, r1 = r0 + 18;
      const a0 = -k * TAU / BINS_PER_LAP, a1 = -(k + 1) * TAU / BINS_PER_LAP;
      ctx.beginPath(); ctx.arc(cx, cy, r1, a0, a1, true); ctx.arc(cx, cy, r0, a1, a0, false); ctx.closePath();
      ctx.globalAlpha = 1; ctx.fillStyle = rule; ctx.fill();
      ctx.globalAlpha = Lab.clamp(st.fear[b], 0, 1); ctx.fillStyle = pink; ctx.fill();
      ctx.globalAlpha = 1;
    }
    const lapNow = Math.floor((st.phi % (TAU * laps)) / TAU), th = st.phi % TAU;
    const rr = 27 + lapNow * 22;
    ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(cx + rr * Math.cos(-th), cy + rr * Math.sin(-th), 4, 0, TAU); ctx.fill();
  }
  function updateReadout() {
    if (!readout) return;
    const s = st.stats;
    readout.querySelector('[data-k=ouch]').textContent = s.ouch;
    readout.querySelector('[data-k=dodged]').textContent = s.dodged;
    readout.querySelector('[data-k=alarms]').textContent = s.alarms;
  }

  /* ---------------- views ---------------- */
  const POSE_EYES = [[2.9, -3.4, 2.4], [0, 0, 0]];
  const POSE_EDGE = [[0, -4.7, 0.02], [0, 0, 0]];
  function setView(v) {
    st.view = v;
    flag.visible = v !== 'ant';
    ch.camera.fov = v === 'ant' ? 62 : 40; ch.camera.updateProjectionMatrix();
    if (v === 'ant') { ch.controls.enabled = false; return; }
    ch.camera.up.set(0, 0, 1);
    ch.controls.enabled = true;
    const p = v === 'edge' ? POSE_EDGE : POSE_EYES;
    Lab.tweenCamera(ch, p[0], p[1], 0.9);
  }

  ch.init = function (section, stage) {
    const { scene, camera, controls } = Lab.makeScene({ pos: POSE_EYES[0] });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    const wood = Lab.woodTexture().clone(); wood.needsUpdate = true; wood.repeat.set(2, 2);
    const desk = new THREE.Mesh(new THREE.PlaneGeometry(10, 10), new THREE.MeshStandardMaterial({ map: wood, roughness: 0.92 }));
    desk.position.z = -1.0; scene.add(desk);
    buildBand();
    const a = makeAnt(); ant = a.group; flag = a.flag; scene.add(ant);
    startFlag = makeStartFlag(); scene.add(startFlag);
    placeStartFlag();

    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.lap = Lab.el('div', { class: 'chip', text: 'Lap 0.00' });
    hud.paint = Lab.el('div', { class: 'chip', text: 'Painted 0%' });
    hud.wrap.append(hud.lap, hud.paint);
    hud.bottom = Lab.el('div', { class: 'hud hud-bottom' });
    hud.flag = Lab.el('div', { class: 'chip', text: 'Flag matches the start' });
    hud.fear = Lab.el('div', { class: 'chip', hidden: '' });
    hud.bottom.append(hud.flag, hud.fear);
    stage.append(hud.wrap, hud.bottom);

    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Shape', id: 'f-shape', value: 1, options: [{ value: 1, label: 'Möbius strip' }, { value: 0, label: 'Plain ring' }],
      onChange: v => { st.n = v; st.phi = 0; buildBand(); placeStartFlag(); if (st.monsters) resetMonsters(); } });
    Lab.ui.seg(c, { label: 'View', id: 'f-view', value: 'eyes', options: [{ value: 'eyes', label: 'Eyes' }, { value: 'edge', label: 'Edge-on' }, { value: 'ant', label: 'Ant cam' }], onChange: setView });
    Lab.ui.slider(c, { label: 'Ant speed', id: 'f-speed', min: 0, max: 3, step: 0.05, value: st.speed, format: v => v.toFixed(2) + '×', onInput: v => { st.speed = v; } });
    const row = Lab.ui.row(Lab.ui.group(c, 'Paint'));
    Lab.ui.button(row, { label: 'Wipe paint', id: 'f-wipe', onClick: () => { resetPaint(); st.phi = st.n % 2 ? st.phi % TAU : st.phi; } });
    Lab.ui.seg(c, { label: 'Monsters', id: 'f-mon', value: 'off', options: [{ value: 'off', label: 'Off' }, { value: 'on', label: 'On' }],
      onChange: v => { st.monsters = v === 'on'; readout.hidden = !st.monsters; hud.fear.hidden = !st.monsters; sensCtl.el.hidden = !st.monsters; resetMonsters(); } });
    const sensCtl = Lab.ui.slider(c, { label: 'Fear sensitivity', id: 'f-sens', min: 0, max: 6, step: 0.1, value: 1,
      format: v => (v === 0 ? 'silenced' : v < 0.7 ? 'low' : v <= 1.6 ? 'calibrated' : 'jumpy'), onInput: v => { st.sens = v; } });
    sensCtl.el.hidden = true;

    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `<h4>Monster log</h4>
      <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center">
        <div class="stats" style="flex:1 1 220px">
          <div class="stat"><div class="v" data-k="ouch">0</div><div class="k">Ouch (missed warnings)</div></div>
          <div class="stat"><div class="v" data-k="dodged">0</div><div class="k">Dodged (good warnings)</div></div>
          <div class="stat"><div class="v" data-k="alarms">0</div><div class="k">False alarms (slowed for nothing)</div></div>
        </div>
        <div style="flex:0 0 150px;text-align:center">
          <canvas data-fear style="width:150px;height:118px" aria-label="Fear's map: how strongly fear expects a monster at each stretch of the route"></canvas>
          <div style="font-size:.75rem;color:var(--muted);line-height:1.35">Fear's map: darker means it expects a monster. On the Möbius strip the inner ring is lap 1 and the outer ring is lap 2.</div>
        </div>
      </div>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">Monsters mostly hide on the far side, where your eyes can't see them from the default view. Fear learns that from experience. Try silenced, calibrated and jumpy, then compare the log.</p>`;
    fearCanvas = readout.querySelector('[data-fear]');
    readout.hidden = true;
    resetMonsters();
  };
  function placeStartFlag() {
    const f = antPose(0, 0);
    orient(startFlag, f.p.clone().add(f.normal.clone().multiplyScalar(0.005)), f.tangent, f.normal);
  }

  ch.leave = function () { if (st.view === 'ant') { st.view = 'eyes'; } };
  ch.enter = function () {
    const segBtn = document.getElementById('f-view-eyes');
    if (st.view === 'eyes' && segBtn) { /* keep */ }
  };

  ch.frame = function (dt, t) {
    const laps = routeLaps();
    // monsters: slow down while preparing for a predicted monster
    let speedFactor = 1;
    const B = binsTotal();
    const route = st.phi % (TAU * laps);
    const bin = Math.floor(route / (TAU / BINS_PER_LAP)) % B;
    if (st.monsters) {
      if (bin !== st.lastBin) {
        if (st.lastBin >= 0) resolveBin(st.lastBin);
        st.lastBin = bin;
        onEnterBin(bin);
      }
      const prep = st.prepared[bin];
      speedFactor = prep ? 0.35 : 1;
      st.sAnt += ((prep ? 0.55 : 0) - st.sAnt) * Math.min(1, dt * 6);
      const nextB = (bin + 1) % B;
      const lvl = Lab.clamp(st.sens * st.fear[nextB], 0, 1);
      hud.fear.innerHTML = `Fear ahead <b>${'▮'.repeat(Math.round(lvl * 6))}${'▯'.repeat(6 - Math.round(lvl * 6))}</b>`;
      drawFearMap();
    } else {
      st.sAnt += (0 - st.sAnt) * Math.min(1, dt * 6);
    }
    st.phi += st.speed * speedFactor * dt * 0.9;

    const f = antPose(st.phi, st.sAnt);
    const up = f.normal;
    orient(ant, f.p.clone().add(up.clone().multiplyScalar(0.012)), f.tangent, up);
    const stepPh = st.phi * 34;
    legs.forEach(l => { l.pivot.rotation.x = Math.sin(stepPh + l.phase) * 0.5 * Math.min(1, st.speed * speedFactor + 0.05); });
    if (st.hitFlash > 0) { st.hitFlash = Math.max(0, st.hitFlash - dt * 2.5); ant.position.add(up.clone().multiplyScalar(Math.sin(st.hitFlash * Math.PI) * 0.06)); }

    // paint the face the ant is on
    const odd = st.n % 2 === 1;
    const face = odd ? Math.floor(st.phi / TAU) % 2 : 0;
    const col = Math.min(SEGU, Math.floor((st.phi % TAU) / TAU * SEGU));
    if (st.lastCol < 0) { paintColumn(face, col); }
    else if (col !== st.lastCol || face !== st.lastFace) {
      let c = st.lastCol, fc = st.lastFace, guard = 0;
      while ((c !== col || fc !== face) && guard++ < SEGU * 2) {
        c++;
        if (c > SEGU - 1) { c = 0; fc = odd ? 1 - fc : fc; }
        paintColumn(fc, c);
      }
    }
    st.lastCol = col; st.lastFace = face;

    const lapsDone = st.phi / TAU;
    hud.lap.innerHTML = `Lap <b>${lapsDone.toFixed(2)}</b>`;
    const frac = paintFraction();
    hud.paint.innerHTML = `Painted <b>${Math.round(frac * 100)}%</b> of the paper` + (odd ? '' : (frac > 0.49 ? ' · the inside is unreachable' : ''));
    const flipped = odd && face === 1;
    hud.flag.textContent = flipped ? 'Flag flipped vs. the start, and no edge was crossed' : 'Flag matches the start';
    hud.flag.className = 'chip' + (flipped ? ' alert' : '');

    if (st.view === 'ant') {
      const camPos = ant.position.clone().add(up.clone().multiplyScalar(0.3)).add(f.tangent.clone().multiplyScalar(-0.7));
      ch.camera.position.lerp(camPos, Math.min(1, dt * 8));
      ch.camera.up.lerp(up, Math.min(1, dt * 8)).normalize();
      const ahead = antPose(st.phi + 0.75, 0);
      ch.camera.lookAt(ahead.p.clone().add(ahead.normal.clone().multiplyScalar(0.08)));
    } else if (!Lab.stepTween(ch, dt)) {
      ch.controls.update();
    }
  };

  Lab.register(ch);
}
