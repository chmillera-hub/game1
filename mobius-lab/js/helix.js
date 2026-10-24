/* Helix Shot — "if you have a helix rotating clockwise, what's the probability the billiard ball moves left,
   right, or straight?" A spinning helix advances along its axis; its tip (a small sphere) strikes a ball.
   Rigid-body impulse with Coulomb friction, exact contact geometry, Monte Carlo over the tip's phase. */
(function () {
  'use strict';
  const ML = window.ML, C = ML.C, TAU = ML.TAU, D = 180 / Math.PI;
  const P = { r: 0.6, rt: 0.25, swirl: 1.2, hand: 1, mu: 0.35, table: true, pudding: false, randomPhase: true, auto: true };
  const NB = 36;
  const st = { shots: [], hLR: new Float64Array(NB), hSpin: new Float64Array(NB), n: 0, left: 0, right: 0, straight: 0, sameSpin: 0, anim: null, timer: 0.3, fixedPhase: 0.9 };
  let cv, ctx, W = 800, H = 600, ro, cvLR, cvSpin, lay = null;

  // ------------------------------------------------------------------ one collision (exact)
  // ball radius 1 at the origin; helix axis = x; tip offset (0, r cosφ, r sinφ); y = left, z = up.
  function shot(phi) {
    const Rb = 1, rt = P.rt, r = P.r, V = 1, w = (P.hand * P.swirl * V) / Math.max(r, 1e-3);
    const Rs = Rb + rt;
    if (r >= Rs) return { miss: true, phi };
    const xc = -Math.sqrt(Rs * Rs - r * r);
    const oy = r * Math.cos(phi), oz = r * Math.sin(phi);
    const n = [-xc / Rs, -oy / Rs, -oz / Rs];                         // from tip centre to ball centre
    const vt = [V, -w * oz, w * oy];                                  // tip velocity: advance + swirl
    const vn = vt[0] * n[0] + vt[1] * n[1] + vt[2] * n[2];
    const e = 1, Jn = (1 + e) * vn;                                   // per unit ball mass (helix is driven)
    const sl = [vt[0] - vn * n[0], vt[1] - vn * n[1], vt[2] - vn * n[2]], sm = Math.hypot(sl[0], sl[1], sl[2]);
    const Jt = sm > 1e-9 ? Math.min(P.mu * Jn, (2 / 7) * sm) : 0;     // Coulomb friction, capped at rolling
    const tt = sm > 1e-9 ? [sl[0] / sm, sl[1] / sm, sl[2] / sm] : [0, 0, 0];
    const v = [Jn * n[0] + Jt * tt[0], Jn * n[1] + Jt * tt[1], Jn * n[2] + Jt * tt[2]];
    // spin from the friction impulse at the contact point (−n·Rb): ω = (r × J)/I, I = 2/5
    const k = -2.5 * Jt;
    const om = [k * (n[1] * tt[2] - n[2] * tt[1]), k * (n[2] * tt[0] - n[0] * tt[2]), k * (n[0] * tt[1] - n[1] * tt[0])];
    const v3 = v.slice();                                             // the kick before the table flattens it
    if (P.table) v[2] = 0;                                            // the table soaks up the vertical part
    let path = null, vf = v.slice();
    if (P.pudding) {
      // travelling through "pudding": drag plus Magnus force (spin × velocity), integrated for 3 time units
      path = []; let x = [0, 0, 0], vv = v.slice(), o = om.slice();
      for (let i = 0; i < 300; i++) {
        const h = 0.01, km = 0.35, g = 0.25;
        const f = [km * (o[1] * vv[2] - o[2] * vv[1]), km * (o[2] * vv[0] - o[0] * vv[2]), km * (o[0] * vv[1] - o[1] * vv[0])];
        for (let c = 0; c < 3; c++) { vv[c] += (f[c] - g * vv[c]) * h; x[c] += vv[c] * h; o[c] *= 1 - 0.1 * h; }
        if (P.table) { vv[2] = 0; x[2] = 0; }
        if (i % 6 === 0) path.push(x.slice());
      }
      vf = vv;
    }
    const lr = Math.atan2(vf[1], vf[0]) * D;                          // + = left, − = right
    return { miss: false, phi, xc, n, v, v3, vf, om, lr, spinX: om[0], path };
  }
  function record(s) {
    st.n++;
    if (s.miss) return;
    const lr = s.lr;
    if (Math.abs(lr) < 2) st.straight++; else if (lr > 0) st.left++; else st.right++;
    if (Math.sign(s.spinX) === P.hand) st.sameSpin++;
    const b = Math.min(NB - 1, Math.max(0, Math.floor(((lr + 90) / 180) * NB)));
    st.hLR[b]++;
    const smax = 1.2, sb = Math.min(NB - 1, Math.max(0, Math.floor(((s.spinX + smax) / (2 * smax)) * NB)));
    st.hSpin[sb]++;
    st.shots.push(s); if (st.shots.length > 400) st.shots.shift();
  }
  function resetStats() { st.shots = []; st.hLR.fill(0); st.hSpin.fill(0); st.n = st.left = st.right = st.straight = st.sameSpin = 0; refresh(true); }
  const nextPhase = () => (P.randomPhase ? Math.random() * TAU : st.fixedPhase);

  // ------------------------------------------------------------------ drawing
  function computeLayout() {
    const pad = 16, narrow = W < 640;
    if (narrow) { const h1 = Math.round(H * 0.55); lay = { A: { x: pad, y: pad + 26, w: W - 2 * pad, h: h1 - pad - 30 }, B: { x: pad, y: h1 + 26, w: W - 2 * pad, h: H - h1 - 34 } }; }
    else { const w1 = Math.round(W * 0.6); lay = { A: { x: pad, y: pad + 26, w: w1 - 2 * pad, h: H - 2 * pad - 30 }, B: { x: w1 + pad, y: pad + 26, w: W - w1 - 2 * pad, h: H - 2 * pad - 30 } }; }
  }
  function title(R, t, sub) {
    const g = ctx;
    g.fillStyle = C.fg; g.font = '600 13px "IBM Plex Sans", sans-serif'; g.textAlign = 'left'; g.textBaseline = 'bottom';
    g.fillText(t, R.x, R.y - 6);
    if (sub) { g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'right'; g.fillText(sub, R.x + R.w, R.y - 7); }
  }
  function drawTop(an) {
    // seen from above: x to the right is the helix's travel direction; up on screen = left
    const g = ctx, R = lay.A, sc = Math.min(R.w / 10, R.h / 5.2), cx = R.x + R.w * 0.62, cy = R.y + R.h / 2;
    const X = (x) => cx + x * sc, Y = (y) => cy - y * sc;
    title(R, 'Seen from above', P.table ? 'ball rolls on a table' : 'ball floats free');
    g.strokeStyle = C.hair; g.lineWidth = 1; g.setLineDash([3, 5]);
    g.beginPath(); g.moveTo(R.x, cy); g.lineTo(R.x + R.w, cy); g.stroke(); g.setLineDash([]);
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'right'; g.textBaseline = 'bottom';
    g.fillText('left ↑', R.x + R.w, R.y + 14); g.textBaseline = 'top'; g.fillText('right ↓', R.x + R.w, R.y + R.h - 14);
    // fan of earlier outcomes
    g.strokeStyle = ML.rgba(C.s1, 0.12); g.lineWidth = 1.5;
    for (const s of st.shots) {
      if (s.miss) continue;
      g.beginPath(); g.moveTo(X(0), Y(0));
      if (s.path) for (const p of s.path) g.lineTo(X(p[0] * 0.9), Y(p[1] * 0.9));
      else { const l = Math.hypot(s.vf[0], s.vf[1]) || 1; g.lineTo(X((s.vf[0] / l) * 4.2), Y((s.vf[1] / l) * 4.2)); }
      g.stroke();
    }
    // helix body (the tip's path over the last two turns) and tip
    const r = P.r, pitch = (TAU * r) / Math.max(0.05, P.swirl);
    const tipX = an ? an.tipX : -5, ph = an ? an.ph : nextPhase();
    const pts = [];
    for (let s = 0; s <= 4.5; s += 0.04) {
      const angle = ph - (P.hand * TAU * s) / pitch;
      pts.push([tipX - s, r * Math.cos(angle), r * Math.sin(angle)]);
    }
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], front = (a[2] + b[2]) / 2 >= 0;
      g.strokeStyle = front ? C.tape : ML.rgba(C.tape, 0.35); g.lineWidth = front ? 4 : 3; g.lineCap = 'round';
      g.beginPath(); g.moveTo(X(a[0]), Y(a[1])); g.lineTo(X(b[0]), Y(b[1])); g.stroke();
    }
    const tip = pts[0];
    // ball
    let bx = 0, by = 0, rot = 0;
    if (an && an.hit && an.s && !an.s.miss) {
      const tt = an.t - an.tHit;
      if (an.s.path) { const idx = Math.min(an.s.path.length - 1, Math.floor(tt * 40)); bx = an.s.path[idx][0] * 0.9; by = an.s.path[idx][1] * 0.9; }
      else { const l = Math.hypot(an.s.vf[0], an.s.vf[1]) || 1; const d = Math.min(4.2, tt * 4.5); bx = (an.s.vf[0] / l) * d; by = (an.s.vf[1] / l) * d; }
      rot = tt * an.s.om[2] * 6;
    }
    g.fillStyle = '#f4efe6'; g.beginPath(); g.arc(X(bx), Y(by), sc, 0, TAU); g.fill();
    g.strokeStyle = C.paperDeep; g.lineWidth = 3; g.beginPath(); g.arc(X(bx), Y(by), sc * 0.62, rot, rot + Math.PI * 0.7); g.stroke();
    g.fillStyle = tip[2] >= 0 ? C.tape : '#9b7f45'; g.beginPath(); g.arc(X(tip[0]), Y(tip[1]), P.rt * sc, 0, TAU); g.fill();
    if (an && an.hit && an.t - an.tHit < 0.18) { g.fillStyle = 'rgba(255,255,255,0.8)'; g.beginPath(); g.arc(X(an.cx), Y(an.cy), 10, 0, TAU); g.fill(); }
  }
  function drawEnd(an) {
    // looking down the helix axis from behind: the tip circles round the ball
    const g = ctx, R = lay.B, sc = Math.min(R.w, R.h) / 4.4, cx = R.x + R.w / 2, cy = R.y + R.h / 2;
    const X = (y) => cx - y * sc, Y = (z) => cy - z * sc;          // y = left → screen left
    title(R, 'Looking down the helix', P.hand > 0 ? 'helix turns ↻' : 'helix turns ↺');
    g.fillStyle = '#f4efe6'; g.beginPath(); g.arc(cx, cy, sc, 0, TAU); g.fill();
    g.strokeStyle = ML.rgba(C.tape, 0.5); g.lineWidth = 1.5; g.setLineDash([4, 4]);
    g.beginPath(); g.arc(cx, cy, P.r * sc, 0, TAU); g.stroke(); g.setLineDash([]);
    // outcome directions as dots round a ring
    const rr = sc * 1.75;
    g.strokeStyle = C.hair; g.lineWidth = 1; g.beginPath(); g.arc(cx, cy, rr, 0, TAU); g.stroke();
    for (const s of st.shots) {
      if (s.miss) continue;
      const tv = Math.hypot(s.v3[1], s.v3[2]) || 1;
      const yy = s.v3[1] / tv, zz = s.v3[2] / tv;
      g.fillStyle = ML.rgba(C.s1, 0.55); g.beginPath(); g.arc(X(yy * 1.75), Y(zz * 1.75), 3, 0, TAU); g.fill();
    }
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'top';
    g.fillText('dots: which way the tip pushed each ball', cx, R.y + R.h - 14);
    g.textBaseline = 'middle'; g.fillText('L', X(2.1), cy); g.fillText('R', X(-2.1), cy);
    const ph = an ? an.ph : nextPhase();
    const ty = P.r * Math.cos(ph), tz = P.r * Math.sin(ph);
    g.fillStyle = C.tape; g.beginPath(); g.arc(X(ty), Y(tz), P.rt * sc, 0, TAU); g.fill();
    if (an && an.hit && an.s && !an.s.miss) {
      const tv = Math.hypot(an.s.v3[1], an.s.v3[2]);
      if (tv > 1e-6) {
        const yy = an.s.v3[1] / tv, zz = an.s.v3[2] / tv;
        g.strokeStyle = C.s1; g.lineWidth = 3; g.beginPath(); g.moveTo(cx, cy); g.lineTo(X(yy * 1.6), Y(zz * 1.6)); g.stroke();
      }
    }
  }

  // ------------------------------------------------------------------ panel
  const IDEAS = `
    <p class="quote">"If you have a helix rotating clockwise, what's the probability the billiard ball moves left, or right, or perfectly straight?"</p>
    <div><h4>What the sim shows</h4><ul>
      <li><b>Left or right: 50/50</b>, as long as you can't control when in its turn the tip arrives. The handedness of the helix does not favour a side.</li>
      <li><b>Dead straight almost never happens.</b> The tip is always off-centre by the helix radius, so the ball always leaves at the same angle from the axis. Only the direction around that cone varies.</li>
      <li><b>The extremes are the most likely.</b> Seen from above, the tip spends most of its time near the edges of its circle, like a pendulum lingering at the ends of its swing. So the left–right histogram is U-shaped.</li>
      <li><b>Handedness shows up as spin.</b> Friction at the hit makes the ball spin about the helix axis in the same sense as the helix, every single time. Turn friction to zero and the spin vanishes.</li>
      <li>Turn on <b>Fixed start</b> and every shot goes the same way. All the randomness was the timing.</li>
      <li>Turn on <b>Pudding</b>: the spinning ball curls as it moves (the Magnus effect, like a curveball). Every ball curls the same way round, but left and right stay balanced.</li>
    </ul></div>
    <div class="hook"><h4>Where this meets real physics</h4><ul>
      <li><b>Beth, 1936:</b> circularly polarised light (a corkscrew of light) made a quartz plate twist. A helix hands over its handedness as angular momentum, exactly as here.</li>
      <li>The U-shaped histogram is the <b>arcsine distribution</b>: what you get when you sample a circle's motion at random moments and look at it side-on.</li>
    </ul></div>`;

  const mode = {
    id: 'helix', tab: 'Helix Shot', kind: '2d',
    buildPanel(el) {
      const U = ML.ui;
      U.head(el, 'Helix shot', 'A spinning helix drives forward and its tip strikes a billiard ball. Real impact physics with friction, fired thousands of times.');
      const b1 = U.block(el, 'The helix');
      U.seg(b1, { id: 'h-hand', label: 'Spin (seen from behind the helix)', options: [[1, 'Clockwise ↻'], [-1, 'Counter-clockwise ↺']], value: P.hand, onChange: (v) => { P.hand = v; resetStats(); } });
      U.slider(b1, { id: 'h-r', label: 'Helix radius (ball radius = 1)', min: 0.1, max: 1.2, step: 0.05, value: P.r, fmt: (v) => v.toFixed(2), onInput: (v) => { P.r = v; resetStats(); } });
      U.slider(b1, { id: 'h-sw', label: 'Swirl speed ÷ forward speed', min: 0, max: 3, step: 0.1, value: P.swirl, fmt: (v) => v.toFixed(1) + '×', onInput: (v) => { P.swirl = v; resetStats(); } });
      U.slider(b1, { id: 'h-mu', label: 'Friction at the tip', min: 0, max: 0.8, step: 0.05, value: P.mu, fmt: (v) => v.toFixed(2), onInput: (v) => { P.mu = v; resetStats(); } });
      U.toggle(b1, { id: 'h-table', label: 'Ball sits on a table', value: P.table, onChange: (v) => { P.table = v; resetStats(); } });
      U.toggle(b1, { id: 'h-rand', label: 'Random timing (off = fixed start)', value: P.randomPhase, onChange: (v) => { P.randomPhase = v; resetStats(); } });
      U.toggle(b1, { id: 'h-pud', label: 'Ball moves through pudding (Magnus curl)', value: P.pudding, onChange: (v) => { P.pudding = v; resetStats(); } });
      const b2 = U.block(el, 'Fire');
      U.toggle(b2, { id: 'h-auto', label: 'Keep firing (animated)', value: P.auto, onChange: (v) => (P.auto = v) });
      U.buttons(b2, [
        { label: 'Fire 2,000 shots', primary: true, id: 'h-many', onClick: () => { for (let i = 0; i < 2000; i++) record(shot(nextPhase())); refresh(true); } },
        { label: 'Clear', id: 'h-clear', onClick: () => resetStats() },
      ]);
      const b3 = U.block(el, 'Results');
      ro = U.readouts(b3, [['n', 'Shots'], ['l', 'Goes left'], ['r', 'Goes right'], ['s', 'Within 2° of straight'], ['spin', 'Spins the same way as the helix']]);
      const f1 = ML.el('figure', { style: 'margin:0;display:grid;gap:4px' });
      f1.append(ML.el('figcaption', { class: 'chartcap', text: 'Final direction, right ← straight → left (−90° to +90°)' }));
      cvLR = ML.el('canvas', { class: 'chart', style: 'height:110px', role: 'img', 'aria-label': 'Histogram of left-right direction' });
      f1.append(cvLR); b3.append(f1);
      const f2 = ML.el('figure', { style: 'margin:0;display:grid;gap:4px' });
      f2.append(ML.el('figcaption', { class: 'chartcap', text: 'Ball spin about the helix axis (−1.2 to +1.2 turns per unit time)' }));
      cvSpin = ML.el('canvas', { class: 'chart', style: 'height:90px', role: 'img', 'aria-label': 'Histogram of ball spin about the helix axis' });
      f2.append(cvSpin); b3.append(f2);
      ML.attachHover(cvLR, (x, y, w) => { const i = ML.clamp(Math.floor(((x - 6) / (w - 12)) * NB), 0, NB - 1), a = -90 + (180 * i) / NB; return (a + 180 / NB / 2 > 0 ? 'left ' : 'right ') + Math.abs(a).toFixed(0) + '° to ' + Math.abs(a + 180 / NB).toFixed(0) + '°: ' + st.hLR[i] + ' shots'; });
      ML.attachHover(cvSpin, (x, y, w) => { const i = ML.clamp(Math.floor(((x - 6) / (w - 12)) * NB), 0, NB - 1), a = -1.2 + (2.4 * i) / NB; return 'spin ' + a.toFixed(2) + ' to ' + (a + 2.4 / NB).toFixed(2) + ': ' + st.hSpin[i] + ' shots'; });
      U.ideas(el, IDEAS);
    },
    buildHud() {},
    init(app) {
      cv = app.c2d;
      for (let i = 0; i < 600; i++) record(shot(nextPhase()));
    },
    enter() { st.timer = 0.2; },
    exit() { ML.tooltip(null); },
    resize(w, h) { W = w; H = h; ctx = ML.fitCanvas(cv, w, h); computeLayout(); refresh(true); },
    frame(dt) {
      if (!ctx) return;
      if (!st.anim && P.auto) { st.timer -= dt; if (st.timer <= 0) st.anim = { t: 0, ph0: nextPhase(), hit: false }; }
      const an = st.anim;
      if (an) {
        an.t += dt;
        const V = 3.2, w = (P.hand * P.swirl) / Math.max(P.r, 1e-3);
        const Rs = 1 + P.rt, xc = P.r < Rs ? -Math.sqrt(Rs * Rs - P.r * P.r) : 1.5;
        const tHit = 0.75;
        // tip reaches the contact point at tHit with the phase chosen for this shot
        an.tipX = xc - V * (tHit - Math.min(an.t, tHit));
        an.ph = an.ph0 - w * V * (tHit - Math.min(an.t, tHit));
        if (!an.hit && an.t >= tHit) {
          an.hit = true; an.tHit = tHit; an.s = shot(an.ph0); record(an.s);
          an.cx = an.s.miss ? 0 : -an.s.n[0]; an.cy = an.s.miss ? 0 : -an.s.n[1];   // contact point on the ball
          refresh(true);
        }
        if (an.t > 2.1) { st.anim = null; st.timer = 0.15; }
      }
      ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
      drawTop(an); drawEnd(an);
      refresh();
    },
    _P: P, _st: st, _shot: shot,
  };
  let rt = 0;
  function refresh(force) {
    rt -= 1 / 60; if (rt > 0 && !force) return; rt = 0.25;
    if (!ro) return;
    const hit = Math.max(1, st.n - 0);
    ro.set('n', ML.fmt(st.n));
    ro.set('l', ML.pct(st.left / hit, 1));
    ro.set('r', ML.pct(st.right / hit, 1));
    ro.set('s', ML.pct(st.straight / hit, 1));
    ro.set('spin', P.mu > 0 ? ML.pct(st.sameSpin / hit, 1) : 'no friction, no spin');
    if (cvLR && cvLR.getBoundingClientRect().width > 0) {
      ML.hist(cvLR, st.hLR, C.s1, { marks: [[0, 'right 90°'], [0.5, 'straight'], [1, 'left 90°']] });
      ML.hist(cvSpin, st.hSpin, C.s3, { marks: [[0, '↺ −1.2'], [0.5, '0'], [1, '↻ +1.2']] });
    }
  }
  ML.register(mode);
})();
