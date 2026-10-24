/* Stretched Strip — "one long Möbius strip, carefully stretched… when it is observed it snaps into two strips,
   one spin up and one spin down." Run as a Bell test with two versions of the idea:
   local  : each half gets its handedness instructions when the strip is stretched;
   ribbon : the strip stays one object until the cut; cutting at Alice sets Bob's end at once. */
(function () {
  'use strict';
  const ML = window.ML, C = ML.C, TAU = ML.TAU;
  const D = Math.PI / 180;
  const st = {
    model: 'ribbon', a: 0, b: 45, auto: true, anim: null, timer: 0.4,
    tallies: {}, sweep: { local: [], ribbon: [] }, chsh: { local: null, ribbon: null }, last: null,
  };
  let cv, ctx, W = 800, H = 600, ro, hud = {}, sa, sb, modelSeg, layout = null, hover = null;

  // ------------------------------------------------------------------ the two models
  function trial(model, a, b) {
    a *= D; b *= D;
    if (model === 'local') {
      const lam = Math.random() * TAU;                       // instructions fixed when the strip is stretched
      const A = Math.cos(a - lam) >= 0 ? 1 : -1, B = Math.cos(b - lam) >= 0 ? -1 : 1;
      return { A, B, lam };
    }
    const A = Math.random() < 0.5 ? 1 : -1;                  // cutting at Alice: a fair coin
    const same = Math.random() < Math.sin((a - b) / 2) ** 2;  // Bob's end is set at once, at Alice's angle
    return { A, B: same ? A : -A, lam: a + (A > 0 ? 0 : Math.PI) };
  }
  const theory = {
    ribbon: (th) => -Math.cos(th * D),
    local: (th) => { let t = Math.abs(((th % 360) + 360) % 360); if (t > 180) t = 360 - t; return -(1 - (2 * t) / 180); },
  };
  function tally(model, a, b, r) {
    const k = model + '|' + a + '|' + b;
    const t = st.tallies[k] || (st.tallies[k] = { n: 0, ab: 0, bp: 0 });
    t.n++; t.ab += r.A * r.B; if (r.B > 0) t.bp++;
    return t;
  }
  function runMany(model, a, b, n) { let t; for (let i = 0; i < n; i++) t = tally(model, a, b, trial(model, a, b)); return t; }
  function E(model, a, b, n) { let s = 0; for (let i = 0; i < n; i++) { const r = trial(model, a, b); s += r.A * r.B; } return s / n; }
  function sweep() {
    for (const m of ['local', 'ribbon']) {
      st.sweep[m] = [];
      for (let d = 0; d <= 360; d += 15) st.sweep[m].push({ th: d, e: E(m, 0, d, 1500), n: 1500 });
    }
  }
  function chsh() {
    for (const m of ['local', 'ribbon']) {
      const n = 4000;
      st.chsh[m] = Math.abs(E(m, 0, 45, n) - E(m, 0, 135, n) + E(m, 90, 45, n) + E(m, 90, 135, n));
    }
  }

  // ------------------------------------------------------------------ drawing
  function computeLayout() {
    const narrow = W < 620;
    const sceneH = Math.round(H * (narrow ? 0.4 : 0.46));
    const pad = 18;
    if (narrow) {
      const chH = Math.round((H - sceneH) * 0.62);
      layout = { scene: { x: 0, y: 0, w: W, h: sceneH }, chart: { x: pad, y: sceneH + 8, w: W - 2 * pad, h: chH - 16 }, meter: { x: pad, y: sceneH + chH, w: W - 2 * pad, h: H - sceneH - chH - 10 } };
    } else {
      const cw = Math.round(W * 0.6);
      layout = { scene: { x: 0, y: 0, w: W, h: sceneH }, chart: { x: pad, y: sceneH + 10, w: cw - 2 * pad, h: H - sceneH - 28 }, meter: { x: cw + pad, y: sceneH + 10, w: W - cw - 2 * pad, h: H - sceneH - 28 } };
    }
  }

  function drawRibbon(x0, x1, yc, hw, phase, alpha, split) {
    const g = ctx, n = 80;
    for (let i = 0; i < n; i++) {
      const u0 = i / n, u1 = (i + 1) / n;
      if (split !== null && u0 < 0.5 && u1 > 0.5) continue;
      const p0 = phase + Math.PI * u0, p1 = phase + Math.PI * u1;         // one half-twist along the strip
      const xa = ML.lerp(x0, x1, u0), xb = ML.lerp(x0, x1, u1);
      const c0 = Math.cos(p0), c1 = Math.cos(p1);
      g.beginPath();
      g.moveTo(xa, yc - hw * c0); g.lineTo(xb, yc - hw * c1); g.lineTo(xb, yc + hw * c1); g.lineTo(xa, yc + hw * c0); g.closePath();
      const front = (c0 + c1) / 2 >= 0;
      g.fillStyle = ML.rgba(front ? C.paper : '#a8466b', alpha); g.fill();
      if (front && i % 6 === 0) { g.strokeStyle = ML.rgba('#3b4cc0', 0.5 * alpha); g.lineWidth = 1; g.beginPath(); g.moveTo(xa, yc - hw * c0); g.lineTo(xa, yc + hw * c0); g.stroke(); }
    }
  }
  function curl(x, y, sign, k, col) {
    // a snapped half curling into a little loop: clockwise = +1, counter-clockwise = −1
    const g = ctx, r = 16 * k;
    g.strokeStyle = col; g.lineWidth = 6; g.lineCap = 'round';
    const a0 = -Math.PI / 2, a1 = a0 + sign * TAU * 0.82 * k;
    g.beginPath(); g.arc(x, y, r, Math.min(a0, a1), Math.max(a0, a1)); g.stroke();
    if (k > 0.6) {
      const ax = x + r * Math.cos(a1), ay = y + r * Math.sin(a1), tang = a1 + (sign * Math.PI) / 2;
      g.fillStyle = col; g.beginPath();
      g.moveTo(ax + 7 * Math.cos(tang), ay + 7 * Math.sin(tang));
      g.lineTo(ax + 6 * Math.cos(tang + 2.4), ay + 6 * Math.sin(tang + 2.4));
      g.lineTo(ax + 6 * Math.cos(tang - 2.4), ay + 6 * Math.sin(tang - 2.4)); g.closePath(); g.fill();
    }
  }
  function dial(x, y, ang, name, res) {
    const g = ctx, r = 30;
    g.fillStyle = C.panel2; g.strokeStyle = C.hair; g.lineWidth = 1.5;
    g.beginPath(); g.arc(x, y, r, 0, TAU); g.fill(); g.stroke();
    g.strokeStyle = C.tape; g.lineWidth = 3; g.lineCap = 'round';
    const ca = Math.cos(-ang * D), sa_ = Math.sin(-ang * D);
    g.beginPath(); g.moveTo(x - ca * (r - 6), y - sa_ * (r - 6)); g.lineTo(x + ca * (r - 6), y + sa_ * (r - 6)); g.stroke();
    g.fillStyle = C.fg; g.font = '600 13px "IBM Plex Sans", sans-serif'; g.textAlign = 'center'; g.textBaseline = 'top';
    g.fillText(name, x, y + r + 8);
    g.fillStyle = C.fg2; g.font = '500 12px "IBM Plex Mono", monospace';
    g.fillText(ang + '°', x, y + r + 26);
    if (res) {
      g.font = '700 15px "IBM Plex Mono", monospace'; g.fillStyle = C.fg;
      g.fillText(res > 0 ? '+1 ↻' : '−1 ↺', x, y - r - 28);
    }
  }

  function drawScene(dt) {
    const g = ctx, L = layout.scene;
    const yc = L.y + L.h * 0.52, xA = L.x + Math.max(60, L.w * 0.12), xB = L.x + L.w - Math.max(60, L.w * 0.12), xm = (xA + xB) / 2;
    // source spool
    g.fillStyle = C.panel2; g.strokeStyle = C.hair; g.lineWidth = 1.5;
    g.beginPath(); g.arc(xm, yc, 14, 0, TAU); g.fill(); g.stroke();
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'top';
    g.fillText('source', xm, yc + 22);
    const an = st.anim;
    let resA = null, resB = null;
    if (an) {
      an.t += dt;
      const grow = ML.clamp(an.t / 0.55, 0, 1), snap = an.t > 0.75, k = ML.clamp((an.t - 0.75) / 0.35, 0, 1);
      const ph = st.model === 'local' ? an.r.lam : an.t * 9;   // local: fixed instructions; ribbon: undecided shimmer
      const xl = ML.lerp(xm, xA + 34, ML.smooth(grow)), xr = ML.lerp(xm, xB - 34, ML.smooth(grow));
      if (!snap) drawRibbon(xl, xr, yc, 14, ph, 1, null);
      if (st.model === 'local' && !snap && grow > 0.3) {
        g.fillStyle = C.fg2; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'bottom';
        g.fillText('each half already carries its instructions', xm, yc - 26);
      }
      if (st.model === 'ribbon' && !snap && grow > 0.3) {
        g.fillStyle = C.fg2; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'bottom';
        g.fillText('one strip, undecided until it is cut', xm, yc - 26);
      }
      if (snap) {
        // the snip at Alice, then both halves curl
        if (an.t < 0.95) { g.fillStyle = 'rgba(255,255,255,' + (1 - (an.t - 0.75) / 0.2) + ')'; g.beginPath(); g.arc(xA + 34, yc, 12, 0, TAU); g.fill(); }
        const back = 1 - k;
        drawRibbon(xA + 34, ML.lerp(xA + 34, xm, back), yc, 14 * back + 0.01, an.r.lam, back, null);
        drawRibbon(ML.lerp(xB - 34, xm, back), xB - 34, yc, 14 * back + 0.01, an.r.lam + Math.PI, back, null);
        curl(xA + 34 + 26, yc, an.r.A, k, C.s1);
        curl(xB - 34 - 26, yc, an.r.B, k, C.s2);
        if (k >= 1) { resA = an.r.A; resB = an.r.B; }
      }
      if (an.t > 1.9) { st.last = an.r; st.anim = null; }
    } else if (st.last) { resA = st.last.A; resB = st.last.B; curl(xA + 60, yc, st.last.A, 1, C.s1); curl(xB - 60, yc, st.last.B, 1, C.s2); }
    dial(xA, yc, st.a, 'Alice', resA);
    dial(xB, yc, st.b, 'Bob', resB);
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'top';
    g.fillText('far apart: no signal has time to cross', xm, L.y + L.h - 22);
  }

  function drawChart() {
    const g = ctx, R = layout.chart;
    const padL = 44, padR = 10, padT = 34, padB = 30;
    const x0 = R.x + padL, x1 = R.x + R.w - padR, y0 = R.y + padT, y1 = R.y + R.h - padB;
    const X = (th) => x0 + (th / 360) * (x1 - x0), Y = (e) => y0 + ((1 - e) / 2) * (y1 - y0);
    g.fillStyle = C.fg; g.font = '600 13px "IBM Plex Sans", sans-serif'; g.textAlign = 'left'; g.textBaseline = 'top';
    g.fillText('How often the two halves agree', R.x, R.y);
    // legend
    const lg = [[C.s2, 'Halves set at stretching (local)'], [C.s1, 'One ribbon, cut sets both']];
    let lx = R.x; g.font = '500 11px "IBM Plex Sans", sans-serif';
    lg.forEach(([c, t]) => { g.fillStyle = c; g.fillRect(lx, R.y + 20, 14, 2); g.fillStyle = C.fg2; g.textBaseline = 'middle'; g.fillText(t, lx + 20, R.y + 21); lx += 26 + g.measureText(t).width + 14; });
    // grid
    g.strokeStyle = C.hair; g.lineWidth = 1;
    for (const e of [-1, 0, 1]) { g.beginPath(); g.moveTo(x0, Math.round(Y(e)) + 0.5); g.lineTo(x1, Math.round(Y(e)) + 0.5); g.stroke(); }
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'right'; g.textBaseline = 'middle';
    [[1, '+1 same'], [0, '0'], [-1, '−1 opposite']].forEach(([e, t]) => g.fillText(e === 0 ? '0' : e > 0 ? '+1' : '−1', x0 - 6, Y(e)));
    g.textAlign = 'center'; g.textBaseline = 'top';
    for (let th = 0; th <= 360; th += 90) g.fillText(th + '°', X(th), y1 + 6);
    g.fillText('angle between Alice and Bob', (x0 + x1) / 2, y1 + 18 > R.y + R.h - 12 ? R.y + R.h - 12 : y1 + 18);
    // theory curves
    for (const [m, col] of [['local', C.s2], ['ribbon', C.s1]]) {
      g.strokeStyle = ML.rgba(col, 0.55); g.lineWidth = 2; g.lineJoin = 'round';
      g.beginPath();
      for (let th = 0; th <= 360; th += 2) { const y = Y(theory[m](th)); if (th) g.lineTo(X(th), y); else g.moveTo(X(th), y); }
      g.stroke();
    }
    // measured points
    for (const [m, col] of [['local', C.s2], ['ribbon', C.s1]]) {
      for (const p of st.sweep[m]) {
        g.beginPath(); g.arc(X(p.th), Y(p.e), 4, 0, TAU); g.fillStyle = col; g.fill();
        g.lineWidth = 2; g.strokeStyle = C.ink; g.stroke();
      }
    }
    // current setting marker
    const th = ((st.b - st.a) % 360 + 360) % 360;
    g.strokeStyle = ML.rgba(C.tape, 0.6); g.setLineDash([3, 4]); g.lineWidth = 1;
    g.beginPath(); g.moveTo(X(th), y0); g.lineTo(X(th), y1); g.stroke(); g.setLineDash([]);
    R.map = { X, Y, x0, x1, y0, y1 };
    if (hover) {
      g.strokeStyle = C.muted; g.lineWidth = 1; g.beginPath(); g.moveTo(X(hover.th), y0); g.lineTo(X(hover.th), y1); g.stroke();
    }
  }

  function drawMeter() {
    const g = ctx, R = layout.meter;
    g.fillStyle = C.fg; g.font = '600 13px "IBM Plex Sans", sans-serif'; g.textAlign = 'left'; g.textBaseline = 'top';
    g.fillText('Bell test score (CHSH)', R.x, R.y);
    const x0 = R.x + 6, x1 = R.x + R.w - 10, Smax = 3;
    const X = (s) => x0 + (s / Smax) * (x1 - x0);
    const rows = [['local', C.s2, 'Local halves'], ['ribbon', C.s1, 'One ribbon']];
    const yb = R.y + 46;
    // lab result band (real experiments)
    g.fillStyle = ML.rgba(C.rule, 0.14);
    g.fillRect(X(2.4), yb - 6, X(2.83) - X(2.4), rows.length * 34 + 4);
    g.strokeStyle = C.hair; g.lineWidth = 1;
    for (const s of [0, 1, 2, 3]) { g.beginPath(); g.moveTo(Math.round(X(s)) + 0.5, yb - 8); g.lineTo(Math.round(X(s)) + 0.5, yb + rows.length * 34); g.stroke(); }
    // limits
    g.strokeStyle = C.fg2; g.setLineDash([4, 3]); g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(X(2), yb - 10); g.lineTo(X(2), yb + rows.length * 34 + 2); g.stroke();
    g.beginPath(); g.moveTo(X(2 * Math.SQRT2), yb - 10); g.lineTo(X(2 * Math.SQRT2), yb + rows.length * 34 + 2); g.stroke(); g.setLineDash([]);
    rows.forEach(([m, col, lbl], i) => {
      const y = yb + i * 34, v = st.chsh[m];
      g.fillStyle = C.fg2; g.font = '500 11px "IBM Plex Sans", sans-serif'; g.textAlign = 'left'; g.textBaseline = 'bottom';
      g.fillText(lbl, x0, y + 2);
      if (v !== null) {
        g.fillStyle = col;
        const w = Math.max(2, X(v) - x0), h = 12, yy = y + 6, r = 4;
        g.beginPath(); g.moveTo(x0, yy); g.lineTo(x0 + w - r, yy); g.quadraticCurveTo(x0 + w, yy, x0 + w, yy + r); g.lineTo(x0 + w, yy + h - r); g.quadraticCurveTo(x0 + w, yy + h, x0 + w - r, yy + h); g.lineTo(x0, yy + h); g.closePath(); g.fill();
        g.fillStyle = C.fg; g.font = '600 12px "IBM Plex Mono", monospace'; g.textAlign = 'left'; g.textBaseline = 'middle';
        g.fillText(v.toFixed(2), Math.min(x0 + w + 6, x1 - 30), yy + h / 2 - (x0 + w + 6 > x1 - 30 ? 14 : 0));
      }
    });
    const ya = yb + rows.length * 34 + 8;
    g.fillStyle = C.muted; g.font = '500 11px "IBM Plex Mono", monospace'; g.textAlign = 'center'; g.textBaseline = 'top';
    for (const s of [0, 1, 2, 3]) g.fillText(String(s), X(s), ya);
    g.textAlign = 'left'; g.fillStyle = C.fg2; g.font = '500 11px "IBM Plex Sans", sans-serif';
    const notes = ['Dashed lines: 2 = most any local version can score;', '2.83 = the most quantum mechanics allows.', 'Shaded: what real labs measure (2.4–2.8).'];
    notes.forEach((t, i) => g.fillText(t, x0, ya + 20 + i * 15));
  }

  // ------------------------------------------------------------------ panel
  const IDEAS = `
    <p class="quote">"One long Möbius strip that was very carefully stretched, and then when it is observed… it snaps into two separate Möbius strips, one spin up and one spin down."</p>
    <div><h4>What the sim does</h4><ul>
      <li>Each trial stretches a strip between Alice and Bob and cuts it. Each half curls one way or the other (↻ = +1, ↺ = −1). Each detector has an angle, like turning your scissors before you cut.</li>
      <li><b>Halves set at stretching:</b> the strip's twist is fixed when it is made, and each half carries its own instructions. This is the "it was always that way, we just looked" version.</li>
      <li><b>One ribbon:</b> the strip stays one object. Cutting at Alice is a coin flip, and in the same instant Bob's end settles relative to Alice's angle. That is your "they are the exact same object" version.</li>
    </ul></div>
    <div class="hook"><h4>Where this meets real physics</h4><ul>
      <li><b>Bell's theorem</b> (1964) and the <b>CHSH score</b> (1969): any version where the halves carry their own instructions scores at most 2, however clever the instructions. Run the local model and it pins at 2.00.</li>
      <li>Real experiments score above 2: Aspect 1982 (about 2.7), and the loophole-free tests of 2015. That won the 2022 Nobel Prize. So the "set at stretching" version of your idea is ruled out by experiment.</li>
      <li>The <b>one-ribbon</b> version scores 2.83, exactly quantum mechanics' value. Your instinct that the two ends are one object is the part of the idea that survives.</li>
      <li>Watch <b>Bob sees +1</b>: it stays at 50% whatever Alice does, so the ribbon can't send a message. Quantum mechanics has the same no-signalling rule.</li>
      <li>The closest mainstream relative of your picture is <b>ER = EPR</b> (Maldacena &amp; Susskind, 2013): the conjecture that entangled particles are joined by a microscopic wormhole, one continuous piece of spacetime.</li>
    </ul></div>`;

  const mode = {
    id: 'entangle', tab: 'Stretched Strip', kind: '2d',
    buildPanel(el) {
      const U = ML.ui;
      U.head(el, 'Stretched strip', 'Your entanglement idea: one strip stretched between two places and cut at one end. Here it runs as a real Bell test, in two versions.');
      const b1 = U.block(el, 'Which version of the strip');
      modelSeg = U.seg(b1, { id: 'e-model', label: '', options: [['local', 'Halves set at stretching'], ['ribbon', 'One ribbon']], value: st.model, onChange: (v) => { st.model = v; st.last = null; } });
      const b2 = U.block(el, 'Detector angles');
      sa = U.slider(b2, { id: 'e-a', label: 'Alice turns her scissors to', min: 0, max: 355, step: 5, value: st.a, fmt: (v) => v + '°', onInput: (v) => (st.a = v) });
      sb = U.slider(b2, { id: 'e-b', label: 'Bob turns his scissors to', min: 0, max: 355, step: 5, value: st.b, fmt: (v) => v + '°', onInput: (v) => (st.b = v) });
      const b3 = U.block(el, 'Run');
      const t = U.toggle(b3, { id: 'e-auto', label: 'Keep cutting (one trial at a time)', value: st.auto, onChange: (v) => (st.auto = v) });
      U.buttons(b3, [
        { label: 'Run 4,000 trials', primary: true, id: 'e-many', onClick: () => { runMany(st.model, st.a, st.b, 4000); refresh(); } },
        { label: 'Re-run Bell test', id: 'e-chsh', onClick: () => { chsh(); sweep(); refresh(); } },
        { label: 'Clear tallies', id: 'e-clear', onClick: () => { st.tallies = {}; refresh(); } },
      ]);
      b3.append(ML.el('p', { class: 'tip', text: 'Bell test angles: Alice 0° or 90°, Bob 45° or 135°.' }));
      const b4 = U.block(el, 'At these angles');
      ro = U.readouts(b4, [['n', 'Trials'], ['agree', 'Halves agree'], ['E', 'Correlation measured'], ['Et', 'Correlation predicted'], ['bob', 'Bob sees +1'], ['sl', 'Bell score, local halves'], ['sr', 'Bell score, one ribbon']]);
      U.ideas(el, IDEAS);
    },
    buildHud() {},
    init(app) {
      cv = app.c2d;
      sweep(); chsh();
      runMany(st.model, st.a, st.b, 600);
      cv.addEventListener('pointermove', (e) => {
        if (ML.app.current !== mode || !layout || !layout.chart.map) return;
        const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top, m = layout.chart.map;
        if (x < m.x0 - 6 || x > m.x1 + 6 || y < m.y0 - 10 || y > m.y1 + 10) { hover = null; ML.tooltip(null); return; }
        const th = ML.clamp(Math.round((((x - m.x0) / (m.x1 - m.x0)) * 360) / 15) * 15, 0, 360);
        hover = { th };
        const pl = st.sweep.local.find((p) => p.th === th), pr = st.sweep.ribbon.find((p) => p.th === th);
        ML.tooltip('angle ' + th + '°<br>local halves: ' + (pl ? pl.e.toFixed(2) : '—') + ' (theory ' + theory.local(th).toFixed(2) + ')<br>one ribbon: ' + (pr ? pr.e.toFixed(2) : '—') + ' (theory ' + theory.ribbon(th).toFixed(2) + ')', e.clientX, e.clientY);
      });
      cv.addEventListener('pointerleave', () => { hover = null; ML.tooltip(null); });
    },
    enter() { st.timer = 0.3; },
    exit() { ML.tooltip(null); hover = null; },
    resize(w, h) { W = w; H = h; ctx = ML.fitCanvas(cv, w, h); computeLayout(); },
    frame(dt) {
      if (!ctx) return;
      if (st.auto && !st.anim) { st.timer -= dt; if (st.timer <= 0) { const r = trial(st.model, st.a, st.b); tally(st.model, st.a, st.b, r); st.anim = { t: 0, r }; st.timer = 0.35; } }
      ctx.fillStyle = C.ink; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#12151e'; ctx.fillRect(layout.scene.x, layout.scene.y, layout.scene.w, layout.scene.h);
      drawScene(dt); drawChart(); drawMeter();
      refresh(dt);
    },
    _st: st, _trial: trial, _E: E,
  };
  let rt = 0;
  function refresh(dt) {
    rt -= dt || 1; if (rt > 0) return; rt = 0.2;
    if (!ro) return;
    const t = st.tallies[st.model + '|' + st.a + '|' + st.b];
    const th = st.b - st.a;
    ro.set('n', t ? ML.fmt(t.n) : '0');
    ro.set('agree', t ? ML.pct((t.n + t.ab) / 2 / t.n) : '—');
    ro.set('E', t ? (t.ab / t.n).toFixed(3) : '—');
    ro.set('Et', theory[st.model](th).toFixed(3));
    ro.set('bob', t ? ML.pct(t.bp / t.n, 1) : '—');
    ro.set('sl', st.chsh.local !== null ? st.chsh.local.toFixed(3) + ' (limit 2)' : '—');
    ro.set('sr', st.chsh.ribbon !== null ? st.chsh.ribbon.toFixed(3) + ' (QM: 2.828)' : '—');
  }
  ML.register(mode);
})();
