/* ============================================================
   Experiment 4: Strip Music.
   A standing wave displaces the band along its normal:
   d(θ) = A cos(mθ) cos(ωt). After one lap the band comes back with
   its normal flipped (Möbius) or not (ring), so the wave fits only
   if cos(2πm) = −1 (Möbius: m = ½, 1½, …) or +1 (ring: m = 0, 1, …).
   Zero-point sums use a smooth cutoff e^{-kε}; after removing the
   1/ε² bulk term the leftovers tend to −1/12 (ring) and +1/24 (Möbius).
   ============================================================ */
{
  const TAU = Lab.TAU;
  const R = 1.25, W = 0.62, SEGU = 240, SEGV = 8, NV = SEGV + 1, AMP = 0.13;
  const MODES = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5];
  const mLabel = m => (m % 1 ? (m === 0.5 ? '½' : `${Math.floor(m)}½`) : String(m));
  const st = { n: 1, m: 0.5, t: 0, electrons: 4, eps: 1, sweep: true, lastPartials: null };
  const ch = { token: 'music', gl: true, background: () => Lab.stageBg() };
  let geo, base, baseN, meshF, meshB, seamLines, hud = {}, readout, ladder, spec, zp, zpOut, ac = null;

  function fits() { const c = Math.cos(TAU * st.m); return st.n % 2 ? c < -0.99 : c > 0.99; }

  function build() {
    if (meshF) { ch.scene.remove(meshF, meshB, seamLines); geo.dispose(); }
    geo = Lab.bandGeometry({ n: st.n, chi: 1, R, W, segU: SEGU, segV: SEGV, tile: W * 1.6 });
    base = Float32Array.from(geo.getAttribute('position').array);
    baseN = Float32Array.from(geo.getAttribute('normal').array);
    geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array((SEGU + 1) * NV * 3), 3));
    const geoB = new THREE.BufferGeometry();
    ['position', 'normal', 'uv', 'color'].forEach(k => geoB.setAttribute(k, geo.getAttribute(k)));
    geoB.setIndex(geo.getIndex());
    meshF = new THREE.Mesh(geo, Lab.paintMaterial(Lab.paperTexture(true), '#16a6c9', THREE.FrontSide));
    meshB = new THREE.Mesh(geoB, Lab.paintMaterial(Lab.paperTexture(false), '#16a6c9', THREE.BackSide));
    // the "rip": a red surface spanning the gap when the wave doesn't meet itself
    const lg = new THREE.BufferGeometry();
    lg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(NV * 2 * 3), 3));
    const ri = []; for (let j = 0; j < NV - 1; j++) { const a = j * 2, b = a + 1, c2 = a + 2, d = a + 3; ri.push(a, b, c2, b, d, c2); }
    lg.setIndex(ri);
    seamLines = new THREE.Mesh(lg, new THREE.MeshBasicMaterial({ color: 0xe0203f, side: THREE.DoubleSide, transparent: true, opacity: 0.85 }));
    ch.scene.add(meshF, meshB, seamLines);
  }
  function displace() {
    const pos = geo.getAttribute('position').array, col = geo.getAttribute('color').array;
    const w = st.m === 0 ? 0 : 2.4 * st.m;
    const ct = st.m === 0 ? 1 : Math.cos(w * st.t);
    for (let i = 0; i <= SEGU; i++) {
      const th = i / SEGU * TAU, shape = Math.cos(st.m * th), d = AMP * shape * ct;
      for (let j = 0; j < NV; j++) {
        const k = (i * NV + j) * 3;
        pos[k] = base[k] + baseN[k] * d; pos[k + 1] = base[k + 1] + baseN[k + 1] * d; pos[k + 2] = base[k + 2] + baseN[k + 2] * d;
        col[k] = Math.abs(shape) * 0.42;
      }
    }
    geo.getAttribute('position').needsUpdate = true; geo.getAttribute('color').needsUpdate = true;
    geo.computeVertexNormals();
    // seam: connect points that started out as the same physical point
    const L = seamLines.geometry.getAttribute('position').array, odd = st.n % 2 === 1;
    for (let j = 0; j < NV; j++) {
      const a = (0 * NV + j) * 3, b = (SEGU * NV + (odd ? NV - 1 - j : j)) * 3;
      L.set([pos[a], pos[a + 1], pos[a + 2], pos[b], pos[b + 1], pos[b + 2]], j * 6);
    }
    seamLines.geometry.getAttribute('position').needsUpdate = true;
    seamLines.geometry.computeBoundingSphere();
    seamLines.visible = !fits();
  }

  /* ---------------- panels ---------------- */
  function drawLadder() {
    const { ctx, w, h } = Lab.fitCanvas(ladder);
    ctx.clearRect(0, 0, w, h);
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), real = Lab.cssVar('--real');
    const mono = Lab.cssVar('--font-mono');
    const top = 26, bot = h - 26, yOf = f => bot - f / 3.5 * (bot - top);
    const cols = [{ x: w * 0.27, name: 'plain ring', levels: [{ f: 0, g: 1 }, { f: 1, g: 2 }, { f: 2, g: 2 }, { f: 3, g: 2 }], color: blue },
      { x: w * 0.73, name: 'Möbius ring', levels: [{ f: 0.5, g: 2 }, { f: 1.5, g: 2 }, { f: 2.5, g: 2 }, { f: 3.5, g: 2 }], color: pink }];
    ctx.strokeStyle = rule; ctx.lineWidth = 1; ctx.setLineDash([3, 4]);
    ctx.beginPath(); ctx.moveTo(12, yOf(0)); ctx.lineTo(w - 12, yOf(0)); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'right'; ctx.fillText('zero', w - 12, yOf(0) - 4);
    cols.forEach((c, ci) => {
      let left = st.electrons;
      let closed = false;
      c.levels.forEach(L => {
        const y = yOf(L.f), half = Math.min(78, w * 0.17);
        const cap = 2 * L.g, put = Math.max(0, Math.min(cap, left)); left -= put;
        if (left === 0 && put === cap) closed = true; else if (put > 0) closed = false;
        ctx.strokeStyle = c.color; ctx.lineWidth = 3;
        ctx.beginPath(); ctx.moveTo(c.x - half, y); ctx.lineTo(c.x + half, y); ctx.stroke();
        ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'right';
        ctx.fillText(`${mLabel(L.f)}${L.g === 2 ? ' ×2' : ''}`, c.x - half - 6, y + 4);
        for (let e = 0; e < put; e++) { const ex = c.x - half + 12 + e * ((2 * half - 24) / Math.max(1, cap - 1)); ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(ex, y - 7, 4, 0, TAU); ctx.fill(); }
      });
      const stable = closed && left === 0;
      ctx.textAlign = 'center'; ctx.font = `600 12px ${mono}`; ctx.fillStyle = ink; ctx.fillText(c.name, c.x, 14);
      ctx.font = `11px ${mono}`; ctx.fillStyle = stable ? real : muted;
      ctx.fillText(st.electrons > 14 ? '' : stable ? 'closed shell: stable' : 'open shell', c.x, h - 6);
    });
  }
  function drawSpectrum() {
    const { ctx, w, h } = Lab.fitCanvas(spec);
    ctx.clearRect(0, 0, w, h);
    const muted = Lab.cssVar('--muted'), rule = Lab.cssVar('--rule'), mono = Lab.cssVar('--font-mono');
    const x0 = 30, x1 = w - 10, y0 = 10, y1 = h - 22;
    ctx.strokeStyle = rule; ctx.beginPath(); ctx.moveTo(x0, y1); ctx.lineTo(x1, y1); ctx.stroke();
    const fmax = 2200; const xOf = f => x0 + f / fmax * (x1 - x0);
    ctx.fillStyle = muted; ctx.font = `10px ${mono}`; ctx.textAlign = 'center';
    [0, 500, 1000, 1500, 2000].forEach(f => ctx.fillText(f + (f === 2000 ? ' Hz' : ''), xOf(f), h - 6));
    const P = st.lastPartials; if (!P) { ctx.textAlign = 'left'; ctx.fillText('press a pluck button', x0 + 6, y0 + 12); return; }
    P.parts.forEach(p => { const x = xOf(p.f); if (x > x1) return; ctx.fillStyle = P.color; ctx.fillRect(x - 3, y1 - p.a * (y1 - y0), 6, p.a * (y1 - y0)); });
    ctx.textAlign = 'left'; ctx.fillStyle = muted; ctx.fillText(P.label, x0 + 6, y0 + 12);
  }
  function zeroPoint(eps) {
    const x = Math.exp(-eps);
    return { ring: x / (1 - x) ** 2 - 1 / eps ** 2, mob: Math.sqrt(x) * (1 + x) / (2 * (1 - x) ** 2) - 1 / eps ** 2 };
  }
  function drawZP() {
    const { ctx, w, h } = Lab.fitCanvas(zp);
    ctx.clearRect(0, 0, w, h);
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), mono = Lab.cssVar('--font-mono');
    const x0 = 48, x1 = w - 12, y0 = 12, y1 = h - 26;
    const lx = e => x0 + (Math.log10(2) - Math.log10(e)) / (Math.log10(2) - Math.log10(0.02)) * (x1 - x0);
    const yv = v => y1 - (v + 0.1) / 0.16 * (y1 - y0);
    ctx.strokeStyle = rule; ctx.lineWidth = 1;
    [-0.08, -0.04, 0, 0.04].forEach(v => { ctx.beginPath(); ctx.moveTo(x0, yv(v)); ctx.lineTo(x1, yv(v)); ctx.stroke(); ctx.fillStyle = muted; ctx.font = `10px ${mono}`; ctx.textAlign = 'right'; ctx.fillText(v.toFixed(2), x0 - 4, yv(v) + 3); });
    ctx.textAlign = 'center'; ctx.fillText('more modes counted →', (x0 + x1) / 2, h - 6);
    const target = [{ v: -1 / 12, c: blue, t: '−1/12' }, { v: 1 / 24, c: pink, t: '+1/24' }];
    target.forEach(T => { ctx.setLineDash([5, 4]); ctx.strokeStyle = T.c; ctx.beginPath(); ctx.moveTo(x0, yv(T.v)); ctx.lineTo(x1, yv(T.v)); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = T.c; ctx.textAlign = 'right'; ctx.font = `600 11px ${mono}`; ctx.fillText(T.t, x1, yv(T.v) - 4); });
    ['ring', 'mob'].forEach((k, i) => {
      ctx.strokeStyle = i ? pink : blue; ctx.lineWidth = 2.5; ctx.beginPath();
      let first = true;
      for (let e = 2; e >= Math.max(0.02, st.eps); e *= 0.97) { const v = zeroPoint(e)[k]; const X = lx(e), Y = yv(Lab.clamp(v, -0.1, 0.06)); first ? ctx.moveTo(X, Y) : ctx.lineTo(X, Y); first = false; }
      ctx.stroke();
    });
    const z = zeroPoint(Math.max(0.02, st.eps));
    zpOut.innerHTML = `plain ring leftover <b style="color:var(--blue)">${z.ring.toFixed(5)}</b> · Möbius ring leftover <b style="color:var(--pink)">${z.mob >= 0 ? '+' : ''}${z.mob.toFixed(5)}</b>`;
  }

  /* ---------------- sound ---------------- */
  function pluck(which) {
    try {
      if (!ac) ac = new (window.AudioContext || window.webkitAudioContext)();
      if (ac.state === 'suspended') ac.resume();
    } catch (e) { Lab.toast(ch.stage, 'Sound is not available in this browser.'); return; }
    const same = document.getElementById('m-same-on')?.getAttribute('aria-pressed') === 'true';
    const f0 = 196, now = ac.currentTime + 0.02;
    const parts = [];
    for (let k = 0; k < 12; k++) {
      const f = which === 'ring' ? f0 * (k + 1) : same ? f0 * (2 * k + 1) : f0 * (k + 0.5);
      parts.push({ f, a: 1 / (1 + 0.55 * k) });
    }
    const master = ac.createGain(); master.gain.value = 0.18; master.connect(ac.destination);
    parts.forEach((p, k) => {
      if (p.f > 9000) return;
      const o = ac.createOscillator(), g = ac.createGain();
      o.type = 'sine'; o.frequency.value = p.f;
      const tau = 1.8 / (1 + 0.22 * k);
      g.gain.setValueAtTime(0, now); g.gain.linearRampToValueAtTime(p.a, now + 0.006); g.gain.exponentialRampToValueAtTime(0.0008, now + tau * 3);
      o.connect(g); g.connect(master); o.start(now); o.stop(now + tau * 3 + 0.05);
    });
    st.lastPartials = { parts, color: which === 'ring' ? Lab.cssVar('--blue') : Lab.cssVar('--pink'), label: which === 'ring' ? `plain ring: ${f0} Hz × 1, 2, 3, 4 … (every harmonic)` : same ? `Möbius ring: ${f0} Hz × 1, 3, 5, 7 … (odd harmonics only)` : `Möbius ring: ${f0 / 2} Hz × 1, 3, 5 … (an octave lower, odd only)` };
    drawSpectrum();
  }

  ch.init = function (section, stage) {
    const { scene, camera, controls } = Lab.makeScene({ pos: [3.0, -3.5, 2.6] });
    ch.scene = scene; ch.camera = camera; ch.controls = controls;
    build();
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.mode = Lab.el('div', { class: 'chip' }); hud.fit = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.mode, hud.fit); stage.append(hud.wrap);

    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Loop', id: 'm-shape', value: 1, options: [{ value: 0, label: 'Plain ring' }, { value: 1, label: 'Möbius ring' }], onChange: v => { st.n = v; build(); } });
    Lab.ui.seg(c, { label: 'Waves around the loop', id: 'm-m', value: st.m, options: MODES.map(m => ({ value: m, label: mLabel(m) })), onChange: v => { st.m = v; st.t = 0; } });
    const row = Lab.ui.row(Lab.ui.group(c, 'Listen'));
    Lab.ui.button(row, { label: '▶ Pluck plain ring', id: 'm-pr', onClick: () => pluck('ring') });
    Lab.ui.button(row, { label: '▶ Pluck Möbius ring', id: 'm-pm', primary: true, onClick: () => pluck('mob') });
    Lab.ui.seg(c, { label: 'Möbius pitch', id: 'm-same', value: 'off', options: [{ value: 'off', label: 'Same size' }, { value: 'on', label: 'Same note' }] });

    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `
      <h4>Allowed waves, and what chemists do with them</h4>
      <canvas data-ladder class="plot" style="height:210px" aria-label="Allowed wave levels for the plain ring (0, 1, 2, 3) and the Möbius ring (one half, one and a half, two and a half, three and a half), filled with electrons"></canvas>
      <div class="controls" style="margin:6px 0 2px" data-elec></div>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">Each line is an allowed wave; two electrons fit per wave. A ring of atoms is extra stable when its electrons exactly fill a set of levels. Plain rings fill at 2, 6, 10 (the 4n + 2 rule, like benzene's 6). Möbius rings fill at 4, 8, 12 (the 4n rule).</p>
      <h4 style="margin-top:14px">What you just heard</h4>
      <canvas data-spec class="plot short" aria-label="Spectrum of the last pluck"></canvas>
      <h4 style="margin-top:14px">Where 1 + 2 + 3 + … = −1/12 lives</h4>
      <canvas data-zp class="plot" aria-label="Zero-point energy leftovers converging to minus one twelfth for the ring and plus one twenty-fourth for the Möbius ring"></canvas>
      <p class="verdict-line" data-zpout style="font-family:var(--font-mono);font-size:.8125rem"></p>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">Quantum physics gives every wave a minimum energy, even at rest. Add them up over all the waves and you get infinity. But the infinite part grows with the ring's length, the same everywhere, so it can't push or pull on anything. What's left over is finite: −1/12 for the plain ring, which pulls it smaller, and +1/24 for the Möbius ring, which pushes it bigger (in units of 2πħc/L). This is the Casimir effect in a one-dimensional world.</p>`;
    ladder = readout.querySelector('[data-ladder]'); spec = readout.querySelector('[data-spec]'); zp = readout.querySelector('[data-zp]'); zpOut = readout.querySelector('[data-zpout]');
    Lab.ui.slider(readout.querySelector('[data-elec]'), { label: 'Electrons in the ring', id: 'm-e', min: 2, max: 12, step: 1, value: st.electrons, format: v => String(v), onInput: v => { st.electrons = v; drawLadder(); } });
    Lab.ui.button(readout.querySelector('[data-elec]'), { label: 'Replay the sum', id: 'm-zp', onClick: () => { st.eps = 2; st.sweep = true; } });
    st.eps = 2; st.sweep = true;
    drawLadder(); drawSpectrum();
  };
  ch.enter = function () { drawLadder(); drawSpectrum(); };
  ch.resize = function () { if (ladder) { drawLadder(); drawSpectrum(); drawZP(); } };
  ch.frame = function (dt) {
    if (!Lab.stepTween(ch, dt)) ch.controls.update();
    st.t += dt;
    displace();
    const ok = fits();
    hud.mode.innerHTML = `<b>${mLabel(st.m)}</b> wave${st.m === 1 ? '' : 's'} around a ${st.n ? 'Möbius' : 'plain'} ring`;
    hud.fit.textContent = ok ? (st.m === 0 ? 'fits: the flat zero mode, frequency 0' : 'fits: it meets itself at the joint') : 'doesn’t fit: it tears at the joint';
    hud.fit.className = 'chip ' + (ok ? 'good' : 'alert');
    if (st.sweep) { st.eps *= Math.pow(0.5, dt * 0.9); if (st.eps <= 0.02) { st.eps = 0.02; st.sweep = false; } drawZP(); }
  };
  Lab.register(ch);
}
