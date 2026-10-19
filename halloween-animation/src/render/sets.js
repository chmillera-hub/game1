// Backgrounds: HILL (house on the hill), ATTIC (skeleton dance room), ROOF (rooftop talk).
const { TAU, clamp, lerp, ellipse, rgba, smoothPath, rng, noise, roundRect, spiralPts, taper } = require('./lib');
const { INK, drawPumpkin } = require('./face');
const { drawMiniGhost, drawBat, drawCat } = require('./chars');

// parallax layer transform
function layer(ctx, view, p) {
  const { cam, S, W, H } = view;
  const z = 1 + (cam.z - 1) * p;
  const cx = 540 + (cam.x - 540) * p, cy = 960 + (cam.y - 960) * p;
  ctx.setTransform(S * z, 0, 0, S * z, W / 2 - cx * S * z, H / 2 - cy * S * z);
}

function sky(ctx, top, mid, bot, y0 = -600, y1 = 2400) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  g.addColorStop(0, top); g.addColorStop(0.45, mid); g.addColorStop(1, bot);
  ctx.fillStyle = g; ctx.fillRect(-1200, -1200, 3480, 4320);
}

const STARS = (() => { const r = rng(7); const a = []; for (let i = 0; i < 70; i++) a.push([r() * 1500 - 210, r() * 1400 - 200, 0.6 + r() * 1.6, r() < 0.2, r() * 6]); return a; })();
function stars(ctx, t, alpha = 1) {
  for (const [x, y, s, tw, ph] of STARS) {
    const a = alpha * (tw ? 0.55 + 0.45 * Math.sin(t * 2 + ph) : 0.8);
    ctx.fillStyle = rgba('#fff3c4', a);
    if (s > 1.7) {
      ctx.beginPath(); ctx.moveTo(x, y - s * 4); ctx.quadraticCurveTo(x, y, x + s * 4, y); ctx.quadraticCurveTo(x, y, x, y + s * 4); ctx.quadraticCurveTo(x, y, x - s * 4, y); ctx.quadraticCurveTo(x, y, x, y - s * 4); ctx.fill();
    } else { ctx.beginPath(); ellipse(ctx, x, y, s, s); ctx.fill(); }
  }
}

// swirly cloud band ending in a curl
function swirl(ctx, x, y, len, amp, dir, w, col) {
  const pts = [];
  for (let i = 0; i <= 20; i++) { const u = i / 20; pts.push([x + dir * u * len, y + Math.sin(u * Math.PI * 1.6) * amp]); }
  const e = pts[pts.length - 1];
  spiralPts(e[0] + dir * 6, e[1] - 28, 30, 0.9, dir, Math.PI * (dir > 0 ? 0.5 : 0.5), 16).forEach((p) => pts.push(p));
  ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}

function moon(ctx, x, y, r, t) {
  const glow = ctx.createRadialGradient(x, y, r * 0.9, x, y, r * 2.1);
  glow.addColorStop(0, 'rgba(250,236,180,0.35)'); glow.addColorStop(1, 'rgba(250,236,180,0)');
  ctx.fillStyle = glow; ctx.beginPath(); ellipse(ctx, x, y, r * 2.1, r * 2.1); ctx.fill();
  const g = ctx.createRadialGradient(x - r * 0.25, y - r * 0.25, r * 0.1, x, y, r);
  g.addColorStop(0, '#fdf5d2'); g.addColorStop(1, '#e6d08c');
  ctx.fillStyle = g; ctx.beginPath(); ellipse(ctx, x, y, r, r); ctx.fill();
  ctx.fillStyle = 'rgba(190,160,90,0.18)';
  for (const [dx, dy, cr] of [[-0.35, -0.2, 0.16], [0.25, 0.3, 0.12], [0.1, -0.45, 0.08], [-0.15, 0.45, 0.1], [0.5, -0.1, 0.07]]) { ctx.beginPath(); ellipse(ctx, x + dx * r, y + dy * r, cr * r, cr * r); ctx.fill(); }
}

// recursive bare tree with curling branch tips (deterministic per seed)
const treeCache = {};
function treeSegs(seed, h) {
  const key = seed + ':' + h;
  if (treeCache[key]) return treeCache[key];
  const r = rng(seed);
  const segs = [];
  const grow = (x, y, ang, len, w, depth) => {
    const pts = [[x, y]];
    let a = ang;
    const n = 6;
    for (let i = 1; i <= n; i++) { a += (r() - 0.5) * 0.35; pts.push([pts[i - 1][0] + Math.cos(a) * len / n, pts[i - 1][1] + Math.sin(a) * len / n]); }
    const end = pts[n];
    if (depth >= 3 || len < 40) {
      const dir = r() < 0.5 ? 1 : -1;
      spiralPts(end[0] + Math.cos(a + dir * Math.PI / 2) * 14, end[1] + Math.sin(a + dir * Math.PI / 2) * 14, 14, 0.9, dir, a - dir * Math.PI / 2, 10).forEach((p) => pts.push(p));
      segs.push({ pts, w0: w, w1: 1.5 });
      return;
    }
    segs.push({ pts, w0: w, w1: w * 0.62 });
    const kids = depth === 0 ? 3 : 2;
    for (let k = 0; k < kids; k++) {
      const da = (k - (kids - 1) / 2) * 0.75 + (r() - 0.5) * 0.4;
      grow(end[0], end[1], a + da, len * (0.62 + r() * 0.15), w * 0.62, depth + 1);
    }
  };
  grow(0, 0, -Math.PI / 2 + (r() - 0.5) * 0.2, h * 0.42, h * 0.07, 0);
  treeCache[key] = segs;
  return segs;
}
function tree(ctx, x, y, h, seed, col, flip = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(flip, 1);
  ctx.fillStyle = col;
  for (const s of treeSegs(seed, h)) { ctx.beginPath(); taper(ctx, s.pts, s.w0, s.w1); ctx.fill(); }
  ctx.restore();
}

function fence(ctx, x0, x1, y, h, t) {
  ctx.strokeStyle = '#120e18'; ctx.fillStyle = '#120e18'; ctx.lineCap = 'round';
  ctx.lineWidth = 7;
  ctx.beginPath(); ctx.moveTo(x0, y - h * 0.25); ctx.bezierCurveTo((x0 + x1) * 0.35, y - h * 0.4, (x0 + x1) * 0.65, y - h * 0.1, x1, y - h * 0.3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x0, y - h * 0.75); ctx.bezierCurveTo((x0 + x1) * 0.35, y - h * 0.9, (x0 + x1) * 0.65, y - h * 0.6, x1, y - h * 0.8); ctx.stroke();
  for (let x = x0; x <= x1; x += 48) {
    const lean = Math.sin(x * 0.07) * 0.08;
    ctx.save(); ctx.translate(x, y); ctx.rotate(lean);
    ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -h); ctx.stroke();
    ctx.lineWidth = 5; ctx.beginPath(); spiralPts(8, -h - 6, 9, 0.85, 1, Math.PI, 10).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(0, -h))); ctx.stroke();
    ctx.restore();
  }
}

function tomb(ctx, x, y, w, h, rot, kind) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.beginPath();
  if (kind === 'cross') { ctx.rect(-w * 0.15, -h, w * 0.3, h); ctx.rect(-w * 0.5, -h * 0.75, w, w * 0.3); }
  else { ctx.moveTo(-w / 2, 0); ctx.lineTo(-w / 2, -h + w / 2); ctx.arc(0, -h + w / 2, w / 2, Math.PI, 0); ctx.lineTo(w / 2, 0); ctx.closePath(); }
  ctx.fillStyle = '#3c4954'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  if (kind !== 'cross') { ctx.strokeStyle = 'rgba(20,20,30,0.5)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-w * 0.25, -h * 0.55); ctx.lineTo(w * 0.25, -h * 0.55); ctx.moveTo(-w * 0.2, -h * 0.4); ctx.lineTo(w * 0.2, -h * 0.4); ctx.stroke(); }
  ctx.restore();
}

function candle(ctx, x, y, h, t, ph = 0) {
  ctx.fillStyle = '#efe6cf'; ctx.fillRect(x - 6, y - h, 12, h);
  ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.strokeRect(x - 6, y - h, 12, h);
  const f = 1 + 0.15 * noise(t * 8 + ph);
  const g = ctx.createRadialGradient(x, y - h - 10, 1, x, y - h - 10, 34 * f);
  g.addColorStop(0, 'rgba(255,214,120,0.6)'); g.addColorStop(1, 'rgba(255,160,60,0)');
  ctx.fillStyle = g; ctx.beginPath(); ellipse(ctx, x, y - h - 10, 34 * f, 34 * f); ctx.fill();
  ctx.beginPath(); ctx.moveTo(x, y - h - 18 * f); ctx.quadraticCurveTo(x + 6, y - h - 6, x, y - h); ctx.quadraticCurveTo(x - 6, y - h - 6, x, y - h - 18 * f);
  ctx.fillStyle = '#ffd36b'; ctx.fill();
}

function flames(ctx, x, y, w, h, t) {
  for (let i = 0; i < 5; i++) {
    const fx = x + (i - 2) * w * 0.18;
    const fh = h * (0.6 + 0.4 * Math.abs(noise(t * 4 + i * 3.1)));
    ctx.beginPath(); ctx.moveTo(fx - w * 0.12, y); ctx.quadraticCurveTo(fx - w * 0.1, y - fh * 0.6, fx + noise(t * 3 + i) * 6, y - fh); ctx.quadraticCurveTo(fx + w * 0.1, y - fh * 0.5, fx + w * 0.12, y); ctx.closePath();
    ctx.fillStyle = i % 2 ? '#ffb13b' : '#ff7a2a'; ctx.fill();
  }
  ctx.beginPath(); ellipse(ctx, x, y - 8, w * 0.25, h * 0.25); ctx.fillStyle = '#ffe28a'; ctx.fill();
}

function smoke(ctx, x, y, t, col, n = 3, scale = 1) {
  ctx.strokeStyle = col; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const u = ((t * 0.18 + i / n) % 1);
    const yy = y - u * 160 * scale, xx = x + Math.sin(u * 5 + i) * 18 * scale;
    ctx.globalAlpha = (1 - u) * 0.7;
    ctx.lineWidth = (8 + u * 10) * scale;
    ctx.beginPath(); spiralPts(xx, yy, (14 + u * 18) * scale, 0.8, i % 2 ? 1 : -1, u * 4, 12).forEach((p, k) => (k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

function bats(ctx, t, list) {
  for (const [cx, cy, rx, ry, sp, s, ph] of list) {
    const a = t * sp + ph;
    drawBat(ctx, cx + Math.cos(a) * rx, cy + Math.sin(a * 1.3) * ry, s, t, ph * 3);
  }
}

// ───────────────────────── THE HOUSE (cut-away dollhouse) ─────────────────────────
function roomLit(V, i) { return clamp(((V.windowsLit ?? 1) * 1.25 - i * 0.14) / 0.3); }

function room(ctx, poly, wall, stripe, i, V, fn) {
  ctx.save();
  ctx.beginPath(); poly.forEach((p, k) => (k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  ctx.clip();
  ctx.fillStyle = wall; ctx.fillRect(0, 0, 1080, 1920);
  if (stripe) { ctx.fillStyle = stripe; for (let x = 0; x < 1080; x += 26) ctx.fillRect(x, 0, 11, 1920); }
  fn();
  const L = roomLit(V, i);
  const glow = (V.houseGlow ?? 1);
  const xs = poly.map((p) => p[0]), ys = poly.map((p) => p[1]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cy = (Math.min(...ys) + Math.max(...ys)) / 2;
  ctx.fillStyle = rgba('#0a0d22', 0.62 * (1 - L) + 0.1);
  ctx.fillRect(0, 0, 1080, 1920);
  const g = ctx.createRadialGradient(cx, cy, 10, cx, cy, 220);
  g.addColorStop(0, rgba('#ffcf7a', 0.28 * L * glow)); g.addColorStop(1, 'rgba(255,200,120,0)');
  ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(0, 0, 1080, 1920); ctx.globalCompositeOperation = 'source-over';
  ctx.restore();
}

function shelfBottles(ctx, x, y, w, t, seed) {
  const r = rng(seed);
  ctx.fillStyle = '#3a2418'; ctx.fillRect(x, y, w, 8);
  const cols = ['#7fd36b', '#b07ad9', '#ff9f5a', '#6bd3c9', '#e86b8a'];
  for (let bx = x + 10; bx < x + w - 12; bx += 22 + r() * 10) {
    const h = 18 + r() * 22, c = cols[Math.floor(r() * cols.length)];
    ctx.beginPath(); roundRect(ctx, bx - 7, y - h, 14, h, 5); ctx.fillStyle = c; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.stroke();
    ctx.fillStyle = '#5a3a28'; ctx.fillRect(bx - 3, y - h - 6, 6, 6);
  }
}

function drawHouse(ctx, t, V, pipDraw, skelDraw) {
  ctx.lineJoin = 'round';
  // tower roof + finial
  ctx.beginPath(); ctx.moveTo(420, 842); ctx.quadraticCurveTo(520, 790, 566, 652); ctx.quadraticCurveTo(612, 790, 714, 836); ctx.closePath();
  ctx.fillStyle = '#2b2139'; ctx.fill();
  ctx.save(); ctx.clip(); ctx.strokeStyle = '#3b2f4c'; ctx.lineWidth = 4;
  for (let y = 680; y < 850; y += 22) { ctx.beginPath(); for (let x = 400; x < 740; x += 22) { ctx.moveTo(x, y); ctx.arc(x + 11, y, 11, Math.PI, 0, true); } ctx.stroke(); }
  ctx.restore();
  ctx.beginPath(); ctx.moveTo(420, 842); ctx.quadraticCurveTo(520, 790, 566, 652); ctx.quadraticCurveTo(612, 790, 714, 836); ctx.closePath();
  ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.stroke();
  // chimney
  ctx.beginPath(); ctx.moveTo(282, 950); ctx.lineTo(290, 846); ctx.lineTo(340, 842); ctx.lineTo(344, 946); ctx.closePath();
  ctx.fillStyle = '#8a3f2a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.stroke();
  ctx.strokeStyle = '#6a2c1c'; ctx.lineWidth = 3; for (let y = 866; y < 946; y += 18) { ctx.beginPath(); ctx.moveTo(288, y); ctx.lineTo(342, y - 2); ctx.stroke(); }
  ctx.fillStyle = '#5a2a1c'; ctx.fillRect(282, 834, 66, 14); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.strokeRect(282, 834, 66, 14);
  // main mansard roof
  ctx.beginPath(); ctx.moveTo(160, 1062); ctx.lineTo(924, 1054); ctx.lineTo(866, 926); ctx.lineTo(246, 934); ctx.closePath();
  ctx.fillStyle = '#2a2138'; ctx.fill();
  ctx.save(); ctx.clip(); ctx.strokeStyle = '#3a2e4a'; ctx.lineWidth = 4;
  for (let y = 944; y < 1062; y += 24) { ctx.beginPath(); for (let x = 150; x < 940; x += 24) { ctx.moveTo(x, y); ctx.arc(x + 12, y, 12, Math.PI, 0, true); } ctx.stroke(); }
  ctx.restore();
  ctx.beginPath(); ctx.moveTo(160, 1062); ctx.lineTo(924, 1054); ctx.lineTo(866, 926); ctx.lineTo(246, 934); ctx.closePath();
  ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.stroke();
  // iron cresting on roof
  ctx.strokeStyle = INK; ctx.lineWidth = 4;
  for (let x = 260; x < 860; x += 30) { if (x > 430 && x < 700) continue; ctx.beginPath(); ctx.moveTo(x, 930); ctx.lineTo(x, 906); ctx.stroke(); ctx.beginPath(); ctx.arc(x + 5, 904, 5, Math.PI, Math.PI * 2.6); ctx.stroke(); }

  // ATTIC room (tower)
  const attic = [[448, 836], [684, 832], [690, 1052], [440, 1054]];
  room(ctx, attic, '#8e4f72', '#7b4163', 0, V, () => {
    ctx.beginPath(); ellipse(ctx, 566, 900, 38, 38); ctx.fillStyle = '#3f7472'; ctx.fill(); ctx.strokeStyle = '#3a2214'; ctx.lineWidth = 8; ctx.stroke();
    ctx.beginPath(); ellipse(ctx, 576, 892, 14, 14); ctx.fillStyle = '#f6eab8'; ctx.fill();
    ctx.fillStyle = '#4a2e2a'; ctx.fillRect(440, 1030, 260, 30);
    ctx.fillStyle = '#5a2e1e'; ctx.fillRect(458, 990, 34, 30); ctx.beginPath(); ctx.moveTo(470, 990); ctx.quadraticCurveTo(480, 960, 500, 950); ctx.lineTo(506, 968); ctx.closePath(); ctx.fillStyle = '#b08a3a'; ctx.fill();
    skelDraw && skelDraw();
  });
  // second floor
  const lib = [[210, 1058], [526, 1056], [528, 1272], [200, 1274]];
  room(ctx, lib, '#5d7550', '#567049', 2, V, () => {
    ctx.fillStyle = '#3a2418';
    for (const y of [1120, 1180]) { ctx.fillRect(225, y, 120, 8); for (let x = 240; x < 340; x += 32) { ctx.beginPath(); ellipse(ctx, x, y - 14, 12, 13); ctx.fillStyle = '#f1ead8'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.stroke(); ctx.fillStyle = INK; ctx.fillRect(x - 6, y - 17, 4, 4); ctx.fillRect(x + 2, y - 17, 4, 4); ctx.fillStyle = '#3a2418'; } }
    ctx.beginPath(); ctx.moveTo(400, 1270); ctx.lineTo(380, 1150); ctx.lineTo(410, 1100); ctx.lineTo(460, 1100); ctx.lineTo(486, 1150); ctx.lineTo(470, 1270); ctx.closePath();
    ctx.fillStyle = '#3d2a24'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
    ctx.strokeStyle = '#7b5b8f'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(400, 1130); ctx.lineTo(460, 1250); ctx.moveTo(470, 1130); ctx.lineTo(410, 1250); ctx.stroke();
    drawCat(ctx, 436, 1100, 0.32, t);
    ctx.strokeStyle = 'rgba(240,240,255,0.35)'; ctx.lineWidth = 1.5;
    for (let i = 0; i < 5; i++) { ctx.beginPath(); ctx.moveTo(212, 1060); ctx.lineTo(212 + Math.cos(i * 0.35) * 60, 1060 + Math.sin(i * 0.35) * 60); ctx.stroke(); }
  });
  const kit = [[526, 1056], [872, 1052], [880, 1270], [528, 1272]];
  room(ctx, kit, '#b9652e', '#ad5c28', 3, V, () => {
    ctx.fillStyle = '#2a2230'; ctx.beginPath(); roundRect(ctx, 760, 1150, 90, 118, 8); ctx.fill();
    const og = ctx.createRadialGradient(805, 1215, 3, 805, 1215, 40); og.addColorStop(0, '#ffd27a'); og.addColorStop(1, '#ff7a2a');
    ctx.fillStyle = og; ctx.beginPath(); roundRect(ctx, 780, 1195, 50, 36, 6); ctx.fill();
    ctx.fillStyle = '#5a3a28'; ctx.fillRect(560, 1215, 160, 10); ctx.fillRect(570, 1225, 10, 45); ctx.fillRect(700, 1225, 10, 45);
    for (const [bx, bw] of [[590, 40], [640, 34], [684, 28]]) { ctx.beginPath(); ellipse(ctx, bx, 1205, bw / 2, 13); ctx.fillStyle = '#d9a25a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2.5; ctx.stroke(); }
    for (let x = 560; x < 740; x += 40) { ctx.beginPath(); ctx.moveTo(x, 1056); ctx.lineTo(x, 1080); ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.stroke(); ctx.beginPath(); ellipse(ctx, x, 1088, 12, 9); ctx.fillStyle = '#8a8f9a'; ctx.fill(); }
    drawMiniGhost(ctx, 650, 1150 + Math.sin(t * 2) * 3, 0.55, t, { ph: 2 });
  });
  // ground floor
  const pot = [[185, 1272], [400, 1272], [402, 1506], [176, 1506]];
  room(ctx, pot, '#2f5a5a', '#2a5252', 4, V, () => {
    shelfBottles(ctx, 200, 1330, 180, t, 3); shelfBottles(ctx, 200, 1390, 180, t, 9);
    ctx.beginPath(); ellipse(ctx, 300, 1470, 52, 36); ctx.fillStyle = '#16121c'; ctx.fill();
    ctx.beginPath(); ellipse(ctx, 300, 1442, 50, 12); ctx.fillStyle = '#7fe36b'; ctx.fill();
    smoke(ctx, 300, 1430, t, 'rgba(140,240,120,0.6)', 3, 0.5);
    for (let i = 0; i < 4; i++) { const u = (t * 0.9 + i * 0.25) % 1; ctx.beginPath(); ellipse(ctx, 280 + i * 13, 1440 - u * 22, 5 * (1 - u) + 1, 5 * (1 - u) + 1); ctx.fillStyle = '#b6ff9a'; ctx.fill(); }
  });
  const hall = [[400, 1272], [665, 1270], [668, 1506], [402, 1506]];
  room(ctx, hall, '#8a7a3a', '#827236', 5, V, () => {
    ctx.fillStyle = '#c76a8a';
    for (let i = 0; i < 8; i++) ctx.fillRect(560 + i * 12, 1490 - i * 26, 110, 14);
    ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(555, 1500); ctx.lineTo(650, 1290); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(470, 1506); ctx.lineTo(470, 1430); ctx.arc(505, 1430, 35, Math.PI, 0); ctx.lineTo(540, 1506); ctx.fillStyle = '#3a2214'; ctx.fill(); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(530, 1272); ctx.lineTo(530, 1300); ctx.stroke();
    ctx.beginPath(); ellipse(ctx, 530, 1308, 34, 7); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
    candle(ctx, 500, 1306, 14, t, 1); candle(ctx, 530, 1302, 14, t, 2); candle(ctx, 560, 1306, 14, t, 3);
    ctx.beginPath(); roundRect(ctx, 418, 1330, 40, 52, 4); ctx.fillStyle = '#5a3a28'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
    ctx.beginPath(); ellipse(ctx, 438, 1356, 12, 15); ctx.fillStyle = '#635e78'; ctx.fill();
    drawPumpkin(ctx, { x: 450, y: 1488, r: 16, face: 'patch', lit: 1, t, glow: true });
  });
  const par = [[665, 1270], [895, 1268], [906, 1506], [668, 1506]];
  room(ctx, par, '#a3562b', '#97502a', 6, V, () => {
    ctx.fillStyle = '#5a5568'; ctx.fillRect(740, 1380, 100, 126); ctx.fillStyle = '#1a1420'; ctx.fillRect(758, 1420, 64, 86);
    flames(ctx, 790, 1504, 60, 60, t);
    ctx.fillStyle = '#3a3348'; ctx.fillRect(730, 1372, 120, 12);
    for (const ax of [700, 868]) { ctx.beginPath(); roundRect(ctx, ax - 26, 1440, 52, 66, 14); ctx.fillStyle = '#d9783a'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke(); }
    drawMiniGhost(ctx, 700, 1440, 0.42, t, { ph: 1 }); drawMiniGhost(ctx, 868, 1440, 0.42, t, { ph: 3, flip: -1 });
    ctx.fillStyle = '#3c8a5a'; ctx.fillRect(712, 1448, 18, 14); ctx.fillStyle = '#3c5a8a'; ctx.fillRect(842, 1448, 18, 14);
  });
  // frame
  ctx.strokeStyle = '#1b1522'; ctx.lineWidth = 14; ctx.lineCap = 'round';
  const lines = [[[176, 1506], [906, 1506]], [[185, 1272], [895, 1268]], [[210, 1058], [872, 1052]], [[400, 1272], [402, 1506]], [[665, 1270], [668, 1506]], [[526, 1056], [528, 1272]],
    [[176, 1506], [185, 1272]], [[185, 1272], [210, 1058]], [[906, 1506], [895, 1268]], [[895, 1268], [872, 1052]], [[440, 1054], [448, 836]], [[690, 1052], [684, 832]], [[448, 836], [684, 832]]];
  ctx.beginPath(); for (const [a, b] of lines) { ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); } ctx.stroke();
  // steps
  ctx.fillStyle = '#5a5470'; ctx.fillRect(470, 1506, 70, 12); ctx.fillRect(460, 1518, 90, 12);
  // the newest ghost on the tower peak
  pipDraw && pipDraw();
}

function drawHill(ctx, view, t, V, chars) {
  layer(ctx, view, 0.04);
  sky(ctx, '#0e1828', '#1f3b48', '#3f6e6a', -400, 1900);
  stars(ctx, t);
  swirl(ctx, -40, 420, 380, 30, 1, 22, 'rgba(120,180,170,0.18)');
  swirl(ctx, 1120, 260, 330, 26, -1, 18, 'rgba(120,180,170,0.15)');
  swirl(ctx, 700, 1020, 300, 20, 1, 16, 'rgba(120,180,170,0.12)');
  layer(ctx, view, 0.15);
  moon(ctx, 610, 620, 300, t);
  bats(ctx, t, [[600, 520, 260, 60, 0.35, 0.9, 0], [420, 760, 200, 40, 0.5, 0.7, 2], [800, 380, 180, 50, 0.42, 0.6, 4]]);
  layer(ctx, view, 0.35);
  ctx.beginPath(); ctx.moveTo(-300, 1320); ctx.bezierCurveTo(0, 1250, 220, 1260, 420, 1310); ctx.bezierCurveTo(620, 1350, 900, 1240, 1400, 1300); ctx.lineTo(1400, 2200); ctx.lineTo(-300, 2200); ctx.closePath();
  ctx.fillStyle = '#21424b'; ctx.fill();
  // town on the far left hill
  for (let i = 0; i < 9; i++) {
    const hx = 30 + i * 38, hy = 1290 + Math.sin(i * 1.7) * 6, hh = 34 + (i * 7) % 20;
    ctx.fillStyle = '#152a31'; ctx.beginPath(); ctx.moveTo(hx - 16, hy); ctx.lineTo(hx - 16, hy - hh); ctx.lineTo(hx, hy - hh - 16); ctx.lineTo(hx + 16, hy - hh); ctx.lineTo(hx + 16, hy); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffcf6b'; ctx.fillRect(hx - 7, hy - hh + 8, 6, 7); if (i % 2) ctx.fillRect(hx + 3, hy - hh + 20, 6, 7);
  }
  ctx.fillStyle = '#152a31'; ctx.beginPath(); ctx.moveTo(196, 1290); ctx.lineTo(196, 1220); ctx.lineTo(206, 1170); ctx.lineTo(216, 1220); ctx.lineTo(216, 1290); ctx.fill();
  layer(ctx, view, 0.6);
  ctx.beginPath(); ctx.moveTo(-300, 1420); ctx.bezierCurveTo(100, 1360, 300, 1400, 540, 1420); ctx.bezierCurveTo(800, 1440, 1000, 1360, 1400, 1400); ctx.lineTo(1400, 2300); ctx.lineTo(-300, 2300); ctx.closePath();
  ctx.fillStyle = '#183039'; ctx.fill();
  tree(ctx, 70, 1430, 520, 11, '#14232a', 1);
  layer(ctx, view, 1);
  // main hill with a curling tip on the right
  ctx.beginPath(); ctx.moveTo(-200, 1560); ctx.bezierCurveTo(150, 1500, 300, 1490, 540, 1500); ctx.bezierCurveTo(760, 1505, 900, 1480, 1010, 1430);
  ctx.bezierCurveTo(1080, 1395, 1110, 1330, 1060, 1310); ctx.bezierCurveTo(1020, 1295, 1000, 1340, 1035, 1350); ctx.bezierCurveTo(1060, 1356, 1068, 1330, 1052, 1325);
  ctx.bezierCurveTo(1200, 1380, 1300, 1500, 1300, 1560); ctx.lineTo(1300, 2400); ctx.lineTo(-200, 2400); ctx.closePath();
  const hg = ctx.createLinearGradient(0, 1480, 0, 1920); hg.addColorStop(0, '#1a2a2c'); hg.addColorStop(1, '#0c1215');
  ctx.fillStyle = hg; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke();
  // path
  ctx.beginPath(); ctx.moveTo(505, 1530); ctx.bezierCurveTo(470, 1600, 620, 1650, 560, 1760); ctx.lineTo(680, 1760); ctx.bezierCurveTo(720, 1650, 560, 1600, 545, 1530); ctx.closePath(); ctx.fillStyle = '#3a3f4c'; ctx.fill();
  tree(ctx, 95, 1560, 760, 5, '#100c16', 1);
  // ghosts around the house
  const ga = V.ghostsA ?? 0;
  if (ga > 0.01) {
    drawMiniGhost(ctx, 120 + Math.sin(t * 0.5) * 20, 1150, 0.7, t, { ph: 0.5, alpha: 0.95 * ga });
    drawMiniGhost(ctx, 960 + Math.sin(t * 0.6) * 18, 960, 0.6, t, { ph: 2.5, alpha: 0.95 * ga, flip: -1 });
  }
  drawHouse(ctx, t, V, chars.pip, chars.skels);
  // rising lantern ghosts
  const up = V.ghostsUp || 0;
  if (up > 0.01) {
    for (let i = 0; i < 7; i++) {
      const u = clamp(up * 1.3 - i * 0.07);
      if (u <= 0) continue;
      const sx = [315, 200, 760, 880, 420, 640, 120][i], sy = [840, 1150, 1100, 1250, 1300, 1280, 1400][i];
      const yy = sy - u * (380 + i * 40), xx = sx + Math.sin(t * 0.8 + i) * 30 + (i % 2 ? 1 : -1) * u * 60;
      drawMiniGhost(ctx, xx, yy, 0.5 + (i % 3) * 0.08, t, { ph: i, lantern: 1, alpha: clamp(u * 4), flip: i % 2 ? -1 : 1 });
    }
  }
  // graveyard
  tomb(ctx, 90, 1620, 60, 90, -0.12, 'round'); tomb(ctx, 190, 1600, 46, 70, 0.08, 'cross'); tomb(ctx, 880, 1610, 56, 84, 0.1, 'round'); tomb(ctx, 980, 1640, 44, 66, -0.15, 'cross');
  drawPumpkin(ctx, { x: 300, y: 1600, r: 30, face: 'patch', lit: 0.9, t }); drawPumpkin(ctx, { x: 780, y: 1590, r: 26, face: 'pip', carve: 1, lit: 0.9, t });
  // right tree with the owl
  tree(ctx, 1010, 1640, 820, 23, '#0d0a12', -1);
  ctx.beginPath(); ctx.moveTo(1040, 1180); ctx.bezierCurveTo(980, 1120, 900, 1128, 830, 1110); ctx.lineWidth = 16; ctx.strokeStyle = '#0d0a12'; ctx.lineCap = 'round'; ctx.stroke();
  ctx.beginPath(); spiralPts(822, 1094, 16, 0.9, -1, Math.PI * 0.5, 12).forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(830, 1110))); ctx.lineWidth = 8; ctx.stroke();
  chars.owl && chars.owl();
  layer(ctx, view, 1.12);
  fence(ctx, -60, 1140, 1790, 110, t);
  drawPumpkin(ctx, { x: 120, y: 1760, r: 44, face: 'patch', lit: 1, t }); drawPumpkin(ctx, { x: 960, y: 1770, r: 50, face: null, t });
}

// ───────────────────────── ATTIC ─────────────────────────
function drawAttic(ctx, view, t, V, chars) {
  layer(ctx, view, 0.5);
  ctx.save();
  ctx.beginPath(); ellipse(ctx, 540, 600, 172, 172); ctx.clip();
  sky(ctx, '#11202e', '#2a5058', '#3f6e6a', 380, 820);
  stars(ctx, t, 0.8);
  moon(ctx, 600, 560, 80, t);
  bats(ctx, t, [[540, 600, 140, 30, 0.6, 0.6, 1]]);
  ctx.restore();
  layer(ctx, view, 1);
  // back wall with stripes, wall cut out where the window is
  ctx.save();
  ctx.beginPath(); ctx.rect(-300, 150, 1680, 1160); ellipse(ctx, 540, 600, 172, 172); ctx.clip('evenodd');
  ctx.fillStyle = '#8e4f72'; ctx.fillRect(-300, 150, 1680, 1160);
  ctx.fillStyle = '#7b4163'; for (let x = -300; x < 1400; x += 64) ctx.fillRect(x, 150, 26, 1160);
  ctx.fillStyle = '#3d2638'; ctx.fillRect(-300, 1060, 1680, 250);
  ctx.strokeStyle = '#2a1826'; ctx.lineWidth = 5; for (let x = -280; x < 1400; x += 120) { ctx.strokeRect(x, 1090, 90, 180); }
  ctx.restore();
  // window frame
  ctx.beginPath(); ellipse(ctx, 540, 600, 176, 176); ctx.strokeStyle = '#3a2214'; ctx.lineWidth = 30; ctx.stroke(); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.beginPath(); ellipse(ctx, 540, 600, 192, 192); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(540, 428); ctx.lineTo(540, 772); ctx.moveTo(368, 600); ctx.lineTo(712, 600); ctx.strokeStyle = '#3a2214'; ctx.lineWidth = 16; ctx.stroke();
  // sill candles
  ctx.fillStyle = '#3a2214'; ctx.fillRect(400, 790, 280, 20);
  candle(ctx, 440, 790, 40, t, 1); candle(ctx, 470, 790, 26, t, 2); candle(ctx, 640, 790, 34, t, 3);
  // slanted ceiling beams
  ctx.fillStyle = '#2a1824';
  ctx.beginPath(); ctx.moveTo(-300, -200); ctx.lineTo(560, -200); ctx.lineTo(-300, 900); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.moveTo(1380, -200); ctx.lineTo(520, -200); ctx.lineTo(1380, 900); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#4a2e3e'; ctx.lineWidth = 26;
  ctx.beginPath(); ctx.moveTo(380, -200); ctx.lineTo(-300, 690); ctx.moveTo(700, -200); ctx.lineTo(1380, 690); ctx.stroke();
  ctx.strokeStyle = INK; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(560, -200); ctx.lineTo(-300, 900); ctx.moveTo(520, -200); ctx.lineTo(1380, 900); ctx.stroke();
  // cobwebs
  for (const [cx, cy, sd] of [[60, 470, 1], [1020, 470, -1]]) {
    ctx.strokeStyle = 'rgba(230,230,250,0.4)'; ctx.lineWidth = 2;
    for (let i = 0; i < 6; i++) { const a = sd > 0 ? -0.9 + i * 0.32 : Math.PI + 0.9 - i * 0.32; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * 150, cy + Math.sin(a) * 150); ctx.stroke(); }
    for (let r = 40; r <= 140; r += 33) { ctx.beginPath(); for (let i = 0; i < 6; i++) { const a = sd > 0 ? -0.9 + i * 0.32 : Math.PI + 0.9 - i * 0.32; const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); }
  }
  // spider on a thread
  const sy = 330 + Math.sin(t * 0.9) * 40;
  ctx.beginPath(); ctx.moveTo(880, 120); ctx.lineTo(880, sy); ctx.strokeStyle = 'rgba(230,230,250,0.5)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = '#15111c'; ctx.beginPath(); ellipse(ctx, 880, sy + 14, 14, 16); ctx.fill();
  ctx.strokeStyle = '#15111c'; ctx.lineWidth = 3; for (let i = 0; i < 4; i++) for (const sd of [-1, 1]) { ctx.beginPath(); ctx.moveTo(880, sy + 10 + i * 4); ctx.quadraticCurveTo(880 + sd * 22, sy + i * 6 - 6, 880 + sd * 28, sy + 14 + i * 8); ctx.stroke(); }
  ctx.fillStyle = '#ff6b6b'; ctx.fillRect(874, sy + 8, 3, 3); ctx.fillRect(883, sy + 8, 3, 3);
  // floor
  ctx.fillStyle = '#4a2e2a'; ctx.fillRect(-300, 1300, 1680, 900);
  ctx.strokeStyle = '#3a2220'; ctx.lineWidth = 4;
  for (let i = -14; i <= 14; i++) { ctx.beginPath(); ctx.moveTo(540 + i * 50, 1300); ctx.lineTo(540 + i * 170, 2000); ctx.stroke(); }
  for (const y of [1360, 1450, 1580, 1760]) { ctx.beginPath(); ctx.moveTo(-300, y); ctx.lineTo(1380, y); ctx.stroke(); }
  ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-300, 1300); ctx.lineTo(1380, 1300); ctx.stroke();
  // rug
  const rugs = [['#5a2e6a', 430, 96], ['#e8872f', 380, 84], ['#3b2050', 330, 72], ['#c76a8a', 250, 56]];
  for (const [c, rx, ry] of rugs) { ctx.beginPath(); ellipse(ctx, 540, 1392, rx, ry); ctx.fillStyle = c; ctx.fill(); }
  ctx.beginPath(); ellipse(ctx, 540, 1392, 430, 96); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  // moonbeam
  ctx.beginPath(); ctx.moveTo(400, 640); ctx.lineTo(680, 560); ctx.lineTo(900, 1420); ctx.lineTo(300, 1460); ctx.closePath();
  ctx.fillStyle = 'rgba(220,240,230,0.06)'; ctx.fill();
  // gramophone on a little table
  ctx.fillStyle = '#3a2214'; ctx.beginPath(); ellipse(ctx, 150, 1140, 110, 22); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.fillRect(140, 1150, 20, 160); ctx.strokeRect(140, 1150, 20, 160);
  ctx.beginPath(); roundRect(ctx, 80, 1060, 140, 70, 8); ctx.fillStyle = '#5a2e1e'; ctx.fill(); ctx.stroke();
  ctx.save(); ctx.translate(150, 1060); ctx.scale(1, 0.25); ctx.rotate(t * 3.5);
  ctx.beginPath(); ellipse(ctx, 0, 0, 62, 62); ctx.fillStyle = '#15111c'; ctx.fill(); ctx.fillStyle = '#c76a8a'; ctx.beginPath(); ellipse(ctx, 0, 0, 16, 16); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(-60, -3, 50, 6); ctx.restore();
  ctx.beginPath(); ctx.moveTo(180, 1050); ctx.quadraticCurveTo(200, 960, 240, 900); ctx.lineTo(330, 820); ctx.quadraticCurveTo(380, 860, 360, 940); ctx.lineTo(258, 920); ctx.quadraticCurveTo(220, 990, 200, 1052); ctx.closePath();
  const hg = ctx.createLinearGradient(240, 820, 360, 940); hg.addColorStop(0, '#d9a84a'); hg.addColorStop(1, '#7b4fa0');
  ctx.fillStyle = hg; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.beginPath(); ellipse(ctx, 345, 880, 30, 62, 0.75); ctx.fillStyle = '#2a1830'; ctx.fill(); ctx.stroke();
  const playing = Math.max(V.dance || 0, V.hum || 0);
  if (playing > 0.05) {
    ctx.fillStyle = rgba('#ffe7a0', playing * 0.9); ctx.font = '700 46px Baloo';
    for (let i = 0; i < 3; i++) { const u = (t * 0.45 + i / 3) % 1; ctx.globalAlpha = (1 - u) * playing; ctx.fillText(i % 2 ? '♪' : '♫', 380 + u * 180 + Math.sin(u * 8 + i) * 20, 840 - u * 260); }
    ctx.globalAlpha = 1;
  }
  // old trunk
  ctx.beginPath(); roundRect(ctx, 840, 1180, 230, 130, 14); ctx.fillStyle = '#5a3424'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.stroke();
  ctx.fillStyle = '#2a1a14'; ctx.fillRect(880, 1180, 18, 130); ctx.fillRect(1010, 1180, 18, 130);
  ctx.fillStyle = '#d9b44a'; ctx.fillRect(945, 1232, 24, 26);
  // characters
  chars.skels && chars.skels();
  // warm candle light
  const g = ctx.createRadialGradient(520, 820, 40, 520, 820, 900);
  g.addColorStop(0, 'rgba(255,190,110,0.16)'); g.addColorStop(1, 'rgba(255,190,110,0)');
  ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(-300, -200, 1680, 2400); ctx.globalCompositeOperation = 'source-over';
}

// ───────────────────────── ROOF ─────────────────────────
function shingles(ctx, ridgeY, t, shake) {
  ctx.save();
  ctx.beginPath(); ctx.moveTo(-400, ridgeY(-400)); for (let x = -400; x <= 1480; x += 40) ctx.lineTo(x, ridgeY(x)); ctx.lineTo(1480, 2300); ctx.lineTo(-400, 2300); ctx.closePath();
  const g = ctx.createLinearGradient(0, 1150, 0, 1920); g.addColorStop(0, '#30283c'); g.addColorStop(1, '#1d1726');
  ctx.fillStyle = g; ctx.fill();
  ctx.clip();
  ctx.strokeStyle = '#41364f'; ctx.lineWidth = 4;
  let row = 0;
  for (let dy = 40; dy < 900; dy += 34 + dy * 0.06) {
    const w = 46 + dy * 0.08;
    ctx.beginPath();
    for (let x = -400 + (row % 2) * w / 2; x < 1480; x += w) {
      const y = ridgeY(x) + dy + (shake ? Math.sin(x * 0.1 + t * 50) * shake * 2 : 0);
      ctx.moveTo(x, y); ctx.arc(x + w / 2, y, w / 2, Math.PI, 0, true);
    }
    ctx.stroke(); row++;
  }
  ctx.restore();
  // ridge cap + iron cresting
  ctx.beginPath(); ctx.moveTo(-400, ridgeY(-400)); for (let x = -400; x <= 1480; x += 30) ctx.lineTo(x, ridgeY(x));
  ctx.strokeStyle = INK; ctx.lineWidth = 26; ctx.stroke(); ctx.strokeStyle = '#3b3046'; ctx.lineWidth = 16; ctx.stroke();
}

function drawRoof(ctx, view, t, V, chars, ridgeY) {
  layer(ctx, view, 0.04);
  sky(ctx, '#0d1726', '#1d3946', '#3a6866', -400, 1300);
  stars(ctx, t);
  swirl(ctx, -60, 300, 420, 34, 1, 26, 'rgba(120,180,170,0.17)');
  swirl(ctx, 1140, 900, 360, 28, -1, 20, 'rgba(120,180,170,0.13)');
  layer(ctx, view, 0.12);
  moon(ctx, 760, 560, 380, t);
  bats(ctx, t, [[760, 420, 300, 70, 0.3, 0.8, 1], [300, 360, 200, 40, 0.45, 0.6, 3]]);
  layer(ctx, view, 0.3);
  ctx.beginPath(); ctx.moveTo(-400, 1080); ctx.bezierCurveTo(0, 1010, 260, 1020, 520, 1070); ctx.bezierCurveTo(780, 1110, 1000, 1030, 1500, 1060); ctx.lineTo(1500, 1800); ctx.lineTo(-400, 1800); ctx.closePath();
  ctx.fillStyle = '#20404a'; ctx.fill();
  for (let i = 0; i < 11; i++) {
    const hx = 30 + i * 36, hy = 1062 + Math.sin(i * 1.3) * 5 - (i > 4 && i < 8 ? 8 : 0), hh = 30 + (i * 11) % 22;
    ctx.fillStyle = '#132831'; ctx.beginPath(); ctx.moveTo(hx - 15, hy); ctx.lineTo(hx - 15, hy - hh); ctx.lineTo(hx, hy - hh - 15); ctx.lineTo(hx + 15, hy - hh); ctx.lineTo(hx + 15, hy); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#ffcf6b'; ctx.fillRect(hx - 7, hy - hh + 7, 5, 6); if (i % 3 !== 1) ctx.fillRect(hx + 3, hy - hh + 18, 5, 6);
  }
  ctx.fillStyle = '#132831'; ctx.beginPath(); ctx.moveTo(206, 1060); ctx.lineTo(206, 990); ctx.lineTo(216, 940); ctx.lineTo(226, 990); ctx.lineTo(226, 1060); ctx.fill();
  const tg = ctx.createRadialGradient(220, 1040, 10, 220, 1040, 260); tg.addColorStop(0, 'rgba(255,200,110,0.18)'); tg.addColorStop(1, 'rgba(255,200,110,0)');
  ctx.fillStyle = tg; ctx.fillRect(-100, 800, 700, 400);
  layer(ctx, view, 0.5);
  tree(ctx, 30, 1260, 560, 31, '#15262c', 1);
  tree(ctx, 1080, 1250, 480, 37, '#15262c', -1);
  layer(ctx, view, 0.85);
  // chimney
  ctx.beginPath(); ctx.moveTo(905, 1220); ctx.lineTo(915, 800); ctx.lineTo(1035, 792); ctx.lineTo(1050, 1210); ctx.closePath();
  ctx.fillStyle = '#7d3a28'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.stroke();
  ctx.save(); ctx.clip(); ctx.strokeStyle = '#5e2a1c'; ctx.lineWidth = 3;
  for (let y = 820, r = 0; y < 1220; y += 28, r++) { ctx.beginPath(); ctx.moveTo(900, y); ctx.lineTo(1060, y - 4); ctx.stroke(); for (let x = 905 + (r % 2) * 28; x < 1060; x += 56) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + 28); ctx.stroke(); } }
  ctx.restore();
  ctx.fillStyle = '#4e2418'; ctx.beginPath(); roundRect(ctx, 898, 774, 156, 30, 6); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 6; ctx.stroke();
  smoke(ctx, 975, 760, t, 'rgba(200,215,220,0.35)', 3, 1.1);
  // weathervane
  ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(70, ridgeY(70)); ctx.lineTo(70, 880); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(10, 930); ctx.lineTo(130, 930); ctx.lineWidth = 5; ctx.stroke();
  ctx.save(); ctx.translate(70, 860); ctx.rotate(Math.sin(t * 0.5) * 0.1);
  ctx.beginPath(); ctx.arc(0, 0, 26, 0.6, Math.PI * 2 - 0.6); ctx.arc(12, 0, 20, Math.PI * 2 - 0.9, 0.9, true); ctx.closePath(); ctx.fillStyle = '#15111c'; ctx.fill();
  ctx.restore();
  layer(ctx, view, 1);
  if (chars.behind) chars.behind();
  shingles(ctx, ridgeY, t, V.roofShake || 0);
  // gutter edge and the drop below
  ctx.beginPath(); ctx.moveTo(-400, 1780); ctx.bezierCurveTo(200, 1770, 700, 1790, 1480, 1772); ctx.lineTo(1480, 2400); ctx.lineTo(-400, 2400); ctx.closePath();
  ctx.fillStyle = '#0b0912'; ctx.fill();
  ctx.beginPath(); ctx.moveTo(-400, 1780); ctx.bezierCurveTo(200, 1770, 700, 1790, 1480, 1772); ctx.strokeStyle = '#4a4058'; ctx.lineWidth = 14; ctx.stroke();
  for (const [x, y, r] of [[200, 1880, 10], [640, 1900, 8], [880, 1870, 9]]) { const g = ctx.createRadialGradient(x, y, 1, x, y, r * 4); g.addColorStop(0, 'rgba(255,170,70,0.8)'); g.addColorStop(1, 'rgba(255,140,40,0)'); ctx.fillStyle = g; ctx.beginPath(); ellipse(ctx, x, y, r * 4, r * 4); ctx.fill(); }
  if (chars.front) chars.front();
  layer(ctx, view, 1.1);
  drawPumpkin(ctx, { x: 990, y: 1690, r: 52, face: 'patch', lit: 1, t });
}

module.exports = { layer, drawHill, drawAttic, drawRoof };
