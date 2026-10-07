// Backgrounds, camera, atmosphere and overlays.

// camera: {x, y, z} = world point at screen centre, zoom
function applyCam(c, cam, p = 1) {
  const z = lerp(1, cam.z, p);
  c.translate(W / 2, H / 2); c.scale(z, z);
  c.translate(-(cam.x * p + 960 * (1 - p)), -(cam.y * p + 540 * (1 - p)));
}
function layer(c, cam, p, fn) { c.save(); applyCam(c, cam, p); fn(); c.restore(); }

// ---- precomputed scatter data
const R = mulberry(7);
const FAR_TREES = Array.from({ length: 60 }, (_, i) => ({ x: -900 + i * 70 + R() * 40, r: 60 + R() * 50, h: R() * 60 }));
const MID_TREES = Array.from({ length: 9 }, (_, i) => ({ x: -500 + i * 420 + R() * 160, r: 110 + R() * 50, h: R() * 50 }));
const TUFTS = Array.from({ length: 260 }, () => ({ x: -800 + R() * 3800, y: 690 + Math.pow(R(), 1.6) * 520, s: .6 + R() * .9, c: R() }));
const FLOWERS = Array.from({ length: 90 }, () => ({ x: -800 + R() * 3800, y: 720 + R() * 450, c: Math.floor(R() * 4), s: .7 + R() * .6 }));
const FLOWER_COLS = ['#f6f1e1', '#f2c94c', '#e98a9a', '#b9a2e6'];

let PAPER = null;
function paper() {
  if (PAPER) return PAPER;
  PAPER = document.createElement('canvas'); PAPER.width = 960; PAPER.height = 540;
  const p = PAPER.getContext('2d'), img = p.createImageData(960, 540), r = mulberry(99);
  for (let i = 0; i < img.data.length; i += 4) {
    const v = 200 + r() * 55; img.data[i] = v; img.data[i + 1] = v * .97; img.data[i + 2] = v * .9; img.data[i + 3] = 255;
  }
  p.putImageData(img, 0, 0); return PAPER;
}
function finish(c, opt = {}) {
  c.save(); c.setTransform(window.SCALE || 1, 0, 0, window.SCALE || 1, 0, 0);
  c.globalCompositeOperation = 'multiply'; c.globalAlpha = .16; c.drawImage(paper(), 0, 0, W, H);
  c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
  const v = opt.vignette ?? .45;
  const g = c.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .95);
  g.addColorStop(0, 'rgba(40,25,15,0)'); g.addColorStop(1, `rgba(40,25,15,${v})`);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.restore();
}

function cloudBlob(c, x, y, s, col) {
  c.fillStyle = col; c.beginPath();
  c.arc(x, y, 50 * s, 0, TAU); c.arc(x + 55 * s, y - 20 * s, 60 * s, 0, TAU); c.arc(x + 120 * s, y, 48 * s, 0, TAU);
  c.rect(x, y - 10 * s, 120 * s, 58 * s); c.fill();
}

function sky(c, top, bottom, horizonY = 700) {
  const g = c.createLinearGradient(0, 0, 0, horizonY); g.addColorStop(0, top); g.addColorStop(1, bottom);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}

function farTreeRow(c, y, col, colHi, list = FAR_TREES) {
  for (const t of list) {
    c.fillStyle = col; c.beginPath(); c.arc(t.x, y - t.h, t.r, 0, TAU); c.fill();
    c.fillStyle = colHi; c.beginPath(); c.arc(t.x - t.r * .25, y - t.h - t.r * .3, t.r * .55, 0, TAU); c.fill();
  }
  c.fillStyle = col; c.fillRect(-1000, y - 30, 5000, 200);
}

function tree(c, x, y, r, trunkH, colA, colB, light = 0) {
  c.fillStyle = '#6e4f36'; c.strokeStyle = OUT; c.lineWidth = 4;
  c.beginPath(); c.moveTo(x - 28, y); c.quadraticCurveTo(x - 16, y - trunkH * .5, x - 18, y - trunkH); c.lineTo(x + 18, y - trunkH);
  c.quadraticCurveTo(x + 16, y - trunkH * .5, x + 30, y); c.closePath(); c.fill(); c.stroke();
  const cy = y - trunkH - r * .6;
  const blobs = [[0, 0, 1], [-.6, .25, .7], [.62, .22, .72], [-.3, -.45, .7], [.35, -.42, .66]];
  for (const [bx, by, br] of blobs) { c.beginPath(); c.arc(x + bx * r, cy + by * r, br * r, 0, TAU); c.fillStyle = colA; c.fill(); c.lineWidth = 3.5; c.stroke(); }
  for (const [bx, by, br] of blobs) { c.beginPath(); c.arc(x + bx * r, cy + by * r, br * r - 2, 0, TAU); c.fillStyle = colA; c.fill(); }
  c.fillStyle = colB;
  for (const [bx, by, br] of blobs) { c.beginPath(); c.arc(x + bx * r - br * r * .2, cy + by * r - br * r * .25, br * r * .55, 0, TAU); c.fill(); }
  if (light) { c.fillStyle = `rgba(255,240,190,${.25 * light})`; c.beginPath(); c.arc(x - r * .3, cy - r * .4, r * .5, 0, TAU); c.fill(); }
}

function grassTufts(c, list, col, t, wind = 1) {
  c.strokeStyle = col; c.lineCap = 'round';
  for (const g of list) {
    const sw = Math.sin(t * 1.6 + g.x * .01) * 4 * wind;
    c.lineWidth = 2.6 * g.s;
    for (let k = -1; k <= 1; k++) {
      c.beginPath(); c.moveTo(g.x + k * 5 * g.s, g.y);
      c.quadraticCurveTo(g.x + k * 8 * g.s, g.y - 12 * g.s, g.x + k * 12 * g.s + sw, g.y - 22 * g.s * (1 + .3 * (k === 0))); c.stroke();
    }
  }
}
function flowers(c, list) {
  for (const f of list) {
    c.fillStyle = FLOWER_COLS[f.c];
    for (let k = 0; k < 5; k++) { c.beginPath(); c.arc(f.x + Math.cos(k * 1.256) * 5 * f.s, f.y + Math.sin(k * 1.256) * 5 * f.s, 4 * f.s, 0, TAU); c.fill(); }
    c.fillStyle = '#e8a53a'; c.beginPath(); c.arc(f.x, f.y, 3 * f.s, 0, TAU); c.fill();
  }
}

function blanket(c, x, y, w, h) {
  c.save();
  const sk = 60;
  const path = new Path2D(); path.moveTo(x - w / 2 + sk, y - h / 2); path.lineTo(x + w / 2 + sk * .4, y - h / 2); path.lineTo(x + w / 2 - sk * .2, y + h / 2); path.lineTo(x - w / 2 - sk * .4, y + h / 2); path.closePath();
  c.fillStyle = '#f2ead5'; c.fill(path); c.clip(path);
  c.fillStyle = 'rgba(90,130,170,.45)';
  for (let i = -10; i < 20; i++) c.fillRect(x - w / 2 - 100 + i * 50, y - h / 2, 25, h);
  for (let j = 0; j < 6; j++) c.fillRect(x - w / 2 - 200, y - h / 2 + j * 36, w + 400, 18);
  c.restore();
  c.lineWidth = 4; c.strokeStyle = OUT; c.stroke(path);
}

// --------------------------------------------------------------- the clearing
// o: {t, storm (0..1), golden (0..1), noBlanket}
function drawClearing(c, cam, o = {}) {
  const t = o.t || 0, storm = o.storm || 0, gold = o.golden || 0;
  sky(c, mixc('#a9d3e6', '#4d5a6e', storm, '#e9b48a', gold), mixc('#f3ead0', '#8a93a0', storm, '#f6d9a8', gold));
  layer(c, cam, .08, () => {
    const a = 1 - storm * .3;
    for (let i = 0; i < 5; i++) cloudBlob(c, ((i * 520 + t * 8) % 2800) - 400, 120 + (i % 3) * 70, .9 + (i % 2) * .4, `rgba(255,255,255,${.75 * a})`);
  });
  layer(c, cam, .25, () => {
    c.fillStyle = mixc('#a9c3a6', '#66746e', storm, '#c4b08a', gold);
    c.beginPath(); c.moveTo(-1200, 700); for (let x = -1200; x <= 3200; x += 100) c.lineTo(x, 560 + Math.sin(x * .004) * 50 + Math.sin(x * .011) * 20); c.lineTo(3200, 800); c.lineTo(-1200, 800); c.fill();
  });
  layer(c, cam, .45, () => farTreeRow(c, 650, mixc('#6f9a78', '#45594d', storm, '#7f8a5c', gold), mixc('#88b08c', '#506657', storm, '#a39a62', gold)));
  layer(c, cam, .7, () => {
    for (const m of MID_TREES) tree(c, m.x, 700, m.r * .8, 120 + m.h, mixc('#5f8f5c', '#3c5444', storm, '#788a4f', gold), mixc('#79a96f', '#4a6350', storm, '#a3a35d', gold));
  });
  layer(c, cam, 1, () => {
    const g = c.createLinearGradient(0, 660, 0, 1300);
    g.addColorStop(0, mixc('#a6c46f', '#5e7351', storm, '#b7b066', gold)); g.addColorStop(1, mixc('#79a14f', '#465d3c', storm, '#8e8c45', gold));
    c.fillStyle = g; c.fillRect(-2000, 680, 6000, 1400);
    c.fillStyle = 'rgba(255,255,255,.08)'; ell(c, 1000, 760, 900, 60); c.fill();
    grassTufts(c, TUFTS, mixc('#5d8a3e', '#3c5233', storm, '#76772f', gold), t);
    if (!storm) flowers(c, FLOWERS);
    // big oak on the left
    tree(c, 170, 940, 330, 380, mixc('#557f4e', '#34493a', storm, '#6c7c45', gold), mixc('#6f9b60', '#3f5645', storm, '#959553', gold), 1 - storm);
    if (!o.noBlanket) blanket(c, 960, 905, 760, 150);
    // thistles by Eeyore's spot
    for (const [x, y] of [[1680, 930], [1740, 960], [1630, 975]]) thistle(c, x, y);
  });
}

function thistle(c, x, y) {
  c.strokeStyle = '#4f6e3a'; c.lineWidth = 4; c.beginPath(); c.moveTo(x, y); c.lineTo(x, y - 60); c.stroke();
  c.fillStyle = '#6f8f4a'; c.beginPath(); c.ellipse(x, y - 64, 11, 13, 0, 0, TAU); c.fill(); c.stroke();
  c.fillStyle = '#a77bc4'; c.beginPath(); c.moveTo(x - 12, y - 72); c.lineTo(x - 6, y - 92); c.lineTo(x, y - 76); c.lineTo(x + 6, y - 92); c.lineTo(x + 12, y - 72); c.closePath(); c.fill();
}

// mix colour a toward b by k, then toward d by k2
function hex(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; }
function mixc(a, b, k, d, k2 = 0) {
  let A = hex(a), B = hex(b); let r = A.map((v, i) => lerp(v, B[i], k || 0));
  if (d && k2) { const D = hex(d); r = r.map((v, i) => lerp(v, D[i], k2)); }
  return `rgb(${r.map(Math.round).join(',')})`;
}

// --------------------------------------------------------------- forest edge + pasture
const EDGE_TREES = Array.from({ length: 26 }, (_, i) => ({ x: -900 + i * 85 + R() * 50, r: 120 + R() * 70, h: 240 + R() * 160, d: R() }));
const PASTURE_TUFTS = Array.from({ length: 640 }, () => ({ x: 1100 + R() * 9600, y: 700 + Math.pow(R(), 1.4) * 460, s: .8 + R() * 1.1, c: R() }));
const PASTURE_FLOWERS = Array.from({ length: 330 }, () => ({ x: 1200 + R() * 9600, y: 720 + R() * 420, c: Math.floor(R() * 4), s: .8 + R() * .8 }));
const FOREST_TUFTS = Array.from({ length: 80 }, () => ({ x: -900 + R() * 2100, y: 700 + Math.pow(R(), 1.4) * 460, s: .6 + R() * .8, c: R() }));

// o: {t, close (0..1 trees leaning in), dim (forest darkness), sun}
function drawEdge(c, cam, o = {}) {
  const t = o.t || 0, close = o.close || 0;
  sky(c, '#8fc7ec', '#fbf1cf', 760);
  layer(c, cam, .05, () => {
    const g = c.createRadialGradient(1500, 260, 10, 1500, 260, 300); g.addColorStop(0, 'rgba(255,248,210,1)'); g.addColorStop(.25, 'rgba(255,240,180,.8)'); g.addColorStop(1, 'rgba(255,240,180,0)');
    c.fillStyle = g; c.fillRect(1000, -200, 1100, 900);
    for (let i = 0; i < 4; i++) cloudBlob(c, ((i * 700 + t * 10) % 3200) - 300, 150 + (i % 2) * 90, 1 + (i % 2) * .3, 'rgba(255,255,255,.8)');
  });
  layer(c, cam, .3, () => {
    c.fillStyle = '#b5d39a';
    c.beginPath(); c.moveTo(0, 760); for (let x = 0; x <= 16000; x += 80) c.lineTo(x, 610 + Math.sin(x * .003) * 60 + Math.sin(x * .0071) * 30); c.lineTo(16000, 1400); c.lineTo(0, 1400); c.fill();
  });
  layer(c, cam, .6, () => {
    c.fillStyle = '#9cc77a';
    c.beginPath(); c.moveTo(600, 800); for (let x = 600; x <= 16000; x += 80) c.lineTo(x, 680 + Math.sin(x * .002 + 1) * 45); c.lineTo(16000, 1400); c.lineTo(600, 1400); c.fill();
  });
  layer(c, cam, 1, () => {
    const g = c.createLinearGradient(0, 700, 0, 1300); g.addColorStop(0, '#a9cf6f'); g.addColorStop(1, '#7fae4e');
    c.fillStyle = g; c.fillRect(-1200, 720, 20000, 1400);
    grassTufts(c, PASTURE_TUFTS, '#5f9a3c', t, 2.2);
    flowers(c, PASTURE_FLOWERS);
    // forest floor: darker, shadowed
    const fg = c.createLinearGradient(700, 0, 1350, 0); fg.addColorStop(0, 'rgba(36,52,34,.75)'); fg.addColorStop(1, 'rgba(36,52,34,0)');
    c.fillStyle = fg; c.fillRect(-1200, 0, 2550, 1500);
    grassTufts(c, FOREST_TUFTS, '#3f5d34', t, .5);
    // trees (lean toward Eeyore when "close")
    for (const tr of EDGE_TREES) {
      const lean = close * (tr.x < 900 ? .12 : 0) * (1 - Math.abs(tr.x - 500) / 1400);
      c.save(); c.translate(tr.x, 1000); c.rotate(lean); c.translate(-tr.x, -1000);
      tree(c, tr.x, 1000 - tr.d * 160, tr.r, tr.h, mixc('#3f6a45', '#2b4433', close * .6), mixc('#55835a', '#33503b', close * .6));
      c.restore();
    }
  });
}

// --------------------------------------------------------------- cycle diagram
function drawParchment(c, dark = 0) {
  const g = c.createRadialGradient(W / 2, H / 2, 100, W / 2, H / 2, 1100);
  g.addColorStop(0, mixc('#f6ecd4', '#c9c2b4', dark)); g.addColorStop(1, mixc('#e2cfa6', '#8f897c', dark));
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}

// --------------------------------------------------------------- weather
function rain(c, t, amt, wind = .25) {
  if (amt <= 0) return;
  c.save(); c.strokeStyle = `rgba(200,215,235,${.55 * amt})`; c.lineWidth = 2.2;
  const r = mulberry(5);
  for (let i = 0; i < 260 * amt; i++) {
    const x0 = r() * (W + 400), sp = 1300 + r() * 600, off = r() * H;
    const y = (off + t * sp) % (H + 100) - 50, x = (x0 + y * wind) % (W + 200) - 100;
    c.beginPath(); c.moveTo(x, y); c.lineTo(x + 30 * wind, y + 30); c.stroke();
  }
  c.restore();
}

function caption(c, text, a, thought, speaker) {
  if (!text || a <= 0) return;
  c.save(); c.globalAlpha = a;
  c.font = `${thought ? 'italic ' : ''}44px "Patrick Hand"`; c.textAlign = 'center'; c.textBaseline = 'middle';
  let lines = wrap(c, text, 1500);
  if (lines.length > 1) lines = wrap(c, text, c.measureText(text).width / lines.length + 90); // balanced lines
  const lh = 52, y0 = H - 70 - (lines.length - 1) * lh;
  const wmax = Math.max(...lines.map(l => c.measureText(l).width));
  c.fillStyle = 'rgba(25,18,12,.55)';
  roundRect(c, W / 2 - wmax / 2 - 28, y0 - 36, wmax + 56, lines.length * lh + 22, 20); c.fill();
  const col = { narr: '#fff8e8', eeyore: '#cfe0ff', pooh: '#ffe0a0', piglet: '#ffd0d6', rabbit: '#f3dcc0', owl: '#e8d2b0', bird: '#cbe8ff' }[speaker] || '#fff';
  c.fillStyle = col;
  lines.forEach((l, i) => c.fillText(l, W / 2, y0 + i * lh));
  c.restore();
}
function wrap(c, text, maxW) {
  const words = text.split(' '), lines = []; let cur = '';
  for (const w of words) { const test = cur ? cur + ' ' + w : w; if (c.measureText(test).width > maxW && cur) { lines.push(cur); cur = w; } else cur = test; }
  if (cur) lines.push(cur); return lines;
}
function roundRect(c, x, y, w, h, r) {
  c.beginPath(); c.moveTo(x + r, y); c.arcTo(x + w, y, x + w, y + h, r); c.arcTo(x + w, y + h, x, y + h, r); c.arcTo(x, y + h, x, y, r); c.arcTo(x, y, x + w, y, r); c.closePath();
}
function chapterCard(c, text, a) {
  if (!text || a <= 0) return;
  c.save(); c.globalAlpha = a;
  c.font = '600 34px Fredoka'; const w = c.measureText(text).width;
  c.translate(60 - (1 - a) * 40, 56);
  c.fillStyle = 'rgba(250,243,225,.92)'; roundRect(c, 0, 0, w + 56, 64, 14); c.fill();
  c.strokeStyle = OUT; c.lineWidth = 3; c.stroke();
  c.fillStyle = '#4a3424'; c.textBaseline = 'middle'; c.fillText(text, 28, 34);
  c.restore();
}
