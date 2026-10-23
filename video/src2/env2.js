// ---------- mythic world: highlands, citadel, crowds, dragons, forge ----------
function ridge(c, y0, amp, col, seed, x0 = -200, x1 = W + 200) {
  c.fillStyle = col; c.beginPath(); c.moveTo(x0, H + 200);
  for (let x = x0; x <= x1; x += 12) c.lineTo(x, y0 - Math.abs(fbm(x * .004, seed)) * amp - fbm(x * .02, seed + 3) * amp * .12);
  c.lineTo(x1, H + 200); c.closePath(); c.fill();
}
function highlandBG(mode = 'dawn') {
  return cached('hl_' + mode, W + 400, H + 400, (c) => {
    c.translate(200, 200);
    const P = {
      dawn: ['#1b2440', '#5a4a6e', '#e5895a', '#ffd08a', ['#4a4a6e', '#3a3858', '#2a2840'], '#2e2430'],
      storm: ['#14161e', '#2e3440', '#5a5a66', '#8a8a90', ['#2e3440', '#232832', '#1a1d24'], '#1e1c20'],
      gold: ['#2a2a4a', '#6a5a7a', '#f0a060', '#ffe0a0', ['#5a4a6a', '#443a58', '#302840'], '#3a2c34'],
    }[mode];
    const g = c.createLinearGradient(0, -200, 0, 760); g.addColorStop(0, P[0]); g.addColorStop(.45, P[1]); g.addColorStop(.85, P[2]); g.addColorStop(1, P[3]);
    c.fillStyle = g; c.fillRect(-200, -200, W + 400, H + 400);
    glow(c, 470, 700, 420, P[3], mode === 'storm' ? .15 : .55);
    ridge(c, 690, 260, P[4][0], 11); ridge(c, 760, 200, P[4][1], 23); ridge(c, 860, 140, P[4][2], 37);
    // static mist bands
    for (let i = 0; i < 5; i++) { const y = 700 + i * 55; const mg = c.createLinearGradient(0, y - 40, 0, y + 40); mg.addColorStop(0, 'rgba(230,220,230,0)'); mg.addColorStop(.5, `rgba(230,220,235,${mode === 'storm' ? .08 : .14})`); mg.addColorStop(1, 'rgba(230,220,230,0)'); c.fillStyle = mg; c.fillRect(-200, y - 40, W + 400, 80); }
    // heather foreground
    const fg = c.createLinearGradient(0, 940, 0, H); fg.addColorStop(0, P[5]); fg.addColorStop(1, '#120e10'); c.fillStyle = fg;
    c.beginPath(); c.moveTo(-200, H + 200); for (let x = -200; x <= W + 200; x += 10) c.lineTo(x, 960 + fbm(x * .006, 51) * 40); c.lineTo(W + 200, H + 200); c.fill();
    const r = rng(9); for (let i = 0; i < 900; i++) { const x = -200 + r() * (W + 400), y = 960 + r() * 520; c.fillStyle = r() < .5 ? 'rgba(120,70,110,.35)' : 'rgba(70,80,50,.35)'; c.fillRect(x, y, 2, 4 + r() * 6); }
  });
}
function clouds(ctx, t, a = .25, y0 = 160) {
  for (let i = 0; i < 6; i++) { const x = ((i * 190 + t * (6 + i * 2)) % 1100) - 200, y = y0 + (i % 3) * 70; ctx.fillStyle = `rgba(255,230,220,${a * (.6 + .4 * (i % 2))})`; ctx.beginPath(); ctx.ellipse(x, y, 160, 26, 0, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.ellipse(x + 60, y - 14, 90, 22, 0, 0, TAU); ctx.fill(); }
}
function windGrass(ctx, t, y0 = 1100, n = 40) {
  ctx.save(); ctx.strokeStyle = 'rgba(90,70,60,.6)'; ctx.lineWidth = 2; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) { const x = hash(i) * W, y = y0 + hash(i + 9) * 180, h = 20 + hash(i + 3) * 30, b = Math.sin(t * 2 + i) * 8 + 10; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + b * .4, y - h * .6, x + b, y - h); ctx.stroke(); }
  ctx.restore();
}
function hud(ctx, lines, t, t0, y = 210, col = '#7dffb0', tEnd = 1e9) {
  const lt = t - t0; if (lt < 0) return;
  const fa = 1 - ramp(t, tEnd, tEnd + .6); if (fa <= 0) return;
  ctx.save(); ctx.globalAlpha = fa; ctx.font = '700 30px "DejaVu Sans Mono"'; ctx.textAlign = 'center';
  lines.forEach((ln, i) => {
    const start = i * .55, n = Math.floor(clamp((lt - start) / .5) * ln.length); if (n <= 0) return;
    const jit = lt - start < .5 ? (hash(Math.floor(t * 30) + i) - .5) * 6 : 0;
    const big = i > 0, fs = big ? 52 : 26;
    ctx.font = `700 ${fs}px "DejaVu Sans Mono"`;
    const yy = y + i * (big ? 66 : 0) + (i > 1 ? (i - 1) * 6 : 0);
    ctx.shadowColor = col; ctx.shadowBlur = 16; ctx.fillStyle = big ? '#fff3d0' : col;
    if (big) { ctx.shadowColor = '#ff8a3a'; }
    ctx.fillText(ln.slice(0, n), W / 2 + jit, yy);
  });
  ctx.restore();
}
function flag(ctx, x, y, w, h, t, col, emblem = true, amt = 1) {
  ctx.save();
  ctx.strokeStyle = '#3a2a1c'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(x, y - 20); ctx.lineTo(x, y + h * 2.6); ctx.stroke();
  const pts = [], n = 16;
  for (let i = 0; i <= n; i++) { const u = i / n; pts.push([x + u * w, y + Math.sin(u * 5 - t * 6) * 12 * u * amt + u * (1 - amt) * h * .7]); }
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(x, y);
  pts.forEach(p => ctx.lineTo(p[0], p[1])); for (let i = n; i >= 0; i--) ctx.lineTo(pts[i][0], pts[i][1] + h * (1 - (1 - amt) * .3 * (i / n)));
  ctx.closePath(); ctx.fill();
  // folds shading
  for (let i = 1; i < n; i += 2) { const s = Math.sin(i / n * 5 - t * 6); ctx.fillStyle = s > 0 ? 'rgba(255,255,255,.08)' : 'rgba(0,0,0,.15)'; ctx.fillRect(pts[i][0], pts[i][1], w / n, h); }
  if (emblem) { const m = pts[n / 2]; flameHeart(ctx, m[0], m[1] + h / 2, h * .32, t); }
  ctx.restore();
}
function flameHeart(ctx, x, y, s, t, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.globalAlpha *= a;
  ctx.fillStyle = '#ffcf6a'; ctx.beginPath(); ctx.moveTo(0, s * .9); ctx.bezierCurveTo(-s * 1.4, -s * .1, -s * .7, -s * 1.1, 0, -s * .45); ctx.bezierCurveTo(s * .7, -s * 1.1, s * 1.4, -s * .1, 0, s * .9); ctx.fill();
  ctx.fillStyle = '#ff7a2a'; const f = Math.sin(t * 8) * .08;
  ctx.beginPath(); ctx.moveTo(-s * .3, s * .1); ctx.quadraticCurveTo(-s * .4, -s * .5, s * f, -s * 1.1); ctx.quadraticCurveTo(s * .4, -s * .5, s * .3, s * .1); ctx.quadraticCurveTo(0, s * .4, -s * .3, s * .1); ctx.fill();
  ctx.restore();
}
// ---- the gilded citadel ----
function citadel(ctx, x, y, s, t, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const gold = (y0, y1) => { const g = ctx.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, '#f4d98a'); g.addColorStop(.5, '#c9a24a'); g.addColorStop(1, '#7a5a20'); return g; };
  // towers
  for (const [tx, th, tw] of [[-260, 520, 110], [260, 520, 110], [-120, 600, 90], [120, 600, 90], [0, 700, 120]]) {
    ctx.fillStyle = gold(-th, 0); ctx.fillRect(tx - tw / 2, -th, tw, th);
    for (let k = 0; k < 4; k++) ctx.fillRect(tx - tw / 2 + k * tw / 3.5, -th - 22, tw / 6, 22);
    ctx.fillStyle = 'rgba(0,0,0,.15)'; ctx.fillRect(tx + tw / 4, -th, tw / 4, th);
    // windows: glowing screens ("digital doors")
    for (let k = 0; k < 3; k++) { const wy = -th + 80 + k * 110; ctx.fillStyle = o.screens ? mix('#2a2030', '#8fd0ff', o.screens * (.6 + .4 * Math.sin(t * 3 + k + tx))) : '#2a2030'; roundRect(ctx, tx - 16, wy, 32, 50, 14); ctx.fill(); }
  }
  // wall
  ctx.fillStyle = gold(-360, 0); ctx.fillRect(-320, -360, 640, 360);
  for (let k = 0; k < 14; k++) ctx.fillRect(-320 + k * 47, -384, 26, 24);
  ctx.strokeStyle = 'rgba(90,60,20,.35)'; ctx.lineWidth = 2; for (let r = 0; r < 9; r++) { ctx.beginPath(); ctx.moveTo(-320, -360 + r * 40); ctx.lineTo(320, -360 + r * 40); ctx.stroke(); }
  // gears in the wall (the machine)
  if (o.gears) for (const [gx, gy, gr, dir] of [[-200, -220, 60, 1], [-118, -250, 38, -1], [200, -220, 60, -1]]) gear(ctx, gx, gy, gr, t * dir * .8, o.gears);
  // the great door
  const dw = 200, dh = 280;
  ctx.fillStyle = '#5a3a14'; ctx.beginPath(); ctx.moveTo(-dw / 2 - 16, 0); ctx.lineTo(-dw / 2 - 16, -dh); ctx.arc(0, -dh, dw / 2 + 16, Math.PI, 0); ctx.lineTo(dw / 2 + 16, 0); ctx.fill();
  const dg = ctx.createLinearGradient(-dw / 2, 0, dw / 2, 0); dg.addColorStop(0, '#e8c46a'); dg.addColorStop(.5, '#fff0b0'); dg.addColorStop(1, '#b08a3a');
  const shake = o.shake || 0;
  ctx.save(); ctx.translate((hash(Math.floor(t * 40)) - .5) * shake * 6, 0);
  ctx.fillStyle = dg; ctx.beginPath(); ctx.moveTo(-dw / 2, 0); ctx.lineTo(-dw / 2, -dh); ctx.arc(0, -dh, dw / 2, Math.PI, 0); ctx.lineTo(dw / 2, 0); ctx.fill();
  ctx.fillStyle = 'rgba(90,60,20,.5)'; ctx.fillRect(-2, -dh - dw / 2, 4, dh + dw / 2);
  for (const sy of [-dh + 30, -60]) for (const sx of [-1, 1]) { ctx.fillStyle = '#3a2810'; ctx.fillRect(sx < 0 ? -dw / 2 - 18 : dw / 2 - 52, sy, 70, 18); ctx.fillStyle = '#7a6040'; ctx.beginPath(); ctx.arc(sx * (dw / 2 + 6), sy + 9, 9, 0, TAU); ctx.fill(); }
  // cracks with light leaking
  if (o.crack > 0) {
    ctx.strokeStyle = `rgba(255,255,230,${clamp(o.crack * 1.5)})`; ctx.lineWidth = 6; ctx.shadowColor = '#fff6c0'; ctx.shadowBlur = 20;
    const r = rng(4);
    for (const [cx, cy] of [[-dw / 2, -dh + 39], [dw / 2, -dh + 39], [-dw / 2, -51], [dw / 2, -51], [0, -dh * .5]]) {
      ctx.beginPath(); ctx.moveTo(cx, cy); let px = cx, py = cy; const n = Math.ceil(o.crack * 6);
      for (let k = 0; k < n; k++) { px += (r() - .5) * 40 - Math.sign(cx || 1) * 8; py += (r() - .3) * 30; ctx.lineTo(px, py); } ctx.stroke();
    }
    ctx.shadowBlur = 0;
    if (o.crack > .6) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; glow(ctx, 0, -dh * .5, 260 * o.crack, '#fff0b0', .35 * (o.crack - .5)); ctx.restore(); }
  }
  ctx.restore();
  ctx.restore();
}
function gear(ctx, x, y, r, a, alphaV = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(a); ctx.globalAlpha *= alphaV;
  ctx.fillStyle = '#8a6a2a'; ctx.beginPath();
  for (let k = 0; k < 24; k++) { const ang = k / 24 * TAU, rr = k % 2 ? r : r * 1.18; ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr); }
  ctx.closePath(); ctx.fill(); ctx.fillStyle = '#5a4018'; ctx.beginPath(); ctx.arc(0, 0, r * .35, 0, TAU); ctx.fill();
  ctx.restore();
}
// ---- dragons ----
function dragon(ctx, x, y, s, t, dir = 1, col = '#7a2a1a', fireOn = 0, seed = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * dir, s);
  const fl = Math.sin(t * 5 + seed);
  const belly = shade(col, .25), dark = shade(col, -.45);
  // far wing
  wing(ctx, -10, -10, fl, shade(col, -.3), -1);
  // tail
  ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineWidth = 22;
  ctx.beginPath(); ctx.moveTo(-60, 0); ctx.bezierCurveTo(-140, 20 + fl * 10, -190, -30 - fl * 14, -260, -10 + fl * 18); ctx.stroke();
  ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(-250, -8 + fl * 18); ctx.lineTo(-300, -6 + fl * 22); ctx.stroke();
  ctx.fillStyle = dark; ctx.beginPath(); ctx.moveTo(-300, -6 + fl * 22); ctx.lineTo(-330, -24 + fl * 22); ctx.lineTo(-322, 12 + fl * 22); ctx.fill();
  // body
  const bg = ctx.createLinearGradient(0, -40, 0, 40); bg.addColorStop(0, col); bg.addColorStop(1, belly);
  ctx.fillStyle = bg; ctx.beginPath(); ctx.ellipse(0, 0, 90, 38, -.08, 0, TAU); ctx.fill();
  // neck + head
  ctx.strokeStyle = col; ctx.lineWidth = 30; ctx.beginPath(); ctx.moveTo(60, -10); ctx.quadraticCurveTo(110, -60 - fl * 6, 150, -64 - fl * 6); ctx.stroke();
  ctx.save(); ctx.translate(160, -66 - fl * 6); ctx.rotate(.15);
  ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(-20, -18); ctx.lineTo(40, -10); ctx.lineTo(62, 4); ctx.lineTo(40, 12); ctx.lineTo(-16, 18); ctx.closePath(); ctx.fill();
  ctx.fillStyle = dark; ctx.beginPath(); ctx.moveTo(-10, -16); ctx.lineTo(-40, -40); ctx.lineTo(4, -18); ctx.fill(); ctx.beginPath(); ctx.moveTo(4, -14); ctx.lineTo(-18, -44); ctx.lineTo(18, -14); ctx.fill();
  ctx.fillStyle = '#ffd34a'; ctx.beginPath(); ctx.ellipse(16, -5, 6, 3.5, .2, 0, TAU); ctx.fill(); glow(ctx, 16, -5, 18, '#ffb020', .6);
  ctx.restore();
  // legs tucked
  ctx.strokeStyle = dark; ctx.lineWidth = 12; for (const lx of [-40, 40]) { ctx.beginPath(); ctx.moveTo(lx, 20); ctx.lineTo(lx - 10, 46); ctx.lineTo(lx + 6, 56); ctx.stroke(); }
  // spines
  ctx.fillStyle = dark; for (let k = 0; k < 6; k++) { const sx = -70 + k * 26; ctx.beginPath(); ctx.moveTo(sx, -32); ctx.lineTo(sx + 8, -50); ctx.lineTo(sx + 16, -32); ctx.fill(); }
  // near wing
  wing(ctx, 0, -20, fl, col, 1);
  if (fireOn > 0) { ctx.save(); ctx.translate(220, -56); for (let k = 0; k < 18; k++) { const p = ((t * 2.2 + k / 18) % 1), d = p * 300 * fireOn; ctx.fillStyle = `rgba(255,${200 - p * 150},${60 - p * 60},${(1 - p) * .8})`; ctx.beginPath(); ctx.arc(d, Math.sin(k * 3.1 + t * 9) * p * 40, 8 + p * 30, 0, TAU); ctx.fill(); } ctx.restore(); }
  ctx.restore();
}
function wing(ctx, x, y, fl, col, side) {
  const up = fl * 1.0;
  ctx.save(); ctx.translate(x, y);
  const tip = [60 - side * 10, -190 * (0.3 + 0.7 * (up * .5 + .5)) + 60 * (1 - (up * .5 + .5))];
  ctx.fillStyle = alpha(col.startsWith('#') ? col : '#7a2a1a', .95);
  ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(tip[0] - 120, tip[1] * .7); ctx.lineTo(tip[0], tip[1]);
  ctx.quadraticCurveTo(tip[0] + 20, tip[1] * .4, 80, 10); ctx.quadraticCurveTo(40, -10, 20, 10); ctx.quadraticCurveTo(-10, -6, -40, 0); ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 3;
  for (const k of [.2, .5, .8]) { ctx.beginPath(); ctx.moveTo(tip[0] * .2, tip[1] * .2); ctx.lineTo(lerp(-40, 80, k), 4); ctx.stroke(); }
  ctx.restore();
}
// ---- forge ----
function anvil(ctx, x, y, s) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const g = ctx.createLinearGradient(0, -60, 0, 80); g.addColorStop(0, '#5a5a62'); g.addColorStop(1, '#1a1a1e');
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-150, -60); ctx.lineTo(120, -60); ctx.quadraticCurveTo(200, -55, 220, -40); ctx.quadraticCurveTo(160, -30, 110, -20); ctx.lineTo(70, 10); ctx.lineTo(100, 80); ctx.lineTo(-100, 80); ctx.lineTo(-70, 10); ctx.lineTo(-150, -25); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(-150, -60, 300, 5);
  ctx.restore();
}
function sparks(ctx, x, y, t, t0, n = 30, spread = 1) {
  const lt = t - t0; if (lt < 0 || lt > 1.2) return;
  for (let k = 0; k < n; k++) { const a = -Math.PI / 2 + (hash(k + t0 * 7) - .5) * 2.6 * spread, v = 200 + hash(k + 3 + t0) * 380; const px = x + Math.cos(a) * v * lt, py = y + Math.sin(a) * v * lt + 500 * lt * lt; ctx.fillStyle = `rgba(255,${200 - lt * 120},80,${1 - lt / 1.2})`; ctx.fillRect(px, py, 3, 3); }
}
function glowKey(ctx, x, y, s, ang, heat = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.scale(s, s);
  const col = mix('#8a8a90', '#ffb040', heat);
  if (heat > .2) glow(ctx, 0, 0, 120, '#ff9a30', .4 * heat);
  ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 12;
  ctx.beginPath(); ctx.arc(-80, 0, 30, 0, TAU); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-50, 0); ctx.lineTo(90, 0); ctx.stroke();
  ctx.fillRect(56, 0, 12, 30); ctx.fillRect(76, 0, 12, 40);
  ctx.restore();
}
function prisonDoor(ctx, x, y, w, h, open, t) {
  ctx.save();
  ctx.fillStyle = '#0a0808'; ctx.fillRect(x, y, w, h);
  if (open > 0) { const g = ctx.createRadialGradient(x + w / 2, y + h / 2, 5, x + w / 2, y + h / 2, w); g.addColorStop(0, `rgba(255,170,80,${.7 * open})`); g.addColorStop(1, 'rgba(255,120,40,0)'); ctx.fillStyle = g; ctx.fillRect(x, y, w, h); }
  const vw = w * Math.cos(open * 1.3);
  ctx.strokeStyle = '#4a4a50'; ctx.lineWidth = 8;
  for (let k = 0; k <= 4; k++) { const px = x + vw * k / 4; ctx.beginPath(); ctx.moveTo(px, y); ctx.lineTo(px, y + h); ctx.stroke(); }
  ctx.lineWidth = 10; for (const yy of [y + 8, y + h / 2, y + h - 8]) { ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x + vw, yy); ctx.stroke(); }
  // padlock
  const ly = y + h / 2 + 12 + open * 60;
  ctx.save(); ctx.translate(x + vw - 6, ly); ctx.rotate(open * 1.2); ctx.globalAlpha = 1 - clamp(open * 1.5 - .5);
  ctx.strokeStyle = '#8a7a50'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(0, -14 - open * 8, 11, Math.PI, 0); ctx.stroke();
  ctx.fillStyle = '#b09a5a'; roundRect(ctx, -16, -14, 32, 28, 5); ctx.fill(); ctx.fillStyle = '#222'; ctx.fillRect(-2, -6, 4, 10);
  ctx.restore();
  ctx.strokeStyle = '#2a2a2e'; ctx.lineWidth = 14; ctx.strokeRect(x - 7, y - 7, w + 14, h + 14);
  ctx.restore();
}
function shards(ctx, x, y, t, t0, dur = 1.4) { // a dark shell cracking off and flying outward
  const lt = (t - t0) / dur;
  for (let k = 0; k < 26; k++) {
    const a = k / 26 * TAU + hash(k) * .3, r0 = 150 + hash(k + 4) * 80;
    const p = clamp(lt), d = easeOut(p) * (300 + hash(k + 9) * 300);
    const px = x + Math.cos(a) * (r0 * .7 + d), py = y + Math.sin(a) * (r0 + d) * 1.3 + 200 * p * p;
    ctx.save(); ctx.translate(px, py); ctx.rotate(a + p * 4 * (hash(k) - .5)); ctx.globalAlpha = 1 - clamp((lt - .6) / .4);
    ctx.fillStyle = mix('#2a2430', '#4a3a40', hash(k + 2)); ctx.beginPath(); ctx.moveTo(-30, -20); ctx.lineTo(34, -12); ctx.lineTo(20, 26); ctx.lineTo(-26, 18); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = `rgba(255,150,60,${.8 * (1 - p)})`; ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
  }
}
function fireWings(ctx, x, y, t, a, span = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (const side of [-1, 1]) for (let k = 0; k < 90; k++) {
    const u = (k % 30) / 30, row = Math.floor(k / 30);            // three feather rows sweeping outward
    const ang = -.55 + u * .75 + row * .22, r = (110 + u * 330 * span) * (1 - row * .12) * (0.94 + .06 * Math.sin(t * 6 + k));
    const px = x + side * Math.cos(ang) * r, py = y + Math.sin(ang) * r * .8 - (1 - u) * 60 + row * 50 * u + Math.sin(t * 4 + k * .5) * 6;
    const sz = 30 - u * 12;
    const g = ctx.createRadialGradient(px, py, 0, px, py, sz); g.addColorStop(0, `rgba(255,${210 - row * 40},90,${.32 * a})`); g.addColorStop(1, 'rgba(255,80,20,0)');
    ctx.fillStyle = g; ctx.fillRect(px - sz, py - sz, sz * 2, sz * 2);
  }
  ctx.restore();
}
function embers(ctx, t, n = 40, a = .8, y0 = H) {
  for (let i = 0; i < n; i++) { const p = (t * .12 + hash(i)) % 1, x = hash(i + 7) * W + Math.sin(p * 9 + i) * 30, y = y0 - p * (y0 + 100); ctx.fillStyle = `rgba(255,${130 + hash(i) * 100},50,${(1 - p) * a})`; ctx.fillRect(x, y, 2.5, 2.5); }
}
