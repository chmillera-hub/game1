'use strict';
// Nana's house (background painter C): three environments in one module.
//
//   kitchen  — Nana's kitchen, Saturday morning, half packed up after her death.
//   memory   — the same kitchen ~25 years earlier: golden late-afternoon light, baking bread.
//   hospital — memory, night: the hospital room, lamp + moonlight through blinds.
//
// Options (o):
//   kitchen.o.tinOpen    0..1, default 0      recipe tin lid: 0 closed, 0..0.45 lifts, 0.45..1 sets it down beside the tin
//   memory  (no options)                      clock ticks, dust motes drift
//   hospital.o.chairEmpty  bool, default true  (the visitor chair is always painted empty; option kept for the API)
//   hospital.o.candle      bool|0..1, default false  lights the candle on the bedside table (gentle flame + warm glow)
//
// Static paint is cached once per environment into offscreen canvases (1.25x world scale + a half mip).
// Per frame only small things are drawn: the tin + lid, dust motes, clock hands (memory), the
// monitor trace and the candle flame (hospital).
const { createCanvas, GlobalFonts } = require('@napi-rs/canvas');

try { GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-SemiBold.otf', 'NanaBgSemi'); } catch (e) { /* optional */ }
try { GlobalFonts.registerFromPath('/usr/share/fonts/opentype/inter/Inter-Bold.otf', 'NanaBgBold'); } catch (e) { /* optional */ }

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
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const ease = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
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
function poly(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }
function lin(ctx, x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function rad(ctx, x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); for (const [o, c] of stops) g.addColorStop(o, c); return g; }
function softGlow(ctx, x, y, r, col, a, sy = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, sy);
  ctx.fillStyle = rad(ctx, 0, 0, 0, r, [[0, rgba(col, a)], [0.35, rgba(col, a * 0.45)], [0.7, rgba(col, a * 0.12)], [1, rgba(col, 0)]]);
  ctx.fillRect(-r, -r, 2 * r, 2 * r); ctx.restore();
}
function blurred(ctx, px, fn) { ctx.save(); ctx.filter = `blur(${px}px)`; fn(); ctx.restore(); }
function contact(ctx, cx, cy, w, h, a) { // soft elliptical contact shadow
  ctx.save(); ctx.translate(cx, cy); ctx.scale(1, h / w);
  ctx.fillStyle = rad(ctx, 0, 0, 0, w, [[0, `rgba(30,22,18,${a})`], [0.55, `rgba(30,22,18,${a * 0.45})`], [1, 'rgba(30,22,18,0)']]);
  ctx.fillRect(-w, -w, 2 * w, 2 * w); ctx.restore();
}
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
// subtle luminance grain over a world rect of a cache
function grain(c, rect, amp, freq, seed, fine = 0.35) {
  const ctx = c.cv.getContext('2d'), S = c.s;
  const px = Math.max(0, Math.floor((rect[0] - c.x0) * S)), py = Math.max(0, Math.floor((rect[1] - c.y0) * S));
  const pw = Math.min(c.cv.width - px, Math.ceil(rect[2] * S)), ph = Math.min(c.cv.height - py, Math.ceil(rect[3] * S));
  if (pw <= 0 || ph <= 0) return;
  const m = ctx.getTransform(); ctx.setTransform(1, 0, 0, 1, 0, 0);
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
      d[k] = clamp(d[k] + dv, 0, 255); d[k + 1] = clamp(d[k + 1] + dv * 0.97, 0, 255); d[k + 2] = clamp(d[k + 2] + dv * 0.93, 0, 255);
    }
  }
  ctx.putImageData(img, px, py);
  ctx.setTransform(m);
}

// ---------------------------------------------------------------- caches
const S = 1.25;
function newCache(x0, y0, x1, y1, s = S) {
  const w = x1 - x0, h = y1 - y0;
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
function pair(c) { return [c, half(c)]; }
function blit(ctx, p, alpha = 1) {
  const m = ctx.getTransform(); const sc = Math.hypot(m.a, m.b);
  const c = sc < 0.6 ? p[1] : p[0];
  const ga = ctx.globalAlpha; ctx.globalAlpha = ga * alpha;
  ctx.drawImage(c.cv, c.x0, c.y0, c.w, c.h);
  ctx.globalAlpha = ga;
}
// apply a full-cache overlay (fn draws in world coords) with a composite op
function overlay(c, op, fn) { const x = c.ctx; x.save(); x.globalCompositeOperation = op; fn(x); x.restore(); }

// ================================================================ NANA'S KITCHEN (shared by kitchen + memory)
const KEXT = { x0: -400, y0: -400, x1: 1600, y1: 2400 };
const KM = 260; // cache margin beyond the extents
const KC = { x0: KEXT.x0 - KM, y0: KEXT.y0 - KM, x1: KEXT.x1 + KM, y1: KEXT.y1 + KM };
const VP = { x: 880, y: 760 };      // eye level / vanishing point
const FLOOR_Y = 1500;               // wall / floor junction
const WIN = { x0: 80, y0: 420, x1: 480, y1: 980, rail: 700, mull: 280 };
const COUNTER = { x0: 600, x1: 1600, back: 1080, front: 1128, edge: 1146 };
const STOVE = { x0: 1282, x1: 1540 };
const UPPER = { x0: 720, x1: 1600, y0: 300, y1: 700 };
const CLOCK = { x: 612, y: 330, r: 54 };
const TIN = { x: 1000, y: 1120, rx: 66, h: 96, ry: 14 };

const persp = (x, y, k) => [VP.x + (x - VP.x) * k, VP.y + (y - VP.y) * k];

function kPal(M) {
  return M ? {
    wall: '#cfe1cf', wallDk: '#a9c2ad', cream: '#f4e8cc', creamDk: '#d9c7a3', lam: '#9fc7b6', enamel: '#f7f0df',
    tileA: '#f4ead6', tileB: '#e9dcc2', floorA: '#efe4cc', floorB: '#cfae9f', ging: '#c4776f', tinBody: '#5f9f96',
  } : {
    wall: '#c8dacb', wallDk: '#a3bba9', cream: '#ece2c9', creamDk: '#cdbf9f', lam: '#a3c2b6', enamel: '#f1ece0',
    tileA: '#efe7d6', tileB: '#e2d8c4', floorA: '#e8dfcb', floorB: '#cfaea3', ging: '#c58a84', tinBody: '#7fa59e',
  };
}

// ---------------------------------------------------------------- room shell
function kWall(ctx, R, P, M) {
  ctx.fillStyle = P.wall; ctx.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, FLOOR_Y - KC.y0);
  for (let i = 0; i < 80; i++) {
    const x = lerp(KC.x0, KC.x1, R()), y = lerp(-300, 1500, R()), r = 120 + R() * 260;
    softGlow(ctx, x, y, r, R() < 0.5 ? shade(P.wall, 0.12) : shade(P.wall, -0.08), 0.22);
  }
  // falloff toward ceiling + right side, light near window
  ctx.fillStyle = lin(ctx, 0, -400, 0, 1500, [[0, 'rgba(40,60,50,0.30)'], [0.3, 'rgba(40,60,50,0.06)'], [0.75, 'rgba(40,60,50,0)'], [1, 'rgba(40,50,40,0.14)']]);
  ctx.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, FLOOR_Y - KC.y0);
  ctx.fillStyle = lin(ctx, -600, 0, 1900, 0, [[0, 'rgba(40,55,50,0.25)'], [0.18, 'rgba(40,55,50,0)'], [0.7, 'rgba(40,55,50,0)'], [1, 'rgba(40,55,50,0.25)']]);
  ctx.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, FLOOR_Y - KC.y0);
  // ceiling + crown moulding
  ctx.fillStyle = lin(ctx, 0, KC.y0, 0, -300, [[0, M ? '#b49a78' : '#9fae9f'], [1, M ? '#d2bc96' : '#c2cfc0']]);
  ctx.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, -300 - KC.y0);
  ctx.fillStyle = lin(ctx, 0, -302, 0, -268, [[0, '#dcd2bd'], [0.45, '#f3ecdc'], [0.55, '#d1c6ae'], [1, '#e9e0cc']]);
  ctx.fillRect(KC.x0, -302, KC.x1 - KC.x0, 34);
  ctx.fillStyle = lin(ctx, 0, -268, 0, -236, [[0, 'rgba(40,50,40,0.22)'], [1, 'rgba(40,50,40,0)']]);
  ctx.fillRect(KC.x0, -268, KC.x1 - KC.x0, 32);
}

function kOutside(ctx, R, M) {
  const { x0, y0, x1, y1 } = WIN;
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip();
  ctx.fillStyle = lin(ctx, 0, y0, 0, y1, M
    ? [[0, '#f6d9a6'], [0.5, '#fbe6bf'], [1, '#f3d29c']]
    : [[0, '#dcebf0'], [0.5, '#eef5f0'], [1, '#f6f4e6']]);
  ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  // distant tree line + neighbouring hedge, washed out by the bright day
  const tree = M ? '#b5a46a' : '#a7bf9a', hedge = M ? '#9c9458' : '#8eaa84';
  blurred(ctx, 6, () => {
    for (let i = 0; i < 16; i++) { ctx.fillStyle = rgba(tree, 0.8); ctx.beginPath(); ctx.ellipse(x0 - 40 + i * 32 + R() * 20, 720 + R() * 40, 50 + R() * 30, 70 + R() * 50, 0, 0, 7); ctx.fill(); }
    ctx.fillStyle = rgba(hedge, 0.9); ctx.fillRect(x0 - 20, 830, x1 - x0 + 40, 200);
    for (let i = 0; i < 14; i++) { ctx.beginPath(); ctx.ellipse(x0 - 20 + i * 34, 835 + R() * 10, 30, 22, 0, 0, 7); ctx.fill(); }
  });
  // white picket fence
  for (let x = x0 + 6; x < x1; x += 30) { ctx.fillStyle = M ? 'rgba(255,240,215,0.85)' : 'rgba(250,250,244,0.85)'; ctx.beginPath(); ctx.moveTo(x, 905); ctx.lineTo(x + 8, 895); ctx.lineTo(x + 16, 905); ctx.lineTo(x + 16, 990); ctx.lineTo(x, 990); ctx.closePath(); ctx.fill(); }
  ctx.fillStyle = M ? 'rgba(255,240,215,0.8)' : 'rgba(248,248,240,0.8)'; ctx.fillRect(x0, 925, x1 - x0, 8);
  // sun bloom (top-left, low and golden in the memory)
  softGlow(ctx, M ? 140 : 110, M ? 560 : 400, M ? 360 : 300, M ? '#fff2c8' : '#ffffff', M ? 0.95 : 0.9);
  ctx.fillStyle = lin(ctx, x0, y0, x1, y1, [[0, 'rgba(255,255,255,0.10)'], [0.45, 'rgba(255,255,255,0)'], [0.55, 'rgba(255,255,255,0.08)'], [0.62, 'rgba(255,255,255,0)']]);
  ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.restore();
}

function gingham(ctx, x0, y0, x1, y1, col, cell, lit) {
  ctx.fillStyle = lit; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.fillStyle = rgba(col, 0.42);
  for (let x = x0; x < x1; x += cell * 2) ctx.fillRect(x, y0, cell, y1 - y0);
  for (let y = y0; y < y1; y += cell * 2) ctx.fillRect(x0, y, x1 - x0, cell);
}

function kWindow(ctx, R, P, M) {
  const { x0, y0, x1, y1, rail, mull } = WIN;
  kOutside(ctx, R, M);
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(40,55,45,0.22)'; ctx.fillRect(x0 - 10, y0 - 6, x1 - x0 + 34, y1 - y0 + 60); });
  // casing
  const trim = M ? '#f6ecd8' : '#f0ebe0';
  ctx.fillStyle = trim;
  ctx.beginPath(); ctx.rect(x0 - 26, y0 - 30, x1 - x0 + 52, y1 - y0 + 30); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.fill('evenodd');
  ctx.fillStyle = lin(ctx, 0, y0 - 40, 0, y0 - 24, [[0, '#f8f2e6'], [1, '#d9d0bd']]); rr(ctx, x0 - 36, y0 - 44, x1 - x0 + 72, 18, 3); ctx.fill();
  // sashes / muntins
  ctx.fillStyle = trim;
  ctx.fillRect(x0, rail - 9, x1 - x0, 18);
  ctx.fillRect(mull - 6, y0, 12, y1 - y0);
  ctx.fillRect(x0, 560 - 5, x1 - x0, 10); ctx.fillRect(x0, 840 - 5, x1 - x0, 10);
  ctx.fillStyle = 'rgba(70,80,70,0.22)'; ctx.fillRect(x0, rail + 9, x1 - x0, 3); ctx.fillRect(x0, y0, x1 - x0, 6); ctx.fillRect(x0, y0, 6, y1 - y0);
  ctx.strokeStyle = 'rgba(90,100,90,0.35)'; ctx.lineWidth = 2; ctx.strokeRect(x0 - 26, y0 - 30, x1 - x0 + 52, y1 - y0 + 30);
  // sill + apron
  ctx.fillStyle = lin(ctx, 0, y1, 0, y1 + 16, [[0, '#ddd4c2'], [1, '#f6f0e4']]);
  poly(ctx, [[x0 - 30, y1], [x1 + 30, y1], [x1 + 42, y1 + 16], [x0 - 42, y1 + 16]]); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, y1 + 16, 0, y1 + 36, [[0, '#f2ebdd'], [1, '#d3c9b4']]); rr(ctx, x0 - 42, y1 + 15, x1 - x0 + 84, 20, 3); ctx.fill();
  ctx.fillStyle = trim; ctx.fillRect(x0 - 16, y1 + 35, x1 - x0 + 32, 26);
  blurred(ctx, 6, () => { ctx.fillStyle = 'rgba(40,55,45,0.32)'; ctx.fillRect(x0 - 14, y1 + 60, x1 - x0 + 28, 12); });
  // café curtains on a brass rod at the meeting rail + valance
  const ging = P.ging;
  const lit = M ? '#fff3dc' : '#fbf6ec';
  ctx.fillStyle = lin(ctx, 0, rail - 4, 0, rail + 4, [[0, '#e8cf8e'], [1, '#9c7d45']]); rr(ctx, x0 - 20, rail - 5, x1 - x0 + 40, 9, 4); ctx.fill();
  for (const [a, b] of [[x0 - 8, mull + 4], [mull - 4, x1 + 8]]) {
    ctx.save();
    const hemY = (x) => y1 - 4 + Math.sin(x * 0.11) * 3;
    ctx.beginPath(); ctx.moveTo(a, rail + 2); ctx.lineTo(b, rail + 2); ctx.lineTo(b, hemY(b));
    for (let x = b; x >= a; x -= 6) ctx.lineTo(x, hemY(x));
    ctx.closePath(); ctx.clip();
    gingham(ctx, a, rail, b, y1 + 6, ging, 13, lit);
    // gathered folds + back-lit glow
    for (let x = a; x < b; x += 26) {
      ctx.fillStyle = lin(ctx, x, 0, x + 26, 0, [[0, 'rgba(90,50,45,0.16)'], [0.45, 'rgba(255,255,255,0.12)'], [1, 'rgba(90,50,45,0.14)']]);
      ctx.fillRect(x, rail, 26, y1 - rail + 10);
    }
    ctx.fillStyle = lin(ctx, 0, rail, 0, y1, [[0, 'rgba(255,250,235,0.0)'], [1, 'rgba(255,250,235,0.25)']]); ctx.fillRect(a, rail, b - a, y1 - rail);
    ctx.restore();
    for (let x = a + 8; x < b; x += 26) { ctx.fillStyle = '#b89757'; ctx.beginPath(); ctx.arc(x, rail + 1, 4, 0, 7); ctx.fill(); }
  }
  // valance with scalloped hem
  ctx.save();
  ctx.beginPath(); ctx.moveTo(x0 - 30, y0 - 26);
  ctx.lineTo(x1 + 30, y0 - 26); ctx.lineTo(x1 + 30, y0 + 64);
  for (let x = x1 + 30; x > x0 - 30; x -= 46) ctx.quadraticCurveTo(x - 23, y0 + 92, x - 46, y0 + 64);
  ctx.closePath(); ctx.clip();
  gingham(ctx, x0 - 30, y0 - 30, x1 + 30, y0 + 100, ging, 13, M ? '#fbefd8' : '#f6f1e6');
  for (let x = x0 - 30; x < x1 + 30; x += 23) { ctx.fillStyle = lin(ctx, x, 0, x + 23, 0, [[0, 'rgba(90,50,45,0.16)'], [0.5, 'rgba(255,255,255,0.1)'], [1, 'rgba(90,50,45,0.14)']]); ctx.fillRect(x, y0 - 30, 23, 130); }
  ctx.fillStyle = lin(ctx, 0, y0 - 26, 0, y0 + 90, [[0, 'rgba(60,50,40,0.18)'], [0.3, 'rgba(0,0,0,0)'], [1, 'rgba(255,250,235,0.18)']]); ctx.fillRect(x0 - 30, y0 - 30, x1 - x0 + 60, 130);
  ctx.restore();
  // sill things: a little geranium + a glass jar
  kSillPlant(ctx, 150, y1 + 2, R, M);
  ctx.fillStyle = 'rgba(230,240,240,0.35)'; rr(ctx, 400, y1 - 62, 40, 62, 8); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.fillRect(406, y1 - 54, 4, 44);
  ctx.fillStyle = M ? '#d3a35a' : '#c9b48a'; rr(ctx, 398, y1 - 70, 44, 10, 3); ctx.fill();
}

function kSillPlant(ctx, cx, by, R, M) {
  // terracotta pot
  ctx.fillStyle = lin(ctx, cx - 30, 0, cx + 30, 0, [[0, '#a8674a'], [0.4, '#c98a66'], [1, '#8e5440']]);
  poly(ctx, [[cx - 30, by - 56], [cx + 30, by - 56], [cx + 24, by], [cx - 24, by]]); ctx.fill();
  ctx.fillStyle = '#b97a5a'; rr(ctx, cx - 34, by - 64, 68, 12, 3); ctx.fill();
  // leaves
  for (let i = 0; i < 9; i++) {
    const a = -Math.PI / 2 + (i - 4) * 0.32, L = 34 + R() * 26;
    const x = cx + Math.cos(a) * L, y = by - 66 + Math.sin(a) * L * 0.8;
    ctx.fillStyle = mix('#6e9a62', '#8fb47c', R()); ctx.beginPath(); ctx.ellipse(x, y, 20, 15, a, 0, 7); ctx.fill();
  }
  // a few geranium blooms (soft coral, small)
  for (const [dx, dy] of [[-14, -128], [12, -134], [0, -118]]) {
    for (let k = 0; k < 6; k++) { ctx.fillStyle = M ? '#e0806f' : '#d9928a'; ctx.beginPath(); ctx.arc(cx + dx + Math.cos(k) * 7, by + dy + Math.sin(k) * 6, 6, 0, 7); ctx.fill(); }
  }
}

function kClock(ctx, M, t) {
  const { x, y, r } = CLOCK;
  blurred(ctx, 6, () => { ctx.fillStyle = 'rgba(40,50,45,0.3)'; ctx.beginPath(); ctx.arc(x + 4, y + 8, r + 2, 0, 7); ctx.fill(); });
  ctx.fillStyle = lin(ctx, x - r, y - r, x + r, y + r, [[0, '#e9b79b'], [0.5, M ? '#d98f76' : '#c99886'], [1, '#9a6656']]);
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
  ctx.fillStyle = rad(ctx, x - 10, y - 12, 4, r, [[0, M ? '#fffaf0' : '#fbf8f0'], [1, M ? '#efe0c2' : '#e4ddcc']]);
  ctx.beginPath(); ctx.arc(x, y, r - 8, 0, 7); ctx.fill();
  ctx.fillStyle = '#5a4a40';
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; const L = i % 3 === 0 ? 8 : 4; ctx.save(); ctx.translate(x + Math.sin(a) * (r - 16), y - Math.cos(a) * (r - 16)); ctx.rotate(a); ctx.fillRect(-1.3, -L / 2, 2.6, L); ctx.restore(); }
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(x - 14, y - 22, 24, 10, -0.5, 0, 7); ctx.fill();
}
function clockHands(ctx, hh, mm, ss) {
  const { x, y } = CLOCK;
  const A = (v, n) => (v / n) * Math.PI * 2 - Math.PI / 2;
  ctx.save(); ctx.lineCap = 'round';
  const hand = (ang, len, w, col) => {
    ctx.strokeStyle = 'rgba(40,30,20,0.2)'; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x + 2, y + 3); ctx.lineTo(x + 2 + Math.cos(ang) * len, y + 3 + Math.sin(ang) * len); ctx.stroke();
    ctx.strokeStyle = col; ctx.beginPath(); ctx.moveTo(x - Math.cos(ang) * 6, y - Math.sin(ang) * 6); ctx.lineTo(x + Math.cos(ang) * len, y + Math.sin(ang) * len); ctx.stroke();
  };
  hand(A(hh, 12), 22, 4.5, '#3a2e26');
  hand(A(mm, 60), 33, 3, '#3a2e26');
  if (ss != null) hand(A(ss, 60), 36, 1.2, '#b0503e');
  ctx.fillStyle = '#3a2e26'; ctx.beginPath(); ctx.arc(x, y, 3.2, 0, 7); ctx.fill();
  ctx.restore();
}

function kCalendar(ctx, R, M) {
  const x0 = 560, x1 = 668, y0 = 470, y1 = 640;
  ctx.fillStyle = '#8a7a66'; ctx.beginPath(); ctx.arc(614, 456, 3, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(80,70,60,0.5)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(614, 456); ctx.lineTo(590, y0); ctx.moveTo(614, 456); ctx.lineTo(638, y0); ctx.stroke();
  blurred(ctx, 5, () => { ctx.fillStyle = 'rgba(40,50,45,0.28)'; ctx.fillRect(x0 + 4, y0 + 6, x1 - x0, y1 - y0); });
  ctx.fillStyle = M ? '#fbf5e6' : '#f1ecdf'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  // picture: a faded print of roses in a jug
  ctx.fillStyle = M ? '#cfdcc5' : '#d3d8c9'; ctx.fillRect(x0 + 6, y0 + 6, x1 - x0 - 12, 70);
  ctx.fillStyle = M ? '#8fb0c0' : '#a8b8bd'; rr(ctx, 600, 508, 28, 32, 6); ctx.fill();
  for (const [fx, fy] of [[604, 500], [618, 494], [628, 504], [612, 507]]) { ctx.fillStyle = M ? '#d97f7a' : '#c99a95'; ctx.beginPath(); ctx.arc(fx, fy, 7, 0, 7); ctx.fill(); }
  ctx.fillStyle = M ? '#6f9a62' : '#8ea585'; ctx.beginPath(); ctx.ellipse(596, 500, 8, 4, -0.6, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(634, 498, 8, 4, 0.6, 0, 7); ctx.fill();
  ctx.fillStyle = '#7a5c50'; ctx.font = '9px NanaBgBold'; ctx.textAlign = 'center';
  ctx.fillText(M ? 'JUNE 1999' : 'OCTOBER', 614, y0 + 90);
  // date grid
  ctx.fillStyle = 'rgba(110,90,80,0.55)';
  for (let r = 0; r < 5; r++) for (let c = 0; c < 7; c++) ctx.fillRect(x0 + 8 + c * 13.5, y0 + 100 + r * 12, 8, 5);
  if (!M) { ctx.strokeStyle = 'rgba(176,70,60,0.75)'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.ellipse(x0 + 39, y0 + 126, 8, 6, 0, 0, 7); ctx.stroke(); }
  // curled bottom corner
  ctx.fillStyle = 'rgba(200,190,170,0.9)'; poly(ctx, [[x1, y1 - 14], [x1, y1], [x1 - 14, y1]]); ctx.fill();
}

function kUppers(ctx, R, P, M) {
  const { x0, x1, y0, y1 } = UPPER;
  blurred(ctx, 14, () => { ctx.fillStyle = 'rgba(40,55,45,0.35)'; ctx.fillRect(x0 - 6, y0, x1 - x0 + 20, y1 - y0 + 24); });
  ctx.fillStyle = P.creamDk; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.fillStyle = lin(ctx, 0, y0 - 18, 0, y0, [[0, shade(P.cream, 0.1)], [1, P.creamDk]]); ctx.fillRect(x0 - 12, y0 - 18, x1 - x0 + 24, 18);
  const n = 4, dw = (x1 - x0) / n;
  for (let i = 0; i < n; i++) {
    const dx = x0 + i * dw + 6, w = dw - 12;
    vintageDoor(ctx, dx, y0 + 8, w, y1 - y0 - 18, P);
    const kx = i % 2 === 0 ? dx + w - 22 : dx + 22;
    knob(ctx, kx, y1 - 40, 7);
  }
  // under-cabinet lip
  ctx.fillStyle = shade(P.creamDk, -0.15); ctx.fillRect(x0, y1 - 4, x1 - x0, 6);
  // things on top of the cabinets
  // a cream pitcher and a woven basket (left), a stack of cake tins (right)
  ctx.fillStyle = lin(ctx, 760, 0, 830, 0, [[0, '#d9cdb4'], [0.4, '#f6efe0'], [1, '#bdb196']]);
  ctx.beginPath(); ctx.moveTo(770, y0 - 18); ctx.bezierCurveTo(760, y0 - 60, 770, y0 - 90, 778, y0 - 104); ctx.lineTo(822, y0 - 104); ctx.bezierCurveTo(830, y0 - 90, 840, y0 - 60, 830, y0 - 18); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#cfc3a8'; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(836, y0 - 66, 16, -1.2, 1.3); ctx.stroke();
  ctx.fillStyle = lin(ctx, 0, y0 - 80, 0, y0 - 18, [[0, '#c69b62'], [1, '#8d6a3f']]); rr(ctx, 870, y0 - 78, 150, 60, 10); ctx.fill();
  ctx.strokeStyle = 'rgba(90,60,30,0.35)'; ctx.lineWidth = 2; for (let y = y0 - 70; y < y0 - 20; y += 9) { ctx.beginPath(); ctx.moveTo(874, y); ctx.lineTo(1016, y); ctx.stroke(); }
  for (let k = 0; k < 3; k++) { const w = 120 - k * 18, y = y0 - 18 - (k + 1) * 26; ctx.fillStyle = lin(ctx, 1400 - w / 2, 0, 1400 + w / 2, 0, [[0, M ? '#a95d58' : '#a07a72'], [0.4, M ? '#d48a80' : '#c3a09a'], [1, M ? '#8d4b47' : '#86655e']]); rr(ctx, 1400 - w / 2, y, w, 26, 4); ctx.fill(); }
  if (!M) { // a folded moving box flattened, leaning on top
    ctx.fillStyle = '#c3a272'; poly(ctx, [[1150, y0 - 18], [1170, y0 - 150], [1300, y0 - 140], [1290, y0 - 18]]); ctx.fill();
    ctx.fillStyle = 'rgba(80,55,30,0.25)'; ctx.fillRect(1160, y0 - 100, 136, 3);
  }
}
function vintageDoor(ctx, x, y, w, h, P) {
  ctx.fillStyle = lin(ctx, x, y, x + w, y + h, [[0, shade(P.cream, 0.08)], [1, shade(P.cream, -0.04)]]);
  rr(ctx, x, y, w, h, 8); ctx.fill();
  // rounded inset panel (shadow top-left inside, highlight bottom-right)
  rr(ctx, x + 18, y + 18, w - 36, h - 36, 16);
  ctx.fillStyle = shade(P.cream, -0.03); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.strokeStyle = 'rgba(90,75,50,0.28)'; ctx.lineWidth = 6; rr(ctx, x + 15, y + 15, w - 30, h - 30, 18); ctx.stroke();
  ctx.restore();
  ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = 1.5; rr(ctx, x + 19, y + 19, w - 38, h - 38, 15); ctx.stroke();
  ctx.strokeStyle = 'rgba(110,95,70,0.35)'; ctx.lineWidth = 1.5; rr(ctx, x, y, w, h, 8); ctx.stroke();
}
function knob(ctx, x, y, r) {
  ctx.fillStyle = 'rgba(40,30,20,0.25)'; ctx.beginPath(); ctx.arc(x + 2, y + 3, r + 1, 0, 7); ctx.fill();
  ctx.fillStyle = rad(ctx, x - r * 0.35, y - r * 0.35, 0.5, r, [[0, '#ffffff'], [0.4, '#d7d8d4'], [1, '#7c7f7c']]);
  ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
}
function chromePull(ctx, x, y, w) {
  ctx.fillStyle = 'rgba(40,30,20,0.25)'; rr(ctx, x - w / 2 + 2, y + 2, w, 9, 4); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, y - 1, 0, y + 9, [[0, '#ffffff'], [0.45, '#c9ccca'], [1, '#6f7370']]);
  rr(ctx, x - w / 2, y - 1, w, 9, 4); ctx.fill();
}

function kBacksplash(ctx, R, P) {
  const x0 = COUNTER.x0, x1 = 1600 + KM, y1 = COUNTER.back;
  const T = 38, top = (x) => (x < UPPER.x0 ? 800 : UPPER.y1), y0 = UPPER.y1;
  ctx.fillStyle = shade(P.tileB, -0.05); ctx.fillRect(x0, 800, UPPER.x0 - x0, y1 - 800); ctx.fillRect(UPPER.x0, y0, x1 - UPPER.x0, y1 - y0);
  for (let y = y1 - T; y > y0 - T; y -= T) {
    for (let x = x0; x < x1; x += T) {
      const yy = Math.max(y, top(x));
      if (y + T - yy < 6) continue;
      ctx.fillStyle = mix(P.tileA, P.tileB, R() * 0.7);
      rr(ctx, x + 1.5, yy + 1.5, T - 3, y + T - yy - 3, 3); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(x + 4, yy + 3, T - 10, 2);
    }
  }
  // mint bullnose cap
  ctx.fillStyle = lin(ctx, 0, y0 - 14, 0, y0 + 2, [[0, shade(P.lam, 0.25)], [1, shade(P.lam, -0.15)]]); rr(ctx, x0 - 4, 786, UPPER.x0 - x0 + 4, 16, 6); ctx.fill();
  // under-cabinet shadow on wall + tiles
  ctx.fillStyle = lin(ctx, 0, UPPER.y1, 0, UPPER.y1 + 150, [[0, 'rgba(35,45,40,0.35)'], [1, 'rgba(35,45,40,0)']]);
  ctx.fillRect(UPPER.x0 - 10, UPPER.y1, UPPER.x1 - UPPER.x0 + 10, 150);
}

function kCounterAndBase(ctx, R, P, M) {
  const { x0, x1, back, front, edge } = COUNTER;
  const segs = [[x0, STOVE.x0], [STOVE.x1, x1 + KM]];
  for (const [a, b] of segs) {
    // base cabinets
    ctx.fillStyle = P.creamDk; ctx.fillRect(a, edge, b - a, FLOOR_Y - edge);
    const n = Math.max(1, Math.round((b - a) / 230)), dw = (b - a) / n;
    for (let i = 0; i < n; i++) {
      const dx = a + i * dw + 6, w = dw - 12;
      vintageDoor(ctx, dx, edge + 10, w, 74, P); chromePull(ctx, dx + w / 2, edge + 42, 54);
      vintageDoor(ctx, dx, edge + 94, w, FLOOR_Y - edge - 150, P);
      knob(ctx, i % 2 === 0 ? dx + w - 24 : dx + 24, edge + 130, 7);
    }
    ctx.fillStyle = '#4f5a52'; ctx.fillRect(a, FLOOR_Y - 46, b - a, 46);
    ctx.fillStyle = lin(ctx, 0, FLOOR_Y - 50, 0, FLOOR_Y - 40, [[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0.2)']]); ctx.fillRect(a, FLOOR_Y - 50, b - a, 10);
    ctx.fillStyle = lin(ctx, 0, edge, 0, edge + 40, [[0, 'rgba(30,30,20,0.38)'], [1, 'rgba(30,30,20,0)']]); ctx.fillRect(a, edge, b - a, 40);
    // laminate top + chrome edge
    ctx.fillStyle = lin(ctx, 0, back, 0, front, [[0, shade(P.lam, -0.12)], [1, shade(P.lam, 0.08)]]);
    poly(ctx, [[a, back], [b, back], [b + (a === x0 ? 0 : 0), front], [a - (a === x0 ? 10 : 0), front]]); ctx.fill();
    // boomerang flecks
    for (let i = 0; i < (b - a) / 6; i++) { ctx.fillStyle = rgba(R() < 0.5 ? '#ffffff' : '#5f8679', 0.2); const fx = lerp(a, b, R()), fy = lerp(back + 3, front - 3, R()); ctx.fillRect(fx, fy, 4 + R() * 6, 1.4); }
    ctx.fillStyle = lin(ctx, 0, front, 0, edge, [[0, '#f4f5f2'], [0.35, '#b9bdb9'], [0.7, '#e2e4e0'], [1, '#7f8480']]);
    ctx.fillRect(a - (a === x0 ? 10 : 0), front, b - a + 10, edge - front);
    ctx.fillStyle = 'rgba(40,45,40,0.25)'; ctx.fillRect(a - 10, edge - 1, b - a + 10, 2);
    if (a === x0) { // left end panel of the run
      ctx.fillStyle = lin(ctx, a - 14, 0, a, 0, [[0, shade(P.creamDk, -0.18)], [1, shade(P.creamDk, -0.06)]]); ctx.fillRect(a - 14, edge, 14, FLOOR_Y - edge - 46);
    }
  }
  // back-of-counter contact shadow against the tiles
  ctx.fillStyle = lin(ctx, 0, back - 10, 0, back + 6, [[0, 'rgba(30,40,35,0)'], [1, 'rgba(30,40,35,0.22)']]); ctx.fillRect(x0, back - 10, x1 + KM - x0, 16);
}

function kStove(ctx, R, P, M) {
  const { x0, x1 } = STOVE, E = P.enamel;
  const top = COUNTER.back - 6, front = COUNTER.front + 2;
  // backguard
  blurred(ctx, 8, () => { ctx.fillStyle = 'rgba(40,50,45,0.3)'; ctx.fillRect(x0 + 6, 930, x1 - x0, 150); });
  ctx.fillStyle = lin(ctx, 0, 924, 0, top, [[0, shade(E, 0.04)], [1, shade(E, -0.08)]]); rr(ctx, x0 + 4, 924, x1 - x0 - 8, top - 924 + 6, 10); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 944, 0, 990, [[0, '#f6f7f4'], [0.5, '#a9adaa'], [1, '#e7e9e6']]); rr(ctx, x0 + 26, 948, x1 - x0 - 52, 40, 6); ctx.fill();
  // little timer clock in the chrome strip
  ctx.fillStyle = '#f9f6ec'; ctx.beginPath(); ctx.arc((x0 + x1) / 2, 968, 15, 0, 7); ctx.fill();
  ctx.strokeStyle = '#6a625a'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo((x0 + x1) / 2, 968); ctx.lineTo((x0 + x1) / 2 + 6, 960); ctx.moveTo((x0 + x1) / 2, 968); ctx.lineTo((x0 + x1) / 2 - 2, 957); ctx.stroke();
  // cooktop
  ctx.fillStyle = lin(ctx, 0, top, 0, front, [[0, shade(E, -0.12)], [1, shade(E, 0.02)]]);
  poly(ctx, [[x0, top], [x1, top], [x1 + 2, front], [x0 - 2, front]]); ctx.fill();
  for (const [bx, by, r] of [[x0 + 68, top + 14, 44], [x1 - 68, top + 14, 44], [x0 + 70, front - 12, 50], [x1 - 70, front - 12, 50]]) {
    ctx.fillStyle = '#3d3a37'; ctx.beginPath(); ctx.ellipse(bx, by, r, r * 0.16, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = '#6c6965'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(bx, by - 2, r * 0.6, r * 0.09, 0, 0, 7); ctx.stroke();
    ctx.strokeStyle = 'rgba(200,200,195,0.5)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.ellipse(bx, by - 3, r, r * 0.16, 0, Math.PI, 2 * Math.PI); ctx.stroke();
  }
  // body
  const yb = front;
  ctx.fillStyle = lin(ctx, x0, 0, x1, 0, [[0, shade(E, -0.1)], [0.15, E], [0.85, shade(E, -0.02)], [1, shade(E, -0.14)]]);
  rr(ctx, x0, yb, x1 - x0, FLOOR_Y - 40 - yb, 6); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, yb, 0, yb + 58, [[0, '#e9ebe8'], [0.5, '#bcc0bc'], [1, '#dfe1de']]); ctx.fillRect(x0 + 4, yb, x1 - x0 - 8, 56);
  for (let i = 0; i < 4; i++) {
    const kx = x0 + 40 + i * ((x1 - x0 - 80) / 3);
    ctx.fillStyle = 'rgba(30,25,20,0.3)'; ctx.beginPath(); ctx.arc(kx + 2, yb + 31, 14, 0, 7); ctx.fill();
    ctx.fillStyle = rad(ctx, kx - 4, yb + 24, 1, 14, [[0, '#ffffff'], [0.5, '#d8d4c8'], [1, '#8b857a']]); ctx.beginPath(); ctx.arc(kx, yb + 28, 13, 0, 7); ctx.fill();
    ctx.fillStyle = '#5a554e'; ctx.fillRect(kx - 1.5, yb + 17, 3, 9);
  }
  // oven door with window + chrome handle
  const dy0 = yb + 78, dy1 = FLOOR_Y - 100;
  ctx.strokeStyle = 'rgba(110,100,85,0.45)'; ctx.lineWidth = 2; rr(ctx, x0 + 14, dy0, x1 - x0 - 28, dy1 - dy0, 10); ctx.stroke();
  ctx.fillStyle = lin(ctx, 0, dy0 + 60, 0, dy0 + 170, [[0, '#2f2c2a'], [1, '#4a4642']]); rr(ctx, x0 + 54, dy0 + 60, x1 - x0 - 108, 110, 10); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; poly(ctx, [[x0 + 64, dy0 + 66], [x0 + 110, dy0 + 66], [x0 + 80, dy0 + 164], [x0 + 60, dy0 + 164]]); ctx.fill();
  chromePull(ctx, (x0 + x1) / 2, dy0 + 22, x1 - x0 - 90);
  ctx.strokeStyle = 'rgba(110,100,85,0.4)'; rr(ctx, x0 + 14, dy1 + 10, x1 - x0 - 28, 40, 6); ctx.stroke();
  chromePull(ctx, (x0 + x1) / 2, dy1 + 26, 70);
  ctx.fillStyle = '#4b4743'; ctx.fillRect(x0 + 10, FLOOR_Y - 40, x1 - x0 - 20, 40);
  for (const fx of [x0 + 14, x1 - 34]) { ctx.fillStyle = '#9da09c'; rr(ctx, fx, FLOOR_Y - 40, 20, 40, 3); ctx.fill(); }
  ctx.fillStyle = lin(ctx, 0, yb, 0, yb + 30, [[0, 'rgba(30,30,20,0.25)'], [1, 'rgba(30,30,20,0)']]); ctx.fillRect(x0, yb, x1 - x0, 30);
  if (M) { // a kettle on the back burner in the memory
    const kx = x1 - 68, ky = top + 14;
    ctx.fillStyle = lin(ctx, kx - 50, 0, kx + 50, 0, [[0, '#8a4c44'], [0.35, '#d68a77'], [1, '#7a423b']]);
    ctx.beginPath(); ctx.moveTo(kx - 48, ky); ctx.bezierCurveTo(kx - 56, ky - 70, kx + 56, ky - 70, kx + 48, ky); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = '#3c3430'; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(kx, ky - 62, 30, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke();
    ctx.fillStyle = '#7a423b'; poly(ctx, [[kx + 40, ky - 26], [kx + 78, ky - 58], [kx + 82, ky - 52], [kx + 46, ky - 14]]); ctx.fill();
  }
}

// checkered linoleum floor in one-point perspective
function kFloor(ctx, R, P, M) {
  const D = 1500, T = 84, Hh = FLOOR_Y - VP.y;
  ctx.fillStyle = P.floorA; ctx.fillRect(KC.x0, FLOOR_Y, KC.x1 - KC.x0, KC.y1 - FLOOR_Y);
  const fp = (X, z) => { const k = D / z; return [VP.x + (X - VP.x) * k, VP.y + Hh * k]; };
  const N = makeNoise(77);
  for (let r = 0; ; r++) {
    const za = D - r * T, zb = D - (r + 1) * T;
    if (zb < 520) break;
    for (let c = -30; c < 30; c++) {
      const Xa = VP.x + c * T - T / 2, Xb = Xa + T;
      const p = [fp(Xa, za), fp(Xb, za), fp(Xb, zb), fp(Xa, zb)];
      if (p[1][0] < KC.x0 - 10 || p[0][0] > KC.x1 + 10) continue;
      const dark = (r + c) & 1;
      const v = (N(c * 0.9 + 3, r * 0.9) - 0.5) * 0.06;
      ctx.fillStyle = shade(dark ? P.floorB : P.floorA, v);
      poly(ctx, p); ctx.fill();
    }
  }
  // grout seams (thin, low contrast)
  ctx.strokeStyle = 'rgba(90,70,60,0.12)'; ctx.lineWidth = 1.2;
  for (let c = -30; c < 30; c++) { const X = VP.x + c * T - T / 2; const a = fp(X, D), b = fp(X, 520); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
  // wear: a paler, scuffed path in front of the counter and stove + general sheen
  blurred(ctx, 30, () => {
    ctx.fillStyle = M ? 'rgba(255,248,230,0.10)' : 'rgba(250,245,232,0.26)';
    ctx.beginPath(); ctx.ellipse(1080, 1640, 420, 90, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.ellipse(720, 1780, 260, 70, -0.2, 0, 7); ctx.fill();
  });
  if (!M) {
    for (let i = 0; i < 140; i++) { // scuffs
      const x = lerp(500, 1500, R()), y = lerp(1560, 1900, R());
      ctx.strokeStyle = `rgba(120,95,80,${0.06 + R() * 0.07})`; ctx.lineWidth = 1 + R() * 1.5;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + 20, y + (R() - 0.5) * 6, x + 30 + R() * 50, y + (R() - 0.5) * 8); ctx.stroke();
    }
    blurred(ctx, 3, () => { ctx.fillStyle = 'rgba(150,120,100,0.15)'; ctx.beginPath(); ctx.ellipse(1240, 1700, 40, 10, 0.3, 0, 7); ctx.fill(); });
  }
  // depth: darker toward the camera, AO at the wall line
  ctx.fillStyle = lin(ctx, 0, FLOOR_Y, 0, KC.y1, [[0, 'rgba(255,240,215,0.06)'], [0.35, 'rgba(0,0,0,0)'], [1, M ? 'rgba(70,35,15,0.35)' : 'rgba(35,40,40,0.32)']]);
  ctx.fillRect(KC.x0, FLOOR_Y, KC.x1 - KC.x0, KC.y1 - FLOOR_Y);
  ctx.fillStyle = lin(ctx, 0, FLOOR_Y, 0, FLOOR_Y + 70, [[0, 'rgba(30,30,25,0.4)'], [1, 'rgba(30,30,25,0)']]);
  ctx.fillRect(KC.x0, FLOOR_Y, KC.x1 - KC.x0, 70);
  // baseboard left of the counter
  ctx.fillStyle = lin(ctx, 0, FLOOR_Y - 50, 0, FLOOR_Y, [[0, '#f3eee2'], [0.15, '#e3dccb'], [1, '#c5bca8']]);
  ctx.fillRect(KC.x0, FLOOR_Y - 50, COUNTER.x0 - 14 - KC.x0, 50);
  ctx.fillStyle = 'rgba(50,60,50,0.25)'; ctx.fillRect(KC.x0, FLOOR_Y - 50, COUNTER.x0 - 14 - KC.x0, 2);
}

// ---------------------------------------------------------------- props
function prism(ctx, x0, x1, yb, h, k, front, top, side) {
  const ft = yb - h;
  const bl = persp(x0, ft, k), br = persp(x1, ft, k), bbr = persp(x1, yb, k), bbl = persp(x0, yb, k);
  // side face toward the vanishing point
  if (x1 < VP.x) { ctx.fillStyle = side; poly(ctx, [[x1, ft], br, bbr, [x1, yb]]); ctx.fill(); }
  else if (x0 > VP.x) { ctx.fillStyle = side; poly(ctx, [[x0, ft], bl, bbl, [x0, yb]]); ctx.fill(); }
  ctx.fillStyle = top; poly(ctx, [[x0, ft], [x1, ft], br, bl]); ctx.fill();
  ctx.fillStyle = front; ctx.fillRect(x0, ft, x1 - x0, h);
  return { ft, bl, br };
}
const CARD = '#c4a273', CARD_D = '#a5845a', CARD_T = '#d4b585';
function box(ctx, R, x0, x1, yb, h, label, opts = {}) {
  contact(ctx, (x0 + x1) / 2 + 20, yb - 4, (x1 - x0) * 0.75, 22, 0.45);
  const b = prism(ctx, x0, x1, yb, h, 0.94, CARD, CARD_T, CARD_D);
  // shading on the front + corrugated edge
  ctx.fillStyle = lin(ctx, x0, 0, x1, 0, [[0, 'rgba(255,240,210,0.12)'], [1, 'rgba(60,40,20,0.12)']]); ctx.fillRect(x0, b.ft, x1 - x0, h);
  ctx.fillStyle = 'rgba(80,55,30,0.35)'; ctx.fillRect(x0, b.ft, x1 - x0, 1.5);
  if (!opts.open) {
    // seam + packing tape over the top and down the front
    const mx = (x0 + x1) / 2;
    ctx.strokeStyle = 'rgba(90,65,35,0.4)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo((b.bl[0] + x0) / 2, (b.bl[1] + b.ft) / 2); ctx.lineTo((b.br[0] + x1) / 2, (b.br[1] + b.ft) / 2); ctx.stroke();
    ctx.fillStyle = 'rgba(214,196,150,0.85)';
    const tw = 16, k = 0.94, tb = persp(mx, b.ft, k);
    poly(ctx, [[mx - tw, b.ft], [mx + tw, b.ft], [tb[0] + tw * k, tb[1]], [tb[0] - tw * k, tb[1]]]); ctx.fill();
    ctx.fillRect(mx - tw, b.ft, tw * 2, 42);
    ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(mx - tw + 3, b.ft, 3, 42);
  }
  if (label) {
    ctx.save(); ctx.fillStyle = 'rgba(55,45,40,0.78)'; ctx.font = `${opts.fs || 22}px NanaBgBold`; ctx.textAlign = 'center';
    ctx.translate(x0 + (x1 - x0) * (opts.lx || 0.5), b.ft + h * 0.62); ctx.rotate(opts.rot || -0.04); ctx.fillText(label, 0, 0); ctx.restore();
  }
  return b;
}
function crumple(ctx, R, cx, cy, r) { // a newspaper-wrapped dish/ball
  ctx.fillStyle = mix('#ddd8cc', '#c9c3b5', R());
  ctx.beginPath();
  for (let i = 0; i <= 10; i++) { const a = i / 10 * Math.PI * 2, rr2 = r * (0.85 + R() * 0.25); ctx.lineTo(cx + Math.cos(a) * rr2, cy + Math.sin(a) * rr2 * 0.8); }
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(80,80,80,0.28)'; ctx.lineWidth = 1;
  for (let j = 0; j < 4; j++) { const y = cy - r * 0.4 + j * r * 0.25; ctx.beginPath(); ctx.moveTo(cx - r * 0.5, y); ctx.lineTo(cx + r * (0.2 + R() * 0.3), y + (R() - 0.5) * 3); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(110,110,100,0.4)'; ctx.beginPath(); ctx.moveTo(cx - r * 0.2, cy - r * 0.6); ctx.lineTo(cx + r * 0.1, cy + r * 0.1); ctx.stroke();
}
function openBox(ctx, R, x0, x1, yb, h, label) {
  const b = box(ctx, R, x0, x1, yb, h, label, { open: true, fs: 18 });
  // interior (back wall visible through the top)
  ctx.fillStyle = '#7a5c3a'; poly(ctx, [[x0 + 4, b.ft], [x1 - 4, b.ft], b.br, b.bl]); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, b.bl[1], 0, b.ft, [[0, '#9c7a52'], [1, '#5e4428']]); poly(ctx, [[x0 + 6, b.ft], [x1 - 6, b.ft], [b.br[0] - 4, b.br[1] + 6], [b.bl[0] + 4, b.bl[1] + 6]]); ctx.fill();
  // wrapped dishes peeking out
  const n = Math.round((x1 - x0) / 34);
  for (let i = 0; i < n; i++) crumple(ctx, R, lerp(x0 + 22, x1 - 22, i / Math.max(1, n - 1)) + (R() - 0.5) * 8, b.ft - 10 - R() * 12, 22 + R() * 6);
  // a plate edge standing up
  ctx.fillStyle = '#f4f1ea'; ctx.beginPath(); ctx.ellipse(lerp(x0, x1, 0.62), b.ft - 30, 30, 34, 0.2, Math.PI, 2 * Math.PI); ctx.fill();
  ctx.strokeStyle = 'rgba(120,150,170,0.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(lerp(x0, x1, 0.62), b.ft - 30, 24, 28, 0.2, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
  // flaps folded out
  ctx.fillStyle = CARD_T; poly(ctx, [[x0, b.ft], [x1, b.ft], [x1 + 8, b.ft + 44], [x0 - 8, b.ft + 44]]);
  ctx.fillStyle = shade(CARD, 0.05); poly(ctx, [[x0, b.ft], [x1, b.ft], [x1 - 4, b.ft - 6], [x0 + 4, b.ft - 6]]); ctx.fill();
  ctx.fillStyle = CARD_D; poly(ctx, [[x0, b.ft], [x0 - 36, b.ft - 20], [b.bl[0] - 40, b.bl[1] - 18], b.bl]); ctx.fill();
  ctx.fillStyle = CARD; poly(ctx, [[x1, b.ft], [x1 + 30, b.ft - 26], [b.br[0] + 30, b.br[1] - 26], b.br]); ctx.fill();
  ctx.fillStyle = 'rgba(80,55,30,0.3)'; ctx.fillRect(x0, b.ft, x1 - x0, 2);
  return b;
}
function dustSheetChair(ctx, R) {
  // a ladder-back chair under a dust sheet; feet at y≈1690
  contact(ctx, -170, 1690, 170, 24, 0.5);
  const col = '#ece6da';
  ctx.fillStyle = lin(ctx, -320, 0, -40, 0, [[0, '#d6cfc1'], [0.4, col], [1, '#c2baab']]);
  ctx.beginPath();
  ctx.moveTo(-262, 1150); ctx.quadraticCurveTo(-230, 1110, -150, 1118); ctx.quadraticCurveTo(-110, 1124, -100, 1170);
  ctx.lineTo(-92, 1400); ctx.quadraticCurveTo(-40, 1410, -36, 1450); ctx.lineTo(-30, 1690);
  for (let x = -30; x > -320; x -= 22) ctx.quadraticCurveTo(x - 11, 1700 + Math.sin(x) * 6, x - 22, 1690);
  ctx.lineTo(-312, 1460); ctx.quadraticCurveTo(-300, 1420, -268, 1410); ctx.closePath(); ctx.fill();
  // folds
  ctx.save(); ctx.clip();
  for (const [x, a] of [[-280, 0.12], [-230, 0.1], [-170, 0.13], [-110, 0.1], [-70, 0.12]]) {
    ctx.fillStyle = lin(ctx, x - 18, 0, x + 18, 0, [[0, 'rgba(80,70,55,0)'], [0.5, `rgba(80,70,55,${a})`], [1, 'rgba(80,70,55,0)']]);
    ctx.fillRect(x - 18, 1150, 36, 560);
  }
  ctx.fillStyle = lin(ctx, 0, 1400, 0, 1470, [[0, 'rgba(255,255,255,0.3)'], [1, 'rgba(80,70,55,0.12)']]); ctx.fillRect(-330, 1400, 320, 70);
  ctx.fillStyle = lin(ctx, 0, 1500, 0, 1700, [[0, 'rgba(70,60,50,0)'], [1, 'rgba(70,60,50,0.2)']]); ctx.fillRect(-330, 1500, 320, 200);
  ctx.restore();
}
function canister(ctx, cx, by, w, h, col, label) {
  contact(ctx, cx + 6, by, w * 0.6, 7, 0.35);
  ctx.fillStyle = lin(ctx, cx - w / 2, 0, cx + w / 2, 0, [[0, shade(col, -0.15)], [0.35, shade(col, 0.15)], [1, shade(col, -0.22)]]);
  rr(ctx, cx - w / 2, by - h, w, h, 6); ctx.fill();
  ctx.fillStyle = lin(ctx, cx - w / 2, 0, cx + w / 2, 0, [[0, '#a8aba7'], [0.4, '#f5f6f3'], [1, '#7f827f']]); rr(ctx, cx - w / 2 - 2, by - h - 12, w + 4, 14, 4); ctx.fill();
  ctx.fillStyle = '#d0d2ce'; rr(ctx, cx - 8, by - h - 20, 16, 9, 3); ctx.fill();
  ctx.fillStyle = 'rgba(70,60,55,0.7)'; ctx.font = `${Math.round(w * 0.16)}px NanaBgBold`; ctx.textAlign = 'center'; ctx.fillText(label, cx, by - h * 0.45);
}

// ---------------------------------------------------------------- the recipe tin (sprites, drawn per frame)
function tinPaint(ctx, M, part) {
  // local coords: bottom centre at (0,0); body h = TIN.h; rx, ry
  const { rx, ry, h } = TIN, body = M ? '#5f9f96' : '#86a8a0';
  const flower = (x, y, s, c) => {
    for (let k = 0; k < 5; k++) { const a = k / 5 * Math.PI * 2; ctx.fillStyle = c; ctx.beginPath(); ctx.ellipse(x + Math.cos(a) * 5 * s, y + Math.sin(a) * 5 * s, 4.6 * s, 3.4 * s, a, 0, 7); ctx.fill(); }
    ctx.fillStyle = M ? '#f2cf6c' : '#e2cf9a'; ctx.beginPath(); ctx.arc(x, y, 2.4 * s, 0, 7); ctx.fill();
  };
  if (part === 'body') {
    contact(ctx, 6, 0, rx * 1.15, 12, 0.5);
    ctx.fillStyle = body;
    ctx.beginPath(); ctx.moveTo(-rx, -h); ctx.lineTo(-rx, 0); ctx.ellipse(0, 0, rx, ry, 0, Math.PI, 0, true); ctx.lineTo(rx, -h); ctx.closePath(); ctx.fill();
    ctx.save(); ctx.clip();
    // flowers wrapped around the cylinder
    const R = mulberry32(M ? 5 : 5);
    for (let i = 0; i < 26; i++) {
      const th = (R() - 0.5) * Math.PI * 0.95, y = -h * (0.18 + R() * 0.62);
      const x = Math.sin(th) * rx, s = 0.9 + R() * 0.6, sq = Math.cos(th);
      ctx.save(); ctx.translate(x, y); ctx.scale(Math.max(0.3, sq), 1);
      ctx.fillStyle = M ? '#6f9a5c' : '#93ad8c'; ctx.beginPath(); ctx.ellipse(-7 * s, 5 * s, 6 * s, 2.6 * s, 0.6, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(7 * s, 4 * s, 6 * s, 2.6 * s, -0.5, 0, 7); ctx.fill();
      flower(0, 0, s, [M ? '#e9a3a0' : '#dcb4ae', M ? '#fbf3e4' : '#efe7d8', M ? '#d7838b' : '#c9a5a6'][i % 3]);
      ctx.restore();
    }
    // cylindrical shading + rolled bands
    ctx.fillStyle = lin(ctx, -rx, 0, rx, 0, [[0, 'rgba(25,35,35,0.42)'], [0.22, 'rgba(255,255,255,0.12)'], [0.35, 'rgba(255,255,255,0.22)'], [0.7, 'rgba(25,35,35,0.06)'], [1, 'rgba(25,35,35,0.48)']]);
    ctx.fillRect(-rx, -h - 2, rx * 2, h + ry + 4);
    if (!M) { ctx.fillStyle = 'rgba(235,228,210,0.18)'; ctx.fillRect(-rx, -h, rx * 2, h + ry); } // faded
    ctx.restore();
    ctx.strokeStyle = M ? 'rgba(220,200,140,0.9)' : 'rgba(200,190,160,0.8)'; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.ellipse(0, -6, rx - 1, ry, 0, 0, Math.PI); ctx.stroke();
    // a few soft scratches / worn spots on the old tin
    if (!M) { ctx.strokeStyle = 'rgba(230,225,210,0.35)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(-30, -60); ctx.lineTo(-12, -54); ctx.moveTo(18, -30); ctx.lineTo(34, -36); ctx.stroke(); }
  } else if (part === 'mouth') { // open top: rim + interior with recipe cards
    ctx.fillStyle = '#2f3533'; ctx.beginPath(); ctx.ellipse(0, -h, rx - 2, ry - 1, 0, 0, 7); ctx.fill();
    ctx.fillStyle = lin(ctx, 0, -h - ry, 0, -h + ry, [[0, '#4d4f48'], [1, '#8b8c84']]); ctx.beginPath(); ctx.ellipse(0, -h, rx - 4, ry - 3, 0, 0, Math.PI); ctx.fill();
    // recipe cards standing in the tin
    ctx.save(); ctx.beginPath(); ctx.rect(-rx, -h - 40, rx * 2, 40); ctx.ellipse(0, -h, rx - 4, ry - 3, 0, 0, Math.PI); ctx.clip();
    const cols = ['#f3ead6', '#efe2c6', '#f7f0e0', '#ead9bb'];
    for (let i = 0; i < 7; i++) { const x = -42 + i * 12, top = -h - 9 + ((i * 5) % 7) - (i === 3 ? 6 : 0), w = 84 - Math.abs(i - 3) * 6; ctx.fillStyle = cols[i % 4]; ctx.fillRect(-w / 2, top + i * 1.6, w, 30); ctx.fillStyle = 'rgba(90,70,50,0.28)'; ctx.fillRect(-w / 2, top + i * 1.6, w, 1.4); }
    ctx.fillStyle = '#e2b9a2'; ctx.fillRect(10, -h - 17, 16, 10); // a tab divider
    ctx.restore();
    ctx.strokeStyle = M ? '#d8c58c' : '#c7bc9c'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.ellipse(0, -h, rx - 1, ry, 0, 0, 7); ctx.stroke();
  } else if (part === 'lid') { // lid local origin: its bottom-centre
    const lh = 22, lrx = rx + 4;
    ctx.fillStyle = shade(body, -0.05);
    ctx.beginPath(); ctx.moveTo(-lrx, -lh); ctx.lineTo(-lrx, 0); ctx.ellipse(0, 0, lrx, ry + 1, 0, Math.PI, 0, true); ctx.lineTo(lrx, -lh); ctx.closePath(); ctx.fill();
    ctx.fillStyle = lin(ctx, -lrx, 0, lrx, 0, [[0, 'rgba(25,35,35,0.45)'], [0.3, 'rgba(255,255,255,0.2)'], [1, 'rgba(25,35,35,0.5)']]);
    ctx.beginPath(); ctx.moveTo(-lrx, -lh); ctx.lineTo(-lrx, 0); ctx.ellipse(0, 0, lrx, ry + 1, 0, Math.PI, 0, true); ctx.lineTo(lrx, -lh); ctx.closePath(); ctx.fill();
    ctx.fillStyle = M ? '#e2c98a' : '#cfc1a0'; ctx.fillRect(-lrx, -lh + 6, lrx * 2, 3);
    // top face with a painted bouquet
    ctx.fillStyle = rad(ctx, -18, -lh - 4, 4, lrx, [[0, shade(body, 0.22)], [1, shade(body, -0.02)]]);
    ctx.beginPath(); ctx.ellipse(0, -lh, lrx, ry + 1, 0, 0, 7); ctx.fill();
    ctx.save(); ctx.translate(0, -lh); ctx.scale(1, (ry + 1) / lrx);
    for (const [x, y, c] of [[-16, -6, M ? '#e9a3a0' : '#dcb4ae'], [10, -14, M ? '#fbf3e4' : '#efe7d8'], [14, 12, M ? '#d7838b' : '#c9a5a6'], [-8, 16, M ? '#fbf3e4' : '#efe7d8'], [30, -2, M ? '#e9a3a0' : '#dcb4ae']]) {
      ctx.fillStyle = M ? '#6f9a5c' : '#93ad8c'; ctx.beginPath(); ctx.ellipse(x + 8, y + 6, 9, 4, 0.5, 0, 7); ctx.fill();
      flower(x, y, 2.2, c);
    }
    ctx.restore();
    if (!M) { ctx.fillStyle = 'rgba(235,228,210,0.2)'; ctx.beginPath(); ctx.ellipse(0, -lh, lrx, ry + 1, 0, 0, 7); ctx.fill(); }
    ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.ellipse(0, -lh, lrx - 1, ry, 0, Math.PI * 1.05, Math.PI * 1.6); ctx.stroke();
  }
}
function spriteOf(x0, y0, x1, y1, fn, s = 2) { const c = newCache(x0, y0, x1, y1, s); fn(c.ctx); return c; }
function drawSprite(ctx, c, x, y) { ctx.drawImage(c.cv, x + c.x0, y + c.y0, c.w, c.h); }

// ---------------------------------------------------------------- sunlight
function shaftGeom(M) {
  // window glass -> floor patch. Morning: high sun, patch near the wall; memory: low golden sun, long patch.
  return M
    ? { far: [[440, 1590], [960, 1590]], near: [[840, 2060], [1520, 2060]] }
    : { far: [[330, 1585], [770, 1585]], near: [[640, 2090], [1220, 2090]] };
}
function kSunlight(ctx, M) {
  const g = shaftGeom(M);
  const warm = M ? '#ffd58a' : '#fff1cf';
  // floor patch, split by the window muntins/rail (upper sash -> far forward, lower sash through the curtains -> dimmer)
  const P = (u, v) => [lerp(lerp(g.far[0][0], g.far[1][0], u), lerp(g.near[0][0], g.near[1][0], u), v), lerp(lerp(g.far[0][1], g.far[1][1], u), lerp(g.near[0][1], g.near[1][1], u), v)];
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  blurred(ctx, M ? 9 : 7, () => {
    const cols = [[0, 0.48], [0.52, 1]], rows = [[0, 0.24, 0.45], [0.27, 0.49, 0.45], [0.53, 0.74, 0.8], [0.77, 1, 0.8]];
    // rows from far (lower sash, through curtain) to near (upper sash, clear)
    for (const [u0, u1] of cols) for (const [v0, v1, a] of rows) {
      ctx.fillStyle = rgba(warm, (M ? 0.6 : 0.62) * a);
      poly(ctx, [P(u0, v0), P(u1, v0), P(u1, v1), P(u0, v1)]); ctx.fill();
    }
  });
  ctx.restore();
  // a warm wash on the wall/counter around the window
  softGlow(ctx, 300, 760, 700, warm, M ? 0.28 : 0.2, 0.9);
  if (M) softGlow(ctx, 1000, 1100, 900, '#ffcf8a', 0.16, 0.6);
}
function kShafts(ctx, M) {
  const g = shaftGeom(M);
  const warm = M ? '#ffd890' : '#fff4dc';
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  blurred(ctx, 18, () => {
    // three bands (two sash columns + a soft overall haze)
    const band = (u0, u1, a) => {
      const L = (u) => [lerp(WIN.x0, WIN.x1, u), WIN.y0 + 40], Lb = (u) => [lerp(WIN.x0, WIN.x1, u), WIN.y1];
      const F = (u) => [lerp(g.near[0][0], g.near[1][0], u), lerp(g.near[0][1], g.near[1][1], u)];
      const pts = [L(u0), L(u1), F(u1), F(u0)];
      const grd = lin(ctx, (pts[0][0] + pts[1][0]) / 2, WIN.y0, (pts[2][0] + pts[3][0]) / 2, pts[2][1], [[0, rgba(warm, a)], [0.5, rgba(warm, a * 0.6)], [1, rgba(warm, 0)]]);
      ctx.fillStyle = grd; poly(ctx, pts); ctx.fill();
    };
    band(0.03, 0.47, M ? 0.55 : 0.55); band(0.53, 0.97, M ? 0.55 : 0.55); band(-0.1, 1.1, M ? 0.2 : 0.18);
    // a few thin brighter rays inside the beams
    band(0.12, 0.2, 0.35); band(0.3, 0.36, 0.25); band(0.64, 0.72, 0.3); band(0.84, 0.9, 0.25);
  });
  ctx.restore();
}
// dust motes: shaft-local (u across, v along) -> world, smooth drift; faded at the shaft ends so wrapping never pops
const MOTES = (() => { const R = mulberry32(4242), a = []; for (let i = 0; i < 70; i++) a.push({ u: R(), v: R(), sp: 0.006 + R() * 0.01, ph: R() * 6.28, r: 1.2 + R() * 2.4, w: 0.5 + R() * 0.5, f: 0.15 + R() * 0.25 }); return a; })();
function drawMotes(ctx, t, M) {
  const g = shaftGeom(M);
  const col = M ? '255,232,180' : '255,250,235';
  for (const m of MOTES) {
    const v = (m.v + t * m.sp) % 1;
    const u = clamp(m.u + 0.04 * Math.sin(t * m.f + m.ph) + 0.02 * Math.sin(t * m.f * 2.3 + m.ph * 1.7), 0, 1);
    const env = Math.sin(v * Math.PI) * smooth(0, 0.15, u) * smooth(1, 0.85, u);
    if (env < 0.03) continue;
    const top = [lerp(WIN.x0, WIN.x1, u), lerp(WIN.y0 + 60, WIN.y1, 0.5)];
    const bot = [lerp(g.near[0][0], g.near[1][0], u), g.near[0][1]];
    const x = lerp(top[0], bot[0], v * 0.85) + 6 * Math.sin(t * 0.3 + m.ph);
    const y = lerp(top[1], bot[1], v * 0.85) + 8 * Math.sin(t * 0.21 + m.ph * 2);
    const a = env * m.w * (0.55 + 0.45 * Math.sin(t * 0.7 + m.ph * 3));
    ctx.fillStyle = `rgba(${col},${(a * 0.55).toFixed(3)})`; ctx.beginPath(); ctx.arc(x, y, m.r * 1.8, 0, 7); ctx.fill();
    ctx.fillStyle = `rgba(${col},${(a * 0.9).toFixed(3)})`; ctx.beginPath(); ctx.arc(x, y, m.r * 0.8, 0, 7); ctx.fill();
  }
}

// ---------------------------------------------------------------- memory: table + stool
const TABLE = { bx0: 330, bx1: 990, back: 1345, fx0: 296, fx1: 1024, front: 1405, apron: 1452, floorF: 1840, floorB: 1650 };
const STOOL = { x: 420, y: 1560 };
function memStool(ctx) {
  const { x, y } = STOOL, w = 78, ry = 13, legB = 1690;
  contact(ctx, x + 10, legB - 2, 110, 16, 0.5);
  const wood = '#b77f4e';
  // legs (splayed)
  for (const [dx, k, c] of [[-50, -1, -0.15], [46, 1, -0.2], [-34, -1, 0], [30, 1, -0.05]]) {
    ctx.fillStyle = lin(ctx, x + dx - 8, 0, x + dx + 8, 0, [[0, shade(wood, c - 0.12)], [0.5, shade(wood, c + 0.05)], [1, shade(wood, c - 0.2)]]);
    poly(ctx, [[x + dx - 7, y + 6], [x + dx + 7, y + 6], [x + dx + 7 + k * 14, legB], [x + dx - 7 + k * 14, legB]]); ctx.fill();
  }
  ctx.fillStyle = shade(wood, -0.15); poly(ctx, [[x - 52, y + 70], [x + 52, y + 70], [x + 54, y + 80], [x - 54, y + 80]]); ctx.fill();
  // seat: top ellipse + edge
  ctx.fillStyle = shade(wood, -0.2); ctx.beginPath(); ctx.ellipse(x, y + 8, w, ry, 0, 0, 7); ctx.fill();
  ctx.fillStyle = lin(ctx, x - w, y, x + w, y, [[0, shade(wood, -0.05)], [0.4, shade(wood, 0.18)], [1, shade(wood, -0.1)]]);
  ctx.beginPath(); ctx.ellipse(x, y, w, ry, 0, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(90,55,25,0.3)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(x, y, w * 0.6, ry * 0.5, 0, 0, 7); ctx.stroke();
}
function memTableBack(ctx) {
  const wood = '#9a6a42';
  for (const x of [TABLE.bx0 + 28, TABLE.bx1 - 28]) {
    ctx.fillStyle = lin(ctx, x - 14, 0, x + 14, 0, [[0, shade(wood, -0.3)], [0.5, shade(wood, -0.12)], [1, shade(wood, -0.35)]]);
    ctx.fillRect(x - 13, TABLE.apron - 10, 26, TABLE.floorB - TABLE.apron + 10);
    contact(ctx, x + 6, TABLE.floorB, 34, 8, 0.4);
  }
}
function memTableFront(ctx, R) {
  const T = TABLE, wood = '#a8754a', top = '#c48f5e';
  // shadow cast on the floor under the table
  blurred(ctx, 34, () => { ctx.fillStyle = 'rgba(70,35,15,0.38)'; poly(ctx, [[T.fx0 + 30, T.floorB - 150], [T.fx1 + 10, T.floorB - 150], [T.fx1 + 60, T.floorB + 20], [T.fx0 + 60, T.floorB + 20]]); ctx.fill(); });
  // front legs (turned)
  for (const x of [T.fx0 + 34, T.fx1 - 34]) {
    contact(ctx, x + 10, T.floorF, 48, 12, 0.5);
    ctx.fillStyle = lin(ctx, x - 22, 0, x + 22, 0, [[0, shade(wood, -0.25)], [0.35, shade(wood, 0.12)], [1, shade(wood, -0.3)]]);
    ctx.beginPath(); ctx.moveTo(x - 20, T.apron); ctx.lineTo(x + 20, T.apron); ctx.lineTo(x + 20, T.apron + 70);
    ctx.quadraticCurveTo(x + 30, T.apron + 90, x + 18, T.apron + 110); ctx.lineTo(x + 13, T.floorF - 8); ctx.lineTo(x - 13, T.floorF - 8); ctx.lineTo(x - 18, T.apron + 110);
    ctx.quadraticCurveTo(x - 30, T.apron + 90, x - 20, T.apron + 70); ctx.closePath(); ctx.fill();
    ctx.fillStyle = shade(wood, -0.35); rr(ctx, x - 15, T.floorF - 12, 30, 12, 3); ctx.fill();
  }
  // apron
  ctx.fillStyle = lin(ctx, 0, T.front, 0, T.apron, [[0, shade(wood, -0.05)], [1, shade(wood, -0.3)]]);
  ctx.fillRect(T.fx0 + 8, T.front, T.fx1 - T.fx0 - 16, T.apron - T.front);
  ctx.fillStyle = 'rgba(60,30,10,0.25)'; ctx.fillRect(T.fx0 + 8, T.apron - 4, T.fx1 - T.fx0 - 16, 4);
  // table top edge
  ctx.fillStyle = lin(ctx, 0, T.front - 2, 0, T.front + 18, [[0, shade(top, 0.15)], [1, shade(wood, -0.15)]]);
  rr(ctx, T.fx0 - 6, T.front - 4, T.fx1 - T.fx0 + 12, 22, 6); ctx.fill();
  // top surface (trapezoid)
  ctx.fillStyle = lin(ctx, 0, T.back, 0, T.front, [[0, shade(top, -0.1)], [1, shade(top, 0.06)]]);
  poly(ctx, [[T.bx0, T.back], [T.bx1, T.back], [T.fx1, T.front], [T.fx0, T.front]]); ctx.fill();
  ctx.save(); poly(ctx, [[T.bx0, T.back], [T.bx1, T.back], [T.fx1, T.front], [T.fx0, T.front]]); ctx.clip();
  for (let i = 0; i < 9; i++) { const y = lerp(T.back, T.front, i / 9); ctx.fillStyle = 'rgba(110,60,25,0.12)'; ctx.fillRect(T.fx0, y, T.fx1 - T.fx0, 1.2); }
  for (let i = 0; i < 30; i++) { ctx.strokeStyle = `rgba(120,70,30,${0.08 + R() * 0.08})`; ctx.lineWidth = 1; const y = lerp(T.back, T.front, R()), x = lerp(T.fx0, T.fx1, R()); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 40 + R() * 90, y + (R() - 0.5)); ctx.stroke(); }
  // golden sunlight across the top
  ctx.fillStyle = lin(ctx, T.fx0, 0, T.fx1, 0, [[0, 'rgba(255,215,140,0.35)'], [0.6, 'rgba(255,215,140,0.12)'], [1, 'rgba(255,215,140,0)']]); ctx.fillRect(T.fx0, T.back, T.fx1 - T.fx0, T.front - T.back);
  // flour: a soft dusting around the board, finger trails
  blurred(ctx, 6, () => {
    ctx.fillStyle = 'rgba(255,252,244,0.55)'; ctx.beginPath(); ctx.ellipse(610, 1380, 220, 22, 0, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,252,244,0.4)'; ctx.beginPath(); ctx.ellipse(430, 1388, 90, 12, 0.05, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(800, 1370, 80, 10, 0, 0, 7); ctx.fill();
  });
  for (let i = 0; i < 260; i++) { const x = 610 + (R() - 0.5) * 520 * R(), y = 1380 + (R() - 0.5) * 50 * R(); ctx.fillStyle = `rgba(255,253,246,${0.25 + R() * 0.5})`; ctx.fillRect(x, y, 1.5 + R() * 2, 1.2); }
  ctx.restore();
  // floured wooden board
  const bd = [[512, 1366], [728, 1366], [742, 1400], [498, 1400]];
  blurred(ctx, 3, () => { ctx.fillStyle = 'rgba(80,40,15,0.35)'; poly(ctx, [[500, 1400], [744, 1400], [740, 1408], [504, 1408]]); ctx.fill(); });
  ctx.fillStyle = shade('#d9a86f', -0.1); poly(ctx, [[498, 1400], [742, 1400], [742, 1408], [498, 1408]]); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 1366, 0, 1400, [[0, '#cf9d64'], [1, '#e2b57e']]); poly(ctx, bd); ctx.fill();
  ctx.save(); poly(ctx, bd); ctx.clip();
  blurred(ctx, 4, () => { ctx.fillStyle = 'rgba(255,253,246,0.6)'; ctx.beginPath(); ctx.ellipse(620, 1386, 100, 12, 0, 0, 7); ctx.fill(); });
  for (let i = 0; i < 120; i++) { ctx.fillStyle = `rgba(255,253,246,${0.3 + R() * 0.5})`; ctx.fillRect(lerp(500, 740, R()), lerp(1366, 1400, R()), 2, 1.2); }
  ctx.restore();
  // dough ball (resting on the board, contact at y≈1395)
  const dx = 620, dy = 1395;
  contact(ctx, dx + 6, dy, 62, 8, 0.45);
  ctx.fillStyle = rad(ctx, dx - 16, dy - 40, 4, 72, [[0, '#fff5e2'], [0.5, '#f1dcb6'], [1, '#d4b182']]);
  ctx.beginPath(); ctx.moveTo(dx - 56, dy); ctx.bezierCurveTo(dx - 60, dy - 52, dx + 58, dy - 56, dx + 54, dy); ctx.quadraticCurveTo(dx, dy + 6, dx - 56, dy); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,250,0.55)'; ctx.beginPath(); ctx.ellipse(dx - 14, dy - 32, 20, 8, -0.3, 0, 7); ctx.fill();
  ctx.strokeStyle = 'rgba(190,150,100,0.35)'; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(dx + 10, dy - 30); ctx.quadraticCurveTo(dx + 26, dy - 22, dx + 30, dy - 8); ctx.stroke();
  // rolling pin (lying left of the board)
  const ry0 = 1384;
  contact(ctx, 420, ry0 + 10, 80, 6, 0.4);
  ctx.save(); ctx.translate(420, ry0); ctx.rotate(-0.08);
  ctx.fillStyle = lin(ctx, 0, -14, 0, 14, [[0, '#e6c08e'], [0.4, '#f3d6a8'], [1, '#a77a4a']]); rr(ctx, -66, -14, 132, 28, 13); ctx.fill();
  for (const s of [-1, 1]) { ctx.fillStyle = lin(ctx, 0, -7, 0, 7, [[0, '#d4a26a'], [1, '#8a5e33']]); rr(ctx, s > 0 ? 66 : -100, -7, 34, 14, 7); ctx.fill(); }
  ctx.fillStyle = 'rgba(255,252,244,0.5)'; ctx.fillRect(-50, -10, 70, 4);
  ctx.restore();
  // mixing bowl (cream, with a sage band) at the right of the table
  const bx = 880, by = 1392;
  contact(ctx, bx + 12, by, 100, 10, 0.5);
  ctx.fillStyle = lin(ctx, bx - 86, 0, bx + 86, 0, [[0, '#cbb895'], [0.35, '#fbf3e1'], [1, '#b39e7b']]);
  ctx.beginPath(); ctx.moveTo(bx - 86, by - 74); ctx.bezierCurveTo(bx - 84, by - 10, bx - 40, by, bx, by); ctx.bezierCurveTo(bx + 40, by, bx + 84, by - 10, bx + 86, by - 74); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(122,150,120,0.85)'; ctx.fillRect(bx - 84, by - 58, 168, 10);
  ctx.fillStyle = lin(ctx, 0, by - 84, 0, by - 64, [[0, '#a58c64'], [1, '#e9dcc0']]); ctx.beginPath(); ctx.ellipse(bx, by - 74, 86, 12, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#efe0bd'; ctx.beginPath(); ctx.ellipse(bx, by - 72, 70, 7, 0, 0, 7); ctx.fill(); // flour inside
  ctx.fillStyle = '#c9a77a'; ctx.save(); ctx.translate(bx + 30, by - 92); ctx.rotate(0.5); rr(ctx, -4, -40, 8, 60, 4); ctx.fill(); ctx.restore(); // wooden spoon
  // a little pile of flour + an egg shell
  ctx.fillStyle = rad(ctx, 760, 1388, 2, 34, [[0, 'rgba(255,253,246,0.95)'], [1, 'rgba(255,253,246,0)']]); ctx.beginPath(); ctx.ellipse(760, 1388, 34, 10, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#f4ead8'; ctx.beginPath(); ctx.ellipse(350, 1372, 12, 8, 0.4, Math.PI, 2 * Math.PI); ctx.fill();
}

// ---------------------------------------------------------------- kitchen builder
function buildKitchen(M) {
  const R = mulberry32(M ? 777 : 333), P = kPal(M);
  const c = newCache(KC.x0, KC.y0, KC.x1, KC.y1), x = c.ctx;
  kWall(x, R, P, M);
  kWindow(x, R, P, M);
  kClock(x, M);
  if (!M) clockHands(x, 4 + 47 / 60, 47, 22); // stopped
  kCalendar(x, R, M);
  kUppers(x, R, P, M);
  kBacksplash(x, R, P);
  kCounterAndBase(x, R, P, M);
  kStove(x, R, P, M);
  // counter top props (the tin itself is drawn per frame)
  const cb = COUNTER.front - 8;
  if (!M) {
    openBox(x, R, 612, 772, cb + 2, 120, 'KITCHEN');
    canister(x, 818, cb - 18, 52, 74, '#e7ded0', 'FLOUR');
    canister(x, 872, cb - 18, 44, 60, '#e7ded0', 'SUGAR');
    // a roll of packing tape and a stack of folded newspaper
    x.fillStyle = 'rgba(220,214,200,0.95)'; poly(x, [[1162, cb - 6], [1252, cb - 8], [1258, cb + 2], [1166, cb + 4]]); x.fill();
    x.fillStyle = 'rgba(150,140,130,0.5)'; for (let i = 0; i < 4; i++) x.fillRect(1172, cb - 4 + i * 2.2, 70, 0.8);
    x.fillStyle = lin(x, 1194, 0, 1236, 0, [[0, '#b39a66'], [0.4, '#e3cf9a'], [1, '#9b8150']]); x.beginPath(); x.ellipse(1215, cb - 14, 22, 8, 0, 0, 7); x.fill();
    x.fillStyle = '#6d5a3c'; x.beginPath(); x.ellipse(1215, cb - 16, 9, 3.5, 0, 0, 7); x.fill();
  } else {
    canister(x, 680, cb - 18, 62, 92, '#f4ecdc', 'FLOUR');
    canister(x, 750, cb - 18, 54, 78, '#f4ecdc', 'SUGAR');
    canister(x, 812, cb - 18, 46, 64, '#f4ecdc', 'TEA');
    // a bread loaf cooling on a rack near the stove
    x.fillStyle = '#8c8f8b'; x.fillRect(1120, cb - 10, 140, 4);
    x.fillStyle = rad(x, 1180, cb - 60, 6, 80, [[0, '#e9b071'], [0.6, '#c27e45'], [1, '#8e5428']]);
    x.beginPath(); x.moveTo(1126, cb - 10); x.bezierCurveTo(1120, cb - 80, 1256, cb - 80, 1252, cb - 10); x.closePath(); x.fill();
    x.strokeStyle = 'rgba(255,220,170,0.6)'; x.lineWidth = 2; for (const sx of [1160, 1190, 1220]) { x.beginPath(); x.moveTo(sx - 8, cb - 52); x.lineTo(sx + 8, cb - 40); x.stroke(); }
  }
  kFloor(x, R, P, M);
  kSunlight(x, M);
  if (!M) {
    dustSheetChair(x, R);
    box(x, R, 10, 200, 1660, 150, 'NANA · DISHES', { fs: 17, rot: -0.03 });
    box(x, R, 26, 186, 1510, 120, 'BOOKS', { fs: 20, rot: 0.03 });
    openBox(x, R, 205, 350, 1720, 130, 'KITCHEN');
  } else {
    memTableBack(x);
    memStool(x);
  }
  // room interior a touch dimmer than the sunlit window zone, so the beams read
  overlay(c, 'multiply', (g) => {
    g.fillStyle = rad(g, 300, 900, 250, 1700, M ? [[0, 'rgba(255,255,255,0)'], [1, 'rgba(215,192,170,1)']] : [[0, 'rgba(255,255,255,0)'], [0.5, 'rgba(225,228,226,1)'], [1, 'rgba(196,204,204,1)']]);
    g.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, KC.y1 - KC.y0);
  });
  kShafts(x, M);
  grain(c, [KC.x0, KC.y0, KC.x1 - KC.x0, FLOOR_Y - KC.y0], 6, 0.03, M ? 21 : 11);
  grain(c, [KC.x0, FLOOR_Y, KC.x1 - KC.x0, KC.y1 - FLOOR_Y], 7, 0.05, M ? 22 : 12, 0.5);
  let front = null;
  if (M) {
    // golden late-afternoon grade + soft vignette, baked into the paint
    overlay(c, 'multiply', (g) => { g.fillStyle = 'rgba(255,214,160,0.55)'; g.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, KC.y1 - KC.y0); });
    overlay(c, 'screen', (g) => { softGlow(g, 260, 760, 900, '#ffcf8a', 0.22, 1); });
    const vig = (g) => { g.fillStyle = rad(g, 600, 1150, 420, 1500, [[0, 'rgba(90,45,20,0)'], [0.6, 'rgba(90,45,20,0.18)'], [1, 'rgba(70,30,12,0.55)']]); g.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, KC.y1 - KC.y0); };
    overlay(c, 'source-over', vig);
    const f = newCache(200, 1280, 1140, 1900); const fx = f.ctx;
    memTableFront(fx, mulberry32(909));
    overlay(f, 'source-atop', (g) => { g.fillStyle = 'rgba(255,214,160,0.18)'; g.fillRect(200, 1280, 940, 620); });
    overlay(f, 'source-atop', (g) => { g.globalCompositeOperation = 'source-atop'; vig(g); });
    front = pair(f);
  } else {
    // morning: cool fresh fill on the right, gentle
    overlay(c, 'soft-light', (g) => { g.fillStyle = lin(g, KC.x0, 0, KC.x1, 0, [[0, 'rgba(255,240,210,0.35)'], [0.5, 'rgba(255,255,255,0)'], [1, 'rgba(150,175,175,0.3)']]); g.fillRect(KC.x0, KC.y0, KC.x1 - KC.x0, KC.y1 - KC.y0); });
  }
  const tin = {
    body: spriteOf(-100, -130, 110, 30, (g) => tinPaint(g, M, 'body')),
    mouth: spriteOf(-100, -160, 110, -70, (g) => tinPaint(g, M, 'mouth')),
    lid: spriteOf(-100, -60, 110, 30, (g) => tinPaint(g, M, 'lid')),
  };
  if (M) for (const k of ['body', 'lid']) overlay(tin[k], 'source-atop', (g) => { g.fillStyle = 'rgba(255,200,130,0.22)'; g.fillRect(-100, -160, 210, 200); });
  return { room: pair(c), front, tin };
}

let KCACHE = null, MCACHE = null;
function drawTin(ctx, C, open) {
  const p = clamp(open || 0, 0, 1);
  const { x, y } = TIN;
  // lid path: lift straight up, then arc over and settle on the counter to the right (resting at counter depth)
  let lx, ly, rot = 0;
  if (p <= 0.45) { const e = ease(p / 0.45); lx = 0; ly = -TIN.h + 2 - 70 * e; rot = -0.06 * e; }
  else { const e = ease((p - 0.45) / 0.55); lx = 158 * e; ly = lerp(-TIN.h - 68, -6, e) - 46 * Math.sin(e * Math.PI) * (1 - e); rot = -0.06 * (1 - e); }
  const lidOnCounter = p > 0.98;
  if (p > 0.45 && lidOnCounter) { ctx.save(); ctx.translate(x + lx, y + ly); drawSprite(ctx, C.tin.lid, 0, 0); ctx.restore(); }
  drawSprite(ctx, C.tin.body, x, y);
  if (p > 0.01) drawSprite(ctx, C.tin.mouth, x, y);
  if (!lidOnCounter) {
    if (p > 0.45) contact(ctx, x + lx + 6, y - 6, 70 * smooth(0.6, 1, p), 8, 0.35 * smooth(0.6, 1, p));
    ctx.save(); ctx.translate(x + lx, y + ly); ctx.rotate(rot); drawSprite(ctx, C.tin.lid, 0, 0); ctx.restore();
  }
}

const kitchen = {
  ENV: {
    name: 'nanaKitchen',
    extents: { ...KEXT },
    options: { tinOpen: 0 },
    anchors: {
      eliCounter: { x: 1050, y: 1600 },
      mayaBeside: { x: 700, y: 1610 },
      tin: { x: 1000, y: 1120 },
      window: { x: 280, y: 700 },
      clock: { x: CLOCK.x, y: CLOCK.y },
      counterTop: { x: 1100, y: 1120 },
      stove: { x: 1410, y: 1120 },
      boxes: { x: 175, y: 1690 },
    },
  },
  drawBack(ctx, t, o = {}) {
    if (!KCACHE) KCACHE = buildKitchen(false);
    ctx.fillStyle = '#b9c9bc'; ctx.fillRect(KC.x0 - 3000, KC.y0 - 3000, 8000, 9000);
    blit(ctx, KCACHE.room);
    drawTin(ctx, KCACHE, o.tinOpen ?? 0);
    drawMotes(ctx, t, false);
  },
  drawFront() { /* characters stand in front of the counter: nothing in front */ },
  lightAt(x, y, t, o = {}) {
    // morning sun from the window on the left (+ bright shaft haze) and a soft cool fill
    const px = x, py = y - 300;
    const win = { x: 280, y: 640 };
    const d = Math.hypot(px - win.x, py - win.y);
    const near = 1 / (1 + Math.pow(d / 900, 2));
    return {
      keyDir: Math.atan2(win.y - py, win.x - px),
      keyColor: '#fff0d6', keyAmt: clamp(0.5 + 0.35 * near, 0.5, 0.85),
      rimDir: Math.atan2(win.y - 120 - py, win.x - 200 - px), rimColor: '#fff6e2', rimAmt: clamp(0.3 + 0.3 * near, 0.3, 0.55),
      shadowColor: '#4c5560', shadowAmt: 0.26,
      ambient: '#eef2e8', ambientAmt: 0.08,
    };
  },
};

const memory = {
  ENV: {
    name: 'memory',
    extents: { ...KEXT },
    options: {},
    anchors: {
      nanaAtTable: { x: 700, y: 1600 },
      kidStool: { x: STOOL.x, y: STOOL.y },
      kidStand: { x: 430, y: 1600 },
      dough: { x: 620, y: 1395 },
      tableTop: { x: 650, y: 1390 },
      window: { x: 280, y: 700 },
      tin: { x: 1000, y: 1120 },
    },
  },
  drawBack(ctx, t, o = {}) {
    if (!MCACHE) MCACHE = buildKitchen(true);
    ctx.fillStyle = '#7a5a3c'; ctx.fillRect(KC.x0 - 3000, KC.y0 - 3000, 8000, 9000);
    blit(ctx, MCACHE.room);
    drawTin(ctx, MCACHE, 0);
    // the clock still runs in the memory: ~4:52 pm, ticking
    const s0 = 16 * 3600 + 52 * 60 + 10 + t, sec = Math.floor(s0), fr = s0 - sec;
    const ss = (sec % 60) + smooth(0, 0.12, fr);
    clockHands(ctx, (s0 / 3600) % 12, (s0 / 60) % 60, ss);
    drawMotes(ctx, t, true);
  },
  drawFront(ctx, t, o = {}) {
    if (!MCACHE) MCACHE = buildKitchen(true);
    blit(ctx, MCACHE.front);
  },
  lightAt(x, y, t, o = {}) {
    const px = x, py = y - 300;
    const win = { x: 260, y: 720 };
    const d = Math.hypot(px - win.x, py - win.y), near = 1 / (1 + Math.pow(d / 800, 2));
    return {
      keyDir: Math.atan2(win.y - py, win.x - px),
      keyColor: '#ffd79a', keyAmt: clamp(0.55 + 0.3 * near, 0.55, 0.85),
      rimDir: Math.atan2(win.y - 150 - py, win.x - 150 - px), rimColor: '#ffcf80', rimAmt: clamp(0.35 + 0.3 * near, 0.35, 0.6),
      shadowColor: '#6a4038', shadowAmt: 0.24,
      ambient: '#ffe6c2', ambientAmt: 0.14,
    };
  },
};

// ================================================================ HOSPITAL (night)
const HEXT = { x0: -300, y0: -300, x1: 1400, y1: 2400 };
const HM = 260;
const HC = { x0: HEXT.x0 - HM, y0: HEXT.y0 - HM, x1: HEXT.x1 + HM, y1: HEXT.y1 + HM };
const H_FLOOR = 1480;
const HWIN = { x0: 500, y0: 130, x1: 1000, y1: 700 };
const LAMPP = { x: -160, y: 1010 };
const CANDLE = { x: 1205, y: 1046 };
const MON = { x0: -236, y0: 432, x1: 6, y1: 604 };
const HCOL = { wall: '#5a6678', wallLo: '#4d586a', floor: '#6c7684', blanket: '#bcc5d3' };

function hWall(ctx, R) {
  ctx.fillStyle = HCOL.wall; ctx.fillRect(HC.x0, HC.y0, HC.x1 - HC.x0, H_FLOOR - HC.y0);
  for (let i = 0; i < 60; i++) softGlow(ctx, lerp(HC.x0, HC.x1, R()), lerp(-300, 1450, R()), 140 + R() * 240, R() < 0.5 ? '#66738a' : '#4d586a', 0.2);
  // lower wall + bumper rail
  ctx.fillStyle = HCOL.wallLo; ctx.fillRect(HC.x0, 1040, HC.x1 - HC.x0, H_FLOOR - 1040);
  ctx.fillStyle = lin(ctx, 0, 1010, 0, 1042, [[0, '#7e899a'], [0.4, '#6c788a'], [1, '#465061']]); ctx.fillRect(HC.x0, 1012, HC.x1 - HC.x0, 30);
  ctx.fillStyle = 'rgba(20,25,35,0.25)'; ctx.fillRect(HC.x0, 1042, HC.x1 - HC.x0, 6);
  // ceiling darkness
  ctx.fillStyle = lin(ctx, 0, HC.y0, 0, 500, [[0, 'rgba(15,18,30,0.65)'], [1, 'rgba(15,18,30,0)']]); ctx.fillRect(HC.x0, HC.y0, HC.x1 - HC.x0, 500 - HC.y0);
  // headwall panel behind the bed head (dim)
  ctx.fillStyle = '#626e80'; rr(ctx, -140, 790, 560, 92, 10); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(-136, 794, 552, 4);
  for (const ox of [-80, -20, 60, 140, 300, 360]) { ctx.fillStyle = '#4f596a'; rr(ctx, ox, 818, 34, 38, 6); ctx.fill(); ctx.fillStyle = '#7e8a9c'; ctx.beginPath(); ctx.arc(ox + 17, 837, 7, 0, 7); ctx.fill(); }
  ctx.fillStyle = 'rgba(120,200,150,0.5)'; ctx.beginPath(); ctx.arc(240, 836, 3, 0, 7); ctx.fill();
  // privacy curtain on a ceiling track (far right)
  ctx.fillStyle = '#3f4858'; ctx.fillRect(1300, -300, 600, 8);
  ctx.fillStyle = lin(ctx, 1330, 0, 1700, 0, [[0, '#8794a6'], [1, '#6d7a8c']]);
  ctx.beginPath(); ctx.moveTo(1336, -292); ctx.lineTo(1700, -292); ctx.lineTo(1700, 1420); for (let x = 1700; x > 1340; x -= 30) ctx.quadraticCurveTo(x - 15, 1432, x - 30, 1420); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.clip();
  for (let x = 1340; x < 1700; x += 44) { ctx.fillStyle = lin(ctx, x, 0, x + 44, 0, [[0, 'rgba(20,25,40,0.3)'], [0.5, 'rgba(200,215,240,0.12)'], [1, 'rgba(20,25,40,0.28)']]); ctx.fillRect(x, -300, 44, 1750); }
  ctx.fillStyle = lin(ctx, 1330, 0, 1420, 0, [[0, 'rgba(10,12,20,0.35)'], [1, 'rgba(10,12,20,0)']]); ctx.fillRect(1330, -300, 100, 1750);
  ctx.restore();
}

function hWindow(ctx, R) {
  const { x0, y0, x1, y1 } = HWIN;
  // night outside: deep blue, moon glow, a few far lights
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip();
  ctx.fillStyle = lin(ctx, 0, y0, 0, y1, [[0, '#1d2846'], [1, '#33456a']]); ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  softGlow(ctx, 860, 250, 260, '#c8d8f4', 0.6);
  ctx.fillStyle = '#eef3fb'; ctx.beginPath(); ctx.arc(860, 250, 26, 0, 7); ctx.fill();
  ctx.fillStyle = '#1a2238'; for (let i = 0; i < 9; i++) { const bx = x0 + i * 60 + R() * 20, bh = 60 + R() * 120; ctx.fillRect(bx, y1 - bh, 50 + R() * 30, bh); }
  for (let i = 0; i < 18; i++) { ctx.fillStyle = `rgba(255,214,150,${0.3 + R() * 0.4})`; ctx.fillRect(x0 + R() * (x1 - x0), y1 - R() * 140, 4, 5); }
  // blinds: tilted slats with thin gaps of moonlight
  for (let y = y0 + 4; y < y1; y += 26) {
    ctx.fillStyle = lin(ctx, 0, y, 0, y + 20, [[0, '#8e9bb2'], [0.5, '#a7b4ca'], [1, '#6a778e']]); ctx.fillRect(x0, y, x1 - x0, 20);
    ctx.fillStyle = 'rgba(210,225,250,0.35)'; ctx.fillRect(x0, y + 20, x1 - x0, 2);
  }
  ctx.fillStyle = 'rgba(205,220,250,0.18)'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  softGlow(ctx, 860, 250, 300, '#dbe6fa', 0.25);
  ctx.restore();
  // blind cords
  ctx.strokeStyle = 'rgba(200,210,225,0.5)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x0 + 30, y0); ctx.lineTo(x0 + 30, y1 + 120); ctx.stroke();
  ctx.fillStyle = '#c2cad8'; rr(ctx, x0 + 25, y1 + 112, 10, 18, 4); ctx.fill();
  // frame + headrail + sill
  ctx.fillStyle = '#8a96a8'; ctx.beginPath(); ctx.rect(x0 - 22, y0 - 22, x1 - x0 + 44, y1 - y0 + 44); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.fill('evenodd');
  ctx.fillStyle = lin(ctx, 0, y0 - 6, 0, y0 + 14, [[0, '#a9b4c6'], [1, '#6e7a8e']]); ctx.fillRect(x0 - 4, y0 - 4, x1 - x0 + 8, 18);
  ctx.fillStyle = lin(ctx, 0, y1 + 20, 0, y1 + 40, [[0, '#a0acbf'], [1, '#6a768a']]); rr(ctx, x0 - 34, y1 + 18, x1 - x0 + 68, 20, 3); ctx.fill();
  blurred(ctx, 8, () => { ctx.fillStyle = 'rgba(10,14,25,0.4)'; ctx.fillRect(x0 - 30, y1 + 38, x1 - x0 + 60, 12); });
  // cool glow spilling from the window onto the wall
  ctx.save(); ctx.globalCompositeOperation = 'screen'; softGlow(ctx, (x0 + x1) / 2, (y0 + y1) / 2, 560, '#7d93c0', 0.35, 1.1); ctx.restore();
}
function moonStripes(ctx, alpha) {
  // soft parallelogram stripes of moonlight from the blinds, falling down-left onto wall, bed and floor
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  blurred(ctx, 7, () => {
    for (let i = 0; i < 9; i++) {
      const yW = 760 + i * 30; // on the lower wall under the window
      ctx.fillStyle = `rgba(160,185,230,${alpha * (1 - i * 0.06)})`;
      poly(ctx, [[560, yW], [1040, yW], [1020, yW + 13], [540, yW + 13]]); ctx.fill();
    }
  });
  ctx.restore();
}

function hBedsideLeft(ctx) {
  // small cabinet + lamp (warm key)
  const x0 = -300, x1 = -30, top = 1172;
  contact(ctx, (x0 + x1) / 2 + 10, H_FLOOR + 30, 170, 18, 0.5);
  ctx.fillStyle = lin(ctx, 0, top, 0, H_FLOOR + 30, [[0, '#8a7462'], [1, '#5a4a40']]); ctx.fillRect(x0, top + 16, x1 - x0, H_FLOOR + 30 - top - 16);
  ctx.fillStyle = '#a58a72'; poly(ctx, [[x0 + 8, top - 6], [x1 - 6, top - 6], [x1, top + 16], [x0, top + 16]]); ctx.fill();
  ctx.strokeStyle = 'rgba(30,20,15,0.35)'; ctx.lineWidth = 2; ctx.strokeRect(x0 + 18, top + 40, x1 - x0 - 36, 90); ctx.strokeRect(x0 + 18, top + 150, x1 - x0 - 36, 160);
  ctx.fillStyle = '#c9b089'; rr(ctx, (x0 + x1) / 2 - 20, top + 80, 40, 7, 3); ctx.fill();
  // lamp
  const lx = LAMPP.x;
  contact(ctx, lx + 6, top + 2, 60, 8, 0.5);
  ctx.fillStyle = lin(ctx, lx - 40, 0, lx + 40, 0, [[0, '#8c6d55'], [0.4, '#d9b48e'], [1, '#6c5040']]);
  ctx.beginPath(); ctx.moveTo(lx - 34, top); ctx.bezierCurveTo(lx - 50, top - 70, lx - 14, top - 90, lx - 8, top - 110); ctx.lineTo(lx + 8, top - 110); ctx.bezierCurveTo(lx + 14, top - 90, lx + 50, top - 70, lx + 34, top); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#b8a07e'; ctx.fillRect(lx - 3, top - 140, 6, 34);
  // shade (glowing)
  const sT = 930, sB = 1034;
  ctx.fillStyle = lin(ctx, lx - 90, 0, lx + 90, 0, [[0, '#e9b97c'], [0.45, '#ffe6bd'], [1, '#d9a465']]);
  poly(ctx, [[lx - 58, sT], [lx + 58, sT], [lx + 90, sB], [lx - 90, sB]]); ctx.fill();
  ctx.fillStyle = 'rgba(255,248,225,0.7)'; ctx.beginPath(); ctx.ellipse(lx, sB, 90, 9, 0, 0, Math.PI); ctx.fill();
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  softGlow(ctx, lx, sB + 20, 260, '#ffcf8a', 0.55, 0.6); // light pool down onto the table
  softGlow(ctx, lx, 980, 900, '#ffb565', 0.32, 1);        // warm spill across the wall
  softGlow(ctx, lx, sT - 10, 200, '#ffd9a0', 0.35, 0.5);   // up-light from the shade top
  ctx.restore();
}

function hMonitor(ctx) {
  const { x0, y0, x1, y1 } = MON;
  // wall arm
  ctx.fillStyle = '#4a5464'; ctx.fillRect(x1 - 10, (y0 + y1) / 2 - 8, 60, 16); ctx.fillStyle = '#3c4553'; rr(ctx, x1 + 44, (y0 + y1) / 2 - 30, 18, 60, 4); ctx.fill();
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(10,12,20,0.45)'; rr(ctx, x0 + 10, y0 + 14, x1 - x0, y1 - y0, 12); ctx.fill(); });
  ctx.fillStyle = lin(ctx, 0, y0, 0, y1, [[0, '#5c6676'], [1, '#3a4250']]); rr(ctx, x0, y0, x1 - x0, y1 - y0, 12); ctx.fill();
  ctx.fillStyle = '#0d1514'; rr(ctx, x0 + 14, y0 + 14, x1 - x0 - 28, y1 - y0 - 40, 6); ctx.fill();
  ctx.fillStyle = 'rgba(120,230,170,0.08)'; rr(ctx, x0 + 14, y0 + 14, x1 - x0 - 28, y1 - y0 - 40, 6); ctx.fill();
  for (let i = 0; i < 4; i++) { ctx.fillStyle = '#2a313c'; ctx.beginPath(); ctx.arc(x0 + 30 + i * 22, y1 - 13, 5, 0, 7); ctx.fill(); }
  ctx.fillStyle = 'rgba(120,230,170,0.7)'; ctx.beginPath(); ctx.arc(x1 - 24, y1 - 13, 3, 0, 7); ctx.fill();
  ctx.save(); ctx.globalCompositeOperation = 'screen'; softGlow(ctx, (x0 + x1) / 2, (y0 + y1) / 2, 220, '#5fc79a', 0.12, 0.8); ctx.restore();
}
function monitorTrace(ctx, t) {
  const sx0 = MON.x0 + 22, sx1 = MON.x1 - 70, base = MON.y0 + 92, W = sx1 - sx0;
  const period = 1.15, sweep = 2.6; // sweep seconds across the screen
  const head = ((t / sweep) % 1) * W;
  const ecg = (s) => { // s in seconds along the trace
    const ph = ((s % period) + period) % period / period;
    const g = (c, w, a) => a * Math.exp(-Math.pow((ph - c) / w, 2));
    return g(0.18, 0.03, -6) + g(0.3, 0.012, 26) + g(0.335, 0.012, -10) + g(0.58, 0.05, -8);
  };
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const pts = [];
  for (let i = 0; i <= W; i += 2) {
    const age = ((head - i) / W + 1) % 1; // 0 at the head, grows behind it
    pts.push([sx0 + i, base - ecg((t - age * sweep)), age]);
  }
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i][2]; if (a > 0.92) continue;
    const al = Math.pow(1 - a, 1.6);
    ctx.strokeStyle = `rgba(120,235,170,${(0.85 * al).toFixed(3)})`; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(pts[i - 1][0], pts[i - 1][1]); ctx.lineTo(pts[i][0], pts[i][1]); ctx.stroke();
  }
  // numbers (static, dim)
  ctx.fillStyle = 'rgba(120,235,170,0.75)'; ctx.font = '22px NanaBgSemi'; ctx.textAlign = 'right'; ctx.fillText('62', MON.x1 - 22, MON.y0 + 44);
  ctx.fillStyle = 'rgba(140,200,240,0.6)'; ctx.font = '14px NanaBgSemi'; ctx.fillText('97', MON.x1 - 24, MON.y0 + 70);
  ctx.restore();
}

function hIV(ctx) {
  const x = 170;
  ctx.fillStyle = lin(ctx, x - 4, 0, x + 4, 0, [[0, '#7c8696'], [0.5, '#d4dae4'], [1, '#6a7484']]); ctx.fillRect(x - 3, 250, 7, 1000);
  ctx.strokeStyle = '#b8c0cc'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x - 60, 270); ctx.quadraticCurveTo(x, 250, x + 60, 270); ctx.stroke();
  // bag
  const bx = x - 60, by = 278;
  ctx.fillStyle = 'rgba(220,232,245,0.45)'; ctx.beginPath(); ctx.moveTo(bx - 34, by + 10); ctx.quadraticCurveTo(bx - 40, by + 140, bx, by + 170); ctx.quadraticCurveTo(bx + 40, by + 140, bx + 34, by + 10); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(200,220,240,0.35)'; ctx.beginPath(); ctx.moveTo(bx - 36, by + 70); ctx.quadraticCurveTo(bx - 38, by + 140, bx, by + 166); ctx.quadraticCurveTo(bx + 38, by + 140, bx + 36, by + 70); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(240,248,255,0.55)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(bx - 26, by + 30); ctx.lineTo(bx - 28, by + 120); ctx.stroke();
  ctx.fillStyle = '#c9d2de'; ctx.fillRect(bx - 6, by - 6, 12, 18); ctx.fillRect(bx - 4, by + 168, 8, 26);
  ctx.strokeStyle = 'rgba(220,230,240,0.55)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(bx, by + 194); ctx.bezierCurveTo(bx - 10, 700, bx + 160, 820, 250, 1150); ctx.stroke();
}

function hBedsideRight(ctx) {
  // small bedside table behind the bed's foot; top at y≈1046
  const x0 = 1100, x1 = 1300, top = 1046;
  ctx.fillStyle = lin(ctx, 0, top, 0, 1200, [[0, '#6e6a72'], [1, '#4a4652']]); ctx.fillRect(x0 + 4, top + 12, x1 - x0 - 8, 200);
  ctx.fillStyle = '#87808a'; poly(ctx, [[x0 + 12, top - 12], [x1 - 12, top - 12], [x1, top + 12], [x0, top + 12]]); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(x0, top + 10, x1 - x0, 3);
  // water glass
  contact(ctx, 1142, top, 22, 4, 0.4);
  ctx.fillStyle = 'rgba(200,215,235,0.35)'; poly(ctx, [[1126, top - 54], [1158, top - 54], [1155, top], [1129, top]]); ctx.fill();
  ctx.fillStyle = 'rgba(170,195,230,0.35)'; poly(ctx, [[1128, top - 30], [1156, top - 30], [1155, top], [1129, top]]); ctx.fill();
  ctx.strokeStyle = 'rgba(230,240,255,0.55)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.ellipse(1142, top - 54, 16, 3, 0, 0, 7); ctx.stroke();
  // small framed photo, leaning
  contact(ctx, 1262, top, 26, 4, 0.4);
  ctx.save(); ctx.translate(1262, top); ctx.rotate(0.06);
  ctx.fillStyle = '#b39a74'; ctx.fillRect(-24, -66, 48, 66); ctx.fillStyle = '#3e4856'; ctx.fillRect(-18, -60, 36, 54);
  ctx.fillStyle = 'rgba(210,180,150,0.6)'; ctx.beginPath(); ctx.arc(-6, -40, 7, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(8, -36, 5, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(123,59,85,0.6)'; ctx.fillRect(-14, -32, 16, 24); ctx.fillStyle = 'rgba(185,163,214,0.6)'; ctx.fillRect(3, -30, 10, 20);
  ctx.restore();
}
function candleBody(ctx) {
  const { x, y } = CANDLE;
  contact(ctx, x + 3, y, 34, 5, 0.45);
  ctx.fillStyle = lin(ctx, 0, y - 6, 0, y + 4, [[0, '#a7a9b2'], [1, '#6f7380']]); ctx.beginPath(); ctx.ellipse(x, y - 2, 30, 6, 0, 0, 7); ctx.fill(); // saucer
  ctx.fillStyle = lin(ctx, x - 17, 0, x + 17, 0, [[0, '#c9bfae'], [0.4, '#efe6d4'], [1, '#a99f8f']]); ctx.fillRect(x - 17, y - 62, 34, 58);
  ctx.fillStyle = '#e6dccb'; ctx.beginPath(); ctx.ellipse(x, y - 62, 17, 4, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#ddd2bf'; ctx.beginPath(); ctx.ellipse(x - 6, y - 58, 4, 9, 0, 0, 7); ctx.fill(); // wax drip
  ctx.strokeStyle = '#3a302a'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(x, y - 62); ctx.quadraticCurveTo(x + 1, y - 68, x + 2, y - 72); ctx.stroke();
}
function candleFlame(ctx, t, amt) {
  const { x, y } = CANDLE, fy = y - 72;
  const f = 1 + 0.07 * Math.sin(t * 7.1) + 0.05 * Math.sin(t * 11.3 + 1.3) + 0.03 * Math.sin(t * 17.9 + 0.4);
  const sway = 1.6 * Math.sin(t * 2.3) + 0.8 * Math.sin(t * 5.1 + 2);
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  softGlow(ctx, x, fy - 6, 460 * f, '#ffb35c', 0.42 * amt, 0.9);
  softGlow(ctx, x, fy - 6, 150 * f, '#ffd58f', 0.6 * amt, 1);
  softGlow(ctx, x, y + 6, 120, '#ffc070', 0.35 * amt, 0.25); // light on the table top
  ctx.restore();
  ctx.save(); ctx.globalAlpha = amt;
  const h = 26 * f;
  ctx.fillStyle = rad(ctx, x + sway * 0.3, fy - h * 0.35, 1, h * 0.7, [[0, '#fffbe8'], [0.45, '#ffd98a'], [1, 'rgba(255,150,60,0)']]);
  ctx.beginPath(); ctx.moveTo(x - 6, fy); ctx.quadraticCurveTo(x - 9, fy - h * 0.5, x + sway, fy - h); ctx.quadraticCurveTo(x + 9, fy - h * 0.5, x + 6, fy); ctx.quadraticCurveTo(x, fy + 5, x - 6, fy); ctx.fill();
  ctx.fillStyle = 'rgba(120,150,255,0.35)'; ctx.beginPath(); ctx.ellipse(x, fy - 2, 3, 4, 0, 0, 7); ctx.fill();
  ctx.restore();
}

function hBed(ctx, R) {
  // headboard (left), bed frame, blanket top surface y≈1150..1400 over x≈100..1300, front drape, pillow
  const BL = HCOL.blanket;
  // headboard
  ctx.fillStyle = lin(ctx, 30, 0, 110, 0, [[0, '#7d8898'], [0.5, '#a9b3c2'], [1, '#6c7686']]); rr(ctx, 30, 930, 76, 640, 20); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; rr(ctx, 40, 944, 10, 600, 5); ctx.fill();
  // under-bed shadow + frame + wheels
  blurred(ctx, 26, () => { ctx.fillStyle = 'rgba(8,10,20,0.55)'; ctx.fillRect(60, 1540, 1270, 260); });
  ctx.fillStyle = '#4c5566'; ctx.fillRect(110, 1570, 1180, 40);
  ctx.fillStyle = 'rgba(200,210,225,0.18)'; ctx.fillRect(110, 1572, 1180, 3);
  for (const x of [170, 1230]) {
    ctx.fillStyle = '#5a6475'; ctx.fillRect(x - 9, 1606, 18, 150);
    ctx.fillStyle = '#2a2f3a'; ctx.beginPath(); ctx.arc(x, 1770, 20, 0, 7); ctx.fill(); ctx.fillStyle = '#6a7484'; ctx.beginPath(); ctx.arc(x, 1770, 7, 0, 7); ctx.fill();
    contact(ctx, x + 6, 1790, 60, 10, 0.5);
  }
  // footboard (low, at the right end)
  ctx.fillStyle = lin(ctx, 1290, 0, 1350, 0, [[0, '#6c7686'], [0.5, '#98a2b2'], [1, '#5e6878']]); rr(ctx, 1292, 1110, 50, 480, 14); ctx.fill();
  // blanket front drape (hangs from the front edge y≈1400 to a soft hem)
  const hem = (x) => 1572 + 6 * Math.sin(x * 0.021) + 4 * Math.sin(x * 0.057 + 1);
  ctx.beginPath(); ctx.moveTo(94, 1398); ctx.lineTo(1300, 1404);
  for (let x = 1300; x >= 94; x -= 8) ctx.lineTo(x, hem(x));
  ctx.closePath();
  ctx.fillStyle = lin(ctx, 0, 1400, 0, 1580, [[0, shade(BL, -0.22)], [1, shade(BL, -0.48)]]); ctx.fill();
  ctx.save(); ctx.clip();
  for (let x = 120; x < 1300; x += 70 + R() * 50) {
    const w = 30 + R() * 30;
    ctx.fillStyle = lin(ctx, x - w, 0, x + w, 0, [[0, 'rgba(20,28,45,0)'], [0.5, 'rgba(20,28,45,0.12)'], [1, 'rgba(20,28,45,0)']]); ctx.fillRect(x - w, 1400, w * 2, 190);
    ctx.fillStyle = lin(ctx, x + w * 0.8, 0, x + w * 1.6, 0, [[0, 'rgba(255,255,255,0)'], [0.5, 'rgba(230,238,250,0.06)'], [1, 'rgba(255,255,255,0)']]); ctx.fillRect(x + w * 0.8, 1400, w, 190);
  }
  ctx.restore();
  // top surface
  const back = (x) => 1150 + 6 * Math.sin(x * 0.006 + 0.5);
  ctx.beginPath(); ctx.moveTo(100, back(100));
  for (let x = 100; x <= 1296; x += 12) ctx.lineTo(x, back(x));
  ctx.quadraticCurveTo(1312, 1160, 1306, 1200); ctx.lineTo(1306, 1392); ctx.quadraticCurveTo(1304, 1410, 1290, 1408);
  ctx.lineTo(110, 1402); ctx.quadraticCurveTo(88, 1400, 90, 1380); ctx.lineTo(96, 1170); ctx.closePath();
  ctx.fillStyle = lin(ctx, 0, 1140, 0, 1410, [[0, shade(BL, -0.2)], [0.5, shade(BL, -0.04)], [1, shade(BL, 0.04)]]); ctx.fill();
  ctx.save(); ctx.clip();
  // soft folds away from the hands area (x≈540..760 stays plain)
  const fold = (x0, y0, x1, y1, w, a) => blurred(ctx, w * 0.5, () => {
    ctx.strokeStyle = `rgba(30,40,60,${a})`; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo((x0 + x1) / 2 + 30, (y0 + y1) / 2, x1, y1); ctx.stroke();
    ctx.strokeStyle = `rgba(255,255,255,${a * 0.8})`; ctx.lineWidth = w * 0.6; ctx.beginPath(); ctx.moveTo(x0 + w, y0); ctx.quadraticCurveTo((x0 + x1) / 2 + 30 + w, (y0 + y1) / 2, x1 + w, y1); ctx.stroke();
  });
  fold(450, 1180, 500, 1390, 30, 0.07); fold(880, 1190, 840, 1390, 34, 0.06); fold(1030, 1180, 1080, 1385, 30, 0.06); fold(1180, 1200, 1160, 1395, 30, 0.05);
  // gentle woven texture: very faint cross-hatch so the surface reads as soft cotton up close
  ctx.globalAlpha = 0.05; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1;
  for (let yy = 1150; yy < 1410; yy += 7) { ctx.beginPath(); ctx.moveTo(90, yy); ctx.lineTo(1310, yy + 4); ctx.stroke(); }
  ctx.globalAlpha = 1;
  // lamp warmth on the head end, darker far edge
  ctx.fillStyle = lin(ctx, 90, 0, 1310, 0, [[0, 'rgba(255,200,140,0.22)'], [0.4, 'rgba(255,210,160,0.06)'], [1, 'rgba(60,80,120,0.12)']]); ctx.fillRect(80, 1140, 1240, 280);
  // a gentle body-less mattress rise along the middle, rounded front edge highlight
  ctx.fillStyle = lin(ctx, 0, 1360, 0, 1406, [[0, 'rgba(255,255,255,0)'], [0.7, 'rgba(255,255,255,0.18)'], [1, 'rgba(40,50,70,0.15)']]); ctx.fillRect(80, 1360, 1240, 50);
  // turned-down sheet band near the pillow
  ctx.fillStyle = shade('#dfe4ec', -0.08); poly(ctx, [[340, 1140], [420, 1140], [404, 1410], [318, 1410]]); ctx.fill();
  ctx.fillStyle = lin(ctx, 404, 0, 440, 0, [[0, 'rgba(20,28,45,0.25)'], [1, 'rgba(20,28,45,0)']]); poly(ctx, [[420, 1140], [452, 1140], [436, 1410], [404, 1410]]); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.3)'; poly(ctx, [[340, 1140], [350, 1140], [328, 1410], [318, 1410]]); ctx.fill();
  ctx.restore();
  // turned-down band over the drape too
  ctx.fillStyle = shade('#dfe4ec', -0.3); poly(ctx, [[318, 1402], [404, 1404], [406, 1560], [316, 1566]]); ctx.fill();
  // pillow
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(20,25,40,0.35)'; ctx.beginPath(); ctx.ellipse(230, 1190, 140, 30, 0, 0, 7); ctx.fill(); });
  ctx.beginPath(); ctx.moveTo(112, 1080); ctx.quadraticCurveTo(108, 1052, 150, 1050); ctx.quadraticCurveTo(230, 1040, 312, 1052); ctx.quadraticCurveTo(352, 1056, 348, 1090);
  ctx.quadraticCurveTo(356, 1150, 344, 1186); ctx.quadraticCurveTo(340, 1204, 300, 1200); ctx.quadraticCurveTo(220, 1210, 140, 1200); ctx.quadraticCurveTo(104, 1198, 108, 1160); ctx.quadraticCurveTo(100, 1120, 112, 1080); ctx.closePath();
  ctx.fillStyle = lin(ctx, 0, 1045, 0, 1205, [[0, '#e8dccb'], [0.45, '#d4d6db'], [1, '#98a2b4']]); ctx.fill();
  ctx.save(); ctx.clip();
  softGlow(ctx, 150, 1070, 160, '#ffe2bc', 0.35, 0.7);   // lamp-lit side
  blurred(ctx, 10, () => { ctx.fillStyle = 'rgba(50,60,85,0.18)'; ctx.beginPath(); ctx.ellipse(240, 1130, 70, 28, 0.05, 0, 7); ctx.fill(); }); // soft hollow where a head rested
  ctx.restore();
  ctx.strokeStyle = 'rgba(60,70,95,0.18)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(150, 1056); ctx.quadraticCurveTo(170, 1090, 156, 1120); ctx.moveTo(300, 1060); ctx.quadraticCurveTo(290, 1100, 312, 1140); ctx.stroke();
  // lowered side rail near the head
  ctx.fillStyle = 'rgba(150,160,178,0.9)'; rr(ctx, 130, 1440, 330, 14, 7); ctx.fill(); rr(ctx, 130, 1520, 330, 12, 6); ctx.fill();
  for (const x of [150, 230, 310, 390, 440]) { ctx.fillStyle = 'rgba(130,140,158,0.9)'; ctx.fillRect(x, 1450, 8, 74); }
  ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.fillRect(134, 1442, 322, 3);
}

function hChair(ctx) {
  // empty visitor chair, pulled up in front of the bed; seat top ≈ y 1500 around x 1150
  const vin = '#7a6070', wood = '#8a6a50';
  contact(ctx, 1165, 1832, 170, 22, 0.55);
  blurred(ctx, 22, () => { ctx.fillStyle = 'rgba(8,10,20,0.35)'; ctx.beginPath(); ctx.ellipse(1150, 1810, 150, 36, 0, 0, 7); ctx.fill(); });
  // back legs
  for (const x of [1082, 1220]) { ctx.fillStyle = shade(wood, -0.45); ctx.fillRect(x - 8, 1520, 16, 250); }
  // back cushion (behind the seat)
  ctx.fillStyle = lin(ctx, 1060, 0, 1240, 0, [[0, shade(vin, -0.25)], [0.35, shade(vin, 0.06)], [1, shade(vin, -0.3)]]);
  ctx.beginPath(); ctx.moveTo(1060, 1490); ctx.lineTo(1062, 1262); ctx.quadraticCurveTo(1064, 1226, 1100, 1222); ctx.quadraticCurveTo(1150, 1214, 1202, 1222); ctx.quadraticCurveTo(1238, 1226, 1240, 1262); ctx.lineTo(1242, 1490); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,225,205,0.10)'; rr(ctx, 1074, 1236, 64, 240, 20); ctx.fill();
  ctx.strokeStyle = 'rgba(30,20,30,0.22)'; ctx.lineWidth = 2; rr(ctx, 1076, 1240, 150, 236, 18); ctx.stroke();
  ctx.strokeStyle = 'rgba(30,20,30,0.16)'; ctx.beginPath(); ctx.moveTo(1080, 1358); ctx.lineTo(1222, 1358); ctx.stroke();
  // seat: top surface + front face
  ctx.fillStyle = lin(ctx, 0, 1470, 0, 1530, [[0, shade(vin, -0.12)], [1, shade(vin, 0.05)]]);
  ctx.beginPath(); ctx.moveTo(1066, 1478); ctx.lineTo(1236, 1474); ctx.quadraticCurveTo(1262, 1500, 1258, 1530); ctx.lineTo(1050, 1534); ctx.quadraticCurveTo(1044, 1500, 1066, 1478); ctx.fill();
  ctx.fillStyle = lin(ctx, 0, 1530, 0, 1574, [[0, shade(vin, -0.12)], [1, shade(vin, -0.38)]]); rr(ctx, 1048, 1526, 212, 46, 14); ctx.fill();
  ctx.fillStyle = 'rgba(255,235,220,0.14)'; ctx.fillRect(1060, 1528, 190, 3);
  // front legs
  for (const [x, k] of [[1066, -1], [1242, 1]]) {
    ctx.fillStyle = lin(ctx, x - 10, 0, x + 10, 0, [[0, shade(wood, -0.35)], [0.45, shade(wood, 0.05)], [1, shade(wood, -0.4)]]);
    poly(ctx, [[x - 10, 1566], [x + 10, 1566], [x + 8 + k * 6, 1830], [x - 8 + k * 6, 1830]]); ctx.fill();
    contact(ctx, x + 4 + k * 6, 1830, 24, 5, 0.6);
  }
  ctx.fillStyle = shade(wood, -0.3); ctx.fillRect(1072, 1700, 168, 8); // stretcher
  // wooden arms
  for (const [x0, x1] of [[1040, 1076], [1226, 1262]]) {
    ctx.fillStyle = lin(ctx, 0, 1378, 0, 1398, [[0, shade(wood, 0.2)], [1, shade(wood, -0.2)]]); rr(ctx, x0 - 4, 1380, x1 - x0 + 8, 18, 8); ctx.fill();
    ctx.fillStyle = shade(wood, -0.2); ctx.fillRect((x0 + x1) / 2 - 6, 1396, 12, 132);
  }
}
function hFloor(ctx, R) {
  ctx.fillStyle = lin(ctx, 0, H_FLOOR, 0, HC.y1, [[0, '#5d6878'], [0.4, '#4f5a6a'], [1, '#3a4252']]); ctx.fillRect(HC.x0, H_FLOOR, HC.x1 - HC.x0, HC.y1 - H_FLOOR);
  // faint sheet-vinyl seams in perspective
  const vx = 650, vy = 900;
  ctx.strokeStyle = 'rgba(20,25,35,0.18)'; ctx.lineWidth = 2;
  for (let x = -1400; x < 2800; x += 300) { const f = (HC.y1 - vy) / (H_FLOOR - vy); ctx.beginPath(); ctx.moveTo(x, H_FLOOR); ctx.lineTo(vx + (x - vx) * f, HC.y1); ctx.stroke(); }
  // baseboard
  ctx.fillStyle = '#3f4858'; ctx.fillRect(HC.x0, H_FLOOR - 30, HC.x1 - HC.x0, 30);
  ctx.fillStyle = lin(ctx, 0, H_FLOOR, 0, H_FLOOR + 60, [[0, 'rgba(10,12,20,0.4)'], [1, 'rgba(10,12,20,0)']]); ctx.fillRect(HC.x0, H_FLOOR, HC.x1 - HC.x0, 60);
  // soft reflections: lamp (warm) and window (cool)
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  softGlow(ctx, LAMPP.x + 40, 1700, 380, '#c08a50', 0.25, 0.35);
  softGlow(ctx, 760, 1900, 520, '#6a80aa', 0.2, 0.3);
  ctx.restore();
  grain(HCACHE_TMP, [HC.x0, H_FLOOR, HC.x1 - HC.x0, HC.y1 - H_FLOOR], 5, 0.05, 31, 0.5);
}
let HCACHE_TMP = null;
function buildHospital() {
  const R = mulberry32(2024);
  const c = newCache(HC.x0, HC.y0, HC.x1, HC.y1), x = c.ctx;
  HCACHE_TMP = c;
  hWall(x, R);
  hWindow(x, R);
  moonStripes(x, 0.16);
  grain(c, [HC.x0, HC.y0, HC.x1 - HC.x0, H_FLOOR - HC.y0], 5, 0.03, 32);
  hMonitor(x);
  hFloor(x, R);
  hBedsideLeft(x);
  hIV(x);
  hBedsideRight(x);
  hBed(x, R);
  // moonlight stripes across the bed's right half + floor (soft; the hands area stays plain)
  x.save(); x.globalCompositeOperation = 'screen';
  blurred(x, 8, () => {
    for (let i = 0; i < 7; i++) {
      const y = 1196 + i * 30;
      x.fillStyle = `rgba(150,175,225,${0.13 - i * 0.008})`;
      poly(x, [[860 - i * 10, y], [1290 - i * 6, y], [1280 - i * 6, y + 13], [850 - i * 10, y + 13]]); x.fill();
    }
    for (let i = 0; i < 7; i++) {
      const y = 1860 + i * 46;
      x.fillStyle = `rgba(130,155,210,${0.1 - i * 0.008})`;
      poly(x, [[420 - i * 30, y], [1080 - i * 20, y], [1060 - i * 22, y + 20], [400 - i * 32, y + 20]]); x.fill();
    }
  });
  x.restore();
  // lamp warmth on the bed's head end + pillow, cool moon on the right
  x.save(); x.globalCompositeOperation = 'soft-light';
  x.fillStyle = lin(x, -300, 0, 1400, 0, [[0, 'rgba(255,190,120,0.55)'], [0.45, 'rgba(255,200,140,0.18)'], [0.7, 'rgba(120,150,210,0.15)'], [1, 'rgba(110,140,210,0.4)']]);
  x.fillRect(HC.x0, HC.y0, HC.x1 - HC.x0, HC.y1 - HC.y0);
  x.restore();
  x.save(); x.globalCompositeOperation = 'screen'; softGlow(x, 120, 1200, 700, '#ffb470', 0.16, 0.6); x.restore();
  candleBody(x);
  hChair(x);
  // night: gentle overall darkening at the edges (top + far left/right)
  x.fillStyle = rad(x, 760, 1250, 500, 1700, [[0, 'rgba(8,10,22,0)'], [1, 'rgba(8,10,22,0.5)']]); x.fillRect(HC.x0, HC.y0, HC.x1 - HC.x0, HC.y1 - HC.y0);
  HCACHE_TMP = null;
  return { room: pair(c) };
}
let HCACHE = null;
const hospital = {
  ENV: {
    name: 'hospital',
    extents: { ...HEXT },
    options: { chairEmpty: true, candle: false },
    anchors: {
      handsOnBlanket: { x: 650, y: 1230 },
      chair: { x: 1150, y: 1500 },
      candle: { x: CANDLE.x, y: CANDLE.y },
      lamp: { x: LAMPP.x, y: LAMPP.y },
      window: { x: 750, y: 415 },
      pillow: { x: 230, y: 1120 },
      monitor: { x: (MON.x0 + MON.x1) / 2, y: (MON.y0 + MON.y1) / 2 },
    },
  },
  drawBack(ctx, t, o = {}) {
    if (!HCACHE) HCACHE = buildHospital();
    ctx.fillStyle = '#2c3342'; ctx.fillRect(HC.x0 - 3000, HC.y0 - 3000, 8000, 9000);
    blit(ctx, HCACHE.room);
    monitorTrace(ctx, t);
    const c = o.candle === true ? 1 : o.candle ? clamp(+o.candle, 0, 1) : 0;
    if (c > 0.001) candleFlame(ctx, t, c);
  },
  drawFront() { /* nothing in front */ },
  lightAt(x, y, t, o = {}) {
    const px = x, py = y - 300;
    const dl = Math.hypot(px - LAMPP.x, py - LAMPP.y), near = 1 / (1 + Math.pow(dl / 900, 2));
    const c = o.candle === true ? 1 : o.candle ? clamp(+o.candle, 0, 1) : 0;
    return {
      keyDir: Math.atan2(LAMPP.y - py, LAMPP.x - px),
      keyColor: '#ffd29a', keyAmt: clamp(0.45 + 0.35 * near + 0.08 * c, 0.45, 0.8),
      rimDir: Math.atan2(415 - py, 750 - px), rimColor: '#a8c0e8', rimAmt: 0.4,
      shadowColor: '#252d45', shadowAmt: 0.38,
      ambient: '#b8c4dc', ambientAmt: 0.2,
    };
  },
};

module.exports = { kitchen, memory, hospital };
