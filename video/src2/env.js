// ---------- environments & props ----------
function mkCanvas(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const CACHE = {};
function cached(key, w, h, fn) { if (!CACHE[key]) { const c = mkCanvas(w, h); fn(c.getContext('2d'), w, h); CACHE[key] = c; } return CACHE[key]; }
function grit(ctx, x, y, w, h, base, amt, seed, n = 1400) {
  const r = rng(seed);
  for (let i = 0; i < n; i++) { const px = x + r() * w, py = y + r() * h, s = 1 + r() * 3; ctx.fillStyle = r() < .5 ? shade(base, -.3 * amt * (.5 + r()), .5) : shade(base, .25 * amt * (.5 + r()), .4); ctx.fillRect(px, py, s, s); }
}
function stains(ctx, x, y, w, h, col, seed, n = 6) {
  const r = rng(seed);
  for (let i = 0; i < n; i++) { const cx = x + r() * w, cy = y + r() * h, rad = 40 + r() * 120; const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, rad); g.addColorStop(0, alpha(col, .18 + r() * .12)); g.addColorStop(1, alpha(col, 0)); ctx.fillStyle = g; ctx.fillRect(cx - rad, cy - rad, rad * 2, rad * 2); }
}
function bricks(ctx, x, y, w, h, base, seed, bw = 90, bh = 40, mortar = '#3a3026') {
  ctx.fillStyle = mortar; ctx.fillRect(x, y, w, h);
  const r = rng(seed);
  for (let row = 0; row * bh < h; row++) {
    const off = (row % 2) * bw / 2;
    for (let bx = -bw; bx < w + bw; bx += bw) {
      const px = x + bx + off + 2, py = y + row * bh + 2, f = (r() - .5) * .22;
      const g = ctx.createLinearGradient(px, py, px, py + bh);
      g.addColorStop(0, shade(base, f + .08)); g.addColorStop(1, shade(base, f - .12));
      ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(px + 3, py); ctx.lineTo(px + bw - 6, py + r() * 2); ctx.lineTo(px + bw - 4, py + bh - 5); ctx.lineTo(px + 2, py + bh - 4 - r() * 2); ctx.closePath(); ctx.fill();
      if (r() < .3) { ctx.fillStyle = shade(base, -.3, .4); ctx.beginPath(); ctx.arc(px + r() * bw, py + r() * bh, 2 + r() * 5, 0, TAU); ctx.fill(); }
    }
  }
  grit(ctx, x, y, w, h, base, 1, seed + 1, Math.floor(w * h / 120));
}
function vignette(ctx, a = .5, col = '#000') {
  const g = ctx.createRadialGradient(W / 2, H * .45, H * .25, W / 2, H * .5, H * .78);
  g.addColorStop(0, alpha(col, 0)); g.addColorStop(1, alpha(col, a)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function glow(ctx, x, y, r, col, a) { const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, alpha(col, a)); g.addColorStop(1, alpha(col, 0)); ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); }
function flame(ctx, x, y, s, t, seed = 0) {
  const fl = 1 + noise1(t * 9 + seed) * .12, sw = noise1(t * 6 + seed * 3) * 3 * s;
  glow(ctx, x, y - 10 * s, 90 * s * fl, '#ffb347', .35);
  ctx.save(); ctx.translate(x, y);
  const g = ctx.createRadialGradient(0, -6 * s, 1, 0, -8 * s, 18 * s); g.addColorStop(0, '#fffbe0'); g.addColorStop(.4, '#ffd36b'); g.addColorStop(1, 'rgba(255,120,30,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(-6 * s, 0); ctx.quadraticCurveTo(-7 * s, -12 * s, sw, -26 * s * fl); ctx.quadraticCurveTo(7 * s, -12 * s, 6 * s, 0); ctx.quadraticCurveTo(0, 4 * s, -6 * s, 0); ctx.fill();
  ctx.restore();
}
function oilLamp(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y);
  const g = ctx.createLinearGradient(0, -10 * s, 0, 14 * s); g.addColorStop(0, '#b0703e'); g.addColorStop(1, '#5d3418');
  ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, 0, 30 * s, 12 * s, 0, 0, TAU); ctx.fill();
  ctx.beginPath(); ctx.moveTo(18 * s, -6 * s); ctx.lineTo(40 * s, -9 * s); ctx.lineTo(40 * s, -2 * s); ctx.lineTo(18 * s, 6 * s); ctx.fill();
  ctx.fillStyle = '#3a2010'; ctx.beginPath(); ctx.ellipse(-2 * s, -4 * s, 8 * s, 3 * s, 0, 0, TAU); ctx.fill();
  ctx.restore();
  flame(ctx, x + 38 * s, y - 8 * s, s, t);
}
function door(ctx, x, y, w, h, open, col, frameCol) { // hinge on the left edge; open 0..1 swings toward camera
  ctx.save();
  ctx.fillStyle = '#0d0a08'; ctx.fillRect(x, y, w, h);
  const ang = open * 1.35, vw = w * Math.cos(ang), bulge = Math.sin(ang) * w * .12;
  const g = ctx.createLinearGradient(x, 0, x + vw, 0); g.addColorStop(0, shade(col, -.1)); g.addColorStop(1, shade(col, -.35 - open * .2));
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + vw, y - bulge); ctx.lineTo(x + vw, y + h + bulge); ctx.lineTo(x, y + h); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = shade(col, -.5, .7); ctx.lineWidth = 3;
  for (let i = 1; i < 4; i++) { const px = x + vw * i / 4; ctx.beginPath(); ctx.moveTo(px, y - bulge * i / 4 + 4); ctx.lineTo(px, y + h + bulge * i / 4 - 4); ctx.stroke(); }
  ctx.fillStyle = '#2b2b2b'; for (const yy of [.2, .8]) ctx.fillRect(x, y + h * yy - 5, Math.min(vw, 50), 10);
  ctx.fillStyle = '#c9a24a'; ctx.beginPath(); ctx.arc(x + vw * .85, y + h * .52, 6, 0, TAU); ctx.fill();
  ctx.strokeStyle = frameCol; ctx.lineWidth = 16; ctx.strokeRect(x - 8, y - 8, w + 16, h + 16);
  ctx.restore();
}
function scroll(ctx, x, y, w, h, ang = 0, open = 1, ink = .7, col = '#e9dcb8') {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  const ww = w * open;
  ctx.fillStyle = col; ctx.fillRect(-ww / 2, -h / 2, ww, h);
  const g = ctx.createLinearGradient(-ww / 2, 0, ww / 2, 0); g.addColorStop(0, 'rgba(120,90,50,.25)'); g.addColorStop(.15, 'rgba(0,0,0,0)'); g.addColorStop(.85, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(120,90,50,.25)');
  ctx.fillStyle = g; ctx.fillRect(-ww / 2, -h / 2, ww, h);
  ctx.strokeStyle = 'rgba(60,40,25,.55)'; ctx.lineWidth = 1.5;
  const r = rng(5); const lines = Math.floor((h - 16) / 9 * ink);
  for (let i = 0; i < lines; i++) { const yy = -h / 2 + 10 + i * 9; let xx = -ww / 2 + 8; while (xx < ww / 2 - 12) { const l = 6 + r() * 16; ctx.beginPath(); ctx.moveTo(xx, yy); ctx.lineTo(Math.min(xx + l, ww / 2 - 8), yy); ctx.stroke(); xx += l + 4; } }
  for (const s of [-1, 1]) { ctx.fillStyle = '#c4ad7c'; ctx.beginPath(); ctx.ellipse(s * ww / 2, 0, 6, h / 2 + 4, 0, 0, TAU); ctx.fill(); ctx.fillStyle = '#6b4a2a'; ctx.fillRect(s * ww / 2 - 3, -h / 2 - 10, 6, 6); ctx.fillRect(s * ww / 2 - 3, h / 2 + 4, 6, 6); }
  ctx.restore();
}
function rolledLetter(ctx, x, y, len, ang, col = '#e9dcb8') {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  const g = ctx.createLinearGradient(0, -9, 0, 9); g.addColorStop(0, shade(col, .1)); g.addColorStop(.5, col); g.addColorStop(1, shade(col, -.3));
  ctx.fillStyle = g; roundRect(ctx, -len / 2, -9, len, 18, 8); ctx.fill();
  ctx.fillStyle = '#9b2a22'; ctx.fillRect(-4, -9, 8, 18); ctx.beginPath(); ctx.arc(0, 9, 6, 0, TAU); ctx.fill();
  ctx.restore();
}
function chainPath(ctx, pts, t, shine = 0) {
  // draw chain links along a polyline
  ctx.save(); ctx.lineWidth = 3.2;
  let acc = 0;
  for (let i = 0; i < pts.length - 1; i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[i + 1], d = Math.hypot(x2 - x1, y2 - y1), a = Math.atan2(y2 - y1, x2 - x1);
    for (let s = 0; s < d; s += 11) {
      const x = x1 + Math.cos(a) * s, y = y1 + Math.sin(a) * s, k = (acc++) % 2;
      ctx.strokeStyle = k ? '#6d6a66' : '#8f8b85'; if (shine) ctx.strokeStyle = mix(k ? '#6d6a66' : '#8f8b85', '#fff4d0', shine * (.5 + .5 * Math.sin(acc * .8 - t * 12)));
      ctx.beginPath(); ctx.ellipse(x, y, 7, k ? 2.2 : 4, a, 0, TAU); ctx.stroke();
    }
  }
  ctx.restore();
}
function sampleCurve(p0, p1, p2, n = 20) { const out = []; for (let i = 0; i <= n; i++) { const u = i / n; out.push([(1 - u) * (1 - u) * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) * (1 - u) * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]]); } return out; }

// ----- apartment -----
function aptBG(mode) {
  return cached('apt_' + mode, W, H, (c) => {
    const dawn = mode === 'dawn';
    const wall = dawn ? '#6c6a5c' : '#4b5049';
    const g = c.createLinearGradient(0, 0, 0, H); g.addColorStop(0, shade(wall, .05)); g.addColorStop(1, shade(wall, -.35));
    c.fillStyle = g; c.fillRect(0, 0, W, H);
    stains(c, 0, 0, W, 700, '#3b3220', 44, 9);
    // water stain from the ceiling corner
    c.save(); const sg = c.createRadialGradient(560, 0, 10, 560, 0, 230); sg.addColorStop(0, 'rgba(90,70,30,.35)'); sg.addColorStop(.7, 'rgba(90,70,30,.15)'); sg.addColorStop(.72, 'rgba(70,50,20,.28)'); sg.addColorStop(.76, 'rgba(90,70,30,0)'); c.fillStyle = sg; c.fillRect(300, 0, 420, 300); c.restore();
    // peeling paint patches
    const r = rng(77); for (let i = 0; i < 5; i++) { const x = 40 + r() * 640, y = 80 + r() * 560; c.fillStyle = shade(wall, .18, .6); c.beginPath(); c.ellipse(x, y, 12 + r() * 18, 6 + r() * 10, r() * 3, 0, TAU); c.fill(); c.strokeStyle = shade(wall, -.4, .5); c.lineWidth = 1; c.stroke(); }
    grit(c, 0, 0, W, 760, wall, .6, 12, 2600);
    // window (left)
    c.fillStyle = '#20232a'; c.fillRect(40, 150, 250, 330);
    const sky = c.createLinearGradient(0, 160, 0, 470);
    if (dawn) { sky.addColorStop(0, '#6f7fae'); sky.addColorStop(.55, '#e9a77f'); sky.addColorStop(1, '#ffd59a'); }
    else { sky.addColorStop(0, '#0d1424'); sky.addColorStop(1, '#22304a'); }
    c.fillStyle = sky; c.fillRect(52, 162, 226, 306);
    // distant buildings
    c.fillStyle = dawn ? '#5a5070' : '#0b0f18';
    for (let i = 0; i < 6; i++) { const bx = 52 + i * 40, bh = 60 + (i * 37 % 90); c.fillRect(bx, 468 - bh, 36, bh); }
    c.fillStyle = dawn ? 'rgba(255,220,150,.6)' : 'rgba(255,210,120,.7)';
    for (let i = 0; i < 14; i++) { const bx = 56 + (i * 53 % 220), by = 380 + (i * 29 % 80); if (by < 468) c.fillRect(bx, by, 5, 7); }
    c.strokeStyle = '#2c2a26'; c.lineWidth = 12; c.strokeRect(46, 156, 238, 318); c.lineWidth = 7; c.beginPath(); c.moveTo(165, 160); c.lineTo(165, 470); c.moveTo(50, 315); c.lineTo(280, 315); c.stroke();
    // sagging blind
    c.fillStyle = 'rgba(210,200,170,.85)'; c.beginPath(); c.moveTo(48, 158); c.lineTo(282, 158); c.lineTo(282, 196); c.quadraticCurveTo(170, 214, 48, 200); c.fill();
    // floor
    const fg = c.createLinearGradient(0, 760, 0, H); fg.addColorStop(0, '#3a3128'); fg.addColorStop(1, '#1d1814'); c.fillStyle = fg; c.fillRect(0, 760, W, H - 760);
    c.strokeStyle = 'rgba(0,0,0,.3)'; c.lineWidth = 2; for (let i = 0; i < 8; i++) { c.beginPath(); c.moveTo(0, 790 + i * 60); c.lineTo(W, 780 + i * 64); c.stroke(); }
    c.fillStyle = '#2a251f'; c.fillRect(0, 752, W, 14);
    // mini fridge + dishes (right)
    c.fillStyle = '#b9b7ad'; c.fillRect(560, 560, 150, 200); c.fillStyle = 'rgba(0,0,0,.2)'; c.fillRect(560, 620, 150, 3); c.fillStyle = '#7c7a70'; c.fillRect(690, 580, 6, 30);
    for (let i = 0; i < 4; i++) { c.fillStyle = i % 2 ? '#d9d4c4' : '#a9b6bf'; c.beginPath(); c.ellipse(610 + i * 6, 552 - i * 9, 42, 9, 0, 0, TAU); c.fill(); c.strokeStyle = 'rgba(0,0,0,.25)'; c.lineWidth = 1; c.stroke(); }
    c.fillStyle = '#8a5a3a'; c.fillRect(670, 500, 18, 40); // mug
    grit(c, 0, 760, W, 520, '#3a3128', .7, 33, 2200);
  });
}
function rain(ctx, x, y, w, h, t, a = .35) {
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.strokeStyle = `rgba(170,190,230,${a})`; ctx.lineWidth = 1.2;
  for (let i = 0; i < 40; i++) { const px = x + (hash(i) * w + t * 30) % w, py = y + ((hash(i + 50) * h + t * 420 * (0.8 + hash(i + 9) * .4)) % h); ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px - 3, py + 16); ctx.stroke(); }
  ctx.restore();
}
function bulb(ctx, x, y, t, flick = 1) {
  const f = flick ? (noise1(t * 7) > .72 ? .35 : 1) : 1;
  ctx.strokeStyle = '#222'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, y - 14); ctx.stroke();
  glow(ctx, x, y, 260, '#ffcf7a', .22 * f);
  ctx.fillStyle = mix('#7a6a50', '#fff3c4', f); ctx.beginPath(); ctx.arc(x, y, 12, 0, TAU); ctx.fill();
  return f;
}

// ----- phone chat panel -----
function chatPanel(ctx, x, y, w, h, msgs, t, a = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a;
  ctx.shadowColor = 'rgba(80,140,255,.45)'; ctx.shadowBlur = 30;
  ctx.fillStyle = '#0f1420'; roundRect(ctx, x, y, w, h, 28); ctx.fill(); ctx.shadowBlur = 0;
  ctx.strokeStyle = '#2a3346'; ctx.lineWidth = 3; roundRect(ctx, x, y, w, h, 28); ctx.stroke();
  ctx.save(); roundRect(ctx, x + 6, y + 6, w - 12, h - 12, 22); ctx.clip();
  // header
  ctx.fillStyle = '#161d2d'; ctx.fillRect(x, y, w, 58);
  const og = ctx.createRadialGradient(x + 40, y + 30, 2, x + 40, y + 30, 18); og.addColorStop(0, '#ffffff'); og.addColorStop(.4, '#9fd0ff'); og.addColorStop(1, '#4b6fd6');
  ctx.fillStyle = og; ctx.beginPath(); ctx.arc(x + 40, y + 30, 15 + Math.sin(t * 3) * 1, 0, TAU); ctx.fill();
  ctx.fillStyle = '#e8eefc'; ctx.font = '600 22px Inter'; ctx.fillText('Chatbot', x + 66, y + 37);
  // messages, bottom-anchored, clipped below the header
  ctx.beginPath(); ctx.rect(x, y + 60, w, h - 60); ctx.clip();
  let by = y + h - 18;
  const shown = msgs.filter(m => t >= m.t).slice(-4).reverse();
  ctx.font = '500 23px Inter';
  for (const m of shown) {
    let text = m.text;
    if (m.line) { if (!m.toks) m.toks = alignTokens(m.line); text = m.toks.filter(k => t >= k[1] - .05).map(k => k[0]).join(' '); }
    const lines = wrap(ctx, text || '…', w * .68);
    const bh = lines.length * 30 + 22, bw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 32;
    by -= bh;
    const me = m.me, bx = me ? x + w - bw - 16 : x + 16;
    const pop = easeOut((t - m.t) / .25);
    ctx.save(); ctx.translate(bx + (me ? bw : 0), by + bh); ctx.scale(lerp(.85, 1, pop), lerp(.85, 1, pop)); ctx.translate(-(bx + (me ? bw : 0)), -(by + bh)); ctx.globalAlpha = a * pop;
    ctx.fillStyle = m.sys ? '#3b2424' : me ? '#2f6fe0' : m.troll ? '#3a3a40' : '#232c40'; roundRect(ctx, bx, by, bw, bh, 18); ctx.fill();
    ctx.fillStyle = m.sys ? '#ff8f8f' : '#eef2fb';
    lines.forEach((l, i) => ctx.fillText(l, bx + 16, by + 34 + i * 30));
    if (m.meta) { ctx.font = '500 16px Inter'; ctx.fillStyle = '#8a93a8'; ctx.fillText(m.meta, me ? bx + bw - ctx.measureText(m.meta).width - 4 : bx + 4, by + bh + 18); ctx.font = '500 23px Inter'; }
    ctx.restore();
    by -= m.meta ? 32 : 12;
  }
  ctx.restore(); ctx.restore();
}
function wrap(ctx, text, maxW) {
  const words = text.split(' '), lines = []; let cur = '';
  for (const w of words) { const test = cur ? cur + ' ' + w : w; if (ctx.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test; }
  if (cur) lines.push(cur); return lines;
}

// ----- Rome room -----
function romeBG() {
  return cached('rome', W + 400, H + 400, (c) => {
    c.translate(200, 200);
    bricks(c, -200, -200, W + 400, 1100, '#9a7a56', 5, 96, 44, '#4a3a2a');
    stains(c, -200, -200, W + 400, 1100, '#2a1a0a', 8, 12);
    // small high window with evening light
    c.fillStyle = '#2a1e14'; c.fillRect(470, 120, 150, 150);
    const s = c.createLinearGradient(0, 130, 0, 260); s.addColorStop(0, '#f2b27a'); s.addColorStop(1, '#a8645a'); c.fillStyle = s; c.fillRect(480, 130, 130, 130);
    c.fillStyle = '#3a2a1c'; for (let i = 0; i < 4; i++) c.fillRect(490 + i * 32, 130, 7, 130);
    // floor
    const fg = c.createLinearGradient(0, 880, 0, H); fg.addColorStop(0, '#5a4532'); fg.addColorStop(1, '#2a1f16'); c.fillStyle = fg; c.fillRect(-200, 880, W + 400, H - 680);
    c.strokeStyle = 'rgba(20,10,5,.4)'; c.lineWidth = 2; for (let i = 0; i < 9; i++) { c.beginPath(); c.moveTo(i * 90 - 40, 880); c.lineTo(i * 130 - 260, H); c.stroke(); }
    grit(c, -200, 880, W + 400, 600, '#5a4532', .8, 17, 2600);
    // shelf with jars
    c.fillStyle = '#4a3220'; c.fillRect(40, 380, 200, 12);
    for (let i = 0; i < 4; i++) { c.fillStyle = ['#a0603a', '#8a7a5a', '#6a4a3a', '#b08a5a'][i]; c.beginPath(); c.ellipse(70 + i * 46, 360, 16, 22, 0, 0, TAU); c.fill(); c.fillRect(64 + i * 46, 330, 12, 10); }
  });
}
function table(ctx, x, y, w, h, col = '#5e3d22') {
  const g = ctx.createLinearGradient(0, y, 0, y + 40); g.addColorStop(0, shade(col, .15)); g.addColorStop(1, shade(col, -.2));
  ctx.fillStyle = g; ctx.fillRect(x, y, w, 40);
  ctx.fillStyle = shade(col, -.45); ctx.fillRect(x, y + 40, w, h - 40);
  ctx.fillStyle = 'rgba(0,0,0,.25)'; for (let i = 0; i < 5; i++) ctx.fillRect(x, y + 8 + i * 7, w, 1);
}

// ----- villa -----
function villaBG() {
  return cached('villa', W, H, (c) => {
    const g = c.createLinearGradient(0, 0, 0, 900); g.addColorStop(0, '#5a5248'); g.addColorStop(1, '#2e2a26'); c.fillStyle = g; c.fillRect(0, 0, W, 900);
    // marble panels
    for (let i = 0; i < 4; i++) { c.fillStyle = 'rgba(230,220,200,.07)'; c.fillRect(20 + i * 180, 80, 160, 600); c.strokeStyle = 'rgba(0,0,0,.25)'; c.lineWidth = 3; c.strokeRect(20 + i * 180, 80, 160, 600); }
    const r = rng(4); c.strokeStyle = 'rgba(255,255,255,.06)'; c.lineWidth = 1.5; for (let i = 0; i < 30; i++) { c.beginPath(); let x = r() * W, y = 80 + r() * 600; c.moveTo(x, y); for (let k = 0; k < 4; k++) { x += (r() - .5) * 60; y += r() * 40; c.lineTo(x, y); } c.stroke(); }
    // red wall band (fresco)
    c.fillStyle = '#6e2a22'; c.fillRect(0, 690, W, 60); c.fillStyle = '#c9a24a'; c.fillRect(0, 690, W, 5); c.fillRect(0, 745, W, 5);
    // floor mosaic
    const fg = c.createLinearGradient(0, 900, 0, H); fg.addColorStop(0, '#6a5a48'); fg.addColorStop(1, '#2a221a'); c.fillStyle = fg; c.fillRect(0, 900, W, H - 900);
    for (let y = 900; y < H; y += 26) for (let x = (y / 26 % 2) * 13; x < W; x += 26) { c.fillStyle = (x + y) % 52 ? 'rgba(255,255,255,.04)' : 'rgba(0,0,0,.08)'; c.fillRect(x, y, 24, 24); }
    // fireplace (right side)
    c.fillStyle = '#4a3e36'; c.fillRect(440, 520, 260, 380); c.fillStyle = '#0c0806'; c.beginPath(); c.moveTo(470, 900); c.lineTo(470, 620); c.quadraticCurveTo(570, 560, 670, 620); c.lineTo(670, 900); c.fill();
    bricks(c, 440, 500, 260, 30, '#6b5a4c', 9, 52, 30, '#2a221c');
    // column
    c.fillStyle = '#d8cfbd'; c.fillRect(30, 0, 70, 900); c.fillStyle = 'rgba(0,0,0,.15)'; for (let i = 0; i < 4; i++) c.fillRect(38 + i * 16, 0, 5, 900);
  });
}
function fire(ctx, x, y, w, t, inten = 1) {
  glow(ctx, x, y - 40, 260 * inten, '#ff8a2a', .35 * inten);
  for (let i = 0; i < 9; i++) {
    const px = x + (i - 4) * w / 9, h = (60 + 50 * (.5 + .5 * noise1(t * 5 + i * 3.1))) * inten, sw = noise1(t * 4 + i) * 12;
    const g = ctx.createLinearGradient(0, y, 0, y - h); g.addColorStop(0, 'rgba(255,240,170,.95)'); g.addColorStop(.4, 'rgba(255,150,40,.85)'); g.addColorStop(1, 'rgba(200,40,10,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(px - 18, y); ctx.quadraticCurveTo(px - 16, y - h * .5, px + sw, y - h); ctx.quadraticCurveTo(px + 16, y - h * .5, px + 18, y); ctx.fill();
  }
  ctx.fillStyle = '#3a2214'; for (let i = 0; i < 3; i++) { ctx.save(); ctx.translate(x - 60 + i * 60, y + 6); ctx.rotate((i - 1) * .2); roundRect(ctx, -50, -9, 100, 18, 8); ctx.fill(); ctx.restore(); }
}
function crumpled(ctx, x, y, r, t, burn = 0) {
  ctx.save(); ctx.translate(x, y);
  const rr = rng(9); const pts = [];
  for (let i = 0; i < 14; i++) { const a = i / 14 * TAU; pts.push([Math.cos(a) * r * (.75 + rr() * .35), Math.sin(a) * r * (.75 + rr() * .35)]); }
  ctx.fillStyle = mix('#e9dcb8', '#2a1a10', burn); ctx.beginPath(); spline(ctx, pts, true, .3); ctx.fill();
  ctx.strokeStyle = 'rgba(90,70,40,.5)'; ctx.lineWidth = 1.4;
  for (let i = 0; i < 7; i++) { ctx.beginPath(); ctx.moveTo((rr() - .5) * r, (rr() - .5) * r); ctx.lineTo((rr() - .5) * r * 1.4, (rr() - .5) * r * 1.4); ctx.stroke(); }
  if (burn > 0) { ctx.globalAlpha = clamp(burn * 2); ctx.strokeStyle = '#ff9a3a'; ctx.lineWidth = 3; ctx.beginPath(); spline(ctx, pts.map(p => [p[0] * (1 - burn * .6), p[1] * (1 - burn * .6)]), true, .3); ctx.stroke(); }
  ctx.restore();
}
