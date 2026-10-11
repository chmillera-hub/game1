// The living-room set and its lighting. World space, wide shot = 1080x1920.

const { clamp, lerp, mixColor, rgba, noise1 } = require('./core');

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

const WIN = { x: 110, y: 250, w: 330, h: 410 };

function drawWindow(ctx, L, t) {
  const { x, y, w, h } = WIN;
  const m = L.morning;
  // glass / outside
  ctx.save();
  roundRect(ctx, x, y, w, h, 6); ctx.clip();
  const g = ctx.createLinearGradient(0, y, 0, y + h);
  g.addColorStop(0, mixColor('#151c36', '#8fc4ea', m));
  g.addColorStop(1, mixColor('#27335a', '#d9eef6', m));
  ctx.fillStyle = g; ctx.fillRect(x, y, w, h);
  // distant buildings
  ctx.fillStyle = mixColor('#0f1428', '#a9b9c6', m);
  const bl = [[0, 0.62], [0.12, 0.55], [0.26, 0.7], [0.38, 0.48], [0.55, 0.6], [0.7, 0.52], [0.84, 0.66], [1.0, 0.58]];
  ctx.beginPath(); ctx.moveTo(x, y + h);
  for (let i = 0; i < bl.length - 1; i++) {
    ctx.lineTo(x + bl[i][0] * w, y + bl[i][1] * h); ctx.lineTo(x + bl[i + 1][0] * w, y + bl[i][1] * h);
  }
  ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fill();
  if (m < 0.99) {
    // lit windows in the distance
    for (let i = 0; i < 26; i++) {
      const wx = x + ((i * 53) % 300) + 10, wy = y + h * (0.62 + ((i * 29) % 30) / 100);
      ctx.fillStyle = rgba(i % 3 ? '#ffd88a' : '#9fd0ff', 0.7 * (1 - m));
      ctx.fillRect(wx, wy, 6, 8);
    }
  }
  if (m > 0.01) {
    ctx.fillStyle = rgba('#ffffff', 0.7 * m);
    for (const [cx, cy, s] of [[x + 80, y + 90, 1], [x + 240, y + 150, 0.8]]) {
      ctx.beginPath(); ctx.ellipse(cx, cy, 46 * s, 16 * s, 0, 0, 7); ctx.ellipse(cx + 30 * s, cy - 10 * s, 30 * s, 14 * s, 0, 0, 7); ctx.fill();
    }
  }
  // rain
  if (L.rain > 0.01) {
    ctx.strokeStyle = rgba('#c7d6ff', 0.32 * L.rain); ctx.lineWidth = 2; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let i = 0; i < 46; i++) {
      const sp = 900 + ((i * 97) % 400);
      const rx = x + ((i * 71.3) % w);
      const ry = y + (((t * sp + i * 137) % (h + 80)) - 40);
      ctx.moveTo(rx, ry); ctx.lineTo(rx - 5, ry + 26);
    }
    ctx.stroke();
    // drops sliding on the glass
    for (let i = 0; i < 14; i++) {
      const sp = 14 + (i % 5) * 9;
      const dx = x + 14 + ((i * 89) % (w - 28));
      const dy = y + ((t * sp + i * 61) % h);
      ctx.fillStyle = rgba('#d8e4ff', 0.45 * L.rain);
      ctx.beginPath(); ctx.ellipse(dx, dy, 3.5, 4.5, 0, 0, 7); ctx.fill();
      ctx.strokeStyle = rgba('#d8e4ff', 0.18 * L.rain); ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(dx, dy - 4); ctx.lineTo(dx + 1, dy - 22); ctx.stroke();
    }
  }
  ctx.restore();
  // frame + muntins
  ctx.strokeStyle = '#e7dfd2'; ctx.lineWidth = 16;
  roundRect(ctx, x, y, w, h, 6); ctx.stroke();
  ctx.lineWidth = 9;
  ctx.beginPath(); ctx.moveTo(x + w / 2, y); ctx.lineTo(x + w / 2, y + h); ctx.moveTo(x, y + h * 0.48); ctx.lineTo(x + w, y + h * 0.48); ctx.stroke();
  ctx.fillStyle = '#e7dfd2'; ctx.fillRect(x - 24, y + h + 4, w + 48, 18);
  ctx.strokeStyle = '#b9ad9a'; ctx.lineWidth = 2; ctx.strokeRect(x - 24, y + h + 4, w + 48, 18);
  // curtains
  for (const [cx, dir] of [[x - 30, 1], [x + w + 30, -1]]) {
    ctx.fillStyle = '#7a4f66';
    ctx.beginPath();
    ctx.moveTo(cx - 48, y - 40); ctx.lineTo(cx + 48, y - 40);
    ctx.bezierCurveTo(cx + 30 + dir * 20, y + 220, cx + 40, y + 420, cx + 52, y + 560);
    ctx.lineTo(cx - 52, y + 560);
    ctx.bezierCurveTo(cx - 40, y + 420, cx - 30 + dir * 20, y + 220, cx - 48, y - 40);
    ctx.fill();
    ctx.strokeStyle = 'rgba(40,20,35,0.45)'; ctx.lineWidth = 3;
    for (const k of [-24, 0, 24]) {
      ctx.beginPath(); ctx.moveTo(cx + k, y - 30); ctx.bezierCurveTo(cx + k + dir * 10, y + 200, cx + k, y + 400, cx + k * 1.1, y + 556); ctx.stroke();
    }
  }
  ctx.fillStyle = '#3a2a24'; ctx.fillRect(x - 100, y - 52, w + 200, 12);
}

function drawClock(ctx, t) {
  const cx = 770, cy = 215, r = 46;
  ctx.fillStyle = '#f1ebe0'; ctx.strokeStyle = '#2d2622'; ctx.lineWidth = 7;
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill(); ctx.stroke();
  ctx.lineWidth = 3;
  for (let i = 0; i < 12; i++) {
    const a = i / 12 * Math.PI * 2;
    ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r * 0.78, cy + Math.sin(a) * r * 0.78); ctx.lineTo(cx + Math.cos(a) * r * 0.9, cy + Math.sin(a) * r * 0.9); ctx.stroke();
  }
  const sec = Math.floor(t) + 23;
  const hands = [[(11.9 / 12), 0.5, 5], [(sec / 60 + 52) / 60, 0.72, 4], [sec / 60, 0.82, 2]];
  ctx.lineCap = 'round';
  for (const [f, len, wdt] of hands) {
    const a = f * Math.PI * 2 - Math.PI / 2;
    ctx.strokeStyle = wdt === 2 ? '#b8392f' : '#2d2622'; ctx.lineWidth = wdt;
    ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(a) * r * len, cy + Math.sin(a) * r * len); ctx.stroke();
  }
}

function drawPhoto(ctx) {
  // Marcus's unit photo
  const x = 615, y = 330, w = 270, h = 180;
  ctx.fillStyle = '#2c2420'; ctx.fillRect(x - 12, y - 12, w + 24, h + 24);
  ctx.fillStyle = '#efe9dc'; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = '#cdb88f'; ctx.fillRect(x + 18, y + 16, w - 36, h - 32);
  ctx.fillStyle = '#9fb3c4'; ctx.fillRect(x + 18, y + 16, w - 36, 50);
  for (let i = 0; i < 5; i++) {
    const px = x + 50 + i * 42, py = y + 92 + (i % 2) * 6;
    ctx.fillStyle = '#5f6b45';
    ctx.beginPath(); ctx.moveTo(px - 17, py + 60); ctx.lineTo(px - 14, py + 18); ctx.quadraticCurveTo(px, py + 8, px + 14, py + 18); ctx.lineTo(px + 17, py + 60); ctx.fill();
    ctx.fillStyle = i === 2 ? '#7b4f35' : ['#c99a78', '#8a5a3c', '#e0b392', '#6e4a33', '#d6a882'][i];
    ctx.beginPath(); ctx.arc(px, py, 11, 0, 7); ctx.fill();
  }
}

function drawLamp(ctx, L) {
  ctx.strokeStyle = '#2a2420'; ctx.lineWidth = 9;
  ctx.beginPath(); ctx.moveTo(990, 570); ctx.lineTo(990, 1120); ctx.stroke();
  ctx.fillStyle = mixColor('#c9b38d', '#fff0c8', L.lamp * (1 - L.morning));
  ctx.strokeStyle = '#8c7754'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(935, 470); ctx.lineTo(1045, 470); ctx.lineTo(1075, 578); ctx.lineTo(905, 578); ctx.closePath();
  ctx.fill(); ctx.stroke();
}

function drawPlant(ctx) {
  ctx.fillStyle = '#b4613e'; ctx.strokeStyle = '#6e3824'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(-10, 1040); ctx.lineTo(90, 1040); ctx.lineTo(78, 1150); ctx.lineTo(2, 1150); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#3f6b4a'; ctx.strokeStyle = '#25412c';
  const leaves = [[40, 1040, -2.2, 150], [40, 1040, -1.7, 190], [40, 1040, -1.25, 170], [40, 1040, -0.8, 130], [40, 1040, -2.6, 110], [40, 1040, -1.45, 230]];
  for (const [x, y, a, l] of leaves) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(a);
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(l * 0.5, -l * 0.18, l, 0); ctx.quadraticCurveTo(l * 0.5, l * 0.18, 0, 0); ctx.fill(); ctx.stroke();
    ctx.restore();
  }
}

function drawCouchBack(ctx) {
  const base = '#b5653d', dark = '#8e4a2b', line = '#5a2c18';
  ctx.lineJoin = 'round';
  // back
  ctx.fillStyle = base; ctx.strokeStyle = line; ctx.lineWidth = 3.5;
  roundRect(ctx, 30, 965, 1020, 300, 46); ctx.fill(); ctx.stroke();
  // back cushions
  for (let i = 0; i < 3; i++) {
    const x = 128 + i * 278;
    ctx.fillStyle = mixColor(base, '#c87a50', 0.35);
    roundRect(ctx, x, 990, 270, 220, 36); ctx.fill(); ctx.stroke();
    ctx.strokeStyle = 'rgba(90,44,24,0.35)'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(x + 30, 1180); ctx.quadraticCurveTo(x + 135, 1196, x + 240, 1180); ctx.stroke();
    ctx.strokeStyle = line; ctx.lineWidth = 3.5;
  }
  // seat
  ctx.fillStyle = mixColor(base, '#c87a50', 0.2);
  roundRect(ctx, 100, 1196, 880, 54, 18); ctx.fill(); ctx.stroke();
}

function drawCouchFront(ctx) {
  const base = '#b5653d', dark = '#8e4a2b', line = '#5a2c18';
  ctx.strokeStyle = line; ctx.lineWidth = 3.5;
  // seat fronts
  ctx.fillStyle = dark;
  roundRect(ctx, 100, 1236, 880, 104, 16); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(393, 1240); ctx.lineTo(393, 1336); ctx.moveTo(687, 1240); ctx.lineTo(687, 1336);
  ctx.strokeStyle = 'rgba(60,25,12,0.6)'; ctx.stroke();
  // arms
  ctx.strokeStyle = line;
  for (const x of [14, 950]) {
    ctx.fillStyle = base;
    roundRect(ctx, x, 1078, 118, 270, 40); ctx.fill(); ctx.stroke();
    ctx.fillStyle = mixColor(base, '#d08a5e', 0.4);
    roundRect(ctx, x + 8, 1078, 102, 46, 22); ctx.fill();
  }
  // legs
  ctx.fillStyle = '#3a2618';
  for (const x of [40, 1010]) { ctx.fillRect(x, 1346, 22, 26); }
}

function drawRoom(ctx, L, t) {
  const m = L.morning;
  // wall
  ctx.fillStyle = mixColor('#3a4065', '#e9dcc3', m);
  ctx.fillRect(-600, -600, 2280, 1900);
  // subtle wall panel stripe
  ctx.fillStyle = rgba(mixColor('#2d3254', '#dccbae', m), 1);
  ctx.fillRect(-600, 900, 2280, 14);
  // floor
  ctx.fillStyle = mixColor('#4a3428', '#a57a58', m);
  ctx.fillRect(-600, 1300, 2280, 1300);
  ctx.strokeStyle = rgba(mixColor('#2e2019', '#7f5a3f', m), 0.6); ctx.lineWidth = 3;
  for (let y = 1340; y < 2100; y += 70) { ctx.beginPath(); ctx.moveTo(-600, y); ctx.lineTo(1700, y); ctx.stroke(); }
  // baseboard
  ctx.fillStyle = mixColor('#2a2d45', '#d8c8ad', m); ctx.fillRect(-600, 1286, 2280, 18);
  // rug
  ctx.fillStyle = mixColor('#4f5b74', '#8fa1b8', m);
  ctx.beginPath(); ctx.ellipse(540, 1650, 560, 190, 0, 0, 7); ctx.fill();
  ctx.strokeStyle = mixColor('#c9b27a', '#efdca8', m); ctx.lineWidth = 6;
  ctx.beginPath(); ctx.ellipse(540, 1650, 520, 165, 0, 0, 7); ctx.stroke();

  drawWindow(ctx, L, t);
  drawPhoto(ctx);
  drawClock(ctx, t);
  drawPlant(ctx);
  drawLamp(ctx, L);
  drawCouchBack(ctx);
}

function drawTable(ctx, L, t, items) {
  const wood = '#7d5337', top = '#956545', line = '#3e2616';
  ctx.lineJoin = 'round'; ctx.strokeStyle = line; ctx.lineWidth = 3.5;
  // legs
  ctx.fillStyle = '#5f3e28';
  for (const x of [175, 880]) { ctx.fillRect(x, 1560, 26, 210); ctx.strokeRect(x, 1560, 26, 210); }
  // top
  ctx.fillStyle = top;
  ctx.beginPath(); ctx.moveTo(210, 1452); ctx.lineTo(870, 1452); ctx.lineTo(935, 1530); ctx.lineTo(145, 1530); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = wood; ctx.fillRect(145, 1530, 790, 40); ctx.strokeRect(145, 1530, 790, 40);
  ctx.strokeStyle = 'rgba(62,38,22,0.35)'; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(260, 1475); ctx.lineTo(820, 1475); ctx.moveTo(220, 1505); ctx.lineTo(880, 1505); ctx.stroke();

  if (items.includes('snacks')) {
    // popcorn bowl
    ctx.fillStyle = '#d34f43'; ctx.strokeStyle = '#7a2420'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.moveTo(470, 1462); ctx.lineTo(610, 1462); ctx.quadraticCurveTo(600, 1512, 540, 1514); ctx.quadraticCurveTo(480, 1512, 470, 1462); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff3c9';
    for (let i = 0; i < 9; i++) { ctx.beginPath(); ctx.arc(480 + i * 15, 1456 - (i % 3) * 5, 11, 0, 7); ctx.fill(); }
    // cans
    for (const [x, c] of [[300, '#3b7bd1'], [356, '#d9a12f'], [760, '#4caf7d']]) {
      ctx.fillStyle = c; ctx.strokeStyle = '#1f2a33';
      roundRect(ctx, x, 1428, 34, 62, 6); ctx.fill(); ctx.stroke();
      ctx.fillStyle = 'rgba(255,255,255,0.4)'; ctx.fillRect(x + 6, 1436, 5, 44);
    }
  }
  for (const [name, x, y, r] of [['controller', 250, 1500, -0.2], ['controller2', 690, 1488, 0.15], ['controller3', 600, 1505, -0.1]]) {
    if (!items.includes(name)) continue;
    ctx.save(); ctx.translate(x, y); ctx.rotate(r); ctx.scale(0.8, 0.8);
    ctx.fillStyle = '#2b2d33'; ctx.strokeStyle = '#111215'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.ellipse(0, 0, 50, 18, 0, 0, 7); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#5ad1c8'; ctx.beginPath(); ctx.arc(26, -3, 4, 0, 7); ctx.fill();
    ctx.restore();
  }
  if (items.includes('mug')) {
    ctx.fillStyle = '#e9e1d2'; ctx.strokeStyle = '#6d6455'; ctx.lineWidth = 3;
    roundRect(ctx, 610, 1430, 48, 58, 8); ctx.fill(); ctx.stroke();
    ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(664, 1458, 13, -1.3, 1.3); ctx.stroke();
  }
  if (items.includes('jam')) {
    ctx.fillStyle = '#9c2b3f'; ctx.strokeStyle = '#4a1420'; ctx.lineWidth = 3;
    roundRect(ctx, 400, 1436, 44, 52, 8); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#e8e2d6'; ctx.fillRect(398, 1430, 48, 12);
  }
}

// --- lighting --------------------------------------------------------------
function buildLightmap(lctx, L, t) {
  const m = L.morning;
  const amb = mixColor(mixColor('#6f6f9c', '#7a7cab', L.tv), '#fff6ea', m);
  lctx.globalCompositeOperation = 'source-over';
  lctx.fillStyle = amb; lctx.fillRect(-1200, -1200, 3500, 4400);
  lctx.globalCompositeOperation = 'lighter';
  if (L.lamp > 0.01) {
    const a = L.lamp * (1 - m);
    const g = lctx.createRadialGradient(990, 560, 20, 990, 640, 980);
    g.addColorStop(0, rgba('#ffcf8f', 0.8 * a));
    g.addColorStop(0.45, rgba('#d9925a', 0.32 * a));
    g.addColorStop(1, rgba('#d9925a', 0));
    lctx.fillStyle = g; lctx.fillRect(-1200, -1200, 3500, 4400);
  }
  // soft frontal fill once the TV is off, so faces stay readable
  {
    const a = (1 - L.tv) * (1 - m) * 0.32;
    if (a > 0.005) {
      const g = lctx.createRadialGradient(470, 1050, 40, 470, 1050, 760);
      g.addColorStop(0, rgba('#ffe2c4', a)); g.addColorStop(1, rgba('#ffe2c4', 0));
      lctx.fillStyle = g; lctx.fillRect(-1200, -1200, 3500, 4400);
    }
  }
  if (L.tv > 0.01) {
    const fl = 0.85 + 0.15 * noise1(t * 3.1, 9) + L.tvFlash;
    const a = L.tv * (1 - m) * fl;
    const g = lctx.createRadialGradient(540, 1700, 50, 540, 1350, 1250);
    g.addColorStop(0, rgba('#8fb4ff', 0.55 * a));
    g.addColorStop(0.6, rgba('#7f9de6', 0.3 * a));
    g.addColorStop(1, rgba('#6f8fe0', 0));
    lctx.fillStyle = g; lctx.fillRect(-1200, -1200, 3500, 4400);
  }
  if (m > 0.01) {
    lctx.fillStyle = rgba('#fff1d6', 0.35 * m);
    lctx.beginPath(); lctx.moveTo(110, 250); lctx.lineTo(440, 250); lctx.lineTo(1100, 1500); lctx.lineTo(500, 1700); lctx.closePath(); lctx.fill();
  }
  lctx.globalCompositeOperation = 'source-over';
}

function drawGlows(ctx, L) {
  const m = L.morning;
  ctx.globalCompositeOperation = 'screen';
  if (L.lamp > 0.01) {
    const a = L.lamp * (1 - m);
    const g = ctx.createRadialGradient(990, 525, 10, 990, 525, 260);
    g.addColorStop(0, rgba('#ffd9a0', 0.32 * a));
    g.addColorStop(1, rgba('#ffd9a0', 0));
    ctx.fillStyle = g; ctx.fillRect(700, 250, 600, 600);
    ctx.fillStyle = rgba('#ffe6b8', 0.45 * a);
    ctx.beginPath(); ctx.moveTo(935, 470); ctx.lineTo(1045, 470); ctx.lineTo(1075, 578); ctx.lineTo(905, 578); ctx.closePath(); ctx.fill();
  }
  if (m > 0.01) {
    const g = ctx.createRadialGradient(275, 455, 40, 275, 455, 420);
    g.addColorStop(0, rgba('#fff4dc', 0.4 * m));
    g.addColorStop(1, rgba('#fff4dc', 0));
    ctx.fillStyle = g; ctx.fillRect(-200, 0, 1000, 1000);
  }
  ctx.globalCompositeOperation = 'source-over';
}

module.exports = { drawRoom, drawCouchFront, drawTable, buildLightmap, drawGlows, roundRect };
