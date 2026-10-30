'use strict';
// The Inner Hearth — the cozy round stone-and-timber room inside Maya's mind.
// Environment module (see CONVENTIONS.md) + drawVision() for the smoke/ember visions
// that appear over the chimney breast.
//
// Options `o` (all optional):
//   view        'kitchen' (default) | 'night' | 'dawn' | 'nana'  — what is seen through the round window
//   viewFn      function(ctx, cx, cy, r) — custom window content; ctx is clipped to the glass circle
//   fire        0..2 (default 1)  1 = cozy, 0.3 = low embers, 2 = roaring (flames lick out of the opening)
//   doorOpen    0..1 (default 0)  back-left door swings inward on its left hinges
//   bellowsHidden  bool (default false) — hide the bellows hanging beside the hearth
//   chairs      {c700:true, c960:true, c1100:true} — set a key false to hide that chair
//   cornerLight 0..1 (default 0)  warms Sadness's corner (lights the floor lantern)
//   candle      bool (default true) — mantel candle lit
//   fairy       0..1 (default 1)  fairy-light brightness
//   steam       0..1 (default 0.6) — faint steam over the tea cup
//
// drawVision(ctx, t, v): world-coordinate visions (see bottom of file).

const { createCanvas } = require('@napi-rs/canvas');

// ------------------------------------------------------------------ helpers
const EXT = { x0: -500, y0: -600, x1: 2100, y1: 2500 };
const CP = 64; // cache covers the extents plus this margin
const CEXT = { x0: EXT.x0 - CP, y0: EXT.y0 - CP, x1: EXT.x1 + CP, y1: EXT.y1 + CP };
const S = 1.25;              // cache scale (px per world unit)
const VPX = 800, VPY = 1050; // vanishing point / horizon (seated eye height)
const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0; let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function h1(i) {
  let x = Math.imul((i | 0) ^ 0x9e3779b9, 0x85ebca6b); x ^= x >>> 13;
  x = Math.imul(x, 0xc2b2ae35); x ^= x >>> 16; return (x >>> 0) / 4294967296;
}
function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(h1(i + seed * 7919), h1(i + 1 + seed * 7919), u);
}
const rgba = (r, g, b, a = 1) => `rgba(${r | 0},${g | 0},${b | 0},${a})`;
function hexToRgb(h) { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; }
function rgbToHex(r, g, b) { return '#' + [r, g, b].map(v => clamp(Math.round(v), 0, 255).toString(16).padStart(2, '0')).join(''); }
function mixHex(a, b, t) { const A = hexToRgb(a), B = hexToRgb(b); return rgbToHex(lerp(A[0], B[0], t), lerp(A[1], B[1], t), lerp(A[2], B[2], t)); }
function shadeRgb(c, k) { return [c[0] * k, c[1] * k, c[2] * k]; }

// gentle, low-frequency firelight flicker (~0.3..1.1 Hz), mean 1
function flick(t) {
  return 1 + 0.045 * Math.sin(t * 4.1) + 0.035 * Math.sin(t * 6.3 + 1.3) +
    0.05 * (noise1(t * 1.7, 3) - 0.5) * 2;
}

// round-room perspective: stone courses bow (U above eye level, gently ∩ below)
function kOf(v) { return v < VPY ? -0.00008 * (VPY - v) / 900 : 0.00002 * (v - VPY) / 430; }
function warpY(x, v) { const d = x - VPX; return v + kOf(v) * d * d; }
const yC = x => warpY(x, 150);   // wall / ceiling junction
const yF = x => warpY(x, 1480);  // wall / floor junction

function sprite(x0, y0, x1, y1, fn, sc = S) {
  const w = Math.ceil((x1 - x0) * sc), h = Math.ceil((y1 - y0) * sc);
  const c = createCanvas(w, h), g = c.getContext('2d');
  g.scale(sc, sc); g.translate(-x0, -y0); fn(g);
  return { c, x0, y0, x1, y1, sc };
}
// Skia rebuilds mipmaps every time a canvas is drawn *downscaled*, which is slow, so
// static layers keep a small pyramid and we always pick a level that is drawn at ~1:1
// or slightly upscaled (a little softness in wide shots reads as depth of field).
function downsample(c, k) {
  const d = createCanvas(Math.max(1, Math.round(c.width * k)), Math.max(1, Math.round(c.height * k)));
  const g = d.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(c, 0, 0, d.width, d.height); return d;
}
function pickLevel(levels, ds) {
  let best = levels[levels.length - 1];
  for (const L of levels) if (L.s <= ds * 1.12 && L.s > (best.s <= ds * 1.12 ? best.s : -1)) best = L;
  return best;
}
function curScale(ctx) { const m = ctx.getTransform(); return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)); }
function blit(ctx, sp, alpha = 1) {
  if (alpha <= 0) return;
  if (!sp.levels) { const s0 = sp.sc || S; sp.levels = [{ s: s0, c: sp.c }, { s: s0 * 0.5, c: downsample(sp.c, 0.5) }]; }
  const L = pickLevel(sp.levels, curScale(ctx));
  const a = ctx.globalAlpha; ctx.globalAlpha = a * alpha;
  ctx.drawImage(L.c, sp.x0, sp.y0, sp.x1 - sp.x0, sp.y1 - sp.y0);
  ctx.globalAlpha = a;
}
// multiplied ("dimmed") copy of a sprite, used to fade drawFront props with the room light
function dimVariant(sp, color) {
  const c = createCanvas(sp.c.width, sp.c.height), g = c.getContext('2d');
  g.drawImage(sp.c, 0, 0); g.globalCompositeOperation = 'multiply'; g.fillStyle = color;
  g.fillRect(0, 0, c.width, c.height); g.globalCompositeOperation = 'destination-in'; g.drawImage(sp.c, 0, 0);
  return { c, x0: sp.x0, y0: sp.y0, x1: sp.x1, y1: sp.y1, sc: sp.sc };
}
function radial(ctx, x, y, r, stops) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  for (const [p, c] of stops) g.addColorStop(p, c);
  return g;
}
function linear(ctx, x0, y0, x1, y1, stops) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  for (const [p, c] of stops) g.addColorStop(p, c);
  return g;
}
// soft elliptical blob (for shadows / glows)
function softEllipse(ctx, x, y, rx, ry, color0, color1 = 'rgba(0,0,0,0)', inner = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(1, ry / rx);
  ctx.fillStyle = radial(ctx, 0, 0, rx, [[inner, color0], [1, color1]]);
  ctx.beginPath(); ctx.arc(0, 0, rx, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}
// world rect visible through the current transform
function visRect(ctx) {
  const m = ctx.getTransform(); const W = ctx.canvas ? ctx.canvas.width : 1080, H = ctx.canvas ? ctx.canvas.height : 1920;
  const det = m.a * m.d - m.b * m.c;
  const inv = (px, py) => { const x = px - m.e, y = py - m.f; return [(m.d * x - m.c * y) / det, (-m.b * x + m.a * y) / det]; };
  const pts = [inv(0, 0), inv(W, 0), inv(0, H), inv(W, H)];
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys), sc: Math.sqrt(Math.abs(det)) };
}

// ---------------------------------------------------------- texture helpers
function makeNoiseTex(size, seed, periods, weights, white) {
  const c = createCanvas(size, size), g = c.getContext('2d');
  const id = g.createImageData(size, size), d = id.data;
  const r = rng(seed);
  const tabs = periods.map(P => { const a = new Float32Array(P * P); for (let i = 0; i < a.length; i++) a[i] = r(); return a; });
  for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) {
    let v = 0;
    periods.forEach((P, k) => {
      const fx = x / size * P, fy = y / size * P, ix = Math.floor(fx), iy = Math.floor(fy);
      const ux = fx - ix, uy = fy - iy, sx = ux * ux * (3 - 2 * ux), sy = uy * uy * (3 - 2 * uy);
      const T = tabs[k], a = T[(iy % P) * P + (ix % P)], b = T[(iy % P) * P + ((ix + 1) % P)];
      const c2 = T[((iy + 1) % P) * P + (ix % P)], e = T[((iy + 1) % P) * P + ((ix + 1) % P)];
      v += weights[k] * lerp(lerp(a, b, sx), lerp(c2, e, sx), sy);
    });
    v += white * (r() - 0.5);
    const q = clamp(128 + (v - 0.5 * weights.reduce((s, w) => s + w, 0)) * 255, 0, 255);
    const i = (y * size + x) * 4; d[i] = d[i + 1] = d[i + 2] = q; d[i + 3] = 255;
  }
  g.putImageData(id, 0, 0);
  return c;
}
function tile(ctx, tex, x0, y0, x1, y1, worldSize, op, alpha) {
  ctx.save(); ctx.globalCompositeOperation = op; ctx.globalAlpha = alpha;
  for (let y = Math.floor(y0 / worldSize) * worldSize; y < y1; y += worldSize)
    for (let x = Math.floor(x0 / worldSize) * worldSize; x < x1; x += worldSize)
      ctx.drawImage(tex, x, y, worldSize + 0.5, worldSize + 0.5);
  ctx.restore();
}

// irregular rounded stone (superellipse with jitter) in (u,v) space, optionally warped
function stonePoly(r, x0, v0, x1, v1, warp, n = 4.5, jit = 0.05) {
  const cx = (x0 + x1) / 2, cv = (v0 + v1) / 2, a = (x1 - x0) / 2, b = (v1 - v0) / 2;
  const pts = []; const N = 22; const ph = r() * 6;
  for (let i = 0; i < N; i++) {
    const th = (i / N) * Math.PI * 2;
    const c = Math.cos(th), s = Math.sin(th);
    const k = 1 + jit * (Math.sin(th * 3 + ph) * 0.6 + (r() - 0.5));
    const x = cx + a * k * Math.sign(c) * Math.pow(Math.abs(c), 2 / n);
    const v = cv + b * k * Math.sign(s) * Math.pow(Math.abs(s), 2 / n);
    pts.push([x, warp ? warpY(x, v) : v]);
  }
  return pts;
}
function polyPath(ctx, pts) { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]); ctx.closePath(); }

function drawStone(ctx, r, x0, v0, x1, v1, o) {
  const ins = o.inset;
  const irr = o.irr ?? 1;
  const pts = stonePoly(r, x0 + ins + r() * 2 * irr, v0 + ins + r() * 6 * irr, x1 - ins - r() * 2 * irr, v1 - ins - r() * 6 * irr, o.warp,
    (o.n || 4.5) + (r() - 0.5) * 2.5 * irr, (o.jit || 0.05) * (1 + irr));
  const base = o.base;
  const kv = o.kVar ?? 0.26; let k = 1 - kv / 2 + kv * r(); if (r() < 0.12) k *= 0.9; if (r() < 0.08) k *= 1.08;
  const warm = (r() - 0.5) * (o.hueVar ?? 14);
  const col = [base[0] * k + warm, base[1] * k + warm * 0.3, base[2] * k - warm * 0.6];
  polyPath(ctx, pts);
  ctx.fillStyle = rgba(...col); ctx.fill();
  const ys = pts.map(p => p[1]); const ya = Math.min(...ys), yb = Math.max(...ys);
  const xs = pts.map(p => p[0]); const xa = Math.min(...xs), xb = Math.max(...xs);
  ctx.fillStyle = linear(ctx, xa, ya, xa + (xb - xa) * 0.15, yb, [[0, 'rgba(255,236,210,0.16)'], [0.3, 'rgba(255,236,210,0.0)'], [0.62, 'rgba(25,14,8,0)'], [1, 'rgba(25,14,8,0.26)']]);
  ctx.fill();
  // soft mottling inside the stone
  ctx.save(); ctx.clip();
  const nm = 2 + Math.floor(r() * 3);
  for (let i = 0; i < nm; i++) {
    const mx = lerp(xa, xb, r()), my = lerp(ya, yb, r()), mr = (xb - xa) * (0.15 + r() * 0.3);
    softEllipse(ctx, mx, my, mr, mr * 0.6, r() < 0.5 ? 'rgba(30,20,12,0.12)' : 'rgba(255,240,220,0.08)');
  }
  // pits / grit
  const np = 3 + Math.floor(r() * 7);
  for (let i = 0; i < np; i++) {
    const px = lerp(xa, xb, r()), py = lerp(ya, yb, r()), pr = 0.8 + r() * 2.2;
    ctx.fillStyle = r() < 0.7 ? 'rgba(28,18,12,0.35)' : 'rgba(255,240,215,0.25)';
    ctx.beginPath(); ctx.arc(px, py, pr, 0, 7); ctx.fill();
  }
  // a chip on an edge now and then
  if (r() < (o.chip ?? 0.35)) {
    const ex = lerp(xa + 6, xb - 6, r()), top = r() < 0.5, ey = top ? ya + 2 : yb - 2, cw = 6 + r() * 10;
    ctx.beginPath(); ctx.moveTo(ex - cw, ey); ctx.lineTo(ex - cw * 0.2, ey + (top ? 1 : -1) * (3 + r() * 5)); ctx.lineTo(ex + cw, ey); ctx.closePath();
    ctx.fillStyle = top ? 'rgba(255,238,215,0.22)' : 'rgba(25,15,10,0.3)'; ctx.fill();
  }
  ctx.restore();
  // chiselled bevel: light top-left rim, dark bottom-right rim
  ctx.save(); polyPath(ctx, pts); ctx.clip();
  ctx.translate(2.5, 3); polyPath(ctx, pts); ctx.strokeStyle = 'rgba(255,238,215,0.13)'; ctx.lineWidth = 5; ctx.stroke();
  ctx.translate(-5, -6); polyPath(ctx, pts); ctx.strokeStyle = 'rgba(25,14,8,0.22)'; ctx.lineWidth = 6; ctx.stroke();
  ctx.restore();
  // hairline cracks
  if (r() < 0.25) { ctx.strokeStyle = 'rgba(30,18,12,0.3)'; ctx.lineWidth = 1; let cx2 = lerp(xa, xb, 0.2 + r() * 0.6), cy2 = ya + 3; ctx.beginPath(); ctx.moveTo(cx2, cy2); for (let k = 0; k < 4; k++) { cx2 += (r() - 0.5) * 12; cy2 += (yb - ya) * 0.2; ctx.lineTo(cx2, cy2); } ctx.stroke(); }
  polyPath(ctx, pts);
  ctx.strokeStyle = rgba(...shadeRgb(col, 0.6), 0.25); ctx.lineWidth = 1.2; ctx.stroke();
}
function stoneCourses(ctx, R, o) {
  const r = rng(o.seed); let v = R.v0;
  while (v < R.v1) {
    const v1 = Math.min(v + lerp(o.hMin, o.hMax, r()), R.v1);
    let x = R.x0 - r() * o.wMax;
    while (x < R.x1) { const w = lerp(o.wMin, o.wMax, r()); drawStone(ctx, r, x, v, x + w, v1, o); x += w; }
    v = v1;
  }
}

// ---------------------------------------------------------- geometry consts
const WIN = { x: 650, y: 640, r: 300 };
const DOOR = { x0: 60, x1: 340, y0: 880, y1: 1480, spring: 1020 };
const FB = { x0: 1370, x1: 1680, y0: 1110, y1: 1470, cx: 1525, spring: 1265, r: 155 };
const FIRE = { x: 1525, y: 1300 };

function doorwayPath(ctx, inset = 0, noBegin = false) {
  const r = (DOOR.x1 - DOOR.x0) / 2 - inset, cx = (DOOR.x0 + DOOR.x1) / 2;
  if (!noBegin) ctx.beginPath();
  const yb = DOOR.y1 + Math.max(0, -inset);
  ctx.moveTo(DOOR.x0 + inset, yb);
  ctx.lineTo(DOOR.x0 + inset, DOOR.spring); ctx.arc(cx, DOOR.spring, r, Math.PI, 0); ctx.lineTo(DOOR.x1 - inset, yb); ctx.closePath();
}
function fireboxPath(ctx, inset = 0, noBegin = false) {
  if (!noBegin) ctx.beginPath();
  ctx.moveTo(FB.x0 + inset, FB.y1); ctx.lineTo(FB.x0 + inset, FB.spring);
  ctx.arc(FB.cx, FB.spring, FB.r - inset, Math.PI, 0); ctx.lineTo(FB.x1 - inset, FB.y1); ctx.closePath();
}
function wallPath(ctx) {
  ctx.beginPath(); ctx.moveTo(EXT.x0 - 90, yC(EXT.x0 - 90) - 2);
  for (let x = EXT.x0; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, yC(x) - 2);
  for (let x = EXT.x1 + 90; x >= EXT.x0 - 90; x -= 20) ctx.lineTo(x, yF(x) + 3);
  ctx.closePath();
}
// line from VP through (xj, yj) evaluated at screen y
function vpX(xj, yj, y) { return VPX + (xj - VPX) * (y - VPY) / (yj - VPY); }

// ============================================================ STATIC ROOM
function paintCeiling(ctx) {
  const r = rng(11);
  ctx.fillStyle = '#3a2a20'; ctx.fillRect(EXT.x0 - 90, EXT.y0 - 90, EXT.x1 - EXT.x0 + 180, 900);
  // ceiling boards radiating from the vanishing point
  const top = EXT.y0 - 90;
  for (let x = -2600; x < 4200; x += 46) {
    const x2 = x + 46, j0 = yC(x), j1 = yC(x2);
    const k = 0.85 + r() * 0.3;
    ctx.beginPath(); ctx.moveTo(x, j0); ctx.lineTo(vpX(x, j0, top), top); ctx.lineTo(vpX(x2, j1, top), top); ctx.lineTo(x2, j1); ctx.closePath();
    ctx.fillStyle = rgba(66 * k, 48 * k, 36 * k); ctx.fill();
    ctx.strokeStyle = 'rgba(20,12,8,0.45)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, j0); ctx.lineTo(vpX(x, j0, top), top); ctx.stroke();
    // grain
    ctx.strokeStyle = 'rgba(25,15,10,0.18)'; ctx.lineWidth = 1;
    for (let i = 0; i < 3; i++) { const f = 0.2 + r() * 0.6, xa = lerp(x, x2, f), ja = lerp(j0, j1, f); ctx.beginPath(); ctx.moveTo(xa, ja - 20); ctx.lineTo(vpX(xa, ja, top + 200 + r() * 300), top + 200 + r() * 300); ctx.stroke(); }
  }
  // joists
  for (let xj = -750; xj < 2500; xj += 350) {
    const hw = 30, a = xj - hw, b = xj + hw, ja = yC(a), jb = yC(b);
    const pts = [[a, ja], [vpX(a, ja, top), top], [vpX(b, jb, top), top], [b, jb]];
    polyPath(ctx, pts);
    ctx.fillStyle = linear(ctx, 0, top, 0, yC(xj), [[0, '#2e2119'], [1, '#5a4130']]); ctx.fill();
    // inner side face (towards the centre)
    const side = xj > VPX ? -1 : 1, e = xj + side * hw, e2 = xj + side * hw * 0.25;
    const je = yC(e), je2 = yC(e2);
    polyPath(ctx, [[e, je], [vpX(e, je, top), top], [vpX(e2, je2, top), top], [e2, je2]]);
    ctx.fillStyle = 'rgba(20,12,8,0.35)'; ctx.fill();
    // cracks / checks in the timber
    ctx.strokeStyle = 'rgba(20,12,8,0.35)'; ctx.lineWidth = 1.5;
    for (let i = 0; i < 2; i++) { const f = 0.3 + r() * 0.4, xa = lerp(a, b, f), jj = yC(xa) - 30 - r() * 100; ctx.beginPath(); ctx.moveTo(xa, jj); ctx.lineTo(vpX(xa, jj, jj - 120 - r() * 160), jj - 120 - r() * 160); ctx.stroke(); }
  }
  // front cross beam (close to camera)
  ctx.beginPath();
  for (let x = EXT.x0 - 90; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, -470 - 0.00002 * (x - 800) ** 2);
  for (let x = EXT.x1 + 90; x >= EXT.x0 - 90; x -= 20) ctx.lineTo(x, -350 - 0.00002 * (x - 800) ** 2);
  ctx.closePath();
  ctx.fillStyle = linear(ctx, 0, -480, 0, -350, [[0, '#2b1f17'], [0.7, '#4a3527'], [0.78, '#5e4432'], [1, '#3a2a1f']]); ctx.fill();
  ctx.strokeStyle = 'rgba(15,9,6,0.3)'; ctx.lineWidth = 2;
  for (let i = 0; i < 9; i++) { const y = -455 + r() * 80, x0 = EXT.x0 + r() * 2400, L = 200 + r() * 500; ctx.beginPath(); ctx.moveTo(x0, y - 0.00002 * (x0 - 800) ** 2); ctx.lineTo(x0 + L, y + 3 - 0.00002 * (x0 + L - 800) ** 2); ctx.stroke(); }
}

function paintWallPlate(ctx) {
  const r = rng(12);
  ctx.beginPath();
  for (let x = EXT.x0 - 90; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, yC(x) - 46);
  for (let x = EXT.x1 + 90; x >= EXT.x0 - 90; x -= 20) ctx.lineTo(x, yC(x) + 20);
  ctx.closePath();
  ctx.fillStyle = linear(ctx, 0, 70, 0, 175, [[0, '#3b2a1f'], [0.55, '#5c4231'], [0.78, '#6a4d38'], [1, '#3e2c20']]); ctx.fill();
  ctx.strokeStyle = 'rgba(20,12,8,0.3)'; ctx.lineWidth = 1.5;
  for (let i = 0; i < 26; i++) { const x0 = EXT.x0 + r() * 2600, L = 80 + r() * 260, v = 110 + r() * 50; ctx.beginPath(); ctx.moveTo(x0, warpY(x0, v)); ctx.quadraticCurveTo(x0 + L / 2, warpY(x0 + L / 2, v + (r() - 0.5) * 6), x0 + L, warpY(x0 + L, v)); ctx.stroke(); }
  // soft shadow of the plate on the wall
  ctx.beginPath();
  for (let x = EXT.x0 - 90; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, yC(x) + 20);
  for (let x = EXT.x1 + 90; x >= EXT.x0 - 90; x -= 20) ctx.lineTo(x, yC(x) + 80);
  ctx.closePath(); ctx.fillStyle = linear(ctx, 0, 170, 0, 230, [[0, 'rgba(20,12,8,0.35)'], [1, 'rgba(20,12,8,0)']]); ctx.fill();
}

function paintWalls(ctx, tex) {
  ctx.save(); wallPath(ctx); ctx.clip();
  ctx.fillStyle = '#6c5e50'; ctx.fillRect(EXT.x0 - 90, 0, EXT.x1 - EXT.x0 + 180, 1600);
  tile(ctx, tex.grit, EXT.x0 - 90, 0, EXT.x1 + 90, 1600, 300, 'overlay', 0.18);
  stoneCourses(ctx, { x0: EXT.x0 - 120, x1: EXT.x1 + 120, v0: 100, v1: 1500 },
    { seed: 21, hMin: 52, hMax: 82, wMin: 80, wMax: 175, inset: 3.5, base: [136, 121, 105], warp: true, kVar: 0.16 });
  tile(ctx, tex.grit, EXT.x0 - 90, 0, EXT.x1 + 90, 1600, 300, 'overlay', 0.35);
  tile(ctx, tex.blotch, EXT.x0 - 90, 0, EXT.x1 + 90, 1600, 1100, 'multiply', 0.35);
  // grime near the floor and water streaks below the window ledge
  ctx.fillStyle = linear(ctx, 0, 1300, 0, 1500, [[0, 'rgba(35,24,18,0)'], [1, 'rgba(35,24,18,0.45)']]);
  ctx.fillRect(EXT.x0 - 90, 1300, EXT.x1 - EXT.x0 + 180, 220);
  const r = rng(31);
  for (let i = 0; i < 9; i++) {
    const x = 450 + r() * 400, L = 60 + r() * 140;
    ctx.fillStyle = linear(ctx, 0, 990, 0, 990 + L, [[0, 'rgba(40,28,20,0.16)'], [1, 'rgba(40,28,20,0)']]);
    ctx.fillRect(x, 990, 5 + r() * 9, L);
  }
  ctx.restore();
}

function paintFloor(ctx, tex) {
  const r = rng(41);
  ctx.save();
  ctx.beginPath(); ctx.moveTo(EXT.x0 - 90, yF(EXT.x0 - 90));
  for (let x = EXT.x0; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, yF(x));
  ctx.lineTo(EXT.x1 + 90, EXT.y1 + 90); ctx.lineTo(EXT.x0 - 90, EXT.y1 + 90); ctx.closePath(); ctx.clip();
  ctx.fillStyle = '#5e4331'; ctx.fillRect(EXT.x0 - 90, 1400, EXT.x1 - EXT.x0 + 180, 1200);
  const bot = EXT.y1 + 90, jy = 1480;
  for (let x = -1200; x < 2900; x += 42) {
    const x2 = x + 42;
    const k = 0.84 + r() * 0.3, hue = (r() - 0.5) * 10;
    const xa0 = vpX(x, jy, jy - 30), xb0 = vpX(x2, jy, jy - 30), xa1 = vpX(x, jy, bot), xb1 = vpX(x2, jy, bot);
    ctx.beginPath(); ctx.moveTo(xa0, jy - 30); ctx.lineTo(xa1, bot); ctx.lineTo(xb1, bot); ctx.lineTo(xb0, jy - 30); ctx.closePath();
    ctx.fillStyle = rgba(112 * k + hue, 80 * k + hue * 0.4, 56 * k); ctx.fill();
    // grain streaks
    for (let i = 0; i < 4; i++) {
      const f = 0.15 + r() * 0.7, d0 = 0.15 + r() * 0.8, y0 = VPY + 430 / Math.max(0.2, 1.4 - d0), y1 = y0 + 60 + r() * 400;
      const xs = lerp(x, x2, f);
      ctx.strokeStyle = r() < 0.6 ? 'rgba(40,25,15,0.18)' : 'rgba(255,230,200,0.07)'; ctx.lineWidth = 1 + r() * 1.5;
      ctx.beginPath(); ctx.moveTo(vpX(xs, jy, y0), y0); ctx.lineTo(vpX(xs, jy, y1), y1); ctx.stroke();
    }
    // board gap
    ctx.strokeStyle = 'rgba(25,15,10,0.6)'; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(xa0, jy - 30); ctx.lineTo(xa1, bot); ctx.stroke();
    // butt joints at perspective-spaced depths
    let d = 1 - r() * 0.5;
    while (d > 0.12) {
      const y = VPY + 430 / d;
      if (y < bot) {
        ctx.strokeStyle = 'rgba(25,15,10,0.55)'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(vpX(x, jy, y), y); ctx.lineTo(vpX(x2, jy, y), y); ctx.stroke();
        ctx.strokeStyle = 'rgba(255,230,200,0.08)'; ctx.beginPath(); ctx.moveTo(vpX(x, jy, y + 2), y + 2); ctx.lineTo(vpX(x2, jy, y + 2), y + 2); ctx.stroke();
      }
      d -= 0.3 + r() * 0.25;
    }
  }
  tile(ctx, tex.grit, EXT.x0 - 90, 1450, EXT.x1 + 90, EXT.y1 + 90, 300, 'overlay', 0.3);
  // dark seam where floor meets wall
  ctx.fillStyle = linear(ctx, 0, 1480, 0, 1560, [[0, 'rgba(25,15,10,0.5)'], [1, 'rgba(25,15,10,0)']]);
  ctx.fillRect(EXT.x0 - 90, 1470, EXT.x1 - EXT.x0 + 180, 90);
  ctx.restore();
  // baseboard-ish shadow line
  ctx.strokeStyle = 'rgba(20,12,8,0.6)'; ctx.lineWidth = 3; ctx.beginPath();
  for (let x = EXT.x0 - 90; x <= EXT.x1 + 90; x += 20) ctx.lineTo(x, yF(x)); ctx.stroke();
}

function paintRug(ctx) {
  const cx = 800, cy = 1668, RX = 540, RY = 140, r = rng(51);
  // soft contact shadow
  softEllipse(ctx, cx, cy + 6, RX + 30, RY + 12, 'rgba(25,15,10,0.45)', 'rgba(25,15,10,0)', 0.85);
  const cols = ['#7a5040', '#9a8466', '#7d806a', '#6a4d3e', '#a08c6c', '#80553f', '#868a70', '#977a5c', '#6e5040', '#a39070', '#7a7f66', '#855b44', '#9c8768', '#6e5446'];
  const rings = 19, rw = RX / rings;
  for (let i = 0; i < rings; i++) {
    const rx = RX - i * rw, ry = rx * RY / RX;
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = cols[i % cols.length]; ctx.fill();
    // braid ticks
    const n = Math.floor(rx / 4);
    const c = hexToRgb(cols[i % cols.length]);
    for (let j = 0; j < n; j++) {
      const a = (j / n) * Math.PI * 2, a2 = a + (Math.PI * 2 / n) * 0.9;
      const rm = rx - rw * 0.5, rmy = rm * RY / RX;
      const x0 = cx + Math.cos(a) * (rx - rw * 0.1), y0 = cy + Math.sin(a) * (ry - rw * 0.1 * RY / RX);
      const x1 = cx + Math.cos(a2) * (rx - rw * 0.9), y1 = cy + Math.sin(a2) * (ry - rw * 0.9 * RY / RX);
      ctx.strokeStyle = rgba(...shadeRgb(c, j % 2 ? 0.82 : 1.1), 0.5); ctx.lineWidth = 2.4;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      void rmy;
    }
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(40,25,18,0.35)'; ctx.lineWidth = 1.5; ctx.stroke();
  }
  // wear / fade in the middle and soft shading at back edge
  softEllipse(ctx, cx + 60, cy, 330, 80, 'rgba(230,210,180,0.12)', 'rgba(230,210,180,0)');
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, RX, RY, 0, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = linear(ctx, 0, cy - RY, 0, cy + RY, [[0, 'rgba(30,18,12,0.25)'], [0.5, 'rgba(30,18,12,0)'], [1, 'rgba(30,18,12,0.15)']]);
  ctx.fillRect(cx - RX, cy - RY, RX * 2, RY * 2); ctx.restore();
  void r;
}

function paintWindowSurround(ctx, tex) {
  const { x, y } = WIN; const r = rng(61);
  // deep stone reveal (radial voussoirs)
  softEllipse(ctx, x + 10, y + 16, 420, 420, 'rgba(20,12,8,0.35)', 'rgba(20,12,8,0)', 0.75);
  const n = 26;
  for (let i = 0; i < n; i++) {
    const a0 = (i / n) * Math.PI * 2 + 0.01, a1 = ((i + 1) / n) * Math.PI * 2 - 0.01;
    const r0 = 342, r1 = 392 + (r() - 0.5) * 14; const k = 0.88 + r() * 0.24;
    ctx.beginPath(); ctx.arc(x, y, r1, a0, a1); ctx.arc(x, y, r0, a1, a0, true); ctx.closePath();
    ctx.fillStyle = rgba(150 * k, 134 * k, 116 * k); ctx.fill();
    ctx.fillStyle = radial(ctx, x, y, r1, [[r0 / r1, 'rgba(20,12,8,0.25)'], [1, 'rgba(255,240,220,0.06)']]); ctx.fill();
    ctx.strokeStyle = 'rgba(40,28,20,0.5)'; ctx.lineWidth = 2.5; ctx.stroke();
  }
  ctx.save(); ctx.beginPath(); ctx.arc(x, y, 395, 0, 7); ctx.arc(x, y, 340, 0, 7, true); ctx.clip();
  tile(ctx, tex.grit, x - 400, y - 400, x + 400, y + 400, 300, 'overlay', 0.6); ctx.restore();
  // thick wooden frame ring
  ctx.beginPath(); ctx.arc(x, y, 344, 0, 7); ctx.arc(x, y, 296, 0, 7, true);
  ctx.fillStyle = '#6b4a33'; ctx.fill('evenodd');
  ctx.save(); ctx.beginPath(); ctx.arc(x, y, 344, 0, 7); ctx.arc(x, y, 296, 0, 7, true); ctx.clip('evenodd');
  // circular grain
  for (let i = 0; i < 40; i++) {
    const rr = 300 + r() * 42, a0 = r() * 7, L = 0.3 + r() * 1.2;
    ctx.strokeStyle = r() < 0.6 ? 'rgba(35,22,14,0.3)' : 'rgba(255,220,180,0.1)'; ctx.lineWidth = 1 + r() * 1.5;
    ctx.beginPath(); ctx.arc(x, y, rr, a0, a0 + L); ctx.stroke();
  }
  // bevel lighting: lit from lower right (fire), inner edge darker
  ctx.fillStyle = radial(ctx, x, y, 344, [[296 / 344, 'rgba(20,10,5,0.35)'], [0.93, 'rgba(20,10,5,0)'], [1, 'rgba(255,220,180,0.12)']]);
  ctx.fillRect(x - 350, y - 350, 700, 700);
  ctx.fillStyle = linear(ctx, x - 340, y - 340, x + 340, y + 340, [[0, 'rgba(20,10,5,0.25)'], [0.5, 'rgba(0,0,0,0)'], [1, 'rgba(255,190,130,0.16)']]);
  ctx.fillRect(x - 350, y - 350, 700, 700);
  // segment joints of the frame
  for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4 + Math.PI / 8; ctx.strokeStyle = 'rgba(30,18,10,0.55)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x + Math.cos(a) * 297, y + Math.sin(a) * 297); ctx.lineTo(x + Math.cos(a) * 343, y + Math.sin(a) * 343); ctx.stroke(); }
  ctx.restore();
  ctx.beginPath(); ctx.arc(x, y, 344, 0, 7); ctx.strokeStyle = 'rgba(30,18,10,0.6)'; ctx.lineWidth = 2.5; ctx.stroke();
}

function paintWindowLedge(ctx) {
  const x0 = 395, x1 = 905, y0 = 950;
  softEllipse(ctx, 650, 1000, 300, 34, 'rgba(20,12,8,0.45)', 'rgba(20,12,8,0)', 0.3);
  // top face
  ctx.beginPath(); ctx.moveTo(x0 + 6, y0); ctx.lineTo(x1 - 6, y0); ctx.lineTo(x1, y0 + 12); ctx.lineTo(x0, y0 + 12); ctx.closePath();
  ctx.fillStyle = linear(ctx, x0, 0, x1, 0, [[0, '#7c5a40'], [1, '#93694a']]); ctx.fill();
  // front face
  ctx.fillStyle = linear(ctx, 0, y0 + 12, 0, y0 + 36, [[0, '#6a4a34'], [1, '#4e3526']]); ctx.fillRect(x0, y0 + 12, x1 - x0, 24);
  ctx.fillStyle = 'rgba(255,215,170,0.18)'; ctx.fillRect(x0, y0 + 12, x1 - x0, 2);
  const r = rng(62); ctx.strokeStyle = 'rgba(35,22,14,0.35)'; ctx.lineWidth = 1;
  for (let i = 0; i < 8; i++) { const yy = y0 + 15 + r() * 18, xa = x0 + r() * 300; ctx.beginPath(); ctx.moveTo(xa, yy); ctx.lineTo(xa + 80 + r() * 160, yy + (r() - 0.5) * 2); ctx.stroke(); }
  // a little potted plant resting on the ledge
  const px = 838, py = y0 + 4;
  softEllipse(ctx, px, py + 2, 34, 6, 'rgba(20,12,8,0.4)');
  ctx.beginPath(); ctx.moveTo(px - 26, py - 44); ctx.lineTo(px + 26, py - 44); ctx.lineTo(px + 20, py); ctx.lineTo(px - 20, py); ctx.closePath();
  ctx.fillStyle = linear(ctx, px - 26, 0, px + 26, 0, [[0, '#8a5a40'], [0.6, '#a86e4c'], [1, '#7a4e37']]); ctx.fill();
  ctx.fillStyle = '#9a6446'; ctx.fillRect(px - 29, py - 50, 58, 9);
  const leaves = [[-0.9, 46], [-0.5, 58], [-0.15, 64], [0.25, 60], [0.6, 50], [0.95, 40], [-1.25, 34], [1.25, 32]];
  leaves.forEach(([a, L], i) => {
    const ang = -Math.PI / 2 + a * 0.75, bx = px + Math.cos(ang) * L, by = py - 48 + Math.sin(ang) * L;
    ctx.beginPath(); ctx.moveTo(px, py - 48);
    ctx.quadraticCurveTo(px + Math.cos(ang - 0.35) * L * 0.6, py - 48 + Math.sin(ang - 0.35) * L * 0.6, bx, by);
    ctx.quadraticCurveTo(px + Math.cos(ang + 0.35) * L * 0.6, py - 48 + Math.sin(ang + 0.35) * L * 0.6, px, py - 48);
    ctx.fillStyle = i % 2 ? '#6f7d55' : '#5e6b48'; ctx.fill();
  });
}

function paintShelves(ctx) {
  const r = rng(71);
  const boards = [520, 700, 880];
  const books = (x, yb, list) => {
    let xx = x;
    for (const [w, h, col, lean] of list) {
      ctx.save(); ctx.translate(xx + (lean > 0 ? w : 0), yb); ctx.rotate(lean || 0);
      const ox = lean > 0 ? -w : 0;
      ctx.fillStyle = col; ctx.fillRect(ox, -h, w, h);
      ctx.fillStyle = linear(ctx, ox, 0, ox + w, 0, [[0, 'rgba(255,240,220,0.15)'], [0.3, 'rgba(0,0,0,0)'], [1, 'rgba(20,10,5,0.3)']]); ctx.fillRect(ox, -h, w, h);
      ctx.fillStyle = 'rgba(230,205,150,0.45)'; ctx.fillRect(ox + 2, -h + 12, w - 4, 3); ctx.fillRect(ox + 2, -18, w - 4, 3);
      ctx.restore();
      xx += w + (lean ? 8 : 1);
    }
    return xx;
  };
  const jar = (x, yb, w, h, flower) => {
    // dried flowers
    const fr = rng(Math.floor(x * 7 + yb));
    for (let i = 0; i < 9; i++) {
      const a = -Math.PI / 2 + (fr() - 0.5) * 1.1, L = h * (0.9 + fr() * 0.9);
      const ex = x + Math.cos(a) * L * 0.6, ey = yb - h * 0.6 + Math.sin(a) * L;
      ctx.strokeStyle = '#7d7a55'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(x + (fr() - 0.5) * w * 0.4, yb - h * 0.5); ctx.quadraticCurveTo(x + (ex - x) * 0.3, ey + 30, ex, ey); ctx.stroke();
      ctx.fillStyle = flower[i % flower.length];
      for (let k = 0; k < 4; k++) { ctx.beginPath(); ctx.arc(ex + (fr() - 0.5) * 9, ey + (fr() - 0.5) * 9, 3 + fr() * 2.5, 0, 7); ctx.fill(); }
    }
    // glass jar
    ctx.beginPath(); ctx.moveTo(x - w / 2 + 6, yb - h); ctx.lineTo(x + w / 2 - 6, yb - h);
    ctx.quadraticCurveTo(x + w / 2, yb - h + 6, x + w / 2, yb - h * 0.75); ctx.lineTo(x + w / 2, yb - 4);
    ctx.quadraticCurveTo(x + w / 2, yb, x + w / 2 - 6, yb); ctx.lineTo(x - w / 2 + 6, yb); ctx.quadraticCurveTo(x - w / 2, yb, x - w / 2, yb - 4);
    ctx.lineTo(x - w / 2, yb - h * 0.75); ctx.quadraticCurveTo(x - w / 2, yb - h + 6, x - w / 2 + 6, yb - h); ctx.closePath();
    ctx.fillStyle = 'rgba(200,215,205,0.22)'; ctx.fill();
    ctx.strokeStyle = 'rgba(230,240,230,0.35)'; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.fillStyle = 'rgba(255,250,240,0.35)'; ctx.fillRect(x - w / 2 + 5, yb - h * 0.7, 4, h * 0.55);
    ctx.fillStyle = 'rgba(150,170,160,0.25)'; ctx.fillRect(x - w / 2 + 2, yb - h * 0.35, w - 4, h * 0.33);
  };
  const frame = (x, yb, w, h, inner) => {
    ctx.save(); ctx.translate(x, yb); ctx.rotate(-0.05);
    ctx.fillStyle = '#5a3e2c'; ctx.fillRect(-w / 2, -h, w, h);
    ctx.fillStyle = '#c9b48f'; ctx.fillRect(-w / 2 + 7, -h + 7, w - 14, h - 14);
    inner(w - 20, h - 20, -h + 10);
    ctx.strokeStyle = 'rgba(255,220,170,0.2)'; ctx.lineWidth = 1.5; ctx.strokeRect(-w / 2 + 1, -h + 1, w - 2, h - 2);
    ctx.restore();
    softEllipse(ctx, x + 4, yb - 2, w * 0.6, 5, 'rgba(20,12,8,0.35)');
  };
  // brackets + boards
  for (const by of boards) {
    softEllipse(ctx, 1110, by + 30, 150, 36, 'rgba(20,12,8,0.4)', 'rgba(20,12,8,0)', 0.2);
    for (const bx of [1030, 1190]) {
      ctx.fillStyle = '#2f2622'; ctx.beginPath(); ctx.moveTo(bx - 4, by); ctx.lineTo(bx + 4, by); ctx.lineTo(bx + 4, by + 50); ctx.quadraticCurveTo(bx, by + 20, bx - 4, by + 8); ctx.closePath(); ctx.fill();
    }
  }
  // shelf 1
  let x = books(1008, 520, [[18, 112, '#6d4b3a', 0], [22, 120, '#5d6a5c', 0], [16, 98, '#8b6a45', 0], [20, 108, '#4f5a66', 0], [18, 100, '#7a5048', 0.2]]);
  jar(1172, 520, 50, 72, ['#b98a8a', '#c7a46a', '#9d8aa8']);
  // shelf 2
  frame(1042, 700, 60, 78, (w, h, y0) => {
    ctx.fillStyle = '#e4d3b2'; ctx.fillRect(-w / 2, y0, w, h);
    ctx.fillStyle = '#9fb0a8'; ctx.fillRect(-w / 2, y0, w, h * 0.45);
    ctx.fillStyle = '#7b5a4a'; ctx.beginPath(); ctx.arc(-6, y0 + h * 0.48, 8, 0, 7); ctx.fill();
    ctx.fillStyle = '#6b4d5a'; ctx.beginPath(); ctx.ellipse(-6, y0 + h, 13, 18, 0, Math.PI, 0); ctx.fill();
    ctx.fillStyle = '#5a4a40'; ctx.beginPath(); ctx.arc(10, y0 + h * 0.55, 6, 0, 7); ctx.fill();
    ctx.fillStyle = '#6a7a8a'; ctx.beginPath(); ctx.ellipse(10, y0 + h, 9, 14, 0, Math.PI, 0); ctx.fill();
  });
  jar(1105, 700, 34, 48, ['#d0b07a', '#c49a9a']);
  // horizontal stack
  [[1140, 1216, 18, '#6a5242'], [1144, 1212, 15, '#7c8268'], [1138, 1214, 17, '#8a6a4c'], [1146, 1208, 14, '#5c5560']].reduce((yb, [a, b, h, c]) => {
    ctx.fillStyle = c; ctx.fillRect(a, yb - h, b - a, h);
    ctx.fillStyle = 'rgba(230,210,170,0.35)'; ctx.fillRect(a, yb - h + 2, 3, h - 4);
    ctx.fillStyle = 'rgba(20,10,5,0.22)'; ctx.fillRect(a, yb - 3, b - a, 3);
    return yb - h;
  }, 700);
  // shelf 3
  x = books(1006, 880, [[20, 96, '#7c6650', 0], [17, 104, '#55606b', 0], [23, 92, '#8c5d46', 0], [15, 100, '#6e7458', 0], [20, 88, '#9a845c', -0.16]]);
  frame(1180, 880, 54, 66, (w, h, y0) => {
    ctx.fillStyle = '#d9c6a2'; ctx.fillRect(-w / 2, y0, w, h);
    ctx.fillStyle = '#b5a07d'; ctx.fillRect(-w / 2, y0 + h * 0.6, w, h * 0.4);
    ctx.fillStyle = '#8a8fa0'; ctx.beginPath(); ctx.arc(0, y0 + h * 0.42, 9, 0, 7); ctx.fill();
    ctx.fillStyle = '#7b3b55'; ctx.beginPath(); ctx.ellipse(0, y0 + h, 14, 20, 0, Math.PI, 0); ctx.fill();
  });
  void x; void r;
  // boards on top of everything (front edges)
  for (const by of boards) {
    ctx.fillStyle = linear(ctx, 0, by, 0, by + 18, [[0, '#8d6648'], [0.25, '#6e4e37'], [1, '#4f3727']]);
    ctx.fillRect(998, by, 228, 18);
    ctx.fillStyle = 'rgba(255,215,170,0.2)'; ctx.fillRect(998, by, 228, 2);
  }
}

function paintChimneyBreast(ctx, tex) {
  const x0 = 1288, x1 = 1762;
  const topAt = x => yC(x) - 4;
  ctx.save();
  ctx.beginPath(); ctx.moveTo(x0 - 18, 1000); ctx.lineTo(x0 - 18, topAt(x0 - 18));
  for (let x = x0; x <= x1 + 18; x += 20) ctx.lineTo(x, topAt(x)); ctx.lineTo(x1 + 18, 1000); ctx.closePath(); ctx.clip();
  ctx.fillStyle = '#3d3430'; ctx.fillRect(x0 - 20, 0, x1 - x0 + 40, 1000);
  stoneCourses(ctx, { x0: x0 - 30, x1: x1 + 30, v0: 60, v1: 1000 },
    { seed: 81, hMin: 54, hMax: 78, wMin: 90, wMax: 165, inset: 4, base: [98, 86, 78], warp: false, hueVar: 8, chip: 0.3 });
  tile(ctx, tex.grit, x0 - 20, 0, x1 + 20, 1000, 300, 'overlay', 0.45);
  // smoky soot: darker up the centre, lit warm from the mantel candle/fire below
  ctx.fillStyle = linear(ctx, 0, 100, 0, 1000, [[0, 'rgba(18,12,10,0.55)'], [0.6, 'rgba(18,12,10,0.25)'], [1, 'rgba(18,12,10,0.05)']]);
  ctx.fillRect(x0 - 20, 0, x1 - x0 + 40, 1000);
  softEllipse(ctx, 1525, 600, 260, 420, 'rgba(15,10,8,0.3)', 'rgba(15,10,8,0)');
  // side returns of the breast (depth)
  ctx.fillStyle = linear(ctx, x0 - 18, 0, x0, 0, [[0, 'rgba(15,10,8,0.65)'], [1, 'rgba(15,10,8,0.2)']]); ctx.fillRect(x0 - 18, 0, 18, 1000);
  ctx.fillStyle = linear(ctx, x1, 0, x1 + 18, 0, [[0, 'rgba(255,190,130,0.08)'], [1, 'rgba(255,190,130,0.18)']]); ctx.fillRect(x1, 0, 18, 1000);
  ctx.restore();
  // cast shadow of breast on wall to the left
  ctx.fillStyle = linear(ctx, x0 - 70, 0, x0 - 18, 0, [[0, 'rgba(20,12,8,0)'], [1, 'rgba(20,12,8,0.35)']]);
  ctx.fillRect(x0 - 70, 120, 52, 880);
}

function paintHearth(ctx, tex) {
  const r = rng(91);
  // surround backing (soft shadow around)
  softEllipse(ctx, 1525, 1240, 360, 320, 'rgba(20,12,8,0.35)', 'rgba(20,12,8,0)', 0.7);
  ctx.save();
  ctx.beginPath(); ctx.rect(1250, 1000, 550, 472); fireboxPath(ctx, -2, true); ctx.clip('evenodd');
  ctx.fillStyle = '#4e4339'; ctx.fillRect(1250, 1000, 550, 472);
  // dressed stone piers + lintel blocks
  const pier = (xa, xb, seed) => {
    const rr = rng(seed); let y = 1000; let alt = 0;
    while (y < 1470) {
      const h = 58 + rr() * 22, y2 = Math.min(1470, y + h);
      if (alt % 2 === 0) drawStone(ctx, rr, xa, y, xb, y2, { inset: 3, base: [150, 134, 114], n: 6, jit: 0.025, hueVar: 10, chip: 0.5 });
      else { const m = lerp(xa, xb, 0.4 + rr() * 0.2); drawStone(ctx, rr, xa, y, m, y2, { inset: 3, base: [150, 134, 114], n: 6, jit: 0.025, chip: 0.5 }); drawStone(ctx, rr, m, y, xb, y2, { inset: 3, base: [150, 134, 114], n: 6, jit: 0.025, chip: 0.5 }); }
      y = y2; alt++;
    }
  };
  pier(1250, 1372, 92); pier(1678, 1800, 93);
  // lintel band above the arch
  let x = 1372;
  while (x < 1678) { const w = 70 + r() * 40; drawStone(ctx, r, x, 1000, Math.min(1678, x + w), 1062, { inset: 3, base: [146, 130, 110], n: 6, jit: 0.025 }); x += w; }
  // arch voussoirs
  const n = 11, R0 = FB.r, R1 = FB.r + 62;
  for (let i = 0; i < n; i++) {
    const a0 = Math.PI + (i / n) * Math.PI + 0.012, a1 = Math.PI + ((i + 1) / n) * Math.PI - 0.012;
    const key = i === (n - 1) / 2; const ro = key ? R1 + 14 : R1;
    ctx.beginPath(); ctx.arc(FB.cx, FB.spring, ro, a0, a1); ctx.arc(FB.cx, FB.spring, R0, a1, a0, true); ctx.closePath();
    const k = 0.9 + r() * 0.2; ctx.fillStyle = rgba(156 * k, 140 * k, 120 * k); ctx.fill();
    ctx.fillStyle = radial(ctx, FB.cx, FB.spring, ro, [[R0 / ro, 'rgba(25,15,10,0.35)'], [(R0 + 18) / ro, 'rgba(25,15,10,0)'], [1, 'rgba(255,240,220,0.08)']]); ctx.fill();
    ctx.strokeStyle = 'rgba(45,32,24,0.55)'; ctx.lineWidth = 2; ctx.stroke();
  }
  tile(ctx, tex.grit, 1250, 1000, 1800, 1480, 300, 'overlay', 0.5);
  // soot licking up from the opening
  softEllipse(ctx, 1525, 1080, 190, 150, 'rgba(18,12,10,0.55)', 'rgba(18,12,10,0)');
  ctx.restore();

  // firebox interior
  ctx.save(); fireboxPath(ctx); ctx.clip();
  ctx.fillStyle = '#1d1512'; ctx.fillRect(FB.x0, FB.y0, FB.x1 - FB.x0, FB.y1 - FB.y0);
  // back wall bricks (inner panel)
  const bx0 = 1428, bx1 = 1622, by0 = 1150;
  ctx.fillStyle = '#0e0908'; ctx.fillRect(bx0, by0, bx1 - bx0, 1450 - by0);
  const br = rng(94);
  for (let y = by0, row = 0; y < 1450; y += 26, row++) {
    for (let xx = bx0 - (row % 2) * 30; xx < bx1; xx += 60) {
      const k = 0.75 + br() * 0.5; ctx.fillStyle = rgba(62 * k, 40 * k, 32 * k); ctx.fillRect(xx + 2, y + 2, 56, 22);
    }
  }
  // side walls in perspective
  ctx.beginPath(); ctx.moveTo(FB.x0, FB.y1); ctx.lineTo(bx0, 1448); ctx.lineTo(bx0, by0); ctx.lineTo(FB.x0, FB.y0 - 40); ctx.closePath();
  ctx.fillStyle = 'rgba(20,14,12,0.85)'; ctx.fill();
  ctx.beginPath(); ctx.moveTo(FB.x1, FB.y1); ctx.lineTo(bx1, 1448); ctx.lineTo(bx1, by0); ctx.lineTo(FB.x1, FB.y0 - 40); ctx.closePath();
  ctx.fillStyle = 'rgba(32,22,17,0.85)'; ctx.fill();
  // soot gradient toward the top of the throat
  ctx.fillStyle = linear(ctx, 0, FB.y0, 0, 1300, [[0, 'rgba(8,5,4,0.95)'], [1, 'rgba(8,5,4,0)']]); ctx.fillRect(FB.x0, FB.y0, 320, 200);
  // ash bed
  ctx.fillStyle = linear(ctx, 0, 1440, 0, 1472, [[0, '#3a302b'], [1, '#55483f']]); ctx.beginPath(); ctx.moveTo(bx0, 1446); ctx.lineTo(bx1, 1446); ctx.lineTo(FB.x1, 1472); ctx.lineTo(FB.x0, 1472); ctx.closePath(); ctx.fill();
  ctx.restore();

  // hearthstone slab
  softEllipse(ctx, 1525, 1545, 330, 22, 'rgba(20,12,8,0.5)', 'rgba(20,12,8,0)', 0.6);
  ctx.beginPath(); ctx.moveTo(1238, 1470); ctx.lineTo(1812, 1470); ctx.lineTo(1826, 1514); ctx.lineTo(1224, 1514); ctx.closePath();
  ctx.fillStyle = linear(ctx, 1224, 0, 1826, 0, [[0, '#76695c'], [0.5, '#8e7e6c'], [1, '#7f705f']]); ctx.fill();
  ctx.save(); ctx.clip(); tile(ctx, tex.grit, 1220, 1460, 1830, 1520, 300, 'overlay', 0.6);
  ctx.strokeStyle = 'rgba(40,28,20,0.5)'; ctx.lineWidth = 2;
  for (const sx of [1420, 1640]) { ctx.beginPath(); ctx.moveTo(sx, 1470); ctx.lineTo(sx + (sx - 800) * 0.03, 1514); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(40,28,20,0.3)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(1300, 1478); ctx.lineTo(1340, 1490); ctx.lineTo(1352, 1506); ctx.stroke();
  ctx.restore();
  ctx.fillStyle = linear(ctx, 0, 1514, 0, 1542, [[0, '#62564a'], [1, '#463c33']]);
  ctx.beginPath(); ctx.moveTo(1224, 1514); ctx.lineTo(1826, 1514); ctx.lineTo(1826, 1540); ctx.lineTo(1224, 1540); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,220,180,0.15)'; ctx.fillRect(1224, 1514, 602, 2);

  // mantel shelf (heavy timber)
  softEllipse(ctx, 1525, 1012, 330, 26, 'rgba(15,9,6,0.55)', 'rgba(15,9,6,0)', 0.4);
  ctx.fillStyle = linear(ctx, 0, 958, 0, 1002, [[0, '#7a573d'], [0.12, '#6a4a33'], [0.8, '#4c3424'], [1, '#3a281c']]);
  ctx.fillRect(1222, 958, 606, 44);
  ctx.fillStyle = 'rgba(255,215,170,0.2)'; ctx.fillRect(1222, 958, 606, 2);
  ctx.strokeStyle = 'rgba(25,15,10,0.35)'; ctx.lineWidth = 1.4;
  for (let i = 0; i < 12; i++) { const yy = 966 + r() * 30, xa = 1225 + r() * 450; ctx.beginPath(); ctx.moveTo(xa, yy); ctx.bezierCurveTo(xa + 50, yy + 3, xa + 100, yy - 3, xa + 120 + r() * 120, yy + (r() - 0.5) * 3); ctx.stroke(); }
  // end grain
  for (const ex of [1222, 1822]) { ctx.fillStyle = 'rgba(30,18,12,0.35)'; ctx.fillRect(ex, 958, 6, 44); }
  // iron hook for the bellows on the left pier
  ctx.strokeStyle = '#2a2420'; ctx.lineWidth = 6; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(1300, 1118); ctx.lineTo(1300, 1134); ctx.quadraticCurveTo(1300, 1146, 1310, 1142); ctx.stroke();
  ctx.fillStyle = '#2a2420'; ctx.beginPath(); ctx.arc(1300, 1116, 7, 0, 7); ctx.fill();
  ctx.lineCap = 'butt';
}

function paintMantelObjects(ctx) {
  const y = 958;
  // framed photo of Nana
  ctx.save(); ctx.translate(1340, y); ctx.rotate(-0.04);
  softEllipse(ctx, 6, -2, 52, 6, 'rgba(15,9,6,0.45)');
  ctx.fillStyle = '#4a3324'; ctx.fillRect(-46, -118, 92, 118);
  ctx.fillStyle = linear(ctx, -46, -118, 46, 0, [[0, '#6b4c35'], [1, '#3e2a1d']]); ctx.fillRect(-42, -114, 84, 110);
  ctx.fillStyle = '#d8c7a4'; ctx.fillRect(-33, -105, 66, 92);
  ctx.save(); ctx.beginPath(); ctx.rect(-33, -105, 66, 92); ctx.clip();
  ctx.fillStyle = linear(ctx, 0, -105, 0, -13, [[0, '#cbb894'], [1, '#a99474']]); ctx.fillRect(-33, -105, 66, 92);
  ctx.fillStyle = '#c4c4c8'; ctx.beginPath(); ctx.arc(0, -70, 17, 0, 7); ctx.fill();            // silver hair
  ctx.fillStyle = '#a8785a'; ctx.beginPath(); ctx.ellipse(0, -66, 12, 14, 0, 0, 7); ctx.fill();  // face
  ctx.fillStyle = '#d0d0d4'; ctx.beginPath(); ctx.ellipse(0, -80, 15, 8, 0, Math.PI, 0); ctx.fill();
  ctx.fillStyle = '#7b3b55'; ctx.beginPath(); ctx.ellipse(0, -18, 28, 34, 0, Math.PI, 0); ctx.fill(); // plum cardigan
  ctx.fillStyle = '#efe6d2'; ctx.beginPath(); ctx.moveTo(-6, -50); ctx.lineTo(6, -50); ctx.lineTo(0, -34); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,240,210,0.12)'; ctx.fillRect(-33, -105, 30, 92);
  ctx.restore();
  ctx.restore();
  // small mantel clock
  const cx = 1610;
  softEllipse(ctx, cx + 6, y - 1, 48, 5, 'rgba(15,9,6,0.45)');
  ctx.fillStyle = '#5c3f2b'; ctx.fillRect(cx - 44, y - 14, 88, 14);
  ctx.beginPath(); ctx.moveTo(cx - 36, y - 14); ctx.lineTo(cx - 36, y - 60); ctx.arc(cx, y - 60, 36, Math.PI, 0); ctx.lineTo(cx + 36, y - 14); ctx.closePath();
  ctx.fillStyle = linear(ctx, cx - 36, 0, cx + 36, 0, [[0, '#4e3524'], [0.6, '#76533a'], [1, '#5a3d29']]); ctx.fill();
  ctx.fillStyle = '#b08d55'; ctx.beginPath(); ctx.arc(cx, y - 58, 25, 0, 7); ctx.fill();
  ctx.fillStyle = '#ede0c4'; ctx.beginPath(); ctx.arc(cx, y - 58, 21, 0, 7); ctx.fill();
  ctx.strokeStyle = '#3a2c22'; ctx.lineWidth = 1.2;
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; ctx.beginPath(); ctx.moveTo(cx + Math.cos(a) * 17, y - 58 + Math.sin(a) * 17); ctx.lineTo(cx + Math.cos(a) * 20, y - 58 + Math.sin(a) * 20); ctx.stroke(); }
  ctx.lineWidth = 2.2; ctx.beginPath(); ctx.moveTo(cx, y - 58); ctx.lineTo(cx - 8, y - 68); ctx.stroke();
  ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(cx, y - 58); ctx.lineTo(cx + 13, y - 52); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.beginPath(); ctx.ellipse(cx - 7, y - 66, 8, 4, -0.6, 0, 7); ctx.fill();
  // candle in a brass holder
  const kx = 1730;
  softEllipse(ctx, kx + 4, y - 1, 30, 4, 'rgba(15,9,6,0.45)');
  ctx.fillStyle = linear(ctx, kx - 26, 0, kx + 26, 0, [[0, '#7a5a2c'], [0.45, '#c79a52'], [1, '#6e4f26']]);
  ctx.beginPath(); ctx.ellipse(kx, y - 4, 26, 6, 0, 0, 7); ctx.fill(); ctx.fillRect(kx - 26, y - 8, 52, 4);
  ctx.fillRect(kx - 6, y - 26, 12, 20); ctx.beginPath(); ctx.ellipse(kx, y - 27, 14, 4, 0, 0, 7); ctx.fill();
  ctx.fillStyle = linear(ctx, kx - 11, 0, kx + 11, 0, [[0, '#d8ccb0'], [0.5, '#f3ead6'], [1, '#c9bb9c']]); ctx.fillRect(kx - 11, y - 96, 22, 70);
  ctx.beginPath(); ctx.ellipse(kx, y - 96, 11, 3, 0, 0, 7); ctx.fillStyle = '#e9dcc0'; ctx.fill();
  ctx.fillStyle = '#f3ead6'; ctx.beginPath(); ctx.moveTo(kx + 6, y - 96); ctx.quadraticCurveTo(kx + 13, y - 86, kx + 11, y - 74); ctx.lineTo(kx + 9, y - 92); ctx.fill(); // drip
  ctx.strokeStyle = '#2a2018'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(kx, y - 96); ctx.lineTo(kx + 1, y - 104); ctx.stroke();
}

function paintDoorSurround(ctx, tex) {
  const r = rng(101); const cx = 200;
  softEllipse(ctx, cx, 1200, 260, 380, 'rgba(20,12,8,0.3)', 'rgba(20,12,8,0)', 0.7);
  // jamb stones
  const jamb = (xa, xb, seed) => { const rr = rng(seed); let y = DOOR.spring; let i = 0; while (y < 1478) { const h = 70 + rr() * 30, y2 = Math.min(1478, y + h); const w = i % 2 ? 0 : 14; drawStone(ctx, rr, xa - (xa < cx ? w : 0), y, xb + (xb > cx ? w : 0), y2, { inset: 3, base: [132, 118, 101], n: 6, jit: 0.03 }); y = y2; i++; } };
  jamb(12, 64, 102); jamb(336, 388, 103);
  const n = 9, R0 = 138, R1 = 196;
  for (let i = 0; i < n; i++) {
    const a0 = Math.PI + (i / n) * Math.PI + 0.015, a1 = Math.PI + ((i + 1) / n) * Math.PI - 0.015;
    ctx.beginPath(); ctx.arc(cx, DOOR.spring, R1 + (i === 4 ? 12 : 0), a0, a1); ctx.arc(cx, DOOR.spring, R0, a1, a0, true); ctx.closePath();
    const k = 0.9 + r() * 0.2; ctx.fillStyle = rgba(134 * k, 120 * k, 103 * k); ctx.fill();
    ctx.strokeStyle = 'rgba(45,32,24,0.55)'; ctx.lineWidth = 2; ctx.stroke();
  }
  ctx.save(); ctx.beginPath(); ctx.arc(cx, DOOR.spring, 212, Math.PI, 0); ctx.rect(4, DOOR.spring, 392, 470); ctx.clip();
  tile(ctx, tex.grit, 0, 800, 400, 1480, 300, 'overlay', 0.5); ctx.restore();
  // timber lining inside the opening
  ctx.beginPath(); ctx.moveTo(DOOR.x0 - 10, DOOR.y1); ctx.lineTo(DOOR.x0 - 10, DOOR.spring); ctx.arc(cx, DOOR.spring, 150, Math.PI, 0); ctx.lineTo(DOOR.x1 + 10, DOOR.y1);
  ctx.lineTo(DOOR.x1, DOOR.y1); ctx.lineTo(DOOR.x1, DOOR.spring); ctx.arc(cx, DOOR.spring, 140, 0, Math.PI, true); ctx.lineTo(DOOR.x0, DOOR.y1); ctx.closePath();
  ctx.fillStyle = '#4a3324'; ctx.fill();
  // threshold stone
  ctx.fillStyle = linear(ctx, 0, 1474, 0, 1500, [[0, '#8a7b6a'], [1, '#5a4e43']]); ctx.fillRect(36, 1474, 328, 24);
  ctx.fillStyle = 'rgba(255,230,200,0.15)'; ctx.fillRect(36, 1474, 328, 2);
}

function paintRightSide(ctx) {
  // fire-tool stand
  const sx = 1860, sb = 1580;
  softEllipse(ctx, sx + 10, sb + 2, 46, 9, 'rgba(15,9,6,0.5)');
  ctx.strokeStyle = '#2b2522'; ctx.lineCap = 'round';
  ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(sx, sb - 8); ctx.lineTo(sx, sb - 330); ctx.stroke();
  ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(sx, sb - 340, 12, 0, 7); ctx.stroke();
  ctx.beginPath(); ctx.ellipse(sx, sb - 6, 34, 7, 0, 0, 7); ctx.fillStyle = '#2b2522'; ctx.fill();
  ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(sx - 26, sb - 300); ctx.lineTo(sx + 26, sb - 300); ctx.stroke();
  // poker + brush hanging
  ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(sx - 20, sb - 300); ctx.lineTo(sx - 22, sb - 60); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(sx - 22, sb - 60); ctx.lineTo(sx - 12, sb - 40); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(sx + 20, sb - 300); ctx.lineTo(sx + 21, sb - 110); ctx.stroke();
  ctx.fillStyle = '#5b4632'; ctx.beginPath(); ctx.ellipse(sx + 21, sb - 80, 13, 34, 0, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,190,130,0.25)'; ctx.fillRect(sx - 24, sb - 300, 2, 240);
  ctx.lineCap = 'butt';
  // log basket
  const bx = 1960, bb = 1660;
  softEllipse(ctx, bx, bb + 4, 130, 18, 'rgba(15,9,6,0.55)', 'rgba(15,9,6,0)', 0.4);
  const r = rng(111);
  // logs inside
  for (let i = 0; i < 6; i++) {
    const lx = bx - 80 + i * 30 + r() * 8, ly = bb - 120 - r() * 30 - (i % 2) * 14;
    ctx.save(); ctx.translate(lx, ly); ctx.rotate((r() - 0.5) * 0.5);
    ctx.fillStyle = linear(ctx, -16, 0, 16, 0, [[0, '#4a3324'], [0.5, '#6e5038'], [1, '#3e2a1d']]); ctx.fillRect(-16, -30, 32, 90);
    ctx.fillStyle = '#b59870'; ctx.beginPath(); ctx.ellipse(0, -30, 16, 7, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(90,60,40,0.6)'; ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(0, -30, 9, 4, 0, 0, 7); ctx.stroke();
    ctx.restore();
  }
  // wicker basket
  ctx.beginPath(); ctx.moveTo(bx - 115, bb - 120); ctx.lineTo(bx + 115, bb - 120); ctx.lineTo(bx + 100, bb); ctx.lineTo(bx - 100, bb); ctx.closePath();
  ctx.fillStyle = linear(ctx, bx - 115, 0, bx + 115, 0, [[0, '#6e5236'], [0.35, '#8e6c47'], [1, '#5c432c']]); ctx.fill();
  ctx.save(); ctx.clip();
  for (let y = bb - 118; y < bb; y += 12) for (let x = bx - 120; x < bx + 120; x += 18) {
    ctx.fillStyle = ((x + y) / 6) % 2 < 1 ? 'rgba(30,18,10,0.22)' : 'rgba(255,220,170,0.08)';
    ctx.beginPath(); ctx.ellipse(x + ((y / 12) % 2) * 9, y + 6, 9, 5, 0, 0, 7); ctx.fill();
  }
  ctx.restore();
  ctx.fillStyle = '#7a5b3c'; ctx.beginPath(); ctx.ellipse(bx, bb - 120, 116, 10, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#5a412b'; ctx.beginPath(); ctx.ellipse(bx, bb - 120, 104, 6, 0, 0, Math.PI); ctx.fill();
}

function paintLeftSide(ctx) {
  // wooden peg rail with a knitted scarf
  const py = 1000;
  ctx.fillStyle = linear(ctx, 0, py - 12, 0, py + 12, [[0, '#6e4e37'], [1, '#4a3324']]); ctx.fillRect(-430, py - 12, 300, 24);
  softEllipse(ctx, -280, py + 20, 160, 14, 'rgba(15,9,6,0.35)');
  for (const x of [-390, -280, -170]) { ctx.fillStyle = '#5a3e2b'; ctx.beginPath(); ctx.ellipse(x, py + 2, 9, 7, 0, 0, 7); ctx.fill(); }
  // scarf on the middle peg
  const sx = -280;
  const strip = (x0, w, L, sway, seed) => {
    const rr = rng(seed);
    ctx.beginPath(); ctx.moveTo(x0, py + 4); ctx.bezierCurveTo(x0 + sway, py + L * 0.4, x0 - sway * 0.5, py + L * 0.7, x0 + sway * 0.3, py + L);
    ctx.lineTo(x0 + w + sway * 0.3, py + L); ctx.bezierCurveTo(x0 + w - sway * 0.5, py + L * 0.7, x0 + w + sway, py + L * 0.4, x0 + w, py + 4); ctx.closePath();
    ctx.fillStyle = '#8a8f6e'; ctx.fill();
    ctx.save(); ctx.clip();
    for (let y = py; y < py + L; y += 46) { ctx.fillStyle = '#b6a27e'; ctx.fillRect(x0 - 40, y + 22, w + 80, 12); }
    for (let y = py; y < py + L; y += 7) for (let x = x0 - 30; x < x0 + w + 30; x += 8) { ctx.fillStyle = 'rgba(30,25,15,0.12)'; ctx.beginPath(); ctx.ellipse(x + ((y / 7) % 2) * 4, y, 3, 2.5, 0.5, 0, 7); ctx.fill(); }
    ctx.fillStyle = linear(ctx, x0, 0, x0 + w, 0, [[0, 'rgba(20,12,8,0.3)'], [0.5, 'rgba(0,0,0,0)'], [1, 'rgba(20,12,8,0.2)']]); ctx.fillRect(x0 - 40, py, w + 80, L);
    ctx.restore();
    // fringe
    ctx.strokeStyle = '#7a7f60'; ctx.lineWidth = 2;
    for (let i = 0; i < 7; i++) { const fx = x0 + sway * 0.3 + i * w / 6; ctx.beginPath(); ctx.moveTo(fx, py + L); ctx.lineTo(fx + (rr() - 0.5) * 4, py + L + 16 + rr() * 6); ctx.stroke(); }
  };
  softEllipse(ctx, sx + 10, py + 200, 60, 200, 'rgba(15,9,6,0.25)');
  strip(sx - 34, 40, 330, 8, 1); strip(sx - 2, 42, 280, -6, 2);
  ctx.fillStyle = '#7e8364'; ctx.beginPath(); ctx.ellipse(sx, py + 6, 40, 14, 0, 0, 7); ctx.fill();
}

function paintCorner(ctx) {
  // lantern (unlit body; lit glow added dynamically)
  const lx = -170, lb = 1632;
  softEllipse(ctx, lx + 6, lb + 2, 40, 8, 'rgba(15,9,6,0.5)');
  ctx.fillStyle = '#2e2622'; ctx.fillRect(lx - 30, lb - 12, 60, 12);
  ctx.fillStyle = 'rgba(160,140,110,0.35)'; ctx.fillRect(lx - 24, lb - 92, 48, 80);
  ctx.strokeStyle = '#2e2622'; ctx.lineWidth = 4; ctx.strokeRect(lx - 24, lb - 92, 48, 80);
  ctx.beginPath(); ctx.moveTo(lx, lb - 92); ctx.lineTo(lx, lb - 12); ctx.stroke();
  ctx.fillStyle = '#e8dcc0'; ctx.fillRect(lx - 7, lb - 46, 14, 34);
  ctx.beginPath(); ctx.moveTo(lx - 32, lb - 92); ctx.lineTo(lx, lb - 118); ctx.lineTo(lx + 32, lb - 92); ctx.closePath(); ctx.fillStyle = '#2e2622'; ctx.fill();
  ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(lx, lb - 126, 9, 0, 7); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.15)'; ctx.fillRect(lx - 20, lb - 88, 6, 70);

  // folded knitted blanket (behind-left)
  const bx = 20, bb = 1668, bw = 104, fh = 58, tw = 22;
  softEllipse(ctx, bx + 6, bb + 4, 125, 18, 'rgba(15,9,6,0.55)', 'rgba(15,9,6,0)', 0.3);
  const knit = (x0, y0, x1, y1, col) => {
    ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, x1 - x0, y1 - y0); ctx.clip();
    ctx.strokeStyle = col; ctx.lineWidth = 1.6;
    for (let x = x0 + 3; x < x1; x += 8) for (let y = y0 + 2; y < y1; y += 6) { ctx.beginPath(); ctx.moveTo(x - 3, y); ctx.lineTo(x, y + 4); ctx.lineTo(x + 3, y); ctx.stroke(); }
    ctx.restore();
  };
  // top face
  ctx.beginPath(); ctx.moveTo(bx - bw + 8, bb - fh - tw); ctx.lineTo(bx + bw - 4, bb - fh - tw); ctx.lineTo(bx + bw + 2, bb - fh); ctx.lineTo(bx - bw, bb - fh); ctx.closePath();
  ctx.fillStyle = '#cbbb9b'; ctx.fill();
  ctx.save(); ctx.clip(); knit(bx - bw, bb - fh - tw, bx + bw + 4, bb - fh, 'rgba(110,92,66,0.28)');
  ctx.fillStyle = 'rgba(122,132,100,0.75)'; ctx.fillRect(bx + bw - 30, bb - fh - tw, 12, tw); ctx.restore();
  // front face with three folded layers
  ctx.beginPath(); ctx.moveTo(bx - bw, bb - fh); ctx.lineTo(bx + bw + 2, bb - fh); ctx.lineTo(bx + bw + 2, bb - 4); ctx.quadraticCurveTo(bx + bw + 2, bb, bx + bw - 4, bb); ctx.lineTo(bx - bw + 4, bb); ctx.quadraticCurveTo(bx - bw, bb, bx - bw, bb - 4); ctx.closePath();
  ctx.fillStyle = '#b9a785'; ctx.fill();
  ctx.save(); ctx.clip();
  knit(bx - bw, bb - fh, bx + bw + 4, bb, 'rgba(95,78,55,0.3)');
  for (let k = 0; k < 3; k++) {
    const y0 = bb - fh + k * fh / 3, y1 = y0 + fh / 3;
    ctx.fillStyle = linear(ctx, 0, y0, 0, y1, [[0, 'rgba(255,245,225,0.16)'], [0.5, 'rgba(0,0,0,0)'], [1, 'rgba(40,28,18,0.32)']]); ctx.fillRect(bx - bw, y0, bw * 2 + 4, fh / 3);
  }
  ctx.fillStyle = 'rgba(122,132,100,0.7)'; ctx.fillRect(bx + bw - 30, bb - fh, 12, fh);
  ctx.fillStyle = linear(ctx, bx - bw, 0, bx + bw, 0, [[0, 'rgba(30,20,12,0.25)'], [0.4, 'rgba(0,0,0,0)'], [1, 'rgba(30,20,12,0.1)']]); ctx.fillRect(bx - bw, bb - fh, bw * 2 + 4, fh);
  ctx.restore();
  // stack of books resting on the folded blanket
  const kx = 6, kb = 1604;
  softEllipse(ctx, kx, kb + 1, 62, 6, 'rgba(15,9,6,0.4)');
  [[64, 18, '#6b5444', -0.02], [58, 15, '#7d8466', 0.03], [62, 17, '#8c6a4a', -0.04], [50, 13, '#5f5866', 0.06]].reduce((y, [w, h, c, a]) => {
    ctx.save(); ctx.translate(kx, y - h / 2); ctx.rotate(a);
    ctx.fillStyle = c; ctx.fillRect(-w, -h / 2, w * 2, h);
    ctx.fillStyle = '#e2d6bc'; ctx.fillRect(-w + 4, -h / 2 + 3, w * 2 - 6, h - 6); ctx.fillStyle = c; ctx.fillRect(-w, -h / 2, 6, h);
    ctx.fillStyle = 'rgba(20,12,8,0.25)'; ctx.fillRect(-w, h / 2 - 3, w * 2, 3);
    ctx.restore(); return y - h;
  }, kb);
  // worn, plump floor cushion (Sadness sits here, centre x 170)
  const cx = 170, cy = 1704, crx = 128, cry = 34, ch = 30;
  softEllipse(ctx, cx + 8, cy + ch + 4, crx + 26, 26, 'rgba(15,9,6,0.6)', 'rgba(15,9,6,0)', 0.3);
  // side wall
  ctx.beginPath(); ctx.ellipse(cx, cy, crx, cry, 0, 0, Math.PI); ctx.lineTo(cx - crx + 4, cy + 4);
  ctx.ellipse(cx, cy + ch - 6, crx - 4, cry, 0, Math.PI, 0, true); ctx.closePath();
  ctx.beginPath(); ctx.moveTo(cx - crx, cy); ctx.bezierCurveTo(cx - crx - 4, cy + ch * 0.6, cx - crx + 10, cy + ch, cx - crx + 30, cy + ch + 10);
  ctx.ellipse(cx, cy + ch - 2, crx - 8, cry * 0.95, 0, Math.PI * 0.84, Math.PI * 0.16, true);
  ctx.bezierCurveTo(cx + crx - 10, cy + ch, cx + crx + 4, cy + ch * 0.6, cx + crx, cy); ctx.closePath();
  ctx.fillStyle = linear(ctx, cx - crx, 0, cx + crx, 0, [[0, '#5e4840'], [0.5, '#7a6058'], [1, '#6a5249']]); ctx.fill();
  // top
  ctx.beginPath(); ctx.ellipse(cx, cy, crx, cry, 0, 0, Math.PI * 2);
  ctx.fillStyle = radial(ctx, cx + 25, cy - 12, crx * 1.05, [[0, '#a0847a'], [0.6, '#8d7168'], [1, '#76605a']]); ctx.fill();
  ctx.save(); ctx.clip();
  // tufts with soft creases
  const tufts = [[0, 0], [-62, -2], [62, 2], [-26, -18], [30, 16]];
  for (const [dx, dy] of tufts) {
    softEllipse(ctx, cx + dx, cy + dy, 26, 9, 'rgba(50,32,26,0.22)');
    ctx.fillStyle = '#5a443d'; ctx.beginPath(); ctx.ellipse(cx + dx, cy + dy, 4, 2.4, 0, 0, 7); ctx.fill();
    softEllipse(ctx, cx + dx - 10, cy + dy - 6, 14, 5, 'rgba(255,235,220,0.1)');
  }
  // worn patch where she always sits
  softEllipse(ctx, cx - 10, cy - 2, 70, 16, 'rgba(225,205,190,0.12)');
  ctx.restore();
  ctx.beginPath(); ctx.ellipse(cx, cy, crx, cry, 0, 0, Math.PI * 2); ctx.strokeStyle = 'rgba(200,175,160,0.4)'; ctx.lineWidth = 3; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(cx, cy + 1.5, crx, cry, 0, 0.1, Math.PI - 0.1); ctx.strokeStyle = 'rgba(40,25,20,0.35)'; ctx.lineWidth = 1.5; ctx.stroke();
  // cup of tea on the floor
  paintTeaCup(ctx, TEA.x, TEA.y);
}
const TEA = { x: 40, y: 1768 };
function paintTeaCup(ctx, x, y) {
  softEllipse(ctx, x + 4, y + 3, 52, 10, 'rgba(15,9,6,0.55)');
  ctx.fillStyle = '#d9cdb6'; ctx.beginPath(); ctx.ellipse(x, y, 46, 11, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#b9ad96'; ctx.beginPath(); ctx.ellipse(x, y - 2, 30, 6, 0, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.moveTo(x - 26, y - 44); ctx.bezierCurveTo(x - 26, y - 6, x - 16, y - 2, x, y - 2); ctx.bezierCurveTo(x + 16, y - 2, x + 26, y - 6, x + 26, y - 44); ctx.closePath();
  ctx.fillStyle = linear(ctx, x - 26, 0, x + 26, 0, [[0, '#cfc2a8'], [0.4, '#efe6d2'], [1, '#bfb298']]); ctx.fill();
  ctx.fillStyle = 'rgba(122,132,80,0.65)'; ctx.fillRect(x - 25, y - 32, 50, 4);
  ctx.strokeStyle = '#cfc2a8'; ctx.lineWidth = 5; ctx.beginPath(); ctx.ellipse(x + 30, y - 26, 9, 11, 0, -1.4, 1.4); ctx.stroke();
  ctx.fillStyle = '#e6dcc6'; ctx.beginPath(); ctx.ellipse(x, y - 44, 26, 6, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#8a5a34'; ctx.beginPath(); ctx.ellipse(x, y - 43, 22, 4.5, 0, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,220,170,0.25)'; ctx.beginPath(); ctx.ellipse(x + 6, y - 44, 8, 1.5, 0, 0, 7); ctx.fill();
}

function bakeLighting(ctx) {
  const W = EXT.x1 - EXT.x0 + 180, H = EXT.y1 - EXT.y0 + 180, X = EXT.x0 - 90, Y = EXT.y0 - 90;
  ctx.save();
  // ceiling falls into shadow
  ctx.globalCompositeOperation = 'multiply';
  ctx.fillStyle = linear(ctx, 0, -600, 0, 300, [[0, '#6e5e60'], [0.7, '#c8bab4'], [1, '#ffffff']]); ctx.fillRect(X, Y, W, 920);
  // vignette toward the edges of the round room
  ctx.save(); ctx.translate(820, 1150); ctx.scale(1, 1.25);
  ctx.fillStyle = radial(ctx, 0, 0, 1700, [[0, '#ffffff'], [0.42, '#f6eee6'], [0.75, '#a08e84'], [1, '#6e5c54']]);
  ctx.fillRect(-2000, -2000, 4000, 4000); ctx.restore();
  // front of floor darker (closer to camera, away from fire)
  ctx.fillStyle = linear(ctx, 0, 1850, 0, 2500, [[0, '#ffffff'], [1, '#8a7c80']]); ctx.fillRect(X, 1850, W, 670);
  // Sadness's corner: slightly shadowed even when lit (the dynamic layer adds the rest)
  ctx.save(); ctx.translate(120, 1680); ctx.scale(1, 0.6);
  ctx.fillStyle = radial(ctx, 0, 0, 520, [[0, '#d8ccd0'], [1, '#ffffff']]); ctx.fillRect(-600, -600, 1200, 1200); ctx.restore();
  // warm firelight (baked base, flicker is added per frame)
  ctx.globalCompositeOperation = 'screen';
  ctx.save(); ctx.translate(FIRE.x, FIRE.y + 60); ctx.scale(1, 0.75);
  ctx.fillStyle = radial(ctx, 0, 0, 1500, [[0, 'rgba(255,150,70,0.32)'], [0.35, 'rgba(255,135,60,0.14)'], [1, 'rgba(255,120,50,0)']]);
  ctx.fillRect(-1700, -1700, 3400, 3400); ctx.restore();
  // steady hot glow on the hearth stones and the floor in front of the fire
  ctx.save(); ctx.translate(FIRE.x, 1420); ctx.scale(1, 0.66);
  ctx.fillStyle = radial(ctx, 0, 0, 1400, [[0, 'rgba(255,145,65,0.3)'], [0.2, 'rgba(255,140,62,0.13)'], [0.39, 'rgba(255,138,60,0.03)'], [1, 'rgba(255,120,50,0)']]);
  ctx.fillRect(-1400, -1400, 2800, 2800); ctx.restore();
  // soft cool light around the window
  ctx.fillStyle = radial(ctx, WIN.x, WIN.y + 60, 620, [[0, 'rgba(150,170,205,0.12)'], [1, 'rgba(150,170,205,0)']]);
  ctx.fillRect(WIN.x - 640, WIN.y - 560, 1280, 1300);
  ctx.restore();
}

function paintFloorShadows(ctx) {
  // table: soft contact + cast shadow (fire is to the right, so it falls slightly left)
  softEllipse(ctx, 780, 1652, 330, 64, 'rgba(25,15,10,0.38)', 'rgba(25,15,10,0)', 0.2);
  softEllipse(ctx, 800, 1646, 130, 22, 'rgba(20,12,8,0.5)', 'rgba(20,12,8,0)', 0.2);
}

// ======================================================== window views
function paintViewKitchen(g) {
  const tmp = createCanvas(g.canvas.width, g.canvas.height), c = tmp.getContext('2d');
  c.scale(S, S); c.translate(300, 300);
  // back wall
  c.fillStyle = linear(c, 0, -300, 0, 300, [[0, '#6e5844'], [0.45, '#a5865f'], [1, '#5a4535']]); c.fillRect(-310, -310, 620, 620);
  c.fillStyle = radial(c, -110, -60, 330, [[0, 'rgba(255,214,150,0.55)'], [1, 'rgba(255,214,150,0)']]); c.fillRect(-310, -310, 620, 620);
  // upper cabinets
  c.fillStyle = '#5e4330'; c.fillRect(-310, -250, 190, 150); c.fillStyle = '#6e5038'; c.fillRect(-300, -240, 80, 130); c.fillRect(-210, -240, 80, 130);
  // kitchen window with dusk sky
  c.fillStyle = '#3c3530'; c.fillRect(-36, -236, 168, 150);
  c.fillStyle = linear(c, 0, -230, 0, -92, [[0, '#4d5a78'], [0.6, '#8a7d8e'], [1, '#c99a7e']]); c.fillRect(-28, -228, 152, 134);
  c.fillStyle = '#3c3530'; c.fillRect(44, -228, 8, 134); c.fillRect(-28, -165, 152, 7);
  // pendant lamp
  c.strokeStyle = '#2a2420'; c.lineWidth = 3; c.beginPath(); c.moveTo(-110, -310); c.lineTo(-110, -175); c.stroke();
  c.fillStyle = '#3a3029'; c.beginPath(); c.moveTo(-150, -138); c.lineTo(-70, -138); c.lineTo(-92, -178); c.lineTo(-128, -178); c.closePath(); c.fill();
  c.fillStyle = radial(c, -110, -130, 230, [[0, 'rgba(255,236,190,0.95)'], [0.1, 'rgba(255,214,150,0.6)'], [1, 'rgba(255,200,130,0)']]);
  c.beginPath(); c.moveTo(-150, -138); c.lineTo(-70, -138); c.lineTo(80, 60); c.lineTo(-300, 60); c.closePath(); c.globalAlpha = 0.45; c.fill(); c.globalAlpha = 1;
  c.fillStyle = '#fff2cf'; c.beginPath(); c.ellipse(-110, -136, 22, 7, 0, 0, 7); c.fill();
  // counter + base cabinets
  c.fillStyle = '#c9b89e'; c.fillRect(-310, 40, 620, 18);
  c.fillStyle = '#6a4d39'; c.fillRect(-310, 58, 620, 260);
  c.fillStyle = 'rgba(30,20,12,0.35)'; for (let x = -300; x < 310; x += 110) c.fillRect(x, 70, 4, 240);
  // kettle on the counter
  c.fillStyle = '#7d8a86'; c.beginPath(); c.ellipse(-200, 10, 38, 32, 0, 0, 7); c.fill(); c.fillRect(-238, 10, 76, 30);
  c.strokeStyle = '#4c5452'; c.lineWidth = 5; c.beginPath(); c.arc(-200, -14, 24, Math.PI, 0); c.stroke();
  // Eli leaning on the counter at the right
  c.fillStyle = '#3d4249';
  c.beginPath(); c.moveTo(130, 320); c.lineTo(140, 20); c.quadraticCurveTo(150, -70, 205, -80); c.quadraticCurveTo(270, -80, 285, -10); c.lineTo(300, 320); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(150, -30); c.quadraticCurveTo(110, 0, 100, 44); c.lineTo(126, 50); c.quadraticCurveTo(140, 10, 168, -10); c.closePath(); c.fill(); // arm to counter
  c.fillStyle = '#6e4a35'; c.beginPath(); c.ellipse(112, 46, 16, 7, 0, 0, 7); c.fill(); // hand
  c.fillStyle = '#5a3d2c'; c.beginPath(); c.ellipse(212, -132, 34, 42, 0.05, 0, 7); c.fill(); // head
  c.fillStyle = '#2a2420'; c.beginPath(); c.ellipse(214, -158, 36, 22, 0.05, Math.PI, 0); c.fill(); // hair
  c.fillStyle = '#3d4249'; c.beginPath(); c.moveTo(170, -100); c.quadraticCurveTo(210, -60, 255, -100); c.lineTo(262, -70); c.lineTo(165, -70); c.closePath(); c.fill(); // hood
  c.fillStyle = 'rgba(255,205,140,0.35)'; c.beginPath(); c.moveTo(142, 10); c.quadraticCurveTo(150, -66, 200, -78); c.lineTo(198, -70); c.quadraticCurveTo(156, -58, 150, 10); c.closePath(); c.fill(); // rim
  // vignette
  c.fillStyle = radial(c, 0, 0, 330, [[0.6, 'rgba(30,18,10,0)'], [1, 'rgba(30,18,10,0.45)']]); c.fillRect(-310, -310, 620, 620);
  g.fillStyle = '#7a6048'; g.fillRect(0, 0, g.canvas.width, g.canvas.height);
  g.filter = 'blur(4px)'; g.drawImage(tmp, 0, 0); g.filter = 'none';
}
function paintViewNight(g) {
  const c = g; c.save(); c.scale(S, S); c.translate(300, 300);
  const r = rng(201);
  c.fillStyle = linear(c, 0, -300, 0, 300, [[0, '#151a2a'], [0.55, '#283048'], [0.8, '#4a4458'], [1, '#5a4a52']]); c.fillRect(-310, -310, 620, 620);
  for (let i = 0; i < 26; i++) { const x = (r() - 0.5) * 560, y = -290 + r() * 230, s = 0.8 + r() * 1.6; c.fillStyle = `rgba(240,235,220,${0.4 + r() * 0.5})`; c.beginPath(); c.arc(x, y, s, 0, 7); c.fill(); }
  const layer = (base, col, hMin, hMax, wMin, wMax, lit, seed) => {
    const rr = rng(seed); let x = -320;
    while (x < 320) {
      const w = lerp(wMin, wMax, rr()), h = lerp(hMin, hMax, rr()), top = base - h;
      c.fillStyle = col; c.fillRect(x, top, w, 400);
      if (rr() < 0.3) { c.fillRect(x + w * 0.4, top - 20 - rr() * 30, 4, 30); }
      for (let wy = top + 10; wy < 300; wy += 16) for (let wx = x + 6; wx < x + w - 8; wx += 13) {
        if (rr() < lit) { c.fillStyle = `rgba(255,${190 + rr() * 40 | 0},${110 + rr() * 50 | 0},${0.55 + rr() * 0.45})`; c.fillRect(wx, wy, 6, 8); }
      }
      c.fillStyle = col; x += w + rr() * 6;
    }
  };
  layer(150, '#30344a', 60, 200, 40, 90, 0.18, 202);
  c.fillStyle = 'rgba(90,80,100,0.25)'; c.fillRect(-310, 0, 620, 300);
  layer(220, '#21243a', 80, 280, 50, 110, 0.32, 203);
  layer(300, '#16182a', 60, 160, 60, 130, 0.45, 204);
  c.fillStyle = radial(c, 0, 260, 380, [[0, 'rgba(255,170,110,0.12)'], [1, 'rgba(255,170,110,0)']]); c.fillRect(-310, -310, 620, 620);
  c.restore();
}
function paintViewDawn(g) {
  const c = g; c.save(); c.scale(S, S); c.translate(300, 300);
  c.fillStyle = linear(c, 0, -300, 0, 300, [[0, '#8fa2c4'], [0.4, '#c9b9c4'], [0.68, '#f2c9a6'], [0.8, '#f7dcae'], [1, '#d9b49a']]); c.fillRect(-310, -310, 620, 620);
  c.fillStyle = radial(c, 60, 110, 300, [[0, 'rgba(255,240,200,0.95)'], [0.12, 'rgba(255,225,170,0.7)'], [1, 'rgba(255,200,150,0)']]); c.fillRect(-310, -310, 620, 620);
  c.fillStyle = '#fff1d0'; c.beginPath(); c.arc(60, 112, 34, 0, 7); c.fill();
  const r = rng(301);
  for (let i = 0; i < 6; i++) { const y = -200 + i * 45 + r() * 20, x = -300 + r() * 300; c.fillStyle = `rgba(250,${200 + r() * 30 | 0},${190 + r() * 20 | 0},0.35)`; c.beginPath(); c.ellipse(x + 120, y, 120 + r() * 100, 6 + r() * 6, 0, 0, 7); c.fill(); }
  const hills = (y0, amp, col, seed) => { const rr = rng(seed); c.beginPath(); c.moveTo(-320, 320); c.lineTo(-320, y0); for (let x = -320; x <= 320; x += 20) c.lineTo(x, y0 - amp * (0.5 + 0.5 * Math.sin(x * 0.012 + seed)) - rr() * 6); c.lineTo(320, 320); c.closePath(); c.fillStyle = col; c.fill(); };
  hills(150, 50, '#b8a2ae', 1); hills(190, 40, '#97848f', 2);
  // rooftops
  c.fillStyle = '#6e5e66'; let x = -320; const rr = rng(302);
  while (x < 320) { const w = 60 + rr() * 70, h = 40 + rr() * 60; c.beginPath(); c.moveTo(x, 320); c.lineTo(x, 250 - h); c.lineTo(x + w / 2, 220 - h); c.lineTo(x + w, 250 - h); c.lineTo(x + w, 320); c.closePath(); c.fill(); if (rr() < 0.5) c.fillRect(x + w * 0.7, 215 - h, 10, 25); x += w + 4; }
  c.restore();
}
function paintViewNana(g) {
  const tmp = createCanvas(g.canvas.width, g.canvas.height), c = tmp.getContext('2d');
  c.scale(S, S); c.translate(300, 300);
  c.fillStyle = linear(c, 0, -300, 0, 300, [[0, '#d9c497'], [0.6, '#ecd9ac'], [1, '#c8ae82']]); c.fillRect(-310, -310, 620, 620);
  // sunny window with curtains
  c.fillStyle = '#8c6b4a'; c.fillRect(-250, -240, 200, 210);
  c.fillStyle = linear(c, 0, -230, 0, -40, [[0, '#cfe0e8'], [1, '#fff3cf']]); c.fillRect(-240, -230, 180, 190);
  c.fillStyle = '#8c6b4a'; c.fillRect(-154, -230, 8, 190); c.fillRect(-240, -140, 180, 7);
  c.fillStyle = '#c98f86'; c.beginPath(); c.moveTo(-262, -250); c.lineTo(-215, -250); c.quadraticCurveTo(-230, -130, -205, -20); c.lineTo(-262, -20); c.closePath(); c.fill();
  c.beginPath(); c.moveTo(-38, -250); c.lineTo(-85, -250); c.quadraticCurveTo(-70, -130, -95, -20); c.lineTo(-38, -20); c.closePath(); c.fill();
  c.fillStyle = 'rgba(255,255,255,0.35)'; for (let y = -245; y < -20; y += 16) { c.fillRect(-262, y, 50, 6); c.fillRect(-92, y, 54, 6); }
  // plant on sill
  c.fillStyle = '#b06a4a'; c.fillRect(-180, -60, 36, 26); c.fillStyle = '#6f8a52'; for (let i = 0; i < 6; i++) { c.beginPath(); c.ellipse(-162 + (i - 2.5) * 9, -74 - (i % 2) * 8, 7, 16, (i - 2.5) * 0.3, 0, 7); c.fill(); }
  // sun beams
  c.fillStyle = 'rgba(255,240,190,0.28)'; c.beginPath(); c.moveTo(-240, -230); c.lineTo(-60, -230); c.lineTo(260, 300); c.lineTo(-40, 300); c.closePath(); c.fill();
  // shelf with jars + copper pot
  c.fillStyle = '#7d5a3c'; c.fillRect(20, -150, 240, 12);
  [['#c99a5a', 40], ['#a5b48a', 82], ['#d6b07a', 124], ['#b77a5a', 166]].forEach(([col, x]) => { c.fillStyle = col; c.fillRect(x, -196, 30, 46); c.fillStyle = '#efe6d2'; c.fillRect(x - 2, -202, 34, 8); });
  c.fillStyle = '#b8743f'; c.beginPath(); c.arc(225, -200, 26, 0, Math.PI); c.fill(); c.fillRect(196, -204, 58, 6);
  // old enamel stove
  c.fillStyle = '#e8dfca'; c.fillRect(40, -10, 210, 320); c.fillStyle = '#3a3330'; c.fillRect(40, -18, 210, 12);
  c.fillStyle = '#cfc5ad'; c.fillRect(64, 60, 160, 120); c.fillStyle = '#9a8c74'; c.fillRect(64, 60, 160, 6);
  c.fillStyle = '#5a504a'; for (const x of [80, 130, 180, 230]) { c.beginPath(); c.arc(x - 10, 20, 6, 0, 7); c.fill(); }
  // table with a loaf of bread
  c.fillStyle = '#9a744e'; c.fillRect(-310, 150, 320, 20); c.fillStyle = '#7d5a3c'; c.fillRect(-310, 170, 320, 140);
  c.fillStyle = '#c98d4c'; c.beginPath(); c.ellipse(-150, 132, 58, 26, 0, Math.PI, 0); c.lineTo(-92, 150); c.lineTo(-208, 150); c.closePath(); c.fill();
  c.strokeStyle = '#a86a34'; c.lineWidth = 3; for (const x of [-180, -150, -120]) { c.beginPath(); c.moveTo(x - 8, 118); c.lineTo(x + 8, 108); c.stroke(); }
  c.fillStyle = radial(c, 0, 0, 330, [[0.6, 'rgba(120,80,30,0)'], [1, 'rgba(120,80,30,0.3)']]); c.fillRect(-310, -310, 620, 620);
  g.fillStyle = '#dcc79c'; g.fillRect(0, 0, g.canvas.width, g.canvas.height);
  g.filter = 'blur(3px)'; g.drawImage(tmp, 0, 0); g.filter = 'none';
}

// ========================================================== dynamic sprites
function paintBellows(ctx) {
  const x = 1300, top = 1140;
  softEllipse(ctx, x + 14, 1270, 52, 120, 'rgba(15,9,6,0.35)');
  // leather hanging loop
  ctx.strokeStyle = '#4a2f20'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x - 10, top + 30); ctx.quadraticCurveTo(x, top - 8, x + 10, top + 30); ctx.stroke();
  // handles
  ctx.fillStyle = linear(ctx, x - 30, 0, x + 30, 0, [[0, '#5a3a24'], [0.6, '#8a6040'], [1, '#5a3a24']]);
  ctx.beginPath(); ctx.ellipse(x - 14, top + 46, 9, 22, 0.25, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.ellipse(x + 14, top + 46, 9, 22, -0.25, 0, 7); ctx.fill();
  // leather gusset (visible around the board)
  ctx.beginPath(); ctx.moveTo(x - 50, top + 72); ctx.bezierCurveTo(x - 66, top + 150, x - 34, top + 216, x - 12, top + 236); ctx.lineTo(x + 12, top + 236); ctx.bezierCurveTo(x + 34, top + 216, x + 66, top + 150, x + 50, top + 72); ctx.closePath();
  ctx.fillStyle = '#4a2e1f'; ctx.fill();
  ctx.strokeStyle = 'rgba(25,14,8,0.6)'; ctx.lineWidth = 2;
  for (let i = 1; i < 4; i++) { ctx.beginPath(); ctx.moveTo(x - 50 - i * 3, top + 80 + i * 6); ctx.bezierCurveTo(x - 64 - i, top + 150, x - 34, top + 210, x - 14, top + 230); ctx.stroke(); }
  // wooden board (pear shape)
  ctx.beginPath(); ctx.moveTo(x - 40, top + 66); ctx.bezierCurveTo(x - 56, top + 150, x - 28, top + 206, x - 10, top + 228); ctx.lineTo(x + 10, top + 228); ctx.bezierCurveTo(x + 28, top + 206, x + 56, top + 150, x + 40, top + 66); ctx.quadraticCurveTo(x, top + 56, x - 40, top + 66); ctx.closePath();
  ctx.fillStyle = linear(ctx, x - 50, 0, x + 50, 0, [[0, '#5e3f28'], [0.55, '#8c6343'], [1, '#6a472f']]); ctx.fill();
  ctx.save(); ctx.clip();
  ctx.strokeStyle = 'rgba(40,24,14,0.35)'; ctx.lineWidth = 1.2;
  for (let i = -4; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(x + i * 9, top + 60); ctx.quadraticCurveTo(x + i * 11, top + 150, x + i * 4, top + 230); ctx.stroke(); }
  ctx.restore();
  // brass tacks + carved heart-ish motif
  ctx.fillStyle = '#c9a25e';
  for (let i = 0; i < 9; i++) { const a = i / 8; const px = lerp(x - 44, x - 12, a * a), py = top + 74 + a * 150; ctx.beginPath(); ctx.arc(px + 4, py, 2.3, 0, 7); ctx.arc(2 * x - px - 4, py, 2.3, 0, 7); ctx.fill(); }
  ctx.strokeStyle = 'rgba(40,24,14,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x, top + 132, 16, 0, 7); ctx.stroke();
  // brass nozzle
  ctx.fillStyle = linear(ctx, x - 12, 0, x + 12, 0, [[0, '#7a5a2c'], [0.5, '#d2a65c'], [1, '#6e4f26']]);
  ctx.beginPath(); ctx.moveTo(x - 12, top + 226); ctx.lineTo(x + 12, top + 226); ctx.lineTo(x + 5, top + 290); ctx.lineTo(x - 5, top + 290); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,200,140,0.18)'; ctx.fillRect(x + 22, top + 80, 3, 120);
}

function paintLogs(ctx, glow, which = [2, 1, 0]) {
  const logs = [
    [1446, 1448, 1610, 1432, 23], [1466, 1420, 1592, 1442, 20], [1456, 1410, 1598, 1404, 18],
  ];
  // andirons
  if (!glow && which.includes(0)) for (const ax of [1448, 1604]) {
    ctx.fillStyle = '#1b1614'; ctx.fillRect(ax - 6, 1420, 12, 46); ctx.beginPath(); ctx.arc(ax, 1416, 10, 0, 7); ctx.fill();
    ctx.fillRect(ax - 18, 1460, 36, 8); ctx.fillStyle = 'rgba(255,150,80,0.25)'; ctx.fillRect(ax + 2, 1414, 3, 50);
  }
  for (const i of which) {
    const [x0, y0, x1, y1, rr] = logs[i]; const a = Math.atan2(y1 - y0, x1 - x0), L = Math.hypot(x1 - x0, y1 - y0);
    ctx.save(); ctx.translate(x0, y0); ctx.rotate(a);
    const body = () => { ctx.beginPath(); ctx.moveTo(0, -rr); ctx.lineTo(L, -rr * 0.92); ctx.ellipse(L, 0, rr * 0.38, rr * 0.92, 0, -Math.PI / 2, Math.PI / 2); ctx.lineTo(0, rr); ctx.ellipse(0, 0, rr * 0.4, rr, 0, Math.PI / 2, Math.PI * 1.5); ctx.closePath(); };
    const r = rng(500 + i);
    if (!glow) {
      body();
      ctx.fillStyle = linear(ctx, 0, -rr, 0, rr, [[0, '#6e5a48'], [0.3, '#4e3d30'], [0.7, '#2a1f19'], [1, '#120c0a']]); ctx.fill();
      ctx.save(); ctx.clip();
      // bark plates
      for (let k = 0; k < 26; k++) {
        const bx = r() * L, by = -rr + r() * rr * 1.6, bw = 14 + r() * 26, bh = 3 + r() * 5;
        ctx.fillStyle = r() < 0.5 ? 'rgba(20,14,10,0.45)' : 'rgba(150,125,100,0.18)';
        ctx.beginPath(); ctx.ellipse(bx, by, bw / 2, bh / 2, (r() - 0.5) * 0.1, 0, 7); ctx.fill();
      }
      // charred, crackled half toward the fire
      ctx.fillStyle = linear(ctx, 0, -rr, 0, rr, [[0, 'rgba(10,6,5,0)'], [0.5, 'rgba(10,6,5,0.35)'], [1, 'rgba(10,6,5,0.6)']]); ctx.fillRect(0, -rr, L, rr * 2);
      ctx.restore();
      // end grain
      ctx.beginPath(); ctx.ellipse(L, 0, rr * 0.38, rr * 0.92, 0, 0, 7); ctx.fillStyle = '#8a6c50'; ctx.fill();
      ctx.strokeStyle = 'rgba(60,38,24,0.55)'; ctx.lineWidth = 1;
      for (const k of [0.3, 0.55, 0.8]) { ctx.beginPath(); ctx.ellipse(L, 0, rr * 0.38 * k, rr * 0.92 * k, 0, 0, 7); ctx.stroke(); }
      ctx.fillStyle = 'rgba(20,12,8,0.5)'; ctx.beginPath(); ctx.ellipse(L - 2, rr * 0.4, rr * 0.3, rr * 0.45, 0, 0, 7); ctx.fill();
      ctx.beginPath(); ctx.ellipse(0, 0, rr * 0.4, rr, 0, 0, 7); ctx.fillStyle = '#1e140f'; ctx.fill();
    } else {
      // embers glowing along the underside + short crackle lines
      ctx.save(); body(); ctx.clip();
      ctx.fillStyle = linear(ctx, 0, 0, 0, rr, [[0, 'rgba(255,90,30,0)'], [0.55, 'rgba(255,100,30,0.35)'], [1, 'rgba(255,150,60,0.85)']]); ctx.fillRect(0, -rr, L, rr * 2);
      ctx.strokeStyle = 'rgba(255,140,50,0.9)'; ctx.lineWidth = 1.6; ctx.lineCap = 'round';
      for (let k = 0; k < 14; k++) {
        const xx = 8 + r() * (L - 20), yy = rr * (0.25 + r() * 0.7), w = 5 + r() * 9;
        ctx.beginPath(); ctx.moveTo(xx, yy); ctx.lineTo(xx + w, yy + (r() - 0.5) * 3); ctx.stroke();
      }
      ctx.restore();
      ctx.beginPath(); ctx.ellipse(0, 0, rr * 0.3, rr * 0.75, 0, 0, 7); ctx.fillStyle = 'rgba(255,110,40,0.6)'; ctx.fill();
    }
    ctx.restore();
  }
}

function paintChairBack(ctx, cx) {
  const wood = '#6e4a32', dark = '#4a3122', lite = '#8f6646';
  softEllipse(ctx, cx, 1604, 120, 18, 'rgba(15,9,6,0.45)', 'rgba(15,9,6,0)', 0.2);
  const leg = (x, y0, y1, w) => { ctx.fillStyle = linear(ctx, x - w / 2, 0, x + w / 2, 0, [[0, dark], [0.6, lite], [1, wood]]); ctx.beginPath(); ctx.moveTo(x - w / 2, y0); ctx.lineTo(x + w / 2, y0); ctx.lineTo(x + w / 2 - 2, y1); ctx.lineTo(x - w / 2 + 2, y1); ctx.closePath(); ctx.fill(); };
  // back legs (further) then stretcher, seat, front legs
  leg(cx - 74, 1450, 1592, 13); leg(cx + 74, 1450, 1592, 13);
  ctx.fillStyle = dark; ctx.fillRect(cx - 74, 1540, 148, 8);
  // back posts and spindles
  const post = (x0, x1) => { ctx.fillStyle = linear(ctx, x0 - 8, 0, x0 + 8, 0, [[0, dark], [0.65, lite], [1, wood]]); ctx.beginPath(); ctx.moveTo(x1 - 7, 1166); ctx.lineTo(x1 + 7, 1166); ctx.lineTo(x0 + 7, 1452); ctx.lineTo(x0 - 7, 1452); ctx.closePath(); ctx.fill(); };
  for (let i = -2; i <= 2; i++) { const sx = cx + i * 25; ctx.fillStyle = linear(ctx, sx - 4, 0, sx + 4, 0, [[0, dark], [0.6, lite], [1, wood]]); ctx.fillRect(sx - 4, 1178, 8, 272); }
  post(cx - 76, cx - 82); post(cx + 76, cx + 82);
  // crest rail (slightly arched)
  ctx.beginPath(); ctx.moveTo(cx - 98, 1160); ctx.quadraticCurveTo(cx, 1140, cx + 98, 1160); ctx.lineTo(cx + 94, 1186); ctx.quadraticCurveTo(cx, 1168, cx - 94, 1186); ctx.closePath();
  ctx.fillStyle = linear(ctx, 0, 1146, 0, 1188, [[0, lite], [0.4, wood], [1, dark]]); ctx.fill();
  ctx.fillStyle = 'rgba(255,200,140,0.22)'; ctx.beginPath(); ctx.moveTo(cx - 96, 1159); ctx.quadraticCurveTo(cx, 1140, cx + 96, 1159); ctx.lineTo(cx + 96, 1163); ctx.quadraticCurveTo(cx, 1145, cx - 96, 1163); ctx.closePath(); ctx.fill();
  // seat
  ctx.beginPath(); ctx.moveTo(cx - 96, 1446); ctx.lineTo(cx + 96, 1446); ctx.lineTo(cx + 104, 1472); ctx.lineTo(cx - 104, 1472); ctx.closePath();
  ctx.fillStyle = linear(ctx, cx - 100, 0, cx + 100, 0, [[0, '#6a4630'], [1, '#86603f']]); ctx.fill();
  ctx.fillStyle = dark; ctx.fillRect(cx - 104, 1472, 208, 14);
  leg(cx - 92, 1484, 1612, 15); leg(cx + 92, 1484, 1612, 15);
}
function paintChairSide(ctx) {
  const wood = '#6e4a32', dark = '#4a3122', lite = '#8f6646';
  softEllipse(ctx, 1160, 1626, 110, 16, 'rgba(15,9,6,0.45)', 'rgba(15,9,6,0)', 0.2);
  const leg = (x0, y0, x1, y1, w, c) => { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); };
  // far legs + far back post
  leg(1112, 1452, 1106, 1600, 11, dark); leg(1208, 1452, 1214, 1600, 11, dark);
  leg(1214, 1452, 1238, 1168, 11, dark);
  // spindles edge-on
  for (let i = 0; i < 3; i++) leg(1214 + i * 3, 1450, 1232 + i * 3, 1190, 5, i ? wood : dark);
  // seat slab
  ctx.beginPath(); ctx.moveTo(1092, 1446); ctx.lineTo(1226, 1442); ctx.lineTo(1232, 1458); ctx.lineTo(1088, 1462); ctx.closePath(); ctx.fillStyle = '#86603f'; ctx.fill();
  ctx.fillStyle = dark; ctx.beginPath(); ctx.moveTo(1088, 1462); ctx.lineTo(1232, 1458); ctx.lineTo(1232, 1474); ctx.lineTo(1088, 1478); ctx.closePath(); ctx.fill();
  // near legs + stretcher
  leg(1100, 1474, 1092, 1626, 13, wood); leg(1220, 1472, 1228, 1626, 13, wood);
  leg(1096, 1560, 1224, 1560, 7, dark);
  ctx.strokeStyle = 'rgba(255,200,140,0.3)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(1226, 1476); ctx.lineTo(1233, 1622); ctx.stroke();
  // near back post + crest (side view)
  leg(1222, 1454, 1250, 1166, 13, wood);
  ctx.strokeStyle = 'rgba(255,200,140,0.35)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(1228, 1450); ctx.lineTo(1256, 1170); ctx.stroke();
  ctx.fillStyle = linear(ctx, 1228, 0, 1262, 0, [[0, dark], [0.6, lite], [1, wood]]);
  ctx.beginPath(); ctx.moveTo(1226, 1150); ctx.lineTo(1262, 1154); ctx.lineTo(1258, 1188); ctx.lineTo(1224, 1184); ctx.closePath(); ctx.fill();
  ctx.lineCap = 'butt';
}
function paintTable(ctx) {
  const cx = 800, cy = 1360, RX = 300, RY = 70, T = 25;
  // pedestal
  const prof = [[1440, 34], [1460, 30], [1490, 42], [1515, 46], [1540, 30], [1565, 24], [1590, 36], [1606, 46]];
  ctx.beginPath(); ctx.moveTo(cx - prof[0][1], prof[0][0]);
  for (const [y, w] of prof) ctx.lineTo(cx - w, y);
  for (let i = prof.length - 1; i >= 0; i--) ctx.lineTo(cx + prof[i][1], prof[i][0]);
  ctx.closePath();
  ctx.fillStyle = linear(ctx, cx - 46, 0, cx + 46, 0, [[0, '#2e1f16'], [0.35, '#55392a'], [0.72, '#8c6142'], [0.9, '#6a4632'], [1, '#4a3123']]); ctx.fill();
  ctx.strokeStyle = 'rgba(20,12,8,0.4)'; ctx.lineWidth = 1.5;
  for (const y of [1490, 1540, 1590]) { ctx.beginPath(); ctx.ellipse(cx, y, prof.find(p => p[0] >= y)[1], 4, 0, 0, Math.PI); ctx.stroke(); }
  // splayed feet
  const foot = (dx, dy, w) => {
    ctx.beginPath(); ctx.moveTo(cx - 30, 1596); ctx.quadraticCurveTo(cx + dx * 0.5, 1600 + dy * 0.3, cx + dx, 1626 + dy); ctx.lineTo(cx + dx + Math.sign(dx || 1) * 6, 1640 + dy);
    ctx.lineTo(cx + dx - Math.sign(dx || 1) * w, 1640 + dy); ctx.quadraticCurveTo(cx + dx * 0.4, 1618 + dy * 0.4, cx + 30, 1600); ctx.closePath();
    ctx.fillStyle = linear(ctx, cx - 140, 0, cx + 140, 0, [[0, '#2e1f16'], [0.6, '#6a4632'], [1, '#7c5439']]); ctx.fill();
  };
  foot(-130, -4, 30); foot(130, -4, 30); foot(-8, 6, 20);
  // edge band
  ctx.beginPath(); ctx.ellipse(cx, cy, RX, RY, 0, 0, Math.PI); ctx.lineTo(cx - RX, cy + T); ctx.ellipse(cx, cy + T, RX, RY, 0, Math.PI, 0, true); ctx.closePath();
  ctx.fillStyle = linear(ctx, cx - RX, 0, cx + RX, 0, [[0, '#3a281c'], [0.5, '#5e412d'], [0.85, '#7c5538'], [1, '#5a3d2a']]); ctx.fill();
  ctx.fillStyle = 'rgba(20,12,8,0.25)'; ctx.beginPath(); ctx.ellipse(cx, cy + T, RX, RY, 0, 0, Math.PI); ctx.ellipse(cx, cy + T - 6, RX, RY, 0, Math.PI, 0, true); ctx.fill();
  // top
  ctx.save(); ctx.beginPath(); ctx.ellipse(cx, cy, RX, RY, 0, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = linear(ctx, cx - RX, cy - RY, cx + RX, cy + RY, [[0, '#6a4630'], [0.55, '#8a6141'], [1, '#9c6e48']]); ctx.fillRect(cx - RX, cy - RY, RX * 2, RY * 2);
  const r = rng(121);
  for (let y = cy - RY + 23; y < cy + RY; y += 24) { ctx.strokeStyle = 'rgba(30,18,10,0.4)'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(cx - RX, y); ctx.lineTo(cx + RX, y); ctx.stroke(); }
  for (let i = 0; i < 40; i++) { const y = cy - RY + r() * RY * 2, x0 = cx - RX + r() * RX * 1.6; ctx.strokeStyle = r() < 0.6 ? 'rgba(40,24,14,0.18)' : 'rgba(255,220,180,0.08)'; ctx.lineWidth = 1 + r(); ctx.beginPath(); ctx.moveTo(x0, y); ctx.bezierCurveTo(x0 + 40, y + 2, x0 + 80, y - 2, x0 + 100 + r() * 120, y + (r() - 0.5) * 3); ctx.stroke(); }
  // warm sheen from the fire (right) + cool sheen from window (back left)
  softEllipse(ctx, cx + 170, cy - 12, 150, 34, 'rgba(255,190,120,0.22)');
  softEllipse(ctx, cx - 170, cy - 30, 120, 24, 'rgba(190,200,220,0.08)');
  ctx.restore();
  ctx.strokeStyle = 'rgba(255,215,170,0.25)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.ellipse(cx, cy, RX - 1, RY - 1, 0, 0.05, Math.PI - 0.05); ctx.stroke();
}

// ================================================================ cache
let CACHE = null;
function getCache() {
  if (CACHE) return CACHE;
  const tex = {
    grit: makeNoiseTex(384, 7, [12, 48], [0.35, 0.2], 0.55),
    blotch: makeNoiseTex(128, 9, [4, 8], [0.6, 0.4], 0),
  };
  const W = Math.ceil((CEXT.x1 - CEXT.x0) * S), H = Math.ceil((CEXT.y1 - CEXT.y0) * S);
  const room = createCanvas(W, H), g = room.getContext('2d');
  g.scale(S, S); g.translate(-CEXT.x0, -CEXT.y0);
  paintCeiling(g);
  paintWalls(g, tex);
  paintWallPlate(g);
  paintFloor(g, tex);
  paintRug(g);
  paintFloorShadows(g);
  paintWindowSurround(g, tex);
  paintShelves(g);
  paintChimneyBreast(g, tex);
  paintHearth(g, tex);
  paintMantelObjects(g);
  paintDoorSurround(g, tex);
  paintRightSide(g);
  paintLeftSide(g);
  paintCorner(g);
  bakeLighting(g);
  // Sadness's corner sits in a soft, cool shadow (cornerLight lifts it per frame)
  g.save(); g.globalCompositeOperation = 'multiply'; g.translate(110, 1700); g.scale(1, 0.62);
  g.fillStyle = radial(g, 0, 0, 560, [[0, rgba(60, 54, 80, 0.46)], [0.5, rgba(60, 54, 80, 0.34)], [1, 'rgba(60,54,80,0)']]);
  g.fillRect(-600, -600, 1200, 1200); g.restore();
  // keep the firebox throat sooty-dark; the fire lights it per frame
  g.save(); fireboxPath(g); g.clip(); g.globalCompositeOperation = 'multiply';
  g.fillStyle = radial(g, FB.cx, 1430, 300, [[0, '#d8bca8'], [0.5, '#8a7068'], [1, '#4a3c3a']]); g.fillRect(FB.x0, FB.y0, 320, 370); g.restore();
  // cut the glass + doorway so dynamic layers can show through
  g.save(); g.globalCompositeOperation = 'destination-out'; g.fillStyle = '#000'; g.globalAlpha = 1;
  g.beginPath(); g.arc(WIN.x, WIN.y, WIN.r, 0, Math.PI * 2); g.fill();
  doorwayPath(g); g.fill(); g.restore();
  // glass: inner shadow from the deep frame + reflection sheen + mullions
  g.save(); g.beginPath(); g.arc(WIN.x, WIN.y, WIN.r, 0, Math.PI * 2); g.clip();
  g.fillStyle = radial(g, WIN.x, WIN.y, WIN.r, [[0.86, 'rgba(25,15,10,0)'], [1, 'rgba(25,15,10,0.35)']]); g.fillRect(WIN.x - 300, WIN.y - 300, 600, 600);
  g.save(); g.translate(WIN.x, WIN.y); g.rotate(-0.7);
  g.fillStyle = linear(g, -300, 0, 300, 0, [[0.18, 'rgba(255,255,255,0)'], [0.28, 'rgba(255,250,240,0.09)'], [0.34, 'rgba(255,250,240,0.03)'], [0.4, 'rgba(255,250,240,0.08)'], [0.46, 'rgba(255,255,255,0)']]);
  g.fillRect(-310, -310, 620, 620); g.restore();
  g.restore();
  // mullions
  g.save(); g.beginPath(); g.arc(WIN.x, WIN.y, WIN.r + 2, 0, Math.PI * 2); g.clip();
  softEllipse(g, WIN.x + 6, WIN.y + 8, 30, 30, 'rgba(15,9,6,0.3)');
  g.fillStyle = linear(g, WIN.x - 11, 0, WIN.x + 11, 0, [[0, '#4a3324'], [0.6, '#7a5a40'], [1, '#5a3e2b']]); g.fillRect(WIN.x - 11, WIN.y - 305, 22, 610);
  g.fillStyle = linear(g, 0, WIN.y - 11, 0, WIN.y + 11, [[0, '#7a5a40'], [0.5, '#6a4a33'], [1, '#3e2a1d']]); g.fillRect(WIN.x - 305, WIN.y - 11, 610, 22);
  g.fillStyle = '#6a4a33'; g.beginPath(); g.arc(WIN.x, WIN.y, 20, 0, 7); g.fill();
  g.fillStyle = 'rgba(255,220,180,0.2)'; g.beginPath(); g.arc(WIN.x - 3, WIN.y - 3, 12, 0, 7); g.fill();
  g.restore();
  paintWindowLedge(g);

  const views = {};
  const mkView = (fn) => { const c = createCanvas(Math.ceil(600 * S), Math.ceil(600 * S)); fn(c.getContext('2d')); return c; };
  views.kitchen = mkView(paintViewKitchen);
  views.night = mkView(paintViewNight);
  views.dawn = mkView(paintViewDawn);
  views.nana = mkView(paintViewNana);

  const bellows = sprite(1230, 1120, 1380, 1440, paintBellows);
  // logs with their ember glow pre-composited at the cozy level (extra glow added per frame)
  const withGlow = (which) => g2 => { paintLogs(g2, false, which); g2.save(); g2.globalCompositeOperation = 'lighter'; g2.globalAlpha = LOG_GLOW0; paintLogs(g2, true, which); g2.restore(); };
  const logs = sprite(1400, 1370, 1650, 1480, withGlow([2, 1]));
  const logsGlow = sprite(1400, 1370, 1650, 1480, g2 => paintLogs(g2, true, [2, 1]));
  const logsF = sprite(1400, 1370, 1650, 1480, withGlow([0]));
  const logsFGlow = sprite(1400, 1370, 1650, 1480, g2 => paintLogs(g2, true, [0]));
  const chair700 = sprite(560, 1120, 840, 1640, g2 => paintChairBack(g2, 700));
  const chair960 = sprite(820, 1120, 1100, 1640, g2 => paintChairBack(g2, 960));
  const chair1100 = sprite(1040, 1130, 1290, 1660, paintChairSide);
  const table = sprite(470, 1280, 1130, 1670, paintTable);
  const tableDim = dimVariant(table, DIM_COLOR);
  const glow = createCanvas(64, 64); { const q = glow.getContext('2d'); q.fillStyle = radial(q, 32, 32, 32, [[0, 'rgba(255,235,190,1)'], [0.15, 'rgba(255,210,140,0.7)'], [0.45, 'rgba(255,170,90,0.18)'], [1, 'rgba(255,150,70,0)']]); q.fillRect(0, 0, 64, 64); }
  const smoke = createCanvas(128, 128); { const q = smoke.getContext('2d'); q.fillStyle = radial(q, 64, 64, 64, [[0, 'rgba(150,128,112,0.55)'], [0.5, 'rgba(120,100,88,0.25)'], [1, 'rgba(100,84,74,0)']]); q.fillRect(0, 0, 128, 128); }

  // fairy light positions along the wall plate
  const fairy = [];
  const pins = []; for (let x = -480; x <= 2120; x += 230) pins.push(x);
  const wire = [];
  for (let i = 0; i < pins.length - 1; i++) {
    const a = pins[i], b = pins[i + 1];
    for (let s = 0; s <= 1.0001; s += 0.05) { const x = lerp(a, b, s); wire.push([x, yC(x) + 24 + 42 * 4 * s * (1 - s)]); }
    for (let k = 1; k < 6; k++) { const s = k / 6, x = lerp(a, b, s); fairy.push({ x, y: yC(x) + 30 + 42 * 4 * s * (1 - s), ph: h1(fairy.length * 3 + 1) * 6.28, sp: 0.18 + 0.2 * h1(fairy.length * 5 + 2), warm: h1(fairy.length * 7) }); }
  }
  CACHE = { room: roomLevels(room), views, bellows, logs, logsGlow, logsF, logsFGlow, chair700, chair960, chair1100, table, tableDim, glow, smoke, fairy, wire };
  return CACHE;
}
const DIM_COLOR = '#4b4458';
const LOG_GLOW0 = 0.7;

// ============================================================ per-frame
function opts(o) {
  o = o || {};
  return {
    view: o.view || 'kitchen', viewFn: o.viewFn || null,
    fire: clamp(o.fire ?? 1, 0, 2), doorOpen: clamp(o.doorOpen ?? 0, 0, 1),
    bellowsHidden: !!o.bellowsHidden, chairs: Object.assign({ c700: true, c960: true, c1100: true }, o.chairs || {}),
    cornerLight: clamp(o.cornerLight ?? 0, 0, 1), candle: o.candle ?? true, fairy: clamp(o.fairy ?? 1, 0, 1),
    steam: clamp(o.steam ?? 0.6, 0, 1),
  };
}
function dimAmount(fire) { return clamp((1 - fire) / 0.7, 0, 1) * 0.42; }

// the room cache is split into padded tiles: drawing a canvas snapshots it, so only
// the visible tiles are touched each frame
const TILE = 508, TPAD = 2;
function makeTiles(room, s) {
  const tiles = [];
  for (let y = 0; y < room.height; y += TILE) for (let x = 0; x < room.width; x += TILE) {
    const w = Math.min(TILE, room.width - x), h = Math.min(TILE, room.height - y);
    const c = createCanvas(w + 2 * TPAD, h + 2 * TPAD), g = c.getContext('2d');
    g.drawImage(room, x - TPAD, y - TPAD, w + 2 * TPAD, h + 2 * TPAD, 0, 0, w + 2 * TPAD, h + 2 * TPAD);
    // replicate edge pixels into the padding where the room ends
    tiles.push({ c, px: x, py: y, w, h });
  }
  return { s, tiles };
}
function roomLevels(room) {
  const levels = [makeTiles(room, S)];
  let c = room;
  for (const k of [0.72, 0.5, 0.36]) { const d = downsample(room, k); levels.push(makeTiles(d, S * k)); }
  void c; return levels;
}
function drawRoom(ctx, levels, V) {
  const { s: S, tiles } = pickLevel(levels, V.sc);
  const x0 = (V.x0 - CEXT.x0) * S - 2, y0 = (V.y0 - CEXT.y0) * S - 2, x1 = (V.x1 - CEXT.x0) * S + 2, y1 = (V.y1 - CEXT.y0) * S + 2;
  for (const T of tiles) {
    if (T.px + T.w < x0 || T.px > x1 || T.py + T.h < y0 || T.py > y1) continue;
    // 5-argument drawImage: a source sub-rect would force a pixel copy of the canvas
    ctx.drawImage(T.c, CEXT.x0 + (T.px - TPAD) / S, CEXT.y0 + (T.py - TPAD) / S, T.c.width / S, T.c.height / S);
  }
}

// ---- door: perspective projection of the hinged leaf
const DOOR_F = 2200;
function proj(x, y, z) { const k = DOOR_F / (DOOR_F - z); return [VPX + (x - VPX) * k, VPY + (y - VPY) * k]; }
function doorAngle(open) { const e = open * open * (3 - 2 * open); return e * 1.45; }
function doorArchY(u) { const r = 140, d = u - 140; return DOOR.spring - Math.sqrt(Math.max(0, r * r - d * d)); }
function drawBeyond(ctx, open) {
  ctx.save(); doorwayPath(ctx, -5); ctx.clip();
  ctx.fillStyle = linear(ctx, 0, 880, 0, 1480, [[0, '#e9b56a'], [0.5, '#f7cf86'], [1, '#e2a95e']]); ctx.fillRect(40, 860, 320, 640);
  // a warm hallway: side walls converging, bright far end
  ctx.fillStyle = 'rgba(160,100,50,0.35)'; ctx.beginPath(); ctx.moveTo(60, 880); ctx.lineTo(150, 1120); ctx.lineTo(150, 1330); ctx.lineTo(60, 1480); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(190,120,60,0.25)'; ctx.beginPath(); ctx.moveTo(340, 880); ctx.lineTo(250, 1120); ctx.lineTo(250, 1330); ctx.lineTo(340, 1480); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(200,140,80,0.4)'; ctx.beginPath(); ctx.moveTo(60, 1480); ctx.lineTo(150, 1330); ctx.lineTo(250, 1330); ctx.lineTo(340, 1480); ctx.closePath(); ctx.fill();
  ctx.fillStyle = radial(ctx, 200, 1220, 200, [[0, 'rgba(255,248,220,0.95)'], [0.4, 'rgba(255,230,170,0.5)'], [1, 'rgba(255,220,150,0)']]); ctx.fillRect(40, 860, 320, 640);
  // inner reveal of the wall thickness on the right jamb
  ctx.fillStyle = linear(ctx, 312, 0, 340, 0, [[0, 'rgba(120,90,60,0.6)'], [1, 'rgba(70,50,35,0.9)']]); ctx.fillRect(312, 880, 28, 600);
  ctx.restore();
  void open;
}
function drawDoorLeaf(ctx, open, t) {
  const th = doorAngle(open), c = Math.cos(th), s = Math.sin(th), W = 280, T = 18;
  const P = (u, y, back) => { let x = DOOR.x0 + u * c, z = u * s; if (back) { x += T * s; z -= T * c; } return proj(x, y, z); };
  const outline = (back) => {
    const pts = [P(0, DOOR.y1, back)];
    for (let i = 0; i <= 24; i++) { const u = (i / 24) * W; pts.push(P(u, doorArchY(u), back)); }
    pts.push(P(W, DOOR.y1, back)); return pts;
  };
  // visible face: front faces the eye while the normal points toward the camera
  const mid = P(W / 2, 1200, false);
  const nx = -s, nz = c; const ex = VPX - (DOOR.x0 + (W / 2) * c), ez = DOOR_F - (W / 2) * s;
  const frontVis = nx * ex + nz * ez > 0; void mid;
  // light falling on the leaf: warm when facing the room, darker when turned away
  const facing = Math.max(0, c);
  // free edge (thickness)
  if (th > 0.01) {
    const e = []; for (let i = 0; i <= 8; i++) { const yy = lerp(DOOR.spring, DOOR.y1, i / 8); e.push(P(W, yy, false)); }
    const eb = []; for (let i = 8; i >= 0; i--) { const yy = lerp(DOOR.spring, DOOR.y1, i / 8); eb.push(P(W, yy, true)); }
    polyPath(ctx, e.concat(eb)); ctx.fillStyle = '#8a6444'; ctx.fill();
    // arch edge band near the top of the free edge
    const ta = [], tb = []; for (let i = 12; i <= 24; i++) { const u = (i / 24) * W; ta.push(P(u, doorArchY(u), false)); tb.unshift(P(u, doorArchY(u), true)); }
    polyPath(ctx, ta.concat(tb)); ctx.fillStyle = '#6e4e36'; ctx.fill();
  }
  const pts = outline(!frontVis);
  ctx.save(); polyPath(ctx, pts); ctx.clip();
  // planks
  const r = rng(131);
  for (let i = 0; i < 5; i++) {
    const u0 = i * W / 5, u1 = (i + 1) * W / 5, k = 0.9 + r() * 0.2;
    const q = [P(u0, 860, !frontVis), P(u1, 860, !frontVis), P(u1, DOOR.y1 + 2, !frontVis), P(u0, DOOR.y1 + 2, !frontVis)];
    polyPath(ctx, q); ctx.fillStyle = rgba(118 * k, 82 * k, 54 * k); ctx.fill();
    // grain
    ctx.strokeStyle = 'rgba(45,28,16,0.3)'; ctx.lineWidth = 1.2;
    for (let j = 0; j < 4; j++) { const u = lerp(u0 + 4, u1 - 4, r()), ya = 900 + r() * 300, yb2 = ya + 120 + r() * 250; const a = P(u, ya, !frontVis), b = P(u + (r() - 0.5) * 6, yb2, !frontVis); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    const a = P(u0, 860, !frontVis), b = P(u0, DOOR.y1, !frontVis); ctx.strokeStyle = 'rgba(30,18,10,0.6)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  }
  if (frontVis) {
    // iron strap hinges on the LEFT (hinge) edge
    for (const hy of [1010, 1390]) {
      const strap = [P(-4, hy - 12, false), P(170, hy - 10, false), P(196, hy, false), P(170, hy + 10, false), P(-4, hy + 12, false)];
      polyPath(ctx, strap); ctx.fillStyle = '#2b2522'; ctx.fill();
      ctx.fillStyle = '#5a504a'; for (const u of [20, 70, 120, 165]) { const p = P(u, hy, false); ctx.beginPath(); ctx.arc(p[0], p[1], 3.5, 0, 7); ctx.fill(); }
      const hl = [P(0, hy - 12, false), P(170, hy - 10, false), P(170, hy - 7, false), P(0, hy - 9, false)]; polyPath(ctx, hl); ctx.fillStyle = 'rgba(255,200,150,0.18)'; ctx.fill();
    }
    // ring handle
    const hp = P(236, 1230, false); ctx.strokeStyle = '#2b2522'; ctx.lineWidth = 5; ctx.beginPath(); ctx.ellipse(hp[0], hp[1] + 16, 15 * Math.max(0.3, c), 17, 0, 0, 7); ctx.stroke();
    ctx.fillStyle = '#2b2522'; ctx.beginPath(); ctx.arc(hp[0], hp[1], 8, 0, 7); ctx.fill();
  } else {
    // ledge-and-brace on the back face
    for (const hy of [1040, 1400]) { polyPath(ctx, [P(10, hy - 22, true), P(270, hy - 22, true), P(270, hy + 22, true), P(10, hy + 22, true)]); ctx.fillStyle = '#6a4a32'; ctx.fill(); }
    polyPath(ctx, [P(20, 1400, true), P(50, 1400, true), P(268, 1050, true), P(238, 1050, true)]); ctx.fillStyle = '#5e422c'; ctx.fill();
  }
  // shading: lit by the fire when facing into the room, dimmer as it turns away; hinge side darker
  const lt = 0.12 + 0.5 * (1 - facing);
  const a = P(0, 1200, !frontVis), b = P(W, 1200, !frontVis);
  ctx.fillStyle = linear(ctx, a[0], a[1], b[0], b[1], [[0, `rgba(20,12,8,${0.35 + lt * 0.3})`], [1, `rgba(20,12,8,${lt * 0.6})`]]);
  ctx.fillRect(-300, 700, 800, 900);
  // light from beyond spilling around the free edge when ajar
  if (open > 0.02) { ctx.fillStyle = linear(ctx, b[0] - 60, 0, b[0], 0, [[0, 'rgba(255,200,120,0)'], [1, `rgba(255,200,120,${0.18 * Math.min(1, open * 4)})`]]); ctx.fillRect(b[0] - 60, 700, 70, 900); }
  // soft top shadow under the arch
  ctx.fillStyle = linear(ctx, 0, 880, 0, 1010, [[0, 'rgba(20,12,8,0.35)'], [1, 'rgba(20,12,8,0)']]); ctx.fillRect(-300, 860, 800, 160);
  ctx.restore();
  // thin dark edge of the leaf
  polyPath(ctx, pts); ctx.strokeStyle = 'rgba(30,18,10,0.55)'; ctx.lineWidth = 2; ctx.stroke();
  void t;
  return { freeBottom: P(W, DOOR.y1, false), th };
}
function drawDoorLight(ctx, open, freeBottom) {
  const e = smooth(0, 1, open); if (e <= 0.001) return;
  const gl = Math.max(DOOR.x0, Math.min(DOOR.x1, freeBottom[0])), gr = DOOR.x1;
  if (gr - gl < 2) return;
  const SX = 200, SY = 1000, Y2 = 2150;
  const ext = x => SX + (x - SX) * (Y2 - SY) / (DOOR.y1 - SY);
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  // layered wedges fake a soft penumbra on both edges
  for (let k = 0; k < 5; k++) {
    const sp = (k - 2) * 16, a = 0.26;
    const l0 = gl - sp * 0.3, r0 = gr + sp * 0.3;
    ctx.beginPath(); ctx.moveTo(l0, DOOR.y1); ctx.lineTo(r0, DOOR.y1); ctx.lineTo(ext(gr) + sp * 2.5, Y2); ctx.lineTo(ext(gl) - sp * 2.5, Y2); ctx.closePath();
    ctx.fillStyle = linear(ctx, 0, DOOR.y1, 0, Y2, [[0, `rgba(255,205,120,${a * 0.75 * e})`], [0.45, `rgba(255,190,110,${a * 0.32 * e})`], [1, 'rgba(255,180,100,0)']]);
    ctx.fill();
  }
  // glow around the doorway
  ctx.fillStyle = radial(ctx, 200, 1250, 420, [[0, `rgba(255,200,120,${0.22 * e})`], [1, 'rgba(255,200,120,0)']]); ctx.fillRect(-220, 830, 840, 840);
  ctx.restore();
}

// ---- fire
function flamePath(ctx, x, yb, w, h, lean, wob) {
  ctx.beginPath(); ctx.moveTo(x - w / 2, yb);
  ctx.bezierCurveTo(x - w * 0.62, yb - h * 0.35, x - w * 0.2 + lean * 0.45 + wob, yb - h * 0.72, x + lean, yb - h);
  ctx.bezierCurveTo(x + w * 0.2 + lean * 0.45 - wob, yb - h * 0.66, x + w * 0.62, yb - h * 0.35, x + w / 2, yb);
  ctx.quadraticCurveTo(x, yb + w * 0.22, x - w / 2, yb);
}
function fireHeight(f) { return f <= 1 ? 235 * Math.pow(f, 1.45) : 235 + 300 * (f - 1); }
function drawFire(ctx, t, f, C) {
  const fl = flick(t);
  const H = fireHeight(f), yb = 1418;
  // interior glow on firebox walls
  ctx.save(); fireboxPath(ctx); ctx.clip(); ctx.globalCompositeOperation = 'lighter';
  ctx.fillStyle = linear(ctx, 0, 1470, 0, FB.y0, [[0, `rgba(255,120,45,${(0.14 + 0.2 * Math.min(f, 1.5)) * fl})`], [0.55, `rgba(255,100,35,${(0.05 + 0.08 * Math.min(f, 1.5)) * fl})`], [1, 'rgba(255,90,30,0)']]);
  ctx.fillRect(FB.x0, FB.y0, 310, 360); ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  // ember bed
  const ember = clamp(0.55 + 0.45 * f, 0, 1.4);
  for (let i = 0; i < 26; i++) {
    const ex = 1452 + h1(i * 13 + 1) * 150, ey = 1446 + h1(i * 13 + 2) * 18, b = noise1(t * 0.6 + i * 1.7, 5);
    ctx.fillStyle = rgba(255, 90 + 90 * b, 30 + 30 * b, (0.25 + 0.55 * b) * ember);
    ctx.beginPath(); ctx.ellipse(ex, ey, 7 + h1(i * 13 + 3) * 7, 3.5 + h1(i) * 2.5, 0, 0, 7); ctx.fill();
  }
  // back flames
  const back = f < 0.5 ? 4 : 6;
  for (let i = 0; i < back; i++) {
    const u = (i + 0.5) / back, x = lerp(1460, 1592, u) + Math.sin(t * 0.7 + i) * 4;
    const prof = 0.55 + 0.45 * Math.sin(u * Math.PI);
    const h = H * prof * (0.62 + 0.38 * noise1(t * 1.5 + i * 3.1, 1));
    const w = (40 + 34 * Math.min(f, 2)) * (0.8 + 0.3 * h1(i * 7));
    const lean = (noise1(t * 0.9 + i * 5.3, 2) - 0.5) * w * 0.9 + (u - 0.5) * (f > 1 ? 50 * (f - 1) : 0);
    const wob = Math.sin(t * 2.6 + i * 1.9) * w * 0.25;
    flamePath(ctx, x, yb, w, h, lean, wob);
    ctx.fillStyle = linear(ctx, 0, yb, 0, yb - h, [[0, 'rgba(230,80,25,0.75)'], [0.45, 'rgba(220,70,25,0.45)'], [1, 'rgba(180,40,15,0)']]); ctx.fill();
  }
  ctx.restore();
  blit(ctx, C.logs);
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  const lg = clamp((0.35 + 0.5 * f) * (0.85 + 0.15 * noise1(t * 0.8, 7)), 0, 1.2) - LOG_GLOW0;
  if (lg > 0.01) blit(ctx, C.logsGlow, lg);
  // front + core flames
  const mid = f < 0.5 ? 3 : 7;
  for (let i = 0; i < mid; i++) {
    const u = (i + 0.5) / mid, x = lerp(1470, 1585, u);
    const prof = 0.5 + 0.5 * Math.sin(u * Math.PI);
    const h = H * 0.72 * prof * (0.6 + 0.4 * noise1(t * 1.9 + i * 2.3, 3));
    const w = (26 + 22 * Math.min(f, 2)) * (0.8 + 0.3 * h1(i * 11 + 5));
    const lean = (noise1(t * 1.1 + i * 4.1, 4) - 0.5) * w;
    flamePath(ctx, x, yb - 4, w, h, lean, Math.sin(t * 3.1 + i * 2.2) * w * 0.3);
    ctx.fillStyle = linear(ctx, 0, yb - 4, 0, yb - 4 - h, [[0, 'rgba(255,170,60,0.85)'], [0.5, 'rgba(255,130,40,0.4)'], [1, 'rgba(255,100,30,0)']]); ctx.fill();
  }
  const core = f < 0.5 ? 2 : 5;
  for (let i = 0; i < core; i++) {
    const u = (i + 0.5) / core, x = lerp(1485, 1570, u);
    const h = H * 0.4 * (0.6 + 0.4 * noise1(t * 2.2 + i * 1.7, 6));
    const w = 20 + 14 * Math.min(f, 2);
    flamePath(ctx, x, yb, w, h, (noise1(t * 1.3 + i, 8) - 0.5) * w * 0.8, 0);
    ctx.fillStyle = linear(ctx, 0, yb, 0, yb - h, [[0, 'rgba(255,235,170,0.8)'], [0.5, 'rgba(255,200,110,0.35)'], [1, 'rgba(255,170,80,0)']]); ctx.fill();
  }
  ctx.globalCompositeOperation = 'source-over';
  blit(ctx, C.logsF);
  ctx.globalCompositeOperation = 'lighter';
  const lg2 = clamp((0.35 + 0.5 * f) * (0.85 + 0.15 * noise1(t * 0.8 + 3, 7)), 0, 1.2) - LOG_GLOW0;
  if (lg2 > 0.01) blit(ctx, C.logsFGlow, lg2);
  // sparks
  const nS = Math.floor(6 + 10 * f);
  for (let i = 0; i < nS; i++) {
    const per = 2.2 + h1(i * 17 + 3) * 1.8, ph = ((t / per + h1(i * 17 + 4)) % 1 + 1) % 1;
    const rise = 180 + 200 * f;
    const x = 1470 + h1(i * 17 + 5) * 110 + Math.sin(t * 1.3 + i) * 18 * ph + (h1(i * 17 + 6) - 0.5) * 60 * ph;
    const y = 1400 - ph * rise;
    if (f <= 1.3 && y < FB.y0 + 30) continue;
    const a = Math.sin(ph * Math.PI) * 0.9;
    ctx.fillStyle = rgba(255, 180, 90, a); ctx.beginPath(); ctx.arc(x, y, 2 + h1(i) * 1.5, 0, 7); ctx.fill();
  }
  ctx.restore();
}

function drawCandleFlame(ctx, t, x, y, scale = 1, glowSp) {
  const s = scale, sw = Math.sin(t * 1.7) * 1.2 + (noise1(t * 1.1, 9) - 0.5) * 2;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  if (glowSp) { ctx.globalAlpha = 0.55; ctx.drawImage(glowSp, x - 70 * s, y - 80 * s, 140 * s, 140 * s); ctx.globalAlpha = 1; }
  flamePath(ctx, x, y, 11 * s, (30 + 3 * Math.sin(t * 2.3)) * s, sw * s, 0);
  ctx.fillStyle = linear(ctx, 0, y, 0, y - 32 * s, [[0, 'rgba(255,200,120,0.95)'], [0.4, 'rgba(255,230,170,0.9)'], [1, 'rgba(255,170,80,0)']]); ctx.fill();
  ctx.fillStyle = 'rgba(120,150,255,0.25)'; ctx.beginPath(); ctx.ellipse(x, y - 3 * s, 3.5 * s, 4 * s, 0, 0, 7); ctx.fill();
  ctx.restore();
}

function drawBack(ctx, t, o0) {
  const o = opts(o0), C = getCache(), V = visRect(ctx);
  const fl = flick(t), f = o.fire;
  // 1. window view
  if (V.x1 > WIN.x - WIN.r && V.x0 < WIN.x + WIN.r && V.y1 > WIN.y - WIN.r && V.y0 < WIN.y + WIN.r) {
    if (o.viewFn) {
      ctx.save(); ctx.beginPath(); ctx.arc(WIN.x, WIN.y, WIN.r + 1, 0, Math.PI * 2); ctx.clip();
      ctx.fillStyle = '#6a5a4a'; ctx.fillRect(WIN.x - WIN.r, WIN.y - WIN.r, WIN.r * 2, WIN.r * 2);
      o.viewFn(ctx, WIN.x, WIN.y, WIN.r); ctx.restore();
    } else {
      const vc = C.views[o.view] || C.views.kitchen;
      ctx.drawImage(vc, WIN.x - 303, WIN.y - 303, 606, 606);
      if (o.view === 'night') { // a few windows slowly switching
        ctx.save(); ctx.beginPath(); ctx.arc(WIN.x, WIN.y, WIN.r, 0, 7); ctx.clip();
        for (let i = 0; i < 4; i++) { const a = smooth(0.3, 0.7, noise1(t * 0.15 + i * 9, 12)); ctx.fillStyle = `rgba(255,205,130,${a * 0.8})`; ctx.fillRect(WIN.x - 230 + i * 130 + h1(i) * 40, WIN.y + 150 + h1(i + 9) * 80, 6, 8); }
        ctx.restore();
      }
    }
  }
  // 2. beyond the door
  if (o.doorOpen > 0.001) drawBeyond(ctx, o.doorOpen);
  else { ctx.save(); doorwayPath(ctx, -5); ctx.fillStyle = '#3a2618'; ctx.fill(); ctx.restore(); }
  // 3. the static room
  drawRoom(ctx, C.room, V);
  // 4. props that can be hidden
  if (o.chairs.c700) blit(ctx, C.chair700);
  if (o.chairs.c960) blit(ctx, C.chair960);
  if (o.chairs.c1100) blit(ctx, C.chair1100);
  if (!o.bellowsHidden) blit(ctx, C.bellows);
  // 5. door leaf
  const door = drawDoorLeaf(ctx, o.doorOpen, t);
  // 6. Sadness's corner shade is baked into the cache; cornerLight lifts it (step 8)
  // 7. overall room level vs. fire (gentle)
  const dim = dimAmount(f);
  ctx.save();
  if (dim > 0.001) {
    ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = dim; ctx.fillStyle = DIM_COLOR;
    ctx.beginPath(); ctx.rect(V.x0 - 10, V.y0 - 10, V.x1 - V.x0 + 20, V.y1 - V.y0 + 20);
    if (o.doorOpen > 0.001) doorwayPath(ctx, 0, true);
    ctx.fill('evenodd'); ctx.globalAlpha = 1;
  }
  // flickering firelight on the room (low frequency, smooth)
  ctx.globalCompositeOperation = 'screen';
  // (the steady hot glow around the hearth is baked into the cache; only its gentle
  //  breathing is added here as a cheap linear wash from the hearth side of the room)
  const fa = clamp(0.035 * Math.min(f, 1.5) * (fl - 0.9) / 0.2, 0, 0.06) + (f > 1 ? 0.07 * (f - 1) : 0);
  if (fa > 0.002) {
    ctx.fillStyle = linear(ctx, FIRE.x + 100, 0, FIRE.x - 1500, 0, [[0, rgba(255, 145, 65, fa)], [0.35, rgba(255, 140, 60, fa * 0.55)], [1, 'rgba(255,130,55,0)']]);
    ctx.fillRect(V.x0 - 4, V.y0 - 4, V.x1 - V.x0 + 8, V.y1 - V.y0 + 8);
  }
  ctx.restore();
  // 8. fire, candle, lantern, fairy lights, door light
  drawFire(ctx, t, f, C);
  if (o.candle) drawCandleFlame(ctx, t, 1730, 862, 1, C.glow);
  if (o.cornerLight > 0.001) {
    const k = o.cornerLight;
    ctx.save(); ctx.globalCompositeOperation = 'screen';
    ctx.translate(-60, 1650); ctx.scale(1, 0.66);
    ctx.fillStyle = radial(ctx, -110 * 0, 0, 640, [[0, rgba(255, 196, 120, 0.42 * k * (0.97 + 0.03 * fl))], [0.18, rgba(255, 190, 115, 0.3 * k)], [0.55, rgba(255, 175, 105, 0.16 * k)], [1, 'rgba(255,160,90,0)']]);
    ctx.fillRect(-660, -660, 1320, 1320); ctx.restore();
    ctx.save(); ctx.globalAlpha = k; drawCandleFlame(ctx, t + 3, -170, 1586, 0.7, C.glow); ctx.restore();
  }
  if (o.steam > 0.01) drawSteam(ctx, t, TEA.x, TEA.y - 48, o.steam * (0.7 + 0.3 * o.cornerLight));
  drawFairy(ctx, t, C, o.fairy);
  if (o.doorOpen > 0.001) drawDoorLight(ctx, o.doorOpen, door.freeBottom);
}
function drawSteam(ctx, t, x, y, a) {
  ctx.save(); ctx.lineCap = 'round';
  for (let i = 0; i < 3; i++) {
    const ph = ((t * 0.18 + i / 3) % 1);
    ctx.beginPath();
    for (let k = 0; k <= 12; k++) { const s = k / 12, yy = y - s * 90 - ph * 30, xx = x + (i - 1) * 8 + Math.sin(s * 5 + t * 0.9 + i * 2) * 8 * s; k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); }
    ctx.strokeStyle = `rgba(235,225,215,${0.14 * a * Math.sin(Math.PI * (0.2 + 0.8 * (1 - ph)))})`; ctx.lineWidth = 5; ctx.stroke();
  }
  ctx.restore();
}
function drawFairy(ctx, t, C, amt) {
  if (amt <= 0) return;
  ctx.save();
  ctx.strokeStyle = 'rgba(40,30,22,0.7)'; ctx.lineWidth = 1.6; ctx.beginPath();
  C.wire.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
  ctx.globalCompositeOperation = 'lighter';
  for (const b of C.fairy) {
    const tw = 0.6 + 0.4 * Math.sin(t * b.sp * 6.283 + b.ph);
    ctx.globalAlpha = amt * (0.35 + 0.45 * tw);
    ctx.drawImage(C.glow, b.x - 22, b.y - 18, 44, 44);
    ctx.globalAlpha = amt * (0.7 + 0.3 * tw);
    ctx.fillStyle = b.warm < 0.5 ? '#ffe2a6' : '#ffd08a'; ctx.beginPath(); ctx.arc(b.x, b.y + 4, 3.2, 0, 7); ctx.fill();
  }
  ctx.restore();
}

function drawFront(ctx, t, o0) {
  const o = opts(o0), C = getCache();
  blit(ctx, C.table);
  const dim = dimAmount(o.fire);
  if (dim > 0.001) blit(ctx, C.tableDim, dim);
  // firelight flicker on the table's right edge
  const fl = flick(t);
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  ctx.beginPath(); ctx.ellipse(800, 1360, 300, 70, 0, 0, Math.PI * 2); ctx.clip();
  ctx.fillStyle = radial(ctx, 1080, 1340, 380, [[0, rgba(255, 150, 70, (0.04 + 0.05 * o.fire) * fl)], [1, 'rgba(255,150,70,0)']]); ctx.fillRect(500, 1280, 610, 160);
  ctx.restore();
}

// ================================================================ lighting
const VIEW_RIM = { kitchen: '#e8c9a0', night: '#a8b8d8', dawn: '#f2c8b0', nana: '#ffe2a8' };
function angTo(x0, y0, x1, y1) { return Math.atan2(y1 - y0, x1 - x0); }
function lerpAng(a, b, t) { let d = b - a; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI; return a + d * t; }
function lightAt(x, y, t, o0) {
  const o = opts(o0), f = o.fire, fl = flick(t);
  const cy = y - 380; // roughly chest height of the character
  const dF = Math.hypot(FIRE.x - x, FIRE.y - cy);
  const fall = 1 / (1 + (dF / 1100) ** 2);
  let keyAmt = clamp((0.3 + 0.55 * fall) * (0.45 + 0.55 * Math.min(f, 1.6)) * (0.97 + 0.03 * fl * fl), 0.25, 0.95);
  let keyDir = angTo(x, cy, FIRE.x, FIRE.y);
  let keyColor = mixHex('#ffc890', '#ffa860', clamp(f - 0.5, 0, 1));
  // window rim
  const view = o.viewFn ? 'kitchen' : o.view;
  let rimColor = VIEW_RIM[view] || VIEW_RIM.kitchen;
  let rimDir = angTo(x, cy, WIN.x, WIN.y);
  const dW = Math.hypot(WIN.x - x, WIN.y - cy);
  let rimAmt = clamp(0.18 + 0.3 / (1 + (dW / 700) ** 2), 0.2, 0.5);
  // characters standing near the fire get a fire rim too
  if (Math.abs(x - FIRE.x) < 500 && rimAmt < 0.35) { rimDir = angTo(x, cy, FIRE.x, FIRE.y); rimColor = '#ffb070'; rimAmt = 0.35 * Math.min(1, f + 0.2); }
  let shadowAmt = clamp(0.36 - 0.08 * (f - 1), 0.22, 0.48), shadowColor = '#3b2c3e';
  let ambient = mixHex('#a99ab8', '#ffd9b8', clamp(f / 1.2, 0, 1)), ambientAmt = 0.16 + 0.06 * Math.abs(1 - f);
  // open door: warm rim from behind-left
  if (o.doorOpen > 0.01) {
    const dD = Math.hypot(200 - x, 1200 - cy), w = o.doorOpen * clamp(1 - dD / 1200, 0, 1);
    if (w > 0.1 && w * 0.6 > rimAmt * 0.6) { rimDir = lerpAng(rimDir, angTo(x, cy, 200, 1200), clamp(w * 1.5, 0, 1)); rimColor = mixHex(rimColor, '#ffd090', clamp(w * 1.5, 0, 1)); rimAmt = Math.max(rimAmt, 0.5 * w + 0.2); }
  }
  // Sadness's corner: dimmer and cooler, warmed by cornerLight (lantern)
  const cf = clamp(1 - Math.hypot((x - 110) / 420, (y - 1700) / 260), 0, 1);
  if (cf > 0) {
    const k = o.cornerLight, sh = cf * (1 - k);
    keyAmt = Math.max(0.25, keyAmt - 0.18 * sh);
    shadowAmt = clamp(shadowAmt + 0.12 * sh, 0, 0.55);
    ambient = mixHex(ambient, '#8f90b8', 0.5 * sh); ambientAmt = clamp(ambientAmt + 0.06 * sh, 0, 0.32);
    if (k > 0) {
      const lw = cf * k; keyDir = lerpAng(keyDir, angTo(x, cy, -170, 1590), lw);
      keyColor = mixHex(keyColor, '#ffc27e', lw); keyAmt = clamp(keyAmt + 0.25 * lw, 0.25, 0.95);
      ambient = mixHex(ambient, '#ffd9b0', lw * 0.7);
    }
  }
  return { keyDir, keyColor, keyAmt, rimDir, rimColor, rimAmt, shadowColor, shadowAmt, ambient, ambientAmt };
}

// ================================================================ visions
// drawVision(ctx, t, v)
//   v.kind 'words'   {items:[{text,t0}], alpha}
//          'tiger'   {p:0..1, alpha}
//          'coaster' {p:0..1, alpha}
//          'water'   {p:0..1, alpha, x=1525, y=600, scale=1}
const VC = { x: 1525, y: 600, w: 520, h: 700 };
// Glows are never done with shadowBlur (very slow on the CPU rasteriser): the shape is
// rendered small, blurred with ctx.filter on that small canvas, and drawn back upscaled.
const LOW = {};
function lowres(name, w, h) {
  let L = LOW[name];
  if (!L || L.c.width !== w || L.c.height !== h) { const c = createCanvas(w, h); L = LOW[name] = { c, g: c.getContext('2d') }; }
  const g = L.g; g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.filter = 'none';
  g.clearRect(0, 0, w, h); return g;
}
// blurred, downsampled copy of a canvas (k = scale factor, blurPx in the small canvas' pixels)
function blurCopy(name, src, k, blurPx) {
  const pad = Math.ceil(blurPx * 2.5);
  const w = Math.ceil(src.width * k) + pad * 2, h = Math.ceil(src.height * k) + pad * 2;
  const g = lowres(name, w, h);
  g.filter = `blur(${blurPx}px)`; g.drawImage(src, pad, pad, src.width * k, src.height * k); g.filter = 'none';
  return { c: LOW[name].c, pad: pad / k };
}
function staticGlow(src, k, blurPx) { // same, but returns a new canvas (for caches)
  const pad = Math.ceil(blurPx * 2.5);
  const c = createCanvas(Math.ceil(src.width * k) + pad * 2, Math.ceil(src.height * k) + pad * 2), g = c.getContext('2d');
  g.filter = `blur(${blurPx}px)`; g.drawImage(src, pad, pad, src.width * k, src.height * k); g.filter = 'none';
  return { c, pad: pad / k };
}

const HZK = 0.16; // smoke haze resolution, px per world unit
function smokeBackdrop(ctx, t, A, cx, cy, w, h, n, seed, tint) {
  const C = getCache(); const spread = 1 + (1 - A) * 0.9;
  const bw = w * spread + 260, bh = h * spread + 260;
  const MW = Math.ceil((w * 1.9 + 260) * HZK), MH = Math.ceil((h * 1.9 + 260) * HZK);
  const g = lowres('haze', MW, MH);
  g.setTransform(HZK, 0, 0, HZK, MW / 2 - cx * HZK, MH / 2 - cy * HZK);
  for (let i = 0; i < n; i++) {
    const hx = h1(seed + i * 3), hy = h1(seed + i * 3 + 1), hs = h1(seed + i * 3 + 2);
    const drift = t * (6 + 8 * hs), yy = (((hy * h - drift) % h) + h) % h;
    const x = cx + ((hx - 0.5) * w * 0.9 + Math.sin(t * 0.2 + i) * 14) * spread;
    const y = cy + (yy - h / 2) * spread;
    const sz = (110 + 130 * hs) * spread;
    g.globalAlpha = A * A * (0.35 + 0.3 * hs) * Math.sin(Math.PI * clamp(yy / h, 0, 1));
    g.drawImage(C.smoke, x - sz / 2, y - sz / 2, sz, sz);
  }
  if (tint) {
    g.globalCompositeOperation = 'lighter'; g.globalAlpha = A * 0.5;
    g.fillStyle = radial(g, cx, cy, Math.max(w, h) * 0.6, [[0, tint], [1, 'rgba(255,100,40,0)']]);
    g.fillRect(cx - w, cy - h, w * 2, h * 2);
  }
  const sw = Math.min(MW, Math.ceil(bw * HZK)), sh = Math.min(MH, Math.ceil(bh * HZK));
  ctx.drawImage(LOW.haze.c, (MW - sw) / 2, (MH - sh) / 2, sw, sh, cx - sw / HZK / 2, cy - sh / HZK / 2, sw / HZK, sh / HZK);
}
function sparks(ctx, t, A, pts, n, seed, col = [255, 170, 80]) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < n; i++) {
    const p = pts[Math.floor(h1(seed + i) * pts.length)]; if (!p) continue;
    const per = 1.6 + h1(seed + i * 7) * 1.6, ph = ((t / per + h1(seed + i * 5)) % 1 + 1) % 1;
    const x = p[0] + (h1(seed + i * 11) - 0.5) * 30 + Math.sin(t + i) * 6, y = p[1] - ph * 60;
    ctx.fillStyle = rgba(col[0], col[1], col[2], A * Math.sin(Math.PI * ph) * 0.9);
    ctx.beginPath(); ctx.arc(x, y, 1.6 + h1(seed + i * 13) * 1.6, 0, 7); ctx.fill();
  }
  ctx.restore();
}

// cached ember glow behind a line of text
const WORD_GLOW = new Map();
function wordGlow(txt, size) {
  const key = size + '|' + txt; let G = WORD_GLOW.get(key);
  if (G) return G;
  const k = 0.3, blur = 3.2, pad = 40;
  const m = createCanvas(4, 4).getContext('2d'); m.font = `bold ${size}px Inter`;
  const tw = m.measureText(txt).width;
  const c = createCanvas(Math.ceil((tw + pad * 2) * k), Math.ceil((size * 1.4 + pad * 2) * k)), g = c.getContext('2d');
  g.scale(k, k); g.font = `bold ${size}px Inter`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillStyle = 'rgba(255,110,35,1)';
  g.filter = `blur(${blur}px)`; g.globalAlpha = 0.55; g.fillText(txt, tw / 2 + pad, size * 0.7 + pad);
  g.filter = `blur(${blur * 0.3}px)`; g.globalAlpha = 0.9; g.fillText(txt, tw / 2 + pad, size * 0.7 + pad);
  g.filter = 'none'; g.globalAlpha = 1;
  G = { c, w: tw + pad * 2, h: size * 1.4 + pad * 2 }; WORD_GLOW.set(key, G);
  if (WORD_GLOW.size > 200) WORD_GLOW.delete(WORD_GLOW.keys().next().value);
  return G;
}
function wordLayout(ctx, all) {
  const maxW = VC.w - 40, base = 70; const lines = [];
  for (const it of all) {
    ctx.font = `bold ${base}px Inter`;
    let size = base, w = ctx.measureText(it.text).width, parts = [it.text];
    if (w > maxW) {
      const words = it.text.split(' ');
      if (words.length > 1 && w * 60 / base > maxW) {
        let best = 1, bw = 1e9;
        for (let k = 1; k < words.length; k++) { const a = ctx.measureText(words.slice(0, k).join(' ')).width, b = ctx.measureText(words.slice(k).join(' ')).width; if (Math.max(a, b) < bw) { bw = Math.max(a, b); best = k; } }
        parts = [words.slice(0, best).join(' '), words.slice(best).join(' ')]; w = bw;
      }
      if (w > maxW) size = Math.max(44, Math.floor(base * maxW / w));
    }
    lines.push({ it, parts, size });
  }
  return lines;
}
function visionWords(ctx, t, v, A) {
  const all = v.items || [];
  smokeBackdrop(ctx, t, A, VC.x, VC.y, VC.w, VC.h, 16, 101, 'rgba(255,110,40,0.10)');
  if (!all.some(it => t >= (it.t0 ?? 0))) return;
  ctx.save();
  // lay out every item (future ones too) so words never shift when later ones appear
  const lines = wordLayout(ctx, all);
  const gap = 22; let total = -gap; for (const L of lines) total += L.parts.length * L.size * 1.12 + gap;
  let y = VC.y - total / 2;
  const C = getCache();
  for (let i = 0; i < lines.length; i++) {
    const L = lines[i], it = L.it, h = L.parts.length * L.size * 1.12;
    const age = t - (it.t0 ?? 0);
    if (age >= 0) {
      const k = smooth(0, 1.1, age);
      const dx = Math.sin(t * 0.45 + i * 1.7) * 5, dy = Math.sin(t * 0.33 + i * 2.3) * 4 - (1 - k) * 18;
      // wisps of smoke gathering into the word
      if (k < 1) for (let s = 0; s < 8; s++) {
        const ang = h1(i * 31 + s) * 6.283, rad = (40 + 160 * h1(i * 31 + s + 7)) * (1 - k);
        const px = VC.x + (h1(i * 17 + s) - 0.5) * 300 + Math.cos(ang + t * 0.3) * rad, py = y + h / 2 + Math.sin(ang + t * 0.3) * rad * 0.5;
        ctx.globalAlpha = A * (1 - k) * 0.5; const sz = 90 + 60 * (1 - k);
        ctx.drawImage(C.smoke, px - sz / 2, py - sz / 2, sz, sz);
      }
      ctx.globalAlpha = 1;
      L.parts.forEach((txt, j) => {
        const ly = y + (j + 0.5) * L.size * 1.12 + dy, lx = VC.x + dx;
        const grow = 1 + 0.12 * (1 - k);
        // ember haze (big + soft while condensing, tighter once formed)
        const G = wordGlow(txt, L.size), gs = grow * (1 + 0.12 * (1 - k));
        ctx.globalCompositeOperation = 'lighter';
        ctx.globalAlpha = A * (0.35 + 0.5 * k) * smooth(0, 0.35, age);
        ctx.drawImage(G.c, lx - G.w * gs / 2, ly - G.h * gs / 2, G.w * gs, G.h * gs);
        ctx.globalCompositeOperation = 'source-over';
        ctx.globalAlpha = A * k * k;
        ctx.save(); ctx.translate(lx, ly); ctx.scale(grow, grow);
        ctx.font = `bold ${L.size}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillStyle = linear(ctx, 0, -L.size * 0.5, 0, L.size * 0.5, [[0, '#ffe7b0'], [0.55, '#ffb35c'], [1, '#f07a32']]);
        ctx.fillText(txt, 0, 0);
        ctx.restore();
      });
      ctx.globalAlpha = 1;
      sparks(ctx, t, A * (0.4 + 0.6 * k), [[VC.x - 120, y + h], [VC.x, y + h], [VC.x + 120, y + h]], 5, 300 + i * 19);
    }
    y += h + gap;
  }
  ctx.restore();
}

// ---- tiger
function capsule(g, x0, y0, x1, y1, r0, r1) {
  const a = Math.atan2(y1 - y0, x1 - x0), n = a + Math.PI / 2;
  g.beginPath();
  g.moveTo(x0 + Math.cos(n) * r0, y0 + Math.sin(n) * r0); g.lineTo(x1 + Math.cos(n) * r1, y1 + Math.sin(n) * r1);
  g.arc(x1, y1, r1, n, n + Math.PI, true); g.lineTo(x0 - Math.cos(n) * r0, y0 - Math.sin(n) * r0);
  g.arc(x0, y0, r0, n + Math.PI, n, true); g.closePath(); g.fill();
}
function limb(g, sx, sy, a1, a2, l1, l2, w1, w2, pawW) {
  const ex = sx + Math.cos(a1) * l1, ey = sy + Math.sin(a1) * l1, px = ex + Math.cos(a2) * l2, py = ey + Math.sin(a2) * l2;
  capsule(g, sx, sy, ex, ey, w1, w2); capsule(g, ex, ey, px, py, w2, w2 * 0.8);
  g.beginPath(); g.ellipse(px + Math.cos(a2) * 4, py + Math.sin(a2) * 4, pawW, pawW * 0.7, a2 - Math.PI / 2, 0, 7); g.fill();
  return [[sx, sy], [ex, ey], [px, py]];
}
function tigerPose(p) {
  // keyframes of joint angles (radians, y down; 0 = forward/+x, PI/2 = down)
  const K = [
    { p: 0.0, fa1: 1.75, fa2: 1.2, ha1: 0.55, ha2: 2.55, body: -0.0, crouch: 1, tail: [-0.2, 0.9], head: 0.25 },
    { p: 0.22, fa1: 0.9, fa2: 1.2, ha1: 1.9, ha2: 2.2, body: -0.38, crouch: 0.3, tail: [0.2, 0.4], head: -0.05 },
    { p: 0.5, fa1: 0.15, fa2: 0.25, ha1: 2.9, ha2: 3.0, body: 0.0, crouch: 0, tail: [0.5, -0.3], head: 0.0 },
    { p: 0.78, fa1: 0.75, fa2: 1.0, ha1: 2.6, ha2: 2.7, body: 0.3, crouch: 0, tail: [0.2, -0.6], head: -0.15 },
    { p: 1.0, fa1: 1.35, fa2: 1.55, ha1: 1.25, ha2: 1.9, body: 0.08, crouch: 0.2, tail: [-0.1, -0.9], head: -0.1 },
  ];
  let i = 0; while (i < K.length - 2 && p > K[i + 1].p) i++;
  const a = K[i], b = K[i + 1], u = smooth(a.p, b.p, p);
  const L = k => lerp(a[k], b[k], u);
  return { fa1: L('fa1'), fa2: L('fa2'), ha1: L('ha1'), ha2: L('ha2'), body: L('body'), crouch: L('crouch'), tail: [lerp(a.tail[0], b.tail[0], u), lerp(a.tail[1], b.tail[1], u)], head: L('head'), stretch: Math.sin(Math.PI * clamp(p, 0, 1)) };
}
function drawTigerShape(g, P, t, mode) {
  // mode 'mask' fills solid; 'stripes' draws stripes; local frame: facing +x, origin mid-body, ~300 long
  const st = P.stretch, cr = P.crouch;
  const Lx = 1 + 0.12 * st, low = cr * 14;
  const sh = [88 * Lx, -6 + low], hip = [-92 * Lx, -2 + low * 0.6];
  if (mode === 'mask') {
    // tail (tapered, sampled bezier)
    const t0 = [-128 * Lx, -18 + low], sw = Math.sin(t * 2.2) * 0.15;
    const c1 = [t0[0] - 60, t0[1] - 60 * (P.tail[0] + sw)], c2 = [t0[0] - 110, t0[1] - 90 * (P.tail[1] + sw)], e = [t0[0] - 150, t0[1] - 70 * (P.tail[1] + sw) - 10];
    for (let i = 0; i < 16; i++) {
      const s0 = i / 16, s1 = (i + 1) / 16;
      const bz = s => { const m = 1 - s; return [m * m * m * t0[0] + 3 * m * m * s * c1[0] + 3 * m * s * s * c2[0] + s * s * s * e[0], m * m * m * t0[1] + 3 * m * m * s * c1[1] + 3 * m * s * s * c2[1] + s * s * s * e[1]]; };
      const A = bz(s0), B = bz(s1); capsule(g, A[0], A[1], B[0], B[1], lerp(13, 8, s0), lerp(13, 8, s1));
    }
    g.__tail = [t0, c1, c2, e];
    // far legs (slightly offset)
    limb(g, sh[0] - 10, sh[1] + 10, P.fa1 + 0.25, P.fa2 + 0.2, 60, 58, 20, 14, 16);
    limb(g, hip[0] + 10, hip[1] + 12, P.ha1 - 0.25, P.ha2 - 0.2, 64, 62, 26, 14, 16);
    // torso
    g.beginPath();
    g.moveTo(-142 * Lx, -10 + low);
    g.bezierCurveTo(-134 * Lx, -58 + low * 0.3, -60 * Lx, -54 - cr * 6, 0, -50 + (1 - st) * 2);
    g.bezierCurveTo(60 * Lx, -48, 100 * Lx, -64 + low, 130 * Lx, -48 + low);
    g.bezierCurveTo(146 * Lx, -14 + low, 138 * Lx, 38 + low, 108 * Lx, 46 + low);
    g.bezierCurveTo(40 * Lx, 54 - st * 10 + low, -40 * Lx, 50 - st * 12 + low, -112 * Lx, 42 + low * 0.5);
    g.bezierCurveTo(-156 * Lx, 32, -158 * Lx, 6, -142 * Lx, -10 + low);
    g.closePath(); g.fill();
    // near legs
    g.__fl = limb(g, sh[0], sh[1] + 6, P.fa1, P.fa2, 62, 60, 24, 15, 18);
    g.__hl = limb(g, hip[0], hip[1] + 8, P.ha1, P.ha2, 66, 64, 31, 15, 18);
    // head
    g.save(); g.translate(150 * Lx, -42 + low * 1.6); g.rotate(P.head);
    g.beginPath(); g.ellipse(0, 0, 46, 40, 0, 0, 7); g.fill();
    g.beginPath(); g.ellipse(34, 14, 27, 21, 0.15, 0, 7); g.fill();               // muzzle
    g.beginPath(); g.moveTo(-34, 4); g.lineTo(-48, 24); g.lineTo(-20, 28); g.closePath(); g.fill(); // cheek ruff
    g.beginPath(); g.moveTo(-26, -20); g.quadraticCurveTo(-30, -52, -8, -36); g.closePath(); g.fill(); // ear
    g.beginPath(); g.moveTo(-6, -30); g.quadraticCurveTo(0, -60, 16, -32); g.closePath(); g.fill();
    g.restore();
  } else {
    // stripes: dark tapered wedges across the body, legs and tail
    const stripe = (x, y0, y1, w, bend) => { g.beginPath(); g.moveTo(x - w, y0); g.quadraticCurveTo(x + bend - w * 0.3, (y0 + y1) / 2, x + bend * 1.6, y1); g.quadraticCurveTo(x + bend + w * 0.6, (y0 + y1) / 2, x + w, y0); g.closePath(); g.fill(); };
    for (let i = 0; i < 10; i++) { const x = (-122 + i * 24 + (h1(i * 5) - 0.5) * 8) * Lx; stripe(x, -64, -14 + (i % 2) * 22 + h1(i * 9) * 16, 4 + 4 * h1(i * 3), -10 + h1(i * 7) * 8); }
    for (let i = 0; i < 5; i++) { const x = (-100 + i * 40) * Lx; stripe(x, 46, 18, 5, 6); }
    // legs bands
    for (const Lg of [g.__fl, g.__hl]) { if (!Lg) continue; for (let k = 1; k <= 3; k++) { const s = k / 4, a = Lg[0], b = Lg[1]; const x = lerp(a[0], b[0], s), y = lerp(a[1], b[1], s), an = Math.atan2(b[1] - a[1], b[0] - a[0]) + Math.PI / 2; g.save(); g.translate(x, y); g.rotate(an); g.fillRect(-16, -2.5, 20, 5); g.restore(); } }
    // tail rings
    const T = g.__tail; if (T) for (let k = 2; k < 9; k++) { const s = k / 9, m = 1 - s; const x = m * m * m * T[0][0] + 3 * m * m * s * T[1][0] + 3 * m * s * s * T[2][0] + s * s * s * T[3][0], y = m * m * m * T[0][1] + 3 * m * m * s * T[1][1] + 3 * m * s * s * T[2][1] + s * s * s * T[3][1]; g.beginPath(); g.arc(x, y, 6, 0, 7); g.fill(); }
    // head marks
    g.save(); g.translate(150 * Lx, -42 + low * 1.6); g.rotate(P.head);
    for (const [x, y, a] of [[-6, -26, 0.3], [6, -28, -0.2], [-22, -10, 0.9], [-24, 8, 1.2]]) { g.save(); g.translate(x, y); g.rotate(a); g.fillRect(-3, -8, 6, 16); g.restore(); }
    g.restore();
  }
}
let BUSH = null;
function bushSprites() {
  if (BUSH) return BUSH;
  const bx = 1400, by = 912, x0 = bx - 200, y0 = by - 190;
  const clumps = [];
  for (let i = 0; i < 11; i++) {
    const u = i / 10, a = Math.PI + u * Math.PI;
    clumps.push([bx + Math.cos(a) * 135 + (h1(i + 3) - 0.5) * 20, by + Math.sin(a) * 92 * (0.75 + 0.3 * h1(i + 8)) + 18, 34 + 18 * h1(i + 5)]);
  }
  for (let i = 0; i < 6; i++) clumps.push([bx + (h1(i + 21) - 0.5) * 170, by - 40 - h1(i + 33) * 40, 36 + 14 * h1(i + 44)]);
  const path = (g, shrink) => { g.beginPath(); for (const [x, y, r] of clumps) { const rr = Math.max(1, r - shrink); g.moveTo(x + rr, y); g.arc(x, y, rr, 0, Math.PI * 2); } g.moveTo(bx - 138 + shrink, by + 12); g.ellipse(bx, by + 12, 138 - shrink, 100 - shrink, 0, Math.PI, Math.PI * 2, false); g.closePath(); };
  const crisp = sprite(x0, y0, x0 + 400, y0 + 230, g => {
    g.fillStyle = 'rgba(255,130,50,0.85)'; path(g, 0); g.fill();
    g.fillStyle = 'rgba(38,16,9,0.95)'; path(g, 4); g.fill();
    g.globalCompositeOperation = 'lighter'; g.strokeStyle = 'rgba(255,130,50,0.35)'; g.lineWidth = 1.6;
    for (const [x, y, r] of clumps) for (let k = 0; k < 3; k++) { const a = -Math.PI / 2 + (k - 1) * 0.7 + (h1(x | 0) - 0.5) * 0.4; g.beginPath(); g.moveTo(x, y + r * 0.4); g.quadraticCurveTo(x + Math.cos(a) * r * 0.3, y + Math.sin(a) * r * 0.2, x + Math.cos(a) * r * 0.75, y + Math.sin(a) * r * 0.75); g.stroke(); }
  }, 1);
  const mask = sprite(x0, y0, x0 + 400, y0 + 230, g => { g.fillStyle = 'rgba(255,110,35,1)'; path(g, 0); g.fill(); }, 1);
  const glow = staticGlow(mask.c, 0.25, 5);
  BUSH = { crisp, glow, x0, y0 };
  return BUSH;
}
const TIGER_PX = 1.0; // offscreen resolution of the tiger (px per world unit)
function visionTiger(ctx, t, v, A) {
  const p = clamp(v.p ?? 0, 0, 1);
  smokeBackdrop(ctx, t, A, VC.x, VC.y + 60, VC.w, VC.h * 0.8, 14, 211, 'rgba(255,100,30,0.10)');
  const scale = 0.92;
  const q = smooth(0, 1, p);
  const px = lerp(1415, 1625, q), py = lerp(850, 840, q) - Math.sin(Math.PI * q) * 330;
  const ang = Math.atan2(lerp(-20, 0, q) - Math.cos(Math.PI * q) * 330 * Math.PI, 235) * 0.35;
  const P = tigerPose(p);
  const k = TIGER_PX, W = Math.ceil(560 * scale * k), H = Math.ceil(460 * scale * k);
  const g = lowres('tiger', W, H);
  const xf = () => { g.setTransform(k * scale, 0, 0, k * scale, W / 2, H / 2); g.rotate(ang + P.body * 0.5); };
  xf(); g.fillStyle = '#fff'; drawTigerShape(g, P, t, 'mask');
  g.globalCompositeOperation = 'source-atop';
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = linear(g, 0, 0, 0, H, [[0, '#ff8a36'], [0.45, '#ffb453'], [0.7, '#ffcf80'], [1, '#ffe2a8']]); g.fillRect(0, 0, W, H);
  xf(); g.fillStyle = 'rgba(70,22,8,0.85)'; drawTigerShape(g, P, t, 'stripes');
  g.save(); g.translate(150 * (1 + 0.12 * P.stretch), -42 + P.crouch * 22); g.rotate(P.head);
  g.fillStyle = '#fff6c8'; g.beginPath(); g.ellipse(12, -8, 6, 3.5, -0.2, 0, 7); g.fill(); g.restore();
  // smoky variation inside the body
  g.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < 6; i++) { const x = W * (0.2 + 0.6 * noise1(t * 0.3 + i * 3, 31)), y = H * (0.3 + 0.4 * noise1(t * 0.25 + i * 5, 32)); g.fillStyle = radial(g, x, y, W * 0.12, [[0, 'rgba(90,30,10,0.35)'], [1, 'rgba(90,30,10,0)']]); g.fillRect(x - W * 0.12, y - W * 0.12, W * 0.24, W * 0.24); }
  const tigerC = LOW.tiger.c, wW = W / k, wH = H / k;
  const glow = blurCopy('tigerGlow', tigerC, 0.22, 5);
  const B = bushSprites();
  const rustle = p < 0.3 ? Math.sin(t * 13) * 3 * smooth(0.0, 0.08, p) * (1 - smooth(0.15, 0.3, p)) : 0;
  const drawTiger = () => {
    ctx.save();
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = A * 0.85;
    ctx.drawImage(glow.c, px - wW / 2 - glow.pad, py - wH / 2 - glow.pad, wW + glow.pad * 2, wH + glow.pad * 2);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = A * 0.92;
    ctx.drawImage(tigerC, px - wW / 2, py - wH / 2, wW, wH);
    ctx.restore();
  };
  const drawBush = () => {
    ctx.save(); ctx.translate(rustle, 0);
    ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = A * 0.8;
    ctx.drawImage(B.glow.c, B.x0 - B.glow.pad, B.y0 - B.glow.pad, 400 + B.glow.pad * 2, 230 + B.glow.pad * 2);
    ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = A;
    blit(ctx, B.crisp);
    ctx.restore();
  };
  if (p < 0.18) { drawTiger(); drawBush(); } else { drawBush(); drawTiger(); }
  const trail = []; for (let kk = 0; kk < 10; kk++) { const qq = clamp(q - kk * 0.04, 0, 1); trail.push([lerp(1415, 1625, qq) - 80, lerp(850, 840, qq) - Math.sin(Math.PI * qq) * 330 + 20]); }
  if (p > 0.12) sparks(ctx, t, A, trail, 18, 777);
}


// ---- roller coaster
let COASTER = null;
function coasterTrack() {
  if (COASTER) return COASTER;
  const pts = [];
  const add = (x, y) => pts.push([x, y]);
  const G = 930;
  // approach
  for (let x = 1250; x < 1310; x += 10) add(x, G - 30);
  // lift hill: straight steep ramp
  const lift0 = pts.length;
  for (let s = 0; s <= 1; s += 0.025) { const e = s * s * (3 - 2 * s); add(lerp(1310, 1435, s), lerp(G - 30, 270, s < 0.15 ? s * s / 0.3 : s - 0.075) + 0); void e; }
  const lift1 = pts.length - 1;
  // crest
  for (let a = -Math.PI * 0.75; a <= -Math.PI * 0.25; a += 0.08) add(1460 + Math.cos(a) * 32, 300 + Math.sin(a) * 32);
  // drop
  for (let s = 0; s <= 1; s += 0.04) add(lerp(1485, 1560, s), lerp(280, 880, s * s * (3 - 2 * s) * 0.7 + s * 0.3));
  // valley
  for (let a = Math.PI; a >= Math.PI * 0.5; a -= 0.1) add(1600 + Math.cos(a) * 40, 880 + Math.sin(a) * 40 - 40 + 40);
  // loop (centre 1680, 790, r 110), entered at bottom going right, travelling counter-clockwise on screen
  for (let a = Math.PI / 2; a >= -Math.PI * 1.5 + 0.05; a -= 0.08) add(1660 + Math.cos(a) * 110 + (Math.PI / 2 - a) * 6, 810 + Math.sin(a) * 110);
  for (let x = 1700; x <= 1800; x += 10) add(x, 920);
  COASTER = { pts, lift0, lift1, G };
  return COASTER;
}
let COASTER_SP = null;
function coasterSprites() {
  if (COASTER_SP) return COASTER_SP;
  const T = coasterTrack(), pts = T.pts;
  const X0 = 1200, Y0 = 200, X1 = 1830, Y1 = 960;
  const draw = (g, glowOnly) => {
    g.lineCap = 'round'; g.lineJoin = 'round';
    // supports (lattice)
    g.strokeStyle = glowOnly ? 'rgba(255,120,40,0.5)' : 'rgba(255,140,60,0.45)'; g.lineWidth = 2;
    for (let i = 0; i < pts.length; i += 4) { const [x, y] = pts[i]; if (y > T.G - 40) continue; g.beginPath(); g.moveTo(x, y + 6); g.lineTo(x, T.G); g.stroke(); }
    g.lineWidth = 1.3; g.strokeStyle = 'rgba(255,140,60,0.3)';
    for (let i = T.lift0; i < T.lift1 - 4; i += 4) { const a = pts[i], b = pts[i + 4]; g.beginPath(); g.moveTo(a[0], a[1] + 6); g.lineTo(b[0], T.G); g.moveTo(b[0], b[1] + 6); g.lineTo(a[0], T.G); g.stroke(); }
    g.strokeStyle = 'rgba(255,150,70,0.6)'; g.lineWidth = 3; g.beginPath(); g.moveTo(1260, T.G); g.lineTo(1800, T.G); g.stroke();
    const rail = (off, w, col) => {
      g.beginPath();
      for (let i = 0; i < pts.length; i++) {
        const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)], n = Math.atan2(b[1] - a[1], b[0] - a[0]) - Math.PI / 2;
        const x = pts[i][0] + Math.cos(n) * off, y = pts[i][1] + Math.sin(n) * off; i ? g.lineTo(x, y) : g.moveTo(x, y);
      }
      g.strokeStyle = col; g.lineWidth = w; g.stroke();
    };
    rail(-5, glowOnly ? 6 : 3.2, 'rgba(255,170,80,0.95)'); rail(5, glowOnly ? 6 : 3.2, 'rgba(255,190,100,0.95)');
    g.strokeStyle = 'rgba(255,150,70,0.6)'; g.lineWidth = 2;
    for (let i = 0; i < pts.length - 1; i += 2) { const a = pts[i], b = pts[i + 1], n = Math.atan2(b[1] - a[1], b[0] - a[0]) - Math.PI / 2; g.beginPath(); g.moveTo(a[0] + Math.cos(n) * 8, a[1] + Math.sin(n) * 8); g.lineTo(a[0] - Math.cos(n) * 8, a[1] - Math.sin(n) * 8); g.stroke(); }
  };
  const crisp = sprite(X0, Y0, X1, Y1, g => draw(g, false), 1.25);
  const gm = sprite(X0, Y0, X1, Y1, g => draw(g, true), 0.5);
  const glow = staticGlow(gm.c, 0.5, 4); // => 0.25 px per world unit
  COASTER_SP = { crisp, glow, X0, Y0, X1, Y1 };
  return COASTER_SP;
}
function visionCoaster(ctx, t, v, A) {
  const p = clamp(v.p ?? 0, 0, 1);
  smokeBackdrop(ctx, t, A, VC.x, VC.y, VC.w, VC.h, 16, 307, 'rgba(255,110,40,0.09)');
  const T = coasterTrack(), pts = T.pts, SP = coasterSprites();
  ctx.save();
  // glow + crisp track (smoke loosens it as alpha fades)
  const loosen = (1 - A) * 18;
  ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = A * 0.9;
  ctx.drawImage(SP.glow.c, SP.X0 - SP.glow.pad - loosen, SP.Y0 - SP.glow.pad - loosen, SP.X1 - SP.X0 + 2 * (SP.glow.pad + loosen), SP.Y1 - SP.Y0 + 2 * (SP.glow.pad + loosen));
  ctx.globalAlpha = A;
  blit(ctx, SP.crisp);
  // chain on the lift hill (moving dashes)
  ctx.setLineDash([5, 7]); ctx.lineDashOffset = -t * 30; ctx.strokeStyle = 'rgba(255,220,150,0.7)'; ctx.lineWidth = 2;
  ctx.beginPath(); for (let i = T.lift0; i <= T.lift1; i++) { const [x, y] = pts[i]; i === T.lift0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y); } ctx.stroke(); ctx.setLineDash([]);
  // the car climbing the lift
  const fi = lerp(T.lift0 + 1, T.lift1, smooth(0, 1, p)), i0 = Math.min(T.lift1 - 1, Math.floor(fi)), u = fi - i0;
  const a = pts[i0], b = pts[i0 + 1];
  const cx = lerp(a[0], b[0], u), cy = lerp(a[1], b[1], u), ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
  const C = getCache();
  ctx.drawImage(C.glow, cx - 60, cy - 70, 120, 120);
  ctx.translate(cx, cy); ctx.rotate(ang);
  ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = 'rgba(255,200,120,0.95)';
  ctx.beginPath(); ctx.moveTo(-26, -8); ctx.lineTo(24, -8); ctx.quadraticCurveTo(30, -26, 18, -30); ctx.lineTo(-22, -30); ctx.quadraticCurveTo(-30, -26, -26, -8); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(255,235,190,1)'; for (const hx of [-12, 8]) { ctx.beginPath(); ctx.arc(hx, -38, 6, 0, 7); ctx.fill(); }
  ctx.fillStyle = 'rgba(120,40,15,0.9)'; for (const wx of [-16, 14]) { ctx.beginPath(); ctx.arc(wx, -6, 5, 0, 7); ctx.fill(); }
  ctx.restore();
  sparks(ctx, t, A * 0.8, pts.filter((_, i) => i % 6 === 0), 14, 909);
}


// ---- water
function visionWater(ctx, t, v, A) {
  const p = clamp(v.p ?? 0, 0, 1), X = v.x ?? 1525, Y = v.y ?? 600, s = v.scale ?? 1;
  ctx.save(); ctx.translate(X, Y); ctx.scale(s, s);
  // soft mist backdrop
  ctx.globalAlpha = A * 0.5;
  ctx.fillStyle = radial(ctx, 0, 40, 300, [[0, 'rgba(180,205,230,0.18)'], [1, 'rgba(180,205,230,0)']]); ctx.fillRect(-320, -300, 640, 640);
  ctx.globalAlpha = A;
  const tilt = lerp(0.1, 1.15, smooth(0, 0.22, p)) + Math.sin(t * 1.2) * 0.02;
  const jx = -120, jy = -190;
  // jug (outline-forward, translucent)
  ctx.save(); ctx.translate(jx, jy); ctx.rotate(tilt);
  ctx.beginPath(); ctx.moveTo(-34, -60); ctx.lineTo(30, -60); ctx.quadraticCurveTo(52, -66, 64, -76); ctx.quadraticCurveTo(52, -50, 46, -40);
  ctx.bezierCurveTo(70, -10, 66, 50, 30, 70); ctx.lineTo(-30, 70); ctx.bezierCurveTo(-66, 50, -66, -10, -40, -40); ctx.closePath();
  ctx.fillStyle = 'rgba(200,220,240,0.22)'; ctx.fill();
  ctx.strokeStyle = 'rgba(235,245,255,0.8)'; ctx.lineWidth = 3; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-46, -30); ctx.bezierCurveTo(-96, -30, -96, 40, -50, 40); ctx.lineWidth = 6; ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.beginPath(); ctx.ellipse(-22, 0, 7, 34, 0.1, 0, 7); ctx.fill();
  // water inside
  ctx.beginPath(); ctx.rect(-62, 10 - 30 * (1 - p), 124, 62); ctx.fillStyle = 'rgba(150,190,225,0.25)'; ctx.fill();
  ctx.restore();
  // spout position in world-local coords
  const sx = jx + Math.cos(tilt) * 64 - Math.sin(tilt) * -76, sy = jy + Math.sin(tilt) * 64 + Math.cos(tilt) * -76;
  const ground = 230;
  const flow = smooth(0.08, 0.2, p) * (1 - smooth(0.96, 1, p) * 0.5);
  const reach = smooth(0.1, 0.3, p); // stream head falling
  if (flow > 0.01) {
    const pts = [], N = 22, vx = 70;
    const endY = lerp(sy, ground, reach);
    for (let i = 0; i <= N; i++) {
      const u = i / N, y = lerp(sy, endY, u), fall = (y - sy) / (ground - sy + 1e-6);
      const x = sx + vx * Math.sqrt(Math.max(0, fall)) * 1.6 + Math.sin(t * 6 - u * 9) * 2.5 * u;
      pts.push([x, y, lerp(9, 5, u) * (0.6 + 0.4 * flow) * (1 + 0.15 * Math.sin(t * 9 - u * 14))]);
    }
    ctx.beginPath(); pts.forEach(([x, y, w], i) => (i ? ctx.lineTo(x - w, y) : ctx.moveTo(x - w, y)));
    for (let i = pts.length - 1; i >= 0; i--) ctx.lineTo(pts[i][0] + pts[i][2], pts[i][1]);
    ctx.closePath(); ctx.fillStyle = 'rgba(175,210,240,0.55)'; ctx.fill();
    ctx.beginPath(); pts.forEach(([x, y, w], i) => (i ? ctx.lineTo(x - w * 0.3, y) : ctx.moveTo(x - w * 0.3, y)));
    ctx.strokeStyle = 'rgba(245,250,255,0.8)'; ctx.lineWidth = 2; ctx.stroke();
    // splash where it lands
    if (reach > 0.98) {
      const ix = pts[pts.length - 1][0];
      for (let i = 0; i < 16; i++) {
        const per = 0.6 + h1(i * 7) * 0.5, ph = ((t / per + h1(i * 3)) % 1 + 1) % 1;
        const dir = (h1(i * 5) - 0.5) * 2.4, spd = 60 + 70 * h1(i * 9);
        const x = ix + Math.sin(dir) * spd * ph, y = ground - (Math.cos(dir) * spd * ph * 1.4 - 160 * ph * ph) * flow;
        ctx.fillStyle = `rgba(225,240,255,${0.75 * (1 - ph) * flow})`; ctx.beginPath(); ctx.arc(x, Math.min(y, ground), 2.5 + 2 * h1(i * 11), 0, 7); ctx.fill();
      }
      // crown
      ctx.strokeStyle = `rgba(230,242,255,${0.6 * flow})`; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.ellipse(ix, ground - 4, 26 + Math.sin(t * 8) * 3, 9, 0, Math.PI, 0); ctx.stroke();
    }
    // pool
    const pr = smooth(0.25, 1, p);
    if (pr > 0) {
      const ix = pts[pts.length - 1][0];
      const rx = 30 + 250 * pr, ry = rx * 0.22, cx = ix + 30 * pr;
      ctx.fillStyle = radial(ctx, cx, ground, rx, [[0, 'rgba(170,205,235,0.45)'], [0.8, 'rgba(170,205,235,0.3)'], [1, 'rgba(170,205,235,0)']]);
      ctx.save(); ctx.translate(cx, ground); ctx.scale(1, ry / rx); ctx.beginPath(); ctx.arc(0, 0, rx, 0, 7); ctx.restore(); ctx.fill();
      for (let k = 0; k < 3; k++) {
        const ph = ((t * 0.7 + k / 3) % 1), rr = lerp(10, rx * 0.95, ph);
        ctx.strokeStyle = `rgba(235,245,255,${0.45 * (1 - ph)})`; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.ellipse(ix, ground, rr, rr * 0.22, 0, 0, 7); ctx.stroke();
      }
      ctx.strokeStyle = 'rgba(240,248,255,0.45)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.ellipse(cx, ground, rx * 0.97, ry * 0.97, 0, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke();
    }
  }
  ctx.restore();
}

function drawVision(ctx, t, v) {
  if (!v) return;
  const A = clamp(v.alpha ?? 1, 0, 1); if (A <= 0.003) return;
  ctx.save();
  if (v.kind === 'words') visionWords(ctx, t, v, A);
  else if (v.kind === 'tiger') visionTiger(ctx, t, v, A);
  else if (v.kind === 'coaster') visionCoaster(ctx, t, v, A);
  else if (v.kind === 'water') visionWater(ctx, t, v, A);
  ctx.restore();
}

// ================================================================== ENV
const ENV = {
  name: 'hearth',
  extents: { ...EXT },
  anchors: {
    annoyWindow: { x: 380, y: 1560 },
    angerSeat: { x: 700, y: 1440 },
    mayaSeat: { x: 960, y: 1440 },
    fearPace: { x0: 1000, x1: 1330, y: 1620 },
    sadCorner: { x: 170, y: 1700 },
    mayaFloorBySad: { x: 330, y: 1710 },
    fire: { x: 1525, y: 1380 },
    windowCenter: { x: 650, y: 640 },
    doorCenter: { x: 200, y: 1180 },
    doorThreshold: { x: 200, y: 1480 },
    teaCup: { x: TEA.x, y: TEA.y },
    bellows: { x: 1300, y: 1250 },
    bellowsHook: { x: 1300, y: 1140 },
    lantern: { x: -170, y: 1632 },
    tableCenter: { x: 800, y: 1360 },
    tableTopY: 1360,
    chair1100: { x: 1160, y: 1450 },
    mantelPhoto: { x: 1340, y: 900 },
    mantelY: 958,
    visionCenter: { x: VC.x, y: VC.y },
    hearthstone: { x: 1525, y: 1500 },
    wide: { x: 800, y: 1000, zoom: 0.72 },
  },
};

module.exports = { ENV, drawBack, drawFront, lightAt, drawVision, _flick: flick };
