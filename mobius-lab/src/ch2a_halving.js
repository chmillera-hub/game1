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
   drawn wider than real paper so they show.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const R0 = 1.25, W0 = 0.9, CHI = 1;                   // the Möbius strip
  const RB = 2.5, HB = 0.5;                             // the long loop laid out: ring radius, saddle height
  const MAXK = 5, SEG = 360, NS = 1440, KERF = 0.006;   // most cuts; mesh segments; measuring samples; cut width
  const THICK = 0.1, THICK_GAP = 0.04;                 // thickened width and spacing of the pieces
  const MM = 25;                                        // a 1-inch first strip, in mm
  const count = k => (k === 0 ? 1 : 2 ** (k - 1));
  const st = { k: 0, view: 'pulled', thick: true, show: 'all', sel: [0, 1], picked: false, cut: null, spread: null, lay: null, meas: null, play: false, playT: 0, twistSign: 1, measT: 0 };
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
  const inStrip = () => st.view === 'strip' || st.k === 0;
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
    meshes.forEach(p => {
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

  /* ---------------- cutting ---------------- */
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
  }
  function setLevel(k) {
    if (st.cut) { clearCutObjs(); st.cut = null; }
    st.spread = null; st.k = k; st.lay = layoutFor(k, st.thick);
    rebuild(); afterLevel();
  }
  function afterLevel() {
    const m = count(st.k);
    hud.top.innerHTML = `<b>${st.k}</b> cut${st.k === 1 ? '' : 's'} · <b>${m}</b> piece${m === 1 ? '' : 's'}`;
    hud.right.textContent = st.k === 0 ? 'one side, one edge' : st.k === 1 ? 'two-sided, 2 full twists' : 'every pair linked twice';
    frame(); startMeasure(); renderReadout(); syncButtons();
  }
  function syncButtons() {
    if (!btn.cut) return;
    const busy = !!(st.cut || st.spread);
    btn.cut.disabled = busy || st.k >= MAXK;
    btn.cut.textContent = st.k >= MAXK ? 'Five cuts: the end of this run' : st.k === 0 ? '✂ Cut along the middle line' : '✂ Cut every piece along its middle';
    btn.back.disabled = busy || st.k === 0;
    btn.play.textContent = st.play ? '■ Stop' : '▶ Make all five cuts';
    btn.play.disabled = !st.play && st.k >= MAXK;
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
    const m = count(st.k), M = st.meas && st.meas.k === st.k ? st.meas : null;
    if (st.show === 'all' || m === 1) { hud.pick.hidden = true; return; }
    hud.pick.hidden = false;
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
    btn.cut = Lab.ui.button(row, { label: '✂ Cut along the middle line', id: 'h-cut', primary: true, onClick: () => { st.play = false; startCut(); syncButtons(); } });
    btn.back = Lab.ui.button(row, { label: 'Undo a cut', id: 'h-back', onClick: () => { st.play = false; setLevel(Math.max(0, st.k - 1)); } });
    btn.play = Lab.ui.button(row, { label: '▶ Make all five cuts', id: 'h-play', onClick: () => { st.play = !st.play; st.playT = 0.3; if (st.play && st.k >= MAXK) setLevel(0); syncButtons(); } });
    Lab.ui.button(row, { label: 'Start over', id: 'h-reset', onClick: () => { st.play = false; setLevel(0); } });
    ctl.view = Lab.ui.seg(c, { label: 'View', id: 'h-view', value: st.view, options: [{ value: 'pulled', label: 'Pulled apart' }, { value: 'strip', label: 'Inside the original strip' }],
      onChange: v => { if (st.cut) { ctl.view.set(st.view); return; } st.view = v; st.spread = null; st.lay = layoutFor(st.k, st.thick); meshes.forEach(syncPiece); frame(); syncButtons(); } });
    ctl.thick = Lab.ui.seg(c, { label: 'Strip width', id: 'h-width', value: 'thick', options: [{ value: 'thick', label: 'Thickened' }, { value: 'true', label: 'True width' }],
      onChange: v => { if (st.cut) { ctl.thick.set(st.thick ? 'thick' : 'true'); return; } st.thick = v === 'thick'; if (!inStrip()) { st.spread = { from: st.lay, to: layoutFor(st.k, st.thick), t: 0, dur: 0.8 }; } else st.lay = layoutFor(st.k, st.thick); } });
    const g = Lab.ui.group(c, 'Show');
    const sr = Lab.el('div', { class: 'btn-row' }); g.append(sr);
    ctl.show = Lab.ui.seg(sr, { label: null, id: 'h-show', value: 'all', options: [{ value: 'all', label: 'Every piece' }, { value: 'one', label: 'One piece' }, { value: 'two', label: 'Two pieces' }], onChange: v => { st.show = v; applyShow(); } });
    ctl.show.el.querySelector('.lbl') && ctl.show.el.querySelector('.lbl').remove();
    Lab.ui.button(sr, { label: 'Pick others', id: 'h-pick', onClick: () => {
      const m = count(st.k); if (m < 2) return;
      st.picked = true;
      if (st.show === 'one') st.sel[0] = (st.sel[0] + 1) % m;
      else { const a = Math.floor(Math.random() * m); let b = Math.floor(Math.random() * (m - 1)); if (b >= a) b++; st.sel = [a, b]; }
      if (st.show === 'all') { st.show = 'two'; ctl.show.set('two'); }
      applyShow();
    } });
    readout = section.querySelector('[data-readout]');
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
      if (st.playT <= 0) { if (st.k < MAXK) { startCut(); st.playT = 1.6; } else { st.play = false; syncButtons(); } }
    }
    stepMeasure(dt);
  };

  Lab.register(ch);
}
