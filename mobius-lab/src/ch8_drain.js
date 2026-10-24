/* ============================================================
   Experiment 9: Drain Gravity.
   Space flows radially inward with speed v(r) (a 2D slice of 3D).
   Anything floating in it accelerates with the flow: a = ∇(v²/2).
     drain (space vanishes only at the planet, so the flux through
       every sphere is the same): v = 1/(√2 r²)  →  a = 1/r⁵
     river (Hamilton & Lisle): v = √(2GM/r)    →  a = GM/r²  (Newton)
   For the river the flux 4πr²v grows with r, so space must vanish
   everywhere, at a rate ∝ r^(−3/2). Units: GM = 1.
   ============================================================ */
{
  const TAU = Lab.TAU, RP = 0.3, REDGE = 2.6, C_LIGHT = 1.2;
  const st = { model: 'drain', sink: false, hole: false, moons: [], tracers: [], pulses: [], log: [], drag: null, nextId: 1, pulseT: 0 };
  const ch = { token: 'drain', gl: false };
  let canvas, hud = {}, readout, forceCanvas, W = 600, H = 450, scale = 100;

  const vflow = r => (st.model === 'drain' ? 1 / (Math.SQRT2 * r * r) : Math.sqrt(2 / r));       // inward speed
  const accel = r => (st.model === 'drain' ? 1 / Math.pow(r, 5) : 1 / (r * r));                 // inward pull
  const toPx = (x, y) => [W / 2 + x * scale, H / 2 - y * scale];
  const fromPx = (px, py) => [(px - W / 2) / scale, -(py - H / 2) / scale];

  function seedTracers() {
    st.tracers = [];
    for (let i = 0; i < 260; i++) { const r = RP + Math.random() * (REDGE - RP), a = Math.random() * TAU; st.tracers.push([r * Math.cos(a), r * Math.sin(a)]); }
  }
  function launch(kind) {
    const r0 = 1.5, ang = Math.random() * TAU, vc = Math.sqrt(accel(r0) * r0) * (kind === 'nudge' ? 1.04 : 1);
    addMoon([r0 * Math.cos(ang), r0 * Math.sin(ang)], [-vc * Math.sin(ang), vc * Math.cos(ang)], kind === 'nudge' ? 'circular orbit, nudged 4%' : 'perfect circular orbit');
    if (kind !== 'nudge' && st.model === 'drain') Lab.toast(ch.stage, 'A perfect circle can balance for a while, like a pencil on its tip. Nudge one to test it.', 3200);
  }
  function addMoon(p, v, label) {
    const id = st.nextId++;
    const m = { id, x: p[0], y: p[1], vx: v[0], vy: v[1], trail: [], angle: 0, lastAng: Math.atan2(p[1], p[0]), state: 'orbiting', label, model: st.model, r0: Math.hypot(...p), rmin: 99, rmax: 0, t: 0 };
    st.moons.push(m); if (st.moons.length > 4) st.moons.shift();
  }
  function stepMoon(m, dt) {
    let t = 0;
    while (t < dt && m.state === 'orbiting') {
      const r = Math.hypot(m.x, m.y), h = Math.min(dt - t, 0.004 * Math.max(0.15, Math.pow(r, 1.5)) * (st.model === 'drain' ? Math.min(1, r * r) : 1));
      const f = (x, y) => { const rr = Math.hypot(x, y), a = accel(rr); return [-a * x / rr, -a * y / rr]; };
      // RK4
      const k1v = f(m.x, m.y), k1x = [m.vx, m.vy];
      const k2v = f(m.x + k1x[0] * h / 2, m.y + k1x[1] * h / 2), k2x = [m.vx + k1v[0] * h / 2, m.vy + k1v[1] * h / 2];
      const k3v = f(m.x + k2x[0] * h / 2, m.y + k2x[1] * h / 2), k3x = [m.vx + k2v[0] * h / 2, m.vy + k2v[1] * h / 2];
      const k4v = f(m.x + k3x[0] * h, m.y + k3x[1] * h), k4x = [m.vx + k3v[0] * h, m.vy + k3v[1] * h];
      m.x += h / 6 * (k1x[0] + 2 * k2x[0] + 2 * k3x[0] + k4x[0]); m.y += h / 6 * (k1x[1] + 2 * k2x[1] + 2 * k3x[1] + k4x[1]);
      m.vx += h / 6 * (k1v[0] + 2 * k2v[0] + 2 * k3v[0] + k4v[0]); m.vy += h / 6 * (k1v[1] + 2 * k2v[1] + 2 * k3v[1] + k4v[1]);
      t += h; m.t += h;
      const rn = Math.hypot(m.x, m.y), an = Math.atan2(m.y, m.x);
      let da = an - m.lastAng; if (da > Math.PI) da -= TAU; if (da < -Math.PI) da += TAU; m.angle += da; m.lastAng = an;
      m.rmin = Math.min(m.rmin, rn); m.rmax = Math.max(m.rmax, rn);
      if (rn < RP) { m.state = 'crashed'; logMoon(m); }
      else if (rn > 6) { m.state = 'escaped'; logMoon(m); }
    }
    m.trail.push([m.x, m.y]); if (m.trail.length > 900) m.trail.shift();
    const orbits = Math.abs(m.angle) / TAU;
    if (m.state === 'orbiting' && orbits >= 3 && !m.logged) { m.state = 'stable'; logMoon(m); m.state = 'orbiting'; }
  }
  function logMoon(m) {
    if (m.logged) return; m.logged = true;
    const orbits = (Math.abs(m.angle) / TAU).toFixed(1), kind = m.model === 'drain' ? 'Drain' : 'River';
    const knife = m.state === 'stable' && m.model === 'drain';
    const txt = m.state === 'crashed' ? `crashed into the planet after ${orbits} orbits` : m.state === 'escaped' ? `flew off into space after ${orbits} orbits`
      : knife ? 'balanced for 3 orbits, like a pencil on its tip. Any nudge breaks it.' : `still orbiting after 3 orbits, staying between r = ${m.rmin.toFixed(2)} and ${m.rmax.toFixed(2)}`;
    st.log.unshift({ ok: knife ? null : m.state === 'stable', text: `${kind} · ${m.label}: ${txt}` });
    st.log = st.log.slice(0, 6);
    renderLog();
  }
  function renderLog() {
    const el = readout.querySelector('[data-k=log]');
    el.innerHTML = st.log.length ? st.log.map(l => `<li><span class="${l.ok ? 'ok' : l.ok === null ? '' : 'miss'}">${l.ok ? '✓' : l.ok === null ? '•' : '✗'}</span> ${l.text}</li>`).join('') : '<li style="color:var(--muted)">Launch a moon to start the log.</li>';
  }
  function drawForce() {
    const { ctx, w, h } = Lab.fitCanvas(forceCanvas);
    ctx.clearRect(0, 0, w, h);
    const muted = Lab.cssVar('--muted'), rule = Lab.cssVar('--rule'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), mono = Lab.cssVar('--font-mono');
    const x0 = 44, x1 = w - 12, y0 = 10, y1 = h - 24;
    const lx = r => x0 + (Math.log10(r) - Math.log10(0.5)) / (Math.log10(3) - Math.log10(0.5)) * (x1 - x0);
    const ly = a => y1 - (Math.log10(a) + 3) / 5 * (y1 - y0);
    ctx.strokeStyle = rule; ctx.font = `10px ${mono}`; ctx.fillStyle = muted;
    [0.001, 0.01, 0.1, 1, 10, 100].forEach(a => { ctx.beginPath(); ctx.moveTo(x0, ly(a)); ctx.lineTo(x1, ly(a)); ctx.stroke(); ctx.textAlign = 'right'; ctx.fillText(String(a), x0 - 4, ly(a) + 3); });
    [0.5, 1, 2, 3].forEach(r => { ctx.textAlign = 'center'; ctx.fillText('r=' + r, lx(r), h - 8); });
    const curve = (fn, col, label, at) => { ctx.strokeStyle = col; ctx.lineWidth = 2.4; ctx.beginPath(); for (let r = 0.5; r <= 3.001; r *= 1.03) { const X = lx(r), Y = ly(Math.max(1e-3, Math.min(100, fn(r)))); r === 0.5 ? ctx.moveTo(X, Y) : ctx.lineTo(X, Y); } ctx.stroke(); ctx.fillStyle = col; ctx.textAlign = 'left'; ctx.fillText(label, lx(at) + 6, ly(fn(at)) - 6); };
    curve(r => 1 / Math.pow(r, 5), pink, 'drain: 1/r⁵', 1.6);
    curve(r => 1 / (r * r), blue, 'river = Newton: 1/r²', 0.62);
  }
  function draw(dt) {
    const { ctx, w, h } = Lab.fitCanvas(canvas);
    W = w; H = h; scale = Math.min(w, h) / 2 / 2.75;
    const stage = Lab.cssVar('--stage'), ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), mono = Lab.cssVar('--font-mono');
    ctx.fillStyle = stage; ctx.fillRect(0, 0, w, h);
    const [cx, cy] = toPx(0, 0);
    // where space must disappear
    if (st.sink) {
      if (st.model === 'river') {
        const g = ctx.createRadialGradient(cx, cy, RP * scale, cx, cy, REDGE * scale);
        for (let k = 0; k <= 10; k++) { const r = RP + (REDGE - RP) * k / 10, v = Math.pow(RP / r, 1.5); g.addColorStop(k / 10, `rgba(232,69,122,${0.55 * v})`); }
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, REDGE * scale, 0, TAU); ctx.fill();
      } else { ctx.fillStyle = 'rgba(232,69,122,.55)'; ctx.beginPath(); ctx.arc(cx, cy, RP * scale * 1.25, 0, TAU); ctx.fill(); }
    }
    // horizon (river model): where the inflow reaches light speed
    const rs = 2 / (C_LIGHT * C_LIGHT);
    if (st.hole) {
      ctx.fillStyle = 'rgba(10,12,24,.85)'; ctx.beginPath(); ctx.arc(cx, cy, rs * scale, 0, TAU); ctx.fill();
      ctx.strokeStyle = '#ffd76a'; ctx.setLineDash([6, 5]); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(cx, cy, rs * scale, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
      ctx.fillStyle = '#ffd76a'; ctx.font = `11px ${mono}`; ctx.textAlign = 'center'; ctx.fillText('horizon: inflow = light speed', cx, cy - rs * scale - 8);
    }
    // tracers: little bits of space being carried in
    ctx.fillStyle = Lab.isDark() ? 'rgba(200,210,255,.55)' : 'rgba(27,33,64,.45)';
    st.tracers.forEach(p => {
      const r = Math.hypot(p[0], p[1]), v = Math.min(3.5, vflow(r)), k = v * dt * 0.5 / r;
      p[0] -= p[0] * k; p[1] -= p[1] * k;
      if (Math.hypot(p[0], p[1]) < RP) { const a = Math.random() * TAU; p[0] = REDGE * Math.cos(a); p[1] = REDGE * Math.sin(a); }
      const [px, py] = toPx(p[0], p[1]); ctx.fillRect(px - 1, py - 1, 2.2, 2.2);
    });
    // light pulses trying to swim out
    if (st.hole) {
      st.pulseT -= dt;
      if (st.pulseT <= 0) { st.pulseT = 0.12; const r = 0.5 + Math.random() * 2.1; st.pulses.push({ r, a: Math.random() * TAU, life: 1 }); }
      st.pulses.forEach(q => { q.r += (C_LIGHT - Math.sqrt(2 / q.r)) * dt * 0.5; if (q.r < RP || q.r > REDGE + 0.2) q.life = 0; });
      st.pulses = st.pulses.filter(q => q.life > 0);
      st.pulses.forEach(q => { const out = q.r > rs; ctx.strokeStyle = out ? '#f1b93f' : '#ff6b6b'; ctx.lineWidth = 2.2; ctx.beginPath(); ctx.arc(cx, cy, q.r * scale, q.a - 0.12, q.a + 0.12); ctx.stroke(); });
    } else st.pulses = [];
    // planet: a little reef of paper loops
    ctx.save(); ctx.translate(cx, cy);
    ['#f27aa2', '#45bdb7', '#f1b93f'].forEach((c, i) => { ctx.strokeStyle = c; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(0, 0, RP * scale * 0.95, RP * scale * 0.45, i * Math.PI / 3 + performance.now() / 4000, 0, TAU); ctx.stroke(); });
    ctx.restore();
    // moons and trails
    st.moons.forEach((m, i) => {
      const col = [pink, blue, '#f1b93f', '#86cc58'][i % 4];
      ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.globalAlpha = 0.75; ctx.beginPath();
      m.trail.forEach((p, k) => { const [px, py] = toPx(p[0], p[1]); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }); ctx.stroke(); ctx.globalAlpha = 1;
      if (m.state === 'orbiting') { const [px, py] = toPx(m.x, m.y); ctx.fillStyle = col; ctx.beginPath(); ctx.arc(px, py, 6, 0, TAU); ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke(); }
    });
    // slingshot preview
    if (st.drag) { const [a, b] = st.drag.start, [c2, d] = st.drag.now; ctx.strokeStyle = ink; ctx.setLineDash([4, 4]); ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(a, b); ctx.lineTo(c2, d); ctx.stroke(); ctx.setLineDash([]); }
    ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'left'; ctx.fillText('drag anywhere to throw a moon', 12, h - 12);
  }

  ch.init = function (section, stage) {
    canvas = Lab.el('canvas', { 'aria-label': 'Space flowing into a planet, with moons trying to orbit' });
    canvas.style.touchAction = 'none';
    stage.append(canvas);
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.model = Lab.el('div', { class: 'chip' }); hud.moon = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.model, hud.moon); stage.append(hud.wrap);
    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'How space flows in', id: 'd-model', value: 'drain', options: [{ value: 'drain', label: 'Drain at the planet' }, { value: 'river', label: 'River (tuned to Newton)' }],
      onChange: v => { st.model = v; st.moons = []; seedTracers(); hs.el.hidden = v !== 'river'; if (v !== 'river') { st.hole = false; hs.set('off'); r1.querySelectorAll('button').forEach(b => { b.disabled = false; }); } drawForce(); } });
    const r1 = Lab.ui.row(Lab.ui.group(c, 'Launch a moon'));
    Lab.ui.button(r1, { label: 'Circular orbit', id: 'd-circ', primary: true, onClick: () => launch('circ') });
    Lab.ui.button(r1, { label: 'Circular, nudged 4%', id: 'd-nudge', onClick: () => launch('nudge') });
    Lab.ui.button(r1, { label: 'Clear', id: 'd-clear', onClick: () => { st.moons = []; } });
    Lab.ui.seg(c, { label: 'Where space vanishes', id: 'd-sink', value: 'off', options: [{ value: 'off', label: 'Hide' }, { value: 'on', label: 'Show' }], onChange: v => { st.sink = v === 'on'; } });
    const hs = Lab.ui.seg(c, { label: 'Black hole', id: 'd-hole', value: 'off', options: [{ value: 'off', label: 'Off' }, { value: 'on', label: 'On' }],
      onChange: v => {
        st.hole = v === 'on';
        // this close to a black hole Newton's law no longer predicts orbits (relativity has no stable ones here), so moons are off
        r1.querySelectorAll('button').forEach(b => { b.disabled = st.hole; });
        if (st.hole) { st.moons = []; Lab.toast(ch.stage, 'Moons are off: this close to a black hole, Newton\u2019s law can\u2019t predict orbits. Watch the light instead.', 3600); }
      } });
    hs.el.hidden = true;
    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `<h4>Orbit log</h4><ul data-k="log" style="margin:0 0 10px;padding-left:18px"></ul>
      <h4>How hard space pulls at distance r</h4>
      <canvas data-force class="plot short" aria-label="Pull versus distance on log scales: drain falls like 1 over r to the fifth, river like 1 over r squared"></canvas>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">If space only disappears at the planet, the same amount must cross every sphere around it, so the flow speeds up like 1/r² and the pull grows like 1/r⁵ close in. Orbits under a pull that steep can't survive a nudge. Newton's 1/r² needs the river profile, and then the inflow through a sphere grows with its size, so space would have to vanish all around the planet (Show it). Planets would also feel a drag through a real fluid, and none has ever been measured.</p>`;
    forceCanvas = readout.querySelector('[data-force]');
    renderLog();
    seedTracers();
    // slingshot: drag to throw
    canvas.addEventListener('pointerdown', e => { const r = canvas.getBoundingClientRect(); st.drag = { start: [e.clientX - r.left, e.clientY - r.top], now: [e.clientX - r.left, e.clientY - r.top] }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => { if (!st.drag) return; const r = canvas.getBoundingClientRect(); st.drag.now = [e.clientX - r.left, e.clientY - r.top]; });
    canvas.addEventListener('pointerup', e => {
      if (!st.drag) return; const [a, b] = st.drag.start, [c2, d] = st.drag.now; st.drag = null;
      const p = fromPx(a, b); if (Math.hypot(...p) < RP * 1.2 || st.hole) return;
      const v = [(c2 - a) / scale * 0.9, -(d - b) / scale * 0.9];
      addMoon(p, v, 'thrown by hand');
    });
    launch('nudge');
  };
  ch.enter = function () { drawForce(); };
  ch.resize = function () { drawForce(); };
  ch.frame = function (dt) {
    const sdt = Math.min(dt, 1 / 30) * 2.5;
    st.moons.forEach(m => { if (m.state === 'orbiting') stepMoon(m, sdt); });
    draw(Math.min(dt, 1 / 30) * 2.5);
    hud.model.innerHTML = st.model === 'drain' ? 'Drain: pull ∝ <b>1/r⁵</b>' : 'River: pull ∝ <b>1/r²</b>';
    const live = st.moons.filter(m => m.state === 'orbiting').length;
    hud.moon.textContent = st.hole ? 'light: yellow escapes, red falls in' : st.moons.length ? `${live} moon${live === 1 ? '' : 's'} still orbiting` : 'no moons yet';
    if (!forceCanvas._drawn) { drawForce(); forceCanvas._drawn = true; }
  };
  Lab.register(ch);
}
