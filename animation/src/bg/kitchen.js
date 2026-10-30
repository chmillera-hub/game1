'use strict';
// Maya's small apartment kitchen at dusk.  (background painter A)
//
// Options (o):
//   o.dusk  0..1, default 0.2  0 = golden-orange sunset glow, 1 = deep blue-violet twilight
//   o.lamp  0..1, default 1    pendant lamp + under-cabinet strip light intensity
//
// Static paint is cached once (two lamp states x two mip levels); per frame we only draw
// the sky, a few lit windows, curtains, the clock hands, glows and tints.
const { createCanvas } = require('@napi-rs/canvas');

// ---------------------------------------------------------------- helpers
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const lerpAng = (a, b, t) => { let d = ((b - a + Math.PI * 3) % (Math.PI * 2)) - Math.PI; return a + d * t; };
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function hex2rgb(h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
function rgb2hex(c) { return '#' + c.map((v) => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join(''); }
function mix(a, b, t) { const A = hex2rgb(a), B = hex2rgb(b); return rgb2hex([lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)]); }
function rgba(h, a) { const c = hex2rgb(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }
function shade(h, k) { return k >= 0 ? mix(h, '#ffffff', k) : mix(h, '#000000', -k); }
function rr(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
}
function lin(ctx, x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function rad(ctx, x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function softGlow(ctx, x, y, r, col, a, sy = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, sy);
  ctx.fillStyle = rad(ctx, 0, 0, 0, r, [[0, rgba(col, a)], [0.35, rgba(col, a * 0.45)], [0.7, rgba(col, a * 0.12)], [1, rgba(col, 0)]]);
  ctx.fillRect(-r, -r, 2 * r, 2 * r); ctx.restore();
}
// value noise
function makeNoise(seed) {
  const R = mulberry32(seed), N = 256, p = new Float32Array(N * N);
  for (let i = 0; i < p.length; i++) p[i] = R();
  return function (x, y) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const x0 = xi & 255, y0 = yi & 255, x1 = (x0 + 1) & 255, y1 = (y0 + 1) & 255;
    const a = p[y0 * N + x0], b = p[y0 * N + x1], c = p[y1 * N + x0], d = p[y1 * N + x1];
    return lerp(lerp(a, b, u), lerp(c, d, u), v);
  };
}
// subtle luminance grain over a world rect of a cache canvas (S = cache scale)
function grain(cv, S, X0, Y0, rect, amp, freq, seed, fine = 0.35) {
  const ctx = cv.getContext('2d');
  const px = Math.max(0, Math.floor((rect[0] - X0) * S)), py = Math.max(0, Math.floor((rect[1] - Y0) * S));
  const pw = Math.min(cv.width - px, Math.ceil(rect[2] * S)), ph = Math.min(cv.height - py, Math.ceil(rect[3] * S));
  if (pw <= 0 || ph <= 0) return;
  const img = ctx.getImageData(px, py, pw, ph), d = img.data;
  const n = makeNoise(seed), R = mulberry32(seed * 7 + 3);
  const f = freq / S;
  for (let j = 0; j < ph; j++) {
    for (let i = 0; i < pw; i++) {
      const k = (j * pw + i) * 4;
      if (d[k + 3] === 0) continue;
      const wx = (px + i) * f, wy = (py + j) * f;
      const v = (n(wx, wy) * 0.6 + n(wx * 2.7 + 17, wy * 2.7 + 5) * 0.4 - 0.5) * 2 * (1 - fine) + (R() - 0.5) * 2 * fine;
      const dv = v * amp;
      d[k] = clamp(d[k] + dv, 0, 255); d[k + 1] = clamp(d[k + 1] + dv * 0.97, 0, 255); d[k + 2] = clamp(d[k + 2] + dv * 0.92, 0, 255);
    }
  }
  ctx.putImageData(img, px, py);
}

// ---------------------------------------------------------------- environment
const EXT = { x0: -300, y0: -400, x1: 1900, y1: 2300 };
const ENV = {
  name: 'kitchen',
  extents: EXT,
  options: { dusk: 0.2, lamp: 1 },
  anchors: {
    mayaSeat: { x: 430, y: 1430 },
    eliLean: { x: 1250, y: 1560 },
    eliSeat: { x: 900, y: 1430 },
    mugSpot: { x: 430, y: 1360 },
    phoneSpot: { x: 700, y: 1372 },
    lamp: { x: 430, y: 780 },
    windowCenter: { x: 380, y: 690 },
    clock: { x: 700, y: 250 },
    kettle: { x: 1500, y: 1090 },
    fruitBowl: { x: 900, y: 1090 },
    counterTop: { x: 1250, y: 1085 },
  },
};

const S = 1.25; // cache scale (world -> cache px)
const WIN = { x0: 120, y0: 360, x1: 640, y1: 1020 };
const PANES = [[144, 384, 229, 288], [387, 384, 229, 288], [144, 694, 229, 302], [387, 694, 229, 302]];
const VP = { x: 700, y: 950 }; // floor/table vanishing point
const LAMP = { x: 430, y: 700, y1: 800 };

const WALL = '#cdb698', CREAM = '#e6dac3', SLATE = '#5e716c', WOOD = '#a9774b', FLOOR = '#7d563a';

let C = null; // caches

function newCache(x0, y0, w, h, s = S) {
  const cv = createCanvas(Math.ceil(w * s), Math.ceil(h * s));
  const ctx = cv.getContext('2d');
  ctx.setTransform(s, 0, 0, s, -x0 * s, -y0 * s);
  return { cv, ctx, x0, y0, w, h, s };
}
function half(c) {
  const s2 = c.s * 0.5, cv = createCanvas(Math.ceil(c.w * s2), Math.ceil(c.h * s2));
  const ctx = cv.getContext('2d'); ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(c.cv, 0, 0, cv.width, cv.height);
  return { cv, x0: c.x0, y0: c.y0, w: c.w, h: c.h, s: s2 };
}
function blit(ctx, c, alpha = 1) {
  if (alpha <= 0.001) return;
  const ga = ctx.globalAlpha; ctx.globalAlpha = ga * alpha;
  ctx.drawImage(c.cv, c.x0, c.y0, c.w, c.h);
  ctx.globalAlpha = ga;
}
function pick(ctx, pair) { // choose a mip from the current device scale
  const m = ctx.getTransform(); const sc = Math.hypot(m.a, m.b);
  return sc < 0.62 ? pair[1] : pair[0];
}

// ---------------------------------------------------------------- painting: room
function paintWall(ctx, R) {
  ctx.fillStyle = WALL; ctx.fillRect(EXT.x0, EXT.y0, EXT.x1 - EXT.x0, 1900);
  // soft plaster mottling
  for (let i = 0; i < 70; i++) {
    const x = lerp(EXT.x0, EXT.x1, R()), y = lerp(-400, 1500, R()), r = 120 + R() * 260;
    softGlow(ctx, x, y, r, R() < 0.5 ? '#d8c3a5' : '#bfa688', 0.18);
  }
  // light falloff: darker near ceiling & far right, warm where the lamp/window is
  ctx.fillStyle = lin(ctx, 0, -400, 0, 1500, [[0, 'rgba(70,45,30,0.38)'], [0.35, 'rgba(70,45,30,0.08)'], [0.8, 'rgba(70,45,30,0)'], [1, 'rgba(60,38,26,0.18)']]);
  ctx.fillRect(EXT.x0, -400, 2200, 1900);
  ctx.fillStyle = lin(ctx, -300, 0, 1900, 0, [[0, 'rgba(60,40,30,0.22)'], [0.15, 'rgba(60,40,30,0)'], [0.75, 'rgba(60,40,30,0)'], [1, 'rgba(60,40,30,0.2)']]);
  ctx.fillRect(EXT.x0, -400, 2200, 1900);
  // ceiling + crown moulding
  ctx.fillStyle = lin(ctx, 0, -400, 0, -335, [[0, '#7d6a58'], [1, '#9b8670']]);
  ctx.fillRect(EXT.x0, -400, 2200, 66);
  ctx.fillStyle = lin(ctx, 0, -336, 0, -300, [[0, '#d9cbb2'], [0.45, '#efe4cf'], [0.55, '#cdbd9f'], [1, '#e3d6bd']]);
  ctx.fillRect(EXT.x0, -336, 2200, 34);
  ctx.fillStyle = lin(ctx, 0, -302, 0, -270, [[0, 'rgba(60,40,25,0.25)'], [1, 'rgba(60,40,25,0)']]);
  ctx.fillRect(EXT.x0, -302, 2200, 32);
  // ceiling canopy for the pendant
  ctx.fillStyle = lin(ctx, 400, 0, 460, 0, [[0, '#8e7a50'], [0.5, '#c9ad72'], [1, '#7c6842']]);
  rr(ctx, 405, -400, 50, 22, 5); ctx.fill();
}

function paintWindowFrame(ctx, R) {
  const { x0, y0, x1, y1 } = WIN;
  // shadow cast on the wall by the casing (light mostly from the lamp, front)
  ctx.save(); ctx.filter = 'blur(10px)';
  ctx.fillStyle = 'rgba(55,35,22,0.28)'; ctx.fillRect(x0 - 16, y0 - 10, x1 - x0 + 36, y1 - y0 + 70);
  ctx.restore();
  // casing
  ctx.fillStyle = '#e9dfcc'; ctx.fillRect(x0 - 18, y0 - 18, x1 - x0 + 36, y1 - y0 + 18);
  ctx.fillStyle = lin(ctx, x0 - 18, 0, x1 + 18, 0, [[0, 'rgba(255,255,255,0.18)'], [0.5, 'rgba(0,0,0,0)'], [1, 'rgba(60,40,20,0.12)']]);
  ctx.fillRect(x0 - 18, y0 - 18, x1 - x0 + 36, y1 - y0 + 18);
  ctx.strokeStyle = 'rgba(120,100,80,0.35)'; ctx.lineWidth = 2;
  ctx.strokeRect(x0 - 1, y0 - 1, x1 - x0 + 2, y1 - y0 + 2);
  // frame / sashes
  ctx.fillStyle = '#efe7d6'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  // inner reveal shading (depth)
  ctx.fillStyle = lin(ctx, 0, y0, 0, y0 + 24, [[0, 'rgba(70,50,35,0.35)'], [1, 'rgba(70,50,35,0.05)']]);
  ctx.fillRect(x0, y0, x1 - x0, 24);
  ctx.fillStyle = lin(ctx, x0, 0, x0 + 24, 0, [[0, 'rgba(70,50,35,0.25)'], [1, 'rgba(70,50,35,0.03)']]);
  ctx.fillRect(x0, y0, 24, y1 - y0);
  // meeting rail highlight
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(x0 + 20, 680, x1 - x0 - 40, 3);
  ctx.fillStyle = 'rgba(80,60,40,0.25)'; ctx.fillRect(x0 + 20, 693, x1 - x0 - 40, 2);
  // sash lock
  ctx.fillStyle = '#b89a62'; rr(ctx, 368, 676, 24, 8, 3); ctx.fill();
  // pane edges (thin putty/shadow lines inside each pane)
  for (const [px, py, pw, ph] of PANES) {
    ctx.strokeStyle = 'rgba(90,70,50,0.45)'; ctx.lineWidth = 3; ctx.strokeRect(px - 1.5, py - 1.5, pw + 3, ph + 3);
  }
  // sill (top surface + front face) and apron
  ctx.fillStyle = lin(ctx, 0, 1018, 0, 1032, [[0, '#d6c9b1'], [1, '#f3ebdc']]);
  ctx.beginPath(); ctx.moveTo(x0 - 14, 1018); ctx.lineTo(x1 + 14, 1018); ctx.lineTo(x1 + 26, 1032); ctx.lineTo(x0 - 26, 1032); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 1032, 0, 1050, [[0, '#ece2cf'], [1, '#cdbfa6']]);
  rr(ctx, x0 - 26, 1031, x1 - x0 + 52, 19, 3); ctx.fill();
  ctx.fillStyle = 'rgba(60,40,25,0.3)'; ctx.fillRect(x0 - 24, 1049, x1 - x0 + 48, 2);
  ctx.fillStyle = lin(ctx, 0, 1050, 0, 1080, [[0, '#ddd2bd'], [1, '#e6dbc7']]);
  ctx.fillRect(x0 - 8, 1050, x1 - x0 + 16, 26);
  ctx.save(); ctx.filter = 'blur(6px)'; ctx.fillStyle = 'rgba(50,32,20,0.35)';
  ctx.fillRect(x0 - 6, 1076, x1 - x0 + 12, 12); ctx.restore();
  // curtain rod + brackets + finials
  ctx.fillStyle = 'rgba(50,35,25,0.25)'; ctx.fillRect(84, 336, 594, 6);
  ctx.fillStyle = lin(ctx, 0, 326, 0, 336, [[0, '#d2b77f'], [0.5, '#a8884f'], [1, '#6f5733']]);
  rr(ctx, 84, 326, 592, 10, 5); ctx.fill();
  for (const fx of [80, 680]) { ctx.fillStyle = rad(ctx, fx - 2, 328, 1, 11, [[0, '#e4cd96'], [1, '#7d6238']]); ctx.beginPath(); ctx.arc(fx, 331, 10, 0, 7); ctx.fill(); }
}

function paintClockFace(ctx) {
  const cx = 700, cy = 250, r = 64;
  ctx.save(); ctx.filter = 'blur(8px)'; ctx.fillStyle = 'rgba(50,30,18,0.35)'; ctx.beginPath(); ctx.arc(cx + 6, cy + 10, r + 4, 0, 7); ctx.fill(); ctx.restore();
  ctx.fillStyle = rad(ctx, cx - 20, cy - 24, 10, r + 6, [[0, '#a87a4c'], [1, '#5f3f25']]);
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, 7); ctx.fill();
  ctx.fillStyle = rad(ctx, cx - 14, cy - 18, 4, r, [[0, '#fbf5e8'], [1, '#e2d6bf']]);
  ctx.beginPath(); ctx.arc(cx, cy, r - 9, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(80,60,40,0.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(cx, cy, r - 9, 0, 7); ctx.stroke();
  for (let i = 0; i < 60; i++) {
    const a = (i / 60) * Math.PI * 2, big = i % 5 === 0;
    const r0 = big ? r - 21 : r - 16, r1 = r - 13;
    ctx.strokeStyle = big ? '#4a3a2c' : 'rgba(80,65,50,0.55)'; ctx.lineWidth = big ? 3 : 1;
    ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0); ctx.lineTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1); ctx.stroke();
  }
  // glass sheen
  ctx.fillStyle = lin(ctx, cx - r, cy - r, cx + r * 0.2, cy + r * 0.2, [[0, 'rgba(255,255,255,0.22)'], [1, 'rgba(255,255,255,0)']]);
  ctx.beginPath(); ctx.arc(cx, cy, r - 9, Math.PI * 0.9, Math.PI * 1.75); ctx.closePath(); ctx.fill();
}

function paintUpperCabinets(ctx, R) {
  const x0 = 760, x1 = 1900, y0 = 280, y1 = 700;
  // soft shadow on the wall around the boxes
  ctx.save(); ctx.filter = 'blur(14px)'; ctx.fillStyle = 'rgba(55,35,22,0.35)'; ctx.fillRect(x0 - 14, y0 - 4, x1 - x0 + 40, y1 - y0 + 26); ctx.restore();
  ctx.fillStyle = '#d7c8ad'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  // crown
  ctx.fillStyle = lin(ctx, 0, 258, 0, 282, [[0, '#efe5d1'], [0.5, '#ddcfb5'], [1, '#c4b497']]);
  ctx.fillRect(x0 - 10, 258, x1 - x0 + 20, 24);
  // things on top of the cabinets
  paintBasket(ctx, 960, 258);
  paintJar(ctx, 1235, 258, 46, 92, '#9fb0a2');
  paintJar(ctx, 1292, 258, 36, 66, '#c7a77b');
  paintTrailingPlant(ctx, 1640, 258, R);
  const n = 4, dw = (x1 - x0) / n;
  for (let i = 0; i < n; i++) {
    const dx = x0 + i * dw + 3, w = dw - 6, y = y0 + 6, h = y1 - y0 - 22;
    paintShakerDoor(ctx, dx, y, w, h, CREAM, 34);
    // knob near the bottom, on the meeting side
    const kx = i % 2 === 0 ? dx + w - 22 : dx + 22, ky = y + h - 36;
    paintKnob(ctx, kx, ky, 7);
  }
  // light rail
  ctx.fillStyle = lin(ctx, 0, y1 - 16, 0, y1, [[0, '#e8dcc5'], [1, '#bcae94']]);
  ctx.fillRect(x0 - 4, y1 - 16, x1 - x0 + 8, 16);
}
function paintShakerDoor(ctx, x, y, w, h, col, st) {
  ctx.fillStyle = col; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = lin(ctx, x, y, x + w, y + h, [[0, 'rgba(255,255,255,0.10)'], [1, 'rgba(40,25,15,0.10)']]); ctx.fillRect(x, y, w, h);
  // recessed panel
  const px = x + st, py = y + st, pw = w - 2 * st, ph = h - 2 * st;
  ctx.fillStyle = shade(col, -0.05); ctx.fillRect(px, py, pw, ph);
  // inner bevel: shadow on top & left (light comes from front/below), highlight bottom/right
  ctx.fillStyle = lin(ctx, 0, py, 0, py + 14, [[0, 'rgba(40,25,15,0.30)'], [1, 'rgba(40,25,15,0)']]); ctx.fillRect(px, py, pw, 14);
  ctx.fillStyle = lin(ctx, px, 0, px + 10, 0, [[0, 'rgba(40,25,15,0.18)'], [1, 'rgba(40,25,15,0)']]); ctx.fillRect(px, py, 10, ph);
  ctx.fillStyle = 'rgba(255,255,255,0.22)'; ctx.fillRect(px, py + ph - 2, pw, 2); ctx.fillRect(px + pw - 2, py, 2, ph);
  // door edge gap
  ctx.strokeStyle = 'rgba(40,28,18,0.45)'; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);
}
function paintKnob(ctx, x, y, r) {
  ctx.save(); ctx.filter = 'blur(2px)'; ctx.fillStyle = 'rgba(40,25,10,0.4)'; ctx.beginPath(); ctx.arc(x + 2, y + 3, r, 0, 7); ctx.fill(); ctx.restore();
  ctx.fillStyle = rad(ctx, x - r * 0.35, y - r * 0.4, 0.5, r * 1.1, [[0, '#f6e2a8'], [0.5, '#c39a52'], [1, '#6e5228']]);
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
}
function paintBarPull(ctx, x, y, w) {
  ctx.save(); ctx.filter = 'blur(2.5px)'; ctx.fillStyle = 'rgba(20,15,10,0.45)'; rr(ctx, x - w / 2 + 2, y + 3, w, 8, 4); ctx.fill(); ctx.restore();
  ctx.fillStyle = lin(ctx, 0, y - 4, 0, y + 5, [[0, '#f0d798'], [0.45, '#c29a55'], [1, '#6b5027']]);
  rr(ctx, x - w / 2, y - 4, w, 9, 4.5); ctx.fill();
}
function paintBasket(ctx, cx, by) {
  const w = 170, h = 74;
  ctx.fillStyle = lin(ctx, 0, by - h, 0, by, [[0, '#b58d5c'], [1, '#7f5f3b']]);
  ctx.beginPath(); ctx.moveTo(cx - w / 2, by - h); ctx.lineTo(cx + w / 2, by - h); ctx.lineTo(cx + w / 2 - 10, by); ctx.lineTo(cx - w / 2 + 10, by); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(70,48,25,0.45)'; ctx.lineWidth = 2;
  for (let y = by - h + 9; y < by; y += 10) { ctx.beginPath(); ctx.moveTo(cx - w / 2 + 4, y); ctx.lineTo(cx + w / 2 - 4, y); ctx.stroke(); }
  for (let x = cx - w / 2 + 12; x < cx + w / 2; x += 14) { ctx.strokeStyle = 'rgba(220,190,140,0.25)'; ctx.beginPath(); ctx.moveTo(x, by - h); ctx.lineTo(x - 2, by); ctx.stroke(); }
  ctx.fillStyle = '#c9a26c'; rr(ctx, cx - w / 2 - 3, by - h - 6, w + 6, 10, 5); ctx.fill();
}
function paintJar(ctx, cx, by, w, h, col) {
  ctx.fillStyle = lin(ctx, cx - w / 2, 0, cx + w / 2, 0, [[0, shade(col, -0.25)], [0.35, shade(col, 0.15)], [1, shade(col, -0.35)]]);
  rr(ctx, cx - w / 2, by - h, w, h, 10); ctx.fill();
  ctx.fillStyle = '#7b6044'; rr(ctx, cx - w / 2 + 4, by - h - 10, w - 8, 12, 3); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.25)'; rr(ctx, cx - w / 2 + 6, by - h + 10, 5, h - 22, 2.5); ctx.fill();
}
function paintTrailingPlant(ctx, cx, by, R) {
  // small pot with trailing pothos vines over the cabinet front
  ctx.fillStyle = lin(ctx, cx - 40, 0, cx + 40, 0, [[0, '#a6684a'], [0.4, '#c7835f'], [1, '#86523a']]);
  ctx.beginPath(); ctx.moveTo(cx - 40, by - 66); ctx.lineTo(cx + 40, by - 66); ctx.lineTo(cx + 32, by); ctx.lineTo(cx - 32, by); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#b87556'; ctx.fillRect(cx - 44, by - 74, 88, 12);
  const vines = [[-30, 230], [-8, 320], [18, 180], [36, 270]];
  for (const [ox, len] of vines) {
    const x = cx + ox, y = by - 60;
    ctx.strokeStyle = '#55703d'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, y);
    for (let s = 0; s <= len; s += 10) ctx.lineTo(x + Math.sin(s * 0.025 + ox) * 12 + (s < 40 ? ox * 0.4 * s / 40 : ox * 0.4), y + s);
    ctx.stroke();
    let side = 1;
    for (let s = 24; s < len; s += 20) {
      const lx = x + Math.sin(s * 0.025 + ox) * 12 + ox * 0.4, ly = y + s;
      side = -side;
      paintLeaf(ctx, lx, ly, 20 + R() * 7, (side > 0 ? 0.5 : Math.PI - 0.5) + (R() - 0.5) * 0.5, R() < 0.5 ? '#5d7a45' : '#6d8a50');
    }
  }
  for (let i = 0; i < 12; i++) paintLeaf(ctx, cx + (R() - 0.5) * 70, by - 66 - R() * 30, 22, -Math.PI / 2 + (R() - 0.5) * 2.6, R() < 0.5 ? '#5a7643' : '#6f8d52');
}
function paintLeaf(ctx, x, y, s, ang, col) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang);
  ctx.fillStyle = lin(ctx, 0, -s * 0.5, 0, s * 0.5, [[0, shade(col, 0.12)], [1, shade(col, -0.22)]]);
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.bezierCurveTo(s * 0.4, -s * 0.55, s * 1.1, -s * 0.35, s * 1.3, 0); ctx.bezierCurveTo(s * 1.1, s * 0.35, s * 0.4, s * 0.55, 0, 0); ctx.fill();
  ctx.strokeStyle = 'rgba(30,45,20,0.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(s * 1.15, 0); ctx.stroke();
  ctx.restore();
}

function paintBacksplash(ctx, R) {
  const x0 = 760, x1 = 1900, y0 = 700, y1 = 1080, tw = 76, th = 38;
  ctx.fillStyle = '#c4b49b'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  for (let row = 0, y = y0; y < y1; row++, y += th) {
    const off = row % 2 ? -tw / 2 : 0;
    for (let x = x0 + off; x < x1; x += tw) {
      const v = (R() - 0.5) * 0.06;
      const col = shade('#e8dcc6', v);
      const tx = Math.max(x, x0) + 2, tx1 = Math.min(x + tw, x1) - 2;
      if (tx1 <= tx) continue;
      ctx.fillStyle = lin(ctx, 0, y + 2, 0, y + th - 2, [[0, shade(col, 0.06)], [0.5, col], [1, shade(col, -0.06)]]);
      rr(ctx, tx, y + 2, tx1 - tx, Math.min(th - 4, y1 - y - 2), 4); ctx.fill();
      // glaze sheen
      ctx.fillStyle = 'rgba(255,255,255,0.18)'; rr(ctx, tx + 5, y + 5, (tx1 - tx) * 0.45, 4, 2); ctx.fill();
    }
  }
  // outlet
  ctx.fillStyle = '#efe7d8'; rr(ctx, 1712, 870, 44, 70, 5); ctx.fill();
  ctx.strokeStyle = 'rgba(90,75,55,0.4)'; ctx.lineWidth = 1.5; rr(ctx, 1712, 870, 44, 70, 5); ctx.stroke();
  ctx.fillStyle = '#8c8070'; for (const yy of [888, 918]) { rr(ctx, 1724, yy, 5, 11, 2); ctx.fill(); rr(ctx, 1739, yy, 5, 11, 2); ctx.fill(); }
  // shadow under the upper cabinets (soft)
  ctx.fillStyle = lin(ctx, 0, y0, 0, y0 + 90, [[0, 'rgba(50,32,20,0.45)'], [1, 'rgba(50,32,20,0)']]);
  ctx.fillRect(x0, y0, x1 - x0, 90);
  ctx.fillStyle = lin(ctx, 0, y1 - 30, 0, y1, [[0, 'rgba(50,32,20,0)'], [1, 'rgba(50,32,20,0.18)']]);
  ctx.fillRect(x0, y1 - 30, x1 - x0, 30);
  // strip light fixture
  ctx.fillStyle = '#bfb19a'; ctx.fillRect(x0 + 20, y0, x1 - x0 - 40, 6);
}

function paintCounter(ctx, R) {
  const x0 = 760, x1 = 1900;
  // base cabinets
  ctx.fillStyle = SLATE; ctx.fillRect(x0, 1110, x1 - x0, 390);
  const n = 4, dw = (x1 - x0) / n;
  for (let i = 0; i < n; i++) {
    const dx = x0 + i * dw + 3, w = dw - 6;
    paintShakerDoor(ctx, dx, 1124, w, 92, SLATE, 22);
    paintBarPull(ctx, dx + w / 2, 1170, 64);
    paintShakerDoor(ctx, dx, 1224, w, 236, SLATE, 30);
    paintBarPull(ctx, i % 2 === 0 ? dx + w - 34 : dx + 34, 1262, 9);
  }
  // re-draw the vertical pulls as vertical bars
  for (let i = 0; i < n; i++) {
    const dx = x0 + i * dw + 3, w = dw - 6, px = i % 2 === 0 ? dx + w - 30 : dx + 30;
    ctx.fillStyle = SLATE; ctx.fillRect(px - 10, 1252, 20, 22);
    ctx.save(); ctx.filter = 'blur(2.5px)'; ctx.fillStyle = 'rgba(20,15,10,0.45)'; rr(ctx, px - 2, 1252, 9, 70, 4); ctx.fill(); ctx.restore();
    ctx.fillStyle = lin(ctx, px - 4, 0, px + 5, 0, [[0, '#f0d798'], [0.45, '#c29a55'], [1, '#6b5027']]);
    rr(ctx, px - 4, 1248, 9, 66, 4.5); ctx.fill();
  }
  // toe kick + floor contact
  ctx.fillStyle = '#2f3533'; ctx.fillRect(x0, 1466, x1 - x0, 34);
  ctx.fillStyle = lin(ctx, 0, 1462, 0, 1472, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0.25)']]); ctx.fillRect(x0, 1462, x1 - x0, 10);
  // overhang shadow
  ctx.fillStyle = lin(ctx, 0, 1110, 0, 1150, [[0, 'rgba(20,15,10,0.5)'], [1, 'rgba(20,15,10,0)']]); ctx.fillRect(x0, 1110, x1 - x0, 40);
  // left end panel side (counter begins at 760 next to the dining area)
  ctx.fillStyle = lin(ctx, x0 - 16, 0, x0, 0, [[0, '#46554f'], [1, '#55665f']]); ctx.fillRect(x0 - 14, 1110, 16, 390);
  // countertop: top surface + front edge, butcher block
  ctx.fillStyle = lin(ctx, 0, 1078, 0, 1094, [[0, '#b98a5c'], [1, '#c99a69']]);
  ctx.beginPath(); ctx.moveTo(x0 - 6, 1078); ctx.lineTo(x1, 1078); ctx.lineTo(x1, 1094); ctx.lineTo(x0 - 18, 1094); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 1094, 0, 1112, [[0, '#a06f43'], [1, '#7c5332']]);
  ctx.fillRect(x0 - 18, 1094, x1 - x0 + 18, 18);
  // butcher block strips on the edge
  let x = x0 - 18;
  while (x < x1) {
    const w = 30 + R() * 50;
    ctx.fillStyle = rgba(R() < 0.5 ? '#5a3a20' : '#d0a070', 0.12 + R() * 0.1); ctx.fillRect(x, 1094, w, 18);
    ctx.fillStyle = 'rgba(60,35,18,0.4)'; ctx.fillRect(x + w - 1, 1094, 1.2, 18);
    x += w;
  }
  ctx.fillStyle = 'rgba(255,230,190,0.35)'; ctx.fillRect(x0 - 18, 1093, x1 - x0 + 18, 1.6);
  for (let i = 0; i < 40; i++) { ctx.strokeStyle = 'rgba(110,70,40,0.18)'; ctx.lineWidth = 1; const y = 1080 + R() * 13, xx = x0 + R() * 1100; ctx.beginPath(); ctx.moveTo(xx, y); ctx.lineTo(xx + 40 + R() * 120, y + (R() - 0.5) * 2); ctx.stroke(); }
}

function contactShadow(ctx, cx, cy, w, h, a) {
  ctx.save(); ctx.translate(cx, cy); ctx.scale(1, h / w);
  ctx.fillStyle = rad(ctx, 0, 0, 0, w, [[0, `rgba(40,22,10,${a})`], [0.6, `rgba(40,22,10,${a * 0.4})`], [1, 'rgba(40,22,10,0)']]);
  ctx.fillRect(-w, -w, 2 * w, 2 * w); ctx.restore();
}

function paintKettle(ctx) {
  const cx = 1500, by = 1088;
  contactShadow(ctx, cx + 6, by + 1, 110, 12, 0.55);
  // base ring
  ctx.fillStyle = '#3c3430'; rr(ctx, cx - 70, by - 10, 140, 11, 5); ctx.fill();
  // spout (behind the body): tapered, curving up, with a lip
  ctx.fillStyle = lin(ctx, cx - 136, by - 130, cx - 60, by - 40, [[0, '#d48b5c'], [0.5, '#a95f39'], [1, '#6f3a24']]);
  ctx.beginPath(); ctx.moveTo(cx - 66, by - 34); ctx.quadraticCurveTo(cx - 104, by - 48, cx - 124, by - 116);
  ctx.lineTo(cx - 138, by - 126); ctx.lineTo(cx - 128, by - 136); ctx.quadraticCurveTo(cx - 108, by - 106, cx - 62, by - 98); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,225,190,0.35)'; ctx.beginPath(); ctx.moveTo(cx - 74, by - 92); ctx.quadraticCurveTo(cx - 104, by - 96, cx - 122, by - 126); ctx.lineTo(cx - 118, by - 124); ctx.quadraticCurveTo(cx - 100, by - 90, cx - 74, by - 86); ctx.fill();
  // body (copper)
  const top = by - 138;
  ctx.fillStyle = rad(ctx, cx - 30, by - 85, 8, 120, [[0, '#f1b483'], [0.35, '#c6774a'], [0.75, '#8e4b2e'], [1, '#5d3020']]);
  ctx.beginPath(); ctx.moveTo(cx - 74, by - 10);
  ctx.bezierCurveTo(cx - 92, by - 70, cx - 62, top, cx, top); ctx.bezierCurveTo(cx + 62, top, cx + 92, by - 70, cx + 74, by - 10); ctx.closePath(); ctx.fill();
  // lid + knob
  ctx.fillStyle = lin(ctx, 0, top - 14, 0, top + 6, [[0, '#d98f5f'], [1, '#8a4a2c']]);
  ctx.beginPath(); ctx.ellipse(cx, top + 2, 40, 10, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#2f2724'; ctx.beginPath(); ctx.ellipse(cx, top - 6, 11, 8, 0, 0, 7); ctx.fill();
  // handle
  ctx.strokeStyle = '#2f2724'; ctx.lineWidth = 11; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(cx - 48, top + 14); ctx.bezierCurveTo(cx - 52, top - 70, cx + 52, top - 70, cx + 48, top + 14); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,0.18)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx - 38, top - 30); ctx.bezierCurveTo(cx - 20, top - 52, cx + 20, top - 52, cx + 38, top - 30); ctx.stroke();
  ctx.lineCap = 'butt';
  // highlights
  ctx.fillStyle = 'rgba(255,240,220,0.55)'; ctx.beginPath(); ctx.ellipse(cx - 38, by - 82, 8, 26, 0.35, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,220,180,0.2)'; ctx.beginPath(); ctx.ellipse(cx + 40, by - 60, 10, 30, -0.2, 0, 7); ctx.fill();
}
function paintFruitBowl(ctx, R) {
  const cx = 900, by = 1090;
  contactShadow(ctx, cx + 4, by, 100, 10, 0.5);
  // fruit (behind the rim)
  const fruit = [
    [-52, -62, 27, '#d98a3a'], [-12, -74, 28, '#e09443'], [30, -66, 27, '#b8432f'], [62, -54, 24, '#c9973f'],
    [-38, -46, 25, '#a83a2c'], [10, -50, 26, '#d48a3c'], [48, -40, 22, '#9a3a2c'],
  ];
  // pear
  ctx.fillStyle = rad(ctx, cx + 70, by - 98, 3, 40, [[0, '#d8cf7a'], [1, '#8f8a3c']]);
  ctx.beginPath(); ctx.ellipse(cx + 66, by - 72, 22, 28, 0.2, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(cx + 72, by - 102, 13, 17, 0.25, 0, 7); ctx.fill();
  ctx.strokeStyle = '#5a4128'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx + 76, by - 118); ctx.lineTo(cx + 82, by - 130); ctx.stroke();
  for (const [ox, oy, r, col] of fruit) {
    ctx.fillStyle = rad(ctx, cx + ox - r * 0.35, by + oy - r * 0.4, r * 0.1, r * 1.15, [[0, shade(col, 0.35)], [0.5, col], [1, shade(col, -0.45)]]);
    ctx.beginPath(); ctx.arc(cx + ox, by + oy, r, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.beginPath(); ctx.ellipse(cx + ox - r * 0.38, by + oy - r * 0.42, r * 0.18, r * 0.12, -0.6, 0, 7); ctx.fill();
  }
  // leaf on one orange
  paintLeaf(ctx, cx - 14, by - 100, 16, -0.5, '#5f7d44');
  // bowl
  ctx.fillStyle = lin(ctx, cx - 92, 0, cx + 92, 0, [[0, '#7c8a86'], [0.3, '#b9c4bd'], [0.7, '#93a29c'], [1, '#5f6b67']]);
  ctx.beginPath(); ctx.moveTo(cx - 95, by - 52); ctx.quadraticCurveTo(cx - 88, by - 4, cx - 34, by - 2); ctx.lineTo(cx + 34, by - 2); ctx.quadraticCurveTo(cx + 88, by - 4, cx + 95, by - 52); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#d6ddd5'; ctx.beginPath(); ctx.ellipse(cx, by - 52, 95, 7, 0, 0, Math.PI); ctx.fill();
  ctx.fillStyle = '#4c5652'; rr(ctx, cx - 38, by - 6, 76, 7, 3); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx - 78, by - 40); ctx.quadraticCurveTo(cx - 70, by - 16, cx - 40, by - 12); ctx.stroke();
}
function paintDishRack(ctx) {
  const x0 = 1680, x1 = 1880, by = 1088;
  contactShadow(ctx, (x0 + x1) / 2, by, 120, 9, 0.45);
  // plates (standing, seen edge-on as tall ellipses)
  const plates = [[1712, 92, '#e7e0d2'], [1734, 96, '#dfe3dd'], [1756, 92, '#e7e0d2'], [1778, 84, '#c9d3d0']];
  for (const [px, r, col] of plates) {
    ctx.fillStyle = lin(ctx, px - 14, 0, px + 14, 0, [[0, shade(col, -0.2)], [0.5, col], [1, shade(col, -0.3)]]);
    ctx.beginPath(); ctx.ellipse(px, by - 14 - r * 0.55, 13, r * 0.55, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(90,90,85,0.35)'; ctx.lineWidth = 1.5; ctx.stroke();
  }
  // cup upside-down + glass
  ctx.fillStyle = lin(ctx, 1810, 0, 1856, 0, [[0, '#7f9a94'], [0.4, '#a8bcb5'], [1, '#5f7671']]);
  rr(ctx, 1812, by - 64, 44, 50, 8); ctx.fill();
  ctx.fillStyle = 'rgba(210,225,225,0.35)'; rr(ctx, 1858, by - 86, 22, 72, 4); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.4)'; ctx.lineWidth = 2; ctx.strokeRect(1858, by - 86, 22, 72);
  // wire rack
  ctx.strokeStyle = '#9aa09c'; ctx.lineWidth = 3;
  ctx.strokeRect(x0, by - 48, x1 - x0, 36);
  for (let x = x0 + 12; x < x1; x += 14) { ctx.beginPath(); ctx.moveTo(x, by - 48); ctx.lineTo(x, by - 12); ctx.stroke(); }
  ctx.strokeStyle = '#7c827e'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x0 + 6, by - 12); ctx.lineTo(x0 + 6, by); ctx.moveTo(x1 - 6, by - 12); ctx.lineTo(x1 - 6, by); ctx.stroke();
  ctx.fillStyle = '#8b918d'; ctx.fillRect(x0, by - 14, x1 - x0, 4);
}

function paintLeftWall(ctx, R) {
  // framed photo (Nana & Maya, softly abstract)
  const fx = -205, fy = 470, fw = 170, fh = 210;
  ctx.save(); ctx.filter = 'blur(9px)'; ctx.fillStyle = 'rgba(50,30,18,0.35)'; ctx.fillRect(fx + 6, fy + 12, fw, fh); ctx.restore();
  ctx.fillStyle = lin(ctx, fx, fy, fx + fw, fy + fh, [[0, '#7a5434'], [1, '#4d3220']]); ctx.fillRect(fx, fy, fw, fh);
  ctx.fillStyle = '#efe6d4'; ctx.fillRect(fx + 14, fy + 14, fw - 28, fh - 28);
  const ix = fx + 30, iy = fy + 30, iw = fw - 60, ih = fh - 60;
  ctx.fillStyle = lin(ctx, 0, iy, 0, iy + ih, [[0, '#c9b28e'], [1, '#9c7e5c']]); ctx.fillRect(ix, iy, iw, ih);
  ctx.save(); ctx.beginPath(); ctx.rect(ix, iy, iw, ih); ctx.clip();
  // two figures: elder with silver hair (left), girl (right)
  ctx.fillStyle = '#7b3b55'; ctx.beginPath(); ctx.ellipse(ix + 34, iy + ih + 6, 30, 46, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#a8714f'; ctx.beginPath(); ctx.arc(ix + 34, iy + 58, 15, 0, 7); ctx.fill();
  ctx.fillStyle = '#d9d6d2'; ctx.beginPath(); ctx.arc(ix + 34, iy + 51, 15, Math.PI, 0); ctx.fill();
  ctx.fillStyle = '#b9a3d6'; ctx.beginPath(); ctx.ellipse(ix + 76, iy + ih + 14, 22, 40, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#a8714f'; ctx.beginPath(); ctx.arc(ix + 76, iy + 84, 12, 0, 7); ctx.fill();
  ctx.fillStyle = '#3a2618'; ctx.beginPath(); ctx.arc(ix + 76, iy + 79, 12.5, Math.PI, 0); ctx.fill();
  ctx.restore();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.beginPath(); ctx.moveTo(fx + 14, fy + 14); ctx.lineTo(fx + 90, fy + 14); ctx.lineTo(fx + 14, fy + 120); ctx.fill();
  // small wall shelf with cookbooks & a jar, on brackets
  const sy = 930;
  ctx.save(); ctx.filter = 'blur(8px)'; ctx.fillStyle = 'rgba(50,30,18,0.32)'; ctx.fillRect(-276, sy + 4, 270, 26); ctx.restore();
  const books = [[-262, 26, 150, '#6e7b5b'], [-235, 22, 138, '#9a5b45'], [-212, 30, 160, '#d1bf94'], [-181, 20, 128, '#56626a'], [-160, 24, 142, '#8a6a8f']];
  for (const [bx, bw, bh, col] of books) {
    ctx.fillStyle = lin(ctx, bx, 0, bx + bw, 0, [[0, shade(col, -0.15)], [0.4, shade(col, 0.08)], [1, shade(col, -0.25)]]);
    ctx.fillRect(bx, sy - bh, bw, bh);
    ctx.fillStyle = 'rgba(255,240,210,0.35)'; ctx.fillRect(bx + 3, sy - bh + 18, bw - 6, 3); ctx.fillRect(bx + 3, sy - 26, bw - 6, 3);
  }
  // leaning book
  ctx.save(); ctx.translate(-84, sy); ctx.rotate(-0.2); ctx.fillStyle = lin(ctx, -24, 0, 0, 0, [[0, '#a8834e'], [1, '#c49e68']]); ctx.fillRect(-24, -130, 24, 130); ctx.fillStyle = 'rgba(255,240,210,0.35)'; ctx.fillRect(-21, -112, 18, 3); ctx.restore();
  paintJar(ctx, -60, sy, 50, 74, '#b9c1b4');
  ctx.fillStyle = lin(ctx, 0, sy, 0, sy + 18, [[0, '#a87a50'], [1, '#704a2c']]); ctx.fillRect(-280, sy, 276, 18);
  ctx.fillStyle = 'rgba(255,230,190,0.35)'; ctx.fillRect(-280, sy, 276, 2);
  for (const bx of [-250, -40]) { ctx.fillStyle = '#5e432b'; ctx.beginPath(); ctx.moveTo(bx, sy + 18); ctx.lineTo(bx + 12, sy + 18); ctx.lineTo(bx + 12, sy + 60); ctx.closePath(); ctx.fill(); }
}

function paintBaseboardAndFloor(ctx, R) {
  // floor planks in perspective
  ctx.fillStyle = FLOOR; ctx.fillRect(EXT.x0, 1500, 2200, 800);
  const N = makeNoise(41);
  const pw = 92; let k = 0;
  for (let x = EXT.x0 - 2600; x < EXT.x1 + 2600; x += pw, k++) {
    // plank between wall points x and x+pw, projected toward the camera
    const f = (2300 - VP.y) / (1500 - VP.y);
    const xa = VP.x + (x - VP.x) * f, xb = VP.x + (x + pw - VP.x) * f;
    const v = (N(k * 0.7, 3) - 0.5) * 0.14;
    ctx.fillStyle = shade(FLOOR, v);
    ctx.beginPath(); ctx.moveTo(x, 1500); ctx.lineTo(x + pw, 1500); ctx.lineTo(xb, 2300); ctx.lineTo(xa, 2300); ctx.closePath(); ctx.fill();
    // staggered board ends (spacing grows toward camera)
    let d = 0.06 + ((k * 37) % 11) / 11 * 0.25;
    while (d < 1) {
      const y = 1500 + (2300 - 1500) * d, ff = (y - VP.y) / (1500 - VP.y);
      const ya = VP.x + (x - VP.x) * ff, yb = VP.x + (x + pw - VP.x) * ff;
      ctx.strokeStyle = 'rgba(45,25,12,0.4)'; ctx.lineWidth = 1.2 + d * 2;
      ctx.beginPath(); ctx.moveTo(ya, y); ctx.lineTo(yb, y); ctx.stroke();
      ctx.fillStyle = shade(FLOOR, (N(k * 1.3, d * 9) - 0.5) * 0.16);
      d += 0.33 + d * 0.5;
    }
    ctx.strokeStyle = 'rgba(45,25,12,0.45)'; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.moveTo(x, 1500); ctx.lineTo(xa, 2300); ctx.stroke();
  }
  // grain streaks
  for (let i = 0; i < 260; i++) {
    const x = lerp(-300, 1900, R()), d0 = R(), len = 0.05 + R() * 0.12;
    const y0 = 1500 + 800 * d0, y1 = Math.min(2300, y0 + 800 * len);
    const f0 = (y0 - VP.y) / (1500 - VP.y), f1 = (y1 - VP.y) / (1500 - VP.y);
    ctx.strokeStyle = rgba(R() < 0.6 ? '#5e3a20' : '#b98858', 0.12 + R() * 0.1); ctx.lineWidth = 1 + d0 * 2;
    ctx.beginPath(); ctx.moveTo(VP.x + (x - VP.x) * f0, y0); ctx.lineTo(VP.x + (x - VP.x) * f1, y1); ctx.stroke();
  }
  // soft sheen & depth: darker toward the camera, warm reflection under the lamp
  ctx.fillStyle = lin(ctx, 0, 1500, 0, 2300, [[0, 'rgba(255,220,170,0.10)'], [0.4, 'rgba(0,0,0,0)'], [1, 'rgba(30,15,8,0.40)']]);
  ctx.fillRect(EXT.x0, 1500, 2200, 800);
  // contact shadow along the wall
  ctx.fillStyle = lin(ctx, 0, 1500, 0, 1560, [[0, 'rgba(30,18,10,0.45)'], [1, 'rgba(30,18,10,0)']]);
  ctx.fillRect(EXT.x0, 1500, 2200, 60);
  // shadow cast under the dining table (soft, the table itself is drawn in front)
  ctx.save(); ctx.filter = 'blur(40px)'; ctx.fillStyle = 'rgba(28,15,8,0.5)';
  ctx.beginPath(); ctx.moveTo(-400, 1600); ctx.lineTo(1000, 1600); ctx.lineTo(1120, 2400); ctx.lineTo(-400, 2400); ctx.closePath(); ctx.fill(); ctx.restore();
  // baseboard (left of the counter)
  ctx.fillStyle = lin(ctx, 0, 1452, 0, 1500, [[0, '#efe5d2'], [0.15, '#e2d6bf'], [1, '#c7b89c']]);
  ctx.fillRect(EXT.x0, 1452, 760 - EXT.x0 - 14, 48);
  ctx.fillStyle = 'rgba(60,40,25,0.25)'; ctx.fillRect(EXT.x0, 1452, 760 - EXT.x0 - 14, 2);
}

// ---------------------------------------------------------------- light overlays baked into the "lamp on" room
function paintLampLightRoom(ctx) {
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  softGlow(ctx, 430, 820, 1250, '#ffbf78', 0.20, 0.9);
  softGlow(ctx, 430, 1150, 650, '#ffc98a', 0.18, 0.75);
  // under-cabinet strip: wash down the backsplash + pool on the counter
  ctx.fillStyle = lin(ctx, 0, 704, 0, 1080, [[0, 'rgba(255,214,150,0.75)'], [0.12, 'rgba(255,205,140,0.42)'], [0.6, 'rgba(255,200,130,0.16)'], [1, 'rgba(255,200,130,0.08)']]);
  ctx.save(); ctx.beginPath(); ctx.rect(760, 704, 1140, 376); ctx.clip();
  ctx.fillRect(760, 704, 1140, 376);
  for (let x = 860; x < 1900; x += 220) softGlow(ctx, x, 712, 170, '#ffe0b0', 0.35, 1.6);
  ctx.restore();
  ctx.fillStyle = lin(ctx, 0, 1078, 0, 1112, [[0, 'rgba(255,205,140,0.35)'], [1, 'rgba(255,205,140,0.06)']]);
  ctx.fillRect(742, 1078, 1158, 34);
  softGlow(ctx, 1500, 960, 140, '#ffd6a0', 0.25);
  ctx.restore();
  // bright strip itself
  ctx.fillStyle = '#fff1d2'; ctx.fillRect(780, 700, 1100, 5);
  ctx.fillStyle = 'rgba(255,238,200,0.6)'; ctx.fillRect(780, 705, 1100, 3);
}

// ---------------------------------------------------------------- sprites
function paintLamp(ctx, on) {
  const cx = LAMP.x;
  // cord
  ctx.strokeStyle = '#2a2420'; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(cx, -380); ctx.lineTo(cx, 690); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,240,220,0.15)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(cx - 1, -380); ctx.lineTo(cx - 1, 690); ctx.stroke();
  // brass cap
  ctx.fillStyle = lin(ctx, cx - 16, 0, cx + 16, 0, [[0, '#7a6036'], [0.4, '#e2c483'], [1, '#6a5130']]);
  rr(ctx, cx - 15, 680, 30, 28, 6); ctx.fill();
  // dome shade
  const y0 = 704, y1 = 800, r = 112;
  ctx.fillStyle = lin(ctx, cx - r, 0, cx + r, 0, [[0, '#1f322b'], [0.3, '#3d5a4f'], [0.55, '#2f4a40'], [1, '#18261f']]);
  ctx.beginPath(); ctx.moveTo(cx - 22, y0); ctx.bezierCurveTo(cx - 60, y0 + 6, cx - r, y1 - 50, cx - r, y1); ctx.lineTo(cx + r, y1);
  ctx.bezierCurveTo(cx + r, y1 - 50, cx + 60, y0 + 6, cx + 22, y0); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,230,190,0.22)'; ctx.beginPath(); ctx.ellipse(cx - 46, y0 + 40, 10, 34, 0.75, 0, 7); ctx.fill();
  // underside rim: lit interior seen from below
  ctx.fillStyle = on ? rad(ctx, cx, y1 + 2, 4, r, [[0, '#fffbea'], [0.35, '#ffe7b0'], [0.8, '#f7c47a'], [1, '#d9964e']]) : lin(ctx, 0, y1 - 8, 0, y1 + 12, [[0, '#cfc6b3'], [1, '#8f877a']]);
  ctx.beginPath(); ctx.ellipse(cx, y1, r, 13, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = on ? '#fffdf4' : '#ece7da';
  ctx.beginPath(); ctx.ellipse(cx, y1 + 7, 26, 9, 0, 0, Math.PI); ctx.fill();
  ctx.strokeStyle = '#1a2a23'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(cx, y1, r, 13, 0, Math.PI, Math.PI * 2); ctx.stroke();
}
function paintCurtain(ctx, x0, x1, side) {
  const y0 = 334, y1 = 1012, w = x1 - x0;
  // sheer: translucent, vertical folds, gathered at the rod
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1, y0);
  if (side < 0) { ctx.bezierCurveTo(x1 + 4, y0 + 300, x1 + 18, y1 - 200, x1 + 22, y1); ctx.lineTo(x0, y1); }
  else { ctx.lineTo(x1, y1); ctx.lineTo(x0 - 22, y1); ctx.bezierCurveTo(x0 - 18, y1 - 200, x0 - 4, y0 + 300, x0, y0); }
  ctx.closePath(); ctx.clip();
  ctx.fillStyle = 'rgba(244,236,222,0.42)'; ctx.fillRect(x0 - 30, y0, w + 60, y1 - y0);
  const folds = 7;
  for (let i = 0; i < folds; i++) {
    const fx = x0 - 20 + ((w + 40) * (i + 0.5)) / folds;
    const fw = (w + 40) / folds;
    ctx.fillStyle = lin(ctx, fx - fw / 2, 0, fx + fw / 2, 0, [[0, 'rgba(120,95,70,0.10)'], [0.35, 'rgba(255,250,240,0.30)'], [0.6, 'rgba(255,250,240,0.12)'], [1, 'rgba(120,95,70,0.12)']]);
    ctx.fillRect(fx - fw / 2, y0, fw, y1 - y0);
  }
  ctx.fillStyle = 'rgba(250,244,232,0.5)'; ctx.fillRect(x0 - 30, y1 - 14, w + 60, 14);
  ctx.fillStyle = 'rgba(250,244,232,0.35)'; ctx.fillRect(x0 - 30, y0, w + 60, 22);
  ctx.restore();
  // rings
  for (let x = x0 + 8; x < x1; x += 22) { ctx.strokeStyle = '#9a7d4a'; ctx.lineWidth = 2.2; ctx.beginPath(); ctx.ellipse(x, 331, 5, 8, 0, 0, 7); ctx.stroke(); }
}
function paintSillPlant(ctx, R) {
  const cx = 262, by = 1026;
  contactShadow(ctx, cx + 8, by, 52, 7, 0.55);
  // terracotta pot
  ctx.fillStyle = lin(ctx, cx - 34, 0, cx + 34, 0, [[0, '#8c4f35'], [0.35, '#c98260'], [1, '#7a4430']]);
  ctx.beginPath(); ctx.moveTo(cx - 32, by - 54); ctx.lineTo(cx + 32, by - 54); ctx.lineTo(cx + 25, by); ctx.lineTo(cx - 25, by); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, by - 66, 0, by - 52, [[0, '#d18d69'], [1, '#9c5c40']]); rr(ctx, cx - 37, by - 66, 74, 14, 3); ctx.fill();
  ctx.fillStyle = '#4a3324'; ctx.beginPath(); ctx.ellipse(cx, by - 66, 33, 5, 0, 0, 7); ctx.fill();
  // pilea: thin stems with round leaves
  const stems = [[-0.9, 120], [-0.5, 165], [-0.15, 190], [0.2, 175], [0.55, 150], [0.95, 115], [-1.25, 80], [1.3, 85], [0.0, 120]];
  for (const [a, len] of stems) {
    const ex = cx + Math.sin(a) * len * 0.7, ey = by - 66 - Math.cos(a) * len;
    ctx.strokeStyle = '#6b7f3f'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(cx + a * 8, by - 66); ctx.quadraticCurveTo(cx + Math.sin(a) * len * 0.2, ey + len * 0.4, ex, ey); ctx.stroke();
    const lr = 15 + R() * 8;
    ctx.fillStyle = rad(ctx, ex - lr * 0.3, ey - lr * 0.3, 1, lr * 1.2, [[0, '#8fae5c'], [0.6, '#5f8240'], [1, '#3f5c2c']]);
    ctx.beginPath(); ctx.ellipse(ex, ey, lr, lr * 0.82, a, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(200,220,160,0.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(ex, ey, lr * 0.25, 0, 7); ctx.stroke();
  }
}

// ---------------------------------------------------------------- front: dining table
function tableTop() {
  // returns the polygon of the top surface (x -400..1080 front, back corner slanted toward VP)
  const k = (1330 - VP.y) / (1420 - VP.y);
  const bx = VP.x + (1080 - VP.x) * k;
  return { bx, pts: [[-400, 1330], [bx, 1330], [1080, 1420], [-400, 1420]] };
}
function tablePath(ctx) {
  const { bx } = tableTop();
  ctx.beginPath(); ctx.moveTo(-400, 1330); ctx.lineTo(bx, 1330); ctx.lineTo(1080, 1420); ctx.lineTo(1080, 1446);
  ctx.lineTo(1060, 1446); ctx.lineTo(1060, 1472); ctx.lineTo(1062, 2400); ctx.lineTo(1006, 2400); ctx.lineTo(1008, 1472);
  ctx.lineTo(-400, 1472); ctx.closePath();
}
function paintTable(ctx, R, on) {
  const { bx } = tableTop();
  const TOP = '#8c5c3a';
  // shade under the table (space beneath, reads as deep shadow)
  ctx.fillStyle = lin(ctx, 0, 1470, 0, 2300, [[0, 'rgba(22,12,7,0.62)'], [0.35, 'rgba(22,12,7,0.42)'], [1, 'rgba(22,12,7,0.30)']]);
  ctx.save(); ctx.beginPath(); ctx.moveTo(-400, 1470); ctx.lineTo(1010, 1470); ctx.lineTo(1010, 2400); ctx.lineTo(-400, 2400); ctx.closePath(); ctx.clip();
  ctx.fillRect(-400, 1470, 1420, 930);
  ctx.restore();
  ctx.fillStyle = lin(ctx, 940, 0, 1012, 0, [[0, 'rgba(22,12,7,0)'], [1, 'rgba(22,12,7,0.25)']]);
  ctx.fillRect(940, 1470, 70, 930);
  // back-right leg (further away, slimmer, in shadow)
  ctx.fillStyle = lin(ctx, 960, 0, 1000, 0, [[0, '#3c2416'], [1, '#2a180e']]);
  ctx.beginPath(); ctx.moveTo(958, 1440); ctx.lineTo(998, 1440); ctx.lineTo(994, 1880); ctx.lineTo(962, 1880); ctx.closePath(); ctx.fill();
  contactShadow(ctx, 978, 1880, 46, 8, 0.5);
  // front-right leg descending off-frame
  ctx.fillStyle = lin(ctx, 1006, 0, 1062, 0, [[0, '#4a2c1a'], [0.35, '#7a4e30'], [0.7, '#5d3a24'], [1, '#3a2213']]);
  ctx.beginPath(); ctx.moveTo(1008, 1446); ctx.lineTo(1060, 1446); ctx.lineTo(1063, 2400); ctx.lineTo(1005, 2400); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 1470, 0, 1560, [[0, 'rgba(20,10,5,0.45)'], [1, 'rgba(20,10,5,0)']]); ctx.fillRect(1005, 1470, 60, 90);
  // apron (recessed under the top)
  ctx.fillStyle = lin(ctx, 0, 1440, 0, 1472, [[0, '#3e2516'], [1, '#5a3a24']]);
  ctx.fillRect(-400, 1440, 1460, 32);
  ctx.fillStyle = 'rgba(255,220,180,0.10)'; ctx.fillRect(-400, 1468, 1408, 2);
  // top slab front edge
  ctx.fillStyle = lin(ctx, 0, 1420, 0, 1446, [[0, '#a06c45'], [0.25, '#7e5133'], [1, '#5d3a24']]);
  ctx.fillRect(-400, 1420, 1480, 26);
  ctx.fillStyle = 'rgba(255,225,185,0.45)'; ctx.fillRect(-400, 1419.5, 1480, 1.8);
  // right end edge of the slab (slanted)
  ctx.fillStyle = '#6a4329';
  ctx.beginPath(); ctx.moveTo(bx, 1330); ctx.lineTo(1080, 1420); ctx.lineTo(1080, 1446); ctx.lineTo(bx - 1, 1352); ctx.closePath(); ctx.fill();
  // top surface
  ctx.fillStyle = lin(ctx, 0, 1330, 0, 1420, [[0, shade(TOP, -0.1)], [1, shade(TOP, 0.08)]]);
  ctx.beginPath(); ctx.moveTo(-400, 1330); ctx.lineTo(bx, 1330); ctx.lineTo(1080, 1420); ctx.lineTo(-400, 1420); ctx.closePath(); ctx.fill();
  // planks of the top (seams running across the depth, in perspective) + grain
  ctx.save(); ctx.beginPath(); ctx.moveTo(-400, 1330); ctx.lineTo(bx, 1330); ctx.lineTo(1080, 1420); ctx.lineTo(-400, 1420); ctx.closePath(); ctx.clip();
  for (let i = 0; i < 4; i++) {
    const y = 1330 + (90 * (i + 1)) / 5 + i * 2;
    ctx.strokeStyle = 'rgba(50,28,14,0.35)'; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(-400, y); ctx.lineTo(1100, y); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,220,180,0.12)'; ctx.beginPath(); ctx.moveTo(-400, y + 1.5); ctx.lineTo(1100, y + 1.5); ctx.stroke();
  }
  for (let i = 0; i < 160; i++) {
    const y = 1332 + R() * 86, x = -400 + R() * 1480, len = 60 + R() * 260;
    ctx.strokeStyle = rgba(R() < 0.6 ? '#4f2f1a' : '#c08a5c', 0.12 + R() * 0.12); ctx.lineWidth = 0.8 + R() * 1.2;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.bezierCurveTo(x + len * 0.3, y + (R() - 0.5) * 3, x + len * 0.6, y + (R() - 0.5) * 3, x + len, y + (R() - 0.5) * 2); ctx.stroke();
  }
  ctx.restore();
  // table runner (front-to-back, draped over the front edge)
  paintRunner(ctx);
  // little jar of dried flowers on the left
  paintDriedFlowers(ctx, -150, 1376, R);
  // lighting on top
  if (on) {
    ctx.save(); ctx.beginPath(); ctx.moveTo(-400, 1330); ctx.lineTo(bx, 1330); ctx.lineTo(1080, 1420); ctx.lineTo(1080, 1446); ctx.lineTo(-400, 1446); ctx.closePath(); ctx.clip();
    ctx.globalCompositeOperation = 'screen';
    softGlow(ctx, 430, 1372, 520, '#ffc27a', 0.42, 0.22);
    softGlow(ctx, 430, 1372, 260, '#ffe2b0', 0.30, 0.25);
    ctx.restore();
  }
  ctx.save(); ctx.globalCompositeOperation = 'source-atop';
  ctx.fillStyle = lin(ctx, -400, 0, 1080, 0, [[0, 'rgba(20,10,5,0.25)'], [0.25, 'rgba(20,10,5,0)'], [0.8, 'rgba(20,10,5,0)'], [1, 'rgba(20,10,5,0.15)']]);
  ctx.fillRect(-400, 1320, 1500, 160);
  ctx.restore();
}
function paintRunner(ctx) {
  // runner centred x~610 on the back edge, widening toward the front (perspective)
  const cxB = 612, cxF = 600, wB = 110, wF = 124;
  const L = (cx, w) => cx - w / 2, Rr = (cx, w) => cx + w / 2;
  const LIN = '#d9ccb1';
  // top part on the table
  ctx.fillStyle = lin(ctx, 0, 1330, 0, 1420, [[0, shade(LIN, -0.12)], [1, LIN]]);
  ctx.beginPath(); ctx.moveTo(L(cxB, wB), 1330); ctx.lineTo(Rr(cxB, wB), 1330); ctx.lineTo(Rr(cxF, wF), 1421); ctx.lineTo(L(cxF, wF), 1421); ctx.closePath(); ctx.fill();
  // drape over the edge and fold (hangs to ~1530)
  ctx.fillStyle = lin(ctx, 0, 1421, 0, 1530, [[0, shade(LIN, -0.02)], [0.2, shade(LIN, -0.14)], [1, shade(LIN, -0.22)]]);
  ctx.beginPath(); ctx.moveTo(L(cxF, wF), 1421); ctx.lineTo(Rr(cxF, wF), 1421); ctx.lineTo(Rr(cxF, wF) + 2, 1526); ctx.lineTo(L(cxF, wF) - 2, 1526); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,248,230,0.35)'; ctx.fillRect(L(cxF, wF), 1419, wF, 3);
  // fringe
  ctx.strokeStyle = '#c8b999'; ctx.lineWidth = 1.6;
  for (let x = L(cxF, wF) + 2; x < Rr(cxF, wF); x += 5) { ctx.beginPath(); ctx.moveTo(x, 1526); ctx.lineTo(x + 0.5, 1540); ctx.stroke(); }
  // stripes (muted terracotta)
  for (const f of [0.18, 0.82]) {
    const xb = L(cxB, wB) + wB * f, xf = L(cxF, wF) + wF * f;
    ctx.fillStyle = 'rgba(160,82,58,0.6)';
    ctx.beginPath(); ctx.moveTo(xb - 4, 1330); ctx.lineTo(xb + 4, 1330); ctx.lineTo(xf + 5, 1421); ctx.lineTo(xf + 5, 1526); ctx.lineTo(xf - 5, 1526); ctx.lineTo(xf - 5, 1421); ctx.closePath(); ctx.fill();
  }
  // fold crease shading near the hanging end
  ctx.fillStyle = lin(ctx, 0, 1480, 0, 1500, [[0, 'rgba(70,50,30,0)'], [0.5, 'rgba(70,50,30,0.18)'], [1, 'rgba(255,245,225,0.12)']]);
  ctx.fillRect(L(cxF, wF) - 2, 1480, wF + 4, 20);
  // shadow the runner casts on the apron
  ctx.save(); ctx.filter = 'blur(5px)'; ctx.fillStyle = 'rgba(15,8,4,0.35)'; ctx.fillRect(Rr(cxF, wF), 1446, 10, 70); ctx.restore();
}
function paintDriedFlowers(ctx, cx, by, R) {
  contactShadow(ctx, cx + 10, by, 46, 6, 0.5);
  for (let i = 0; i < 9; i++) {
    const a = -Math.PI / 2 + (i - 4) * 0.16 + (R() - 0.5) * 0.1, len = 120 + R() * 70;
    const ex = cx + Math.cos(a) * len, ey = by - 40 + Math.sin(a) * len;
    ctx.strokeStyle = '#8a7b4c'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(cx, by - 40); ctx.quadraticCurveTo(cx + Math.cos(a) * len * 0.5, by - 40 + Math.sin(a) * len * 0.6, ex, ey); ctx.stroke();
    ctx.fillStyle = ['#c9b07a', '#b98d7a', '#e0d3b0', '#a7896e'][i % 4];
    for (let j = 0; j < 4; j++) { ctx.beginPath(); ctx.arc(ex + (R() - 0.5) * 12, ey + (R() - 0.5) * 12, 4 + R() * 3, 0, 7); ctx.fill(); }
  }
  ctx.fillStyle = lin(ctx, cx - 26, 0, cx + 26, 0, [[0, '#8f9e98'], [0.35, '#d5dcd6'], [1, '#6f7c77']]);
  rr(ctx, cx - 24, by - 64, 48, 64, 12); ctx.fill();
  ctx.fillStyle = '#c4cdc7'; ctx.beginPath(); ctx.ellipse(cx, by - 62, 17, 5, 0, 0, 7); ctx.fill();
}

// ---------------------------------------------------------------- skyline
const SKY_BUILD = [];
const LIT = [];
function buildSkyline() {
  const R = mulberry32(777);
  // far layer
  let x = 100;
  while (x < 660) { const w = 50 + R() * 90, top = 780 + R() * 110; SKY_BUILD.push({ layer: 0, x, w, top }); x += w - 6; }
  x = 96;
  while (x < 660) {
    const w = 70 + R() * 110, top = 860 + R() * 90, roof = R();
    const b = { layer: 1, x, w, top, roof, chim: R() < 0.5 ? x + 12 + R() * (w - 30) : -1 };
    SKY_BUILD.push(b);
    // windows on the near layer
    for (let wy = top + 18; wy < 1010; wy += 26) for (let wx = x + 10; wx < x + w - 16; wx += 22) {
      if (R() < 0.42) LIT.push({ x: wx, y: wy, th: 0.1 + R() * 0.85, warm: R() });
    }
    x += w + 2 + R() * 10;
  }
}
function paintSkyline(ctx, dusk) {
  const far = mix('#a77f88', '#3b3762', dusk), near = mix('#5c4048', '#1f1e36', dusk);
  for (const b of SKY_BUILD) {
    ctx.fillStyle = b.layer === 0 ? far : near;
    if (b.layer === 0) { ctx.fillRect(b.x, b.top, b.w, 1100 - b.top); if (b.w > 100) ctx.fillRect(b.x + b.w * 0.4, b.top - 30, 6, 30); continue; }
    ctx.beginPath();
    if (b.roof < 0.4) { ctx.moveTo(b.x, b.top + 16); ctx.lineTo(b.x + b.w / 2, b.top - 18); ctx.lineTo(b.x + b.w, b.top + 16); }
    else { ctx.moveTo(b.x, b.top); ctx.lineTo(b.x + b.w, b.top); }
    ctx.lineTo(b.x + b.w, 1100); ctx.lineTo(b.x, 1100); ctx.closePath(); ctx.fill();
    ctx.fillRect(b.x - 3, b.top - 4 + (b.roof < 0.4 ? 16 : 0), b.w + 6, 5);
    if (b.chim > 0) ctx.fillRect(b.chim, b.top - 30, 14, 34);
  }
  // water tower on one roof
  ctx.fillStyle = near; const wt = SKY_BUILD.find((b) => b.layer === 1 && b.w > 110) || SKY_BUILD[SKY_BUILD.length - 1];
  const tx = wt.x + wt.w * 0.6;
  ctx.fillRect(tx - 18, wt.top - 64, 36, 40); ctx.beginPath(); ctx.moveTo(tx - 22, wt.top - 64); ctx.lineTo(tx, wt.top - 84); ctx.lineTo(tx + 22, wt.top - 64); ctx.fill();
  ctx.fillRect(tx - 16, wt.top - 26, 3, 26); ctx.fillRect(tx + 13, wt.top - 26, 3, 26);
}

// ---------------------------------------------------------------- init
// Static paint happens once.  Every (dusk level, lamp state) pair is then baked into a full
// composite (sky + room + tint + curtains + glows + lamp) on first use and kept in a small LRU,
// so a frame is one or two drawImage calls plus the clock hands.
const DUSK_STEP = 0.1;
function init() {
  if (C) return C;
  buildSkyline();
  const R = mulberry32(1234);
  const W = EXT.x1 - EXT.x0, H = EXT.y1 - EXT.y0;
  const base = newCache(EXT.x0, EXT.y0, W, H);
  const b = base.ctx;
  paintWall(b, R);
  paintWindowFrame(b, R);
  paintClockFace(b);
  paintLeftWall(b, R);
  paintUpperCabinets(b, R);
  paintBacksplash(b, R);
  paintCounter(b, R);
  paintFruitBowl(b, R);
  paintDishRack(b);
  paintKettle(b);
  paintBaseboardAndFloor(b, R);
  grain(base.cv, S, EXT.x0, EXT.y0, [EXT.x0, -400, W, 1900], 7, 0.03, 11);
  grain(base.cv, S, EXT.x0, EXT.y0, [EXT.x0, 1500, W, 800], 9, 0.05, 12, 0.5);
  // lamp-on variant
  const onC = newCache(EXT.x0, EXT.y0, W, H);
  onC.ctx.setTransform(1, 0, 0, 1, 0, 0); onC.ctx.drawImage(base.cv, 0, 0); onC.ctx.setTransform(S, 0, 0, S, -EXT.x0 * S, -EXT.y0 * S);
  paintLampLightRoom(onC.ctx);
  const offC = base; // lamp off: dimmer
  offC.ctx.save(); offC.ctx.globalCompositeOperation = 'multiply'; offC.ctx.fillStyle = '#a89c9a'; offC.ctx.fillRect(EXT.x0, EXT.y0, W, H); offC.ctx.restore();
  for (const c of [onC, offC]) for (const [px, py, pw, ph] of PANES) c.ctx.clearRect(px, py, pw, ph);
  // window sprites (curtains + sill plant)
  const win = newCache(60, 300, 640, 800);
  paintCurtain(win.ctx, 94, 206, -1); paintCurtain(win.ctx, 556, 668, 1);
  paintSillPlant(win.ctx, mulberry32(99));
  const lamp = [false, true].map((on) => { const c = newCache(300, -400, 260, 1230); paintLamp(c.ctx, on); return c; });
  const tables = [false, true].map((on) => { const c = newCache(-400, 1150, 1500, 1250); paintTable(c.ctx, mulberry32(555), on); if (!on) tintCache(c, '#a89c9a'); return c; });
  const grab = (c) => c.ctx.getImageData(0, 0, c.cv.width, c.cv.height).data;
  C = { room: [offC, onC], win, lamp, tables, winData: grab(win), tableData: tables.map(grab), levels: new Map(), tlevels: new Map(), pool: [], tpool: [] };
  return C;
}
function tintCache(c, col) {
  // per-pixel colour multiply (alpha untouched, correct for semi-transparent pixels)
  const [r, g, b] = hex2rgb(col).map((v) => v / 255);
  const x = c.ctx, img = x.getImageData(0, 0, c.cv.width, c.cv.height), d = img.data;
  for (let i = 0; i < d.length; i += 4) { d[i] *= r; d[i + 1] *= g; d[i + 2] *= b; }
  x.putImageData(img, 0, 0);
}
// LRU of baked composites; evicted canvases go to a pool and are re-used (avoids native-memory churn)
function lru(map, key, make, max, pool) {
  if (map.has(key)) { const v = map.get(key); map.delete(key); map.set(key, v); return v; }
  while (map.size >= max) { const k = map.keys().next().value; pool.push(map.get(k)); map.delete(k); }
  const v = make(pool.pop()); map.set(key, v);
  return v;
}
function freshPair(x0, y0, w, h, reuse) {
  if (!reuse) { const c = newCache(x0, y0, w, h); return [c, { cv: createCanvas(Math.ceil(w * S * 0.5), Math.ceil(h * S * 0.5)), x0, y0, w, h, s: S * 0.5 }]; }
  const c = reuse[0]; c.ctx.save(); c.ctx.setTransform(1, 0, 0, 1, 0, 0); c.ctx.clearRect(0, 0, c.cv.width, c.cv.height); c.ctx.restore();
  return reuse;
}
function finishPair(pair) {
  const h = pair[1], x = h.cv.getContext('2d');
  x.clearRect(0, 0, h.cv.width, h.cv.height); x.imageSmoothingQuality = 'high';
  x.drawImage(pair[0].cv, 0, 0, h.cv.width, h.cv.height);
  return pair;
}
let SCR = null; // scratch caches
function scratch() {
  if (!SCR) SCR = { wsp: newCache(60, 300, 640, 800), sky: newCache(WIN.x0, WIN.y0, WIN.x1 - WIN.x0, WIN.y1 - WIN.y0) };
  for (const c of Object.values(SCR)) { c.ctx.save(); c.ctx.setTransform(1, 0, 0, 1, 0, 0); c.ctx.clearRect(0, 0, c.cv.width, c.cv.height); c.ctx.restore(); }
  return SCR;
}
function bakeLevel(dusk, on, reuse) {
  const W = EXT.x1 - EXT.x0, H = EXT.y1 - EXT.y0;
  const pair = freshPair(EXT.x0, EXT.y0, W, H, reuse), c = pair[0], x = c.ctx;
  scratch();
  drawSky(x, dusk);
  blit(x, C.room[on ? 1 : 0]);
  // dusk tint + gentle vignette (room only, not the glass)
  x.save();
  x.beginPath(); x.rect(EXT.x0 - 10, EXT.y0 - 10, W + 20, H + 20);
  for (const [px, py, pw, ph] of PANES) { x.moveTo(px, py); x.lineTo(px, py + ph); x.lineTo(px + pw, py + ph); x.lineTo(px + pw, py); x.closePath(); }
  x.clip('evenodd');
  x.globalCompositeOperation = 'multiply';
  x.fillStyle = lightMap(x, dusk, on); x.fillRect(EXT.x0, EXT.y0, W, H);
  // the dome shade throws its light downward: upper wall and ceiling fall off into soft dusk
  x.fillStyle = lin(x, 0, LM.vy0, 0, LM.vy1, lightStops(dusk, on).vertical);
  x.fillRect(EXT.x0, EXT.y0, W, 1170);
  x.restore();
  // curtains + plant, tinted the same way
  const wsp = SCR.wsp; tintFromSrc(wsp, C.winData, dusk, on);
  blit(x, wsp);
  // window glow onto the room
  x.save(); x.globalCompositeOperation = 'screen';
  const wc = mix('#ffa660', '#7466b0', dusk);
  softGlow(x, 380, 700, 700, wc, 0.32 * (1 - 0.45 * dusk), 1.05);
  softGlow(x, 380, 700, 380, wc, 0.18 * (1 - 0.45 * dusk), 1.1);
  softGlow(x, 380, 1034, 320, wc, 0.22 * (1 - 0.45 * dusk), 0.25);
  x.restore();
  // pendant
  blit(x, C.lamp[on ? 1 : 0]);
  if (on) {
    x.save(); x.globalCompositeOperation = 'screen';
    softGlow(x, LAMP.x, 806, 340, '#ffcf8a', 0.6, 0.6);
    softGlow(x, LAMP.x, 806, 120, '#fff2d0', 0.6, 0.45);
    x.filter = 'blur(22px)';
    x.fillStyle = lin(x, 0, 800, 0, 1350, [[0, 'rgba(255,214,150,0.30)'], [0.55, 'rgba(255,200,140,0.12)'], [1, 'rgba(255,200,140,0.03)']]);
    x.beginPath(); x.moveTo(330, 802); x.lineTo(530, 802); x.lineTo(860, 1360); x.lineTo(0, 1360); x.closePath(); x.fill();
    x.filter = 'none';
    x.restore();
  }
  return finishPair(pair);
}
function bakeTable(dusk, on, reuse) {
  const pair = freshPair(-400, 1150, 1500, 1250, reuse), c = pair[0];
  tintFromSrc(c, C.tableData[on ? 1 : 0], dusk, on);
  return finishPair(pair);
}
// draw a quantized-level composite, cross-fading between neighbouring levels
function drawLevels(ctx, dusk, lamp, map, bake, max, pool) {
  const q = dusk / DUSK_STEP, i0 = Math.floor(q + 1e-6), f = q - i0;
  const parts = [];
  const lampStates = lamp >= 0.999 ? [[1, 1]] : lamp <= 0.001 ? [[0, 1]] : [[0, 1], [1, lamp]];
  for (const [on, la] of lampStates) {
    const get = (i) => lru(map, i + ':' + on, (reuse) => bake(Math.min(1, i * DUSK_STEP), on, reuse), max, pool);
    parts.push([get(i0), la]);
    if (f > 0.004) parts.push([get(i0 + 1), la * f]);
  }
  for (const [pair, a] of parts) blit(ctx, pick(ctx, pair), a);
}
// room light map: warm pool around the pendant, cooler/darker toward the edges as dusk deepens
const LM = { cx: 480, cy: 1080, r0: 200, r1: 1850, vy0: -400, vy1: 760 };
function lightStops(dusk, on) {
  const k = on ? 1 : 0.6;
  const edge = mix(mix('#a08a7c', '#6c6888', dusk), '#ffffff', 1 - k);
  const mid = mix(mix('#efe2d4', '#c4bad6', dusk), '#ffffff', 1 - k);
  const centre = on ? '#fff8ee' : mix('#e9e0da', '#c4bad6', dusk);
  return {
    radial: [[0, centre], [0.3, mid], [0.7, mix(mid, edge, 0.6)], [1, edge]],
    vertical: [[0, mix('#9a8a84', '#7a7696', dusk)], [0.55, mix('#d9cdc4', '#c2bcd2', dusk)], [1, '#ffffff']],
  };
}
function lightMap(x, dusk, on) {
  return rad(x, LM.cx, LM.cy, LM.r0, LM.r1, lightStops(dusk, on).radial);
}
function stopEval(stops, t) { // linear sRGB interpolation like canvas gradients, returns [r,g,b] 0..1
  t = clamp(t, 0, 1);
  for (let i = 1; i < stops.length; i++) {
    if (t <= stops[i][0]) {
      const [t0, c0] = stops[i - 1], [t1, c1] = stops[i], f = (t - t0) / (t1 - t0 || 1);
      const A = hex2rgb(c0), B = hex2rgb(c1);
      return [lerp(A[0], B[0], f) / 255, lerp(A[1], B[1], f) / 255, lerp(A[2], B[2], f) / 255];
    }
  }
  return hex2rgb(stops[stops.length - 1][1]).map((v) => v / 255);
}
// per-pixel multiply of a sprite by the room light map (radial pool + top falloff), alpha untouched.
// src = pixel data captured once at init (getImageData is only called at init: it leaks in this canvas build)
function tintFromSrc(c, src, dusk, on) {
  const st = lightStops(dusk, on), W = c.cv.width, H = c.cv.height;
  if (!c.img) { c.img = c.ctx.createImageData(W, H); }
  const d = c.img.data;
  const LUT = 256, rl = new Float32Array(LUT * 3);
  for (let i = 0; i < LUT; i++) { const v = stopEval(st.radial, i / (LUT - 1)); rl[i * 3] = v[0]; rl[i * 3 + 1] = v[1]; rl[i * 3 + 2] = v[2]; }
  for (let j = 0; j < H; j++) {
    const wy = c.y0 + (j + 0.5) / c.s;
    const vv = wy >= LM.vy1 ? [1, 1, 1] : stopEval(st.vertical, (wy - LM.vy0) / (LM.vy1 - LM.vy0));
    const dy2 = (wy - LM.cy) * (wy - LM.cy);
    for (let i = 0; i < W; i++) {
      const k = (j * W + i) * 4;
      const a = src[k + 3];
      if (a === 0) { d[k + 3] = 0; continue; }
      const wx = c.x0 + (i + 0.5) / c.s, dx = wx - LM.cx;
      let t = (Math.sqrt(dx * dx + dy2) - LM.r0) / (LM.r1 - LM.r0); t = t < 0 ? 0 : t > 1 ? 1 : t;
      const li = ((t * (LUT - 1)) | 0) * 3;
      d[k] = src[k] * rl[li] * vv[0]; d[k + 1] = src[k + 1] * rl[li + 1] * vv[1]; d[k + 2] = src[k + 2] * rl[li + 2] * vv[2]; d[k + 3] = a;
    }
  }
  c.ctx.putImageData(c.img, 0, 0);
}
function tintColor(dusk) {
  return mix('#fff4e6', '#cdc6e0', smooth(0, 1, dusk));
}
function skyStops(d) {
  return [
    [0, mix('#7f97bf', '#1c1f4a', d)],
    [0.45, mix('#d9a58e', '#433c78', d)],
    [0.75, mix('#f3b773', '#7a5c93', d)],
    [1, mix('#f8cf86', '#a07494', d)],
  ];
}
function drawSky(ctx, dusk) {
  const { x0, y0, x1, y1 } = WIN;
  ctx.save();
  ctx.beginPath(); for (const [px, py, pw, ph] of PANES) ctx.rect(px - 2, py - 2, pw + 4, ph + 4); ctx.clip();
  ctx.fillStyle = lin(ctx, 0, y0, 0, 960, skyStops(dusk)); ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  const sa = Math.pow(1 - dusk, 1.3);
  if (sa > 0.01) {
    const sy = 880 + dusk * 160;
    softGlow(ctx, 300, sy, 420, '#ffcf8a', 0.55 * sa, 0.7);
    ctx.fillStyle = rgba('#fff0c8', 0.9 * sa); ctx.beginPath(); ctx.arc(300, sy, 34, 0, 7); ctx.fill();
  }
  const st = smooth(0.55, 1, dusk);
  if (st > 0.01) {
    const R = mulberry32(31);
    for (let i = 0; i < 26; i++) {
      const sx = lerp(x0, x1, R()), sy = lerp(y0, 760, R()), r = 0.8 + R() * 1.4;
      ctx.fillStyle = `rgba(255,248,230,${(0.35 + R() * 0.5) * st})`; ctx.beginPath(); ctx.arc(sx, sy, r, 0, 7); ctx.fill();
    }
  }
  ctx.fillStyle = rgba(mix('#f6c9a0', '#6d5b8c', dusk), 0.35);
  for (const [cx, cy, w] of [[230, 560, 160], [480, 610, 200], [360, 470, 120]]) { ctx.beginPath(); ctx.ellipse(cx, cy, w, 12, 0, 0, 7); ctx.fill(); }
  const sk = SCR.sky; paintSkyline(sk.ctx, dusk); blit(ctx, sk);
  for (const w of LIT) {
    const a = smooth(w.th, w.th + 0.1, dusk);
    if (a < 0.01) continue;
    ctx.fillStyle = rgba(w.warm < 0.75 ? '#ffc97a' : '#fff0c0', 0.85 * a); ctx.fillRect(w.x, w.y, 8, 11);
  }
  ctx.fillStyle = lin(ctx, 0, 900, 0, 1020, [[0, rgba(mix('#f6c890', '#7c5c8e', dusk), 0)], [1, rgba(mix('#f6c890', '#7c5c8e', dusk), 0.35)]]);
  ctx.fillRect(x0, 900, x1 - x0, 120);
  ctx.fillStyle = lin(ctx, x0, y0, x1, y1, [[0, 'rgba(255,255,255,0.07)'], [0.4, 'rgba(255,255,255,0)'], [0.55, 'rgba(255,255,255,0.05)'], [0.6, 'rgba(255,255,255,0)']]);
  ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.restore();
}

function drawBack(ctx, t, o = {}) {
  init();
  const dusk = clamp(o.dusk ?? 0.2, 0, 1), lamp = clamp(o.lamp ?? 1, 0, 1);
  drawLevels(ctx, dusk, lamp, C.levels, bakeLevel, 4, C.pool);
  drawClockHands(ctx, t);
}

function drawClockHands(ctx, t) {
  const cx = 700, cy = 250;
  const sec = Math.floor(t), fr = t - sec;
  // smooth tick: quick ease into each new second with a tiny overshoot
  const e = fr < 0.14 ? (() => { const u = fr / 0.14; return 1 + 0.12 * Math.sin(u * Math.PI) - Math.pow(1 - u, 3); })() : 1;
  const s = (sec - 1 + clamp(e, 0, 1.12)) % 60;
  const base = 18 * 3600 + 41 * 60 + 12; // 6:41 pm
  const total = base + t;
  const m = (total / 60) % 60, h = (total / 3600) % 12;
  const A = (v, n) => (v / n) * Math.PI * 2 - Math.PI / 2;
  ctx.save(); ctx.lineCap = 'round';
  const hand = (ang, len, w, col, tail = 8) => {
    ctx.strokeStyle = 'rgba(40,25,15,0.18)'; ctx.lineWidth = w; ctx.beginPath();
    ctx.moveTo(cx + 2 - Math.cos(ang) * tail, cy + 3 - Math.sin(ang) * tail); ctx.lineTo(cx + 2 + Math.cos(ang) * len, cy + 3 + Math.sin(ang) * len); ctx.stroke();
    ctx.strokeStyle = col; ctx.beginPath();
    ctx.moveTo(cx - Math.cos(ang) * tail, cy - Math.sin(ang) * tail); ctx.lineTo(cx + Math.cos(ang) * len, cy + Math.sin(ang) * len); ctx.stroke();
  };
  hand(A(h, 12), 28, 5, '#2f2620');
  hand(A(m, 60), 42, 3.5, '#2f2620');
  hand(A(s + 1, 60), 46, 1.4, '#a8432f', 12);
  ctx.fillStyle = '#a8432f'; ctx.beginPath(); ctx.arc(cx, cy, 3.5, 0, 7); ctx.fill();
  ctx.restore();
}

function drawFront(ctx, t, o = {}) {
  init();
  const dusk = clamp(o.dusk ?? 0.2, 0, 1), lamp = clamp(o.lamp ?? 1, 0, 1);
  drawLevels(ctx, dusk, lamp, C.tlevels, bakeTable, 4, C.tpool);
}

// ---------------------------------------------------------------- lighting for characters
function dirTo(fx, fy, tx, ty) { return Math.atan2(ty - fy, tx - fx); }
function lightAt(x, y, t, o = {}) {
  const dusk = clamp(o.dusk ?? 0.2, 0, 1), lamp = clamp(o.lamp ?? 1, 0, 1);
  // representative chest point: standing (feet on floor) vs seated (hip point)
  const seated = y < 1490;
  const px = x, py = seated ? y - 330 : y - 600;
  const lampP = { x: LAMP.x, y: 800 }, winP = { x: 380, y: 700 };
  const dl = Math.hypot(px - lampP.x, py - lampP.y), dw = Math.hypot(px - winP.x, py - winP.y);
  const wl = lamp * 1.0 / (1 + Math.pow(dl / 650, 2));
  const winCol = mix('#ffb070', '#9d8fd6', dusk);
  const wwin = (0.55 - 0.25 * dusk) / (1 + Math.pow(dw / 900, 2));
  const lampCol = '#ffd29a';
  // key: weighted direction toward lamp and window
  const vl = [lampP.x - px, lampP.y - py], vw = [winP.x - px, winP.y - py];
  const nl = Math.hypot(...vl) || 1, nw = Math.hypot(...vw) || 1;
  const kx = (vl[0] / nl) * wl + (vw[0] / nw) * wwin, ky = (vl[1] / nl) * wl + (vw[1] / nw) * wwin;
  const keyDir = Math.atan2(ky, kx);
  const keyColor = mix(lampCol, winCol, clamp(wwin / (wl + wwin + 1e-6), 0, 1));
  const keyAmt = clamp(0.35 + 0.45 * (wl + wwin), 0.35, 0.85);
  // rim: window behind/left; near the counter the under-cabinet strip gives a warm top rim
  let rimDir = dirTo(px, py, winP.x, winP.y), rimColor = winCol, rimAmt = clamp(0.25 + 0.35 * wwin * 2, 0.25, 0.6);
  const nearCounter = x > 780 && !seated;
  if (nearCounter && lamp > 0.2) {
    const uc = lamp * smooth(780, 1000, x);
    rimDir = lerpAng(rimDir, -Math.PI * 0.62, uc * 0.6);
    rimColor = mix(winCol, '#ffd9a0', uc * 0.7);
    rimAmt = Math.max(rimAmt, 0.3 + 0.25 * uc);
  }
  const shadowColor = mix('#5a4048', '#3d3a62', dusk);
  const shadowAmt = clamp(0.28 + 0.12 * dusk - 0.08 * lamp, 0.15, 0.45);
  const ambient = mix('#ffe2c4', '#b9b2dc', dusk);
  const ambientAmt = clamp(0.1 + 0.12 * dusk + 0.08 * (1 - lamp), 0, 0.32);
  return { keyDir, keyColor, keyAmt, rimDir, rimColor, rimAmt, shadowColor, shadowAmt, ambient, ambientAmt };
}

module.exports = { ENV, drawBack, drawFront, lightAt };
