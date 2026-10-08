// Environments and props. Everything is flat shapes so the video compresses well.
const U = require('./util');
const { W, H, TAU, clamp, lerp, prog, ease, hash, noise, circle, ellipse, fillRR, rrect, line, text, rgba, mix, vgrad, rgrad } = U;
const C = require('./characters');

// ---------- night living room (wide shot coordinates) ----------
function rain(ctx, x, y, w, h, t, amount = 1, seed = 3) {
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip();
  ctx.strokeStyle = 'rgba(170,195,235,0.35)'; ctx.lineWidth = 2.2; ctx.lineCap = 'round';
  const n = Math.round(46 * amount);
  ctx.beginPath();
  for (let i = 0; i < n; i++) {
    const sx = x + hash(i * 3.1 + seed) * w, sp = 900 + hash(i * 7.7) * 500;
    const yy = y + ((hash(i * 1.3 + seed) * h + t * sp) % (h + 80)) - 40;
    ctx.moveTo(sx, yy); ctx.lineTo(sx - 7, yy + 34);
  }
  ctx.stroke(); ctx.restore();
}

function nightRoom(ctx, t, o = {}) {
  const lamp = o.lamp || 0;
  ctx.fillStyle = vgrad(ctx, 0, 1500, ['#1c233b', '#29304d']); ctx.fillRect(0, 0, W, 1500);
  ctx.fillStyle = '#171a2a'; ctx.fillRect(0, 1500, W, 420);
  // window
  fillRR(ctx, 104, 294, 432, 572, 14, '#3a4166');
  ctx.fillStyle = vgrad(ctx, 310, 850, ['#0d1730', '#1f3157']); ctx.fillRect(120, 310, 400, 540);
  for (let i = 0; i < 16; i++) {
    const bx = 130 + hash(i * 4.3) * 380, by = 640 + hash(i * 9.1) * 200, r = 10 + hash(i * 2.2) * 18;
    const c = ['#ffcf7a', '#ff9f80', '#9fd0ff', '#ffe6a8'][i % 4];
    circle(ctx, bx, by, r, rgba(c, 0.18 + 0.1 * Math.sin(t * 0.8 + i)));
  }
  // building silhouettes
  ctx.fillStyle = '#121a30';
  [[120, 720, 90], [215, 680, 70], [290, 740, 110], [405, 700, 115]].forEach(([bx, by, bw]) => ctx.fillRect(bx, by, bw, 850 - by));
  for (let i = 0; i < 18; i++) { const wx = 135 + (i % 6) * 64, wy = 735 + Math.floor(i / 6) * 34; if (hash(i * 5.5) > 0.45) ctx.fillStyle = rgba('#ffd98a', 0.55), ctx.fillRect(wx, wy, 12, 14); }
  rain(ctx, 120, 310, 400, 540, t, o.rain == null ? 1 : o.rain);
  ctx.fillStyle = '#3a4166'; ctx.fillRect(316, 310, 8, 540); ctx.fillRect(120, 576, 400, 8);
  // curtain
  ctx.fillStyle = '#4a3f6e';
  ctx.beginPath(); ctx.moveTo(80, 270); ctx.lineTo(190, 270); ctx.quadraticCurveTo(150 + Math.sin(t * 0.7) * 6, 600, 200, 930); ctx.lineTo(80, 930); ctx.closePath(); ctx.fill();
  fillRR(ctx, 70, 258, 500, 18, 9, '#2c2f4a');
  // clock
  const cx = 840, cy = 430;
  circle(ctx, cx, cy, 76, '#2c2f4a'); circle(ctx, cx, cy, 64, mix('#d9d3c7', '#ffe2a8', lamp * 0.3));
  for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; line(ctx, cx + Math.cos(a) * 52, cy + Math.sin(a) * 52, cx + Math.cos(a) * 58, cy + Math.sin(a) * 58, '#55505e', 4); }
  const mins = o.clockMin == null ? 47 : o.clockMin, hrs = 11 + mins / 60;
  const ha = hrs / 12 * TAU - Math.PI / 2, ma = mins / 60 * TAU - Math.PI / 2;
  line(ctx, cx, cy, cx + Math.cos(ha) * 30, cy + Math.sin(ha) * 30, '#2a2630', 7);
  line(ctx, cx, cy, cx + Math.cos(ma) * 46, cy + Math.sin(ma) * 46, '#2a2630', 5);
  circle(ctx, cx, cy, 6, '#c4553f');
  // shelf + books
  fillRR(ctx, 660, 640, 330, 16, 6, '#3d3557');
  [['#6b5b95', 34, 92], ['#b56576', 28, 80], ['#e0a96d', 40, 100], ['#577590', 30, 86], ['#6d597a', 26, 70]].reduce((x, [c, bw, bh]) => { fillRR(ctx, x, 640 - bh, bw, bh, 4, rgba(c, 0.8)); return x + bw + 6; }, 690);
  circle(ctx, 940, 610, 26, '#4c6e5d'); fillRR(ctx, 920, 610, 40, 30, 6, '#7a5c4c');
  // lamp
  fillRR(ctx, 926, 960, 10, 560, 5, '#2e2a40');
  fillRR(ctx, 880, 1510, 100, 18, 9, '#2e2a40');
  ctx.beginPath(); ctx.moveTo(870, 980); ctx.lineTo(990, 980); ctx.lineTo(960, 890); ctx.lineTo(900, 890); ctx.closePath();
  ctx.fillStyle = lamp > 0 ? mix('#5b5170', '#ffd58f', lamp) : '#5b5170'; ctx.fill();
  // couch (back + arms)
  fillRR(ctx, 60, 1110, 960, 330, 70, '#4a3d6a');
  fillRR(ctx, 110, 1140, 330, 230, 50, '#56497a'); fillRR(ctx, 640, 1140, 330, 230, 50, '#56497a');
}
function couchFront(ctx, o = {}) {
  // blanket on lap + seat front + couch arms (drawn over the sitter)
  fillRR(ctx, 30, 1260, 150, 380, 60, '#43375f'); fillRR(ctx, 900, 1260, 150, 380, 60, '#43375f');
  fillRR(ctx, 120, 1520, 840, 150, 40, '#3c3157');
  // knitted blanket draped over the knees (two soft bumps), with a fringe
  ctx.save();
  ctx.beginPath(); ctx.moveTo(240, 1660); ctx.bezierCurveTo(230, 1520, 300, 1446, 420, 1452);
  ctx.bezierCurveTo(480, 1455, 510, 1478, 540, 1480); ctx.bezierCurveTo(570, 1478, 600, 1455, 660, 1452);
  ctx.bezierCurveTo(780, 1446, 850, 1520, 840, 1660); ctx.closePath();
  ctx.fillStyle = o.blanket || '#b8645a'; ctx.fill(); ctx.clip();
  for (let i = 0; i < 6; i++) { ctx.fillStyle = 'rgba(255,230,200,0.20)'; ctx.fillRect(200, 1500 + i * 30, 700, 9); }
  for (let i = 0; i < 9; i++) { ctx.beginPath(); ctx.moveTo(300 + i * 60, 1460); ctx.lineTo(310 + i * 60, 1660); ctx.strokeStyle = 'rgba(80,30,30,0.12)'; ctx.lineWidth = 3; ctx.stroke(); }
  ctx.restore();
  ctx.fillStyle = '#171a2a'; ctx.fillRect(0, 1660, W, 260);
}
function lampLight(ctx, amt) {
  if (amt <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = rgrad(ctx, 930, 960, 760, [[0, rgba('#ffb85c', 0.55 * amt)], [0.5, rgba('#ff9f4a', 0.18 * amt)], [1, rgba('#ff9f4a', 0)]]);
  ctx.fillRect(0, 0, W, H); ctx.restore();
}
function phoneGlow(ctx, x, y, amt, color = '#8fb8ff', r = 520) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.fillStyle = rgrad(ctx, x, y, r, [[0, rgba(color, 0.42 * amt)], [0.55, rgba(color, 0.12 * amt)], [1, rgba(color, 0)]]);
  ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.restore();
}
function vignette(ctx, amt = 0.5) {
  ctx.fillStyle = rgrad(ctx, W / 2, H * 0.45, H * 0.75, [[0.55, 'rgba(0,0,0,0)'], [1, `rgba(5,6,15,${amt})`]]);
  ctx.fillRect(0, 0, W, H);
}

// ---------- big "zoomed phone screen" panel ----------
function phonePanel(ctx, x, y, w, h, t, draw, o = {}) {
  fillRR(ctx, x - 14, y - 14, w + 28, h + 28, 64, '#0b0c12');
  ctx.save(); rrect(ctx, x, y, w, h, 52); ctx.clip();
  ctx.fillStyle = o.bg || '#14161f'; ctx.fillRect(x, y, w, h);
  draw(x, y, w, h);
  // status bar
  ctx.fillStyle = o.bg || '#14161f'; ctx.fillRect(x, y, w, 64);
  text(ctx, o.clock || '11:47', x + 64, y + 36, { size: 28, weight: 800, color: '#cfd3e0', align: 'left' });
  const bl = o.battery == null ? 0.12 : o.battery;
  fillRR(ctx, x + w - 112, y + 22, 54, 26, 7, '#545a6e'); fillRR(ctx, x + w - 108, y + 26, 46 * bl, 18, 4, bl < 0.2 ? '#ff6b5e' : '#cfd3e0'); fillRR(ctx, x + w - 56, y + 30, 5, 10, 2, '#545a6e');
  ctx.restore();
}

const FEED = [
  { kind: 'ad', title: 'LIMITED TIME!!', sub: 'buy the thing. be happy.', col: '#3b3550' },
  { kind: 'list', title: '10 hacks to be MORE productive', sub: '#grind #hustle', col: '#2e3446' },
  { kind: 'cat', title: 'cat doing absolutely nothing', sub: '2.1M likes', col: '#33364a' },
  { kind: 'news', title: 'Everything costs more again', sub: 'breaking', col: '#3a2f3a' },
  { kind: 'selfie', title: 'living my best life ✨', sub: 'sponsored', col: '#30384a' },
  { kind: 'list', title: 'Wake up at 4am. Here is why.', sub: '#mindset', col: '#2e3446' },
  { kind: 'ad', title: 'You deserve this. ($89.99)', sub: 'shop now', col: '#3b3550' },
];
function feedCard(ctx, x, y, w, item, t) {
  const h = 330;
  fillRR(ctx, x, y, w, h, 28, '#1f2230');
  circle(ctx, x + 50, y + 48, 22, '#3d4257'); fillRR(ctx, x + 86, y + 34, 160, 14, 7, '#3d4257'); fillRR(ctx, x + 86, y + 56, 90, 10, 5, '#2f3346');
  fillRR(ctx, x + 24, y + 88, w - 48, 170, 20, item.col);
  const cx = x + w / 2, cy = y + 173;
  if (item.kind === 'cat') { ellipse(ctx, cx, cy + 30, 70, 34, '#565a72'); circle(ctx, cx - 60, cy + 4, 30, '#565a72'); ctx.fillStyle = '#565a72'; ctx.beginPath(); ctx.moveTo(cx - 84, cy - 14); ctx.lineTo(cx - 76, cy - 40); ctx.lineTo(cx - 62, cy - 22); ctx.moveTo(cx - 56, cy - 22); ctx.lineTo(cx - 42, cy - 40); ctx.lineTo(cx - 38, cy - 12); ctx.fill(); line(ctx, cx - 70, cy + 4, cx - 64, cy + 4, '#2a2c3a', 3); line(ctx, cx - 54, cy + 4, cx - 48, cy + 4, '#2a2c3a', 3); }
  else if (item.kind === 'selfie') { circle(ctx, cx, cy - 10, 40, '#5d6178'); ellipse(ctx, cx, cy + 70, 70, 40, '#5d6178'); }
  else if (item.kind === 'news') { text(ctx, '$$$', cx, cy, { size: 80, weight: 900, color: '#5e4a5a' }); }
  else if (item.kind === 'ad') { text(ctx, '%', cx, cy, { size: 110, weight: 900, color: '#5a5276' }); }
  else { for (let i = 0; i < 4; i++) fillRR(ctx, x + 60, cy - 55 + i * 34, w - 160 - i * 40, 16, 8, '#46506a'); }
  text(ctx, item.title, x + 30, y + 286, { size: 30, weight: 800, color: '#a9aec2', align: 'left' });
  text(ctx, item.sub, x + 30, y + 314, { size: 20, weight: 700, color: '#646a82', align: 'left' });
  return h;
}

function keyboard(ctx, x, y, w, h, t, typing) {
  fillRR(ctx, x, y, w, h, 0, '#1b1d27');
  const rows = [10, 9, 7];
  const kw = (w - 40) / 10, kh = (h - 120) / 4;
  rows.forEach((n, r) => {
    for (let i = 0; i < n; i++) {
      const kx = x + 20 + (10 - n) * kw / 2 + i * kw, ky = y + 18 + r * (kh + 8);
      const lit = typing && hash(Math.floor(t * 12) * 13 + r * 10 + i) > 0.93;
      fillRR(ctx, kx + 4, ky, kw - 8, kh, 10, lit ? '#6a7090' : '#353849');
    }
  });
  fillRR(ctx, x + 20 + kw * 2, y + 18 + 3 * (kh + 8), kw * 6 - 8, kh, 10, '#353849');
}

function notification(ctx, x, y, w, t0, t, tOut = Infinity) {
  const k = Math.min(ease.back(prog(t, t0, t0 + 0.5)), 1 - ease.in(prog(t, tOut, tOut + 0.35)));
  if (k <= 0) return;
  const yy = lerp(y - 160, y, k);
  fillRR(ctx, x, yy, w, 150, 34, '#2b2f40');
  circle(ctx, x + 75, yy + 75, 44, '#ffe0b0');
  C.drawPerson(ctx, 'alex', { x: x + 75, y: yy + 80, s: 0.36, t, noBody: true, smile: 0.4, lids: 0.9, seed: 3 });
  text(ctx, 'alex replied to your comment', x + 140, yy + 52, { size: 30, weight: 800, color: '#e9ebf3', align: 'left' });
  text(ctx, '"Hey. I saw your comment..."', x + 140, yy + 98, { size: 28, weight: 600, color: '#9ea5bd', align: 'left' });
}

// ---------- warm "explainer" world ----------
function warmBG(ctx, t, tint = '#fbf1e1') {
  ctx.fillStyle = tint; ctx.fillRect(0, 0, W, H);
  const blobs = [[160, 520, 260, '#f6e2c4'], [940, 380, 220, '#f9dccb'], [880, 1180, 300, '#f4e6cf'], [140, 1500, 280, '#f7dfc8']];
  blobs.forEach(([x, y, r, c], i) => circle(ctx, x + Math.sin(t * 0.25 + i) * 20, y + Math.cos(t * 0.21 + i * 2) * 16, r, c));
}
function stepTitle(ctx, n, title, t, t0) {
  const k = ease.back(prog(t, t0, t0 + 0.55));
  if (k <= 0) return;
  ctx.save(); ctx.translate(W / 2, 268); ctx.scale(k, k);
  U.font(ctx, 54, 700, U.FONTS.title);
  const tw = ctx.measureText(title).width;
  const w = tw + 190;
  fillRR(ctx, -w / 2, -52, w, 104, 52, '#2d2a3e');
  circle(ctx, -w / 2 + 52, 0, 38, '#ffb347');
  text(ctx, String(n), -w / 2 + 52, 3, { size: 50, weight: 700, family: U.FONTS.title, color: '#2d2a3e' });
  text(ctx, title, -w / 2 + 110, 3, { size: 54, weight: 600, family: U.FONTS.title, color: '#fff7ea', align: 'left' });
  ctx.restore();
}

function lightbulb(ctx, x, y, s, on, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  if (on > 0) {
    ctx.fillStyle = rgrad(ctx, 0, -20, 240, [[0, rgba('#ffd66b', 0.7 * on)], [1, rgba('#ffd66b', 0)]]); ctx.fillRect(-240, -260, 480, 480);
    for (let i = 0; i < 10; i++) {
      const a = i / 10 * TAU + t * 0.3, r1 = 140, r2 = 175 + Math.sin(t * 4 + i) * 10;
      line(ctx, Math.cos(a) * r1, -20 + Math.sin(a) * r1, Math.cos(a) * r2, -20 + Math.sin(a) * r2, rgba('#f4a62a', on), 9);
    }
  }
  circle(ctx, 0, -20, 105, mix('#e6e1d6', '#ffe28a', on));
  ctx.beginPath(); ctx.moveTo(-34, 30); ctx.quadraticCurveTo(-20, -40, 0, -20); ctx.quadraticCurveTo(20, -40, 34, 30);
  ctx.strokeStyle = mix('#b8b0a0', '#f08c1a', on); ctx.lineWidth = 7; ctx.stroke();
  fillRR(ctx, -48, 70, 96, 26, 10, '#8d8a99'); fillRR(ctx, -42, 98, 84, 22, 10, '#77748a'); fillRR(ctx, -26, 122, 52, 18, 9, '#5d5a70');
  ctx.restore();
}

function thought(ctx, x, y, w, h, k, tailTo) {
  if (k <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(k, k);
  fillRR(ctx, -w / 2, -h / 2, w, h, Math.min(w, h) / 2.2, '#ffffff');
  ctx.restore();
  if (tailTo) { const [tx, ty] = tailTo; circle(ctx, lerp(x, tx, 0.55), lerp(y + h / 2 * k, ty, 0.55), 16 * k, '#fff'); circle(ctx, lerp(x, tx, 0.8), lerp(y + h / 2 * k, ty, 0.8), 10 * k, '#fff'); }
}

function polaroid(ctx, x, y, s, t, rot = 0, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.fillStyle = 'rgba(0,0,0,0.12)'; rrect(ctx, -146, -166, 300, 348, 10); ctx.fill();
  fillRR(ctx, -150, -175, 300, 350, 10, '#fffdf8');
  ctx.save(); ctx.beginPath(); ctx.rect(-130, -155, 260, 250); ctx.clip();
  ctx.fillStyle = '#f6d9a5'; ctx.fillRect(-130, -155, 260, 250);
  fillRR(ctx, -110, -140, 90, 90, 6, '#bfe3f2');
  C.drawPerson(ctx, 'grandma', { x: 45, y: -30, s: 0.5, t, smile: 0.6, squint: 0.4, lids: 0.7, arms: 'down', gx: -0.6, gy: 0.3, seed: 8 });
  C.drawPerson(ctx, 'kid', { x: -55, y: 15, s: 0.38, t, smile: 0.5, lids: 1, gx: 0.6, gy: -0.5, seed: 4 });
  fillRR(ctx, -130, 60, 260, 40, 0, '#c98f5a');
  for (let i = 0; i < 4; i++) dumpling(ctx, -70 + i * 45, 62, 0.45, 1);
  ctx.restore();
  text(ctx, o.label || 'grandma + me', 0, 140, { size: 34, family: U.FONTS.hand, weight: 400, color: '#5b4a3f' });
  ctx.restore();
}

function dumpling(ctx, x, y, s, fold = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  if (fold < 1) {
    ellipse(ctx, 0, 0, 44, 44 * lerp(1, 0.55, fold), '#f7efe0');
    ellipse(ctx, 0, 0, 18, 18 * lerp(1, 0.5, fold), rgba('#c98b6b', 1 - fold));
  }
  if (fold > 0) {
    ctx.globalAlpha *= clamp(fold * 1.5);
    ctx.beginPath(); ctx.moveTo(-44, 10); ctx.quadraticCurveTo(0, -48, 44, 10); ctx.quadraticCurveTo(0, 24, -44, 10); ctx.closePath();
    ctx.fillStyle = '#f7efe0'; ctx.fill(); ctx.strokeStyle = '#dccbb0'; ctx.lineWidth = 3; ctx.stroke();
    for (let i = -2; i <= 2; i++) line(ctx, i * 12, -16 + Math.abs(i) * 4, i * 12 + 4, -4 + Math.abs(i) * 4, '#d9c6a6', 3);
  }
  ctx.restore();
}

function heartCloud(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  [[-40, 0, 46], [10, -22, 54], [56, 4, 42], [0, 18, 50]].forEach(([cx, cy, r]) => circle(ctx, cx, cy, r, '#9bb4d6'));
  for (let i = 0; i < 4; i++) line(ctx, -40 + i * 28, 72 + ((t * 120 + i * 30) % 50), -46 + i * 28, 90 + ((t * 120 + i * 30) % 50), '#7aa0d4', 5);
  ctx.translate(8, -4); ctx.scale(0.5, 0.5);
  ctx.beginPath(); ctx.moveTo(0, 30); ctx.bezierCurveTo(-60, -10, -30, -60, 0, -28); ctx.bezierCurveTo(30, -60, 60, -10, 0, 30); ctx.fillStyle = '#ff7b8a'; ctx.fill();
  ctx.restore();
}
function catAstronaut(ctx, x, y, s, t) {
  ctx.save(); ctx.translate(x, y + Math.sin(t * 2) * 8); ctx.rotate(Math.sin(t * 0.8) * 0.15); ctx.scale(s, s);
  fillRR(ctx, -40, 20, 80, 70, 24, '#e9e6f2');
  circle(ctx, 0, -10, 58, rgba('#bfe6ff', 0.65)); circle(ctx, 0, -6, 40, '#f2a65a');
  ctx.fillStyle = '#f2a65a'; ctx.beginPath(); ctx.moveTo(-34, -24); ctx.lineTo(-28, -56); ctx.lineTo(-10, -38); ctx.moveTo(34, -24); ctx.lineTo(28, -56); ctx.lineTo(10, -38); ctx.fill();
  circle(ctx, -14, -8, 5, '#2a1a14'); circle(ctx, 14, -8, 5, '#2a1a14'); ellipse(ctx, 0, 4, 5, 3, '#e8706a');
  ctx.beginPath(); ctx.arc(0, -10, 58, 0, TAU); ctx.strokeStyle = '#c9c4da'; ctx.lineWidth = 7; ctx.stroke();
  circle(ctx, 22, -34, 10, 'rgba(255,255,255,0.7)');
  ctx.restore();
}

function socialPost(ctx, x, y, w, t, who = '@someone', msg = ['my dad used to whistle while he cooked.', 'some days I can still hear it.']) {
  fillRR(ctx, x, y, w, 200, 30, '#ffffff');
  circle(ctx, x + 56, y + 56, 30, '#9ec5a8'); circle(ctx, x + 56, y + 48, 12, '#5d8a6a'); ellipse(ctx, x + 56, y + 72, 18, 10, '#5d8a6a');
  text(ctx, who, x + 102, y + 56, { size: 32, weight: 800, color: '#333', align: 'left' });
  msg.forEach((m, i) => text(ctx, m, x + 36, y + 120 + i * 42, { size: 34, weight: 600, color: '#444', align: 'left' }));
}

function sparkle(ctx, x, y, r, color = '#ffc94d', rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  ctx.beginPath();
  for (let i = 0; i < 8; i++) { const a = i / 8 * TAU, rr = i % 2 ? r * 0.3 : r; ctx.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
  ctx.closePath(); ctx.fillStyle = color; ctx.fill(); ctx.restore();
}
function check(ctx, x, y, s, k = 1, color = '#3fb37f') {
  if (k <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s * k, s * k);
  circle(ctx, 0, 0, 40, color);
  ctx.beginPath(); ctx.moveTo(-18, 2); ctx.lineTo(-5, 16); ctx.lineTo(20, -14); ctx.strokeStyle = '#fff'; ctx.lineWidth = 10; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
  ctx.restore();
}
function note(ctx, x, y, s, color = '#6c5ce7') {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  ellipse(ctx, 0, 0, 16, 12, color, -0.4); ellipse(ctx, 38, -10, 16, 12, color, -0.4);
  ctx.fillStyle = color; ctx.fillRect(12, -70, 6, 70); ctx.fillRect(50, -80, 6, 70);
  ctx.beginPath(); ctx.moveTo(12, -70); ctx.lineTo(56, -80); ctx.lineTo(56, -64); ctx.lineTo(12, -54); ctx.fill();
  ctx.restore();
}

// ---------- chat + terminal windows ----------
function chatWindow(ctx, x, y, w, h, title = 'Chat') {
  ctx.fillStyle = 'rgba(60,40,20,0.10)'; rrect(ctx, x + 6, y + 10, w, h, 36); ctx.fill();
  fillRR(ctx, x, y, w, h, 36, '#ffffff');
  ctx.save(); rrect(ctx, x, y, w, h, 36); ctx.clip();
  ctx.fillStyle = '#f3eefc'; ctx.fillRect(x, y, w, 92);
  ctx.restore();
  C.drawBot(ctx, x + 60, y + 48, 0.3, 0, { still: true });
  text(ctx, title, x + 104, y + 48, { size: 34, weight: 800, color: '#3b3355', align: 'left' });
}
function bubble(ctx, x, y, w, lines, o = {}) {
  U.font(ctx, o.size || 34, o.weight || 650, o.family || U.FONTS.ui);
  const lh = (o.size || 34) * 1.32, h = lines.length * lh + 40;
  fillRR(ctx, x, y, w, h, 28, o.bg || '#3e8c98');
  ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillStyle = o.color || '#fff';
  lines.forEach((l, i) => ctx.fillText(l, x + 26, y + 20 + i * lh));
  return h;
}
function typingDots(ctx, x, y, t) {
  fillRR(ctx, x, y, 140, 70, 35, '#efeaff');
  for (let i = 0; i < 3; i++) circle(ctx, x + 40 + i * 30, y + 35 - Math.max(0, Math.sin(t * 8 - i * 0.8)) * 9, 9, '#8f7cf7');
}
function termWindow(ctx, x, y, w, h, title) {
  ctx.fillStyle = 'rgba(0,0,0,0.18)'; rrect(ctx, x + 6, y + 12, w, h, 30); ctx.fill();
  fillRR(ctx, x, y, w, h, 30, '#1f1b2e');
  ctx.save(); rrect(ctx, x, y, w, h, 30); ctx.clip(); ctx.fillStyle = '#2b2640'; ctx.fillRect(x, y, w, 64); ctx.restore();
  ['#ff6b6b', '#ffd166', '#06d6a0'].forEach((c, i) => circle(ctx, x + 40 + i * 34, y + 32, 11, c));
  if (title) text(ctx, title, x + w / 2 + 30, y + 33, { size: 26, weight: 700, color: '#a9a2c8', family: U.FONTS.mono });
}
const CODE = [
  [['const ', '#c792ea'], ['grandma', '#82aaff'], [' = drawPerson({', '#d6deeb']],
  [['  hair: ', '#d6deeb'], ['"silver bun"', '#c3e88d'], [',', '#d6deeb']],
  [['  smile: ', '#d6deeb'], ['0.7', '#f78c6c'], [', eyes: ', '#d6deeb'], ['"kind"', '#c3e88d']],
  [['});', '#d6deeb']],
  [['voice', '#82aaff'], ['(', '#d6deeb'], ['"Gently..."', '#c3e88d'], [')', '#d6deeb']],
  [['music', '#82aaff'], ['({ mood: ', '#d6deeb'], ['"warm"', '#c3e88d'], [' })', '#d6deeb']],
  [['scene', '#82aaff'], ['(', '#d6deeb'], ['"kitchen"', '#c3e88d'], [', steam: ', '#d6deeb'], ['true', '#f78c6c'], [')', '#d6deeb']],
  [['render', '#ffcb6b'], ['(', '#d6deeb'], ['"dumpling_lesson.mp4"', '#c3e88d'], [')', '#d6deeb']],
];
function codeLines(ctx, x, y, n, size = 30, charsShown = Infinity) {
  U.font(ctx, size, 500, U.FONTS.mono); ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  let budget = charsShown;
  for (let i = 0; i < Math.min(n, CODE.length); i++) {
    let cx = x;
    for (const [s, c] of CODE[i]) {
      if (budget <= 0) return;
      const part = s.slice(0, Math.max(0, budget)); budget -= s.length;
      ctx.fillStyle = c; ctx.fillText(part, cx, y + i * size * 1.5); cx += ctx.measureText(s).width;
    }
  }
}
function waveform(ctx, x, y, w, h, t, amp = 1, color = '#ff8fa3') {
  const n = 22, bw = w / n;
  for (let i = 0; i < n; i++) {
    const v = (0.25 + 0.75 * Math.abs(noise(t * 6 + i * 0.7, 2))) * amp;
    fillRR(ctx, x + i * bw + 3, y - v * h / 2, bw - 6, Math.max(6, v * h), 4, color);
  }
}
function filmStrip(ctx, x, y, w, h, frames, t) {
  fillRR(ctx, x, y, w, h, 12, '#2d2a3e');
  for (let i = 0; i < Math.floor(w / 36); i++) { fillRR(ctx, x + 10 + i * 36, y + 8, 20, 14, 3, '#fff7ea'); fillRR(ctx, x + 10 + i * 36, y + h - 22, 20, 14, 3, '#fff7ea'); }
  const fw = (w - 20) / frames.length;
  frames.forEach((c, i) => fillRR(ctx, x + 10 + i * fw + 6, y + 30, fw - 12, h - 60, 8, c));
}
function fileCard(ctx, x, y, s, name, k) {
  if (k <= 0) return;
  ctx.save(); ctx.translate(x, y); ctx.scale(s * k, s * k);
  fillRR(ctx, -170, -110, 340, 220, 26, '#ffffff');
  fillRR(ctx, -140, -84, 120, 120, 18, '#ffb347');
  ctx.beginPath(); ctx.moveTo(-98, -50); ctx.lineTo(-98, 2); ctx.lineTo(-56, -24); ctx.closePath(); ctx.fillStyle = '#fff'; ctx.fill();
  text(ctx, name, 0, 70, { size: 26, weight: 800, color: '#3b3355', family: U.FONTS.mono });
  fillRR(ctx, 4, -70, 130, 16, 8, '#e6e0f5'); fillRR(ctx, 4, -40, 100, 16, 8, '#e6e0f5'); fillRR(ctx, 4, -10, 116, 16, 8, '#e6e0f5');
  ctx.restore();
}

// ---------- kitchen (Riley's video) ----------
function kitchen(ctx, t, o = {}) {
  ctx.fillStyle = vgrad(ctx, 0, 1300, ['#f8e2b6', '#f3d39c']); ctx.fillRect(0, 0, W, 1300);
  // window with daylight
  fillRR(ctx, 96, 230, 470, 560, 20, '#e7c48a');
  ctx.fillStyle = vgrad(ctx, 250, 770, ['#a9dcf2', '#d9f0f7']); ctx.fillRect(116, 250, 430, 520);
  circle(ctx, 450, 350, 60, '#fff6c9');
  [[160, 640, 120], [300, 600, 150], [420, 650, 140]].forEach(([x, y, r]) => circle(ctx, x, y + 120, r, '#9fd18b'));
  ctx.fillStyle = '#e7c48a'; ctx.fillRect(326, 250, 12, 520); ctx.fillRect(116, 500, 430, 12);
  // curtains
  ctx.fillStyle = '#e98c7a'; ctx.beginPath(); ctx.moveTo(80, 210); ctx.lineTo(220, 210); ctx.quadraticCurveTo(170, 420, 120, 560); ctx.lineTo(80, 560); ctx.fill();
  ctx.beginPath(); ctx.moveTo(582, 210); ctx.lineTo(442, 210); ctx.quadraticCurveTo(492, 420, 542, 560); ctx.lineTo(582, 560); ctx.fill();
  // tiles
  ctx.fillStyle = '#f1cf93';
  for (let r = 0; r < 4; r++) for (let c = 0; c < 12; c++) if ((r + c) % 2 === 0) ctx.fillRect(c * 92, 940 + r * 92, 92, 92);
  // shelf with jars
  fillRR(ctx, 650, 380, 360, 18, 8, '#b98657');
  [['#e76f51', 60], ['#2a9d8f', 50], ['#e9c46a', 70], ['#8ab17d', 54]].reduce((x, [c, h]) => { fillRR(ctx, x, 380 - h, 56, h, 10, c); fillRR(ctx, x + 6, 380 - h - 12, 44, 14, 5, '#7a5a40'); return x + 80; }, 670);
  // hanging plant
  line(ctx, 900, 0, 900, 150, '#8a6a50', 4); fillRR(ctx, 860, 150, 80, 60, 16, '#d17a55');
  for (let i = 0; i < 5; i++) ellipse(ctx, 870 + i * 15, 220 + (i % 2) * 30, 14, 34, '#6fa86b', 0.3 * (i - 2));
  // sunbeam
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.beginPath(); ctx.moveTo(120, 260); ctx.lineTo(560, 260); ctx.lineTo(1080, 1300); ctx.lineTo(520, 1300); ctx.closePath();
  ctx.fillStyle = 'rgba(255,240,190,0.18)'; ctx.fill(); ctx.restore();
  // stove + pot + steam
  fillRR(ctx, 800, 1180, 240, 40, 8, '#4a4a55');
  fillRR(ctx, 830, 1070, 180, 120, 26, '#7c8a96'); fillRR(ctx, 815, 1060, 210, 24, 12, '#5f6b76');
  for (let i = 0; i < 5; i++) {
    const p = ((t * 0.35 + i * 0.2) % 1), sx = 900 + i * 18 + Math.sin(t * 1.5 + i * 2) * 30 * p;
    circle(ctx, sx, 1040 - p * 420, 24 + p * 46, `rgba(255,255,255,${0.45 * (1 - p)})`);
  }
  // people behind counter
  const gm = o.grandma || {};
  C.drawPerson(ctx, 'grandma', Object.assign({ x: 660, y: 830, s: 1.18, t, arms: 'counter', seed: 8, lids: 0.75, smile: 0.5, gx: -0.5, gy: 0.4 }, gm));
  const kd = o.kid || {};
  C.drawPerson(ctx, 'kid', Object.assign({ x: 300, y: 1040, s: 0.9, t, arms: 'counter', seed: 4, lids: 1, smile: 0.3, gx: 0.7, gy: -0.5 }, kd));
  // counter
  ctx.fillStyle = '#c98f5a'; ctx.fillRect(0, 1290, W, 40);
  ctx.fillStyle = '#a8714a'; ctx.fillRect(0, 1330, W, 590);
  for (let i = 0; i < 4; i++) { fillRR(ctx, 30 + i * 265, 1380, 235, 420, 18, '#b57c52'); fillRR(ctx, 125 + i * 265, 1420, 50, 14, 7, '#e8c49a'); }
  // flour + tray of dumplings
  ellipse(ctx, 520, 1300, 170, 18, 'rgba(255,255,255,0.55)');
  fillRR(ctx, 140, 1262, 260, 40, 14, '#e2d5c0');
  for (let i = 0; i < 4; i++) dumpling(ctx, 180 + i * 60, 1268, 0.6, 1);
  if (o.extra) o.extra(ctx);
}

// ---------- montage panels ----------
function photoFrame(ctx, x, y, w, h, rot, draw, label) {
  ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.rotate(rot); ctx.translate(-w / 2, -h / 2);
  ctx.fillStyle = 'rgba(0,0,0,0.18)'; rrect(ctx, 10, 16, w, h, 18); ctx.fill();
  fillRR(ctx, 0, 0, w, h, 18, '#fbf7f0');
  ctx.save(); rrect(ctx, 22, 22, w - 44, h - 110, 10); ctx.clip(); ctx.translate(22, 22); draw(w - 44, h - 110); ctx.restore();
  if (label) text(ctx, label, w / 2, h - 46, { size: 46, family: U.FONTS.hand, weight: 400, color: '#4a4048' });
  ctx.restore();
}
function battery(ctx, x, y, s, level, t, label = true) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  fillRR(ctx, -130, -55, 260, 110, 24, '#2d2a3e'); fillRR(ctx, 130, -22, 22, 44, 8, '#2d2a3e');
  const low = level < 0.15, blinkOn = !low || Math.floor(t * 3) % 2 === 0;
  const col = level > 0.5 ? '#5cc98a' : level > 0.2 ? '#ffc04d' : '#ff5e57';
  if (blinkOn) fillRR(ctx, -116, -41, Math.max(16, 232 * level), 82, 14, col);
  if (label) text(ctx, Math.round(level * 100) + '%', 0, 2, { size: 52, weight: 900, color: '#ffffff' });
  ctx.restore();
}
function envelope(ctx, x, y, rot, label, color = '#d64545') {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot);
  fillRR(ctx, -110, -66, 220, 132, 10, '#fffaf0');
  ctx.beginPath(); ctx.moveTo(-110, -66); ctx.lineTo(0, 10); ctx.lineTo(110, -66); ctx.strokeStyle = '#d8cdb8'; ctx.lineWidth = 4; ctx.stroke();
  ctx.save(); ctx.rotate(-0.12); fillRR(ctx, -92, 10, 184, 46, 8, color); text(ctx, label, 0, 34, { size: 30, weight: 900, color: '#fff' }); ctx.restore();
  ctx.restore();
}
function wallClock(ctx, x, y, r, hourA, minA) {
  circle(ctx, x, y, r + 10, '#4a4458'); circle(ctx, x, y, r, '#fbf7f0');
  line(ctx, x, y, x + Math.cos(hourA) * r * 0.5, y + Math.sin(hourA) * r * 0.5, '#2d2a3e', 9);
  line(ctx, x, y, x + Math.cos(minA) * r * 0.8, y + Math.sin(minA) * r * 0.8, '#2d2a3e', 6);
  circle(ctx, x, y, 8, '#e76f51');
}

// ---------- style tiles ----------
function pixelSprite(ctx, x, y, px, t) {
  const blink = Math.floor(t * 1.2) % 4 === 0 && (t * 1.2) % 1 < 0.2;
  const G = [
    '..hhhhhh..', '.hhhhhhhh.', 'hhhhhhhhhh', 'hssssssssh', 'sseesseess', 'sseesseess', 'ssssssssss', 'sssmmmmsss', '.ssssssss.', '..tttttt..', '.tttttttt.', 'tttttttttt',
  ];
  const col = { h: '#2b1d17', s: '#b07650', e: blink ? '#b07650' : '#1d1410', m: '#7a3f30', t: '#3e8c98' };
  G.forEach((row, r) => [...row].forEach((c, i) => { if (c !== '.') { ctx.fillStyle = col[c]; ctx.fillRect(x + i * px, y + r * px, px, px); } }));
}
function cube3d(ctx, x, y, s, t) {
  const a = t * 0.9, b = 0.55 + Math.sin(t * 0.5) * 0.2;
  const P = [];
  for (const X of [-1, 1]) for (const Y of [-1, 1]) for (const Z of [-1, 1]) {
    let x1 = X * Math.cos(a) - Z * Math.sin(a), z1 = X * Math.sin(a) + Z * Math.cos(a);
    let y1 = Y * Math.cos(b) - z1 * Math.sin(b), z2 = Y * Math.sin(b) + z1 * Math.cos(b);
    const f = 4 / (4 + z2); P.push([x + x1 * s * f, y + y1 * s * f, z2]);
  }
  const faces = [[0, 1, 3, 2, '#ff8f6b'], [4, 5, 7, 6, '#ff8f6b'], [0, 1, 5, 4, '#ffd166'], [2, 3, 7, 6, '#ffd166'], [0, 2, 6, 4, '#8f7cf7'], [1, 3, 7, 5, '#8f7cf7']];
  faces.map((f) => ({ f, z: (P[f[0]][2] + P[f[1]][2] + P[f[2]][2] + P[f[3]][2]) / 4 }))
    .sort((p, q) => q.z - p.z)
    .forEach(({ f }) => {
      const [i, j, k, l, c] = f;
      // simple lambert-ish shading from face normal
      const ux = P[j][0] - P[i][0], uy = P[j][1] - P[i][1], vx = P[l][0] - P[i][0], vy = P[l][1] - P[i][1];
      const nz = Math.abs(ux * vy - uy * vx) / (s * s * 4);
      ctx.beginPath(); ctx.moveTo(P[i][0], P[i][1]); ctx.lineTo(P[j][0], P[j][1]); ctx.lineTo(P[k][0], P[k][1]); ctx.lineTo(P[l][0], P[l][1]); ctx.closePath();
      ctx.fillStyle = mix('#2d2a3e', c, 0.45 + 0.55 * clamp(nz)); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 3; ctx.stroke();
    });
}
function paperScene(ctx, x, y, w, h, t) {
  const layer = (c, yy, amp, ph, dy) => {
    ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.25)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 6;
    ctx.beginPath(); ctx.moveTo(x, y + h);
    for (let i = 0; i <= 8; i++) ctx.lineTo(x + i * w / 8, y + yy + Math.sin(i * 1.3 + ph) * amp + Math.sin(t * 1.2 + i) * 3 + dy);
    ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fillStyle = c; ctx.fill(); ctx.restore();
  };
  ctx.fillStyle = '#ffe9c7'; ctx.fillRect(x, y, w, h);
  ctx.save(); ctx.shadowColor = 'rgba(0,0,0,0.2)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 5; circle(ctx, x + w * 0.7, y + h * 0.3 + Math.sin(t) * 4, 44, '#ffb347'); ctx.restore();
  layer('#9cc9a0', h * 0.55, 22, 0, 0); layer('#6fae7c', h * 0.7, 18, 2, 0); layer('#4f8c63', h * 0.84, 14, 4, 0);
}

module.exports = {
  rain, nightRoom, couchFront, lampLight, phoneGlow, vignette, phonePanel, FEED, feedCard, keyboard, notification,
  warmBG, stepTitle, lightbulb, thought, polaroid, dumpling, heartCloud, catAstronaut, socialPost, sparkle, check, note,
  chatWindow, bubble, typingDots, termWindow, codeLines, CODE, waveform, filmStrip, fileCard, kitchen, photoFrame, battery,
  envelope, wallClock, pixelSprite, cube3d, paperScene,
};
