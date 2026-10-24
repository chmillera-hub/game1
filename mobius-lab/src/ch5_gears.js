/* ============================================================
   Experiment 5: Gear Lock (geometric frustration).
   Gears are rotors joined by stiff tooth springs. Touching gears of
   equal size need θi + θj = const (they counter-rotate). Across a
   Möbius joint the rule flips to θi − θj = const, because that gear is
   seen from the other face of the band. A loop can turn only if the
   flips multiply to +1. Teeth can slip when the strain gets too big.
   ============================================================ */
{
  const TAU = Lab.TAU, TEETH = 12, K = 70, DAMP = 0.35, TMAX = 6, WMOT = 3;
  const st = { layout: 'ring', N: 5, mobius: false, lattice: 'square', grip: 8, motor: true, slips: 0, t: 0 };
  const ch = { token: 'gears', gl: false };
  let canvas, gears = [], meshes = [], sparks = [], hud = {}, readout, W = 600, H = 450;

  function build() {
    gears = []; meshes = []; sparks = []; st.slips = 0; st.wAvg = null;
    const cx = W / 2, cy = H / 2;
    if (st.layout === 'ring') {
      const N = st.N, Rr = (Math.min(W, H) / 2 - 14) / (1 + 1.16 * Math.sin(Math.PI / N)), rg = Rr * Math.sin(Math.PI / N) * 0.985;
      st.Rr = Rr;
      for (let i = 0; i < N; i++) { const a = -Math.PI / 2 + i * TAU / N; gears.push({ x: cx + Rr * Math.cos(a), y: cy + Rr * Math.sin(a), r: rg, th: 0, w: 0 }); }
      for (let i = 0; i < N; i++) meshes.push({ a: i, b: (i + 1) % N, sg: (st.mobius && i === N - 1) ? -1 : 1, seam: i === N - 1 });
    } else if (st.layout === 'strip') {
      const N = st.N, pad = 40, rg = Math.min((W - 2 * pad) / (2 * (N + 1)), H * 0.16);
      const y = cy + 10;
      for (let i = 0; i < N; i++) gears.push({ x: pad + rg + i * 2 * rg, y, r: rg * 0.985, th: 0, w: 0 });
      for (let i = 0; i < N - 1; i++) meshes.push({ a: i, b: i + 1, sg: 1 });
      meshes.push({ a: N - 1, b: 0, sg: st.mobius ? -1 : 1, seam: true, ghost: true });
    } else {
      const rows = 5, cols = 5, rg = Math.min(W / (2 * cols + 2), H / (2 * rows + 2)) * 0.98;
      const idx = {};
      for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
        const tri = st.lattice === 'triangle';
        const x = cx + (c - (cols - 1) / 2) * 2 * rg + (tri && r % 2 ? rg : 0) - (tri ? rg / 2 : 0);
        const y = cy + (r - (rows - 1) / 2) * 2 * rg * (tri ? Math.sqrt(3) / 2 : 1);
        idx[r + ',' + c] = gears.length; gears.push({ x, y, r: rg * 0.985, th: 0, w: 0 });
      }
      for (let i = 0; i < gears.length; i++) for (let j = i + 1; j < gears.length; j++) {
        const d = Math.hypot(gears[i].x - gears[j].x, gears[i].y - gears[j].y);
        if (d < gears[i].r + gears[j].r + 2) meshes.push({ a: i, b: j, sg: 1 });
      }
    }
    // initial phases so neighbouring teeth interleave (as well as the geometry allows)
    const seen = new Set([0]); const order = [0];
    while (order.length) {
      const i = order.shift();
      meshes.forEach(m => {
        const j = m.a === i ? m.b : m.b === i ? m.a : -1;
        if (j < 0 || seen.has(j) || m.ghost) return;
        const al = Math.atan2(gears[j].y - gears[i].y, gears[j].x - gears[i].x);
        gears[j].th = 2 * al + Math.PI - gears[i].th - Math.PI / TEETH;
        seen.add(j); order.push(j);
      });
    }
    meshes.forEach(m => { m.c = gears[m.a].th + m.sg * gears[m.b].th; m.strain = 0; m.tooth = null; });
    st.motorGear = st.layout === 'lattice' ? Math.floor(gears.length / 2) : 0;
  }
  function step(dt) {
    const g = gears;
    g.forEach(q => { q.tq = -DAMP * q.w; });
    const mg = g[st.motorGear];
    if (st.motor) mg.tq += Math.max(0, TMAX * (1 - mg.w / WMOT));
    let E = 0;
    const pitch = TAU / TEETH, rigid = st.grip >= 1e8;
    meshes.forEach(m => {
      const a = g[m.a], b = g[m.b];
      const x = a.th + m.sg * b.th - m.c;
      let F;
      if (rigid) { F = K * x; E += 0.5 * K * x * x; }
      else {
        // teeth as a washboard: they hold up to `grip`, then skip to the next tooth
        F = st.grip * Math.sin(TAU * x / pitch);
        E += st.grip * pitch / TAU * (1 - Math.cos(TAU * x / pitch));
        const tooth = Math.round(x / pitch);
        if (m.tooth == null) m.tooth = tooth;
        if (tooth !== m.tooth) { m.tooth = tooth; st.slips++; if (sparks.length < 40) sparks.push({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, life: 1 }); }
      }
      m.strain = F;
      F += 5 * (a.w + m.sg * b.w);   // tooth damping
      a.tq -= F; b.tq -= m.sg * F;
    });
    g.forEach(q => { q.w += q.tq * dt; q.th += q.w * dt; q.ws = (q.ws || 0) + (q.w - (q.ws || 0)) * Math.min(1, dt * 2); });
    st.energy = E;
  }
  function gearPath(ctx, q) {
    const n = TEETH, ro = q.r * 1.13, ri = q.r * 0.88;
    ctx.beginPath();
    for (let k = 0; k < n; k++) {
      const a0 = q.th + k * TAU / n;
      const pts = [[a0 - 0.30 * TAU / n, ri], [a0 - 0.17 * TAU / n, ro], [a0 + 0.17 * TAU / n, ro], [a0 + 0.30 * TAU / n, ri]];
      pts.forEach(([a, r], i) => { const X = q.x + Math.cos(a) * r, Y = q.y + Math.sin(a) * r; (k === 0 && i === 0) ? ctx.moveTo(X, Y) : ctx.lineTo(X, Y); });
    }
    ctx.closePath();
  }
  function draw() {
    const { ctx, w, h } = Lab.fitCanvas(canvas);
    if (Math.abs(w - W) > 1 || Math.abs(h - H) > 1) { W = w; H = h; build(); }
    const stage = Lab.cssVar('--stage'), ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), red = Lab.cssVar('--stretch'), green = Lab.cssVar('--real');
    const mono = Lab.cssVar('--font-mono');
    ctx.fillStyle = stage; ctx.fillRect(0, 0, w, h);
    // the band the gears sit on
    if (st.layout === 'ring') {
      const Rr = st.Rr, bw = gears[0].r * 2.6;
      ctx.strokeStyle = '#f6b3c9'; ctx.globalAlpha = 0.55; ctx.lineWidth = bw;
      const N = st.N, seamA = -Math.PI / 2 - Math.PI / N;
      ctx.beginPath(); ctx.arc(W / 2, H / 2, Rr, seamA + 0.12, seamA + TAU - 0.12); ctx.stroke(); ctx.globalAlpha = 1;
    } else if (st.layout === 'strip') {
      const g0 = gears[0], gl = gears[gears.length - 1], bw = g0.r * 2.7, x0 = g0.x - g0.r * 1.4, x1 = gl.x + g0.r * 3.4;
      ctx.fillStyle = '#f6b3c9'; ctx.globalAlpha = 0.55; ctx.fillRect(x0, g0.y - bw / 2, x1 - x0, bw); ctx.globalAlpha = 1;
      const arrow = (x, up) => { const y0 = g0.y + bw / 2 - 8, y1 = g0.y - bw / 2 + 8; ctx.strokeStyle = pink; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, up ? y0 : y1); ctx.lineTo(x, up ? y1 : y0); ctx.stroke(); const ty = up ? y1 : y0, d = up ? 1 : -1; ctx.beginPath(); ctx.moveTo(x - 6, ty + 9 * d); ctx.lineTo(x, ty); ctx.lineTo(x + 6, ty + 9 * d); ctx.stroke(); };
      arrow(x0 + 8, true); arrow(x1 - 8, !st.mobius);
      ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'center';
      ctx.fillText(st.mobius ? 'the ends are glued with a flip, so the copy of gear 1 is seen from behind' : 'the ends are glued straight, so the copy of gear 1 turns the same way', W / 2, g0.y + bw / 2 + 22);
    }
    // contacts
    meshes.forEach(m => {
      if (m.ghost) return;
      const a = gears[m.a], b = gears[m.b], mx = (a.x * b.r + b.x * a.r) / (a.r + b.r), my = (a.y * b.r + b.y * a.r) / (a.r + b.r);
      const s = Lab.clamp(Math.abs(m.strain) / (TMAX * 0.4), 0, 1);
      ctx.fillStyle = s > 0.3 ? red : green; ctx.globalAlpha = 0.25 + 0.75 * s;
      ctx.beginPath(); ctx.arc(mx, my, 4 + 8 * s, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
    });
    // gears
    const jam = st.locked;
    gears.forEach((q, i) => {
      const dir = Math.abs(q.ws || 0) < 0.12 ? 0 : Math.sign(q.ws);
      gearPath(ctx, q);
      ctx.fillStyle = dir === 0 ? (jam ? '#b9bdd2' : '#c9cde0') : dir > 0 ? '#86a0f0' : '#f48fb1';
      ctx.fill(); ctx.strokeStyle = ink; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.fillStyle = stage; ctx.beginPath(); ctx.arc(q.x, q.y, q.r * 0.22, 0, TAU); ctx.fill(); ctx.stroke();
      // spoke so turning is visible
      ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(q.x + Math.cos(q.th) * q.r * 0.25, q.y + Math.sin(q.th) * q.r * 0.25); ctx.lineTo(q.x + Math.cos(q.th) * q.r * 0.75, q.y + Math.sin(q.th) * q.r * 0.75); ctx.stroke();
      if (i === st.motorGear) { ctx.fillStyle = ink; ctx.font = `700 ${Math.max(10, Math.min(13, q.r * 0.4))}px ${mono}`; ctx.textAlign = 'center'; ctx.fillText('motor', q.x, q.y + q.r * 0.55 + 6); }
      if (st.layout !== 'lattice' && q.r > 18) { ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'center'; ctx.fillText(String(i + 1), q.x, q.y - q.r * 0.38); }
    });
    // where the Möbius joint is: a badge on top of everything, just outside the ring
    if (st.layout === 'ring' && st.mobius) {
      const N = st.N, seamA = -Math.PI / 2 - Math.PI / N, rr = st.Rr;
      const a = gears[N - 1], b = gears[0], mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const bx = W / 2 + Math.cos(seamA) * (rr + gears[0].r * 0.2), by = H / 2 + Math.sin(seamA) * (rr + gears[0].r * 0.2);
      ctx.fillStyle = pink; ctx.beginPath(); ctx.arc(mx, my, 7, 0, TAU); ctx.fill();
      const label = 'Möbius joint';
      ctx.font = `700 12px ${mono}`; const tw = ctx.measureText(label).width + 16;
      let lx = Lab.clamp(bx - tw / 2, 6, W - tw - 6), ly = Lab.clamp(by - 11, 6, H - 28);
      ctx.fillStyle = stage; ctx.strokeStyle = pink; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(lx, ly, tw, 22, 11) : ctx.rect(lx, ly, tw, 22); ctx.fill(); ctx.stroke();
      ctx.fillStyle = pink; ctx.textAlign = 'center'; ctx.fillText(label, lx + tw / 2, ly + 15);
    }
    // the ghost copy of gear 1 at the end of the unrolled strip
    if (st.layout === 'strip') {
      const g0 = gears[0], gl = gears[gears.length - 1];
      const ghost = { x: gl.x + 2 * g0.r, y: g0.y, r: g0.r, th: st.mobius ? Math.PI - g0.th : g0.th };
      ctx.globalAlpha = 0.45; gearPath(ctx, ghost); ctx.setLineDash([4, 3]); ctx.strokeStyle = ink; ctx.lineWidth = 1.5; ctx.stroke(); ctx.setLineDash([]);
      ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(ghost.x + Math.cos(ghost.th) * ghost.r * 0.25, ghost.y + Math.sin(ghost.th) * ghost.r * 0.25); ctx.lineTo(ghost.x + Math.cos(ghost.th) * ghost.r * 0.75, ghost.y + Math.sin(ghost.th) * ghost.r * 0.75); ctx.stroke();
      ctx.globalAlpha = 1;
      ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'center'; ctx.fillText('gear 1 again', ghost.x, ghost.y - ghost.r * 1.25);
      const m = meshes[meshes.length - 1], s = Lab.clamp(Math.abs(m.strain) / TMAX, 0, 1);
      ctx.fillStyle = s > 0.25 ? red : green; ctx.globalAlpha = 0.25 + 0.75 * s; ctx.beginPath(); ctx.arc(gl.x + g0.r, g0.y, 4 + 8 * s, 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
    }
    // sparks where teeth slip
    sparks.forEach(sp => { ctx.strokeStyle = Lab.cssVar('--rhyme'); ctx.lineWidth = 2; ctx.globalAlpha = sp.life; for (let k = 0; k < 6; k++) { const a = k * TAU / 6 + sp.life * 3, r0 = 6 + (1 - sp.life) * 10, r1 = r0 + 8; ctx.beginPath(); ctx.moveTo(sp.x + Math.cos(a) * r0, sp.y + Math.sin(a) * r0); ctx.lineTo(sp.x + Math.cos(a) * r1, sp.y + Math.sin(a) * r1); ctx.stroke(); } ctx.globalAlpha = 1; });
    // legend
    ctx.font = `11px ${mono}`; ctx.textAlign = 'left';
    const lg = [['#f48fb1', 'clockwise'], ['#86a0f0', 'counter-clockwise'], ['#c9cde0', 'stuck']];
    lg.forEach(([c, t], i) => { const y = h - 14 - i * 16; ctx.fillStyle = c; ctx.fillRect(12, y - 9, 12, 12); ctx.fillStyle = muted; ctx.fillText(t, 30, y + 1); });
  }
  function parityLine() {
    if (st.layout === 'lattice') return st.lattice === 'square'
      ? 'Every loop on a square grid has an even number of steps (4, 6, 8 …), so every gear can alternate. It spins.'
      : 'A triangular grid is full of 3-gear loops, and 3 is odd. Every triangle has at least one pair of gears that can’t both be satisfied.';
    const N = st.N, flips = N % 2 ? -1 : 1, joint = st.mobius ? -1 : 1, ok = flips * joint === 1;
    return `Going once around: each of the ${N} contacts flips the direction, giving (−1)<sup>${N}</sup> = ${flips > 0 ? '+1' : '−1'}.${st.mobius ? ' The Möbius joint flips it once more: × (−1).' : ''} Total ${ok ? '+1, so the loop agrees with itself and can turn' : '−1, so the loop contradicts itself and locks'}.`;
  }
  function updateReadout() {
    const ok = st.layout === 'lattice' ? st.lattice === 'square' : ((st.N % 2 ? -1 : 1) * (st.mobius ? -1 : 1)) === 1;
    readout.querySelector('[data-k=rule]').innerHTML = parityLine();
    readout.querySelector('[data-k=pred]').innerHTML = ok ? '<span class="ok">Predicted: spins</span>' : '<span class="miss">Predicted: locks</span>';
  }

  ch.init = function (section, stage) {
    canvas = Lab.el('canvas', { 'aria-label': 'Gears turning or locked' });
    stage.append(canvas);
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.state = Lab.el('div', { class: 'chip' }); hud.meter = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.state, hud.meter); stage.append(hud.wrap);
    const c = section.querySelector('[data-controls]');
    const layout = Lab.ui.seg(c, { label: 'Layout', id: 'g-layout', value: 'ring', options: [{ value: 'ring', label: 'Ring' }, { value: 'strip', label: 'Unrolled' }, { value: 'lattice', label: 'Grid' }],
      onChange: v => { st.layout = v; nCtl.el.hidden = v === 'lattice'; jCtl.el.hidden = v === 'lattice'; latCtl.el.hidden = v !== 'lattice'; build(); updateReadout(); } });
    const nCtl = Lab.ui.slider(c, { label: 'Gears in the loop', id: 'g-n', min: 3, max: 12, step: 1, value: st.N, format: v => String(v), onInput: v => { st.N = v; build(); updateReadout(); } });
    const jCtl = Lab.ui.seg(c, { label: 'Joint', id: 'g-joint', value: 'plain', options: [{ value: 'plain', label: 'Plain band' }, { value: 'mobius', label: 'Möbius band' }], onChange: v => { st.mobius = v === 'mobius'; build(); updateReadout(); } });
    const latCtl = Lab.ui.seg(c, { label: 'Grid', id: 'g-lat', value: 'square', options: [{ value: 'square', label: 'Square' }, { value: 'triangle', label: 'Triangle' }], onChange: v => { st.lattice = v; build(); updateReadout(); } });
    latCtl.el.hidden = true;
    Lab.ui.slider(c, { label: 'Tooth grip', id: 'g-grip', min: 1, max: 8, step: 0.1, value: st.grip, format: v => (v >= 7.9 ? 'never slips' : v > 4 ? 'firm' : v > 2.6 ? 'loose' : 'slippery'), onInput: v => { st.grip = v >= 7.9 ? 1e9 : v; } });
    st.grip = 1e9;
    Lab.ui.seg(c, { label: 'Motor', id: 'g-motor', value: 'on', options: [{ value: 'on', label: 'On' }, { value: 'off', label: 'Off' }], onChange: v => { st.motor = v === 'on'; } });
    const row = Lab.ui.row(Lab.ui.group(c, ' '));
    Lab.ui.button(row, { label: 'Reset', id: 'g-reset', onClick: () => build() });
    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `<h4>The parity rule</h4><p style="margin:0 0 6px" data-k="rule"></p><p style="margin:0 0 10px" data-k="pred"></p>
      <div class="stats">
        <div class="stat"><div class="v" data-k="speed">0</div><div class="k">motor speed (turns/min)</div></div>
        <div class="stat"><div class="v" data-k="energy">0</div><div class="k">strain stored in teeth</div></div>
        <div class="stat"><div class="v" data-k="slips">0</div><div class="k">teeth slipped</div></div>
      </div>`;
    updateReadout();
    W = 0; H = 0;
  };
  ch.resize = function () { draw(); };
  ch.frame = function (dt) {
    if (!gears.length) { const r = canvas.getBoundingClientRect(); W = r.width; H = r.height; build(); }
    const sub = 6; for (let i = 0; i < sub; i++) step(Math.min(dt, 1 / 30) / sub);
    sparks.forEach(s => { s.life -= dt * 2.2; }); sparks = sparks.filter(s => s.life > 0);
    const mg = gears[st.motorGear];
    st.wAvg = (st.wAvg == null ? mg.w : st.wAvg + (mg.w - st.wAvg) * Math.min(1, dt * 1.5));
    st.locked = st.motor && Math.abs(st.wAvg) < 0.15;
    draw();
    const rpm = st.wAvg / TAU * 60;
    hud.state.textContent = !st.motor ? 'motor off' : st.locked ? (st.slips ? 'locked, teeth grinding' : 'locked: the motor stalls') : (st.slips && st.grip < 1e8 ? 'turning in jerks by slipping' : 'spinning freely');
    hud.state.className = 'chip ' + (st.motor && st.locked ? 'alert' : st.motor ? 'good' : '');
    hud.meter.innerHTML = `strain <b>${st.energy < 0.005 ? '0' : st.energy.toFixed(2)}</b>`;
    readout.querySelector('[data-k=speed]').textContent = Math.abs(rpm) < 0.5 ? '0' : Math.abs(rpm).toFixed(0);
    readout.querySelector('[data-k=energy]').textContent = st.energy < 0.005 ? '0' : st.energy.toFixed(2);
    readout.querySelector('[data-k=slips]').textContent = st.slips;
  };
  Lab.register(ch);
}
