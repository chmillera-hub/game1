/* ============================================================
   Experiment 6: Cosmic Forge (topological defects, Kibble–Zurek).
   Time-dependent Ginzburg–Landau on a periodic grid:
     dψ/dt = ∇²ψ + (μ(t) − |ψ|²) ψ + noise
   μ ramps from −1 (the flat, symmetric state) to +1 over the cooling
   time. Each grid square ends up "pointing" somewhere; where
   neighbours disagree a winding freezes in. For arrows ψ is the arrow
   (full twists, ±1). For headless lines ψ = e^{2iθ} of the line angle
   θ, the one-constant 2D liquid-crystal model, so the same windings
   are half twists (±½) of the lines.
   ============================================================ */
{
  const TAU = Lab.TAU;
  const st = { N: 128, material: 'lines', view: 'color', tauQ: 30, t: 0, noise: 2e-4, counts: [], plus: 0, minus: 0, test: null, testResults: [] };
  const ch = { token: 'forge', gl: false };
  let canvas, off, offCtx, img, re, im, re2, im2, rand, hud = {}, readout, histCanvas, testCanvas, testBtn, lut;

  function gaussFactory(seed) { const r = Lab.rng(seed); return () => { let u = 0; while (!u) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * r()); }; }
  function alloc(N) { return { re: new Float32Array(N * N), im: new Float32Array(N * N), re2: new Float32Array(N * N), im2: new Float32Array(N * N) }; }
  function melt() {
    const N = st.N, g = gaussFactory((Math.random() * 1e9) | 0);
    for (let i = 0; i < N * N; i++) { re[i] = 0.01 * g(); im[i] = 0.01 * g(); }
    st.t = 0; st.counts = [];
    rand = g;
  }
  function stepField(F, N, mu, noise, dt, g) {
    const { re, im, re2, im2 } = F, amp = Math.sqrt(2 * noise * dt);
    for (let y = 0; y < N; y++) {
      const y0 = y * N, ym = ((y - 1 + N) % N) * N, yp = ((y + 1) % N) * N;
      for (let x = 0; x < N; x++) {
        const i = y0 + x, xm = y0 + (x === 0 ? N - 1 : x - 1), xp = y0 + (x === N - 1 ? 0 : x + 1);
        const a = re[i], b = im[i];
        const lr = re[xm] + re[xp] + re[ym + x] + re[yp + x] - 4 * a, li = im[xm] + im[xp] + im[ym + x] + im[yp + x] - 4 * b;
        const k = mu - (a * a + b * b);
        re2[i] = a + dt * (lr + k * a) + amp * g();
        im2[i] = b + dt * (li + k * b) + amp * g();
      }
    }
    F.re = re2; F.im = im2; F.re2 = re; F.im2 = im;
  }
  const wrap = d => (d > Math.PI ? d - TAU : d < -Math.PI ? d + TAU : d);
  function findDefects(reA, imA, N, list) {
    const ph = new Float32Array(N * N);
    for (let i = 0; i < N * N; i++) ph[i] = Math.atan2(imA[i], reA[i]);
    let plus = 0, minus = 0;
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
      const x1 = (x + 1) % N, y1 = (y + 1) % N;
      const a = ph[y * N + x], b = ph[y * N + x1], c = ph[y1 * N + x1], d = ph[y1 * N + x];
      const s = wrap(b - a) + wrap(c - b) + wrap(d - c) + wrap(a - d);
      if (s > Math.PI) { plus++; if (list) list.push([x + 0.5, y + 0.5, 1]); }
      else if (s < -Math.PI) { minus++; if (list) list.push([x + 0.5, y + 0.5, -1]); }
    }
    return { plus, minus };
  }
  function mu() { return Math.min(1, -1 + 2 * st.t / st.tauQ); }

  /* ---------------- rendering ---------------- */
  function buildLut() {
    lut = new Uint8ClampedArray(360 * 3);
    for (let h = 0; h < 360; h++) {
      const c = hsl(h / 360, 0.72, 0.56);
      lut[h * 3] = c[0]; lut[h * 3 + 1] = c[1]; lut[h * 3 + 2] = c[2];
    }
  }
  function hsl(h, s, l) { // hsl -> rgb
    const f = n => { const k = (n + h * 12) % 12, a = s * Math.min(l, 1 - l); return 255 * (l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1))); };
    return [f(0), f(8), f(4)];
  }
  function draw(defects) {
    const { ctx, w, h } = Lab.fitCanvas(canvas);
    const N = st.N, data = img.data, m = Math.max(0.05, mu());
    const pol = st.view === 'pol' && st.material === 'lines';
    for (let i = 0; i < N * N; i++) {
      const a = re[i], b = im[i], amp2 = (a * a + b * b) / m, br = Math.min(1, Math.sqrt(amp2));
      const k = i * 4;
      if (pol) {
        const ang = Math.atan2(b, a), s = Math.sin(ang), I = s * s * Math.min(1, amp2) * 255;
        data[k] = I * 1.0 + 6; data[k + 1] = I * 0.94 + 4; data[k + 2] = I * 0.82 + 8;
      } else {
        let hdeg = Math.floor((Math.atan2(b, a) / TAU + 1) * 360) % 360;
        data[k] = lut[hdeg * 3] * br + 20 * (1 - br); data[k + 1] = lut[hdeg * 3 + 1] * br + 22 * (1 - br); data[k + 2] = lut[hdeg * 3 + 2] * br + 40 * (1 - br);
      }
      data[k + 3] = 255;
    }
    offCtx.putImageData(img, 0, 0);
    const S = Math.min(w, h), ox = (w - S) / 2, oy = (h - S) / 2, cell = S / N;
    ctx.fillStyle = Lab.cssVar('--stage'); ctx.fillRect(0, 0, w, h);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, ox, oy, S, S);
    // glyphs: arrows or headless lines
    const step = N >= 120 ? 8 : 6, len = cell * step * 0.42;
    ctx.strokeStyle = pol ? 'rgba(255,255,255,.55)' : 'rgba(15,18,40,.55)'; ctx.lineWidth = 1.4; ctx.lineCap = 'round';
    for (let y = step / 2; y < N; y += step) for (let x = step / 2; x < N; x += step) {
      const i = (y | 0) * N + (x | 0), a = re[i], b = im[i];
      if (a * a + b * b < 0.05 * m) continue;
      const cx = ox + (x + 0.5) * cell, cy = oy + (y + 0.5) * cell;
      if (st.material === 'lines') {
        const th = Math.atan2(b, a) / 2, dx = Math.cos(th) * len, dy = Math.sin(th) * len;
        ctx.beginPath(); ctx.moveTo(cx - dx, cy - dy); ctx.lineTo(cx + dx, cy + dy); ctx.stroke();
      } else {
        const th = Math.atan2(b, a), dx = Math.cos(th) * len, dy = Math.sin(th) * len;
        ctx.beginPath(); ctx.moveTo(cx - dx, cy - dy); ctx.lineTo(cx + dx, cy + dy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(cx + dx, cy + dy); ctx.lineTo(cx + dx - Math.cos(th - 0.5) * len * 0.5, cy + dy - Math.sin(th - 0.5) * len * 0.5);
        ctx.moveTo(cx + dx, cy + dy); ctx.lineTo(cx + dx - Math.cos(th + 0.5) * len * 0.5, cy + dy - Math.sin(th + 0.5) * len * 0.5); ctx.stroke();
      }
    }
    // defect markers
    if (defects && defects.length < 400) {
      const pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue');
      defects.forEach(([x, y, s]) => {
        const cx = ox + (x + 0.5) * cell, cy = oy + (y + 0.5) * cell;
        ctx.lineWidth = 2.2; ctx.strokeStyle = '#fff'; ctx.fillStyle = s > 0 ? '#e8457a' : '#3352d1';
        ctx.beginPath(); ctx.arc(cx, cy, Math.max(4, cell * 1.4), 0, TAU); ctx.fill(); ctx.stroke();
        ctx.fillStyle = '#fff'; ctx.font = `700 ${Math.max(9, cell * 1.6)}px ${Lab.cssVar('--font-mono')}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(s > 0 ? '+' : '−', cx, cy + 0.5); ctx.textBaseline = 'alphabetic';
      });
    }
  }
  function drawHistory() {
    const { ctx, w, h } = Lab.fitCanvas(histCanvas);
    ctx.clearRect(0, 0, w, h);
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), rule = Lab.cssVar('--rule'), pink = Lab.cssVar('--pink'), mono = Lab.cssVar('--font-mono');
    const x0 = 40, x1 = w - 10, y0 = 10, y1 = h - 24, tmax = Math.max(st.tauQ * 1.6, 60);
    const ly = v => y1 - Math.log10(Math.max(1, v)) / 3 * (y1 - y0);
    ctx.strokeStyle = rule; ctx.lineWidth = 1; ctx.font = `10px ${mono}`; ctx.fillStyle = muted; ctx.textAlign = 'right';
    [1, 10, 100, 1000].forEach(v => { ctx.beginPath(); ctx.moveTo(x0, ly(v)); ctx.lineTo(x1, ly(v)); ctx.stroke(); ctx.fillText(String(v), x0 - 4, ly(v) + 3); });
    const xq = x0 + st.tauQ / tmax * (x1 - x0);
    ctx.setLineDash([4, 4]); ctx.strokeStyle = muted; ctx.beginPath(); ctx.moveTo(xq, y0); ctx.lineTo(xq, y1); ctx.stroke(); ctx.setLineDash([]);
    ctx.textAlign = 'left'; ctx.fillText('cooling done', Math.min(xq + 4, x1 - 80), y0 + 10);
    ctx.textAlign = 'center'; ctx.fillText('time →', (x0 + x1) / 2, h - 6);
    ctx.strokeStyle = pink; ctx.lineWidth = 2.2; ctx.beginPath();
    st.counts.forEach(([t, c], i) => { const X = x0 + Math.min(t, tmax) / tmax * (x1 - x0), Y = ly(c); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
    ctx.stroke();
  }
  function drawTest() {
    const { ctx, w, h } = Lab.fitCanvas(testCanvas);
    ctx.clearRect(0, 0, w, h);
    const muted = Lab.cssVar('--muted'), rule = Lab.cssVar('--rule'), pink = Lab.cssVar('--pink'), ink = Lab.cssVar('--ink'), mono = Lab.cssVar('--font-mono');
    const x0 = 44, x1 = w - 12, y0 = 12, y1 = h - 26;
    const lx = v => x0 + (Math.log10(v) - Math.log10(4)) / (Math.log10(400) - Math.log10(4)) * (x1 - x0);
    const ly = v => y1 - Math.log10(Math.max(0.7, v)) / Math.log10(300) * (y1 - y0);
    ctx.strokeStyle = rule; ctx.font = `10px ${mono}`; ctx.fillStyle = muted;
    [1, 10, 100].forEach(v => { ctx.beginPath(); ctx.moveTo(x0, ly(v)); ctx.lineTo(x1, ly(v)); ctx.stroke(); ctx.textAlign = 'right'; ctx.fillText(String(v), x0 - 4, ly(v) + 3); });
    [5, 20, 80, 320].forEach(v => { ctx.textAlign = 'center'; ctx.fillText(String(v), lx(v), h - 12); });
    ctx.fillText('cooling time (slower →)', (x0 + x1) / 2, h - 1);
    if (!st.testResults.length) { ctx.fillStyle = muted; ctx.textAlign = 'left'; ctx.fillText('press "Run the forge test"', x0 + 8, y0 + 14); return; }
    ctx.fillStyle = pink;
    st.testResults.forEach(r => r.counts.forEach(c => { ctx.beginPath(); ctx.arc(lx(r.tau), ly(c), 4, 0, TAU); ctx.fill(); }));
    ctx.strokeStyle = ink; ctx.lineWidth = 1.5; ctx.beginPath();
    st.testResults.forEach((r, i) => { const m = r.counts.reduce((a, b) => a + b, 0) / r.counts.length; i ? ctx.lineTo(lx(r.tau), ly(m)) : ctx.moveTo(lx(r.tau), ly(m)); });
    ctx.stroke();
  }
  /* ---------------- the forge test: several quenches, run in the background ---------------- */
  function startTest() {
    const taus = [5, 16, 50, 160], seeds = [11, 22, 33], N = 72;
    st.testResults = taus.map(tau => ({ tau, counts: [] }));
    const jobs = []; taus.forEach((tau, ti) => seeds.forEach(sd => jobs.push({ tau, ti, sd })));
    st.test = { jobs, cur: null, N };
    testBtn.disabled = true; testBtn.textContent = 'Running…';
  }
  function runTestChunk(budgetMs) {
    const T = st.test; if (!T) return;
    const t0 = performance.now();
    while (performance.now() - t0 < budgetMs) {
      if (!T.cur) {
        const job = T.jobs.shift();
        if (!job) { st.test = null; testBtn.disabled = false; testBtn.textContent = 'Run the forge test'; drawTest(); summarizeTest(); return; }
        const F = alloc(T.N), g = gaussFactory(job.sd * 7919 + job.tau);
        for (let i = 0; i < T.N * T.N; i++) { F.re[i] = 0.01 * g(); F.im[i] = 0.01 * g(); }
        T.cur = { job, F, g, t: 0 };
      }
      const C = T.cur;
      for (let k = 0; k < 20; k++) { stepField(C.F, T.N, Math.min(1, -1 + 2 * C.t / C.job.tau), 2e-4, 0.1, C.g); C.t += 0.1; }
      if (C.t >= C.job.tau + 4) {
        const d = findDefects(C.F.re, C.F.im, T.N, null);
        st.testResults[C.job.ti].counts.push(d.plus + d.minus);
        T.cur = null; drawTest();
      }
    }
  }
  function summarizeTest() {
    const r = st.testResults, f = r[0], l = r[r.length - 1];
    const mf = f.counts.reduce((a, b) => a + b, 0) / f.counts.length, ml = l.counts.reduce((a, b) => a + b, 0) / l.counts.length;
    readout.querySelector('[data-k=test]').innerHTML = `Cooling ${l.tau / f.tau}× slower left <b>${mf.toFixed(0)} → ${ml.toFixed(0)}</b> twists on the same 72×72 patch (average of 3 runs each). Faster cooling freezes in more twists, which is the Kibble–Zurek prediction.`;
  }

  /* ---------------- interaction: drop a twist pair ---------------- */
  function dropPair(ev) {
    const r = canvas.getBoundingClientRect(), w = r.width, h = r.height, S = Math.min(w, h), ox = (w - S) / 2, oy = (h - S) / 2;
    const gx = (ev.clientX - r.left - ox) / S * st.N, gy = (ev.clientY - r.top - oy) / S * st.N;
    if (gx < 0 || gy < 0 || gx >= st.N || gy >= st.N) return;
    const N = st.N, d = 7, x1 = gx - d, x2 = gx + d, y1 = gy, y2 = gy;
    const amp = Math.sqrt(Math.max(0.2, mu()));
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
      // the pair's phase: the two branch cuts differ by whole turns, so e^{i·ph} is smooth
      const ph = Math.atan2(y - y1, x - x1) - Math.atan2(y - y2, x - x2);
      const i = y * N + x, a = re[i], b = im[i];
      const c = Math.cos(ph), s = Math.sin(ph);
      let nr = a * c - b * s, ni = a * s + b * c;
      if (Math.hypot(nr, ni) < 0.3 * amp) { nr = amp * Math.cos(ph); ni = amp * Math.sin(ph); }
      re[i] = nr; im[i] = ni;
    }
    Lab.toast(ch.stage, st.material === 'lines' ? 'Dropped a +½ and a −½ twist. Watch them find each other.' : 'Dropped a +1 and a −1 twist. Watch them find each other.', 2200);
  }

  ch.init = function (section, stage) {
    st.N = window.innerWidth < 600 ? 96 : 128;
    canvas = Lab.el('canvas', { 'aria-label': 'A cooling field with frozen-in twists. Tap to drop a pair of twists.' });
    stage.append(canvas);
    off = document.createElement('canvas'); off.width = off.height = st.N; offCtx = off.getContext('2d');
    img = offCtx.createImageData(st.N, st.N);
    re = new Float32Array(st.N * st.N); im = new Float32Array(st.N * st.N); re2 = new Float32Array(st.N * st.N); im2 = new Float32Array(st.N * st.N);
    buildLut(); melt();
    canvas.addEventListener('click', dropPair);
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.phase = Lab.el('div', { class: 'chip' }); hud.count = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.phase, hud.count); stage.append(hud.wrap);
    const bottom = Lab.el('div', { class: 'hud hud-bottom' });
    bottom.append(Lab.el('div', { class: 'chip', text: 'Tap the field to drop a pair of opposite twists.' }));
    stage.append(bottom);

    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Material', id: 'c-mat', value: st.material, options: [{ value: 'lines', label: 'Headless lines (half twists)' }, { value: 'arrows', label: 'Arrows (full twists)' }],
      onChange: v => { st.material = v; vs.el.hidden = v !== 'lines'; if (v !== 'lines') st.view = 'color'; vs.set(st.view); } });
    const vs = Lab.ui.seg(c, { label: 'View', id: 'c-view', value: 'color', options: [{ value: 'color', label: 'Colors' }, { value: 'pol', label: 'Polarizer' }], onChange: v => { st.view = v; } });
    Lab.ui.seg(c, { label: 'Cooling', id: 'c-cool', value: st.tauQ, options: [{ value: 8, label: 'Fast' }, { value: 30, label: 'Medium' }, { value: 120, label: 'Slow' }], onChange: v => { st.tauQ = v; melt(); } });
    const row = Lab.ui.row(Lab.ui.group(c, ' '));
    Lab.ui.button(row, { label: 'Melt and cool again', id: 'c-melt', primary: true, onClick: melt });

    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `<h4>Twist census</h4>
      <div class="stats" style="margin-bottom:8px">
        <div class="stat"><div class="v" data-k="plus">0</div><div class="k">twists one way (+)</div></div>
        <div class="stat"><div class="v" data-k="minus">0</div><div class="k">twists the other way (−)</div></div>
        <div class="stat"><div class="v" data-k="net">0</div><div class="k">net twist (always 0 here)</div></div>
      </div>
      <canvas data-hist class="plot short" aria-label="Number of twists over time"></canvas>
      <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">Twists are only ever made or destroyed in opposite pairs, so the net count never changes. That's what topologically locked means. After cooling, pairs find each other and cancel, so the count falls slowly (coarsening).</p>
      <h4 style="margin-top:14px">The forge test</h4>
      <canvas data-test class="plot short" aria-label="Twists left after cooling versus cooling time"></canvas>
      <div class="btn-row" style="margin-top:6px" data-testrow></div>
      <p class="verdict-line" data-k="test" style="font-size:.875rem">Runs twelve quenches on a smaller patch at four cooling speeds and counts the twists left just after cooling ends.</p>`;
    histCanvas = readout.querySelector('[data-hist]'); testCanvas = readout.querySelector('[data-test]');
    testBtn = Lab.ui.button(readout.querySelector('[data-testrow]'), { label: 'Run the forge test', id: 'c-test', onClick: startTest });
    drawTest();
  };
  ch.resize = function () { if (histCanvas) { drawHistory(); drawTest(); } };
  ch.frame = function (dt) {
    const F = { re, im, re2, im2 };
    const steps = 2;
    for (let k = 0; k < steps; k++) { stepField(F, st.N, mu(), st.noise, 0.1, rand); st.t += 0.1; }
    re = F.re; im = F.im; re2 = F.re2; im2 = F.im2;
    const list = [];
    const d = findDefects(re, im, st.N, list);
    if (!st.counts.length || st.t - st.counts[st.counts.length - 1][0] >= 0.5) { if (mu() > 0) st.counts.push([st.t, d.plus + d.minus]); drawHistory(); }
    draw(mu() > 0.2 ? list : null);
    const half = st.material === 'lines';
    const m = mu();
    hud.phase.innerHTML = m < 0 ? 'Hot: flat and featureless' : m < 1 ? `Cooling <b>${Math.round((m) * 100)}%</b>` : 'Cold: twists are frozen in';
    hud.count.innerHTML = m > 0.2 ? `<b>${d.plus + d.minus}</b> ${half ? 'half-twists (±½)' : 'full twists (±1)'}` : 'no twists yet';
    readout.querySelector('[data-k=plus]').textContent = m > 0.2 ? d.plus : 0;
    readout.querySelector('[data-k=minus]').textContent = m > 0.2 ? d.minus : 0;
    readout.querySelector('[data-k=net]').textContent = m > 0.2 ? d.plus - d.minus : 0;
    runTestChunk(9);
  };
  Lab.register(ch);
}
