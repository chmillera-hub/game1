'use strict';
// Environments, weather and effects.

// ------------------------------------------------------------------ rain
function drawRain(c, t, amount, opts = {}) {
  if (amount <= 0) return;
  const n = Math.floor(260 * amount);
  const ang = opts.angle ?? 0.18, spd = opts.speed ?? 900, len = opts.len ?? 26;
  const x0 = opts.x0 ?? 0, y0 = opts.y0 ?? 0, w = opts.w ?? W, h = opts.h ?? H;
  c.save();
  c.strokeStyle = opts.color || 'rgba(190,210,235,0.35)';
  c.lineWidth = opts.lw || 1.2;
  c.beginPath();
  for (let i = 0; i < n; i++) {
    const r1 = hrand(i * 3.1 + 1), r2 = hrand(i * 7.7 + 2), r3 = hrand(i * 1.3 + 9);
    const sp = spd * (0.7 + 0.6 * r3);
    const y = ((r2 * h + t * sp) % (h + len * 2)) - len + y0;
    const x = ((r1 * (w + 200) + (y - y0) * ang) % (w + 200)) - 100 + x0;
    c.moveTo(x, y); c.lineTo(x - ang * len, y - len);
  }
  c.stroke(); c.restore();
}

// ------------------------------------------------------------------ silhouettes (memories, crowds)
function sil(c, x, y, h, o = {}) {
  c.save(); c.translate(x, y);
  if (o.lying) c.rotate(-Math.PI / 2 * 0.98);
  if (o.flip) c.scale(-1, 1);
  const s = h / 9;
  c.scale(s, s);
  c.fillStyle = o.color || '#120d0b';
  const ph = o.walk ?? null, st = ph === null ? 0 : Math.sin(ph) * 0.8;
  c.lineCap = 'round'; c.strokeStyle = c.fillStyle;
  // legs
  c.lineWidth = 0.7;
  if (o.sitting) {
    c.beginPath(); c.moveTo(-0.3, -3.6); c.lineTo(1.6, -3.3); c.lineTo(1.9, -0.2); c.stroke();
    c.beginPath(); c.moveTo(0.3, -3.6); c.lineTo(1.9, -3.0); c.lineTo(2.3, -0.2); c.stroke();
  } else {
    c.beginPath(); c.moveTo(-0.3, -4); c.lineTo(-0.35 + st, 0); c.stroke();
    c.beginPath(); c.moveTo(0.3, -4); c.lineTo(0.35 - st, 0); c.stroke();
  }
  // body
  c.beginPath(); c.moveTo(-1.1, -7.2); c.quadraticCurveTo(0, -7.7, 1.1, -7.2); c.lineTo(0.85, -3.7); c.lineTo(-0.85, -3.7); c.closePath(); c.fill();
  if (o.sitting) { c.fillRect(-0.85, -4.2, 1.7, 0.8); }
  // head
  c.beginPath(); c.arc(o.headDown ? 0.4 : 0, o.headDown ? -7.6 : -8.2, 0.85, 0, TAU); c.fill();
  // arms
  c.lineWidth = 0.55;
  const ar = o.reach ? -1 : 0;
  c.beginPath(); c.moveTo(-1.0, -7); c.lineTo(-1.25 - st * 0.4, -4.2); c.stroke();
  c.beginPath(); c.moveTo(1.0, -7); c.lineTo(o.reach ? 2.8 : 1.25 + st * 0.4, o.reach ? -6.2 : -4.2 + ar); c.stroke();
  if (o.suitcase) { c.fillRect(1.0, -4.4, 1.6, 1.5); }
  if (o.umbrella) {
    c.lineWidth = 0.15; c.beginPath(); c.moveTo(1.2, -4.5); c.lineTo(1.2, -10.5); c.stroke();
    c.beginPath(); c.moveTo(-2.6, -9.8); c.quadraticCurveTo(1.2, -13.2, 5.0, -9.8); c.closePath(); c.fill();
  }
  c.restore();
}

// ------------------------------------------------------------------ the room
function drawRoom(c, t, o = {}) {
  const night = o.night ?? 1;
  // back wall
  let gr = c.createLinearGradient(0, 0, 0, 565);
  gr.addColorStop(0, '#141a1f'); gr.addColorStop(1, '#2b3236');
  c.fillStyle = gr; c.fillRect(-200, -200, W + 400, 765);
  // wallpaper stripes
  c.fillStyle = 'rgba(255,255,255,0.025)';
  for (let x = -200; x < W + 200; x += 46) c.fillRect(x, -200, 18, 765);
  // peeling patches and water stains
  for (let i = 0; i < 9; i++) {
    const px = hrand(i + 40) * W, py = 80 + hrand(i + 50) * 380, r = 20 + hrand(i + 60) * 50;
    c.fillStyle = i % 3 === 0 ? 'rgba(90,70,45,0.18)' : 'rgba(180,190,185,0.06)';
    c.beginPath();
    for (let k = 0; k < 9; k++) { const a = k / 9 * TAU, rr = r * (0.6 + 0.5 * hrand(i * 10 + k)); c.lineTo(px + Math.cos(a) * rr, py + Math.sin(a) * rr * 0.8); }
    c.fill();
  }
  // floor
  gr = c.createLinearGradient(0, 565, 0, 760);
  gr.addColorStop(0, '#2a211b'); gr.addColorStop(1, '#16110e');
  c.fillStyle = gr; c.fillRect(-200, 565, W + 400, 300);
  c.strokeStyle = 'rgba(0,0,0,0.35)'; c.lineWidth = 2;
  for (let k = -10; k <= 10; k++) { c.beginPath(); c.moveTo(640 + k * 70, 565); c.lineTo(640 + k * 170, 900); c.stroke(); }
  for (let k = 0; k < 5; k++) { const y = 565 + (k * k + k) * 9; c.beginPath(); c.moveTo(-200, y); c.lineTo(W + 200, y); c.stroke(); }
  c.fillStyle = '#1c1612'; c.fillRect(-200, 555, W + 400, 12); // baseboard

  // window
  const wx = 985, wy = 205, ww = 215, wh = 265;
  gr = c.createLinearGradient(0, wy, 0, wy + wh);
  gr.addColorStop(0, '#0b1426'); gr.addColorStop(1, '#1d2c45');
  c.fillStyle = gr; c.fillRect(wx, wy, ww, wh);
  // distant city lights through the glass
  for (let i = 0; i < 14; i++) {
    const lx = wx + hrand(i + 5) * ww, ly = wy + wh * 0.45 + hrand(i + 9) * wh * 0.5;
    const rg = c.createRadialGradient(lx, ly, 0, lx, ly, 10 + hrand(i) * 14);
    rg.addColorStop(0, i % 4 ? 'rgba(255,190,110,0.5)' : 'rgba(160,200,255,0.4)'); rg.addColorStop(1, 'rgba(0,0,0,0)');
    c.fillStyle = rg; c.fillRect(lx - 30, ly - 30, 60, 60);
  }
  if (o.stars) { // after the rain
    for (let i = 0; i < 30; i++) {
      c.fillStyle = `rgba(255,255,255,${o.stars * (0.4 + 0.6 * hrand(i + 3)) * (0.7 + 0.3 * Math.sin(t * 2 + i))})`;
      c.fillRect(wx + hrand(i + 70) * ww, wy + hrand(i + 80) * wh * 0.45, 1.6, 1.6);
    }
  }
  c.save(); c.beginPath(); c.rect(wx, wy, ww, wh); c.clip();
  drawRain(c, t, (o.rain ?? 1) * 0.5, { x0: wx, y0: wy, w: ww, h: wh, len: 18, color: 'rgba(170,200,240,0.3)' });
  // drops sliding on the glass
  for (let i = 0; i < 16; i++) {
    const dx = wx + hrand(i + 100) * ww, sp = 10 + hrand(i + 120) * 30;
    const dy = wy + ((hrand(i + 110) * wh + t * sp) % wh);
    c.fillStyle = 'rgba(200,220,255,0.35)'; c.beginPath(); c.arc(dx, dy, 2 + hrand(i) * 2, 0, TAU); c.fill();
    c.strokeStyle = 'rgba(200,220,255,0.12)'; c.lineWidth = 1.5; c.beginPath(); c.moveTo(dx, dy); c.lineTo(dx, dy - 25); c.stroke();
  }
  c.restore();
  c.strokeStyle = '#3b3027'; c.lineWidth = 12; c.strokeRect(wx, wy, ww, wh);
  c.lineWidth = 7; c.beginPath(); c.moveTo(wx + ww / 2, wy); c.lineTo(wx + ww / 2, wy + wh); c.moveTo(wx, wy + wh * 0.45); c.lineTo(wx + ww, wy + wh * 0.45); c.stroke();
  c.fillStyle = '#463a2f'; c.fillRect(wx - 16, wy + wh + 4, ww + 32, 12);
  // blue light from the window on the floor
  c.save(); c.globalCompositeOperation = 'lighter';
  gr = c.createLinearGradient(wx, 0, wx - 300, 0);
  gr.addColorStop(0, 'rgba(60,90,140,0.16)'); gr.addColorStop(1, 'rgba(60,90,140,0)');
  c.fillStyle = gr;
  c.beginPath(); c.moveTo(wx, wy); c.lineTo(wx + ww, wy); c.lineTo(wx + ww - 120, 720); c.lineTo(wx - 420, 720); c.closePath(); c.fill();
  c.restore();

  // door (hinged on its left edge, opens inward toward the viewer)
  const dx0 = 110, dy0 = 232, dw = 180, dh = 333;
  const open = o.door ?? 0.15;
  gr = c.createLinearGradient(0, dy0, 0, dy0 + dh);
  gr.addColorStop(0, '#0a1120'); gr.addColorStop(1, '#1b2a40');
  c.fillStyle = gr; c.fillRect(dx0, dy0, dw, dh);
  // the street outside the doorway
  const sl = c.createRadialGradient(dx0 + dw * 0.7, dy0 + 60, 0, dx0 + dw * 0.7, dy0 + 60, 200);
  sl.addColorStop(0, 'rgba(255,200,130,0.35)'); sl.addColorStop(1, 'rgba(255,200,130,0)');
  c.fillStyle = sl; c.fillRect(dx0, dy0, dw, dh);
  c.save(); c.beginPath(); c.rect(dx0, dy0, dw, dh); c.clip();
  drawRain(c, t, (o.rain ?? 1) * 0.35, { x0: dx0, y0: dy0, w: dw, h: dh, len: 20 });
  if (o.doorway) o.doorway(c);
  c.restore();
  // door panel
  const pw = dw * Math.cos(open * Math.PI * 0.5);
  if (pw > 2) {
    c.fillStyle = '#3a2a1f';
    c.beginPath(); c.moveTo(dx0, dy0); c.lineTo(dx0 + pw, dy0 + 8 * open); c.lineTo(dx0 + pw, dy0 + dh + 6 * open); c.lineTo(dx0, dy0 + dh); c.closePath(); c.fill();
    c.strokeStyle = '#2a1e16'; c.lineWidth = 3;
    c.strokeRect(dx0 + pw * 0.15, dy0 + 30, pw * 0.7, dh * 0.38); c.strokeRect(dx0 + pw * 0.15, dy0 + dh * 0.5, pw * 0.7, dh * 0.4);
    c.fillStyle = '#9a8460'; c.beginPath(); c.arc(dx0 + pw * 0.88, dy0 + dh * 0.52, 4, 0, TAU); c.fill();
  }
  c.strokeStyle = '#2c2119'; c.lineWidth = 10; c.strokeRect(dx0 - 5, dy0 - 5, dw + 10, dh + 5);
  // blue spill from the open door onto the floor
  if (open > 0.2) {
    c.save(); c.globalCompositeOperation = 'lighter';
    c.fillStyle = `rgba(70,100,150,${0.12 * open})`;
    c.beginPath(); c.moveTo(dx0, dy0 + dh); c.lineTo(dx0 + dw, dy0 + dh); c.lineTo(dx0 + dw + 260, 720); c.lineTo(dx0 - 40, 720); c.closePath(); c.fill();
    c.restore();
  }

  // eviction notice taped to the wall
  c.save(); c.translate(355, 300); c.rotate(-0.05);
  c.fillStyle = '#c9c2ae'; c.fillRect(0, 0, 54, 70);
  c.fillStyle = '#7a1f1a'; c.font = 'bold 7px "Liberation Sans"'; c.fillText('NOTICE TO', 7, 13); c.fillText('VACATE', 12, 22);
  c.fillStyle = 'rgba(40,40,40,0.6)'; for (let k = 0; k < 6; k++) c.fillRect(7, 30 + k * 6, 40 - (k % 2) * 10, 2);
  c.fillStyle = 'rgba(230,230,200,0.5)'; c.fillRect(20, -4, 14, 7);
  c.restore();
  // mattress and a crumpled sheet
  c.fillStyle = '#4b4a46'; c.beginPath(); c.roundRect(360, 560, 260, 34, 8); c.fill();
  c.fillStyle = '#5d5d58'; c.beginPath(); c.moveTo(380, 562); c.quadraticCurveTo(450, 545, 520, 560); c.quadraticCurveTo(560, 575, 600, 566); c.lineTo(590, 590); c.lineTo(390, 590); c.closePath(); c.fill();
  // empty bowl
  c.fillStyle = '#7a756c'; c.beginPath(); c.ellipse(700, 612, 24, 8, 0, 0, TAU); c.fill();
  c.fillStyle = '#3a3733'; c.beginPath(); c.ellipse(700, 609, 18, 5, 0, 0, TAU); c.fill();

  // bulb
  const bx = 640 + Math.sin(t * 0.7) * 6, by = 140;
  c.strokeStyle = '#111'; c.lineWidth = 2; c.beginPath(); c.moveTo(640, -200); c.lineTo(bx, by - 10); c.stroke();
  c.fillStyle = '#ffe9b8'; c.beginPath(); c.arc(bx, by, 9, 0, TAU); c.fill();
  return { bulb: [bx, by], window: [wx + ww / 2, wy + wh / 2] };
}
function roomLight(c, t, bulb, k = 1) {
  c.save(); c.globalCompositeOperation = 'lighter';
  const fl = 1 + 0.03 * Math.sin(t * 9) + 0.02 * noise1(t * 4);
  let gr = c.createRadialGradient(bulb[0], bulb[1], 0, bulb[0], bulb[1], 520 * fl);
  gr.addColorStop(0, `rgba(255,214,150,${0.32 * k})`); gr.addColorStop(0.3, `rgba(255,190,120,${0.12 * k})`); gr.addColorStop(1, 'rgba(255,170,90,0)');
  c.fillStyle = gr; c.fillRect(-300, -300, W + 600, H + 600);
  gr = c.createRadialGradient(bulb[0], bulb[1], 0, bulb[0], bulb[1], 40);
  gr.addColorStop(0, `rgba(255,240,200,${0.9 * k})`); gr.addColorStop(1, 'rgba(255,220,160,0)');
  c.fillStyle = gr; c.fillRect(bulb[0] - 40, bulb[1] - 40, 80, 80);
  // dust motes floating in the light
  for (let i = 0; i < 40; i++) {
    const a = hrand(i + 200) * TAU, r = 60 + hrand(i + 300) * 320;
    const x = bulb[0] + Math.cos(a) * r + noise1(t * 0.2 + i) * 30, y = bulb[1] + 60 + Math.abs(Math.sin(a)) * r + noise1(t * 0.15 + i + 9) * 30;
    c.fillStyle = `rgba(255,230,190,${0.25 * k * (0.5 + 0.5 * Math.sin(t + i))})`;
    c.fillRect(x, y, 2, 2);
  }
  c.restore();
}

// ------------------------------------------------------------------ the street
function drawSky(c, t, o = {}) {
  const gr = c.createLinearGradient(0, -200, 0, 560);
  gr.addColorStop(0, mix('#060912', '#0b1430', o.clear || 0)); gr.addColorStop(1, mix('#1b2133', '#26304f', o.clear || 0));
  c.fillStyle = gr; c.fillRect(-400, -400, W + 800, 1000);
  const clear = o.clear || 0;
  if (clear > 0) {
    for (let i = 0; i < 160; i++) {
      const x = hrand(i + 400) * (W + 400) - 200, y = hrand(i + 500) * 520 - 200;
      const a = clear * (0.3 + 0.7 * hrand(i + 600)) * (0.75 + 0.25 * Math.sin(t * (1 + hrand(i)) + i));
      c.fillStyle = `rgba(235,240,255,${a})`; c.fillRect(x, y, 1.6, 1.6);
    }
    // moon
    const mx = 980, my = 40;
    const mg = c.createRadialGradient(mx, my, 0, mx, my, 160);
    mg.addColorStop(0, `rgba(220,230,255,${0.35 * clear})`); mg.addColorStop(1, 'rgba(200,210,255,0)');
    c.fillStyle = mg; c.fillRect(mx - 160, my - 160, 320, 320);
    c.fillStyle = `rgba(240,242,255,${clear})`; c.beginPath(); c.arc(mx, my, 26, 0, TAU); c.fill();
  }
  // clouds drifting (they part as `clear` rises)
  for (let i = 0; i < 18; i++) {
    const r = 120 + hrand(i + 20) * 160;
    const side = i % 2 ? 1 : -1;
    const x = ((hrand(i + 30) * (W + 600) + t * (6 + hrand(i) * 8)) % (W + 600)) - 300 + side * clear * 500;
    const y = -60 + hrand(i + 40) * 300;
    const cg = c.createRadialGradient(x, y, 0, x, y, r);
    cg.addColorStop(0, `rgba(40,46,64,${0.55 * (1 - clear * 0.85)})`); cg.addColorStop(1, 'rgba(40,46,64,0)');
    c.fillStyle = cg; c.fillRect(x - r, y - r, r * 2, r * 2);
  }
}
function building(c, x, y, w, h, color, seed, lit = 0.3, windowsLit = null) {
  c.fillStyle = color; c.fillRect(x, y, w, h);
  const cols = Math.max(2, Math.floor(w / 34)), rows = Math.max(2, Math.floor(h / 46));
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const k = seed * 100 + i * 10 + j;
    const wx = x + 10 + i * (w - 20) / cols, wy = y + 14 + j * (h - 30) / rows;
    let on = hrand(k) < lit;
    let a = on ? 0.55 + 0.4 * hrand(k + 1) : 0;
    if (windowsLit) a = Math.max(a, windowsLit(wx, wy, k));
    c.fillStyle = a > 0 ? `rgba(255,${190 + 30 * hrand(k + 2)},120,${a})` : 'rgba(10,12,20,0.6)';
    c.fillRect(wx, wy, 14, 20);
  }
}
const STREET = { door: [935, 395, 70, 175], win: [785, 420, 120, 95], lamp: [560, 330], shop: [1135, 420, 80, 150] };
function drawStreet(c, t, o = {}) {
  drawSky(c, t, o);
  // far skyline
  for (let i = 0; i < 14; i++) {
    const w = 80 + hrand(i + 700) * 120, h = 160 + hrand(i + 710) * 260;
    building(c, i * 110 - 220, 560 - h - 40, w, h, '#121624', i + 20, 0.18, o.windowsLit);
  }
  // near buildings: left block, and the singer's building on the right
  building(c, -200, 210, 360, 350, '#1d1d24', 3, 0.15, o.windowsLit);
  building(c, 160, 260, 340, 300, '#22202a', 4, 0.12, o.windowsLit);
  c.fillStyle = '#2a2622'; c.fillRect(700, 180, 780, 400);
  c.fillStyle = 'rgba(0,0,0,0.25)'; for (let k = 0; k < 18; k++) c.fillRect(700, 190 + k * 22, 780, 2); // brick courses
  for (let i = 0; i < 7; i++) for (let j = 0; j < 3; j++) {
    const k = 900 + i * 7 + j, wx = 730 + i * 80, wy = 210 + j * 62;
    const a = Math.max(hrand(k) < 0.2 ? 0.6 : 0, o.windowsLit ? o.windowsLit(wx, wy, k) : 0);
    c.fillStyle = a ? `rgba(255,200,125,${a})` : '#14161d'; c.fillRect(wx, wy, 30, 40);
  }
  // the singer's window — warm
  const [wx, wy, ww, wh] = STREET.win;
  const wg = c.createLinearGradient(0, wy, 0, wy + wh);
  wg.addColorStop(0, '#f2b766'); wg.addColorStop(1, '#a8652f');
  c.fillStyle = wg; c.fillRect(wx, wy, ww, wh);
  // the singer's silhouette, swaying as she sings
  if (o.singerSil !== false) {
    const sway = Math.sin(t * 0.9) * 3;
    c.fillStyle = 'rgba(40,20,15,0.85)';
    c.beginPath(); c.arc(wx + 50 + sway, wy + 42, 15, 0, TAU); c.fill();
    c.beginPath(); c.moveTo(wx + 22 + sway, wy + wh); c.quadraticCurveTo(wx + 26 + sway, wy + 55, wx + 50 + sway, wy + 55); c.quadraticCurveTo(wx + 76 + sway, wy + 55, wx + 80 + sway, wy + wh); c.fill();
    c.beginPath(); c.moveTo(wx + 36 + sway, wy + 40); c.quadraticCurveTo(wx + 30 + sway, wy + 70, wx + 34 + sway, wy + 80); c.lineTo(wx + 66 + sway, wy + 80); c.quadraticCurveTo(wx + 70 + sway, wy + 60, wx + 64 + sway, wy + 40); c.fill();
  }
  if (o.windowLight) {
    c.save(); c.globalCompositeOperation = 'lighter';
    const lg = c.createRadialGradient(wx + ww / 2, wy + wh / 2, 0, wx + ww / 2, wy + wh / 2, 120);
    lg.addColorStop(0, `rgba(255,220,160,${o.windowLight})`); lg.addColorStop(1, 'rgba(255,220,160,0)');
    c.fillStyle = lg; c.fillRect(wx - 120, wy - 120, ww + 240, wh + 240); c.restore();
  }
  c.strokeStyle = '#3a3029'; c.lineWidth = 6; c.strokeRect(wx, wy, ww, wh);
  c.lineWidth = 4; c.beginPath(); c.moveTo(wx + ww / 2, wy); c.lineTo(wx + ww / 2, wy + wh); c.stroke();
  // the door, ajar with warm light
  const [dx, dy, dw, dh] = STREET.door;
  c.fillStyle = '#d99a52'; c.fillRect(dx, dy, dw, dh);
  const ajar = o.doorAjar ?? 0.25;
  c.fillStyle = '#2e2119'; c.fillRect(dx + dw * ajar, dy, dw * (1 - ajar), dh);
  c.strokeStyle = '#1d1510'; c.lineWidth = 6; c.strokeRect(dx, dy, dw, dh);
  if (o.inDoor) o.inDoor(c);
  // the shop doorway on the right, where someone sleeps in the cold
  const [sx, sy, sw, sh] = STREET.shop;
  c.fillStyle = '#121014'; c.fillRect(sx, sy, sw, sh);
  c.strokeStyle = '#1b1612'; c.lineWidth = 6; c.strokeRect(sx, sy, sw, sh);
  // sidewalk and street
  c.fillStyle = '#25262b'; c.fillRect(-400, 570, W + 800, 50);
  c.fillStyle = '#1a1b20'; c.fillRect(-400, 618, W + 800, 6);
  const sg = c.createLinearGradient(0, 624, 0, 760);
  sg.addColorStop(0, '#15171d'); sg.addColorStop(1, '#0b0c10');
  c.fillStyle = sg; c.fillRect(-400, 624, W + 800, 300);
  // reflections on wet asphalt
  c.save(); c.globalCompositeOperation = 'lighter';
  const wet = o.wet ?? 1;
  for (const [lx, col, wdt] of [[STREET.win[0] + 60, '255,190,110', 70], [STREET.door[0] + 20, '255,190,110', 30], [STREET.lamp[0], '255,210,150', 50]]) {
    for (let k = 0; k < 14; k++) {
      const y = 628 + k * 9, a = 0.16 * wet * (1 - k / 14);
      const ww = wdt * (0.6 + 0.5 * hrand(k + lx)) * (1 + 0.15 * noise1(t * 1.5 + k));
      const rg = c.createLinearGradient(lx - ww / 2, 0, lx + ww / 2, 0);
      rg.addColorStop(0, `rgba(${col},0)`); rg.addColorStop(0.5, `rgba(${col},${a})`); rg.addColorStop(1, `rgba(${col},0)`);
      c.fillStyle = rg; c.fillRect(lx - ww / 2 + noise1(t * 2 + k) * 4, y, ww, 4);
    }
  }
  c.restore();
  // lamp post
  const [lx, ly] = STREET.lamp;
  c.fillStyle = '#0d0e12'; c.fillRect(lx - 4, ly, 8, 260); c.fillRect(lx - 28, ly - 6, 56, 10);
  c.save(); c.globalCompositeOperation = 'lighter';
  const lgr = c.createRadialGradient(lx, ly + 4, 0, lx, ly + 4, 260);
  lgr.addColorStop(0, 'rgba(255,215,160,0.45)'); lgr.addColorStop(1, 'rgba(255,200,140,0)');
  c.fillStyle = lgr;
  c.beginPath(); c.moveTo(lx - 20, ly + 4); c.lineTo(lx + 20, ly + 4); c.lineTo(lx + 170, 600); c.lineTo(lx - 170, 600); c.closePath(); c.fill();
  c.restore();
}

// ------------------------------------------------------------------ storm (inside the mind)
function drawStorm(c, t, o = {}) {
  const k = o.amount ?? 1, sp = o.speed ?? 1, gold = o.gold || 0, cx = o.cx ?? 640, cy = o.cy ?? 330;
  const tt = o.tt ?? t * sp;
  const base = c.createRadialGradient(cx, cy, 50, cx, cy, 900);
  base.addColorStop(0, mix('#1a1222', '#f5d9a0', gold)); base.addColorStop(1, mix('#050308', '#6b4a3a', gold));
  c.save(); c.globalAlpha = k;
  c.fillStyle = base; c.fillRect(-300, -300, W + 600, H + 600);
  // swirling cloud puffs: dark bodies with faintly lit upper edges
  const flick = o.flicker ? Math.max(0, noise1(tt * 3.1) * 1.6 - 0.9) : 0; // distant sheet lightning
  for (let i = 0; i < 54; i++) {
    const ring = 100 + hrand(i + 1) * 640;
    const a0 = hrand(i + 2) * TAU, w0 = (0.05 + hrand(i + 3) * 0.08) * (i % 3 ? 1 : -0.6);
    const a = a0 + tt * w0;
    const x = cx + Math.cos(a) * ring * 1.35, y = cy + Math.sin(a) * ring * 0.75 + noise1(tt * 0.3 + i) * 30;
    const r = 90 + hrand(i + 4) * 160;
    const dark = hrand(i + 5);
    const cg = c.createRadialGradient(x, y, 0, x, y, r);
    cg.addColorStop(0, mix(dark > 0.5 ? '#16101a' : '#2a2030', dark > 0.5 ? '#ffdca0' : '#fff0d0', gold, 0.9));
    cg.addColorStop(0.6, mix(dark > 0.5 ? '#1c1422' : '#30243a', '#ffe2b0', gold, 0.5));
    cg.addColorStop(1, 'rgba(20,10,20,0)');
    c.fillStyle = cg; c.fillRect(x - r, y - r, r * 2, r * 2);
    // lit rim
    const lg = c.createRadialGradient(x - r * 0.15, y - r * 0.45, r * 0.2, x, y - r * 0.2, r * 0.9);
    const la = (0.08 + 0.25 * flick) * (1 - gold);
    lg.addColorStop(0, `rgba(150,130,190,${la})`); lg.addColorStop(1, 'rgba(150,130,190,0)');
    c.fillStyle = lg; c.fillRect(x - r, y - r, r * 2, r * 2);
  }
  // red undertone when the demon is close
  if (o.red) {
    const rg = c.createRadialGradient(cx, cy + 250, 0, cx, cy + 250, 700);
    rg.addColorStop(0, `rgba(160,20,10,${0.35 * o.red})`); rg.addColorStop(1, 'rgba(80,0,0,0)');
    c.fillStyle = rg; c.fillRect(-300, -300, W + 600, H + 600);
  }
  c.restore();
}
function lightningBolt(c, seed, x0, y0, len, a) {
  if (a <= 0) return;
  const pts = [[x0, y0]];
  let x = x0, y = y0;
  for (let i = 0; i < 14; i++) { x += (hrand(seed * 31 + i) - 0.5) * 70; y += len / 14; pts.push([x, y]); }
  const path = () => { c.beginPath(); c.moveTo(pts[0][0], pts[0][1]); for (const p of pts) c.lineTo(p[0], p[1]); };
  c.save(); c.globalCompositeOperation = 'lighter'; c.lineJoin = 'round';
  path(); c.strokeStyle = `rgba(170,150,255,${0.25 * a})`; c.lineWidth = 16; c.stroke();
  path(); c.strokeStyle = `rgba(220,210,255,${0.6 * a})`; c.lineWidth = 5; c.stroke();
  path(); c.strokeStyle = `rgba(255,255,255,${a})`; c.lineWidth = 1.8; c.stroke();
  // a branch
  const b = pts[5 + Math.floor(hrand(seed) * 5)];
  c.beginPath(); c.moveTo(b[0], b[1]);
  let bx = b[0], by = b[1];
  for (let i = 0; i < 5; i++) { bx += (hrand(seed * 17 + i) - 0.2) * 50 * (seed % 2 ? 1 : -1); by += len / 18; c.lineTo(bx, by); }
  c.strokeStyle = `rgba(230,220,255,${0.6 * a})`; c.lineWidth = 1.5; c.stroke();
  c.restore();
}
// how lit the scene is by the latest lightning strike (0..1) and which strike
function strike(t, times) {
  let best = 0, idx = -1;
  for (let i = 0; i < times.length; i++) {
    const d = t - times[i];
    if (d >= -0.05 && d < 1.2) {
      const flick = d < 0.25 ? (0.7 + 0.3 * Math.sin(d * 90)) : 1;
      const v = Math.exp(-Math.max(d, 0) / 0.22) * flick;
      if (v > best) { best = v; idx = i; }
    }
  }
  return [best, idx];
}

// a scene of memory painted into the clouds, lit by lightning
function memoryInCloud(c, which, t, a, cx, cy, sc) {
  if (a <= 0.01) return;
  c.save(); c.translate(cx, cy); c.scale(sc, sc);
  c.globalAlpha = a;
  const glow = c.createRadialGradient(0, 0, 0, 0, 0, 230);
  glow.addColorStop(0, 'rgba(200,190,255,0.55)'); glow.addColorStop(1, 'rgba(200,190,255,0)');
  c.fillStyle = glow; c.beginPath(); c.arc(0, 0, 230, 0, TAU); c.fill();
  const col = '#0d0810';
  if (which === 0) { // someone on the ground, people stepping past
    sil(c, -40, 60, 120, { lying: true, color: col });
    for (let i = 0; i < 4; i++) sil(c, -150 + i * 85 + ((t * 30) % 85), 70, 150, { walk: t * 5 + i, color: col, flip: i % 2 === 1 });
  } else if (which === 1) { // a hand pulls the bread away from a reaching hand
    c.fillStyle = col;
    c.beginPath(); c.ellipse(-60, -10, 75, 40, -0.2, 0, TAU); c.fill(); // hand
    c.beginPath(); c.ellipse(-60, -60, 60, 26, -0.1, 0, TAU); c.fill(); // bread
    c.fillRect(-200, -30, 140, 40);
    c.save(); c.translate(120, 40); c.rotate(-0.3);
    c.beginPath(); c.ellipse(0, 0, 45, 22, 0, 0, TAU); c.fill(); c.fillRect(30, -10, 140, 22);
    for (let k = 0; k < 4; k++) { c.fillRect(-60, -18 + k * 10, 30, 6); }
    c.restore();
  } else if (which === 2) { // a door shut on someone with a suitcase
    c.fillStyle = col; c.fillRect(30, -150, 100, 220);
    c.fillStyle = 'rgba(255,230,180,0.7)'; c.fillRect(30, -150, 8, 220);
    sil(c, -30, 70, 150, { suitcase: true, color: col, headDown: true });
  } else if (which === 3) { // a line outside a shelter that is FULL
    c.fillStyle = col; c.fillRect(110, -140, 90, 210);
    c.fillStyle = 'rgba(230,220,255,0.9)'; c.font = 'bold 22px "Liberation Sans"'; c.fillText('FULL', 126, -100);
    for (let i = 0; i < 6; i++) sil(c, 70 - i * 45, 70, 130 + (i % 2) * 10, { color: col, headDown: i % 2 === 0 });
  } else if (which === 4) { // a circle of turned backs around someone on their knees
    sil(c, 0, 50, 80, { sitting: true, color: col, headDown: true });
    for (let i = 0; i < 6; i++) { const a = i / 6 * TAU; sil(c, Math.cos(a) * 150, 70 + Math.sin(a) * 30, 150 + Math.sin(a) * 20, { color: col }); }
  }
  c.restore();
}

// the giant shadow-demon made of storm behind him
function drawDemon(c, t, a, cx, cy, sc, o = {}) {
  if (a <= 0.01) return;
  c.save(); c.translate(cx, cy); c.scale(sc, sc); c.globalAlpha = a;
  const gold = o.gold || 0;
  const body = mix('#050205', '#3a2a20', gold);
  c.fillStyle = body;
  // head and shoulders
  c.beginPath();
  c.moveTo(-700, 460); c.quadraticCurveTo(-640, 140, -380, 90);
  c.quadraticCurveTo(-360, -230, 0, -250); c.quadraticCurveTo(360, -230, 380, 90);
  c.quadraticCurveTo(640, 140, 700, 460); c.closePath(); c.fill();
  // horns
  for (const s of [-1, 1]) {
    c.beginPath(); c.moveTo(s * 200, -190);
    c.bezierCurveTo(s * 420, -300, s * 520, -500, s * 380, -640);
    c.bezierCurveTo(s * 430, -480, s * 330, -340, s * 110, -230); c.closePath(); c.fill();
  }
  // smoky edge
  for (let i = 0; i < 30; i++) {
    const ang = Math.PI + i / 29 * Math.PI, r = 330 + noise1(t * 0.8 + i) * 50;
    const x = Math.cos(ang) * r * 1.5, y = Math.sin(ang) * r * 0.85 + 100;
    const sg = c.createRadialGradient(x, y, 0, x, y, 110);
    sg.addColorStop(0, rgba('#050205', 0.6 * (1 - gold))); sg.addColorStop(1, 'rgba(5,2,5,0)');
    c.fillStyle = sg; c.fillRect(x - 110, y - 110, 220, 220);
  }
  // eyes, far apart, above and beside his head
  const ey = o.eyes ?? 1;
  if (ey > 0 && gold < 0.5) {
    c.globalCompositeOperation = 'lighter';
    for (const s of [-1, 1]) {
      const exx = s * 235, eyy = -95;
      const eg = c.createRadialGradient(exx, eyy, 0, exx, eyy, 90);
      eg.addColorStop(0, `rgba(255,90,40,${ey})`); eg.addColorStop(0.3, `rgba(255,30,10,${0.6 * ey})`); eg.addColorStop(1, 'rgba(255,0,0,0)');
      c.fillStyle = eg; c.fillRect(exx - 90, eyy - 90, 180, 180);
      c.fillStyle = `rgba(255,230,200,${ey})`;
      c.beginPath(); c.moveTo(exx - s * 45, eyy - 5); c.quadraticCurveTo(exx, eyy - 22, exx + s * 45, eyy + 8); c.quadraticCurveTo(exx, eyy + 6, exx - s * 45, eyy - 5); c.fill();
    }
  }
  c.restore();
}

// ------------------------------------------------------------------ the spark
function drawSpark(c, x, y, size, t, o = {}) {
  if (size <= 0) return;
  c.save(); c.globalCompositeOperation = 'lighter';
  const pulseK = 1 + 0.12 * Math.sin(t * 2.2) + 0.05 * Math.sin(t * 7.3);
  const s = size * pulseK;
  // soft rays
  if (o.rays) {
    for (let i = 0; i < 12; i++) {
      const a = i / 12 * TAU + t * 0.05 + (i % 2) * 0.1;
      const L = s * (14 + 6 * Math.sin(t * 0.7 + i * 1.7)) * o.rays;
      const rg = c.createLinearGradient(x, y, x + Math.cos(a) * L, y + Math.sin(a) * L);
      rg.addColorStop(0, `rgba(255,230,170,${0.16 * o.rays})`); rg.addColorStop(1, 'rgba(255,220,150,0)');
      c.fillStyle = rg;
      c.beginPath(); c.moveTo(x, y);
      c.lineTo(x + Math.cos(a - 0.06) * L, y + Math.sin(a - 0.06) * L);
      c.lineTo(x + Math.cos(a + 0.06) * L, y + Math.sin(a + 0.06) * L); c.closePath(); c.fill();
    }
  }
  let gr = c.createRadialGradient(x, y, 0, x, y, s * 12);
  gr.addColorStop(0, 'rgba(255,240,200,0.55)'); gr.addColorStop(0.25, 'rgba(255,210,140,0.18)'); gr.addColorStop(1, 'rgba(255,190,110,0)');
  c.fillStyle = gr; c.beginPath(); c.arc(x, y, s * 12, 0, TAU); c.fill();
  gr = c.createRadialGradient(x, y, 0, x, y, s * 2.2);
  gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.4, 'rgba(255,248,225,0.9)'); gr.addColorStop(1, 'rgba(255,230,170,0)');
  c.fillStyle = gr; c.beginPath(); c.arc(x, y, s * 2.2, 0, TAU); c.fill();
  // cross glints
  const gl = s * (5 + 1.5 * Math.sin(t * 3));
  c.strokeStyle = 'rgba(255,250,235,0.85)'; c.lineWidth = Math.max(1, s * 0.18);
  c.save(); c.translate(x, y); c.rotate(t * 0.15);
  for (let k = 0; k < 2; k++) {
    c.rotate(Math.PI / 2);
    const lg = c.createLinearGradient(-gl, 0, gl, 0);
    lg.addColorStop(0, 'rgba(255,250,235,0)'); lg.addColorStop(0.5, 'rgba(255,250,235,0.9)'); lg.addColorStop(1, 'rgba(255,250,235,0)');
    c.strokeStyle = lg; c.beginPath(); c.moveTo(-gl, 0); c.lineTo(gl, 0); c.stroke();
  }
  c.restore();
  c.restore();
}
// golden motes / embers drifting
function motes(c, t, cx, cy, n, spread, o = {}) {
  c.save(); c.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const life = o.life || 4, born = hrand(i + 900) * life;
    const age = ((t + born) % life) / life;
    const a0 = hrand(i + 910) * TAU, r0 = spread * (0.2 + hrand(i + 920));
    let x, y;
    if (o.inward) { const r = r0 * (1 - age); x = cx + Math.cos(a0 + age) * r; y = cy + Math.sin(a0 + age) * r * 0.7; }
    else { x = cx + Math.cos(a0) * r0 * 0.5 + noise1(t * 0.7 + i) * 20; y = cy + Math.sin(a0) * r0 * 0.3 - age * (o.rise || 260); }
    const al = Math.sin(age * Math.PI) * (o.alpha || 0.8);
    const col = o.color || '255,215,140';
    c.fillStyle = `rgba(${col},${al})`;
    const sz = (o.size || 2.4) * (0.6 + hrand(i + 930));
    c.beginPath(); c.arc(x, y, sz, 0, TAU); c.fill();
  }
  c.restore();
}

// ------------------------------------------------------------------ overlays
let GRAIN = null;
function makeGrain() {
  GRAIN = [];
  for (let k = 0; k < 4; k++) {
    const cnv = document.createElement('canvas'); cnv.width = 256; cnv.height = 256;
    const x = cnv.getContext('2d'), im = x.createImageData(256, 256);
    for (let i = 0; i < im.data.length; i += 4) { const v = Math.floor(hrand(i * 0.37 + k * 1000) * 255); im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    x.putImageData(im, 0, 0); GRAIN.push(cnv);
  }
}
function overlays(t, o = {}) {
  g.setTransform(1, 0, 0, 1, 0, 0);
  // vignette
  const vg = g.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(0,0,0,${o.vignette ?? 0.6})`);
  g.fillStyle = vg; g.fillRect(0, 0, W, H);
  // grain
  if (!GRAIN) makeGrain();
  const fr = Math.floor(t * 24);
  g.save(); g.globalAlpha = o.grain ?? 0.045; g.globalCompositeOperation = 'overlay';
  const pat = g.createPattern(GRAIN[fr % 4], 'repeat');
  g.translate(-(fr * 37 % 256), -(fr * 91 % 256));
  g.fillStyle = pat; g.fillRect(0, 0, W + 256, H + 256);
  g.restore();
}
function flash(a, col = '235,230,255') {
  if (a <= 0) return;
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = `rgba(${col},${a})`; g.fillRect(0, 0, W, H);
}
function fade(a) { if (a > 0) { g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = `rgba(0,0,0,${clamp(a)})`; g.fillRect(0, 0, W, H); } }

function subtitle(t) {
  if (!TL || !TL.subtitles) return;
  g.setTransform(1, 0, 0, 1, 0, 0);
  const active = TL.cues.filter(q => t >= q.start - 0.1 && t <= q.end + 0.5);
  let y = H - 52;
  for (const q of active.reverse()) {
    const a = sstep(t, q.start - 0.1, q.start + 0.15) * (1 - sstep(t, q.end + 0.2, q.end + 0.5));
    const inner = q.speaker === 'listener', wh = q.speaker === 'whisper';
    g.font = wh ? 'italic 24px "Liberation Serif"' : inner ? 'italic 31px "Liberation Serif"' : '31px "Liberation Serif"';
    g.textAlign = 'center';
    g.shadowColor = 'rgba(0,0,0,0.9)'; g.shadowBlur = 8;
    g.fillStyle = wh ? `rgba(190,170,210,${0.75 * a})` : `rgba(250,246,238,${a})`;
    g.fillText(q.text, W / 2, y);
    g.shadowBlur = 0;
    y -= wh ? 32 : 40;
  }
  g.textAlign = 'left';
}
function titleText(text, y, size, a, o = {}) {
  if (a <= 0) return;
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.font = `${o.italic ? 'italic ' : ''}${size}px "FreeSerif", "Liberation Serif"`;
  g.textAlign = 'center';
  if ('letterSpacing' in g) g.letterSpacing = (o.spacing || 0) + 'px';
  g.shadowColor = o.glow || 'rgba(0,0,0,0.8)'; g.shadowBlur = o.blur ?? 12;
  g.fillStyle = o.color ? o.color.replace('A', a) : `rgba(245,238,225,${a})`;
  g.fillText(text, W / 2, y);
  g.shadowBlur = 0; g.textAlign = 'left';
  if ('letterSpacing' in g) g.letterSpacing = '0px';
}
