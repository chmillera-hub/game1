/* ============================================================
   Experiment 8: Spooky Ribbon.
   Part A, corkscrew: the helix tip circles with radius r; it hits the
   ball at phase θ, pushing it sideways by −cos θ (in the table's
   plane). Random timing means uniform θ, so the sideways kick has the
   arcsine distribution. The spin it gives always has the helix's hand.
   Part B, Bell/CHSH with a spin-½ pair, angles a and b:
     pre-twisted ribbon: shared hidden angle λ, A = sgn cos(λ−a), B = −sgn cos(λ−b)
     snapping ribbon: A = ±1; Bob's end flips to oppose A; B agrees with that
       with probability cos²((a−b)/2), chosen to reproduce quantum mechanics
     quantum mechanics: P(A = B) = sin²((a−b)/2)
   ============================================================ */
{
  const TAU = Lab.TAU, D = Math.PI / 180;
  const st = {
    part: 'cork', hand: 1, fixed: false, phase0: 0, shots: [], hist: new Array(24).fill(0), total: 0, spinCW: 0, anim: null,
    model: 'pre', a: 0, b: 45, trials: [], running: 0, pulse: null, chsh: null, signal: null
  };
  const ch = { token: 'ribbon', gl: false };
  let canvas, hud = {}, readout, rnd = Math.random, partCtl = [];

  /* ---------------- corkscrew ---------------- */
  function fire(n) {
    for (let k = 0; k < n; k++) {
      const th = st.fixed ? st.phase0 : Math.random() * TAU;
      const side = -Math.cos(th);                      // sideways kick, −1 … 1
      const bin = Math.min(st.hist.length - 1, Math.floor((side + 1) / 2 * st.hist.length));
      st.hist[bin]++; st.total++; if (Math.abs(side) < 0.05) st.straight = (st.straight || 0) + 1;
      if (st.hand > 0) st.spinCW++;
      if (st.shots.length > 120) st.shots.shift();
      st.shots.push({ side, life: 1 });
    }
    if (n === 1) st.anim = { t: 0, th: st.fixed ? st.phase0 : null };
    updateCorkReadout();
  }
  function corkStats() {
    let L = 0, Rt = 0, S = 0;
    const nb = st.hist.length;
    st.hist.forEach((c, i) => { const mid = -1 + (i + 0.5) * 2 / nb; if (mid < 0) L += c; else Rt += c; });
    return { L, R: Rt, S: st.straight || 0, n: st.total };
  }
  function updateCorkReadout() {
    const s = corkStats(), pc = v => (s.n >= 20 ? (100 * v / s.n).toFixed(1) + '%' : '–');
    readout.querySelector('[data-k=left]').textContent = pc(s.L);
    readout.querySelector('[data-k=right]').textContent = pc(s.R);
    readout.querySelector('[data-k=straight]').textContent = pc(s.S);
    readout.querySelector('[data-k=spin]').textContent = s.n ? (st.hand > 0 ? '100% clockwise' : '100% counter-clockwise') : '–';
    readout.querySelector('[data-k=n]').textContent = s.n;
  }
  function drawCork(ctx, w, h, dt) {
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), mono = Lab.cssVar('--font-mono');
    const narrow = w < 560;
    // table view
    const tx0 = 12, tw = narrow ? w - 24 : w * 0.64, th0 = 34, thh = narrow ? h * 0.44 : h - 120;
    ctx.fillStyle = '#2f7d5b'; ctx.fillRect(tx0, th0, tw, thh);
    ctx.strokeStyle = '#7a4b2a'; ctx.lineWidth = 6; ctx.strokeRect(tx0, th0, tw, thh);
    const by = th0 + thh / 2, bx = tx0 + tw * 0.42, br = Math.min(16, thh * 0.06);
    ctx.fillStyle = 'rgba(255,255,255,.85)'; ctx.font = `11px ${mono}`; ctx.textAlign = 'left'; ctx.fillText('table, seen from above', tx0 + 10, th0 + 16);
    // past shots fan out
    st.shots.forEach(s => {
      const ang = Math.atan(s.side * 0.75), len = tw * 0.55;
      ctx.strokeStyle = `rgba(255,255,255,${0.08 + 0.25 * s.life})`; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + Math.cos(ang) * len, by - Math.sin(ang) * len); ctx.stroke();
    });
    // the corkscrew: side view of a helix is a wave, front half bright, back half dim
    const t = performance.now() / 1000, spin = st.hand * 9;
    const anim = st.anim; let tipPhase = spin * t;
    if (anim) { anim.t += dt; }
    const hx1 = bx - br - 4 - (anim ? Math.max(0, 1 - anim.t * 2) * tw * 0.25 : tw * 0.25), hx0 = tx0 + 10;
    const amp = br * 0.9;
    for (let pass = 0; pass < 2; pass++) {
      ctx.beginPath();
      for (let x = hx0; x <= hx1; x += 2) {
        const ph = tipPhase + (x - hx1) / 9, y = by - Math.cos(ph) * amp, front = Math.sin(ph) > 0;
        if (front !== (pass === 1)) { ctx.moveTo(x, y); continue; }
        ctx.lineTo(x, y);
      }
      ctx.strokeStyle = pass ? '#ffd76a' : 'rgba(255,215,106,.35)'; ctx.lineWidth = pass ? 3 : 2; ctx.stroke();
    }
    // the ball
    let ballX = bx, ballY = by;
    if (anim && anim.t > 0.5) {
      const last = st.shots[st.shots.length - 1], ang = Math.atan(last.side * 0.75), d = Math.min(1, (anim.t - 0.5) * 1.6) * tw * 0.5;
      ballX = bx + Math.cos(ang) * d; ballY = by - Math.sin(ang) * d;
      if (anim.t > 1.3) st.anim = null;
    }
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ballX, ballY, br, 0, TAU); ctx.fill();
    ctx.strokeStyle = st.hand > 0 ? pink : blue; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(ballX, ballY, br * 0.6, 0.3, 4.6); ctx.stroke();
    // end view: where the tip is on its circle at impact
    const tb = th0 + thh;
    const er = narrow ? Math.max(18, Math.min(44, (h - tb - 64) / 2)) : Math.min(60, (w - tw) * 0.32);
    const ex = narrow ? w * 0.25 : tx0 + tw + (w - tx0 - tw) / 2, ey = narrow ? tb + 30 + er : th0 + 70;
    ctx.fillStyle = muted; ctx.textAlign = 'center'; ctx.font = `11px ${mono}`; ctx.fillText(narrow ? 'end view' : 'looking down the corkscrew', ex, ey - er - 10);
    ctx.strokeStyle = rule; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(ex, ey, er, 0, TAU); ctx.stroke();
    ctx.setLineDash([4, 4]); ctx.beginPath(); ctx.arc(ex, ey, er * 0.62, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
    const shownPhase = anim && anim.th != null ? anim.th : (st.fixed ? st.phase0 : tipPhase);
    const tipx = ex + Math.cos(shownPhase) * er * 0.62 * -1, tipy = ey + Math.sin(shownPhase) * er * 0.62;
    ctx.fillStyle = '#e0a400'; ctx.beginPath(); ctx.arc(tipx, tipy, 5, 0, TAU); ctx.fill();
    ctx.fillStyle = muted; ctx.fillText('ball', ex, ey + 4);
    ctx.fillText(st.hand > 0 ? (narrow ? 'tip: clockwise' : 'tip circles clockwise') : (narrow ? 'tip: counter-cw' : 'tip circles counter-clockwise'), ex, ey + er + 16);
    // histogram
    const hx = narrow ? w * 0.52 : tx0 + tw + 14, hw = narrow ? w * 0.46 : w - tx0 - tw - 26, hy0 = narrow ? tb + 34 : ey + er + 40, hy1 = h - 24;
    const nb = st.hist.length, maxc = Math.max(1, ...st.hist);
    ctx.fillStyle = muted; ctx.textAlign = 'center'; ctx.fillText('where the ball went', hx + hw / 2, hy0 - 8);
    st.hist.forEach((c, i) => { const bh = c / maxc * (hy1 - hy0 - 6); ctx.fillStyle = i < nb / 2 ? blue : pink; ctx.fillRect(hx + i * hw / nb + 1, hy1 - bh, hw / nb - 2, bh); });
    if (st.total > 30) {
      ctx.strokeStyle = ink; ctx.lineWidth = 1.5; ctx.beginPath();
      const scale = st.total * (2 / nb) / maxc * (hy1 - hy0 - 6);
      for (let i = 0; i <= 60; i++) { const y = -0.985 + i / 60 * 1.97, p = 1 / (Math.PI * Math.sqrt(1 - y * y)); const X = hx + (y + 1) / 2 * hw, Y = hy1 - Math.min(hy1 - hy0, p * scale); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); }
      ctx.stroke();
    }
    ctx.fillStyle = muted; ctx.textAlign = 'left'; ctx.fillText('left', hx, h - 8); ctx.textAlign = 'right'; ctx.fillText('right', hx + hw, h - 8); ctx.textAlign = 'center'; ctx.fillText('straight', hx + hw / 2, h - 8);
    st.shots.forEach(s => { s.life = Math.max(0, s.life - dt * 0.4); });
  }

  /* ---------------- Bell test ---------------- */
  function trial(model, a, b) {
    if (model === 'pre') { const l = rnd() * TAU; return [Math.cos(l - a) >= 0 ? 1 : -1, Math.cos(l - b) >= 0 ? -1 : 1, l]; }
    const A = rnd() < 0.5 ? 1 : -1;
    const pOpp = Math.cos((a - b) / 2) ** 2;            // snap: odds set by hand to match quantum mechanics
    return [A, rnd() < pOpp ? -A : A, null];
  }
  function E(model, a, b, n) { let s = 0; for (let i = 0; i < n; i++) { const r = trial(model, a, b); s += r[0] * r[1]; } return s / n; }
  function runCHSH() {
    const n = 5000, a = 0, a2 = 90 * D, b = 45 * D, b2 = 135 * D;
    const e = [E(st.model, a, b, n), E(st.model, a, b2, n), E(st.model, a2, b, n), E(st.model, a2, b2, n)];
    const S = Math.abs(e[0] - e[1] + e[2] + e[3]), sig = Math.sqrt(e.reduce((acc, v) => acc + (1 - v * v) / n, 0));
    st.chsh = { S, sig, model: st.model };
    drawCHSH();
  }
  function runSignal() {
    // Alice tries to send bits by choosing her angle (0 → a = 0°, 1 → a = 90°). Bob only sees his own results.
    const bits = [0, 1, 1, 0, 1, 0, 0, 1], n = 3000, out = [];
    bits.forEach(bit => { let plus = 0; for (let i = 0; i < n; i++) if (trial(st.model, bit ? 90 * D : 0, st.b * D)[1] > 0) plus++; out.push(plus / n); });
    st.signal = { bits, out };
    const rows = bits.map((b, i) => `<td>${b}</td>`).join(''), rows2 = st.signal.out.map(p => `<td>${(p * 100).toFixed(1)}%</td>`).join('');
    readout.querySelector('[data-k=signal]').innerHTML = `<div class="tbl-wrap"><table class="pieces" style="min-width:360px"><tr><th>Alice's bit</th>${rows}</tr><tr><th>Bob sees +</th>${rows2}</tr></table></div>
      <p class="verdict-line" style="font-size:.875rem">Bob's results stay at 50% whatever Alice chooses, so no message gets through. The ribbon is connected, but it isn't a telephone.</p>`;
  }
  function drawCHSH() {
    const cv = readout.querySelector('[data-chsh]'); const { ctx, w, h } = Lab.fitCanvas(cv);
    ctx.clearRect(0, 0, w, h);
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), real = Lab.cssVar('--real'), stretch = Lab.cssVar('--stretch'), mono = Lab.cssVar('--font-mono');
    const x0 = 12, x1 = w - 12, xOf = v => x0 + v / 3 * (x1 - x0);
    ctx.font = `10.5px ${mono}`;
    // scale
    ctx.strokeStyle = rule; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x0, h - 22); ctx.lineTo(x1, h - 22); ctx.stroke();
    [0, 1, 2, 3].forEach(v => { ctx.fillStyle = muted; ctx.textAlign = 'center'; ctx.fillText(String(v), xOf(v), h - 8); });
    ctx.fillStyle = 'rgba(180,45,71,.10)'; ctx.fillRect(xOf(2), 4, xOf(3) - xOf(2), h - 28);
    const mark = (v, label, col, y, dash) => { ctx.strokeStyle = col; ctx.lineWidth = 2; if (dash) ctx.setLineDash([5, 4]); ctx.beginPath(); ctx.moveTo(xOf(v), 6); ctx.lineTo(xOf(v), h - 22); ctx.stroke(); ctx.setLineDash([]); ctx.fillStyle = col; ctx.textAlign = v > 2.6 ? 'right' : 'left'; ctx.fillText(label, xOf(v) + (v > 2.6 ? -5 : 5), y); };
    mark(2, 'local limit 2', ink, 16, true);
    mark(2 * Math.SQRT2, 'quantum max 2.83', blue, 16, true);
    // experiments (published values of |S|)
    [[2.697, 'Aspect 1982'], [2.73, 'Weihs 1998'], [2.42, 'Delft 2015']].forEach(([v, l], i) => { ctx.fillStyle = real; ctx.beginPath(); ctx.arc(xOf(v), 34 + i * 14, 4, 0, TAU); ctx.fill(); ctx.textAlign = 'right'; ctx.fillText(l, xOf(v) - 7, 38 + i * 14); });
    if (st.chsh) {
      const y = h - 40, c = st.chsh.S > 2.05 ? pink : stretch;
      ctx.fillStyle = c; ctx.fillRect(xOf(0), y - 7, xOf(st.chsh.S) - xOf(0), 14);
      ctx.fillStyle = ink; ctx.textAlign = 'left'; ctx.font = `700 12px ${mono}`;
      const name = { pre: 'pre-twisted ribbon', snap: 'snapping ribbon', qm: 'quantum mechanics' }[st.chsh.model];
      ctx.fillText(`${name}: S = ${st.chsh.S.toFixed(2)} ± ${st.chsh.sig.toFixed(2)}`, xOf(0) + 6, y - 11);
    } else { ctx.fillStyle = muted; ctx.textAlign = 'left'; ctx.fillText('press "Run the Bell test"', x0, h - 40); }
  }
  function drawBell(ctx, w, h, dt) {
    const ink = Lab.cssVar('--ink'), muted = Lab.cssVar('--muted'), pink = Lab.cssVar('--pink'), blue = Lab.cssVar('--blue'), rule = Lab.cssVar('--rule'), mono = Lab.cssVar('--font-mono');
    const top = h * 0.46, cy = 26 + top * 0.5, ax = Math.max(60, w * 0.13), bx = w - ax, sx = w / 2, dr = Math.min(42, top * 0.36);
    // ribbon: drawn as a twisted strip from Alice to Bob
    const last = st.trials[st.trials.length - 1];
    const lam = last && last[2] != null ? last[2] : null;
    for (let x = ax + dr; x < bx - dr; x += 3) {
      const u = (x - ax) / (bx - ax), tw = (lam != null ? lam : performance.now() / 900) + u * Math.PI, wdt = 9 * Math.cos(tw);
      ctx.strokeStyle = Math.cos(tw) > 0 ? '#f27aa2' : '#e15c88'; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(x, cy - wdt); ctx.lineTo(x, cy + wdt); ctx.stroke();
    }
    // pulse / snap
    if (st.pulse) {
      st.pulse.t += dt * 2.2;
      const p = Math.min(1, st.pulse.t);
      if (st.model === 'pre') {
        [sx - p * (sx - ax - dr), sx + p * (bx - dr - sx)].forEach(x => { ctx.fillStyle = '#ffd76a'; ctx.beginPath(); ctx.arc(x, cy, 6, 0, TAU); ctx.fill(); });
      } else if (p > 0.5) { ctx.strokeStyle = 'rgba(255,215,106,.9)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(ax + dr, cy); ctx.lineTo(bx - dr, cy); ctx.stroke(); }
      else { const x = sx - p * 2 * (sx - ax - dr); ctx.fillStyle = '#ffd76a'; ctx.beginPath(); ctx.arc(x, cy, 6, 0, TAU); ctx.fill(); }
      if (st.pulse.t > 1.4) st.pulse = null;
    }
    ctx.fillStyle = muted; ctx.font = `11px ${mono}`; ctx.textAlign = 'center';
    ctx.fillText(st.model === 'pre' ? 'each end leaves with its answer already set' : 'when Alice measures, the whole ribbon snaps at once', sx, cy + 40);
    // detectors
    const det = (x, ang, name, res) => {
      ctx.strokeStyle = rule; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, cy, dr, 0, TAU); ctx.stroke();
      const a = -Math.PI / 2 + ang * D;
      ctx.strokeStyle = ink; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x - Math.cos(a) * dr * 0.8, cy - Math.sin(a) * dr * 0.8); ctx.lineTo(x + Math.cos(a) * dr * 0.8, cy + Math.sin(a) * dr * 0.8); ctx.stroke();
      ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(x + Math.cos(a) * dr * 0.8, cy + Math.sin(a) * dr * 0.8, 4, 0, TAU); ctx.fill();
      ctx.fillStyle = ink; ctx.font = `600 12px ${mono}`; ctx.fillText(`${name} · ${Math.round(ang)}°`, x, cy - dr - 10);
      if (res) { ctx.fillStyle = res > 0 ? pink : blue; ctx.font = `700 20px ${mono}`; ctx.fillText(res > 0 ? '↑' : '↓', x, cy + dr + 22); }
    };
    const showRes = last && !st.pulse;
    det(ax, st.a, 'Alice', showRes ? last[0] : 0); det(bx, st.b, 'Bob', showRes ? last[1] : 0);
    // correlation plot
    const px0 = 44, px1 = w - 14, py0 = top + 44, py1 = h - 28;
    const xOf = d => px0 + d / 180 * (px1 - px0), yOf = e => py0 + (1 - e) / 2 * (py1 - py0);
    ctx.strokeStyle = rule; ctx.lineWidth = 1; ctx.font = `10px ${mono}`; ctx.fillStyle = muted;
    [-1, 0, 1].forEach(e => { ctx.beginPath(); ctx.moveTo(px0, yOf(e)); ctx.lineTo(px1, yOf(e)); ctx.stroke(); ctx.textAlign = 'right'; ctx.fillText((e > 0 ? '+' : '') + e, px0 - 6, yOf(e) + 3); });
    [0, 45, 90, 135, 180].forEach(d => { ctx.textAlign = 'center'; ctx.fillText(d + '°', xOf(d), py1 + 14); });
    ctx.textAlign = 'left'; ctx.fillText('correlation of the two ends (−1 always opposite, +1 always the same) vs. angle between detectors', px0, py0 - 8);
    // theory curves
    ctx.lineWidth = 2; ctx.strokeStyle = Lab.cssVar('--stretch'); ctx.setLineDash([6, 4]); ctx.beginPath();
    for (let d = 0; d <= 180; d += 2) { const e = -1 + 2 * d / 180, X = xOf(d), Y = yOf(e); d ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); } ctx.stroke();
    ctx.strokeStyle = blue; ctx.setLineDash([]); ctx.beginPath();
    for (let d = 0; d <= 180; d += 2) { const e = -Math.cos(d * D), X = xOf(d), Y = yOf(e); d ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); } ctx.stroke();
    ctx.fillStyle = Lab.cssVar('--stretch'); ctx.textAlign = 'left'; ctx.fillText('any pre-set ribbon (straight line)', xOf(100), yOf(-0.62));
    ctx.fillStyle = blue; ctx.fillText('quantum mechanics and experiments (curve)', xOf(10), yOf(0.55));
    // measured point at the current angle difference
    let dd = Math.abs(st.a - st.b) % 360; if (dd > 180) dd = 360 - dd;
    if (st.trials.length) {
      const n = st.trials.length, e = st.trials.reduce((s, r) => s + r[0] * r[1], 0) / n, er = Math.sqrt(Math.max(0, 1 - e * e) / n);
      ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(xOf(dd), yOf(Math.min(1, e + er))); ctx.lineTo(xOf(dd), yOf(Math.max(-1, e - er))); ctx.stroke();
      ctx.fillStyle = pink; ctx.beginPath(); ctx.arc(xOf(dd), yOf(e), 6, 0, TAU); ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.stroke();
      hud.b.innerHTML = `angle ${dd.toFixed(0)}° · ${n} pairs · agreement <b>${e.toFixed(2)}</b>`;
    } else hud.b.innerHTML = `angle ${dd.toFixed(0)}° · no pairs yet`;
  }
  function sendPairs(n) {
    for (let i = 0; i < n; i++) st.trials.push(trial(st.model, st.a * D, st.b * D));
    if (st.trials.length > 20000) st.trials.splice(0, st.trials.length - 20000);
    st.pulse = n === 1 ? { t: 0 } : null;
  }

  /* ---------------- frame ---------------- */
  let lastT = performance.now();
  function draw() {
    const { ctx, w, h } = Lab.fitCanvas(canvas);
    const now = performance.now(), dt = Math.min(0.05, (now - lastT) / 1000); lastT = now;
    ctx.fillStyle = Lab.cssVar('--stage'); ctx.fillRect(0, 0, w, h);
    if (st.part === 'cork') drawCork(ctx, w, h, dt); else drawBell(ctx, w, h, dt);
  }
  function setPart(p) {
    st.part = p;
    partCtl.forEach(([el, part]) => { el.hidden = part !== p; });
    readout.querySelectorAll('[data-part]').forEach(el => { el.hidden = el.dataset.part !== p; });
    hud.a.textContent = p === 'cork' ? 'Part A · the corkscrew lottery' : 'Part B · Bell test';
    hud.b.hidden = p !== 'bell';
    if (p === 'bell') drawCHSH();
  }
  ch.init = function (section, stage) {
    canvas = Lab.el('canvas', { 'aria-label': 'Corkscrew billiards and a Bell test of the stretched ribbon' });
    stage.append(canvas);
    hud.wrap = Lab.el('div', { class: 'hud' });
    hud.a = Lab.el('div', { class: 'chip' }); hud.b = Lab.el('div', { class: 'chip' });
    hud.wrap.append(hud.a, hud.b); stage.append(hud.wrap);
    const c = section.querySelector('[data-controls]');
    Lab.ui.seg(c, { label: 'Part', id: 'r-part', value: 'cork', options: [{ value: 'cork', label: 'A · Corkscrew' }, { value: 'bell', label: 'B · Bell test' }], onChange: setPart });
    // corkscrew controls
    const g1 = Lab.ui.seg(c, { label: 'Corkscrew turns', id: 'r-hand', value: 1, options: [{ value: 1, label: 'Clockwise' }, { value: -1, label: 'Counter-clockwise' }], onChange: v => { st.hand = v; st.spinCW = 0; updateCorkReadout(); } });
    const g2 = Lab.ui.seg(c, { label: 'Timing', id: 'r-time', value: 'random', options: [{ value: 'random', label: 'Random (unknown)' }, { value: 'fixed', label: 'Known exactly' }], onChange: v => { st.fixed = v === 'fixed'; st.phase0 = Math.random() * TAU; } });
    const r1 = Lab.ui.row(Lab.ui.group(c, 'Shoot'));
    Lab.ui.button(r1, { label: 'Fire 1', id: 'r-f1', primary: true, onClick: () => fire(1) });
    Lab.ui.button(r1, { label: 'Fire 100', id: 'r-f100', onClick: () => fire(100) });
    Lab.ui.button(r1, { label: 'Fire 2,000', id: 'r-f2k', onClick: () => fire(2000) });
    Lab.ui.button(r1, { label: 'Clear', id: 'r-clear', onClick: () => { st.hist.fill(0); st.total = 0; st.straight = 0; st.shots = []; updateCorkReadout(); } });
    // bell controls
    const g3 = Lab.ui.seg(c, { label: 'Ribbon model', id: 'r-model', value: 'pre', options: [{ value: 'pre', label: 'Pre-twisted (your notes)' }, { value: 'snap', label: 'Snaps as one piece' }, { value: 'qm', label: 'Quantum mechanics' }],
      onChange: v => { st.model = v; st.trials = []; st.chsh = null; drawCHSH(); readout.querySelector('[data-k=signal]').innerHTML = ''; } });
    const sa = Lab.ui.slider(c, { label: "Alice's detector", id: 'r-a', min: 0, max: 180, step: 5, value: st.a, format: v => v + '°', onInput: v => { st.a = v; st.trials = []; } });
    const sb = Lab.ui.slider(c, { label: "Bob's detector", id: 'r-b', min: 0, max: 180, step: 5, value: st.b, format: v => v + '°', onInput: v => { st.b = v; st.trials = []; } });
    const r2 = Lab.ui.row(Lab.ui.group(c, 'Send pairs'));
    Lab.ui.button(r2, { label: 'Send 1', id: 'r-p1', primary: true, onClick: () => sendPairs(1) });
    Lab.ui.button(r2, { label: 'Send 1,000', id: 'r-p1k', onClick: () => sendPairs(1000) });
    partCtl = [[g1.el, 'cork'], [g2.el, 'cork'], [r1.parentElement, 'cork'], [g3.el, 'bell'], [sa.el, 'bell'], [sb.el, 'bell'], [r2.parentElement, 'bell']];
    readout = section.querySelector('[data-readout]');
    readout.innerHTML = `
      <div data-part="cork">
        <h4>Your question, answered</h4>
        <div class="stats">
          <div class="stat"><div class="v" data-k="left">–</div><div class="k">went left</div></div>
          <div class="stat"><div class="v" data-k="right">–</div><div class="k">went right</div></div>
          <div class="stat"><div class="v" data-k="straight">–</div><div class="k">nearly straight (within 5% of the max kick)</div></div>
          <div class="stat"><div class="v" data-k="spin" style="font-size:1rem">–</div><div class="k">spin given to the ball</div></div>
        </div>
        <p class="verdict-line" style="font-size:.875rem;color:var(--muted)"><span data-k="n">0</span> shots. The black curve is the arcsine law, what you get from anything that swings with a random timing. Switch Timing to "Known exactly" and every shot goes the same way: the randomness was only ignorance of the timing, a hidden variable.</p>
      </div>
      <div data-part="bell" hidden>
        <h4>The Bell test (CHSH)</h4>
        <canvas data-chsh class="plot" style="height:150px" aria-label="CHSH score of the model compared with the local limit, the quantum maximum and three experiments"></canvas>
        <div class="btn-row" style="margin-top:6px" data-chshrow></div>
        <p class="verdict-line" style="font-size:.875rem;color:var(--muted)">S combines the agreement at four detector settings (0°, 90° for Alice; 45°, 135° for Bob). Any ribbon whose ends carry their answers from the start scores at most 2. Green dots are published experimental results.</p>
        <h4 style="margin-top:12px">Can Alice text Bob?</h4>
        <div data-k="signal"></div>
      </div>`;
    const cr = readout.querySelector('[data-chshrow]');
    Lab.ui.button(cr, { label: 'Run the Bell test', id: 'r-chsh', primary: true, onClick: runCHSH });
    Lab.ui.button(cr, { label: 'Try to send a message', id: 'r-sig', onClick: runSignal });
    setPart('cork');
    fire(300);
    fire(1);
  };
  ch.resize = function () { draw(); if (st.part === 'bell') drawCHSH(); };
  ch.frame = function () { draw(); };
  Lab.register(ch);
}
