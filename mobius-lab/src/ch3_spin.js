/* ============================================================
   Experiment 3: 720°, Dirac's belt trick.
   Every tether point at distance fraction s from the cube is
   rotated by the quaternion Q(s, t). Points at the same s share
   one rigid rotation and sit on one sphere, so tethers can never
   cross each other or the cube. Q(0,t) is the cube, Q(1,t) = 1.
   Q has period 720° in t: that is the two-turn memory.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const A = 0.48;              // cube half-size
  const RF = 2.6;              // frame half-size (tethers end at the walls' centres)
  const SEG = 72;              // segments per tether
  const TW = 0.16;             // tether width
  const st = { t: 0, playing: true, speed: 1, mode: 'belt', target: null, flash: 0, lastSign: 1 };
  const ch = { token: 'spin', gl: true, background: () => Lab.stageBg() };
  let cube, tethers = [], hud = {}, dial, readout;

  // Unit quaternion [w, x, y, z] for the belt trick.
  // The twist is concentrated near the cube so the far ends of the tethers stay calm.
  const prof = s => { const x = Math.min(1, s / 0.72); return x * x * (3 - 2 * x); };
  function beltQ(s, t) {
    const be = prof(s) * Math.PI / 2, sb = Math.sin(be), cb = Math.cos(be), c = Math.cos(t / 2), sn = Math.sin(t / 2);
    return [sb * sb + cb * cb * c, 0, sb * cb * (1 - c), cb * sn];
  }
  // "One-turn" tethers: the shortest rotation from the frame to the cube, which forgets which way round it went.
  function naiveQ(s, t) {
    let w = Math.cos(t / 2), z = Math.sin(t / 2);
    if (w < 0) { w = -w; z = -z; }
    const ang = 2 * Math.atan2(z, w) * (1 - prof(s));
    return [Math.cos(ang / 2), 0, 0, Math.sin(ang / 2)];
  }
  function applyQ(q, v, out) {
    // rotate vector v by unit quaternion q = [w,x,y,z]
    const [w, x, y, z] = q, vx = v[0], vy = v[1], vz = v[2];
    const ix = w * vx + y * vz - z * vy, iy = w * vy + z * vx - x * vz, iz = w * vz + x * vy - y * vx, iw = -x * vx - y * vy - z * vz;
    out[0] = ix * w + iw * -x + iy * -z - iz * -y;
    out[1] = iy * w + iw * -y + iz * -x - ix * -z;
    out[2] = iz * w + iw * -z + ix * -y - iy * -x;
    return out;
  }

  function makeCube() {
    const faceColors = ['#f27aa2', '#45bdb7', '#f1b93f', '#9f86f5', '#86cc58', '#ff9668'];
    const mats = faceColors.map((c, i) => {
      const cv = document.createElement('canvas'); cv.width = cv.height = 128; const g = cv.getContext('2d');
      g.fillStyle = c; g.fillRect(0, 0, 128, 128);
      g.strokeStyle = 'rgba(27,33,64,.35)'; g.lineWidth = 6; g.strokeRect(3, 3, 122, 122);
      if (i === 0) { // an arrow on one face so the orientation is easy to read
        g.fillStyle = '#1b2140'; g.beginPath(); g.moveTo(64, 18); g.lineTo(104, 62); g.lineTo(78, 62); g.lineTo(78, 108); g.lineTo(50, 108); g.lineTo(50, 62); g.lineTo(24, 62); g.closePath(); g.fill();
      }
      const tx = new THREE.CanvasTexture(cv); tx.encoding = THREE.sRGBEncoding;
      return new THREE.MeshStandardMaterial({ map: tx, roughness: 0.8 });
    });
    const m = new THREE.Mesh(new THREE.BoxGeometry(2 * A, 2 * A, 2 * A), mats);
    return m;
  }
  const TCOL = ['#f27aa2', '#45bdb7', '#f1b93f', '#9f86f5', '#86cc58', '#ff9668'];
  const DIRS = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]];
  function makeTethers() {
    // Each tether starts on the cube's circumscribed sphere (via a short rigid post), so it can never touch the cube.
    const r0 = A * Math.sqrt(3) * 1.04, r1 = RF;
    const postMat = new THREE.MeshStandardMaterial({ color: 0x1b2140, roughness: 0.5 });
    DIRS.forEach((dv, k) => {
      const d = new THREE.Vector3(...dv);
      const e = Math.abs(dv[2]) ? new THREE.Vector3(1, 0, 0) : Math.abs(dv[0]) ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(0, 0, 1);
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, r0 - A, 8), postMat);
      post.position.copy(d.clone().multiplyScalar((A + r0) / 2));
      post.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
      cube.add(post);
      const nv = (SEG + 1) * 2;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
      const uv = new Float32Array(nv * 2);
      for (let i = 0; i <= SEG; i++) for (let j = 0; j < 2; j++) { uv[(i * 2 + j) * 2] = i / SEG * (r1 - r0) / (TW * 3.2); uv[(i * 2 + j) * 2 + 1] = j; }
      geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      const idx = []; for (let i = 0; i < SEG; i++) { const a = i * 2, b = a + 2; idx.push(a, b, a + 1, b, b + 1, a + 1); }
      geo.setIndex(idx);
      const front = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(true, TCOL[k]), roughness: 0.85, side: THREE.FrontSide }));
      const back = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ map: Lab.paperTexture(false, TCOL[k]), roughness: 0.85, side: THREE.BackSide }));
      const grp = new THREE.Group(); grp.add(front, back);
      ch.scene.add(grp);
      const rest = [];
      for (let i = 0; i <= SEG; i++) {
        const sv = i / SEG, r = r0 + (r1 - r0) * sv;
        rest.push([[d.x * r + e.x * TW / 2, d.y * r + e.y * TW / 2, d.z * r + e.z * TW / 2], [d.x * r - e.x * TW / 2, d.y * r - e.y * TW / 2, d.z * r - e.z * TW / 2]]);
      }
      tethers.push({ geo, rest, mats: [front.material, back.material] });
    });
  }
  function makeFrame() {
    const g = new THREE.EdgesGeometry(new THREE.BoxGeometry(2 * RF, 2 * RF, 2 * RF));
    const line = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0x59608a, transparent: true, opacity: 0.45 }));
    ch.scene.add(line);
    const plate = new THREE.MeshStandardMaterial({ color: 0x1b2140, roughness: 0.6 });
    DIRS.forEach(dv => {
      const k = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.04, 20), plate);
      const d = new THREE.Vector3(...dv);
      k.position.copy(d.clone().multiplyScalar(RF));
      k.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d);
      ch.scene.add(k);
    });
  }
  function update() {
    const Qf = st.mode === 'belt' ? beltQ : naiveQ;
    const qc = Qf(0, st.t);
    cube.quaternion.set(qc[1], qc[2], qc[3], qc[0]);
    const out = [0, 0, 0];
    tethers.forEach(tt => {
      const arr = tt.geo.getAttribute('position').array;
      for (let i = 0; i <= SEG; i++) {
        const q = Qf(i / SEG, st.t);
        for (let j = 0; j < 2; j++) { applyQ(q, tt.rest[i][j], out); const v = (i * 2 + j) * 3; arr[v] = out[0]; arr[v + 1] = out[1]; arr[v + 2] = out[2]; }
      }
      tt.geo.getAttribute('position').needsUpdate = true;
      tt.geo.computeVertexNormals();
      tt.geo.computeBoundingSphere();
    });
  }
  function drawDial() {
    const { ctx, w, h } = Lab.fitCanvas(dial);
    ctx.clearRect(0, 0, w, h);
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule');
    const R = Math.min(w / 4, h / 2) - 16, cy = h / 2 - 6;
    const draw = (cx, ang, label, sub, col) => {
      ctx.strokeStyle = rule; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.stroke();
      for (let k = 0; k < 4; k++) { const a = -Math.PI / 2 + k * Math.PI / 2; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * (R - 6), cy + Math.sin(a) * (R - 6)); ctx.lineTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R); ctx.stroke(); }
      const a = -Math.PI / 2 + ang;
      ctx.strokeStyle = col; ctx.lineWidth = 4; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * (R - 8), cy + Math.sin(a) * (R - 8)); ctx.stroke();
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(cx, cy, 4, 0, TAU); ctx.fill();
      ctx.fillStyle = ink; ctx.font = `600 12px ${Lab.cssVar('--font-mono')}`; ctx.textAlign = 'center';
      ctx.fillText(label, cx, cy + R + 16);
      ctx.fillStyle = muted; ctx.font = `11px ${Lab.cssVar('--font-mono')}`; ctx.fillText(sub, cx, cy + R + 30);
    };
    draw(w * 0.27, st.t % TAU, 'cube', 'repeats every 360°', blue);
    const sign = Math.cos(st.t / 2) >= 0 ? '+' : '−';
    draw(w * 0.73, (st.t / 2) % TAU, `hidden sign ${sign}`, 'repeats every 720°', pink);
  }
  function statusText() {
    const deg = st.t * 180 / Math.PI;
    const m = ((deg % 720) + 720) % 720;
    const nearDeg = (x) => Math.abs(m - x) < 3 || Math.abs(m - x - 720) < 3;
    if (st.mode === 'naive') return 'One-turn tethers only remember the shortest way back, so each time the cube passes 180° they flip to the other side by jumping through each other. Real strings can\'t do that.';
    if (nearDeg(0) && deg > 5) return `720° done. Cube and tethers are both back where they started, and the tethers never crossed.`;
    if (nearDeg(360)) return 'The cube is back in its starting orientation, but the tethers are wound up. You cannot unwind them without turning the cube back. Keep going.';
    if (m < 360) return 'First turn: the tethers wind up as the cube turns.';
    return 'Second turn: the same rotation again, and now the tethers unwind themselves.';
  }

  const POSE = [[5.4, -6.6, 4.0], [0, 0, 0]];
  ch.init = function (section, stage) {
    const { scene, camera, controls } = Lab.makeScene({ pos: POSE[0], fov: 40 });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    controls.maxDistance = 20;
    cube = makeCube(); scene.add(cube);
    makeTethers(); makeFrame();
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.angle = Lab.el('div', { class: 'chip' }); hud.state = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.angle, hud.state);
    stage.append(hud.wrap);

    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Tethers', id: 'p-mode', value: 'belt', options: [{ value: 'belt', label: 'Belt trick' }, { value: 'naive', label: 'One-turn tethers' }], onChange: v => { st.mode = v; update(); } });
    const play = Lab.ui.seg(c, { label: 'Motion', id: 'p-play', value: 'play', options: [{ value: 'play', label: 'Spin' }, { value: 'pause', label: 'Pause' }], onChange: v => { st.playing = v === 'play'; st.target = null; } });
    Lab.ui.slider(c, { label: 'Speed', id: 'p-speed', min: 0.1, max: 2.5, step: 0.05, value: 1, format: v => v.toFixed(2) + '×', onInput: v => { st.speed = v; } });
    const row = Lab.ui.row(Lab.ui.group(c, 'Go to'));
    const goto = deg => { st.target = deg * Math.PI / 180; st.playing = false; play.set('pause'); };
    Lab.ui.button(row, { label: '0°', id: 'p-0', onClick: () => { st.t = 0; st.target = null; st.playing = false; play.set('pause'); update(); } });
    Lab.ui.button(row, { label: '360°', id: 'p-360', onClick: () => goto(360) });
    Lab.ui.button(row, { label: '720°', id: 'p-720', onClick: () => goto(720) });

    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `<h4>Two clocks</h4>
      <canvas data-dial class="plot short" aria-label="Two dials: the cube's angle, which repeats every 360 degrees, and the hidden sign, which repeats every 720 degrees"></canvas>
      <p class="verdict-line" data-status style="margin-top:6px"></p>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">The pink hand turns at half speed. That's how an electron's wave behaves: after one full turn it points backwards (a minus sign), and only after two turns is it back. Neutron experiments in 1975 measured exactly this.</p>`;
    dial = readout.querySelector('[data-dial]');
    hud.status = readout.querySelector('[data-status]');
    update();
  };
  ch.frame = function (dt) {
    if (!Lab.stepTween(ch, dt)) ch.controls.update();
    if (st.target != null) {
      const d = st.target - st.t, stepv = Math.sign(d) * Math.min(Math.abs(d), dt * 2.2 * st.speed);
      st.t += stepv; if (Math.abs(d) < 1e-4) { st.t = st.target; st.target = null; }
    } else if (st.playing) st.t += dt * 1.25 * st.speed;
    if (st.t > 4 * Math.PI * 50) st.t -= 4 * Math.PI * 50;
    const sign = Math.cos(st.t / 2) >= 0 ? 1 : -1;
    if (st.mode === 'naive') {
      const half = Math.floor((st.t + Math.PI) / TAU);
      if (half !== st.lastHalf) { if (st.lastHalf != null) { st.flash = 1; Lab.toast(ch.stage, 'Jump! The tethers just passed through each other.', 1500); } st.lastHalf = half; }
    } else st.lastHalf = null;
    st.flash = Math.max(0, st.flash - dt * 2);
    tethers.forEach(tt => tt.mats.forEach(m => m.emissive && m.emissive.setRGB(st.flash * 0.7, 0, 0)));
    update();
    const deg = st.t * 180 / Math.PI;
    hud.angle.innerHTML = `Cube turned <b>${deg.toFixed(0)}°</b>`;
    const m = ((deg % 720) + 720) % 720;
    const home = st.mode === 'belt' && (m < 4 || m > 716);
    const wound = st.mode === 'belt' && Math.abs(m - 360) < 4;
    hud.state.textContent = st.mode === 'naive' ? 'one-turn tethers' : home ? 'everything back' : wound ? 'cube back, tethers wound up' : (m < 360 ? 'turn 1' : 'turn 2');
    hud.state.className = 'chip' + (wound ? ' alert' : home && deg > 5 ? ' good' : '');
    hud.status.textContent = statusText();
    drawDial();
    st.lastSign = sign;
  };
  ch.debugSet = deg => { st.t = deg * Math.PI / 180; st.playing = false; st.target = null; update(); return deg; };
  Lab.register(ch);
}
