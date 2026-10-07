// ===== Environments =====
// ---- City (pre-rendered world, 1280 x 1700, ground at y=1600) ----
const CITY_GROUND = 1600;
const CITY_DARK = [];
const CITY = (() => {
  const c = mkCanvas(W, 1700), g = c.getContext('2d');
  const sky = g.createLinearGradient(0, 0, 0, 1400);
  sky.addColorStop(0, '#05060d'); sky.addColorStop(0.55, '#131628'); sky.addColorStop(1, '#2a2436');
  g.fillStyle = sky; g.fillRect(0, 0, W, 1700);
  const r = rng(42);
  const layers = [
    { y: 1400, hmin: 300, hmax: 900, col: [26, 28, 44], win: 0.08, ws: 5 },
    { y: 1500, hmin: 250, hmax: 750, col: [17, 18, 30], win: 0.12, ws: 7 },
    { y: 1600, hmin: 200, hmax: 520, col: [11, 12, 20], win: 0.16, ws: 9 },
  ];
  for (const Ly of layers) {
    let x = -40;
    while (x < W + 40) {
      const bw = 70 + r() * 140, bh = Ly.hmin + r() * (Ly.hmax - Ly.hmin);
      g.fillStyle = rgba(Ly.col); g.fillRect(x, Ly.y - bh, bw, bh + 200);
      if (r() > 0.6) { g.fillRect(x + bw * 0.4, Ly.y - bh - 40, 4, 40); }
      for (let wy = Ly.y - bh + 14; wy < Ly.y - 20; wy += Ly.ws * 2.6) for (let wx = x + 8; wx < x + bw - 8; wx += Ly.ws * 2) {
        if (Ly.y === 1600 || Ly.y === 1500) CITY_DARK.push([wx + Ly.ws / 2, wy + Ly.ws * 0.65, Ly.ws]);
        if (r() < Ly.win) { const warm = r() > 0.3; g.fillStyle = warm ? `rgba(255,${190 + r() * 40 | 0},${110 + r() * 40 | 0},${0.35 + r() * 0.5})` : `rgba(150,190,255,${0.3 + r() * 0.4})`; g.fillRect(wx, wy, Ly.ws, Ly.ws * 1.3); }
      }
      x += bw + 4 + r() * 20;
    }
  }
  // street
  g.fillStyle = '#0d0e15'; g.fillRect(0, CITY_GROUND, W, 100);
  g.fillStyle = '#1a1b24'; g.fillRect(0, CITY_GROUND - 6, W, 8);
  // the station facade (left)
  g.fillStyle = '#2a2220'; g.fillRect(40, CITY_GROUND - 330, 420, 330);
  g.fillStyle = '#3a2e2a'; for (let by = CITY_GROUND - 330; by < CITY_GROUND; by += 12) for (let bx = 40 + ((by / 12) % 2) * 16; bx < 460; bx += 32) g.fillRect(bx, by, 30, 10);
  g.fillStyle = '#1b1616'; g.fillRect(30, CITY_GROUND - 345, 440, 20);
  // arched windows of station (warm)
  for (const wx of [80, 330]) { g.fillStyle = 'rgba(255,190,110,0.35)'; g.beginPath(); g.moveTo(wx, CITY_GROUND - 80); g.lineTo(wx, CITY_GROUND - 230); g.arc(wx + 45, CITY_GROUND - 230, 45, Math.PI, 0); g.lineTo(wx + 90, CITY_GROUND - 80); g.fill(); }
  // door
  g.fillStyle = '#3b2a1e'; g.fillRect(215, CITY_GROUND - 200, 90, 200);
  g.fillStyle = 'rgba(255,190,110,0.4)'; g.fillRect(230, CITY_GROUND - 185, 60, 70);
  // sign
  g.fillStyle = '#111'; g.fillRect(170, CITY_GROUND - 300, 180, 40);
  g.font = 'bold 22px "Liberation Sans", sans-serif'; g.textAlign = 'center'; g.fillStyle = 'rgba(255,170,90,0.9)'; g.fillText('WAITING ROOM', 260, CITY_GROUND - 272);
  // doorway on right with huddled person
  g.fillStyle = '#16141a'; g.fillRect(900, CITY_GROUND - 260, 380, 260);
  g.fillStyle = '#0a090c'; g.fillRect(1010, CITY_GROUND - 190, 110, 190);
  return c;
})();
function drawCity(ctx, t, camY, opt = {}) {
  ctx.drawImage(CITY, 0, -camY);
  const gy = CITY_GROUND - camY;
  // street lamps
  for (const lx of [560, 860, 1180]) {
    ctx.fillStyle = '#0a0a10'; ctx.fillRect(lx - 3, gy - 260, 6, 260);
    ctx.fillRect(lx - 3, gy - 262, 40, 5);
    glow(ctx, lx + 34, gy - 250, 140, [255, 190, 110], 0.5 + 0.03 * Math.sin(t * 20 + lx));
    // pool + reflection
    ctx.save(); ctx.globalCompositeOperation = 'lighter';
    const rg = ctx.createLinearGradient(0, gy, 0, gy + 100); rg.addColorStop(0, 'rgba(255,180,100,0.18)'); rg.addColorStop(1, 'rgba(255,180,100,0)');
    ctx.fillStyle = rg; ctx.fillRect(lx + 20, gy, 28, 100); ctx.restore();
  }
  // huddled person in right doorway
  ctx.fillStyle = '#26222a'; ctx.beginPath(); ctx.ellipse(1065, gy - 30, 34, 36, 0, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.arc(1060, gy - 72, 16, 0, 7); ctx.fill();
  ctx.fillStyle = '#3a3440'; ctx.fillRect(1030, gy - 4, 80, 6);
  // pedestrians
  for (let i = 0; i < 5; i++) {
    const dir = i % 2 ? 1 : -1, sp = 70 + i * 13;
    const x = dir > 0 ? ((t * sp + i * 300) % 1700) - 200 : W + 200 - ((t * sp + i * 377) % 1700);
    drawPedestrian(ctx, x, gy + 4, 170 + (i % 3) * 10, t * 5 + i, dir, [12 + i * 2, 13, 20]);
  }
  if (opt.him) drawFigure(ctx, Object.assign({ who: 'him', y: gy + 2, h: 175, pose: 'walk', dir: -1, bag: true, headDown: 0.6, t }, opt.him));
  rainStreaks(ctx, t, 260, 1500, 0.15, 0.22, 3, 30);
  // street sheen
  ctx.fillStyle = 'rgba(120,140,190,0.04)'; ctx.fillRect(0, gy, W, 100);
}

// ---- Station interior (static, 1280x720) ----
const WIN = { x: 120, y: 110, w: 330, h: 380 };
const STATION = (() => {
  const c = mkCanvas(), g = c.getContext('2d');
  // wall
  const wg = g.createLinearGradient(0, 0, 0, 560); wg.addColorStop(0, '#2c302d'); wg.addColorStop(1, '#3b403b');
  g.fillStyle = wg; g.fillRect(0, 0, W, 560);
  // tiles lower wall
  g.fillStyle = '#44504b'; g.fillRect(0, 380, W, 180);
  g.strokeStyle = 'rgba(0,0,0,0.18)'; g.lineWidth = 1;
  for (let y = 380; y < 560; y += 22) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
  for (let y = 380, k = 0; y < 560; y += 22, k++) for (let x = (k % 2) * 22; x < W; x += 44) { g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 22); g.stroke(); }
  g.fillStyle = '#2a302c'; g.fillRect(0, 372, W, 10);
  // window (night outside)
  const { x, y, w, h } = WIN;
  g.save(); g.beginPath(); g.moveTo(x, y + h); g.lineTo(x, y + w / 2); g.arc(x + w / 2, y + w / 2, w / 2, Math.PI, 0); g.lineTo(x + w, y + h); g.closePath();
  g.fillStyle = '#0b1020'; g.fill(); g.clip();
  const r = rng(77);
  for (let i = 0; i < 70; i++) { const bx = x + r() * w, by = y + 120 + r() * (h - 120), br = 4 + r() * 16; const warm = r() > 0.35; const gr = g.createRadialGradient(bx, by, 0, bx, by, br); gr.addColorStop(0, warm ? 'rgba(255,190,110,0.55)' : 'rgba(140,180,255,0.45)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(bx - br, by - br, br * 2, br * 2); }
  g.restore();
  g.strokeStyle = '#1d211f'; g.lineWidth = 12;
  g.beginPath(); g.moveTo(x, y + h); g.lineTo(x, y + w / 2); g.arc(x + w / 2, y + w / 2, w / 2, Math.PI, 0); g.lineTo(x + w, y + h); g.closePath(); g.stroke();
  g.lineWidth = 6; g.beginPath(); g.moveTo(x + w / 2, y); g.lineTo(x + w / 2, y + h); g.moveTo(x, y + 230); g.lineTo(x + w, y + 230); g.stroke();
  // second window (right)
  g.fillStyle = '#0c1120'; g.fillRect(560, 140, 200, 220); g.strokeStyle = '#1d211f'; g.lineWidth = 10; g.strokeRect(560, 140, 200, 220);
  // clock
  g.fillStyle = '#d8d2c0'; g.beginPath(); g.arc(880, 150, 34, 0, 7); g.fill(); g.strokeStyle = '#222'; g.lineWidth = 4; g.stroke();
  g.lineWidth = 3; g.beginPath(); g.moveTo(880, 150); g.lineTo(880, 128); g.moveTo(880, 150); g.lineTo(896, 158); g.stroke();
  // notice board
  g.fillStyle = '#4a3a2a'; g.fillRect(820, 230, 150, 110);
  for (let i = 0; i < 5; i++) { g.fillStyle = ['#ddd5c0', '#e8e0b0', '#cfd8dc', '#f0e6d0', '#d0c8b8'][i]; g.save(); g.translate(835 + (i % 3) * 45, 245 + Math.floor(i / 3) * 48); g.rotate((r() - .5) * 0.2); g.fillRect(0, 0, 36, 40); g.restore(); }
  // door (right)
  g.fillStyle = '#3a2a1e'; g.fillRect(1050, 200, 150, 360); g.fillStyle = '#2b1f16'; g.fillRect(1060, 210, 130, 340);
  g.fillStyle = '#0c1120'; g.fillRect(1080, 230, 90, 120);
  g.fillStyle = '#b8a070'; g.beginPath(); g.arc(1072, 400, 6, 0, 7); g.fill();
  // floor
  const fg = g.createLinearGradient(0, 560, 0, H); fg.addColorStop(0, '#2a2622'); fg.addColorStop(1, '#151311');
  g.fillStyle = fg; g.fillRect(0, 560, W, H - 560);
  g.strokeStyle = 'rgba(0,0,0,0.25)'; g.lineWidth = 1;
  for (let i = -20; i < 40; i++) { g.beginPath(); g.moveTo(640 + i * 60, 560); g.lineTo(640 + i * 160, H); g.stroke(); }
  for (let yy = 575, k = 1; yy < H; yy += 14 * k, k++) { g.beginPath(); g.moveTo(0, yy); g.lineTo(W, yy); g.stroke(); }
  // radiator under window
  g.fillStyle = '#5a5e5a'; for (let i = 0; i < 12; i++) g.fillRect(150 + i * 22, 470, 14, 70);
  g.fillRect(146, 535, 270, 8);
  // benches
  bench(g, 130, 560, 360); bench(g, 610, 575, 300);
  return c;
})();
function bench(g, x, y, w) {
  g.fillStyle = '#5b3f2a'; g.fillRect(x, y - 70, w, 14); g.fillRect(x, y - 110, w, 12); g.fillRect(x, y - 136, w, 12);
  g.fillStyle = '#3d2a1c'; g.fillRect(x + 10, y - 136, 10, 136); g.fillRect(x + w - 20, y - 136, 10, 136);
  g.fillStyle = 'rgba(0,0,0,0.3)'; g.fillRect(x, y - 56, w, 6);
  g.fillStyle = 'rgba(0,0,0,0.35)'; g.beginPath(); g.ellipse(x + w / 2, y + 4, w / 2, 8, 0, 0, 7); g.fill();
}
function bulbFlicker(t, steady = 0) {
  const f = 0.85 + 0.15 * noise1(t * 3);
  const glitch = (noise1(t * 11 + 3) > 0.75 && noise1(t * 0.7) > 0.2) ? 0.55 : 1;
  return lerp(f * glitch, 1, steady);
}
function drawStationBG(ctx, t, opt = {}) {
  ctx.drawImage(STATION, 0, 0);
  ctx.save();
  ctx.beginPath(); ctx.moveTo(WIN.x, WIN.y + WIN.h); ctx.lineTo(WIN.x, WIN.y + WIN.w / 2); ctx.arc(WIN.x + WIN.w / 2, WIN.y + WIN.w / 2, WIN.w / 2, Math.PI, 0); ctx.lineTo(WIN.x + WIN.w, WIN.y + WIN.h); ctx.rect(560, 140, 200, 220); ctx.clip();
  const r = rng(9); ctx.strokeStyle = 'rgba(180,200,230,0.35)'; ctx.lineWidth = 1.5;
  for (let i = 0; i < 60; i++) { const dx = r() * 700 + 100, sp = 40 + r() * 120, ph = r(); const yy = ((ph * 500 + t * sp) % 500) + 100; ctx.beginPath(); ctx.moveTo(dx, yy); ctx.lineTo(dx + Math.sin(yy * 0.05) * 2, yy + 14 + r() * 10); ctx.stroke(); }
  ctx.restore();
  if (opt.doorOpen > 0) { // open door: night gap with rain
    const d = opt.doorOpen;
    ctx.fillStyle = '#070a14'; ctx.fillRect(1060, 210, 130 * d, 340);
    ctx.save(); ctx.beginPath(); ctx.rect(1060, 210, 130 * d, 340); ctx.clip(); rainStreaks(ctx, t, 40, 1200, 0.1, 0.3, 5, 20); ctx.restore();
    ctx.fillStyle = '#2b1f16'; ctx.fillRect(1060 + 130 * d, 205, 22 * d, 350);
  }
  const bx = 640, by = 170;
  ctx.strokeStyle = '#111'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(bx, 0); ctx.lineTo(bx + Math.sin(t * 0.8) * 2, by - 14); ctx.stroke();
  ctx.fillStyle = '#222'; ctx.fillRect(bx - 7, by - 18, 14, 10);
}
function drawStationLight(ctx, t, fl, opt = {}) {
  const bx = 640, by = 170, warm = opt.warm || 0;
  const dg = ctx.createRadialGradient(bx, by + 120, 30, bx, by + 120, 900);
  dg.addColorStop(0, rgba([0, 0, 0], 0.05 + (1 - fl) * 0.3));
  dg.addColorStop(0.4, rgba([5, 8, 18], 0.42 + (1 - fl) * 0.3 - warm * 0.25));
  dg.addColorStop(1, rgba([2, 3, 10], 0.82 - warm * 0.35));
  ctx.fillStyle = dg; ctx.fillRect(0, 0, W, H);
  if (warm > 0) { ctx.save(); ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = rgba([255, 170, 90], 0.07 * warm); ctx.fillRect(0, 0, W, H); ctx.restore(); }
  glow(ctx, bx, by, 300, [255, 196, 120], 0.45 * fl + warm * 0.2);
  glow(ctx, bx, by, 40, [255, 240, 200], 0.9 * fl);
  ctx.fillStyle = rgba([255, 245, 220], fl); ctx.beginPath(); ctx.arc(bx, by, 9, 0, 7); ctx.fill();
  glow(ctx, bx, 640, 120, [255, 190, 120], 0.12 * fl);
}
const STATION_BLUR = (() => { const c = mkCanvas(), g = c.getContext('2d'); g.filter = 'blur(7px)'; g.drawImage(STATION, 0, 0); g.filter = 'none';
  // add bulb light to blurred version
  const dg = g.createRadialGradient(640, 290, 30, 640, 290, 900); dg.addColorStop(0, 'rgba(0,0,0,0.05)'); dg.addColorStop(0.4, 'rgba(5,8,18,0.42)'); dg.addColorStop(1, 'rgba(2,3,10,0.82)'); g.fillStyle = dg; g.fillRect(0, 0, W, H);
  return c; })();
// draw the blurred station as a close-up background: (cx,cy) = point of the room to centre on, z = zoom
function stationCloseBG(ctx, t, cx, cy, z, opt = {}) {
  const sw = W / z, sh = H / z;
  ctx.drawImage(STATION_BLUR, cx - sw / 2, cy - sh / 2, sw, sh, 0, 0, W, H);
  const fl = opt.fl ?? 1;
  // window bokeh flicker + rain smear
  const r = rng(31);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 26; i++) { const wx = WIN.x + r() * WIN.w, wy = WIN.y + 120 + r() * 250; const X = (wx - cx) * z + W / 2, Y = (wy - cy) * z + H / 2; const rr = (10 + r() * 22) * z * 0.6; const warm = r() > 0.4; const a = 0.08 + 0.06 * Math.sin(t * (0.5 + r()) + i);
    const gr = ctx.createRadialGradient(X, Y, 0, X, Y, rr); gr.addColorStop(0, warm ? `rgba(255,190,110,${a})` : `rgba(140,180,255,${a})`); gr.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = gr; ctx.fillRect(X - rr, Y - rr, rr * 2, rr * 2); }
  ctx.restore();
  const bx = (640 - cx) * z + W / 2, by = (170 - cy) * z + H / 2;
  glow(ctx, bx, by, 260 * z * 0.6, [255, 196, 120], 0.35 * fl);
  if (opt.dark) { ctx.fillStyle = rgba([0, 0, 0], opt.dark); ctx.fillRect(0, 0, W, H); }
}

// ---- Mindscape storm ----
function drawMindSky(ctx, t, o = {}) {
  const flash = o.flash || 0, red = o.red ?? 1, calm = o.calm || 0;
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, rgba(mixc([8, 5, 14], [10, 10, 24], calm))); g.addColorStop(0.7, rgba(mixc([38, 14, 30], [30, 26, 50], calm))); g.addColorStop(1, rgba(mixc([60, 18, 22], [50, 40, 60], calm)));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  stormClouds(ctx, t, { seed: 5, n: 50, y0: -150, y1: H * 0.55, col: [18, 10, 24], col2: mixc([70, 22, 40], [50, 50, 80], calm), speed: (1.6 - calm) * (o.speed || 1), alpha: 0.9, flash, swirl: o.swirl || 0, cx: o.cx ?? W / 2, cy: o.cy ?? H * 0.35 });
  stormClouds(ctx, t * 1.3, { seed: 8, n: 35, y0: -50, y1: H * 0.45, col: [30, 14, 30], col2: mixc([110, 30, 40], [80, 80, 120], calm), speed: (2 - calm) * (o.speed || 1), alpha: 0.6, flash, swirl: o.swirl || 0, cx: o.cx ?? W / 2, cy: o.cy ?? H * 0.35 });
  if (flash > 0) { ctx.fillStyle = rgba([200, 190, 255], flash * 0.35); ctx.fillRect(0, 0, W, H); }
}
function demonShadow(ctx, cx, cy, s, a, t, eyes = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(cx, cy); ctx.scale(s, s);
  ctx.fillStyle = 'rgb(6,2,6)'; ctx.shadowColor = 'rgba(0,0,0,1)'; ctx.shadowBlur = 60;
  ctx.beginPath();
  ctx.moveTo(-420, 400); ctx.bezierCurveTo(-380, 160, -220, 110, -120, 90);
  ctx.bezierCurveTo(-150, 20, -130, -90, -80, -130);
  ctx.bezierCurveTo(-170, -200, -210, -330, -150, -420); ctx.bezierCurveTo(-160, -320, -110, -230, -50, -170);
  ctx.quadraticCurveTo(0, -190, 50, -170);
  ctx.bezierCurveTo(110, -230, 160, -320, 150, -420); ctx.bezierCurveTo(210, -330, 170, -200, 80, -130);
  ctx.bezierCurveTo(130, -90, 150, 20, 120, 90); ctx.bezierCurveTo(220, 110, 380, 160, 420, 400); ctx.closePath(); ctx.fill();
  ctx.shadowBlur = 0;
  if (eyes > 0) for (const sx of [-1, 1]) { glow(ctx, sx * 42, -40, 70, [255, 30, 10], 0.8 * eyes); ctx.fillStyle = rgba([255, 120, 80], eyes); ctx.beginPath(); ctx.ellipse(sx * 42, -40, 16, 5, sx * 0.25, 0, 7); ctx.fill(); }
  ctx.restore();
}
function drawRock(ctx, cx, gy, s = 1, col = [10, 6, 10]) {
  ctx.fillStyle = rgba(col);
  ctx.beginPath(); ctx.moveTo(cx - 700 * s, H + 10); ctx.lineTo(cx - 300 * s, gy + 140 * s); ctx.lineTo(cx - 160 * s, gy + 40 * s); ctx.lineTo(cx - 60 * s, gy + 6 * s); ctx.lineTo(cx + 70 * s, gy); ctx.lineTo(cx + 170 * s, gy + 60 * s); ctx.lineTo(cx + 320 * s, gy + 160 * s); ctx.lineTo(cx + 700 * s, H + 10); ctx.fill();
  ctx.fillStyle = 'rgba(120,40,40,0.12)'; ctx.beginPath(); ctx.moveTo(cx - 60 * s, gy + 6 * s); ctx.lineTo(cx + 70 * s, gy); ctx.lineTo(cx + 40 * s, gy + 30 * s); ctx.fill();
}
function lightningSchedule(t, times, dur = 0.5) {
  let f = 0, idx = -1;
  for (let i = 0; i < times.length; i++) { const d = t - times[i]; if (d >= 0 && d < dur) { const v = (d < 0.06 ? 1 : d < 0.12 ? 0.35 : d < 0.18 ? 0.85 : Math.exp(-(d - 0.18) * 9) * 0.6); if (v > f) { f = v; idx = i; } } }
  return { f, idx };
}

// ---- Memory vignettes ----
function drawMemory(ctx, k, lt, cx, cy, r, a) {
  if (a <= 0) return;
  const g = layer(2);
  g.save(); g.translate(cx, cy);
  g.beginPath(); g.arc(0, 0, r, 0, 7); g.clip();
  const bg = g.createRadialGradient(0, 0, 0, 0, 0, r); bg.addColorStop(0, '#7a3a2a'); bg.addColorStop(1, '#2a0c0c');
  g.fillStyle = bg; g.fillRect(-r, -r, 2 * r, 2 * r);
  const s = r / 200; g.scale(s, s);
  const ink = [20, 8, 8];
  g.fillStyle = rgba(ink);
  const gy = 120;
  if (k !== 3) g.fillRect(-220, gy, 440, 100);
  if (k === 0) { // ignored on the sidewalk
    drawFigure(g, { who: 'her', x: -90, y: gy, h: 150, pose: 'sit', dir: 1, arm: sh => [sh, [sh[0] + 30, sh[1] + 10], [sh[0] + 70, sh[1] - 5]] });
    g.globalCompositeOperation = 'source-atop'; g.fillStyle = 'rgba(30,10,10,0.75)'; g.fillRect(-200, -200, 400, 400); g.globalCompositeOperation = 'source-over';
    for (let i = 0; i < 3; i++) drawPedestrian(g, -260 + ((lt * 90 + i * 170) % 520), gy, 190, lt * 6 + i, 1, ink, i === 1);
  } else if (k === 1) { // the queue / closed window
    g.fillStyle = '#c9a080'; g.fillRect(110, -120, 100, 120);
    const sh = clamp((lt - 1.2) / 0.8);
    g.fillStyle = rgba(ink); g.fillRect(110, -120, 100, 120 * sh);
    g.fillStyle = '#d04030'; g.font = 'bold 26px "Liberation Sans"'; g.textAlign = 'center'; if (sh > 0.9) g.fillText('CLOSED', 160, -50);
    for (let i = 0; i < 7; i++) drawPedestrian(g, 70 - i * 48, gy, 170 - i * 4, i * 0.7, 1, ink, false);
  } else if (k === 2) { // worked harder: two jobs, endless clock
    g.fillStyle = '#e6c8a0'; g.beginPath(); g.arc(-90, -80, 60, 0, 7); g.fill();
    g.strokeStyle = rgba(ink); g.lineWidth = 6; g.beginPath(); g.moveTo(-90, -80); g.lineTo(-90 + Math.sin(lt * 9) * 45, -80 - Math.cos(lt * 9) * 45); g.stroke();
    g.lineWidth = 8; g.beginPath(); g.moveTo(-90, -80); g.lineTo(-90 + Math.sin(lt * 0.75) * 30, -80 - Math.cos(lt * 0.75) * 30); g.stroke();
    g.fillStyle = rgba(ink); g.fillRect(0, 40, 200, 12); g.fillRect(20, 52, 10, 70); g.fillRect(170, 52, 10, 70);
    g.beginPath(); g.ellipse(80, 20, 50, 26, 0.2, 0, 7); g.fill(); g.beginPath(); g.arc(55, 0, 24, 0, 7); g.fill();
    glow(g, 120, -40, 90, [255, 200, 120], 0.4);
  } else if (k === 3) { // reaching hand pulled back + scale with one loaf
    const back = clamp((lt - 1.0) / 1.2);
    drawHand(g, -40, 70, -0.15, 1.0, ink);
    drawHand(g, 30, -70 - back * 130, Math.PI + 0.3, 1.0, ink);
    g.fillStyle = '#e0b070'; g.beginPath(); g.ellipse(140, 60, 34, 18, 0, 0, 7); g.fill();
    g.strokeStyle = '#e0b070'; g.lineWidth = 4; g.beginPath(); g.moveTo(100, 80); g.lineTo(180, 80); g.stroke();
  } else if (k === 4) { // spiked bench, keep walking
    g.fillStyle = rgba(ink); g.fillRect(-170, 40, 300, 16); g.fillRect(-160, 56, 12, 64); g.fillRect(110, 56, 12, 64);
    for (let i = 0; i < 14; i++) { g.beginPath(); g.moveTo(-165 + i * 21, 40); g.lineTo(-155 + i * 21, 18); g.lineTo(-145 + i * 21, 40); g.fill(); }
    g.beginPath(); g.ellipse(-20, gy - 10, 110, 20, 0, 0, 7); g.fill(); g.beginPath(); g.arc(-140, gy - 18, 18, 0, 7); g.fill();
    for (let i = 0; i < 2; i++) drawPedestrian(g, 220 - ((lt * 160 + i * 250) % 500), gy + 10, 260, lt * 7 + i, -1, ink, false);
  } else if (k === 5) { // eviction notice, door slams
    const close = clamp((lt - 1.4) / 0.3);
    g.fillStyle = '#4a2a1e'; g.fillRect(-90, -170, 180, 290);
    g.fillStyle = 'rgba(0,0,0,0.6)'; g.fillRect(-90, -170, 180 * (1 - close), 290);
    g.fillStyle = '#efe6d0'; g.save(); g.translate(-10, -60); g.rotate(-0.05); g.fillRect(-45, -50, 90, 110);
    g.fillStyle = '#b02020'; g.font = 'bold 16px "Liberation Sans"'; g.textAlign = 'center'; g.fillText('EVICTION', 0, -25); g.fillText('NOTICE', 0, -6);
    g.fillStyle = 'rgba(0,0,0,0.5)'; for (let i = 0; i < 5; i++) g.fillRect(-35, 8 + i * 9, 70 - (i % 2) * 20, 3); g.restore();
    g.fillStyle = '#c0a060'; g.beginPath(); g.arc(70, -20, 8, 0, 7); g.fill();
  }
  g.restore();
  // grain + edge burn
  g.save(); g.translate(cx, cy); g.globalCompositeOperation = 'source-atop';
  const eg = g.createRadialGradient(0, 0, r * 0.6, 0, 0, r); eg.addColorStop(0, 'rgba(0,0,0,0)'); eg.addColorStop(1, 'rgba(0,0,0,0.85)');
  g.fillStyle = eg; g.fillRect(-r, -r, 2 * r, 2 * r); g.restore();
  ctx.save(); ctx.globalAlpha = a; ctx.drawImage(LAYER[2], 0, 0); ctx.restore();
  ctx.save(); ctx.globalAlpha = a * 0.5; ctx.strokeStyle = 'rgba(255,90,60,0.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.stroke(); ctx.restore();
}

// ---- Captions & cards ----
function wrapText(ctx, text, maxW) {
  const words = text.split(' '); const lines = []; let cur = '';
  for (const w of words) { const tst = cur ? cur + ' ' + w : w; if (ctx.measureText(tst).width > maxW && cur) { lines.push(cur); cur = w; } else cur = tst; }
  if (cur) lines.push(cur); return lines;
}
function capStyle(c) {
  let font = '500 28px Inter, sans-serif', col = [255, 255, 255], text = c.text;
  if (c.spk === 'song') { font = 'italic 500 25px Inter, sans-serif'; col = [255, 222, 160]; text = '\u266A  ' + text + '  \u266A'; }
  else if (c.spk === 'him' || c.spk === 'rage') { font = 'italic 500 28px Inter, sans-serif'; col = [230, 236, 255]; }
  else if (c.spk.startsWith('v_')) { font = 'italic 400 27px Inter, sans-serif'; col = [175, 185, 205]; }
  else if (c.spk === 'demon') { font = 'italic 700 30px Inter, sans-serif'; col = [255, 90, 70]; }
  else if (c.spk === 'christ') { col = [255, 240, 205]; }
  return { font, col, text };
}
function drawCapLines(ctx, c, a, yBottom) {
  const st = capStyle(c);
  ctx.save(); ctx.font = st.font; ctx.textAlign = 'center';
  const lines = wrapText(ctx, st.text, 1000);
  let y = yBottom - (lines.length - 1) * 36;
  for (const ln of lines) {
    ctx.lineWidth = 6; ctx.strokeStyle = `rgba(0,0,0,${0.7 * a})`; ctx.lineJoin = 'round'; ctx.strokeText(ln, W / 2, y);
    ctx.fillStyle = rgba(st.col, a); ctx.fillText(ln, W / 2, y); y += 36;
  }
  ctx.restore();
  return lines.length;
}
function drawCaptions(ctx, t, caps) {
  const dia = caps.filter(c => c.spk !== 'song'), song = caps.filter(c => c.spk === 'song');
  let used = 0, dAlpha = 0;
  for (let i = 0; i < dia.length; i++) {
    const c = dia[i], nx = dia[i + 1];
    const end = Math.min(c.end + 0.4, nx ? nx.start - 0.05 : 1e9);
    if (t < c.start - 0.1 || t > end) continue;
    const a = fade(t, c.start - 0.1, end, 0.15, 0.25);
    const n = drawCapLines(ctx, c, a, H - 42);
    used = Math.max(used, n); dAlpha = Math.max(dAlpha, a);
  }
  for (const c of song) {
    if (t < c.start - 0.1 || t > c.end + 0.4) continue;
    const a = fade(t, c.start - 0.1, c.end + 0.4, 0.2, 0.3);
    const yb = used ? H - 42 - used * 36 - 8 : H - 42;
    drawCapLines(ctx, c, a * (used ? 0.75 : 1), yb);
  }
}
function titleCard(ctx, t, title, sub, a, opt = {}) {
  ctx.save(); ctx.globalAlpha = a; ctx.textAlign = 'center';
  ctx.font = '400 64px "Liberation Serif", "DejaVu Serif", serif';
  ctx.fillStyle = rgba(opt.col || [235, 225, 210]);
  ctx.shadowColor = rgba(opt.glow || [255, 200, 140], 0.5); ctx.shadowBlur = 24;
  ctx.letterSpacing = '8px';
  ctx.fillText(title, W / 2, H / 2 - 10);
  ctx.shadowBlur = 0; ctx.letterSpacing = '3px';
  ctx.font = 'italic 300 30px Inter, sans-serif'; ctx.fillStyle = rgba([200, 200, 215], 0.9);
  if (sub) ctx.fillText(sub, W / 2, H / 2 + 50);
  ctx.restore();
}

function drawHand(g, x, y, ang, s, col) {
  g.save(); g.translate(x, y); g.rotate(ang); g.scale(s, s); g.fillStyle = rgba(col);
  g.fillRect(-22, 0, 44, 220); // forearm
  g.beginPath(); g.ellipse(0, -10, 30, 36, 0, 0, 7); g.fill(); // palm
  const fingers = [[-21, -38, 0.12, 42], [-7, -46, 0.03, 50], [7, -46, -0.03, 48], [20, -38, -0.12, 40]];
  for (const [fx, fy, fa, fl] of fingers) { g.save(); g.translate(fx, fy + 8); g.rotate(fa); g.beginPath(); g.ellipse(0, -fl / 2, 6.5, fl / 2, 0, 0, 7); g.fill(); g.restore(); }
  g.save(); g.translate(-28, 0); g.rotate(-0.8); g.beginPath(); g.ellipse(0, -16, 8, 22, 0, 0, 7); g.fill(); g.restore();
  g.restore();
}
